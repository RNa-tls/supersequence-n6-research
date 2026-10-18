#!/usr/bin/env python3
"""Round P -- CP-SAT model of the single-opening 6A+24phi family (exploratory second prover).
Order: AddCircuit over the 30 trails + a depot (arc depot->t: t first, t->depot: t last).
Options: one-hot x[o] per trail.  Link cost: literals b[t,u,j] = 'arc t->u used and its excess >= j'
(j = 1..CAP); support clauses  arc(t,u) & x[o] & ~b[t,u,j]  ->  OR_{o' in u, e(o,o') < j} x[o'],
and the reverse direction.  Start cost: s1 = first option has cut 2.
Objective: minimise s1 + sum b  (= sum min(e, CAP) + [c0 = 2] <= true cost).  With CAP = 6 it is exact.
Redundant: for every triple (p, t, s) the exact local minimum C(p,t,s) of in+out cost at t (capped).
usage: cpsat_model.py FAMILY.json E.npy CAP time_limit workers OUT.json [ub]"""
import sys, os, json, time
import numpy as np
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rN", "src"))
import options as OP


def main():
    fam_p, E_p, CAP, tl, workers, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    ub = int(sys.argv[7]) if len(sys.argv) > 7 else None
    fam, opts = OP.load(fam_p)
    E = np.minimum(np.load(E_p).astype(np.int16), CAP)
    T = np.array([o["t"] for o in opts]); cut = np.array([o["cut"] for o in opts]); NT = 30
    topts = [np.nonzero(T == t)[0] for t in range(NT)]
    m = cp_model.CpModel()
    x = [m.NewBoolVar("x%d" % o) for o in range(len(T))]
    for t in range(NT): m.AddExactlyOne([x[o] for o in topts[t]])
    D = NT
    arc = {}
    arcs = []
    for t in range(NT):
        for u in range(NT):
            if t != u: arc[(t, u)] = m.NewBoolVar("a%d_%d" % (t, u)); arcs.append((t, u, arc[(t, u)]))
        arc[(D, t)] = m.NewBoolVar("s%d" % t); arcs.append((D, t, arc[(D, t)]))
        arc[(t, D)] = m.NewBoolVar("f%d" % t); arcs.append((t, D, arc[(t, D)]))
    m.AddCircuit(arcs)
    b = {}
    obj = []
    for t in range(NT):
        for u in range(NT):
            if t == u: continue
            sub = E[np.ix_(topts[t], topts[u])]
            for j in range(1, CAP + 1):
                bj = m.NewBoolVar("b%d_%d_%d" % (t, u, j)); b[(t, u, j)] = bj; obj.append(bj)
                m.AddImplication(bj, arc[(t, u)])
                if j > 1: m.AddImplication(bj, b[(t, u, j - 1)])
            for j in range(1, CAP + 1):
                ok = sub < j                       # pairs with excess < j
                for i, o in enumerate(topts[t]):
                    sup = [x[int(topts[u][k])] for k in np.nonzero(ok[i])[0]]
                    # arc & x[o] & ~b_j -> OR sup
                    m.AddBoolOr(sup + [arc[(t, u)].Not(), x[int(o)].Not(), b[(t, u, j)]])
                for k, o2 in enumerate(topts[u]):
                    sup = [x[int(topts[t][i])] for i in np.nonzero(ok[:, k])[0]]
                    m.AddBoolOr(sup + [arc[(t, u)].Not(), x[int(o2)].Not(), b[(t, u, j)]])
    s1 = m.NewBoolVar("start2")
    for t in range(NT):
        for o in topts[t]:
            if cut[o] == 2: m.AddBoolOr([arc[(D, t)].Not(), x[int(o)].Not(), s1])
    obj.append(s1)
    if ub is not None: m.Add(sum(obj) <= ub)
    m.Minimize(sum(obj))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    solver.parameters.num_workers = workers
    solver.parameters.log_search_progress = True
    t0 = time.time(); st = solver.Solve(m)
    res = dict(status=solver.StatusName(st), obj=solver.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
               bound=solver.BestObjectiveBound(), sec=time.time() - t0, CAP=CAP)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        nxt = {t: u for (t, u), v in arc.items() if solver.Value(v)}
        order = []; cur = nxt[D]
        while cur != D: order.append(cur); cur = nxt[cur]
        res["order"] = order
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
