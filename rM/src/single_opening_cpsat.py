#!/usr/bin/env python3
"""Round M -- the single-opening model (see single_opening_mip.py) with OR-tools CP-SAT:
trail-level AddCircuit (30 trails + depot) handles subtour elimination exactly; option literals
y_o (exactly one per trail), arc literals z_a for enumerated arcs (excess e <= EMAX, z_a => y_o,
y_o', X[T,T']), else literals g[T,T'] of cost EMAX + 1 (a lower bound of every non-enumerated
boundary), X[T,T'] = sum z + g.  Objective = sum e z + (EMAX+1) sum g + [cut = 2] on the first piece;
J >= 77 + objective bound.  Proven optimum = 23 would show: every single-opening word of the family
has J >= 100.
usage: single_opening_cpsat.py FAMILY.json [EMAX] [TIME] [WORKERS] [HINT_DESCRIPTION.json]"""
import sys, os, json, time, itertools
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE

def main():
    from ortools.sat.python import cp_model
    fam = json.load(open(sys.argv[1])); EMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    TL = float(sys.argv[3]) if len(sys.argv) > 3 else 3600.0
    WK = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    hint = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else None
    t0 = time.time()
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
    m = cp_model.CpModel()
    Y = [m.NewBoolVar("") for _ in opts]
    for t in range(T): m.AddExactlyOne([Y[o] for o in trail_opts[t]])
    D = T
    X = {}; lits = []
    for i in range(T):
        for j in range(T):
            if i != j: X[i, j] = m.NewBoolVar(""); lits.append((i, j, X[i, j]))
    S = {}; E_ = {}
    for t in range(T):
        S[t] = m.NewBoolVar(""); E_[t] = m.NewBoolVar(""); lits.append((D, t, S[t])); lits.append((t, D, E_[t]))
    m.AddCircuit(lits)
    by_pair = defaultdict(list); Z = []
    for (a, b, e) in arcs:
        z = m.NewBoolVar(""); Z.append(z)
        m.AddImplication(z, Y[a]); m.AddImplication(z, Y[b])
        by_pair[opts[a][0], opts[b][0]].append((z, e))
    G = {}
    for (i, j), x in X.items():
        g = m.NewBoolVar(""); G[i, j] = g
        m.Add(sum(z for z, e in by_pair[i, j]) + g == x)
    # first piece cost [cut = 2]: start literal per option
    SO = []
    for t in range(T):
        so = [m.NewBoolVar("") for _ in trail_opts[t]]
        for l, o in zip(so, trail_opts[t]): m.AddImplication(l, Y[o])
        m.Add(sum(so) == S[t])
        SO += [(l, 1 if opts[o][3] == 2 else 0) for l, o in zip(so, trail_opts[t])]
    obj = []
    for (i, j), lst in by_pair.items():
        for z, e in lst:
            if e: obj.append(e * z)
    obj += [(EMAX + 1) * g for g in G.values()]
    obj += [c * l for l, c in SO if c]
    m.Minimize(sum(obj))
    if hint is not None:
        desc = hint["description"]
        order = [d[0] for d in desc]
        chosen = {}
        for d in desc:
            t, v, k = d[0], d[1], d[2]
            for o in trail_opts[t]:
                if opts[o][4] == v and opts[o][5] == k: chosen[t] = o
        for t in range(T):
            for o in trail_opts[t]: m.AddHint(Y[o], 1 if chosen.get(t) == o else 0)
    print(json.dumps(dict(trails=T, options=len(opts), arcs=len(arcs), emax=EMAX, build_sec=round(time.time() - t0, 1))), flush=True)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TL
    solver.parameters.num_search_workers = WK
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = True
    solver.parameters.linearization_level = 2
    if len(sys.argv) > 6: solver.parameters.objective_upper_bound = float(sys.argv[6]) if hasattr(solver.parameters, "objective_upper_bound") else 0
    st = solver.Solve(m)
    res = dict(status=solver.StatusName(st), objective=solver.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
               bound=solver.BestObjectiveBound(), J_lower=77 + solver.BestObjectiveBound(), sec=round(time.time() - t0, 1))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        succ = {}
        for (i, j), x in X.items():
            if solver.Value(x): succ[i] = j
        first = [t for t in range(T) if solver.Value(S[t])][0]
        order = [first]
        while order[-1] in succ: order.append(succ[order[-1]])
        v, pth = TOE.evaluate(layers, const, order, True)
        res.update(order=order, exact_value_of_order=v, measured=TOE.build(fam, pth))
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
