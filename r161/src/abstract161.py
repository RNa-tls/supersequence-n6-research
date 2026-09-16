#!/usr/bin/env python3
"""Round 161 Phases 17/20 -- abstract falsification and hypothesis necessity.

Three finite universes, each completely specified, plus ablations.

U-E  LEMMA E.  Vertices {0..m-1} forming ONE cycle under a successor map,
     a phase labelling ph: V -> Z/r, and an edge labelling in {E, nonE} with
        (e1) an E edge satisfies ph(target) = ph(source) + 1 (mod r).
     Hypotheses that may be ablated:
        (e2) the phases of the cycle's vertices are DISTINCT
             (in the real object: pass entries are distinct selected windows)
     Claim: an all-E cycle has length exactly r and its phases are all of Z/r.
     Universe at (m, r): r^m phase labellings x 2^m edge labellings, all
     enumerated.

U-F  LEMMA F.  A permutation beta of {0..m-1} together with a subset E of its
     edges.  Claim: P - |E| equals the number of PATH components of the E
     subgraph (cycles contribute 0), and deleting an all-E cycle -- its r
     vertices and its r E edges -- leaves that number unchanged.
     Universe at m: m! permutations x 2^m edge subsets, all enumerated.

U-A  LEMMA A.  `W is a cover` is ablated by feeding words that are NOT covers
     and checking that a hexagon really can end up with no pass.
"""
from __future__ import annotations
import itertools, json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
sys.path.insert(0, str(HERE))
from lemmas161 import build                                       # noqa: E402


# ------------------------------------------------------------------ Lemma E
def sweep_E(m, r, distinct=True):
    """All phase labellings x all edge labellings on one m-cycle."""
    st, ex = Counter(), []
    succ = [(i + 1) % m for i in range(m)]
    if distinct and m > r:
        # no injective labelling exists; the universe is empty
        return st, ex
    for ph in itertools.product(range(r), repeat=m):
        if distinct and len(set(ph)) != m:
            continue
        for emask in range(1 << m):
            E = {i for i in range(m) if emask >> i & 1}
            # (e1) must hold on every E edge, else the instance is not in U-E
            if any((ph[succ[i]] - ph[i]) % r != 1 for i in E):
                continue
            st["cases"] += 1
            if len(E) != m:                      # not an all-E cycle
                continue
            st["all_E"] += 1
            bad = []
            if m != r:
                bad.append("length != r")
            if set(ph) != set(range(r)):
                bad.append("phases are not all of Z/r")
            if bad:
                st["violations"] += 1
                for b in bad:
                    st["v_" + b] += 1
                if len(ex) < 4:
                    ex.append(dict(m=m, r=r, ph=list(ph), broke=bad))
    return st, ex


# ------------------------------------------------------------------ Lemma F
def path_components(m, succ, E):
    """Components of the E subgraph that are PATHS (cycles excluded)."""
    nxt = {i: succ[i] for i in E}
    indeg = Counter(nxt.values())
    seen, paths = set(), 0
    for s in range(m):
        if indeg.get(s):
            continue
        paths += 1
        x = s
        while True:
            seen.add(x)
            if x not in nxt:
                break
            x = nxt[x]
    return paths, len(seen)


def sweep_F(m, permutation=True):
    st, ex = Counter(), []
    src = (itertools.permutations(range(m)) if permutation
           else itertools.product(range(m), repeat=m))
    for succ in src:
        succ = list(succ)
        for emask in range(1 << m):
            E = {i for i in range(m) if emask >> i & 1}
            st["cases"] += 1
            paths, covered = path_components(m, succ, E)
            blocks = m - len(E)
            bad = []
            if blocks != paths:
                bad.append("P - |E| != #path components")
            # F4: delete an all-E beta cycle
            if permutation:
                cyc = X.components(succ)
                for cy in cyc:
                    if not all(q in E for q in cy):
                        continue
                    keep = [q for q in range(m) if q not in cy]
                    idx = {q: i for i, q in enumerate(keep)}
                    s2 = [idx[succ[q]] for q in keep] if all(
                        succ[q] in idx for q in keep) else None
                    if s2 is None:
                        continue
                    E2 = {idx[q] for q in keep if q in E}
                    p2, _ = path_components(len(keep), s2, E2)
                    if (len(keep) - len(E2)) != blocks or p2 != paths:
                        bad.append("F4 deleting an all-E cycle changed blocks")
            if bad:
                st["violations"] += 1
                for b in bad:
                    st["v_" + b] += 1
                if len(ex) < 4:
                    ex.append(dict(m=m, succ=list(succ), E=sorted(E),
                                   blocks=blocks, paths=paths, broke=bad))
    return st, ex


