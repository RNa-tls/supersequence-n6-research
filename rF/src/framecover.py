#!/usr/bin/env python3
"""Final round -- m = 0 routes: exact covers of all classes by (n-3)! frames (phi-cycles of full rows,
any special s, any moving letter Y), then search for an ordering + start choice with all junction
costs exactly 4 (length f(n) = n!+(n-1)!+(n-2)!+(n-3)!+n-4), or report the minimum junction excess
found.  A frame (s, Y, F): rows with starts rot^j(F) + (Y, s), j = 0..n-3 (F a cyclic word of
[n] \ {s, Y}); its rows are full and pairwise disjoint (same special, distinct words)."""
import sys, math, random, os, json
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r178", "src")); sys.path.insert(0, os.path.join(ROOT, "r176", "src"))
sys.path.insert(0, HERE)
from bridge178 import cost
from checkA176 import CheckerA
from phichain import route_of

def frames(n):
    A = CheckerA(n); out = []
    for s in range(n):
        for Y in range(n):
            if Y == s: continue
            others = [t for t in range(n) if t not in (s, Y)]
            first = others[0]
            for rest in permutations(others[1:]):
                f = (first,) + rest
                starts = [f[j:] + f[:j] + (Y, s) for j in range(n - 2)]
                cls = set()
                for p in starts: cls |= A.visible((p, n - 1, ()))
                out.append((starts, frozenset(cls)))
    return out

def exact_covers(n, fr, rng, want, limit):
    X = {}
    for i, (_, cs) in enumerate(fr):
        for c in cs: X.setdefault(c, set()).add(i)
    sols = []; sol = []; cnt = [0]
    def solve():
        cnt[0] += 1
        if cnt[0] > limit or len(sols) >= want: return
        if not X: sols.append(list(sol)); return
        c = min(X, key=lambda c: (len(X[c]), rng.random()))
        cand = list(X[c]); rng.shuffle(cand)
        for i in cand:
            cols = []
            for c1 in fr[i][1]:
                for j in list(X[c1]):
                    for c2 in fr[j][1]:
                        if c2 != c1: X[c2].discard(j)
                cols.append((c1, X.pop(c1)))
            sol.append(i); solve(); sol.pop()
            for c1, st in reversed(cols):
                X[c1] = st
                for j in st:
                    for c2 in fr[j][1]:
                        if c2 != c1: X[c2].add(j)
            if len(sols) >= want or cnt[0] > limit: return
    sys.setrecursionlimit(100000); solve()
    return sols

def best_chain(n, trails, rng, limit):
    """min total junction excess sum(c_j - 4) over orderings/start choices (DFS, branch & bound)."""
    R = lambda x: x[1:] + x[:1]; Rinv = lambda x: x[-1:] + x[:-1]
    Finv = lambda x: (x[n - 2],) + x[:n - 2] + (x[n - 1],)
    phiinv = lambda p: (p[n - 3],) + p[:n - 3] + p[n - 2:]
    K = len(trails)
    nodes = [(i, j) for i in range(K) for j in range(n - 2)]
    last = {(i, j): Rinv(Finv(phiinv(trails[i][j]))) for i, j in nodes}
    w = {}
    for u in nodes:
        for v in nodes:
            if u[0] != v[0]: w[u, v] = cost(last[u], trails[v[0]][v[1]], n) - 4
    best = [10**9, None]; cnt = [0]; used = [False] * K; path = []
    def dfs(acc):
        cnt[0] += 1
        if cnt[0] > limit or acc >= best[0]: return
        if len(path) == K: best[0] = acc; best[1] = list(path); return
        u = path[-1]
        cand = [v for v in nodes if not used[v[0]]]
        cand.sort(key=lambda v: (w[u, v], rng.random()))
        for v in cand:
            used[v[0]] = True; path.append(v); dfs(acc + w[u, v]); path.pop(); used[v[0]] = False
    for u in nodes:
        if u[1] != 0 and u[0] == 0: pass
        used[u[0]] = True; path.append(u); dfs(0); path.pop(); used[u[0]] = False
    return best

if __name__ == "__main__":
    out = []
    for n, want, limit, climit in ((6, 400, 10**6, 200000), (7, 6, 10**6, 300000)):
        fr = frames(n); rng = random.Random(7)
        sols = exact_covers(n, fr, rng, want, limit)
        bestall = None
        for sol in sols:
            trails = [fr[i][0] for i in sol]
            b = best_chain(n, trails, rng, climit)
            if bestall is None or b[0] < bestall[0]: bestall = (b[0], trails, b[1])
            if b[0] == 0: break
        line = f"n={n}: frames {len(fr)}, exact frame covers examined {len(sols)}, min junction excess found {bestall[0] if bestall else None}"
        if bestall and bestall[2]:
            order = [bestall[1][i][j] for i, j in bestall[2]]
            st = [tuple(p) for p in order]
            route = route_of(st, n); N = math.factorial(n)
            L = n + sum(cost(route[i], route[i + 1], n) for i in range(N - 1))
            f = sum(math.factorial(n - i) for i in range(4)) + n - 4
            line += f"; best route length {L} (f(n) = {f}), covering {len(set(route)) == N and len(route) == N}"
        print(line, flush=True); out.append(line)
    open(os.path.join(HERE, "..", "certs", "framecover.txt"), "w").write("\n".join(out) + "\n")
