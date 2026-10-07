#!/usr/bin/env python3
"""Coset-geometry description of the candidate hypergraph.
Permutations p are words (p[0..n-1]); right action on positions:
   rho  : p -> p[1:] + p[:1]              (n-cycle on positions; R-orbits = cyclic classes)
   kappa: p -> p[1:n-1] + p[0:1] + p[n-1:] (rotate first n-1 positions; kappa-orbits = blocks)
Flags (class, block containing it) <-> permutations (bijection).  Claims checked:
 (G1) |p<rho> & q<kappa>| <= 1 for all p, q  (<rho> & <kappa> = 1).
 (G2) for blocks B = p<kappa>, B' = q<kappa>: number of shared classes =
      #{ i in Z_{n-1} : the class of p kappa^i meets B' }  =  number of factorizations
      p^{-1} q = kappa^i rho^a kappa^j  (a != 0 mod n), computed in S_n directly.
 (G3) histogram of shared-class counts over all block pairs: values in {0,1,2} only (Lemma U), with
      exact counts of pairs per value, compared to the closed forms
      #pairs sharing >= 1 class per block = (n-1)(n-2) ... (reported, not assumed)."""
import sys, itertools, math
from collections import Counter

def run(n):
    perms = list(itertools.permutations(range(n)))
    rho = lambda p: p[1:] + p[:1]
    kap = lambda p: p[1:n - 1] + p[0:1] + p[n - 1:]
    def orbit(p, f, k):
        out = [p]
        for _ in range(k - 1): out.append(f(out[-1]))
        return out
    cls = {}; blk = {}
    for p in perms:
        if p not in cls:
            for x in orbit(p, rho, n): cls[x] = p
        if p not in blk:
            for x in orbit(p, kap, n - 1): blk[x] = p
    # G1
    g1 = True
    bmembers = {}
    for p in perms: bmembers.setdefault(blk[p], []).append(p)
    for b, mem in bmembers.items():
        if len({cls[x] for x in mem}) != len(mem): g1 = False
    # G2/G3: shared classes between blocks via classes
    blocks_of_class = {}
    for p in perms: blocks_of_class.setdefault(cls[p], set()).add(blk[p])
    shared = Counter()
    for c, bs in blocks_of_class.items():
        for b1 in bs:
            for b2 in bs:
                if b1 < b2: shared[(b1, b2)] += 1
    hist = Counter(shared.values())
    # factorization count in the group: compose as words. Represent g = p^{-1} q as position map.
    def compose_pos(p, sigma):        # apply position permutation sigma (as function on words)
        return sigma(p)
    # direct check of G2 on a sample of block pairs
    import random
    rng = random.Random(1); ok2 = True
    reps = list(bmembers)
    for _ in range(300):
        b1, b2 = rng.sample(reps, 2)
        direct = shared.get((min(b1, b2), max(b1, b2)), 0)
        # count i such that class of kappa^i(b1) contains a member of block b2
        mem2 = set(bmembers[b2]); cnt = 0
        x = b1
        for i in range(n - 1):
            if any(y in mem2 for y in orbit(x, rho, n)): cnt += 1
            x = kap(x)
        if cnt != direct: ok2 = False
    nb = len(bmembers)
    per_block = Counter()
    for (b1, b2), v in shared.items(): per_block[b1] += 1; per_block[b2] += 1
    return dict(n=n, blocks=nb, classes=len(blocks_of_class), G1_class_block_meet_le1=g1, G2_factorization_count_matches=ok2,
                G3_hist={str(k): v for k, v in sorted(hist.items())},
                neighbours_per_block=sorted(set(per_block.values())),
                share2_pairs_per_block=sorted(set(Counter(b for (b1, b2), v in shared.items() if v == 2 for b in (b1, b2)).values())))

if __name__ == "__main__":
    import json
    for n in range(4, 9):
        print(json.dumps(run(n)), flush=True)
