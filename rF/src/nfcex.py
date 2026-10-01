#!/usr/bin/env python3
"""Final round -- explicit infinite counterexample family to NF on domain A (Theorem Q of the report).
Symbols 0..n-1, special s = n-1, moving letter Y0 = 0, patch special t0 = 1.
  s-rows : for every cyclic word f of {1..n-2} (fixed with f[0] = 1): start p = (f1..f_{n-3}, 0, f0, s),
           T-row (length n-3); trail = p, tm p, ..., tm^{n-3} p  (tm of R180; order n-2).
  patches: for every arrangement x of {2..n-2} and pair in {(0,s),(s,0)}: start q = x + pair + (1,),
           charge-1 row (length n-2); one trail per patch.
Verification: exact partition of all classes (independent hexagon count), distinct blocks, ModelTrail
of every trail (checkers A and B), pairwise disjointness (checker B, n <= 8), r = 0 realization
(Theorem Z) -> covering route, parameters directly and via bridge178.coarsen (n <= 8)."""
import math, os, random, sys, json
from itertools import permutations
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r176/src", "r178/src", "r182/src"): sys.path.insert(0, os.path.join(ROOT, d))
from checkA176 import CheckerA
from checkB176 import CheckerB

def family(n):
    s = n - 1
    tm = lambda p: (p[n - 2],) + p[:n - 4] + (p[n - 3], p[n - 4], p[n - 1])
    trails = []
    for rest in permutations(range(2, n - 1)):
        f = (1,) + rest
        p = f[1:] + (0, f[0], s)
        assert len(p) == n and p[n - 3] == 0
        t = []
        for _ in range(n - 2): t.append((p, n - 3, ())); p = tm(p)
        assert p == t[0][0]
        trails.append(t)
    for x in permutations(range(2, n - 1)):
        for pair in ((0, s), (s, 0)):
            trails.append([(x + pair + (1,), n - 2, ())])
    return trails

def verify(n, pairwise):
    A, B = CheckerA(n), CheckerB(n)
    tr = family(n); rows = [x for t in tr for x in t]
    ORB = math.factorial(n - 2); HEX = math.factorial(n - 1)
    vis = Counter(c for x in rows for c in A.visible(x))
    allc = {A.hexagon(p) for p in permutations(range(n))}
    exact = set(vis) == allc and all(v == 1 for v in vis.values())
    blocks_distinct = len({A.block(x[0]) for x in rows}) == len(rows)
    trailsA = all(A.trail(t)[0] for t in tr); trailsB = all(B.trail(t)[0] for t in tr)
    pw = None
    if pairwise:
        pw = all(B.disjoint(rows[i], rows[j]) for i in range(len(rows)) for j in range(i + 1, len(rows)))
    nnf = sum(1 for x in rows if A.charge(x) >= 1)
    return tr, dict(n=n, rows=len(rows), trails=len(tr), exact_partition=exact, blocks_distinct=blocks_distinct,
                    trails_checkerA=trailsA, trails_checkerB=trailsB, pairwise_B=pw, N_nf=nnf,
                    predicted=dict(rows=ORB + 2 * math.factorial(n - 3), trails=3 * math.factorial(n - 3),
                                   N_nf=n * math.factorial(n - 3), m=2 * math.factorial(n - 3)))

if __name__ == "__main__":
    from ttrail182 import to_route
    from r0routes182 import direct_params
    from bridge178 import coarsen, check_instance
    out = []
    for n in (6, 7, 8, 9):
        tr, d = verify(n, pairwise=(n <= 8))
        route = to_route(tr, n)
        dp = direct_params(route, n)
        d.update(route_direct=dp)
        if n <= 8:
            res = coarsen(route, n, random.Random(0))
            flat = [x for t in res["instance"] for x in t]
            d.update(bridge=dict(m=res["m"], r=res["r"], a=res["a"], b=res["b"], eta=res["eta"], D=res["D"],
                                 N_nf=sum(1 for x in flat if (n - 1 - x[1]) + len(x[2]) >= 1),
                                 instance_checkerB=check_instance(res, CheckerB(n))[0],
                                 instance_checkerA=check_instance(res, CheckerA(n))[0] if n <= 7 else None))
        X = dp["m"] + dp["b"] + dp["eta"]
        d.update(X=X, ratio=round(dp["N_nf"] / X, 3), n_over_5=n / 5)
        print(json.dumps(d), flush=True); out.append(d)
    json.dump(out, open(os.path.join(HERE, "..", "certs", "nfcex.json"), "w"), indent=1)
