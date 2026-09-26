#!/usr/bin/env python3
"""Round 176 -- checker A: direct marked-model capacity search (no lemma of R175/R176).

M_n(g) := max { len(rows) : ModelTrail rows, chargeSum rows <= g }   (external
SearchSound.lean / CapTab.lean, read for general n):
  MarkedRow = (start p, length l in 1..n-1, omitted subset of interior positions
              {i : 0 < i, i+1 < l});  charge = (n-1-l) + |omitted|
  ModelTrail: beta(x) = alpha(next start) for consecutive rows; every pair of rows has
              distinct F-blocks and disjoint visible hexagon sets.
Only rows with charge <= g can occur, so for g <= 2 the lengths are n-1, n-2, n-3.
WLOG (simultaneous relabelling, RowModel.lean) the first row starts at the identity.
Pruning (sound): the suffix after a row is a ModelTrail with charge <= g - (charge so
far), hence has at most M(g - used) rows, for already computed smaller budgets.

usage: capA176.py n gmax [--witness out.json]"""
import json, sys
from itertools import permutations, combinations
sys.setrecursionlimit(100000)


def rows_of(n, gmax):
    def F(s): return s[1:n - 1] + (s[0], s[n - 1])
    def Rinv(s): return (s[n - 1],) + s[:n - 1]
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
    info = {}
    for p in permutations(range(n)):
        st = [p]
        for _ in range(n - 2):
            st.append(F(st[-1]))
        lst = []
        for l in range(max(1, n - 1 - gmax), n):
            base = n - 1 - l
            interior = [i for i in range(1, l - 1)]
            for k in range(0, gmax - base + 1):
                for om in combinations(interior, k):
                    vis = frozenset(hexrep(st[i]) for i in range(l) if i not in om)
                    lst.append((base + k, l, om, Rinv(st[l - 1])[3:], vis))
        info[p] = (min(st), lst)
    return info


def capacity(n, gmax):
    info = rows_of(n, gmax)
    M, wit = {}, {}
    for g in range(gmax + 1):
        best = [0, None]
        path = []

        def rec(beta, used, blocks, hexes):
            for q in permutations([c for c in range(n) if c not in beta]):
                p = beta + q
                b, rows = info[p]
                if b in blocks:
                    continue
                for c, l, om, nb, vis in rows:
                    u = used + c
                    if u > g or (vis & hexes):
                        continue
                    path.append((p, l, om))
                    if len(path) > best[0]:
                        best[0], best[1] = len(path), list(path)
                    if len(path) + M.get(g - u, 10 ** 9) > best[0]:
                        blocks.add(b)
                        rec(nb, u, blocks, hexes | vis)
                        blocks.discard(b)
                    path.pop()
        p0 = tuple(range(n))
        b0, rows0 = info[p0]
        for c, l, om, nb, vis in rows0:
            if c > g:
                continue
            path.append((p0, l, om))
            if len(path) > best[0]:
                best[0], best[1] = 1, list(path)
            rec(nb, c, {b0}, set(vis))
            path.pop()
        M[g], wit[g] = best
        print(f"n={n} g={g} M={best[0]}", flush=True)
    return M, wit


if __name__ == "__main__":
    n, gmax = int(sys.argv[1]), int(sys.argv[2])
    M, wit = capacity(n, gmax)
    if "--witness" in sys.argv:
        out = sys.argv[sys.argv.index("--witness") + 1]
        json.dump(dict(n=n, M=M, witness={g: [("".join(map(str, p)), l, list(om)) for p, l, om in w]
                                          for g, w in wit.items()}), open(out, "w"), indent=1)
