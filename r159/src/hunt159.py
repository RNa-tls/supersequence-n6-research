#!/usr/bin/env python3
"""Round 159 Phase 5/11 -- targeted hunt for the configurations the ordinary
corpus does not produce.

Looked for:
  * a (hexagon, beta-component) group carrying TWO OR MORE type A/B edges
    (the only case where the counting lemma's `m - 1` does more than bound 1);
  * ADJACENT dirty beta-edges  p -> q -> r  with both typed A or B, in all four
    orders AB, BA, AA, BB;
  * several dirty events inside one beta-component;
  * words where D2 + Qs exceeds the POST-CUT repeat count `rep`, which is what
    decides whether SAME-HEX is a corollary of the Extraction Theorem.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402
from samehex159 import samehex                                    # noqa: E402


def patterns(st):
    beta, etype, hexr, dummy = (st["beta"], st["etype"], st["hexr"],
                                st["dummy"])
    P = st["P"]
    comps = X.components(beta)
    compof = {q: i for i, cy in enumerate(comps) for q in cy}
    ab = {p: t for p, t in etype.items() if t in ("A", "B")}
    grp = Counter()
    for p in ab:
        grp[(hexr[p], compof[p])] += 1
    adj = Counter()
    for p, t in ab.items():
        q = beta[p]
        if q in ab:
            adj[t + ab[q]] += 1
    percomp = Counter()
    for p in ab:
        percomp[compof[p]] += 1
    return dict(max_group=max(grp.values()) if grp else 0,
                adj=dict(adj),
                max_per_component=max(percomp.values()) if percomp else 0)


def main(budget_min=14):
    t0 = time.time()
    rng = random.Random(20260917)
    _, w5 = R.words()
    tally, best, fails = Counter(), {}, []
    rounds = 0
    while time.time() - t0 < budget_min * 60:
        rounds += 1
        words = ([(4, w) for w in C.corpus(4, "1234", [R.W4], rng, 700)]
                 + [(5, w) for w in C.corpus(5, "01234", w5, rng, 350)])
        for n, w in words:
            try:
                st = X.structure(w, n)
            except ValueError:
                continue
            r = samehex(st)
            tally["words"] += 1
            if not r["ok"]:
                tally["failures"] += 1
                if len(fails) < 6:
                    fails.append(dict(n=n, word=w, failures=r["failures"][:5]))
            pat = patterns(st)
            tally[f"max_group_{min(pat['max_group'], 4)}"] += 1
            for k, v in pat["adj"].items():
                tally["adj_" + k] += v
                if k not in best:
                    best[k] = dict(n=n, word=w, D2=r["D2"], Qs=r["Qs"],
                                   R_int=r["R_int"], two_g=r["two_g"],
                                   ok=r["ok"])
            if pat["max_group"] >= 2 and "group>=2" not in best:
                best["group>=2"] = dict(n=n, word=w, max_group=pat["max_group"],
                                        D2=r["D2"], Qs=r["Qs"],
                                        R_int=r["R_int"], ok=r["ok"])
            if pat["max_per_component"] >= 2 and "comp>=2" not in best:
                best["comp>=2"] = dict(n=n, word=w,
                                       per_comp=pat["max_per_component"],
                                       D2=r["D2"], Qs=r["Qs"],
                                       R_int=r["R_int"], ok=r["ok"])
            if r["D2Qs_exceeds_postcut_rep"]:
                tally["D2Qs_gt_rep"] += 1
                gap = r["D2"] + r["Qs"] - r["rep"]
                tally["max_D2Qs_minus_rep"] = max(
                    tally["max_D2Qs_minus_rep"], gap)
                if "D2Qs_gt_rep" not in best:
                    best["D2Qs_gt_rep"] = dict(n=n, word=w, D2=r["D2"],
                                               Qs=r["Qs"], rep=r["rep"],
                                               R_int=r["R_int"], d=r["d"])
            tally["max_D2"] = max(tally["max_D2"], r["D2"])
            tally["max_Qs"] = max(tally["max_Qs"], r["Qs"])
            tally["max_R_int"] = max(tally["max_R_int"], r["R_int"])
            if r["tight_lower"]:
                tally["tight_lower"] += 1
    out = dict(seconds=round(time.time() - t0, 1), rounds=rounds,
               tally=dict(tally), examples=best, failures=fails,
               ok=(tally["failures"] == 0))
    (ROOT / "r159" / "certs" / "hunt_159.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "examples"},
                     ensure_ascii=False, indent=1)[:2500])
    print("examples:", json.dumps(sorted(best), ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 14))
