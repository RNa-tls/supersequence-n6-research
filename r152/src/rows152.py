#!/usr/bin/env python3
"""Round 152 -- the CERTIFIED-ONLY row evaluator.

Every capacity value used here must carry an EXACT_CERTIFIED verdict from
r152/src/checker152.py (or its C twin) in the verification report passed with
--verify.  Nothing else is read: the round-147 tables are NOT consulted.  A
budget vector with no certified cell falls back to the analytic bound
(P2) 120 + a + bb + e, which is proved in research/RR_L6_R147_SOUND_UB.md and
is therefore not an act of trust.

Two further departures from r148/src/rows148.py:

  * the heavy-retained (merged) model is keyed on HMAX = H, not on the joint
    count h.  r148 used h; see r152/src/heavyfix152.py and
    r152/certs/heavyfix_152.json for the reproduction and the repair.
  * the piece model is not used at all.  It is the one model whose bound is
    not a sum of chain capacities, so leaving it out makes the census rest on
    certified capacities alone.  If a row needs it, the row is reported as
    SURVIVING rather than quietly closed.

Usage:
  rows152.py --verify r152/certs/verify_all_152.json --layers 3 4
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COORD = ("k", "Z", "H", "Bstar", "G", "g", "c", "d", "D2", "Qs", "h")
HEXCAP, NEG = 120, -10 ** 9
CERT = {}
FALLBACKS = Counter()


def rows(t):
    """Row enumeration, G outermost (same shape as the round-148 third pass)."""
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


def CC(b, d, a, bb, e, h=0):
    """A certified capacity, or the proved analytic bound when there is none."""
    v = CERT.get((b, d, a, bb, e, h))
    if v is None:
        FALLBACKS[(b, d, a, bb, e, h)] += 1
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
    sv = NEG
    for r in variants:                                  # heavy CUT: d+1+h chains
        n = r["d"] + 1 + r["h"]
        if n == 1 and r["s"] != 0:
            continue
        best.cache_clear()
        tot = 2 * r["g"]
        v, _ = best(n, r["b_sum"], r["D_sum"], min(r["D2"], tot),
                    min(r["Qs"], tot), min(max(0, r["Z"] - r["Qs"]), tot), tot)
        if v > sv:
            sv = v
    if sv > NEG // 2:
        res["split"] = sv
    mv = None
    for r in variants:                                  # heavy KEPT: d+1 chains
        if r["H"] == 0 or r["d"] + 1 != 1 or r["s"] != 0:
            continue
        tot = 2 * r["g"]
        v, _ = CC(r["b_sum"], r["D_sum"], min(r["D2"], tot), min(r["Qs"], tot),
                  min(max(0, r["Z"] - r["Qs"]), tot), r["H"])
        if mv is None or v > mv:
            mv = v
    if mv is not None:
        res["merged"] = mv
    return req, res


def census(t):
    groups = {}
    for r in rows(t):
        groups.setdefault(tuple(r[c] for c in COORD), []).append(r)
    tally, detail, closers = Counter(), [], Counter()
    for key, variants in sorted(groups.items()):
        req, res = bounds(variants)
        closing = {k: v for k, v in res.items() if v < req}
        if closing:
            tally["STRICTLY_CLOSED"] += 1
            closers[min(closing, key=lambda k: closing[k])] += 1
            continue
        verdict = "EQUALITY" if res and min(res.values()) == req else "SURVIVING"
        tally[verdict] += 1
        detail.append(dict(zip(COORD, key)) |
                      dict(required=req, verdict=verdict, bounds=res))
    return dict(rows=len(groups), tally=dict(tally), closed_by=dict(closers),
                non_strict=detail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="append", required=True)
    ap.add_argument("--layers", nargs="*", type=int, default=[3, 4])
    ap.add_argument("--out", default="r152/certs/census_152.json")
    a = ap.parse_args()
    for f in a.verify:
        rep = json.loads(Path(f).read_text())
        for row in rep["rows"]:
            if row["status"] != "EXACT_CERTIFIED":
                continue
            CERT[tuple(int(x) for x in row["cell"].split("|"))] = row["cap"]
    print(f"certified cells available: {len(CERT)}", flush=True)
    out = dict(certified_cells=len(CERT), verify_reports=a.verify, layers={})
    for t in a.layers:
        c = census(t)
        out["layers"][f"L{867 + t}"] = c
        print(f"L{867 + t}: rows={c['rows']} {json.dumps(c['tally'])} "
              f"closed_by={json.dumps(c['closed_by'])}", flush=True)
        for x in c["non_strict"]:
            print("   ", json.dumps(x), flush=True)
    out["analytic_fallback_cells"] = len(FALLBACKS)
    out["analytic_fallback_uses"] = sum(FALLBACKS.values())
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"fallback cells={len(FALLBACKS)} uses={sum(FALLBACKS.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
