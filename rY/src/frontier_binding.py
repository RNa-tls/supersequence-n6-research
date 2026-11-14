#!/usr/bin/env python3
"""Round Y, sections E/H -- which constraints of the kappa(46) packing knapsack bind in each of the 40 cells.
For each cell: the least deficit of the full knapsack (Round X), and the least deficit when ONE constraint is relaxed:
  nu+1   : sum of nu (disjoint line-1 parts >= 46) <= 3 instead of 2
  e+1    : two chains may hold line-1 parts >= 50 (instead of one)
  X2+1   : two line-2 exceptional chains (instead of one)
  zone-  : the zone statement (H3) dropped
A relaxation that lowers the least deficit marks a binding (tight) constraint.  Also the "slack vector": for each
relaxation the drop in least deficit.  (Exact recomputation; same tables as rX/src/frontier_packing.py.)
usage: frontier_binding.py T0 T1 T1e T2 T2e L2N L2X ROUNDW_KNAPSACK.json ROUNDX_40.json OUT.json"""
import sys, json
import numpy as np
def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F
RMAX, NMAX, INF = 800, 12, 10 ** 9
def dtab(F1, F2, zone=True):
    dm = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(1, RMAX + 1):
        d = 0
        while True:
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            if (v1 <= 0 or v1 in F1[r]) and (v2 <= 0 or v2 in F2[r]) and (not zone or not (v1 >= 54 and v2 >= 258 and v1 != 56)): break
            d += 1
        dm[r] = d
    return dm
def conv(f, g):
    h = np.full(RMAX + 1, INF, dtype=np.int64)
    for s in range(RMAX + 1):
        if f[s] >= INF: continue
        r = np.arange(0, RMAX + 1 - s); h[s:] = np.minimum(h[s:], f[s] + g[r])
    return h
L1 = {k: feas(p) for k, p in zip(("T0", "T1", "T1e", "T2", "T2e"), sys.argv[1:6])}
L2 = {"N": feas(sys.argv[6]), "X": feas(sys.argv[7])}
W = json.load(open(sys.argv[8])); X40 = json.load(open(sys.argv[9])); outp = sys.argv[10]
nu = {"T0": 0, "T1": 1, "T1e": 1, "T2": 2, "T2e": 2}; ex = {"T0": 0, "T1": 0, "T1e": 1, "T2": 0, "T2e": 1}; ex2 = {"N": 0, "X": 1}
types = [(a, b) for a in L1 for b in L2]
def run(capnu, cape, capx, zone):
    tab = {t: dtab(L1[t[0]], L2[t[1]], zone) for t in types}
    base = {}
    for t in types:
        b = np.full(RMAX + 1, INF, dtype=np.int64); b[1:] = tab[t][1:]; base[t] = b
    states = [(u, e, x) for u in range(capnu + 1) for e in range(cape + 1) for x in range(capx + 1)]
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    P = [{s: (unit.copy() if s == (0, 0, 0) else np.full(RMAX + 1, INF, dtype=np.int64)) for s in states}]
    for m in range(1, NMAX + 1):
        cur = {s: np.full(RMAX + 1, INF, dtype=np.int64) for s in states}
        for s, arr in P[-1].items():
            if arr.min() >= INF: continue
            for t in types:
                s2 = (s[0] + nu[t[0]], s[1] + ex[t[0]], s[2] + ex2[t[1]])
                if s2[0] > capnu or s2[1] > cape or s2[2] > capx: continue
                cur[s2] = np.minimum(cur[s2], conv(arr, base[t]))
        P.append(cur)
    best = [np.minimum.reduce([P[m][s] for s in states]) for m in range(NMAX + 1)]
    res = {}
    for cl in W["rows"]:
        R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]
        lb = INF
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                bm = min((int(best[m][pieces]) for m in range(0, min(NMAX, n - Fi - sh) + 1)), default=INF)
                if bm < INF: lb = min(lb, bm + Fi + 8 * Fii - 6 * sh)
        res[(R, F)] = lb
    return res
surv = [(c["R"], c["F"], c["Delta"], c["min_deficit"]) for c in X40["rows"] if not c["excluded"]]
runs = {"base": run(2, 1, 1, True), "nu+1": run(3, 1, 1, True), "e+1": run(2, 2, 1, True), "X2+1": run(2, 1, 2, True), "zone-": run(2, 1, 1, False)}
rows = []
for R, F, D, md in surv:
    b = runs["base"][(R, F)]; assert b == md, (R, F, b, md)
    rows.append(dict(R=R, F=F, Delta=D, min_deficit=b, margin=b - D, drop={k: b - v[(R, F)] for k, v in runs.items() if k != "base"}))
json.dump(dict(cells=len(rows), rows=rows), open(outp, "w"), indent=1)
for r in rows: print(r["R"], r["F"], "margin", r["margin"], "drops", r["drop"])
