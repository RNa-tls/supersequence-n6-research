#!/usr/bin/env python3
"""Cyclic-trail structure of an r=0 word: does each trail close (cost-3 join from its last run end back
to its first start)?  Do residual trails glue into a closed cycle?  Accounting:
  L = CONST - ORB + q + sum_{inter-trail joins} (c - 3) + (#trails - 1) * 0   [since eta+E5 = sum (c-3) over c>=4]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
Rinv = lambda s: s[-1:] + s[:-1]
def end_of(ch): return Rinv(S[ch[-1]])
res = []
for k, t in enumerate(trails):
    c = cost(end_of(t[-1]), S[t[0][0]], n)
    res.append(dict(trail=k, chains=len(t), closes_cost=c))
print(json.dumps([(r["trail"], r["chains"], r["closes_cost"]) for r in res]))
# residual trails: try all orders to glue into one cycle
small = [t for t in trails if len(t) not in (6, 104)]
import itertools
for perm in itertools.permutations(range(len(small))):
    seq = [small[i] for i in perm]
    cs = [cost(end_of(seq[i][-1]), S[seq[(i + 1) % len(seq)][0][0]], n) for i in range(len(seq))]
    print("residual order", perm, "rows", [len(x) for x in seq], "cyclic join costs", cs)
# inter-trail joins on the route
J = info["J"]; chains = info["chains"]
inter = [J[ch[-1]] for ch in chains[:-1] if J[ch[-1]] >= 4]
print("inter-trail join costs", inter, "sum(c-3) =", sum(x - 3 for x in inter))
