#!/usr/bin/env python3
"""L6 endgame — row evaluation on the COUPLED CHAIN model.

Instead of pricing the hex-simple pieces separately and then re-imposing the
companion-hexagon lemma by hand, this evaluator prices a whole nonpure beta
COMPONENT at once.  The retained type A (sigma) and type B (sigma^2) dirty
edges stay inside the object, and a hexagon may be revisited only

  * at the target of such a dirty edge (its hexagon IS the source's), or
  * at one of the EXTRA collisions paid for out of the repeat budget.

The companion-hexagon lemma is then a consequence of literal hexagon occupancy,
not an extra hypothesis, and the freedom the piece model double-counted -- each
piece choosing its own first port -- is gone.

BUDGETS for one arithmetic row (Round142 RouteB, re-derived here):

    chains            = d + 1 + h          (d cycles + the dummy component,
                                            then h heavy cuts)
    sum of deficits   = 5k - G + 5s
    sum of tokens     = B* - s
    sum A             <= D2                (some A may be spent opening cycles)
    sum B             <= Qs
    sum A + B + extra <= R_int <= 2g       (every retained A/B target and every
                                            ordinary collision consumes one unit
                                            of the within-component repeat
                                            excess)
    required ports     = 120 + G - 5c

Every achievable configuration lies inside this envelope, so a row is CLOSED
only when the maximum of  sum_i CC(b_i, D_i, a_i, bb_i, e_i)  over the envelope
is STRICTLY below the required port count.
"""
from __future__ import annotations
import json, subprocess, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "outputs" / "l6chain_144.exe"
CACHE = ROOT / "outputs" / "rr_l6_chain_capacity_144.json"
UB = ROOT / "outputs" / "rr_l6_chain_ub_144.txt"
HEXCAP = 120
NEG = -10 ** 9

sys.path.insert(0, str(ROOT / "src"))
import l6_coupled_144 as PIECE                                    # noqa: E402
from l6_coupled_144 import rows_for                              # noqa: E402

_PIECE_READY = [False]


def piece_bound(r):
    """The independent endpoint-marked PIECE bound (src/l6_coupled_144.py).

    Both models are sound upper bounds, so a row may be closed by either.
    Evaluating the cheap piece bound first keeps the expensive chain cells to
    the rows that really need them.
    """
    if not _PIECE_READY[0]:
        PIECE.load_caps()
        _PIECE_READY[0] = True
    v, det = PIECE.evaluate_row(dict(r), coupled=True)
    if det.get("unknown_seen"):
        return None
    return v

_C: dict = {}
REQUESTED: set = set()
FALLBACK = [False]


def load_cache():
    global _C
    raw = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    _C = {}
    for k, v in raw.items():
        parts = k.split("|")
        if len(parts) == 4:                    # migrate the pre-EMAX cache
            k = "|".join(parts + ["0"])
        _C[k] = v
    return _C


# ---------------------------------------------------------------------------
# ROUND 146 -- WHY THE EMITTED TABLE WAS NOT A VALID UPPER BOUND.
#
# The searcher's pruning table is keyed by the COMBINED remaining budget
#     left = (AMAX - au) + (BMAX - bu) + (EMAX - eu),
# so UB[tok][d][S][h] has to bound every chain whose three budgets sum to at
# most S, i.e. it has to be the MAXIMUM over the splits (x, y, z) with
# x + y + z <= S.  `write_ub` emitted one line per CACHED CELL, i.e. one line
# per split, all under the same key S = a + bb + e, and the C loader keeps the
# SMALLEST value it sees for a key ("several independent upper bounds, take the
# best").  For 163 of the 425 keys the splits disagree -- e.g. b=0, d=0, S=10
# carries values from 20 to 50 -- so the table handed the searcher 20 where 50
# was needed, the searcher over-pruned, and the cells it then recorded were
# BELOW the true capacity (measured: 0|0|0|0|9 recorded 45, true 50;
# 0|0|0|0|10 recorded 40, true 55; 87 of the 377 b<=0,d<=1 cells too small).
# A capacity table that is too small is not a sound upper-bound model, so every
# row closed only by the chain models has to be redone.  See
# research/ERRATA_146_CHAIN_UB.md and src/l6_chain_recheck_146.py.
#
# The fix below aggregates by MAX per key, which is the sound direction.  It is
# NOT by itself enough: the values being aggregated must themselves come from
# runs that did not use an unsound table, which is what the recheck driver
# establishes cell by cell.
# ---------------------------------------------------------------------------


