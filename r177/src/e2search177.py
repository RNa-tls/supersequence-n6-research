#!/usr/bin/env python3
"""Round 177 -- exhaustive E2 counterexample search with UNRESTRICTED neighbour charge.

Run R = n-3 full rows p, phi p, ..., phi^{n-4} p, p = identity (WLOG: every full run is a
phi-chain in one frame, and relabelling puts its first start at the identity).
x = any row (any length 1..n-1, any interior omission set) with beta(x) = alpha(p);
y = any row with alpha(y.start) = beta(phi^{n-4} p).
A counterexample to E2 is x R y a ModelTrail with charge(x) >= 2 and charge(y) >= 2
(then R is a maximal full run of n-3 rows flanked by charge >= 2 rows).
For every valid (x, y) we record (charge x, charge y) and the boundary class of x and y
(X1..X3 / Y1..Y3 of r177 report section 3), classified from the definitions.
Checker: A (direct hexagon semantics) for the search, B (Lemma U) re-checks every hit.
usage: e2search177.py n [n ...] [--checkerB]"""
import json, os, sys
from itertools import permutations, combinations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB


def phi(n, s): return s[1:n - 2] + (s[0],) + s[n - 2:]


def search(n, use="A"):
    A, B = CheckerA(n), CheckerB(n)
    K = A if use == "A" else B        # checker used for the whole search
    Other = B if use == "A" else A    # the other one re-checks every hit
    p = tuple(range(n))
    R = [(p, n - 1, ())]
    for _ in range(n - 4):
        R.append((phi(n, R[-1][0]), n - 1, ()))
    assert A.trail(R)[0]
    c = {i + 1: p[i] for i in range(n)}
    v, e, a, sg = c[n - 3], c[n - 2], c[n - 1], c[n]

    def all_rows(start):
        for l in range(1, n):
            inner = list(range(1, l - 1))
            for k in range(len(inner) + 1):
                for om in combinations(inner, k):
                    yield (start, l, om)

    def xclass(x):   # order of (l_n, l_1, l_2) in the last state
        last = A.states(x[0], x[1])[-1]
        t = (last[n - 1], last[0], last[1])
        return {(sg, a, e): "X1", (a, sg, e): "X2", (a, e, sg): "X3"}.get(t, "X-other")

    def yclass(y):   # order of the three leftovers at the end of y.start
        t = y[0][n - 3:]
        return {(v, a, sg): "Y1", (v, sg, a): "Y2", (sg, v, a): "Y3"}.get(t, "Y-other")

    alpha = p[:n - 3]
    xs = [x for q in permutations(range(n)) for x in all_rows(q)
          if K.beta(x) == alpha and K.charge(x) >= 1 and K.trail([x] + R)[0]]
    beta = K.beta(R[-1])
    ys = [y for t in permutations([s for s in range(n) if s not in beta]) for y in all_rows(beta + t)
          if K.charge(y) >= 1 and K.trail(R + [y])[0]]
    hits = []
    for x in xs:
        for y in ys:
            if K.disjoint(x, y):
                assert Other.trail([x] + R + [y])[0], "checkers disagree"
                hits.append((A.charge(x), A.charge(y), xclass(x), yclass(y), x, y))
    return xs, ys, hits


if __name__ == "__main__":
    out = {}
    use = "B" if "--checkerB" in sys.argv else "A"
    for n in [int(a) for a in sys.argv[1:] if not a.startswith("-")]:
        xs, ys, hits = search(n, use)
        by = {}
        for cx, cy, xc, yc, x, y in hits:
            by.setdefault((xc, yc), set()).add((cx, cy))
        ge2 = [h for h in hits if h[0] >= 2 and h[1] >= 2]
        print(f"[checker {use}] n={n}: legal left neighbours {len(xs)}, right {len(ys)}; legal x R y: {len(hits)}; "
              f"with both charges >= 2: {len(ge2)}")
        for k, s in sorted(by.items()):
            print(f"   {k}: charge pairs {sorted(s)}")
        out[n] = dict(hits=len(hits), both_ge2=len(ge2),
                      classes={f"{k[0]},{k[1]}": sorted(s) for k, s in by.items()},
                      examples_both_ge2=[dict(x=[list(h[4][0]), h[4][1], list(h[4][2])],
                                              y=[list(h[5][0]), h[5][1], list(h[5][2])],
                                              charges=[h[0], h[1]], cls=[h[2], h[3]]) for h in ge2[:5]])
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "certs", f"e2search_177_{use}.json"), "w"), indent=1)
