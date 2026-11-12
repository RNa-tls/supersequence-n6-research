#!/usr/bin/env python3
"""Round V -- exact optimum of the proxy objective  Q + LAM * T  over all packings by the walk types of a library,
by branching on the cheapest type present.  Types are ordered by density d = (Q + LAM * T) / L.  Branch i: the
packing contains an image of type i (fixed, by the relabeling symmetry) and no image of the types 0 .. i-1.
Branches are needed only for types with d < TARGET / 120: a packing without them costs at least TARGET.
Each branch is an exact integer programme (HiGHS).  usage: orbit_branch.py TYPES.txt WORK OUT.json [--lam 1.5] [--target 88]"""
import sys, os, json, subprocess, argparse, time
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL, packing as PK
ap = argparse.ArgumentParser(); ap.add_argument("types"); ap.add_argument("work"); ap.add_argument("out"); ap.add_argument("--lam", type=float, default=1.5); ap.add_argument("--target", type=float, default=88.0)
ap.add_argument("--timelimit", type=float, default=3000); ap.add_argument("--threads", type=int, default=2); ap.add_argument("--maxdens", type=float, default=1.0)
a = ap.parse_args()
types = [t for t in PK.read_types(a.types, a.maxdens, a.lam)]; types.sort(key=lambda t: ((t[1] + a.lam * t[2]) / t[0], t[3]))
dens = [(t[1] + a.lam * t[2]) / t[0] for t in types]; nb = sum(1 for d in dens if d < a.target / 120 - 1e-9)
print("library types", len(types), "branches", nb, flush=True); res = []
for i in range(nb):
    L, Q, T, w = types[i]; kept = dict(PK.walk_from(w)); kl = {SL.canon(x) for x in kept}
    free = [l for l in SL.LOOPS if l not in kl]; fid = {l: j for j, l in enumerate(free)}
    tp = os.path.join(a.work, "ob_types.txt"); open(tp, "w").write("".join("%d %d %d %s\n" % t for t in types[i:]))
    fp = os.path.join(a.work, "ob_free.txt"); open(fp, "w").write("".join(l + "\n" for l in free))
    out = subprocess.run([os.path.join(a.work, "cols_within"), tp, fp], capture_output=True, text=True).stdout.split("\n")
    cols = []
    for line in out:
        if not line.strip(): continue
        Lc, Qc, Tc, wc, st = line.split(); rows = dict(PK.walk_from(wc, st)); cols.append(([fid[SL.canon(x)] for x in rows], int(Qc), int(Tc), wc, st))
    nc = len(cols); nF = len(free); nvar = nc + nF; t0 = time.time()
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit)
    h.addVars(nvar, np.zeros(nvar), np.ones(nvar)); h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), np.array([c[1] + a.lam * c[2] for c in cols] + [a.lam] * nF, dtype=np.float64))
    h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
    byl = [[] for _ in range(nF)]
    for j, c in enumerate(cols):
        for l in c[0]: byl[l].append(j)
    for l in range(nF):
        idx = byl[l] + [nc + l]; h.addRow(1, 1, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    # stop as soon as the bound shows that the branch cannot go below the target
    h.run(); st = h.getModelStatus(); info = h.getInfo(); feas = info.primal_solution_status == 2
    obj = info.objective_function_value + Q + a.lam * T if feas else None; bound = info.mip_dual_bound + Q + a.lam * T
    r = dict(branch=i, type=w, L=L, Q=Q, T=T, density=round(dens[i], 4), free_loops=nF, columns=nc, status=h.modelStatusToString(st), best_total=obj, lower_bound_total=round(bound, 3), sec=round(time.time() - t0, 1))
    if feas:
        sol = np.array(h.getSolution().col_value); rows = dict(kept)
        for j in range(nc):
            if sol[j] > 0.5: rows.update(dict(PK.walk_from(cols[j][3], cols[j][4])))
        sm = SL.summary(rows); r.update(Q_total=sm["Q"], T_total=sm["T"], walk_lengths=sm["walk_lengths"], rows=dict(sorted(rows.items())))
    res.append(r); print({k: v for k, v in r.items() if k != "rows"}, flush=True)
    json.dump(dict(lam=a.lam, target=a.target, library_types=len(types), branches=res, density_of_first_type_without_branch=(dens[nb] if nb < len(dens) else None)), open(a.out, "w"), indent=1)
