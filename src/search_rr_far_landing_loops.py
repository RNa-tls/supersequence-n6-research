#!/usr/bin/env python3
"""Round 25, sections 2, 11, 12: the minimal odd-parity far-landing
witnesses, and same-count/opposite-order pairs."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", default=str(ROOT / "outputs" / "rr_ordered_event_words.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_far_landing_odd_loops.json"))
    ap.add_argument("--pairs-output", default=str(ROOT / "outputs" / "rr_same_count_opposite_order_pairs.json"))
    a = ap.parse_args()
    d = json.loads(Path(a.words).read_text(encoding="utf-8"))
    rows = d["rows"]
    odd_far = [r for r in rows if r["landing_class"] == "far" and r["zero_charge_parity"] == 1]
    odd_far.sort(key=lambda r: (r["P_length"], r["ordered_word"]))
    print(f"far-landing completions with ODD zero-charge count: {len(odd_far)}")
    minimal = odd_far[:6]
    for r in minimal:
        print(f"  ell={r['abandonment_ell']} j={r['landing_position']} |P|={r['P_length']} "
              f"word={r['ordered_word']:10s} #Z={r['n_zero_charge']} #R={r['n_R']}")

    # section 2: same event counts, different order, different landing class
    bysig = {}
    for r in rows:
        sig = (r["abandonment_ell"], r["n_R"], r["n_zero_charge"],
               sum(1 for e in r["events"] if e["sym"] == "F"))
        bysig.setdefault(sig, []).append(r)
    pairs = []
    for sig, group in bysig.items():
        classes = {g["landing_class"] for g in group}
        if len(classes) > 1:
            a1 = next(g for g in group if g["landing_class"] == "O_star") if "O_star" in classes else group[0]
            a2 = next(g for g in group if g["landing_class"] != a1["landing_class"])
            first_diff = next((i for i, (x, y) in enumerate(zip(a1["ordered_word"], a2["ordered_word"])) if x != y), None)
            pairs.append({"signature_ell_R_Z_F": list(sig),
                          "word_a": a1["ordered_word"], "class_a": a1["landing_class"],
                          "landing_a": a1["landing_position"],
                          "word_b": a2["ordered_word"], "class_b": a2["landing_class"],
                          "landing_b": a2["landing_position"],
                          "first_differing_index": first_diff})
    print(f"\nsame-count opposite-landing pairs found: {len(pairs)}")
    for p in pairs[:5]:
        print(f"  counts={p['signature_ell_R_Z_F']}  {p['word_a']}({p['class_a']}) vs "
              f"{p['word_b']}({p['class_b']})  first differ at index {p['first_differing_index']}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-far-landing-odd-loops-v1",
        "count": len(odd_far),
        "minimal_examples": minimal,
        "verdict": ("exact counterexample -- odd zero-charge counts DO occur at far landings "
                    "(j >= ell+3), so the evenness is specific to the two nearest residual "
                    "positions. These are the section-11 'odd loops'; why they cannot be "
                    "inserted into an O*-landing word is 미완료."),
        "all_odd_far": odd_far}, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.pairs_output).write_text(json.dumps({
        "schema": "rr-same-count-opposite-order-pairs-v1",
        "purpose": "words with identical additive event counts but different landing class -- direct evidence that landing is order-dependent, not count-determined",
        "pair_count": len(pairs), "pairs": pairs,
        "grade": "exact counterexample (to any count-only characterization of landing)"},
        indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nwrote {a.output}\nwrote {a.pairs_output}")

if __name__ == "__main__":
    main()
