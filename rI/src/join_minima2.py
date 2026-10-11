#!/usr/bin/env python3
"""Join-cost minima including the X' realization of bundles (variant_search.setup): for each pair of
cycle kinds and realization/orientation, the minimum cost from a path end (any opening) to a path
start (any opening) of a different cycle."""
import sys, os, json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import cost
from variant_search import setup, chains_for
src, orbfile, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
n, F, cycles = setup(src, orbfile, k)
nc = len(cycles)
ends = {}; starts = {}
for real in (0, 1):
    for ori in (0, 1):
        state = [((real if len(cy) > 1 else 0), ori) for cy in cycles]
        chs = chains_for(n, F, cycles, state); pos = 0
        for ci, cy in enumerate(cycles):
            L = len(cy[state[ci][0]])
            tag = ("long" if len(cy) > 1 else "phi") + ("X'" if (len(cy) > 1 and real) else "") + ("/7" if ori else "/0")
            ends.setdefault((ci, tag), set()).update(chs[pos + (a - 1) % L][1] for a in range(L))
            starts.setdefault((ci, tag), set()).update(chs[pos + a][0] for a in range(L))
            pos += L
best = defaultdict(lambda: 99)
for (ci, t1), E in ends.items():
    for (cj, t2), T in starts.items():
        if ci == cj: continue
        key = (t1.split("/")[0], t2.split("/")[0])
        if best[key] <= 4: continue
        best[key] = min(best[key], min(cost(e, t, n) for e in E for t in T))
print(json.dumps({f"{a}->{b}": v for (a, b), v in sorted(best.items())}))