def write_ub():
    """Every proved chain cell is a sound suffix bound for a deeper search."""
    lines = []
    for key, rec in _C.items():
        if rec.get("capped"):
            continue
        b, d, a, bb, e = (int(x) for x in key.split("|"))
        v = rec["cc"] if not rec.get("bound_below") else rec["bound_below"] - 1
        lines.append(f"{b} {d} {a + bb + e} 0 {v}")
    base = ROOT / "outputs" / "rr_l6_marked_capacity_table_144.json"
    if base.exists():                          # a = 0 coincides with the pieces
        st = json.loads(base.read_text())
        for b, tab in st["tables"].items():
            for k, v in tab.items():
                dd, mask = k.split("|")
                if mask == "00" and v >= 0:
                    lines.append(f"{b} {dd} 0 0 {v}")
    hv = ROOT / "outputs" / "rr_l6_heavychain_capacity_144.json"
    if hv.exists():                        # proved heavy cells bound deeper ones
        for key, rec in json.loads(hv.read_text()).items():
            if rec.get("capped"):
                continue
            b, d, a, bb, e, h = (int(x) for x in key.split("|"))
            v = rec["cc"] if not rec.get("bound_below") else rec["bound_below"] - 1
            lines.append(f"{b} {d} {a + bb + e} {h} {v}")
    # aggregate by MAX per (b, d, combined budget, h) key: the C loader keeps
    # the minimum it sees, so emitting only the per-key maximum makes the two
    # agree on the one sound value.
    best: dict = {}
    for ln in lines:
        b, d, a, h, v = (int(x) for x in ln.split())
        k = (b, d, a, h)
        if k not in best or v > best[k]:
            best[k] = v
    UB.write_text("\n".join(f"{b} {d} {a} {h} {v}"
                            for (b, d, a, h), v in sorted(best.items())) + "\n")


def _save_cache():
    """Persist the chain cell cache, refusing to SHRINK it.

    ROUND 146 DATA-INTEGRITY GUARD.  `compute()` used to write `_C` straight
    back to the 1,501-cell ledger.  `_C` starts EMPTY and is only filled by
    `load_cache()`, so a single call to `compute()` without that preceding call
    replaced the whole audited ledger with one entry.  (It happened during the
    round-146 audit and was restored from git.)  Writing now (i) loads first if
    `_C` is empty, (ii) refuses any write that would drop cells, and (iii) is
    atomic, so an interrupted write cannot leave a truncated file behind.
    """
    on_disk = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    missing = set(on_disk) - set(_C)
    if missing:
        raise SystemExit(
            f"refusing to shrink {CACHE.name}: {len(missing)} cached cells "
            f"would be lost (call load_cache() first)")
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_C, ensure_ascii=False, indent=1))
    tmp.replace(CACHE)


def compute(b, d, a, bb, e, node_cap=0, target=0, h=0):
    """Prove one chain cell.

    With `target > 0` the searcher only answers "is `target` reachable?".  That
    is still exhaustive for THAT question -- every prefix of a chain with
    `target` ports has reach >= target, so it is never pruned -- so a run that
    ends uncapped below the target proves `CC <= target - 1`.

    ROUND 146 FIX.  The searcher grew a separate heavy budget HMAX (argv[6])
    when the heavy chain cells were added, and this driver was never updated:
    it passed `node_cap` where HMAX is read, the ub path where NODECAP is read
    and `target` where the ub FILE NAME is read, so every call died with
    "ubfile".  The 1,501 cached chain cells all predate that change and were
    produced by the then-correct six-argument call; the argument list below is
    the one `l6_871_analysis_144.heavy_cell` already used correctly.
    """
    if not _C:
        load_cache()
    write_ub()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        str(h), str(node_cap), str(UB), str(target)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"chain cell {b},{d},{a},{bb},{e} failed: {r.stderr[:300]}")
    c = json.loads(r.stdout)
    rec = dict(cc=c["cc"], nodes=c["nodes"], capped=c["capped"],
               seconds=c["seconds"])
    if target and not c["capped"] and c["cc"] < target:
        rec["bound_below"] = target      # proved: CC <= target - 1
    elif target:
        rec["target_run"] = target
    _C[f"{b}|{d}|{a}|{bb}|{e}"] = rec
    _save_cache()
    return rec


