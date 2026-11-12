#!/usr/bin/env python3
"""Round V -- integer programme over selections written with segments (HiGHS).
Entry lemma (checked for all 720 x 4 cases): a short row that leads to a state y0 lies in the loop of G6^4(y0).  Hence in a
closed walk a run of rows of length 6 that is entered by a short row has at most three rows before the next short
row: every walk except 66666 is a cyclic sequence of segments  6^k v  (k = 0..3, v in {1,2,3,4}), of cost 6 - v >= 2.
Variables: x[e, k, v] (segment entered at state e), u[orbit] (a walk 66666), z[loop] (no row).
   cover : every loop in exactly one segment / 66666 walk / z
   flow  : for every state e,  segments entered at e  =  segments that lead to e
   objective: sum (6 - v) x + LAM * (sum z + 5 sum u)   [+ MU per segment: a walk has at least one segment]
Lazy cuts (--maxwalks, --minlen, --maxtrails) as in sel_ilp.py.  Solutions are written as rows.
usage: seg_ilp.py OUT.jsonl [--lam 1.5] [--count N] [--timelimit s] [--maxwalks W] [--fix FILE(rows to keep)] ..."""
import sys, os, json, time, itertools, argparse
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--lam", type=float, default=1.5); ap.add_argument("--count", type=int, default=1); ap.add_argument("--timelimit", type=float, default=600)
ap.add_argument("--threads", type=int, default=2); ap.add_argument("--maxwalks", type=int, default=0); ap.add_argument("--minlen", type=int, default=0); ap.add_argument("--maxtrails", type=int, default=5)
ap.add_argument("--maxrowless", type=int, default=120); ap.add_argument("--no66666", action="store_true"); ap.add_argument("--walkcost", type=float, default=0.0); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args(); S = SL.STATES; SID = SL.SID; nL = len(SL.LOOPS)
segs = []
for e in S:
    y = e; loops = []
    for k in range(4):
        loops = loops + [SL.LID[SL.canon(y)]]
        for v in (1, 2, 3, 4): segs.append((e, k, v, tuple(loops), SL.step(y, v)))
        y = SL.step(y, 6)
orbs = []; seen = set()
for e in S:
    if e in seen: continue
    o = [e]
    for _ in range(4): o.append(SL.step(o[-1], 6))
    seen |= set(o); orbs.append(o)
ns = len(segs); no = len(orbs); nvar = ns + no + nL
h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit); h.setOptionValue("random_seed", a.seed)
cost = np.array([6 - s[2] + a.walkcost * 0 for s in segs] + [5 * a.lam] * no + [a.lam] * nL, dtype=np.float64)
ub = np.ones(nvar)
if a.no66666: ub[ns:ns + no] = 0
h.addVars(nvar, np.zeros(nvar), ub); h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), cost)
h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
def addrow(lo, hi, idx, val): h.addRow(lo, hi, len(idx), np.array(idx, dtype=np.int32), np.array(val, dtype=np.float64))
byl = [[] for _ in range(nL)]
for j, s in enumerate(segs):
    for l in s[3]: byl[l].append(j)
for j, o in enumerate(orbs):
    for y in o: byl[SL.LID[SL.canon(y)]].append(ns + j)
for l in range(nL): addrow(1, 1, byl[l] + [ns + no + l], [1.0] * (len(byl[l]) + 1))
ent = {e: [] for e in S}; tgt = {e: [] for e in S}
for j, s in enumerate(segs): ent[s[0]].append(j); tgt[s[4]].append(j)
for e in S:
    co = {}
    for j in ent[e]: co[j] = co.get(j, 0) + 1.0
    for j in tgt[e]: co[j] = co.get(j, 0) - 1.0
    idx = [k for k, c in co.items() if c != 0]
    if idx: addrow(0, 0, idx, [co[k] for k in idx])
addrow(0, a.maxrowless, list(range(ns + no, nvar)), [1.0] * nL)
inf = highspy.kHighsInf; fo = open(a.out, "a"); t0 = time.time(); found = 0; nsolve = 0; ncut = 0
def rows_of(sol):
    rows = {}
    for j, s in enumerate(segs):
        if sol[j] > 0.5:
            y = s[0]
            for _ in range(s[1]): rows[y] = 6; y = SL.step(y, 6)
            rows[y] = s[2]
    for j, o in enumerate(orbs):
        if sol[ns + j] > 0.5:
            for y in o: rows[y] = 6
    return rows
while found < a.count:
    h.run(); nsolve += 1; st = h.getModelStatus(); info = h.getInfo()
    if info.primal_solution_status != 2: print("no solution:", h.modelStatusToString(st)); break
    opt = st == highspy.HighsModelStatus.kOptimal; sol = np.array(h.getSolution().col_value); rows = rows_of(sol); wks = SL.walks_of(rows); bad = False
    chosen = [j for j in range(ns) if sol[j] > 0.5]
    if a.maxwalks and len(wks) > a.maxwalks:
        for wk in wks:
            inside = {SL.LID[SL.canon(x)] for x, _ in wk}
            leave = [j for j, s in enumerate(segs) if s[3][-1] in inside and SL.LID[SL.canon(s[4])] not in inside]
            L0 = next(iter(inside))
            for wk2 in wks:
                if wk2 is wk: continue
                M0 = SL.LID[SL.canon(wk2[0][0])]; addrow(1, inf, leave + [ns + no + L0, ns + no + M0], [1.0] * (len(leave) + 2)); ncut += 1
        bad = True
    if not bad:
        for wk in wks:
            if (a.minlen and len(wk) < a.minlen) or SL.trails_of_walk(wk) > a.maxtrails:
                ws = set(x for x, _ in wk); idx = [j for j in chosen if segs[j][0] in ws]; addrow(-inf, len(idx) - 1, idx, [1.0] * len(idx)); ncut += 1; bad = True
    if bad and opt: continue
    sm = SL.summary(rows); sm.update(objective=round(info.objective_function_value, 3), bound=round(info.mip_dual_bound, 3), proved_optimal=opt and not bad, violates_lazy=bad, rows=dict(sorted(rows.items())), solves=nsolve, cuts=ncut, sec=round(time.time() - t0, 1))
    fo.write(json.dumps(sm) + "\n"); fo.flush(); found += 1
    print(found, "obj", sm["objective"], "bound", sm["bound"], "opt" if opt else "feasible", "Q", sm["Q"], "rowless", sm["rowless"], "T", sm["T"], "proxy1.5", sm["Q"] + 1.5 * sm["T"], "walks", sm["walk_lengths"], "trails", sm["walk_trails"], "solves", nsolve, "cuts", ncut, "%.0fs" % (time.time() - t0), flush=True)
    idx = chosen + [ns + j for j in range(no) if sol[ns + j] > 0.5]; addrow(-inf, len(idx) - 1, idx, [1.0] * len(idx))
