#!/usr/bin/env python3
"""Round X -- second implementation of the disjoint-placement count (rX/csrc/disjoint.c), with different data and
algorithm: the 5040 rotation classes are numbered, the action of all 40320 relabelings on classes is tabulated once
(T[g, class]), and for a pair (X, Y) the set of relabelings g with classes(X) and g(classes(Y)) disjoint is found by
elimination: start from all g and remove those that send the k-th class of Y into X, k = 1, 2, ...  The reversed
orientation uses the reversal map on classes.  Prints  nameX nameY count count_rev  for the requested pairs.
usage: disjoint2.py CHAINS.txt [all | first:K]"""
import sys, itertools
import numpy as np

def main():
    lines = [l.split() for l in open(sys.argv[1]) if l.strip()]
    names = [t[0] for t in lines]; ents = [t[2:2 + int(t[1])] for t in lines]
    # classes: canonical cyclic words starting with '8'
    cls = sorted({"8" + "".join(p) for p in itertools.permutations("1234567")}); idx = {c: i for i, c in enumerate(cls)}
    assert len(cls) == 5040
    def canon(w):
        i = w.index("8"); return w[i:] + w[:i]
    W = np.array([[int(ch) - 1 for ch in c] for c in cls], dtype=np.int8)          # 5040 x 8, digits 0..7
    perms = np.array(list(itertools.permutations(range(8))), dtype=np.int8)         # 40320 x 8
    key = np.full(8 ** 7, -1, dtype=np.int32)
    for i, c in enumerate(cls):
        k = 0
        for ch in c[1:]: k = k * 8 + int(ch) - 1
        key[k] = i
    T = np.empty((40320, 5040), dtype=np.int16)
    pw = (8 ** np.arange(6, -1, -1)).astype(np.int64)
    for s in range(0, 40320, 2016):
        g = perms[s:s + 2016]                                                          # G x 8
        img = g[:, W]                                                                  # G x 5040 x 8 (relabel digits)
        pos = np.argmax(img == 7, axis=2)                                              # position of symbol 8
        ar = (pos[:, :, None] + np.arange(8)[None, None, :]) % 8
        rot = np.take_along_axis(img, ar, axis=2)                                      # rotate so that 8 is first
        k = (rot[:, :, 1:].astype(np.int64) * pw).sum(axis=2)
        T[s:s + 2016] = key[k]
    assert (T >= 0).all()
    revmap = np.array([idx[canon(c[::-1])] for c in cls], dtype=np.int64)
    sets = [np.array(sorted({idx[canon(e)] for e in E}), dtype=np.int64) for E in ents]
    order = [np.random.default_rng(1).permutation(s) for s in sets]
    def count(i, j, rev):
        mask = np.zeros(5040, dtype=bool); mask[sets[i]] = True
        Y = order[j] if not rev else revmap[order[j]]
        G = np.arange(40320)
        for c in Y:
            G = G[~mask[T[G, c]]]
            if G.size == 0: break
        return int(G.size)
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    n = len(names) if mode == "all" else int(mode.split(":")[1])
    for i in range(n):
        for j in range(i, n):
            print(names[i], names[j], count(i, j, False), count(i, j, True), flush=True)

main()
