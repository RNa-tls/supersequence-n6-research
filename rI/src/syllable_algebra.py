#!/usr/bin/env python3
"""Symbolic syllable algebra (sec. 7-8).  Conventions: right action s -> s o pi, (p o q)[i] = p[q[i]].
   F   = rotation of positions 0..n-2 (fixes n-1);     phi = rotation of positions 0..n-3
   kap = F^-1 o T_cba = (0 1 ... n-3 n-1 n-2)  (an n-cycle)
   pi(l, bac) = F^l o phi,   pi(l, cba) = F^l o kap
   S_r = F^-2 phi^(r+1),     X_r = F^-2 kap F^-1 phi kap F^-3 phi^(r+1)
Checks these identities against the direct definition for n = 5..14, tabulates cycle types/orders of
a_n = F^-2 phi^-1 (= S_{n-4}), b_n = F^-2 phi^-2 (= S_{n-5}), and of the guessed long-trail period
T_n = S_{n-5} S_{n-4} X_{n-4} S_{n-5} S_{n-4}, and tests validity of the closed trail T_n^m."""
import json
from math import lcm
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def inv(p):
    r = [0] * len(p)
    for i, x in enumerate(p): r[x] = i
    return tuple(r)
def pw(p, k):
    n = len(p); r = tuple(range(n))
    if k < 0: p = inv(p); k = -k
    for _ in range(k): r = comp(r, p)
    return r
def ctype(p):
    seen = set(); c = []
    for i in range(len(p)):
        if i in seen: continue
        j = i; L = 0
        while j not in seen: seen.add(j); j = p[j]; L += 1
        c.append(L)
    return tuple(sorted(c, reverse=True))
def order(p):
    o = 1
    for x in ctype(p): o = lcm(o, x)
    return o
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
rows = []
for n in range(5, 15):
    I = tuple(range(n))
    F = tuple(list(range(1, n - 1)) + [0, n - 1])
    phi = tuple(list(range(1, n - 2)) + [0, n - 2, n - 1])
    T = lambda s: tuple(list(range(2, n - 1)) + list(s))
    bac, cba = (1, 0, n - 1), (n - 1, 1, 0)
    kap = comp(pw(F, -1), T(cba))
    assert kap == tuple(list(range(1, n - 2)) + [n - 1, 0, n - 2])
    assert comp(pw(F, -1), T(bac)) == phi
    step = lambda l, s: comp(pw(F, l - 1), T(s))
    for l in range(1, n):
        assert step(l, bac) == comp(pw(F, l), phi) and step(l, cba) == comp(pw(F, l), kap)
    S = lambda r: comp(pw(F, -2), pw(phi, r + 1))
    X = lambda r: comp(comp(comp(comp(comp(pw(F, -2), kap), pw(F, -1)), phi), kap), comp(pw(F, -3), pw(phi, r + 1)))
    # direct letter lists
    Sl = lambda r: [(n - 3, bac)] + [(n - 1, bac)] * r
    Xl = lambda r: [(n - 3, cba), (n - 2, bac), (n - 1, cba), (n - 4, bac)] + [(n - 1, bac)] * r
    def prod(letters):
        P = I
        for l, s in letters: P = comp(P, step(l, s))
        return P
    for r in range(0, n - 2):
        assert prod(Sl(r)) == S(r)
        if n >= 5: assert prod(Xl(r)) == X(r)
    a, b = S(n - 4), S(n - 5)
    word = Sl(n - 5) + Sl(n - 4) + Xl(n - 4) + Sl(n - 5) + Sl(n - 4)
    Pi = prod(word); m = order(Pi)
    # validity of the closed trail word^m
    P = I; seen = set(); ok = True; chains = 0
    for _ in range(m):
        for l, s in word:
            for j in range(l):
                c = canon(comp(P, pw(F, j)))
                if c in seen: ok = False
                seen.add(c)
            chains += 1; P = comp(P, step(l, s))
    rows.append(dict(n=n, a_ctype=ctype(a), a_order=order(a), b_ctype=ctype(b), b_order=order(b),
                     T_len=len(word), T_ctype=ctype(Pi), T_order=m, closed_valid=ok and P == I,
                     chains=chains, classes=len(seen), rate=(chains + 1) / len(seen), phi_rate=1 / (n - 2)))
for r in rows: print(json.dumps(r))
json.dump(rows, open(__file__.replace("src/syllable_algebra.py", "certs/syllable_algebra.json"), "w"))
