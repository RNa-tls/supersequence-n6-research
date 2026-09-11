#!/usr/bin/env python3
"""L6 endgame — COUPLED evaluation of the arithmetic rows for L = 869/870/871.

Why coupled.  Summing independent fragment capacities double-counts the
freedom that the type-A (dirty sigma) seams destroy: a seam whose two
incident clean-E blocks are both FULL forces a second repeated hexagon by the
companion-hexagon lemma, and the repeat budget R_int pays for at most
`Z - Qs` such seams.  So the pieces cannot be priced independently; the mask
of one piece constrains its neighbour.  This module therefore runs a DP along
the piece path, with the constrained seams placed ADVERSARIALLY (the relaxation
lets the hypothetical cover choose where they sit), and maximises

    sum_j  C(b_j, D_j, mask_j)

subject to  sum b_j = B*-s,  sum D_j = 5k-G+5s,  and every constrained seam
having at least one partial incident endpoint block.

Everything here is an UPPER bound on the realisable port total.  A row is
CLOSED only when that upper bound is STRICTLY below the required 120+G-5c.
"""
from __future__ import annotations
import json, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPFILE = ROOT / "outputs" / "rr_l6_marked_capacity_table_144.json"

NEG = -10**9
_CAP: dict = {}
MISSING: set = set()


def load_caps(path=CAPFILE):
    global _CAP
    _CAP = {}
    raw = json.loads(Path(path).read_text())
    for b, tab in raw["tables"].items():
        for key, val in tab.items():
            d, mask = key.split("|")
            _CAP[(int(b), int(d), mask)] = val
    _CAP["_dmax"] = raw["dmax"]
    _CAP["_bmax"] = raw["bmax"]
    return raw


HEXCAP = 120          # a hex-simple chain can never exceed the 120 hexagons


def C(b, d, fp, lp):
    """Marked capacity.  Uncomputed cells fall back to the sound bound 120.

    The fallback keeps every verdict valid: a row closed with it is genuinely
    closed.  Rows that merely SURVIVE while touching a fallback cell are
    reported separately, because a finer cell might still close them.
    """
    if b < 0 or d < 0:
        return None
    bm = _CAP["_bmax"].get(str(b))
    if bm is None or d > bm:
        MISSING.add((b, d))
        return HEXCAP
    v = _CAP.get((b, d, f"{fp}{lp}"))
    if v is None:
        MISSING.add((b, d))
        return HEXCAP
    return None if v < 0 else v     # v < 0 means the mask is infeasible


def best_chain(m, btot, Dtot, nmark):
    """Max sum of marked capacities over m pieces in a path.

    `nmark` constrained seams are placed adversarially among the m-1 seams;
    a constrained seam needs its left piece's LAST block or its right piece's
    FIRST block to be partial.  Returns None if some needed cell is unknown,
    NEG if no admissible assignment exists.
    """
    unknown = [False]

    @lru_cache(maxsize=None)
    def go(j, b, d, a, forced_fp):
        # j pieces already placed; a constrained seams still to place
        if j == m:
            return 0 if (a == 0 and not forced_fp) else NEG
        if a > m - j - 1:
            return NEG
        best = NEG
        for fp in ((1,) if forced_fp else (0, 1)):
            for lp in (0, 1):
                for bb in range(b + 1):
                    for dd in range(d + 1):
                        v = C(bb, dd, fp, lp)
                        if v is None:
                            continue
                        if v == HEXCAP:
                            unknown[0] = True
                        # seam after this piece
                        if j == m - 1:
                            r = go(j + 1, b - bb, d - dd, a, 0)
                            if r > NEG // 2:
                                best = max(best, v + r)
                            continue
                        # seam not constrained
                        r = go(j + 1, b - bb, d - dd, a, 0)
                        if r > NEG // 2:
                            best = max(best, v + r)
                        if a > 0:
                            # constrained seam, covered on the left
                            if lp:
                                r = go(j + 1, b - bb, d - dd, a - 1, 0)
                                if r > NEG // 2:
                                    best = max(best, v + r)
                            # constrained seam, covered on the right
                            r = go(j + 1, b - bb, d - dd, a - 1, 1)
                            if r > NEG // 2:
                                best = max(best, v + r)
        return best

    r = go(0, btot, Dtot, nmark, 0)
    go.cache_clear()
    return r, unknown[0]


