#!/usr/bin/env python3
"""Round X -- second implementation of rX/src/frontier_exceptional.py: one integer program per cell (HiGHS), with the
deficit tables rebuilt here from the two-sided tables of the SECOND implementation (rX/src/check_twosided.py output).

Variables per cell and junction pattern (F_loops, F_pairs, shared rows s): x_r >= 0 integer (non-exceptional chains
with r pieces), and for CROSS = 1: z_r in {0, 1} (the exceptional chain), sum z <= 1;  for CROSS = 0: z1_r, z2_r, w_r
binary (exceptional for line 1 only, line 2 only, both), sum z1 + sum w <= 1, sum z2 + sum w <= 1.
   minimise  sum dR(r) x_r + sum dF(r) z_r (+ ...) + F_loops + 8 F_pairs - 6 s
   subject to  sum of all chain variables <= n - F_loops - s,   sum r (all chain variables) = R - F_loops - 2 F_pairs + s.
The deficit tables:  dmin from (v1 feasible or <= 0) and (v2 feasible or <= 0) and the zone statement, as in the
first implementation, but read from the second implementation's feasible sets.
Cells already excluded by Round W stay excluded (the new tables are pointwise >= the Round W table, checked here), so
only the 69 Round W survivors are solved; PART k/K solves every K-th of them.
usage: frontier_exceptional_ilp.py CTS1_FULL CTS2_FULL CTS1_RESTR CTS2_RESTR ROUNDW_KNAPSACK.json CROSS FIRST_IMPL_OUT.json OUT.json [k K]"""
import sys, json
import numpy as np, highspy

def feas(path):
    F = {}
    for l in open(path):
        if l.startswith("#"): continue
        t = l.split(); F[int(t[0])] = {int(x.split(":")[0]) for x in t[1:]}
    return F
RMAX = 800
def dtab(F1, F2):
    out = [0] * (RMAX + 1)
    for r in range(1, RMAX + 1):
        d = 0
        while True:
            v1, v2 = 4 * r - 9 * d, 17 * r - 38 * d
            if (v1 <= 0 or v1 in F1[r]) and (v2 <= 0 or v2 in F2[r]) and not (v1 >= 54 and v2 >= 258 and v1 != 56): break
            d += 1
        out[r] = d
    return out
F1, F2, F1r, F2r = (feas(p) for p in sys.argv[1:5]); W = json.load(open(sys.argv[5])); cross = int(sys.argv[6])
first = {(c["R"], c["F"]): c for c in json.load(open(sys.argv[7]))["rows"]}; outp = sys.argv[8]
dF, dR, d1, d2 = dtab(F1, F2), dtab(F1r, F2r), dtab(F1, F2r), dtab(F1r, F2)
dW = W["dmin_first"]
assert all(min(dF[r], dR[r], d1[r], d2[r]) >= dW[r] for r in range(1, 60)), "new tables below the Round W table"
part = (int(sys.argv[9]), int(sys.argv[10])) if len(sys.argv) > 10 else (0, 1)
def solve_pattern(pieces, chains, base):
    if pieces == 0: return base
    if chains <= 0: return None
    rs = list(range(1, pieces + 1)); nr = len(rs)
    blocks = [("x", dR, False)] + ([("z", dF, True)] if cross else [("z1", d1, True), ("z2", d2, True), ("w", dF, True)])
    nv = nr * len(blocks)
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    lo = np.zeros(nv); hi = np.concatenate([np.full(nr, float(chains)) if not b[2] else np.ones(nr) for b in blocks])
    h.addVars(nv, lo, hi)
    cost = np.concatenate([np.array([float(b[1][r]) for r in rs]) for b in blocks])
    h.changeColsCost(nv, np.arange(nv, dtype=np.int32), cost)
    h.changeColsIntegrality(nv, np.arange(nv, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nv))
    idx = np.arange(nv, dtype=np.int32)
    h.addRow(-highspy.kHighsInf, float(chains), nv, idx, np.ones(nv))
    h.addRow(float(pieces), float(pieces), nv, idx, np.tile(np.array([float(r) for r in rs]), len(blocks)))
    names = [b[0] for b in blocks]
    def block_idx(nm): k = names.index(nm); return np.arange(k * nr, (k + 1) * nr, dtype=np.int32)
    if cross:
        h.addRow(-highspy.kHighsInf, 1.0, nr, block_idx("z"), np.ones(nr))
    else:
        i1 = np.concatenate([block_idx("z1"), block_idx("w")]); i2 = np.concatenate([block_idx("z2"), block_idx("w")])
        h.addRow(-highspy.kHighsInf, 1.0, len(i1), i1, np.ones(len(i1))); h.addRow(-highspy.kHighsInf, 1.0, len(i2), i2, np.ones(len(i2)))
    h.run()
    if h.getModelStatus() != highspy.HighsModelStatus.kOptimal: return None
    return int(round(h.getInfo().objective_function_value)) + base
rows = []; mism = 0
todo = [c for c in W["rows"] if not c["excluded_junctions"]]
for c in todo[part[0]::part[1]]:
    R, n, F, D = c["R"], c["chains"], c["F"], c["Delta"]; best = None
    for Fi in range(F + 1):
        Fii = F - Fi
        for s in range(Fii + 1):
            pieces = R - Fi - 2 * Fii + s; chains = n - Fi - s
            if pieces < 0 or chains < 0: continue
            v = solve_pattern(pieces, chains, Fi + 8 * Fii - 6 * s)
            if v is not None and (best is None or v < best): best = v
    ex = best is None or best > D; f = first[(R, F)]
    agree = ex == f["excluded"] and best == f["min_deficit"]
    mism += not agree
    rows.append(dict(R=R, F=F, Delta=D, min_deficit_ilp=best, excluded_ilp=ex, min_deficit_first=f["min_deficit"], excluded_first=f["excluded"], agree=agree))
res = dict(cells=len(rows), excluded_ilp=sum(r["excluded_ilp"] for r in rows), survivors_ilp=sum(not r["excluded_ilp"] for r in rows), cross=cross, mismatches=mism, rows=rows)
json.dump(res, open(outp, "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
