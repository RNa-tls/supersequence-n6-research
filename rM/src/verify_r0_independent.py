#!/usr/bin/env python3
"""Round M -- independent verifier for r = 0 superpermutation words (n = 8).  Shares no code with
rI/rJ/rK/rL.  Everything is recomputed from the raw string.

Checks
  1. alphabet of size n, every one of the n! permutations occurs as a window of length n;
  2. the route (permutations in order of first occurrence) has the tight length
     len(word) = n + sum of overlap distances;
  3. r = 0: the route splits into blocks of n consecutive rotations, one block per cyclic class,
     every class exactly once (class partition);
  4. chain / trail decomposition: consecutive blocks joined by distance 2 are in one chain,
     chains joined by distance 3 are in one trail; q = #chains, tau = #trails,
     lambda = sum over joins of distance >= 4 of (distance - 4), E = q - (n-1)!/(n-1);
  5. the identity  len = n + n! + (n-1)! + (n-2)! - 3 + E + (tau - 1) + lambda
     (for n = 8: 46085 + E + (tau-1) + lambda) and J = E + (tau-1) + lambda.
usage: verify_r0_independent.py WORD [...]"""
import sys, math, json, hashlib, itertools

def verify(path):
    raw = open(path, "rb").read()
    text = "".join(ch for ch in raw.decode() if not ch.isspace())
    syms = sorted(set(text)); n = len(syms)
    idx = {c: i for i, c in enumerate(syms)}
    w = [idx[c] for c in text]
    N = math.factorial(n)
    # 1. all permutations
    first = {}
    for i in range(len(w) - n + 1):
        t = tuple(w[i:i + n])
        if len(set(t)) == n and t not in first: first[t] = i
    ok_all = len(first) == N
    # 2. tight length
    route = sorted(first, key=first.get)
    def dist(x, y):
        for k in range(n - 1, 0, -1):
            if x[k:] == y[:n - k]: return k
        return n
    d = [dist(route[i], route[i + 1]) for i in range(N - 1)]
    ok_tight = (len(w) == n + sum(d))
    # 3. r = 0 blocks
    rot = lambda p: p[1:] + p[:1]
    blocks = []; i = 0; ok_r0 = True
    while i < N:
        blk = [route[i]]
        while len(blk) < n and i + len(blk) < N and route[i + len(blk)] == rot(blk[-1]): blk.append(route[i + len(blk)])
        if len(blk) != n: ok_r0 = False; break
        blocks.append(blk[0]); i += n
    cls = lambda p: min(p[k:] + p[:k] for k in range(n))
    ok_part = ok_r0 and len({cls(b) for b in blocks}) == math.factorial(n - 1) and len(blocks) == math.factorial(n - 1)
    res = dict(file=path, sha256=hashlib.sha256(raw).hexdigest(), n=n, length=len(w), all_perms=ok_all,
               tight=ok_tight, r0=ok_r0, class_partition=ok_part)
    if not (ok_all and ok_tight and ok_r0 and ok_part): return res
    # 4. joins between consecutive blocks: distance from the block's last perm to the next block start
    last = lambda p: p[-1:] + p[:-1]
    J = [dist(last(blocks[k]), blocks[k + 1]) for k in range(len(blocks) - 1)]
    q = 1 + sum(1 for x in J if x != 2)
    tau = 1 + sum(1 for x in J if x >= 4)
    lam = sum(x - 4 for x in J if x >= 4)
    E = q - math.factorial(n - 1) // (n - 1)
    base = n + N + math.factorial(n - 1) + math.factorial(n - 2) - 3
    Jtot = E + (tau - 1) + lam
    res.update(q=q, E=E, tau=tau, lam=lam, J=Jtot, identity_ok=(len(w) == base + Jtot), base=base,
               join_hist={str(k): J.count(k) for k in sorted(set(J))})
    return res

if __name__ == "__main__":
    out = [verify(p) for p in sys.argv[1:]]
    for r in out: print(json.dumps(r))
