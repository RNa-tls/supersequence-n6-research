#!/usr/bin/env python3
"""Round M (sections 4-9) -- EXACT optimum of the SINGLE-OPENING model of a closed-trail family
(every trail visited in one piece, opened at any cyclic edge of any version, any trail order),
as a MIP with lazy trail-level subtour elimination.

Identity (rM/lean/OpeningJoint.lean, joint_J_pieces): for pieces p_0..p_29
        J = E0 + 29 + [cut(p_0) = 2] + sum_k e_k,     e_k = w(exit(p_{k-1}), entry(p_k)) - cut(p_k) - 1 >= 0
(e >= 0 for every inter-trail arc of the 46187 family: ideal_graph.py).
Arcs with e <= EMAX are enumerated exactly; every other boundary is represented by a trail-level
"else" arc F[T,T'] of cost EMAX + 1 (a LOWER bound on its true excess).  Hence the MIP optimum is a
lower bound on min sum_k e_k over all single-opening words, and it is exact when the optimal
solution uses no else arc whose true excess exceeds EMAX + 1 (checked on the decoded route).
Variables: y_o (option o of trail T chosen, sum_o y_o = 1), z_a (enumerated arc), h_o / r_o (else
out / in of option o), F[T,T'] (else arc between trails), s_o / t_o (first / last piece).
Subtours: every nonempty trail set S must be left (z or F arcs, or t inside S); violated sets of
the integer solution are added and the MIP is re-solved (all pairs are added up front).
With CUTOFF (e.g. 22.5) only solutions of objective < CUTOFF are sought (HiGHS objective_bound):
status Infeasible after the subtour loop proves  min sum e >= ceil(CUTOFF), i.e. no single-opening
word with J <= 77 + ceil(CUTOFF) - 1.
usage: single_opening_mip.py FAMILY.json [EMAX] [TIME_PER_SOLVE] [THREADS] [CUTOFF]"""
import sys, os, json, time, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE

