#!/usr/bin/env python3
"""Round 182 -- exploratory: long ModelTrails made only of charge-1 rows (length n-2, no omissions).
DFS with node limit (bounded; not a census).  Checker B for compatibility/disjointness."""
import random, sys, os
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkB176 import CheckerB

def search(n, L, nodes_max, seed):
    B = CheckerB(n); rng = random.Random(seed)
    start = (tuple(range(n)), L, ())
    best = [start]; path = [start]; cnt = [0]
    def succ(row):
        beta = B.beta(row); rest = [t for t in range(n) if t not in beta]
        out = [(beta + tuple(p), L, ()) for p in permutations(rest)]
        rng.shuffle(out); return out
    def dfs():
        nonlocal best
        cnt[0] += 1
        if cnt[0] > nodes_max: return
        if len(path) > len(best): best = list(path)
        for y in succ(path[-1]):
            if all(B.disjoint(x, y) for x in path):
                path.append(y); dfs(); path.pop()
                if cnt[0] > nodes_max: return
    sys.setrecursionlimit(100000); dfs()
    return best

if __name__ == "__main__":
    for n in range(5, 10):
        for L, name in ((n - 2, "charge1"),):
            b = max((search(n, L, 20000, sd) for sd in range(3)), key=len)
            sp = [r[0][-1] for r in b]
            print(n, name, "longest found", len(b), "specials used", len(set(sp)))
