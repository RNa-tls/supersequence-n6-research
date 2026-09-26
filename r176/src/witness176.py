#!/usr/bin/env python3
"""Round 176 -- witness tables for the transitions between a full row and a charge-2 row.

Block-level data only: for two starts p, q it lists every hexagon common to the FULL
F-blocks of p and q together with its position in each (position i = state F^i,
special symbol right after w_i, w_0 := w_{n-1}).  Which row types can use the
transition then follows from the hidden-position sets:
   full {} ; T (length n-3) {n-3, n-2} ; L_i (loop, omission i<=n-4) {i, n-2} ;
   M_ij (full length, omissions i<j<=n-3) {i, j}.
Symbolic labels: positions 0, 1, n-4, n-3, n-2 are printed symbolically; the table must
be identical for every n given (checked).
  (1) full r = u B y z  ->  q = B + perm(u, y, z)            [same as R175, re-derived]
  (2) T at p = c_1..c_n  ->  q = D + perm(v, w, z),  D = c_{n-1} c_1..c_{n-4},
      v = c_{n-3}, w = c_{n-2}, z = c_n                      [beta of a length-(n-3) row]
usage: witness176.py n [n ...]"""
import sys
from itertools import permutations


def table(n):
    def F(s): return s[1:n - 1] + (s[0], s[n - 1])
    def Rinv(s): return (s[n - 1],) + s[:n - 1]
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
    def pos(p):
        st = [p]
        for _ in range(n - 2): st.append(F(st[-1]))
        return {hexrep(s): i for i, s in enumerate(st)}, min(st)
    def sym(i): return {0: '0', 1: '1', n - 4: 'n-4', n - 3: 'n-3', n - 2: 'n-2'}.get(i, 'mid%d' % i)
    p = tuple(range(n)); c = {i + 1: p[i] for i in range(n)}
    out = {}
    # (1) full -> q
    P, bp = pos(p); B = p[1:n - 2]; nm = {c[1]: 'u', c[n - 1]: 'y', c[n]: 'z'}
    for t in permutations([c[1], c[n - 1], c[n]]):
        q = B + t; Q, bq = pos(q)
        out["full->B+" + "".join(nm[s] for s in t)] = "same block" if bq == bp else \
            sorted((sym(P[h]), sym(Q[h])) for h in set(P) & set(Q))
    # (2) T -> q
    st = [p]
    for _ in range(n - 2): st.append(F(st[-1]))
    D = Rinv(st[n - 4])[3:]
    assert D == (c[n - 1],) + p[:n - 4], D
    nm = {c[n - 3]: 'v', c[n - 2]: 'w', c[n]: 'z'}
    for t in permutations([c[n - 3], c[n - 2], c[n]]):
        q = D + t; Q, bq = pos(q)
        out["T->D+" + "".join(nm[s] for s in t)] = "same block" if bq == bp else \
            sorted((sym(P[h]), sym(Q[h])) for h in set(P) & set(Q))
    return out


if __name__ == "__main__":
    ref = None
    for n in map(int, sys.argv[1:] or [6, 7, 8, 9, 10]):
        t = table(n)
        if ref is None: ref = t
        print(n, "identical to first n:", t == ref)
    for k, v in ref.items():
        print("  ", k, v)
