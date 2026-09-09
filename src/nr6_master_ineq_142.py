#!/usr/bin/env python3
"""NR6 hard core — the exact DEFECT master inequality, and its verification.

For a trimmed covering word X of length L over n symbols, let
    M = number of permutation-window occurrences = n! + R   (R = repeats)
    P = number of maximal sigma-runs
    the walk has M-1 edges, of which exactly M-P are sigma steps,
    so there are P-1 non-sigma edges.
Then

    L = n + (M - P) + sum_{non-sigma} w
      = n + n! - 2 + R + P + sum_{non-sigma} (w - 2).

Every one of the (n-1)! sigma-classes must contain a run, so P >= (n-1)!.
Writing  Xrun = P - (n-1)! >= 0  and  Hvy = sum_{non-sigma}(w-2) >= 0:

    R + Xrun + Hvy  =  L - n - n! - (n-1)! + 2  -  (L_max - L)
    R + Xrun + Hvy <=  Lmax - n - n! - (n-1)! + 2  =: SLACK(n, Lmax).   (MASTER)

    n=3, Lmax=9   -> SLACK = 0
    n=4, Lmax=33  -> SLACK = 1
    n=5, Lmax=153 -> SLACK = 6
    n=6, Lmax=867 -> SLACK = 23
    n=6, Lmax=871 -> SLACK = 27

This is an exact identity plus P >= (n-1)!, so it is strictly finer than the
bare repeat bound R <= SLACK: repeats, extra runs and edge heaviness all draw
on ONE budget.  In particular a weight-6 edge costs 4 of the 27 at n=6, so a
counterexample with R repeats admits at most (SLACK-R)/4 weight-n edges --
exactly the edges at which the TRIM DICHOTOMY would let us shorten.
"""
from __future__ import annotations
import json, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nr6_geometry_142 import Geo

ROOT = Path(__file__).resolve().parent.parent


def slack(n, Lmax):
    return Lmax - n - math.factorial(n) - math.factorial(n - 1) + 2


def analyse_walk(g, walk):
    """Exact (L, M, P, R, Xrun, Hvy) of a covering walk given as a vertex list."""
    n = g.n
    M = len(walk)
    W = [g.W[walk[i]][walk[i + 1]] for i in range(M - 1)]
    cost = sum(W)
    L = n + cost
    P = 1 + sum(1 for w in W if w != 1)
    R = M - len({*walk})
    nonsig = [w for w in W if w != 1]
    Hvy = sum(w - 2 for w in nonsig)
    Xrun = P - math.factorial(n - 1)
    return dict(L=L, M=M, P=P, R=R, Xrun=Xrun, Hvy=Hvy,
                identity_ok=(L == n + math.factorial(n) - 2 + R + P + Hvy),
                sigma_steps=sum(1 for w in W if w == 1),
                nonsigma_edges=len(nonsig),
                weight_hist={w: W.count(w) for w in sorted(set(W))},
                covered=len({*walk}), defect_sum=R + Xrun + Hvy)


def check_solutions(n, budget, sols):
    g = Geo(n)
    S = slack(n, n + budget)
    out = []
    for walk in sols:
        a = analyse_walk(g, walk)
        a["slack"] = S
        a["master_ok"] = (a["defect_sum"] <= S)
        a["defect_equals_slack"] = (a["defect_sum"] == S)
        out.append(a)
    return out


if __name__ == "__main__":
    res = {"slack": {f"n{n},Lmax{L}": slack(n, L)
                     for n, L in ((3, 9), (4, 33), (4, 34), (5, 153),
                                  (6, 867), (6, 871), (6, 872))}}
    print(json.dumps(res, indent=1))
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_nr6_master_ineq_142.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
