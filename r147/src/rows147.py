#!/usr/bin/env python3
"""Round 147 Phase 7 -- regenerate every coordinate row FROM THE DEFINITIONS.

No closure label and no cached row ledger is read.  The rows are re-derived
from the statement of MASTER-142 and the bookkeeping inequalities as written in
research/RR_L6_PROOF_145_CLAUDE.md section 8, with a deliberately different
loop structure from src/l6_coupled_144.py::rows_for (that one drives G, g, c and
computes d; this one enumerates the component decomposition (g, c, d) first and
derives G), and the two are then compared as SETS.

The constraints, each with the fact it comes from:

  t = k + Z + H + B*                 MASTER-142: L = 867 + k + Z + H + B*
  0 <= G <= 5k                       G = P - 120 extra passes, each unit of k
                                     buys at most five
  G = 2g + c + d                     G+1 = K + 2g with K = c + 1 + d: the
                                     incidence bound K + R_int <= G + 1 at
                                     R_int = 2g, c pure circuits and d+1
                                     nonpure components
  z = G - c = 2g + d                 the non-pure part of the pass excess
  D2 = z - Z >= 0                    Z = z - D2, Z >= 0
  0 <= Qs <= Z                       Qs counts same-hex B joints, a subset of Z
  D2 + Qs <= 2g                      SAME-HEX: D2 + Qs <= R_int <= 2g
  h = 0 if H = 0 else 1 <= h <= H    H = sum (w-3)+ >= 1 forces >= 1 heavy
                                     joint and each heavy joint costs >= 1
  0 <= s <= B*                       the extraction parameter
  D_sum = 5k - G + 5s >= 0           sum over chains of deficit
  b_sum = B* - s                     sum over chains of tokens
  required = 120 + G - 5c            sum_i P_i, the ports the row must carry
  m_max = z + 1 + h                  piece count bound

The optional sigma-deficit inequality is NOT used (`use_sigma_deficit=False` in
round 144 too): it would only remove rows, and leaving it out is the generous
direction.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COORD = ("k", "Z", "H", "Bstar", "G", "g", "c", "d", "D2", "Qs", "h")


def rows(t):
    """Every admissible row for L = 867 + t, derived from the definitions."""
    out = []
    for k in range(t + 1):
        for Z in range(t - k + 1):
            for H in range(t - k - Z + 1):
                Bs = t - k - Z - H
                hs = [0] if H == 0 else list(range(1, H + 1))
                # component decomposition first: g shared-repeat pairs,
                # c pure circuits, d+1 nonpure components
                for g in range(0, 5 * k // 2 + 1):
                    for c in range(0, 5 * k + 1):
                        for d in range(0, 5 * k + 1):
                            G = 2 * g + c + d
                            if G > 5 * k:
                                break
                            z = G - c            # = 2g + d
                            D2 = z - Z
                            if D2 < 0:
                                continue
                            if D2 > 2 * g:       # D2 + Qs <= 2g with Qs >= 0
                                continue
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


def as_set(rs):
    return {tuple(r[c] for c in COORD) + (r["s"],) for r in rs}


def compare(t):
    """Compare with src/l6_coupled_144.py::rows_for(t, False) as SETS."""
    sys.path.insert(0, str(ROOT / "src"))
    import l6_coupled_144 as PIECE
    mine, theirs = rows(t), PIECE.rows_for(t, False)
    A, B = as_set(mine), as_set(theirs)
    # derived fields must agree too
    dmine = {tuple(r[c] for c in COORD) + (r["s"],):
             (r["required"], r["D_sum"], r["b_sum"], r["m_max"]) for r in mine}
    dth = {tuple(r[c] for c in COORD) + (r["s"],):
           (r["required"], r["D_sum"], r["b_sum"], r["m_max"]) for r in theirs}
    bad = [k for k in A & B if dmine[k] != dth[k]]
    groups = {tuple(r[c] for c in COORD) for r in mine}
    return dict(t=t, L=867 + t, rows_with_s=len(A), rows_144=len(B),
                coordinate_groups=len(groups),
                only_mine=len(A - B), only_144=len(B - A),
                derived_field_mismatches=len(bad),
                examples_only_mine=sorted(A - B)[:3],
                examples_only_144=sorted(B - A)[:3],
                agree=(A == B and not bad))


def main(argv):
    ts = [int(x) for x in (argv or ["0", "1", "2", "3", "4"])]
    out = {"note": "rows regenerated from the definitions; no closure label read",
           "layers": {}}
    ok = True
    for t in ts:
        r = compare(t)
        out["layers"][f"L{867 + t}"] = r
        ok &= r["agree"]
        print(json.dumps(r), flush=True)
    out["all_agree"] = ok
    (ROOT / "r147" / "rows" / "rows_regenerated_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
