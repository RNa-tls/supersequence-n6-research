#!/usr/bin/env python3
"""Round K -- break attempt by large-neighbourhood search at the ROTATION level (heuristic; it can
find shorter words, it proves nothing).

The input word must be an r = 0 superpermutation: its first-occurrence order is a sequence of
runs (one per cyclic class), run i starting at perm p_i.  L = n + (n-1)*HEX + sum_i cost(e(p_i), p_{i+1}),
e(p) = last perm of the run = rotate p right by one.  A window = runs i..j-1.  Keeping everything
else fixed, CP-SAT re-chooses, for the window's classes, the start rotation of every run AND
their order (a generalized-TSP path from e(p_{i-1}) to p_j), minimizing the window's join cost.
Arcs are restricted to cost <= CMAX (a restriction: every solution found is genuine).
Any strictly cheaper window gives a shorter word, which is rebuilt and checked independently.
usage: lns_window.py WORD i j [CMAX] [timelimit]"""
import sys, os, json, time, itertools
from ortools.sat.python import cp_model
n = 8
def load(path):
    t = "".join(open(path).read().split()); al = sorted(set(t)); m = {c: k for k, c in enumerate(al)}
    return [m[c] for c in t]
def runs_of(w):
    seen = set(); order = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); order.append(p)
    assert len(order) == 40320
    runs = [order[i] for i in range(0, 40320, n)]
    for i in range(0, 40320, n):
        for k in range(1, n): assert order[i + k] == order[i + k - 1][1:] + order[i + k - 1][:1], "not r=0"
    return runs
def last(p): return p[-1:] + p[:-1]
def cost(x, y):
    for k in range(n - 1, 0, -1):
        if x[n - k:] == y[:k]: return n - k
    return n
def rots(p): return [p[k:] + p[:k] for k in range(n)]
def word_from_runs(runs):
    out = list(runs[0]); cur = runs[0]
    for _ in range(n - 1):
        cur = cur[1:] + cur[:1]; out.append(cur[-1])
    for p in runs[1:]:
        c = cost(cur, p); out.extend(p[n - c:]); cur = p
        for _ in range(n - 1):
            cur = cur[1:] + cur[:1]; out.append(cur[-1])
    return out

def solve_window(runs, i, j, cmax, tl, workers=4):
    W = runs[i:j]
    cls = [rots(p) for p in W]                       # 8 candidate starts per class
    nodes = [(ci, k) for ci in range(len(W)) for k in range(n)]
    nid = {nd: 2 + t for t, nd in enumerate(nodes)}
    src = last(runs[i - 1]) if i > 0 else None
    dst = runs[j] if j < len(runs) else None
    cur_cost = sum(cost(last(runs[t]), runs[t + 1]) for t in range(max(i - 1, 0), min(j, len(runs) - 1)))
    m = cp_model.CpModel(); arcs = []; obj = []
    lits = {}
    def arc(a, b, c):
        l = m.NewBoolVar(""); arcs.append((a, b, l)); obj.append(c * l); lits[(a, b)] = l
    # source / sink
    for (ci, k), t in nid.items():
        p = cls[ci][k]
        c0 = cost(src, p) if src is not None else 0
        if c0 <= cmax: arc(0, t, c0)
        c1 = cost(last(p), dst) if dst is not None else 0
        if c1 <= cmax: arc(t, 1, c1)
    arc(1, 0, 0)
    m.Add(lits[(1, 0)] == 1)
    # internal arcs: index the window's candidate starts by prefixes of length k >= n - cmax
    bypre = {}
    for (ci, k), t in nid.items():
        q = cls[ci][k]
        for L in range(max(1, n - cmax), n): bypre.setdefault(q[:L], []).append((ci, k, t))
    for (ci, k), t in nid.items():
        e = last(cls[ci][k]); done = set()
        for L in range(n - 1, max(1, n - cmax) - 1, -1):          # longest overlap first = exact cost
            for (cj, k2, t2) in bypre.get(e[n - L:], []):
                if cj == ci or t2 in done: continue
                done.add(t2); arc(t, t2, n - L)
    skip = {}
    for (ci, k), t in nid.items():
        s = m.NewBoolVar(""); skip[(ci, k)] = s; arcs.append((t, t, s))
    for ci in range(len(W)): m.Add(sum(1 - skip[(ci, k)] for k in range(n)) == 1)
    m.AddCircuit(arcs)
    m.Minimize(sum(obj))
    # hint: the current window
    cur_rot = {ci: cls[ci].index(W[ci]) for ci in range(len(W))}
    for (ci, k), s in skip.items(): m.AddHint(s, 0 if cur_rot[ci] == k else 1)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    st = sv.Solve(m)
    res = dict(i=i, j=j, classes=len(W), cmax=cmax, current=cur_cost, status=sv.StatusName(st), arcs=len(arcs),
               sec=round(sv.WallTime(), 1))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res["best"] = int(round(sv.ObjectiveValue())); res["bound"] = sv.BestObjectiveBound()
        if res["best"] < cur_cost:
            # rebuild the order
            succ = {a: b for (a, b, l) in arcs if a != b and sv.Value(l)}
            seq = []; v = succ[0]
            while v != 1:
                ci, k = nodes[v - 2]; seq.append(cls[ci][k]); v = succ[v]
            res["new_runs"] = seq
    return res

if __name__ == "__main__":
    path, i, j = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    cmax = int(sys.argv[4]) if len(sys.argv) > 4 else 5; tl = float(sys.argv[5]) if len(sys.argv) > 5 else 120
    runs = runs_of(load(path))
    res = solve_window(runs, i, j, cmax, tl)
    if "new_runs" in res:
        new = runs[:i] + [tuple(p) for p in res["new_runs"]] + runs[j:]
        word = word_from_runs(new)
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"lns_word_{len(word)}.txt")
        open(out, "w").write("".join(str(c + 1) for c in word) + "\n")
        res["word_length"] = len(word); res["word_file"] = out
        del res["new_runs"]
    print(json.dumps(res), flush=True)
