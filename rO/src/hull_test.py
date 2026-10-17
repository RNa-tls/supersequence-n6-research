#!/usr/bin/env python3
"""Round O (sections 8-10) -- is the trail-level support of the 16.111 LP optimum a convex
combination of genuine trail orders?

1. Solve the Round M/N single-opening arc LP (Gavish-Graves flow, EMAX = 2 + trail-level else arcs).
2. Aggregate the optimal option flows to the trail level: z_tu (arcs t -> u, else arcs included),
   f_t (path starts at t), l_t (path ends at t).
3. Membership LP (column generation over Hamiltonian trail paths, exact 30-node pricing MIP):
       min sum |slack|  s.t.  sum_pi lam_pi (z^pi, f^pi, l^pi) + slack = (z, f, l),  sum lam = 1.
   Optimum 0  <=>  (z, f, l) lies in the order hull; then the support {pi : lam_pi > 0} is an explicit
   decomposition of the fractional optimum into orders, and their exact values F(pi) are reported.
   Optimum > 0: the final duals (a, b_f, b_l, theta) give an inequality a.z + b_f.f + b_l.l <= theta
   valid for EVERY order and violated by the LP optimum (a 'comb-like' order cut).
usage: hull_test.py FAMILY.json E.npy OUT.json"""
import sys, os, json, time
import numpy as np
import highspy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src"))
import options as OP
import gtsp_mip as GM
import oh_lp as OH
import fixed_order as FA


def aggregate(r, opts, NT):
    sol = r["_sol"]; c = r["_cols"]; ids = r["_ids"]; arcs = r["_arcs"]; fidx = r["_fidx"]; tset = r["_tset"]
    z = np.zeros((NT, NT)); f = np.zeros(NT); l = np.zeros(NT)
    for k, (a, b, e) in enumerate(arcs): z[opts[a]["t"], opts[b]["t"]] += sol[c["cz"] + k]
    for (i, j), col in fidx.items(): z[tset[i], tset[j]] += sol[col]
    for k, o in enumerate(ids):
        f[opts[o]["t"]] += sol[c["cs"] + k]; l[opts[o]["t"]] += sol[c["ct"] + k]
    return z, f, l


def membership(z, f, l, max_iter=400):
    NT = len(f); pairs = [(t, u) for t in range(NT) for u in range(NT) if t != u]
    target = np.concatenate([[z[t, u] for t, u in pairs], f, l, [1.0]])
    nr = len(target)
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    # slack columns s+ and s- for the first nr-1 rows (not for convexity)
    lp = highspy.HighsLp(); ns = 2 * (nr - 1); lp.num_col_ = ns; lp.num_row_ = nr
    lp.col_cost_ = np.ones(ns); lp.col_lower_ = np.zeros(ns); lp.col_upper_ = np.full(ns, highspy.kHighsInf)
    lp.row_lower_ = target.copy(); lp.row_upper_ = target.copy()
    st = list(range(0, ns + 1)); ix = []; vl = []
    for r in range(nr - 1): ix += [r]; vl += [1.0]
    for r in range(nr - 1): ix += [r]; vl += [-1.0]
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(ix, np.int32); lp.a_matrix_.value_ = np.array(vl)
    h.passModel(lp)
    pidx = {p: k for k, p in enumerate(pairs)}
    paths = []
    m = OH.OHMaster.__new__(OH.OHMaster); m.NT = NT
    def add_path(pi):
        rows = [pidx[(a, b)] for a, b in zip(pi, pi[1:])] + [len(pairs) + pi[0], len(pairs) + NT + pi[-1], nr - 1]
        h.addCol(0.0, 0.0, highspy.kHighsInf, len(rows), np.array(rows, np.int32), np.ones(len(rows)))
        paths.append(list(pi))
    # seed: greedy path following the heaviest arcs
    start = int(np.argmax(f)); pi = [start]
    while len(pi) < NT:
        cand = [(z[pi[-1], u], u) for u in range(NT) if u not in pi]; pi.append(max(cand)[1])
    add_path(pi)
    for it in range(max_iter):
        h.run(); obj = h.getInfo().objective_function_value; y = np.array(h.getSolution().row_dual)
        M = np.zeros((NT, NT))
        for k, (t, u) in enumerate(pairs): M[t, u] = -y[k]
        nf = -y[len(pairs):len(pairs) + NT]; nl = -y[len(pairs) + NT:len(pairs) + 2 * NT]
        v, q, bound, stt = OH.OHMaster.exact_path(m, M, nf, nl)
        rc = v - y[nr - 1]
        if rc > -1e-9: break
        add_path(q)
    x = np.array(h.getSolution().col_value)
    lam = [(paths[k], float(x[ns + k])) for k in range(len(paths)) if x[ns + k] > 1e-9]
    return obj, lam, y, pairs, it


def main():
    fam_p, E_p, out = sys.argv[1:4]
    fam, opts = OP.load(fam_p); NT = 30
    t0 = time.time()
    r = GM.solve(opts, list(range(NT)), emax=2, C=1, start_cost=1.0, time_limit=3000, threads=2, relax=True, solver="ipm", crossover=True)
    z, f, l = aggregate(r, opts, NT)
    print(json.dumps(dict(event="lp", lp=r["obj"], status=r["status"], sec=round(time.time() - t0, 1), z_sum=float(z.sum()), f_sum=float(f.sum()))), flush=True)
    dist, lam, y, pairs, its = membership(z, f, l)
    res = dict(lp=r["obj"], membership_distance=dist, iterations=its, support=len(lam))
    if dist < 1e-6:
        fo = FA.FixedOrder(fam_p, E_p)
        vals = [(fo.F(p), w, p) for p, w in lam]
        res.update(in_hull=True, decomposition=[dict(order=p, lam=w, F=v) for v, w, p in sorted(vals, key=lambda t: -t[1])],
                   lam_weighted_F=sum(v * w for v, w, _ in vals), min_F=min(v for v, _, _ in vals))
    else:
        a = {f"{t}->{u}": float(y[k]) for k, (t, u) in enumerate(pairs) if abs(y[k]) > 1e-9}
        res.update(in_hull=False, cut_coeffs=a, cut_first={str(t): float(y[len(pairs) + t]) for t in range(NT) if abs(y[len(pairs) + t]) > 1e-9},
                   cut_last={str(t): float(y[len(pairs) + NT + t]) for t in range(NT) if abs(y[len(pairs) + NT + t]) > 1e-9}, theta=float(y[-1]))
    res["z_support"] = {f"{t}->{u}": round(float(z[t, u]), 4) for t in range(NT) for u in range(NT) if z[t, u] > 1e-6}
    res["first"] = {str(t): round(float(f[t]), 4) for t in range(NT) if f[t] > 1e-6}
    res["last"] = {str(t): round(float(l[t]), 4) for t in range(NT) if l[t] > 1e-6}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k in ("lp", "membership_distance", "in_hull", "support", "lam_weighted_F", "min_F", "iterations")}))


if __name__ == "__main__":
    main()
