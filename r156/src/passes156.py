#!/usr/bin/env python3
"""Round 156 Phase 3 + Phase 12 -- the INPUT layer of H.extract.

H.extract consumes the pass / nu / beta construction and the catalogue.  Those
are other nodes (H.splice, H.catalogue), but an audit of H.extract has to know
that the objects it is handed really are what they are called, so every clause
it depends on is re-verified here from the definitions:

  A  the arcs of a hexagon partition it; every hexagon carries a pass;
     sum_h (m_h - 1) = G;  P = HEX + G
  B  nu is a permutation, its cycles are exactly the hexagons, lengths m_h
  C  the joint leaving pass i leaves the word position of end(v_{nu(i)}),
     so reassigning it to (nu(i), i+1) changes nothing
  D  beta = T alpha^{-1} is a permutation with beta(nu(i)) = i+1
  cat the hidden-window count of each joint agrees with its catalogue type
     (E 0, A 1, B 2)

Phase 12 adds a genuinely EXHAUSTIVE small-n family: at n = 3 every ordering
of the 6 permutations is tried, the maximum-overlap word is built, and every
resulting fixed representative is extracted under every cut policy.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402


def check_inputs(W, n):
    """Lemmas A-D and the catalogue hidden counts, from the definitions."""
    bad = []
    N = factorial(n)
    st = X.structure(W, n)
    passes, P, nu, beta, dummy = (st["passes"], st["P"], st["nu"], st["beta"],
                                  st["dummy"])
    G = P - N // n
    # ---- A
    byhex = {}
    for i, (v, l) in enumerate(passes):
        byhex.setdefault(X.hexrep(v), []).append(i)
    if len(byhex) != N // n:
        bad.append(("A: a hexagon carries no pass", len(byhex)))
    if sum(len(x) - 1 for x in byhex.values()) != G:
        bad.append("A: sum (m_h - 1) != G")
    for h, idxs in byhex.items():
        cover = []
        for i in idxs:
            v, l = passes[i]
            cover += [X.sig_pow(v, t) for t in range(l)]
        if len(cover) != n or len(set(cover)) != n:
            bad.append(("A: arcs do not partition a hexagon", h))
    # ---- B
    if sorted(nu) != list(range(P)):
        bad.append("B: nu is not a permutation")
    seen, cyc = [False] * P, []
    for i in range(P):
        if seen[i]:
            continue
        c, x = [], i
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = nu[x]
        cyc.append(c)
    if len(cyc) != N // n:
        bad.append(("B: c(nu) != n!/n", len(cyc)))
    if sorted(len(c) for c in cyc) != sorted(len(v) for v in byhex.values()):
        bad.append("B: nu cycle lengths are not the m_h")
    for c in cyc:
        if len({X.hexrep(passes[i][0]) for i in c}) != 1:
            bad.append("B: a nu cycle spans two hexagons")
    # ---- C is asserted inside X.structure (it raises); re-assert the count
    if len(st["etype"]) != P - 1:
        bad.append("C: wrong number of reassigned joints")
    # ---- D
    if sorted(beta) != list(range(P + 1)):
        bad.append("D: beta is not a permutation")
    for i in range(P - 1):
        if beta[nu[i]] != i + 1:
            bad.append(("D: beta(nu(i)) != i+1", i))
    if beta[nu[P - 1]] != dummy or beta[dummy] != 0:
        bad.append("D: the two dummy edges are wrong")
    # ---- catalogue hidden counts
    exp = {"E": 0, "A": 1, "B": 2}
    for x, t in st["etype"].items():
        if t in exp and st["ehidden"][x] != exp[t]:
            bad.append(("cat: hidden count disagrees with the type", t,
                        st["ehidden"][x]))
    return st, bad


def n3_family():
    """Every ordering of the 6 permutations of {1,2,3}; keep the fixed
    representatives among the maximum-overlap words."""
    perms = ["".join(p) for p in itertools.permutations("123")]
    out, seen = [], set()
    for order in itertools.permutations(perms):
        w = order[0]
        for j in range(1, 6):
            k = X.omega(order[j - 1], order[j], 3)
            w += order[j][3 - k:]
        if not X.is_cover(w, 3, "123"):
            continue
        if w in seen:
            continue
        seen.add(w)
        try:
            if C.fixed_representative(w, 3) != w:
                continue
        except AssertionError:
            continue
        out.append(w)
    return out


def main():
    t0 = time.time()
    ws, w5 = R.words()
    import random
    rng = random.Random(31415)
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 600))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 250))]
    n3 = n3_family()
    pool += [(f"n3e{i}", 3, w) for i, w in enumerate(n3)]

    inbad, tally = [], Counter()
    for tag, n, W in pool:
        st, bad = check_inputs(W, n)
        tally["words"] += 1
        tally[f"n{n}"] += 1
        if bad:
            tally["input_failures"] += 1
            if len(inbad) < 8:
                inbad.append(dict(tag=tag, n=n, bad=bad[:5]))
    # ---- n = 3, exhaustive family, every policy
    n3bad, n3st = [], Counter()
    for w in n3:
        st = X.structure(w, 3)
        for kh in (False, True):
            for pol in X.POLICIES:
                r = X.extract(st, keep_heavy=kh, policy=pol)
                n3st["runs"] += 1
                if not r["ok"]:
                    n3st["failures"] += 1
                    if len(n3bad) < 8:
                        n3bad.append(dict(word=w, keep_heavy=kh, policy=pol,
                                          failures=r["failures"][:5]))
                if r["chains"] > 1:
                    n3st["multi_chain"] += 1
                if r["c"] > 0:
                    n3st["c_pos"] += 1
                if r["sigma"] > 0:
                    n3st["sigma_pos"] += 1
                if r["retained_AB"]:
                    n3st["with_AB"] += 1
    out = dict(seconds=round(time.time() - t0, 1), pool=dict(tally),
               input_failures=inbad,
               n3=dict(orderings=factorial(6),
                       fixed_representatives=len(n3), stats=dict(n3st),
                       failures=n3bad),
               ok=(tally["input_failures"] == 0 and n3st["failures"] == 0))
    (ROOT / "r156" / "certs" / "inputs_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
