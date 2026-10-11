#!/usr/bin/env python3
"""Exact lower bound for the chain-level ATSP (same model as chain_atsp.py).
Sparse arcs: every pair with overlap >= 1 (cost c <= n-1), weight c - 3 (c = 2 -> -1).
Arcs with no overlap (c = n) are replaced EXACTLY by a hub (OR-tools AddMultipleCircuit depot 0):
depot -> b costs n - 3, a -> depot costs 0; objective - (n - 3) for the free path start.
Exactness: a real route maps to a hub solution of equal cost; conversely the segments of a hub
solution can be chained in any order with real join cost <= n - 3 each, so optima coincide."""
import sys, os, json, math, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
from chain_atsp import chains_of
path, tl, workers = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
w, n = load(path); out, info = analyse(w, n)
chs = chains_of(info, n); q = len(chs)
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
byprefix = {}
for b, (t, _, _) in enumerate(chs):
    for j in range(1, n): byprefix.setdefault(t[:j], []).append(b)
m = cp_model.CpModel(); arcs = []; obj = []; lits = {}
for a, (_, e, _) in enumerate(chs):
    seen = set()
    for j in range(n - 1, 0, -1):
        for b in byprefix.get(e[n - j:], []):
            if b == a or b in seen: continue
            seen.add(b)
            c = cost(e, chs[b][0], n)
            v = m.NewBoolVar(""); arcs.append((a + 1, b + 1, v)); obj.append((c - 3) * v); lits[(a, b)] = (v, c)
for b in range(q):
    v = m.NewBoolVar(""); arcs.append((0, b + 1, v)); obj.append((n - 3) * v)
    v = m.NewBoolVar(""); arcs.append((b + 1, 0, v))
m.AddMultipleCircuit(arcs)
m.Minimize(sum(obj) - (n - 3))
# hint: the original route order (chains in route order)
for (a, b), (v, c) in lits.items(): m.AddHint(v, 1 if b == a + 1 else 0)
sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
sv.parameters.log_search_progress = False
t0 = time.time(); st = sv.Solve(m)
base = CONST - ORB + q
print(json.dumps(dict(status=sv.StatusName(st), arcs=len(arcs), objective=sv.ObjectiveValue(), bound=sv.BestObjectiveBound(),
                      length_found=base + int(round(sv.ObjectiveValue())), length_lower_bound=base + math.ceil(sv.BestObjectiveBound() - 1e-9),
                      sec=round(time.time() - t0, 1))), flush=True)
