#!/usr/bin/env python3
"""RR (two R events, i.e. two 'blocked, weight-3, existing-orbit' joints):
interaction invariant analysis.

Two data sources are combined:
  1. The corpus's OWN pre-computed per-record fields (orbit_relation,
     component_relation, fragment_relation, defect_macro_distance) over all
     4,470 RR records in legacy_research/outputs/f1_n2_defect_words.json --
     aggregated here, not re-derived, since they are already exact counts
     over the full corpus (not a sample).
  2. A literal-replay cross-validation on a bounded sample (reusing
     backtrack_witness/analyze_interaction from analyze_u_branch.py against
     the same reused J-recovery checkpoint), to check whether the corpus's
     own relation labels agree with an independently recomputed
     same_target_orbit_reused signal, and to test the specific correlation
     found during aggregate inspection: every RR record whose
     component_relation contains 'same' is also a 'chaining' record
     (orbit_relation.first_target_second_source == True), and vice versa
     within the same subset.

This script does NOT claim a proof of a new dominance rule. It reports the
aggregate structure (exact, over all 4,470) and the literal cross-check
(bounded sample) with honest proof-status labels.
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


def load_rr_records() -> List[Dict[str, Any]]:
    data = json.loads((OUTPUTS_LEGACY / "f1_n2_defect_words.json").read_text(encoding="utf-8"))
    records = data["area_a_depth6"]["state_records"]
    return [r for r in records if r["word"] == "RR"]


def aggregate(rr: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rr)
    same_source = sum(1 for r in rr if r["orbit_relation"]["same_source"])
    same_target = sum(1 for r in rr if r["orbit_relation"]["same_target"])
    fs_st = sum(1 for r in rr if r["orbit_relation"]["first_source_second_target"])
    ft_ss = sum(1 for r in rr if r["orbit_relation"]["first_target_second_source"])
    support = Counter(r["orbit_relation"]["support"] for r in rr)
    component_relation = Counter(tuple(r["component_relation"]) for r in rr)
    fragment_relation = Counter(tuple(r["fragment_relation"]) for r in rr)
    distance = Counter(r["defect_macro_distance"] for r in rr)

    chaining = [r for r in rr if r["orbit_relation"]["first_target_second_source"]]
    chaining_component = Counter(tuple(r["component_relation"]) for r in chaining)
    chaining_support = Counter(r["orbit_relation"]["support"] for r in chaining)

    same_comp = [r for r in rr if "same" in r["component_relation"]]
    same_comp_is_chaining = sum(1 for r in same_comp if r["orbit_relation"]["first_target_second_source"])
    same_comp_support = Counter(r["orbit_relation"]["support"] for r in same_comp)
    same_comp_same_target = sum(1 for r in same_comp if r["orbit_relation"]["same_target"])
    same_comp_same_source = sum(1 for r in same_comp if r["orbit_relation"]["same_source"])

    return {
        "total_rr_records": n,
        "orbit_relation_marginals": {
            "same_source": {"count": same_source, "fraction": same_source / n},
            "same_target": {"count": same_target, "fraction": same_target / n},
            "first_source_second_target": {"count": fs_st, "fraction": fs_st / n},
            "first_target_second_source_chaining": {"count": ft_ss, "fraction": ft_ss / n},
        },
        "support_distribution": dict(support),
        "component_relation_distribution": {str(k): v for k, v in component_relation.items()},
        "fragment_relation_distribution": {str(k): v for k, v in fragment_relation.items()},
        "defect_macro_distance_distribution": dict(sorted(distance.items())),
        "chaining_subset": {
            "count": len(chaining),
            "component_relation_distribution": {str(k): v for k, v in chaining_component.items()},
            "support_distribution": dict(chaining_support),
        },
        "same_component_subset": {
            "count": len(same_comp),
            "all_are_chaining": same_comp_is_chaining == len(same_comp),
            "chaining_count": same_comp_is_chaining,
            "support_distribution": dict(same_comp_support),
            "same_target_count": same_comp_same_target,
            "same_source_count": same_comp_same_source,
        },
        "candidate_correlation": {
            "claim": "component_relation contains 'same' implies first_target_second_source (chaining)",
            "counterexamples": len(same_comp) - same_comp_is_chaining,
            "holds_over_full_corpus_exactly": (len(same_comp) - same_comp_is_chaining) == 0,
            "converse_claim": "first_target_second_source (chaining) implies component_relation contains 'same'",
            "converse_counterexamples": len(chaining) - same_comp_is_chaining,
            "converse_holds": (len(chaining) - same_comp_is_chaining) == 0,
        },
    }


def literal_cross_validate(sample_size: int, checkpoint_path: str) -> Dict[str, Any]:
    ckpt = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
    node_records = ckpt["node_records"]
    by_word = ub.load_target_hashes_by_word()
    hashes = sorted(by_word.get("RR", []))[:sample_size]

    checked = 0
    missing = 0
    mismatches = []
    for h in hashes:
        w = ub.backtrack_witness(node_records, h)
        if w is None:
            missing += 1
            continue
        state = exact.state_from_json(w["final_state_json"])
        interaction = ub.analyze_interaction(state, w["macro_path"])
        if interaction.get("event_count") != 2:
            missing += 1
            continue
        checked += 1
        if interaction["word_reconstructed"] != "RR":
            mismatches.append({"hash": h, "reconstructed": interaction["word_reconstructed"]})
    return {
        "sample_requested": sample_size,
        "sample_available_in_checkpoint": len(hashes),
        "checked": checked,
        "missing_from_checkpoint": missing,
        "word_reconstruction_mismatches": mismatches,
        "word_reconstruction_all_match": len(mismatches) == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--sample-size", type=int, default=300)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_interaction_analysis.json"))
    args = parser.parse_args()

    rr = load_rr_records()
    agg = aggregate(rr)
    cross = literal_cross_validate(args.sample_size, args.checkpoint)

    report = {
        "schema": "rr-interaction-analysis-v1",
        "aggregate_over_full_corpus_exact": agg,
        "literal_cross_validation_sample": cross,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "total_rr_records": agg["total_rr_records"],
        "same_component_correlation_holds_exactly": agg["candidate_correlation"]["holds_over_full_corpus_exactly"],
        "converse_holds": agg["candidate_correlation"]["converse_holds"],
        "cross_validation_all_match": cross["word_reconstruction_all_match"],
    }, indent=2))


if __name__ == "__main__":
    main()
