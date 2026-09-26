#!/usr/bin/env python3
"""Round 180 -- ceiling for every per-trail capacity argument.

A per-trail capacity argument derives a lower bound on D from:  a Bridge(n) instance with
k = ORB + m - r + a rows on tau = eta + 1 + b trails with charges c_i, sum c_i <= (n-1)m - r,
must satisfy k <= sum_i M_n(c_i).  Any explicit lower bound M_n(g0) >= R0 makes that
inequality satisfiable at the parameters  r = a = b = 0, tau trails each of charge g0,
m = ceil(g0 * tau / (n-1)),  tau * R0 >= ORB + m.  Hence no such argument can prove more than
    D_ceiling = min over tau of { m + tau - 1 }.
Proved input  : M_n(2K) >= (n-3)K + 1, K = floor((n-3)/3)        (Theorem W, family180.py)
Empirical input: M_n(2J) >= (n-3)J  for the full periodic walk (growth180.py, n <= 40)
Compared with the R178 bound ceil(2(n-2)((n-3)!-1)/(n^2-4n+1)).
usage: ceiling180.py"""
from math import factorial as f
import re
def ceiling(n, g0, R0):
    ORB = f(n - 2)
    from fractions import Fraction as Fr
    eff = Fr(R0) - Fr(g0, n - 1)
    t0 = max(1, int(Fr(ORB) / eff) - 3)
    best = None
    for t in range(t0, t0 + 400):
        m = -(-g0 * t // (n - 1))
        if t * R0 >= ORB + m:
            D = m + t - 1
            best = D if best is None or D < best else best
    return best
def r178(n):
    num, den = 2 * (n - 2) * (f(n - 3) - 1), n * n - 4 * n + 1
    return -(-num // den)
emp = {}
for line in open("r180/certs/growth180.txt"):
    mm = re.match(r"n=\s*(\d+).*J =\s*(\d+)\s+rows =\s*(\d+)", line)
    if mm: emp[int(mm.group(1))] = (int(mm.group(2)), int(mm.group(3)))
print(f"{'n':>3} {'R178 bound':>14} {'ceiling(proved K)':>18} {'ratio':>7} {'ceiling(full walk)':>19} {'ratio':>7}")
for n in list(range(8, 41)):
    K = (n - 3) // 3
    b = r178(n)
    cp = ceiling(n, 2 * K, (n - 3) * K + 1) if K >= 1 else None
    ce = ceiling(n, 2 * emp[n][0], emp[n][1]) if n in emp else None
    if n <= 14 or n % 3 == 2 or n in (39, 40):
        print(f"{n:>3} {b:>14.6g} {cp:>18.6g} {cp/b:>7.3f} {ce if ce is None else f'{ce:.6g}':>19} {'' if ce is None else f'{ce/b:.3f}':>7}")
