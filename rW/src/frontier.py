#!/usr/bin/env python3
"""Round W -- the 46135 frontier of Theorem D (Halfar), canonical table and the (r, delta) knapsack.

Arithmetic of D8.lean at length 46134 (w + 8 <= 46134):
  coverage  7*46085 + Delta + 7 (X + J) <= 7 * 46134,  holes  Delta = 7 (R - 720),
  line 1    4R + 5F <= 9 Delta + 56 (1 + X + J),   line 2   17R + 6F <= 38 Delta + 264 (1 + X + J),
  n = X + cc = X + J + F + 1 chains,  Tri(R, Delta, n).
R + p <= 768 (p = X + J) is the 46134 theorem, so only R + p = 769 remains (Round V).

Per chain (r pieces, deficit d):  line 1 with the piece-count lemma  4r - 9d <= M1(r),  line 2 with its census
17r - 38d <= M2(r),  the zone statement, and integrality; so  d >= dmin(r).  A cell needs n chains with
sum r = R and sum d = Delta; the necessary condition used here is  min over partitions of  sum dmin(r_i) <= Delta,
refined at free junctions (Halfar's Lemma J1(c)): a free junction is either a single-row component that is its own
source and target (deficit >= 1), or the two pieces at it have deficits >= 2 with sum >= 8; cutting an end piece of
deficit e off a chain leaves a chain, so a chain with free ends of deficits e_1.. has  d >= dmin(r - #ends) + sum e.
usage: frontier.py CENSUS1.json CENSUS2.json OUT_cells.json"""
import sys, json, math, hashlib
import numpy as np

def census(path):
    L = open(path).read().strip().split("\n"); h = json.loads(L[0]); b = json.loads(L[1]); a, bb, c = h["params"]
    raw = {int(k): int(v) for k, v in b["least_pieces_by_value"].items()}
    return (a, bb, c), raw

def Mtab(raw, c, RMAX):
    """M(r) = largest v in 1..c with a primitive chain of value >= v and <= r pieces; 0 if none."""
    m = {}
    cur = 10 ** 9
    for v in range(c, 0, -1):
        if v in raw: cur = min(cur, raw[v])
        m[v] = cur
    M = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(RMAX + 1):
        best = 0
        for v in range(c, 0, -1):
            if m[v] <= r: best = v; break
        M[r] = best
    return M, m

