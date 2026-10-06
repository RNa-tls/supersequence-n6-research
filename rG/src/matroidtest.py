#!/usr/bin/env python3
"""Is the family of completion block-sets the base family of a matroid?  Enumerate ALL completions
(acyclic exact ownership covers) of a kernel by exhaustive Algorithm X, collect distinct block sets,
and test the basis-exchange axiom: for bases B1, B2 and x in B1-B2 there is y in B2-B1 with
B1 - x + y a base.  Report a counterexample if any."""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World
from ownx import build
from flowsat import verify

def all_completions(W, rows):
    A = analyse(W, rows); U = A["U"]; opts = build(W, A)
    X = {c: set() for c in U}; byblock = {}
    for i, (b, a, O) in enumerate(opts):
        for c in O: X[c].add(i)
        byblock.setdefault(b, []).append(i)
    sol = []; out = set()
    def solve():
        if not X:
            bs = frozenset(opts[i][0] for i in sol)
            if verify(W, rows, list(bs), W.n)[0]: out.add(bs)
            return
        c = min(X, key=lambda c: len(X[c]))
        for i in list(X[c]):
            log = []; cols = []
            for cc in opts[i][2]:
                for j in list(X[cc]):
                    for c2 in opts[j][2]:
                        if c2 in X and j in X[c2]: X[c2].discard(j); log.append((c2, j))
                cols.append((cc, X.pop(cc)))
            for j in byblock[opts[i][0]]:
                for c2 in opts[j][2]:
                    if c2 in X and j in X[c2]: X[c2].discard(j); log.append((c2, j))
            sol.append(i); solve(); sol.pop()
            for cc, s in reversed(cols): X[cc] = s
            for c2, j in reversed(log): X[c2].add(j)
    solve(); return out

if __name__ == "__main__":
    n = int(sys.argv[1]); W = World(n); rows = kernel_rows(n, sys.argv[2])
    bases = all_completions(W, rows)
    print(f"n={n} kernel {sys.argv[2]}: {len(bases)} distinct completion block-sets, sizes {set(map(len, bases))}")
    cex = None
    for B1 in bases:
        for B2 in bases:
            for xb in B1 - B2:
                if not any((B1 - {xb}) | {y} in bases for y in B2 - B1):
                    cex = (B1, B2, xb); break
            if cex: break
        if cex: break
    if cex:
        B1, B2, xb = cex
        print("basis exchange FAILS: B1 =", sorted(W.blocks[b] for b in B1), "\n  B2 =", sorted(W.blocks[b] for b in B2),
              "\n  x =", W.blocks[xb], "-> no y in B2-B1 makes B1-x+y a completion")
    else:
        print("basis exchange holds on this family")
