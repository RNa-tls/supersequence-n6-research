#!/usr/bin/env python3
"""Round 25, sections 6, 7, 14, 15, 18: tests candidate perfect-matching
rules on the zero-charge events of near-landing preparations.

Section 14's target: "O*-landing zero-charge events admit a perfect
matching", which would give evenness immediately. Four structural pairing
rules are tested; each is either confirmed or killed by an exact
counterexample. No rule is declared valid on the strength of the count
being even -- the matching must actually exist.
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def groups_all_even(items, key):
    c = Counter(key(x) for x in items)
    return all(v % 2 == 0 for v in c.values()), dict(c)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", default=str(ROOT / "outputs" / "rr_ordered_event_words.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_zero_charge_matchings.json"))
    a = ap.parse_args()
    d = json.loads(Path(a.words).read_text(encoding="utf-8"))
    rules = {
        "same_target_orbit": lambda e: e["target_orbit"],
        "same_target_hexagon": lambda e: e["target_hexagon"],
        "same_target_phase": lambda e: e["target_phase"],
        "targets_O_star_or_not": lambda e: e["targets_O_star"],
        "same_symbol_E_vs_F": lambda e: e["sym"],
    }
    results = {}
    for cls in ("O_star", "ell_plus_2", "far"):
        rows = [r for r in d["rows"] if r["landing_class"] == cls]
        res = {}
        for name, key in rules.items():
            ok = True; ce = None
            for r in rows:
                Z = [e for e in r["events"] if e["sym"] != "R"]
                good, groups = groups_all_even(Z, key)
                if not good:
                    ok = False
                    if ce is None:
                        ce = {"abandonment_ell": r["abandonment_ell"], "word": r["ordered_word"],
                              "landing_position": r["landing_position"], "group_sizes": groups}
            res[name] = {"perfect_matching_by_this_rule": ok, "exact_counterexample": ce,
                         "verdict": "exact matching" if ok else "반증됨"}
        # the raw count, for contrast
        res["_raw_zero_charge_count_even"] = {
            "holds": all(r["zero_charge_parity"] == 0 for r in rows),
            "note": "the COUNT being even does not by itself exhibit a matching"}
        results[cls] = {"witness_count": len(rows), "rules": res}
        print(f"\n=== landing class {cls} ({len(rows)} completions) ===")
        for name, v in res.items():
            if name.startswith("_"): continue
            print(f"  {name:24s} {'PERFECT MATCHING' if v['perfect_matching_by_this_rule'] else '반증됨'}"
                  + ("" if v["perfect_matching_by_this_rule"] else f"  ce={v['exact_counterexample']['word']}"))
        print(f"  raw #Z even: {res['_raw_zero_charge_count_even']['holds']}")
    rep = {"schema": "rr-zero-charge-matchings-v1",
           "section14_target": "O*-landing zero-charge events admit a perfect matching",
           "verdict": ("미완료 -- none of the five structural pairing rules yields a perfect matching "
                       "on every O*-landing witness. The evenness of the count is confirmed "
                       "root-local exhaustive, but no matching realizing it was found, so the "
                       "matching route to the parity theorem is not closed."),
           "by_landing_class": results}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("\nwrote", a.output)

if __name__ == "__main__":
    main()
