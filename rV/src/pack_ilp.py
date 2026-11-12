#!/usr/bin/env python3
"""Round V -- set packing of the 120 loops by images of closed walk types (HiGHS).
   minimise  sum over chosen walks (Q_w + LAM * T_w) + LAM * (number of loops left without a row)
Each solution is a selection; it is written with its Q, T and rows.  After each solution a cut removes it (the same
set of walks), and the programme is solved again: --count solutions.  HiGHS may stop at its time limit with a
feasible packing: such a packing is still written (flag "proved_optimal": false).
usage: pack_ilp.py OUT.jsonl TYPES.txt [TYPES2.txt ...] [--lam 1.5] [--maxdens 0.95] [--count 20] [--timelimit 120]"""
import sys, os, json, time, argparse
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL, packing as PK
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("types", nargs="+"); ap.add_argument("--lam", type=float, default=1.5); ap.add_argument("--maxdens", type=float, default=0.95)
ap.add_argument("--count", type=int, default=20); ap.add_argument("--timelimit", type=float, default=120); ap.add_argument("--threads", type=int, default=2); ap.add_argument("--maxtypes", type=int, default=100000)
ap.add_argument("--maxuncovered", type=int, default=120); ap.add_argument("--maxtrails", type=int, default=1000); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
types = []
for p in a.types: types += PK.read_types(p, a.maxdens, a.lam)
types = sorted(set(types), key=lambda t: (t[1] + a.lam * t[2]) / t[0])[:a.maxtypes]
cols = []
for (L, Q, T, w) in types:
    for loops, rows in PK.images(w): cols.append((loops, rows, Q, T, w))
nL = len(SL.LOOPS); nc = len(cols); print("types", len(types), "columns", nc, flush=True)
h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit); h.setOptionValue("random_seed", a.seed)
nvar = nc + nL; cost = np.array([c[2] + a.lam * c[3] for c in cols] + [a.lam] * nL, dtype=np.float64)
for j in range(nvar): h.addVar(0.0, 1.0)
h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), cost)
h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
byloop = [[] for _ in range(nL)]
for j, c in enumerate(cols):
    for l in c[0]: byloop[l].append(j)
def addrow(lo, hi, idx, val): h.addRow(lo, hi, len(idx), np.array(idx, dtype=np.int32), np.array(val, dtype=np.float64))
for l in range(nL): addrow(1, 1, byloop[l] + [nc + l], [1.0] * (len(byloop[l]) + 1))
inf = highspy.kHighsInf
addrow(0, a.maxuncovered, list(range(nc, nvar)), [1.0] * nL)
addrow(0, a.maxtrails, list(range(nvar)), [float(c[3]) for c in cols] + [1.0] * nL)
fo = open(a.out, "a"); t0 = time.time()
for it in range(a.count):
    h.run(); st = h.getModelStatus(); info = h.getInfo()
    if info.primal_solution_status != 2: print("no feasible solution:", h.modelStatusToString(st)); break
    sol = np.array(h.getSolution().col_value); chosen = [j for j in range(nc) if sol[j] > 0.5]
    rows = {}
    for j in chosen: rows.update(cols[j][1])
    sm = SL.summary(rows); sm.update(objective=round(info.objective_function_value, 3), proved_optimal=(st == highspy.HighsModelStatus.kOptimal), bound=round(info.mip_dual_bound, 3),
                                     types=sorted(cols[j][4] for j in chosen), rows=dict(sorted(rows.items())), lam=a.lam, sec=round(time.time() - t0, 1))
    fo.write(json.dumps(sm) + "\n"); fo.flush()
    print(it, "obj", sm["objective"], "bound", sm["bound"], "opt" if sm["proved_optimal"] else "feasible", "Q", sm["Q"], "T", sm["T"], "Q+T-1", sm["Q"] + sm["T"] - 1, "rowless", sm["rowless"], "walks", sm["walk_lengths"], "%.0fs" % (time.time() - t0), flush=True)
    addrow(-inf, len(chosen) - 1, chosen, [1.0] * len(chosen))
