#!/usr/bin/env python3
"""Round 160 -- the MASTER identity recomputed from the raw word.

Nothing is imported from src/l6_master_identity_144.py, src/l6_bookkeeping_144.py
or any other module that states the identity.  The pass / nu / beta / catalogue
layer comes from the round-156 independent reconstruction (r156/src/extract156.py,
which imports nothing from src/); every quantity in the identity is then
recomputed here from its definition.

THE CHAIN, general n (N = n!, HEX = N/n, ORB = N/(n(n-1))):

  W1  L = n + sum_j g_j                       (trimmed fixed representative)
  W2  #gaps = N - 1 = (N - P) gap-1 steps + (P - 1) joints
  W3  sum_joints w = 2(P - 1) + S + H         (S = #{w >= 3}, H = sum (w-3)_+)
  FO  L = (n + N + HEX - 2) + G + S + H       (P = HEX + G)
  B*  B* := blocks - (O - c) = S + 1 + D2 - O + c,  blocks = P - cleanE
  Z   Z := z - D2,  z := G - c                so  G = Z + D2 + c
  O   O = ORB + k
  M   L = (n + N + HEX + ORB - 3) + k + Z + H + B*
      (n = 6:  6 + 720 + 120 + 24 - 3 = 867)

Everything above is checked literally on every word, together with the
nonnegativity of each term and the h-versus-H distinction.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402


def master(st):
    n, P, beta, dummy = st["n"], st["P"], st["beta"], st["dummy"]
    etype, eweight = st["etype"], st["eweight"]
    hexr, orbr, sel, gaps, W = (st["hexr"], st["orbr"], st["sel"],
                                st["gaps"], st["W"])
    N = factorial(n)
    HEX = N // n
    ORB = N // (n * (n - 1))
    fails = []

    # ---- W1 : the word length from the trimmed selected sequence
    if sel[0][0] != 0:
        fails.append(("W1 not trimmed at the left", sel[0][0]))
    if sel[-1][0] + n != len(W):
        fails.append(("W1 not trimmed at the right", sel[-1][0] + n, len(W)))
    L = len(W)
    if L != n + sum(gaps):
        fails.append(("W1 L != n + sum gaps", L, n + sum(gaps)))

    # ---- W2 : the gap census
    if len(gaps) != N - 1:
        fails.append(("W2 gap count", len(gaps), N - 1))
    n_one = sum(1 for g in gaps if g == 1)
    n_joint = sum(1 for g in gaps if g != 1)
    if n_one != N - P:
        fails.append(("W2 gap-1 count", n_one, N - P))
    if n_joint != P - 1:
        fails.append(("W2 joint count", n_joint, P - 1))
    if n_one + n_joint != N - 1:
        fails.append("W2 gaps do not add up")

    # ---- W3 : the joint cost
    S = sum(1 for w in eweight.values() if w >= 3)
    Hh = sum(max(w - 3, 0) for w in eweight.values())
    h = sum(1 for w in eweight.values() if w >= 4)
    sumw = sum(eweight.values())
    if len(eweight) != P - 1:
        fails.append(("W3 eweight size", len(eweight), P - 1))
    if sumw != sum(g for g in gaps if g != 1):
        fails.append(("W3 spliced weights != raw joint gaps", sumw))
    if sumw != 2 * (P - 1) + S + Hh:
        fails.append(("W3 sum w != 2(P-1)+S+H", sumw, 2 * (P - 1) + S + Hh))

    # ---- FO
    G = P - HEX
    FO = (n + N + HEX - 2) + G + S + Hh
    if L != FO:
        fails.append(("FO", L, FO))

    # ---- the structural quantities
    comps = X.components(beta)
    K = len(comps)
    pure = [cy for cy in comps if dummy not in cy
            and all(etype.get(q) == "E" for q in cy)]
    c = len(pure)
    d = K - 1 - c
    two_g = G + 1 - K
    g = two_g // 2 if two_g % 2 == 0 else None
    D2 = sum(1 for t in etype.values() if t == "A")
    Qs = sum(1 for t in etype.values() if t == "B")
    cleanE = sum(1 for t in etype.values() if t == "E")
    O = len(set(orbr))
    k = O - ORB
    blocks = P - cleanE
    Bstar = blocks - (O - c)
    z = G - c
    Z = z - D2
    if blocks != S + 1 + D2:
        fails.append(("blocks != S+1+D2", blocks, S + 1 + D2))
    if Bstar != S + 1 + D2 - O + c:
        fails.append(("B* closed form", Bstar, S + 1 + D2 - O + c))
    if G != Z + D2 + c:
        fails.append(("G != Z+D2+c", G, Z, D2, c))
    if O != ORB + k:
        fails.append(("O != ORB+k", O, ORB, k))

    # ---- MASTER
    CONST = n + N + HEX + ORB - 3
    M = CONST + k + Z + Hh + Bstar
    if L != M:
        fails.append(("MASTER", L, M, CONST))
    # the same constant, split structurally
    CONST2 = n + (N - HEX) + 2 * (HEX - 1) + (ORB - 1)
    if CONST2 != CONST:
        fails.append(("constant split", CONST2, CONST))

    # ---- nonnegativity, term by term
    for name, v in (("k", k), ("Z", Z), ("H", Hh), ("B*", Bstar),
                    ("G", G), ("S", S), ("c", c), ("d", d), ("z", z),
                    ("D2", D2), ("Qs", Qs)):
        if v < 0:
            fails.append((f"negative {name}", v))
    if g is None or g < 0:
        fails.append(("g not a nonnegative integer", two_g))

    # ---- h versus H
    h_would_break = (Hh != h) and (L != CONST + k + Z + h + Bstar)
    return dict(n=n, L=L, N=N, HEX=HEX, ORB=ORB, P=P, G=G, S=S, H=Hh, h=h,
                O=O, k=k, K=K, c=c, d=d, g=g, two_g=two_g, z=z, Z=Z,
                D2=D2, Qs=Qs, cleanE=cleanE, blocks=blocks, Bstar=Bstar,
                CONST=CONST, sum_gaps=sum(gaps), sum_w=sumw,
                t=k + Z + Hh + Bstar, h_ne_H=(h != Hh),
                h_substitution_breaks=h_would_break,
                failures=fails, ok=not fails)


def main():
    t0 = time.time()
    rng = random.Random(160160)
    ws, w5 = R.words()
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import passes156 as P3                                        # noqa: E402
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n3e{i}", 3, w) for i, w in enumerate(P3.n3_family())]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 1200))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 500))]
    st_, bad, named = Counter(), [], {}
    maxdiff = 0
    for tag, n, W in pool:
        stt = X.structure(W, n)
        r = master(stt)
        st_["words"] += 1
        st_[f"n{n}"] += 1
        st_[f"n{n}_const_{r['CONST']}"] += 1
        if not r["ok"]:
            st_["failures"] += 1
            if len(bad) < 8:
                bad.append(dict(tag=tag, n=n, failures=r["failures"][:5]))
        maxdiff = max(maxdiff, abs(r["L"] - (r["CONST"] + r["k"] + r["Z"]
                                             + r["H"] + r["Bstar"])))
        for key, cond in (("H_pos", r["H"] > 0), ("h_ne_H", r["h_ne_H"]),
                          ("h_substitution_breaks", r["h_substitution_breaks"]),
                          ("k_pos", r["k"] > 0), ("Z_pos", r["Z"] > 0),
                          ("Bstar_pos", r["Bstar"] > 0), ("c_pos", r["c"] > 0),
                          ("G_zero", r["G"] == 0), ("D2_pos", r["D2"] > 0)):
            if cond:
                st_[key] += 1
        if tag in ("n4_optimum", "n6_witness_872"):
            named[tag] = {kk: vv for kk, vv in r.items() if kk != "failures"}
    out = dict(seconds=round(time.time() - t0, 1), stats=dict(st_),
               max_abs_difference=maxdiff, named=named, failures=bad,
               ok=(st_["failures"] == 0 and maxdiff == 0))
    (ROOT / "r160" / "certs" / "real_160.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({kk: vv for kk, vv in out.items() if kk != "named"},
                     ensure_ascii=False, indent=1)[:2000])
    for kk, vv in named.items():
        print(kk, json.dumps({q: vv[q] for q in
                              ("n", "L", "P", "G", "S", "H", "h", "O", "k",
                               "c", "Z", "Bstar", "CONST", "t", "ok")}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
