#!/usr/bin/env python3
"""Round P -- CNF for  "exists a single-opening word (order + one option per trail) with
                       [c0 = 2] + sum_links min(e, CAP) <= B".
UNSAT for B = 22 proves F >= 23 for every single-opening word (sum min(e,CAP) <= sum e).

Variables
  x[o]       option o is used by its trail                 (exactly one per trail, ladder AMO)
  a[t][u]    trail u directly follows trail t               st[t] / en[t]: t first / last
  p[t][u]    t precedes u (t < u index; transitive)        -> no cycles
  c[t][u][j] link t->u is used and its capped excess >= j  (j = 1..CAP)
  s2         first option has cut 2
Support clauses (both directions):  a[t][u] & x[o] & ~c[t][u][j]  ->  OR_{o' in u: e(o,o') < j} x[o'].
Redundant: exact local triple minima  C(p,t,s)  (sum of the two capped link costs at t >= C).
Budget: totalizer over all c literals and s2, at most B.
Symmetry: first trail is an orbit representative of the trail group (orbits of the option-level group).
usage: sat_encode_p.py FAMILY.json E.npy CAP B OUT.cnf [--first T] [--fix ORDERFILE] [--norep]"""
import sys, os, json, argparse
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src"))
import options as OP


class CNF:
    def __init__(self): self.n = 0; self.cl = []
    def var(self): self.n += 1; return self.n
    def add(self, c): self.cl.append(c)
    def amo_ladder(self, lits):
        if len(lits) <= 1: return
        if len(lits) <= 6:
            for i in range(len(lits)):
                for j in range(i + 1, len(lits)): self.add([-lits[i], -lits[j]])
            return
        s = [self.var() for _ in range(len(lits) - 1)]
        for i in range(len(lits) - 1):
            self.add([-lits[i], s[i]])
            if i > 0: self.add([-s[i - 1], s[i]]); self.add([-lits[i], -s[i - 1]])
        self.add([-lits[-1], -s[-1]])
    def exactly_one(self, lits): self.add(list(lits)); self.amo_ladder(list(lits))
    def totalizer_atmost(self, lits, k):
        """sum(lits) <= k via a totalizer truncated at k+1"""
        def build(ls):
            if len(ls) == 1: return [ls[0]]
            m = len(ls) // 2; A = build(ls[:m]); Bv = build(ls[m:])
            r = min(len(A) + len(Bv), k + 1); R = [self.var() for _ in range(r)]
            for i in range(len(A) + 1):
                for j in range(len(Bv) + 1):
                    s = i + j
                    if s == 0 or s > r: continue
                    cl = [R[s - 1]]
                    if i: cl.append(-A[i - 1])
                    if j: cl.append(-Bv[j - 1])
                    self.add(cl)
            return R
        R = build(lits)
        if len(R) > k: self.add([-R[k]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fam"); ap.add_argument("E"); ap.add_argument("CAP", type=int); ap.add_argument("B", type=int); ap.add_argument("out")
    ap.add_argument("--first", type=int, default=None); ap.add_argument("--fix", default=None); ap.add_argument("--norep", action="store_true")
    ap.add_argument("--group", default=os.path.join(HERE, "..", "..", "rO", "certs", "group_options.npz"))
    A = ap.parse_args()
    fam, opts = OP.load(A.fam)
    E = np.minimum(np.load(A.E).astype(np.int16), A.CAP)
    T = np.array([o["t"] for o in opts]); cut = np.array([o["cut"] for o in opts]); NT = 30; CAP = A.CAP
    topts = [np.nonzero(T == t)[0] for t in range(NT)]
    f = CNF()
    x = [f.var() for _ in range(len(T))]
    for t in range(NT): f.exactly_one([x[o] for o in topts[t]])
    a = {(t, u): f.var() for t in range(NT) for u in range(NT) if t != u}
    st = [f.var() for _ in range(NT)]; en = [f.var() for _ in range(NT)]
    for t in range(NT):
        f.exactly_one([st[t]] + [a[(s, t)] for s in range(NT) if s != t])
        f.exactly_one([en[t]] + [a[(t, u)] for u in range(NT) if u != t])
    f.exactly_one(st); f.exactly_one(en)
    p = {(t, u): f.var() for t in range(NT) for u in range(t + 1, NT)}
    def bef(t, u): return p[(t, u)] if t < u else -p[(u, t)]
    for t in range(NT):
        for u in range(NT):
            if u == t: continue
            f.add([-a[(t, u)], bef(t, u)])
            for w in range(NT):
                if w in (t, u): continue
                f.add([-bef(t, u), -bef(u, w), bef(t, w)])
    c = {}
    for (t, u), av in a.items():
        for j in range(1, CAP + 1):
            c[(t, u, j)] = f.var(); f.add([-c[(t, u, j)], av])
            if j > 1: f.add([-c[(t, u, j)], c[(t, u, j - 1)]])
        sub = E[np.ix_(topts[t], topts[u])]
        for j in range(1, CAP + 1):
            ok = sub < j
            for i, o in enumerate(topts[t]):
                if ok[i].all(): continue
                f.add([-av, -x[o], c[(t, u, j)]] + [x[int(topts[u][k])] for k in np.nonzero(ok[i])[0]])
            for k, o2 in enumerate(topts[u]):
                if ok[:, k].all(): continue
                f.add([-av, -x[o2], c[(t, u, j)]] + [x[int(topts[t][i])] for i in np.nonzero(ok[:, k])[0]])
    s2 = f.var()
    for t in range(NT):
        for o in topts[t]:
            if cut[o] == 2: f.add([-st[t], -x[o], s2])
    # redundant exact local triple minima on capped costs
    if not A.norep:
        In = np.full((NT, len(T)), CAP, np.int16); Out = np.full((NT, len(T)), CAP, np.int16)
        for t in range(NT):
            for q in range(NT):
                if q == t: continue
                In[q, topts[t]] = E[np.ix_(topts[q], topts[t])].min(0)
                Out[q, topts[t]] = E[np.ix_(topts[t], topts[q])].min(1)
        def cl_sum_ge(l1, l2, k):           # unary capped costs y1 = l1[1..CAP], y2: y1 + y2 >= k
            for i in range(0, k):            # y1 <= i  ->  y2 >= k - i
                kk = k - i
                cl = []
                if i + 1 <= CAP: cl.append(l1[i + 1])
                if kk <= CAP: cl.append(l2[kk])
                else: pass
                if kk > CAP and i + 1 > CAP: continue
                yield cl
        nred = 0
        for t in range(NT):
            ot = topts[t]
            for q in range(NT):
                if q == t: continue
                for s in range(NT):
                    if s in (q, t): continue
                    k = int((In[q, ot] + Out[s, ot]).min())
                    if k <= 0: continue
                    l1 = {j: c[(q, t, j)] for j in range(1, CAP + 1)}; l2 = {j: c[(t, s, j)] for j in range(1, CAP + 1)}
                    for cl in cl_sum_ge(l1, l2, k):
                        f.add([-a[(q, t)], -a[(t, s)]] + cl); nred += 1
                # start: t first, successor s: s2 + y(t,s) >= min_o [cut=2] + Out
                k = None
            for s in range(NT):
                if s == t: continue
                k = int(((cut[ot] == 2).astype(np.int16) + Out[s, ot]).min())
                if k <= 0: continue
                l2 = {j: c[(t, s, j)] for j in range(1, CAP + 1)}
                for i in range(0, min(k, 2)):    # s2 in {0,1}: s2 <= i -> y >= k - i
                    kk = k - i
                    if kk > CAP: continue
                    cl = [-st[t], -a[(t, s)], l2[kk]]
                    if i == 0: cl.append(s2)
                    f.add(cl); nred += 1
    # symmetry: first trail is an orbit representative
    tp = np.load(A.group)["tperm"]
    orb = list(range(NT))
    def find(z):
        while orb[z] != z: z = orb[z]
        return z
    for g in tp:
        for t in range(NT):
            r1, r2 = find(t), find(int(g[t]))
            if r1 != r2: orb[max(r1, r2)] = min(r1, r2)
    reps = sorted(set(find(t) for t in range(NT)))
    if A.first is not None: f.add([st[A.first]])
    elif not A.fix: f.add([st[r] for r in reps])
    if A.fix:
        d = json.load(open(A.fix)); order = d["order"]; optsel = d.get("options")
        f.add([st[order[0]]])
        for u, v in zip(order, order[1:]): f.add([a[(u, v)]])
        if optsel:
            for o in optsel: f.add([x[o]])
    lits = [c[k] for k in c] + [s2]
    f.totalizer_atmost(lits, A.B)
    with open(A.out, "w") as fh:
        fh.write("p cnf %d %d\n" % (f.n, len(f.cl)))
        for cl in f.cl: fh.write(" ".join(map(str, cl)) + " 0\n")
    json.dump(dict(vars=f.n, clauses=len(f.cl), reps=reps, CAP=CAP, B=A.B, x0=x[0], a_first=a[(0, 1)], st0=st[0]), open(A.out + ".map.json", "w"))
    print(json.dumps(dict(vars=f.n, clauses=len(f.cl), reps=reps)))


if __name__ == "__main__":
    main()
