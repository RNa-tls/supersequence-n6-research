#!/usr/bin/env python3
"""Round P -- cap-c path cover with trail-level single-commodity flow (no cycles), exploratory.
max sum (c - e) y  over option-consistent acyclic path covers by arcs with e < c.
Also reports the chains of the incumbent and the exact F of every concatenation order of the chains
(fixed-order DP re-optimises all options).
usage: pathcover_gg.py FAMILY.json E.npy c time_limit OUT.json"""
import sys, os, json, time, itertools
import numpy as np
import highspy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src")); sys.path.insert(0, os.path.join(HERE, "..", "..", "rO", "src"))
import options as OP
import fixed_order as FA


def main():
    fam_p, E_p, c, tl, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
    fam, opts = OP.load(fam_p)
    E = np.load(E_p).astype(np.int8)
    T = np.array([o["t"] for o in opts]); N = len(T); NT = 30
    same = T[:, None] == T[None, :]
    src, dst = np.nonzero((E < c) & ~same); NA = len(src)
    w = (c - E[src, dst]).astype(float)
    ts, td = T[src], T[dst]
    pairs = sorted(set(zip(ts.tolist(), td.tolist()))); pidx = {p: i for i, p in enumerate(pairs)}; NP = len(pairs)
    # columns: x (N), y (NA), f (NP), s (NT), g (NT)
    cx, cy, cf, cs, cg = 0, N, N + NA, N + NA + NP, N + NA + NP + NT
    ncol = cg + NT
    cost = np.zeros(ncol); cost[cy:cy + NA] = -w
    lo = np.zeros(ncol); up = np.ones(ncol); up[cf:cf + NP] = 29.0; up[cg:cg + NT] = 30.0
    integ = [highspy.HighsVarType.kInteger] * (N + NA) + [highspy.HighsVarType.kContinuous] * NP + [highspy.HighsVarType.kInteger] * NT + [highspy.HighsVarType.kContinuous] * NT
    R_lo, R_up, idx, val, st = [], [], [], [], [0]
    inf = highspy.kHighsInf
    def row(ix, vx, l, u):
        idx.extend(ix); val.extend(vx); st.append(len(idx)); R_lo.append(l); R_up.append(u)
    for t in range(NT):
        o = np.nonzero(T == t)[0]; row((cx + o).tolist(), [1.0] * len(o), 1, 1)
    outa = [[] for _ in range(N)]; ina = [[] for _ in range(N)]; tin = [[] for _ in range(NT)]; parcs = [[] for _ in range(NP)]
    for a in range(NA):
        outa[src[a]].append(a); ina[dst[a]].append(a); tin[td[a]].append(a); parcs[pidx[(ts[a], td[a])]].append(a)
    for o in range(N):
        if outa[o]: row([cy + a for a in outa[o]] + [cx + o], [1.0] * len(outa[o]) + [-1.0], -inf, 0)
        if ina[o]: row([cy + a for a in ina[o]] + [cx + o], [1.0] * len(ina[o]) + [-1.0], -inf, 0)
    for t in range(NT):      # s_t + sum in-arcs = 1
        row([cs + t] + [cy + a for a in tin[t]], [1.0] * (1 + len(tin[t])), 1, 1)
        # flow: g_t + sum_u f_ut - sum_u f_tu = 1
        ix = [cg + t]; vx = [1.0]
        for (p, q), i in pidx.items():
            if q == t: ix.append(cf + i); vx.append(1.0)
            if p == t: ix.append(cf + i); vx.append(-1.0)
        row(ix, vx, 1, 1)
        row([cg + t, cs + t], [1.0, -30.0], -inf, 0)
    for i in range(NP):
        row([cf + i] + [cy + a for a in parcs[i]], [1.0] + [-29.0] * len(parcs[i]), -inf, 0)
    h = highspy.Highs(); h.setOptionValue("output_flag", True); h.setOptionValue("time_limit", tl); h.setOptionValue("threads", 4)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(R_lo)
    lp.col_cost_ = cost; lp.col_lower_ = lo; lp.col_upper_ = up; lp.row_lower_ = np.array(R_lo, float); lp.row_upper_ = np.array(R_up, float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(idx, np.int32); lp.a_matrix_.value_ = np.array(val)
    lp.integrality_ = integ
    h.passModel(lp); h.run()
    info = h.getInfo(); sol = np.array(h.getSolution().col_value)
    res = dict(c=c, status=h.modelStatusToString(h.getModelStatus()), W=-info.objective_function_value, bound=-info.mip_dual_bound)
    y = np.nonzero(sol[cy:cy + NA] > 0.5)[0]
    nxt = {int(ts[a]): int(td[a]) for a in y}; prv = {v: k for k, v in nxt.items()}
    chains = []
    for t in range(NT):
        if t in prv: continue
        ch = [t]
        while ch[-1] in nxt: ch.append(nxt[ch[-1]])
        chains.append(ch)
    res["chains"] = chains; res["covered"] = sum(len(ch) for ch in chains)
    fo = FA.FixedOrder(fam_p, E_p)
    best = None
    if len(chains) <= 8:
        for perm in itertools.permutations(range(len(chains))):
            order = [t for i in perm for t in chains[i]]
            v = fo.F(order)
            if best is None or v < best[0]: best = (v, order)
        res["best_concat_F"] = best[0]; res["best_concat_order"] = best[1]
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
