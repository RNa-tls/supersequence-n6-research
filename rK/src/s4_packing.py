#!/usr/bin/env python3
"""Round K -- break attempt: maximum packings of S4^10 closed trails (330 classes, 50 chains,
saving 4 each) and how much of the complement phi-sets can cover.
Enumerates maximum packings containing image 0 (S_8 transitive), for each computes the maximum
number of pairwise disjoint phi-sets (all 28 pairs) inside the complement (exact B&B), and writes
the packings for routing.
usage: s4_packing.py [max_packings_to_enumerate]"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trail_packing import masks_of, word_info, reps
n = 8
t0 = time.time()
cls, k, size, s = word_info("S4")
X = masks_of(cls)
PH = set()
for a, b in itertools.combinations(range(n), 2):
    groups = {}
    for i, c in enumerate(reps):
        C = tuple(x for x in c if x not in (a, b)); kk = C.index(min(C)); C = C[kk:] + C[:kk]
        groups[C] = groups.get(C, 0) | (1 << i)
    PH |= set(groups.values())
PH = list(PH)
print(json.dumps(dict(S4_images=len(X), phi_sets=len(PH), sec=round(time.time() - t0, 1))), flush=True)
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 50
found = []
def search(chosen, used, cand, target):
    if len(found) >= LIMIT: return
    if len(chosen) == target: found.append(list(chosen)); return
    if len(chosen) + len(cand) < target: return
    for i, m in enumerate(cand):
        if len(chosen) + len(cand) - i < target: break
        search(chosen + [m], used | m, [x for x in cand[i + 1:] if not (x & m)], target)
X0 = X[0]
search([X0], X0, [x for x in X if not (x & X0)], 12)
print(json.dumps(dict(packings_of_12_found=len(found), sec=round(time.time() - t0, 1))), flush=True)
def max_disjoint_sets(masks, used=0, cur=0, best=(0, [])):
    cand = [m for m in masks if not (m & used)]
    if cur + len(cand) <= best[0]: return best
    if not cand: return (cur, []) if cur > best[0] else best
    for i, m in enumerate(cand):
        if cur + len(cand) - i <= best[0]: break
        r = max_disjoint_sets(cand[i + 1:], used | m, cur + 1, best)
        if r[0] > best[0]: best = (r[0], [m] + r[1]) if r is not best else best
    return best
results = []
for idx, p in enumerate(found):
    used = 0
    for m in p: used |= m
    inside = [ph for ph in PH if not (ph & used)]
    nphi, _ = max_disjoint_sets(inside)
    left = 5040 - 12 * 330 - 42 * nphi
    results.append(dict(packing=idx, phi_sets_inside=len(inside), max_disjoint_phi=nphi, classes_left=left))
    print(json.dumps(results[-1]), flush=True)
out = dict(packings=[[int(m).bit_length() for m in p] for p in found][:0], results=results, sec=round(time.time() - t0, 1))
json.dump(dict(results=results, packings=[[format(m, "x") for m in p] for p in found]),
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "s4_packing.json"), "w"))
print(json.dumps(dict(done=True, sec=round(time.time() - t0, 1))), flush=True)
