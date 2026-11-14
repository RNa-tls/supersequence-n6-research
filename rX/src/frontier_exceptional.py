#!/usr/bin/env python3
"""Round X -- the 46135 frontier with the two-sided piece-count lemma and the exceptional-chain lemma.

Exceptional-chain lemma (section E of the report): for a line (a, b, c) and a threshold theta, if no two census chains
of value >= theta can be placed class-disjointly (rX/csrc/disjoint.c, all 40320 relabelings, both orientations), then
all forward- or backward-primitive parts of value >= theta of one Hamiltonian path lie in a single chain Q*.  Every
other chain has none, so its two-sided feasible values come from the census truncated below theta (rX/csrc/twosided.c
on the truncated points).  With thresholds for both lines, and cross pairs checked, Q* is one chain for both lines;
otherwise (CROSS=0) a line-1 exceptional chain and a line-2 exceptional chain may differ.

dmin_full(r): two-sided, full census (any chain).  dmin_restr(r): two-sided, truncated census (non-exceptional chain).
Knapsack per cell (junction refinement of rW/src/frontier.py): the remaining chains are m sub-chains, at most one
(CROSS=1) or two (CROSS=0: one per line) of them exceptional.
usage: frontier_exceptional.py TS1_FULL TS2_FULL TS1_RESTR TS2_RESTR ROUNDW_KNAPSACK.json CROSS OUT.json
       (TS*_RESTR may be the full file when no threshold is used for that line)"""
import sys, json, hashlib
import numpy as np

def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F

RMAX, NMAX, INF = 800, 40, 10 ** 9

def dmin_from(F1, F2):
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
    F1, F2, F1r, F2r = (feas(p) for p in sys.argv[1:5]); W = json.load(open(sys.argv[5])); cross = int(sys.argv[6]); outp = sys.argv[7]
    dfull = dmin_from(F1, F2); drest = dmin_from(F1r, F2r)
    d1only = dmin_from(F1, F2r); d2only = dmin_from(F1r, F2)        # exceptional for one line only (CROSS = 0)
    assert all(drest[r] >= dfull[r] for r in range(1, RMAX + 1))
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    def powers(base):
        b = np.full(RMAX + 1, INF, dtype=np.int64); b[1:] = base[1:]; P = [unit]
        for n in range(1, NMAX + 1): P.append(conv(P[-1], b))
        return P
    PR = powers(drest)
    def with_one(P, dex):               # m chains, at most one of them with dex instead of drest
        b = np.full(RMAX + 1, INF, dtype=np.int64); b[1:] = dex[1:]
        Q = [unit]
        for n in range(1, NMAX + 1): Q.append(np.minimum(P[n], conv(P[n - 1], b)))
        return Q
    if cross:
        PX = with_one(PR, dfull)
    else:
        P1 = with_one(PR, d1only)                                   # at most one line-1 exceptional
        PX = [unit]                                                 # plus at most one line-2 exceptional, or one chain both
        b2 = np.full(RMAX + 1, INF, dtype=np.int64); b2[1:] = d2only[1:]
        bf = np.full(RMAX + 1, INF, dtype=np.int64); bf[1:] = dfull[1:]
        for n in range(1, NMAX + 1):
            x = np.minimum(P1[n], conv(P1[n - 1], b2)); x = np.minimum(x, conv(PR[n - 1], bf)); PX.append(x)
    def at(P, m, x):
        if m < 0 or x < 0 or m > NMAX: return INF
        return int(P[m][x])
    rows = []
    for cl in W["rows"]:
        R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]
        lb = INF; arg = None
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                bm = min((at(PX, m, pieces) for m in range(0, n - Fi - sh + 1)), default=INF)
                if bm >= INF: continue
                v = bm + Fi + 8 * Fii - 6 * sh
                if v < lb: lb = v; arg = dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh)
        rows.append(dict(R=R, p=cl["p"], F=F, chains=n, Delta=D, min_deficit_roundW=cl["min_deficit_junctions"],
                         min_deficit=int(lb), excluded=bool(lb > D), margin=int(lb - D), junction_argmin=arg))
    surv = [r for r in rows if not r["excluded"]]
    res = dict(cells=len(rows), excluded=len(rows) - len(surv), survivors=len(surv), cross=cross,
               dmin_full=[int(x) for x in dfull], dmin_restricted=[int(x) for x in drest], rows=rows)
    s = json.dumps(res, indent=1); open(outp, "w").write(s)
    print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "dmin_full", "dmin_restricted")}))
    print("survivors:", [(r["R"], r["F"], r["margin"]) for r in surv])
    print("sha256", hashlib.sha256(s.encode()).hexdigest())

main()
