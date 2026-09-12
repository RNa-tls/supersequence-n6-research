"""Small exhaustive literal controls for the independent generic port engine.

No producer table/recurrence is imported. The Python oracle enumerates short
entry sequences using tuple strings, explicit sets, and shortest overlap.
This is a bounded implementation cross-check, not the necessary-model proof.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WORDS = list(itertools.permutations(range(6)))
INDEX = {w: i for i, w in enumerate(WORDS)}


def geometry():
    hexa = {}
    orbits = {}
    edges = {}
    for w in WORDS:
        hexa[w] = min(w[s:] + w[:s] for s in range(6))
        orbits[w] = min(w[s:5] + w[:s] + w[5:] for s in range(5))
        ep = w[-1:] + w[:-1]
        available = []
        for t in WORDS:
            overlap = next((n for n in range(5, 0, -1) if ep[-n:] == t[:n]), 0)
            weight = 6 - overlap
            if weight == 1:
                continue
            is_e = weight == 2 and t == w[1:5] + w[:1] + w[5:]
            is_a = weight == 2 and t == w[1:] + w[:1]
            is_q = weight == 3 and t == w[2:] + w[:2]
            if weight == 2:
                assert is_e != is_a
            available.append((t, weight, is_e, is_a, is_q))
        assert sum(e[1] == 2 for e in available) == 2
        assert sum(e[1] == 3 for e in available) == 6
        edges[w] = available
    return hexa, orbits, edges


def brute(query, geometry_data):
    B, D, A, Q, R, H, P = query
    hexa, orbits, edges = geometry_data
    answer = {}
    initial = WORDS[0]

    def rec(path, seen, opened, covered, b, a, q, repeated, heavy):
        if len(path) == P:
            d = 5 * len(opened) - P
            if a == A and q == Q and d <= D:
                answer[tuple(INDEX[x] for x in path)] = (b, d, len(opened), a, q, repeated, heavy)
            return
        for t, weight, is_e, is_a, is_q in edges[path[-1]]:
            if t in seen:
                continue
            bb = b + (not is_e and orbits[t] in opened)
            aa, qq = a + is_a, q + is_q
            rr = repeated + (hexa[t] in covered)
            hh = heavy + max(0, weight - 3)
            if bb > B or aa > A or qq > Q or rr > R or hh > H:
                continue
            rec(path + (t,), seen | {t}, opened | {orbits[t]}, covered | {hexa[t]}, bb, aa, qq, rr, hh)

    rec((initial,), {initial}, {orbits[initial]}, {hexa[initial]}, 0, 0, 0, 0, 0)
    return answer


def run(executable, query, target, cap=0, table=None):
    B, D, A, Q, R, H, P = query
    command = [str(executable), str(B), str(D), str(cap), str(A), str(Q), str(R), str(H), str(P), str(target)]
    if table is not None:
        command.append(str(table))
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    meta = json.loads(proc.stdout)
    paths = {}
    for line in target.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        key = tuple(row["entries"])
        assert key not in paths
        paths[key] = tuple(row[x] for x in ("b", "D", "O", "A", "Qs", "R", "H"))
    assert len(paths) == meta["exported_prefixes"]
    return meta, paths, command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--producer", type=Path)
    parser.add_argument("--certified-bounds", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    executable = args.exe.resolve()
    geo = geometry()
    # B,D,A,Q,R,H,P: E, A, B, mixed A/B, repeated entry, and heavy w4..w6.
    queries = [
        (0, 4, 0, 0, 0, 0, 1),
        (0, 8, 0, 0, 0, 0, 3),
        (1, 10, 1, 0, 1, 0, 4),
        (1, 10, 0, 1, 1, 0, 4),
        (2, 15, 1, 1, 3, 0, 4),
        (2, 15, 2, 0, 1, 0, 4),
        (1, 15, 0, 0, 2, 1, 3),
        (2, 15, 1, 0, 3, 2, 3),
        (2, 15, 0, 0, 3, 3, 3),
        (1, 0, 0, 0, 1, 0, 5),
    ]
    controls = []
    with tempfile.TemporaryDirectory(prefix="r143_general_ports_") as directory:
        tmp = Path(directory)
        # A and B are necessarily repeated-hex arrivals. Thus exact remaining
        # a+q > remaining R gives certified upper zero; all other cells INF.
        table = tmp / "repeat_impossibility.txt"
        rows = []
        for a, q, r, h, b, delta in itertools.product(range(3), range(2), range(4), range(4), range(3), range(26)):
            upper = 0 if a + q > r else 720
            rows.append(f"{a} {q} {r} {h} {b} {delta} {upper}\n")
        table.write_text("".join(rows), encoding="ascii")
        for number, query in enumerate(queries):
            expected = brute(query, geo)
            plain, paths, command = run(executable, query, tmp / f"plain_{number}.jsonl")
            bounded, bounded_paths, _ = run(executable, query, tmp / f"bounded_{number}.jsonl", table=table)
            assert plain["completed"] and bounded["completed"]
            assert not plain["capped"] and not bounded["capped"]
            assert expected == paths == bounded_paths, (query, len(expected), len(paths), len(bounded_paths))
            assert plain["geometry_comparisons"] == 720 * 720
            producer_checks = []
            if args.producer:
                B, D, A, Q, R, H, P = query
                for variant, producer_table in [("plain", None), ("trivial", table),
                                                 ("certified", args.certified_bounds)]:
                    if variant == "certified" and producer_table is None:
                        continue
                    destination = tmp / f"producer_{variant}_{number}.jsonl"
                    producer_command = [str(args.producer.resolve()), str(B), str(D), "0", str(A), str(Q),
                                        str(R), str(H), str(P), str(destination)]
                    if producer_table is not None:
                        producer_command.append(str(producer_table.resolve()))
                    result = subprocess.run(producer_command, capture_output=True, text=True, check=True)
                    meta = json.loads(result.stdout)
                    literal_rows = [tuple(json.loads(line)) for line in destination.read_text().splitlines()]
                    assert len(literal_rows) == len(set(literal_rows)) == meta["exported_prefixes"]
                    assert meta["completed"] and not meta["capped"]
                    assert set(literal_rows) == set(expected), (query, variant)
                    producer_checks.append({"variant": variant, "nodes": meta["nodes"], "prefixes": len(literal_rows)})
            if args.certified_bounds:
                certified, certified_paths, _ = run(executable, query, tmp / f"certified_{number}.jsonl",
                                                    table=args.certified_bounds.resolve())
                assert certified["completed"] and certified_paths == expected
            existing = Path(command[-1])
            old_digest = hashlib.sha256(existing.read_bytes()).hexdigest()
            refused = subprocess.run(command, capture_output=True, text=True)
            assert refused.returncode != 0 and hashlib.sha256(existing.read_bytes()).hexdigest() == old_digest
            controls.append({"query": list(query), "literal_paths": len(paths), "nodes": plain["nodes"],
                             "bounded_nodes": bounded["nodes"], "suffix_prunes": bounded["suffix_bound_prunes"],
                             "producer_comparisons": producer_checks})
        limited, _, _ = run(executable, queries[2], tmp / "limited.jsonl", cap=1)
        assert limited["nodes"] == 1 and limited["capped"] and not limited["completed"]
        assert limited["status"] == "UNKNOWN_CAP"
    result = {"schema": "round143-general-port-small-controls-v1", "verified": True,
              "scope": "bounded literal implementation cross-check; no generic capacity theorem",
              "engine_sha256": hashlib.sha256((ROOT / "src/round143_general_ports_independent.c").read_bytes()).hexdigest(),
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "controls": controls, "cap_is_unknown": True, "overwrite_refused": True}
    if args.certified_bounds:
        result["certified_bound_sha256"] = hashlib.sha256(args.certified_bounds.read_bytes()).hexdigest()
    if args.producer:
        result["producer_source_sha256"] = hashlib.sha256((ROOT / "src/round143_general_runs_codex.c").read_bytes()).hexdigest()
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
