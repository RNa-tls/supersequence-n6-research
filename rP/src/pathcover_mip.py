#!/usr/bin/env python3
"""Round P -- cap-c path-cover relaxation of the single-opening model.

For every single-opening word (order pi, options o_1..o_30):
    F = [cut(o_1) = 2] + sum_{i<30} e_i  >=  sum_i min(e_i, c)  =  29 c - sum_{i: e_i < c} (c - e_i).
The links with e_i < c form vertex-disjoint, option-consistent, acyclic paths (a 'cheap path cover').
Hence  F >= 29 c - W_c*,  W_c* = max over option-consistent acyclic path covers by arcs with e < c of
sum (c - e).  No Hamiltonicity is involved.  This script computes W_c* by MIP with lazy acyclicity
cuts (iterate: solve, find cycles, add  sum_{arcs inside S} y <= |S| - 1, re-solve).
usage: pathcover_mip.py FAMILY.json E.npy c OUT.json [time_limit]"""
import sys, os, json, time
import numpy as np
import highspy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rN", "src"))
import options as OP


def build(fam_p, E_p, c):
    fam, opts = OP.load(fam_p)
    E = np.load(E_p).astype(np.int8)
    T = np.array([o["t"] for o in opts]); N = len(T)
    same = T[:, None] == T[None, :]
    src, dst = np.nonzero((E < c) & ~same)
    w = (c - E[src, dst]).astype(float)
    return T, src, dst, w, E[src, dst]


def solve(T, src, dst, w, time_limit=3600, cuts=None, verbose=False):
    N = len(T); NA = len(src); NT = int(T.max()) + 1
    h = highspy.Highs(); h.setOptionValue("output_flag", verbose); h.setOptionValue("time_limit", float(time_limit))
    h.setOptionValue("mip_rel_gap", 0.0); h.setOptionValue("threads", 4)
    inf = highspy.kHighsInf
    # columns: x_o (N) then y_a (NA)
    lp = highspy.HighsLp(); lp.num_col_ = N + NA
    lp.col_cost_ = np.concatenate([np.zeros(N), -w]); lp.col_lower_ = np.zeros(N + NA); lp.col_upper_ = np.ones(N + NA)
    rows_lo = []; rows_up = []; idx = []; val = []; starts = [0]
    def addrow(ix, vx, lo, up):
        idx.extend(ix); val.extend(vx); starts.append(len(idx)); rows_lo.append(lo); rows_up.append(up)
    for t in range(NT):
        o = np.nonzero(T == t)[0]; addrow(o.tolist(), [1.0] * len(o), 1.0, 1.0)
    out = [[] for _ in range(N)]; inn = [[] for _ in range(N)]
    for a in range(NA): out[src[a]].append(a); inn[dst[a]].append(a)
    for o in range(N):
        if out[o]: addrow([N + a for a in out[o]] + [o], [1.0] * len(out[o]) + [-1.0], -inf, 0.0)
        if inn[o]: addrow([N + a for a in inn[o]] + [o], [1.0] * len(inn[o]) + [-1.0], -inf, 0.0)
    ts, td = T[src], T[dst]
    pairarcs = {}
    for a in range(NA): pairarcs.setdefault((min(ts[a], td[a]), max(ts[a], td[a])), []).append(a)
    for (p, q), al in pairarcs.items():             # 2-cycles at the trail level
        if any(ts[a] == p for a in al) and any(ts[a] == q for a in al): addrow([N + a for a in al], [1.0] * len(al), -inf, 1.0)
    for S in (cuts or []):
        S = set(S); al = [a for a in range(NA) if ts[a] in S and td[a] in S]
        addrow([N + a for a in al], [1.0] * len(al), -inf, len(S) - 1.0)
    lp.num_row_ = len(rows_lo); lp.row_lower_ = np.array(rows_lo); lp.row_upper_ = np.array(rows_up)
    # row-wise matrix
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(starts, np.int32); lp.a_matrix_.index_ = np.array(idx, np.int32); lp.a_matrix_.value_ = np.array(val)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * (N + NA)
    h.passModel(lp)
    t0 = time.time(); h.run()
    info = h.getInfo(); st = h.modelStatusToString(h.getModelStatus())
    sol = np.array(h.getSolution().col_value)
    return dict(status=st, obj=-info.objective_function_value, bound=-info.mip_dual_bound, gap=info.mip_gap, sec=time.time() - t0), sol


def cycles(T, src, dst, sol, N):
    y = sol[N:] > 0.5
    nxt = {}
    for a in np.nonzero(y)[0]: nxt[int(T[src[a]])] = int(T[dst[a]])
    seen = set(); cyc = []
    for s in nxt:
        if s in seen: continue
        path = []; u = s; pos = {}
        while u in nxt and u not in pos and u not in seen:
            pos[u] = len(path); path.append(u); u = nxt[u]
        if u in pos: cyc.append(path[pos[u]:])
        seen.update(path)
    return cyc


def main():
    fam_p, E_p, c, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    tl = float(sys.argv[5]) if len(sys.argv) > 5 else 3600
    T, src, dst, w, e = build(fam_p, E_p, c)
    N = len(T); cuts = []; log = []
    while True:
        r, sol = solve(T, src, dst, w, tl, cuts)
        cyc = cycles(T, src, dst, sol, N)
        r["cycles"] = cyc; log.append(r)
        print(json.dumps(r), flush=True)
        if not cyc or r["status"] != "Optimal": break
        cuts += cyc
    y = np.nonzero(sol[N:] > 0.5)[0]
    res = dict(c=c, arcs=int(len(src)), W=r["obj"], bound=r["bound"], status=r["status"], F_lower=29 * c - r["bound"], cuts=cuts, log=log,
               chosen=[dict(src=int(src[a]), dst=int(dst[a]), e=int(e[a]), ts=int(T[src[a]]), td=int(T[dst[a]])) for a in y],
               options=[int(o) for o in np.nonzero(sol[:N] > 0.5)[0]])
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k in ("c", "arcs", "W", "bound", "status", "F_lower")}))


if __name__ == "__main__":
    main()
