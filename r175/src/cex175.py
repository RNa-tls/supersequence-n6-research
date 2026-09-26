#!/usr/bin/env python3
"""Round 175 -- the explicit general-n counterexample to marked LL (Theorem B', sharpness).
p = c_1..c_n (identity), A = c_1..c_{n-3}, x = c_{n-2}, y = c_{n-1}, z = c_n:
  row 1: loop  at A x y z
  row 2: loop  at A z y x
  row 3+k (k = 0..n-4): full-length row at phi^k(A y x z) with position n-3-k omitted
n-1 rows, every charge = 1.  Each row is re-verified from the definitions by
llsearch175.verify (independent of the search tables)."""
import json, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from llsearch175 import verify
def walk(n):
    A = tuple(range(n - 3)); x, y, z = n - 3, n - 2, n - 1
    phi = lambda s: s[1:n - 2] + (s[0],) + s[n - 2:]
    w = [(A + (x, y, z), n - 2, None), (A + (z, y, x), n - 2, None)]
    q = A + (y, x, z)
    for k in range(n - 3):
        w.append((q, n - 1, n - 3 - k)); q = phi(q)
    return w
out = {}
for n in range(4, 15):
    w = walk(n); assert len(w) == n - 1; verify(n, w)
    out[n] = ["".join(chr(ord('a') + c) for c in p) + (":loop" if om is None else ":mark%d" % om) for p, l, om in w]
    print(n, "verified,", len(w), "rows =", "n-1;", " ".join(out[n]) if n <= 8 else "")
json.dump(dict(construction=__doc__, walks=out, verified_n=list(out)), open("r175/certs/counterexample_175.json", "w"), indent=1)
