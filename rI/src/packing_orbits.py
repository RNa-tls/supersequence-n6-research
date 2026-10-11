#!/usr/bin/env python3
"""All maximum packings of A-images (the 46188 long-trail shape) in the {0,7}-system of n = 8,
up to relabelling of {1..6}.  Template = long trail 0 of 46188 (pair {0,7}); an A-image is the
template relabelled by g in S_6 (acting on symbols 1..6).  Output: one representative per orbit,
as a list of 6 relabellings g (each mapping symbol i -> g[i], 0 and 7 fixed)."""
import sys, os, json, itertools
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):
    k = p.index(0); w_ = list(p[k:] + p[:k]); return cyc_canon([x for x in w_ if x not in (0, n - 1)])
tmpl = [t for t in trails if len(t) == 104][0]
CT = frozenset(Cof(S[ch[0]]) for ch in tmpl)
others = list(range(1, n - 1))
ground = sorted({cyc_canon(list(p)) for p in itertools.permutations(others)}); gid = {C: i for i, C in enumerate(ground)}
img_of = {}
for perm in itertools.permutations(others):
    g = [0] + list(perm) + [n - 1]
    key = frozenset(gid[cyc_canon([g[x] for x in C])] for C in CT)
    img_of.setdefault(key, tuple(g))
imgs = list(img_of)
class Col(cp_model.CpSolverSolutionCallback):
    def __init__(s, xs): super().__init__(); s.xs = xs; s.sols = []
    def on_solution_callback(s): s.sols.append(frozenset(i for i, v in enumerate(s.xs) if s.Value(v)))
m = cp_model.CpModel(); x = [m.NewBoolVar("") for _ in imgs]
for c in range(len(ground)): m.Add(sum(x[i] for i, I in enumerate(imgs) if c in I) <= 1)
m.Add(sum(x) == 6)
sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_workers = 1
cb = Col(x); sv.Solve(m, cb)
sols = cb.sols
# orbits under S_6 relabelling
def act(perm, I):
    g = [0] + list(perm) + [n - 1]
    return frozenset(gid[cyc_canon([g[x] for x in ground[c]])] for c in I)
imgidx = {I: i for i, I in enumerate(imgs)}
seen = set(); reps = []
for s_ in sols:
    if s_ in seen: continue
    orb = set()
    for perm in itertools.permutations(others):
        orb.add(frozenset(imgidx[act(perm, imgs[i])] for i in s_))
    seen |= orb; reps.append((s_, len(orb)))
orig = frozenset(imgidx[frozenset(gid[Cof(S[ch[0]])] for ch in t)] for t in trails if len(t) == 104)
out = dict(max_packings=len(sols), orbits=len(reps), orbit_sizes=[o for _, o in reps],
           original_orbit=[k for k, (s_, o) in enumerate(reps) if orig in {frozenset(imgidx[act(p, imgs[i])] for i in s_) for p in itertools.permutations(others)}],
           reps=[[img_of[imgs[i]] for i in sorted(s_)] for s_, _ in reps])
print(json.dumps({k: v for k, v in out.items() if k != "reps"}))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "packing_orbits_n8.json"), "w"))
