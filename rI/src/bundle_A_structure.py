#!/usr/bin/env python3
"""Structure of the A-bundle images (46188 long-trail shape) in the 120 cyclic arrangements of {1..6}:
number of distinct images, max number of pairwise disjoint images (exact), number of maximum
packings, and simple invariants that might explain the bound (complement structure of a max packing)."""
import sys, os, json, itertools
from collections import Counter
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_pack import bundle_Cset, cyc_canon
n = 8
shapes = json.load(open(sys.argv[1]))
A = [s for s in shapes if s["word"] == "S3 S4 S3 S4 X4"][0]
B = [s for s in shapes if s["word"] == "S2 S2 S2 S3 X3"][0]
others = list(range(1, n - 1))
ground = sorted({cyc_canon(list(p)) for p in itertools.permutations(others)})
gid = {C: i for i, C in enumerate(ground)}
def images(sh):
    Cset, _ = bundle_Cset(n, sh["word"], tuple(sh["pair"]))
    src = [x for x in range(n) if x not in sh["pair"]]
    out = set()
    for img in itertools.permutations(others):
        mp = dict(zip(src, img))
        out.add(frozenset(gid[cyc_canon([mp[x] for x in C])] for C in Cset))
    return list(out)
IA, IB = images(A), images(B)
class Count(cp_model.CpSolverSolutionCallback):
    def __init__(s, xs): super().__init__(); s.xs = xs; s.n = 0; s.sols = []
    def on_solution_callback(s):
        s.n += 1
        if len(s.sols) < 3: s.sols.append([i for i, v in enumerate(s.xs) if s.Value(v)])
def maxpack(imgs):
    m = cp_model.CpModel(); x = [m.NewBoolVar("") for _ in imgs]
    for c in range(120): m.Add(sum(x[i] for i, I in enumerate(imgs) if c in I) <= 1)
    m.Maximize(sum(x)); sv = cp_model.CpSolver(); sv.parameters.num_workers = 1; sv.Solve(m)
    best = int(sv.ObjectiveValue())
    m2 = cp_model.CpModel(); y = [m2.NewBoolVar("") for _ in imgs]
    for c in range(120): m2.Add(sum(y[i] for i, I in enumerate(imgs) if c in I) <= 1)
    m2.Add(sum(y) == best)
    sv2 = cp_model.CpSolver(); sv2.parameters.enumerate_all_solutions = True; sv2.parameters.num_workers = 1
    cb = Count(y); sv2.Solve(m2, cb)
    return best, cb.n, cb.sols
bA, nA, solsA = maxpack(IA); bB, nB, _ = maxpack(IB)
# arrangement parity relative to a reference reading (m = 6 even: rotation is odd, so use the
# parity of the linear word starting at symbol 1)
def par(C):
    k = C.index(1); w = C[k:] + C[:k]
    inv = sum(1 for i in range(len(w)) for j in range(i + 1, len(w)) if w[i] > w[j]); return inv % 2
parA = Counter(tuple(sorted(Counter(par(ground[c]) for c in I).items())) for I in IA)
comp_ = set(range(120)) - set().union(*[IA[i] for i in solsA[0]])
out = dict(A_images=len(IA), B_images=len(IB), max_disjoint_A=bA, number_of_max_A_packings=nA, max_disjoint_B=bB,
           number_of_max_B_packings=nB, parity_profile_of_A_images=[[list(k), v] for k, v in parA.items()],
           complement_of_a_max_A_packing_size=len(comp_), complement_parity=dict(Counter(par(ground[c]) for c in comp_)))
print(json.dumps(out))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "bundle_A_structure.json"), "w"))
