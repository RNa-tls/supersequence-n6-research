#!/usr/bin/env python3
"""Linking profile of an r=0 word: the inter-trail joins (cost >= 4) with the types of the trails they
connect (long = bundle piece, phi = free phi-cycle, other), and the total linking loss sum(c - 4)."""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
J = info["J"]; chains = info["chains"]; trails = info["trails"]
def typ(t): return "phi" if len(t) == 6 and all(len(ch) == n - 1 for ch in t) else ("long" if len(t) > 20 else f"short{len(t)}")
kinds = [typ(t) for t in trails]
joins = []
ti = 0
for k in range(len(chains) - 1):
    c = J[chains[k][-1]]
    if c >= 4:
        joins.append((kinds[ti], kinds[ti + 1], c)); ti += 1
cnt = Counter((a if a < b else b, b if a < b else a, c) for a, b, c in joins)
print(json.dumps(dict(trails=len(trails), kinds=dict(Counter(kinds)), joins=len(joins), loss=sum(c - 4 for _, _, c in joins),
                      cost_hist=dict(Counter(c for _, _, c in joins)))))
for k, v in sorted(cnt.items()): print(k, v)
