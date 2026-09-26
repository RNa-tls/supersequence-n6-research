#!/usr/bin/env python3
"""Round 174 -- falsification test for Lemma LL: in the external row model, the longest
trail whose rows ALL have charge <= 1 (length n-1 or n-2), with no bound on total
charge.  LL claims n-2.  Exhaustive DFS from the identity start (relabelling WLOG);
also reports the longest such trail containing >= 2 charge-1 rows."""
import sys
from itertools import permutations
sys.setrecursionlimit(10000)
n = int(sys.argv[1])
alph = "".join(str(i + 1) for i in range(n))
def F(s): return s[1:n - 1] + s[0] + s[n - 1]
def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
info = {}
for p in ("".join(t) for t in permutations(alph)):
    st = [p]
    for _ in range(n - 2): st.append(F(st[-1]))
    rows = []
    for l in (n - 1, n - 2):
        last = st[l - 1]; x = last[-1] + last[:-1]
        rows.append((l, x[3:], frozenset(hexrep(s) for s in st[:l])))
    info[p] = (min(st), rows)
best = [0, 0]; nodes = [0]
def rec(beta, depth, loops, blocks, hexes):
    nodes[0] += 1
    for q in ("".join(t) for t in permutations([c for c in alph if c not in beta])):
        p = beta + q; b, rows = info[p]
        if b in blocks: continue
        for l, nb, hs in rows:
            if hs & hexes: continue
            d = depth + 1; lp = loops + (l == n - 2)
            best[0] = max(best[0], d)
            if lp >= 2: best[1] = max(best[1], d)
            blocks.add(b); rec(nb, d, lp, blocks, hexes | hs); blocks.discard(b)
b0, rows0 = info[alph]
for l, nb, hs in rows0:
    best[0] = max(best[0], 1)
    rec(nb, 1, int(l == n - 2), {b0}, set(hs))
print(f"n={n}: longest all-charge<=1 trail = {best[0]} rows (LL claims {n-2}); with >=2 loop rows: {best[1]}; nodes {nodes[0]}")
