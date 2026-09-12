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
    UB.write_text("\n".join(lines) + "\n")


def compute(b, d, a, bb, e, node_cap=0, target=0):
    """Prove one chain cell.

    With `target > 0` the searcher only answers "is `target` reachable?".  That
    is still exhaustive for THAT question -- every prefix of a chain with
    `target` ports has reach >= target, so it is never pruned -- so a run that
    ends uncapped below the target proves `CC <= target - 1`.
    """
    write_ub()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        str(node_cap), str(UB), str(target)],
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
    CACHE.write_text(json.dumps(_C, ensure_ascii=False, indent=1))
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
