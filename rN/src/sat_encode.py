#!/usr/bin/env python3
"""Round N (section 14) -- CNF encoding of
    "exists a single-opening word of the 6A+24phi family with  [c0 = 2] + sum_b min(e_b, 3) <= B"
(J = 77 + [c0=2] + sum e, so B = 22 encodes J <= 99; counting e >= 3 as 3 makes the CNF a
relaxation: UNSAT proves every single-opening word has J >= 77 + B + 1).
Variables: x_o (option of trail T), s_TU (U follows T), b_T / f_T (first / last), p_Tk (position),
q_oo' (arc o -> o' with e <= 2 used), d^k_TU (boundary T->U has relaxed excess >= k, k = 1,2,3),
d0 (first option is an F-step cut).  Positions forbid subtours.  Cardinality by a totalizer.
Optional symmetry breaking (--sym GROUP.json): the first trail is the smallest member of its
orbit and, if the group contains a version-swapping element fixing it, uses version 0.
usage: sat_encode.py FAMILY.json E.npy B OUT.cnf [--sym GROUP.json] [--keep DOM.json]"""
import sys, os, json, argparse
import numpy as np
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def bitot(lits, ub, pool, cnf):
    """bidirectional totalizer: returns outputs o[0..m-1] with o[j] <-> (sum(lits) >= j+1), m = min(len, ub)"""
    def build(ls):
        if len(ls) == 1: return [ls[0]]
        mid = len(ls) // 2
        A = build(ls[:mid]); Bq = build(ls[mid:])
        m = min(len(A) + len(Bq), ub)
        bitot.counter += 1
        R = [pool.id(("tot", bitot.counter, j)) for j in range(m)]
        p, q = len(A), len(Bq)
        for i in range(0, p + 1):
            for j in range(0, q + 1):
                k = i + j
                if 1 <= k <= m:          # a_i & b_j -> r_k
                    cl = [R[k - 1]]
                    if i > 0: cl.append(-A[i - 1])
                    if j > 0: cl.append(-Bq[j - 1])
                    cnf.append(cl)
                if k + 1 <= m:           # r_{k+1} -> a_{i+1} | b_{j+1}
                    cl = [-R[k]]
                    if i < p: cl.append(A[i])
                    if j < q: cl.append(Bq[j])
                    cnf.append(cl)
        return R
    return build(list(lits))
