#!/usr/bin/env python3
"""Round 148 Phases 8/9 -- fresh L=870 and L=871 censuses, from the definitions.

Independent of round 147's evaluator: the rows are regenerated here by a THIRD
enumeration (driving the pass excess G outermost and solving for the component
decomposition, rather than driving k/Z/H/B* or driving (g,c,d)), the bounds are
recomputed, and every row records WHICH bound closes it.  No closure label, no
Q1/Q2 label and no round-144 chain table is read.

The equality rows are only compared with the historical Q1/Q2 labels AFTER they
have been found, in r148/certs/equality_identification_148.json.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
sys.path.insert(0, str(ROOT / "src"))
import l6_coupled_144 as PIECE                                      # noqa: E402

COORD = ("k", "Z", "H", "Bstar", "G", "g", "c", "d", "D2", "Qs", "h")
HEXCAP, NEG = 120, -10 ** 9
CH, HV = {}, {}


def load():
    global CH, HV
    for f, dst in (("chain_cells_147.json", "CH"), ("heavy_cells_147.json", "HV")):
        d = {}
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") != "EXACT_UNCAPPED":
                raise SystemExit(f"{f}: {k} is {v.get('status')}, refusing")
            d[tuple(int(x) for x in k.split("|"))] = v["cc"]
        globals()[dst] = d


def rows(t):
    """Third enumeration: G outermost, then the decomposition, then the rest."""
    out = []
    for G in range(0, 5 * t + 1):
        for k in range((G + 4) // 5, t + 1):
            if G > 5 * k:
                continue
            for g in range(0, G // 2 + 1):
                for c in range(0, G - 2 * g + 1):
                    d = G - 2 * g - c
                    z = 2 * g + d
                    for Z in range(0, t - k + 1):
                        D2 = z - Z
                        if D2 < 0 or D2 > 2 * g:
                            continue
                        for H in range(0, t - k - Z + 1):
                            Bs = t - k - Z - H
                            hs = [0] if H == 0 else list(range(1, H + 1))
                            for Qs in range(0, min(Z, 2 * g - D2) + 1):
                                for s in range(0, Bs + 1):
                                    Dsum = 5 * k - G + 5 * s
                                    if Dsum < 0:
                                        continue
                                    for h in hs:
                                        out.append(dict(
                                            t=t, k=k, Z=Z, H=H, Bstar=Bs, G=G,
                                            g=g, c=c, d=d, D2=D2, Qs=Qs, s=s,
                                            h=h, m_max=z + 1 + h,
                                            required=120 + G - 5 * c,
                                            D_sum=Dsum, b_sum=Bs - s))
    return out


FB = [0]


def CC(b, d, a, bb, e, h=0):
    v = (HV if h else CH).get((b, d, a, bb, e, h))
    if v is None:
        FB[0] += 1
        return HEXCAP + a + bb + e, True
    return v, False


@lru_cache(maxsize=3_000_000)
def best(n, b, D, a, bb, e, tot):
    r, fb = NEG, False
    for xa in range(min(a, tot) + 1):
        for xb2 in range(min(bb, tot - xa) + 1):
            for xe in range(min(e, tot - xa - xb2) + 1):
                for xb in range(b + 1):
                    for xd in range(D + 1):
                        if n == 1:
                            if xb != b or xd != D:
                                continue
                            v, f = CC(xb, xd, xa, xb2, xe)
                            if v > r:
                                r, fb = v, f
                            continue
                        v, f = CC(xb, xd, xa, xb2, xe)
                        q, f2 = best(n - 1, b - xb, D - xd, a - xa, bb - xb2,
                                     e - xe, tot - xa - xb2 - xe)
                        if q > NEG // 2 and v + q > r:
                            r, fb = v + q, f or f2
    return r, fb


def bounds(variants):
    req = variants[0]["required"]
    res = {}
    pv, pf = NEG, False
    for r in variants:
        v, det = PIECE.evaluate_row(dict(r), coupled=True)
        if v > pv:
            pv, pf = v, bool(det.get("unknown_seen"))
    res["piece"] = (pv, pf)
    sv, sf = NEG, False
    for r in variants:
        n = r["d"] + 1 + r["h"]
        if n == 1 and r["s"] != 0:
            continue
        best.cache_clear()
        tot = 2 * r["g"]
        v, f = best(n, r["b_sum"], r["D_sum"], min(r["D2"], tot),
                    min(r["Qs"], tot), min(max(0, r["Z"] - r["Qs"]), tot), tot)
        if v > sv:
            sv, sf = v, f
    if sv > NEG // 2:
        res["split"] = (sv, sf)
    mv = None
    for r in variants:
        if r["h"] == 0 or r["d"] + 1 != 1 or r["s"] != 0:
            continue
        tot = 2 * r["g"]
        key = (r["b_sum"], r["D_sum"], min(r["D2"], tot), min(r["Qs"], tot),
               min(max(0, r["Z"] - r["Qs"]), tot), r["h"])
        v = HV.get(key)
        if v is not None and (mv is None or v > mv):
            mv = v
    if mv is not None:
        res["merged"] = (mv, False)
    return req, res


def census(t):
    groups = {}
    for r in rows(t):
        groups.setdefault(tuple(r[c] for c in COORD), []).append(r)
    tally, detail, closers = Counter(), [], Counter()
    for key, variants in sorted(groups.items()):
        req, res = bounds(variants)
        clean = {k: v for k, v in res.items() if not v[1]}
        closing = {k: v[0] for k, v in clean.items() if v[0] < req}
        if closing:
            verdict = "STRICTLY_CLOSED"
            who = min(closing, key=lambda k: closing[k])
            closers[who] += 1
        elif clean and min(v[0] for v in clean.values()) == req:
            verdict = "EQUALITY"
            who = None
        elif clean:
            verdict = "SURVIVING"
            who = None
        else:
            verdict = "UNKNOWN_CAP"
            who = None
        tally[verdict] += 1
        if verdict != "STRICTLY_CLOSED":
            detail.append(dict(zip(COORD, key)) |
                          dict(required=req, verdict=verdict,
                               bounds={k: v[0] for k, v in res.items()}))
    return dict(rows=len(groups), tally=dict(tally), closed_by=dict(closers),
                non_strict=detail)


def main(argv):
    load()
    out = dict(chain_cells=len(CH), heavy_cells=len(HV), layers={})
    for t in [int(x) for x in (argv or ["3", "4"])]:
        c = census(t)
        out["layers"][f"L{867 + t}"] = c
        print(f"L{867 + t}: rows={c['rows']} {json.dumps(c['tally'])} "
              f"closed_by={json.dumps(c['closed_by'])} "
              f"fallbacks_used={FB[0]}", flush=True)
        for x in c["non_strict"]:
            print("   ", json.dumps(x), flush=True)
    out["analytic_fallbacks_used"] = FB[0]
    (R148 / "rows" / "census_148.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
