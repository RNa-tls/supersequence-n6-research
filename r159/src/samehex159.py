#!/usr/bin/env python3
"""Round 159 -- SAME-HEX measured independently on real covers.

The pass / nu / alpha / T / beta layer comes from the round-156 independent
reconstruction (r156/src/extract156.py, which imports nothing from src/).
Everything SAME-HEX talks about is rebuilt here.

WHAT IS CHECKED, per word

  G1  every type A edge has v_{beta(p)} = sigma(v_p); every type B edge has
      v_{beta(p)} = sigma^2(v_p)                       -- verified from strings
  G2  hence hex(beta(p)) = hex(p), and beta(p) is in p's beta-component
  H1  the connector's hidden windows are literally the claimed ones:
      type A -> [v_p];  type B -> [v_p, sigma^2(p')]   -- verified from strings
  I1  index increase: for every A/B edge p -> q = beta(p),  p < q, and in fact
      p + 2 <= q  (i.e. nu(i) < i with q = i+1)
  F1  inside each (hexagon h, component j) group: all A/B endpoints stay in the
      group; targets are distinct (in-degree <= 1); the edge digraph is acyclic;
      at least one group vertex is not a target; hence #edges <= m_{h,j} - 1
  S1  sum over groups of #edges = D2 + Qs
  S2  D2 + Qs <= R_int                                  (the theorem)
  S3  R_int <= 2g                                       (H.incidence, re-checked)
  S4  D2 + Qs <= 2g,  Z >= Qs >= 0                      (the corollary the row
                                                         enumeration consumes)
  R1  the histogram R_int equals the incidence-graph pair excess
      |E(B~)| - |E(B)| (the definition H.incidence uses)
  D1  no A/B edge touches the dummy; the dummy contributes 0 to R_int
  P1  the POST-CUT repeat count `rep` is recorded, so that the claim
      "D2 + Qs <= R_int is implied by the Extraction Theorem" can be tested:
      it would need D2 + Qs <= rep, which is FALSE in general.
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


def hidden_list(src, tgt, gap, n):
    raw = src + tgt[n - gap:] if gap < n else src + tgt
    return [raw[o:o + n] for o in range(1, gap)
            if len(set(raw[o:o + n])) == n]


def samehex(st):
    n, P, beta, dummy = st["n"], st["P"], st["beta"], st["dummy"]
    etype, eweight = st["etype"], st["eweight"]
    hexr, passes = st["hexr"], st["passes"]
    sel, gaps = st["sel"], st["gaps"]
    HEX = factorial(n) // n
    G = P - HEX
    fails = []

    comps = X.components(beta)
    K = len(comps)
    compof = {q: i for i, cy in enumerate(comps) for q in cy}
    # ---- R_int, histogram form (the form SAME-HEX and the extraction use)
    R_hist = 0
    for cy in comps:
        cnt = Counter(hexr[q] for q in cy if q != dummy)
        R_hist += sum(v - 1 for v in cnt.values())
    # ---- R_int, incidence-graph form (the form H.incidence uses)
    alpha = list(st["nu"]) + [dummy]
    ac = X.components(alpha)
    A = {q: i for i, cy in enumerate(ac) for q in cy}
    multi = Counter((A[q], compof[q]) for q in list(range(P)) + [dummy])
    R_graph = sum(multi.values()) - len(multi)
    if R_hist != R_graph:
        fails.append(("R1 two R_int definitions disagree", R_hist, R_graph))
    R_int = R_hist
    two_g = G + 1 - K
    if two_g % 2:
        fails.append(("G+1-K odd", G, K))
    g = two_g // 2

    D2 = sum(1 for t in etype.values() if t == "A")
    Qs = sum(1 for t in etype.values() if t == "B")
    pure = [cy for cy in comps if dummy not in cy
            and all(etype.get(q) == "E" for q in cy)]
    cc = len(pure)
    z = G - cc
    Z = z - D2

    # ---- the joint source string, per typed edge, recomputed from the word
    endpos = {}
    for i, (v, l) in enumerate(passes):
        endpos[X.sig_pow(v, l - 1)] = i
    srcstr, tgtstr = {}, {}
    for j in range(len(gaps)):
        if gaps[j] == 1:
            continue
        i = endpos[sel[j][1]]
        p = st["nu"][i]
        srcstr[p] = sel[j][1]
        tgtstr[p] = sel[j + 1][1]

    ab_edges = []
    for p, t in etype.items():
        if t not in ("A", "B"):
            continue
        q = beta[p]
        v_p = passes[p][0]
        # ---- G1: the algebraic form of the target, from strings
        want = X.sigma(v_p) if t == "A" else X.sigma(X.sigma(v_p))
        if q == dummy or passes[q][0] != want:
            fails.append(("G1 target is not sigma/sigma^2 of the source", t, p))
            continue
        if tgtstr[p] != want:
            fails.append(("G1 the word's target window disagrees", t, p))
        # ---- G2
        if hexr[q] != hexr[p]:
            fails.append(("G2 hexagons differ", t, p))
        if compof[q] != compof[p]:
            fails.append(("G2 components differ", t, p))
        # ---- H1: the hidden windows, literally
        hw = hidden_list(srcstr[p], tgtstr[p], eweight[p], n)
        pprime = srcstr[p]
        if t == "A":
            if hw != [X.sigma(pprime)] or X.sigma(pprime) != v_p:
                fails.append(("H1 type A hidden window", p, hw))
        else:
            if hw != [X.sigma(pprime), X.sigma(X.sigma(pprime))] or \
                    X.sigma(pprime) != v_p:
                fails.append(("H1 type B hidden windows", p, hw))
        # ---- I1
        if not p < q:
            fails.append(("I1 index does not increase", t, p, q))
        if p + 2 > q:
            fails.append(("I1 nu(i) < i fails (p+2 > q)", t, p, q))
        ab_edges.append((p, q, t))

    # ---- F1: the per-(hexagon, component) in-forest
    groups = {}
    for q in range(P):
        groups.setdefault((hexr[q], compof[q]), []).append(q)
    by_group = {}
    for (p, q, t) in ab_edges:
        by_group.setdefault((hexr[p], compof[p]), []).append((p, q, t))
    total_edges = 0
    for key, edges in by_group.items():
        verts = set(groups[key])
        m = len(verts)
        tgts = [q for (_, q, _) in edges]
        if any(p not in verts or q not in verts for (p, q, _) in edges):
            fails.append(("F1 an A/B edge leaves its group", key))
        if len(tgts) != len(set(tgts)):
            fails.append(("F1 two A/B edges share a target", key))
        # acyclicity: indices strictly increase along every edge
        if any(p >= q for (p, q, _) in edges):
            fails.append(("F1 a group edge does not increase the index", key))
        roots = verts - set(tgts)
        if not roots:
            fails.append(("F1 no root: the group would contain a cycle", key))
        if len(edges) > m - 1:
            fails.append(("F1 group has more than m-1 edges", key, len(edges), m))
        total_edges += len(edges)
    if total_edges != D2 + Qs:
        fails.append(("S1 grouped edges != D2 + Qs", total_edges, D2, Qs))

    # ---- the theorem and its corollary
    if D2 + Qs > R_int:
        fails.append(("S2 D2 + Qs > R_int", D2, Qs, R_int))
    if R_int > 2 * g:
        fails.append(("S3 R_int > 2g", R_int, 2 * g))
    if D2 + Qs > 2 * g:
        fails.append(("S4 D2 + Qs > 2g", D2, Qs, 2 * g))
    if Z < 0 or Qs > Z:
        fails.append(("S4 Z < 0 or Qs > Z", Z, Qs))

    # ---- D1: the dummy
    if any(p == dummy or q == dummy for (p, q, _) in ab_edges):
        fails.append("D1 an A/B edge touches the dummy")
    if etype.get(dummy) is not None:
        fails.append("D1 the dummy carries an edge type")

    # ---- P1: the post-cut repeat count, for the Phase-8 comparison
    r6 = X.extract(st, keep_heavy=False, policy="light_first")
    rep = r6["hex_repeats"]

    return dict(n=n, P=P, G=G, K=K, c=cc, g=g, two_g=two_g, z=z, Z=Z,
                D2=D2, Qs=Qs, R_int=R_int, R_graph=R_graph, rep=rep,
                d=r6["d"], groups_with_edges=len(by_group),
                max_group_edges=max([len(v) for v in by_group.values()] or [0]),
                ab_edges=len(ab_edges),
                slack_lower=R_int - (D2 + Qs), slack_upper=2 * g - R_int,
                tight_lower=(D2 + Qs == R_int and R_int > 0),
                tight_upper=(R_int == 2 * g and R_int > 0),
                D2Qs_exceeds_postcut_rep=(D2 + Qs > rep),
                failures=fails, ok=not fails)


def main():
    t0 = time.time()
    rng = random.Random(159159)
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
    prof = Counter()
    for tag, n, W in pool:
        stt = X.structure(W, n)
        r = samehex(stt)
        st_["words"] += 1
        st_[f"n{n}"] += 1
        if not r["ok"]:
            st_["failures"] += 1
            if len(bad) < 8:
                bad.append(dict(tag=tag, n=n, failures=r["failures"][:5]))
        for k, cond in (("D2_pos", r["D2"] > 0), ("Qs_pos", r["Qs"] > 0),
                        ("both_AB", r["D2"] > 0 and r["Qs"] > 0),
                        ("R_pos", r["R_int"] > 0),
                        ("tight_lower", r["tight_lower"]),
                        ("tight_upper", r["tight_upper"]),
                        ("multi_edge_group", r["max_group_edges"] > 1),
                        ("D2Qs_gt_postcut_rep", r["D2Qs_exceeds_postcut_rep"]),
                        ("d_pos", r["d"] > 0), ("g_pos", r["g"] > 0)):
            if cond:
                st_[k] += 1
        prof[(r["n"], r["D2"], r["Qs"], r["R_int"], 2 * r["g"])] += 1
        if tag in ("n4_optimum", "n6_witness_872"):
            named[tag] = {k: v for k, v in r.items() if k != "failures"}
    out = dict(seconds=round(time.time() - t0, 1), stats=dict(st_),
               distinct_profiles=len(prof), named=named, failures=bad,
               ok=(st_["failures"] == 0))
    (ROOT / "r159" / "certs" / "real_159.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "named"},
                     ensure_ascii=False, indent=1)[:1800])
    for k, v in named.items():
        print(k, json.dumps({q: v[q] for q in
                             ("P", "G", "K", "g", "D2", "Qs", "R_int", "rep",
                              "ab_edges", "ok")}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
