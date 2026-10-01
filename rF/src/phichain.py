#!/usr/bin/env python3
"""Final round -- upper-bound probe: m = 0, r = 0 routes built from phi-cycles.
Special s = n-1, moving letter Y0 = 0.  For every cyclic word F of {1..n-2} the phi-cycle (frame)
consists of the n-2 full rows with starts rot^j(F) + (0, s).  A trail = one phi-cycle started at
some j.  We look for an ordering of all (n-3)! frames, with a start choice for each, such that every
junction (last permutation of a trail -> first permutation of the next) has cost exactly 4.
By the conservation law such a route has D = (n-3)! - 1, E5 = 0, i.e. length
f(n) = n! + (n-1)! + (n-2)! + (n-3)! + n - 4."""
import sys, math, random, os
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r178", "src"))
from bridge178 import cost

def setup(n):
    s = n - 1
    R = lambda x: x[1:] + x[:1]; Rinv = lambda x: x[-1:] + x[:-1]
    Fm = lambda x: x[1:n - 1] + (x[0], x[n - 1])
    Finv = lambda x: (x[n - 2],) + x[:n - 2] + (x[n - 1],)
    phi = lambda p: p[1:n - 2] + (p[0],) + p[n - 2:]
    phiinv = lambda p: (p[n - 3],) + p[:n - 3] + p[n - 2:]
    frames = []
    for rest in permutations(range(2, n - 1)):
        f = (1,) + rest
        frames.append([f[j:] + f[:j] + (0, s) for j in range(n - 2)])
    def last(p):                     # last permutation of the trail started at p
        q = phiinv(p)                # last row start
        return Rinv(Finv(q))
    return frames, last

def search(n, rng, limit=2000000):
    frames, last = setup(n)
    K = len(frames)
    # succ[(i,j)] = list of (i2,j2) with cost 4
    starts = [(i, j) for i in range(K) for j in range(n - 2)]
    byprefix = {}
    for i, j in starts:
        byprefix.setdefault(frames[i][j][:n - 4], []).append((i, j))
    def succ(i, j):
        z = last(frames[i][j])
        return [(i2, j2) for (i2, j2) in byprefix.get(z[4:], []) if i2 != i and cost(z, frames[i2][j2], n) == 4]
    used = [False] * K; path = []; cnt = [0]
    sys.setrecursionlimit(100000)
    def dfs():
        cnt[0] += 1
        if cnt[0] > limit: return False
        if len(path) == K: return True
        i, j = path[-1]
        nx = [x for x in succ(i, j) if not used[x[0]]]
        rng.shuffle(nx)
        nx.sort(key=lambda x: sum(1 for y in succ(*x) if not used[y[0]]))   # Warnsdorff
        for x in nx:
            used[x[0]] = True; path.append(x)
            if dfs(): return True
            path.pop(); used[x[0]] = False
        return False
    for j in range(n - 2):
        used[0] = True; path.append((0, j))
        if dfs(): return [frames[i][jj] for i, jj in path]
        path.pop(); used[0] = False
    return None

def route_of(starts, n):
    R = lambda x: x[1:] + x[:1]; Fm = lambda x: x[1:n - 1] + (x[0], x[n - 1])
    phi = lambda p: p[1:n - 2] + (p[0],) + p[n - 2:]
    route = []
    for p in starts:
        row = p
        for _ in range(n - 2):
            x = row
            for _ in range(n - 1):
                y = x
                for _ in range(n): route.append(y); y = R(y)
                x = Fm(x)
            row = phi(row)
    return route

if __name__ == "__main__":
    for n in (5, 6, 7, 8, 9):
        st = search(n, random.Random(n))
        if st is None: print(n, "no cost-4 chain found"); continue
        route = route_of(st, n)
        N = math.factorial(n)
        L = n + sum(cost(route[i], route[i + 1], n) for i in range(N - 1))
        f = sum(math.factorial(n - i) for i in range(4)) + n - 4
        print(f"n={n}: chain of {len(st)} phi-cycles found; covering={len(route) == N and len(set(route)) == N}; length={L}; f(n)={f}; Egan={f + 1}", flush=True)
