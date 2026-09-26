#!/usr/bin/env python3
"""Round 182 -- exhaustive local windows: which charge sequences (c_1..c_w) (no omissions) occur
as w consecutive rows of a ModelTrail?  Start fixed at the identity (all starts are equivalent
under symbol relabelling).  Exhaustive over successors and lengths; checker B, cross-checked
with checker A for n <= 8."""
import sys, os
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB

def windows(n, w, K):
    p0 = tuple(range(n)); feas = set()
    def ext(path):
        if len(path) == w:
            feas.add(tuple(n - 1 - r[1] for r in path)); return
        if not path:
            for l in range(1, n): ext([(p0, l, ())])
            return
        beta = K.beta(path[-1]); rest = [t for t in range(n) if t not in beta]
        for sig in permutations(rest):
            q = beta + sig
            for l in range(1, n):
                y = (q, l, ())
                if all(K.disjoint(x, y) for x in path): ext(path + [y])
                else: break    # visible sets are prefixes: larger l also conflicts with the same row
    ext([]); return feas

if __name__ == "__main__":
    for n in range(6, 10):
        for w in (2, 3):
            fB = windows(n, w, CheckerB(n))
            if n <= 8: assert fB == windows(n, w, CheckerA(n)), (n, w)
            ones = [c for c in fB if all(x == 1 for x in c)]
            small = sorted(c for c in fB if all(1 <= x <= 1 for x in c))
            nonfull_all = [c for c in fB if all(x >= 1 for x in c)]
            print(f"n={n} w={w}: feasible patterns {len(fB)}; all-charge-1 {ones}; "
                  f"min max-charge among all-nonfull windows = {min(max(c) for c in nonfull_all) if nonfull_all else None}")
