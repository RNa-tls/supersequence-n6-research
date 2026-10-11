#!/usr/bin/env python3
"""Details of the phi-cycle bundles of 46188: for each long trail, all exact covers of its class set
by contained phi-cycles (enumerated), the specials of the covering phi-cycles, and whether the 96
bundle phi-cycles + the 24 free phi-cycles of the route form one partition of all 5040 classes into
120 phi-cycles of a single special (a 'phi-cycle system')."""
import sys, os, json
from collections import Counter
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def canon(t):
    k = t.index(0); return t[k:] + t[:k]
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
F = tuple(list(range(1, n - 1)) + [0, n - 1]); phi = tuple(list(range(1, n - 2)) + [0, n - 2, n - 1])
Fp = [tuple(range(n))]
for _ in range(n - 2): Fp.append(comp(Fp[-1], F))
def phicyc(g):
    cl = set(); x = g
    for _ in range(n - 2):
        for f in Fp: cl.add(canon(comp(x, f)))
        x = comp(x, phi)
    return frozenset(cl)
def classes(t): return frozenset(canon(S[i]) for ch in t for i in ch)
class SolCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, xs, cap): super().__init__(); self.xs = xs; self.sols = []; self.cap = cap
    def on_solution_callback(self):
        self.sols.append([i for i, v in enumerate(self.xs) if self.Value(v)])
        if len(self.sols) >= self.cap: self.StopSearch()
longs = [t for t in trails if len(t) == 104]
report = []
bundle_phis = []
for li, t in enumerate(longs):
    C = classes(t)
    cand = {}
    for c in C:
        for k in range(n):
            p = c[k + 1:] + c[:k + 1]
            for f in Fp:
                g = comp(p, f); pc = phicyc(g)
                if pc <= C: cand.setdefault(pc, set()).add(g[n - 1])
    keys = list(cand)
    m = cp_model.CpModel(); x = [m.NewBoolVar("") for _ in keys]
    by = {}
    for i, pc in enumerate(keys):
        for c in pc: by.setdefault(c, []).append(x[i])
    for c in C: m.AddExactlyOne(by[c])
    sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_workers = 1
    cb = SolCollector(x, 1000); sv.Solve(m, cb)
    sp_of_sol = [Counter(sorted(cand[keys[i]])[0] if len(cand[keys[i]]) == 1 else tuple(sorted(cand[keys[i]])) for i in s) for s in cb.sols]
    report.append(dict(trail=li, contained=len(keys), specials_of_contained=dict(Counter(str(sorted(v)) for v in cand.values())),
                       exact_covers=len(cb.sols), specials_per_cover=[dict((str(k), v) for k, v in d.items()) for d in sp_of_sol[:4]]))
    bundle_phis.append([keys[i] for i in cb.sols[0]])
    print(json.dumps(report[-1]), flush=True)
# free phi-cycles of the route (6-chain closed trails + glued residual)
Rinv = lambda s: s[-1:] + s[:-1]
free = [classes(t) for t in trails if len(t) == 6]
free.append(frozenset().union(*[classes(t) for t in trails if len(t) not in (6, 104)]))
free_specials = Counter(S[t[0][0]][n - 1] for t in trails if len(t) == 6)
allphis = [p for b in bundle_phis for p in b] + free
cover = Counter(c for p in allphis for c in p)
res = dict(free_phi_cycles=len(free), free_specials=dict(free_specials), total_phi_cycles=len(allphis),
           partition_of_all_classes=(len(cover) == 5040 and set(cover.values()) == {1}))
print(json.dumps(res))
json.dump(dict(report=report, global_=res), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "phi_bundle46188_detail.json"), "w"))
