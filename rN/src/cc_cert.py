#!/usr/bin/env python3
"""Round N (section 3, checker A) -- exact integer check of a CC-LP dual certificate.

Weak duality for the CC-LP master (see cc_lp.py for the model):  for every dual vector y with
y >= 0 on the cut rows,
    [c0 = 2] + sum e  >=  b^T y + sum over column groups of min(0, min reduced cost in the group),
because every single-opening word is a feasible 0/1 point of the master whose cost is <= its true
[c0 = 2] + sum e, and the columns of each group sum to at most 1 in every feasible point:
    explicit arcs (e <= 2) grouped by tail option, else arcs (cost 3 <= e) by tail trail,
    eout / ein per option, s and t globally, z per free trail, cover columns per component.
The cover group minimum is computed by an exact subset DP over ALL covers of the component.

Everything is done in integers: y is rounded to multiples of 2^-30 (cut duals clipped at 0),
E and the costs are scaled by 2^30.  The row layout is rebuilt here from its definition:
  in_row[o] = o, out_row[o] = NO + o, then one selection row per free trail (increasing trail id),
  eo rows (30), ei rows (30), one convexity row per component (increasing id), s row, t row, cuts.
usage: cc_cert.py FAMILY.json E.npy DUALS.npz MODE [key=y_best] [out.json]"""
import sys, os, json
from fractions import Fraction
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

C1 = [2, 3, 4, 5, 6, 7, 23, 24, 25, 26, 27]
C2 = [9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21]
AT = [1, 8, 15, 22, 28, 29]
SC = 1 << 30
BIG = np.int64(1) << 60


def cover_min(Eloc, tl, din, dout, nt):
    """exact min over covers of (sum internal Eloc + sum din(start) + sum dout(end)); int64"""
    nm = 1 << nt; nl = len(tl)
    P = np.full((nm, nl), BIG, np.int64)
    P[1 << tl, np.arange(nl)] = din
    member = [np.nonzero((S >> tl) & 1)[0] for S in range(nm)]
    for S in range(1, nm):
        ii = member[S]; v = P[S, ii]
        if v.min() >= BIG // 2: continue
        oo = np.nonzero(((S >> tl) & 1) == 0)[0]
        if len(oo) == 0: continue
        cand = (v[:, None] + Eloc[np.ix_(ii, oo)]).min(0)
        S2 = S | (1 << tl[oo])
        np.minimum.at(P, (S2, oo), cand)
    Q = np.full(nm, BIG, np.int64)
    for S in range(1, nm):
        ii = member[S]; Q[S] = (P[S, ii] + dout[ii]).min()
    Cov = np.full(nm, BIG, np.int64); Cov[0] = 0
    for S in range(1, nm):
        low = S & -S; rest = S ^ low; sub = rest; best = BIG
        while True:
            U = sub | low
            val = Q[U] + Cov[S ^ U]
            if val < best: best = val
            if sub == 0: break
            sub = (sub - 1) & rest
        Cov[S] = best
    return int(Cov[nm - 1])