def CC(b, d, a, bb, e):
    """Chain capacity and whether it is the sound HEXCAP fallback, not a proof.

    A cell proved only in TARGET mode carries `bound_below`: the search was
    exhaustive for the question "are `bound_below` ports reachable?", so
    `bound_below - 1` is a proved upper bound for this cell.
    """
    # absolute bound: every port needs a fresh hexagon or one unit of reuse
    absolute = HEXCAP + a + bb + e
    rec = _C.get(f"{b}|{d}|{a}|{bb}|{e}")
    if rec is None or (rec.get("capped") and not rec.get("bound_below")):
        REQUESTED.add((b, d, a, bb, e))
        return absolute, True
    if rec.get("bound_below"):
        return min(rec["bound_below"] - 1, absolute), False
    return rec["cc"], False


@lru_cache(maxsize=600000)
def _best(nch, b, D, a, bb, e, tot):   # returns (value, used_fallback)
    """Max sum of CC over nch chains inside the budget envelope.

    a, bb, e are the remaining type A / type B / ordinary-collision budgets and
    `tot` the remaining shared repeat budget R_int; every unit of a, bb or e
    consumes one unit of tot.
    """
    best, fb = NEG, False
    for xb in range(b + 1):
        for xd in range(D + 1):
            for xa in range(min(a, tot) + 1):
                for xbb in range(min(bb, tot - xa) + 1):
                    for xe in range(min(e, tot - xa - xbb) + 1):
                        v, f1 = CC(xb, xd, xa, xbb, xe)
                        if nch == 1:
                            if xb == b and xd == D and v > best:
                                best, fb = v, f1
                            continue
                        r, f2 = _best(nch - 1, b - xb, D - xd, a - xa, bb - xbb,
                                      e - xe, tot - xa - xbb - xe)
                        if v + r > best:
                            best, fb = v + r, (f1 or f2)
    return best, fb


def row_bound(r):
    """Envelope:  a <= D2,  bb <= Qs,  e <= max(0, Z-Qs),  a+bb+e <= 2g."""
    nch = r["d"] + 1 + r["h"]
    tot = 2 * r["g"]
    emax = max(0, r["Z"] - r["Qs"])
    v, fb = _best(nch, r["b_sum"], r["D_sum"], min(r["D2"], tot),
                  min(r["Qs"], tot), min(emax, tot), tot)
    return v, nch, fb


def run(t, use_sigma_deficit=False):
    rows = rows_for(t, use_sigma_deficit)
    strict = surv = fb = 0
    by_piece = 0
    surviving = []
    for r in rows:
        pv = piece_bound(r)
        if pv is not None and pv < r["required"]:
            r["chains"] = r["d"] + 1 + r["h"]
            r["piece_bound"] = pv
            r["chain_bound"] = None
            r["verdict"] = "STRICT"
            strict += 1
            by_piece += 1
            continue
        r["piece_bound"] = pv
        v, nch, used_fb = row_bound(r)
        r["chains"] = nch
        r["chain_bound"] = v
        if v < r["required"]:
            r["verdict"] = "STRICT"
            strict += 1
        else:
            r["verdict"] = "EQUALITY" if v == r["required"] else "OPEN"
            surv += 1
            surviving.append(r)
            if used_fb:
                fb += 1
    return dict(t=t, L=867 + t, rows=len(rows), strict=strict,
                strict_by_piece_model=by_piece, surviving=surv,
                surviving_using_fallback=fb, surviving_rows=surviving)


if __name__ == "__main__":
    load_cache()
    out = {}
    for t in [int(x) for x in (sys.argv[1:] or ["3"])]:
        res = run(t)
        out[f"L{867 + t}"] = {k: v for k, v in res.items() if k != "surviving_rows"}
        out[f"L{867 + t}_surviving"] = res["surviving_rows"][:80]
        print(f"L{867 + t}", json.dumps(out[f"L{867 + t}"]), flush=True)
    need = sorted(REQUESTED)
    out["cells_requested_but_unproved"] = [list(x) for x in need]
    (ROOT / "outputs" / "rr_l6_chain_rows_144.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("unproved cells requested:", len(need))
