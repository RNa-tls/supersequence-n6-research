#!/usr/bin/env python3
"""Greedoid test (n = 5 standard kernel): feasible sets = families F of candidate blocks whose
incidence graph with the root vertex r is a tree containing r (rooted Berge subtree).
Check accessibility and the greedoid augmentation axiom:
  |B| > |A|, A, B feasible  =>  some b in B - A with A + b feasible."""
import sys, os, itertools, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World
from hypertree import hyperedges, R

def rooted_tree(H, F):
    par = {}
    def f(a):
        while par.setdefault(a, a) != a: par[a] = par[par[a]]; a = par[a]
        return a
    verts = {R}
    for b in F:
        for v in H[b]:
            ra, rb = f(("b", b)), f(("v", v))
            if ra == rb: return False
            par[ra] = rb; verts.add(v)
    nodes = [("b", b) for b in F] + [("v", v) for v in verts]
    return len({f(x) for x in nodes}) == 1

n = 5; W = World(n); A = analyse(W, kernel_rows(n, "std")); H = hyperedges(W, A)
cand = sorted(H); P = len(A["U"]) // (n - 2)
feas = [frozenset(F) for k in range(0, P + 1) for F in itertools.combinations(cand, k) if rooted_tree(H, F)]
fs = set(feas)
acc = all(any((F - {b}) in fs for b in F) for F in feas if F)
cex = None
for A_ in feas:
    for B_ in feas:
        if len(B_) > len(A_) and not any((A_ | {b}) in fs for b in B_ - A_):
            cex = (A_, B_); break
    if cex: break
print(json.dumps(dict(feasible_sets=len(feas), accessible=acc, augmentation_holds=cex is None,
                      counterexample=None if cex is None else dict(A=sorted(map(str, (W.blocks[b] for b in cex[0]))),
                                                                   B=sorted(map(str, (W.blocks[b] for b in cex[1])))))))
