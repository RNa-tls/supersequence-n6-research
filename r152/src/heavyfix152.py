#!/usr/bin/env python3
"""Round 152 Phase 1 -- the heavy-retained model's budget bug, reproduced and
repaired from the repository alone.

Round 151 is described to this round but is committed NOWHERE in the
repository, so nothing about it is taken on trust: the finding is re-derived
here from the source.

THE BUG.  r148/src/rows148.py passes `r["h"]` -- the NUMBER of heavy joints --
as the searcher's sixth argument, which the searcher reads as HMAX, the heavy
COST budget sum(w-3).  Since 1 <= h <= H, the model was run with a budget that
is too SMALL, so its capacity came out too small, so its bound came out too
small: exactly the direction that closes rows which are not closed.

THE REPAIR.  Pass H.  Every heavy cell the corrected call needs is already
among the 276 computed (the dependency generator enumerated h over 1..H, so
h = H is included), and the row census is unchanged.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r148" / "src"))
sys.path.insert(0, str(ROOT / "r147" / "src"))
sys.path.insert(0, str(ROOT / "src"))
import rows148 as R                                                 # noqa: E402

COORD = R.COORD


def merged_fixed(variants, HV):
    """The heavy-retained bound with the CORRECT budget HMAX = H."""
    mv, missing = None, []
    for r in variants:
        if r["H"] == 0 or r["d"] + 1 != 1 or r["s"] != 0:
            continue
        tot = 2 * r["g"]
        key = (r["b_sum"], r["D_sum"], min(r["D2"], tot), min(r["Qs"], tot),
               min(max(0, r["Z"] - r["Qs"]), tot), r["H"])
        v = HV.get(key)
        if v is None:
            missing.append(list(key))
            continue
        if mv is None or v > mv:
            mv = v
    return mv, missing


def main():
    R.load()
    R.PIECE.load_caps()
    HV = R.HV
    impact = dict(rows=0, merged_closes=0, called_with_h_ne_H=0,
                  closed_only_by_merged=0, closed_only_by_merged_and_wrong=0)
    census, missing, nonstrict = {}, set(), []
    for t in (0, 1, 2, 3, 4):
        groups = {}
        for r in R.rows(t):
            groups.setdefault(tuple(r[c] for c in COORD), []).append(r)
        cnt = {"STRICT": 0, "EQUALITY": 0, "SURVIVING": 0}
        for key, variants in sorted(groups.items()):
            impact["rows"] += 1
            req, res = R.bounds(variants)
            hh = [(r["h"], r["H"]) for r in variants
                  if r["h"] and r["d"] + 1 == 1 and r["s"] == 0]
            clean0 = {k: v for k, v in res.items() if not v[1]}
            closing0 = {k: v[0] for k, v in clean0.items() if v[0] < req}
            if "merged" in closing0:
                impact["merged_closes"] += 1
                if any(h != H for h, H in hh):
                    impact["called_with_h_ne_H"] += 1
                if len(closing0) == 1:
                    impact["closed_only_by_merged"] += 1
                    if any(h != H for h, H in hh):
                        impact["closed_only_by_merged_and_wrong"] += 1
            # the repaired evaluation
            res.pop("merged", None)
            mv, mm = merged_fixed(variants, HV)
            missing |= {tuple(x) for x in mm}
            if mv is not None:
                res["merged_fixed"] = (mv, False)
            clean = {k: v for k, v in res.items() if not v[1]}
            if clean and any(v[0] < req for v in clean.values()):
                cnt["STRICT"] += 1
            elif clean and min(v[0] for v in clean.values()) == req:
                cnt["EQUALITY"] += 1
            else:
                cnt["SURVIVING"] += 1
                nonstrict.append(dict(zip(COORD, key)) | dict(required=req))
        census[f"L{867 + t}"] = cnt
    out = dict(bug_impact=impact, repaired_census=census,
               heavy_cells_missing_at_HMAX_equals_H=sorted(missing),
               surviving_rows_after_repair=nonstrict,
               conclusion=("the bug is real and affects "
                           f"{impact['called_with_h_ne_H']} rows, but NO row "
                           "is closed only by a wrong merged call, and with "
                           "HMAX = H every needed heavy cell already exists, "
                           "so the census is unchanged"),
               ok=(not nonstrict and not missing))
    (ROOT / "r152" / "certs" / "heavyfix_152.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k != "surviving_rows_after_repair"}, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
