#!/usr/bin/env python3
"""Round Y, section A -- the 40 cells left by Round X (kappa(46) <= 2 packing knapsack, rX/src/frontier_packing.py),
recomputed with the same tables and with an optimal chain decomposition reconstructed for every cell.
Per cell: R, p, F, n = 1 + p + F chains, Delta = 7(R - 720), V1 = 4R - 9 Delta, V2 = 17R - 38 Delta, the least deficit
of the knapsack, margin = least deficit - Delta, the optimal junction pattern, and one optimal decomposition into chains
(pieces r, least deficit d(r) of the chain's type, line values v1 = 4r - 9d, v2 = 17r - 38d, the chain's packing type).
usage: frontier40_table.py T0 T1 T1e T2 T2e L2N L2X ROUNDW_KNAPSACK.json ROUNDX_40.json OUT.json"""
import sys, json, hashlib
import numpy as np
def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F
RMAX, NMAX, INF = 800, 12, 10 ** 9
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
def conv_arg(f, g):
    h = np.full(RMAX + 1, INF, dtype=np.int64); arg = np.full(RMAX + 1, -1, dtype=np.int64)
    for s in range(RMAX + 1):
        if f[s] >= INF: continue
        r = np.arange(0, RMAX + 1 - s); cand = f[s] + g[r]; better = cand < h[s:]
        h[s:][better] = cand[better]; arg[s:][better] = r[better]
    return h, arg
def main():
    L1 = {k: feas(p) for k, p in zip(("T0", "T1", "T1e", "T2", "T2e"), sys.argv[1:6])}
    L2 = {"N": feas(sys.argv[6]), "X": feas(sys.argv[7])}
    W = json.load(open(sys.argv[8])); X40 = json.load(open(sys.argv[9])); outp = sys.argv[10]
    nu = {"T0": 0, "T1": 1, "T1e": 1, "T2": 2, "T2e": 2}; ex = {"T0": 0, "T1": 0, "T1e": 1, "T2": 0, "T2e": 1}; ex2 = {"N": 0, "X": 1}
    types = [(a, b) for a in L1 for b in L2]
    tab = {t: dtab(L1[t[0]], L2[t[1]]) for t in types}
    base = {}
    for t in types:
        b = np.full(RMAX + 1, INF, dtype=np.int64); b[1:] = tab[t][1:]; base[t] = b
    states = [(u, e, x) for u in range(3) for e in range(2) for x in range(2)]
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    P = [{s: (unit.copy() if s == (0, 0, 0) else np.full(RMAX + 1, INF, dtype=np.int64)) for s in states}]
    PAR = [None]
    for m in range(1, NMAX + 1):
        cur = {s: np.full(RMAX + 1, INF, dtype=np.int64) for s in states}; par = {s: {} for s in states}
        for s, arr in P[-1].items():
            if arr.min() >= INF: continue
            for t in types:
                s2 = (s[0] + nu[t[0]], s[1] + ex[t[0]], s[2] + ex2[t[1]])
                if s2[0] > 2 or s2[1] > 1 or s2[2] > 1: continue
                h, arg = conv_arg(arr, base[t]); better = h < cur[s2]
                for x in np.nonzero(better)[0]: par[s2][int(x)] = (s, t, int(arg[x]))
                cur[s2] = np.minimum(cur[s2], h)
        P.append(cur); PAR.append(par)
    def best(m, x):
        if m < 0 or x < 0 or m > NMAX: return INF, None
        v, sb = INF, None
        for s in states:
            if P[m][s][x] < v: v, sb = int(P[m][s][x]), s
        return v, sb
    def back(m, s, x):
        out = []
        while m > 0:
            ps, t, r = PAR[m][s][x]
            d = int(tab[t][r]); out.append(dict(r=r, d=d, v1=4 * r - 9 * d, v2=17 * r - 38 * d, line1_type=t[0], line2_type=t[1]))
            m, s, x = m - 1, ps, x - r
        return sorted(out, key=lambda c: -c["r"])
    surv = {(c["R"], c["F"]) for c in X40["rows"] if not c["excluded"]}
    rows = []
    for cl in W["rows"]:
        R, n, D, F, p = cl["R"], cl["chains"], cl["Delta"], cl["F"], cl["p"]
        if (R, F) not in surv: continue
        lb, arg = INF, None
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                for m in range(0, n - Fi - sh + 1):
                    v, sb = best(m, pieces)
                    if v >= INF: continue
                    tot = v + Fi + 8 * Fii - 6 * sh
                    if tot < lb: lb, arg = tot, (Fi, Fii, sh, m, sb, pieces)
        Fi, Fii, sh, m, sb, pieces = arg
        chains = back(m, sb, pieces)
        assert sum(c["r"] for c in chains) == pieces and sum(c["d"] for c in chains) + Fi + 8 * Fii - 6 * sh == lb
        rows.append(dict(R=R, p=p, F=F, chains=n, Delta=D, V1=4 * R - 9 * D, V2=17 * R - 38 * D, min_deficit=lb, margin=lb - D,
                         S0=(F == 0), junctions=dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh, chains_used=m, free_chains=n - Fi - sh - m),
                         decomposition=chains))
    for r in rows:
        x = next(c for c in X40["rows"] if (c["R"], c["F"]) == (r["R"], r["F"]))
        assert x["min_deficit"] == r["min_deficit"], (r["R"], r["F"])
    s = json.dumps(dict(cells=len(rows), source="rX/certs/lower_bound/frontier_46135_packing46_knapsack.json (same tables)", rows=rows), indent=1)
    open(outp, "w").write(s); print("cells", len(rows), "sha256", hashlib.sha256(s.encode()).hexdigest())
    for r in rows:
        print(f"({r['R']},{r['p']},{r['F']}) n={r['chains']} D={r['Delta']} V1={r['V1']} V2={r['V2']} margin={r['margin']} jn={r['junctions']['F_loops']}L{r['junctions']['F_pairs']}P",
              ' '.join(f"{c['r']}:{c['v1']}/{c['v2']}{'' if c['line1_type']=='T0' else c['line1_type']}{'X' if c['line2_type']=='X' else ''}" for c in r['decomposition']))
main()
