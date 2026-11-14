#!/usr/bin/env python3
"""Round Y -- what a density lemma would have to say (HYPOTHETICAL constraints, not theorems).
Re-runs the kappa(46) packing knapsack of rX/src/frontier_packing.py on the 40 surviving cells with one extra
hypothetical per-chain cap, to measure how strong a long-chain or tail statement must be to remove cells:
  LONG r0 c   : every chain with r >= r0 pieces has line-2 value 17 r - 38 d <= c   (a long-chain density statement)
  LONG1 r0 c  : the same for line 1 (4 r - 9 d <= c)
usage: frontier_hypothesis.py T0 T1 T1e T2 T2e L2N L2X ROUNDW_KNAPSACK.json ROUNDX_40.json MODE r0 c"""
import sys, json
import numpy as np
def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F
RMAX, NMAX, INF = 800, 12, 10 ** 9
MODE, R0, CAP = sys.argv[10], int(sys.argv[11]), int(sys.argv[12])
def dtab(F1, F2):
    dm = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(1, RMAX + 1):
        d = 0
        while True:
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            ok = (v1 <= 0 or v1 in F1[r]) and (v2 <= 0 or v2 in F2[r]) and not (v1 >= 54 and v2 >= 258 and v1 != 56)
            if ok and r >= R0 and ((MODE == "LONG" and v2 > CAP) or (MODE == "LONG1" and v1 > CAP)): ok = False
            if ok: break
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
W = json.load(open(sys.argv[8])); X40 = json.load(open(sys.argv[9]))
nu = {"T0": 0, "T1": 1, "T1e": 1, "T2": 2, "T2e": 2}; ex = {"T0": 0, "T1": 0, "T1e": 1, "T2": 0, "T2e": 1}; ex2 = {"N": 0, "X": 1}
types = [(a, b) for a in L1 for b in L2]; tab = {t: dtab(L1[t[0]], L2[t[1]]) for t in types}
base = {}
for t in types:
    b = np.full(RMAX + 1, INF, dtype=np.int64); b[1:] = tab[t][1:]; base[t] = b
states = [(u, e, x) for u in range(3) for e in range(2) for x in range(2)]
unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
P = [{s: (unit.copy() if s == (0, 0, 0) else np.full(RMAX + 1, INF, dtype=np.int64)) for s in states}]
for m in range(1, NMAX + 1):
    cur = {s: np.full(RMAX + 1, INF, dtype=np.int64) for s in states}
    for s, arr in P[-1].items():
        if arr.min() >= INF: continue
        for t in types:
            s2 = (s[0] + nu[t[0]], s[1] + ex[t[0]], s[2] + ex2[t[1]])
            if s2[0] > 2 or s2[1] > 1 or s2[2] > 1: continue
            cur[s2] = np.minimum(cur[s2], conv(arr, base[t]))
    P.append(cur)
best = [np.minimum.reduce([P[m][s] for s in states]) for m in range(NMAX + 1)]
surv40 = {(c["R"], c["F"]) for c in X40["rows"] if not c["excluded"]}
out = []
for cl in W["rows"]:
    R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]
    if (R, F) not in surv40: continue
    lb = INF
    for Fi in range(F + 1):
        Fii = F - Fi
        for sh in range(Fii + 1):
            if Fi + sh > n: continue
            pieces = R - Fi - (2 * Fii - sh)
            if pieces < 0: continue
            bm = min((int(best[m][pieces]) for m in range(0, min(NMAX, n - Fi - sh) + 1)), default=INF)
            if bm >= INF: continue
            lb = min(lb, bm + Fi + 8 * Fii - 6 * sh)
    out.append((R, F, lb - D))
surv = [(R, F, mg) for R, F, mg in out if mg <= 0]
print(json.dumps(dict(mode=MODE, r0=R0, cap=CAP, cells=len(out), survivors=len(surv))), "survivors:", surv)
