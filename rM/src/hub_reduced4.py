#!/usr/bin/env python3
"""Round M -- A-HUB ELIMINATION v4 (blocks of 1..6 A-bundles through exact chained transfer costs).

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
v4: Lk(o, x) = cheapest way from phi option o through k consecutive A's ending at A option x
(L1 = e(o -> x), Lk = L(k-1) (x) AA, consistent at every A option, A-identity repeats allowed);
tau_k = Lk (x) Out for k = 1..6 (single blocks per A as in v3); start blocks of k A's cost
min_x sigma_k(x) + e(x -> o) with sigma_1 = [cut = 2], sigma_k = sigma_(k-1) (x) AA; end blocks of k
A's cost min_x Lk(o, x); the six A's are used exactly.  No hub relaxations remain.
usage: hub_reduced4.py FAMILY.json [TIME] [CUTOFF]"""
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
    aoff = {}; off = 0
    for A in Atr: aoff[A] = off; off += len(ao[A])
    NAo = off
    AAall = np.full((NAo, NAo), KM + 1, np.int8)
    for (A_, B_), M_ in AA.items():
        AAall[aoff[A_]:aoff[A_] + len(ao[A_]), aoff[B_]:aoff[B_] + len(ao[B_])] = np.minimum(M_, KM + 1)
    InAll = np.concatenate([np.minimum(In[A], KM + 1) for A in Atr], axis=1)      # NP x NAo
    OutAll = np.concatenate([np.minimum(Out[A], KM + 1) for A in Atr], axis=0)    # NAo x NP
    acutAll = np.concatenate([np.array([1 if opts[o][3] == 2 else 0 for o in ao[A]], np.int64) for A in Atr])
    Lk = {1: InAll}; tauk = {}
    for k in range(2, 7): Lk[k] = minplus([Lk[k - 1], AAall], KM)
    for k in range(2, 7): tauk[k] = minplus([Lk[k], OutAll], KM)
    endk = {k: Lk[k].min(axis=1).astype(np.int64) for k in range(1, 7)}
    sig = acutAll.copy(); startk = {}
    for k in range(1, 7):
        startk[k] = np.min(sig[:, None] + OutAll.astype(np.int64), axis=0)
        if k < 6:
            sig = np.min(sig[:, None] + AAall.astype(np.int64), axis=0)
    cut2 = np.array([1 if opts[o][3] == 2 else 0 for o in po])
    print(json.dumps(dict(phi_options=NP, direct_arcs=len(D), tau1=dict(Counter(tau1.ravel().tolist())),
                          **{"tau%d" % k: dict(Counter(tauk[k].ravel().tolist())) for k in range(2, 7)},
                          **{"start%d" % k: dict(Counter(startk[k].tolist())) for k in range(1, 7)},
                          **{"end%d" % k: dict(Counter(endk[k].tolist())) for k in range(1, 7)},
                          sec=round(time.time() - t0, 1))), flush=True)
    # ---------------- MIP ----------------
    ptr = [opts[o][0] for o in po]; P = len(Ph); tpos = {t: i for i, t in enumerate(Ph)}
    tr_of = [tpos[t] for t in ptr]
    topts = defaultdict(list)
    for i, t in enumerate(tr_of): topts[t].append(i)
    same = lambda i, j: tr_of[i] == tr_of[j]
    arcsD = [(i, j, e) for (i, j), e in D.items() if not same(i, j)]
    arcs1 = [(i, j, int(tau1A[A][i, j]), A) for A in Atr for i, j in zip(*np.nonzero(tau1A[A] <= KM)) if not same(i, j)]
    arcsK = {k: [(i, j, int(tauk[k][i, j])) for i, j in zip(*np.nonzero(tauk[k] <= KM)) if not same(i, j)] for k in range(2, 7)}
    pairs = [(a, b) for a in range(P) for b in range(P) if a != b]
    cols = []                                                  # (kind, data, cost, nA)
    def add(kind, data, cost, nA=0): cols.append((kind, data, cost, nA)); return len(cols) - 1
    cy = [add("y", i, 0.0) for i in range(NP)]
    cD = [add("D", (i, j), e) for (i, j, e) in arcsD]
    c1 = [add("S1", (i, j, A), e, 1) for (i, j, e, A) in arcs1]
    cK = {k: [add("S%d" % k, (i, j), e, k) for (i, j, e) in arcsK[k]] for k in range(2, 7)}
    cFD = {p: add("FD", p, float(CAP)) for p in pairs}
    cF1A = {(p, A): add("F1", p + (A,), float(KM + 1), 1) for p in pairs for A in Atr}
    cFk = {k: {p: add("F%d" % k, p, float(KM + 1), k) for p in pairs} for k in range(2, 7)}
    KINDS = ("D", "1", "2", "3", "4", "5", "6")
    ch = {k: [add("h" + k, i, 0.0) for i in range(NP)] for k in KINDS}
    cr = {k: [add("r" + k, i, 0.0) for i in range(NP)] for k in KINDS}
    cs = [add("s", i, float(cut2[i])) for i in range(NP)]
    csK = {k: [add("sA", i, float(startk[k][i]), k) for i in range(NP)] for k in range(1, 7)}
    ct = [add("t", i, 0.0) for i in range(NP)]
    ctK = {k: [add("tA", i, float(endk[k][i]), k) for i in range(NP)] for k in range(1, 7)}
    csA = [c for k in range(1, 7) for c in csK[k]]; ctA = [c for k in range(1, 7) for c in ctK[k]]
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
    for lst, cc in [(arcsD, cD), ([(i, j, e) for (i, j, e, A) in arcs1], c1)] + [(arcsK[k], cK[k]) for k in range(2, 7)]:
        for (i, j, e), c in zip(lst, cc):
            outs[i].append(c); ins[j].append(c); bypair[tr_of[i], tr_of[j]].append(c)
    for i in range(NP):
        row([(c, 1.0) for c in outs[i]] + [(ch[k][i], 1.0) for k in ch] + [(ct[i], 1.0)] + [(ctK[k][i], 1.0) for k in range(1, 7)] + [(cy[i], -1.0)], 0.0, 0.0)
        row([(c, 1.0) for c in ins[i]] + [(cr[k][i], 1.0) for k in cr] + [(cs[i], 1.0)] + [(csK[k][i], 1.0) for k in range(1, 7)] + [(cy[i], -1.0)], 0.0, 0.0)
    Fk = {"D": cFD}; Fk.update({str(k): cFk[k] for k in range(2, 7)})
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
    for p in pairs:
        row([(c, 1.0) for c in bypair[p]] + [(Fk[k][p], 1.0) for k in Fk] + [(cF1A[(p, A)], 1.0) for A in Atr] + [(cX[p], -1.0)], 0.0, 0.0)
    # A budget: exactly six A's in gaps and end blocks
    row([(c, float(cols[c][3])) for c in range(ncol) if cols[c][3] > 0], 6.0, 6.0)
    def sec(S):
        S = set(S); e_ = [(cX[(a, b)], 1.0) for (a, b) in pairs if a in S and b not in S]
        for t in S: e_ += [(ct[i], 1.0) for i in topts[t]] + [(ctK[k][i], 1.0) for i in topts[t] for k in range(1, 7)]
        return e_
    for a in range(P):
        for b in range(a + 1, P): row(sec([a, b]), 1.0, np.inf)
    for t in range(P):                       # Gavish-Graves flow over phi-trails
        row([(cG[(u, t)], 1.0) for u in range(P) if u != t] + [(cGD[t], 1.0)] + [(cG[(t, u)], -1.0) for u in range(P) if u != t], 1.0, 1.0)
    row([(c, 1.0) for c in cGD], float(P), float(P))
    for p in pairs: row([(cG[p], 1.0), (cX[p], -(P - 1.0))], -np.inf, 0.0)
    for t in range(P): row([(cGD[t], 1.0)] + [(cs[i], -float(P)) for i in topts[t]] + [(csK[k][i], -float(P)) for i in topts[t] for k in range(1, 7)], -np.inf, 0.0)
    import scipy.sparse as sps
    Am = sps.csr_matrix((rows_v, (rows_i, rows_j)), shape=(len(lo), ncol))
    h = highspy.Highs(); h.setOptionValue("output_flag", True); h.setOptionValue("log_to_console", True)
    h.setOptionValue("mip_rel_gap", 0.0)
    if CUT is not None: h.setOptionValue("objective_bound", CUT)
    inf = highspy.kHighsInf
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = Am.shape[0]
    lp.col_cost_ = np.array([c[2] for c in cols]); lp.col_lower_ = np.zeros(ncol)
    lp.col_upper_ = np.array([float(P) if c[0] in ("G", "GD") else 1.0 for c in cols])
    lp.row_lower_ = np.array([-inf if x == -np.inf else x for x in lo]); lp.row_upper_ = np.array([inf if x == np.inf else x for x in hi])
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = Am.indptr.astype(np.int32); lp.a_matrix_.index_ = Am.indices.astype(np.int32); lp.a_matrix_.value_ = Am.data
    integer = {"y", "D", "S1", "S2", "S3", "S4", "S5", "S6", "FD", "F1", "F2", "F3", "F4", "F5", "F6", "X", "s", "sA", "t", "tA"}
    lp.integrality_ = [highspy.HighsVarType.kInteger if c[0] in integer else highspy.HighsVarType.kContinuous for c in cols]
    h.passModel(lp)
    print(json.dumps(dict(cols=ncol, rows=Am.shape[0], direct=len(arcsD), s1=len(arcs1), sk={k: len(arcsK[k]) for k in arcsK}, build_sec=round(time.time() - t0, 1))), flush=True)
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
                if sol[c] > 0.5 and kind in ("D", "S1", "S2", "S3", "S4", "S5", "S6"):
                    i, j = data[0], data[1]; gap[tr_of[i]] = (tr_of[j], kind, int(i), int(j))
                if sol[c] > 0.5 and kind in ("FD", "F1", "F2", "F3", "F4", "F5", "F6"):
                    a_, b_ = data[0], data[1]; gap[a_] = (b_, kind, None, None)
            chosen = {tr_of[i]: int(i) for i in range(NP) if sol[cy[i]] > 0.5}
            first = [tr_of[i] for i in range(NP) if sol[cs[i]] > 0.5 or any(sol[csK[k][i]] > 0.5 for k in range(1, 7))]
            dump = dict(obj=info.objective_function_value, first=first, chosen={Ph[t]: [opts[po[i]][4], opts[po[i]][5]] for t, i in chosen.items()},
                        gaps={Ph[t]: [Ph[v[0]], v[1]] for t, v in gap.items()})
            json.dump(dump, open(os.environ["HUB_DUMP"], "w"))
            print(json.dumps(dict(dumped=os.environ["HUB_DUMP"])), flush=True)
            return
        succ = {}
        for p, c in cX.items():
            if sol[c] > 0.5: succ[p[0]] = p[1]
        first = [tr_of[i] for i in range(NP) if sol[cs[i]] > 0.5 or any(sol[csK[k][i]] > 0.5 for k in range(1, 7))][0]
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
