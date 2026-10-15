#!/usr/bin/env python3
"""Round M -- LP relaxation of the single-opening model (single_opening_mip.py) with EXACT
trail-level subtour separation, and a safe dual certificate.

Same columns / rows as the MIP (integrality dropped).  Subtour cuts: for every nonempty trail set S,
X(delta+(S)) + t(S) >= 1 (X = trail-level arc flows, t = flow to the path end); separated exactly
by max-flow on the 31-node trail graph (30 trails + depot) after every LP solve.
Safe bound (all columns in [0, 1]): sum_r dual_r * rhs_r + sum_c min(rc_c, 0), rc = c - A^T dual,
with duals of >= rows clipped at 0; every single-opening word gives a feasible 0/1 point of cost
<= its sum of excesses, so  J >= 77 + ceil(bound).
usage: single_opening_lp.py FAMILY.json [EMAX] [ROUNDS] [CERT.npz]"""
import sys, os, json, time, itertools
from collections import defaultdict
import numpy as np
import scipy.sparse as sps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE

def build(fam, EMAX):
    layers, const = TOE.load_layers(fam)
    T = len(layers)
    opts = []; by_entry = defaultdict(list); trail_opts = [[] for _ in range(T)]
    for t, L in enumerate(layers):
        for o in L:
            j = len(opts); opts.append((t,) + o); by_entry[o[0]].append(j); trail_opts[t].append(j)
    arcs = []
    for a, (t, entry, ex, cut, v, k) in enumerate(opts):
        for w in range(2, EMAX + 5):
            for perm in itertools.permutations(ex[:w]):
                y = ex[w:] + perm
                if TOE.wt(ex, y) != w: continue
                for b in by_entry.get(y, []):
                    if opts[b][0] == t: continue
                    e = w - opts[b][3] - 1
                    if e <= EMAX: arcs.append((a, b, e))
    return layers, const, opts, trail_opts, arcs

