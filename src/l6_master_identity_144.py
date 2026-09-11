#!/usr/bin/env python3
"""L6 endgame — MASTER-142 identity, verified symbolically and numerically.

Recovered definitions (Round 142 Route B, FIRST-OCCURRENCE / "selected" level):

  Retain the first occurrence of every permutation; trim.  Selected passes are
  maximal consecutive weight-1 runs among retained occurrences.
    P = 120 + G        selected passes
    O = 24 + k         distinct E-orbits of selected pass ENTRIES
    D_phi = 5O - P = 5k - G >= 0
    S = #{joints of weight >= 3},   H = sum max(w-3,0)
    L = 844 + G + S + H                                            (FO)

  Dirty taxonomy of a selected joint, spliced target from entry v = sigma(p):
    tail 10  w2 -> E(v)          clean tau            0 hidden
    tail 01  w2 -> sigma(v)      type A dirty sigma   1 hidden
    tail 012 w3 -> sigma^2(v)    type B dirty sigma^2 2 hidden
    tail 021 w3 -> E(sigma(v))   type C mixed E-sigma 1 hidden
    tail 102 w3 -> sigma(E(v))   type D mixed sigma-E 1 hidden
    tails 120/201/210 w3         clean paid           0 hidden

  Splice bookkeeping: alpha = nu + fixed dummy, T chronological, beta = T alpha^-1
    K + R_int <= G + 1,  K = G+1 (mod 2),  g = (G+1-K)/2,  R_int <= 2g
    D2 = #type A,  Qs = #type B,   D2 + Qs <= R_int <= 2g          (SAME-HEX)
    c  = # circuits of clean E edges only
    d  = K - 1 - c >= 0,   z = G - c = 2g + d,   Z = z - D2,   Z >= Qs >= 0
    B* = sum b_j + s = S + 1 + D2 - O + c >= 0
    sum P_j = 120 + G - 5c,   sum D_j = 5k - G + 5s

Then MASTER-142:  L = 867 + k + Z + H + B*.

This module proves that identity is an exact rearrangement of (FO), so it
carries no extra hypothesis beyond the definitions of B* and Z.
"""
from __future__ import annotations
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def symbolic_check():
    """L = 844+G+S+H  and the definitions of Z, B*  ==>  L = 867+k+Z+H+B*."""
    # G = Z + D2 + c   (since Z = z - D2 and z = G - c)
    # S = B* - D2 - c + 23 + k   (since B* = S + 1 + D2 - (24+k) + c)
    # => 844 + G + S + H = 844 + (Z+D2+c) + (B*-D2-c+23+k) + H = 867+k+Z+H+B*
    bad = []
    for k, Z, H, Bs, D2, c in product(range(5), range(5), range(5),
                                      range(5), range(5), range(5)):
        G = Z + D2 + c
        O = 24 + k
        S = Bs + O - 1 - D2 - c
        L_fo = 844 + G + S + H
        L_master = 867 + k + Z + H + Bs
        if L_fo != L_master:
            bad.append((k, Z, H, Bs, D2, c, L_fo, L_master))
    return dict(combinations=5 ** 6, mismatches=len(bad), examples=bad[:3],
                identity_holds=(len(bad) == 0),
                derivation=["G = Z + D2 + c",
                            "S = B* + O - 1 - D2 - c,  O = 24 + k",
                            "844 + G + S + H = 867 + k + Z + H + B*"])


def fo_identity_from_word_level():
    """(FO) itself: L = 844 + G + S + H, from counting alone."""
    # L = 6 + (720 - P) + sum_joints w ;  joints = P-1 ; sum w = 2(P-1) + S + H
    bad = []
    for G in range(0, 25):
        for S in range(0, 40):
            for H in range(0, 6):
                P = 120 + G
                L = 6 + (720 - P) + (2 * (P - 1) + S + H)
                if L != 844 + G + S + H:
                    bad.append((G, S, H))
    return dict(mismatches=len(bad), holds=(len(bad) == 0),
                statement="L = 6 + (720-P) + sum_joints w, P = 120+G, "
                          "sum_joints w = 2(P-1) + S + H")


def budgets(Lmax=871):
    """Exact resource budgets t = L - 867 = k + Z + H + B*."""
    out = {}
    for L in (867, 868, 869, 870, 871, 872):
        t = L - 867
        rows = []
        for k in range(0, t + 1):
            for Z in range(0, t - k + 1):
                for H in range(0, t - k - Z + 1):
                    Bs = t - k - Z - H
                    rows.append(dict(k=k, Z=Z, H=H, B=Bs))
        out[str(L)] = dict(t=t, n_rows=len(rows), rows=rows)
    return out


if __name__ == "__main__":
    res = dict(symbolic=symbolic_check(),
               fo=fo_identity_from_word_level(),
               budgets=budgets())
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_l6_master_identity_144.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: (v if k != "budgets" else
                          {kk: {"t": vv["t"], "n_rows": vv["n_rows"]}
                           for kk, vv in v.items()})
                      for k, v in res.items()}, ensure_ascii=False, indent=1))
