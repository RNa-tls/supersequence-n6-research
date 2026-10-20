#!/usr/bin/env python3
"""Round Q, section 4 -- kappa table of the A single-visit re-routings "one rotated full chain + the rest" (exact kappa).
For a trail-version with full chain C = runs s..s+6 (w2 wrap) and a1 = s + a (a = 1..6):
  form 1: [a1 .. C_end] wrap [C_start .. a1-1] jump [N_start .. Prev_end]   entry a1,      exit s-1,   kappa = w(a1-1 -> N_start) - 3
  form 2: [N_start .. Prev_end] jump [a1 .. C_end] wrap [C_start .. a1-1]   entry s+7,     exit a1-1,  kappa = w(Prev_end -> a1) - 3
(kappa = [first mid] + sum of jump terms E' = w - c(head); the wrap contributes -1).  Writes the m x m int8 table
(99 = absent, -1 diagonal) for dominance.c, keeping the least kappa per (entry, exit).
usage: rotation_reroute_kappa.py FAMILY.json TRAIL VERSION OUT.bin"""
import sys, json
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, 8):
        if x[k:] == y[:8 - k]: return k
    return 8
fam = json.load(open(sys.argv[1])); t = int(sys.argv[2]); v = int(sys.argv[3])
st = fam["trails"][t]["versions"][v]; R = [tuple(int(c) for c in st[8 * k:8 * k + 8]) for k in range(len(st) // 8)]; m = len(R)
J = lambda i, j: wt(last(R[i % m]), R[j % m])
K = bytearray([99]) * (m * m)
for i in range(m): K[i * m + i] = 255   # -1
for k in range(m): K[k * m + (k - 1) % m] = 3 - J(k - 1, k)   # single pieces (k, k-1): kappa = [cut = 2]
n1 = n2 = 0; hist = {}
for s in range(m):
    if J(s - 1, s) != 3: continue
    L = 1
    while L < m and J(s + L - 1, s + L) == 2: L += 1
    if L != 7 or J(s + 6, s) != 2: continue
    for a in range(1, 7):
        a1 = (s + a) % m
        k1 = J(a1 - 1, s + 7) - 3; y, x = a1, (s - 1) % m
        if K[y * m + x] == 99 or k1 < K[y * m + x]: K[y * m + x] = k1
        k2 = J(s - 1, a1) - 3; y2, x2 = (s + 7) % m, (a1 - 1) % m
        if K[y2 * m + x2] == 99 or k2 < K[y2 * m + x2]: K[y2 * m + x2] = k2
        hist[k1] = hist.get(k1, 0) + 1; hist[k2] = hist.get(k2, 0) + 1; n1 += 1
open(sys.argv[4], "wb").write(bytes(K))
print(json.dumps(dict(trail=t, version=v, runs=m, rotations=n1, kappa_hist={str(k): hist[k] for k in sorted(hist)})))
