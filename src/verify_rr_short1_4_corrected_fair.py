#!/usr/bin/env python3
"""Independent read-only verifier for the v5 short_ell1--4 fair pilots."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / "outputs" / "rr_short1_4_corrected_fair_results.json"
CLASSES = ROOT / "outputs" / "rr_short1_4_target_a_classes.json"
PROFILES = ROOT / "outputs" / "rr_short5_cross_root_profiles.json"
OUT = ROOT / "outputs" / "rr_short1_4_corrected_fair_verified.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load("rr_short14_verify_pilot", ROOT / "src" / "search_rr_short1_4_corrected_fair.py")
rr, exact, core = pilot.rr, pilot.exact, pilot.core
target_b = pilot.target_b


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def edge_from_json(state, data: Mapping[str, object]):
    return pilot.edge_from_json(state, data)


def checkpoint_for(branch: Mapping[str, object]) -> dict[str, object]:
    path = ROOT / branch["checkpoint"]["path"]
    if sha256_file(path) != branch["checkpoint"]["sha256"]:
        raise AssertionError("branch checkpoint SHA-256 mismatch")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != pilot.CHECKPOINT_SCHEMA or not raw.get("complete_frontier_snapshot"):
        raise AssertionError("branch checkpoint schema or atomic-completeness failure")
    return raw


def replay_node(root, child, nodes: Mapping[str, Mapping[str, object]], node_id: str,
                cache: dict[str, tuple[Any, Any, list[dict[str, object]]]]):
    if node_id in cache:
        return cache[node_id]
    node = nodes[node_id]
    if node["parent_id"] is None:
        state, dec = pilot.replay_trace(root, list(child["literal_macro_trace"]))
        trace = list(child["literal_macro_trace"])
    else:
        parent_state, parent_dec, parent_trace = replay_node(root, child, nodes, str(node["parent_id"]), cache)
        edge = edge_from_json(parent_state, node["incoming_macro_edge"])
        state = edge.state
        dec = rr.advance_decoration(edge.run.state, edge.joint, parent_dec)
        trace = parent_trace + [node["incoming_macro_edge"]]
    if rr.state_hash(state) != node["exact_state_hash"] or dec.to_json() != node["decoration"]:
        raise AssertionError("parent-DAG literal replay mismatch")
    cache[node_id] = (state, dec, trace)
    return cache[node_id]


def literal_source_ast_guard() -> None:
    for path in (ROOT / "src" / "search_rr_short1_4_corrected_fair.py",
                 ROOT / "src" / "analyze_rr_short_ell0_target_b.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(isinstance(node, ast.Name) and node.id == "true_phase_walk_capacity" for node in ast.walk(tree)):
            raise AssertionError("v5 Target-B path reaches the suspect phase helper")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=RESULT)
    ap.add_argument("--classes", type=Path, default=CLASSES)
    ap.add_argument("--profiles", type=Path, default=PROFILES)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    classes = json.loads(args.classes.read_text(encoding="utf-8"))
    profiles = json.loads(args.profiles.read_text(encoding="utf-8"))
    if result.get("schema") != pilot.SCHEMA or result.get("checkpoint_schema") != pilot.CHECKPOINT_SCHEMA:
        raise AssertionError("v5 result schema mismatch")
    if result.get("recognizer_semantics") != pilot.R2_SEMANTICS:
        raise AssertionError("literal R2 semantic tag missing from v5 result")
    if result.get("prune_profile") != rr.TARGET_A_SAFE_PROFILE:
        raise AssertionError("completion-only prune profile enabled")
    if result.get("macro_entry_semantics") != rr.R2_MACRO_ENTRY_PROVENANCE_TAG:
        raise AssertionError("macro-entry provenance tag mismatch")
    literal_source_ast_guard()
    expected_roots = pilot.root_records()
    if set(result["roots"]) != set(expected_roots):
        raise AssertionError("incorrect short-root universe")

    witness_count = 0
    root_status = {}
    all_branch_budget_ok = True
    canonical_known = pilot.historical_known_by_canonical()
    for root_id, item in result["roots"].items():
        root = item["root_record"]
        if root != expected_roots[root_id]:
            raise AssertionError("literal short root changed")
        admission = item["admission"]
        if admission.get("schema") != pilot.ADMISSION_SCHEMA:
            raise AssertionError("admission schema mismatch")
        children = {str(row["branch_id"]): row for row in admission["frozen_R1_children"]}
        for child in children.values():
            state, dec = pilot.replay_trace(root, list(child["literal_macro_trace"]))
            if dec.r_count != 1 or dec.r1 is None or rr.state_hash(state) != child["exact_state_hash"]:
                raise AssertionError("frozen R1 root literal replay failure")
            pre_state, pre_dec = pilot.replay_trace(root, list(child["literal_macro_trace"][:-1]))
            final_label = child["literal_macro_trace"][-1]["label"]
            edge = next((edge for edge, collision in rr.iter_raw_macro_candidates(pre_state)
                         if collision is None and edge is not None and edge.label == final_label), None)
            if edge is None:
                raise AssertionError("frozen R1 edge is no longer literal-legal")
            event_id, event = rr.r1_event_export(edge, pre_dec, dec, tuple(child["literal_macro_trace"][:-1]))
            if event_id != child["r1_event_id"] or event != child["literal_R1_event"]:
                raise AssertionError("frozen R1 event provenance mismatch")
        audit = item["state_key_audit"]
        if not audit.get("passed") or audit.get("grade") != "exhaustive tested-universe equivalence; not a theorem":
            raise AssertionError("post-R1 state-key audit is not validly scoped")
        for branch in item["branches"]:
            if branch["branch_id"] not in children:
                raise AssertionError("branch lacks an admitted R1 origin")
            config = pilot.branch_config(root, children[branch["branch_id"]], int(result["budget_per_R1_child"]))
            checkpoint = checkpoint_for(branch)
            if checkpoint.get("config") != config:
                raise AssertionError("checkpoint config lacks v5 literal-source identity")
            if checkpoint.get("child", {}).get("branch_origin_hash") != branch["branch_origin_hash"]:
                raise AssertionError("branch origin hash mismatch")
            if int(checkpoint["stats"]["expanded"]) != int(branch["expanded"]):
                raise AssertionError("checkpoint/result expansion mismatch")
            if int(branch["expanded"]) != int(result["budget_per_R1_child"]) and not branch["naturally_exhausted"]:
                raise AssertionError("nonexhausted branch did not receive equal fair cap")
            all_branch_budget_ok &= int(branch["expanded"]) == int(result["budget_per_R1_child"]) or bool(branch["naturally_exhausted"])
            nodes = {str(node["node_id"]): node for node in checkpoint["nodes"]}
            cache: dict[str, tuple[Any, Any, list[dict[str, object]]]] = {}
            for path in checkpoint["r2_paths"]:
                if not path.get("literal_Target_A"):
                    continue
                witness_count += 1
                state, dec, _trace = replay_node(root, children[branch["branch_id"]], nodes,
                                                  str(path["r2_predecessor_node_id"]), cache)
                edge = edge_from_json(state, path["r2_edge"])
                after = rr.advance_decoration(edge.run.state, edge.joint, dec)
                recognition = rr.target_a_recognizer(rr.r2_literal_joint_source(edge), edge.joint, dec, after)
                if not recognition["is_target_a"] or recognition["source_state_semantic_tag"] != pilot.R2_SEMANTICS:
                    raise AssertionError("stored Target-A hit is not a literal-joint-source hit")
        root_status[root_id] = next(row["status"] for row in profiles["roots"] if row["root_id"] == root_id)
    if not all_branch_budget_ok or not result.get("equal_budget_verified"):
        raise AssertionError("fair budget equality failed")
    if witness_count != int(classes["counts"]["literal_Target_A_hits"]):
        raise AssertionError("literal Target-A count is not conserved")
    if len(classes["literal_target_a_witnesses"]) != witness_count:
        raise AssertionError("Target-A witness export count mismatch")
    for witness in classes["literal_target_a_witnesses"]:
        known = canonical_known.get(witness["canonical_state_hash"], [])
        label = witness["known18_comparison"]["classification"]
        if label == "GENUINELY_NEW" and known:
            raise AssertionError("new class has a proved known-18 canonical match")
        if label != "GENUINELY_NEW" and not known:
            raise AssertionError("known-18 claim lacks left-S6 state equality")
    if profiles["cross_root"]["new_boundary_classes"] != classes["counts"]["new_state_classes"]:
        raise AssertionError("cross-root/new-class count mismatch")
    payload = {
        "schema": "rr-short1-4-corrected-fair-independent-verifier-v5",
        "status": "VERIFIED_CAPPED_PILOTS", "scope": "bounded fair pilots; no exhaustion conclusion",
        "input_sha256": {
            str(path.resolve().relative_to(ROOT)): sha256_file(path.resolve())
            for path in (args.result, args.classes, args.profiles)
        },
        "literal_Target_A_hits_replayed": witness_count,
        "fair_budget_verified": True,
        "v5_schema_verified": True,
        "literal_R2_source_verified": True,
        "known18_comparison_verified": True,
        "helper_free_Target_B_path_verified": True,
        "root_status": root_status,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
