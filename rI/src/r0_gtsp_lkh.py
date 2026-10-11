#!/usr/bin/env python3
"""r = 0 problem as a GTSP solved heuristically with LKH (Noon-Bean transformation to ATSP).
Clusters = cyclic classes; node = (class, run start s); original arc s -> t (different classes) has
cost c = cost(R^-1 s, t); one depot cluster (path ends).  Noon-Bean: nodes of a cluster are put on a
zero-cost cycle; the original arc (u -> w) becomes pred(u) -> w with cost c + M.
L = n + N - HEX + (tour cost - (#clusters) * M).  The resulting word is written and must be verified."""
import sys, os, json, math, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import cost
import elkai
n, runs, seeds = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
perms = list(itertools.permutations(range(n))); N = len(perms); HEX = N // n
canon = lambda p: min(p[i:] + p[:i] for i in range(n))
clusters = {}
for p in perms: clusters.setdefault(canon(p), []).append(p)
order = []; cl_of = {}
for ci, (c, ps) in enumerate(sorted(clusters.items())):
    for p in sorted(ps): cl_of[p] = ci; order.append(p)
idx = {p: i for i, p in enumerate(order)}
V = N + 1; D = N
pred = {}
for c, ps in clusters.items():
    ps = sorted(ps)
    for i, p in enumerate(ps): pred[p] = ps[i - 1]
M = 10 * (HEX + 2) * n; BIG = 1000 * M
W = [[BIG] * V for _ in range(V)]
for c, ps in clusters.items():
    ps = sorted(ps)
    for i, p in enumerate(ps): W[idx[p]][idx[ps[(i + 1) % len(ps)]]] = 0
Rinv = lambda s: s[-1:] + s[:-1]
for u in perms:
    e = Rinv(u); pu = idx[pred[u]]
    for w in perms:
        if cl_of[w] == cl_of[u]: continue
        W[pu][idx[w]] = cost(e, w, n) + M
    W[pu][D] = M          # u is last cluster: leave to depot
for w in perms: W[D][idx[w]] = 0
best = None
for sd in range(seeds):
    t0 = time.time()
    tour = elkai.DistanceMatrix(W).solve_tsp(runs=runs)
    if tour[-1] == tour[0]: tour = tour[:-1]
    k = tour.index(D); seq = tour[k + 1:] + tour[:k]
    # decode: selected node per cluster = entry node
    starts = []; i = 0
    while i < len(seq):
        p = order[seq[i]]; starts.append(p)
        i += len(clusters[canon(p)])
    assert len(starts) == HEX
    L = n + N - HEX + sum(cost(Rinv(a), b, n) for a, b in zip(starts, starts[1:]))
    print(json.dumps(dict(n=n, seed=sd, length=L, sec=round(time.time() - t0, 1))), flush=True)
    if best is None or L < best[0]: best = (L, starts)
L, starts = best
R = lambda s: s[1:] + s[:1]
ps = []
for s in starts:
    p = s
    for _ in range(n): ps.append(p); p = R(p)
word = list(ps[0])
for x, y in zip(ps, ps[1:]):
    c = cost(x, y, n); word.extend(y[n - c:])
outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"r0_gtsp_n{n}_{len(word)}.txt")
open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
print("wrote", outp, "length", len(word))
