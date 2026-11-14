#!/usr/bin/env python3
"""Round Z -- {z,t}-block statistics of a two-world word (exact).
For the two moving symbols z, t of a word whose rows use only these two worlds, every class lies in exactly one
{z,t}-block B({z,t}, D) (D = the cyclic order of the other six symbols); the block has 6 z-2-cycles (rows) and
6 t-2-cycles (columns).  Every class needs its row or its column used, so a = 6 or b = 6, and W_B = 7 (a + b - 6).
Prints the histogram of (a, b) and checks W = sum_B W_B.  usage: block_stats.py WORD.txt"""
import sys, collections
sys.argv = [sys.argv[0], sys.argv[1]]
src = open(sys.argv[1]).read().strip()
syms = sorted(set(src)); n = 8
first = {}
for i in range(len(src) - n + 1):
    s = src[i:i + n]
    if len(set(s)) == n and s not in first: first[s] = i
seq = sorted(first.items(), key=lambda t: t[1])
perm = [p for p, _ in seq]; pos = [q for _, q in seq]
def cls(p): k = p.index(syms[0]); return p[k:] + p[:k]
def cyc(s): k = s.index(min(s)); return s[k:] + s[:k]
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
used = collections.Counter()
for r in rows:
    full = [b for b in r if len(blocks[b]) == 8] or r
    e = perm[blocks[full[0]][0]]; z = e[-1]; used[(z, cyc(e[:-1]))] += 1
worlds = sorted({G[0] for G in used})
print("worlds:", worlds, "used 2-cycles:", len(used))
assert len(worlds) == 2
z, t = worlds
hist = collections.Counter(); WB = 0
blk = collections.defaultdict(lambda: [set(), set()])
for (w, C) in used:
    other = t if w == z else z
    D = cyc(C.replace(other, ''))
    k = C.index(other)
    blk[D][0 if w == z else 1].add(C)
for D, (A, B) in blk.items():
    hist[(len(A), len(B))] += 1
allD = 120
pure_missing = allD - len(blk)
for (a, b), c in hist.items(): WB += c * 7 * (a + b - 6)
print("blocks seen:", len(blk), "of", allD, " histogram (a = used", z, "rows, b = used", t, "columns):", dict(sorted(hist.items())))
print("sum_B 7(a+b-6) =", WB, " (should equal W = 7U - 5040 =", 7 * len(used) - 5040, ")")
