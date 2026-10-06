#!/usr/bin/env python3
"""Completion = spanning Berge hypertree (Theorem H of COMPLETION_REPORT, sec. H).
Contract all kernel-visible classes (with the kernel rows) to one root vertex r.  Candidate block B
(non-kernel, <= 1 kernel-visible class) -> hyperedge N(B) on U + {r}, |N(B)| = n-1.
Completion exists  <=>  a set X of candidates, |X| = |U|/(n-2), whose incidence graph is a tree
                   <=>  X Berge-acyclic and |X| = |U|/(n-2)  (then it spans and is connected).
Solver: CP-SAT master with
   x_B in {0,1}, sum x = |U|/(n-2), every u in U covered,
   static 2-cycle conflicts  x_B + x_B' <= 1  if |N(B) & N(B')| >= 2,
   lazy Berge-cycle cuts     sum_{B in C} x_B <= |C| - 1  for cycles found in master solutions;
iterate until an acyclic solution (certified by an independent union-find forest check) or INFEASIBLE.
INFEASIBLE with the cuts added is a genuine non-completability result (each cut is valid)."""
import sys, os, json, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World

R = -1   # root vertex id


def hyperedges(W, A):
    Us = set(A["U"]); vis = A["vis"]
    H = {}
    for b in A["cand"]:
        cl = W.bcls[b]
        e = frozenset(c if c in Us else R for c in cl)
        if len(e) == W.n - 1: H[b] = e          # (blocks with 2 kernel classes are not candidates)
    return H


def find_cycles(H, X):
    """union-find over incidence graph; return list of block-sets of cycles found greedily."""
    par = {}
    def f(a):
        while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
        return a
    adj = {}                       # incidence adjacency for path recovery
    cycles = []
    for b in X:
        vs = list(H[b])
        roots = [f(("v", v)) for v in vs]
        if len(set(roots)) < len(roots):
            # cycle: find two vertices of b already connected; recover block path via BFS in current forest
            seen = {}
            for v in vs:
                rt = f(("v", v))
                if rt in seen:
                    path = bfs_path(adj, ("v", seen[rt]), ("v", v))
                    blocks = {p[1] for p in path if p[0] == "b"} | {b}
                    cycles.append(frozenset(blocks))
                    break
                seen[rt] = v
            continue                      # do not add b (keep a forest)
        node = ("b", b); par[node] = node
        for v in vs:
            par[f(("v", v))] = f(node)
            adj.setdefault(node, []).append(("v", v)); adj.setdefault(("v", v), []).append(node)
    return cycles


def bfs_path(adj, s, t):
    from collections import deque
    prev = {s: None}; q = deque([s])
    while q:
        a = q.popleft()
        if a == t: break
        for b in adj.get(a, []):
            if b not in prev: prev[b] = a; q.append(b)
    path = []; a = t
    while a is not None: path.append(a); a = prev[a]
    return path


def is_spanning_tree(H, X, U):
    par = {}
    def f(a):
        while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
        return a
    for b in X:
        for v in H[b]:
            ra, rb = f(("b", b)), f(("v", v))
            if ra == rb: return False, "cycle"
            par[ra] = rb
    nodes = [("b", b) for b in X] + [("v", v) for v in list(U) + [R]]
    roots = {f(x) for x in nodes}
    return (len(roots) == 1), f"components {len(roots)}"


def solve(W, A, tl_total, workers=4, verbose=True, max_iter=10**6):
    n = W.n; U = A["U"]; H = hyperedges(W, A)
    if len(U) % (n - 2): return "NOT_DIVISIBLE", None, {}
    P = len(U) // (n - 2)
    cand = sorted(H)
    m = cp_model.CpModel()
    x = {b: m.NewBoolVar(f"x{b}") for b in cand}
    m.Add(sum(x.values()) == P)
    byv = {}
    for b in cand:
        for v in H[b]: byv.setdefault(v, []).append(b)
    for u in U:
        if u not in byv: return "INFEASIBLE_ORPHAN", None, {}
        m.AddBoolOr([x[b] for b in byv[u]])
    # static 2-cycle conflicts
    npair = 0
    for v, bl in byv.items():
        for i in range(len(bl)):
            for j in range(i + 1, len(bl)):
                b1, b2 = bl[i], bl[j]
                if b1 < b2 and len(H[b1] & H[b2]) >= 2 and min(H[b1] & H[b2]) == v:
                    m.Add(x[b1] + x[b2] <= 1); npair += 1
                elif b2 < b1 and len(H[b1] & H[b2]) >= 2 and min(H[b1] & H[b2]) == v:
                    m.Add(x[b1] + x[b2] <= 1); npair += 1
    t0 = time.time(); it = 0; ncuts = 0; seen_cuts = set()
    while time.time() - t0 < tl_total and it < max_iter:
        it += 1
        sv = cp_model.CpSolver(); sv.parameters.num_workers = workers
        sv.parameters.max_time_in_seconds = max(1.0, tl_total - (time.time() - t0))
        st = sv.Solve(m)
        if st == cp_model.INFEASIBLE:
            return "INFEASIBLE", None, dict(iterations=it, cuts=ncuts, pair_conflicts=npair, seconds=round(time.time() - t0, 1))
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return "UNKNOWN_" + sv.StatusName(st), None, dict(iterations=it, cuts=ncuts, pair_conflicts=npair, seconds=round(time.time() - t0, 1))
        X = [b for b in cand if sv.Value(x[b])]
        cyc = find_cycles(H, X)
        if not cyc:
            ok, why = is_spanning_tree(H, X, U)
            return ("COMPLETION" if ok else "BUG_" + why), X, dict(iterations=it, cuts=ncuts, pair_conflicts=npair,
                                                                  seconds=round(time.time() - t0, 1))
        new = 0
        for C in cyc:
            if C in seen_cuts: continue
            seen_cuts.add(C); m.Add(sum(x[b] for b in C) <= len(C) - 1); new += 1
        ncuts += new
        m.ClearHints()
        for b in cand: m.AddHint(x[b], 1 if b in X else 0)
        if verbose and it % 5 == 0:
            print(f"    iter {it}: cycles found {len(cyc)}, cuts total {ncuts}, sizes {sorted(len(c) for c in cyc)[:8]}", flush=True)
    return "UNKNOWN_TIME", None, dict(iterations=it, cuts=ncuts, pair_conflicts=npair, seconds=round(time.time() - t0, 1))


if __name__ == "__main__":
    tl = float(sys.argv[1]); worlds = {}
    for job in sys.argv[2:]:
        n, spec = int(job.split("/")[0]), job.split("/")[1]
        W = worlds.setdefault(n, World(n)); rows = kernel_rows(n, spec)
        A = analyse(W, rows); k = len(rows); G = sum(n - 1 - r[1] for r in rows)
        st, X, info = solve(W, A, tl)
        line = dict(n=n, kernel=spec[:40], score=k - G, status=st, **info)
        if X:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from flowsat import verify
            ok, why = verify(W, rows, X, n); line.update(forest_check=ok)
            json.dump(dict(n=n, kernel=spec, rows=[[list(r[0]), r[1], list(r[2])] for r in rows],
                           payload=[[list(W.blocks[b][0]), W.blocks[b][1]] for b in X]),
                      open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs",
                                        f"ht_completion_{n}_{spec.replace(':', '_')[:40]}.json"), "w"))
        print(json.dumps(line), flush=True)
