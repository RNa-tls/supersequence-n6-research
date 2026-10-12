#!/usr/bin/env python3
"""Boundary types of the chains of a {0,7}-system r=0 word (n = 8).
For chain c: start t = s_c, last start x (end e = R^-1 x, e[4:8] = x[3:7]).
A cost-4 join e -> t requires t[0:4] = x[3:7] and t[4:8] a permutation of (x7, x0, x1, x2).
Record, for every chain, the pattern of pair symbols {0,7} ('p') vs others ('.') in
   OUT(c) = x[3:7]  (what a successor must start with)   and   IN(c) = t[0:4],
plus the cycle kind (bundle / phi), to see which (OUT, IN) combinations are compatible."""
import sys, os, json
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from r0verifyA import load, analyse, cost
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, chains, trails = info["S"], info["chains"], info["trails"]
pairs = {0, n - 1}
def pat(seq): return "".join("p" if v in pairs else "." for v in seq)
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
F = tuple(list(range(1, n - 1)) + [0, n - 1])
# cycle kind per chain: chains of 104-chain closed cycles or split pieces -> by cycle reconstruction
kind = {}
for t in trails:
    k = "phi" if len(t) == 6 and all(len(ch) == n - 1 for ch in t) else "bundle"
    for ch in t: kind[ch[0]] = k
outp = Counter(); inp = Counter()
for ch in chains:
    s = S[ch[0]]; x = S[ch[-1]]; k = kind[ch[0]]
    outp[(k, pat(x[3:7]), pat((x[7], x[0], x[1], x[2])))] += 1
    inp[(k, pat(s[0:4]), pat(s[4:8]))] += 1
print("OUT patterns (kind, pair-pattern of x3..x6, of {x7,x0,x1,x2}):")
for k, v in sorted(outp.items()): print("  ", k, v)
print("IN patterns (kind, pair-pattern of t0..t3, of t4..t7):")
for k, v in sorted(inp.items()): print("  ", k, v)
