#!/usr/bin/env python3
"""Round M -- the RUN-LEVEL ATSP of an r = 0 family with fixed run starts.

An r = 0 word is a sequence of 5040 runs (run = the 8 left rotations of its start s); consecutive
runs s -> t cost w(last(s), t) with last(s) = s[7] s[0..6].  Every Hamiltonian path of the 5040 runs
(any order, fixed starts) is a superpermutation of length
        L = 8 + 7*5040 + sum of inter-run weights = 35288 + cost(path),
and this covers every r = 0 opening pattern of a closed-trail family (any number of openings per
trail, any fragments, any order, wrap-around F-steps): a cut between two runs is just a missing
arc.  J = L - 46085 = cost - 10797.
This module: run starts of a word / of a family version vector, the weight matrix, the word of an
order.  Self-contained (no imports from earlier rounds)."""
import math, json
import numpy as np

n = 8

def load_word(path):
    text = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(text)); return [al.index(c) for c in text]

def starts_of_word(word):
    seen = set(); route = []
    for i in range(len(word) - n + 1):
        p = tuple(word[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    assert len(route) == math.factorial(n)
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j], "not r = 0"
    return st

def family_versions(path):
    fam = json.load(open(path)); F = []
    for tr in fam["trails"]:
        F.append([[tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)] for s in tr["versions"]])
    return F

def last(p): return p[-1:] + p[:-1]

def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def weight_matrix(starts):
    """W[i, j] = w(last(starts[i]), starts[j]) (int8); diagonal set to 8 (never useful)."""
    N = len(starts)
    S = np.array(starts, dtype=np.int64)                      # N x 8
    X = np.concatenate([S[:, 7:], S[:, :7]], axis=1)          # last perms
    W = np.full((N, N), n, dtype=np.int8)
    for m in range(1, n):                                     # overlap m -> weight n - m (larger m wins)
        k = n - m
        sx = np.zeros(N, dtype=np.int64); py = np.zeros(N, dtype=np.int64)
        for t in range(m):
            sx = sx * 8 + X[:, k + t]; py = py * 8 + S[:, t]
        order = np.argsort(py, kind="stable"); spy = py[order]
        lo = np.searchsorted(spy, sx, "left"); hi = np.searchsorted(spy, sx, "right")
        for i in np.nonzero(hi > lo)[0]:
            W[i, order[lo[i]:hi[i]]] = k
    np.fill_diagonal(W, n)
    return W

def path_cost(W, order):
    o = np.asarray(order); return int(W[o[:-1], o[1:]].astype(np.int64).sum())

def word_of(starts, order):
    route = []
    for i in order:
        s = starts[i]; route += [s[j:] + s[:j] for j in range(n)]
    w = list(route[0])
    for x, y in zip(route, route[1:]):
        k = wt(x, y); w += list(y[n - k:])
    return w

def write_word(w, path):
    open(path, "w").write("".join(str(c + 1) for c in w) + "\n")
