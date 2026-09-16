#!/usr/bin/env python3
"""Round 156 Phase 5 -- the WRITTEN recipe against the IMPLEMENTED recipe.

The extraction is stated twice in the corpus:

  src/l6_extraction_145.py, lines 18-22
    "Delete the c pure circuits.  The remaining K - c = d + 1 beta components
     are cycles; open each at one non-E edge (a nonpure cycle has one by
     definition).  Then cut the h heavy joints. ... the result is d + 1 + h
     paths"

  r149/PROOF.md section 3, steps 3-5
    same wording in Korean.

Exactly one of the d + 1 components contains the DUMMY vertex.  The dummy is
not a pass: it owns no port, no orbit and no hexagon.  The implementation
opens that component by DELETING THE DUMMY VERTEX, not at a non-E edge -- and
it performs only d openings, not d + 1.  This file measures the difference:

  impl     the implemented recipe (d openings, dummy deleted)
  proseA   the literal recipe -- also open the dummy component at a non-E edge,
           then drop the dummy because it is not a port
  proseB   the literal recipe with the dummy left inside the chain as if it
           were a port

and reports, per real cover, whether each still satisfies Claim 1 and the
chain-count bound #chains <= d + 1 + h that the capacity models consume.
It also asks whether the dummy component can fail to HAVE a non-E edge, which
would make the written recipe not merely off by one but unexecutable.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402


def variants(st, keep_heavy=False):
    n, P, beta, dummy = st["n"], st["P"], st["beta"], st["dummy"]
    etype, eweight, orbr = st["etype"], st["eweight"], st["orbr"]
    r = n - 1
    comps = X.components(beta)
    pure = [c for c in comps if dummy not in c
            and all(etype.get(x) == "E" for x in c)]
    purevs = {x for c in pure for x in c}
    cc, K = len(pure), len(comps)
    d = K - 1 - cc
    h = sum(1 for w in eweight.values() if w >= 4)
    star = next(c for c in comps if dummy in c)
    star_nonE = [x for x in star if etype.get(x) not in (None, "E")]

    def chains_of(cut, drop_dummy):
        succ = {}
        rng = range(P) if drop_dummy else range(P + 1)
        for x in rng:
            if x in purevs or x in cut:
                continue
            y = beta[x]
            if y in purevs or (drop_dummy and y == dummy):
                continue
            succ[x] = y
        indeg = Counter(succ.values())
        out, used = [], set()
        for s in rng:
            if s in purevs or indeg.get(s):
                continue
            ch, x = [], s
            while True:
                ch.append(x)
                used.add(x)
                if x not in succ:
                    break
                x = succ[x]
            out.append(ch)
        full = (set(rng) - purevs)
        return out, (used == full)

    heavy = set() if keep_heavy else {x for x, w in eweight.items() if w >= 4}
    op = []
    for c in comps:
        if dummy in c or c in pure:
            continue
        op.append(next(x for x in c if etype.get(x) not in (None, "E")))
    res = {}
    # impl -----------------------------------------------------------------
    ch, okpart = chains_of(set(op) | heavy, True)
    res["impl"] = dict(chains=len(ch), sumP=sum(len(x) for x in ch),
                       partition=okpart)
    # proseA ---------------------------------------------------------------
    if star_nonE:
        ch, okpart = chains_of(set(op) | {star_nonE[0]} | heavy, True)
        res["proseA"] = dict(chains=len(ch), sumP=sum(len(x) for x in ch),
                             partition=okpart)
    else:
        res["proseA"] = dict(chains=None, note="dummy component has no non-E "
                             "edge: the written recipe cannot be carried out")
    # proseB ---------------------------------------------------------------
    if star_nonE:
        ch, okpart = chains_of(set(op) | {star_nonE[0]} | heavy, False)
        res["proseB"] = dict(chains=len(ch), sumP=sum(len(x) for x in ch),
                             partition=okpart,
                             dummy_inside_a_chain=any(dummy in x for x in ch))
    else:
        res["proseB"] = dict(chains=None)
    res["bound"] = d + 1 + (0 if keep_heavy else h)
    res["required_sumP"] = P - r * cc
    res["d"], res["h"], res["c"], res["K"] = d, h, cc, K
    res["star_all_E"] = not star_nonE
    return res


def main():
    t0 = time.time()
    rng = random.Random(9091)
    ws, w5 = R.words()
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 800))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 350))]
    tally = Counter()
    samples = {"proseA_over_bound": [], "star_all_E": [], "proseB_bad_sumP": []}
    for tag, n, W in pool:
        st = X.structure(W, n)
        for kh in (False, True):
            v = variants(st, kh)
            tally["cases"] += 1
            if v["star_all_E"]:
                tally["star_all_E"] += 1
                if len(samples["star_all_E"]) < 4:
                    samples["star_all_E"].append(dict(tag=tag, n=n, v=v))
            if v["impl"]["chains"] > v["bound"] or \
                    v["impl"]["sumP"] != v["required_sumP"] or \
                    not v["impl"]["partition"]:
                tally["impl_broken"] += 1
            a = v["proseA"]
            if a["chains"] is not None:
                tally["proseA_cases"] += 1
                if a["chains"] > v["bound"]:
                    tally["proseA_over_bound"] += 1
                    if len(samples["proseA_over_bound"]) < 4:
                        samples["proseA_over_bound"].append(
                            dict(tag=tag, n=n, keep_heavy=kh, v=v))
                if a["sumP"] != v["required_sumP"]:
                    tally["proseA_bad_sumP"] += 1
            b = v["proseB"]
            if b["chains"] is not None:
                tally["proseB_cases"] += 1
                if b["sumP"] != v["required_sumP"]:
                    tally["proseB_bad_sumP"] += 1
                    if len(samples["proseB_bad_sumP"]) < 3:
                        samples["proseB_bad_sumP"].append(
                            dict(tag=tag, n=n, keep_heavy=kh, v=v))
                if b.get("dummy_inside_a_chain"):
                    tally["proseB_dummy_in_chain"] += 1
    out = dict(seconds=round(time.time() - t0, 1), words=len(pool),
               tally=dict(tally), samples=samples,
               verdict=dict(
                   implementation_sound=(tally["impl_broken"] == 0),
                   written_recipe_exceeds_the_model_chain_bound=
                   tally["proseA_over_bound"] > 0,
                   written_recipe_miscounts_ports=tally["proseB_bad_sumP"] > 0,
                   written_recipe_sometimes_unexecutable=
                   tally["star_all_E"] > 0))
    (ROOT / "r156" / "certs" / "prose_vs_impl_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "samples"},
                     ensure_ascii=False, indent=1))
    for k, v in out["samples"].items():
        if v:
            print(k, json.dumps(v[0], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
