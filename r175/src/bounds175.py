#!/usr/bin/env python3
"""Round 175 -- compare Delta(n) lower bounds (all as Delta = L - CONST(n)).
Liu: hunterBound(k) + gamma(k) - CONST, transcribed from
Haruhiyuki/superpermutations-preimage-chain-lower-bounds@23fdbc5 PreimageChain/Numerics.lean.
T3 variants (R174 Theorem 3, CONDITIONAL on Bridge(n)):
  alpha = n-1       (segment bound, proved)
  alpha = (n-1)/2   (R175 Theorem C, proved in the model; marked and unmarked)
  alpha = (n-3)/2   (C1, conjecture)"""
from math import factorial as f
from fractions import Fraction as Fr
def cdiv(a, b): return -(-a // b)
def liu(k):
    d = (k-1)*(k-2)-1; e = (k-1)*(k-3)
    hb = cdiv(f(k-2)-(k-2), d)
    kap = d*hb - (f(k-2)-(k-2))
    C = lambda s: (k-1)*(k-2)**2 + (d+1)*(kap + s*d)
    z0 = max(0, cdiv((k-2)*f(k-1) - C(0), (k-2)*d)) if (k-2)*f(k-1) >= C(0) else 0
    ready = lambda s: z0 - 1 <= k*s + (kap + s*(k-2))//e   # LayerReady (monotone in s)
    lo, hi = 0, max(1, z0)
    while lo < hi:                      # least s with ready(s) (= Nat.find)
        mid = (lo + hi)//2
        if ready(mid): hi = mid
        else: lo = mid + 1
    return hb + lo
def t3(n, a):
    den = max(Fr(n-2), a*(n-1)-1)
    v = Fr((n-2)*(f(n-3)-1)) / den
    return -(-v.numerator // v.denominator)
print(f"{'n':>3} {'Liu':>14} {'T3 a=n-1':>14} {'T3 a=(n-1)/2':>14} {'T3 C1':>14} {'ratio LL/Liu':>12}")
for n in list(range(5, 21)) + [25, 30, 40]:
    L = liu(n); a = t3(n, Fr(n-1)); b = t3(n, Fr(n-1, 2)); c = t3(n, Fr(n-3, 2))
    print(f"{n:>3} {L:>14} {a:>14} {b:>14} {c:>14} {float(Fr(b, L)):>12.5f}"[:200])
