#!/usr/bin/env python3
"""Final attack, construction thread -- exact CP-SAT model of Problem A(n):
a set of blocks containing the principal phi-cycle kernel (n-2 blocks of special s = n-1 forming the
frame of moving letter Y = 0), covering every cyclic class, whose block-class incidence graph is a
forest with exactly n-2 components (each containing one kernel block).  By Theorem E (final round) any
solution yields a superpermutation of length f(n) = n!+(n-1)!+(n-2)!+(n-3)!+n-4 (realized and checked
here by rF/src/forest_realize.realize).
Model: x_B (block used); own[c,B] (B introduces class c); att[B,c] (c is B's attachment class);
depth d_B; every class has exactly one owner; for a used non-kernel block exactly one attachment class,
all its other classes owned by it; attachment class owned by a block of strictly smaller depth."""
import sys, os, math, time, itertools
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "rF", "src")); sys.path.insert(0, os.path.join(ROOT, "r178", "src"))

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))

def structures(n):
    classes = sorted({canon(p) for p in itertools.permutations(range(n))}); cid = {c: i for i, c in enumerate(classes)}
    blocks = []; bid = {}
    for c in classes:
        for t in range(n):
            i = c.index(t); W = canon(c[i + 1:] + c[:i])
            if (W, t) not in bid: bid[(W, t)] = len(blocks); blocks.append((W, t))
    bcls = [[cid[canon(W[:g] + (t,) + W[g:])] for g in range(n - 1)] for W, t in blocks]
    return classes, blocks, bid, bcls

def kernel(n):
    s = n - 1; f = (1,) + tuple(range(2, n - 1))
    starts = [f[j:] + f[:j] + (0, s) for j in range(n - 2)]
    return starts

def solve(n, timelimit, workers=4, extra=None):
    classes, blocks, bid, bcls = structures(n)
    K = [bid[(canon(p[:n - 1]), p[n - 1])] for p in kernel(n)]
    Kset = set(K)
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{b}") for b in range(len(blocks))]
    Dmax = len(blocks)
    d = [m.NewIntVar(0, Dmax, f"d{b}") for b in range(len(blocks))]
    own = {}; att = {}
    cblk = [[] for _ in classes]
    for b, cl in enumerate(bcls):
        for c in cl: cblk[c].append(b)
    for b, cl in enumerate(bcls):
        for c in cl:
            own[c, b] = m.NewBoolVar("")
            if b in Kset: m.Add(own[c, b] == x[b])
            else:
                att[b, c] = m.NewBoolVar("")
                m.Add(own[c, b] + att[b, c] == x[b])
        if b not in Kset:
            m.Add(sum(att[b, c] for c in cl) == x[b])
    for b in K: m.Add(x[b] == 1); m.Add(d[b] == 0)
    for c in range(len(classes)):
        m.AddExactlyOne(own[c, b] for b in cblk[c])
    # attachment ordering: att[b,c] & own[c,b2] -> d[b] >= d[b2] + 1
    for c in range(len(classes)):
        for b in cblk[c]:
            if b in Kset: continue
            for b2 in cblk[c]:
                if b2 == b: continue
                m.Add(d[b] >= d[b2] + 1).OnlyEnforceIf([att[b, c], own[c, b2]])
    M = math.factorial(n - 2) + math.factorial(n - 3) - 1
    m.Add(sum(x) == M)
    if extra: extra(m, x, blocks, bid)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = timelimit; sv.parameters.num_workers = workers
    t0 = time.time(); st = sv.Solve(m)
    res = dict(n=n, status=sv.StatusName(st), seconds=round(time.time() - t0, 1), blocks=len(blocks), classes=len(classes), M=M)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        chosen = [blocks[b] for b in range(len(blocks)) if sv.Value(x[b])]
        res["chosen"] = chosen
    return res

if __name__ == "__main__":
    from forest_realize import realize
    from bridge178 import cost
    for n, tl in [(int(a.split(':')[0]), float(a.split(':')[1])) for a in sys.argv[1:]]:
        r = solve(n, tl)
        line = {k: v for k, v in r.items() if k != "chosen"}
        if "chosen" in r:
            rt = realize(set(r["chosen"]), kernel(n), n)
            N = math.factorial(n)
            L = n + sum(cost(rt[i], rt[i + 1], n) for i in range(len(rt) - 1))
            f = sum(math.factorial(n - i) for i in range(4)) + n - 4
            line.update(route_hamiltonian=(len(rt) == N and len(set(rt)) == N), length=L, f=f)
        print(line, flush=True)