bitot.counter = 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("family"); ap.add_argument("E"); ap.add_argument("B", type=int); ap.add_argument("out")
    ap.add_argument("--sym"); ap.add_argument("--keep")
    ap.add_argument("--bridge", help="dir with tau1_A<a>.npy: add redundant A-bridge clauses (cut-charge, tau1 >= 2 pairs)")
    ap.add_argument("--pc", help="JSON {component: [trails], pc: [PC(1), PC(2), ...]} redundant path-cover constraints")
    a = ap.parse_args()
    fam, opts = OP.load(a.family); E = np.load(a.E)
    keep = set(json.load(open(a.keep))["keep"]) if a.keep else set(range(len(opts)))
    T = len(fam["trails"]); tr = [o["t"] for o in opts]
    pool = IDPool(); cnf = CNF()
    X = {o: pool.id(("x", o)) for o in keep}
    S = {(t, u): pool.id(("s", t, u)) for t in range(T) for u in range(T) if t != u}
    Bv = {t: pool.id(("b", t)) for t in range(T)}; Fv = {t: pool.id(("f", t)) for t in range(T)}
    P = {(t, k): pool.id(("p", t, k)) for t in range(T) for k in range(T)}
    def exactly_one(lits):
        enc = CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter)
        cnf.extend(enc.clauses)
    by_trail = {t: [o for o in keep if tr[o] == t] for t in range(T)}
    for t in range(T): exactly_one([X[o] for o in by_trail[t]])
    for t in range(T):
        exactly_one([S[(t, u)] for u in range(T) if u != t] + [Fv[t]])
        exactly_one([S[(u, t)] for u in range(T) if u != t] + [Bv[t]])
        exactly_one([P[(t, k)] for k in range(T)])
    for k in range(T): exactly_one([P[(t, k)] for t in range(T)])
    for t in range(T):
        cnf.append([-Bv[t], P[(t, 0)]]); cnf.append([Bv[t], -P[(t, 0)]])
        cnf.append([-Fv[t], P[(t, T - 1)]]); cnf.append([Fv[t], -P[(t, T - 1)]])
    for (t, u), sv in S.items():
        cnf.append([-sv, -P[(t, T - 1)]])
        for k in range(T - 1): cnf.append([-sv, -P[(t, k)], P[(u, k + 1)]])
    # arcs
    ids = sorted(keep); idx = np.array(ids)
    Esub = E[np.ix_(idx, idx)]
    ii, jj = np.nonzero(Esub <= 2)
    Q = {}; cheap = {}
    for i, j in zip(ii.tolist(), jj.tolist()):
        o, o2 = ids[i], ids[j]
        if tr[o] == tr[o2]: continue
        e = int(Esub[i, j]); q = pool.id(("q", o, o2)); Q[(o, o2)] = (q, e)
        cnf.append([-q, X[o]]); cnf.append([-q, X[o2]]); cnf.append([-q, S[(tr[o], tr[o2])]])
        cheap.setdefault((tr[o], tr[o2]), []).append((q, e))
    D = {}
    cost_lits = []
    for (t, u), sv in S.items():
        lst = cheap.get((t, u), [])
        for k in (1, 2, 3):
            d = pool.id(("d", t, u, k)); D[(t, u, k)] = d; cost_lits.append(d)
            cnf.append([-sv, d] + [q for (q, e) in lst if e < k])
        cnf.append([-D[(t, u, 3)], D[(t, u, 2)]]); cnf.append([-D[(t, u, 2)], D[(t, u, 1)]])
        cnf.append([-D[(t, u, 1)], sv])     # cost only on used boundaries
    d0 = pool.id(("d0",)); cost_lits.append(d0)
    for o in keep:
        if opts[o]["cut"] == 2: cnf.append([-Bv[tr[o]], -X[o], d0])
    if a.sym:
        G = json.load(open(a.sym))
        reps = [min(orb) for orb in G["trail_orbits"]]
        cnf.append([Bv[r] for r in reps])
        # version 0 for the first trail when a group element fixes it and swaps its versions
        for r in reps:
            swaps = any(ta[str(r)][0] == r and va[str(r)][0] == 1 for ta, va in zip(G["trail_action"], G["version_action"]))
            if swaps:
                for o in by_trail[r]:
                    if opts[o]["v"] == 1: cnf.append([-Bv[r], -X[o]])
    nred = 0
    if a.bridge:
        phi_ids = [i for i, o in enumerate(opts) if o["m"] == 42]
        tp = np.array([tr[i] for i in phi_ids])
        phis = sorted(set(tp.tolist()))
        for A_t in sorted({tr[i] for i, o in enumerate(opts) if o["m"] == 672}):
            tauA = np.load(os.path.join(a.bridge, "tau1_A%d.npy" % A_t)).astype(np.int16)
            for t in phis:
                rows = tp == t
                for u in phis:
                    if u == t: continue
                    m = int(tauA[np.ix_(rows, tp == u)].min())
                    st, su = S[(t, A_t)], S[(A_t, u)]
                    # min over options of e(t->A) + e(A->u) >= m  (m >= 1 always: cut-charge lemma)
                    if m >= 1: cnf.append([-st, -su, D[(t, A_t, 1)], D[(A_t, u, 1)]]); nred += 1
                    if m >= 2:
                        cnf.append([-st, -su, D[(t, A_t, 1)], D[(A_t, u, 2)]]); cnf.append([-st, -su, D[(t, A_t, 2)], D[(A_t, u, 1)]]); nred += 2
                    if m >= 3:
                        cnf.append([-st, -su, D[(t, A_t, 1)], D[(A_t, u, 3)]]); cnf.append([-st, -su, D[(t, A_t, 3)], D[(A_t, u, 1)]])
                        cnf.append([-st, -su, D[(t, A_t, 2)], D[(A_t, u, 2)]]); nred += 3
    runcount_outputs = []
    if a.pc:
        spec = json.load(open(a.pc))
        for Xc, pcv in zip(spec["components"], spec["pc"]):
            ys = []
            for t in Xc:
                y = pool.id(("runstart", t)); ys.append(y)
                preds = [S[(u, t)] for u in Xc if u != t]
                # y <-> no predecessor inside X
                cnf.append([y] + preds)
                for p_ in preds: cnf.append([-y, -p_])
            ilits = [D[(t, u, k)] for t in Xc for u in Xc if t != u for k in (1, 2, 3)]
            oy = bitot(ys, len(ys), pool, cnf); oi = bitot(ilits, max(pcv) + 1, pool, cnf)
            runcount_outputs.append(oy)
            # oy[j] <-> (#run starts in X >= j+1), oi[j] <-> (internal relaxed cost >= j+1)
            for c, need in enumerate(pcv, start=1):
                if need <= 0: continue
                cl = ([oy[c]] if c < len(oy) else []) + [oi[need - 1]]
                cnf.append(cl); nred += 1
    enc = CardEnc.atmost(lits=cost_lits, bound=a.B, vpool=pool, encoding=EncType.totalizer)
    cnf.extend(enc.clauses)
    cnf.to_file(a.out)
    meta = dict(vars=pool.top, clauses=len(cnf.clauses), q=len(Q), options=len(keep), B=a.B, sym=bool(a.sym), redundant=nred)
    json.dump(dict(meta=meta, varmap={"x": {str(o): v for o, v in X.items()}, "s": {"%d_%d" % k: v for k, v in S.items()},
                                     "b": {str(t): v for t, v in Bv.items()}, "runcount": runcount_outputs}), open(a.out + ".map.json", "w"))
    print(json.dumps(meta))

if __name__ == "__main__":
    main()