def main():
    import highspy
    fam = json.load(open(sys.argv[1])); EMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    ROUNDS = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    cert = sys.argv[4] if len(sys.argv) > 4 else None
    t0 = time.time()
    layers, const, opts, trail_opts, arcs = build(fam, EMAX)
    T = len(layers); NO = len(opts); NA = len(arcs)
    pairs = [(i, j) for i in range(T) for j in range(T) if i != j]; NF = len(pairs)
    cy = 0; cz = cy + NO; ch = cz + NA; cr = ch + NO; cs = cr + NO; ct = cs + NO; cf = ct + NO; cx = cf + NF; ncol = cx + NF
    cost = np.zeros(ncol)
    cost[cz:cz + NA] = [e for (a, b, e) in arcs]
    cost[cs:cs + NO] = [1.0 if opts[o][3] == 2 else 0.0 for o in range(NO)]
    cost[cf:cf + NF] = EMAX + 1
    R_i = []; R_j = []; R_v = []; lo = []; hi = []
    def addrow(idx, vals, l, u):
        r = len(lo); R_i.extend([r] * len(idx)); R_j.extend(idx); R_v.extend(vals); lo.append(l); hi.append(u)
    out_arcs = defaultdict(list); in_arcs = defaultdict(list)
    for i, (a, b, e) in enumerate(arcs): out_arcs[a].append(cz + i); in_arcs[b].append(cz + i)
    for t in range(T): addrow([cy + o for o in trail_opts[t]], [1.0] * len(trail_opts[t]), 1.0, 1.0)
    for o in range(NO):
        idx = out_arcs[o] + [ch + o, ct + o, cy + o]; addrow(idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0)
        idx = in_arcs[o] + [cr + o, cs + o, cy + o]; addrow(idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0)
    fidx = {p: cf + i for i, p in enumerate(pairs)}; xidx = {p: cx + i for i, p in enumerate(pairs)}
    for t in range(T):
        idx = [ch + o for o in trail_opts[t]] + [fidx[(t, u)] for u in range(T) if u != t]
        addrow(idx, [1.0] * len(trail_opts[t]) + [-1.0] * (T - 1), 0.0, 0.0)
        idx = [cr + o for o in trail_opts[t]] + [fidx[(u, t)] for u in range(T) if u != t]
        addrow(idx, [1.0] * len(trail_opts[t]) + [-1.0] * (T - 1), 0.0, 0.0)
    addrow([cs + o for o in range(NO)], [1.0] * NO, 1.0, 1.0)
    addrow([ct + o for o in range(NO)], [1.0] * NO, 1.0, 1.0)
    by_pair = defaultdict(list)
    for i, (a, b, e) in enumerate(arcs): by_pair[opts[a][0], opts[b][0]].append(cz + i)
    for p in pairs:
        idx = by_pair[p] + [fidx[p], xidx[p]]; addrow(idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0)
    nbase = len(lo)
    cuts = []
    def sec(S):
        Sset = set(S); idx = [c for (ta, tb), c in xidx.items() if ta in Sset and tb not in Sset]
        for t in S: idx += [ct + o for o in trail_opts[t]]
        return idx
    for i in range(T):
        for j in range(i + 1, T):
            addrow(sec([i, j]), [1.0] * len(sec([i, j])), 1.0, np.inf); cuts.append([i, j])
    A = sps.csr_matrix((R_v, (R_i, R_j)), shape=(len(lo), ncol))
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    h.setOptionValue("solver", "ipm"); h.setOptionValue("run_crossover", "off")
    inf = highspy.kHighsInf
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = A.shape[0]
    lp.col_cost_ = cost; lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.ones(ncol)
    lp.row_lower_ = np.array(lo); lp.row_upper_ = np.array([inf if x == np.inf else x for x in hi])
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = A.indptr.astype(np.int32); lp.a_matrix_.index_ = A.indices.astype(np.int32); lp.a_matrix_.value_ = A.data
    h.passModel(lp)
    print(json.dumps(dict(options=NO, arcs=NA, cols=ncol, rows=A.shape[0], build_sec=round(time.time() - t0, 1))), flush=True)
    from scipy.sparse.csgraph import maximum_flow, breadth_first_order
    for rnd in range(ROUNDS):
        t1 = time.time(); h.run()
        obj = h.getInfo().objective_function_value; sol = np.array(h.getSolution().col_value)
        # trail graph with depot D = T: capacities X, s, t (scaled)
        SC = 10 ** 6
        cap = np.zeros((T + 1, T + 1))
        for (i, j), c in xidx.items(): cap[i, j] += sol[c]
        for t in range(T):
            cap[T, t] += sum(sol[cs + o] for o in trail_opts[t]); cap[t, T] += sum(sol[ct + o] for o in trail_opts[t])
        G = sps.csr_matrix(np.floor(cap * SC).astype(np.int32))
        new = []; seen = set()
        for t in range(T):
            f = maximum_flow(G, t, T)
            if f.flow_value < SC - 100:
                Rg = (G - f.flow).tocsr(); Rg.data[Rg.data < 0] = 0; Rg.eliminate_zeros()
                side = breadth_first_order(Rg, t, directed=True, return_predecessors=False)
                S = sorted(int(x) for x in side if x != T)
                if tuple(S) not in seen: seen.add(tuple(S)); new.append(S)
        print(json.dumps(dict(round=rnd, lp=obj, J_lb=77 + obj, new_cuts=len(new), sizes=[len(S) for S in new][:12],
                              lp_sec=round(time.time() - t1, 1), sec=round(time.time() - t0, 1))), flush=True)
        if not new: break
        for S in new:
            idx = sec(S); h.addRow(1.0, inf, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx))); cuts.append(S)
    # safe dual bound
    dual = np.array(h.getSolution().row_dual)
    nrow = h.getNumRow()
    lo_all = np.array(lo + [1.0] * (nrow - len(lo)))
    is_ge = np.array([hh == np.inf for hh in hi] + [True] * (nrow - len(lo)))
    d = dual.copy(); d[is_ge] = np.maximum(d[is_ge], 0.0)
    # full matrix including added cuts
    Ri = list(R_i); Rj = list(R_j); Rv = list(R_v)
    for r, S in enumerate(cuts[len([1 for i in range(T) for j in range(i + 1, T)]):], start=len(lo)):
        idx = sec(S); Ri += [r] * len(idx); Rj += idx; Rv += [1.0] * len(idx)
    Af = sps.csr_matrix((Rv, (Ri, Rj)), shape=(nrow, ncol))
    rc = cost - Af.T.dot(d)
    safe = float(d.dot(lo_all) + np.minimum(rc, 0).sum())
    res = dict(emax=EMAX, lp=obj, safe_bound=safe, J_lower=77 + int(np.ceil(safe - 1e-9)), cuts=len(cuts),
               sec=round(time.time() - t0, 1))
    print(json.dumps(res), flush=True)
    if cert:
        np.save(cert.replace(".npz", "_primal.npy"), sol)
        # semantic dual layout (row order of this script): select[T], then per option (out, in),
        # hbal[T] / rbal[T] interleaved per trail, start, end, X rows over ordered pairs (i != j,
        # lexicographic), then one row per cut set (cuts list)
        o_keys = np.array([[opts[o][0], opts[o][4], opts[o][5]] for o in range(NO)])   # (trail, version, edge)
        k = 0
        d_sel = d[k:k + T]; k += T
        d_oi = d[k:k + 2 * NO].reshape(NO, 2); k += 2 * NO
        d_bal = d[k:k + 2 * T].reshape(T, 2); k += 2 * T
        d_start, d_end = d[k], d[k + 1]; k += 2
        d_X = d[k:k + NF]; k += NF
        d_cut = d[k:]
        assert len(d_cut) == len(cuts)
        np.savez_compressed(cert, emax=EMAX, option_keys=o_keys, d_sel=d_sel, d_out=d_oi[:, 0], d_in=d_oi[:, 1],
                            d_hbal=d_bal[:, 0], d_rbal=d_bal[:, 1], d_start=d_start, d_end=d_end, d_X=d_X,
                            pairs=np.array(pairs), d_cut=d_cut, cuts_ptr=np.cumsum([0] + [len(S) for S in cuts]),
                            cuts=np.concatenate([np.array(S) for S in cuts]), safe_bound=safe)

if __name__ == "__main__":
    main()
