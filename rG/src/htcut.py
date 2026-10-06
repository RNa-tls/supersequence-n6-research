#!/usr/bin/env python3
"""Exact completion solver via Theorem H (spanning Berge hypertree in the root-contracted candidate
hypergraph) with generalized subtour-elimination cuts.
Valid inequalities (any completion X, any vertex set S of U+{r}):
     (n-2) * #{B in X : N(B) subset of S}  <=  |S| - 1          (forest restricted to S)
Master (CP-SAT): x_B binary, sum x = |U|/(n-2), coverage of every u, static pair conflicts
(|N(B) & N(B')| >= 2), plus lazily added S-cuts for S = vertex set of every cyclic component of the
current solution and of every detected cycle.  Terminates with
  COMPLETION  (independent union-find spanning-tree check + forest check on the original graph), or
  INFEASIBLE  (all constraints valid => no completion: a genuine non-completability proof modulo
               the solver's correctness; the added S-cuts are recorded as the certificate skeleton)."""
import sys, os, json, time
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from candcore import analyse, kernel_rows
from complete import World
from hypertree import hyperedges, find_cycles, is_spanning_tree, R


def comp_cuts(H, X, n):
    par = {}
    def f(a):
        while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
        return a
    for b in X:
        for v in H[b]:
            ra, rb = f(("v", v)), f(("b", b))
            if ra != rb: par[ra] = rb
    cb = {}; cv = {}
    for b in X:
        r = f(("b", b)); cb.setdefault(r, []).append(b)
        cv.setdefault(r, set()).update(H[b])
    out = []
    for r, bl in cb.items():
        V = cv[r]
        if (n - 2) * len(bl) > len(V) - 1: out.append(frozenset(V))
    for C in find_cycles(H, X):
        V = frozenset(v for b in C for v in H[b])
        if (n - 2) * len(C) > len(V) - 1: out.append(V)
    return out


def solve(W, A, tl_total, workers=4, verbose=False, static_short=False):
    n = W.n; U = A["U"]; H = hyperedges(W, A)
    if len(U) % (n - 2): return "NOT_DIVISIBLE", None, {}, []
    P = len(U) // (n - 2); cand = sorted(H)
    byv = {}
    for b in cand:
        for v in H[b]: byv.setdefault(v, []).append(b)
    for u in U:
        if u not in byv: return "INFEASIBLE_ORPHAN", None, {}, [("orphan", u)]
    m = cp_model.CpModel()
    x = {b: m.NewBoolVar(f"x{b}") for b in cand}
    m.Add(sum(x.values()) == P)
    for u in U: m.AddBoolOr([x[b] for b in byv[u]])
    pairs = set()
    for v, bl in byv.items():
        for i in range(len(bl)):
            for j in range(i + 1, len(bl)):
                b1, b2 = sorted((bl[i], bl[j]))
                if (b1, b2) not in pairs and len(H[b1] & H[b2]) >= 2:
                    pairs.add((b1, b2)); m.Add(x[b1] + x[b2] <= 1)
    if static_short:
        from shortcycles import short_cycles
        _, three, four = short_cycles(H)
        for C in three | four: m.Add(sum(x[b] for b in C) <= len(C) - 1)
    t0 = time.time(); it = 0; cuts = []; seen = set()
    while True:
        it += 1
        left = tl_total - (time.time() - t0)
        if left <= 0: return "UNKNOWN_TIME", None, dict(iterations=it, cuts=len(cuts), pairs=len(pairs)), cuts
        sv = cp_model.CpSolver(); sv.parameters.num_workers = workers; sv.parameters.max_time_in_seconds = left
        st = sv.Solve(m)
        info = dict(iterations=it, cuts=len(cuts), pairs=len(pairs), seconds=round(time.time() - t0, 1))
        if st == cp_model.INFEASIBLE: return "INFEASIBLE", None, info, cuts
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return "UNKNOWN_" + sv.StatusName(st), None, info, cuts
        X = [b for b in cand if sv.Value(x[b])]
        new = [S for S in comp_cuts(H, X, n) if S not in seen]
        if not new:
            ok, why = is_spanning_tree(H, X, U)
            return ("COMPLETION" if ok else "BUG_" + why), X, info, cuts
        for S in new:
            seen.add(S); cuts.append(S)
            m.Add(sum(x[b] for b in cand if H[b] <= S) <= (len(S) - 1) // (n - 2))
        m.ClearHints()
        for b in cand: m.AddHint(x[b], 1 if b in X else 0)
        if verbose and it % 10 == 0:
            print(f"    iter {it}: +{len(new)} cuts (total {len(cuts)}), sizes {sorted(len(S) for S in new)[:6]}, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    tl = float(sys.argv[1]); worlds = {}
    from flowsat import verify
    for job in sys.argv[2:]:
        n, spec = int(job.split("/")[0]), job.split("/")[1]
        W = worlds.setdefault(n, World(n)); rows = kernel_rows(n, spec)
        A = analyse(W, rows); k = len(rows); G = sum(n - 1 - r[1] for r in rows)
        st, X, info, cuts = solve(W, A, tl, verbose=True, static_short=os.environ.get('STATIC') == '1')
        line = dict(n=n, kernel=spec[:60], score=k - G, status=st, **info)
        tag = spec.replace(':', '_')[:60]
        if X:
            ok, why = verify(W, rows, X, n); line.update(forest_check=ok)
            json.dump(dict(n=n, kernel=spec, rows=[[list(r[0]), r[1], list(r[2])] for r in rows],
                           payload=[[list(W.blocks[b][0]), W.blocks[b][1]] for b in X]),
                      open(os.path.join(HERE, "..", "certs", f"htcut_completion_{n}_{tag}.json"), "w"))
        if st == "INFEASIBLE":
            json.dump(dict(n=n, kernel=spec, scuts=[sorted(map(int, S)) for S in cuts]),
                      open(os.path.join(HERE, "..", "certs", f"htcut_infeasible_{n}_{tag}.json"), "w"))
        print(json.dumps(line), flush=True)
