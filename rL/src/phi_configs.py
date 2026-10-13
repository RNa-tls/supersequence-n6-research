#!/usr/bin/env python3
"""Round L (section 14) -- classification of the minimal repair configurations of a phi-set in
two-world routes.

A configuration = partition of the 42 classes of P({a,b},C) into world-a column segments and
world-b row segments (chains inside P).  Cost E_P = sum (7 - l)/7.  This script enumerates ALL
partitions with 7*E_P <= MAXC (exact cover by Algorithm X with cost pruning), and classifies them
by (number of world-a classes, multiset of (world, length)), and by orbit under the cyclic symmetry
of C (relabelling C's symbols by the rotation, which permutes columns and rows simultaneously).
usage: phi_configs.py [MAXC=14]"""
import os, sys, json, itertools
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from worlds import World, canon_cyc

def main():
    MAXC = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    W = World(8); a, b = 7, 6
    key = sorted(W.phi_sets(a, b))[0]; C = key[2]
    P = sorted(W.phi_sets(a, b)[key]); Ps = set(P); idx = {c: i for i, c in enumerate(P)}
    segs = []
    for s_ in (a, b):
        for D, mem in W.orb_members[s_].items():
            if not set(mem) <= Ps: continue
            cyc = W.orbit_cycle(s_, D); m = len(cyc)
            for st in range(m):
                for l in range(1, m + 1):
                    segs.append((s_, frozenset(idx[cyc[(st + t) % m]] for t in range(l)), l))
    segs = list({(s_, cl): (s_, cl, l) for s_, cl, l in segs}.values())
    by_cell = [[] for _ in range(42)]
    for k, (s_, cl, l) in enumerate(segs):
        for c in cl: by_cell[c].append(k)
    sols = []
    def rec(covered, chosen, cost):
        if cost > MAXC: return
        if len(covered) == 42:
            sols.append(tuple(sorted(chosen))); return
        # choose the uncovered cell with fewest options
        best = None
        for c in range(42):
            if c in covered: continue
            opts = [k for k in by_cell[c] if not (segs[k][1] & covered)]
            if best is None or len(opts) < len(best[1]):
                best = (c, opts)
                if len(opts) <= 1: break
        c, opts = best
        for k in opts:
            s_, cl, l = segs[k]
            rec(covered | cl, chosen + [k], cost + 7 - l)
    rec(frozenset(), [], 0)
    # rotation symmetry of C: relabel C[i] -> C[i+1]
    rot = {C[i]: C[(i + 1) % 6] for i in range(6)}; rot[a] = a; rot[b] = b
    def img(cell):
        c = W.reps[P[cell]]; return idx[W.cid[canon_cyc([rot[x] for x in c])]]
    seg_index = {(s_, cl): k for k, (s_, cl, l) in enumerate(segs)}
    def rot_sol(sol):
        out = []
        for k in sol:
            s_, cl, l = segs[k]
            out.append(seg_index[(s_, frozenset(img(c) for c in cl))])
        return tuple(sorted(out))
    seen = set(); orbits = []
    for s in sols:
        if s in seen: continue
        orb = {s}; t = s
        for _ in range(5):
            t = rot_sol(t); orb.add(t)
        seen |= orb; orbits.append(s)
    def shape(sol):
        A = sum(segs[k][2] for k in sol if segs[k][0] == a)
        lens = tuple(sorted((("a" if segs[k][0] == a else "b") + str(segs[k][2]) for k in sol)))
        cost = sum(7 - segs[k][2] for k in sol)
        return (cost, A, lens)
    tab = Counter(shape(s) for s in orbits)
    res = dict(phi_set=[a, b, list(C)], max_7E=MAXC, partitions=len(sols), orbits_under_C_rotation=len(orbits),
               by_cost_7E=dict(sorted(Counter(shape(s)[0] for s in sols).items())),
               shapes=[dict(sevenE=k[0], worldA_classes=k[1], chains=" ".join(k[2]), orbits=v) for k, v in sorted(tab.items())])
    print(json.dumps({k: v for k, v in res.items() if k != "shapes"}))
    for s in res["shapes"]:
        if s["sevenE"] > 0: print(json.dumps(s))
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"phi_configs_{MAXC}.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
