"""NR normalization foundation: literal words and order exchanges only.

No outer-cell engine, checkpoint, frontier, or capacity helper is imported.
The NR3 census is complete; optional NR4 trap discovery is a bounded control.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import time


def permutations(n: int) -> tuple[str, ...]:
    return tuple("".join(p) for p in itertools.permutations(map(str, range(n))))


def windows(word: str, n: int) -> list[tuple[int, str]]:
    alphabet = set(map(str, range(n)))
    return [(i, word[i:i+n]) for i in range(len(word)-n+1)
            if set(word[i:i+n]) == alphabet]


def overlap(a: str, b: str) -> int:
    return next(k for k in range(len(a), -1, -1) if a[len(a)-k:] == b[:k])


def spell(order: tuple[str, ...]) -> str:
    return order[0] + "".join(b[overlap(a, b):] for a, b in zip(order, order[1:]))


def metrics(order: tuple[str, ...]) -> tuple[int, int]:
    w = spell(order)
    return len(w), len(windows(w, len(order[0]))) - len(order)


def literal_metrics(word: str, n: int) -> dict:
    ww = windows(word, n)
    counts = Counter(p for _, p in ww)
    return dict(word=word, length=len(word), occurrences=len(ww), distinct=len(counts),
                duplicates=len(ww)-len(counts), windows=ww, counts=dict(sorted(counts.items())))


def loop_delete(word: str, n: int, a: int, b: int) -> dict:
    assert 0 <= a < b <= len(word)-n and word[a:a+n] == word[b:b+n]
    assert (a, word[a:a+n]) in windows(word, n)
    reduced = word[:a] + word[b:]
    before = windows(word, n)
    after = windows(reduced, n)
    lost = sorted({p for _, p in before} - {p for _, p in after})
    exact_lost = sorted(p for p in {p for _, p in before}
                        if all(a < i < b for i, q in before if q == p))
    assert lost == exact_lost
    return dict(before=word, after=reduced, boundary=word[a:a+n], a=a, b=b,
                lost=lost, coverage_preserved=not lost,
                globally_unique_inside=[p for i, p in before if a < i < b
                                       and sum(q == p for _, q in before) == 1])


def hidden_relocations(order: tuple[str, ...]) -> set[tuple[str, ...]]:
    n = len(order[0])
    children = set()
    for a, b in zip(order, order[1:]):
        edge = a + b[overlap(a, b):]
        for offset, t in windows(edge, n):
            if offset in (0, len(edge)-n):
                continue
            new = list(order)
            new.remove(t)
            new.insert(new.index(a)+1, t)
            child = tuple(new)
            assert metrics(child)[0] <= metrics(order)[0]
            children.add(child)
    return children


def all_relocations(order: tuple[str, ...]) -> set[tuple[str, ...]]:
    out = set()
    for old in range(len(order)):
        for new in range(len(order)):
            child = list(order)
            t = child.pop(old)
            child.insert(new, t)
            out.add(tuple(child))
    out.discard(order)
    return out


def normalization_graph(n: int = 3) -> dict:
    assert n == 3, "No broad n=4/n=6 order enumeration is allowed here."
    vertices = list(itertools.permutations(permutations(n)))
    index = {o: i for i, o in enumerate(vertices)}
    mm = [metrics(o) for o in vertices]
    clean = [i for i, m in enumerate(mm) if m[1] == 0]
    result = dict(n=n, vertices=len(vertices), clean_orders=len(clean),
                  minimum_length=min(m[0] for m in mm),
                  minimum_orders=sum(m[0] == min(t[0] for t in mm) for m in mm),
                  minimum_non_NR_orders=sum(m[0] == min(t[0] for t in mm) and m[1] > 0 for m in mm))
    for name, generator in (("hidden_only", hidden_relocations), ("single_vertex", all_relocations)):
        reverse = [[] for _ in vertices]
        edge_count = 0
        for u, order in enumerate(vertices):
            for child in generator(order):
                v = index[child]
                if mm[v][0] <= mm[u][0]:
                    reverse[v].append(u)
                    edge_count += 1
        distance = {i: 0 for i in clean}
        next_vertex = {}
        todo = deque(clean)
        while todo:
            v = todo.popleft()
            for u in sorted(reverse[v]):
                if u not in distance:
                    distance[u] = distance[v]+1
                    next_vertex[u] = v
                    todo.append(u)
        certificates = []
        for u in sorted(distance):
            path = [list(vertices[u])]
            v = u
            while v in next_vertex:
                v = next_vertex[v]
                path.append(list(vertices[v]))
            certificates.append(dict(start_order=list(vertices[u]), path=path))
        absent = [i for i in range(len(vertices)) if i not in distance]
        result[name] = dict(edges=edge_count, normalized=len(distance), unresolved=len(absent),
                            maximum_certificate_steps=max(distance.values()),
                            unresolved_orders=[list(vertices[i]) for i in absent],
                            certificates=certificates)
    return result


def verify_normalization_certificates(data: dict) -> dict:
    """Does not trust the generator's edge set, distances, spelling or overlap.

    Every move is checked by literal assembly plus a direct remove-one test.
    Coverage/duplicates are checked by membership in the six explicitly listed words.
    """
    symbols = ("012", "021", "102", "120", "201", "210")
    universe = set(itertools.permutations(symbols))
    def literal(order):
        text = order[0]
        for target in order[1:]:
            fits = [j for j in range(1, 4) if (text+target[3-j:])[-3:] == target]
            text += target[3-min(fits):]
        return text
    certs = data["single_vertex"]["certificates"]
    assert {tuple(c["start_order"]) for c in certs} == universe
    checked_moves = 0
    for cert in certs:
        path = [tuple(x) for x in cert["path"]]
        assert path[0] == tuple(cert["start_order"])
        for order in path:
            assert order in universe
            text = literal(order)
            assert all(p in text for p in symbols)
        for a, b in zip(path, path[1:]):
            assert any(tuple(x for x in a if x != p) == tuple(x for x in b if x != p) for p in symbols)
            assert len(literal(b)) <= len(literal(a))
            checked_moves += 1
        text = literal(path[-1])
        occ = [text[i:i+3] for i in range(len(text)-2) if text[i:i+3] in symbols]
        assert len(occ) == 6 and set(occ) == set(symbols)
    return dict(verified=True, all_orders=len(universe), certificate_paths=len(certs), checked_moves=checked_moves)


def exact_completion_cost(word: str, n: int) -> dict:
    """Unrestricted character automaton, not the permutation-overlap search."""
    ps = permutations(n)
    ids = {p: i for i, p in enumerate(ps)}
    covered = sum(1 << ids[p] for p in {p for _, p in windows(word, n)})
    full = (1 << len(ps))-1
    start = word[-n+1:], covered
    todo = deque([(start, "")])
    seen = {start}
    while todo:
        (suffix, mask), tail = todo.popleft()
        if mask == full:
            return dict(cost=len(tail), tail=tail, visited_states=len(seen), covered_mask=covered)
        for x in map(str, range(n)):
            candidate = suffix+x
            new_mask = mask | (1 << ids[candidate] if candidate in ids else 0)
            child = candidate[-n+1:], new_mask
            if child not in seen:
                seen.add(child)
                todo.append((child, tail+x))
    raise AssertionError("Concatenating all permutations is always a completion.")


def splicing_balance(word: str, n: int) -> dict:
    ww = windows(word, n)
    starts, endpoints = [], []
    for j, (i, p) in enumerate(ww):
        if j == 0 or i != ww[j-1][0]+1:
            starts.append(p)
        if j == len(ww)-1 or ww[j+1][0] != i+1:
            endpoints.append(p[1:]+p[0])
    return dict(word=word, pass_entries=dict(Counter(starts)),
                next_rotation_endpoints=dict(Counter(endpoints)),
                successor_matching_exists=Counter(starts) == Counter(endpoints))


def nr4_lex_trap(seed_count: int = 30) -> dict:
    """Bounded discovery, followed by COMPLETE one-move neighborhood check.

    Refutes a stronger universal *strict one-move* descent claim only.
    It does not certify a closed plateau/SCC or failure of NR4.
    """
    ps = permutations(4)
    rng = random.Random(14120260909)
    traps = []
    evaluated = 0
    for _ in range(seed_count):
        order = list(ps)
        rng.shuffle(order)
        order = tuple(order)
        while True:
            current = metrics(order)
            neighborhood = sorted(all_relocations(order))
            evaluated += len(neighborhood)
            better = [(metrics(c), c) for c in neighborhood if metrics(c) < current]
            if not better:
                if current[1]:
                    hist = Counter(metrics(c) for c in neighborhood)
                    traps.append(dict(order=list(order), word=spell(order), length=current[0],
                                      duplicates=current[1], neighbors=len(neighborhood),
                                      neighborhood_metrics=[dict(length=k[0], duplicates=k[1], count=v)
                                                            for k, v in sorted(hist.items())]))
                break
            order = min(better)[1]
    return dict(scope="BOUNDED_DISCOVERY_COMPLETE_LOCAL_NEIGHBORHOOD_ONLY", seed_count=seed_count,
                evaluated_neighbors=evaluated, found_traps=len(traps),
                minimal_found=min(traps, key=lambda r: (r["length"], r["duplicates"], r["word"])) if traps else None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nr4-seeds", type=int, default=0)
    ap.add_argument("--output")
    args = ap.parse_args()
    started = time.perf_counter()
    root = Path(__file__).resolve().parents[1]
    rel = Path(__file__).resolve().relative_to(root).as_posix()
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    committed = subprocess.check_output(['git','show',commit+':'+rel],cwd=root)
    runtime = Path(__file__).read_bytes()
    assert committed == runtime, 'commit/push exact source before finite jobs'
    graph = normalization_graph()
    checked = verify_normalization_certificates(graph)
    shortcut_order = ("012", "120", "201", "021", "210", "102")
    plateau_order = ("012", "210", "102", "201", "021", "120")
    partial = loop_delete("01202102101200120010200201", 3, 0, 9)
    assert partial["lost"] == ["021", "210"] and not partial["globally_unique_inside"]
    plateau_children = [list(x) for x in sorted(hidden_relocations(plateau_order))]
    assert len(plateau_children) == 1 and spell(tuple(plateau_children[0])) == spell(plateau_order)
    contexts = {w: exact_completion_cost(w, 3) for w in ("0120012", "0121012")}
    assert [contexts[w]["cost"] for w in contexts] == [6, 5]
    result = dict(schema="round141-nr-foundation-v1", status="NR6_UNPROVED_EXACT_ORDER_EXCHANGE_HARD_CORE",
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  graph=graph, independent_certificate_check=checked,
                  counterexamples=dict(hidden_repeat_regenerated=dict(order=list(shortcut_order),
                       literal=literal_metrics(spell(shortcut_order), 3)),
                       hidden_relocation_plateau=dict(order=list(plateau_order), children=plateau_children,
                       literal=literal_metrics(spell(plateau_order), 3)),
                       no_globally_unique_does_not_imply_direct_deletion=partial,
                       endpoint_and_coverage_count_insufficient=contexts,
                       non_NR_splicing_multiset_failure=splicing_balance("0120102102", 3)))
    if args.nr4_seeds:
        result["nr4_bounded_control"] = nr4_lex_trap(args.nr4_seeds)
    result.update(source_commit=commit,
                  committed_source_sha256=hashlib.sha256(committed).hexdigest(),
                  runtime_source_sha256=hashlib.sha256(runtime).hexdigest(),
                  executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                  argv=[sys.executable,*sys.argv],seconds=time.perf_counter()-started,
                  NR6='UNPROVED',global_L6_ge872='NOT_PROVED')
    payload = json.dumps(result, ensure_ascii=False, indent=2)+"\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8", newline="\n")
    print(json.dumps(dict(status=result["status"], vertices=graph["vertices"],
                         hidden_normalized=graph["hidden_only"]["normalized"],
                         relocation_normalized=graph["single_vertex"]["normalized"],
                         verified=checked, nr4=result.get("nr4_bounded_control")), ensure_ascii=False))


if __name__ == "__main__":
    main()
