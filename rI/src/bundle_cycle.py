#!/usr/bin/env python3
"""The 16-cycle of arrangements C_0..C_15 of a 46188 bundle: for each step C_k -> C_{k+1}, which two
symbols are swapped; the orbit structure of the bundle (which symbols move)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
A, B = 0, n - 1
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
F = tuple(list(range(1, n - 1)) + [0, n - 1])
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):
    k = p.index(A); w_ = list(p[k:] + p[:k])
    return cyc_canon([x for x in w_ if x not in (A, B)])
def swapped(C1, C2):
    m = len(C1)
    for i in range(m):
        t = list(C1); t[i], t[(i + 1) % m] = t[(i + 1) % m], t[i]
        if cyc_canon(t) == C2: return (C1[i], C1[(i + 1) % m])
    return None
for li, t in enumerate([t for t in trails if len(t) == 104][:3]):
    seq = [Cof(S[ch[0]]) for ch in t]
    order = []
    for C in seq:
        if not order or order[-1] != C: order.append(C)
    if order[0] == order[-1]: order = order[:-1]
    lap = []
    for C in order:
        if C in lap: break
        lap.append(C)
    print(f"trail {li}: lap length {len(lap)}; C_0 = {lap[0]}")
    sw = [swapped(lap[k], lap[(k + 1) % len(lap)]) for k in range(len(lap))]
    print("  swaps along the lap:", " ".join(f"({a}{b})" for a, b in sw))
    print("  lap:", " -> ".join("".join(map(str, C)) for C in lap))
