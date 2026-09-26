#!/usr/bin/env python3
"""Round 182 -- bounded DFS: longest ModelTrail whose rows all have charge in a set C (no omissions).
Node-limited (not a census).  Checker B; best trail re-checked with checker A."""
import random, sys, os
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB

def search(n, C, nodes_max, seed):
    B = CheckerB(n); rng = random.Random(seed)
    lens = [n - 1 - c for c in C]
    best = []; path = []; cnt = [0]
    def dfs():
        nonlocal best
        cnt[0] += 1
        if cnt[0] > nodes_max: return
        if len(path) > len(best): best = list(path)
        if path:
            beta = B.beta(path[-1]); rest = [t for t in range(n) if t not in beta]
            opts = [(beta + tuple(p), l, ()) for p in permutations(rest) for l in lens]
        else:
            opts = [(tuple(range(n)), l, ()) for l in lens]
        rng.shuffle(opts)
        for y in opts:
            if all(B.disjoint(x, y) for x in path):
                path.append(y); dfs(); path.pop()
                if cnt[0] > nodes_max: return
    sys.setrecursionlimit(1000000); dfs()
    return best

if __name__ == "__main__":
    out = []
    for n in range(6, 11):
        for C in ((2,), (1, 2), (2, 3)):
            b = max((search(n, C, 200000, sd) for sd in range(2)), key=len)
            okA = CheckerA(n).trail(b)[0] if n <= 9 else None
            line = f"n={n} charges {C}: longest found {len(b)} (checker A {okA}), specials used {len({r[0][-1] for r in b})}"
            print(line, flush=True); out.append(line)
    open(os.path.join(os.path.dirname(__file__), "..", "certs", "lowcharge182.txt"), "w").write("\n".join(out) + "\n")
