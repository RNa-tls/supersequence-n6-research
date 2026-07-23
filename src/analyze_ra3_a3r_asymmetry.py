#!/usr/bin/env python3
"""RA3 vs A3R order-asymmetry: a single interaction theorem, not two
separate case analyses.

Theorem (F-budget/fragment order-lock). In the F<=1, H=0 slab, the
corpus's own ``fragment_hex`` (exact.f1_normal_form) is, by construction,
"the unique NON-CURRENT partial hexagon" -- it can be non-None at some
point of a walk only if an earlier joint in that SAME walk already
abandoned a hexagon (F: 0->1). The model enforces F<=1 (at most one
abandonment ever), and there are exactly four abandoning joint kinds:
A2, A3, J (all positive-charge / "defect" events) and Z2_abandon_w2_new
(weight-2, abandonment=True, new_orbit=True -- ZERO-charge, i.e. NOT
counted as one of a word's defect events).

Consequence for a two-event U-branch word W1 W2:
  - If W2 is itself abandoning (A2 or A3 -- i.e. words RA2, RA3), then W2
    IS the walk's one allowed abandonment, so NO earlier abandoning joint
    (including a hidden zero-charge Z2_abandon) can have fired before it.
    fragment_hex is therefore forced to be None at every point strictly
    before W2 -- in particular at W1 too. This is not an empirical
    tendency, it follows deductively from F<=1 plus the definition of
    fragment_hex.
  - If W1 is itself abandoning (A3R), a fragment exists from immediately
    after W1 fires onward, unless/until intervening zero-charge joints
    complete it back to FULL before W2 fires.
  - If NEITHER event abandons (RR), the F budget stays fully available
    throughout, so a hidden zero-charge Z2_abandon MAY optionally fire at
    any point -- producing genuine, unforced heterogeneity in both slots.

This script re-derives the prediction table from the theorem and checks
it against the corpus's own exact fragment_relation counts (all 4 words,
full corpus, no sampling), then spot-verifies the mechanism by literal
replay on a small sample of RR states with a resolved second-slot
fragment_relation, confirming a Z2_abandon (zero-charge, abandoning) event
appears in their macro path before the state where fragment_relation was
evaluated.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_LEGACY = ROOT / "legacy_research" / "outputs"
WORK = ROOT / "legacy_research" / "work"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(ROOT / "src"))
import analyze_u_branch as ub  # noqa: E402

macro = ub.macro
exact = ub.exact
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1_MOVE = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def load_records() -> List[Dict[str, Any]]:
    data = json.loads((OUTPUTS_LEGACY / "f1_n2_defect_words.json").read_text(encoding="utf-8"))
    return data["area_a_depth6"]["state_records"]


def fragment_relation_table(records: List[Dict[str, Any]], words: List[str]) -> Dict[str, Any]:
    out = {}
    for word in words:
        recs = [r for r in records if r["word"] == word]
        slot0 = Counter(r["fragment_relation"][0] for r in recs)
        slot1 = Counter(r["fragment_relation"][1] for r in recs)
        out[word] = {
            "total": len(recs),
            "slot0_distribution": dict(slot0),
            "slot1_distribution": dict(slot1),
            "slot0_always_no_observable_fragment": set(slot0) == {"no_observable_fragment"},
            "slot1_always_no_observable_fragment": set(slot1) == {"no_observable_fragment"},
        }
    return out


def theorem_predictions() -> Dict[str, str]:
    return {
        "RA2": "W2=A2 abandons => fragment forced None at BOTH slots (100% no_observable_fragment, both slots)",
        "RA3": "W2=A3 abandons => fragment forced None at BOTH slots (100% no_observable_fragment, both slots)",
        "A3R": "W1=A3 abandons => fragment exists from after W1 onward; slot0 still forced None (nothing abandoned yet before W1); slot1 mostly resolved, occasionally reverts to none if the fragment gets completed before W2",
        "RR": "neither event abandons => F budget free throughout => a hidden zero-charge Z2_abandon MAY fire anywhere => genuine heterogeneity possible in BOTH slots",
    }


def check_predictions(table: Dict[str, Any]) -> Dict[str, Any]:
    checks = {
        "RA2_both_slots_forced_none": table["RA2"]["slot0_always_no_observable_fragment"] and table["RA2"]["slot1_always_no_observable_fragment"],
        "RA3_both_slots_forced_none": table["RA3"]["slot0_always_no_observable_fragment"] and table["RA3"]["slot1_always_no_observable_fragment"],
        "A3R_slot0_forced_none": table["A3R"]["slot0_always_no_observable_fragment"],
        "A3R_slot1_mostly_resolved": (1 - table["A3R"]["slot1_distribution"].get("no_observable_fragment", 0) / table["A3R"]["total"]) > 0.9,
        "RR_slot0_heterogeneous": not table["RR"]["slot0_always_no_observable_fragment"],
        "RR_slot1_heterogeneous": not table["RR"]["slot1_always_no_observable_fragment"],
    }
    checks["all_predictions_confirmed"] = all(checks.values())
    return checks


def literal_mechanism_spotcheck(checkpoint_path: str, sample_size: int) -> Dict[str, Any]:
    """For RR states with a resolved 2nd-slot fragment_relation, replay the
    literal macro path and confirm a Z2abandon event kind appears somewhere
    before the 2nd R (proving the mechanism, not just the correlation)."""
    ckpt = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
    node_records = ckpt["node_records"]
    records = load_records()
    rr = [r for r in records if r["word"] == "RR"]
    resolved = [r for r in rr if r["fragment_relation"][1] != "no_observable_fragment"]

    checked = 0
    z2abandon_before_second_r = 0
    samples = []
    for r in resolved[:sample_size]:
        h = r["state_hash"]
        w = ub.backtrack_witness(node_records, h)
        if w is None:
            continue
        checked += 1
        cur = exact.canonicalize(exact.initial_state())
        kinds = []
        for step in w["macro_path"]:
            rot_part, joint_part = step["edge_label"].split(";")
            ell = int(rot_part[len("rot^"):])
            for _ in range(ell):
                tr = exact.extend(cur, W1_MOVE)
                cur = tr.state
            move = move_by_label[joint_part]
            tr = exact.extend(cur, move)
            cur = exact.canonicalize(tr.state)
            kinds.append(joint_kind(move.weight, tr.abandonment, tr.new_orbit))
        r_positions = [i for i, k in enumerate(kinds) if k == "R"]
        if len(r_positions) != 2:
            continue
        before_second_r = kinds[: r_positions[1]]
        has_z2abandon = "Z2abandon" in before_second_r
        if has_z2abandon:
            z2abandon_before_second_r += 1
        samples.append({"hash": h[:12], "kinds": kinds, "z2abandon_before_second_r": has_z2abandon})
    return {
        "resolved_slot1_rr_states_total": len(resolved),
        "sample_checked": checked,
        "z2abandon_confirmed_before_second_r": z2abandon_before_second_r,
        "mechanism_confirmed_rate": z2abandon_before_second_r / checked if checked else None,
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra3_a3r_asymmetry.json"))
    args = parser.parse_args()

    records = load_records()
    words = ["RA2", "RA3", "A3R", "RR"]
    table = fragment_relation_table(records, words)
    predictions = theorem_predictions()
    checks = check_predictions(table)
    mechanism = literal_mechanism_spotcheck(args.checkpoint, args.sample_size)

    report = {
        "schema": "ra3-a3r-asymmetry-v1",
        "theorem": (
            "fragment_hex (exact.f1_normal_form) can be non-None at a point "
            "of a walk only if an earlier joint in the same walk already "
            "abandoned a hexagon. F<=1 allows at most one abandonment total. "
            "So if a word's SECOND event is itself abandoning (RA2, RA3), no "
            "earlier abandonment (visible or the hidden zero-charge "
            "Z2_abandon_w2_new) can have fired -- fragment_hex is forced None "
            "at every point up to and including just before that second "
            "event. This is a deductive consequence of the model's F<=1 "
            "constraint, not an empirical regularity."
        ),
        "predictions": predictions,
        "fragment_relation_table_full_corpus": table,
        "prediction_checks_against_full_corpus": checks,
        "literal_mechanism_spotcheck_on_RR": mechanism,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "all_predictions_confirmed": checks["all_predictions_confirmed"],
        "mechanism_confirmed_rate": mechanism["mechanism_confirmed_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