def rows_for(t, use_sigma_deficit=True):
    """Necessary arithmetic rows for L = 867 + t, from MASTER-142 + bookkeeping."""
    out = []
    for k in range(t + 1):
        for Z in range(t - k + 1):
            for H in range(t - k - Z + 1):
                Bs = t - k - Z - H
                for G in range(0, 5 * k + 1):
                    for g in range(0, G // 2 + 1):
                        for c in range(0, G - 2 * g + 1):
                            d = G - 2 * g - c
                            z = G - c
                            D2 = z - Z
                            if D2 < 0:
                                continue
                            for Qs in range(0, Z + 1):
                                if D2 + Qs > 2 * g:
                                    continue
                                if use_sigma_deficit and \
                                   5 * k - G + 5 * Bs < D2 + Qs - Z - d:
                                    continue
                                for s in range(0, Bs + 1):
                                    for h in range(0, H + 1):
                                        Dsum = 5 * k - G + 5 * s
                                        if Dsum < 0:
                                            continue
                                        out.append(dict(
                                            t=t, k=k, Z=Z, H=H, Bstar=Bs, G=G,
                                            g=g, c=c, d=d, D2=D2, Qs=Qs, s=s,
                                            h=h, m_max=z + 1 + h,
                                            required=120 + G - 5 * c,
                                            D_sum=Dsum, b_sum=Bs - s))
    return out


def evaluate_row(r, coupled=True):
    """Best over all admissible piece counts; returns (bound, detail)."""
    nA = max(0, r["D2"] - r["d"])                 # retained interior A seams
    nB = max(0, r["Qs"] - r["d"])                 # retained interior B seams
    badmax = max(0, r["Z"] - r["Qs"])             # full/full A seams affordable
    nmark = max(0, nA - badmax) if coupled else 0
    m_lo = max(1, r["D2"] + r["Qs"] - r["d"] + 1)   # every retained A/B edge is a join
    m_hi = r["m_max"]
    if m_lo > m_hi:
        return NEG, dict(reason="m_lo>m_hi", m_lo=m_lo, m_hi=m_hi, nmark=nmark)
    best, unknown, arg = NEG, False, None
    for m in range(m_lo, m_hi + 1):
        v, unk = best_chain(m, r["b_sum"], r["D_sum"], min(nmark, m - 1))
        unknown = unknown or unk
        if v > best:
            best, arg = v, m
    return best, dict(nmark=nmark, m_lo=m_lo, m_hi=m_hi, m_arg=arg,
                      unknown_seen=unknown)


def run(t, coupled=True, use_sigma_deficit=True):
    rows = rows_for(t, use_sigma_deficit)
    strict = surv = unk = 0
    surviving, unknown_rows = [], []
    for r in rows:
        b, det = evaluate_row(r, coupled)
        r["detail"] = det
        if b <= NEG // 2:
            r["bound"] = "INFEASIBLE"
            r["verdict"] = "STRICT"
            strict += 1
        elif b < r["required"]:
            r["bound"] = b
            r["verdict"] = "STRICT"
            strict += 1
        else:
            r["bound"] = b
            r["verdict"] = "EQUALITY" if b == r["required"] else "OPEN"
            surv += 1
            surviving.append(r)
            if det.get("unknown_seen"):
                unk += 1
                unknown_rows.append(r)
    return dict(t=t, L=867 + t, coupled=coupled, rows=len(rows), strict=strict,
                surviving=surv, surviving_with_fallback_cell=unk,
                surviving_rows=surviving[:60], unknown_rows=unknown_rows[:60])


if __name__ == "__main__":
    load_caps()
    res = {}
    for t in [int(x) for x in (sys.argv[1:] or ["2"])]:
        for coup in (False, True):
            r = run(t, coupled=coup)
            res[f"L{867+t}_{'coupled' if coup else 'independent'}"] = r
    res["missing_cells"] = sorted(MISSING)
    (ROOT / "outputs" / "rr_l6_coupled_144.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    for kk, vv in res.items():
        if kk == "missing_cells":
            print("missing cells:", vv[:40], "…" if len(vv) > 40 else "")
            continue
        print(kk, json.dumps({x: vv[x] for x in
                              ("rows", "strict", "surviving", "unknown")}))
