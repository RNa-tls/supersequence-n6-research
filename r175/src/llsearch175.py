#!/usr/bin/env python3
"""Round 175 -- exhaustive falsification search for Lemma LL at small n.

Model = jlebar/superperm7-ge-5898 (Rows.lean, RowModel.lean, Coarsen.lean,
SearchSound.lean), read for general n:

  perm      word s = s_0 .. s_{n-1} over {0..n-1}
  R(s)      = s_1 .. s_{n-1} s_0                (rClass = R-orbit, the "hexagon")
  F(s)      = s_1 .. s_{n-2} s_0 s_{n-1}         (fBlock = F-orbit, n-1 states)
  Row       = (start p, length l in 1..n-1), states F^i p (i < l)
  beta(x)   = drop 3 (Rinv (F^{l-1} p)),  Rinv(s) = s_{n-1} s_0 .. s_{n-2}
  alpha(q)  = take (n-3) q
  MarkedRow = (Row, omitted), omitted positions i with 0 < i and i+1 < l
  charge    = (n-1-l) + |omitted|
  visible   = rClasses of states F^i p, i < l, i not omitted
  ModelTrail: consecutive rows beta(x) = alpha(y.start); all pairs: distinct
              blocks and disjoint visible masks.

LL question: max length of a ModelTrail all of whose rows have charge <= 1.
Rows of charge <= 1 are exactly:  full (l=n-1, no omission, charge 0),
loop (l=n-2, no omission, charge 1), marked full (l=n-1, one omission, charge 1).

Every contiguous sub-list of a ModelTrail is a ModelTrail (the conditions are
consecutive + pairwise), so the longest charge<=1 run inside any trail equals the
longest all-charge<=1 trail.  WLOG (relabel invariance, RowModel.lean) the first
row starts at the identity.

usage: llsearch175.py n [unmarked|marked] [out.json]
Prints the maximum and one witness of maximum length, independently re-verified."""
import json, sys
from itertools import permutations

sys.setrecursionlimit(100000)


def build(n, marked):
    def F(s): return s[1:n - 1] + (s[0], s[n - 1])
    def Rinv(s): return (s[n - 1],) + s[:n - 1]
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
    kinds = [("full", n - 1, None), ("loop", n - 2, None)]
    if marked:
        kinds += [("mark%d" % i, n - 1, i) for i in range(1, n - 2)]
    info = {}
    for p in permutations(range(n)):
        st = [p]
        for _ in range(n - 2):
            st.append(F(st[-1]))
        rows = []
        for name, l, om in kinds:
            vis = frozenset(hexrep(st[i]) for i in range(l) if i != om)
            rows.append((name, l, om, Rinv(st[l - 1])[3:], vis))
        info[p] = (min(st), rows)
    return info, F, Rinv, hexrep


def verify(n, walk):
    """Independent re-check of a walk [(start, length, omitted)], straight from the
    definitions (no shared tables)."""
    def F(s): return s[1:n - 1] + (s[0], s[n - 1])
    def R(s): return s[1:] + s[:1]
    def orbit(f, s, k):
        out = [s]
        for _ in range(k - 1):
            out.append(f(out[-1]))
        return out
    def rclass(s): return frozenset(orbit(R, s, n))
    rows = []
    for p, l, om in walk:
        assert sorted(p) == list(range(n))
        assert 1 <= l <= n - 1
        assert om is None or (0 < om and om + 1 < l)
        states = orbit(F, p, l)
        last = states[-1]
        rinv = orbit(R, last, n)[n - 1]          # R^{n-1} = R^{-1}
        beta = rinv[3:]
        charge = (n - 1 - l) + (0 if om is None else 1)
        vis = {rclass(states[i]) for i in range(l) if i != om}
        rows.append(dict(p=p, beta=beta, charge=charge, vis=vis,
                         block=frozenset(orbit(F, p, n - 1))))
    for a, b in zip(rows, rows[1:]):
        assert a["beta"] == b["p"][:n - 3], "compat"
    for i in range(len(rows)):
        assert rows[i]["charge"] <= 1
        for j in range(i + 1, len(rows)):
            assert rows[i]["block"] != rows[j]["block"], "block"
            assert not (rows[i]["vis"] & rows[j]["vis"]), "class"
    return True


def search(n, marked):
    info, *_ = build(n, marked)
    best = [0, None]
    nodes = [0]
    path = []

    def rec(beta, blocks, hexes):
        nodes[0] += 1
        rest = [c for c in range(n) if c not in beta]
        for q in permutations(rest):
            p = beta + q
            b, rows = info[p]
            if b in blocks:
                continue
            for name, l, om, nb, vis in rows:
                if vis & hexes:
                    continue
                path.append((p, l, om))
                if len(path) > best[0]:
                    best[0], best[1] = len(path), list(path)
                blocks.add(b)
                rec(nb, blocks, hexes | vis)
                blocks.discard(b)
                path.pop()

    p0 = tuple(range(n))
    b0, rows0 = info[p0]
    for name, l, om, nb, vis in rows0:
        path.append((p0, l, om))
        if len(path) > best[0]:
            best[0], best[1] = 1, list(path)
        rec(nb, {b0}, set(vis))
        path.pop()
    return best[0], best[1], nodes[0]


if __name__ == "__main__":
    n = int(sys.argv[1])
    marked = len(sys.argv) > 2 and sys.argv[2] == "marked"
    L, walk, nodes = search(n, marked)
    verify(n, walk)
    w = ["".join(map(str, p)) + ":%s" % ("full" if l == n - 1 and om is None else
                                         "loop" if om is None else "mark%d" % om)
         for p, l, om in walk]
    print(f"n={n} model={'marked' if marked else 'unmarked'} longest charge<=1 trail = {L} "
          f"(n-2 = {n-2}); nodes {nodes}; witness {w}")
    if len(sys.argv) > 3:
        json.dump(dict(n=n, model="marked" if marked else "unmarked", longest=L,
                       n_minus_2=n - 2, nodes=nodes, witness=w, witness_verified=True),
                  open(sys.argv[3], "w"), indent=1)
