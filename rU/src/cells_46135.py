#!/usr/bin/env python3
"""Round U -- the cells that survive the arithmetic of Theorem D (n = 8) at length 46134, i.e. what a proof of
L(8) >= 46135 by the same reduction would have to exclude.  Cell = (R rows, X heavy seams, J paid junctions,
F free junctions); holes D = 7R - 5040, chains n = X + F + J + 1.  Constraints as in rT/src/d8_cells.py.
Classification by R, by the number of chains, by which clause of Tri holds, by the slacks of the two lines.
usage: cells_46135.py OUT.json"""
import sys, json, collections
L = 46134; E = L - 46085; cells = []
for R in range(720, 720 + E + 2):
    D = 7 * R - 5040
    for XJ in range(0, E + 1):
        if D + 7 * XJ > 7 * E: continue
        for F in range(0, 400):
            if not (4 * R + 5 * F <= 9 * D + 56 * (1 + XJ) and 17 * R + 6 * F <= 38 * D + 264 * (1 + XJ)): break
            n = XJ + F + 1; s1 = 9 * D + 56 * n - 4 * R; s2 = 38 * D + 264 * n - 17 * R
            if s1 < 0 or s2 < 0: continue
            cl = "on_line1" if s1 == 0 else ("both" if s1 >= 3 and s2 >= 7 else "line1_gap>=3" if s1 >= 3 else "line2_gap>=7" if s2 >= 7 else None)
            if cl is None: continue
            for J in range(0, XJ + 1): cells.append(dict(R=R, D=D, X=XJ - J, J=J, F=F, n=n, s1=s1, s2=s2, clause=cl, budget_slack=7 * E - D - 7 * XJ))
res = dict(length=L, cells=len(cells))
proj = {(c["R"], c["X"] + c["J"], c["F"]) for c in cells}; res["cells_up_to_the_split_X_J"] = len(proj)
res["by_rows_R"] = {str(k): v for k, v in sorted(collections.Counter(c["R"] for c in cells).items())}
res["by_rows_R_projected"] = {str(k): v for k, v in sorted(collections.Counter(r for r, _, _ in proj).items())}
res["by_clause"] = dict(collections.Counter(c["clause"] for c in cells))
res["by_free_junctions_F"] = {str(k): v for k, v in sorted(collections.Counter(c["F"] for c in cells).items())}
res["by_chains_n"] = {str(k): v for k, v in sorted(collections.Counter(c["n"] for c in cells).items())}
res["R_range"] = [min(c["R"] for c in cells), max(c["R"] for c in cells)]
res["budget_slack_histogram"] = {str(k): v for k, v in sorted(collections.Counter(c["budget_slack"] // 7 for c in cells).items())}
res["tight_cells_slack1_le_2"] = sorted({(c["R"], c["X"] + c["J"], c["F"], c["s1"], c["s2"]) for c in cells if c["s1"] <= 2})[:40]
res["least_slack_line1_by_R"] = {str(R): min(c["s1"] for c in cells if c["R"] == R) for R in sorted({c["R"] for c in cells})}
res["least_slack_line2_by_R"] = {str(R): min(c["s2"] for c in cells if c["R"] == R) for R in sorted({c["R"] for c in cells})}
# what a third line a r <= b delta + c (per chain) with gamma-type junction term would have to do is not modelled here
json.dump(res, open(sys.argv[1], "w"), indent=1)
for k in ("cells", "cells_up_to_the_split_X_J", "by_clause", "R_range", "by_rows_R_projected", "by_free_junctions_F", "budget_slack_histogram", "least_slack_line1_by_R", "tight_cells_slack1_le_2"): print(k, json.dumps(res[k])[:700])
