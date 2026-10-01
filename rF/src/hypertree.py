#!/usr/bin/env python3
"""Final round -- Egan-1 construction search: kernel phi-cycle (n-2 full rows of special s, moving
letter Y) + blocks added one at a time, each meeting the covered class set in EXACTLY one class.
A complete growth gives a hole-free spanning block forest with n-2 components rooted at the kernel,
hence (Theorem E) a superpermutation of length f(n) = n!+(n-1)!+(n-2)!+(n-3)!+n-4."""
import sys, os, random, math
from itertools import permutations
from collections import defaultdict

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))

def setup(n):
    classes = sorted({canon(p) for p in permutations(range(n))})
    cid = {c: i for i, c in enumerate(classes)}
    blocks = []; bid = {}
    for c in classes:
        for t in range(n):
            i = c.index(t); W = canon(c[i + 1:] + c[:i])
            key = (W, t)
            if key not in bid: bid[key] = len(blocks); blocks.append(key)
    bcls = []
    for W, t in blocks:
        bcls.append([cid[canon(W[:g] + (t,) + W[g:])] for g in range(n - 1)])
    cblk = defaultdict(list)
    for b, cl in enumerate(bcls):
        for c in cl: cblk[c].append(b)
    return classes, blocks, bcls, cblk, bid, cid

def grow(n, rng, data, kernel_starts):
    classes, blocks, bcls, cblk, bid, cid = data
    covered = [False] * len(classes); cnt = [0] * len(blocks); used = [False] * len(blocks)
    order = []
    def add(b):
        used[b] = True; order.append(b)
        for c in bcls[b]:
            if not covered[c]:
                covered[c] = True
                for b2 in cblk[c]: cnt[b2] += 1
    for p in kernel_starts:
        W = canon(p[:n - 1]); add(bid[(W, p[n - 1])])
    ncov = sum(covered)
    while ncov < len(classes):
        # most constrained uncovered class
        best = None
        for c in range(len(classes)):
            if covered[c]: continue
            opts = [b for b in cblk[c] if not used[b] and cnt[b] == 1]
            if opts and (best is None or len(opts) < len(best[1])):
                best = (c, opts)
                if len(opts) == 1: break
        if best is None: return None, ncov
        c, opts = best
        b = rng.choice(opts); add(b); ncov = sum(covered)
    return order, ncov

if __name__ == "__main__":
    for n in (5, 6, 7, 8):
        data = setup(n); s = n - 1
        f = (1,) + tuple(range(2, n - 1))
        kernel = [f[j:] + f[:j] + (0, s) for j in range(n - 2)]
        best = 0; ok = None
        for sd in range(20 if n <= 7 else 4):
            order, ncov = grow(n, random.Random(sd), data, kernel)
            best = max(best, ncov)
            if order: ok = order; break
        M = math.factorial(n - 2) + math.factorial(n - 3) - 1
        print(f"n={n}: classes {len(data[0])}; complete growth {'FOUND, blocks ' + str(len(ok)) + ' (target ' + str(M) + ')' if ok else 'not found; best coverage ' + str(best)}", flush=True)
