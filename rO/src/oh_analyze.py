#!/usr/bin/env python3
"""Round O (section 8) -- anatomy of an order-hull LP solution.
For the orders pi_k in the support (weights lam_k) compute the exact fixed-order values F(pi_k);
compare sum lam_k F(pi_k) with the LP value: the difference is the 'option mixing' gain that the LP
obtains by routing option flows across different orders (cross-overs at shared trails).
Also reports trail-level statistics of the support: A positions, phi0/phi14 neighbours, the number of
distinct predecessor/successor pairs per trail.
usage: oh_analyze.py FAMILY.json E.npy OH_RESULT.json"""
import sys, os, json
from collections import Counter, defaultdict
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixed_order as FA

AT = [1, 8, 15, 22, 28, 29]


def main():
    fam, E_p, res_p = sys.argv[1:4]
    fo = FA.FixedOrder(fam, E_p)
    d = json.load(open(res_p))
    sup = [(p["order"], p["lam"]) for p in d["lambda_paths"] if p["lam"] > 1e-9]
    vals = [(fo.F(o), lam, o) for o, lam in sup]
    mix = sum(v * l for v, l, _ in vals)
    ctx = defaultdict(Counter)
    for o, lam in sup:
        for i, t in enumerate(o):
            ctx[t][(o[i - 1] if i else None, o[i + 1] if i + 1 < len(o) else None)] += lam
    apos = Counter()
    for o, lam in sup:
        for i, t in enumerate(o):
            if t in AT: apos[(o[i - 1] if i else None) in AT, (o[i + 1] if i + 1 < len(o) else None) in AT] += lam
    out = dict(lp=d["lp"], Lbest=d["Lbest"], support=len(sup), lam_weighted_F=mix, min_F_in_support=min(v for v, _, _ in vals),
               F_hist={str(k): round(sum(l for v, l, _ in vals if v == k), 4) for k in sorted(set(v for v, _, _ in vals))},
               contexts_per_trail={str(t): len(c) for t, c in sorted(ctx.items())},
               A_neighbour_types={f"pred_is_A={a},succ_is_A={b}": round(v, 4) for (a, b), v in apos.items()})
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
