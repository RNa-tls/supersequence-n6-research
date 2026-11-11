#!/usr/bin/env python3
"""Round T -- independent brute-force check of the closed-tour table CYC[U] of csrc/cyc_tree.c for every U with
2 or 3 trails (min-plus products of the full arc-to-arc join matrices), and of PATH[U] for the same sets.
usage: cyc_spotcheck.py OPTIONS.txt CYC.bin OUT.json"""
import sys, json, itertools
import numpy as np
T = 16
rows = [l.split() for l in open(sys.argv[1])]; rows = [r for r in rows if int(r[3]) <= 1]
tr = np.array([int(r[0]) for r in rows]); cost = np.array([int(r[3]) for r in rows]); head = [r[4] for r in rows]; tail = [r[5] for r in rows]
raw = np.fromfile(sys.argv[2], np.int8).astype(int); PATH = raw[:1 << T]; CYC = raw[1 << T:]
idx = [np.nonzero(tr == t)[0] for t in range(T)]
def joinmat(a, b):
    """J[i, j] = 5 - overlap(tail of arc i of trail a, head of arc j of trail b)"""
    M = np.full((len(idx[a]), len(idx[b])), 5, np.int32)
    for k in range(1, 8):
        d = {}
        for j, o in enumerate(idx[b]): d.setdefault(head[o][:k], []).append(j)
        for i, o in enumerate(idx[a]):
            js = d.get(tail[o][7 - k:])
            if js: M[i, js] = 5 - k
    return M
JM = {(a, b): joinmat(a, b) for a in range(T) for b in range(T) if a != b}
def mp(A, B): return (A[:, :, None] + B[None, :, :]).min(1) if A.shape[0] * A.shape[1] * B.shape[1] < 3e8 else np.stack([(A[i][:, None] + B).min(0) for i in range(A.shape[0])])
bad = 0; n = 0
for a, b in itertools.combinations(range(T), 2):
    U = 1 << a | 1 << b; A = JM[(a, b)] + cost[idx[b]][None, :]; B = JM[(b, a)] + cost[idx[a]][None, :]
    cyc = int((A + B.T).min()); path = int(min((cost[idx[a]][:, None] + A).min(), (cost[idx[b]][:, None] + B).min()))
    n += 1; bad += (cyc != CYC[U]) + (path != PATH[U])
for a, b, c in itertools.combinations(range(T), 3):
    U = 1 << a | 1 << b | 1 << c; best = 10 ** 9; bp = 10 ** 9
    for x, y, z in ((a, b, c), (a, c, b)):                       # the two cyclic orders
        A = JM[(x, y)] + cost[idx[y]][None, :]; B = JM[(y, z)] + cost[idx[z]][None, :]; C = JM[(z, x)] + cost[idx[x]][None, :]
        AB = mp(A, B); best = min(best, int((AB + C.T).min()))
    for x, y, z in itertools.permutations((a, b, c)):
        A = JM[(x, y)] + cost[idx[y]][None, :]; B = JM[(y, z)] + cost[idx[z]][None, :]
        bp = min(bp, int(((cost[idx[x]][:, None] + A)[:, :, None] + B[None, :, :]).min()) if len(idx[x]) * len(idx[y]) * len(idx[z]) < 3e8 else int((mp(cost[idx[x]][:, None] + A, B)).min()))
    n += 1; bad += (best != CYC[U]) + (bp != PATH[U])
res = dict(sets_checked=n, mismatches=int(bad)); json.dump(res, open(sys.argv[3], "w"), indent=1); print(res)
