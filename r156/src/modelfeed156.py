#!/usr/bin/env python3
"""Round 156 Phases 9-10 -- the REAL COVER -> MODEL direction, made explicit.

H.extract is only worth anything if the chains it produces are an ADMISSIBLE
input to the capacity models, so that a model bound below `required` really
does refute the existence of the cover.  This file checks that direction on
the one real n = 6 object there is -- the 872 witness -- and checks the two
structural facts the direction rests on:

  (R1)  the row the witness actually realises is enumerated by the row
        enumeration, and its model bound is >= required.  It is in fact EXACTLY
        equal, so any bookkeeping error that inflated `required` or deflated a
        budget by even one unit would contradict a real object.
  (R2)  the model is monotone in the NUMBER of chains: using d+1+h chains when
        the extraction produced fewer can only raise the bound.  That is what
        makes "the chain count is at most d+1+h" a sound relaxation.

Capacities come only from r152/certs/verify_all_c152.json (EXACT/UPPER
certified); anything missing falls back to the proved analytic bound (P2).
"""
from __future__ import annotations
import json, sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract156 as X                                            # noqa: E402

HEXCAP, NEG = 120, -10 ** 9
CERT, EXACT = {}, {}


def load():
    rep = json.loads((ROOT / "r152" / "certs" / "verify_all_c152.json").read_text())
    for row in rep["rows"]:
        if row["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            continue
        key = tuple(int(x) for x in row["cell"].split("|"))
        CERT[key] = row["cap"]
        EXACT[key] = (row["status"] == "EXACT_CERTIFIED")
    return len(CERT)


def CC(b, d, a, bb, e, h=0):
    v = CERT.get((b, d, a, bb, e, h))
    return (HEXCAP + a + bb + e) if v is None else v


@lru_cache(maxsize=2_000_000)
def best(n, b, D, a, bb, e, tot):
    """Max sum of chain capacities over EXACTLY n chains sharing b and D."""
    if n == 1:
        r = NEG
        for xa in range(min(a, tot) + 1):
            for xb2 in range(min(bb, tot - xa) + 1):
                for xe in range(min(e, tot - xa - xb2) + 1):
                    r = max(r, CC(b, D, xa, xb2, xe))
        return r
    r = NEG
    for xa in range(min(a, tot) + 1):
        for xb2 in range(min(bb, tot - xa) + 1):
            for xe in range(min(e, tot - xa - xb2) + 1):
                for xb in range(b + 1):
                    for xd in range(D + 1):
                        q = best(n - 1, b - xb, D - xd, a - xa, bb - xb2,
                                 e - xe, tot - xa - xb2 - xe)
                        if q > NEG // 2:
                            r = max(r, CC(xb, xd, xa, xb2, xe) + q)
    return r


def rows(t):
    """The row enumeration, rebuilt from MASTER-142 and the proved
    inequalities -- identical in shape to r152/src/rows152.py:rows()."""
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
                                    if 5 * k - G + 5 * s < 0:
                                        continue
                                    for h in hs:
                                        out.append(dict(
                                            t=t, k=k, Z=Z, H=H, Bstar=Bs, G=G,
                                            g=g, c=c, d=d, D2=D2, Qs=Qs, s=s,
                                            h=h, required=120 + G - 5 * c,
                                            D_sum=5 * k - G + 5 * s,
                                            b_sum=Bs - s))
    return out


def main():
    ncert = load()
    out = {"certified_cells": ncert}

    # ---- the witness, extracted independently
    W6 = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    st = X.structure(W6, 6)
    r = X.extract(st)
    coord = {x: r[x] for x in ("k", "Z", "H", "Bstar", "G", "g", "c", "d",
                               "D2", "Qs", "h")}
    t = r["k"] + r["Z"] + r["H"] + r["Bstar"]
    out["witness"] = dict(coord=coord, t=t, length=r["length"],
                          sigma=r["sigma"], chains=r["chains"],
                          required=r["required"], sum_P=r["sum_P"],
                          D_sum=r["D_sum"], b_sum=r["b_sum"],
                          per_chain=r["per_chain"])

    # ---- (R1) is that row enumerated at t = 5, and what does the model say?
    hit = [row for row in rows(t)
           if all(row[x] == coord[x] for x in coord) and row["s"] == r["sigma"]]
    out["row_enumerated"] = len(hit)
    if hit:
        row = hit[0]
        n = row["d"] + 1 + row["h"]
        tot = 2 * row["g"]
        best.cache_clear()
        v = best(n, row["b_sum"], row["D_sum"], min(row["D2"], tot),
                 min(row["Qs"], tot), min(max(0, row["Z"] - row["Qs"]), tot),
                 tot)
        cell = (row["b_sum"], row["D_sum"], min(row["D2"], tot),
                min(row["Qs"], tot), min(max(0, row["Z"] - row["Qs"]), tot), 0)
        out["witness_row"] = dict(row=row, chains_in_model=n, split_bound=v,
                                  cell="|".join(map(str, cell)),
                                  cell_certified=cell in CERT,
                                  cell_exact=EXACT.get(cell),
                                  excludes_the_witness=(v < row["required"]),
                                  tight=(v == row["required"]))

    # ---- (R2) monotonicity of the model in the number of chains
    mono, viol = 0, []
    for b in range(0, 4):
        for D in range(0, 6):
            for a in range(0, 3):
                for tot in range(0, 3):
                    prev = None
                    for n in range(1, 5):
                        best.cache_clear()
                        v = best(n, b, D, min(a, tot), 0, 0, tot)
                        if prev is not None:
                            mono += 1
                            if v < prev:
                                viol.append(dict(b=b, D=D, a=a, tot=tot, n=n,
                                                 prev=prev, now=v))
                        prev = v
    out["chain_monotonicity"] = dict(comparisons=mono, violations=len(viol),
                                     examples=viol[:4],
                                     empty_chain_capacity=CC(0, 0, 0, 0, 0))

    out["ok"] = (out.get("witness_row", {}).get("excludes_the_witness") is False
                 and out["row_enumerated"] > 0
                 and not viol)
    (ROOT / "r156" / "certs" / "modelfeed_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "witness"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
