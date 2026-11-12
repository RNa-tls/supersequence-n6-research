#!/usr/bin/env python3
"""Round V -- the branch "the packing contains an A walk (4666)^4" of src/orbit_branch.py, refined: for every set S of
pairwise disjoint A images (82 up to relabeling, file A_cliques.json) the exact optimum of  Q + LAM * T  over the
packings whose A walks are exactly S: the other loops are packed by the library types other than A (HiGHS).
usage: orbit_branch_A.py TYPES.txt WORK OUT.json [--lam 1.5] [--maxdens 1.0] [--timelimit 1200]"""
import sys, os, json, subprocess, argparse, time
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL, packing as PK
ap = argparse.ArgumentParser(); ap.add_argument("types"); ap.add_argument("work"); ap.add_argument("out"); ap.add_argument("--lam", type=float, default=1.5)
ap.add_argument("--timelimit", type=float, default=1200); ap.add_argument("--threads", type=int, default=2); ap.add_argument("--maxdens", type=float, default=1.0)
a = ap.parse_args(); AW = "4666466646664666"
types = [t for t in PK.read_types(a.types, a.maxdens, a.lam) if t[3] != AW]
ims = PK.images(AW); cliques = json.load(open(os.path.join(a.work, "A_cliques.json")))
tp = os.path.join(a.work, "obA_types.txt"); open(tp, "w").write("".join("%d %d %d %s\n" % t for t in types))
res = []; done = {}
if os.path.exists(a.out):
    for r in json.load(open(a.out))["branches"]: done[tuple(r["A_images"])] = r; res.append(r)
for cl in cliques:
    if tuple(cl) in done: continue
    kept = {}
    for j in cl: kept.update(ims[j][1])
    kl = {SL.canon(x) for x in kept}; free = [l for l in SL.LOOPS if l not in kl]; fid = {l: j for j, l in enumerate(free)}
    fp = os.path.join(a.work, "obA_free.txt"); open(fp, "w").write("".join(l + "\n" for l in free))
    out = subprocess.run([os.path.join(a.work, "cols_within"), tp, fp], capture_output=True, text=True).stdout.split("\n")
    cols = []
    for line in out:
        if not line.strip(): continue
        Lc, Qc, Tc, wc, st = line.split(); rows = dict(PK.walk_from(wc, st)); cols.append(([fid[SL.canon(x)] for x in rows], int(Qc), int(Tc), wc, st))
    nc = len(cols); nF = len(free); nvar = nc + nF; t0 = time.time(); k = len(cl); base = k * (8 + a.lam)
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit)
    h.addVars(nvar, np.zeros(nvar), np.ones(nvar)); h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), np.array([c[1] + a.lam * c[2] for c in cols] + [a.lam] * nF, dtype=np.float64))
    h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
    byl = [[] for _ in range(nF)]
    for j, c in enumerate(cols):
        for l in c[0]: byl[l].append(j)
    for l in range(nF):
        idx = byl[l] + [nc + l]; h.addRow(1, 1, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    h.run(); st = h.getModelStatus(); info = h.getInfo(); feas = info.primal_solution_status == 2
    r = dict(A_images=list(cl), A_walks=k, free_loops=nF, columns=nc, status=h.modelStatusToString(st), best_total=(round(info.objective_function_value + base, 3) if feas else None), lower_bound_total=round(info.mip_dual_bound + base, 3), sec=round(time.time() - t0, 1))
    if feas:
        sol = np.array(h.getSolution().col_value); rows = dict(kept)
        for j in range(nc):
            if sol[j] > 0.5: rows.update(dict(PK.walk_from(cols[j][3], cols[j][4])))
        sm = SL.summary(rows); r.update(Q_total=sm["Q"], T_total=sm["T"], walk_lengths=sm["walk_lengths"], rows=dict(sorted(rows.items())))
    res.append(r); print({kk: v for kk, v in r.items() if kk != "rows"}, flush=True)
    json.dump(dict(lam=a.lam, library_types_without_A=len(types), branches=res), open(a.out, "w"), indent=1)
lbs = [r["lower_bound_total"] for r in res]; print("branches", len(res), "least lower bound", min(lbs), "least best", min(r["best_total"] for r in res if r["best_total"] is not None))
