#!/usr/bin/env python3
"""Round 157 -- the incidence graph built literally on real covers.

The pass / nu / alpha / T / beta layer is taken from r157's own copy of the
round-156 independent reconstruction (r156/src/extract156.py), which imports
nothing from src/.  The bipartite incidence graph is then built here as an
EXPLICIT EDGE LIST -- one edge per element of X, parallel edges kept -- so that
multiplicities are visible rather than implicit.

Checked on every word, for n = 3, 4, 5 and the n = 6 witness:

  V1  c(alpha) = n!/n + 1                 (every hexagon carries a pass)
  V2  |V(B)| = n!/n + 1 + K
  E1  |E(B~)| = |X| = P + 1 = n!/n + 1 + G
  E2  |E(B)| = |E(B~)| - R_int
  R1  R_int computed as sum over (alpha-cycle, beta-cycle) pairs of
      (|A cap C| - 1)  ==  R_int computed as the per-component hexagon
      histogram excess with the dummy skipped        (the two repository
      definitions agree, and the dummy contributes 0 to both)
  C1  B is connected, and comp(B) = #<alpha,beta>-orbits
  M1  mu(B) = |E(B)| - |V(B)| + 1 >= 0
  I1  K + R_int <= G + 1
  P1  K = G + 1 (mod 2)
  S1  2g := G + 1 - K = mu(B) + R_int      (the split identity)
  T1  K + R_int = G + 1  <=>  B is a tree
  D1  g = 0  =>  mu(B) = 0 and R_int = 0   (the form H.tight consumes)
  D2  R_int <= 2g                          (the form the row enumeration
                                            consumes)
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


class UF:
    def __init__(s, items):
        s.p = {i: i for i in items}
        s.cycle_found = False

    def find(s, x):
        while s.p[x] != x:
            s.p[x] = s.p[s.p[x]]
            x = s.p[x]
        return x

    def union(s, a, b):
        ra, rb = s.find(a), s.find(b)
        if ra == rb:
            s.cycle_found = True
        else:
            s.p[ra] = rb


def incidence(st):
    """Build B~ and B from the pass structure and check every clause."""
    n, P, beta, dummy = st["n"], st["P"], st["beta"], st["dummy"]
    nu, hexr = st["nu"], st["hexr"]
    HEX = factorial(n) // n
    G = P - HEX
    Xs = list(range(P)) + [dummy]
    alpha = list(nu) + [dummy]
    fails = []

    ac = X.components(alpha)
    bc = X.components(beta)
    A = {x: i for i, c in enumerate(ac) for x in c}
    Cc = {x: i for i, c in enumerate(bc) for x in c}
    K = len(bc)
    # V1: alpha-cycles are the hexagons plus the dummy
    if len(ac) != HEX + 1:
        fails.append(("V1 c(alpha)", len(ac), HEX + 1))
    hexes_of_cycle = [{hexr[x] for x in c if x != dummy} for c in ac]
    if sorted(len(h) for h in hexes_of_cycle) != [0] + [1] * HEX:
        fails.append("V1 an alpha-cycle is not one hexagon (or the dummy)")
    if len({h for hs in hexes_of_cycle for h in hs}) != HEX:
        fails.append("V1 a hexagon carries no pass")

    multi = Counter((A[x], Cc[x]) for x in Xs)
    E_multi, E_simple = sum(multi.values()), len(multi)
    R_graph = E_multi - E_simple
    V = len(ac) + K
    if E_multi != P + 1:
        fails.append(("E1", E_multi, P + 1))
    if E_multi != HEX + 1 + G:
        fails.append(("E1b", E_multi, HEX + 1 + G))
    if V != HEX + 1 + K:
        fails.append(("V2", V, HEX + 1 + K))
    # R1: the histogram definition used everywhere downstream
    R_hist = 0
    for c in bc:
        cnt = Counter(hexr[x] for x in c if x != dummy)
        R_hist += sum(v - 1 for v in cnt.values())
    if R_hist != R_graph:
        fails.append(("R1 two R_int definitions disagree", R_hist, R_graph))
    R_int = R_graph
    if E_simple != E_multi - R_int:
        fails.append("E2")

    # degree bookkeeping: no incidence omitted, none double counted
    degA, degB = Counter(), Counter()
    for (a, b), m in multi.items():
        degA[a] += m
        degB[b] += m
    if sum(degA.values()) != E_multi or sum(degB.values()) != E_multi:
        fails.append("degree sums != |E(B~)|")
    dum_cycle = A[dummy]
    if degA[dum_cycle] != 1 or len(ac[dum_cycle]) != 1:
        fails.append(("the dummy alpha-cycle is not a singleton of degree 1",
                      degA[dum_cycle], len(ac[dum_cycle])))
    if sum(v - 1 for i, v in degA.items() if i != dum_cycle) != G:
        fails.append("sum over hexagons of (deg - 1) != G")
    if sum(degB.values()) != P + 1:
        fails.append("beta-side degree sum != P+1")
    if any(v == 0 for v in list(degA.values()) + list(degB.values())):
        fails.append("a vertex has degree 0")

    uf = UF([("A", i) for i in range(len(ac))] + [("B", i) for i in range(K)])
    for (a, b) in multi:
        uf.union(("A", a), ("B", b))
    comp = len({uf.find(v) for v in uf.p})
    # C1: <alpha, beta>-orbits
    ainv = {}
    for x, y in zip(Xs, alpha):
        ainv[y] = x
    seen, orbits = set(), 0
    for s0 in Xs:
        if s0 in seen:
            continue
        orbits += 1
        stack = [s0]
        seen.add(s0)
        while stack:
            x = stack.pop()
            for y in (alpha[x], beta[x], ainv[x]):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
    if comp != orbits:
        fails.append(("C1 comp != orbits", comp, orbits))
    if comp != 1:
        fails.append(("C1 B is not connected", comp))
    mu = E_simple - V + comp
    if mu < 0:
        fails.append(("M1 mu < 0", mu))
    if K + R_int > G + 1:
        fails.append(("I1 inequality violated", K, R_int, G))
    if (K - (G + 1)) % 2:
        fails.append(("P1 parity", K, G))
    two_g = G + 1 - K
    if two_g != mu + R_int:
        fails.append(("S1 split identity", two_g, mu, R_int))
    tight = (K + R_int == G + 1)
    # independent acyclicity: replay the unions and watch for a closing edge
    uf2 = UF([("A", i) for i in range(len(ac))] + [("B", i) for i in range(K)])
    for (a, b) in multi:
        uf2.union(("A", a), ("B", b))
    is_tree = (comp == 1 and not uf2.cycle_found)
    if is_tree != (E_simple == V - 1 and comp == 1):
        fails.append("T1 two tree tests disagree")
    if tight != is_tree:
        fails.append(("T1 tight <-> tree", tight, is_tree))
    g = two_g // 2 if two_g % 2 == 0 else None
    if g == 0 and (mu != 0 or R_int != 0):
        fails.append(("D1 g=0 but mu or R_int nonzero", mu, R_int))
    if g is not None and R_int > 2 * g:
        fails.append(("D2 R_int > 2g", R_int, 2 * g))
    return dict(n=n, P=P, G=G, K=K, R_int=R_int, R_hist=R_hist, V=V,
                E_multi=E_multi, E_simple=E_simple, comp=comp, orbits=orbits,
                mu=mu, two_g=two_g, g=g, tight=tight, is_tree=is_tree,
                c_alpha=len(ac), max_mult=max(multi.values()),
                dummy_degree=degA[A[dummy]],
                max_hex_degree=max(v for i, v in degA.items() if i != A[dummy]),
                max_beta_degree=max(degB.values()),
                failures=fails, ok=not fails)


def main():
    t0 = time.time()
    rng = random.Random(1570157)
    ws, w5 = R.words()
    pool = [(tag, n, W) for tag, n, W in ws]
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import passes156 as P3                                        # noqa: E402
    n3 = P3.n3_family()
    pool += [(f"n3e{i}", 3, w) for i, w in enumerate(n3)]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 900))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 400))]
    tally, bad, prof = Counter(), [], Counter()
    named = {}
    for tag, n, W in pool:
        st = X.structure(W, n)
        r = incidence(st)
        tally["words"] += 1
        tally[f"n{n}"] += 1
        if not r["ok"]:
            tally["failures"] += 1
            if len(bad) < 8:
                bad.append(dict(tag=tag, n=n, failures=r["failures"][:5]))
        for key, cond in (("tight", r["tight"]), ("tree", r["is_tree"]),
                          ("R_int_pos", r["R_int"] > 0),
                          ("mu_pos", r["mu"] > 0),
                          ("g_zero", r["g"] == 0),
                          ("multi_edge", r["max_mult"] > 1),
                          ("K_gt_1", r["K"] > 1)):
            if cond:
                tally[key] += 1
        prof[(r["n"], r["G"], r["K"], r["R_int"], r["mu"], r["tight"])] += 1
        if tag in ("n4_optimum", "n6_witness_872") or tag.startswith("n5_min"):
            named[tag] = {k: r[k] for k in
                          ("n", "P", "G", "K", "R_int", "V", "E_multi",
                           "E_simple", "comp", "mu", "two_g", "g", "tight",
                           "is_tree", "c_alpha", "max_mult", "ok")}
    out = dict(seconds=round(time.time() - t0, 1), tally=dict(tally),
               named=named, distinct_profiles=len(prof),
               richest=[[list(k), v] for k, v in prof.most_common(10)],
               failures=bad, ok=(tally["failures"] == 0))
    (ROOT / "r157" / "certs" / "real_157.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("named", "richest")},
                     ensure_ascii=False, indent=1))
    for k, v in named.items():
        print(k, json.dumps(v, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
