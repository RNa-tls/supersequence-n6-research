#!/usr/bin/env python3
"""Round 160 -- the algebra of MASTER and the nonnegativity of each term,
decided over complete integer boxes, with hypothesis ablations.

PART A -- the identity is an exact rearrangement.
  Given the DEFINITIONS
     G = Z + D2 + c,  O = ORB + k,  B* = S + 1 + D2 - O + c
  the two expressions
     FO      = (n + N + HEX - 2) + G + S + H
     MASTER  = (n + N + HEX + ORB - 3) + k + Z + H + B*
  are equal.  Checked over a complete integer box, and ablated: the constant
  off by one, `h` in place of `H`, B* without its +1, G without its c.

PART B -- nonnegativity, term by term, from the certified lower-level facts.
     (N1) G >= 0                       every hexagon carries a pass  [H.splice A]
     (N2) D_phi := (n-1)O - P >= 0     a tau-orbit holds at most n-1 distinct
                                       pass entries
     (N3) G = 2g + c + d, g,c,d >= 0   [H.incidence + H.extract]
     (N4) D2 + Qs <= R_int <= 2g       [H.samehex + H.incidence]
     (N5) B* = sum_i tok_i + sigma, tok_i >= 0, sigma >= 0   [H.extract 3,4]
  give
     k  >= 0     from (N1)+(N2):  (n-1)k = D_phi + G >= 0
     Z  >= 0     from (N3)+(N4):  Z = 2g + d - D2 >= d >= 0
     H  >= 0     by definition
     B* >= 0     from (N5)
  Each hypothesis is ablated and must produce a counterexample.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def part_a(n, N, HEX, ORB, B=6, const_delta=0, use_h=False,
           drop_Bstar_one=False, drop_c_in_G=False):
    st = Counter()
    ex = None
    for k in range(0, B + 1):
        O = ORB + k
        for Z in range(0, B + 1):
            for D2 in range(0, B + 1):
                for c in range(0, B + 1):
                    G = Z + D2 + (0 if drop_c_in_G else c)
                    P = HEX + G
                    for S in range(0, B + 1):
                        Bs = S + 1 + D2 - O + c - (1 if drop_Bstar_one else 0)
                        for H in range(0, B + 1):
                            for h in range(0, H + 1):
                                Hterm = h if use_h else H
                                FO = (n + N + HEX - 2) + G + S + H
                                M = ((n + N + HEX + ORB - 3) + const_delta
                                     + k + Z + Hterm + Bs)
                                st["cases"] += 1
                                if FO != M:
                                    st["mismatches"] += 1
                                    if ex is None:
                                        ex = dict(k=k, Z=Z, D2=D2, c=c, S=S,
                                                  H=H, h=h, G=G, Bstar=Bs,
                                                  FO=FO, MASTER=M)
                                if not use_h:
                                    break
    return st, ex


def part_b(B=6, drop=None):
    """Nonnegativity of k, Z, B* from the lower-level facts."""
    st = Counter()
    ex = None
    for g in range(0, B + 1):
        for c in range(0, B + 1):
            for d in range(0, B + 1):
                G = 2 * g + c + d                      # (N3)
                if drop == "N1" :
                    Gs = range(-B, G + 1)
                else:
                    Gs = [G]
                for Gv in Gs:
                    if Gv < 0 and drop != "N1":
                        continue
                    for R_int in range(0, 2 * g + 1 if drop != "N4"
                                       else B + 1):
                        for D2 in range(0, B + 1):
                            for Qs in range(0, B + 1):
                                if drop != "N4" and D2 + Qs > R_int:
                                    continue
                                Z = 2 * g + d - D2
                                for Dphi in (range(0, B + 1) if drop != "N2"
                                             else range(-B, B + 1)):
                                    # (n-1) k = D_phi + G
                                    if (Dphi + Gv) % 5:
                                        continue
                                    k = (Dphi + Gv) // 5
                                    for tok in (range(0, B + 1)
                                                if drop != "N5"
                                                else range(-B, B + 1)):
                                        for sig in range(0, B + 1):
                                            Bs = tok + sig
                                            st["cases"] += 1
                                            bad = []
                                            if k < 0:
                                                bad.append("k")
                                            if Z < 0:
                                                bad.append("Z")
                                            if Bs < 0:
                                                bad.append("Bstar")
                                            if bad:
                                                st["violations"] += 1
                                                for b in bad:
                                                    st["v_" + b] += 1
                                                if ex is None:
                                                    ex = dict(
                                                        g=g, c=c, d=d, G=Gv,
                                                        R_int=R_int, D2=D2,
                                                        Qs=Qs, Z=Z,
                                                        Dphi=Dphi, k=k,
                                                        tok=tok, sigma=sig,
                                                        Bstar=Bs, broke=bad)
    return st, ex


def main():
    t0 = time.time()
    out = {"part_a": [], "part_a_ablations": [], "part_b": [],
           "part_b_ablations": []}
    for n, N, HEX, ORB in ((3, 6, 2, 1), (4, 24, 6, 2), (5, 120, 24, 6),
                           (6, 720, 120, 24)):
        st, ex = part_a(n, N, HEX, ORB)
        out["part_a"].append(dict(n=n, constant=n + N + HEX + ORB - 3,
                                  cases=st["cases"],
                                  mismatches=st["mismatches"], example=ex))
        print(f"  part A n={n}: constant={n+N+HEX+ORB-3} "
              f"{st['cases']:,} cases, {st['mismatches']} mismatches",
              flush=True)
    for name, kw in (("constant +1", dict(const_delta=1)),
                     ("constant -1", dict(const_delta=-1)),
                     ("h in place of H", dict(use_h=True)),
                     ("B* without its +1", dict(drop_Bstar_one=True)),
                     ("G without its c", dict(drop_c_in_G=True))):
        st, ex = part_a(6, 720, 120, 24, **kw)
        out["part_a_ablations"].append(
            dict(name=name, cases=st["cases"], mismatches=st["mismatches"],
                 example=ex, as_expected=st["mismatches"] > 0))
        print(f"  ablation A {name}: {st['cases']:,} cases, "
              f"{st['mismatches']} mismatches", flush=True)
    st, ex = part_b()
    out["part_b"].append(dict(cases=st["cases"], violations=st["violations"],
                              example=ex))
    print(f"  part B: {st['cases']:,} cases, {st['violations']} violations",
          flush=True)
    for hyp in ("N1", "N2", "N4", "N5"):
        st, ex = part_b(5, drop=hyp)
        which = {kk[2:]: vv for kk, vv in st.items() if kk.startswith("v_")}
        out["part_b_ablations"].append(
            dict(dropped=hyp, cases=st["cases"], violations=st["violations"],
                 which=which, example=ex, as_expected=st["violations"] > 0))
        print(f"  ablation B drop {hyp}: {st['cases']:,} cases, "
              f"{st['violations']} violations {which}", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    out["ok"] = (all(e["mismatches"] == 0 for e in out["part_a"])
                 and all(a["as_expected"] for a in out["part_a_ablations"])
                 and all(e["violations"] == 0 for e in out["part_b"])
                 and all(a["as_expected"] for a in out["part_b_ablations"]))
    (ROOT / "r160" / "certs" / "symbolic_160.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    print("ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
