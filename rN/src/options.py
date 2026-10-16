#!/usr/bin/env python3
"""Round N -- single-piece opening options of every trail and version, and the vectorised
boundary weight between an option's exit and another option's entry.
option = (trail, version, edge k): entry = st[k], exit = last(st[k-1]) as a PERM (the last perm of
run st[k-1]), cut = w(exit, entry).  e(o -> o') = w(exit(o), entry(o')) - cut(o') - 1."""
import json
import numpy as np

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def load(path):
    fam = json.load(open(path)); opts = []
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            m = len(st)
            for k in range(m):
                ex = last(st[k - 1]); en = st[k]
                opts.append(dict(t=t, v=v, k=k, entry=en, exit=ex, cut=wt(ex, en), m=m))
    return fam, opts

def weight_block(exits, entries):
    """W[i, j] = w(exits[i], entries[j]) for perm tuples (int8 matrix)"""
    X = np.array(exits, dtype=np.int64); Y = np.array(entries, dtype=np.int64)
    W = np.full((len(X), len(Y)), n, dtype=np.int8)
    for m in range(1, n):                 # overlap m -> weight n - m; process small overlaps first
        k = n - m
        sx = np.zeros(len(X), np.int64); py = np.zeros(len(Y), np.int64)
        for t in range(m):
            sx = sx * 8 + X[:, k + t]; py = py * 8 + Y[:, t]
        order = np.argsort(py, kind="stable"); spy = py[order]
        lo = np.searchsorted(spy, sx, "left"); hi = np.searchsorted(spy, sx, "right")
        for i in np.nonzero(hi > lo)[0]:
            W[i, order[lo[i]:hi[i]]] = k
    return W
