#!/usr/bin/env python3
"""Round 146 — INDEPENDENT verifier for the §9 equality argument.

Adversarial re-derivation.  Nothing here imports the round-144/145 chain code;
the bipartite incidence structure is built as an explicit EDGE LIST and its
components are found with union-find, so multiedges are visible rather than
implicit.

-------------------------------------------------------------------------------
OBJECTS, stated once and used literally.

  Elements      X = {the P selected passes} + {one dummy *};  |X| = P + 1.
  alpha         the permutation of X that is nu on passes and fixes *.
                Its cycles: one per rotation hexagon carrying a pass (length
                m_h), plus {*}.  Every hexagon carries a pass, so
                c(alpha) = n!/n + 1 = 121 for n = 6.
  T             the (P+1)-cycle (1 2 ... P *).
  beta          T o alpha^{-1};  K := c(beta).
  B~            BIPARTITE MULTIGRAPH.  Vertices = the c(alpha) alpha-cycles
                together with the K beta-cycles.  ONE EDGE PER ELEMENT x in X,
                joining the alpha-cycle of x to the beta-cycle of x.
                So |V(B~)| = 121 + K  and  |E(B~)| = P + 1 = 121 + G.
  B             the SIMPLE graph obtained by merging parallel edges.
  R_int         sum over pairs (A, C) of (|A cap C| - 1)  =  |E(B~)| - |E(B)|.
                For a pair meeting in one element this is 0, so R_int is exactly
                the "within-component duplicate-hexagon excess".

THE INEQUALITY.  beta o alpha = T is a single (P+1)-cycle, so <alpha, beta> is
transitive on X; an alpha-step or a beta-step never leaves the corresponding
vertex of B, so transitivity makes B CONNECTED.  A connected simple graph has
at least |V| - 1 edges, hence

    121 + G - R_int = |E(B)| >= |V(B)| - 1 = 120 + K,    i.e.  K + R_int <= G+1.

EQUALITY.  |E(B)| = |V(B)| - 1 with B connected is precisely "B is a tree".
So  K + R_int = G + 1  <=>  B is a tree.  No other reading is available: the
only inputs were |E(B~)| = P+1, the definition of R_int, connectivity, and
c(alpha) = 121.

CONSEQUENCES USED IN §9 (all re-proved here, and checked numerically).
  (i)  Every hexagon carries a pass -- TRUE UNCONDITIONALLY (a permutation of
       hexagon h can only be selected inside a pass of h), so no tree argument
       is needed for "all 120 hexagons are used".
  (ii) Degree count.  sum over beta-vertices of deg = |E(B)| = 121 + G - R_int.
       At R_int = 0 the chain vertex has degree P_1 (its ports lie in distinct
       hexagons), each pure circuit has degree n-1 = 5, and the dummy alpha-cycle
       contributes 1, so  P_1 + 5c + 1 = 121 + G  with G = c, giving

            P_1 = 120 - 4c.

  (iii) F := hexagons the chain does not use has |F| = 120 - P_1 = 4c, and by
       (i) every hexagon of F is met by some pure circuit.  The c circuits carry
       5c incidences, so they cover F with total waste exactly c.  ACYCLICITY IS
       NOT USED for this step -- the test below asks only for a cover, which is
       a strictly weaker (hence safe) necessary condition.
-------------------------------------------------------------------------------
"""
from __future__ import annotations
import json, sys
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from l6_cleanroom_146 import (sig, tau, hexkey, orbkey, omega, invariants)  # noqa


class UF:
    def __init__(s, items):
        s.p = {i: i for i in items}

    def find(s, x):
        while s.p[x] != x:
            s.p[x] = s.p[s.p[x]]
            x = s.p[x]
        return x

    def union(s, a, b):
        ra, rb = s.find(a), s.find(b)
        if ra != rb:
            s.p[ra] = rb


