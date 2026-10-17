#!/usr/bin/env python3
"""Round O (section 3) -- interaction radius of the order value F(pi).

(a) Mixed second differences.  Take an order pi and two disjoint local modifications L (positions
    i, i+1 swapped) and R (positions j, j+1 swapped).  If F(pi) were a sum of terms each depending on
    a window of <= 2w+1 consecutive positions, every window sees at most one of L, R as soon as
    j - (i+1) > 2w, hence
        Delta = F(pi) - F(pi^L) - F(pi^R) + F(pi^LR) = 0.
    A nonzero Delta at gap g = j - i - 1 therefore PROVES that no exact representation of radius
    w < g/2 exists (for the class of orders containing these four).
(b) Pair potential c2(t, u) = min over options e(o_t, o_u) gives F(pi) >= LB_1(pi) = sum c2 along pi;
    its global minimum over all orders is an exact 30-node ATSP-path (MIP), a valid lower bound on
    min_pi F(pi).
(c) Triple potential: F(pi) >= sum_i min_{o_i} [ 1/2 min e(o_{i-1}, o_i) + 1/2 min e(o_i, o_{i+1}) ]
    (half of every link to each side; first/last links fully) -- reported for the 46185 order.
usage: radius.py FAMILY.json E.npy AUDIT.json OUT.json [n_pairs]"""
import sys, os, json, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixed_order as FA
import oh_lp as OH


def main():
    fam, E_p, audit, out = sys.argv[1:5]
    npairs = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    fo = FA.FixedOrder(fam, E_p)
    order = [r["trail"] for r in json.load(open(audit))["table"]]
    n = len(order); base = fo.F(order)
    rnd = random.Random(5)
    def sw(p, i):
        q = list(p); q[i], q[i + 1] = q[i + 1], q[i]; return q
    by_gap = {}
    pairs = [(i, j) for i in range(n - 1) for j in range(i + 2, n - 1)]
    rnd.shuffle(pairs)
    cache = {}
    def Fc(p):
        k = tuple(p)
        if k not in cache: cache[k] = fo.F(p)
        return cache[k]
    for (i, j) in pairs[:npairs]:
        f00 = base; f10 = Fc(sw(order, i)); f01 = Fc(sw(order, j)); f11 = Fc(sw(sw(order, i), j))
        D = f00 - f10 - f01 + f11; g = j - i - 1
        by_gap.setdefault(g, []).append(D)
    gap_stats = {g: dict(n=len(v), nonzero=sum(1 for x in v if x != 0), max_abs=max(abs(x) for x in v)) for g, v in sorted(by_gap.items())}
    far = [g for g, s in gap_stats.items() if s["nonzero"] > 0]
    # (b) pair potential and its exact global minimum
    NT = fo.NT
    c2 = np.zeros((NT, NT))
    for t in range(NT):
        for u in range(NT):
            if t != u: c2[t, u] = fo.E[np.ix_(fo.topts[t], fo.topts[u])].min()
    lb1_46185 = float(sum(c2[a, b] for a, b in zip(order, order[1:])))
    m = OH.OHMaster.__new__(OH.OHMaster); m.NT = NT
    v, pi, bound, st = OH.OHMaster.exact_path(m, c2, np.zeros(NT), np.zeros(NT))
    # (c) triple potential on the 46185 order
    tri = 0.0
    for k in range(n):
        A = fo.topts[order[k]]
        left = fo.E[np.ix_(fo.topts[order[k - 1]], A)].min(0) if k > 0 else np.zeros(len(A))
        right = fo.E[np.ix_(A, fo.topts[order[k + 1]])].min(1) if k < n - 1 else np.zeros(len(A))
        wl = 1.0 if k == 1 else 0.5; wr = 1.0 if k == n - 2 else 0.5
        tri += float((wl * left + wr * right).min()) if 0 < k < n - 1 else float(((0.5 if k == 0 else 0.5) * (left + right)).min())
    res = dict(base_F=base, pairs_tested=min(npairs, len(pairs)), gap_stats=gap_stats, max_gap_with_nonzero_delta=max(far) if far else None,
               pair_potential=dict(LB1_on_46185=lb1_46185, global_min_LB1=v, argmin=pi, status=st,
                                   c2_hist={str(k): int(c) for k, c in zip(*np.unique(c2[~np.eye(NT, dtype=bool)], return_counts=True))}),
               triple_potential_on_46185=tri)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(dict(base_F=base, max_gap_with_nonzero_delta=res["max_gap_with_nonzero_delta"], LB1_46185=lb1_46185, global_min_LB1=v, tri_46185=tri)))


if __name__ == "__main__":
    main()
