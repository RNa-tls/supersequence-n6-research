#!/usr/bin/env python3
"""CP-SAT feasibility (uncertified, independent attempt) with the root-LP reduced-cost budget:
any route of weight <= T-1 satisfies  sum_j r_j x_j <= (T-1) - y.b  (weak duality identity with the
certified root dual of root_*.json).  Hub/depot arcs of the B&C model are merged into a multi-visit
depot here; their budget coefficients use min(r_D-arc, r_H-arc) (a valid relaxation)."""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model
from ortools.sat.python import cp_model
word, rootf, T, tl, workers = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
w, n = load_word(word); ch = chains_from_word(w, n); M = Model(ch, n)
Z = np.load(rootf)                    # produced by root_reduced_costs.py (exact integer root reduced costs)
r = Z["r"]; SC = int(Z["scale"][0]); budget = (T - 1) * SC - int(Z["yb"][0])
fixed0 = set(int(v) for v in Z["fixed0"])
m = cp_model.CpModel(); arcs = []; obj = []; bud = []
for j, (a, b, wt) in enumerate(M.arcs):
    if a < M.q and b < M.q and j not in fixed0:
        v = m.NewBoolVar(""); arcs.append((a + 1, b + 1, v)); obj.append(wt * v); bud.append(int(r[j]) * v)
for b in range(M.q):
    v = m.NewBoolVar(""); arcs.append((0, b + 1, v)); obj.append((n - 3) * v)
    bud.append(min(int(r[M.arc_id[(M.D, b)]]), int(r[M.arc_id[(M.H, b)]])) * v)
    v = m.NewBoolVar(""); arcs.append((b + 1, 0, v))
    bud.append(min(int(r[M.arc_id[(b, M.D)]]), int(r[M.arc_id[(b, M.H)]])) * v)
m.AddMultipleCircuit(arcs)
m.Add(sum(obj) - (n - 3) <= T - 1)
m.Add(sum(bud) <= budget)
m.Minimize(sum(obj))
sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
sv.parameters.linearization_level = 2
t0 = time.time(); st = sv.Solve(m)
res = dict(status=sv.StatusName(st), arcs=len(arcs), T=T, budget=budget / SC, sec=round(time.time() - t0, 1))
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    res.update(weight=sv.ObjectiveValue() - (n - 3), length=M.BASE + sv.ObjectiveValue() - (n - 3))
    # extract segments: successor map over chain nodes, segments start after the depot
    succ = {}; starts = []
    for (a, b, v) in arcs:
        if sv.Value(v):
            if a == 0: starts.append(b - 1)
            elif b != 0: succ[a - 1] = b - 1
    order = []
    for st0 in starts:
        x = st0
        while True:
            order.append(x)
            if x not in succ: break
            x = succ[x]
    assert sorted(order) == list(range(M.q)), "extraction failed"
    real = M.route_weight(order)
    res.update(real_weight=real, real_length=M.BASE + real)
    from chainset_model import ov_cost
    R_ = lambda s_: s_[1:] + s_[:1]; Fm = lambda s_: s_[1:n - 1] + (s_[0], s_[n - 1])
    perms = []
    for c in order:
        s0, _, l = ch[c]; x = s0
        for _ in range(l):
            p_ = x
            for _ in range(n): perms.append(p_); p_ = R_(p_)
            x = Fm(x)
    word_ = list(perms[0])
    for a_, b_ in zip(perms, perms[1:]):
        c_ = ov_cost(a_, b_, n); word_.extend(b_[n - c_:])
    outw = os.path.join(os.path.dirname(os.path.abspath(rootf)), f"cpsat_word_n{n}_{len(word_)}.txt")
    open(outw, "w").write("".join(str(v + 1) for v in word_) + "\n"); res["word_file"] = outw
print(json.dumps(res), flush=True)
