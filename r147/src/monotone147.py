#!/usr/bin/env python3
"""Round 147 Phase 15 -- monotonicity as a HARD invariant of the cell table.

Every budget the chain searcher takes is an upper limit, never a requirement:

    tokens      `cost > tok` returns            -> more tokens, more moves
    deficit     a chain is recorded when `deficit <= DMAX`
    a (type A)  `au < AMAX` gates the A move
    bb (type B) `bu < BMAX` gates the B move
    e (ordinary collision)  `eu >= EMAX` returns
    h (heavy)   `hu + cost <= HMAX` gates the heavy moves

So for budget vectors K <= K' componentwise, every chain admissible for K is
admissible for K', and therefore

    (M)  cap(K) <= cap(K')      for all K <= K'.

(M) is used twice in round 147: to justify the entries of the pruning table
(r147/src/ub147.py) and as the invariant checked here.  A table of true
capacities MUST satisfy it, so a violation is a proof that the table is wrong.
The round-144 chain table violated it in 28 places, which was the visible
symptom of the unsound pruning bound -- the audit that chased those 28 down is
what found the defect.  Here a violation is a hard failure, not a report.

This module also re-derives the analytic bound of (P2) and checks every cell
against it:  cap(K) <= 120 + a + bb + e.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
DIRS = ("b", "d", "a", "bb", "e", "h")


def load(paths):
    cells = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        for k, v in json.loads(p.read_text()).items():
            if v.get("status") != "EXACT_UNCAPPED":
                continue
            cells[tuple(int(x) for x in k.split("|"))] = v["cc"]
    return cells


def audit(cells):
    viol, analytic = [], []
    for K, cc in cells.items():
        if cc > 120 + K[2] + K[3] + K[4]:
            analytic.append(dict(cell=list(K), cc=cc,
                                 analytic=120 + K[2] + K[3] + K[4]))
        for i in range(6):
            lo = list(K)
            lo[i] -= 1
            lo = tuple(lo)
            if lo in cells and cells[lo] > cc:
                viol.append(dict(direction=DIRS[i], lower=list(lo),
                                 upper=list(K), cc_lower=cells[lo],
                                 cc_upper=cc))
    # pairs that are comparable but not adjacent: a sampled global check
    keys = sorted(cells)
    far = []
    for i, K in enumerate(keys):
        for L in keys[i + 1:]:
            if all(K[j] <= L[j] for j in range(6)) and cells[K] > cells[L]:
                far.append(dict(lower=list(K), upper=list(L),
                                cc_lower=cells[K], cc_upper=cells[L]))
                if len(far) > 20:
                    break
        if len(far) > 20:
            break
    return dict(cells=len(cells), adjacent_violations=len(viol),
                comparable_violations=len(far),
                analytic_violations=len(analytic),
                examples=viol[:6] + far[:6] + analytic[:3],
                ok=not viol and not far and not analytic)


def main(argv):
    paths = argv or [R147 / "tables" / "chain_cells_147.json",
                     R147 / "tables" / "heavy_cells_147.json"]
    cells = load(paths)
    out = audit(cells)
    (R147 / "certs" / "monotonicity_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
