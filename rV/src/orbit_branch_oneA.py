#!/usr/bin/env python3
"""Round V -- the last branch of the proxy optimum over library packings: packings with EXACTLY ONE A walk (4666)^4.
(Packings with two or more A walks: src/orbit_branch_A.py, all 81 sets proved.)
Branch on the cheapest non-A type t present, for the types with density (Q + LAM T) / L below DMAX = (TARGET - (8 + LAM)) / 104:
by the relabeling symmetry one image of t is fixed; the other loops are packed by the types at least as dense as t and
by exactly one A image (constraint: sum of the A columns = 1).  A packing with exactly one A walk and no such type costs
at least (8 + LAM) + 104 * DMAX = TARGET.
usage: orbit_branch_oneA.py TYPES.txt WORK OUT.json [--lam 1.5] [--target 88] [--maxdens 1.0] [--timelimit 1500]"""
import sys, os, json, subprocess, argparse, time
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL, packing as PK
ap = argparse.ArgumentParser(); ap.add_argument("types"); ap.add_argument("work"); ap.add_argument("out"); ap.add_argument("--lam", type=float, default=1.5); ap.add_argument("--target", type=float, default=88.0)
ap.add_argument("--timelimit", type=float, default=1500); ap.add_argument("--threads", type=int, default=3); ap.add_argument("--maxdens", type=float, default=1.0)
a = ap.parse_args(); AW = "4666466646664666"
types = [t for t in PK.read_types(a.types, a.maxdens, a.lam) if t[3] != AW]; types.sort(key=lambda t: ((t[1] + a.lam * t[2]) / t[0], t[3]))
dens = [(t[1] + a.lam * t[2]) / t[0] for t in types]; dmax = (a.target - (8 + a.lam)) / 104; nb = sum(1 for d in dens if d < dmax - 1e-9)
print("non-A types", len(types), "density threshold %.4f" % dmax, "branches", nb, flush=True)
res = []; done = set()
if os.path.exists(a.out):
    res = json.load(open(a.out))["branches"]; done = {r["type"] for r in res}
for i in range(nb):
    L, Q, T, w = types[i]
    if w in done: continue
    kept = dict(PK.walk_from(w)); kl = {SL.canon(x) for x in kept}; free = [l for l in SL.LOOPS if l not in kl]; fid = {l: j for j, l in enumerate(free)}
    tp = os.path.join(a.work, "ob1_types.txt"); open(tp, "w").write("".join("%d %d %d %s\n" % t for t in types[i:]) + "16 8 1 %s\n" % AW)
    fp = os.path.join(a.work, "ob1_free.txt"); open(fp, "w").write("".join(l + "\n" for l in free))
    out = subprocess.run([os.path.join(a.work, "cols_within"), tp, fp], capture_output=True, text=True).stdout.split("\n")
    cols = []
    for line in out:
        if not line.strip(): continue
        Lc, Qc, Tc, wc, st = line.split(); rows = dict(PK.walk_from(wc, st)); cols.append(([fid[SL.canon(x)] for x in rows], int(Qc), int(Tc), wc, st))
    nc = len(cols); nF = len(free); nvar = nc + nF; t0 = time.time(); base = Q + a.lam * T
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit)
    h.addVars(nvar, np.zeros(nvar), np.ones(nvar)); h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), np.array([c[1] + a.lam * c[2] for c in cols] + [a.lam] * nF, dtype=np.float64))
    h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
    byl = [[] for _ in range(nF)]
    for j, c in enumerate(cols):
        for l in c[0]: byl[l].append(j)
    for l in range(nF):
        idx = byl[l] + [nc + l]; h.addRow(1, 1, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    acols = [j for j, c in enumerate(cols) if c[3] == AW]
    h.addRow(1, 1, len(acols), np.array(acols, dtype=np.int32), np.ones(len(acols)))
    h.run(); st = h.getModelStatus(); info = h.getInfo(); feas = info.primal_solution_status == 2
    r = dict(type=w, L=L, Q=Q, T=T, density=round(dens[i], 4), free_loops=nF, columns=nc, A_columns=len(acols), status=h.modelStatusToString(st),
             best_total=(round(info.objective_function_value + base, 3) if feas else None), lower_bound_total=(round(info.mip_dual_bound + base, 3) if st != highspy.HighsModelStatus.kInfeasible else None), sec=round(time.time() - t0, 1))
    if feas:
        sol = np.array(h.getSolution().col_value); rows = dict(kept)
        for j in range(nc):
            if sol[j] > 0.5: rows.update(dict(PK.walk_from(cols[j][3], cols[j][4])))
        sm = SL.summary(rows); r.update(Q_total=sm["Q"], T_total=sm["T"], walk_lengths=sm["walk_lengths"], rows=dict(sorted(rows.items())))
    res.append(r); print({kk: v for kk, v in r.items() if kk != "rows"}, flush=True)
    json.dump(dict(lam=a.lam, target=a.target, density_threshold=dmax, branches=res), open(a.out, "w"), indent=1)
