#!/usr/bin/env python3
"""Minimum join costs between cycle types of a {0,7}-bundle packing (orbit k), over all opening
points and both orientations of each cycle: bundle->phi, phi->bundle, bundle->bundle, phi->phi.
A join from a path ending at chain boundary e (run end before the opening) to a path starting at t."""
import sys, os, json, itertools
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import cost
from orient_search import setup, chains_for
src, orbfile, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
n, F, cycles = setup(src, orbfile, k)
kinds = ["long" if len(cy) > 20 else "phi" for cy in cycles]
ends = defaultdict(list); starts = defaultdict(list)       # per (cycle, orientation): opening -> (start, end)
for b in (0, 1):
    chs = chains_for(n, F, cycles, [b] * len(cycles))
    pos = 0
    for ci, cy in enumerate(cycles):
        L = len(cy)
        for a in range(L):
            st = chs[pos + a][0]; en = chs[pos + (a - 1) % L][1]
            starts[(ci, b)].append(st); ends[(ci, b)].append(en)
        pos += L
best = {}
for (ci, b1), E in ends.items():
    Eset = set(E)
    for (cj, b2), T in starts.items():
        if ci == cj: continue
        key = (kinds[ci], kinds[cj])
        m = min(cost(e, t, n) for e in Eset for t in set(T)) if key not in best or best[key] > 4 else best[key]
        best[key] = min(best.get(key, 99), m)
print(json.dumps({f"{a}->{b}": v for (a, b), v in best.items()}))
