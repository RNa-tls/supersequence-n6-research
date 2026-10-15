#!/usr/bin/env python3
"""Round M -- self-tests of the exact neighbourhood evaluators (second, naive implementations).

1. local_exact.py Or-opt / swap deltas: for random moves the delta formula is compared with the
   cost of the explicitly rebuilt run order (list surgery + full recomputation).
2. trail_order_exact.py: for random trail orders the layered shortest path value is compared with
   (a) the length of the rebuilt route measured from scratch and (b) an independent brute force
   over versions/cuts for orders restricted to ... (all trails, but with the exact DP recomputed by a
   plain O(n_prev * n_cur) min over all predecessor/successor pairs for the phi-only layers).
usage: local_selftest.py WORD FAMILY.json DESCRIPTION.json [SAMPLES]"""
import sys, os, json, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def main():
    word, famp, descp = sys.argv[1], sys.argv[2], sys.argv[3]
    S = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
    rnd = random.Random(11)
    st = RA.starts_of_word(RA.load_word(word)); N = len(st)
    W = RA.weight_matrix(st).astype(np.int64)
    Wd = np.zeros((N + 1, N + 1), np.int64); Wd[:N, :N] = W
    tour = list(range(N + 1)); M = N + 1
    def cyc_cost(t): return sum(int(Wd[t[i], t[(i + 1) % len(t)]]) for i in range(len(t)))
    base = cyc_cost(tour)
    bad = 0
    for _ in range(S):
        l = rnd.randint(1, 200); i = rnd.randrange(M)
        seg = [(i + d) % M for d in range(l)]
        rest = [p for p in range(M) if p not in set(seg)]
        k = rnd.randrange(len(rest))                       # insert after rest[k]
        p = (i - 1) % M; q = (i + l) % M
        if rest[k] == p: continue
        Bf, Bl = tour[seg[0]], tour[seg[-1]]
        a_, b_ = tour[rest[k]], tour[rest[(k + 1) % len(rest)]]
        delta = int(Wd[tour[p], tour[q]] + Wd[a_, Bf] + Wd[Bl, b_] - Wd[tour[p], Bf] - Wd[Bl, tour[q]] - Wd[a_, b_])
        newt = []
        for idx, pp in enumerate(rest):
            newt.append(tour[pp])
            if idx == k: newt += [tour[x] for x in seg]
        bad += (cyc_cost(newt) - base != delta)
    sw_bad = 0
    for _ in range(S):
        l1 = rnd.randint(1, 60); l2 = rnd.randint(1, 60); i = rnd.randrange(M)
        pos = [(i + d) % M for d in range(l1 + l2)]
        A_ = tour[(i - 1) % M]; B = [tour[x] for x in pos[:l1]]; C = [tour[x] for x in pos[l1:]]; D = tour[(i + l1 + l2) % M]
        delta = int(Wd[A_, C[0]] + Wd[C[-1], B[0]] + Wd[B[-1], D] - Wd[A_, B[0]] - Wd[B[-1], C[0]] - Wd[C[-1], D])
        others = [tour[(i + l1 + l2 + d) % M] for d in range(M - l1 - l2)]
        newt = others + C + B                               # cyclic: ... A=others[-1], C, B, D=others[0]
        sw_bad += (cyc_cost(newt) - base != delta)
    res = dict(oropt_samples=S, oropt_mismatch=bad, swap_samples=S, swap_mismatch=sw_bad)
    print(json.dumps(res), flush=True)
    # trail_order_exact cross-check: naive layered DP (every predecessor/successor pair, plain wt)
    import trail_order_exact as TOE
    fam = json.load(open(famp)); desc = json.load(open(descp))
    layers, const = TOE.load_layers(fam)
    order0 = [d[0] for d in desc["description"]]
    def naive(order):
        lab = [-o[2] for o in layers[order[0]]]
        for t in order[1:]:
            prev = layers[t - 0] if False else None
        prevL = layers[order[0]]
        for t in order[1:]:
            cur = layers[t]
            nl = []
            for o in cur:
                nl.append(min(lab[i] + RA.wt(po[1], o[0]) for i, po in enumerate(prevL)) - o[2])
            lab = nl; prevL = cur
        return const + min(lab)
    orders = [order0]
    phis = [t for t in range(len(layers)) if len(layers[t]) == 84]
    for _ in range(2):
        r = list(order0); rnd.shuffle(r); orders.append(r)
    cmp = []
    for o in orders:
        v, pth = TOE.evaluate(layers, const, o, True)
        cmp.append(dict(dp=v, rebuilt=TOE.build(fam, pth), naive=naive(o)))
    res2 = dict(trail_order_checks=cmp, all_equal=all(c["dp"] == c["rebuilt"] == c["naive"] for c in cmp))
    print(json.dumps(res2), flush=True)

if __name__ == "__main__":
    main()
