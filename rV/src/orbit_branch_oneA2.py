#!/usr/bin/env python3
"""Round V -- packings with EXACTLY ONE A walk (4666)^4, decided against a cutoff (proxy objective Q + LAM*T).

Decomposition (complete for the library TYPES.txt, density <= MAXDENS):
  * The A walks form one orbit (180 images) under the relabelings S6, so the A walk is image 0 of PK.images(A).
  * Let t be the cheapest non-A walk type present (order: density, then word).  If its density is >= DMAX =
    (CUTOFF_TARGET - (8 + LAM)) / 104 the packing costs >= TARGET.  Otherwise t = types[i] for one of the branches i;
    the image of t is disjoint from A image 0 and is taken up to the stabilizer of A image 0 (order 4).
  * For every (i, representative image): the other loops are packed by non-A types j >= i (sorted order) or left
    rowless (cost LAM each).  A row  sum cost * x <= CUTOFF - base  is added: status Infeasible proves that every
    packing of the sub-branch has proxy total > CUTOFF.
usage: orbit_branch_oneA2.py TYPES.txt WORK OUT.json [--lam 1.5] [--target 88] [--cutoff 87.75] [--maxdens 1.0]
                             [--timelimit 600] [--threads 3]
       orbit_branch_oneA2.py TYPES.txt WORK OUT.json --control A_IMAGES --cutoff C      (A images fixed, all non-A types)"""
import sys, os, json, subprocess, argparse, time
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL, packing as PK
ap = argparse.ArgumentParser(); ap.add_argument("types"); ap.add_argument("work"); ap.add_argument("out")
ap.add_argument("--lam", type=float, default=1.5); ap.add_argument("--target", type=float, default=88.0); ap.add_argument("--cutoff", type=float, default=87.75)
ap.add_argument("--timelimit", type=float, default=600); ap.add_argument("--threads", type=int, default=3); ap.add_argument("--maxdens", type=float, default=1.0)
ap.add_argument("--control", default=None)
a = ap.parse_args(); AW = "4666466646664666"
types = [t for t in PK.read_types(a.types, a.maxdens, a.lam) if t[3] != AW]; types.sort(key=lambda t: ((t[1] + a.lam * t[2]) / t[0], t[3]))
dens = [(t[1] + a.lam * t[2]) / t[0] for t in types]; dmax = (a.target - (8 + a.lam)) / 104; nb = sum(1 for d in dens if d < dmax - 1e-9)
imsA = PK.images(AW); A0 = imsA[0][1]
stab = [mp for mp in PK.PERMS if {"".join(mp[c] for c in x): v for x, v in A0.items()} == A0]

def solve(kept, allowed, base):
    kl = {SL.canon(x) for x in kept}; free = [l for l in SL.LOOPS if l not in kl]; fid = {l: j for j, l in enumerate(free)}
    tp = os.path.join(a.work, "ob2_types.txt"); open(tp, "w").write("".join("%d %d %d %s\n" % t for t in allowed))
    fp = os.path.join(a.work, "ob2_free.txt"); open(fp, "w").write("".join(l + "\n" for l in free))
    out = subprocess.run([os.path.join(a.work, "cols_within"), tp, fp], capture_output=True, text=True, check=True).stdout.split("\n")
    cols = []
    for line in out:
        if not line.strip(): continue
        Lc, Qc, Tc, wc, st = line.split(); rows = dict(PK.walk_from(wc, st)); assert not (set(rows) & set(kept))
        cols.append(([fid[SL.canon(x)] for x in rows], int(Qc), int(Tc), wc, st))
    nc = len(cols); nF = len(free); nvar = nc + nF; t0 = time.time()
    cost = np.array([c[1] + a.lam * c[2] for c in cols] + [a.lam] * nF, dtype=np.float64)
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit)
    h.addVars(nvar, np.zeros(nvar), np.ones(nvar)); h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), cost)
    h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
    byl = [[] for _ in range(nF)]
    for j, c in enumerate(cols):
        for l in c[0]: byl[l].append(j)
    for l in range(nF):
        idx = byl[l] + [nc + l]; h.addRow(1, 1, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    h.addRow(-highspy.kHighsInf, a.cutoff - base, nvar, np.arange(nvar, dtype=np.int32), cost)       # the cutoff row
    h.run(); st = h.getModelStatus(); info = h.getInfo(); feas = info.primal_solution_status == 2
    r = dict(free_loops=nF, columns=nc, status=h.modelStatusToString(st), proved_above_cutoff=(st == highspy.HighsModelStatus.kInfeasible),
             best_total=(round(info.objective_function_value + base, 3) if feas else None), sec=round(time.time() - t0, 1))
    if feas:
        sol = np.array(h.getSolution().col_value); rows = dict(kept)
        for j in range(nc):
            if sol[j] > 0.5: rows.update(dict(PK.walk_from(cols[j][3], cols[j][4])))
        sm = SL.summary(rows); r.update(Q_total=sm["Q"], T_total=sm["T"], walk_lengths=sm["walk_lengths"], rows=dict(sorted(rows.items())))
    return r

if a.control is not None:
    js = [int(x) for x in a.control.split(",")]; kept = {}
    for j in js: kept.update(imsA[j][1])
    r = solve(kept, types, len(js) * (8 + a.lam)); r.update(control_A_images=js, cutoff=a.cutoff)
    print({k: v for k, v in r.items() if k != "rows"}, flush=True); json.dump(r, open(a.out, "w"), indent=1); sys.exit(0)

res = []; done = set()
if os.path.exists(a.out): res = json.load(open(a.out))["sub_branches"]; done = {(r["branch"], r["rep"]) for r in res}
print("non-A types", len(types), "DMAX %.4f" % dmax, "branches", nb, "stabilizer of A image 0:", len(stab), flush=True)
for i in range(nb):
    L, Q, T, w = types[i]; seen = set(); reps = []
    for im in PK.images(w):
        if set(im[1]) & set(A0) or {SL.canon(x) for x in im[1]} & {SL.canon(x) for x in A0}: continue
        key = frozenset(im[1].items())
        if key in seen: continue
        reps.append(im[1])
        for mp in stab: seen.add(frozenset({"".join(mp[c] for c in x): v for x, v in im[1].items()}.items()))
    for k, rep in enumerate(reps):
        if (i, k) in done: continue
        kept = dict(A0); kept.update(rep); base = (8 + a.lam) + Q + a.lam * T
        r = solve(kept, types[i:], base); r.update(branch=i, rep=k, reps_in_branch=len(reps), type=w, L=L, Q=Q, T=T, density=round(dens[i], 4))
        res.append(r); print({kk: v for kk, v in r.items() if kk != "rows"}, flush=True)
        json.dump(dict(lam=a.lam, target=a.target, cutoff=a.cutoff, density_threshold=dmax, branches=nb, stabilizer_A0=len(stab), sub_branches=res), open(a.out, "w"), indent=1)
open_ = [r for r in res if not r["proved_above_cutoff"]]
print("sub-branches", len(res), "not proved above cutoff", len(open_), "least best", min([r["best_total"] for r in res if r["best_total"] is not None], default=None))
