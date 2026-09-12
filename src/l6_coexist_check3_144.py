#!/usr/bin/env python3
"""Third, independent solver for the circuit-coexistence question.

Materially different from `l6_circuit_coexist_144.py`: no incremental cover
state and no pivot hexagon.  It enumerates c-subsets of the candidate orbits
directly, ordered by |hex(orbit) cap F| descending, pruned only by the
arithmetic necessity

    sum over the subset of |hex(orbit) cap F|  >=  |F|,

then tests the union literally.  Since |F| = 4c and an orbit meets five
hexagons, that bound is extremely tight and the enumeration is small; the
counts it prints can be checked by hand against the overlap histogram.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from verify_f2_structure_126 import setup                          # noqa: E402

G = setup(6)
HEX, ORB, IDX, P6, TA = G["hexid"], G["orbid"], G["idx"], G["perms"], G["tau"]
NP, NH, NQ = 720, 120, 144
OH = []
for q in range(NQ):
    v = next(u for u in range(NP) if ORB[u] == q)
    hs, x = set(), v
    for _ in range(5):
        hs.add(HEX[x])
        x = IDX[TA(P6[x])]
    OH.append(hs)


class _Found(Exception):
    """Opt-in early exit; default behaviour is unchanged and exhaustive."""


def solve(chain, c, first_only=False):
    Hc = {HEX[v] for v in chain}
    Oc = {ORB[v] for v in chain}
    F = set(range(NH)) - Hc
    cands = sorted(((len(OH[q] & F), q) for q in range(NQ)
                    if q not in Oc and OH[q] & F), reverse=True)
    n = len(cands)
    sols, nodes = [], [0]

    def rec(i, chosen, ssum):
        nodes[0] += 1
        if len(chosen) == c:
            if ssum >= len(F) and set().union(*[OH[q] & F for q in chosen]) == F:
                sols.append(sorted(chosen))
                if first_only:
                    raise _Found()
            return
        slots = c - len(chosen)
        if i >= n:
            return
        if ssum + sum(k for k, _ in cands[i:i + slots]) < len(F):
            return                           # even the best remaining is too small
        for j in range(i, n):
            k, q = cands[j]
            if ssum + k + sum(kk for kk, _ in cands[j + 1:j + slots]) < len(F):
                break
            rec(j + 1, chosen + [q], ssum + k)

    try:
        rec(0, [], 0)
    except _Found:
        pass
    return dict(ports=len(chain), free=len(F), c=c, candidates=n,
                overlap_top=[k for k, _ in cands[:c]], nodes=nodes[0],
                solutions=len(sols), examples=sols[:2], ok=bool(sols))


if __name__ == "__main__":
    path, c = sys.argv[1], int(sys.argv[2])
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        r = solve(json.loads(line)["ports"], c)
        out.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    tag = Path(path).stem
    (ROOT / "outputs" / f"rr_l6_coexist3_{tag}_144.json").write_text(
        json.dumps(dict(any_ok=any(x["ok"] for x in out), detail=out),
                   ensure_ascii=False, indent=1))
    print("any admits the circuits:", any(x["ok"] for x in out))
