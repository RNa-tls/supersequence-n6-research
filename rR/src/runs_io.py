#!/usr/bin/env python3
"""Round R -- shared loader for runs.bin (Round P checker-B format): for t in 0..29, v in 0..1: int32 m, m x 8 uint8
(the first permutation of every run, in the version's cyclic order).  An option / run is addressed globally by
o = tofs[t] + v * m_t + k (trail-major, as in ckB.c).  The two versions of a trail cover the same 8-cycles of
permutations (classes) but mostly with different entry rotations, so the run set depends on the version vector."""
import struct
import numpy as np

n = 8

def load(path):
    f = open(path, "rb"); vers = {}
    for t in range(30):
        for v in range(2):
            m = struct.unpack("<i", f.read(4))[0]
            vers[(t, v)] = [tuple(int(c) for c in b) for b in np.frombuffer(f.read(8 * m), np.uint8).reshape(m, 8)]
    runs = []; tv = []; tofs = []; mlen = []
    for t in range(30):
        tofs.append(len(runs)); mlen.append(len(vers[(t, 0)]))
        for v in range(2):
            for k, r in enumerate(vers[(t, v)]): runs.append(r); tv.append((t, v, k))
    return runs, tv, tofs, mlen

def weight_matrix(runs):
    """W[x, y] = overlap distance from the last permutation of run x to the first permutation of run y (8 if none).
    The diagonal is set to 8."""
    N = len(runs); S = np.array(runs, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)   # last(x)
    W = np.full((N, N), 8, np.int8)
    from collections import defaultdict
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1).tolist(); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1).tolist()
        d = defaultdict(list)
        for j, key in enumerate(b): d[key].append(j)
        for i, key in enumerate(a):
            for j in d.get(key, ()): W[i, j] = k
    np.fill_diagonal(W, 8)
    return W
