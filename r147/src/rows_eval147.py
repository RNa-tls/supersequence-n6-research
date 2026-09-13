#!/usr/bin/env python3
"""Round 147 Phase 8/9 -- evaluate every coordinate row with SOUND capacities.

Reads only:
  r147/rows                                  rows regenerated from definitions
  r147/tables/chain_cells_147.json           sound chain capacities (Phase 2)
  r147/tables/heavy_cells_147.json           sound heavy capacities (Phase 2)
  outputs/rr_l6_marked_capacity_table_144.json   the PIECE table, which round
      146 showed is untouched by the UB defect (mask-00-only UB file, no budget
      dimension in its key, no conflicting duplicate line, five sampled cells
      recomputed table-free agreeing exactly on all four masks)

Never reads: the refuted round-144 chain tables, rr_l6_rows_final_144.json, or
any closure label.

The split/merged envelope maximisation is re-implemented here rather than
imported, with its own memo and its own loop order.

CLASSIFICATION of a row (group of variants differing only in s):
  STRICTLY_CLOSED  some model's bound, computed with no fallback value, is
                   strictly below the required port count
  EQUALITY         the minimum over models equals required exactly
  SURVIVING        the minimum over models exceeds required
  UNKNOWN_CAP      the only bound below required leans on a cell that is not an
                   exact uncapped capacity (never counted as closed)
"""
from __future__ import annotations
import json, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147 = ROOT / "r147"
sys.path.insert(0, str(R147 / "src"))
sys.path.insert(0, str(ROOT / "src"))
import rows147                                                      # noqa: E402
import l6_coupled_144 as PIECE                                      # noqa: E402

HEXCAP = 120
NEG = -10 ** 9
COORD = rows147.COORD

CH, HV = {}, {}
FALLBACK = [0]


def load_cells():
    global CH, HV
    p = R147 / "tables" / "chain_cells_147.json"
    CH = {}
    for k, v in json.loads(p.read_text()).items():
        if v.get("status") == "EXACT_UNCAPPED":
            CH[tuple(int(x) for x in k.split("|"))] = v["cc"]
    q = R147 / "tables" / "heavy_cells_147.json"
    HV = {}
    if q.exists():
        for k, v in json.loads(q.read_text()).items():
            if v.get("status") == "EXACT_UNCAPPED":
                HV[tuple(int(x) for x in k.split("|"))] = v["cc"]


def CC(b, d, a, bb, e, h=0):
    """Sound chain capacity, and whether it is only the analytic fallback.

    (P2) of r147/src/ub147.py: a chain with those reuse budgets carries at most
    120 + a + bb + e ports.  That is a proved bound, so a row closed while
    touching it is genuinely closed -- but it is so weak that in practice a row
    that needs it is reported UNKNOWN_CAP rather than closed."""
    src = HV if h else CH
    v = src.get((b, d, a, bb, e, h))
    if v is None:
        FALLBACK[0] += 1
        return HEXCAP + a + bb + e, True
    return v, False


@lru_cache(maxsize=2_000_000)
def _split(nch, b, D, a, bb, e, tot):
    """Max total ports over nch chains inside the envelope, plus a fallback flag.

    Envelope (round 142 section 6): a <= D2, bb <= Qs, e <= max(0, Z-Qs) and
    a + bb + e <= R_int <= 2g; each unit of a, bb or e consumes one unit of the
    shared repeat budget `tot`.
    """
    best, fb = NEG, False
    for xa in range(min(a, tot) + 1):
        for xbb in range(min(bb, tot - xa) + 1):
            for xe in range(min(e, tot - xa - xbb) + 1):
                for xb in range(b + 1):
                    for xd in range(D + 1):
                        if nch == 1:
                            if xb != b or xd != D:
                                continue
                            v, f = CC(xb, xd, xa, xbb, xe)
                            if v > best:
                                best, fb = v, f
                            continue
                        v, f = CC(xb, xd, xa, xbb, xe)
                        r, f2 = _split(nch - 1, b - xb, D - xd, a - xa,
                                       bb - xbb, e - xe,
                                       tot - xa - xbb - xe)
                        if r > NEG // 2 and v + r > best:
                            best, fb = v + r, (f or f2)
    return best, fb


