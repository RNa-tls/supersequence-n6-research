#!/usr/bin/env python3
"""Independent Round-48 audit of R2's literal source semantics.

This verifier has two deliberately separate jobs.  First, it replays every
R2 candidate of the corrected fair 4x25,000 prefix from its parent DAG and
checks the Target-A predicate at ``edge.run.state``.  Secondly it reproduces
the sole surviving known-18 class's helper-free Target-B flow with the older
independent DFS implementation.  It never invokes the suspect general phase
capacity helper.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / "outputs" / "rr_short_ell0_corrected_fair_repair_results.json"
HIERARCHY = ROOT / "outputs" / "rr_short_ell0_corrected_repair_hierarchy.json"
WITNESSES = ROOT / "outputs" / "rr_short_ell0_corrected_repair_witnesses.json"
CLASSES = ROOT / "outputs" / "rr_short_ell0_corrected_target_a_classes.json"
KNOWN = ROOT / "outputs" / "rr_short_ell0_corrected_known18_comparison.json"
LEDGER = ROOT / "outputs" / "rr_short_ell0_corrected_target_b_ledger.json"
OLD_HIERARCHY = ROOT / "outputs" / "rr_short_ell0_repair_hierarchy.json"
OLD_WITNESSES = ROOT / "outputs" / "rr_short_ell0_repair_witnesses.json"
OUT = ROOT / "outputs" / "rr_short_ell0_corrected_r2_source_verified.json"
AUDIT = ROOT / "outputs" / "rr_r2_source_callsite_audit.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fair = load("rr_r2_literal_fair", ROOT / "src" / "search_rr_short_ell0_repair_fair.py")
split, rr, exact = fair.split, fair.rr, fair.exact
target_b_verify = load("rr_r2_literal_target_b_independent", ROOT / "src" / "verify_rr_short_ell0_target_b.py")
MOVE = {move.label: move for move in exact.ALL_MOVES}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def edge_for_data(state, data: Mapping[str, object]):
    ell = int(data["rotation_length"])
    label = str(data["joint"])
    runs = [run for run in rr.macro.rotation_runs(state) if run.ell == ell]
    if len(runs) != 1:
        raise AssertionError("serialized macro run is absent or ambiguous")
    joint = exact.extend(runs[0].state, MOVE[label])
    if joint is None:
        raise AssertionError("serialized macro joint is literal-collision illegal")
    edge = rr.macro.MacroEdge(runs[0], joint)
    if edge.label != data["label"]:
        raise AssertionError("serialized macro label disagreement")
    return edge


def replay_branch(blob: Mapping[str, object], root_child: Mapping[str, object]):
    root_state, root_dec, *_ = split.replay_trace(split.record(), root_child["literal_macro_trace"])
    nodes = {str(row["node_id"]): row for row in blob["nodes"]}  # type: ignore[index]
    cache: dict[str, tuple[Any, Any]] = {}

    def replay(node_id: str):
        if node_id in cache:
            return cache[node_id]
        node = nodes[node_id]
        if node["parent_id"] is None:
            answer = (root_state, root_dec)
        else:
            parent_state, parent_dec = replay(str(node["parent_id"]))
            edge = edge_for_data(parent_state, node["incoming_macro_edge"])
            answer = (edge.state, rr.advance_decoration(edge.run.state, edge.joint, parent_dec))
        if rr.state_hash(answer[0]) != node["exact_state_hash"]:
            raise AssertionError(f"parent-DAG state mismatch at {node_id}")
        if answer[1].to_json() != node["decoration"]:
            raise AssertionError(f"parent-DAG decoration mismatch at {node_id}")
        cache[node_id] = answer
        return answer

    for node_id in nodes:
        replay(node_id)
    return cache


def node_transcript(blob: Mapping[str, object]) -> str:
    rows = []
    for node in sorted(blob["nodes"], key=lambda row: str(row["node_id"])):  # type: ignore[index]
        incoming = node["incoming_macro_edge"]
        rows.append((node["node_id"], node["parent_id"],
                     None if incoming is None else incoming["label"],
                     node["exact_state_hash"], repr(node["decoration"]), tuple(node["repair_ids"])))
    return hashlib.sha256(repr(rows).encode("utf-8")).hexdigest()


def helper_free(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return not any(isinstance(node, ast.Name) and node.id == "true_phase_walk_capacity" for node in ast.walk(tree))


def callsite_table() -> list[dict[str, object]]:
    return [
        {"file": "src/search_rr_target_a_exhaustive.py", "function": "target_a_recognizer",
         "old_state_used": "ambiguous parameter named pre_state", "correct_state": "joint_source_state / edge.run.state",
         "semantic_role": "R2 source orbit, incidence membership, same-component and chaining", "affected_outputs": ["all R2 recognizer records"]},
        {"file": "src/search_rr_target_a_exhaustive.py", "function": "geometry_failure_record + same_component_failure_record",
         "old_state_used": "pre_state parameter", "correct_state": "edge.run.state",
         "semantic_role": "R2 endpoint diagnostics", "affected_outputs": ["R2 geometry/component evidence"]},
        {"file": "src/search_rr_short_ell0_repair_fair.py", "function": "hierarchy_for_r2",
         "old_state_used": "macro-entry pre_state", "correct_state": "edge.run.state",
         "semantic_role": "repair hierarchy R2 source and same-component", "affected_outputs": ["rr_short_ell0_repair_hierarchy.json (v1 invalid)"]},
        {"file": "src/search_rr_short_ell0_r1_split.py", "function": "predicate_before_r2",
         "old_state_used": "ambiguous pre_state parameter", "correct_state": "joint_source_state",
         "semantic_role": "focused pre-Target-A predicate", "affected_outputs": ["focused predecessor records"]},
        {"file": "src/search_rr_short_ell0_fair_r1.py", "function": "repair_predicate",
         "old_state_used": "ambiguous pre_state parameter", "correct_state": "joint_source_state",
         "semantic_role": "fair repair predicate", "affected_outputs": ["fair R1 repair records"]},
        {"file": "src/verify_rr_short_ell0_repair_search.py", "function": "R4+ literal replay",
         "old_state_used": "macro-entry state", "correct_state": "edge.run.state",
         "semantic_role": "independent same-component replay", "affected_outputs": ["v1 verifier invalid for R2 source semantics"]},
        {"file": "src/analyze_rr_short_ell0_target_b.py", "function": "analysis",
         "old_state_used": "already correct edge.run.state", "correct_state": "edge.run.state",
         "semantic_role": "literal R2 corpus and Target-B dispatch", "affected_outputs": ["corrected Target-A/Target-B ledgers"]},
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=RESULT)
    ap.add_argument("--hierarchy", type=Path, default=HIERARCHY)
    ap.add_argument("--witnesses", type=Path, default=WITNESSES)
    ap.add_argument("--classes", type=Path, default=CLASSES)
    ap.add_argument("--known", type=Path, default=KNOWN)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--output", type=Path, default=OUT)
    ap.add_argument("--node-cap", type=int, default=20_000)
    ap.add_argument("--seconds", type=float, default=30.0)
    args = ap.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    hierarchy = json.loads(args.hierarchy.read_text(encoding="utf-8"))
    witnesses = json.loads(args.witnesses.read_text(encoding="utf-8"))
    if not (result["schema"] == hierarchy["schema"] == witnesses["schema"] == fair.SCHEMA):
        raise AssertionError("corrected output schema mismatch")
    if result.get("checkpoint_schema") != fair.CHECKPOINT_SCHEMA:
        raise AssertionError("v2 checkpoint schema not carried in result")
    if result["prune_profile"] != rr.TARGET_A_SAFE_PROFILE:
        raise AssertionError("completion-only prune enabled in corrected prefix")

    old_hierarchy = json.loads(OLD_HIERARCHY.read_text(encoding="utf-8"))
    old_witnesses = json.loads(OLD_WITNESSES.read_text(encoding="utf-8"))
    roots = {str(row["branch_id"]): row for row in hierarchy["frozen_R1_children"]}
    if set(roots) != set(witnesses["branches"]):
        raise AssertionError("branch/root universe mismatch")

    old_transcripts = {branch: node_transcript(old_witnesses["branches"][branch]) for branch in roots}
    new_transcripts = {branch: node_transcript(witnesses["branches"][branch]) for branch in roots}
    if old_transcripts != new_transcripts:
        raise AssertionError("boundary correction altered traversal transcript")
    for branch, row in result["branches"].items():
        if int(row["stats"]["expanded"]) != 25_000:
            raise AssertionError("corrected fair prefix lost equal budget")
        # The driver-level digest was formed from live Python dicts; JSON
        # decoding changes their insertion order although not their contents.
        # ``node_transcript`` above is the canonical JSON-stable comparison.
        # Retain the historical generation digest as provenance only.
        if len(str(row["traversal_transcript_sha256"])) != 64:
            raise AssertionError("missing driver traversal provenance digest")

    replayed = {branch: replay_branch(witnesses["branches"][branch], roots[branch]) for branch in roots}
    paths = hierarchy["paths"]
    literal_hits = []
    old_semantic_hits = 0
    source_changed = 0
    first_counterexample = None
    per_branch = Counter()
    for row in paths:
        branch = str(row["branch_id"])
        macro_entry, dec = replayed[branch][str(row["r2_predecessor_node_id"])]
        edge = edge_for_data(macro_entry, row["r2_edge"])
        after = rr.advance_decoration(edge.run.state, edge.joint, dec)
        literal = rr.target_a_recognizer(edge.run.state, edge.joint, dec, after)
        old_semantic = rr.target_a_recognizer(macro_entry, edge.joint, dec, after)
        if literal != row["recognizer"]:
            raise AssertionError("hierarchy recognizer not literal-joint-source result")
        if rr.state_hash(macro_entry) != row["literal_macro_entry"]["state_hash"]:
            raise AssertionError("macro entry provenance mismatch")
        if rr.state_hash(edge.run.state) != row["literal_joint_source"]["state_hash"]:
            raise AssertionError("joint source provenance mismatch")
        if row["predicate_state_roles"] != {
            "target_a_recognizer": "literal_joint_source",
            "incidence_forest_membership": "literal_joint_source",
            "same_component": "literal_joint_source",
        }:
            raise AssertionError("predicate-state role ledger mismatch")
        if rr.state_hash(macro_entry) != rr.state_hash(edge.run.state):
            source_changed += 1
        if old_semantic["is_target_a"]:
            old_semantic_hits += 1
        if old_semantic["conditions"]["same_component"] and not literal["conditions"]["same_component"] and first_counterexample is None:
            first_counterexample = {
                "branch_id": branch,
                "r2_predecessor_node_id": row["r2_predecessor_node_id"],
                "literal_macro_trace_suffix": row["r2_edge"],
                "macro_entry_hash": rr.state_hash(macro_entry),
                "joint_source_hash": rr.state_hash(edge.run.state),
                "macro_entry_same_component": True,
                "joint_source_same_component": False,
            }
        if literal["is_target_a"]:
            literal_hits.append(row)
            per_branch[branch] += 1
    if len(paths) != 46_128:
        raise AssertionError(f"unexpected corrected repaired R2 path count {len(paths)}")
    if old_semantic_hits != 38_406 or len(literal_hits) != 1:
        raise AssertionError((old_semantic_hits, len(literal_hits)))
    if source_changed != len(paths) or first_counterexample is None:
        raise AssertionError("required macro-entry vs literal-source counterexample missing")

    classes = json.loads(args.classes.read_text(encoding="utf-8"))
    known = json.loads(args.known.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    if classes["counts"]["stored_R6_claims"] != 1 or classes["counts"]["exact_Target_A_literal_replays"] != 1:
        raise AssertionError("corrected Target-A freeze is not singleton")
    if len(classes["canonical_classes"]) != 1 or len(known["canonical_class_comparison"]) != 1:
        raise AssertionError("corrected Target-A canonisation is not singleton")
    comparison = known["canonical_class_comparison"][0]
    if comparison["classification"] != "SYMMETRY_EQUIVALENT_TO_KNOWN18":
        raise AssertionError("surviving Target-A state is not known18-equivalent")
    if not helper_free(ROOT / "src" / "analyze_rr_short_ell0_target_b.py"):
        raise AssertionError("Target-B analyzer reaches suspect helper")
    state = target_b_verify.state_from_json(classes["canonical_classes"][0]["canonical_state"])
    independent_flow = target_b_verify.independent_flow(state, args.node_cap, args.seconds)
    ledger_row = ledger["rows"][0]
    stored_flow = ledger_row["exact_flow"]
    if stored_flow is None:
        raise AssertionError("corrected known class did not receive exact Target-B flow")
    for key in ("verdict", "nodes", "truncated", "max_depth", "max_visited", "leaf_states", "prunes", "surviving_ells"):
        if stored_flow[key] != independent_flow[key]:
            raise AssertionError(f"independent helper-free flow disagreement: {key}")
    if independent_flow["verdict"] != "EXHAUSTED_NO_PATH" or independent_flow["nodes"] != 3_214 or independent_flow["truncated"]:
        raise AssertionError("known class flow did not independently exhaust in 3214 nodes")

    audit = {
        "schema": "rr-r2-literal-source-callsite-audit-v2",
        "correction": "R2 source is edge.run.state, never macro-entry state",
        "call_sites": callsite_table(),
        "historical_outputs": [
            {"path": str(OLD_HIERARCHY.relative_to(ROOT)), "status": "INVALID_R2_SOURCE_SEMANTICS", "sha256": sha256_file(OLD_HIERARCHY)},
            {"path": str(OLD_WITNESSES.relative_to(ROOT)), "status": "PROVENANCE_REPLAYABLE_BUT_OLD_HIERARCHY_LABELS_INVALID", "sha256": sha256_file(OLD_WITNESSES)},
        ],
        "regression_fixture": first_counterexample,
    }
    atomic_json(AUDIT, audit)
    payload = {
        "schema": "rr-r2-literal-source-independent-verifier-v2",
        "status": "VERIFIED",
        "scope": "same capped 4x25,000 fair prefix; no deeper continuation search",
        "traversal_transcript_preserved": True,
        "corrected_repaired_R2_paths": len(paths),
        "old_macro_entry_semantic_Target_A_claims": old_semantic_hits,
        "corrected_literal_same_component_failures": old_semantic_hits - len(literal_hits),
        "corrected_literal_Target_A_hits": len(literal_hits),
        "literal_hit_branch_distribution": dict(per_branch),
        "canonical_classes": len(classes["canonical_classes"]),
        "known18_classification": comparison,
        "helper_free_target_B": independent_flow,
        "counterexample_fixture": first_counterexample,
        "input_sha256": {str(path.relative_to(ROOT)): sha256_file(path) for path in
                         (args.result, args.hierarchy, args.witnesses, args.classes, args.known, args.ledger)},
    }
    atomic_json(args.output, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
