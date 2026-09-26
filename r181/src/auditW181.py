#!/usr/bin/env python3
"""Round 181 -- independent audit of Theorem W (Round 180), fresh implementation.

(1) Build the walk directly from its definition (phi / T-exit on starts) -- simulation.
(2) Build the same word multiset PURELY from the symbolic description in the proof:
      T-row word W_{j+1} = W_j with positions (c_j, c_j + 1) swapped, c_j = n-5-3j (mod N);
      period j rows = frame (W_j minus x_j, x_j), x_j = W_0[c_j+1], at the n-3 gaps other than
      the gap x_j occupies in W_{j+1}; final row W_K.
(3) Compare the two (as sets of cyclic words), check distinctness, row count (n-3)K+1,
    charge 2K, common special, and re-check the simulated walk with checker A (n <= 16).
(4) Corrected consequence: LS(n;A,c) forces A >= 1 + (n-3-2c) K.  Print the forced A for
    c = 1, 2, (n-3)/2 - 1/2 to show the bound is quadratic only for c = O(1)-like c.
usage: auditW181.py nmin nmax"""
import os, sys
from fractions import Fraction as Fr
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
def canon(w):
    i = w.index(0); return tuple(w[i:] + w[:i])
def simulate(n, K):
    phi = lambda s: s[1:n - 2] + (s[0],) + s[n - 2:]
    tm = lambda s: (s[n - 2],) + s[:n - 4] + (s[n - 3], s[n - 4], s[n - 1])
    s = tuple(range(n)); rows = []
    for j in range(K):
        rows.append((s, n - 3, ())); s = tm(s)
        for _ in range(n - 4): rows.append((s, n - 1, ())); s = phi(s)
    rows.append((s, n - 1, ()))
    return rows
def symbolic(n, K):
    N = n - 1; W = list(range(N)); words = []
    for j in range(K):
        c = (n - 5 - 3 * j) % N; x = W[(c + 1) % N]
        Wn = list(W); Wn[c], Wn[(c + 1) % N] = Wn[(c + 1) % N], Wn[c]
        E = [t for t in W if t != x]
        # gap of x in Wn (as element of E following x)
        i = Wn.index(x); forbidden = Wn[(i + 1) % N]
        for g in range(len(E)):
            if E[g] == forbidden: continue
            words.append(canon(E[:g] + [x] + E[g:]))
        W = Wn
    words.append(canon(W))
    return words
lo, hi = int(sys.argv[1]), int(sys.argv[2])
for n in range(lo, hi + 1):
    K = (n - 3) // 3
    rows = simulate(n, K)
    sim = [canon(list(r[0][:n - 1])) for r in rows]
    sym = symbolic(n, K)
    ok = (sorted(sim) == sorted(sym) and len(set(sim)) == len(sim) == (n - 3) * K + 1
          and all(r[0][-1] == n - 1 for r in rows) and sum((n - 1 - r[1]) for r in rows) == 2 * K)
    A = CheckerA(n).trail(rows, 2 * K)[0] if n <= 16 else None
    forced = {c: 1 + (n - 3 - 2 * c) * K for c in (Fr(1), Fr(2), Fr(n - 3, 2) - Fr(1, 2))}
    print(f"n={n:2d} K={K} rows={len(rows)} symbolic==simulated&distinct&counts: {ok}  checkerA: {A}  "
          f"forced A for c=1: {forced[Fr(1)]}, c=2: {forced[Fr(2)]}, c=(n-4)/2: {forced[Fr(n-3,2)-Fr(1,2)]}")
