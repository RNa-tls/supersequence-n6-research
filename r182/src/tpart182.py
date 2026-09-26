#!/usr/bin/env python3
"""Round 182 -- exact partitions of all cyclic classes by T-rows (length n-3, no omissions), found by
randomized Algorithm X, then chained into trails by a maximum matching on the compatibility digraph
(beta(x) = alpha(y)); each matching cycle is broken once.  Exploratory (bounded)."""
import math, os, random, sys
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r176", "src"))
from checkA176 import CheckerA

def options(n, L):
    A = CheckerA(n); opts = {}
    for p in permutations(range(n)):
        row = (p, L, ())
        blk = A.block(p)
        key = (blk, p)
        opts[key] = (row, frozenset(A.visible(row)))
    return list(opts.values())

def exact_cover(items, opts, rng, limit=200000):
    X = {i: set() for i in items}
    for j, (_, cs, _b) in enumerate(opts):
        for c in cs: X[c].add(j)
    blkof = {}
    sol = []; cnt = [0]; usedblk = set()
    A = None
    def select(j):
        cols = []
        for c in opts[j][1]:
            for k in list(X[c]):
                for c2 in opts[k][1]:
                    if c2 != c: X[c2].discard(k)
            cols.append((c, X.pop(c)))
        return cols
    def deselect(j, cols):
        for c, s in reversed(cols):
            X[c] = s
            for k in s:
                for c2 in opts[k][1]:
                    if c2 != c: X[c2].add(k)
    def solve():
        cnt[0] += 1
        if cnt[0] > limit: return False
        if not X: return True
        c = min(X, key=lambda c: (len(X[c]), rng.random()))
        cand = list(X[c]); rng.shuffle(cand)
        for j in cand:
            b = opts[j][2]
            if b in usedblk: continue
            usedblk.add(b); sol.append(j); cols = select(j)
            if solve(): return True
            deselect(j, cols); sol.pop(); usedblk.discard(b)
        return False
    ok = solve()
    return [opts[j][0] for j in sol] if ok else None

def chain(rows, n):
    A = CheckerA(n)
    byalpha = {}
    for i, r in enumerate(rows): byalpha.setdefault(r[0][:n - 3], []).append(i)
    succ = {i: [j for j in byalpha.get(A.beta(r), []) if j != i] for i, r in enumerate(rows)}
    match_r = {}
    def aug(u, seen):
        for v in succ[u]:
            if v in seen: continue
            seen.add(v)
            if v not in match_r or aug(match_r[v], seen):
                match_r[v] = u; return True
        return False
    for u in range(len(rows)): aug(u, set())
    nxt = {u: v for v, u in match_r.items()}
    prv = {v: u for v, u in match_r.items()}
    trails, seen = [], set()
    for s in range(len(rows)):
        if s in prv or s in seen: continue
        t = [s]; seen.add(s)
        while t[-1] in nxt: t.append(nxt[t[-1]]); seen.add(t[-1])
        trails.append(t)
    for s in range(len(rows)):           # remaining = cycles; break each once
        if s in seen: continue
        t = [s]; seen.add(s)
        while nxt[t[-1]] not in seen: t.append(nxt[t[-1]]); seen.add(t[-1])
        trails.append(t)
    return [[rows[i] for i in t] for t in trails]

if __name__ == "__main__":
    for n in (6, 7):
        L = n - 3
        A = CheckerA(n)
        raw = options(n, L)
        opts = [(r, cs, A.block(r[0])) for r, cs in raw]
        items = {A.hexagon(p) for p in permutations(range(n))}
        best = None
        for sd in range(4 if n == 6 else 2):
            rows = exact_cover(items, opts, random.Random(sd))
            if rows is None: print(n, "seed", sd, "no cover within limit"); continue
            tr = chain(rows, n)
            ORB = math.factorial(n - 2)
            k = len(rows); m = k - ORB; tau = len(tr); X = m + tau - 1
            ok = all(A.trail(t)[0] for t in tr)
            print(f"n={n} seed={sd} rows={k} m={m} trails={tau} X=m+eta={X} N_nf={k} ratio={k/X:.3f} trails_valid={ok}", flush=True)
