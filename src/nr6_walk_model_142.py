#!/usr/bin/env python3
"""NR6 hard core — the covering-walk reformulation, verified.

REFORMULATION (derived here, not taken from the R141 report).

Let CG_n be the digraph on the n! permutations whose edges (p,q) are the
CLEAN ones: the max-overlap spelling of p then q has no permutation window
strictly inside.  Weight w(p,q) = n - maxoverlap.

  * Every word X over the alphabet, read as its sequence of permutation
    windows in position order, is a WALK in CG_n: consecutive windows have
    no window between them, so each step is clean.  |X| = n + (walk weight),
    provided X is trimmed to start/end at a permutation window.
  * Conversely every walk spells such a word.
  * X covers all permutations  <=>  the walk is a covering walk.
  * X has exactly n! windows   <=>  the walk is a Hamilton PATH.

Hence, writing minHam = min cost of a Hamilton ORDER under the metric w
(a Hamilton order's geodesic spelling is a covering walk of the same cost,
and any covering walk shortcuts to its first-occurrence order at no greater
cost), and minCleanHam = min cost of a Hamilton path all of whose edges are
clean:

    L_n            = n + minHam
    min NR_n length = n + minCleanHam

So NR_n (threshold form) is exactly the statement minHam = minCleanHam in
the relevant range, and the outer 55/55 theorem is minCleanHam_6 >= 866.
"""
from __future__ import annotations
import json, sys
from itertools import permutations
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nr6_geometry_142 import Geo

ROOT = Path(__file__).resolve().parent.parent


def clean_cost(g, a, b, maxpad=2):
    """wc(a,b) = min gap of a CLEAN a->b connector (allowing padding)."""
    n, P = g.n, g.P
    pa, pb = P[a], P[b]
    for gap in range(g.W[a][b], n + 1):
        if gap < n and pa[gap:] != pb[:n - gap]:
            continue
        s = pa + pb[n - gap:]
        if all(len(set(s[i:i + n])) != n for i in range(1, gap)):
            return gap
    # pad with a repeated symbol
    for extra in range(1, maxpad * n + 1):
        s = pa + (pa[0],) * extra + pb
        if all(len(set(s[i:i + n])) != n for i in range(1, n + extra)):
            return n + extra
    return None


def repeat_bound(n, L):
    """Independent derivation of the repeat bound from run/hexagon counting.

    A covering walk with R repeated occurrences has M = n! + R vertex
    occurrences and M-1 edges, total weight C = L - n.
      sum_e (w_e - 1) = C - (M-1) = L - n - n! - R + 1.
    Weight-1 edges are exactly the sigma steps, so the number of non-sigma
    edges is at most that excess, and #runs = #non-sigma + 1.
    Every run lies inside one sigma-class (hexagon) and every one of the
    (n-1)! hexagons must be met, so #runs >= (n-1)!.  Therefore

        (n-1)!  <=  L - n - n! - R + 2      =>   R <= L - n - n! - (n-1)! + 2.
    """
    import math
    fact = math.factorial
    return L - n - fact(n) - fact(n - 1) + 2


def verify(n, Ls):
    g = Geo(n)
    N = g.N
    # sigma^k edges are exactly the max-transit ones
    sigk_ok = True
    for p in range(N):
        x = p
        for k in range(1, n):
            x = g.SIG[x]
            if k >= 2:
                t = [v for _, v in g.transit(p, x)]
                exp = []
                y = p
                for _ in range(k - 1):
                    y = g.SIG[y]
                    exp.append(y)
                if g.W[p][x] != k or t != exp:
                    sigk_ok = False
    # clean weight-2 successor is unique and equals tau = E.sigma
    w2 = all(len([b for b in range(N) if g.W[p][b] == 2 and g.clean(p, b)]) == 1
             and [b for b in range(N) if g.W[p][b] == 2 and g.clean(p, b)][0] == g.TAU[p]
             for p in range(N))
    # dirty weight-2 successor is sigma^2
    d2 = all([b for b in range(N) if g.W[p][b] == 2 and not g.clean(p, b)]
             == [g.SIG[g.SIG[p]]] for p in range(N))
    from collections import Counter
    wc_pen = Counter()
    for p in range(N):
        for q in range(N):
            if p == q:
                continue
            if not g.clean(p, q):
                c = clean_cost(g, p, q)
                wc_pen[(g.W[p][q], c)] += 1
    return dict(n=n, sigma_k_edges_are_max_transit=sigk_ok,
                unique_clean_w2_is_tau=w2, dirty_w2_is_sigma2=d2,
                clean_cost_of_dirty_edges={f"w{a}->wc{b}": c
                                           for (a, b), c in sorted(wc_pen.items())},
                repeat_bounds={L: repeat_bound(n, L) for L in Ls})


if __name__ == "__main__":
    out = {}
    for n, Ls in ((3, [9, 10]), (4, [33, 34, 35]), (5, [153, 154])):
        out[f"n{n}"] = verify(n, Ls)
    out["n6_repeat_bound"] = {L: repeat_bound(6, L) for L in (867, 871, 872)}
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_nr6_walk_model_142.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))
