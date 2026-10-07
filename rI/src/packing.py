#!/usr/bin/env python3
"""Exact-partition packing (sec. 11-12): tile the cyclic classes of S_n by left translates g*C of
closed trail shapes C (syllable words from syllable_search.py) and phi-cycles, minimizing
Phi_core = sum over chosen trails of (chains + 1)  (each closed trail opened once).
Then  L >= CONST - ORB - 1 + Phi_core,  with equality iff the trails can be linked by cost-4 joins.
Translates are deduplicated as class sets; the trail data (start, word) of each is kept for the
route reconstruction."""
import sys, os, json, itertools, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))

def setup(n):
    I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
    Fp = [I]
    for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
    BAC, CBA = (1, 0, n - 1), (n - 1, 1, 0)
    T = {s: tuple(list(range(2, n - 1)) + list(s)) for s in (BAC, CBA)}
    syl = {}
    for r in range(0, n - 2):
        syl[f"S{r}"] = [(n - 3, BAC)] + [(n - 1, BAC)] * r
        if n - 4 >= 1: syl[f"X{r}"] = [(n - 3, CBA), (n - 2, BAC), (n - 1, CBA), (n - 4, BAC)] + [(n - 1, BAC)] * r
    syl["PHI"] = [(n - 1, BAC)]
    return I, Fp, T, syl

def canon(p):
    k = p.index(0); return p[k:] + p[:k]

def closed_letters(n, word, I, Fp, T, syl):
    letters = [x for s in word.split() for x in syl[s]]
    step = lambda l, s: comp(Fp[l - 1], T[s])
    Pi = I
    for l, s in letters: Pi = comp(Pi, step(l, s))
    m = 1; X = Pi
    while X != I: X = comp(X, Pi); m += 1
    return letters * m

def shape(n, letters, I, Fp, T):
    """relative chain starts and the class list (as position perms) of the closed trail from I."""
    P = I; starts = []; cl = []
    for l, s in letters:
        starts.append((P, l))
        for j in range(l): cl.append(comp(P, Fp[j]))
        P = comp(P, comp(Fp[l - 1], T[s]))
    assert P == I
    return starts, cl

def build(n, words):
    I, Fp, T, syl = setup(n)
    perms = list(itertools.permutations(range(n)))
    cls_id = {}
    for p in perms:
        c = canon(p)
        if c not in cls_id: cls_id[c] = len(cls_id)
    cands = {}      # frozenset(class ids) -> (cost, word, g)
    for wd in words:
        letters = closed_letters(n, wd, I, Fp, T, syl)
        starts, cl = shape(n, letters, I, Fp, T)
        assert len({canon(c) for c in cl}) == len(cl), "shape not valid"
        cost = len(letters) + 1
        for g in perms:
            key = frozenset(cls_id[canon(comp(g, c))] for c in cl)
            if key not in cands or cands[key][0] > cost: cands[key] = (cost, wd, g)
    if os.environ.get("FILL") == "1":       # single-chain trails (open), cost 2, any block arc
        for g in perms:
            for l in range(1, n):
                key = frozenset(cls_id[canon(comp(g, Fp[j]))] for j in range(l))
                if key not in cands: cands[key] = (2, f"CHAIN{l}", g)
    return cls_id, cands, (I, Fp, T, syl)

def solve(n, cands, ncls, tl, workers=3, hint=None):
    m = cp_model.CpModel(); keys = list(cands)
    x = [m.NewBoolVar("") for _ in keys]
    cover = [[] for _ in range(ncls)]
    for i, k in enumerate(keys):
        for c in k: cover[c].append(x[i])
    for c in range(ncls): m.AddExactlyOne(cover[c])
    if os.environ.get("NONPHI") == "1":
        m.Add(sum(x[i] for i, k in enumerate(keys) if cands[k][1] not in ("PHI",) and not cands[k][1].startswith("CHAIN")) >= 1)
    m.Minimize(sum(cands[k][0] * x[i] for i, k in enumerate(keys)))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    st = sv.Solve(m)
    sol = [keys[i] for i in range(len(keys)) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) and sv.Value(x[i])]
    return sv.StatusName(st), (sv.ObjectiveValue() if sol else None), sv.BestObjectiveBound(), sol

if __name__ == "__main__":
    import math
    n = int(sys.argv[1]); tl = float(sys.argv[2]); words = sys.argv[3].split(",")
    t0 = time.time()
    cls_id, cands, ctx = build(n, words)
    HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    print(json.dumps(dict(n=n, words=words, candidates=len(cands), classes=len(cls_id), build_sec=round(time.time() - t0, 1))), flush=True)
    st, obj, bd, sol = solve(n, cands, len(cls_id), tl)
    out = dict(status=st, Phi_core=obj, bound=bd,
               L_if_cost4_links=None if obj is None else CONST - ORB - 1 + int(obj),
               L_lower_bound_this_shape_family=CONST - ORB - 1 + math.ceil(bd - 1e-9), f=CONST + math.factorial(n - 3) - 1,
               used=None if not sol else dict(__import__("collections").Counter(cands[k][1] for k in sol)))
    print(json.dumps(out), flush=True)
    if sol:
        json.dump(dict(n=n, trails=[dict(word=cands[k][1], g=cands[k][2]) for k in sol]),
                  open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"packing_n{n}_{int(obj)}.json"), "w"))
