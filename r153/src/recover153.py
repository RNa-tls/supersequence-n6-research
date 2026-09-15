#!/usr/bin/env python3
"""Round 153 Phase 1 -- recover the round-148 equality/coexistence proof objects
from committed files, without trusting the round-148 summary.

Everything reported here is read off disk: the witness files, the pruning tables
the enumeration used, the solver sources, and their hashes.  The one judgement
made is whether the pruning table round 148 fed its enumerator is DOMINATED by
the round-152 certified capacities -- because a prune is only admissible if the
value it prunes with has been proved, and round 152 proved 1,101 of them.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R148 = ROOT / "r148"
R152 = ROOT / "r152"

ARTEFACTS = [
    "r148/certs/witnesses_148.json",
    "r148/certs/synthetic_controls_148.json",
    "r148/certs/solver_controls_148.json",
    "r148/witnesses/row96_table.jsonl",
    "r148/witnesses/row96_notable.jsonl",
    "r148/witnesses/row92_table.jsonl",
    "r148/witnesses/row92_notable.jsonl",
    "r148/witnesses/ub_row96.txt",
    "r148/witnesses/ub_row92.txt",
    "r148/src/witness148.py",
    "r148/src/synthetic_control148.py",
    "src/l6_cover_bfs_146.py",
    "src/l6_circuit_coexist_144.py",
    "src/l6_coexist_check3_144.py",
    "r147/src/l6_chain_capacity_147.c",
    "r147/src/ub147.py",
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_jsonl(p):
    return [json.loads(x)["ports"] for x in Path(p).read_text().splitlines()
            if x.strip()]


def read_ub(p):
    """Round-147 UB file: 'UB7 <count>' then '<b> <d> <a> <bb> <e> <h> <val>'."""
    lines = Path(p).read_text().splitlines()
    assert lines[0].split()[0] == "UB7", lines[0]
    n = int(lines[0].split()[1])
    rows = {}
    for ln in lines[1:]:
        if not ln.strip():
            continue
        *k, v = (int(x) for x in ln.split())
        rows[tuple(k)] = v
    assert len(rows) == n, (len(rows), n)
    return rows


def main():
    out = {"artefacts": {}}
    for rel in ARTEFACTS:
        p = ROOT / rel
        out["artefacts"][rel] = (dict(present=True, sha256=sha(p),
                                      bytes=p.stat().st_size)
                                 if p.exists() else dict(present=False))

    w148 = json.loads((R148 / "certs" / "witnesses_148.json").read_text())
    out["round148_rows"] = []
    for r in w148["rows"]:
        out["round148_rows"].append(dict(
            name=r["name"], cell="|".join(map(str, r["cell"])),
            target=r["target"], circuits=r["circuits"],
            ub_validator_ok=r["ub_validator_ok"],
            route_table={k: v for k, v in r["route_table"].items()
                         if k != "canonical"},
            route_notable={k: v for k, v in r["route_notable"].items()
                           if k != "canonical"},
            routes_agree=r["routes_agree"],
            all_excluded=r["all_excluded"], controls_ok=r["controls_ok"],
            n_certificates=len(r["certificates"])))

    # the witness files actually on disk
    out["witness_files"] = {}
    for name in ("row96", "row92"):
        for kind in ("table", "notable"):
            p = R148 / "witnesses" / f"{name}_{kind}.jsonl"
            ports = load_jsonl(p)
            out["witness_files"][f"{name}_{kind}"] = dict(
                count=len(ports), lengths=sorted({len(x) for x in ports}),
                starts_at_0=all(x[0] == 0 for x in ports))

    # is every value round 148 pruned with one that round 152 PROVED?
    cert = {}
    for rel in ("verify_all_c152.json",):
        for row in json.loads((R152 / "certs" / rel).read_text())["rows"]:
            if row["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
                cert[tuple(int(x) for x in row["cell"].split("|"))] = row["cap"]
    out["round152_certified_cells"] = len(cert)
    ubcheck = {}
    for name, cell in (("row96", (0, 14, 0, 0, 0, 0)),
                       ("row92", (0, 8, 0, 0, 0, 1))):
        rows = read_ub(R148 / "witnesses" / f"ub_{name}.txt")
        bad, unproved = [], []
        for k, v in rows.items():
            # the entry must be >= some PROVED capacity for a cell dominating k,
            # or >= the analytic bound; otherwise round 148 pruned with a value
            # round 152 has not established.
            analytic = 120 + k[2] + k[3] + k[4]
            best = min([analytic] + [c for kk, c in cert.items()
                                     if all(a >= b for a, b in zip(kk, k))
                                     and kk != cell])
            if v < best:
                bad.append((k, v, best))
            if v > analytic and not any(all(a >= b for a, b in zip(kk, k))
                                        and kk != cell and c <= v
                                        for kk, c in cert.items()):
                unproved.append((k, v))
        ubcheck[name] = dict(entries=len(rows), self_excluded=cell not in rows,
                             below_certified_bound=len(bad),
                             examples=[[list(x[0]), x[1], x[2]] for x in bad[:5]],
                             not_backed_by_a_certified_cell=len(unproved))
    out["round148_prune_tables_vs_round152"] = ubcheck
    out["prune_tables_are_dominated_by_certified_values"] = all(
        v["below_certified_bound"] == 0 for v in ubcheck.values())

    try:
        out["git_head"] = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception as exc:                                     # noqa: BLE001
        out["git_head"] = f"unavailable: {exc}"

    (ROOT / "r153" / "certs" / "recover_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "artefacts"},
                     indent=1))
    absent = [k for k, v in out["artefacts"].items() if not v["present"]]
    print("absent artefacts:", absent)
    return 0 if not absent else 1


if __name__ == "__main__":
    sys.exit(main())
