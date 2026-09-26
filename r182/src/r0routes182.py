#!/usr/bin/env python3
"""Round 182 -- r = 0 covering routes (every cyclic class traversed as one full rotation run) built
by a randomized greedy with a target row length l*, used to probe NF:  N_nf <= theta (m + b + eta).

Two independent parameter computations:
  (I)  direct: S = entries, M = #blocks of entries, q = 1 + #(cost >= 3), p = 1 + #(cost >= 4),
       k = M (A = id), b = q - k, eta = p - 1, N_nf = #touched blocks with a hole (B9: charge of the
       row of a component = holes of its block; for r = 0 the component is the block itself);
  (II) bridge178.coarsen (full Bridge construction) + checker B on the produced instance.
Also: coverage of all n! permutations and the word length n + weight.
usage: r0routes182.py"""
import json, math, os, random, sys
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r178", "src")); sys.path.insert(0, os.path.join(ROOT, "r176", "src"))
from bridge178 import coarsen, cost, normalize, check_instance
from checkB176 import CheckerB


def build(n, lstar, rng, sample=40):
    R = lambda s: s[1:] + s[:1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    cls = lambda s: min(s[i:] + s[:i] for i in range(n))
    def blk(s):
        w = s[:n - 1]; return (min(w[i:] + w[:i] for i in range(n - 1)), s[n - 1])
    visited, touched = set(), set()
    unvisited = {cls(p) for p in permutations(range(n))}
    route = []
    def potential(x, cap):
        c = 0; y = x; seen = set()
        while c < cap and cls(y) not in visited and cls(y) not in seen:
            seen.add(cls(y)); c += 1; y = F(y)
        return c
    x = tuple(range(n)); touched.add(blk(x)); rowlen = 0
    while True:
        y = x
        for _ in range(n): route.append(y); y = R(y)
        visited.add(cls(x)); unvisited.discard(cls(x)); rowlen += 1
        if not unvisited: break
        z = route[-1]
        c2 = F(x); c2ok = cls(c2) not in visited
        c3 = [z[3:] + sg for sg in permutations(z[:3])]
        c3 = [q for q in c3 if cls(q) not in visited and blk(q) not in touched]
        if c2ok and rowlen < lstar:
            x = c2; continue
        if c3:
            sc = [(potential(q, lstar), rng.random(), q) for q in c3]
            x = max(sc)[2]; touched.add(blk(x)); rowlen = 0; continue
        if c2ok:
            x = c2; continue
        pool = rng.sample(sorted(unvisited), min(sample, len(unvisited)))
        cand = []
        for cc in pool:
            for i in range(n):
                e = cc[i:] + cc[:i]
                cand.append((blk(e) not in touched, potential(e, lstar), rng.random(), e))
        x = max(cand)[3]; touched.add(blk(x)); rowlen = 0
    return route


def direct_params(route, n):
    N, HEX, ORB = math.factorial(n), math.factorial(n - 1), math.factorial(n - 2)
    R = lambda s: s[1:] + s[:1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    c = [cost(route[i], route[i + 1], n) for i in range(len(route) - 1)]
    S = {route[0]} | {route[i + 1] for i in range(len(c)) if c[i] != 1}
    r = len(S) - HEX
    def blkset(s):
        out = [s]
        for _ in range(n - 2): out.append(F(out[-1]))
        return frozenset(out)
    blocks = {}
    for s in S: blocks.setdefault(blkset(s), set()).add(s)
    M = len(blocks); q = 1 + sum(1 for x in c if x >= 3); p = 1 + sum(1 for x in c if x >= 4)
    k = M; b = q - k; eta = p - 1; m = M - ORB
    nnf = sum(1 for B, E in blocks.items() if len(E) < n - 1)
    hist = {}
    for B, E in blocks.items(): hist[n - 1 - len(E)] = hist.get(n - 1 - len(E), 0) + 1
    return dict(r=r, M=M, m=m, k=k, b=b, eta=eta, q=q, p=p, N_nf=nnf, X=m + b + eta, D=m + b + eta,
                length=n + sum(c), covered=len(set(route)) == N, normalized=all(route[i + 1] != R(R(route[i])) for i in range(len(c))),
                charge_hist=dict(sorted(hist.items())))


def run():
    rng = random.Random(182)
    out = []
    for n, trials in ((5, 30), (6, 20), (7, 8), (8, 3)):
        for lstar in (n - 1, n - 2, n - 3, 2):
            for _ in range(trials if n < 8 else (trials if lstar in (n - 1, n - 2) else 1)):
                route = build(n, lstar, rng)
                d = direct_params(route, n)
                chk = None
                if n <= 7:
                    res = coarsen(route, n, rng)
                    flat = [x for t in res["instance"] for x in t]
                    nnf2 = sum(1 for x in flat if (n - 1 - x[1]) + len(x[2]) >= 1)
                    okB = check_instance(res, CheckerB(n))[0]
                    chk = (res["m"], res["b"], res["eta"], res["r"], res["a"], nnf2) == (d["m"], d["b"], d["eta"], d["r"], 0, d["N_nf"]) and okB
                d.update(n=n, lstar=lstar, bridge_agrees=chk, ratio=round(d["N_nf"] / d["X"], 3) if d["X"] else None)
                out.append(d)
    return out


if __name__ == "__main__":
    res = run()
    lines = []
    for n in (5, 6, 7, 8):
        for lstar in sorted({d["lstar"] for d in res if d["n"] == n}, reverse=True):
            R_ = [d for d in res if d["n"] == n and d["lstar"] == lstar]
            best = max(R_, key=lambda d: d["ratio"])
            lines.append(f"n={n} l*={lstar} routes={len(R_)} max N_nf/X={best['ratio']} (N_nf={best['N_nf']}, m={best['m']}, b={best['b']}, "
                         f"eta={best['eta']}, D={best['D']}, len={best['length']}, cover={best['covered']}, norm={best['normalized']}, "
                         f"bridge_agrees={best['bridge_agrees']}, hist={best['charge_hist']})  min D={min(d['D'] for d in R_)}")
    lines.append("all bridge checks: " + str(all(d["bridge_agrees"] in (True, None) for d in res)))
    txt = "\n".join(lines); print(txt)
    open(os.path.join(HERE, "..", "certs", "r0routes182.txt"), "w").write(txt + "\n")
    json.dump(res, open(os.path.join(HERE, "..", "certs", "r0routes182.json"), "w"))
