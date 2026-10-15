#!/usr/bin/env python3
"""Round M -- A-HUB ELIMINATION v3 (per-A single blocks, exact blocks of <= 4 A-bundles).

In a single-opening word the 6 A-bundles sit in blocks between consecutive phi-cycles (or at the two
ends).  The cost of the boundaries of a block depends only on the phi options o (before) and o'
(after) and on the A options inside the block; minimising over the A options EXACTLY (with the
consistency "an A is entered and left at the same option") gives transfer costs
   tau1(o,o') = min_{A, a} [ e(o->a) + e(a->o') ]                       (block of one A)
   tau2(o,o') = min_{A != A', a, a'} [ e(o->a) + e(a->a') + e(a'->o') ]  (block of two A's)
   tau3+(o,o') >= Lh(o) + Rh(o'),  Lh(o) = min_a [e(o->a) + min_{a' other A} e(a->a')],
                                   Rh(o') = min_a' [min_{a other A} e(a->a') + e(a'->o')]   (>= 3 A's)
(all excesses capped at CAP = 3, a lower bound of every larger excess).  A block at the start costs
>= out_min(first phi option) (or the phi's own [cut = 2]), a block at the end >= 0.
Reduced model: a Hamiltonian path of the 24 phi-cycles (one option each, consistent), every gap is
direct (e), a 1-, 2- or >=3-A block (tau1, tau2, Lh+Rh), at most 6 A's in internal gaps.  Its optimum
is a LOWER bound on min sum_k e_k over all single-opening words (J = 77 + sum e + [cut0 = 2]).
Exact MIP (HiGHS) with lazy subtour elimination over phi-trails; also reports the LP value.
v2: tau3 (three consecutive A's) is computed through the middle option b: tau3(o,o') =
min_b [L2(o,b) + R2(b,o')], L2(o,b) = min_{A != B(b), a} e(o->a) + e(a->b), R2(b,o') =
min_{C != B(b), c} e(b->c) + e(c->o') (A = C allowed: still a lower bound); blocks of >= 4 A's cost
>= min_b L2(o,b) + min_b' R2(b',o'); a block at the START costs >= min(S1(o), min_b R2(b,o)) with
S1(o) = min_a [cut(a)=2] + e(a->o), at the END >= min(min_a e(o->a), min_b L2(o,b)); the six A's are
used exactly (gaps + start block + end block).
v3: single-A blocks are variables PER A-bundle (each A serves at most one single block), blocks of
four A's use tau4(o,o') = min_{b,c} L2(o,b) + e(b->c) + R2(c,o') (b, c in different A's), blocks of
>= 5 A's cost >= min_c L3(o,c) + min_b R2(b,o'), L3 = L2 (x) AA.
usage: hub_reduced3.py FAMILY.json [TIME] [CUTOFF]"""
import sys, os, json, time, itertools
from collections import defaultdict, Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import single_opening_lp as SL

CAP = 3

def minplus(Ms, kmax):
    """min-plus product of a chain of small-integer matrices (values 0..CAP), exact up to kmax;
    entries > kmax are reported as kmax + 1"""
    n0 = Ms[0].shape[0]; n1 = Ms[-1].shape[1]
    res = np.full((n0, n1), kmax + 1, np.int8)
    for k in range(kmax, -1, -1):
        acc = np.zeros((n0, n1), bool)
        for split in itertools.product(range(k + 1), repeat=len(Ms)):
            if sum(split) != k: continue
            P = (Ms[0] <= split[0]).astype(np.float32)
            for M, s in zip(Ms[1:], split[1:]): P = (P @ (M <= s).astype(np.float32) > 0.5).astype(np.float32)
            acc |= P > 0.5
        res[acc] = k
    return res

