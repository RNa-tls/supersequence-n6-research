#!/usr/bin/env python3
"""The five cost-3 successor operations of a FULL chain (length n-1), as position permutations
pi_sigma = F^(n-2) o T_sigma.  For each: order, and whether the closed trail of full chains it
generates (word sigma^order) has pairwise distinct classes (shape validity, independent of start)."""
import sys, json, itertools
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def powp(p, k):
    r = tuple(range(len(p)))
    for _ in range(k): r = comp(r, p)
    return r
def order(p):
    e = tuple(range(len(p))); x = p; k = 1
    while x != e: x = comp(x, p); k += 1
    return k
def canon(p):
    n = len(p); return min(p[i:] + p[:i] for i in range(n))
for n in range(5, 10):
    F = tuple(list(range(1, n - 1)) + [0, n - 1])
    out = []
    for sig in itertools.permutations((0, 1, n - 1)):
        T = tuple(list(range(2, n - 1)) + list(sig))
        pi = comp(powp(F, n - 2), T)
        # same class as x?  (R^2 x)
        if sorted(set(canon(comp(tuple(range(n)), pi)) for _ in [0])) == [canon(powp(F, n - 2))]:
            pass
        o = order(pi)
        P = tuple(range(n)); cl = []
        ok = True
        for k in range(min(o, 10000)):
            for i in range(n - 1): cl.append(canon(comp(P, powp(F, i))))
            P = comp(P, pi)
        valid = len(cl) == len(set(cl))
        name = "".join("abc"[[0, 1, n - 1].index(z)] for z in sig)
        out.append((name, o, valid, len(cl)))
    print(n, json.dumps(out))
