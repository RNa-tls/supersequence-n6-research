#!/usr/bin/env python3
"""Round 156 Phase 11 -- adversarial work against the reconstructed theorem.

Three things:

 (1) JOINT FEATURE COVERAGE.  A claim that holds only on easy covers is not
     worth much.  Every combination of the risk features
       c>0 (pure circuits), d>0 (extra components), h>0 (heavy joints),
       D2>0 (type A), Qs>0 (type B), sigma>0, multi-chain, e>0
     that the corpus realises is tabulated, so the gaps are visible.

 (2) MUTATION OF THE CLAIMS.  Each claim constant is perturbed by one unit and
     the corpus is asked whether it notices.  A claim nothing can falsify is
     not being tested.  The mutation that matters most is M1: Claim 1 off by
     one, which is exactly the error the WRITTEN recipe makes by leaving the
     dummy inside a chain.

 (3) MUTATION OF THE CATALOGUE HYPOTHESES.  The type labels are corrupted so
     that a "type A" edge no longer lands in its source's hexagon, and the
     Claim-5 bookkeeping is asked whether it notices.
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

FEATURES = ("c", "d", "h", "D2", "Qs", "sigma", "multi_chain", "e")


def feature_key(r):
    return tuple(int(bool(r["chains"] > 1 if f == "multi_chain" else r[f]))
                 for f in FEATURES)


MUTATIONS = {
    "M1_required_plus_1":  lambda r: r["sum_P"] != r["required"] + 1,
    "M1b_required_minus_1": lambda r: r["sum_P"] != r["required"] - 1,
    "M2_Dsum_plus_1":      lambda r: r["sum_D"] != r["D_sum"] + 1,
    "M3_bsum_plus_1":      lambda r: r["sum_tok"] != r["b_sum"] + 1,
    "M3b_bsum_minus_1":    lambda r: r["sum_tok"] != r["b_sum"] - 1,
    "M4_chains_le_d_plus_h": lambda r: r["chains"] > r["d"] + r["h"],
    "M5_e_le_Z_minus_Qs_minus_1":
        lambda r: r["e"] > max(0, r["Z"] - r["Qs"] - 1),
    "M6_a_le_D2_minus_1":  lambda r: r["a"] > max(0, r["D2"] - 1),
    "M7_rep_le_R_int_minus_1": lambda r: r["hex_repeats"] > r["R_int"] - 1,
    "M8_sigma_le_Bstar_minus_1": lambda r: r["sigma"] > r["Bstar"] - 1,
    "M9_abe_le_2g_minus_1": lambda r: r["a"] + r["bb"] + r["e"] > 2 * r["g"] - 1,
}


def corrupt_types(st, rng):
    """Relabel one non-E edge as 'A' even though its target is in a different
    hexagon -- i.e. break the catalogue property Claim 5 leans on."""
    cand = [x for x, t in st["etype"].items()
            if t not in ("E", "A", "B")
            and st["hexr"][st["beta"][x]] != st["hexr"][x]]
    if not cand:
        return None
    x = rng.choice(cand)
    st2 = dict(st)
    st2["etype"] = dict(st["etype"])
    st2["etype"][x] = "A"
    return st2


def main():
    t0 = time.time()
    rng = random.Random(778899)
    ws, w5 = R.words()
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 900))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 400))]

    cover = Counter()
    mut = Counter()
    runs = 0
    corrupt = Counter()
    for tag, n, W in pool:
        st = X.structure(W, n)
        for kh in (False, True):
            for pol in X.POLICIES:
                r = X.extract(st, keep_heavy=kh, policy=pol)
                runs += 1
                cover[feature_key(r)] += 1
                for name, f in MUTATIONS.items():
                    if f(r):
                        mut[name] += 1
        st2 = corrupt_types(st, rng)
        if st2 is not None:
            corrupt["attempts"] += 1
            r2 = X.extract(st2)
            if any((isinstance(f, tuple) and "retained A/B" in str(f[0]))
                   or "retained A/B edge is not a hexagon repeat" in str(f)
                   for f in r2["failures"]):
                corrupt["detected"] += 1
            elif not r2["ok"]:
                corrupt["detected_other"] += 1
            else:
                corrupt["undetected"] += 1

    tab = sorted(((list(k), v) for k, v in cover.items()),
                 key=lambda kv: (-sum(kv[0]), -kv[1]))
    out = dict(seconds=round(time.time() - t0, 1), words=len(pool), runs=runs,
               features=list(FEATURES),
               distinct_feature_patterns=len(cover),
               richest_patterns=tab[:12],
               mutation_detections={k: mut.get(k, 0) for k in MUTATIONS},
               undetected_mutations=[k for k in MUTATIONS if not mut.get(k)],
               catalogue_corruption=dict(corrupt))
    out["ok"] = (not out["undetected_mutations"]
                 and corrupt["undetected"] == 0 and corrupt["attempts"] > 0)
    (ROOT / "r156" / "certs" / "adversarial_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:3000])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
