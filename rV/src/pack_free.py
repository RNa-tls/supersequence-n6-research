#!/usr/bin/env python3
"""Round V -- exact re-packing of a set of free loops, the rest of a selection being kept.
Columns = all images of the walk types of the library that lie inside the free loops (csrc/cols_within.c).
   minimise sum (Q_w + LAM * T_w) + LAM * (free loops left without a row)        (HiGHS, proved optimal when it says so)
Then all solutions with objective <= best + SLACK are enumerated with no-good cuts (up to --count).
usage: pack_free.py KEPT.json(rows of the kept walks) COLUMNS.txt OUT.jsonl [--lam 1.5] [--slack 3] [--count 50] [--objlam1max X]"""
import sys, os, json, time, argparse
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL, packing as PK
ap = argparse.ArgumentParser(); ap.add_argument("kept"); ap.add_argument("columns"); ap.add_argument("out"); ap.add_argument("--lam", type=float, default=1.5)
ap.add_argument("--slack", type=float, default=3.0); ap.add_argument("--count", type=int, default=50); ap.add_argument("--timelimit", type=float, default=300); ap.add_argument("--threads", type=int, default=2)
a = ap.parse_args()
kept = json.load(open(a.kept)); kept = {x: int(v) for x, v in kept.items()}; keptloops = {SL.canon(x) for x in kept}
free = [l for l in SL.LOOPS if l not in keptloops]; fid = {l: i for i, l in enumerate(free)}; nF = len(free)
cols = []
for line in open(a.columns):
    L, Q, T, w, st = line.split(); rows = dict(PK.walk_from(w, st)); loops = [fid[SL.canon(x)] for x in rows]; assert len(set(loops)) == int(L)
    cols.append((loops, rows, int(Q), int(T), w))
nc = len(cols); nvar = nc + nF
h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit)
cost = np.array([c[2] + a.lam * c[3] for c in cols] + [a.lam] * nF, dtype=np.float64)
h.addVars(nvar, np.zeros(nvar), np.ones(nvar)); h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), cost)
h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
byl = [[] for _ in range(nF)]
for j, c in enumerate(cols):
    for l in c[0]: byl[l].append(j)
def addrow(lo, hi, idx, val): h.addRow(lo, hi, len(idx), np.array(idx, dtype=np.int32), np.array(val, dtype=np.float64))
for l in range(nF): addrow(1, 1, byl[l] + [nc + l], [1.0] * (len(byl[l]) + 1))
ks = SL.summary(kept) if kept else dict(Q=0, T=0)
kq = ks["Q"]; kt = sum(ks["walk_trails"]) if kept else 0
fo = open(a.out, "a"); t0 = time.time(); best = None; n = 0
print("free loops", nF, "columns", nc, "kept Q", kq, "kept trails", kt, flush=True)
while n < a.count:
    h.run(); st = h.getModelStatus(); info = h.getInfo()
    if info.primal_solution_status != 2: break
    opt = st == highspy.HighsModelStatus.kOptimal; obj = info.objective_function_value
    if best is None: best = obj
    if obj > best + a.slack + 1e-6: break
    sol = np.array(h.getSolution().col_value); chosen = [j for j in range(nc) if sol[j] > 0.5]
    rows = dict(kept)
    for j in chosen: rows.update(cols[j][1])
    sm = SL.summary(rows); sm.update(free_objective=round(obj, 3), total_proxy=round(sm["Q"] + a.lam * sm["T"], 3), proved_optimal=opt, new_types=sorted(cols[j][4] for j in chosen), rows=dict(sorted(rows.items())), lam=a.lam)
    fo.write(json.dumps(sm) + "\n"); fo.flush(); n += 1
    print(n, "free obj", round(obj, 2), "opt" if opt else "feasible", "| total Q", sm["Q"], "T", sm["T"], "Q+T-1", sm["Q"] + sm["T"] - 1, "proxy", sm["total_proxy"], "rowless", sm["rowless"], "walks", sm["walk_lengths"], "%.0fs" % (time.time() - t0), flush=True)
    addrow(-highspy.kHighsInf, len(chosen) - 1 if chosen else -1, chosen if chosen else [nc], [1.0] * max(1, len(chosen)))
    if not chosen: break
