#!/usr/bin/env python3
"""Round 180 -- growth of the periodic walk (T F^{n-4})^J (special c_n, first row T at the
identity): number of T rows J(n) and rows R(n) before the first repeated cyclic word.
usage: growth180.py nmin nmax"""
import sys
def run(n, k):
    phi = lambda s: s[1:n - 2] + (s[0],) + s[n - 2:]
    tm = lambda s: (s[n - 2],) + s[:n - 4] + (s[n - 3], s[n - 4], s[n - 1])
    def W(s):
        w = s[:n - 1]; i = w.index(0); return w[i:] + w[:i]
    s = tuple(range(n)); used = {W(s)}; rows = 1; J = 0; pos = k
    while True:
        is_T = (pos == k)
        nxt = tm(s) if is_T else phi(s)
        if W(nxt) in used: break
        if is_T: J += 1; pos = 0
        else: pos += 1
        s = nxt; used.add(W(s)); rows += 1
    return rows, J
lo, hi = int(sys.argv[1]), int(sys.argv[2])
for n in range(lo, hi + 1):
    rows, J = run(n, n - 4)
    print(f"n={n:3d} n-1 mod 3 = {(n-1)%3}   J = {J:6d}   rows = {rows:8d}   rows/J = {rows/J:.3f}   J/n^2 = {J/n**2:.3f}   (rows - 2J)/n = {(rows-2*J)/n:.1f}")
