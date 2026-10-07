#!/usr/bin/env python3
"""Exact re-linking of a FIXED r=0 cyclic-trail partition (generalized ATSP, CP-SAT AddCircuit).
Each closed cyclic trail X (a cyclic sequence of chains joined at cost 3) is opened once, at a chain a:
the path starts at start(a) and ends at the run end of chain a-1.  Joining path P (opened at a) to
path Q (opened at b) costs cost(end_a, start_b) - 3 extra over a cost-3 join.  Total length
   L = CONST - ORB + q + sum over the (#cycles - 1) joins of (c - 3)
(with all chains kept, q fixed).  Objective: minimize that sum.  Arcs with cost <= MAXC are used;
the optimum under the restriction is an upper bound on the true optimum and is exact if it is
<= (#cycles-1) * (MAXC-3) ... we simply report the status."""
import sys, os, json, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse, cost

def cyclic_trails(info, n):
    S, trails = info["S"], info["trails"]
    Rinv = lambda s: s[-1:] + s[:-1]
    end_of = lambda ch: Rinv(S[ch[-1]])
    cyc, rest = [], []
    for t in trails:
        (cyc if cost(end_of(t[-1]), S[t[0][0]], n) == 3 else rest).append(t)
    # glue residual trails greedily into cycles by cost-3 joins
    while rest:
        cur = [rest.pop(0)]
        while cost(end_of(cur[-1][-1]), S[cur[0][0][0]], n) != 3:
            nxt = next(i for i, t in enumerate(rest) if cost(end_of(cur[-1][-1]), S[t[0][0]], n) == 3)
            cur.append(rest.pop(nxt))
        cyc.append([ch for t in cur for ch in t])
    return [[(S[ch[0]], Rinv(S[ch[-1]]), len(ch)) for ch in t] for t in cyc]

def solve(cycles, n, maxc, tl, workers=8):
    nodes = []            # (cluster, start, end_of_previous_chain)
    for X, cy in enumerate(cycles):
        k = len(cy)
        for a in range(k): nodes.append((X, cy[a][0], cy[(a - 1) % k][1]))
    N = len(nodes); D = N
    byprefix = {}
    for b, (Y, t, _) in enumerate(nodes):
        for j in range(1, n): byprefix.setdefault(t[:j], []).append(b)
    m = cp_model.CpModel(); arcs = []; obj = []
    lit = {}
    for a, (X, _, e) in enumerate(nodes):
        cand = set()
        for j in range(n - maxc, n):          # overlap j >= n - maxc
            cand.update(byprefix.get(e[n - j:], []))
        for b in cand:
            if nodes[b][0] == X: continue
            c = cost(e, nodes[b][1], n)
            if c > maxc: continue
            v = m.NewBoolVar(""); lit[(a, b)] = (v, c); arcs.append((a, b, v)); obj.append((c - 3) * v)
    skip = []
    for a in range(N):
        s = m.NewBoolVar(""); arcs.append((a, a, s)); skip.append(s)
        v1 = m.NewBoolVar(""); arcs.append((D, a, v1)); v2 = m.NewBoolVar(""); arcs.append((a, D, v2))
    for X in range(len(cycles)):
        m.AddExactlyOne([skip[a].Not() for a in range(N) if nodes[a][0] == X])
    m.AddCircuit(arcs)
    m.Minimize(sum(obj))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    t0 = time.time(); st = sv.Solve(m)
    sol = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # recover order
        succ = {}
        for a, b, v in arcs:
            if a != b and sv.Value(v): succ[a] = b
        order = []; x = succ[D]
        while x != D: order.append(x); x = succ[x]
        sol = order
    return sv.StatusName(st), (sv.ObjectiveValue() if sol else None), sv.BestObjectiveBound(), sol, nodes, len(lit), round(time.time() - t0, 1)

def build_word(cycles, nodes, order, n):
    """Concatenate the opened cycles in the given order into a word; return it."""
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    seq = []                                          # list of class run starts
    for a in order:
        X = nodes[a][0]; cy = cycles[X]; k = len(cy)
        st = next(i for i in range(k) if cy[i][0] == nodes[a][1])
        for i in range(k):
            s, _, l = cy[(st + i) % k]
            for _ in range(l): seq.append(s); s = F(s)
    word = list(seq[0])
    R = lambda s: s[1:] + s[:1]
    perms = []
    for s in seq:
        p = s
        for _ in range(n): perms.append(p); p = R(p)
    for x, y in zip(perms, perms[1:]):
        c = cost(x, y, n); word.extend(y[n - c:])
    return word

if __name__ == "__main__":
    path, maxc, tl = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    w, n = load(path); out, info = analyse(w, n)
    cycles = cyclic_trails(info, n)
    print("cycles", len(cycles), "sizes", sorted(len(c) for c in cycles), flush=True)
    st, obj, bd, order, nodes, na, sec = solve(cycles, n, maxc, tl)
    import math
    N = math.factorial(n); HEX = N // n; ORB = HEX // (n - 1); CONST = N + HEX + ORB + n - 3
    q = sum(len(c) for c in cycles)
    print(json.dumps(dict(status=st, objective=obj, bound=bd, arcs=na, sec=sec, q=q,
                          length=None if obj is None else CONST - ORB + q + int(obj))), flush=True)
    if order:
        word = build_word(cycles, nodes, order, n)
        outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"relink_n{n}_{len(word)}.txt")
        open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
        print("wrote", outp, "length", len(word))
