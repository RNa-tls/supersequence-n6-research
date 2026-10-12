#!/usr/bin/env python3
"""CP-SAT feasibility: is there a route on the chain set with weight <= T-1?  (uncertified, used as an
independent exact attempt).  Arcs: chain->chain arcs not removed by the certified root reduced-cost
fixing (valid for weight <= T-1 solutions), plus a multi-visit depot (node 0) that models both the path
ends and the no-overlap links: depot->b costs n-3 (a 'jump'), a->depot costs 0; objective - (n-3)."""
import sys, os, json, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model
word, certf, T, tl, workers = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
w, n = load_word(word); ch = chains_from_word(w, n); M = Model(ch, n)
fixed0 = set(json.load(open(certf))["root"]["fixed0"]) if certf != "-" else set()
m = cp_model.CpModel(); arcs = []; obj = []
for j, (a, b, wt) in enumerate(M.arcs):
    if a < M.q and b < M.q and j not in fixed0:
        v = m.NewBoolVar(""); arcs.append((a + 1, b + 1, v)); obj.append(wt * v)
for b in range(M.q):
    v = m.NewBoolVar(""); arcs.append((0, b + 1, v)); obj.append((n - 3) * v)
    v = m.NewBoolVar(""); arcs.append((b + 1, 0, v))
m.AddMultipleCircuit(arcs)
m.Add(sum(obj) - (n - 3) <= T - 1)
m.Minimize(sum(obj))
sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
sv.parameters.linearization_level = 2
t0 = time.time(); st = sv.Solve(m)
res = dict(status=sv.StatusName(st), arcs=len(arcs), T=T, sec=round(time.time() - t0, 1))
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE): res.update(weight=sv.ObjectiveValue() - (n - 3), length=M.BASE + sv.ObjectiveValue() - (n - 3))
res["bound_weight"] = sv.BestObjectiveBound() - (n - 3)
print(json.dumps(res), flush=True)
