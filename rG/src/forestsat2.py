#!/usr/bin/env python3
"""Final attack, upper thread -- exact CP-SAT completion model for an ARBITRARY kernel (single trail of
omission-free rows).  Kernel rows own exactly their visible classes; their blocks are not payload.
Payload block b used (x_b): owns all its classes but one attachment class att[b,c]; every class has
exactly one owner; the attachment class of b is owned by a block of strictly smaller depth
(depth domain [0, Dmax], kernel rows depth 0).  Any solution is an attachment forest with one
component per kernel row (hole-free payload), hence (generalized Theorem E) a superpermutation of
length CONST + ((n-2)! - (k - G))/(n-2); the route is rebuilt and checked independently."""
import sys, os, math, time, itertools, json
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "r178", "src"))
from complete import World, kernel_from_lengths, std_kernel, canon


def solve(W, rows, Dmax, timelimit, workers=4, seed=0, log=False):
    n = W.n
    kb = {W.bid[(canon(r[0][:n - 1]), r[0][n - 1])]: i for i, r in enumerate(rows)}
    kvis = {}
    for i, r in enumerate(rows):
        for c in W.row_visible(r): kvis[c] = i
    m = cp_model.CpModel()
    NB = len(W.blocks)
    pay = [b for b in range(NB) if b not in kb]
    x = {b: m.NewBoolVar(f"x{b}") for b in pay}
    d = {b: m.NewIntVar(1, Dmax, f"d{b}") for b in pay}
    own = {}; att = {}
    for b in pay:
        for c in W.bcls[b]:
            own[c, b] = m.NewBoolVar(""); att[b, c] = m.NewBoolVar("")
            m.Add(own[c, b] + att[b, c] == x[b])
        m.Add(sum(att[b, c] for c in W.bcls[b]) == x[b])
    for c in range(W.C):
        owners = [own[c, b] for b in W.cblk[c] if b in x]
        if c in kvis:
            for o in owners: m.Add(o == 0)          # kernel owns its visible classes
        else:
            m.AddExactlyOne(owners)
    for c in range(W.C):
        for b in W.cblk[c]:
            if b not in x: continue
            if c in kvis: continue                    # attached to a kernel row: depth >= 1 holds
            for b2 in W.cblk[c]:
                if b2 == b or b2 not in x: continue
                m.Add(d[b] >= d[b2] + 1).OnlyEnforceIf([att[b, c], own[c, b2]])
    k = len(rows); G = sum(n - 1 - r[1] - len(r[2]) for r in rows)
    HEX = math.factorial(n - 1)
    P = (HEX - (n - 1) * k + G)
    if P % (n - 2): return dict(status="SCORE_NOT_DIVISIBLE")
    m.Add(sum(x.values()) == P // (n - 2))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = timelimit
    sv.parameters.num_workers = workers; sv.parameters.random_seed = seed
    sv.parameters.log_search_progress = log
    t0 = time.time(); st = sv.Solve(m)
    out = dict(status=sv.StatusName(st), seconds=round(time.time() - t0, 1), payload_target=P // (n - 2))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        out["payload"] = [W.blocks[b] for b in pay if sv.Value(x[b])]
    return out


def realize_and_check(W, rows, payload):
    """independent rebuild: selected states = visible states of kernel rows + all states of payload
    blocks; traverse each component's T = F o A cycle from its row start, rows in trail order."""
    from bridge178 import cost
    n = W.n
    R = lambda x: x[1:] + x[:1]; F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    S = set()
    for (p, l, om) in rows:
        y = p
        for i in range(l):
            if i not in om: S.add(y)
            y = F(y)
    for (Wd, s) in payload:
        y = tuple(Wd) + (s,)
        for _ in range(n - 1): S.add(y); y = F(y)
    def A(y):
        z = R(y)
        while z not in S: z = R(z)
        return z
    route = []
    for (p, l, om) in rows:
        y = p; guard = 0
        while True:
            z = y
            while True:
                route.append(z)
                if R(z) in S: break
                z = R(z)
            nxt = F(A(y))
            if nxt not in S: break                   # reached the row's hole gap: chain ends
            y = nxt; guard += 1
            if y == p or guard > 10**7: break
    N = math.factorial(n)
    ham = len(route) == N and len(set(route)) == N
    L = n + sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1)) if route else None
    return ham, L, route


if __name__ == "__main__":
    n = int(sys.argv[1]); spec = sys.argv[2]; Dmax = int(sys.argv[3]); tl = float(sys.argv[4])
    W = World(n)
    rows = std_kernel(n) if spec == "std" else kernel_from_lengths(n, [int(ch) for ch in spec])
    k = len(rows); G = sum(n - 1 - r[1] for r in rows)
    CONST = math.factorial(n) + math.factorial(n - 1) + math.factorial(n - 2) + n - 3
    print(f"n={n} kernel {spec} rows={k} charge={G} score={k - G} target length {CONST + (math.factorial(n - 2) - (k - G)) / (n - 2)}", flush=True)
    r = solve(W, rows, Dmax, tl)
    print({kk: v for kk, v in r.items() if kk != "payload"}, flush=True)
    if "payload" in r:
        ham, L, route = realize_and_check(W, rows, r["payload"])
        print(f"  rebuilt route Hamiltonian: {ham}, length {L}", flush=True)
        json.dump(dict(n=n, kernel=spec, payload=[[list(a), b] for a, b in r["payload"]], length=L, hamiltonian=ham),
                  open(os.path.join(HERE, "..", "certs", f"sat_completion_n{n}_{spec[:40]}.json"), "w"))
