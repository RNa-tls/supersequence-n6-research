#!/usr/bin/env python3
"""Read-only Round 35 audit of the bounded Round 27 Target-A roots.

This is deliberately an *audit*, not a new Target-A search.  It reconstructs
the 22 roots whose old bounded search returned ``INCOMPLETE`` from the frozen
prefix corpus, verifies the stored post-prefix state hash, and reports only
quotients justified by existing data:

* literal prefix identity;
* exact post-return state identity;
* the already-defined left-S6 canonical ``(state, O*, R1-target)`` pair.

It intentionally does not merge roots by a guessed "terminal relevant"
history relation.  Later RR chaining predicates retain history which is not a
function of ``ExactState`` alone.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def load_module(name: str, filename: Path):
    spec = importlib.util.spec_from_file_location(name, filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hashed(value: Any) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefixes", type=Path,
                        default=ROOT / "outputs" / "rr_long_excursion_prefixes.json")
    parser.add_argument("--results", type=Path,
                        default=ROOT / "outputs" / "rr_long_prefix_extension_results.json")
    parser.add_argument("--quotient", type=Path,
                        default=ROOT / "outputs" / "rr_long_prefix_quotient.json")
    parser.add_argument("--out-ledger", type=Path,
                        default=ROOT / "outputs" / "rr_target_a_22_root_ledger.json")
    parser.add_argument("--out-quotient", type=Path,
                        default=ROOT / "outputs" / "rr_target_a_root_quotient.json")
    args = parser.parse_args()

    prefixes_data = json.loads(args.prefixes.read_text(encoding="utf-8"))
    results_data = json.loads(args.results.read_text(encoding="utf-8"))
    stored_quotient = json.loads(args.quotient.read_text(encoding="utf-8"))
    prefix_records = prefixes_data["prefixes"]
    result_records = results_data["results"]
    incomplete_results = [r for r in result_records if r["status"] == "INCOMPLETE"]
    if len(incomplete_results) != 22:
        raise AssertionError(f"expected 22 old INCOMPLETE roots, got {len(incomplete_results)}")
    if any(r["truncated_by_ceiling"] or not r["truncated_by_node_cap"]
           for r in incomplete_results):
        raise AssertionError("an INCOMPLETE root does not have the expected node-cap-only status")

    roots_module = load_module("round35_root_audit_roots",
                               ROOT / "src" / "build_rr_long_excursion_roots.py")
    ledger_roots = []
    exact_groups: dict[str, list[str]] = defaultdict(list)
    canonical_groups: dict[str, list[str]] = defaultdict(list)
    conservative_history_groups: dict[str, list[str]] = defaultdict(list)

    for result in sorted(incomplete_results, key=lambda r: r["prefix_index"]):
        index = result["prefix_index"]
        record = prefix_records[index]
        state = roots_module.replay_state(record)
        state_hash = roots_module.state_hash(state)
        if state_hash != record["post_return_state_hash"]:
            raise AssertionError(f"state hash mismatch at prefix {index}")
        if repr(state.stable_key()) != record["post_return_stable_key"]:
            raise AssertionError(f"stable-key mismatch at prefix {index}")
        canonical_key, stabilizer_ties = roots_module.canonical_pair_key(
            state, record["o_star"], record["r1_target_orbit"])
        exact_key = record["post_return_stable_key"]
        canonical_key_repr = repr(canonical_key)
        if stored_quotient["exact_state_classes"].get(exact_key) != [index]:
            raise AssertionError(f"stored exact quotient disagrees at prefix {index}")
        if stored_quotient["canonical_classes"].get(canonical_key_repr) != [index]:
            raise AssertionError(f"stored canonical quotient disagrees at prefix {index}")
        conservative_history_key = repr((
            state.stable_key(), record["o_star"], record["r1_target_orbit"],
            record["r_count"], record["root_ell"],
        ))
        root_id = f"R27-prefix-{index}"
        exact_groups[exact_key].append(root_id)
        canonical_groups[canonical_key_repr].append(root_id)
        conservative_history_groups[conservative_history_key].append(root_id)
        ledger_roots.append({
            "root_id": root_id,
            "prefix_index": index,
            "old_round27_status": result["status"],
            "old_search": {
                "node_cap": results_data["node_cap"],
                "extension_depth_ceiling": results_data["extension_depth_ceiling"],
                "nodes_expanded": result["nodes_expanded"],
                "dedup_states": result["dedup_states"],
                "r2_boundaries_reached": result["r2_boundaries_reached"],
                "same_component_hits": result["n_same_component_witnesses"],
                "truncated_by_node_cap": result["truncated_by_node_cap"],
                "truncated_by_ceiling": result["truncated_by_ceiling"],
                "prior_max_depth": None,
                "prior_max_depth_status": "MISSING_NOT_SERIALIZED",
            },
            "root_unit": "(literal joint word, abandonment root ell) state-bearing pair",
            "root_ell": record["root_ell"],
            "o_star": record["o_star"],
            "literal_joint_word": record["literal_joint_word"],
            "symbolic_word": record["symbolic_word"],
            "L": record["L"],
            "G": record["G"],
            "return_exponent": record["return_exponent"],
            "r_count": record["r_count"],
            "r1_target_orbit": record["r1_target_orbit"],
            "f_sym_count": record["f_sym_count"],
            "f_def": record["f_def"],
            "phi": record["phi"],
            "P": record["P"], "S": record["S"], "H": record["H"],
            "O": record["O"], "D": record["D"], "N_def": record["N_def"],
            "visited_count": record["visited_count"],
            "post_return_state_hash": state_hash,
            "post_return_stable_key_sha256": hashed(exact_key),
            "left_s6_canonical_pair_sha256": hashed(canonical_key_repr),
            "left_s6_stabilizer_ties": stabilizer_ties,
            "conservative_history_key_sha256": hashed(conservative_history_key),
            "replay_checked": True,
            "source_functions": [
                "build_rr_long_excursion_roots.replay_prefix",
                "build_rr_long_excursion_roots.replay_state",
                "build_rr_long_excursion_roots.canonical_pair_key",
                "search_rr_long_prefix_extensions.search",
            ],
        })

    def serialise_groups(groups: dict[str, list[str]]) -> list[dict[str, Any]]:
        return [{"key_sha256": hashed(k), "root_ids": value, "size": len(value)}
                for k, value in sorted(groups.items())]

    exact_dupes = [g for g in exact_groups.values() if len(g) > 1]
    canonical_dupes = [g for g in canonical_groups.values() if len(g) > 1]
    conservative_dupes = [g for g in conservative_history_groups.values() if len(g) > 1]
    if exact_dupes or canonical_dupes or conservative_dupes:
        raise AssertionError("the frozen 22-root cohort unexpectedly contains a quotient duplicate")

    ledger = {
        "schema": "rr-target-a-22-root-ledger-v1",
        "grade": "exact replay and existing exact left-S6 canonicalization; no new search",
        "repository_input_sha256": {
            "prefixes": sha256_file(args.prefixes),
            "results": sha256_file(args.results),
            "stored_quotient": sha256_file(args.quotient),
        },
        "selection": {
            "source_result": "old Round 27 records with status INCOMPLETE",
            "expected_status_histogram": {"FOUND": 6, "INCOMPLETE": 22,
                                          "EXHAUSTED_IMPOSSIBLE": 0},
            "actual_status_histogram": dict(Counter(r["status"] for r in result_records)),
            "all_selected_roots_truncated_by_node_cap_only": True,
            "all_selected_roots_have_nodes_expanded_8000": all(
                r["old_search"]["nodes_expanded"] == 8000 for r in ledger_roots),
        },
        "roots": ledger_roots,
    }
    quotient = {
        "schema": "rr-target-a-root-quotient-v1",
        "grade": "exact replay + existing canonical_pair_key; terminal-relevant quotient deliberately not asserted",
        "root_count": len(ledger_roots),
        "root_unit": "raw state-bearing (literal joint word, root ell) pair",
        "exact_state": {
            "class_count": len(exact_groups), "duplicate_classes": serialise_groups(
                {k: v for k, v in exact_groups.items() if len(v) > 1}),
        },
        "left_s6_decorated_pair": {
            "definition": "canonical_pair_key(state, O*, R1 target orbit)",
            "class_count": len(canonical_groups), "duplicate_classes": serialise_groups(
                {k: v for k, v in canonical_groups.items() if len(v) > 1}),
        },
        "conservative_history_preserving_key": {
            "definition": "(ExactState, O*, R1 target orbit, R-count, root ell)",
            "class_count": len(conservative_history_groups),
            "duplicate_classes": serialise_groups(
                {k: v for k, v in conservative_history_groups.items() if len(v) > 1}),
            "status": "unique in this cohort, but not claimed minimal",
        },
        "terminal_relevant_history_equivalence": {
            "status": "NOT_PROVED; NO_QUOTIENT_MERGE_USED",
            "reason": ("Round 35 CH1/CH2/chaining predicates retain distinctions, including "
                       "R1-target data, not determined by ExactState alone.  A relation-based "
                       "merge would require a separate proof."),
        },
        "cross_check_with_full_prefix_quotient": {
            "all_literal_prefixes": stored_quotient["literal_prefixes"],
            "all_exact_state_classes": stored_quotient["distinct_exact_states"],
            "all_left_s6_pair_classes": stored_quotient["distinct_left_s6_canonical_pairs"],
            "cohort_unique_under_each_proven_quotient": True,
        },
    }
    args.out_ledger.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_quotient.write_text(json.dumps(quotient, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out_ledger} ({len(ledger_roots)} roots)")
    print(f"wrote {args.out_quotient} (exact={len(exact_groups)}, canonical={len(canonical_groups)})")


if __name__ == "__main__":
    main()
