#!/usr/bin/env python3
"""Round K -- break attempt: exact cover of the 5040 classes of S_8 by bundle images of ALL special
pairs (Round I/J only used the {0,7} system).

Columns: every S_8-image of the class set of bundle A ("S3 S4 S3 S4 X4", 672 classes, saving 7),
of bundle B ("S2 S2 S2 S3 X3", 504 classes, saving 3), and every phi-set P({a,b},C) (42 classes,
saving 0) for all 28 pairs.  Saving = classes/6 - (chains + 1); L = 46204 - sum saving + lambda.
Question 1: maximum number of pairwise disjoint A-images (symmetry: fix one).
Question 2: maximum total saving of an exact cover (CP-SAT), compared with 42 (the {0,7} optimum).
usage: mixed_packing.py stage [timelimit]"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rI", "src"))
from bundle_scan_lib import closed_classes
n = 8
def canon(p):
    k = p.index(0); return tuple(p[k:] + p[:k])
reps = sorted({canon(p) for p in itertools.permutations(range(n))})
cid = {c: i for i, c in enumerate(reps)}
assert len(reps) == 5040

def class_ids(cls):
    return sorted(cid[canon(tuple(c))] for c in cls)

def images(base_classes):
    """all distinct S_8 images of a class set (relabel symbols by g)"""
    out = {}
    for g in itertools.permutations(range(n)):
        key = tuple(sorted(cid[canon(tuple(g[x] for x in c))] for c in base_classes))
        if key not in out: out[key] = g
    return out

def phi_sets():
    out = set()
    for a, b in itertools.combinations(range(n), 2):
        groups = {}
        for i, c in enumerate(reps):
            C = tuple(x for x in c if x not in (a, b)); k = C.index(min(C)); C = C[k:] + C[:k]
            groups.setdefault(C, []).append(i)
        for C, lst in groups.items():
            assert len(lst) == (n - 2) * (n - 1)
            out.add(tuple(sorted(lst)))
    return sorted(out)

def build():
    t0 = time.time()
    A = closed_classes(n, "S3 S4 S3 S4 X4"); B = closed_classes(n, "S2 S2 S2 S3 X3")
    assert len(A) == 672 and len(B) == 504
    IA = images(A); IB = images(B); PH = phi_sets()
    print(json.dumps(dict(A_images=len(IA), B_images=len(IB), phi_sets=len(PH), sec=round(time.time() - t0, 1))), flush=True)
    return list(IA), list(IB), PH

if __name__ == "__main__":
    stage = sys.argv[1]; tl = float(sys.argv[2]) if len(sys.argv) > 2 else 600
    IA, IB, PH = build()
    from ortools.sat.python import cp_model
    if stage == "maxA":
        # maximum number of pairwise disjoint A-images, image 0 fixed (S_8 is transitive on images)
        m = cp_model.CpModel(); x = [m.NewBoolVar(f"a{i}") for i in range(len(IA))]
        cover = [[] for _ in range(5040)]
        for i, S in enumerate(IA):
            for c in S: cover[c].append(x[i])
        for c in range(5040): m.AddAtMostOne(cover[c])
        m.Add(x[0] == 1); m.Maximize(sum(x))
        sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = 4
        st = sv.Solve(m)
        print(json.dumps(dict(stage="maxA", status=sv.StatusName(st), best=sv.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
                              bound=sv.BestObjectiveBound(), sec=round(sv.WallTime(), 1))), flush=True)
    elif stage == "cover":
        # maximum saving exact cover by A-, B-images and phi-sets of all pairs; A-image 0 fixed if any A used
        cols = [(S, 7) for S in IA] + [(S, 3) for S in IB] + [(S, 0) for S in PH]
        m = cp_model.CpModel(); x = [m.NewBoolVar(f"x{i}") for i in range(len(cols))]
        cover = [[] for _ in range(5040)]
        for i, (S, sv_) in enumerate(cols):
            for c in S: cover[c].append(x[i])
        for c in range(5040): m.AddExactlyOne(cover[c])
        target = int(sys.argv[3]) if len(sys.argv) > 3 else None
        obj = sum(sv_ * x[i] for i, (S, sv_) in enumerate(cols) if sv_)
        if target is not None: m.Add(obj >= target)
        m.Maximize(obj)
        sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = 4
        st = sv.Solve(m)
        res = dict(stage="cover", status=sv.StatusName(st), bound=sv.BestObjectiveBound(), sec=round(sv.WallTime(), 1))
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            res["best"] = sv.ObjectiveValue()
            res["nA"] = sum(sv.Value(x[i]) for i in range(len(IA))); res["nB"] = sum(sv.Value(x[len(IA) + i]) for i in range(len(IB)))
        print(json.dumps(res), flush=True)
