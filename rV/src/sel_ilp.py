#!/usr/bin/env python3
"""Round V -- integer programme over selections (HiGHS).  Variables y[x, v] (row (x, v)) and z[l] (loop l has no row).
   cover:    for every loop  sum_{x in loop, v} y + z = 1
   balance:  for every state x  sum_v y[x, v] = sum of y[x', v'] over the rows with step(x', v') = x
   objective: sum (6 - v) y + LAMBDA * sum z      (LAMBDA prices a rowless loop = one more trail)
Lazy constraints, added after each solve until the solution is accepted:
   --minlen L    no closed walk with fewer than L loops (all 720 relabelings of an offending walk are cut)
   --maxwalks W  at most W closed walks (connectivity cuts)
   --maxtrails t no walk that is read as more than t closed trails
Accepted solutions are written (one JSON line each, with Q, T, walks); then all relabelings of the solution are
cut off and the programme is solved again, --count times.   usage: sel_ilp.py OUT.jsonl [options]"""
import sys, os, json, time, itertools, argparse
import numpy as np, highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--lam", type=float, default=1.5); ap.add_argument("--minlen", type=int, default=6)
ap.add_argument("--maxwalks", type=int, default=0); ap.add_argument("--maxtrails", type=int, default=5); ap.add_argument("--count", type=int, default=1)
ap.add_argument("--maxrowless", type=int, default=120); ap.add_argument("--minrowless", type=int, default=0); ap.add_argument("--timelimit", type=float, default=600)
ap.add_argument("--maxobj", type=float, default=1e9); ap.add_argument("--threads", type=int, default=2); ap.add_argument("--vs", default="1,2,3,4,6"); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args(); VS = tuple(int(v) for v in a.vs.split(","))
S = SL.STATES; nS = len(S); nV = len(VS); nL = len(SL.LOOPS)
def yv(x, v): return SL.SID[x] * nV + VS.index(v)
def zv(l): return nS * nV + l
nvar = nS * nV + nL
h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", a.threads); h.setOptionValue("time_limit", a.timelimit); h.setOptionValue("random_seed", a.seed)
cost = np.zeros(nvar)
for x in S:
    for v in VS: cost[yv(x, v)] = 6 - v
for l in range(nL): cost[zv(l)] = a.lam
inf = highspy.kHighsInf
for j in range(nvar): h.addVar(0.0, 1.0)
h.changeColsCost(nvar, np.arange(nvar, dtype=np.int32), cost)
h.changeColsIntegrality(nvar, np.arange(nvar, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nvar))
def addrow(lo, hi, idx, val): h.addRow(lo, hi, len(idx), np.array(idx, dtype=np.int32), np.array(val, dtype=np.float64))
for l, lp in enumerate(SL.LOOPS):
    idx = [yv(lp[i:] + lp[:i], v) for i in range(6) for v in VS] + [zv(l)]; addrow(1, 1, idx, [1.0] * len(idx))
pre = {x: [] for x in S}
for x in S:
    for v in VS: pre[SL.step(x, v)].append((x, v))
for x in S:
    co = {}
    for v in VS: co[yv(x, v)] = co.get(yv(x, v), 0) + 1.0
    for (x2, v2) in pre[x]: co[yv(x2, v2)] = co.get(yv(x2, v2), 0) - 1.0
    idx = [k for k, c in co.items() if c != 0]; addrow(0, 0, idx, [co[k] for k in idx])
addrow(a.minrowless, a.maxrowless, [zv(l) for l in range(nL)], [1.0] * nL)
PERMS = [dict(zip("012345", p)) for p in itertools.permutations("012345")]
def images(rows):
    """all relabelings of a set of rows, as frozensets of variable indices"""
    out = set()
    for mp in PERMS: out.add(frozenset(yv("".join(mp[c] for c in x), v) for x, v in rows))
    return out
cutseen = set()
def cut_walk(wk):
    n = 0
    for im in images(wk):
        if im in cutseen: continue
        cutseen.add(im); addrow(-inf, len(im) - 1, sorted(im), [1.0] * len(im)); n += 1
    return n
fo = open(a.out, "a"); found = 0; t0 = time.time(); nsolve = 0; ncut = 0
while found < a.count:
    h.run(); nsolve += 1; st = h.getModelStatus()
    if st not in (highspy.HighsModelStatus.kOptimal,):
        print("status", h.modelStatusToString(st), "after", nsolve, "solves", "%.0fs" % (time.time() - t0)); break
    sol = np.array(h.getSolution().col_value); obj = h.getInfo().objective_function_value
    if obj > a.maxobj + 1e-6: print("objective", obj, "above the limit; stop"); break
    rows = {x: v for x in S for v in VS if sol[yv(x, v)] > 0.5}; wks = SL.walks_of(rows); bad = False
    for wk in wks:
        if len(wk) < a.minlen or SL.trails_of_walk(wk) > a.maxtrails: ncut += cut_walk(wk); bad = True
    if not bad and a.maxwalks and len(wks) > a.maxwalks:
        # connectivity: for the loop set of each walk, some row must leave it whenever a loop inside and a loop outside both have rows
        for wk in wks:
            inside = {SL.canon(x) for x, _ in wk}; L0 = SL.LID[SL.canon(wk[0][0])]
            leave = [yv(x, v) for x in S if SL.canon(x) in inside for v in VS if SL.canon(SL.step(x, v)) not in inside]
            for wk2 in wks:
                if wk2 is wk: continue
                M0 = SL.LID[SL.canon(wk2[0][0])]
                # sum(leave) >= (1 - z_L0) + (1 - z_M0) - 1   <=>   sum(leave) + z_L0 + z_M0 >= 1
                addrow(1, inf, leave + [zv(L0), zv(M0)], [1.0] * (len(leave) + 2)); ncut += 1
        bad = True
    if bad: continue
    sm = SL.summary(rows); sm.update(objective=round(obj, 4), rows={x: v for x, v in sorted(rows.items())}, solves=nsolve, cuts=ncut, sec=round(time.time() - t0, 1))
    fo.write(json.dumps(sm) + "\n"); fo.flush(); found += 1
    print("found", found, "obj", round(obj, 3), "Q", sm["Q"], "rowless", sm["rowless"], "walks", sm["walk_lengths"], "trails", sm["walk_trails"], "T", sm["T"], "solves", nsolve, "cuts", ncut, "%.0fs" % (time.time() - t0), flush=True)
    # cut off this selection and its relabelings
    full = [(x, v) for x, v in rows.items()]
    for im in images(full):
        if im in cutseen: continue
        cutseen.add(im); addrow(-inf, len(im) - 1, sorted(im), [1.0] * len(im))