def main():
    import highspy
    fam = json.load(open(sys.argv[1])); TL = float(sys.argv[2]) if len(sys.argv) > 2 else 3600
    CUT = float(sys.argv[3]) if len(sys.argv) > 3 else None
    t0 = time.time()
    layers, const, opts, trail_opts, arcs = SL.build(fam, 2)
    T = len(layers)
    Atr = [t for t in range(T) if len(layers[t]) > 100]; Ph = [t for t in range(T) if t not in Atr]
    po = [o for t in Ph for o in trail_opts[t]]; pidx = {o: i for i, o in enumerate(po)}
    ao = {A: trail_opts[A] for A in Atr}; aidx = {A: {o: i for i, o in enumerate(ao[A])} for A in Atr}
    trA = {o: opts[o][0] for o in range(len(opts))}
    NP = len(po)
    In = {A: np.full((NP, len(ao[A])), CAP, np.int8) for A in Atr}
    Out = {A: np.full((len(ao[A]), NP), CAP, np.int8) for A in Atr}
    AA = {(A, B): np.full((len(ao[A]), len(ao[B])), CAP, np.int8) for A in Atr for B in Atr if A != B}
    D = {}                                                     # direct phi->phi arcs (o, o') -> e
    for (a, b, e) in arcs:
        ta, tb = trA[a], trA[b]
        if ta in Ph and tb in Ph: D[(pidx[a], pidx[b])] = e
        elif ta in Ph and tb in Atr: In[tb][pidx[a], aidx[tb][b]] = min(In[tb][pidx[a], aidx[tb][b]], e)
        elif ta in Atr and tb in Ph: Out[ta][aidx[ta][a], pidx[b]] = min(Out[ta][aidx[ta][a], pidx[b]], e)
        else: AA[ta, tb][aidx[ta][a], aidx[tb][b]] = min(AA[ta, tb][aidx[ta][a], aidx[tb][b]], e)
    KM = 2
    tau1 = np.full((NP, NP), KM + 1, np.int8); tau1A = {}
    for A in Atr:
        tau1A[A] = minplus([In[A], Out[A]], KM); tau1 = np.minimum(tau1, tau1A[A])
    tau2 = np.full((NP, NP), KM + 1, np.int8)
    for A in Atr:
        for B in Atr:
            if A != B: tau2 = np.minimum(tau2, minplus([In[A], AA[A, B], Out[B]], KM))
    # L2(o, b) over all A options b (stacked by A), R2(b, o')
    aoff = {}; off = 0
    for A in Atr: aoff[A] = off; off += len(ao[A])
    NAo = off
    L2 = np.full((NP, NAo), KM + 1, np.int8); R2 = np.full((NAo, NP), KM + 1, np.int8)
    for B in Atr:
        lb = np.full((NP, len(ao[B])), KM + 1, np.int8); rb = np.full((len(ao[B]), NP), KM + 1, np.int8)
        for A in Atr:
            if A == B: continue
            lb = np.minimum(lb, minplus([In[A], AA[A, B]], KM))
            rb = np.minimum(rb, minplus([AA[B, A], Out[A]], KM))
        L2[:, aoff[B]:aoff[B] + len(ao[B])] = lb; R2[aoff[B]:aoff[B] + len(ao[B]), :] = rb
    tau3 = minplus([L2, R2], KM)
    AAall = np.full((NAo, NAo), KM + 1, np.int8)
    for (A_, B_), M_ in AA.items():
        AAall[aoff[A_]:aoff[A_] + len(ao[A_]), aoff[B_]:aoff[B_] + len(ao[B_])] = np.minimum(M_, KM + 1)
    tau4 = minplus([L2, AAall, R2], KM)
    L3 = minplus([L2, AAall], KM)
    L3min = L3.min(axis=1).astype(np.int64)
    L2min = L2.min(axis=1).astype(np.int64); R2min = R2.min(axis=0).astype(np.int64)
    acut = {A: np.array([1 if opts[o][3] == 2 else 0 for o in ao[A]], np.int8) for A in Atr}
    S1 = np.min(np.stack([(acut[A][:, None] + Out[A]).min(axis=0) for A in Atr]), axis=0).astype(np.int64)
    E1 = np.min(np.stack([In[A].min(axis=1) for A in Atr]), axis=0).astype(np.int64)
    startA = np.minimum(S1, R2min); endA = np.minimum(E1, L2min)
    aaout = {A: np.min(np.stack([AA[A, B].min(axis=1) for B in Atr if B != A]), axis=0) for A in Atr}
    aain = {B: np.min(np.stack([AA[A, B].min(axis=0) for A in Atr if A != B]), axis=0) for B in Atr}
    Lh = np.min(np.stack([(In[A] + aaout[A][None, :]).min(axis=1) for A in Atr]), axis=0)
    Rh = np.min(np.stack([(aain[A][:, None] + Out[A]).min(axis=0) for A in Atr]), axis=0)
    outmin = np.min(np.stack([Out[A].min(axis=0) for A in Atr]), axis=0)
    cut2 = np.array([1 if opts[o][3] == 2 else 0 for o in po])
    startc = np.minimum(cut2, outmin)
    print(json.dumps(dict(phi_options=NP, direct_arcs=len(D), tau1=dict(Counter(tau1.ravel().tolist())),
                          tau2=dict(Counter(tau2.ravel().tolist())), tau3=dict(Counter(tau3.ravel().tolist())),
                          tau4=dict(Counter(tau4.ravel().tolist())), L3min=dict(Counter(L3min.tolist())),
                          L2min=dict(Counter(L2min.tolist())), R2min=dict(Counter(R2min.tolist())),
                          startA=dict(Counter(startA.tolist())), endA=dict(Counter(endA.tolist())),
                          sec=round(time.time() - t0, 1))), flush=True)
    # ---------------- MIP ----------------
    ptr = [opts[o][0] for o in po]; P = len(Ph); tpos = {t: i for i, t in enumerate(Ph)}
    tr_of = [tpos[t] for t in ptr]
    topts = defaultdict(list)
    for i, t in enumerate(tr_of): topts[t].append(i)
    same = lambda i, j: tr_of[i] == tr_of[j]
    arcsD = [(i, j, e) for (i, j), e in D.items() if not same(i, j)]
    arcs1 = [(i, j, int(tau1A[A][i, j]), A) for A in Atr for i, j in zip(*np.nonzero(tau1A[A] <= KM)) if not same(i, j)]
    arcs4 = [(i, j, int(tau4[i, j])) for i, j in zip(*np.nonzero(tau4 <= KM)) if not same(i, j)]
    arcs2 = [(i, j, int(tau2[i, j])) for i, j in zip(*np.nonzero(tau2 <= KM)) if not same(i, j)]
    arcs3 = [(i, j, int(tau3[i, j])) for i, j in zip(*np.nonzero(tau3 <= KM)) if not same(i, j)]
    pairs = [(a, b) for a in range(P) for b in range(P) if a != b]
    cols = []                                                  # (kind, data, cost, nA)
    def add(kind, data, cost, nA=0): cols.append((kind, data, cost, nA)); return len(cols) - 1
    cy = [add("y", i, 0.0) for i in range(NP)]
    cD = [add("D", (i, j), e) for (i, j, e) in arcsD]
    c1 = [add("S1", (i, j, A), e, 1) for (i, j, e, A) in arcs1]
    c4 = [add("S4", (i, j), e, 4) for (i, j, e) in arcs4]
    c2 = [add("S2", (i, j), e, 2) for (i, j, e) in arcs2]
    c3 = [add("S3", (i, j), e, 3) for (i, j, e) in arcs3]
    # trail-level else variables: direct-else (3), S1/S2/S3-else (3; 1/2/3 A's), S4 hub (L2min + R2min, >= 4 A's)
    cFD = {p: add("FD", p, float(CAP)) for p in pairs}
    cF1A = {(p, A): add("F1", p + (A,), float(KM + 1), 1) for p in pairs for A in Atr}
    cF1 = {p: None for p in pairs}
    cF2 = {p: add("F2", p, float(KM + 1), 2) for p in pairs}
    cF3 = {p: add("F3", p, float(KM + 1), 3) for p in pairs}
    cF4 = {p: add("F4", p, float(KM + 1), 4) for p in pairs}
    cF5 = {p: add("F5", p, 0.0, 5) for p in pairs}
    KINDS = ("D", "1", "2", "3", "4", "5")
    ch = {k: [add("h" + k, i, (float(L3min[i]) if k == "5" else 0.0)) for i in range(NP)] for k in KINDS}
    cr = {k: [add("r" + k, i, (float(R2min[i]) if k == "5" else 0.0)) for i in range(NP)] for k in KINDS}
    # start / end: plain phi (cost [cut=2] / 0) or an A-block (cost startA / endA)
    cs = [add("s", i, float(cut2[i])) for i in range(NP)]
    csA = [add("sA", i, float(startA[i])) for i in range(NP)]
    ct = [add("t", i, 0.0) for i in range(NP)]
    ctA = [add("tA", i, float(endA[i])) for i in range(NP)]
    nAs = add("nAs", 0, 0.0); nAe = add("nAe", 0, 0.0)          # numbers of A's in the end blocks
    cX = {p: add("X", p, 0.0) for p in pairs}
    cG = {p: add("G", p, 0.0) for p in pairs}
    cGD = [add("GD", t, 0.0) for t in range(P)]
    ncol = len(cols)
    rows_i, rows_j, rows_v, lo, hi = [], [], [], [], []
    def row(entries, l, u):
        r = len(lo)
        for c, v in entries: rows_i.append(r); rows_j.append(c); rows_v.append(v)
        lo.append(l); hi.append(u)
    for t in range(P): row([(cy[i], 1.0) for i in topts[t]], 1.0, 1.0)
    outs = defaultdict(list); ins = defaultdict(list); bypair = defaultdict(list)
    for lst, cc in ((arcsD, cD), ([(i, j, e) for (i, j, e, A) in arcs1], c1), (arcs2, c2), (arcs3, c3), (arcs4, c4)):
        for (i, j, e), c in zip(lst, cc):
            outs[i].append(c); ins[j].append(c); bypair[tr_of[i], tr_of[j]].append(c)
    for i in range(NP):
        row([(c, 1.0) for c in outs[i]] + [(ch[k][i], 1.0) for k in ch] + [(ct[i], 1.0), (ctA[i], 1.0), (cy[i], -1.0)], 0.0, 0.0)
        row([(c, 1.0) for c in ins[i]] + [(cr[k][i], 1.0) for k in cr] + [(cs[i], 1.0), (csA[i], 1.0), (cy[i], -1.0)], 0.0, 0.0)
    Fk = {"D": cFD, "2": cF2, "3": cF3, "4": cF4, "5": cF5}
    def fcols(k, t, u):
        return [cF1A[((t, u), A)] for A in Atr] if k == "1" else [Fk[k][(t, u)]]
    for k in KINDS:
        for t in range(P):
            row([(ch[k][i], 1.0) for i in topts[t]] + [(c, -1.0) for u in range(P) if u != t for c in fcols(k, t, u)], 0.0, 0.0)
            row([(cr[k][i], 1.0) for i in topts[t]] + [(c, -1.0) for u in range(P) if u != t for c in fcols(k, u, t)], 0.0, 0.0)
    # every A-bundle serves at most one single-A block
    for A in Atr:
        row([(c, 1.0) for (i, j, e, A2), c in zip(arcs1, c1) if A2 == A] + [(cF1A[(p, A)], 1.0) for p in pairs], 0.0, 1.0)
    row([(c, 1.0) for c in cs + csA], 1.0, 1.0); row([(c, 1.0) for c in ct + ctA], 1.0, 1.0)
    # end-block A counts: 1 <= nAs <= 6 iff the start block exists
    row([(nAs, 1.0)] + [(c, -1.0) for c in csA], 0.0, np.inf); row([(nAs, 1.0)] + [(c, -6.0) for c in csA], -np.inf, 0.0)
    row([(nAe, 1.0)] + [(c, -1.0) for c in ctA], 0.0, np.inf); row([(nAe, 1.0)] + [(c, -6.0) for c in ctA], -np.inf, 0.0)
    for p in pairs:
        row([(c, 1.0) for c in bypair[p]] + [(Fk[k][p], 1.0) for k in Fk] + [(cF1A[(p, A)], 1.0) for A in Atr] + [(cX[p], -1.0)], 0.0, 0.0)
    # A budget: gaps (>= 4 counted as at least 4) + end blocks = 6 exactly; F4 uses 4..6 A's
    row([(c, float(cols[c][3])) for c in range(ncol) if cols[c][3] > 0] + [(nAs, 1.0), (nAe, 1.0)], 0.0, 6.0)
    row([(c, float(cols[c][3])) for c in range(ncol) if cols[c][3] > 0 and cols[c][3] < 5] + [(nAs, 1.0), (nAe, 1.0)]
        + [(c, 6.0) for c in range(ncol) if cols[c][3] >= 5], 6.0, np.inf)
    def sec(S):
        S = set(S); e_ = [(cX[(a, b)], 1.0) for (a, b) in pairs if a in S and b not in S]
        for t in S: e_ += [(ct[i], 1.0) for i in topts[t]] + [(ctA[i], 1.0) for i in topts[t]]
        return e_
    for a in range(P):
        for b in range(a + 1, P): row(sec([a, b]), 1.0, np.inf)
    for t in range(P):                       # Gavish-Graves flow over phi-trails
        row([(cG[(u, t)], 1.0) for u in range(P) if u != t] + [(cGD[t], 1.0)] + [(cG[(t, u)], -1.0) for u in range(P) if u != t], 1.0, 1.0)
    row([(c, 1.0) for c in cGD], float(P), float(P))
    for p in pairs: row([(cG[p], 1.0), (cX[p], -(P - 1.0))], -np.inf, 0.0)
    for t in range(P): row([(cGD[t], 1.0)] + [(cs[i], -float(P)) for i in topts[t]] + [(csA[i], -float(P)) for i in topts[t]], -np.inf, 0.0)
    import scipy.sparse as sps
    Am = sps.csr_matrix((rows_v, (rows_i, rows_j)), shape=(len(lo), ncol))
    h = highspy.Highs(); h.setOptionValue("output_flag", True); h.setOptionValue("log_to_console", True)
    h.setOptionValue("mip_rel_gap", 0.0)
    if CUT is not None: h.setOptionValue("objective_bound", CUT)
    inf = highspy.kHighsInf
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = Am.shape[0]
    lp.col_cost_ = np.array([c[2] for c in cols]); lp.col_lower_ = np.zeros(ncol)
    lp.col_upper_ = np.array([float(P) if c[0] in ("G", "GD") else (6.0 if c[0] in ("nAs", "nAe") else 1.0) for c in cols])
    lp.row_lower_ = np.array([-inf if x == -np.inf else x for x in lo]); lp.row_upper_ = np.array([inf if x == np.inf else x for x in hi])
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = Am.indptr.astype(np.int32); lp.a_matrix_.index_ = Am.indices.astype(np.int32); lp.a_matrix_.value_ = Am.data
    integer = {"y", "D", "S1", "S2", "S3", "S4", "FD", "F1", "F2", "F3", "F4", "F5", "X", "nAs", "nAe", "s", "sA", "t", "tA"}
    lp.integrality_ = [highspy.HighsVarType.kInteger if c[0] in integer else highspy.HighsVarType.kContinuous for c in cols]
    h.passModel(lp)
    print(json.dumps(dict(cols=ncol, rows=Am.shape[0], direct=len(arcsD), s1=len(arcs1), s2=len(arcs2), build_sec=round(time.time() - t0, 1))), flush=True)
    it = 0
    while True:
        it += 1; h.setOptionValue("time_limit", TL); h.run()
        st = h.modelStatusToString(h.getModelStatus()); info = h.getInfo()
        print(json.dumps(dict(iter=it, status=st, obj=info.objective_function_value, bound=info.mip_dual_bound,
                              sec=round(time.time() - t0, 1))), flush=True)
        if st == "Infeasible":
            print(json.dumps(dict(result="no solution below cutoff", cutoff=CUT, claim="min sum e >= %g" % CUT)), flush=True); return
        sol = np.array(h.getSolution().col_value)
        if len(sol) < ncol: return
        if os.environ.get("HUB_DUMP"):
            # decode the incumbent: phi successor, gap type, options
            gap = {}
            for c, (kind, data, cost, nA) in enumerate(cols):
                if sol[c] > 0.5 and kind in ("D", "S1", "S2", "S3", "S4"):
                    i, j = data[0], data[1]; gap[tr_of[i]] = (tr_of[j], kind, int(i), int(j))
                if sol[c] > 0.5 and kind in ("FD", "F1", "F2", "F3", "F4", "F5"):
                    a_, b_ = data[0], data[1]; gap[a_] = (b_, kind, None, None)
            chosen = {tr_of[i]: int(i) for i in range(NP) if sol[cy[i]] > 0.5}
            first = [tr_of[i] for i in range(NP) if sol[cs[i]] > 0.5]
            dump = dict(obj=info.objective_function_value, first=first, chosen={Ph[t]: [opts[po[i]][4], opts[po[i]][5]] for t, i in chosen.items()},
                        gaps={Ph[t]: [Ph[v[0]], v[1]] for t, v in gap.items()})
            json.dump(dump, open(os.environ["HUB_DUMP"], "w"))
            print(json.dumps(dict(dumped=os.environ["HUB_DUMP"])), flush=True)
            return
        succ = {}
        for p, c in cX.items():
            if sol[c] > 0.5: succ[p[0]] = p[1]
        first = [tr_of[i] for i in range(NP) if sol[cs[i]] > 0.5 or sol[csA[i]] > 0.5][0]
        seen = [first]
        while seen[-1] in succ and succ[seen[-1]] not in seen: seen.append(succ[seen[-1]])
        rest = [t for t in range(P) if t not in seen]
        if not rest:
            print(json.dumps(dict(result="optimal path", obj=info.objective_function_value, bound=info.mip_dual_bound,
                                  J_lower=77 + int(np.ceil(info.mip_dual_bound - 1e-6)), order=[Ph[t] for t in seen], status=st)), flush=True)
            return
        left = set(rest); comps = []
        while left:
            x = left.pop(); comp = [x]; y = succ.get(x)
            while y is not None and y in left: comp.append(y); left.discard(y); y = succ.get(y)
            comps.append(comp)
        for comp in comps:
            e_ = sec(comp); h.addRow(1.0, inf, len(e_), np.array([c for c, v in e_], dtype=np.int32), np.array([v for c, v in e_]))
        print(json.dumps(dict(added=len(comps), sizes=[len(c) for c in comps])), flush=True)

if __name__ == "__main__":
    main()
