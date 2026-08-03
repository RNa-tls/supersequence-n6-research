#!/usr/bin/env python3
"""Build immutable v6 endpoint ledgers and a no-search replay-validated v7 plan."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
V5 = ROOT / "outputs" / "rr_short1_4_corrected_fair_results.json"
V6 = ROOT / "outputs" / "rr_short5_top8_continuation.json"
ANALYSIS = ROOT / "outputs" / "rr_short5_top8_continuation_analysis.json"
VERIFIED = ROOT / "outputs" / "rr_short5_top8_continuation_verified.json"
LEDGER = ROOT / "outputs" / "rr_short5_top8_official_ledger.json"
PROVENANCE = ROOT / "outputs" / "rr_v6_provenance_loss_audit.json"
V7 = ROOT / "outputs" / "rr_top8_v7_replay_manifest.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load("rr_top8_v7_plan_pilot", ROOT / "src" / "search_rr_short1_4_corrected_fair.py")
rr, exact = pilot.rr, pilot.exact


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def node_trace(nodes: Mapping[str, Mapping[str, object]], node_id: str) -> list[Mapping[str, object]]:
    trace: list[Mapping[str, object]] = []
    while True:
        node = nodes[node_id]
        parent = node["parent_id"]
        if parent is None:
            break
        trace.append(node["incoming_macro_edge"])
        node_id = str(parent)
    trace.reverse()
    return trace


def main() -> None:
    v5 = json.loads(V5.read_text(encoding="utf-8"))
    v6 = json.loads(V6.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    verified = json.loads(VERIFIED.read_text(encoding="utf-8"))
    if not verified.get("passed"):
        raise AssertionError("v6 independent ledger was not verified")
    base: dict[str, Mapping[str, object]] = {}
    child_lookup: dict[str, tuple[Mapping[str, object], Mapping[str, object]]] = {}
    for row in v5["roots"].values():
        for branch in row["branches"]:
            base[str(branch["branch_id"])] = branch
        for child in row["admission"]["frozen_R1_children"]:
            child_lookup[str(child["branch_id"])] = (row["root_record"], child)
    analysis_by_child = {str(row["child_id"]): row for row in analysis["branches"]}
    capped, exhausted = [], []
    for record in v6["children"]:
        branch_id = str(record["child_id"])
        result = record["continuation_result"]
        checkpoint = ROOT / result["checkpoint"]["path"]
        endpoint = "NATURALLY_EXHAUSTED" if int(result["frontier_size"]) == 0 else "CAP_REACHED_NONEMPTY_FRONTIER"
        common = {
            "child_id": branch_id, "checkpoint_path": str(checkpoint.relative_to(ROOT)),
            "checkpoint_sha256": sha256_file(checkpoint), "total_expansions": int(result["expanded"]),
            "additional_v6_expansions": int(result["expanded"]) - 5000, "frontier_size": int(result["frontier_size"]),
            "max_depth": int(result["max_depth"]), "endpoint": endpoint,
            "engine_state_validated_by": "rr-short5-top8-continuation-verifier-v1",
            "engine_state_hash_definition": "SHA-256 of canonical frontier-state records (node id, exact state hash, decoration, lineage)",
            "missing_v6_auxiliary_provenance_fields": ["top8_continuation.schema", "top8_continuation.source_checkpoint",
                                                         "top8_continuation.source_sha256", "top8_continuation.base_expanded",
                                                         "top8_continuation.additional_budget"],
            "repair_profile": analysis_by_child[branch_id]["repair_events"],
            "r2_profile": analysis_by_child[branch_id]["r2"],
        }
        if endpoint == "NATURALLY_EXHAUSTED":
            raw = json.loads(checkpoint.read_text(encoding="utf-8"))
            if raw["frontier"]:
                raise AssertionError(f"nonempty exhausted frontier: {branch_id}")
            prune = {str(key): int(value) for key, value in raw["stats"].items() if str(key).startswith("prune:")}
            exhausted.append({**common, "empty_frontier_certificate": {"complete_frontier_snapshot": bool(raw["complete_frontier_snapshot"]),
                                                                          "frontier_count": 0, "checkpoint_schema": raw["schema"],
                                                                          "config_sha256": sha_json(raw["config"]),
                                                                          "terminal_prune_histogram": dict(sorted(prune.items())),
                                                                          "repair_candidate_count": len(raw["repair_events"]),
                                                                          "r2_candidate_count": len(raw["r2_paths"]),
                                                                          "component_merge_count": sum(bool(event["component_merge"]) for event in raw["repair_events"])}})
        else:
            raw = json.loads(checkpoint.read_text(encoding="utf-8"))
            if not raw["frontier"] or int(raw["stats"]["expanded"]) != 55000:
                raise AssertionError(f"invalid capped endpoint: {branch_id}")
            nodes = {str(node["node_id"]): node for node in raw["nodes"]}
            frontier = []
            for row in raw["frontier"]:
                state = exact.state_from_json(row["state"])
                trace = node_trace(nodes, str(row["node_id"]))
                frontier.append({"node_id": str(row["node_id"]), "depth": int(row["depth"]),
                                 "exact_state_hash": rr.state_hash(state), "decoration": row["decoration"],
                                 "lineage": row["lineage"], "macro_trace_sha256": sha_json(trace),
                                 "macro_trace_length": len(trace), "parent_node_id": nodes[str(row["node_id"])]["parent_id"]})
            root, child = child_lookup[branch_id]
            source = ROOT / base[branch_id]["checkpoint"]["path"]
            if sha256_file(source) != base[branch_id]["checkpoint"]["sha256"]:
                raise AssertionError(f"immutable v5 source SHA mismatch: {branch_id}")
            capped.append({**common, "trusted_immutable_anchor": {"v5_source_checkpoint": str(source.relative_to(ROOT)),
                                                                     "v5_source_sha256": sha256_file(source),
                                                                     "root_id": root["root_id"], "root_hash": sha_json(root),
                                                                     "r1_child_origin_hash": child["branch_origin_hash"],
                                                                     "r1_literal_trace_sha256": sha_json(child["literal_macro_trace"]),
                                                                     "r1_literal_trace_length": len(child["literal_macro_trace"])},
                           "v6_frontier_engine_state_sha256": sha_json(frontier), "frontier_literal_replay_anchors": frontier,
                           "nearest_profile": {"bridge_template_occurrences": 0,
                                               "r2_hierarchy": analysis_by_child[branch_id]["r2"]["hierarchy_maximum_levels"],
                                               "r2_outcomes": analysis_by_child[branch_id]["r2"]["outcomes"],
                                               "literal_target_a_hits": len(analysis_by_child[branch_id]["r2"]["target_a_hits"])}})
    if len(capped) != 2 or len(exhausted) != 6:
        raise AssertionError("expected v6 endpoint partition 2 capped + 6 exhausted")
    ledger = {"schema": "rr-short5-top8-official-ledger-v1", "scope": "v6 fixed 50,000-additional endpoint corpus",
              "input": {"v6_result_sha256": sha256_file(V6), "analysis_sha256": sha256_file(ANALYSIS),
                        "verification_sha256": sha256_file(VERIFIED)}, "capped_children": capped,
              "exhausted_certificates": exhausted,
              "aggregate": {"top_children": 8, "naturally_exhausted": 6, "capped_nonempty": 2,
                            "additional_expansions": 167820, "repair_literal_replays": 207842,
                            "r2_literal_replays": 99438, "component_merges": 0,
                            "bridge_template_occurrences": 0, "literal_target_a_hits": 0,
                            "target_b_survivors": 0, "independent_ledger_verifier": "passed"}}
    provenance = {"schema": "rr-v6-provenance-loss-audit-v1", "finding": "AUXILIARY_PROVENANCE_NOT_CLOSED_UNDER_V5_CHECKPOINT_SERIALIZER",
                  "severity": "resume metadata unsafe; completed engine-state analysis unaffected",
                  "v6_introducing_commit": "06dae7c", "shared_writer_commit": "4785cc6",
                  "first_affected_checkpoint_version": "rr-short1-4-corrected-fair-checkpoint-v5-literal-r2-source used as v6 payload",
                  "first_defective_write": "first pilot.run_branch atomic checkpoint rewrite after v6 bootstrap",
                  "call_sites": [
                      {"file": "src/search_rr_short5_top8_continuation.py", "lines": "45-49", "role": "adds v6-only top8_continuation then invokes shared writer", "effect": "metadata exists only before the first shared checkpoint rewrite"},
                      {"file": "src/search_rr_short1_4_corrected_fair.py", "lines": "311-318", "role": "checkpoint_payload whitelist serializer", "effect": "does not carry unrecognised top-level fields"},
                      {"file": "src/search_rr_short1_4_corrected_fair.py", "lines": "454-465", "role": "atomic checkpoint write", "effect": "replaces v6 bootstrap payload with whitelist payload"},
                      {"file": "src/search_rr_short5_top8_continuation.py", "lines": "46-48", "role": "v6 resume guard", "effect": "later resume requires source_sha256 that the shared writer dropped"}],
                  "lost_fields": ["top8_continuation.schema", "top8_continuation.source_checkpoint", "top8_continuation.source_sha256",
                                  "top8_continuation.base_expanded", "top8_continuation.additional_budget"],
                  "not_lost": ["checkpoint schema", "config including engine/recognizer hash", "root", "R1 child", "frontier", "seen keys",
                               "nodes/parent DAG", "repair events", "R2 paths", "stats", "complete_frontier_snapshot"],
                  "impact": {"v5": "not affected: v5 never asserted these v6 wrapper fields", "v6_completed_analysis": "not affected: source SHA externally anchored by v5 aggregate and all engine-state replay checks pass", "v6_same_driver_resume": "unsafe: the wrapper requires the omitted source_sha256"},
                  "remediation": "Do not modify v6 checkpoints. Reconstruct a fresh v7 payload by literal replay from the immutable v5 anchor and compare it to v6 endpoint states."}
    v7 = {"schema": "rr-top8-v7-replay-manifest-v1", "status": "PLAN_ONLY_NO_SEARCH_STARTED",
          "proposed_checkpoint_schema": "rr-short5-top8-replay-validated-checkpoint-v7",
          "proposed_provenance": ["trusted_v5_source_checkpoint and SHA-256", "v6_endpoint_checkpoint and SHA-256",
                                  "v6_frontier_engine_state_sha256", "root and R1-child origin hashes", "R1 literal trace hash",
                                  "engine/driver/recognizer semantics SHA-256", "initialization verifier SHA-256"],
          "per_capped_child": [{"child_id": item["child_id"], "trusted_anchor": item["trusted_immutable_anchor"],
                                  "v6_endpoint_checkpoint": item["checkpoint_path"], "v6_endpoint_sha256": item["checkpoint_sha256"],
                                  "v6_frontier_engine_state_sha256": item["v6_frontier_engine_state_sha256"],
                                  "frontier_anchor_count": len(item["frontier_literal_replay_anchors"]),
                                  "validation_steps": ["literal replay from immutable v5 R1 anchor through every parent-DAG macro trace",
                                                       "recompute all provenance fields without deserializing missing v6 auxiliary metadata",
                                                       "compare exact state hash, decoration, decorated key, and frontier-state digest to v6",
                                                       "compare legal successor signatures for every endpoint frontier state",
                                                       "compare exact literal-R2 recognizer outputs for every legal R2 candidate",
                                                       "require a separate read-only independent verifier before any v7 traversal"]}
                               for item in capped],
          "forbidden": ["resume v6 with missing metadata", "infer provenance from absent top8_continuation field", "start a search in this planning round"],
          "strategy_comparison": {
              "A_deepen_two_capped": {"estimate": "two new replay-validated branches; a first equal increment of 50,000 each is 100,000 exact expansions, with current endpoint checkpoints about 0.73 and 0.81 GiB", "proof_value": "highest near-term: may convert one or both small frontiers into exact empty-frontier certificates", "new_target_a_likelihood": "moderate relative to alternatives; these are the only top8 frontiers already known to survive", "exhaustion_likelihood": "plausible but unproved"},
              "B_other_105_capped": {"estimate": "breadth-first pilot at the same 50,000 cap would be up to 5,250,000 extra exact expansions plus checkpoint storage", "proof_value": "broader Target-A discovery coverage but little immediate closure", "new_target_a_likelihood": "unknown; no theorem ranks them above the two current frontiers", "exhaustion_likelihood": "low per unit cost because every selected child is already capped"},
              "C_hand_theorem": {"estimate": "small computation but open-ended mathematical effort", "proof_value": "maximal if successful", "new_target_a_likelihood": "not applicable", "exhaustion_likelihood": "not applicable; six-of-eight and zero bridge observations do not yet imply a theorem"}},
          "recommendation": "A_deepen_two_capped_after_v7_validation", "reason": "It is the smallest rigorously scoped next batch, preserves exact provenance, and can add exact empty-frontier certificates without extrapolating capped observations."}
    atomic_json(LEDGER, ledger); atomic_json(PROVENANCE, provenance); atomic_json(V7, v7)
    print(json.dumps({"status": "CODEX_TOP8_V7_PLAN_READY", "capped": [x["child_id"] for x in capped],
                      "exhausted": len(exhausted)}, sort_keys=True))


if __name__ == "__main__":
    main()
