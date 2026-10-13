#!/usr/bin/env python3
"""Round L (section 13) -- the only modular invariant found: parity of closed trails.

Run starts of a trail evolve by right multiplication: inside a chain p -> p o F (F = 7-cycle on the
positions 0..6: even), across a cost-3 join x -> x o T_sigma.  A closed trail returns to its first run
start, so the product of all its step permutations is the identity (even).  Hence
    #(joins with odd T_sigma) is even for every closed trail.
Parities (computed below): bac odd, skip even, (0,7,1) odd, (1,7,0) even, cba odd.
For an open route there is no such constraint (its end points are free), so this gives no bound on L.
The script prints the parities and checks the invariant on the closed trails of rK/rL searches."""
import itertools, json, sys, os
n = 8
def sign(p):
    s = 0
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            if p[i] > p[j]: s += 1
    return s % 2
F = tuple(list(range(1, n - 1)) + [0, n - 1])
SIG = {"bac": (1, 0, 7), "skip": (0, 1, 7), "s071": (0, 7, 1), "s170": (1, 7, 0), "cba": (7, 1, 0)}
par = {k: sign(tuple(list(range(2, n - 1)) + list(s))) for k, s in SIG.items()}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import closed_letters
names = {v: k for k, v in SIG.items()}
checks = {}
for w in ["S4", "S3 S3 S4 S2 S4 S4 S4", "S3 S4 S3 S4 X4", "S2 S2 S2 S3 X3", "X4", "X2 X4 X4", "X0 X3 X4 X4 X4 X3"]:
    letters, Fp, T = closed_letters(n, w)
    odd = sum(par[names[s]] for l, s in letters)
    checks[w] = dict(chains=len(letters), odd_joins=odd, even=(odd % 2 == 0))
print(json.dumps(dict(F_parity=sign(F), join_parity=par, closed_trails=checks)))
