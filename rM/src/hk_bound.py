#!/usr/bin/env python3
"""Round M -- Held-Karp (assignment + subtour elimination) LP lower bound for the RUN-LEVEL ATSP of a
fixed-start r = 0 family (runatsp.py), with a safe dual certificate.

Graph: depot 0 + runs 1..N; arcs i -> j (i != j) cost W[i, j] (2..8), depot arcs cost 0.
LP:  min c x,  x(delta+(v)) = x(delta-(v)) = 1  (all v),  x(delta+(S)) >= 1 (S a set of runs,
     1 <= |S| <= N - 1),  x >= 0.   Every Hamiltonian path of runs is feasible, so
     L >= 35288 + LP  and  J >= ceil(LP) - 10797.
The LP is solved on the arcs of weight <= WMAX; the dual solution (u_v, v_v, y_S >= 0) is then
checked against ALL N^2 arcs; the reported bound is the dual objective minus the total negative
reduced cost (each x_ij <= 1 in any feasible solution), so it is valid even if the restricted LP
missed an arc or HiGHS is inexact.  Duals and cut sets are written to a certificate (checked by
hk_check.py).
usage: hk_bound.py WORD [WMAX] [ROUNDS] [CERT.npz]"""
import sys, os, json, time
import numpy as np
import scipy.sparse as sps
from scipy.sparse.csgraph import connected_components, maximum_flow
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def separate_fractional(sol, sup, tail, head, V, N, add_cut, eps=1e-6, maxcuts=300):
    """SEC separation on the symmetrised support graph (x(delta+(S)) >= 1  <=>  x(delta(S)) >= 2 by flow
    conservation).  Arcs with x >= 1 - eps are contracted first (safe: every node keeps symmetrised
    degree 2, so moving it across a violated cut never increases the cut value); then for every
    contracted node t a max flow depot -> t (scipy, integer capacities = floor(1e6 x)) finds the
    minimum depot/t cut; the t-side of every cut of value < 2 is added.  Any set S found is a valid
    SEC (validity does not depend on the separation being exact or complete)."""
    import scipy.sparse as sps
    from scipy.sparse.csgraph import maximum_flow, breadth_first_order
    par = np.arange(V)
    def find(a):
        r = a
        while par[r] != r: r = par[r]
        while par[a] != r: par[a], a = r, par[a]
        return r
    xs = sol[sup]; ts = tail[sup]; hs = head[sup]
    for a_, b_, x in zip(ts, hs, xs):
        if x >= 1 - eps:
            ra, rb = find(a_), find(b_)
            if ra != rb: par[ra] = rb
    root = np.array([find(a_) for a_ in range(V)])
    ids, comp = np.unique(root, return_inverse=True)
    K = len(ids)
    if K <= 2: return 0
    ca, cb = comp[ts], comp[hs]; m = ca != cb
    SCALE = 10 ** 6
    capv = np.floor(xs[m] * SCALE).astype(np.int64)
    # symmetrise: cap{i,j} on both arcs
    rows = np.concatenate([ca[m], cb[m]]); cols = np.concatenate([cb[m], ca[m]]); vals = np.concatenate([capv, capv])
    G = sps.csr_matrix((vals, (rows, cols)), shape=(K, K)); G.sum_duplicates()
    G = sps.csr_matrix((G.data.astype(np.int32), G.indices, G.indptr), shape=(K, K))
    s0 = comp[0]
    found = 0; seen = set()
    order = np.random.RandomState(0).permutation(K)
    for t in order:
        if t == s0 or found >= maxcuts: continue
        f = maximum_flow(G, s0, t)
        if f.flow_value >= 2 * SCALE - 1000: continue
        R = (G - f.flow).tocsr(); R.data[R.data < 0] = 0; R.eliminate_zeros()
        side = breadth_first_order(R, s0, directed=True, return_predecessors=False)   # depot side
        dep = np.zeros(K, bool); dep[side] = True
        members = np.nonzero(~dep[comp])[0]
        members = members[members != 0]
        key = tuple(members.tolist())
        if not (1 <= len(members) <= N) or key in seen: continue
        seen.add(key); add_cut(members); found += 1
    return found

