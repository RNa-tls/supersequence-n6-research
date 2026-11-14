#!/usr/bin/env python3
"""Round X -- the 46135 frontier with the two-sided piece-count lemma (rX/csrc/twosided.c).

dmin2(r) = least d >= 0 such that the value v1 = 4 r - 9 d is <= 0 or feasible for line 1 (two-sided lemma), the value
v2 = 17 r - 38 d is <= 0 or feasible for line 2, and the zone statement (H3) holds (not: v1 >= 54, v2 >= 258, v1 != 56).
The junction-refined knapsack of rW/src/frontier.py is then rerun with dmin2 on all 170 cells R + p = 769.
usage: frontier_twosided.py TS1.txt TS2.txt ROUNDW_KNAPSACK.json OUT.json"""
import sys, json, hashlib
import numpy as np

def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); r = int(t[0]); F[r] = {int(x.split(":")[0]) for x in t[1:]}
    return F

def main():
    F1, F2 = feas(sys.argv[1]), feas(sys.argv[2]); W = json.load(open(sys.argv[3])); outp = sys.argv[4]
    RMAX, NMAX, INF = 800, 40, 10 ** 9
    dold = W["dmin_first"]
    dmin = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(1, RMAX + 1):
        d = 0
        while True:
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            ok = (v1 <= 0 or v1 in F1[r]) and (v2 <= 0 or v2 in F2[r]) and not (v1 >= 54 and v2 >= 258 and v1 != 56)
            if ok: break
            d += 1
        dmin[r] = d
    old = np.load(sys.argv[5]) if len(sys.argv) > 5 else None
    if old is not None:
        bad = [r for r in range(1, min(len(old), RMAX + 1)) if dmin[r] < old[r]]
        assert not bad, ("two-sided dmin below the Round W dmin at", bad[:10])
    assert all(int(dmin[r]) >= dold[r] for r in range(1, 60))
    def conv(f, g):
        h = np.full(RMAX + 1, INF, dtype=np.int64)
        for s in range(RMAX + 1):
            if f[s] >= INF: continue
            r = np.arange(0, RMAX + 1 - s); h[s:] = np.minimum(h[s:], f[s] + g[r])
        return h
    base0 = np.full(RMAX + 1, INF, dtype=np.int64); base0[1:] = dmin[1:]
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    P0 = [unit]
    for n in range(1, NMAX + 1): P0.append(conv(P0[-1], base0))
    def P0at(m, x):
        if m < 0 or x < 0 or m > NMAX: return INF
        return int(P0[m][x])
    rows = []
    for cl in W["rows"]:
        R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]
        lb0 = P0at(n, R); lb1 = INF; arg = None
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                best_m = min((P0at(m, pieces) for m in range(0, n - Fi - sh + 1)), default=INF)
                if best_m >= INF: continue
                v = best_m + Fi + 8 * Fii - 6 * sh
                if v < lb1: lb1 = v; arg = dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh)
        rows.append(dict(R=R, p=cl["p"], F=F, chains=n, Delta=D, min_deficit_plain_roundW=cl["min_deficit_plain"],
                         min_deficit_junctions_roundW=cl["min_deficit_junctions"], min_deficit_plain=lb0,
                         min_deficit_junctions=int(lb1), junction_argmin=arg, excluded=bool(lb1 > D), margin=int(lb1 - D)))
    surv = [r for r in rows if not r["excluded"]]
    res = dict(cells=len(rows), excluded=len(rows) - len(surv), survivors=len(surv),
               survivors_roundW=sum(not c["excluded_junctions"] for c in W["rows"]),
               dmin_changes=[[r, int(dmin[r]), None] for r in range(1, RMAX + 1)][:0],
               dmin_twosided=[int(x) for x in dmin], rows=rows)
    s = json.dumps(res, indent=1); open(outp, "w").write(s)
    print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "dmin_twosided", "dmin_changes")}))
    print("survivors:", [(r["R"], r["F"], r["margin"]) for r in surv])
    print("sha256", hashlib.sha256(s.encode()).hexdigest())

main()
