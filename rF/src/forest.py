#!/usr/bin/env python3
"""Final round -- extract the block forest of an Egan-1 word: touched blocks (all fully selected when
u = 0), class multiplicities, components, per-component block counts, special distribution, the rows."""
import math, sys, os, random
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "r182/src", "rF/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, cost, coarsen

def analyse(route, n):
    N = len(route)
    R = lambda x: x[1:] + x[:1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    S = {route[0]} | {route[i + 1] for i in range(N - 1) if route[i + 1] != R(route[i])}
    def blk(x):
        w = x[:n - 1]; return (min(w[i:] + w[:i] for i in range(n - 1)), x[n - 1])
    cls = lambda x: min(x[i:] + x[:i] for i in range(n))
    blocks = defaultdict(set)
    for s in S: blocks[blk(s)].add(s)
    full = all(len(v) == n - 1 for v in blocks.values())
    mult = Counter(cls(s) for s in S)
    # union-find blocks via classes
    par = {b: b for b in blocks}
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    bycls = defaultdict(list)
    for s in S: bycls[cls(s)].append(blk(s))
    for c, bl in bycls.items():
        for b in bl[1:]: par[find(b)] = find(bl[0])
    comp = Counter(find(b) for b in blocks)
    spec = Counter(b[1] for b in blocks)
    return dict(M=len(blocks), all_blocks_full=full, mult_hist=dict(sorted(Counter(mult.values()).items())),
                components=len(comp), comp_sizes=sorted(comp.values()), specials=dict(sorted(spec.items())))

if __name__ == "__main__":
    from run178 import words, to_route
    SP = "/tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/echols/superpermutations"
    w8 = min(words(8, 5), key=len)
    w9 = "".join(ch for ch in open(os.path.join(SP, "9/408965.txt")).read() if ch.isdigit())
    for n, w in ((8, w8), (9, w9)):
        mp = {c: i for i, c in enumerate(sorted(set(w)))}
        route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
        print(n, len(w), analyse(route, n), flush=True)
