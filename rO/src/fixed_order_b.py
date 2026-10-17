#!/usr/bin/env python3
"""Round O (section 2, implementation B) -- independent fixed-order value F(pi).

Independent of options.py, Efull.npy and fixed_order.py:
  * options are rebuilt from the family JSON (trail t, version v, opening edge k: entry = run k,
    exit = last permutation of run k-1);
  * the overlap weight w(x, y) = least s >= 1 with x[s:] == y[:8-s] is computed by direct tuple
    comparison, only for the pairs that the order actually needs;
  * the recurrence is run BACKWARDS:  B_30(o) = 0,  B_i(o) = min_{o'} e(o, o') + B_{i+1}(o'),
    F(pi) = min_o [cut(o) = 2] + B_1(o).
usage: fixed_order_b.py FAMILY.json ORDER(comma list | audit.json)"""
import sys, json

N = 8


def w(x, y):
    for s in range(1, N):
        if x[s:] == y[:N - s]: return s
    return N


def build(fam_path):
    fam = json.load(open(fam_path)); opts = {}
    for t, tr in enumerate(fam["trails"]):
        L = []
        for v, s in enumerate(tr["versions"]):
            runs = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            for k in range(len(runs)):
                p = runs[k - 1]; x = (p[7],) + p[:7]
                L.append((v, k, runs[k], x, w(x, runs[k])))     # (version, edge, entry, exit, cut)
        opts[t] = L
    return opts


def F(opts, order):
    nxt = None
    for i in range(len(order) - 1, -1, -1):
        cur = []
        for (v, k, en, ex, cut) in opts[order[i]]:
            if nxt is None: cur.append(0); continue
            best = None
            for (v2, k2, en2, ex2, cut2), val in zip(opts[order[i + 1]], nxt):
                c = w(ex, en2) - cut2 - 1 + val
                if best is None or c < best: best = c
            cur.append(best)
        nxt = cur
    return min((1 if cut == 2 else 0) + val for (v, k, en, ex, cut), val in zip(opts[order[0]], nxt))


def main():
    opts = build(sys.argv[1])
    a = sys.argv[2]
    order = [r["trail"] for r in json.load(open(a))["table"]] if a.endswith(".json") else [int(x) for x in a.split(",")]
    val = F(opts, order)
    print(json.dumps(dict(checker="B", order=order, F=val, J=77 + val)))


if __name__ == "__main__":
    main()
