#!/usr/bin/env python3
"""Round 180 -- deterministic periodic special-c_n walks: row pattern (F^k T) repeated,
starting from the identity with an initial offset of f0 full rows.  Simulate until the next
row's cyclic word W would repeat; report rows, J (# T rows), charge 2J, and rows / J.
usage: periodic180.py n [n ...]"""
import sys
def run(n, k, f0, cap=10**6):
    phi = lambda s: s[1:n - 2] + (s[0],) + s[n - 2:]
    tm = lambda s: (s[n - 2],) + s[:n - 4] + (s[n - 3], s[n - 4], s[n - 1])
    W = lambda s: min(s[:n-1][i:] + s[:n-1][:i] for i in range(n - 1))
    s = tuple(range(n)); used = {W(s)}; rows = 1; J = 0; pos = -f0   # pos counts full rows in current run
    types = []
    while rows < cap:
        is_T = (pos == k)
        nxt = tm(s) if is_T else phi(s)
        if W(nxt) in used:
            break                                   # the current (last) row can be taken as F
        if is_T: J += 1; pos = 0
        else: pos += 1
        s = nxt; used.add(W(s)); rows += 1
    return rows, J
for n in map(int, sys.argv[1:]):
    best = None
    for k in range(max(1, n - 6), n - 2):
        for f0 in range(0, n - 2):
            rows, J = run(n, k, f0)
            if best is None or rows > best[0]: best = (rows, J, k, f0)
        rows, J = run(n, k, 0)
        print(f"n={n} k={k} (runs of k full rows): rows {rows}, J {J}, charge {2*J}, rows/J {rows/max(J,1):.2f}  [n-3 = {n-3}; (n-2)! = {__import__('math').factorial(n-2)}]")
    print(f"   best over k, offsets: rows {best[0]} J {best[1]} k {best[2]} f0 {best[3]}")