def main():
    import highspy
    fam = json.load(open(sys.argv[1])); EMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    TL = float(sys.argv[3]) if len(sys.argv) > 3 else 3600.0
    TH = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    CUT = float(sys.argv[5]) if len(sys.argv) > 5 else None
    t0 = time.time()
    layers, const = TOE.load_layers(fam)
    T = len(layers); E0 = const - 8 - 9 * 5040 - 720 + 0     # const = 8 + 45360 + sum k_T
    E0 = (const - 8 - 45360) - 720
    opts = []; by_entry = defaultdict(list); trail_opts = [[] for _ in range(T)]
    for t, L in enumerate(layers):
        for o in L:
            j = len(opts); opts.append((t,) + o); by_entry[o[0]].append(j); trail_opts[t].append(j)
    arcs = []                                                    # (from opt, to opt, e)
    for a, (t, entry, ex, cut, v, k) in enumerate(opts):
        for w in range(2, EMAX + 5):
            for perm in itertools.permutations(ex[:w]):
                y = ex[w:] + perm
                if TOE.wt(ex, y) != w: continue
                for b in by_entry.get(y, []):
                    if opts[b][0] == t: continue
                    e = w - opts[b][3] - 1
                    assert e >= 0, "negative excess between trails"
                    if e <= EMAX: arcs.append((a, b, e))
    NO = len(opts); NA = len(arcs)
    pairs = [(i, j) for i in range(T) for j in range(T) if i != j]
    NF = len(pairs)
    # column layout
    cy = 0; cz = cy + NO; ch = cz + NA; cr = ch + NO; cs = cr + NO; ct = cs + NO; cf = ct + NO; cx = cf + NF; ncol = cx + NF
    cost = np.zeros(ncol)
    for i, (a, b, e) in enumerate(arcs): cost[cz + i] = e
    for o in range(NO): cost[cs + o] = 1.0 if opts[o][3] == 2 else 0.0
    cost[cf:cf + NF] = EMAX + 1
    lower = np.zeros(ncol); upper = np.ones(ncol)
    integ = np.zeros(ncol, dtype=np.int32)
    integ[cy:cy + NO] = 1; integ[cz:cz + NA] = 1; integ[cf:cf + NF] = 1; integ[cx:cx + NF] = 1
    rows = []                                                    # (idx list, val list, lo, hi)
    out_arcs = defaultdict(list); in_arcs = defaultdict(list)
    for i, (a, b, e) in enumerate(arcs): out_arcs[a].append(cz + i); in_arcs[b].append(cz + i)
    for t in range(T):
        rows.append(([cy + o for o in trail_opts[t]], [1.0] * len(trail_opts[t]), 1.0, 1.0))
    for o in range(NO):
        idx = out_arcs[o] + [ch + o, ct + o, cy + o]; rows.append((idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0))
        idx = in_arcs[o] + [cr + o, cs + o, cy + o]; rows.append((idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0))
    fidx = {p: cf + i for i, p in enumerate(pairs)}
    for t in range(T):
        idx = [ch + o for o in trail_opts[t]] + [fidx[(t, u)] for u in range(T) if u != t]
        rows.append((idx, [1.0] * len(trail_opts[t]) + [-1.0] * (T - 1), 0.0, 0.0))
        idx = [cr + o for o in trail_opts[t]] + [fidx[(u, t)] for u in range(T) if u != t]
        rows.append((idx, [1.0] * len(trail_opts[t]) + [-1.0] * (T - 1), 0.0, 0.0))
    rows.append(([cs + o for o in range(NO)], [1.0] * NO, 1.0, 1.0))
    rows.append(([ct + o for o in range(NO)], [1.0] * NO, 1.0, 1.0))
    arc_trails = [(opts[a][0], opts[b][0]) for (a, b, e) in arcs]
    xidx = {p: cx + i for i, p in enumerate(pairs)}
    by_pair = defaultdict(list)
    for i, tp in enumerate(arc_trails): by_pair[tp].append(cz + i)
    for p in pairs:                       # X[T,T'] = sum of z arcs T -> T' + F[T,T']
        idx = by_pair[p] + [fidx[p], xidx[p]]
        rows.append((idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0))
    def sec_row(S):
        Sset = set(S); idx = []
        for (ta, tb), c in xidx.items():
            if ta in Sset and tb not in Sset: idx.append(c)
        for t in S: idx += [ct + o for o in trail_opts[t]]
        return (idx, [1.0] * len(idx), 1.0, highspy.kHighsInf)
    for i in range(T):
        for j in range(i + 1, T): rows.append(sec_row([i, j]))
    print(json.dumps(dict(trails=T, options=NO, arcs=NA, emax=EMAX, cols=ncol, rows=len(rows), E0=E0,
                          build_sec=round(time.time() - t0, 1))), flush=True)
    h = highspy.Highs(); h.setOptionValue("output_flag", True); h.setOptionValue("log_to_console", True)
    h.setOptionValue("mip_rel_gap", 0.0); h.setOptionValue("threads", TH)
    if CUT is not None: h.setOptionValue("objective_bound", CUT)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows)
    lp.col_cost_ = cost; lp.col_lower_ = lower; lp.col_upper_ = upper
    lp.row_lower_ = np.array([r[2] for r in rows]); lp.row_upper_ = np.array([r[3] for r in rows])
    st = [0]; ix = []; vl = []
    for r in rows: ix += r[0]; vl += r[1]; st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(st, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(vl)
    lp.integrality_ = [highspy.HighsVarType.kInteger if integ[c] else highspy.HighsVarType.kContinuous for c in range(ncol)]
    h.passModel(lp)
    it = 0
    while True:
        it += 1
        h.setOptionValue("time_limit", TL)
        h.run()
        info = h.getInfo(); status = h.modelStatusToString(h.getModelStatus())
        sol = np.array(h.getSolution().col_value)
        obj = info.objective_function_value; bound = info.mip_dual_bound
        # decode: chosen options, successor relation at trail level
        if len(sol) < ncol: print(json.dumps(dict(result="no solution", status=status))); return
        ys = [o for o in range(NO) if sol[cy + o] > 0.5]
        succ = {}
        for i, (a, b, e) in enumerate(arcs):
            if sol[cz + i] > 0.5: succ[opts[a][0]] = (opts[b][0], "z", e)
        for (ta, tb), c in fidx.items():
            if sol[c] > 0.5: succ[ta] = (tb, "F", None)
        first = [opts[o][0] for o in range(NO) if sol[cs + o] > 0.5]
        order = []; cur = first[0] if first else None; seen = set()
        while cur is not None and cur not in seen:
            order.append(cur); seen.add(cur); cur = succ.get(cur, (None,))[0]
        rest = [t for t in range(T) if t not in seen]
        print(json.dumps(dict(iter=it, status=status, obj=obj, dual_bound=bound, J_lower=77 + bound if bound is not None else None,
                              path_trails=len(order), outside=len(rest), sec=round(time.time() - t0, 1))), flush=True)
        if status == "Infeasible":
            print(json.dumps(dict(result="no solution below cutoff", cutoff=CUT, emax=EMAX,
                                  claim="min sum e >= %d, every single-opening word has J >= %d" % (int(-(-CUT // 1)), 77 + int(-(-CUT // 1))),
                                  sec=round(time.time() - t0, 1))), flush=True)
            return
        if status not in ("Optimal",) and len(order) < T and not rest:
            break
        if rest:
            # add SECs for every cycle among the remaining trails (connected by succ)
            comps = []; left = set(rest)
            while left:
                x = left.pop(); comp = [x]; y_ = succ.get(x, (None,))[0]
                while y_ is not None and y_ in left: comp.append(y_); left.discard(y_); y_ = succ.get(y_, (None,))[0]
                comps.append(comp)
            for comp in comps:
                r = sec_row(comp)
                h.addRow(r[2], r[3], len(r[0]), np.array(r[0], dtype=np.int32), np.array(r[1]))
            print(json.dumps(dict(added_secs=len(comps), sizes=[len(c) for c in comps])), flush=True)
            continue
        break
    # rebuild the route for the found order with exact cuts and measure it
    if len(order) == T:
        v, pth = TOE.evaluate(layers, const, order, True)
        meas = TOE.build(fam, pth)
        print(json.dumps(dict(result="path", order=order, mip_obj=obj, dual_bound=bound, J_mip_lower=77 + bound,
                              exact_value_of_order=v, measured=meas, status=status, sec=round(time.time() - t0, 1))), flush=True)

if __name__ == "__main__":
    main()
