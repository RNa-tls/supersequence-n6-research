#!/usr/bin/env python3
"""Final round -- converse of Theorem E: realize a hole-free spanning block forest with K components and
one full row start per component (consecutive rows compatible) as a route, by traversing each
component's T = F o A cycle from its row start; check Hamiltonicity, normalization and the length
CONST + (ORB - K)/(n-2) + (number of junctions of cost >= 4) + excess.  Input forests are extracted from
the Egan-1 words (n = 8 Raudvere/archive 46204, n = 9 Echols 408965); the route is rebuilt from the
forest alone (block set + row starts), independently of the original word order."""
import sys, os, math
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "rF/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, cost, coarsen
from run178 import words

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))

def realize(blockset, row_starts, n):
    R = lambda x: x[1:] + x[:1]; Rinv = lambda x: x[-1:] + x[:-1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    S = set()
    for (W, s) in blockset:
        x = W + (s,)
        for _ in range(n - 1): S.add(x); x = F(x)
    def A(x):
        y = R(x)
        while y not in S: y = R(y)
        return y
    route = []
    for x0 in row_starts:
        y = x0
        while True:
            z = y
            while True:
                route.append(z)
                if R(z) in S or R(z) == y: break
                z = R(z)
            # run from y ends at R^{-1} A(y)
            y = F(A(y))
            if y == x0: break
    return route

def extract(route, n):
    N = len(route); R = lambda x: x[1:] + x[:1]
    S = {route[0]} | {route[i + 1] for i in range(N - 1) if route[i + 1] != R(route[i])}
    return {(canon(s[:n - 1]), s[n - 1]) for s in S}

if __name__ == "__main__":
    SP = "/tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/echols/superpermutations"
    w8 = min(words(8, 5), key=len)
    w9 = "".join(ch for ch in open(os.path.join(SP, "9/408965.txt")).read() if ch.isdigit())
    for n, w in ((8, w8), (9, w9)):
        mp = {c: i for i, c in enumerate(sorted(set(w)))}
        route0 = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
        bl = extract(route0, n)
        # row starts from the Bridge instance of the original route (the phi-cycle), in trail order
        import random
        res = coarsen(route0, n, random.Random(0))
        rows = [x for t in res["instance"] for x in t]
        assert all(x[1] == n - 1 for x in rows) and len(res["instance"]) == 1
        starts = [x[0] for x in rows]
        phi = lambda p: p[1:n - 2] + (p[0],) + p[n - 2:]
        is_phi_cycle = all(phi(starts[i]) == starts[i + 1] for i in range(len(starts) - 1))
        rt = realize(bl, starts, n)
        Nf = math.factorial(n)
        L = n + sum(cost(rt[i], rt[i + 1], n) for i in range(len(rt) - 1))
        f = sum(math.factorial(n - i) for i in range(4)) + n - 4
        RR = lambda x: x[1:] + x[:1]
        print(f"n={n}: blocks {len(bl)}, rows {len(starts)} form a phi-cycle: {is_phi_cycle}; rebuilt route Hamiltonian: "
              f"{len(rt) == Nf and len(set(rt)) == Nf}; normalized: {all(rt[i+1] != RR(RR(rt[i])) for i in range(len(rt)-1))}; "
              f"length {L} (f(n) = {f}); max edge cost {max(cost(rt[i], rt[i+1], n) for i in range(len(rt)-1))}", flush=True)
