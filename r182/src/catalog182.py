#!/usr/bin/env python3
"""Round 182 -- local transition catalog.  For a row x = (p, l, ()) with p = identity and each of the
6 successor starts q = beta(x) + sigma(rest), report the largest l' such that (q, l', ()) is disjoint
from x (visible sets are prefixes, so disjointness is monotone in l').  Checkers A and B."""
import sys, os
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB

def catalog(n, K):
    p = tuple(range(n)); out = {}
    for l in range(1, n):
        x = (p, l, ())
        beta = K.beta(x); rest = [t for t in range(n) if t not in beta]
        row = []
        for sig in permutations(rest):
            q = beta + sig
            best = 0
            for l2 in range(1, n):
                if K.disjoint(x, (q, l2, ())): best = l2
                else: break
            # label: special kept / changed, and which letter becomes special
            row.append((("keep" if q[-1] == p[-1] else "chg"), sig, best))
        out[l] = row
    return out

if __name__ == "__main__":
    for n in range(6, 12):
        cA = catalog(n, CheckerA(n)) if n <= 9 else None
        cB = catalog(n, CheckerB(n))
        if cA is not None: assert cA == cB, n
        print(f"n={n}  (checker A agrees: {cA is not None})")
        for l in range(1, n):
            print(f"  l={l:2d} (charge {n-1-l}):  " + "  ".join(f"{k}{''.join(map(str,s))}:{b}" for k, s, b in cB[l]))
