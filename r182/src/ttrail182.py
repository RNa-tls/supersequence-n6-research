#!/usr/bin/env python3
"""Round 182 -- joint search: exact partition of all classes by rows of fixed length L (no omissions)
built trail by trail.  Backtracking exact cover (Algorithm X bookkeeping) where the next row is
preferably a compatible successor of the current trail end; a new trail starts at the most
constrained class.  Node-limited.  Result verified by checkers A and B and turned into a covering
route (r = 0 realization) whose Bridge parameters are recomputed by bridge178.coarsen."""
import math, os, random, sys, json
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r176", "src")); sys.path.insert(0, os.path.join(ROOT, "r178", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB

def search(n, L, rng, limit):
    A = CheckerA(n)
    opts = []; byalpha = {}
    for p in permutations(range(n)):
        row = (p, L, ()); opts.append((row, frozenset(A.visible(row)), A.block(p)))
        byalpha.setdefault(p[:n - 3], []).append(len(opts) - 1)
    X = {}
    for j, (_, cs, _) in enumerate(opts):
        for c in cs: X.setdefault(c, set()).add(j)
    beta = [A.beta(o[0]) for o in opts]
    used = set(); trails = [[]]; cnt = [0]; best = [None]
    alive = set(range(len(opts)))
    def select(j):
        cols = []
        for c in opts[j][1]:
            for k in list(X[c]):
                for c2 in opts[k][1]:
                    if c2 != c: X[c2].discard(k)
            cols.append((c, X.pop(c)))
        return cols
    def deselect(cols):
        for c, s in reversed(cols):
            X[c] = s
            for k in s:
                for c2 in opts[k][1]:
                    if c2 != c: X[c2].add(k)
    def ok(j):
        return opts[j][2] not in used and all(c in X and j in X[c] for c in opts[j][1])
    def solve():
        cnt[0] += 1
        if cnt[0] > limit: return False
        if not X: return True
        if any(not s for s in X.values()): return False
        cur = trails[-1]
        succ = [j for j in byalpha.get(beta[cur[-1]], []) if ok(j)] if cur else []
        if succ:
            rng.shuffle(succ)
            succ.sort(key=lambda j: min(len(X[c]) for c in opts[j][1]))
            moves = [(j, False) for j in succ[:3]]
        else:
            c = min(X, key=lambda c: (len(X[c]), rng.random()))
            cand = [j for j in X[c] if opts[j][2] not in used]; rng.shuffle(cand)
            moves = [(j, True) for j in cand]
        for j, new in moves:
            if new: trails.append([])
            used.add(opts[j][2]); trails[-1].append(j); cols = select(j)
            if solve(): return True
            deselect(cols); trails[-1].pop(); used.discard(opts[j][2])
            if new: trails.pop()
        return False
    sys.setrecursionlimit(1000000)
    if not solve(): return None
    return [[opts[j][0] for j in t] for t in trails if t]

def to_route(trails, n):
    R = lambda s: s[1:] + s[:1]; F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    route = []
    for t in trails:
        for (p, l, _) in t:
            x = p
            for _ in range(l):
                y = x
                for _ in range(n): route.append(y); y = R(y)
                x = F(x)
    return route

if __name__ == "__main__":
    from bridge178 import coarsen, cost, check_instance
    res_all = []
    for n, L, seeds, limit in ((6, 3, 6, 200000), (7, 4, 3, 400000)):
        best = None
        for sd in range(seeds):
            tr = search(n, L, random.Random(sd), limit)
            if tr is None: print(f"n={n} L={L} seed={sd}: none within limit", flush=True); continue
            rows = [x for t in tr for x in t]
            okA = all(CheckerA(n).trail(t)[0] for t in tr); okB = all(CheckerB(n).trail(t)[0] for t in tr)
            route = to_route(tr, n)
            N = math.factorial(n); ORB = math.factorial(n - 2)
            cover = len(route) == N and len(set(route)) == N
            res = coarsen(route, n, random.Random(0))
            flat = [x for t in res["instance"] for x in t]
            nnf = sum(1 for x in flat if (n - 1 - x[1]) + len(x[2]) >= 1)
            X = res["m"] + res["b"] + res["eta"]
            length = n + sum(cost(route[i], route[i + 1], n) for i in range(N - 1))
            d = dict(n=n, L=L, seed=sd, rows=len(rows), trails=len(tr), checkerA=okA, checkerB=okB, cover=cover,
                     m=res["m"], r=res["r"], a=res["a"], b=res["b"], eta=res["eta"], D=res["D"], N_nf=nnf, X=X,
                     ratio=round(nnf / X, 3), length=length, bridge_instance_ok=check_instance(res, CheckerB(n))[0])
            print(d, flush=True); res_all.append((d, tr))
    json.dump([[d, [[[list(r[0]), r[1]] for r in t] for t in tr]] for d, tr in res_all],
              open(os.path.join(HERE, "..", "certs", "ttrail182.json"), "w"))