def split_bound(r):
    nch = r["d"] + 1 + r["h"]
    tot = 2 * r["g"]
    return _split(nch, r["b_sum"], r["D_sum"], min(r["D2"], tot),
                  min(r["Qs"], tot), min(max(0, r["Z"] - r["Qs"]), tot), tot)


def merged_bound(r):
    """d+1 objects with the heavy joints kept INSIDE; only defined for one
    object, which is where round 144 implemented it."""
    if r["h"] == 0 or r["d"] + 1 != 1:
        return None, False
    tot = 2 * r["g"]
    key = (r["b_sum"], r["D_sum"], min(r["D2"], tot), min(r["Qs"], tot),
           min(max(0, r["Z"] - r["Qs"]), tot), r["h"])
    v = HV.get(key)
    if v is None:
        return None, True
    return v, False


def piece_bound(r):
    v, det = PIECE.evaluate_row(dict(r), coupled=True)
    return v, bool(det.get("unknown_seen"))


def classify(variants):
    req = variants[0]["required"]
    cands = []
    for name, fn in (("piece", piece_bound), ("split", split_bound),
                     ("merged", merged_bound)):
        best, fb, seen = None, False, False
        for r in variants:
            if name in ("split", "merged"):
                nch = r["d"] + 1 + (r["h"] if name == "split" else 0)
                if nch == 1 and r["s"] != 0:
                    continue          # one object forces s = 0
            v, f = fn(r)
            if v is None:
                continue
            seen = True
            if best is None or v > best:
                best, fb = v, f
        if seen and best is not None:
            cands.append((name, best, fb))
    if not cands:
        return dict(verdict="ERROR", required=req, bounds={})
    hard = [c for c in cands if not c[2] and c[1] < req]
    bounds = {c[0]: c[1] for c in cands}
    flags = {c[0]: c[2] for c in cands}
    if hard:
        best = min(hard, key=lambda c: c[1])
        return dict(verdict="STRICTLY_CLOSED", closed_by=best[0],
                    bound=best[1], required=req, bounds=bounds, flags=flags)
    clean = [c for c in cands if not c[2]]
    if clean:
        lo = min(clean, key=lambda c: c[1])
        if lo[1] == req:
            return dict(verdict="EQUALITY", closed_by=lo[0], bound=lo[1],
                        required=req, bounds=bounds, flags=flags)
        return dict(verdict="SURVIVING", bound=lo[1], required=req,
                    bounds=bounds, flags=flags)
    return dict(verdict="UNKNOWN_CAP", required=req, bounds=bounds, flags=flags)


def main(argv):
    load_cells()
    PIECE.load_caps()
    print(f"sound chain cells={len(CH)} heavy cells={len(HV)}", flush=True)
    out = {"chain_cells": len(CH), "heavy_cells": len(HV), "layers": {}}
    for t in [int(x) for x in (argv or ["0", "1", "2", "3", "4"])]:
        groups = {}
        for r in rows147.rows(t):
            groups.setdefault(tuple(r[c] for c in COORD), []).append(r)
        tally, survivors = {}, []
        for key, variants in sorted(groups.items()):
            _split.cache_clear()
            res = classify(variants)
            tally[res["verdict"]] = tally.get(res["verdict"], 0) + 1
            if res["verdict"] != "STRICTLY_CLOSED":
                survivors.append(dict(zip(COORD, key)) | res)
        out["layers"][f"L{867 + t}"] = dict(rows=len(groups), tally=tally)
        out[f"L{867 + t}_survivors"] = survivors
        print(f"L{867 + t}: rows={len(groups)} {json.dumps(tally)}", flush=True)
    (R147 / "rows" / "rows_eval_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
