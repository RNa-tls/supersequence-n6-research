#!/usr/bin/env python3
"""Round Q -- independent rebuild of one rotated-chain excision move on a single-opening order (checks order_excise.c).
Computes optimal options of the order by its own fixed-order DP, builds the route, applies the move
(kind 0: rotated chain C at T's place, R = T - C at the best gap; kind 1: R at T's place, rotated chain at the best gap),
writes the word and verifies it from scratch.
usage: excise_rebuild.py FAMILY.json ORDER(comma) TRAIL CHAIN_START A KIND OUT.txt"""
import sys, json, math
n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
def J(a, b): return wt(last(a), b)
fam = json.load(open(sys.argv[1])); order = [int(x) for x in sys.argv[2].split(",")]
T, s, a, kind = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
V = [[[tuple(int(c) for c in st[8 * k:8 * k + 8]) for k in range(len(st) // 8)] for st in tr["versions"]] for tr in fam["trails"]]
opts = {t: [(v, k) for v in range(2) for k in range(len(V[t][v]))] for t in range(30)}
def ent(t, o): return V[t][o[0]][o[1]]
def ex(t, o): R = V[t][o[0]]; return last(R[(o[1] - 1) % len(R)])
def cut(t, o): return wt(ex(t, o), ent(t, o))
import numpy as np
cur = np.array([cut(order[0], o) == 2 for o in opts[order[0]]], np.int64); back = []
for i in range(1, 30):
    A_, B_ = order[i - 1], order[i]
    M = np.array([[wt(ex(A_, oa), ent(B_, ob)) - cut(B_, ob) - 1 for ob in opts[B_]] for oa in opts[A_]], np.int64)
    tot = cur[:, None] + M; back.append(tot.argmin(0)); cur = tot.min(0)
F = int(cur.min()); q = int(cur.argmin()); sel = [None] * 30; sel[29] = q
for i in range(29, 0, -1): sel[i - 1] = int(back[i - 1][sel[i]])
route = []; blocks = {}
for i, t in enumerate(order):
    v, k = opts[t][sel[i]]; m = len(V[t][v]); blocks[t] = (len(route), v, k)
    route += [V[t][v][(k + u) % m] for u in range(m)]
def cost(rt): return sum(J(rt[i], rt[i + 1]) for i in range(len(rt) - 1))
base = cost(route)
i0, v, k = blocks[T]; Vv = V[T][v]; m = len(Vv); j0 = i0 + m - 1
C = [Vv[(s + u) % m] for u in range(7)]; X = C[a:] + C[:a]; R = [Vv[(s + 7 + u) % m] for u in range(m - 7)]
assert J(C[6], C[0]) == 2 and all(J(C[u], C[u + 1]) == 2 for u in range(6))
here, other = (X, R) if kind == 0 else (R, X)
rest = route[:i0] + here + route[j0 + 1:]
hpos = (i0, i0 + len(here))   # positions of the in-place block in rest
best = None
for g in range(len(rest) + 1):
    if hpos[0] < g < hpos[1]: continue
    cand = rest[:g] + other + rest[g:]
    c = cost(cand)
    if best is None or c < best[0]: best = (c, g)
c, g = best; newroute = rest[:g] + other + rest[g:]
assert len(newroute) == 5040 and len(set(newroute)) == 5040
w = list(newroute[0])
for i, r in enumerate(newroute):
    if i > 0: kk = J(newroute[i - 1], r); w += list(r[8 - kk:])
    w += list(r[:7])
seen = set(tuple(w[i:i + 8]) for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8)
open(sys.argv[7], "w").write("".join(str(x + 1) for x in w) + "\n")
print(json.dumps(dict(F=F, base_L=35288 + base, new_L=35288 + c, delta=c - base, word_len=len(w), all_perms=len(seen) == 40320, gap=g)))
