#!/usr/bin/env python3
"""Round 175 -- one-step transition table of charge<=1 rows, checked for several n.

For a charge<=1 row x at start p = c_1..c_n (types: full, loop, mark_j = full row with
position j omitted, 1 <= j <= n-3) the compatible starts are q = beta(x) + (a
permutation of the three symbols not in beta).  We label the six candidates
symbolically and record, for every row type of q, whether blocks differ and visible
masks are disjoint (pairwise condition with x only).

Symbolic labels (see r175/ROW_RUN_LEMMA_REPORT.md section 3):
  after a length-(n-1) row (full / mark_j):  beta = B = c_2..c_{n-2}, leftovers
      u = c_1, y = c_{n-1}, z = c_n; candidates B+uyz (= phi p), B+uzy, B+yuz,
      B+yzu, B+zuy, B+zyu.
  after a loop row: beta = A = c_1..c_{n-3}, x = c_{n-2}, y = c_{n-1}, z = c_n;
      candidates A+xyz (= p), A+xzy, A+yxz, A+yzx, A+zxy, A+zyx.
Relabelling invariance (RowModel.lean) => checking p = identity is exhaustive."""
import json, sys
from itertools import permutations


def table(n):
    def F(s): return s[1:n - 1] + (s[0], s[n - 1])
    def Rinv(s): return (s[n - 1],) + s[:n - 1]
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))

    def states(p):
        st = [p]
        for _ in range(n - 2):
            st.append(F(st[-1]))
        return st
    types = [("full", n - 1, None), ("loop", n - 2, None)] + \
            [("mark%d" % j, n - 1, j) for j in range(1, n - 2)]

    def row(p, t):
        _, l, om = t
        st = states(p)
        return dict(block=min(st), beta=Rinv(st[l - 1])[3:],
                    vis=frozenset(hexrep(st[i]) for i in range(l) if i != om))
    p = tuple(range(n))
    c = {i + 1: p[i] for i in range(n)}
    out = {}
    for tx in types:
        x = row(p, tx)
        beta = x["beta"]
        if tx[0] == "loop":
            names = dict(x=c[n - 2], y=c[n - 1], z=c[n])
            assert beta == p[:n - 3]
        else:
            names = dict(u=c[1], y=c[n - 1], z=c[n])
            assert beta == p[1:n - 2]
        inv = {v: k for k, v in names.items()}
        res = {}
        for tail in permutations(names.values()):
            q = beta + tail
            lab = ("A+" if tx[0] == "loop" else "B+") + "".join(inv[s] for s in tail)
            ok = []
            for ty in types:
                y = row(q, ty)
                if y["block"] != x["block"] and not (x["vis"] & y["vis"]):
                    ok.append(ty[0])
            res[lab] = ok
        out[tx[0]] = res
    return out


if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or [5, 6, 7, 8, 9]
    tabs = {n: table(n) for n in ns}

    # normalise: mark_j names relative to n (mark1, mark_{n-3}, other)
    def norm(n, name):
        if not name.startswith("mark"):
            return name
        j = int(name[4:])
        return "mark1" if j == 1 else "mark(n-3)" if j == n - 3 else "mark(mid)"

    def normtab(n, t):
        o = {}
        for tx, res in t.items():
            k = norm(n, tx)
            o.setdefault(k, {})
            for lab, ok in res.items():
                s = sorted({norm(n, a) for a in ok})
                o[k].setdefault(lab, [])
                if s not in o[k][lab]:
                    o[k][lab].append(s)
        return o
    N = {n: normtab(n, tabs[n]) for n in ns}
    ref = N[ns[-1]]
    same = {n: N[n] == ref for n in ns}
    for tx in ref:
        print(tx)
        for lab, ok in ref[tx].items():
            print("   ", lab, ok)
    print("uniform in n:", same)
    if "--json" in sys.argv:
        pass
    json.dump(dict(ns=ns, table_largest_n=ref, uniform=same), open("r175/certs/transitions_175.json", "w"), indent=1)
