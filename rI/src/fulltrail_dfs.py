#!/usr/bin/env python3
"""Longest valid trail consisting only of FULL chains (any of the 5 cost-3 successors), by exhaustive
DFS (shape validity is independent of the start, so start = identity).  Also: longest such trail that
contains at least one non-bac step and does not reduce to a phi-cycle."""
import sys, itertools, time
sys.setrecursionlimit(100000)
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
n = int(sys.argv[1]); TL = float(sys.argv[2])
F = tuple(list(range(1, n - 1)) + [0, n - 1])
Fp = [tuple(range(n))]
for _ in range(n - 2): Fp.append(comp(Fp[-1], F))
def canon(p): return min(p[i:] + p[:i] for i in range(n))
steps = []
for sig in itertools.permutations((0, 1, n - 1)):
    if sig == (n - 1, 0, 1): continue               # R^2 x : same class
    T = tuple(list(range(2, n - 1)) + list(sig))
    steps.append(("".join("abc"[[0, 1, n - 1].index(z)] for z in sig), comp(Fp[n - 2], T)))
best = [0, None]; used = set(); t0 = time.time(); nodes = [0]
def dfs(P, word):
    nodes[0] += 1
    if time.time() - t0 > TL: return
    cl = [canon(comp(P, f)) for f in Fp]
    if any(c in used for c in cl): return
    used.update(cl)
    if len(word) + 1 > best[0]: best[0] = len(word) + 1; best[1] = "".join(w[0] for w in word)
    for name, pi in steps: dfs(comp(P, pi), word + [(name,)])
    used.difference_update(cl)
dfs(tuple(range(n)), [])
print(dict(n=n, longest_full_chain_trail=best[0], word=best[1], complete=time.time() - t0 <= TL, nodes=nodes[0], HEX_over_n1=len(list(itertools.permutations(range(n)))) // n // (n - 1)))
