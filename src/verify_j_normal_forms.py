#!/usr/bin/env python3
"""Classification of the 230 recorded J-type states, bounded by what data
actually exists in this corpus.

Honesty note (read this before trusting any grouping below as a "normal
form" in the strict sense): ``legacy_research/outputs/f1_n2_defect_words.json``
records, for all 230 J instances, only:

    state_hash, deficit_phase_type, legal_macro_tail_count,
    global_visited_mask_fingerprint, word

-- the four pairwise-relation fields (component_relation, fragment_relation,
orbit_relation, defect_macro_distance) are ``null`` for J, because those are
defined only for *two*-event words (RR, RA3, A3R, RA2); J is a single event.
No hex/orbit mask, no literal walk, and no fragment descriptor is stored per
J-instance -- only for the ONE literal representative (handled in
``src/analyze_j_completion.py``).

So this script can group the 230 states by ``deficit_phase_type`` and
``legal_macro_tail_count`` (both are real, per-state, exact values on file)
and can confirm those groupings are internally consistent, but it CANNOT
build the requested exact canonical normal form (source/target orbit, split
hexagon position, fragment position, endpoint, open component structure,
visited-mask support, legal-tail signature) for 229 of the 230 states,
because that data was never computed and stored for them individually in
this corpus. That is reported explicitly below, not silently worked around.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "legacy_research" / "outputs"


def load_j_records() -> List[Dict[str, Any]]:
    data = json.loads((OUTPUTS / "f1_n2_defect_words.json").read_text(encoding="utf-8"))
    records = data["area_a_depth6"]["state_records"]
    j_records = [r for r in records if r["word"] == "J"]
    if len(j_records) != 230:
        raise AssertionError(f"expected 230 J records, found {len(j_records)}")
    return j_records


def classify(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_phase: Counter = Counter()
    by_tail_count: Counter = Counter()
    phase_x_tail: Dict[str, Counter] = defaultdict(Counter)
    seen_hashes = set()
    duplicate_hashes = []
    for r in records:
        phase_key = str(tuple(r["deficit_phase_type"]))
        by_phase[phase_key] += 1
        by_tail_count[r["legal_macro_tail_count"]] += 1
        phase_x_tail[phase_key][r["legal_macro_tail_count"]] += 1
        h = r["state_hash"]
        if h in seen_hashes:
            duplicate_hashes.append(h)
        seen_hashes.add(h)

    for k in ("component_relation", "fragment_relation", "orbit_relation", "defect_macro_distance"):
        vals = {r[k] for r in records}
        if vals != {None}:
            raise AssertionError(f"expected {k} to be null for every J record; got {vals}")

    return {
        "total_records": len(records),
        "distinct_state_hashes": len(seen_hashes),
        "duplicate_state_hashes": duplicate_hashes,
        "pairwise_relation_fields_all_null_as_expected": True,
        "deficit_phase_type_groups": dict(sorted(by_phase.items(), key=lambda kv: -kv[1])),
        "deficit_phase_type_group_count": len(by_phase),
        "legal_macro_tail_count_distribution": dict(sorted(by_tail_count.items())),
        "deficit_phase_type_x_legal_macro_tail_count": {
            k: dict(sorted(v.items())) for k, v in phase_x_tail.items()
        },
    }


def cross_check_against_aggregate_file() -> Dict[str, Any]:
    """Cross-check the per-record tallies against the separately-recorded
    aggregate counters in f1_n2_depth6_decomposition.json's
    representatives_by_word['J'] and legal_macro_tail_count_distribution,
    where those exist and are comparable."""
    agg = json.loads((OUTPUTS / "f1_n2_depth6_decomposition.json").read_text(encoding="utf-8"))
    rep = agg["representatives_by_word"]["J"]
    return {
        "representative_deficit_phase_type": rep["deficit_phase_type"],
        "representative_legal_macro_tail_count": rep["legal_macro_tail_count"],
        "representative_state_hash": rep["state_hash"],
        "note": (
            "The aggregate file's own legal_macro_tail_count_distribution and "
            "deficit_phase_counts mix all five words together (A3R/RA3/RR/J/RA2), "
            "so they are not directly comparable to the J-only tallies above "
            "without re-deriving the split -- which is exactly what this "
            "script does from state_records, independently of that aggregation."
        ),
    }


def build_report() -> Dict[str, Any]:
    records = load_j_records()
    classification = classify(records)
    cross_check = cross_check_against_aggregate_file()
    return {
        "schema": "j-normal-forms-v1",
        "scope": (
            "Coarse classification of the 230 recorded F=1,H=0,N=2 J-type "
            "states, bounded by the summary fields actually stored in this "
            "corpus. NOT a full exact canonical normal form -- see module "
            "docstring for exactly what is and is not available."
        ),
        "classification": classification,
        "representative_cross_check": cross_check,
        "data_availability_limitation": (
            "Only 1 of the 230 J states (the stored 'representative') has a "
            "literal walk / hex-orbit-mask record in this corpus. The other "
            "229 are known only by state_hash + deficit_phase_type + "
            "legal_macro_tail_count. A full canonical normal form (source "
            "orbit, target orbit, split-hexagon position, fragment position, "
            "open component structure, visited-mask support, legal-tail "
            "signature) cannot be reconstructed for those 229 without "
            "re-running the generating search, which this task explicitly "
            "does not do (no new large-scale search)."
        ),
    }


def main() -> None:
    report = build_report()
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "j_normal_forms.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path),
                       "deficit_phase_type_group_count": report["classification"]["deficit_phase_type_group_count"]},
                      indent=2))


if __name__ == "__main__":
    main()
