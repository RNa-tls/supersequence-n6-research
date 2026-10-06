#!/usr/bin/env python3
"""Completion via exact ownership cover + single-commodity FLOW (exact cycle elimination).
Variables: x_B (candidate block chosen), own[c,B] (B owns class c of U), att[B,c] (attachment class of a
chosen block whose U-part has n-1 classes), g[c,B,B2] >= 0 = flow from owner B of class c to the block
B2 attaching at c.
  * every c in U owned exactly once; a chosen B owns exactly n-2 classes of U;
  * B with |B&U| = n-1 ("inner"): own + att = x on each U-class, exactly one attachment;
    B with |B&U| = n-2 ("rooted"): attaches at its kernel-visible class (flow supplied by the kernel);
  * g[c,B,B2] <= P*own[c,B],  sum_B g[c,B,B2] <= P*att[B2,c];
  * inner B: inflow sum_{c,B'} g[c,B',B] = x_B + outflow sum_{c,B2} g[c,B,B2];
    rooted B: no inflow constraint (kernel supplies).
Theorem (report C4): feasible <=> completion.  A cyclic ownership component Q (blocks attached only
inside Q) has zero inflow but must absorb |Q| units: impossible.  Conversely a completion forest
supports the flow 'subtree size'."""
import sys, os, json, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World


def solve(W, A, tl, workers=4, seed=0, hint=None):
    n = W.n; U = A["U"]; Us = set(U); cand = A["cand"]
    P = len(U) // (n - 2)
    m = cp_model.CpModel()
    x = {b: m.NewBoolVar("") for b in cand}
    own = {}; att = {}; inner = {}
    for b in cand:
        cu = [c for c in W.bcls[b] if c in Us]
        inner[b] = len(cu) == n - 1
        for c in cu:
            own[c, b] = m.NewBoolVar(""); m.AddImplication(own[c, b], x[b])
        m.Add(sum(own[c, b] for c in cu) == (n - 2) * x[b])
        if inner[b]:
            for c in cu:
                att[b, c] = m.NewBoolVar(""); m.Add(own[c, b] + att[b, c] == x[b])
    byc = {c: [] for c in U}
    for (c, b) in own: byc[c].append(b)
    for c in U:
        if not byc[c]: return "INFEASIBLE_ORPHAN", None
        m.AddExactlyOne(own[c, b] for b in byc[c])
    m.Add(sum(x.values()) == P)
    g = {}
    infl = {b: [] for b in cand}; outf = {b: [] for b in cand}
    for c in U:
        attachers = [b2 for b2 in byc[c] if (b2, c) in att]
        for b2 in attachers:
            col = []
            for b in byc[c]:
                if b == b2: continue
                v = m.NewIntVar(0, P, ""); g[c, b, b2] = v
                m.Add(v <= P * own[c, b]).OnlyEnforceIf(own[c, b].Not()) if False else m.Add(v <= P * own[c, b])
                col.append(v); infl[b2].append(v); outf[b].append(v)
            m.Add(sum(col) <= P * att[b2, c])
    for b in cand:
        if inner[b]:
            m.Add(sum(infl[b]) == x[b] + sum(outf[b]))
    if hint:
        for b in cand: m.AddHint(x[b], 1 if b in hint else 0)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl
    sv.parameters.num_workers = workers; sv.parameters.random_seed = seed
    st = sv.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sol = [b for b in cand if sv.Value(x[b])]
        ownership = {c: b for (c, b), v in own.items() if sv.Value(v)}
        attach = {b: c for (b, c), v in att.items() if sv.Value(v)}
        return sv.StatusName(st), dict(blocks=sol, owner=ownership, attach=attach)
    return sv.StatusName(st), None


def verify(W, rows, blocks, n):
    """independent certificate check: incidence graph (rows-visible classes, blocks-all classes) is a
    forest covering all classes with exactly len(rows) components, each containing one row."""
    vis = {}
    for i, r in enumerate(rows):
        for c in W.row_visible(r): vis[c] = i
    par = {}
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    nodes = [("r", i) for i in range(len(rows))] + [("b", b) for b in blocks] + [("c", c) for c in range(W.C)]
    for v in nodes: par[v] = v
    edges = [(("r", i), ("c", c)) for c, i in vis.items()] + [(("b", b), ("c", c)) for b in blocks for c in W.bcls[b]]
    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru == rv: return False, "cycle"
        par[ru] = rv
    comps = {find(v) for v in nodes}
    covered = all(any(True for _ in [0]) for _ in [0])
    cov = set(vis) | {c for b in blocks for c in W.bcls[b]}
    if len(cov) != W.C: return False, "uncovered"
    if len(comps) != len(rows): return False, f"components {len(comps)}"
    roots = {find(("r", i)) for i in range(len(rows))}
    if len(roots) != len(rows): return False, "two rows in one component"
    return True, "forest ok"


if __name__ == "__main__":
    tl = float(sys.argv[1]); worlds = {}
    for job in sys.argv[2:]:
        n, spec = int(job.split("/")[0]), job.split("/")[1]
        W = worlds.setdefault(n, World(n)); rows = kernel_rows(n, spec)
        A = analyse(W, rows); k = len(rows); G = sum(n - 1 - r[1] for r in rows)
        t0 = time.time(); st, sol = solve(W, A, tl)
        line = dict(n=n, kernel=spec[:40], score=k - G, status=st, seconds=round(time.time() - t0, 1))
        if sol:
            ok, why = verify(W, rows, sol["blocks"], n)
            line.update(certificate_check=ok, why=why, payload=len(sol["blocks"]))
            json.dump(dict(n=n, kernel=spec, rows=[[list(r[0]), r[1]] for r in rows],
                           payload=[[list(W.blocks[b][0]), W.blocks[b][1]] for b in sol["blocks"]]),
                      open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs",
                                        f"flow_completion_{n}_{spec.replace(':', '_')[:40]}.json"), "w"))
        print(json.dumps(line), flush=True)