def main():
    (a1, b1, c1), raw1 = census(sys.argv[1]); (a2, b2, c2), raw2 = census(sys.argv[2]); outp = sys.argv[3]
    assert (a1, b1, c1) == (4, 9, 56) and (a2, b2, c2) == (17, 38, 264)
    RMAX = 800
    M1, m1 = Mtab(raw1, c1, RMAX); M2, m2 = Mtab(raw2, c2, RMAX)
    INF = 10 ** 9
    dmin = np.zeros(RMAX + 1, dtype=np.int64)
    for r in range(1, RMAX + 1):
        d = max(0, -((M1[r] - 4 * r) // 9), -((M2[r] - 17 * r) // 38))      # ceil((4r - M1)/9), ceil((17r - M2)/38)
        while True:                                                         # zone statement (H3)
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            if v1 >= 54 and v2 >= 258 and v1 != 56: d += 1; continue
            break
        dmin[r] = d
    # n-fold min-plus convolutions of dmin over r >= 1
    NMAX = 40
    def conv(f, g):
        h = np.full(RMAX + 1, INF, dtype=np.int64)
        for s in range(RMAX + 1):
            if f[s] >= INF: continue
            r = np.arange(0, RMAX + 1 - s); h[s:] = np.minimum(h[s:], f[s] + g[r])
        return h
    base0 = np.full(RMAX + 1, INF, dtype=np.int64); base0[1:] = dmin[1:]                      # normal chain
    base1 = np.full(RMAX + 1, INF, dtype=np.int64); base1[1:] = dmin[:-1]                     # one free end cut off
    base2 = np.full(RMAX + 1, INF, dtype=np.int64); base2[2:] = dmin[:-2]                     # two free ends cut off (r >= 2)
    one = np.full(RMAX + 1, INF, dtype=np.int64); one[1] = 0                                  # a single piece (deficit counted elsewhere)
    unit = np.full(RMAX + 1, INF, dtype=np.int64); unit[0] = 0
    P0 = [unit]
    for n in range(1, NMAX + 1): P0.append(conv(P0[-1], base0))
    # cells
    cells = []
    for R in range(747, 770):
        p = 769 - R; D = 7 * (R - 720)
        for F in range(0, 80):
            if not (4 * R + 5 * F <= 9 * D + 56 * (1 + p) and 17 * R + 6 * F <= 38 * D + 264 * (1 + p)): break
            n = 1 + p + F; s1 = 9 * D + 56 * n - 4 * R; s2 = 38 * D + 264 * n - 17 * R
            if s1 < 0 or s2 < 0: continue
            if not (s1 == 0 or s1 >= 3 or s2 >= 7): continue
            l1 = 9 * D + 56 * (1 + p) - 4 * R - 5 * F; l2 = 38 * D + 264 * (1 + p) - 17 * R - 6 * F
            cells.append(dict(R=R, p=p, F=F, chains=n, Delta=D, V1=4 * R - 9 * D, V2=17 * R - 38 * D,
                              tri_slack1=s1, tri_slack2=s2, line1_junction_slack=l1, line2_junction_slack=l2))
    # knapsack 0: no junction refinement:  min over n chains with sum r = R of sum dmin(r_i)  = P0[n][R]
    # knapsack 1: free junctions = F_i loops (a single row of deficit >= 1, its own source and target) and F_ii
    #   pairs (end pieces of deficits >= 2 with sum >= 8).  Cut every free end piece off its chain: the rest are
    #   chains (possibly empty).  A row that is an end piece at two pairs (a component of one row entered and left by
    #   free junctions) counts once; its deficit is at most 6, so the end-piece deficits sum to >= 8 F_ii - 6 s
    #   (s such rows) over 2 F_ii - s distinct pieces.  With m nonempty remaining chains (m <= n - F_i - s) the deficit
    #   is >= P0[m][R - F_i - (2 F_ii - s)] + F_i + 8 F_ii - 6 s, and P0[m][x] does not increase with m.
    def P0at(m, x):
        if m < 0 or x < 0 or m > NMAX: return INF
        return int(P0[m][x])
    out = []
    for cl in cells:
        R, n, D, F = cl["R"], cl["chains"], cl["Delta"], cl["F"]
        lb0 = P0at(n, R)
        lb1 = INF; arg = None
        for Fi in range(F + 1):
            Fii = F - Fi
            for sh in range(Fii + 1):
                if Fi + sh > n: continue
                pieces = R - Fi - (2 * Fii - sh)
                if pieces < 0: continue
                best_m = INF
                for m in range(0, n - Fi - sh + 1):          # all m (monotonicity is not assumed)
                    v = P0at(m, pieces)
                    if v < best_m: best_m = v
                if best_m >= INF: continue
                v = best_m + Fi + 8 * Fii - 6 * sh
                if v < lb1: lb1 = v; arg = dict(F_loops=Fi, F_pairs=Fii, shared_rows=sh)
        cl.update(min_deficit_plain=lb0, min_deficit_junctions=int(lb1), junction_argmin=arg,
                  excluded_plain=bool(lb0 > D), excluded_junctions=bool(lb1 > D), deficit_margin=int(lb1 - D))
        out.append(cl)
    res = dict(cells=len(out), excluded_plain=sum(c["excluded_plain"] for c in out), excluded_junctions=sum(c["excluded_junctions"] for c in out),
               dmin_first=[int(x) for x in dmin[:60]], dmin_tail=[int(x) for x in dmin[760:770]], rows=out)
    s = json.dumps(res, indent=1); open(outp, "w").write(s)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
    print("sha256", hashlib.sha256(s.encode()).hexdigest())

main()
