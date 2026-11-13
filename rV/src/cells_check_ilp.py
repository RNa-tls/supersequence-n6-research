#!/usr/bin/env python3
"""Round V -- second implementation of the cell exclusion of src/cells_tight.py, as an integer program (HiGHS).
For a cell (R, p, F), n = 1 + p + F chains and one line a r <= b d + c with census table m (least pieces of a chain of
value >= v):  maximise  sum_v v x_v  over integers x_v >= 0 (v = 1..c: chains of value v, m(v) pieces each) and
x_0 >= 0 (chains of value <= 0, counted as value 0 and one piece) with  sum x = n,  sum m(v) x_v + x_0 <= R.
The cell is excluded by the line if the maximum is below a R - b * 7 (R - 720).  The census tables are read directly
from the census JSON files (not through cells_tight.py); the verdicts are compared with the cells_tight.py output.
usage: cells_check_ilp.py CENSUS1.json CENSUS2.json CELLS_TIGHT_OUT.json OUT.json"""
import sys, json
import numpy as np, highspy
def table(path):
    lines = open(path).read().strip().split("\n"); head = json.loads(lines[0]); body = json.loads(lines[1]); a, b, c = head["params"]
    raw = {int(k): int(v) for k, v in body["least_pieces_by_value"].items()}
    m = {}
    for v in range(1, c + 1):
        cand = [raw[w] for w in raw if w >= v]
        m[v] = min(cand) if cand else None        # None: no chain of value >= v exists at all
    return a, b, c, m
def maxsum(n, R, c, m):
    vs = [v for v in range(1, c + 1) if m[v] is not None]; nv = len(vs) + 1
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    cost = np.array([-float(v) for v in vs] + [0.0]); h.addVars(nv, np.zeros(nv), np.full(nv, float(n)))
    h.changeColsCost(nv, np.arange(nv, dtype=np.int32), cost)
    h.changeColsIntegrality(nv, np.arange(nv, dtype=np.int32), np.array([highspy.HighsVarType.kInteger] * nv))
    h.addRow(n, n, nv, np.arange(nv, dtype=np.int32), np.ones(nv))
    h.addRow(-highspy.kHighsInf, R, nv, np.arange(nv, dtype=np.int32), np.array([float(m[v]) for v in vs] + [1.0]))
    h.run(); st = h.getModelStatus()
    if st != highspy.HighsModelStatus.kOptimal: return None
    return int(round(-h.getInfo().objective_function_value))
c1p, c2p, tightp, outp = sys.argv[1:5]
L = [table(c1p), table(c2p)]; ref = json.load(open(tightp)); rows = []; mism = 0
for cell in ref["cells_detail"]:
    R, p, F, n = cell["R"], cell["p"], cell["F"], cell["chains"]; D = 7 * (R - 720); why = []
    for a, b, c, m in L:
        V = a * R - b * D; ms = maxsum(n, R, c, m)
        if ms is None or ms < V: why.append("line %d %d %d: needs %d, at most %s" % (a, b, c, V, ms))
    ex = bool(why); agree = ex == cell["excluded"]; mism += not agree
    rows.append(dict(R=R, p=p, F=F, chains=n, excluded_ilp=ex, excluded_dp=cell["excluded"], agree=agree, why=why))
res = dict(cells=len(rows), excluded_ilp=sum(r["excluded_ilp"] for r in rows), excluded_dp=sum(r["excluded_dp"] for r in rows), mismatches=mism, rows=rows)
json.dump(res, open(outp, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
