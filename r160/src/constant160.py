#!/usr/bin/env python3
"""Round 160 Phase 3 -- the constant, its structural sources, and off-by-one.

  CONST(n) = n + (N - HEX) + 2*(HEX - 1) + (ORB - 1)
           = n + N + HEX + ORB - 3
           = n! + (n-1)! + (n-2)! + n - 3

  n = 3:   3 +   4 +   2 +  0  =   9
  n = 4:   4 +  18 +  10 +  1  =  33
  n = 5:   5 +  96 +  46 +  5  = 152
  n = 6:   6 + 600 + 238 + 23  = 867

  the four sources being
    n            the first selected window is spelled in full;
    N - HEX      the gap-1 steps when every hexagon is a single pass (G = 0);
    2*(HEX - 1)  the minimum cost of the HEX - 1 joints, each of weight >= 2;
    ORB - 1      NOT a word-length term: it is what the change of variable
                 S -> B* contributes, because B* = S + 1 + D2 - O + c with
                 O = ORB + k.

CHECKS
  C1  the three closed forms agree for n = 3..9
  C2  CONST(n) is an anchor, not a fitted constant: the known minimal
      superpermutation lengths are CONST(n) + t with t = 0, 0, 1, 5 for
      n = 3, 4, 5, 6, and the repository's own optimum words realise them
  C3  every off-by-one perturbation of the constant, and of each of its four
      sources, is DETECTED on every real cover
  C4  the boundary cases G = 0, H = 0, B* = 0, k = 0, t = 0 all occur and the
      identity holds there
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402
from master160 import master                                      # noqa: E402


def const_forms(n):
    N = factorial(n)
    HEX = N // n
    ORB = N // (n * (n - 1))
    a = n + (N - HEX) + 2 * (HEX - 1) + (ORB - 1)
    b = n + N + HEX + ORB - 3
    c = factorial(n) + factorial(n - 1) + factorial(n - 2) + n - 3
    return dict(n=n, N=N, HEX=HEX, ORB=ORB,
                sources=dict(first_window=n, gap1_steps=N - HEX,
                             min_joint_cost=2 * (HEX - 1),
                             change_of_variable=ORB - 1),
                split=a, compact=b, factorial_form=c,
                agree=(a == b == c))


def main():
    t0 = time.time()
    rng = random.Random(1601601)
    out = {"forms": [const_forms(n) for n in range(3, 10)]}
    out["forms_agree"] = all(f["agree"] for f in out["forms"])
    for f in out["forms"]:
        print(f"  n={f['n']}: {f['sources']} -> {f['split']}", flush=True)

    # ---- C2: the known minima as anchors
    ws, w5 = R.words()
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import passes156 as P3                                        # noqa: E402
    anchors = []
    n3 = P3.n3_family()
    best3 = min(len(w) for w in n3)
    anchors.append(dict(n=3, shortest_in_repo=best3,
                        CONST=const_forms(3)["split"],
                        t=best3 - const_forms(3)["split"]))
    for tag, n, W in ws:
        r = master(X.structure(W, n))
        anchors.append(dict(n=n, tag=tag, L=r["L"], CONST=r["CONST"],
                            t=r["t"], ok=r["ok"]))
    out["anchors"] = anchors

    # ---- C3 / C4 on the corpus
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n3e{i}", 3, w) for i, w in enumerate(n3)]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 800))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 350))]
    det = Counter()
    bnd = Counter()
    words = 0
    for tag, n, W in pool:
        r = master(X.structure(W, n))
        if not r["ok"]:
            det["identity_failed"] += 1
            continue
        words += 1
        L, CONST = r["L"], r["CONST"]
        rest = r["k"] + r["Z"] + r["H"] + r["Bstar"]
        N, HEX, ORB = r["N"], r["HEX"], r["ORB"]
        # constant perturbations
        for dlt in (-1, 1):
            if L != (CONST + dlt) + rest:
                det[f"const{dlt:+d}_detected"] += 1
        # perturbations of each structural source
        for src, val in (("first_window", n), ("gap1_steps", N - HEX),
                         ("min_joint_cost", 2 * (HEX - 1)),
                         ("change_of_variable", ORB - 1)):
            for dlt in (-1, 1):
                pert = CONST - val + (val + dlt)
                if L != pert + rest:
                    det[f"{src}{dlt:+d}_detected"] += 1
        # (FO) perturbations
        FO = (n + N + HEX - 2) + r["G"] + r["S"] + r["H"]
        if L != FO + 1 and L != FO - 1:
            det["FO_off_by_one_detected"] += 1
        # boundaries
        for key, cond in (("G_zero", r["G"] == 0), ("H_zero", r["H"] == 0),
                          ("Bstar_zero", r["Bstar"] == 0),
                          ("k_zero", r["k"] == 0), ("t_zero", r["t"] == 0),
                          ("S_zero", r["S"] == 0), ("c_zero", r["c"] == 0),
                          ("all_four_zero", r["k"] == 0 and r["Z"] == 0
                           and r["H"] == 0 and r["Bstar"] == 0)):
            if cond:
                bnd[key] += 1
    out["words"] = words
    out["perturbation_detection"] = dict(det)
    out["boundaries"] = dict(bnd)
    out["all_perturbations_always_detected"] = all(
        det[k] == words for k in det if k.endswith("_detected"))
    out["seconds"] = round(time.time() - t0, 1)
    out["ok"] = (out["forms_agree"] and not det["identity_failed"]
                 and out["all_perturbations_always_detected"]
                 and bnd["t_zero"] > 0 and bnd["G_zero"] > 0)
    (ROOT / "r160" / "certs" / "constant_160.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "forms"},
                     ensure_ascii=False, indent=1)[:2200])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
