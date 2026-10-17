#!/usr/bin/env python3
"""Round O (sections 2, 20) -- checker A vs checker B on random orders, plus mutation tests:
a corrupted excess matrix (one entry on the optimal path lowered) must change A's value and be
caught by the disagreement with B.  usage: fixed_order_crosscheck.py FAMILY.json E.npy N SEED"""
import sys, os, json, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixed_order as FA, fixed_order_b as FB

def main():
    fam, E_p, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    fa = FA.FixedOrder(fam, E_p); ob = FB.build(fam)
    rnd = random.Random(seed); res = []
    A = [1, 8, 15, 22, 28, 29]
    for t in range(n):
        order = list(range(30)); rnd.shuffle(order)
        if t % 3 == 0:                       # force some adjacent A blocks
            rest = [x for x in order if x not in A]; pos = rnd.randrange(len(rest) + 1)
            order = rest[:pos] + A[:3] + rest[pos:]; order = [x for x in order if x not in A[3:]] + A[3:]
        a = fa.F(order); b = FB.F(ob, order); res.append(dict(order=order, A=a, B=b))
    agree = all(r["A"] == r["B"] for r in res)
    # mutation: lower one excess entry on the optimal path of the 46185 order by 1 -> A changes, B does not
    d = json.load(open(os.path.join(HERE, "..", "..", "rN", "certs", "audit_superperm8_46185.json")))
    order = [r["trail"] for r in d["table"]]
    val, ch = fa.F(order, True)
    i = next(k for k in range(29) if fa.E[ch[k], ch[k + 1]] > 0)
    fa.E[ch[i], ch[i + 1]] -= 1
    mut = fa.F(order); b0 = FB.F(ob, order)
    print(json.dumps(dict(random_orders=n, agree=agree, values=sorted(set(r["A"] for r in res)),
                          min_random=min(r["A"] for r in res), mutation=dict(original=val, mutated_A=mut, B=b0, detected=(mut != b0)))))

if __name__ == "__main__":
    main()
