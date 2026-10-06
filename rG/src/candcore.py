#!/usr/bin/env python3
"""Completion analysis (canonical definition, final-attack report sec. C1).
Input: kernel = trail of omission-free rows (distinct blocks, pairwise class-disjoint visible sets).
U = classes not visible in the kernel.  A completion is a set P of non-kernel blocks such that the
incidence graph (rows - their visible classes, P blocks - all their classes) is a forest with exactly
k components (one per row) covering all classes.
Facts used (proved in the report):
  (O) order-free: valid iff the final incidence graph is such a forest (BFS from rows = attachment order);
  (C) every block of P meets U in >= n-2 classes ("candidate"), owns exactly n-2 classes of U, and the
      owned sets partition U;  |P| = |U|/(n-2).
This script computes, per kernel: |U|, |P|, candidate counts by |B & U| (n-2 or n-1), candidate degree of
classes, and solves (with CP-SAT) relaxation R1 = exact ownership cover (no acyclicity), then the full
problem R2 = R1 + acyclic parent relation (depth labels)."""
import sys, os, math, json, time, itertools
from collections import Counter
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
from complete import World, kernel_from_lengths, std_kernel, canon


def analyse(W, rows):
    n = W.n
    kb = set(W.bid[(canon(r[0][:n - 1]), r[0][n - 1])] for r in rows)
    vis = set()
    for r in rows:
        for c in W.row_visible(r):
            assert c not in vis; vis.add(c)
    U = [c for c in range(W.C) if c not in vis]; Us = set(U)
    cand = [b for b in range(len(W.blocks)) if b not in kb and sum(1 for c in W.bcls[b] if c in Us) >= n - 2]
    full_u = [b for b in cand if all(c in Us for c in W.bcls[b])]
    deg = Counter()
    for b in cand:
        for c in W.bcls[b]:
            if c in Us: deg[c] += 1
    degs = [deg[c] for c in U]
    return dict(U=U, cand=cand, kb=kb, vis=vis,
                stats=dict(k=len(rows), U=len(U), P=len(U) / (n - 2), cand=len(cand),
                           cand_attach_kernel=len(cand) - len(full_u), cand_inside_U=len(full_u),
                           min_class_deg=min(degs) if degs else None,
                           zero_deg_classes=sum(1 for d in degs if d == 0),
                           deg_hist=dict(sorted(Counter(degs).items()))))


def solve(W, A, acyclic, tl, workers=4):
    n = W.n; U = A["U"]; Us = set(U); cand = A["cand"]
    if len(U) % (n - 2): return "NOT_DIVISIBLE", None
    m = cp_model.CpModel()
    x = {b: m.NewBoolVar("") for b in cand}
    own = {}
    for b in cand:
        cu = [c for c in W.bcls[b] if c in Us]
        for c in cu: own[c, b] = m.NewBoolVar(""); m.AddImplication(own[c, b], x[b])
        m.Add(sum(own[c, b] for c in cu) == (n - 2) * x[b])
    byc = {c: [] for c in U}
    for (c, b) in own: byc[c].append(own[c, b])
    for c in U:
        if not byc[c]: return "INFEASIBLE_ZERO_DEGREE", None
        m.AddExactlyOne(byc[c])
    m.Add(sum(x.values()) == len(U) // (n - 2))
    if acyclic:
        Dmax = 40
        d = {b: m.NewIntVar(1, Dmax, "") for b in cand}
        for b in cand:
            cu = [c for c in W.bcls[b] if c in Us]
            if len(cu) == n - 1:                      # attachment inside U: parent = its owner
                for c in cu:
                    for b2 in cand:
                        if b2 != b and (c, b2) in own:
                            m.Add(d[b] >= d[b2] + 1).OnlyEnforceIf([x[b], own[c, b2], own[c, b].Not()])
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    st = sv.Solve(m)
    sol = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sol = [b for b in cand if sv.Value(x[b])]
    return sv.StatusName(st), sol


def kernel_rows(n, spec):
    if spec == "std": return std_kernel(n)
    if spec.startswith("gap179:"):
        t = json.load(open(os.path.join(ROOT, "r179", "certs", "gap179.json")))[int(spec.split(":")[1])]
        return [(tuple(int(ch) for ch in s), l, ()) for s, l in t["trail"]]
    return kernel_from_lengths(n, [int(ch) for ch in spec])


if __name__ == "__main__":
    tl = float(sys.argv[1]); jobs = sys.argv[2:]
    worlds = {}
    for job in jobs:
        n, spec = int(job.split("/")[0]), job.split("/")[1]
        if n not in worlds: worlds[n] = World(n)
        W = worlds[n]; rows = kernel_rows(n, spec)
        k = len(rows); G = sum(n - 1 - r[1] for r in rows)
        A = analyse(W, rows)
        t0 = time.time(); r1, _ = solve(W, A, False, tl)
        t1 = time.time(); r2, sol = (solve(W, A, True, tl) if r1 in ("OPTIMAL", "FEASIBLE") else ("skipped", None))
        print(json.dumps(dict(n=n, kernel=spec[:30], score=k - G, **A["stats"], R1_exact_ownership=r1,
                              R1_s=round(t1 - t0, 1), R2_full=r2, R2_s=round(time.time() - t1, 1))), flush=True)
        if sol:
            json.dump(dict(n=n, kernel=spec, payload=[[list(W.blocks[b][0]), W.blocks[b][1]] for b in sol]),
                      open(os.path.join(HERE, "..", "certs", f"completion_{n}_{spec.replace(':','_')[:30]}.json"), "w"))
