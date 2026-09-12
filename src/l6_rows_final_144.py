#!/usr/bin/env python3
"""L6 endgame — the CORRECT combination of the three upper-bound models.

WHY THIS FILE EXISTS (self-correction).  The extraction parameter

    s = (sum of per-object orbit counts) - (orbits outside the pure E circuits)

is NOT a property of the cover alone: it depends on WHICH decomposition is
used.  Writing s_p, s_c, s_m for the piece, split-chain and merged-chain
decompositions, one cover satisfies

    s_m <= s_c <= s_p,
    deficit budget = 5k - G + 5s_M,   token budget = B* - s_M     (per model M)

so evaluating two different models at the SAME s and taking the minimum is
unsound: each model may be closed at an s that is not its own.  The sound
combination groups the rows by the model-independent coordinates and takes

    bound_M(C) = max over the s values admissible for M of bound_M(C, s),
    excluded   iff  min over M of bound_M(C) < required.

An extra sharp constraint is available: a model with exactly ONE object has
s = 0, because then that object's orbits ARE the orbits outside the pure
circuits.  The split-chain model has d+1+h objects and the merged-chain model
d+1, both fixed by the row, so the constraint applies exactly there.

MODELS
  piece   : hex-simple marked pieces, m <= z+1+h, companion-hex masks (l6_coupled_144)
  split   : d+1+h chains, A/B dirty edges retained, heavy joints CUT
  merged  : d+1 chains, A/B dirty edges retained, heavy joints KEPT INSIDE
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_coupled_144 as PIECE                                    # noqa: E402
import l6_chain_rows_144 as CR                                    # noqa: E402
import l6_871_analysis_144 as AN                                  # noqa: E402

COORD = ("k", "Z", "H", "Bstar", "G", "g", "c", "d", "D2", "Qs", "h")
NEED_MERGED: set = set()


def group_rows(t):
    """Rows keyed by the model-independent coordinates; s is kept as a list."""
    out = {}
    for r in CR.rows_for(t, False):
        key = tuple(r[c] for c in COORD)
        out.setdefault(key, []).append(r)
    return out


def piece_max(variants):
    best, unknown = -1, False
    for r in variants:
        v, det = PIECE.evaluate_row(dict(r), coupled=True)
        if det.get("unknown_seen"):
            unknown = True
        best = max(best, v)
    return best, unknown


def split_max(variants):
    r0 = variants[0]
    nch = r0["d"] + 1 + r0["h"]
    best, fb = -1, False
    for r in variants:
        if nch == 1 and r["s"] != 0:
            continue                       # one object forces s = 0
        CR._best.cache_clear()
        v, _, f = CR.row_bound(r)
        best, fb = max(best, v), fb or f
    return best, fb


def merged_max(variants, node_cap=8_000_000_000, allow_compute=True):
    """The heavy-merged model: d+1 objects, heavy joints inside."""
    r0 = variants[0]
    nch = r0["d"] + 1
    if r0["h"] == 0:
        return None, False                 # identical to `split`, nothing new
    best, fb = -1, False
    for r in variants:
        if nch == 1 and r["s"] != 0:
            continue
        if nch != 1:
            return None, False             # not implemented for several components
        tot = 2 * r["g"]
        args = (r["b_sum"], r["D_sum"], min(r["D2"], tot), min(r["Qs"], tot),
                min(max(0, r["Z"] - r["Qs"]), tot), r["h"])
        key = "%d|%d|%d|%d|%d|%d" % args
        rec = AN._H.get(key)
        if rec is None or rec.get("capped"):
            if not allow_compute:
                NEED_MERGED.add(args)
                return None, True
            # the decision form first: it is only ever used to CLOSE a row
            rec = AN.heavy_cell(*args, node_cap=node_cap, target=r["required"])
            if rec["capped"]:
                rec = AN.heavy_cell(*args, node_cap=node_cap * 5,
                                    target=r["required"])
        if rec["capped"]:
            NEED_MERGED.add(args)
            fb = True
            continue
        best = max(best, rec["cc"])
    return (best if best >= 0 else None), fb


def run(t, allow_compute=True):
    groups = group_rows(t)
    strict = surv = 0
    survivors, detail = [], []
    for key, variants in sorted(groups.items()):
        req = variants[0]["required"]
        pv, punk = piece_max(variants)
        sv, sfb = split_max(variants)
        bound = min(x for x in (pv, sv) if x is not None)
        closed_by = "piece" if pv <= sv else "split"
        mv = None
        if bound >= req:
            mv, mfb = merged_max(variants, allow_compute=allow_compute)
            if mv is not None and mv < bound:
                bound, closed_by = mv, "merged"
        rec = dict(zip(COORD, key))
        rec.update(required=req, piece=pv, split=sv, merged=mv, bound=bound,
                   s_values=[r["s"] for r in variants],
                   fallback=(punk or sfb))
        if bound < req:
            rec["verdict"] = "STRICT"
            rec["closed_by"] = closed_by
            strict += 1
        else:
            rec["verdict"] = "EQUALITY" if bound == req else "OPEN"
            surv += 1
            survivors.append(rec)
        detail.append(rec)
    return dict(t=t, L=867 + t, coordinate_rows=len(groups), strict=strict,
                surviving=surv, survivors=survivors,
                surviving_with_fallback=sum(1 for x in survivors if x["fallback"]))


if __name__ == "__main__":
    PIECE.load_caps()
    CR.load_cache()
    AN.load_h()
    out = {"disclaimer": "Upper-bound models only.  This does NOT prove L6 >= 872."}
    for t in [int(x) for x in (sys.argv[1:] or ["2", "3", "4"])]:
        res = run(t)
        out[f"L{867 + t}"] = {k: v for k, v in res.items() if k != "survivors"}
        out[f"L{867 + t}_survivors"] = res["survivors"]
        print(f"L{867 + t}", json.dumps(out[f"L{867 + t}"]), flush=True)
        for x in res["survivors"][:40]:
            print("   ", json.dumps({k: x[k] for k in
                                     ("k", "Z", "H", "Bstar", "G", "c", "d",
                                      "D2", "h", "required", "piece", "split",
                                      "merged", "bound", "verdict")}), flush=True)
    out["merged_cells_needed"] = [list(x) for x in sorted(NEED_MERGED)]
    (ROOT / "outputs" / "rr_l6_rows_final_144.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