def main():
    fam_p, E_p, d_p, mode = sys.argv[1:5]
    key = sys.argv[5] if len(sys.argv) > 5 else "y_best"
    out_p = sys.argv[6] if len(sys.argv) > 6 else None
    fam, opts = OP.load(fam_p)
    E = np.load(E_p).astype(np.int64)
    NO = len(opts); T = np.array([o["t"] for o in opts]); NT = int(T.max()) + 1
    cut = np.array([o["cut"] for o in opts], np.int64)
    D = np.load(d_p)
    y = D[key].astype(float)
    comp = np.zeros(NT, int)
    comps = {}
    if mode in ("cc", "cca"): comp[C1] = 1; comp[C2] = 2; comps = {1: C1, 2: C2}
    if mode == "cca": comp[AT] = 3; comps[3] = AT
    if mode == "ccr": comp[C1] = 1; comp[C2] = 2; comp[AT] = 3; comp[[0, 14]] = 3; comps = {1: C1, 2: C2, 3: AT + [0, 14]}
    assert np.array_equal(comp, D["comp"])
    # rebuild the row layout
    in_row = np.arange(NO); out_row = NO + np.arange(NO); r = 2 * NO
    free = [t for t in range(NT) if comp[t] == 0]
    sel_row = {t: r + i for i, t in enumerate(free)}; r += len(free)
    eo_row = r + np.arange(NT); r += NT
    ei_row = r + np.arange(NT); r += NT
    conv_row = {X: r + i for i, X in enumerate(sorted(comps))}; r += len(comps)
    s_row = r; t_row = r + 1; r += 2
    sec_sets = D["sec_sets"].astype(bool); sec_rows = D["sec_rows"]
    assert len(sec_rows) == 0 or (sec_rows[0] == r and np.array_equal(sec_rows, r + np.arange(len(sec_rows))))
    if len(y) < r + len(sec_rows): y = np.concatenate([y, np.zeros(r + len(sec_rows) - len(y))])   # later cuts: dual 0
    Y = np.round(y * SC).astype(np.int64)
    rho = np.maximum(Y[sec_rows], 0) if len(sec_rows) else np.zeros(0, np.int64)
    # M[t, u] = sum of rho over cuts S with t not in S and u in S
    Msc = np.zeros((NT, NT), np.int64)
    for S, rv in zip(sec_sets, rho):
        if rv: Msc[np.ix_(~S, S)] += rv
    allowed = ~((comp[:, None] == comp[None, :]) & (comp[:, None] > 0)) & ~np.eye(NT, dtype=bool)
    bY = sum(int(Y[rr]) for rr in sel_row.values()) + sum(int(Y[rr]) for rr in conv_row.values()) + int(Y[s_row]) + int(Y[t_row]) + int(rho.sum())
    corr = {}
    # explicit arcs: all allowed pairs with e <= 2, grouped by tail option
    g = np.zeros(NO, np.int64)
    for lo in range(0, NO, 1024):
        a = np.arange(lo, min(NO, lo + 1024))
        Eb = E[a]
        ok = (Eb <= 2) & allowed[T[a]][:, T]
        d = Eb * SC - Y[out_row[a]][:, None] - Y[in_row][None, :] - Msc[T[a]][:, T]
        d = np.where(ok, d, 0)
        g[a] = np.minimum(0, d.min(1))
    corr["arc"] = int(g.sum())
    # else arcs (cost 3), grouped by tail trail
    de = 3 * SC + Y[eo_row][:, None] + Y[ei_row][None, :] - Msc
    de = np.where(allowed, de, 0)
    corr["else"] = int(np.minimum(0, de.min(1)).sum())
    corr["eout"] = int(np.minimum(0, -Y[out_row] - Y[eo_row[T]]).sum())
    corr["ein"] = int(np.minimum(0, -Y[in_row] - Y[ei_row[T]]).sum())
    secsum = np.zeros(NT, np.int64)
    for S, rv in zip(sec_sets, rho): secsum[S] += rv
    corr["s"] = int(min(0, ((3 - cut) * SC - Y[in_row] - Y[s_row] - secsum[T]).min()))
    corr["t"] = int(min(0, (-Y[out_row] - Y[t_row]).min()))
    cz = 0
    for t in free:
        oo = np.nonzero(T == t)[0]
        cz += int(min(0, (-Y[sel_row[t]] + Y[in_row[oo]] + Y[out_row[oo]]).min()))
    corr["z"] = cz
    cc = 0; cov_detail = {}
    for X in sorted(comps):
        trails = comps[X]
        loc = np.concatenate([np.nonzero(T == t)[0] for t in trails])
        tl = np.concatenate([np.full(int((T == t).sum()), i) for i, t in enumerate(trails)])
        Tg = T[loc]
        Eloc = E[np.ix_(loc, loc)] * SC - Msc[np.ix_(Tg, Tg)]
        Eloc[tl[:, None] == tl[None, :]] = BIG
        cm = cover_min(Eloc, tl, Y[in_row[loc]], Y[out_row[loc]], len(trails)) - int(Y[conv_row[X]])
        cov_detail[X] = cm; cc += min(0, cm)
    corr["cover"] = cc
    total = bY + sum(corr.values())
    LB = Fraction(total, SC)
    res = dict(mode=mode, key=key, scale="2^30", bY=bY, corrections=corr, cover_rc_min={str(k): v for k, v in cov_detail.items()},
               lower_bound=str(LB), lower_bound_float=float(LB), sum_e_plus_c0_at_least=int(-(-LB.numerator // LB.denominator)) if LB > 0 else 0,
               J_at_least=77 + int(-(-LB.numerator // LB.denominator)) if LB > 0 else None, cuts=int(len(sec_rows)))
    print(json.dumps(res))
    if out_p: json.dump(res, open(out_p, "w"), indent=1)


if __name__ == "__main__":
    main()
