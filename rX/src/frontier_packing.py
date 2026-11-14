#!/usr/bin/env python3
"""Round X -- the 46135 frontier with a two-level packing bound on line 1 (to be used only if the packing statement
kappa(48) <= 2 has been established) and the exceptional-chain bound on line 2.

Packing statements (line 1):  no two census chains of value >= 50 can be placed class-disjointly (kappa(50) = 1), and
no THREE census chains of value >= 48 can be placed pairwise class-disjointly (kappa(48) <= 2).  Then, with nu(Q) the
largest number of pairwise row-disjoint parts of value >= 48 of a chain Q (forward- or backward-primitive),
sum over chains of nu(Q) <= 2, and at most one chain has a part of value >= 50 (and no two disjoint ones).
Line-1 chain types and their two-sided tables:
  T0  nu = 0                    census truncated below 48
  T1  nu = 1, no part >= 50     census truncated below 50, case B with u1, u2 >= 48 excluded
  T1e nu = 1, parts >= 50       full census, case B with u1, u2 >= 48 excluded
  T2  nu = 2, no part >= 50     census truncated below 50
  T2e nu = 2, parts >= 50       full census, case B with u1, u2 >= 50 excluded
Line 2 (independent): non-exceptional (truncated below 230) or the one exceptional chain (full, case B both >= 230 out).
Constraints: sum nu <= 2, #(T1e, T2e) <= 1, #(line-2 exceptional) <= 1.  Junction refinement as in frontier.py.
With 13 arguments (L2 given as five tables U0 U1 U1e U2 U2e of the same form for line 2, with the high threshold of
line 2 in the place of 50), line 2 gets the same two-level packing types and caps.
usage: frontier_packing.py T0 T1 T1e T2 T2e L2N L2X ROUNDW_KNAPSACK.json OUT.json
       frontier_packing.py T0 T1 T1e T2 T2e U0 U1 U1e U2 U2e ROUNDW_KNAPSACK.json OUT.json"""
import sys, json, hashlib, itertools
import numpy as np

def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F
RMAX, NMAX, INF = 800, 40, 10 ** 9
def dtab(F1, F2):
    dm = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(1, RMAX + 1):
        d = 0
        while True:
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            if (v1 <= 0 or v1 in F1[r]) and (v2 <= 0 or v2 in F2[r]) and not (v1 >= 54 and v2 >= 258 and v1 != 56): break
            d += 1
        dm[r] = d
    return dm
def conv(f, g):
    h = np.full(RMAX + 1, INF, dtype=np.int64)
    for s in range(RMAX + 1):
        if f[s] >= INF: continue
        r = np.arange(0, RMAX + 1 - s); h[s:] = np.minimum(h[s:], f[s] + g[r])
    return h
def main():
    L1 = {k: feas(p) for k, p in zip(("T0", "T1", "T1e", "T2", "T2e"), sys.argv[1:6])}
    nu = {"T0": 0, "T1": 1, "T1e": 1, "T2": 2, "T2e": 2}; ex = {"T0": 0, "T1": 0, "T1e": 1, "T2": 0, "T2e": 1}
    if len(sys.argv) == 13:
        L2 = {k: feas(p) for k, p in zip(("U0", "U1", "U1e", "U2", "U2e"), sys.argv[6:11])}; W = json.load(open(sys.argv[11])); outp = sys.argv[12]
        nu2 = {"U0": 0, "U1": 1, "U1e": 1, "U2": 2, "U2e": 2}; ex2 = {"U0": 0, "U1": 0, "U1e": 1, "U2": 0, "U2e": 1}
    else:
        L2 = {"N": feas(sys.argv[6]), "X": feas(sys.argv[7])}; W = json.load(open(sys.argv[8])); outp = sys.argv[9]
        nu2 = {"N": 0, "X": 0}; ex2 = {"N": 0, "X": 1}
    types = [(a, b) for a in L1 for b in L2]
    tab = {t: dtab(L1[t[0]], L2[t[1]]) for t in types}
    states = [(u, e, x, y) for u in range(3) for e in range(2) for x in range(2) for y in range(3)]
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    # P[m][state]: least deficit of m chains using exactly the resources `state` (then take min over states)
    P = [{s: (unit.copy() if s == (0, 0, 0, 0) else np.full(RMAX + 1, INF, dtype=np.int64)) for s in states}]
    base = {}
    for t in types:
        b = np.full(RMAX + 1, INF, dtype=np.int64); b[1:] = tab[t][1:]; base[t] = b
    for m in range(1, NMAX + 1):
        cur = {s: np.full(RMAX + 1, INF, dtype=np.int64) for s in states}
        for s, arr in P[-1].items():
            if arr.min() >= INF: continue
            for t in types:
                s2 = (s[0] + nu[t[0]], s[1] + ex[t[0]], s[2] + ex2[t[1]], s[3] + nu2[t[1]])
                if s2[0] > 2 or s2[1] > 1 or s2[2] > 1 or s2[3] > 2: continue
                cur[s2] = np.minimum(cur[s2], conv(arr, base[t]))
        P.append(cur)
    best = [np.minimum.reduce([P[m][s] for s in states]) for m in range(NMAX + 1)]
    def at(m, x):
        if m < 0 or x < 0 or m > NMAX: return INF
        return int(best[m][x])
    rows = []
    for cl in W["rows"]:
        R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]; lb = INF; arg = None
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                bm = min((at(m, pieces) for m in range(0, n - Fi - sh + 1)), default=INF)
                if bm >= INF: continue
                v = bm + Fi + 8 * Fii - 6 * sh
                if v < lb: lb = v; arg = dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh)
        rows.append(dict(R=R, p=cl["p"], F=F, chains=n, Delta=D, min_deficit=int(lb), excluded=bool(lb > D), margin=int(lb - D), junction_argmin=arg))
    surv = [r for r in rows if not r["excluded"]]
    res = dict(cells=len(rows), excluded=len(rows) - len(surv), survivors=len(surv), rows=rows)
    s = json.dumps(res, indent=1); open(outp, "w").write(s)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
    print("survivors:", [(r["R"], r["F"], r["margin"]) for r in surv])
    print("sha256", hashlib.sha256(s.encode()).hexdigest())
main()
