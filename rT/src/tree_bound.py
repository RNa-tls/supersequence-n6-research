#!/usr/bin/env python3
"""Round T -- lower bound for every bracket tree on the public 16-trail selection (run-level cuts).
Tables from csrc/cyc_tree.c: PATH[M] (best path through the trails of M, one arc each) and CYC[U] (best closed tour).
A bracket hosted by trail t with member set B adds CYC[B + {t}] (the second cut of t and the |B| + 1 joins).
    J(tree) >= PATH[M] + sum_i CYC[B_i + {t_i}],   M and the B_i a partition of the 16 trails, t_i not in B_i.
Relaxation: the host of each bracket is any trail outside it; several brackets on one host are not forced to use
different links.  Hence   LB = min_M PATH[M] + g[all - M],  g[S] = min over partitions of S of sum c[B],
c[B] = min_{t not in B} CYC[B + {t}].       usage: tree_bound.py CYC.bin OUT.json"""
import sys, json
import numpy as np
T = 16; FULL = (1 << T) - 1
raw = np.fromfile(sys.argv[1], np.int8).astype(np.int32); PATH = raw[:1 << T]; CYC = raw[1 << T:]
INF = 100
c = np.full(1 << T, INF, np.int32)
allS = np.arange(1 << T)
for t in range(T):
    m = (allS >> t & 1) == 0; c[m] = np.minimum(c[m], CYC[allS[m] | (1 << t)])
c[0] = INF
pc = np.array([bin(x).count("1") for x in range(1 << T)])
g = np.full(1 << T, 10 ** 6, np.int64); g[0] = 0; nblocks = np.zeros(1 << T, np.int32)
for S in range(1, 1 << T):
    low = S & -S; rest = S ^ low; sub = rest; best = 10 ** 6
    while True:                                   # block = low + sub
        B = low | sub; v = c[B] + g[S ^ B]
        if v < best: best = v
        if sub == 0: break
        sub = (sub - 1) & rest
    g[S] = best
tot = PATH[1:] + g[FULL ^ allS[1:]]; LB = int(tot.min())
byb = {}
# best value by the number of non-main trails (bracket members)
for k in range(0, T):
    m = pc[FULL ^ allS[1:]] == k
    if m.any(): byb[str(k)] = int(tot[m].min())
res = dict(PATH_all=int(PATH[FULL]), least_closed_tour_cost_by_size={str(k): int(CYC[(pc == k) & (CYC < INF)].min()) for k in range(2, T + 1)},
           least_bracket_cost_by_members={str(k): int(c[(pc == k)].min()) for k in range(1, T)},
           bracket_tree_lower_bound_J=LB, lower_bound_length=46149 + LB, best_by_number_of_bracket_members=byb,
           note="bracket trees with at least one bracket: min over M != all")
res["bracket_tree_lower_bound_J_with_a_bracket"] = int(tot[:-1].min()) if len(tot) > 1 else None
json.dump(res, open(sys.argv[2], "w"), indent=1); print(json.dumps(res))