def main():
    import highspy
    word = sys.argv[1]; WMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    ROUNDS = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    cert = sys.argv[4] if len(sys.argv) > 4 else None
    t0 = time.time()
    starts = RA.starts_of_word(RA.load_word(word)); N = len(starts)
    W = RA.weight_matrix(starts).astype(np.int64)
    V = N + 1                                   # node 0 = depot
    ii, jj = np.nonzero(W <= WMAX)
    tail = np.concatenate([ii + 1, np.zeros(N, np.int64), np.arange(1, V)])
    head = np.concatenate([jj + 1, np.arange(1, V), np.zeros(N, np.int64)])
    cost = np.concatenate([W[ii, jj], np.zeros(2 * N, np.int64)]).astype(float)
    A = len(tail)
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    h.setOptionValue("solver", "ipm"); h.setOptionValue("run_crossover", "off")
    inf = highspy.kHighsInf
    # rows 0..V-1: out-degree, V..2V-1: in-degree
    h.addVars(A, np.zeros(A), np.full(A, inf))
    h.changeColsCost(A, np.arange(A, dtype=np.int32), cost)
    rows_idx = [];
    M_out = sps.csr_matrix((np.ones(A), (tail, np.arange(A))), shape=(V, A))
    M_in = sps.csr_matrix((np.ones(A), (head, np.arange(A))), shape=(V, A))
    for Mx in (M_out, M_in):
        h.addRows(V, np.ones(V), np.ones(V), Mx.nnz, Mx.indptr[:-1].astype(np.int32), Mx.indices.astype(np.int32), Mx.data)
    cuts = []                                   # list of node arrays S (runs, 1-based ids)
    def add_cut(S):
        mask = np.zeros(V, bool); mask[S] = True
        cols = np.nonzero(mask[tail] & ~mask[head])[0]
        h.addRow(1.0, inf, len(cols), cols.astype(np.int32), np.ones(len(cols)))
        cuts.append(np.array(sorted(S), np.int64))
    log = []
    for rnd in range(ROUNDS):
        t1 = time.time(); h.run(); lp_sec = time.time() - t1
        sol = np.array(h.getSolution().col_value); obj = h.getInfo().objective_function_value
        sup = sol > 1e-6
        G = sps.csr_matrix((sol[sup], (tail[sup], head[sup])), shape=(V, V))
        ncomp, lab = connected_components(G, directed=True, connection="strong")
        added = 0
        if ncomp > 1:
            for c in range(ncomp):
                S = np.nonzero(lab == c)[0]
                if 0 in S: S = np.setdiff1d(np.arange(1, V), S)
                if 1 <= len(S) <= N - 1: add_cut(S); added += 1
        else:
            added += separate_fractional(sol, sup, tail, head, V, N, add_cut)
        log.append(dict(round=rnd, lp=obj, comps=int(ncomp), added=added, cuts=len(cuts), lp_sec=round(lp_sec, 1), sec=round(time.time() - t0, 1)))
        print(json.dumps(log[-1]), flush=True)
        if added == 0: break
    # duals and safe bound over ALL arcs
    dual = np.array(h.getSolution().row_dual)
    u = dual[:V]; v = dual[V:2 * V]; y = np.maximum(dual[2 * V:], 0.0)
    dual_obj = u.sum() + v.sum() + y.sum()
    # reduced costs for all run->run arcs: W[i,j] - u_i - v_j - sum_{S: i in S, j not in S} y_S
    Wf = W.astype(float)
    RC = Wf - u[1:, None] - v[None, 1:]
    for S, yS in zip(cuts, y):
        if yS <= 0: continue
        m = np.zeros(N, bool); m[S - 1] = True
        RC[np.ix_(m, ~m)] -= yS
    np.fill_diagonal(RC, 0.0)
    neg_runs = np.minimum(RC, 0).sum()
    # depot arcs: 0 -> j: 0 - u_0 - v_j - sum_{S: j not in S (0 never in S)} ... 0 in no S, so depot->j crosses no delta+(S)
    rc_d_out = 0.0 - u[0] - v[1:]
    # j -> 0 crosses delta+(S) for every S containing j
    ysum = np.zeros(N)
    for S, yS in zip(cuts, y): ysum[S - 1] += yS
    rc_d_in = 0.0 - u[1:] - v[0] - ysum
    neg = neg_runs + np.minimum(rc_d_out, 0).sum() + np.minimum(rc_d_in, 0).sum()
    safe = dual_obj + neg
    res = dict(word=word, N=N, wmax=WMAX, lp=log[-1]["lp"], dual_obj=dual_obj, neg_reduced=neg, safe_bound=safe,
               L_bound=35288 + int(np.ceil(safe - 1e-6)), J_bound=int(np.ceil(safe - 1e-6)) - 10797,
               cuts=len(cuts), sec=round(time.time() - t0, 1))
    print(json.dumps(res), flush=True)
    if cert:
        np.savez_compressed(cert, u=u, v=v, y=y, cut_ptr=np.cumsum([0] + [len(S) for S in cuts]),
                            cut_nodes=np.concatenate(cuts) if cuts else np.zeros(0, np.int64))

if __name__ == "__main__":
    main()
