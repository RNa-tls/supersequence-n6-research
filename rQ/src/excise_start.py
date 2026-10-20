#!/usr/bin/env python3
"""Round Q, section 3 -- single rotated-chain excision with the remainder R placed at the START of the route (case E2).
Route R, SIGMA_1..SIGMA_30 (V1 = T's chain C rotated at a1 sits inside SIGMA as option T(a1), T != SIGMA_1):
    G = e(T(C_start) -> o_1) + sum_{SIGMA edges} e        (R starts at a chain start: no [cut = 2] term; wrap -1, visit +1).
Since F(SIGMA) = [cut(o_1) = 2] + sum e >= 22 for every single-opening assignment, G <= 21 needs F = 22, cut(o_1) = 2 and
e(T(C_start) -> o_1) = 0; so only the optimal orders (F = 22) can give G = 21.  Exact check over those orders: for every
trail T != SIGMA_1 and every mid-chain run a1 of a full chain of T, minimise G exactly over all other options.
usage: excise_start.py FAMILY.json ORDERS_22.txt OUT.json"""
import sys, json
import numpy as np
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, 8):
        if x[k:] == y[:8 - k]: return k
    return 8
fam = json.load(open(sys.argv[1]))
V = [[[tuple(int(c) for c in st[8 * k:8 * k + 8]) for k in range(len(st) // 8)] for st in tr["versions"]] for tr in fam["trails"]]
opts = {t: [(v, k) for v in range(2) for k in range(len(V[t][v]))] for t in range(30)}
ent = lambda t, o: V[t][o[0]][o[1]]
exr = lambda t, o: last(V[t][o[0]][(o[1] - 1) % len(V[t][o[0]])])
cutw = {t: np.array([wt(exr(t, o), ent(t, o)) for o in opts[t]]) for t in range(30)}
# all option-level excesses at once (vectorised): e[a, b] = w(exit(a), entry(b)) - cut(b) - 1
ALLO = [(t, o) for t in range(30) for o in opts[t]]; tofs = {}; c0 = 0
for t in range(30): tofs[t] = c0; c0 += len(opts[t])
X = np.array([exr(t, o) for t, o in ALLO], np.int64); S = np.array([ent(t, o) for t, o in ALLO], np.int64); NO = len(ALLO)
W = np.full((NO, NO), 8, np.int8)
for k in range(7, 0, -1):
    a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
    ob = np.argsort(b, kind="stable"); bs = b[ob]
    lo = np.searchsorted(bs, a); hi = np.searchsorted(bs, a, side="right")
    for i in np.nonzero(hi > lo)[0]: W[i, ob[lo[i]:hi[i]]] = k
CUT = np.concatenate([cutw[t] for t in range(30)])
def emat(a, b):
    return W[tofs[a]:tofs[a] + len(opts[a]), tofs[b]:tofs[b] + len(opts[b])].astype(np.int64) - CUT[tofs[b]:tofs[b] + len(opts[b])][None, :] - 1
def mid_full(t):          # option index -> (rin, rout) for mid-chain runs of full chains
    res = {}
    for v in range(2):
        R = V[t][v]; m = len(R); J = lambda i, j: wt(last(R[i % m]), R[j % m])
        for s in range(m):
            if J(s - 1, s) != 3: continue
            L = 1
            while L < m and J(s + L - 1, s + L) == 2: L += 1
            if L != 7 or J(s + 6, s) != 2: continue
            for a in range(1, 7): res[v * m + (s + a) % m] = (v * m + (s + 7) % m, v * m + s)
    return res
orders = [list(map(int, l.split())) for l in open(sys.argv[2]) if l.strip()]
best = 10 ** 9; checked = 0; found = []
for oi, sig in enumerate(orders):
    # unforced forward (edges only, start vector chosen later) and backward
    n = 30
    bwd = [None] * n; bwd[n - 1] = np.zeros(len(opts[sig[-1]]), np.int64)
    for i in range(n - 2, -1, -1): bwd[i] = (emat(sig[i], sig[i + 1]) + bwd[i + 1][None, :]).min(1)
    for s in range(1, n):
        T = sig[s]; MF = mid_full(T)
        # group mid runs by rout (= chain): one forward DP per chain, start vector e(T(C_start) -> o_1)
        bychain = {}
        for q, (ri, ro) in MF.items(): bychain.setdefault(ro, []).append(q)
        for ro, qs in bychain.items():
            st = W[tofs[T] + ro, tofs[sig[0]]:tofs[sig[0]] + len(opts[sig[0]])].astype(np.int64) - cutw[sig[0]] - 1     # e(R_out -> o_1)
            f = st
            for i in range(1, s + 1): f = (f[:, None] + emat(sig[i - 1], sig[i])).min(0)
            for q in qs:
                g = int(f[q] + bwd[s][q]); checked += 1
                if g < best: best = g
                if g <= 21: found.append(dict(order_index=oi, trail=T, pos=s, a1_option=q, G=g))
json.dump(dict(case="E2: remainder at the route start", orders=len(orders), excisions_checked=checked, min_G=best, G_le_21=found), open(sys.argv[3], "w"), indent=1)
print(json.dumps(dict(orders=len(orders), checked=checked, min_G=best, n_le21=len(found))))
