#!/usr/bin/env python3
"""Round T -- the arithmetic of Halfar's Theorem D at n = 8 (proofs/lean/n8_46134/LowerBounds/D8.lean, d8_arith),
re-derived by plain enumeration: for a given length L = wt + 8, list every integer cell
(R rows, Delta holes, X heavy seams, J paid junctions, F free junctions) allowed by
   coverage   7*46085 + Delta + 7*(X + J) <= 7*L          holes  Delta + 7*720 = 7*R
   line 1     4R + 5F <= 9 Delta + 56 (1 + X + J)          line 2 17R + 6F <= 38 Delta + 264 (1 + X + J)
   Tri(R, Delta, n) with n = X + F + J + 1 chains:  both lines summed over chains, and
        (4R = 9 Delta + 56 n) or (4R + 3 <= 9 Delta + 56 n) or (17R + 7 <= 38 Delta + 264 n)
The three hypotheses (H1), (H2), (H3) about chains are taken as given (they are the three native_decide equations).
usage: d8_cells.py OUT.json"""
import sys, json
def cells(L, use_tri=True, use_lines=True):
    out = []
    E = L - 46085
    for R in range(720, 720 + E + 2):
        D = 7 * R - 5040
        for XJ in range(0, E + 1):
            if D + 7 * XJ > 7 * E: continue
            for F in range(0, 400):
                if use_lines and not (4 * R + 5 * F <= 9 * D + 56 * (1 + XJ) and 17 * R + 6 * F <= 38 * D + 264 * (1 + XJ)): break
                for J in range(0, XJ + 1):
                    X = XJ - J; n = X + F + J + 1
                    if use_tri:
                        if not (4 * R <= 9 * D + 56 * n and 17 * R <= 38 * D + 264 * n): continue
                        if not (4 * R == 9 * D + 56 * n or 4 * R + 3 <= 9 * D + 56 * n or 17 * R + 7 <= 38 * D + 264 * n): continue
                    out.append(dict(R=R, holes=D, X=X, J=J, F=F, chains=n, slack_line1=9 * D + 56 * n - 4 * R, slack_line2=38 * D + 264 * n - 17 * R))
                if not use_lines: break
    return out
res = {}
for L in range(46128, 46137):
    a = cells(L, False, True); b = cells(L, True, True)
    res[str(L)] = dict(cells_with_lines_only=len(a), cells_with_lines_and_zone=len(b), examples=b[:12])
    print(L, "lines only:", len(a), " lines + zone:", len(b), b[:3])
res["least_length_allowed_by_lines_only"] = min(int(k) for k, v in res.items() if isinstance(v, dict) and v["cells_with_lines_only"])
res["least_length_allowed_by_lines_and_zone"] = min(int(k) for k, v in res.items() if isinstance(v, dict) and v["cells_with_lines_and_zone"])
json.dump(res, open(sys.argv[1], "w"), indent=1); print(res["least_length_allowed_by_lines_only"], res["least_length_allowed_by_lines_and_zone"])
