#!/usr/bin/env python3
"""Round S -- counting lower bound for bracket trees with c cycles (item a), from two certificates:
  * rR/certs/brackets/cheap_cycles.json : every cover cycle costs >= 1; cost 1 only for 960 cycles with 5 vertices,
    cost 2 only for 7188 cycles with 3 or 4 vertices; all other cycles cost >= 3  (bracket = 1 + cost);
  * rR/certs/brackets/partial_path_bounds.json : F[n_phi][n_A] (path component, with the first-piece term) and
    F0[n_phi][n_A] (mains of a cycle in their order, without it): relaxed minima over all phi sets of each size.
For a bracket tree with path component (p_phi, p_A) and cycles with mains (f_i phi, a_i A):
    G >= F[p_phi][p_A] + sum_i max( type bound_i , 1 + F0[f_i][a_i] ),
    type bound = 2 if the composition occurs among the cost-1 cycles, 3 if among the cost-2 cycles, else 4.
The minimum over all compositions with exactly c cycles is LB(c).  (The phi sets of the parts are NOT required to be
disjoint here, so LB(c) is a relaxation; it is rigorous but weak.)
usage: bracket_count_bound.py CHEAP.json PATHS.json OUT.json"""
import sys, json
from functools import lru_cache
ch = json.load(open(sys.argv[1])); pb = json.load(open(sys.argv[2]))
F = {int(k): v for k, v in pb["F_with_first_piece_term"].items()}; F0 = {int(k): v for k, v in pb["F0_without_first_piece_term"].items()}
FA = pb["FA_A_only_chain_with_term"]; FA0 = pb["FA0_A_only_chain_without_term"]
# compositions of the mains (a, f) available from the catalogs: vertices (nv, nA) minus one anchor (A or phi)
def mains(comp):
    out = set()
    for key in comp:
        nv, na = [int(x) for x in key.split(",")]
        if na >= 1: out.add((na - 1, nv - na))
        if nv - na >= 1: out.add((na, nv - na - 1))
    return out
m1 = mains(ch["cost_1_cycles"]["by_vertices_and_A_vertices"]); m2 = mains(ch["cost_2_cycles"]["by_vertices_and_A_vertices"])
def cyc(a, f):
    tb = 2 if (a, f) in m1 else (3 if (a, f) in m2 else 4)
    pl = 1 + (F0[f][a] if f >= 1 else FA0[a])
    return max(tb, pl)
def path(a, f):
    if f == 0: return FA[a] if a >= 1 else None
    return F[f][a]
INF = 10 ** 9
@lru_cache(None)
def best(c, a, f):       # least total of c cycles using exactly a A mains and f phi mains
    if c == 0: return 0 if (a, f) == (0, 0) else INF
    b = INF
    for a1 in range(a + 1):
        for f1 in range(f + 1):
            if a1 + f1 == 0: continue
            r = best(c - 1, a - a1, f - f1)
            if r < INF: b = min(b, r + cyc(a1, f1))
    return b
LB = {}; arg = {}
for c in range(0, 16):
    b = INF
    for a in range(7):
        for f in range(25):
            p = path(6 - a, 24 - f)
            if p is None: continue
            t = best(c, a, f)
            if t < INF and p + t < b: b = p + t; arg[c] = dict(path=[24 - f, 6 - a], path_bound=p, cycles_bound=t)
    LB[c] = b
out = dict(main_compositions_cost1=sorted(m1), main_compositions_cost2=sorted(m2), LB_by_number_of_cycles={str(c): LB[c] for c in LB}, argmin={str(c): arg[c] for c in arg},
           least_c_with_LB_ge_21=min(c for c in LB if all(LB[d] >= 21 for d in LB if d >= c)))
json.dump(out, open(sys.argv[3], "w"), indent=1)
print(json.dumps(out)[:1500])
