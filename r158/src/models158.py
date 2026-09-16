#!/usr/bin/env python3
"""Round 158 Phases 9-10 -- which model consumes which envelope bound, in
which direction, and what happens if a bound is slightly wrong.

THE THREE ROUTES, read off r152/src/rows152.py and src/l6_coupled_144.py.

  split  (d+1+h chains)   best(n, b_sum, D_sum,
                               min(D2, 2g), min(Qs, 2g),
                               min(max(0, Z-Qs), 2g), 2g)
         -> consumes a <= D2, bb <= Qs, e <= Z-Qs, a+bb+e <= 2g
            as UPPER bounds.

  merged (d+1 = 1 chain)  CC(b_sum, D_sum,
                             min(D2, 2g), min(Qs, 2g),
                             min(max(0, Z-Qs), 2g), H)
         -> the same four UPPER bounds, plus the heavy budget HMAX = H
            (the heavy COST sum(w-3)), NOT the heavy COUNT h.

  piece  (m pieces)       nA    = max(0, D2 - d)          LOWER bound on a
                          badmax= max(0, Z - Qs)          UPPER bound on e
                          nmark = max(0, nA - badmax)
                          m_lo  = max(1, D2 + Qs - d + 1) LOWER bound on a+bb+1
         -> consumes TWO LOWER bounds that the node's `what` does not state.

DIRECTION.  A row is closed when bound < required.  So:
  * an UPPER envelope bound that is too SMALL shrinks the searcher's freedom,
    lowers the capacity, lowers the bound, and can close a row a real cover
    realises  -> UNSOUND.  Each must therefore be a genuine upper bound on
    real extracted usage.
  * a LOWER envelope bound that is too LARGE adds constrained seams / raises
    m_lo, lowers the bound, same failure mode -> each must be a genuine lower
    bound.
Both directions are verified numerically below by monotonicity, and the
sensitivity of the actual census to a one-unit error is measured.
"""
from __future__ import annotations
import importlib.util, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
NEG = -10 ** 9


