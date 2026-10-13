#!/usr/bin/env python3
"""Round K -- which efficient closed trails are (generalized) bundles?
For a closed syllable trail W^m: is its class set an exact union of phi-sets P({a,b},C)
  (a) of ONE pair (a classical bundle; complement coverable by phi-cycles of that pair), or
  (b) of possibly DIFFERENT pairs (exact cover by phi-sets, CP-SAT on the trail's own classes)?
usage: bundle_test.py WORD [WORD ...]"""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trail_packing import word_info, reps, cid
n = 8
phi = {}
for a, b in itertools.combinations(range(n), 2):
    groups = {}
    for i, c in enumerate(reps):
        C = tuple(x for x in c if x not in (a, b)); kk = C.index(min(C)); C = C[kk:] + C[:kk]
        groups.setdefault(C, set()).add(i)
    phi[(a, b)] = [frozenset(v) for v in groups.values()]
from ortools.sat.python import cp_model
for w in sys.argv[1:]:
    cls, k, size, s = word_info(w)
    S = frozenset(cid[tuple(c)] for c in cls)
    single = [pr for pr, sets in phi.items() if all((P <= S) or not (P & S) for P in sets)]
    inside = [P for sets in phi.values() for P in sets if P <= S]
    m = cp_model.CpModel(); x = [m.NewBoolVar("") for _ in inside]
    for c in S: m.AddExactlyOne([x[i] for i, P in enumerate(inside) if c in P] or [m.NewConstant(0)])
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 120; st = sv.Solve(m)
    print(json.dumps(dict(word=w, classes=size, chains=k, saving=str(s), classes_mod_42=size % 42,
                          single_pair_bundle=[list(p) for p in single], phi_sets_inside=len(inside),
                          mixed_pair_union=sv.StatusName(st))), flush=True)
