#!/usr/bin/env python3
"""Round 146 -- re-evaluate every coordinate row with SOUND chain capacities.

Feeds the table-free values from
    outputs/rr_l6_chain_recheck_146.json   (plain chain cells)
    outputs/rr_l6_heavy_recheck_146.json   (heavy cells, merged model)
into the round-144 row machinery in place of the round-144 ledger, and reports
for each length how many coordinate rows are still closed.

SUBSTITUTION RULES (each one keeps the bound an UPPER bound):
  exact            -> that value (the table-free search is uncapped, so it IS
                      the capacity of the cell)
  bound_below      -> target - 1 (the decision run answered "not reachable")
  target_reached   -> the analytic bound 120 + a + bb + e, and flagged: the
                      round-144 "CC <= target - 1" is refuted but the true
                      capacity is not known
  UNKNOWN_CAP /
  ERROR / absent   -> the analytic bound 120 + a + bb + e, and flagged

A row counts as CLOSED only when the minimum over the models is strictly below
its required port count with NO flagged cell entering that minimum.  Rows whose
closure needs a flagged cell are reported separately as UNKNOWN, never closed.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_rows_final_144 as RF                                     # noqa: E402
import l6_chain_rows_144 as CR                                     # noqa: E402
import l6_coupled_144 as PIECE                                     # noqa: E402
import l6_871_analysis_144 as AN                                   # noqa: E402

HEXCAP = 120
CH = json.loads((ROOT / "outputs" / "rr_l6_chain_recheck_146.json").read_text())
HV_P = ROOT / "outputs" / "rr_l6_heavy_recheck_146.json"
HV = json.loads(HV_P.read_text()) if HV_P.exists() else {}
USED_FLAG = [False]


def sound_cc(b, d, a, bb, e):
    """Sound chain capacity, plus whether it is only the analytic fallback."""
    absolute = HEXCAP + a + bb + e
    rec = CH.get(f"{b}|{d}|{a}|{bb}|{e}")
    if rec is None:
        return absolute, True
    st = rec.get("status")
    if st == "exact":
        return min(rec["cc"], absolute), False
    if st == "bound_below":
        return min(rec["target"] - 1, absolute), False
    return absolute, True                    # target_reached / UNKNOWN_CAP / ERROR


def patched_CC(b, d, a, bb, e):
    v, fb = sound_cc(b, d, a, bb, e)
    if fb:
        USED_FLAG[0] = True
    return v, fb


def sound_heavy():
    """Keep only heavy cells whose table-free recheck is conclusive."""
    out = {}
    for k, v in HV.items():
        if v.get("status") == "exact":
            out[k] = dict(cc=v["cc"], nodes=v["nodes"], capped=False)
        elif v.get("status") == "bound_below":
            out[k] = dict(cc=v["target"] - 1, nodes=v["nodes"], capped=False)
    return out


def main(argv):
    PIECE.load_caps()
    CR.load_cache()
    AN.load_h()
    CR.CC = patched_CC
    AN._H = sound_heavy()
    print(f"chain recheck cells={len(CH)} usable="
          f"{sum(1 for v in CH.values() if v.get('status') in ('exact', 'bound_below'))} "
          f"heavy recheck cells={len(HV)} usable={len(AN._H)}", flush=True)
    report = {}
    for t in [int(x) for x in (argv or ["2", "3", "4"])]:
        groups = RF.group_rows(t)
        closed = unknown = surviving = 0
        survivors = []
        for key, variants in sorted(groups.items()):
            req = variants[0]["required"]
            pv, punk = RF.piece_max(variants)
            USED_FLAG[0] = False
            CR._best.cache_clear()
            sv, _ = RF.split_max(variants)
            split_flagged = USED_FLAG[0]
            mv, _ = RF.merged_max(variants, allow_compute=False)
            cands = [("piece", pv, punk), ("split", sv, split_flagged)]
            if mv is not None:
                cands.append(("merged", mv, False))
            cands = [c for c in cands if c[1] is not None]
            best = min(cands, key=lambda c: c[1])
            rec = dict(zip(RF.COORD, key))
            rec.update(required=req, piece=pv, split=sv, merged=mv,
                       bound=best[1], closed_by=best[0], flagged=best[2])
            if best[1] < req and not best[2]:
                closed += 1
            elif best[1] < req and best[2]:
                unknown += 1
                survivors.append(dict(rec, verdict="UNKNOWN_FLAGGED_CELL"))
            else:
                # a row can still be closed by a model that is NOT the minimum
                # but is unflagged
                hard = [c for c in cands if not c[2] and c[1] < req]
                if hard:
                    closed += 1
                else:
                    surviving += 1
                    survivors.append(dict(rec, verdict="OPEN"))
        report[f"L{867 + t}"] = dict(rows=len(groups), closed=closed,
                                     unknown_flagged=unknown, open=surviving)
        report[f"L{867 + t}_survivors"] = survivors[:200]
        print(f"L{867 + t}: rows={len(groups)} closed={closed} "
              f"unknown_flagged={unknown} open={surviving}", flush=True)
    (ROOT / "outputs" / "rr_l6_rows_recheck_146.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
