#!/usr/bin/env python3
"""Round Z -- independent check of one reported triple (no code shared with the C tools): builds the class sets of X,
g(Y) (or g(rev Y)) and searches all h in S8 (both orientations of Z) for h(Z) disjoint from X and from g(Y); prints
the first such h and re-checks the three pairwise disjointnesses.  Lehmer ranks as in rX/csrc/disjoint_bits.c.
usage: verify_triple.py FPLIST X Y o g Z oz"""
import sys, itertools
fpl, X, Y, o, g, Z, oz = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6], int(sys.argv[7])
fact = [1, 1, 2, 6, 24, 120, 720, 5040, 40320]
def unrank(r):
    avail = list(range(8)); out = []
    for i in range(8):
        f = fact[7 - i]; d, r = divmod(r, f); out.append(avail.pop(d))
    return out
ch = {}
for l in open(fpl):
    t = l.split()
    if t[0] in (X, Y, Z): ch[t[0]] = t[2:]
def canon(w):
    k = w.index(7); return tuple(w[k:] + w[:k])
def classes(name, rev):
    out = set()
    for e in ch[name]:
        w = [int(c, 16) - 1 for c in e]
        if rev: w = w[::-1]
        out.add(canon(w))
    return out
def apply(perm, S): return {canon([perm[x] for x in c]) for c in S}
CX = classes(X, 0); CY = apply(unrank(g), classes(Y, o))
assert not (CX & CY), 'X and g(Y) overlap'
CZ = classes(Z, oz); U = CX | CY
found = None
for h in itertools.permutations(range(8)):
    hz = apply(h, CZ)
    if not (hz & U): found = (h, hz); break
assert found, 'no third placement'
h, hz = found
print('X', len(CX), 'classes; g(Y)', len(CY), '; h(Z)', len(hz), '; pairwise intersections:', len(CX & CY), len(CX & hz), len(CY & hz), '; h =', h, '; h(8) =', h[7] + 1)
