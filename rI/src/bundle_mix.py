#!/usr/bin/env python3
"""Feasible mixes of A- and B-bundles in the {0,7}-system of n = 8: for each (nA, nB), is there a
packing of nA disjoint A-images and nB disjoint B-images?  Reports feasibility, saving 7nA+3nB,
the number of trails (nA + nB + free phi-cycles) and the estimate L ~ 46204 - saving + loss, and
stores one packing per feasible mix as relabelling lists for routing."""
import sys, os, json, itertools
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_pack import bundle_Cset, cyc_canon
n = 8
shapes = {s["word"]: s for s in json.load(open(sys.argv[1]))}
others = list(range(1, n - 1))
ground = sorted({cyc_canon(list(p)) for p in itertools.permutations(others)}); gid = {C: i for i, C in enumerate(ground)}
def images(sh):
    Cset, _ = bundle_Cset(n, sh["word"], tuple(sh["pair"]))
    src = [x for x in range(n) if x not in sh["pair"]]
    out = {}
    for img in itertools.permutations(others):
        mp = dict(zip(src, img))
        key = frozenset(gid[cyc_canon([mp[x] for x in C])] for C in Cset)
        out.setdefault(key, img)
    return out
IA = images(shapes["S3 S4 S3 S4 X4"]); IB = images(shapes["S2 S2 S2 S3 X3"])
KA, KB = list(IA), list(IB)
res = []
for nA in range(0, 7):
    for nB in range(0, 11):
        if 16 * nA + 12 * nB > 120: continue
        m = cp_model.CpModel(); xa = [m.NewBoolVar("") for _ in KA]; xb = [m.NewBoolVar("") for _ in KB]
        for c in range(120):
            m.Add(sum(xa[i] for i, I in enumerate(KA) if c in I) + sum(xb[i] for i, I in enumerate(KB) if c in I) <= 1)
        m.Add(sum(xa) == nA); m.Add(sum(xb) == nB)
        sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 60; sv.parameters.num_workers = 1
        st = sv.StatusName(sv.Solve(m))
        free = 120 - 16 * nA - 12 * nB
        r = dict(nA=nA, nB=nB, status=st, saving=7 * nA + 3 * nB, trails=nA + nB + free)
        if st in ("OPTIMAL", "FEASIBLE"):
            r["packing"] = dict(A=[IA[KA[i]] for i in range(len(KA)) if sv.Value(xa[i])], B=[IB[KB[i]] for i in range(len(KB)) if sv.Value(xb[i])])
        res.append(r)
        if st in ("OPTIMAL", "FEASIBLE", "INFEASIBLE"):
            print(json.dumps({k: v for k, v in r.items() if k != "packing"}), flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "bundle_mix_n8.json"), "w"))