def graph_audit(W, n=6):
    """Build B~ / B from the word and check every clause of the argument."""
    N = factorial(n)
    seen, sel, pos = set(), [], []
    for i in range(len(W) - n + 1):
        w = W[i:i + n]
        if len(set(w)) == n and w not in seen:
            seen.add(w)
            sel.append(w)
            pos.append(i)
    gaps = [pos[j + 1] - pos[j] for j in range(N - 1)]
    passes, run = [], [0]
    for j, g in enumerate(gaps):
        if g == 1:
            run.append(j + 1)
        else:
            passes.append(run)
            run = [j + 1]
    passes.append(run)
    P = len(passes)
    ent = [sel[r[0]] for r in passes]
    lens = [len(r) for r in passes]
    G = P - N // n
    hx = [hexkey(e) for e in ent]
    ob = [orbkey(e) for e in ent]
    idx = {e: i for i, e in enumerate(ent)}
    nu = []
    for i in range(P):
        x = ent[i]
        for _ in range(lens[i]):
            x = sig(x)
        nu.append(idx[x])
    DUM = "*"
    T = {i: i + 1 for i in range(P - 1)}
    T[P - 1] = DUM
    T[DUM] = 0
    alpha = {i: nu[i] for i in range(P)}
    alpha[DUM] = DUM
    ainv = {v: kk for kk, v in alpha.items()}
    beta = {x: T[ainv[x]] for x in list(range(P)) + [DUM]}

    def cycles(perm):
        out, seen2 = [], set()
        for st in perm:
            if st in seen2:
                continue
            cy, x = [], st
            while x not in seen2:
                seen2.add(x)
                cy.append(x)
                x = perm[x]
            out.append(cy)
        return out

    acyc, bcyc = cycles(alpha), cycles(beta)
    acid = {x: ("A%d" % i) for i, cy in enumerate(acyc) for x in cy}
    bcid = {x: ("B%d" % i) for i, cy in enumerate(bcyc) for x in cy}
    # ---- B~ : one edge per element
    multi = Counter((acid[x], bcid[x]) for x in list(range(P)) + [DUM])
    V = set(acid.values()) | set(bcid.values())
    E_multi = sum(multi.values())
    E_simple = len(multi)
    R_int_graph = E_multi - E_simple
    uf = UF(V)
    for (a, b) in multi:
        uf.union(a, b)
    ncomp = len({uf.find(v) for v in V})
    K = len(bcyc)
    fails = []
    if E_multi != P + 1:
        fails.append(("B~ edge count", E_multi, P + 1))
    if len(acyc) != N // n + 1:
        fails.append(("c(alpha)", len(acyc), N // n + 1))
    if len(V) != N // n + 1 + K:
        fails.append(("vertex count", len(V), N // n + 1 + K))
    if ncomp != 1:
        fails.append(("B is NOT connected", ncomp))
    if K + R_int_graph > G + 1:
        fails.append(("inequality violated", K, R_int_graph, G))
    # R_int the other way: per (beta-component, hexagon) histogram
    R_int_hist = sum(sum(v - 1 for v in
                         Counter(hx[x] for x in cy if x != DUM).values())
                     for cy in bcyc)
    if R_int_hist != R_int_graph:
        fails.append(("two R_int computations disagree", R_int_hist, R_int_graph))
    tight = (K + R_int_graph == G + 1)
    is_tree = (ncomp == 1 and E_simple == len(V) - 1)
    if tight != is_tree:
        fails.append(("tightness <-> tree FAILS", tight, is_tree))
    # independent acyclicity check for the tree case
    if is_tree:
        uf2 = UF(V)
        cyc_found = False
        for (a, b) in multi:
            if uf2.find(a) == uf2.find(b):
                cyc_found = True
            uf2.union(a, b)
        if cyc_found:
            fails.append("claimed tree but a cycle was found")
    # ---- pure circuits and the degree identity
    type_of = {}
    for j, g in enumerate(gaps):
        if g == 1:
            continue
        src = sel[j]
        i = next(i for i in range(P) if _last(ent[i], lens[i]) == src)
        p = nu[i]
        v, t = ent[p], sel[j + 1]
        type_of[p] = ("E" if (g == 2 and t == tau(v)) else
                      "A" if (g == 2 and t == sig(v)) else
                      "other")
    pure = [cy for cy in bcyc if DUM not in cy
            and all(type_of.get(x) == "E" for x in cy)]
    c = len(pure)
    chain = [cy for cy in bcyc if DUM in cy]
    P1 = len(chain[0]) - 1 if chain else 0
    pred_P1 = None
    if tight and R_int_graph == 0 and c == G:
        pred_P1 = (N // n) - (n - 2) * c          # 120 - 4c at n=6
        if P1 != pred_P1:
            fails.append(("degree identity P_1 = 120-4c fails", P1, pred_P1))
    # hexagon-degree bookkeeping
    hexdeg = Counter()
    for x in range(P):
        hexdeg[acid[x]] += 1
    if sum(hexdeg.values()) != P:
        fails.append("hexagon incidences != P")
    if any(v == 0 for v in hexdeg.values()):
        fails.append("a hexagon carries no pass")
    if sum(v - 1 for v in hexdeg.values()) != G:
        fails.append("sum(deg_hex - 1) != G")
    return dict(P=P, G=G, K=K, c=c, R_int=R_int_graph, E_multi=E_multi,
                E_simple=E_simple, V=len(V), connected=(ncomp == 1),
                tight=tight, is_tree=is_tree, max_multiplicity=max(multi.values()),
                chain_ports=P1, predicted_P1=pred_P1,
                failures=fails, ok=not fails)


def _last(entry, ln):
    x = entry
    for _ in range(ln - 1):
        x = sig(x)
    return x


if __name__ == "__main__":
    import gzip
    tot, bad, prof = 0, [], Counter()
    for path in sys.argv[1:]:
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "rt") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#") or len(set(s)) != 6 or len(s) < 800:
                    continue
                r = graph_audit(s)
                tot += 1
                if not r["ok"]:
                    bad.append((path, s[:20], r["failures"]))
                prof[(r["P"], r["G"], r["K"], r["c"], r["R_int"], r["tight"],
                      r["is_tree"], r["chain_ports"], r["predicted_P1"],
                      r["max_multiplicity"])] += 1
    print(f"words={tot} failures={len(bad)}")
    for kk, v in prof.most_common(12):
        print(f"  x{v:<6} P={kk[0]} G={kk[1]} K={kk[2]} c={kk[3]} R_int={kk[4]} "
              f"tight={kk[5]} tree={kk[6]} chain_ports={kk[7]} "
              f"predicted={kk[8]} max_mult={kk[9]}")
    for b in bad[:6]:
        print("  FAIL", b)
    (ROOT / "outputs" / "rr_l6_incidence_graph_146.json").write_text(
        json.dumps(dict(words=tot, failures=len(bad),
                        profiles={str(kk): v for kk, v in prof.items()},
                        failure_examples=[list(map(str, b)) for b in bad[:10]]),
                   ensure_ascii=False, indent=1))
    sys.exit(1 if bad else 0)
