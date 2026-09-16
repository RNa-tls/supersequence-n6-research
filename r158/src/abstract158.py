#!/usr/bin/env python3
"""Round 158 -- the envelope split into its STRUCTURAL and ARITHMETIC halves,
each decided on a completely specified finite universe.

STRUCTURAL HALF (E6).  On the cut structure alone:

      a = D2 - x,   bb = Qs - y,   x + y <= d

  where x (resp. y) is the number of type A (resp. B) joints spent as a cycle
  OPENING, and d is the number of non-pure, non-dummy beta components.  The
  only hypotheses are: (i) every typed edge is either retained in a chain or
  cut; (ii) the cut is exactly {one opening per non-pure cycle} union {heavy};
  (iii) an A or B joint is never heavy.  Enumerated EXHAUSTIVELY over the
  abstract cut structures of r156 (cycles + exactly one path, every clean-E
  labelling, every heavy labelling, every opening choice).

ARITHMETIC HALF.  Given
      (H1) a + bb + e = rep <= R_int          [round-156 Claim 5]
      (H2) R_int <= 2g                        [H.incidence]
      (H3) a = D2 - x, bb = Qs - y, x + y <= d   [E6, above]
      (H4) z = G - c = 2g + d,  Z = z - D2       [definitions]
      (H5) D2 + Qs <= R_int                   [H.samehex]
  derive
      (E1) a <= D2      (E2) bb <= Qs
      (E3) e <= Z - Qs  (E4) a + bb + e <= 2g
      (Z0) Z - Qs >= d >= 0
      (L1) a >= D2 - d  (L2) a + bb >= D2 + Qs - d
  The derivation is linear; it is written out in the audit document.  Here the
  implication is additionally DECIDED over a complete integer box, and each
  hypothesis is ablated to show it is load-bearing.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import abstract156 as A6                                          # noqa: E402


# --------------------------------------------------------- structural half
def structural(m, stats, ex):
    """Exhaustive over shapes x clean-E labels x A/B/heavy labels x openings."""
    for succ, cycles, path in A6.shapes(m):
        edges = list(succ)
        ne = len(edges)
        for Emask in range(1 << ne):
            E = {edges[i] for i in range(ne) if Emask >> i & 1}
            nonE = [q for q in edges if q not in E]
            pure = [cy for cy in cycles if all(q in E for q in cy)]
            nonpure = [cy for cy in cycles if not all(q in E for q in cy)]
            opts, skip = [], False
            for cy in nonpure:
                o = [q for q in cy if q not in E]
                if not o:
                    skip = True
                    break
                opts.append(o)
            if skip:
                continue
            d = len(nonpure)
            # label each non-E edge as A, B, N (other light) or Hv (heavy);
            # A and B are never heavy, which is the hypothesis being used
            for lab in itertools.product("ABNH", repeat=len(nonE)):
                lm = dict(zip(nonE, lab))
                D2 = sum(1 for v in lm.values() if v == "A")
                Qs = sum(1 for v in lm.values() if v == "B")
                heavy = {q for q, v in lm.items() if v == "H"}
                for openings in (itertools.product(*opts) if opts else [()]):
                    for keep in (False, True):
                        cut = set(openings) | (set() if keep else heavy)
                        purev = {q for cy in pure for q in cy}
                        s2 = {q: w for q, w in succ.items()
                              if q not in purev and q not in cut
                              and w not in purev}
                        retA = sum(1 for q in s2 if lm.get(q) == "A")
                        retB = sum(1 for q in s2 if lm.get(q) == "B")
                        x = sum(1 for q in openings if lm.get(q) == "A")
                        y = sum(1 for q in openings if lm.get(q) == "B")
                        stats["cases"] += 1
                        bad = []
                        if retA != D2 - x:
                            bad.append("a != D2 - x")
                        if retB != Qs - y:
                            bad.append("bb != Qs - y")
                        if x + y > d:
                            bad.append("x + y > d")
                        if retA < D2 - d:
                            bad.append("L1")
                        if retA + retB < D2 + Qs - d:
                            bad.append("L2")
                        if bad:
                            stats["violations"] += 1
                            for b in bad:
                                stats["v_" + b] += 1
                            if len(ex) < 4:
                                ex.append(dict(m=m, succ=succ, E=sorted(E),
                                               labels=lm, openings=list(openings),
                                               keep=keep, broke=bad))
    return stats


# --------------------------------------------------------- arithmetic half
def arith_box(B=6, ablate=None):
    """Decide the implication over the complete integer box [0, B]."""
    st = Counter()
    ex = None
    for g in range(0, B + 1):
        for d in range(0, B + 1):
            two_g = 2 * g
            z = two_g + d
            for D2 in range(0, min(z, B) + 1):
                Z = z - D2
                for Qs in range(0, B + 1):
                    for R_int in range(0, B + 1):
                        if ablate != "H2" and R_int > two_g:
                            continue
                        if ablate != "H5" and D2 + Qs > R_int:
                            continue
                        for x in range(0, D2 + 1):
                            for y in range(0, Qs + 1):
                                if ablate != "H3" and x + y > d:
                                    continue
                                a, bb = D2 - x, Qs - y
                                for e in range(0, B + 1):
                                    if ablate != "H1" and a + bb + e > R_int:
                                        continue
                                    st["cases"] += 1
                                    bad = []
                                    if a > D2:
                                        bad.append("E1")
                                    if bb > Qs:
                                        bad.append("E2")
                                    if e > Z - Qs:
                                        bad.append("E3")
                                    if a + bb + e > two_g:
                                        bad.append("E4")
                                    if Z - Qs < d:
                                        bad.append("Z0")
                                    if a < D2 - d:
                                        bad.append("L1")
                                    if a + bb < D2 + Qs - d:
                                        bad.append("L2")
                                    if bad:
                                        st["violations"] += 1
                                        for b in bad:
                                            st["v_" + b] += 1
                                        if ex is None:
                                            ex = dict(g=g, d=d, D2=D2, Qs=Qs,
                                                      Z=Z, R_int=R_int, x=x,
                                                      y=y, a=a, bb=bb, e=e,
                                                      broke=bad)
    return st, ex


def disjointness(m, stats, ex):
    """One chain of m ports: do the a / bb / e classes partition the repeats?

    Universe: every hexagon labelling of the m ports (a set partition of m)
    times every edge labelling in {A, B, N}^(m-1), keeping only those where an
    A or B edge has target hexagon = source hexagon (the catalogue property
    the classification rests on).  EXHAUSTIVE for the stated m.
    """
    labs = A6.part_labels(m)
    for hexa in labs:
        for lab in itertools.product("ABN", repeat=max(m - 1, 0)):
            ok_hyp = all(lab[i] not in "AB" or hexa[i] == hexa[i + 1]
                         for i in range(m - 1))
            if not ok_hyp:
                continue
            stats["cases"] += 1
            seen = {hexa[0]}
            rep = a = bb = e = 0
            adj = 0
            classes = []
            for i in range(m - 1):
                t = lab[i]
                isrep = hexa[i + 1] in seen
                if isrep:
                    rep += 1
                    if t == "A":
                        a += 1
                        classes.append(("a", i + 1))
                    elif t == "B":
                        bb += 1
                        classes.append(("bb", i + 1))
                    else:
                        e += 1
                        classes.append(("e", i + 1))
                elif t in "AB":
                    stats["hypothesis_would_be_violated"] += 1
                if t in "AB" and i > 0 and lab[i - 1] in "AB":
                    adj += 1
                seen.add(hexa[i + 1])
            if adj:
                stats["with_adjacent_AB"] += 1
            bad = []
            if a + bb + e != rep:
                bad.append("partition")
            if len({p for _, p in classes}) != len(classes):
                bad.append("two events share a port")
            if rep != m - len(set(hexa)):
                bad.append("rep != ports - distinct hexagons")
            if bad:
                stats["violations"] += 1
                if len(ex) < 4:
                    ex.append(dict(m=m, hexa=hexa, lab=list(lab), broke=bad))
    return stats


def main():
    t0 = time.time()
    out = {"structural": [], "arithmetic": [], "disjointness": [],
           "ablations": []}
    for m in range(1, 6):
        st, ex = Counter(), []
        structural(m, st, ex)
        out["structural"].append(dict(m=m, cases=st["cases"],
                                      violations=st["violations"],
                                      examples=ex))
        print(f"  structural m={m}: {st['cases']:,} cases, "
              f"{st['violations']} violations", flush=True)
    for m in range(1, 8):
        st, ex = Counter(), []
        disjointness(m, st, ex)
        out["disjointness"].append(dict(m=m, cases=st["cases"],
                                        violations=st["violations"],
                                        with_adjacent_AB=st["with_adjacent_AB"],
                                        examples=ex))
        print(f"  disjointness m={m}: {st['cases']:,} cases, "
              f"{st['violations']} violations, adjacent A/B in "
              f"{st['with_adjacent_AB']:,}", flush=True)
    for B in (4, 6, 8):
        st, ex = arith_box(B)
        out["arithmetic"].append(dict(box=B, cases=st["cases"],
                                      violations=st["violations"],
                                      example=ex))
        print(f"  arithmetic box<= {B}: {st['cases']:,} cases, "
              f"{st['violations']} violations", flush=True)
    for hyp in ("H1", "H2", "H3", "H5"):
        st, ex = arith_box(5, ablate=hyp)
        which = {k[2:]: v for k, v in st.items() if k.startswith("v_")}
        out["ablations"].append(dict(dropped=hyp, cases=st["cases"],
                                     violations=st["violations"],
                                     which=which, example=ex,
                                     as_expected=st["violations"] > 0))
        print(f"  ablate {hyp}: {st['cases']:,} cases, {st['violations']} "
              f"violations {which}", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    out["structural_cases"] = sum(e["cases"] for e in out["structural"])
    out["disjointness_cases"] = sum(e["cases"] for e in out["disjointness"])
    out["arithmetic_cases"] = sum(e["cases"] for e in out["arithmetic"])
    out["ok"] = (all(e["violations"] == 0 for e in out["structural"])
                 and all(e["violations"] == 0 for e in out["disjointness"])
                 and any(e["with_adjacent_AB"] for e in out["disjointness"])
                 and all(e["violations"] == 0 for e in out["arithmetic"])
                 and all(a["as_expected"] for a in out["ablations"]))
    (ROOT / "r158" / "certs" / "abstract_158.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    print("structural", out["structural_cases"],
          "disjointness", out["disjointness_cases"],
          "arithmetic", out["arithmetic_cases"], "ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
