#!/usr/bin/env python3
"""Round M -- CLUSTER OPTIMIZATION of an r = 0 word: keep the ORDER of the 5040 classes, re-choose
every run start freely among the 8 rotations of its class (exact layered shortest path, 5040 x 64).
This is the full r = 0 freedom for a fixed class order (any start per class, any world): the result
is the minimum length over all r = 0 words with that class order.
usage: cluster_opt.py WORD [OUT]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def rot(p, j): return p[j:] + p[:j]

def best_starts(classes_in_order, first=None):
    """classes_in_order: list of run starts (any rotation); returns (cost, list of starts)"""
    n = 8; L = len(classes_in_order)
    opts = [[rot(p, j) for j in range(n)] for p in classes_in_order]
    f = [0] * n if first is None else [0 if opts[0][j] == first else 10 ** 9 for j in range(n)]
    back = []
    for i in range(1, L):
        g = [10 ** 9] * n; b = [0] * n
        lasts = [RA.last(s) for s in opts[i - 1]]
        for jj, t in enumerate(opts[i]):
            for j in range(n):
                c = f[j] + RA.wt(lasts[j], t)
                if c < g[jj]: g[jj] = c; b[jj] = j
        f = g; back.append(b)
    j = min(range(n), key=lambda x: f[x]); cost = f[j]
    sel = [j]
    for b in reversed(back): j = b[j]; sel.append(j)
    sel.reverse()
    return cost, [opts[i][sel[i]] for i in range(L)]

def main():
    st = RA.starts_of_word(RA.load_word(sys.argv[1]))
    c0 = sum(RA.wt(RA.last(a), b) for a, b in zip(st, st[1:]))
    c, st2 = best_starts(st)
    changed = sum(1 for a, b in zip(st, st2) if a != b)
    res = dict(word=sys.argv[1], cost_before=c0, L_before=35288 + c0, cost_after=c, L_after=35288 + c, changed_starts=changed)
    if len(sys.argv) > 2 and c < c0:
        w = []
        route = []
        for s in st2: route += [rot(s, j) for j in range(8)]
        w = list(route[0])
        for x, y in zip(route, route[1:]): k = RA.wt(x, y); w += list(y[8 - k:])
        RA.write_word(w, sys.argv[2]); res["file"] = sys.argv[2]; res["measured"] = len(w)
    print(json.dumps(res))

if __name__ == "__main__":
    main()
