#!/usr/bin/env python3
"""Round K -- for each packing of A-images (A0 fixed; all special pairs), the maximum number of
pairwise disjoint images of a second closed trail X in the complement (exact, bitset B&B).
Reports the best saving 7 nA + s_X nX per nA, and the class-count residue mod 42 (an exact cover
by A, X and phi-sets needs the uncovered rest to be a union of phi-sets, so its size must be a
multiple of 42).
usage: mixed_trail_enum.py 'WORD'"""
import sys, os, json, time, itertools
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trail_packing import masks_of, word_info, max_disjoint
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import closed_classes
n = 8
t0 = time.time()
word = sys.argv[1]
cls, k, size, s = word_info(word); X = masks_of(cls)
A = masks_of(closed_classes(n, "S3 S4 S3 S4 X4"))
A0 = A[0]; nb = [m for m in A if m != A0 and not (m & A0)]
packs = [[A0]]
def rec(chosen, used, cand):
    for i, m in enumerate(cand):
        packs.append(chosen + [m]); rec(chosen + [m], used | m, [x for x in cand[i + 1:] if not (x & m)])
rec([A0], A0, nb)
res = {}
for p in packs:
    used = 0
    for m in p: used |= m
    inside = [x for x in X if not (x & used)]
    best = max_disjoint(inside) if inside else 0
    res[len(p)] = max(res.get(len(p), 0), best)
X0 = X[0]; alone = 1 + max_disjoint([x for x in X if not (x & X0)])
rows = []
for nA in range(0, 7):
    nX = alone if nA == 0 else res.get(nA, 0)
    rows.append(dict(nA=nA, max_nX=nX, saving=str(7 * nA + s * nX), classes=672 * nA + size * nX))
out = dict(word=word, chains=k, classes=size, saving_each=str(s), images=len(X), table=rows, sec=round(time.time() - t0, 1))
print(json.dumps(out), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "mixed_trail_" + word.replace(" ", "") + ".json"), "w"), indent=1)
