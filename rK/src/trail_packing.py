#!/usr/bin/env python3
"""Round K -- break attempt: class-level exact covers using NEW efficient closed trails.

A closed trail word W (syllables S_r/X_r of rI) with period m gives a class set; all its S_8 images
are columns.  Saving s = classes/6 - (chains + 1) (fractional allowed; the total is integral).
Stage 'maxdisj': maximum number of pairwise disjoint images (image 0 fixed, S_8 transitive).
Stage 'cover': maximum total saving of an exact cover by images of the given words, A, B and all
phi-sets (savings scaled by 6 to integers), CP-SAT.
usage: trail_packing.py stage 'WORD1;WORD2;...' [timelimit]"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import closed_classes, closed_letters
from fractions import Fraction
n = 8
def canon(p):
    k = p.index(0); return tuple(p[k:] + p[:k])
reps = sorted({canon(p) for p in itertools.permutations(range(n))}); cid = {c: i for i, c in enumerate(reps)}
def masks_of(cls):
    seen = set(); out = []
    for g in itertools.permutations(range(n)):
        m = 0
        for c in cls: m |= 1 << cid[canon(tuple(g[x] for x in c))]
        if m not in seen: seen.add(m); out.append(m)
    return out
def word_info(word):
    cls = closed_classes(n, word)
    letters, _, _ = closed_letters(n, word)
    k = len(letters); size = len(cls)
    return cls, k, size, Fraction(size, 6) - (k + 1)
def max_disjoint(masks, used=0, cur=0, best=0):
    cand = [m for m in masks if not (m & used)]
    if cur + len(cand) <= best: return best
    if not cand: return max(best, cur)
    for i, m in enumerate(cand):
        if cur + len(cand) - i <= best: break
        best = max(best, max_disjoint(cand[i + 1:], used | m, cur + 1, best))
    return best
if __name__ == "__main__":
    stage, words = sys.argv[1], [w.strip() for w in sys.argv[2].split(";") if w.strip()]
    tl = float(sys.argv[3]) if len(sys.argv) > 3 else 600
    t0 = time.time(); lib = []
    for w in words:
        cls, k, size, s = word_info(w); M = masks_of(cls)
        lib.append((w, M, size, s))
        print(json.dumps(dict(word=w, chains=k, classes=size, saving=str(s), images=len(M), sec=round(time.time() - t0, 1))), flush=True)
    if stage == "maxdisj":
        for w, M, size, s in lib:
            M0 = M[0]
            best = 1 + max_disjoint([m for m in M if not (m & M0)])
            print(json.dumps(dict(word=w, max_disjoint=best, capacity=5040 // size, sec=round(time.time() - t0, 1))), flush=True)
    elif stage == "cover":
        from ortools.sat.python import cp_model
        A = masks_of(closed_classes(n, "S3 S4 S3 S4 X4")); B = masks_of(closed_classes(n, "S2 S2 S2 S3 X3"))
        PH = set()
        for a, b in itertools.combinations(range(n), 2):
            groups = {}
            for i, c in enumerate(reps):
                C = tuple(x for x in c if x not in (a, b)); kk = C.index(min(C)); C = C[kk:] + C[:kk]
                groups.setdefault(C, 0); groups[C] |= 1 << i
            PH |= set(groups.values())
        cols = [(m, 42) for m in A] + [(m, 18) for m in B] + [(m, 0) for m in PH]   # savings x6
        for w, M, size, s in lib: cols += [(m, int(6 * s)) for m in M]
        mdl = cp_model.CpModel(); x = [mdl.NewBoolVar("") for _ in cols]
        cover = [[] for _ in range(5040)]
        for i, (m, sv) in enumerate(cols):
            mm = m; c = 0
            while mm:
                if mm & 1: cover[c].append(x[i])
                mm >>= 1; c += 1
        for c in range(5040): mdl.AddExactlyOne(cover[c])
        target = int(sys.argv[4]) if len(sys.argv) > 4 else 6 * 42 + 1
        mdl.Add(sum(sv * x[i] for i, (m, sv) in enumerate(cols) if sv) >= target)
        sv_ = cp_model.CpSolver(); sv_.parameters.max_time_in_seconds = tl; sv_.parameters.num_workers = 4
        st = sv_.Solve(mdl)
        print(json.dumps(dict(stage="cover", target_x6=target, status=sv_.StatusName(st), sec=round(sv_.WallTime(), 1))), flush=True)
