#!/usr/bin/env python3
"""Round X -- second implementation of rX/src/frontier_packing.py: one integer program per cell and junction pattern
(HiGHS), deficit tables rebuilt from the second implementation's two-sided tables (rX/src/check_twosided.py).
Chain types: line 1 in {T0, T1, T1e, T2, T2e} (nu = 0, 1, 1, 2, 2; e = parts of value >= 50 allowed) times line 2 in
{N, X} (X = the exceptional chain of line 2).  Variables x[t][r] >= 0 integer.  Constraints: number of chains <=
n - F_loops - s, pieces = R - F_loops - 2 F_pairs + s, sum nu x <= 2, sum over e-types x <= 1, sum over X-types x <= 1.
Only the cells that survive the exceptional knapsack are solved (the packing constraints only add deficit).
usage: frontier_packing_ilp.py T0 T1 T1e T2 T2e L2N L2X ROUNDW_KNAPSACK.json SURVIVORS_OF_EXCEPTIONAL.json FIRST_IMPL.json OUT.json [k K]"""
import sys, json
import numpy as np, highspy
def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F
RMAX = 800
def dtab(F1, F2):
    out = [0] * (RMAX + 1)
    for r in range(1, RMAX + 1):
        d = 0
        while True:
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            if (v1 <= 0 or v1 in F1[r]) and (v2 <= 0 or v2 in F2[r]) and not (v1 >= 54 and v2 >= 258 and v1 != 56): break
            d += 1
        out[r] = d
    return out
names1 = ["T0", "T1", "T1e", "T2", "T2e"]; nu = {"T0": 0, "T1": 1, "T1e": 1, "T2": 2, "T2e": 2}; ex = {"T0": 0, "T1": 0, "T1e": 1, "T2": 0, "T2e": 1}
L1 = {k: feas(p) for k, p in zip(names1, sys.argv[1:6])}; L2 = {"N": feas(sys.argv[6]), "X": feas(sys.argv[7])}
W = json.load(open(sys.argv[8])); surv = {(c["R"], c["F"]) for c in json.load(open(sys.argv[9]))["rows"] if not c["excluded"]}
first = {(c["R"], c["F"]): c for c in json.load(open(sys.argv[10]))["rows"]}; outp = sys.argv[11]
part = (int(sys.argv[12]), int(sys.argv[13])) if len(sys.argv) > 13 else (0, 1)
types = [(a, b) for a in names1 for b in ("N", "X")]
tab = {t: dtab(L1[t[0]], L2[t[1]]) for t in types}
def solve(pieces, chains, base):
    if pieces == 0: return base
    if chains <= 0: return None
    rs = list(range(1, pieces + 1)); nr = len(rs); nt = len(types); nv = nr * nt
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    hi = np.concatenate([np.full(nr, float(chains)) if t == ("T0", "N") else np.full(nr, 2.0) for t in types])
    h.addVars(nv, np.zeros(nv), hi)
    cost = np.concatenate([np.array([float(tab[t][r]) for r in rs]) for t in types])
    idx = np.arange(nv, dtype=np.int32)
    h.changeColsCost(nv, idx, cost); h.changeColsIntegrality(nv, idx, np.array([highspy.HighsVarType.kInteger] * nv))
    h.addRow(-highspy.kHighsInf, float(chains), nv, idx, np.ones(nv))
    h.addRow(float(pieces), float(pieces), nv, idx, np.tile(np.array([float(r) for r in rs]), nt))
    h.addRow(-highspy.kHighsInf, 2.0, nv, idx, np.concatenate([np.full(nr, float(nu[t[0]])) for t in types]))
    h.addRow(-highspy.kHighsInf, 1.0, nv, idx, np.concatenate([np.full(nr, float(ex[t[0]])) for t in types]))
    h.addRow(-highspy.kHighsInf, 1.0, nv, idx, np.concatenate([np.full(nr, 1.0 if t[1] == "X" else 0.0) for t in types]))
    h.run()
    if h.getModelStatus() != highspy.HighsModelStatus.kOptimal: return None
    return int(round(h.getInfo().objective_function_value)) + base
todo = [c for c in W["rows"] if (c["R"], c["F"]) in surv]
rows = []; mism = 0
for c in todo[part[0]::part[1]]:
    R, n, F, D = c["R"], c["chains"], c["F"], c["Delta"]; best = None
    for Fi in range(F + 1):
        Fii = F - Fi
        for s in range(Fii + 1):
            pieces = R - Fi - 2 * Fii + s; chains = n - Fi - s
            if pieces < 0 or chains < 0: continue
            v = solve(pieces, chains, Fi + 8 * Fii - 6 * s)
            if v is not None and (best is None or v < best): best = v
    f = first[(R, F)]; exl = best is None or best > D
    agree = exl == f["excluded"] and best == f["min_deficit"]; mism += not agree
    rows.append(dict(R=R, F=F, Delta=D, min_deficit_ilp=best, excluded_ilp=exl, min_deficit_first=f["min_deficit"], excluded_first=f["excluded"], agree=agree))
res = dict(cells=len(rows), excluded_ilp=sum(r["excluded_ilp"] for r in rows), survivors_ilp=sum(not r["excluded_ilp"] for r in rows), mismatches=mism, rows=rows)
json.dump(res, open(outp, "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
