#!/usr/bin/env python3
"""Round Z -- largest line-1 and line-2 value of any contiguous part (window) of any exact weight-3 chain of a word
(the packing statements kappa1(45) <= 2, X2(222), kappa2(210) <= 2 concern parts of value >= 45 / >= 210 / >= 222;
a real word must not contradict them).  Uses the chains of rZ/certs/words/anatomy_*.json is not enough (no row
sizes per position), so it recomputes rows from the word.  usage: word_max_windows.py WORD.txt"""
import sys, json
w = open(sys.argv[1]).read().strip(); n = 8; syms = sorted(set(w))
first = {}
for i in range(len(w) - n + 1):
    s = w[i:i + n]
    if len(set(s)) == n and s not in first: first[s] = i
seq = sorted(first.items(), key=lambda t: t[1]); perm = [p for p, _ in seq]; pos = [q for _, q in seq]
def cls(p): k = p.index(syms[0]); return p[k:] + p[:k]
steps = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
blocks = []; cur = [0]
for i, st in enumerate(steps):
    if st == 1 and cls(perm[i]) == cls(perm[i + 1]): cur.append(i + 1)
    else: blocks.append(cur); cur = [i + 1]
blocks.append(cur)
after = [steps[b[-1]] if b[-1] < len(steps) else None for b in blocks]
rows = []; cur = [0]
for bi in range(len(blocks) - 1):
    if after[bi] == 2: cur.append(bi + 1)
    else: rows.append(cur); cur = [bi + 1]
rows.append(cur)
seamw = [pos[blocks[rows[i + 1][0]][0]] - pos[blocks[rows[i][-1]][-1]] for i in range(len(rows) - 1)]
chains = []; cur = [0]
for i in range(len(rows) - 1):
    if seamw[i] == 3: cur.append(i + 1)
    else: chains.append(cur); cur = [i + 1]
chains.append(cur)
best = {1: -10**9, 2: -10**9}
for ch in chains:
    for line, (a, b) in ((1, (4, 9)), (2, (17, 38))):
        pre = [0]
        for ri in ch: pre.append(pre[-1] + a - b * (7 - len(rows[ri])))
        mn = pre[0]
        for x in pre[1:]:
            best[line] = max(best[line], x - mn); mn = min(mn, x)
print(json.dumps(dict(word=sys.argv[1], chains=len(chains), max_window_line1=best[1], max_window_line2=best[2])))
