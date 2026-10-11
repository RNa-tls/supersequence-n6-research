#!/usr/bin/env python3
"""Independent re-solve of the bundle packing (bundle_pack.py) with HiGHS MIP (scipy.optimize.milp),
plus the LP relaxation value and an explicit dual (arrangement weights) certificate:
max sum s_B x_B  s.t.  sum_{B ni C} x_B <= 1,  x >= 0.  Dual: min sum_C y_C, y >= 0,
sum_{C in B} y_C >= s_B for every candidate B.  A feasible dual y gives saving <= sum y."""
import sys, os, json, itertools
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds, linprog
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_pack import bundle_Cset, cyc_canon
n = int(sys.argv[1]); bfile = sys.argv[2]
shapes = [s for s in json.load(open(bfile)) if s["saving"] > 0]
others = list(range(1, n - 1))
ground = sorted({cyc_canon(list(p)) for p in itertools.permutations(others)})
gid = {C: i for i, C in enumerate(ground)}
cands = {}
for si, sh in enumerate(shapes):
    Cset, _ = bundle_Cset(n, sh["word"], tuple(sh["pair"]))
    src = [x for x in range(n) if x not in sh["pair"]]
    for img in itertools.permutations(others):
        mp = dict(zip(src, img))
        key = frozenset(gid[cyc_canon([mp[x] for x in C])] for C in Cset)
        cands[key] = max(cands.get(key, 0), sh["saving"])
keys = list(cands); K = len(keys); G = len(ground)
A = np.zeros((G, K))
for j, k in enumerate(keys):
    for c in k: A[c, j] = 1
s = np.array([cands[k] for k in keys], dtype=float)
res = milp(-s, constraints=[LinearConstraint(A, -np.inf, 1)], integrality=np.ones(K), bounds=Bounds(0, 1))
lp = linprog(-s, A_ub=A, b_ub=np.ones(G), bounds=[(0, None)] * K, method="highs")
dual = linprog(np.ones(G), A_ub=-A.T, b_ub=-s, bounds=[(0, None)] * G, method="highs")
out = dict(candidates=K, ground=G, mip_opt=-res.fun, mip_status=res.message, lp_opt=-lp.fun, dual_opt=dual.fun,
           dual_weights_distinct=sorted(set(np.round(dual.x, 6).tolist())))
print(json.dumps(out))
