#!/usr/bin/env python3
"""L6 endgame — what exactly is left at length 871.

For every row that neither the piece model nor the chain model closes, this
records
  * the exact budget allocation that attains the upper bound (the numerical
    equality witness Phase 6 asks for),
  * a cross-check against the HEAVY-MERGED chain model, in which weight >= 4
    joints stay inside the component instead of handing the model h free
    objects (chains = d+1 rather than d+1+h),
  * the structural family the row belongs to.

Nothing here closes 871.  The point is to state precisely what does not close
and to check that the remainder is not an artefact of one particular relaxation.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_chain_rows_144 as CR                                    # noqa: E402

EXE = ROOT / "outputs" / "l6chain_144.exe"
HCACHE = ROOT / "outputs" / "rr_l6_heavychain_capacity_144.json"
_H = {}


def load_h():
    global _H
    _H = json.loads(HCACHE.read_text()) if HCACHE.exists() else {}


def heavy_cell(b, d, a, bb, e, h, node_cap=0, target=0):
    key = f"{b}|{d}|{a}|{bb}|{e}|{h}"
    rec = _H.get(key)
    if rec is not None and not rec.get("capped"):
        return rec
    CR.write_ub()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e), str(h),
                        str(node_cap), str(CR.UB), str(target)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"heavy cell {key} failed: {r.stderr[:300]}")
    c = json.loads(r.stdout)
    rec = dict(cc=c["cc"], nodes=c["nodes"], capped=c["capped"],
               seconds=c["seconds"], target=target)
    _H[key] = rec
    HCACHE.write_text(json.dumps(_H, ensure_ascii=False, indent=1))
    return rec


def allocation(r):
    """Exact budget split attaining the chain upper bound (brute force, small)."""
    nch = r["d"] + 1 + r["h"]
    tot = 2 * r["g"]
    emax = max(0, r["Z"] - r["Qs"])
    res = {"best": None, "split": None}

    def go2(i, b, D, a, e, split, total):
        if i == nch:
            if b == 0 and D == 0 and (res["best"] is None or total > res["best"]):
                res["best"], res["split"] = total, list(split)
            return
        for xb in range(b + 1):
            for xd in range(D + 1):
                for xa in range(min(a, tot) + 1):
                    for xe in range(min(e, tot - xa) + 1):
                        v, _ = CR.CC(xb, xd, xa, min(r["Qs"], tot), xe)
                        go2(i + 1, b - xb, D - xd, a - xa, e - xe,
                            split + [dict(b=xb, D=xd, a=xa, e=xe, cc=v)],
                            total + v)

    go2(0, r["b_sum"], r["D_sum"], min(r["D2"], tot), min(emax, tot), [], 0)
    return res


def main():
    CR.load_cache()
    load_h()
    out = {"disclaimer": "871 is NOT closed here.  These are the rows that "
                         "survive both relaxations, with their witnesses."}
    rows = []
    for r in CR.rows_for(4, False):
        pv = CR.piece_bound(r)
        if pv is not None and pv < r["required"]:
            continue
        CR._best.cache_clear()
        v, nch, fb = CR.row_bound(r)
        if v < r["required"]:
            continue
        rec = {k: r[k] for k in ("k", "Z", "H", "Bstar", "G", "g", "c", "d",
                                 "D2", "Qs", "s", "h", "required", "D_sum",
                                 "b_sum")}
        rec["chains_split_model"] = nch
        rec["piece_bound"] = pv
        rec["chain_bound"] = v
        rec["slack"] = v - r["required"]
        rec["fallback_used"] = fb
        alloc = allocation(r)
        rec["witness_allocation"] = alloc["split"]
        # heavy-merged cross-check: only for a single component
        if r["d"] == 0 and r["h"] > 0:
            args = (r["b_sum"], r["D_sum"], min(r["D2"], 2 * r["g"]),
                    min(r["Qs"], 2 * r["g"]),
                    min(max(0, r["Z"] - r["Qs"]), 2 * r["g"]), r["h"])
            hc = heavy_cell(*args, node_cap=8_000_000_000)
            if hc["capped"]:                      # fall back to the decision form
                hc = heavy_cell(*args, node_cap=40_000_000_000,
                                target=r["required"])
            rec["heavy_merged"] = dict(cc=hc["cc"], capped=hc["capped"],
                                       nodes=hc["nodes"],
                                       target=hc.get("target", 0))
            rec["heavy_closes"] = (not hc["capped"]) and hc["cc"] < r["required"]
        rows.append(rec)
        print(json.dumps({k: rec[k] for k in
                          ("k", "Z", "H", "Bstar", "G", "c", "d", "D2", "s", "h",
                           "required", "D_sum", "b_sum", "chain_bound", "slack")}),
              flush=True)
    out["surviving"] = rows
    out["count"] = len(rows)
    fam = {}
    for x in rows:
        key = f"h={x['h']} d={x['d']} D2={x['D2']} b_sum={x['b_sum']}"
        fam[key] = fam.get(key, 0) + 1
    out["families"] = fam
    (ROOT / "outputs" / "rr_l6_871_analysis_144.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("surviving:", len(rows))
    print("families:", json.dumps(fam, ensure_ascii=False))
    print("heavy-merged closes:",
          sum(1 for x in rows if x.get("heavy_closes")), "of",
          sum(1 for x in rows if "heavy_merged" in x))


if __name__ == "__main__":
    main()
