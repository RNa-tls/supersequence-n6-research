#!/usr/bin/env python3
"""L6 endgame — independent enumeration of the L=869/870/871 resource rows.

Uses only:
  * the MASTER identity  L = 867 + k + Z + H + B*   (verified as a rearrangement
    of the pure-counting identity L = 844 + G + S + H);
  * the Round-142 splice bookkeeping relations, re-derived here as CONSTRAINTS;
  * the sigma-deficit inequality  5k - G + 5B* >= D2 + Qs - Z - d  (proved
    independently in src/l6_sigma_deficit_144.py);
  * MY OWN N*(b,0,D) capacity tables, computed in earlier rounds and matching
    Astra's "marked capacities" cell for cell.

Relations (all from Round 142 Route B section B4/B5):
    0 <= G <= 5k                      (D_phi = 5k - G >= 0)
    K = G + 1 - 2g >= 1,  g >= 0      (incidence theorem, K = G+1 mod 2)
    c >= 0,  d = K - 1 - c = G - 2g - c >= 0
    z = G - c = 2g + d
    D2 = z - Z >= 0                   (definition of Z)
    0 <= Qs <= Z,  D2 + Qs <= 2g      (SAME-HEX)
    0 <= s <= B*,  sum b_j = B* - s
    h <= H                            (each heavy joint contributes >=1 to H)
    m <= z + 1 + h
    required passes  = 120 + G - 5c
    sum D_j          = 5k - G + 5s
"""
from __future__ import annotations
import json, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# My own independently computed N*(b,0,D).  None = not yet computed.
NSTAR = {
    0: {0: 20, 1: 20, 2: 33, 3: 33, 4: 46, 5: 46, 6: 49, 7: 58, 8: 62, 9: 66,
        10: 70, 11: 74, 12: 83, 13: 83, 14: 96, 15: 96, 16: 96, 17: 103},
    1: {0: 35, 1: 35, 2: 48, 3: 48, 4: 61, 5: 61, 6: 64, 7: 73, 8: 77, 13: 98},
    2: {0: 50, 1: 50, 2: 63, 3: 63, 4: 76, 5: 76, 6: 79, 7: 88, 8: 92},
    3: {0: 65, 1: 65, 2: 78, 3: 78},
}
MISSING = set()


def cap(b, D):
    """Upper bound for one marked hex-simple piece; None if unknown."""
    if b < 0 or D < 0:
        return None
    tab = NSTAR.get(b)
    if tab is None:
        MISSING.add((b, D))
        return None
    if D in tab:
        return tab[D]
    known = [d for d in tab if d <= D]
    if not known:
        MISSING.add((b, D))
        return None
    # N* is nondecreasing in D; using a larger tabulated D is a safe OVER-bound
    bigger = [d for d in tab if d >= D]
    if bigger:
        return tab[min(bigger)]
    MISSING.add((b, D))
    return None


def max_capacity(m, btot, Dtot):
    """Max sum of cap(b_j,D_j) over m pieces with the given totals (padding ok)."""
    @lru_cache(maxsize=None)
    def go(i, b, D):
        if i == m - 1:
            v = cap(b, D)
            return v
        best = None
        for bb in range(b + 1):
            for dd in range(D + 1):
                v = cap(bb, dd)
                if v is None:
                    continue
                r = go(i + 1, b - bb, D - dd)
                if r is None:
                    continue
                t = v + r
                if best is None or t > best:
                    best = t
        return best
    r = go(0, btot, Dtot)
    go.cache_clear()
    return r


def rows_for(t, sigma_deficit=True):
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
                                if sigma_deficit and \
                                   5 * k - G + 5 * Bs < D2 + Qs - Z - d:
                                    continue
                                for s in range(0, Bs + 1):
                                    for h in range(0, H + 1):
                                        m = z + 1 + h
                                        req = 120 + G - 5 * c
                                        Dsum = 5 * k - G + 5 * s
                                        btot = Bs - s
                                        if Dsum < 0 or req < 1:
                                            continue
                                        out.append(dict(
                                            t=t, k=k, Z=Z, H=H, Bstar=Bs, G=G,
                                            g=g, c=c, d=d, D2=D2, Qs=Qs, s=s,
                                            h=h, m_max=m, required=req,
                                            D_sum=Dsum, b_sum=btot))
    return out


def evaluate(rows):
    surv, closed, unknown = [], 0, []
    for r in rows:
        cp = max_capacity(r["m_max"], r["b_sum"], r["D_sum"])
        r["capacity"] = cp
        if cp is None:
            r["verdict"] = "UNKNOWN_CAPACITY"
            unknown.append(r)
        elif cp < r["required"]:
            r["verdict"] = "STRICT"
            closed += 1
        elif cp == r["required"]:
            r["verdict"] = "EQUALITY"
            surv.append(r)
        else:
            r["verdict"] = "OPEN"
            surv.append(r)
    return dict(total=len(rows), strict=closed, surviving=len(surv),
                unknown=len(unknown),
                surviving_rows=surv[:40], unknown_rows=unknown[:20])


if __name__ == "__main__":
    res = {}
    for t, L in ((2, 869), (3, 870), (4, 871)):
        for sd in (False, True):
            rows = rows_for(t, sigma_deficit=sd)
            ev = evaluate(rows)
            res[f"L{L}{'_sigma' if sd else '_nosigma'}"] = {
                kk: vv for kk, vv in ev.items()
                if kk not in ("surviving_rows", "unknown_rows")}
            if sd:
                res[f"L{L}_sigma_detail"] = dict(
                    surviving=ev["surviving_rows"], unknown=ev["unknown_rows"])
    res["missing_capacity_cells"] = sorted(MISSING)
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_l6_rows_144.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if "detail" not in k},
                     ensure_ascii=False, indent=1))
