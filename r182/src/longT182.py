#!/usr/bin/env python3
"""Round 182 -- NF counterexample probe: build a covering r = 0 route from several long trails of
T-rows (charge 2), each found by node-limited DFS avoiding previously used blocks and covered
classes, then chain-free fill of the remaining classes by greedy maximal arcs in unused blocks.
The route is realized by the r = 0 construction (ttrail182.to_route) and its Bridge parameters
recomputed by bridge178.coarsen; instances checked by checkers A and B."""
import math, os, random, sys
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r176/src", "r178/src", "r182/src"): sys.path.insert(0, os.path.join(ROOT, d))
from checkA176 import CheckerA
from checkB176 import CheckerB
from ttrail182 import to_route
from bridge178 import coarsen, check_instance, cost

def long_trail(n, L, A, covered, usedblk, nodes, rng, starts):
    best = []; path = []; cnt = [0]
    def ok(y):
        v = A.visible(y)
        return A.block(y[0]) not in usedblk and not (v & covered) and all(A.block(x[0]) != A.block(y[0]) and not (A.visible(x) & v) for x in path)
    def dfs():
        nonlocal best
        cnt[0] += 1
        if cnt[0] > nodes: return
        if len(path) > len(best): best = list(path)
        beta = A.beta(path[-1]); rest = [t for t in range(n) if t not in beta]
        opts = [(beta + tuple(p), L, ()) for p in permutations(rest)]; rng.shuffle(opts)
        for y in opts:
            if ok(y):
                path.append(y); dfs(); path.pop()
                if cnt[0] > nodes: return
    for s in starts:
        y = (s, L, ())
        if ok(y):
            path.append(y); dfs(); path.pop()
            break
    return best

def run(n, ntrails, nodes, seed):
    A = CheckerA(n); L = n - 3; rng = random.Random(seed)
    allp = list(permutations(range(n))); rng.shuffle(allp)
    covered, usedblk, trails = set(), set(), []
    for _ in range(ntrails):
        t = long_trail(n, L, A, covered, usedblk, nodes, rng, allp)
        if not t: break
        trails.append(t)
        for x in t: covered |= A.visible(x); usedblk.add(A.block(x[0]))
    # fill: for every uncovered class, take the longest arc of uncovered classes in an unused block
    allc = {A.hexagon(p) for p in allp}
    fill = []
    while covered != allc:
        c = next(iter(allc - covered)); best = None
        for i in range(n):
            e = c[i:] + c[:i]
            if A.block(e) in usedblk: continue
            l = 0; st = A.states(e, n - 1)
            while l < n - 1 and A.hexagon(st[l]) not in covered and A.hexagon(st[l]) not in {A.hexagon(z) for z in st[:l]}: l += 1
            if best is None or l > best[1]: best = (e, l)
        if best is None: return None
        row = (best[0], best[1], ()); fill.append([row])
        covered |= A.visible(row); usedblk.add(A.block(best[0]))
    alltr = trails + fill
    route = to_route(alltr, n)
    N = math.factorial(n)
    cover = len(route) == N and len(set(route)) == N
    res = coarsen(route, n, random.Random(0))
    flat = [x for t in res["instance"] for x in t]
    nnf = sum(1 for x in flat if (n - 1 - x[1]) + len(x[2]) >= 1)
    X = res["m"] + res["b"] + res["eta"]
    return dict(n=n, seed=seed, long_trails=[len(t) for t in trails], fill_rows=len(fill), cover=cover,
                okA=check_instance(res, CheckerA(n))[0] if n <= 7 else None, okB=check_instance(res, CheckerB(n))[0],
                m=res["m"], r=res["r"], b=res["b"], eta=res["eta"], D=res["D"], N_nf=nnf, X=X, ratio=round(nnf / X, 3),
                length=n + sum(cost(route[i], route[i + 1], n) for i in range(N - 1)))

if __name__ == "__main__":
    lines = []
    for n, nt, nodes, seeds in ((6, 6, 20000, 3), (7, 8, 8000, 2)):
        for sd in range(seeds):
            o = run(n, nt, nodes, sd); print(o, flush=True); lines.append(str(o))
    open(os.path.join(HERE, "..", "certs", "longT182.txt"), "w").write("\n".join(lines) + "\n")
