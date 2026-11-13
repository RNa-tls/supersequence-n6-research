#!/usr/bin/env python3
"""Round W -- second implementation of the (r, delta) knapsack of src/frontier.py, as one integer program per cell
(HiGHS), with the deficit table rebuilt here from the census files.

Cell (R, p, F): n = 1 + p + F chains, Delta = 7 (R - 720).  Variables: x_r >= 0 (number of nonempty chains, after the
free end pieces are cut off, with r pieces, r = 1..R), integers Fi (loops), Fii (pairs), s (rows shared by two pairs):
   minimise   sum_r dmin(r) x_r + Fi + 8 Fii - 6 s
   subject to sum_r x_r <= n - Fi - s,   sum_r r x_r = R - Fi - 2 Fii + s,   Fi + Fii = F,   0 <= s <= Fii.
The cell is excluded when the minimum exceeds Delta.  dmin(r) = max(0, ceil((4r - M1(r))/9), ceil((17r - M2(r))/38)),
raised while (4r - 9d >= 54 and 17r - 38d >= 258 and 4r - 9d != 56) (zone statement).
--mutate R0: lower dmin(R0) by one (control: the verdicts must be able to change).
usage: frontier_ilp.py CENSUS1 CENSUS2 KNAPSACK_OUT.json OUT.json [--mutate R0]"""
import sys, json, math
import numpy as np, highspy
def table(path):
    lines = open(path).read().strip().split("\n"); head = json.loads(lines[0]); body = json.loads(lines[1]); a, b, c = head["params"]
    raw = {int(k): int(v) for k, v in body["least_pieces_by_value"].items()}
    return a, b, c, raw
def Mof(raw, c, r):
    best = 0
    for v in range(1, c + 1):
        if any(raw[w] <= r for w in raw if w >= v): best = v
    return best
args = sys.argv[1:]; mut = None
if "--mutate" in args: mut = int(args[args.index("--mutate") + 1])
(a1, b1, c1, raw1), (a2, b2, c2, raw2) = table(args[0]), table(args[1]); ref = json.load(open(args[2]))["rows"]; outp = args[3]
RMAX = 770
# M(r) by a direct scan (different code path from frontier.py)
lp1 = sorted(raw1.items()); lp2 = sorted(raw2.items())
def Mfast(lp, r):
    vals = [v for v, m in lp if m <= r]; return max(vals) if vals else 0
dmin = [0] * (RMAX + 1)
for r in range(1, RMAX + 1):
    m1, m2 = Mfast(lp1, r), Mfast(lp2, r)
    d = max(0, math.ceil((4 * r - m1) / 9), math.ceil((17 * r - m2) / 38))
    while 4 * r - 9 * d >= 54 and 17 * r - 38 * d >= 258 and 4 * r - 9 * d != 56: d += 1
    dmin[r] = d
if mut is not None: dmin[mut] -= 1
def solve(R, n, F):
    best = None
    for Fi in range(F + 1):
        Fii = F - Fi
        for s in range(Fii + 1):
            pieces = R - Fi - 2 * Fii + s; chains = n - Fi - s
            if pieces < 0 or chains < 0: continue
            if pieces == 0: val = Fi + 8 * Fii - 6 * s
            else:
                if chains == 0: continue
                rs = list(range(1, pieces + 1)); nv = len(rs)
                h = highspy.Highs(); h.setOptionValue("output_flag", False)
                h.addVars(nv, np.zeros(nv), np.full(nv, float(chains)))
                h.changeColsCost(nv, np.arange(nv, dtype=np.int32), np.array([float(dmin[r]) for r in rs]))
                h.changeColsIntegrality(nv, np.arange(nv, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nv))
                h.addRow(-highspy.kHighsInf, float(chains), nv, np.arange(nv, dtype=np.int32), np.ones(nv))
                h.addRow(float(pieces), float(pieces), nv, np.arange(nv, dtype=np.int32), np.array([float(r) for r in rs]))
                h.run()
                if h.getModelStatus() != highspy.HighsModelStatus.kOptimal: continue
                val = int(round(h.getInfo().objective_function_value)) + Fi + 8 * Fii - 6 * s
            if best is None or val < best: best = val
    return best
rows = []; mism = 0
for c in ref:
    R, n, F, D = c["R"], c["chains"], c["F"], c["Delta"]
    v = solve(R, n, F); ex = v is None or v > D
    agree = (ex == c["excluded_junctions"]) and (mut is not None or v == c["min_deficit_junctions"])
    mism += not agree
    rows.append(dict(R=R, F=F, min_deficit_ilp=v, excluded_ilp=ex, excluded_dp=c["excluded_junctions"], agree=agree))
res = dict(cells=len(rows), excluded_ilp=sum(r["excluded_ilp"] for r in rows), mismatches=mism, mutate=mut, rows=rows)
json.dump(res, open(outp, "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