# ------------------------------------------------------------------ Lemma A
def sweep_A(tries, rng):
    """Words that are NOT covers: does a hexagon lose its pass?"""
    st, ex = Counter(), []
    base = "123412314231243121342132413214321"
    for _ in range(tries):
        w = base
        for _ in range(rng.randint(1, 3)):
            p = rng.randrange(len(w))
            k = rng.randint(1, 6)
            w = w[:p] + w[p + k:]
        if X.is_cover(w, 4, "1234"):
            continue
        st["non_covers"] += 1
        r = build(w, 4, require_cover=False, require_fixed=False)
        f = [str(x) for x in r["failures"]]
        if any("A1" in x for x in f):
            st["A1_detected"] += 1
        if any("A4" in x or "A3" in x for x in f):
            st["hexagon_without_pass_or_broken_arcs"] += 1
            if len(ex) < 3:
                ex.append(dict(word=w[:40], failures=f[:3]))
    return st, ex


def main():
    t0 = time.time()
    rng = random.Random(1611611)
    out = {"lemma_E": [], "lemma_E_ablation": [], "lemma_F": [],
           "lemma_F_ablation": [], "lemma_A_ablation": {}}
    for r in (2, 3, 4, 5):
        for m in range(1, 2 * r + 1):
            st, ex = sweep_E(m, r)
            out["lemma_E"].append(dict(m=m, r=r, cases=st["cases"],
                                       all_E=st["all_E"],
                                       violations=st["violations"],
                                       examples=ex))
    tot = sum(e["cases"] for e in out["lemma_E"])
    vio = sum(e["violations"] for e in out["lemma_E"])
    allE = sum(e["all_E"] for e in out["lemma_E"])
    print(f"  Lemma E: {tot:,} cases ({allE:,} all-E cycles), "
          f"{vio} violations", flush=True)
    for r in (2, 3, 4):
        for m in range(1, min(2 * r, 6) + 1):
            st, ex = sweep_E(m, r, distinct=False)
            out["lemma_E_ablation"].append(dict(m=m, r=r, cases=st["cases"],
                                                all_E=st["all_E"],
                                                violations=st["violations"],
                                                examples=ex[:1]))
    tot2 = sum(e["cases"] for e in out["lemma_E_ablation"])
    vio2 = sum(e["violations"] for e in out["lemma_E_ablation"])
    print(f"  Lemma E, DROP distinctness: {tot2:,} cases, "
          f"{vio2} counterexamples", flush=True)
    for m in range(1, 8):
        st, ex = sweep_F(m)
        out["lemma_F"].append(dict(m=m, cases=st["cases"],
                                   violations=st["violations"], examples=ex))
    tot3 = sum(e["cases"] for e in out["lemma_F"])
    vio3 = sum(e["violations"] for e in out["lemma_F"])
    print(f"  Lemma F: {tot3:,} cases, {vio3} violations", flush=True)
    for m in range(1, 5):
        st, ex = sweep_F(m, permutation=False)
        out["lemma_F_ablation"].append(dict(m=m, cases=st["cases"],
                                            violations=st["violations"],
                                            examples=ex[:1]))
    tot4 = sum(e["cases"] for e in out["lemma_F_ablation"])
    vio4 = sum(e["violations"] for e in out["lemma_F_ablation"])
    print(f"  Lemma F, DROP `beta is a permutation`: {tot4:,} cases, "
          f"{vio4} counterexamples", flush=True)
    st, ex = sweep_A(600, rng)
    out["lemma_A_ablation"] = dict(stats=dict(st), examples=ex)
    print(f"  Lemma A, DROP `W is a cover`: {json.dumps(dict(st))}",
          flush=True)
    out["totals"] = dict(E_cases=tot, E_violations=vio, E_all_E=allE,
                         E_ablation_cases=tot2, E_ablation_counterexamples=vio2,
                         F_cases=tot3, F_violations=vio3,
                         F_ablation_cases=tot4,
                         F_ablation_counterexamples=vio4)
    out["seconds"] = round(time.time() - t0, 1)
    out["ok"] = (vio == 0 and vio3 == 0 and vio2 > 0 and vio4 > 0
                 and st["A1_detected"] > 0)
    (ROOT / "r161" / "certs" / "abstract_161.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    print("ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
