#!/usr/bin/env python3
"""Round L -- exact r = 0 optimum for small n (target n = 6) by CP-SAT on the chain-level model.

Model (a RELAXATION of r = 0 routes; every r = 0 route gives a feasible solution of no larger cost):
  nodes  : every chain (run start p, length 1 <= l <= n-1), optional (self-loop when unused),
           one depot (route start/end), K hub nodes (optional).
  cover  : every cyclic class lies in exactly one chosen chain.
  arcs   : chain c1 -> chain c2 with weight w = w(last perm of c1, first perm of c2) <= WMAX, cost w-2;
           chain -> hub cost (WMAX+1)-2 (any join of weight > WMAX), hub -> chain cost 0;
           depot <-> chain cost 0.   AddCircuit over all nodes.
  value  : L = n + n! + (n-1)! - 2 + sum of arc costs  (exact for r = 0 routes, Round I identity).
A route using more than K joins of weight > WMAX costs at least K+1 times (WMAX-1); the script
reports the bound min(objective bound, K+1 hub-cost) so the result is a valid lower bound on L_r0(n).
Symmetry: the chain covering the class (0 1 .. n-1) is required to have special n-1 (Z_n symmetry).
usage: r0_exact_small.py n [WMAX] [K] [timelimit] [workers]"""
import sys, os, json, time, math, itertools
from ortools.sat.python import cp_model

def main():
    n = int(sys.argv[1]); WMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 9
    tl = float(sys.argv[4]) if len(sys.argv) > 4 else 3600; workers = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    t0 = time.time()
    def F(p): return p[1:n - 1] + p[:1] + p[n - 1:]
    def cyc(p):
        k = p.index(0); return p[k:] + p[:k]
    def last(p): return p[-1:] + p[:-1]
    def wt(x, y):
        for j in range(n - 1, 0, -1):
            if x[n - j:] == y[:j]: return n - j
        return n
    perms = list(itertools.permutations(range(n)))
    classes = sorted({cyc(p) for p in perms}); cid = {c: i for i, c in enumerate(classes)}
    chains = []                                      # (start, end_runstart, l, class ids)
    for p in perms:
        x = p; cl = []
        for l in range(1, n):
            cl.append(cid[cyc(x)])
            chains.append((p, x, l, tuple(cl)))
            x = F(x)
    by_start = {}
    for i, (p, x, l, cl) in enumerate(chains): by_start.setdefault(p, []).append(i)
    m = cp_model.CpModel()
    y = [m.NewBoolVar(f"y{i}") for i in range(len(chains))]
    cover = [[] for _ in classes]
    for i, (p, x, l, cl) in enumerate(chains):
        for c in cl: cover[c].append(y[i])
    for c in range(len(classes)): m.AddExactlyOne(cover[c])
    # symmetry: class 0 = (0,1,..,n-1) covered by a chain whose special is n-1
    m.Add(sum(y[i] for i, (p, x, l, cl) in enumerate(chains) if 0 in cl and p[n - 1] != n - 1) == 0)
    N = len(chains); depot = N; hubs = list(range(N + 1, N + 1 + K))
    arcs = []; cost = []
    for i in range(N): arcs.append((i, i, y[i].Not()))
    for h in hubs:
        u = m.NewBoolVar(f"hub{h}"); arcs.append((h, h, u.Not()))
    targets = {}
    nar = 0
    for i, (p, x, l, cl) in enumerate(chains):
        e = last(x)
        if e not in targets:
            tg = []
            for w_ in range(2, WMAX + 1):
                for perm in itertools.permutations(e[:w_]):
                    t = e[w_:] + perm
                    if wt(e, t) == w_ and cyc(t) != cyc(e): tg.append((t, w_))
            targets[e] = tg
        for t, w_ in targets[e]:
            for j in by_start[t]:
                if set(chains[j][3]) & set(cl): continue
                b = m.NewBoolVar(""); arcs.append((i, j, b)); cost.append((b, w_ - 2)); nar += 1
        for h in hubs:
            b = m.NewBoolVar(""); arcs.append((i, h, b)); cost.append((b, WMAX - 1))
            b2 = m.NewBoolVar(""); arcs.append((h, i, b2))
        b = m.NewBoolVar(""); arcs.append((depot, i, b))
        b = m.NewBoolVar(""); arcs.append((i, depot, b))
    m.AddCircuit(arcs)
    obj = sum(c * b for b, c in cost)
    m.Minimize(obj)
    base = n + math.factorial(n) + math.factorial(n - 1) - 2
    print(json.dumps(dict(n=n, chains=N, arcs=len(arcs), chain_arcs=nar, build_sec=round(time.time() - t0, 1))), flush=True)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    sv.parameters.log_search_progress = False
    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(s): super().__init__(); s.t = time.time()
        def on_solution_callback(s):
            print(json.dumps(dict(sol=base + s.ObjectiveValue(), bound=base + s.BestObjectiveBound(), sec=round(time.time() - t0, 1))), flush=True)
    st = sv.Solve(m, CB())
    lb = base + min(sv.BestObjectiveBound(), (K + 1) * (WMAX - 1))
    res = dict(n=n, status=sv.StatusName(st), best=base + sv.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
               objective_bound=base + sv.BestObjectiveBound(), valid_lower_bound_L_r0=lb, WMAX=WMAX, K=K, sec=round(time.time() - t0, 1))
    print(json.dumps(res), flush=True)
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"r0_exact_n{n}.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
