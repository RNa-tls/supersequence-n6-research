#!/usr/bin/env python3
"""Independent (solver-free) check of the A/B packing bound over ALL special pairs.

Columns: the 5040 S_8-images of bundle A (672 classes, saving 7) and of bundle B (504 classes,
saving 3).  Claim: every family of pairwise class-disjoint A- and B-images has 7 nA + 3 nB <= 42.
Proof by exhaustive enumeration with bitsets (S_8 is transitive on A-images, so one A-image may be
fixed when nA >= 1, and one B-image when nA = 0):
  * every packing of A-images containing A0 is enumerated (cliques in the disjointness graph);
  * for each A-packing of size nA, the B-images inside the complement are listed and the maximum
    number of pairwise disjoint ones is computed exactly (branch and bound on bitsets);
  * nA = 0: maximum number of disjoint B-images (B0 fixed).
Shares no code with mixed_packing.py except the bundle trail generator of Round I."""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import closed_classes
n = 8
t0 = time.time()
def canon(p):
    k = p.index(0); return tuple(p[k:] + p[:k])
reps = sorted({canon(p) for p in itertools.permutations(range(n))}); cid = {c: i for i, c in enumerate(reps)}
def image_masks(base):
    seen = set(); out = []
    for g in itertools.permutations(range(n)):
        m = 0
        for c in base: m |= 1 << cid[canon(tuple(g[x] for x in c))]
        if m not in seen: seen.add(m); out.append(m)
    return out
A = image_masks(closed_classes(n, "S3 S4 S3 S4 X4")); B = image_masks(closed_classes(n, "S2 S2 S2 S3 X3"))
assert all(bin(m).count("1") == 672 for m in A) and all(bin(m).count("1") == 504 for m in B)
print(json.dumps(dict(A_images=len(A), B_images=len(B), sec=round(time.time() - t0, 1))), flush=True)

def max_disjoint(masks, used=0, start=0, best=0, cur=0):
    """maximum number of pairwise disjoint masks (also disjoint from `used`), simple B&B"""
    cand = [m for m in masks[start:] if not (m & used)]
    if cur + len(cand) <= best: return best
    if not cand: return max(best, cur)
    for i, m in enumerate(cand):
        if cur + len(cand) - i <= best: break
        best = max(best, max_disjoint(cand, used | m, i + 1, best, cur + 1))
    return best

def a_packings(A0):
    """all sets of pairwise disjoint A-images containing A0 (as lists of masks)"""
    nb = [m for m in A if m != A0 and not (m & A0)]
    out = [[A0]]
    def rec(chosen, used, cand):
        for i, m in enumerate(cand):
            nu = used | m; nc = [x for x in cand[i + 1:] if not (x & m)]
            out.append(chosen + [m]); rec(chosen + [m], nu, nc)
    rec([A0], A0, nb)
    return out

A0 = A[0]
packs = a_packings(A0)
from collections import Counter
sizes = Counter(len(p) for p in packs)
print(json.dumps(dict(A_packings_with_A0=dict(sizes), sec=round(time.time() - t0, 1))), flush=True)
best_total = 0; detail = {}
for p in packs:
    used = 0
    for m in p: used |= m
    inside = [b for b in B if not (b & used)]
    nb = max_disjoint(inside) if inside else 0
    tot = 7 * len(p) + 3 * nb
    key = len(p); detail[key] = max(detail.get(key, 0), nb)
    best_total = max(best_total, tot)
# nA = 0: maximum number of disjoint B-images, B0 fixed
B0 = B[0]
nb0 = 1 + max_disjoint([b for b in B if not (b & B0)])
best_total = max(best_total, 3 * nb0)
res = dict(max_B_given_nA={str(k): v for k, v in sorted(detail.items())}, max_B_alone=nb0,
           max_saving=best_total, sec=round(time.time() - t0, 1))
print(json.dumps(res), flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "ab_packing_enum.json"), "w"), indent=1)
assert best_total == 42
