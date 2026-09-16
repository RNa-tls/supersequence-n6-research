#!/usr/bin/env python3
"""Round 158 -- the ENVELOPE, measured independently on real covers.

The pass / nu / alpha / T / beta / catalogue layer comes from the round-156
independent reconstruction (r156/src/extract156.py), which imports nothing
from src/.  The CUT and the envelope quantities are re-implemented here from
the definitions, so this file does not inherit r156's measurement either; the
two are compared afterwards.

QUANTITIES (all defined on the CHAINS produced by the cut)

  D2   # type A joints in the whole word        (target = sigma(v_source))
  Qs   # type B joints in the whole word        (target = sigma^2(v_source))
  x    # type A joints spent as a cycle OPENING
  y    # type B joints spent as a cycle opening
  a    # retained (= chain-internal) type A joints
  bb   # retained type B joints
  rep  # ports whose hexagon already occurred earlier in their OWN chain
  e    rep - a - bb
  d    # non-pure, non-dummy beta components  = # openings
  c    # pure clean-E beta components
  G    P - n!/n            z  G - c            Z  z - D2
  K    c(beta)             2g  G + 1 - K
  R_int  within-component duplicate-hexagon excess

CHECKED

  E1  a  <= D2                     E2  bb <= Qs
  E3  e  <= Z - Qs                 E4  a + bb + e <= 2g
  E5  a + bb + e = rep <= R_int    (exact, not just an inequality)
  E6  a = D2 - x,  bb = Qs - y,  x + y <= d      (the structural core)
  L1  a      >= D2 - d             (a LOWER bound the PIECE model consumes)
  L2  a + bb >= D2 + Qs - d        (a LOWER bound the PIECE model consumes)
  Z0  Z - Qs >= 0
  DJ  the a / bb / e classes partition the repeats; every retained A/B edge's
      target is a repeat and distinct A/B edges have distinct targets
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


def envelope(st, keep_heavy=False, policy="light_first", rng=None,
             forced_openings=None):
    n, P, beta, dummy = st["n"], st["P"], st["beta"], st["dummy"]
    etype, eweight = st["etype"], st["eweight"]
    hexr, orbr = st["hexr"], st["orbr"]
    r = n - 1
    HEX = factorial(n) // n
    G = P - HEX
    rng = rng or random.Random(0)
    fails = []

    comps = X.components(beta)
    K = len(comps)
    R_int = 0
    for cy in comps:
        cnt = Counter(hexr[q] for q in cy if q != dummy)
        R_int += sum(v - 1 for v in cnt.values())
    pure = [cy for cy in comps if dummy not in cy
            and all(etype.get(q) == "E" for q in cy)]
    cc = len(pure)
    d = K - 1 - cc
    two_g = G + 1 - K
    if two_g % 2:
        fails.append(("G+1-K odd", G, K))
    g = two_g // 2
    D2 = sum(1 for t in etype.values() if t == "A")
    Qs = sum(1 for t in etype.values() if t == "B")
    h = sum(1 for w in eweight.values() if w >= 4)
    Hh = sum(max(w - 3, 0) for w in eweight.values())
    z = G - cc
    Z = z - D2

    # ---- the cut, re-implemented here
    purev = {q for cy in pure for q in cy}
    openings = []
    for cy in comps:
        if dummy in cy or cy in pure:
            continue
        if forced_openings is not None:
            openings.append(forced_openings[len(openings)])
        else:
            openings.append(X.choose_opening(cy, etype, eweight, policy, rng))
    if len(openings) != d:
        fails.append(("openings != d", len(openings), d))
    x = sum(1 for q in openings if etype.get(q) == "A")
    y = sum(1 for q in openings if etype.get(q) == "B")
    cut = set(openings)
    heavy = set()
    if not keep_heavy:
        heavy = {q for q, w in eweight.items() if w >= 4}
        cut |= heavy
    # a heavy cut is never an A or B edge (weights 2 and 3)
    if any(etype.get(q) in ("A", "B") for q in heavy):
        fails.append("a type A/B joint was cut as heavy")

    succ = {}
    for q in range(P):
        if q in purev or q in cut:
            continue
        w = beta[q]
        if w != dummy and w not in purev:
            succ[q] = w
    indeg = Counter(succ.values())
    chains, used = [], set()
    for s0 in range(P):
        if s0 in purev or indeg.get(s0):
            continue
        ch, q = [], s0
        while True:
            ch.append(q)
            used.add(q)
            if q not in succ:
                break
            q = succ[q]
        chains.append(ch)
    if used != set(range(P)) - purev:
        fails.append("chains do not partition the non-circuit passes")

    # ---- measure a, bb, e and the repeats
    a = bb = e = rep = 0
    adj_ab = 0
    ab_targets = []
    for ch in chains:
        seenh = {hexr[ch[0]]}
        prev_ab = False
        for u, v in zip(ch, ch[1:]):
            t = etype.get(u)
            isrep = hexr[v] in seenh
            if isrep:
                rep += 1
                if t == "A":
                    a += 1
                    ab_targets.append(v)
                elif t == "B":
                    bb += 1
                    ab_targets.append(v)
                else:
                    e += 1
            else:
                if t in ("A", "B"):
                    fails.append(("DJ a retained A/B target is not a repeat", t))
            if t in ("A", "B"):
                if prev_ab:
                    adj_ab += 1
                prev_ab = True
            else:
                prev_ab = False
            seenh.add(hexr[v])
    # DJ: distinct A/B edges have distinct targets
    if len(ab_targets) != len(set(ab_targets)):
        fails.append("DJ two retained A/B edges share a target")
    if a + bb + e != rep:
        fails.append(("DJ classes do not partition the repeats", a, bb, e, rep))

    # ---- the inequalities
    if a > D2:
        fails.append(("E1 a > D2", a, D2))
    if bb > Qs:
        fails.append(("E2 bb > Qs", bb, Qs))
    if e > Z - Qs:
        fails.append(("E3 e > Z-Qs", e, Z, Qs))
    if a + bb + e > 2 * g:
        fails.append(("E4 a+bb+e > 2g", a + bb + e, 2 * g))
    if a + bb + e > R_int:
        fails.append(("E5 a+bb+e > R_int", a + bb + e, R_int))
    if a != D2 - x:
        fails.append(("E6 a != D2 - x", a, D2, x))
    if bb != Qs - y:
        fails.append(("E6 bb != Qs - y", bb, Qs, y))
    if x + y > d:
        fails.append(("E6 x+y > d", x, y, d))
    if a < D2 - d:
        fails.append(("L1 a < D2 - d", a, D2, d))
    if a + bb < D2 + Qs - d:
        fails.append(("L2 a+bb < D2+Qs-d", a, bb, D2, Qs, d))
    if Z - Qs < 0:
        fails.append(("Z0 Z < Qs", Z, Qs))
    return dict(n=n, P=P, G=G, K=K, c=cc, d=d, g=g, two_g=two_g, z=z, Z=Z,
                D2=D2, Qs=Qs, R_int=R_int, h=h, H=Hh, a=a, bb=bb, e=e,
                rep=rep, x=x, y=y, adj_AB=adj_ab, chains=len(chains),
                keep_heavy=keep_heavy, policy=policy,
                ZmQs=Z - Qs, slack_E1=D2 - a, slack_E2=Qs - bb,
                slack_E3=(Z - Qs) - e, slack_E4=2 * g - (a + bb + e),
                slack_E5=R_int - (a + bb + e),
                tight1=(a == D2), tight2=(bb == Qs), tight3=(e == Z - Qs),
                tight4=(a + bb + e == 2 * g), tight5=(a + bb + e == R_int),
                failures=fails, ok=not fails)


def main():
    t0 = time.time()
    rng = random.Random(158158)
    ws, w5 = R.words()
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import passes156 as P3                                        # noqa: E402
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n3e{i}", 3, w) for i, w in enumerate(P3.n3_family())]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 900))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 400))]
    st_, bad, agree_bad = Counter(), [], []
    named = {}
    for tag, n, W in pool:
        stt = X.structure(W, n)
        st_["words"] += 1
        st_[f"n{n}"] += 1
        for kh in (False, True):
            for pol in X.POLICIES:
                r = envelope(stt, keep_heavy=kh, policy=pol, rng=rng)
                st_["runs"] += 1
                if not r["ok"]:
                    st_["failures"] += 1
                    if len(bad) < 8:
                        bad.append(dict(tag=tag, keep_heavy=kh, policy=pol,
                                        failures=r["failures"][:5]))
                for k in ("tight1", "tight2", "tight3", "tight4", "tight5"):
                    if r[k]:
                        st_[k] += 1
                for k, cond in (("a_pos", r["a"] > 0), ("bb_pos", r["bb"] > 0),
                                ("e_pos", r["e"] > 0), ("xy_pos", r["x"] + r["y"] > 0),
                                ("x_pos", r["x"] > 0), ("y_pos", r["y"] > 0),
                                ("d_pos", r["d"] > 0), ("g_pos", r["g"] > 0),
                                ("adjacent_AB", r["adj_AB"] > 0),
                                ("heavy_pos", r["h"] > 0),
                                ("multi_chain", r["chains"] > 1),
                                ("c_pos", r["c"] > 0),
                                ("ZmQs_pos", r["Z"] - r["Qs"] > 0)):
                    if cond:
                        st_[k] += 1
                # cross-check against the round-156 measurement
                r6 = X.extract(stt, keep_heavy=kh, policy=pol, rng=random.Random(0))
                # r156 uses its own rng for the "random" policy; compare only
                # on the deterministic policies
                if pol != "random":
                    for k156, k158 in (("a", "a"), ("bb", "bb"), ("e", "e"),
                                       ("D2", "D2"), ("Qs", "Qs"), ("Z", "Z"),
                                       ("g", "g"), ("R_int", "R_int"),
                                       ("d", "d"), ("c", "c"), ("K", "K")):
                        if r6[k156] != r[k158]:
                            st_["agreement_failures"] += 1
                            if len(agree_bad) < 6:
                                agree_bad.append(dict(tag=tag, policy=pol,
                                                      key=k156,
                                                      r156=r6[k156],
                                                      r158=r[k158]))
        if tag in ("n4_optimum", "n6_witness_872"):
            named[tag] = {k: v for k, v in envelope(stt).items()
                          if k != "failures"}
    out = dict(seconds=round(time.time() - t0, 1), stats=dict(st_),
               named=named, failures=bad, agreement_failures=agree_bad,
               ok=(st_["failures"] == 0 and st_["agreement_failures"] == 0))
    (ROOT / "r158" / "certs" / "real_158.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "named"},
                     ensure_ascii=False, indent=1)[:2000])
    for k, v in named.items():
        print(k, json.dumps({q: v[q] for q in
                             ("P", "G", "K", "c", "d", "g", "Z", "D2", "Qs",
                              "R_int", "a", "bb", "e", "x", "y", "rep", "ok")}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
