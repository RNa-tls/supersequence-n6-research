#!/usr/bin/env python3
"""L6 endgame round 144 — the end-to-end verdict script.

It reruns the whole chain and prints what is and is not established:

  1. the identity checks (FO, MASTER-142, the extraction bookkeeping);
  2. the geometric lemmas (joint catalogue, companion hexagon, mixed shadow,
     left S6 symmetry, incidence theorem);
  3. the row evaluation for L = 867..871 under the three upper-bound models,
     combined the sound way (max over each model's own s, then min over models);
  4. for every row the models leave at EQUALITY, the exhaustive equality-witness
     enumeration and the pure-E-circuit coexistence test.

It does NOT assert L6 = 872, and it does not re-audit the Round-142 hand
reductions it stands on (see the report's limitations section).
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
WIT = ROOT / "outputs" / "witness_144"

# the two equality rows and the searcher arguments that enumerate their witnesses
EQ_ROWS = {
    "Q1": dict(row=dict(k=4, Z=0, H=0, Bstar=0, G=6, g=0, c=6, d=0, D2=0, Qs=0,
                        h=0, s=0),
               required=96, ports=96, deficit=14, heavy=0, c=6,
               witness="wit_Q1.jsonl"),
    "Q2": dict(row=dict(k=3, Z=0, H=1, Bstar=0, G=7, g=0, c=7, d=0, D2=0, Qs=0,
                        h=1, s=0),
               required=92, ports=92, deficit=8, heavy=1, c=7,
               witness="wit_Q2.jsonl"),
}


def main():
    import l6_master_identity_144 as MI
    import l6_bookkeeping_144 as BK
    import l6_marked_capacity_144 as MC
    import l6_incidence_144 as IN
    import l6_coupled_144 as PIECE
    import l6_chain_rows_144 as CR
    import l6_871_analysis_144 as AN
    import l6_rows_final_144 as RF
    import l6_circuit_coexist_144 as CO
    import l6_coexist_check3_144 as CO3

    out = {"disclaimer":
           "Upper-bound (relaxed) models plus one exhaustive witness analysis. "
           "This script does NOT re-audit the Round-142 hand reductions it "
           "stands on, and it does not assert L6 = 872."}
    out["identities"] = dict(
        master=MI.symbolic_check()["mismatches"] == 0,
        fo=MI.fo_identity_from_word_level()["mismatches"] == 0,
        bookkeeping=BK.check(50000)["holds"])
    out["lemmas"] = dict(
        joint_catalogue=MC.catalogue_check()["holds"],
        companion_hex=MC.companion_lemma()["holds"],
        mixed_shadow=MC.shadow_theorem()["holds"],
        left_S6=MC.s6_symmetry()["holds"],
        incidence=IN.check(2000)["holds"])

    PIECE.load_caps()
    CR.load_cache()
    AN.load_h()
    rows = {}
    for t in range(0, 5):
        r = RF.run(t, allow_compute=False)
        rows[f"L{867 + t}"] = dict(
            coordinate_rows=r["coordinate_rows"], strict=r["strict"],
            surviving=r["surviving"],
            surviving_with_fallback=r["surviving_with_fallback"],
            survivors=[{k: x[k] for k in ("k", "Z", "H", "Bstar", "G", "c", "d",
                                          "D2", "h", "required", "bound",
                                          "verdict")} for x in r["survivors"]])
    out["rows"] = rows

    eq = {}
    for tag, spec in EQ_ROWS.items():
        wf = WIT / spec["witness"]
        chains = [json.loads(l)["ports"] for l in wf.read_text().splitlines()
                  if l.strip()]
        d1 = [CO.coexist(ch, spec["c"]) for ch in chains]
        d3 = [CO3.solve(ch, spec["c"]) for ch in chains]
        eq[tag] = dict(required=spec["required"], ports=spec["ports"],
                       deficit=spec["deficit"], heavy=spec["heavy"], c=spec["c"],
                       witnesses=len(chains),
                       coexist_dfs_any=any(x["ok"] for x in d1),
                       coexist_subset_any=any(x["ok"] for x in d3),
                       excluded=not (any(x["ok"] for x in d1) or
                                     any(x["ok"] for x in d3)))
    out["equality_rows"] = eq

    all_closed = all(v["surviving"] == 0 for k, v in rows.items()
                     if k != "L871")
    l871_left = rows["L871"]["surviving"]
    l871_excluded = (l871_left == len(EQ_ROWS)
                     and all(v["excluded"] for v in eq.values())
                     and rows["L871"]["surviving_with_fallback"] == 0)
    out["summary"] = dict(
        rows_867_870_all_strict=all_closed,
        L871_equality_rows=l871_left,
        L871_equality_rows_excluded_by_witnesses=l871_excluded,
        every_length_up_to_871_excluded=(all_closed and l871_excluded),
        note="'excluded' means excluded inside the stated relaxations, given "
             "the Round-142 first-occurrence framework.  NR6 is NOT used.")
    (ROOT / "outputs" / "rr_l6_final_144.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    for k, v in rows.items():
        print(k, json.dumps({x: v[x] for x in
                             ("coordinate_rows", "strict", "surviving")}))


if __name__ == "__main__":
    main()
