#!/usr/bin/env python3
"""Final attack -- BFS depth (in block steps) of the attachment forest of known record words:
n = 7 (5906, kernel score 10), n = 8 (46204).  Roots = kernel row blocks (Bridge rows)."""
import sys, os, random
from collections import defaultdict, deque
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen
from run178 import words

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))
for n, L in ((7, 5906), (8, 46204)):
    w = [w for w in words(n, 200) if len(w) == L][0]
    mp = {c: i for i, c in enumerate(sorted(set(w)))}
    route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
    R = lambda x: x[1:] + x[:1]
    S = {route[0]} | {route[i + 1] for i in range(len(route) - 1) if route[i + 1] != R(route[i])}
    blk = lambda x: (canon(x[:n - 1]), x[n - 1])
    res = coarsen(route, n, random.Random(0))
    roots = {blk(x[0]) for t in res["instance"] for x in t}
    bycls = defaultdict(set); byblk = defaultdict(set)
    for s in S: bycls[canon(s)].add(blk(s)); byblk[blk(s)].add(canon(s))
    depth = {b: 0 for b in roots}; q = deque(roots)
    while q:
        b = q.popleft()
        for c in byblk[b]:
            for b2 in bycls[c]:
                if b2 not in depth: depth[b2] = depth[b] + 1; q.append(b2)
    print(n, L, "blocks", len(byblk), "roots", len(roots), "reached", len(depth), "max depth", max(depth.values()))
