#!/usr/bin/env python3
"""Round X -- canonical table of the 69 cells of the 46135 frontier left by Round W, with optimal chain partitions.

Same arithmetic as rW/src/frontier.py (Theorem D of Halfar at length 46134, junction-refined deficit knapsack), recomputed
here from the two piece-count censuses; dmin is compared with the Round W table.  For every surviving cell the script
lists every optimal junction pattern (F_loops, F_pairs, shared rows, number m of non-empty remaining chains) and one
explicit optimal partition of the remaining rows into chains (lengths r_i with dmin(r_i), and the values
v1 = 4 r - 9 d, v2 = 17 r - 38 d of each chain at d = dmin(r)).
usage: frontier69.py CENSUS1.json CENSUS2.json ROUNDW_KNAPSACK.json OUT.json"""
import sys, json, hashlib
import numpy as np

def census(path):
    L = open(path).read().strip().split("\n"); h = json.loads(L[0]); b = json.loads(L[1])
    return tuple(h["params"]), {int(k): int(v) for k, v in b["least_pieces_by_value"].items()}

def Mtab(raw, c, RMAX):
    m, cur = {}, 10 ** 9
    for v in range(c, 0, -1):
        if v in raw: cur = min(cur, raw[v])
        m[v] = cur
    M = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(RMAX + 1):
        M[r] = next((v for v in range(c, 0, -1) if m[v] <= r), 0)
    return M

def main():
    p1, raw1 = census(sys.argv[1]); p2, raw2 = census(sys.argv[2]); W = json.load(open(sys.argv[3])); outp = sys.argv[4]
    assert p1 == (4, 9, 56) and p2 == (17, 38, 264)
    RMAX, NMAX, INF = 800, 40, 10 ** 9
    M1, M2 = Mtab(raw1, 56, RMAX), Mtab(raw2, 264, RMAX)
    dmin = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(1, RMAX + 1):
        d = max(0, -((M1[r] - 4 * r) // 9), -((M2[r] - 17 * r) // 38))
        while 4 * r - 9 * d >= 54 and 17 * r - 38 * d >= 258 and 4 * r - 9 * d != 56: d += 1
        dmin[r] = d
    assert [int(x) for x in dmin[:60]] == W["dmin_first"] and [int(x) for x in dmin[760:770]] == W["dmin_tail"]
    # min-plus powers with argmin
    P = [np.full(RMAX + 1, INF, dtype=np.int64)]; P[0][0] = 0; ARG = [None]
    for n in range(1, NMAX + 1):
        h = np.full(RMAX + 1, INF, dtype=np.int64); a = np.zeros(RMAX + 1, dtype=np.int64)
        for x in range(1, RMAX + 1):
            r = np.arange(1, x + 1); v = P[-1][x - r] + dmin[r]; i = int(np.argmin(v)); h[x] = v[i]; a[x] = r[i]
        h[h > INF] = INF; P.append(h); ARG.append(a)
    def part(m, x):
        out = []
        while m > 0: r = int(ARG[m][x]); out.append(r); x -= r; m -= 1
        assert x == 0; return sorted(out, reverse=True)
    keep = [c for c in W["rows"] if not c["excluded_junctions"]]
    assert len(keep) == 69
    rows = []
    for cl in keep:
        R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]
        best, pats = INF, []
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                for m in range(0, n - Fi - sh + 1):
                    if m > NMAX or P[m][pieces] >= INF: continue
                    v = int(P[m][pieces]) + Fi + 8 * Fii - 6 * sh
                    if v < best: best, pats = v, []
                    if v == best: pats.append((Fi, Fii, sh, m, pieces))
        assert best == cl["min_deficit_junctions"], (cl, best)
        Fi, Fii, sh, m, pieces = pats[0]
        pr = part(m, pieces)
        chains = [dict(r=r, dmin=int(dmin[r]), v1=4 * r - 9 * int(dmin[r]), v2=17 * r - 38 * int(dmin[r])) for r in pr]
        cluster = "S0" if F == 0 else ("SL" if all(p[1] == 0 for p in pats) else "SM")
        rows.append(dict(R=R, p=cl["p"], F=F, chains=n, Delta=D, N_extra_rows=R - 720, V1=cl["V1"], V2=cl["V2"],
                         tri_slack1=cl["tri_slack1"], tri_slack2=cl["tri_slack2"],
                         line1_junction_slack=cl["line1_junction_slack"], line2_junction_slack=cl["line2_junction_slack"],
                         min_deficit=best, margin=best - D, spare_deficit=D - best, cluster=cluster,
                         optimal_patterns=[dict(F_loops=a, F_pairs=b, shared_rows=c, nonempty_chains=d, rows_in_chains=e) for a, b, c, d, e in pats],
                         example_partition=dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh, chains=chains,
                                                end_pieces=2 * Fii - sh, end_piece_deficit_lower_bound=8 * Fii - 6 * sh)))
    res = dict(cells=len(rows), clusters={k: sum(r["cluster"] == k for r in rows) for k in ("S0", "SL", "SM")},
               margin_histogram={str(k): sum(r["margin"] == k for r in rows) for k in range(-6, 1)},
               dmin_all=[int(x) for x in dmin], rows=rows)
    s = json.dumps(res, indent=1); open(outp, "w").write(s)
    print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "dmin_all")}))
    print("sha256", hashlib.sha256(s.encode()).hexdigest())

main()
