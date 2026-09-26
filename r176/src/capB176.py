#!/usr/bin/env python3
"""Round 176 -- M_n(g), g <= 2, recomputed with checker B's symbolic rules only
(compatibility via the beta formula, disjointness via the universal frame rule), as an
independent confirmation of capA176.  WLOG first start = identity; same sound pruning.
usage: capB176.py n gmax"""
import sys, os
from itertools import permutations, combinations
sys.path.insert(0, os.path.dirname(__file__))
from checkB176 import CheckerB
n, gmax = int(sys.argv[1]), int(sys.argv[2])
B = CheckerB(n)
def rows_at(p, budget):
    for l in range(max(1, n - 1 - budget), n):
        inner = list(range(1, l - 1))
        for k in range(0, budget - (n - 1 - l) + 1):
            for om in combinations(inner, k):
                yield (p, l, om)
M = {}
for g in range(gmax + 1):
    best = [0]; path = []
    def rec(used):
        last = path[-1]
        beta = B.beta(last)
        for t in permutations([c for c in range(n) if c not in beta]):
            p = beta + t
            for r in rows_at(p, g - used):
                if all(B.disjoint(r, y) for y in path):
                    path.append(r); u = used + B.charge(r)
                    best[0] = max(best[0], len(path))
                    if len(path) + M.get(g - u, 10 ** 9) > best[0]:
                        rec(u)
                    path.pop()
    for r in rows_at(tuple(range(n)), g):
        path.append(r); best[0] = max(best[0], 1); rec(B.charge(r)); path.pop()
    M[g] = best[0]
    print(f"[checker B] n={n} g={g} M={best[0]}", flush=True)
