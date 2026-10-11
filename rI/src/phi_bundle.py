#!/usr/bin/env python3
"""Is the class set of a long trail of 46188 an exact union of phi-cycle class sets?
A phi-cycle is determined by a start g (any permutation): classes {class(g phi^k F^i)}, k < n-2,
i < n-1 (its special is g[n-1]).  For a target class set C we list every phi-cycle contained in C
(for every special and every start inside each block) and solve the exact cover of C by them."""
import sys, os, json
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
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
res = []
targets = [("long", classes(t)) for t in trails if len(t) == 104]
allc = frozenset(canon(S[i]) for ch in info["chains"] for i in ch)
for name, C in targets[:2] + [("ALL_LONG", frozenset().union(*[c for _, c in targets]))]:
    cand = set()
    for c in C:
        for k in range(n):
            p = c[k + 1:] + c[:k + 1]           # rotation ending in symbol c[k]
            for f in Fp:
                pc = phicyc(comp(p, f))
                if pc <= C: cand.add(pc)
    cand = list(cand)
    m = cp_model.CpModel(); x = [m.NewBoolVar("") for _ in cand]
    by = {}
    for i, pc in enumerate(cand):
        for c in pc: by.setdefault(c, []).append(x[i])
    covered = all(c in by for c in C)
    if covered:
        for c in C: m.AddExactlyOne(by[c])
        sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 300; sv.parameters.num_workers = 2
        st = sv.StatusName(sv.Solve(m))
    else: st = "SOME_CLASS_IN_NO_CONTAINED_PHI_CYCLE"
    uncovered = sum(1 for c in C if c not in by)
    res.append(dict(target=name, classes=len(C), contained_phi_cycles=len(cand), classes_not_in_any=uncovered, exact_cover=st))
    print(json.dumps(res[-1]), flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "phi_bundle46188.json"), "w"))
