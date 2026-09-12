#!/usr/bin/env python3
"""Second, deliberately different check of the circuit-coexistence obstruction.

`l6_circuit_coexist_144.py` runs an exact-cover DFS.  This module instead
computes, for every candidate tau-orbit, how many of the chain's UNUSED
hexagons it meets, and applies the averaging bound

    sum over the c chosen orbits of |hex(orbit) cap F|  >=  |F| = 4c,

so a solution needs at least one orbit meeting 4 or more hexagons of F, and in
fact the multiset of the c values must average at least 4.  If the largest
attainable value is 3 or less the obstruction is immediate and can be checked
by hand from the printed histogram.  No search is involved.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from verify_f2_structure_126 import setup                          # noqa: E402

G = setup(6)
HEX, ORB, SG, IDX, P6 = G["hexid"], G["orbid"], G["sig"], G["idx"], G["perms"]
NP, NH, NQ = 720, 120, 144

# rebuild the orbit -> hexagon incidence from scratch, via tau applied literally
TA = G["tau"]
orb_members = [[] for _ in range(NQ)]
for v in range(NP):
    orb_members[ORB[v]].append(v)
orb_hexes = []
for q in range(NQ):
    v = orb_members[q][0]
    hs, x = [], v
    for _ in range(5):
        hs.append(HEX[x])
        x = IDX[TA(P6[x])]
    assert sorted(hs) == sorted({HEX[u] for u in orb_members[q]})
    orb_hexes.append(set(hs))
assert all(len(h) == 5 for h in orb_hexes)


def analyse(chain, c):
    Hc = {HEX[v] for v in chain}
    Oc = {ORB[v] for v in chain}
    F = set(range(NH)) - Hc
    hist = Counter()
    best = 0
    for q in range(NQ):
        if q in Oc:
            continue
        k = len(orb_hexes[q] & F)
        hist[k] += 1
        best = max(best, k)
    # the c chosen orbits must average at least 4 hexagons of F
    top = sorted((len(orb_hexes[q] & F) for q in range(NQ) if q not in Oc),
                 reverse=True)[:c]
    return dict(ports=len(chain), free=len(F), c=c, hex_simple=(len(Hc) == len(chain)),
                max_overlap=best, best_c_sum=sum(top), needed=len(F),
                histogram={str(k): v for k, v in sorted(hist.items())},
                impossible_by_averaging=(sum(top) < len(F)))


if __name__ == "__main__":
    path, c = sys.argv[1], int(sys.argv[2])
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        r = analyse(json.loads(line)["ports"], c)
        out.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    tag = Path(path).stem
    (ROOT / "outputs" / f"rr_l6_coexist2_{tag}_144.json").write_text(
        json.dumps(dict(all_impossible=all(x["impossible_by_averaging"] for x in out),
                        detail=out), ensure_ascii=False, indent=1))
    print("all impossible by averaging:",
          all(x["impossible_by_averaging"] for x in out))
