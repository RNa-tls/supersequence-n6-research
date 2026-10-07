#!/usr/bin/env python3
"""Exact r = 0 optimum for small n.
An r = 0 route = choice of one start s per cyclic class + an order of the classes; length
   L = n + N - HEX + sum_i cost(R^-1 s_i, s_{i+1}).
Relaxation with cap K (every join of true cost >= K is charged exactly K):
   LB_K = min sum_i min(c_i, K)   <=  true min sum_i c_i.
Model: CP-SAT AddMultipleCircuit, depot 0 (= a 'jump' of cost K, may be used many times), perm nodes
with self-loop literal (= not the chosen start of its class), exactly one chosen start per class,
arcs a->b for every pair of distinct classes with cost <= K-1.  Objective = sum arc costs + K*(#jumps) - K.
If the optimal relaxed solution's segments can be chained with joins of true cost exactly K the
bound is attained (we chain segments by a second exact solve and report the resulting true length)."""
import sys, json, math, time, itertools
from ortools.sat.python import cp_model

def cost(x, y, n):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n

def run(n, K, tl, workers=3):
    perms = list(itertools.permutations(range(n))); N = len(perms); HEX = N // n
    canon = lambda p: min(p[i:] + p[:i] for i in range(n))
    cls = {p: canon(p) for p in perms}
    idx = {p: i + 1 for i, p in enumerate(perms)}
    byprefix = {}
    for p in perms:
        for j in range(1, n): byprefix.setdefault(p[:j], []).append(p)
    m = cp_model.CpModel(); arcs = []; obj = []
    for a in perms:
        e = a[-1:] + a[:-1]
        for j in range(n - K + 1, n):
            for b in byprefix.get(e[n - j:], []):
                if cls[b] == cls[a]: continue
                c = cost(e, b, n)
                if c != n - j: continue
                v = m.NewBoolVar(""); arcs.append((idx[a], idx[b], v)); obj.append(c * v)
    skip = {}
    jumps = []
    for p in perms:
        s = m.NewBoolVar(""); arcs.append((idx[p], idx[p], s)); skip[p] = s
        v1 = m.NewBoolVar(""); arcs.append((0, idx[p], v1)); obj.append(K * v1); jumps.append(v1)
        v2 = m.NewBoolVar(""); arcs.append((idx[p], 0, v2))
    byc = {}
    for p in perms: byc.setdefault(cls[p], []).append(p)
    for c, ps in byc.items(): m.AddExactlyOne([skip[p].Not() for p in ps])
    m.AddMultipleCircuit(arcs)
    m.Minimize(sum(obj) - K)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    t0 = time.time(); st = sv.Solve(m)
    res = dict(n=n, K=K, status=sv.StatusName(st), arcs=len(arcs), sec=round(time.time() - t0, 1))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        base = n + N - HEX
        res.update(relaxed_obj=sv.ObjectiveValue(), relaxed_bound=sv.BestObjectiveBound(),
                   LB_length=base + math.ceil(sv.BestObjectiveBound() - 1e-6) + 0,
                   jumps=sum(sv.Value(v) for v in jumps))
        # segments
        succ = {}
        for a, b, v in arcs:
            if a != b and a != 0 and b != 0 and sv.Value(v): succ[a] = b
        heads = [b for a, b, v in arcs if a == 0 and sv.Value(v)]
        segs = []
        for h in heads:
            seg = [h]
            while seg[-1] in succ: seg.append(succ[seg[-1]])
            segs.append(seg)
        res["segments"] = len(segs)
        # chain segments exactly (ATSP over segments, true costs)
        P = [perms[i - 1] for i in range(1, N + 1)]
        ends = [P[s[-1] - 1][-1:] + P[s[-1] - 1][:-1] for s in segs]; starts = [P[s[0] - 1] for s in segs]
        inner = sum(cost(P[s[i] - 1][-1:] + P[s[i] - 1][:-1], P[s[i + 1] - 1], n) for s in segs for i in range(len(s) - 1))
        k = len(segs)
        m2 = cp_model.CpModel(); a2 = []; o2 = []
        for i in range(k):
            v = m2.NewBoolVar(""); a2.append((k, i, v)); v = m2.NewBoolVar(""); a2.append((i, k, v))
            for j in range(k):
                if i != j:
                    v = m2.NewBoolVar(""); a2.append((i, j, v)); o2.append(cost(ends[i], starts[j], n) * v)
        m2.AddCircuit(a2); m2.Minimize(sum(o2))
        s2 = cp_model.CpSolver(); s2.parameters.max_time_in_seconds = tl; s2.parameters.num_workers = workers
        st2 = s2.Solve(m2)
        res.update(chain_status=s2.StatusName(st2), UB_length=base + inner + int(s2.ObjectiveValue()))
    return res

if __name__ == "__main__":
    n, K, tl = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
    print(json.dumps(run(n, K, tl)), flush=True)