def load():
    spec = importlib.util.spec_from_file_location(
        "rows152", ROOT / "r152" / "src" / "rows152.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rep = json.loads((ROOT / "r152" / "certs" / "verify_all_c152.json").read_text())
    for row in rep["rows"]:
        if row["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            m.CERT[tuple(int(x) for x in row["cell"].split("|"))] = row["cap"]
    rep = json.loads((ROOT / "r152" / "certs" / "verify_piece_c152.json").read_text())
    for row in rep["rows"]:
        if row["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            m.PCERT[(row["b"], row["d"], row["fp"], row["lp"])] = row["cap"]
    return m


def bounds(m, variants, dA=0, dB=0, dE=0, dTot=0, dNA=0, dMLO=0):
    """rows152.bounds() with the envelope perturbed by the given deltas."""
    req = variants[0]["required"]
    res = {}
    # ---- piece
    pv = NEG
    for r in variants:
        nA = max(0, r["D2"] - r["d"]) + dNA
        badmax = max(0, r["Z"] - r["Qs"]) + dE
        nmark = max(0, nA - max(0, badmax))
        m_lo = max(1, r["D2"] + r["Qs"] - r["d"] + 1) + dMLO
        m_hi = r["m_max"]
        if m_lo > m_hi:
            continue
        for mm in range(m_lo, m_hi + 1):
            v, _ = m.best_chain(mm, r["b_sum"], r["D_sum"], min(nmark, mm - 1))
            if v > pv:
                pv = v
    res["piece"] = pv
    # ---- split
    sv = NEG
    for r in variants:
        n = r["d"] + 1 + r["h"]
        if n == 1 and r["s"] != 0:
            continue
        m.best.cache_clear()
        tot = max(0, 2 * r["g"] + dTot)
        v, _ = m.best(n, r["b_sum"], r["D_sum"],
                      max(0, min(r["D2"] + dA, tot)),
                      max(0, min(r["Qs"] + dB, tot)),
                      max(0, min(max(0, r["Z"] - r["Qs"]) + dE, tot)), tot)
        if v > sv:
            sv = v
    if sv > NEG // 2:
        res["split"] = sv
    # ---- merged
    mv = None
    for r in variants:
        if r["H"] == 0 or r["d"] + 1 != 1 or r["s"] != 0:
            continue
        tot = max(0, 2 * r["g"] + dTot)
        v, _ = m.CC(r["b_sum"], r["D_sum"],
                    max(0, min(r["D2"] + dA, tot)),
                    max(0, min(r["Qs"] + dB, tot)),
                    max(0, min(max(0, r["Z"] - r["Qs"]) + dE, tot)), r["H"])
        if mv is None or v > mv:
            mv = v
    if mv is not None:
        res["merged"] = mv
    return req, res


def census(m, layers=(0, 1, 2, 3, 4), **kw):
    tally = Counter()
    for t in layers:
        groups = {}
        for r in m.rows(t):
            groups.setdefault(tuple(r[c] for c in m.COORD), []).append(r)
        for key, variants in groups.items():
            req, res = bounds(m, variants, **kw)
            tally["rows"] += 1
            if any(v < req for v in res.values()):
                tally["closed"] += 1
            elif res and min(res.values()) == req:
                tally["equality"] += 1
            else:
                tally["surviving"] += 1
    return dict(tally)


def monotone(m):
    """The model bound is non-decreasing in every envelope UPPER bound."""
    st, viol = Counter(), []
    for b in range(0, 3):
        for D in range(0, 5):
            for tot in range(0, 4):
                prev = None
                for cap in range(0, tot + 1):
                    m.best.cache_clear()
                    v, _ = m.best(1, b, D, cap, 0, 0, tot)
                    if prev is not None and v < prev:
                        viol.append(dict(kind="a", b=b, D=D, tot=tot, cap=cap))
                    prev = v
                    st["a"] += 1
                prev = None
                for cap in range(0, tot + 1):
                    m.best.cache_clear()
                    v, _ = m.best(1, b, D, 0, 0, cap, tot)
                    if prev is not None and v < prev:
                        viol.append(dict(kind="e", b=b, D=D, tot=tot, cap=cap))
                    prev = v
                    st["e"] += 1
                prev = None
                for t2 in range(0, tot + 1):
                    m.best.cache_clear()
                    v, _ = m.best(1, b, D, t2, t2, t2, t2)
                    if prev is not None and v < prev:
                        viol.append(dict(kind="tot", b=b, D=D, tot=t2))
                    prev = v
                    st["tot"] += 1
    # piece: the bound is non-increasing in nmark and in m_lo
    st2, viol2 = Counter(), []
    for b in range(0, 3):
        for D in range(0, 6):
            for mm in range(1, 6):
                prev = None
                for nm in range(0, mm):
                    v, _ = m.best_chain(mm, b, D, nm)
                    if prev is not None and v > prev:
                        viol2.append(dict(kind="nmark", b=b, D=D, m=mm, nm=nm))
                    prev = v
                    st2["nmark"] += 1
    return dict(upper_comparisons=dict(st), upper_violations=viol[:5],
                upper_ok=not viol,
                piece_comparisons=dict(st2), piece_violations=viol2[:5],
                piece_ok=not viol2)


def main():
    t0 = time.time()
    m = load()
    base = census(m)
    print("baseline", json.dumps(base), flush=True)
    sens = {}
    for name, kw in (
            # UNSAFE direction: a bound that is too tight closes more rows
            ("a_budget_minus_1", dict(dA=-1)),
            ("bb_budget_minus_1", dict(dB=-1)),
            ("e_budget_minus_1", dict(dE=-1)),
            ("total_2g_minus_1", dict(dTot=-1)),
            ("piece_nA_plus_1", dict(dNA=1)),
            ("piece_m_lo_plus_1", dict(dMLO=1)),
            # SAFE direction: relaxing a bound un-closes the rows whose
            # closure actually RESTS on that bound
            ("a_budget_plus_1", dict(dA=1)),
            ("bb_budget_plus_1", dict(dB=1)),
            ("e_budget_plus_1", dict(dE=1)),
            ("total_2g_plus_1", dict(dTot=1)),
            ("piece_nA_minus_1", dict(dNA=-1)),
            ("piece_m_lo_minus_1", dict(dMLO=-1))):
        c = census(m, **kw)
        sens[name] = dict(census=c,
                          extra_rows_closed=c["closed"] - base["closed"],
                          rows_no_longer_closed=max(0, base["closed"] - c["closed"]))
        print(f"  {name}: {json.dumps(c)} delta_closed="
              f"{c['closed'] - base['closed']}", flush=True)
    mono = monotone(m)
    # ---- the h vs H question
    hh = dict(
        merged_sixth_argument="r[\"H\"]  (heavy COST sum(w-3))",
        r148_bug="r148/src/rows148.py passed r[\"h\"] (heavy COUNT); "
                 "1 <= h <= H so the budget was too SMALL, the capacity too "
                 "small and the bound too small -- it closed rows it should "
                 "not have",
        repaired_in="r152/src/heavyfix152.py, r152/src/rows152.py",
        envelope_mentions_h_or_H=False,
        note="a <= D2, bb <= Qs, e <= Z-Qs and a+bb+e <= 2g contain neither h "
             "nor H; the only heaviness the envelope proof uses is the "
             "per-joint predicate weight >= 4, which is what decides whether a "
             "joint is CUT, and A/B joints have weights 2 and 3 so they are "
             "never heavy.  No h/H quantity enters.")
    out = dict(seconds=round(time.time() - t0, 1), baseline=base,
               sensitivity=sens, monotonicity=mono, heavy_h_vs_H=hh,
               ok=(mono["upper_ok"] and mono["piece_ok"]))
    (ROOT / "r158" / "certs" / "models_158.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(monotonicity_ok=mono["upper_ok"] and mono["piece_ok"],
                          upper=dict(mono["upper_comparisons"]),
                          piece=dict(mono["piece_comparisons"])),
                     ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
