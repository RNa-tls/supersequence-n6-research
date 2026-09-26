#!/usr/bin/env python3
"""Round 177 -- checks of the symbolic nine-case classification and of the explicit
counterexample family (both proved in r177/SEPARATOR_E2_REPORT.md), with checkers A
(direct) and B (Lemma U) from r176.

Notation (n >= 5): symbols c_1..c_n, C = c_1..c_{n-4}, v = c_{n-3}, e = c_{n-2},
a = c_{n-1}, s = c_n.  Run R = p, phi p, ..., phi^{n-4} p (p = identity): frame
E = <C v e>, pair {a, s}, gaps c_1..c_{n-3}; missing block B* = (<C v a e>, s).
Left boundary classes (x's last state):   X1 = a e C v s,  X2 = s e C v a,  X3 = e s C v a
Right boundary classes (y's first state): Y1 = e C v a s,  Y2 = e C v s a,  Y3 = e C s v a
Checked claims (for each n):
  (1) the only arrangements of the 3 leftovers whose boundary hexagon avoids the rows
      of R are exactly X1..X3 / Y1..Y3;
  (2) blocks: X1 = Y1 = B*,  X2 = Y2;  X1 != X2 != X3, Y3 distinct;
  (3) boundary hexagons: last(X1) = first(Y2),  last(X2) = first(Y1);
  (4) number of states of each block that share a hexagon with some row of R:
      X1, Y1: 0;  X2, Y2: n-3;  X3, Y3: n-2   (so charge >= that number);
  (5) counterexample family  x = (C v a e s, length n-2, omit {n-4}),  R,  y = (Y3 start,
      length 1):  ModelTrail for A and B, charges 2, 0.., n-2;  mutations rejected.
usage: nine177.py"""
import json, os, sys
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB


def phi(n, s): return s[1:n - 2] + (s[0],) + s[n - 2:]


def setup(n):
    p = tuple(range(n))
    R = [(p, n - 1, ())]
    for _ in range(n - 4): R.append((phi(n, R[-1][0]), n - 1, ()))
    c = {i + 1: p[i] for i in range(n)}
    C = tuple(c[i] for i in range(1, n - 3))
    v, e, a, s = c[n - 3], c[n - 2], c[n - 1], c[n]
    X = {"X1": (a, e) + C + (v, s), "X2": (s, e) + C + (v, a), "X3": (e, s) + C + (v, a)}
    Y = {"Y1": (e,) + C + (v, a, s), "Y2": (e,) + C + (v, s, a), "Y3": (e,) + C + (s, v, a)}
    return p, R, C, v, e, a, s, X, Y


def check(n):
    A, B = CheckerA(n), CheckerB(n)
    p, R, C, v, e, a, s, X, Y = setup(n)
    res = {}
    visR = set().union(*[A.visible(r) for r in R])
    # (1) leftover arrangements whose boundary hexagon avoids R
    alpha = p[:n - 3]
    lefts = []
    for t in permutations([e, a, s]):
        last = (t[1], t[2]) + alpha + (t[0],)          # l_1 l_2 alpha l_n
        if A.hexagon(last) not in visR: lefts.append(last)
    beta = A.beta(R[-1])
    rights = []
    for t in permutations([x for x in range(n) if x not in beta]):
        q = beta + t
        if A.hexagon(q) not in visR: rights.append(q)
    res["(1)"] = sorted(lefts) == sorted(X.values()) and sorted(rights) == sorted(Y.values())
    # (2) blocks
    blk = {k: A.block(v_) for k, v_ in {**X, **Y}.items()}
    res["(2)"] = (blk["X1"] == blk["Y1"] == A.block((e,) + C + (v, a, s)) and blk["X2"] == blk["Y2"]
                  and len({blk["X1"], blk["X2"], blk["X3"], blk["Y3"]}) == 4)
    # (3) boundary hexagons
    res["(3)"] = A.hexagon(X["X1"]) == A.hexagon(Y["Y2"]) and A.hexagon(X["X2"]) == A.hexagon(Y["Y1"])
    # (4) states of each block conflicting with R: count with A, and with B (per state, length-1 rows)
    cnt = {}
    for k, st in {**X, **Y}.items():
        states = A.states(st, n - 1)
        ca = sum(1 for q in states if A.hexagon(q) in visR)
        cb = sum(1 for q in states if not all(B.disjoint((q, 1, ()), r) for r in R))
        cnt[k] = (ca, cb)
    want = {"X1": 0, "Y1": 0, "X2": n - 3, "Y2": n - 3, "X3": n - 2, "Y3": n - 2}
    res["(4)"] = all(cnt[k] == (want[k], want[k]) for k in want)
    # (5) counterexample family
    xrow = (C + (v, a, e, s), n - 2, (n - 4,))
    yrow = (Y["Y3"], 1, ())
    W = [xrow] + R + [yrow]
    ra, rb = A.trail(W), B.trail(W)
    charges = [A.charge(r) for r in W]
    muts = {
        "x without omission (plain loop)": [(xrow[0], n - 2, ())] + R + [yrow],
        "x omission shifted": [(xrow[0], n - 2, (n - 5,) if n - 5 >= 1 else ())] + R + [yrow],
        "y length 2": [xrow] + R + [(yrow[0], 2, ())],
        "y from class Y1 (length 1)": [xrow] + R + [(Y["Y1"], 1, ())],
        "y from class Y2 (length 1)": [xrow] + R + [(Y["Y2"], 1, ())],
        "x start off by one (F^-1)": [((xrow[0][n - 2],) + xrow[0][:n - 2] + (s,), n - 2, (n - 4,))] + R + [yrow],
        "R extended to n-2 rows": [xrow] + R + [(phi(n, R[-1][0]), n - 1, ())] + [yrow],
    }
    mres = {k: (A.trail(w), B.trail(w)) for k, w in muts.items()}
    res["(5)"] = ra[0] and rb[0] and charges[0] == 2 and charges[-1] == n - 2 and all(c == 0 for c in charges[1:-1]) \
        and all(not a_[0] and not b_[0] for a_, b_ in mres.values())
    return res, cnt, charges, mres


if __name__ == "__main__":
    out = {}
    allok = True
    for n in range(5, 15):
        res, cnt, charges, mres = check(n)
        allok &= all(res.values())
        print(f"n={n}: {res}  hidden-counts {cnt}  cex charges {charges[0]},{charges[-1]}")
        out[n] = dict(claims=res, counts=cnt, cex_charges=charges,
                      mutants={k: [a_[1], b_[1]] for k, (a_, b_) in mres.items()})
    print("ALL CLAIMS HOLD" if allok else "FAILURE")
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "certs", "nine_177.json"), "w"), indent=1)
