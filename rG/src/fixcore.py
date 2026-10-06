#!/usr/bin/env python3
"""Why is the d=3 repair infeasible?  Re-solve the first score-15 extension with the base-forest
fixings as ASSUMPTIONS and extract a sufficient infeasible subset; then explain each core block."""
import sys, os, json
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lns5905 as L
from candcore import analyse
W, n = L.W, L.n
exts = L.extensions()
e = [x for x in exts if x[0] == "pre"][0]
rows = L.build_rows(e)
A = analyse(W, rows); U = A["U"]; Us = set(U); cand = sorted(A["cand"]); P = len(U) // (n - 2)
vis_new = set(range(W.C)) - Us
conflict = {b for b in L.pay0 if b in A["kb"] or any(c in vis_new for c in W.bcls[b])}
kept = sorted((L.pay0 - conflict))
print("kept base blocks:", len(kept), "of which candidates:", sum(1 for b in kept if b in A["cand"]))
notcand = [b for b in kept if b not in A["cand"]]
print("kept base blocks that are NOT candidates any more:", len(notcand))
for b in notcand[:5]:
    cu = [c for c in W.bcls[b] if c in Us]
    print("  block", W.blocks[b], "classes in U:", len(cu), "of", n - 1)
m = cp_model.CpModel()
x = {b: m.NewBoolVar(f"x{b}") for b in cand}
own = {}
for b in cand:
    cu = [c for c in W.bcls[b] if c in Us]
    for c in cu: own[c, b] = m.NewBoolVar(""); m.AddImplication(own[c, b], x[b])
    m.Add(sum(own[c, b] for c in cu) == (n - 2) * x[b])
byc = {c: [] for c in U}
for (c, b) in own: byc[c].append(b)
for c in U: m.AddExactlyOne(own[c, b] for b in byc[c])
m.Add(sum(x.values()) == P)
lits = [x[b] for b in kept if b in x]
m.AddAssumptions(lits)
sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 120; sv.parameters.num_workers = 1
st = sv.Solve(m)
print("ownership-only with ALL kept base blocks assumed:", sv.StatusName(st))
if st == cp_model.INFEASIBLE:
    core = sv.SufficientAssumptionsForInfeasibility()
    idx = {x[b].Index(): b for b in x}
    cb = [idx[i] for i in core if i in idx]
    print("core size:", len(cb))
    for b in cb:
        cu = [c for c in W.bcls[b] if c in Us]
        print("  core block", W.blocks[b], "|B&U| =", len(cu))
