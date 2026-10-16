#!/usr/bin/env python3
"""Round N -- checker B for the component path-cover table (independent of the MIP code).
Exact dynamic programming over subsets: for a trail set X (|X| = 11) and every c, PC(c) = min total
excess of the internal boundaries of a cover of X by c directed paths, each trail with one option,
excess e(o -> o') = w(exit(o), entry(o')) - cut(o') - 1 computed here from scratch (no option or E
file is reused), all boundary weights exact (no EMAX truncation).  With --cap 3 the excess of every
boundary is replaced by min(e, 3) (the SAT relaxation).
State: (subset S, last trail T, number of paths p) -> vector over T's options of the minimum cost.
usage: pc_dp_check.py FAMILY.json TRAILS(comma) [--cap K]"""
import sys, json, argparse
import numpy as np

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("family"); ap.add_argument("trails"); ap.add_argument("--cap", type=int, default=None)
    a = ap.parse_args()
    fam = json.load(open(a.family)); X = [int(t) for t in a.trails.split(",")]; m = len(X)
    ent = []; ext = []; cut = []
    for t in X:
        E_ = []; X_ = []; C_ = []
        for v, s in enumerate(fam["trails"][t]["versions"]):
            st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            for k in range(len(st)):
                ex = last(st[k - 1]); en = st[k]
                E_.append(en); X_.append(ex); C_.append(wt(ex, en))
        ent.append(E_); ext.append(X_); cut.append(np.array(C_))
    no = [len(e) for e in ent]
    # pairwise excess matrices M[i][j][a, b] = e(option a of X[i] -> option b of X[j])
    M = {}
    for i in range(m):
        for j in range(m):
            if i == j: continue
            W = np.array([[wt(x, y) for y in ent[j]] for x in ext[i]], dtype=np.int64)
            e = W - cut[j][None, :] - 1
            assert e.min() >= 0
            if a.cap is not None: e = np.minimum(e, a.cap)
            M[(i, j)] = e
    INF = 10 ** 9
    full = (1 << m) - 1
    # best[(S, T, p)] = vector over options of T
    best = {}
    for i in range(m):
        best[(1 << i, i, 1)] = np.zeros(no[i], dtype=np.int64)
    for S in range(1, full + 1):
        pc = bin(S).count("1")
        for i in range(m):
            if not (S >> i) & 1: continue
            for p in range(1, pc + 1):
                vec = best.get((S, i, p))
                if vec is None: continue
                mn = int(vec.min())
                for j in range(m):
                    if (S >> j) & 1: continue
                    S2 = S | (1 << j)
                    # extend the current path by the arc i -> j
                    cand = (vec[:, None] + M[(i, j)]).min(0)
                    key = (S2, j, p)
                    if key in best: np.minimum(best[key], cand, out=best[key])
                    else: best[key] = cand.copy()
                    # or start a new path at j (any option, cost 0)
                    key = (S2, j, p + 1)
                    z = np.full(no[j], mn, dtype=np.int64)
                    if key in best: np.minimum(best[key], z, out=best[key])
                    else: best[key] = z
    res = {}
    for p in range(1, m + 1):
        vals = [int(best[(full, i, p)].min()) for i in range(m) if (full, i, p) in best]
        res[p] = min(vals) if vals else None
    print(json.dumps(dict(trails=X, cap=a.cap, PC=res)))

if __name__ == "__main__":
    main()
