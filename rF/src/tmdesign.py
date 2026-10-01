#!/usr/bin/env python3
"""Final round -- tm-orbit design.  Special s = n-1.  tm (R180) maps a T-row start to the start of the
next same-special T-row; tm has order n-2 and an orbit visits n-2 distinct blocks, so every tm-orbit
is a ModelTrail of n-2 charge-2 rows.  Step 1: exact cover of all s-blocks by tm-orbits (Algorithm X).
Step 2: hole structure (2 per row) inside non-s blocks."""
import sys, os, random
from itertools import permutations
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r176", "src"))
from checkA176 import CheckerA

def canon(w): return min(tuple(w[i:] + w[:i]) for i in range(len(w)))

def orbits(n):
    s = n - 1
    tm = lambda p: (p[n - 2],) + p[:n - 4] + (p[n - 3], p[n - 4], p[n - 1])
    seen = set(); orbs = []
    for q in permutations(range(n - 1)):
        p = q + (s,)
        if p in seen: continue
        o = [p]; seen.add(p); x = tm(p)
        while x != p: o.append(x); seen.add(x); x = tm(x)
        orbs.append(o)
    return orbs

def cover(n, orbs, rng, limit=10**6):
    blocks = [frozenset(canon(p[:n - 1]) for p in o) for o in orbs]
    good = [i for i, b in enumerate(blocks) if len(b) == n - 2]
    X = {}
    for i in good:
        for b in blocks[i]: X.setdefault(b, set()).add(i)
    sol = []; cnt = [0]
    def solve():
        cnt[0] += 1
        if cnt[0] > limit: return False
        if not X: return True
        c = min(X, key=lambda c: (len(X[c]), rng.random()))
        cand = list(X[c]); rng.shuffle(cand)
        for i in cand:
            cols = []
            for b in blocks[i]:
                for j in list(X[b]):
                    for b2 in blocks[j]:
                        if b2 != b: X[b2].discard(j)
                cols.append((b, X.pop(b)))
            sol.append(i)
            if solve(): return True
            sol.pop()
            for b, st in reversed(cols):
                X[b] = st
                for j in st:
                    for b2 in blocks[j]:
                        if b2 != b: X[b2].add(j)
        return False
    sys.setrecursionlimit(100000)
    return [orbs[i] for i in sol] if solve() else None

if __name__ == "__main__":
    for n in (6, 7, 8):
        orbs = orbits(n)
        sol = cover(n, orbs, random.Random(n))
        print(f"n={n}: tm-orbits {len(orbs)} (length {set(map(len, orbs))}); exact cover of {len(set(canon(p[:n-1]) for o in orbs for p in o))} s-blocks: "
              f"{'found, ' + str(len(sol)) + ' orbits' if sol else 'NONE'}", flush=True)
