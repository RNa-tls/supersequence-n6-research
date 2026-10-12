#!/usr/bin/env python3
"""For each maximum A-packing orbit (3 orbits): minimum join cost between chains of two different
bundles of the packing, over realizations X/X' and both orientations of each bundle."""
import sys, os, json, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from variant_search import setup
from r0verifyA import cost
src, orb = sys.argv[1], sys.argv[2]
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
Rinv = lambda s: s[-1:] + s[:-1]
out = []
for k in range(3):
    n, F, cycles = setup(src, orb, k)
    sw = {0: n - 1, n - 1: 0}
    bundles = [cy for cy in cycles if len(cy) > 1]
    ends = []; starts = []
    for bi, cy in enumerate(bundles):
        E, S = set(), set()
        for real in (0, 1):
            for ori in (0, 1):
                for s, l in cy[real]:
                    if ori: s = tuple(sw.get(v, v) for v in s)
                    x = s
                    for _ in range(l - 1): x = comp(x, F)
                    E.add(Rinv(x)); S.add(s)
        ends.append(E); starts.append(S)
    best = 99
    for i in range(len(bundles)):
        pref = {}
        for j in range(len(bundles)):
            if j == i: continue
            for t in starts[j]:
                for kk in range(1, n): pref.setdefault(t[:kk], True)
        for e in ends[i]:
            for kk in range(n - 1, 3, -1):           # overlaps >= 4  <=> cost <= 4
                if e[n - kk:] in pref: best = min(best, n - kk); break
    out.append(dict(orbit=k, bundles=len(bundles), min_bundle_bundle_join_cost_le4_found=(best if best <= 4 else None)))
    print(json.dumps(out[-1]), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "packing_bb_joins.json"), "w"))
