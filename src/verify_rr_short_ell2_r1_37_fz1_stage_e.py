#!/usr/bin/env python3
"""Independent replay verifier for the Round 59 FZ1 Stage-E search.

The verifier treats the Stage-D checkpoints as immutable roots.  It rebuilds
every Stage-E child with the exact macro engine, regenerates every candidate
of every expanded node, and checks the stored checkpoint/result ledgers.  The
candidate distance is deliberately absent: it is a scheduling hint, not a
legality or pruning rule.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
STAGE_E_DRIVER = ROOT / "src" / "search_rr_short_ell2_r1_37_fz1_stage_e.py"
STAGE_D_DRIVER = ROOT / "src" / "search_rr_short_ell2_r1_37_first_component_z3.py"
CANDIDATE_ANALYZER = ROOT / "src" / "analyze_rr_short_ell2_r1_37_fz1_candidates.py"
MANIFEST = ROOT / "outputs" / "rr_short_ell2_r1_37_stage_e_manifest.json"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_stage_e_results.json"
VERIFIED = ROOT / "outputs" / "rr_short_ell2_r1_37_stage_e_verified.json"

CHECKPOINT_SCHEMA = "rr-short-ell2-r1-37-fz1-stage-e-checkpoint-v1"
MANIFEST_SCHEMA = "rr-short-ell2-r1-37-fz1-stage-e-manifest-v1"
RESULT_SCHEMA = "rr-short-ell2-r1-37-fz1-stage-e-results-v1"
SEMANTICS = "FZ1_CANDIDATE_DISTANCE_ORDER_ONLY_TARGET_A_SAFE_V1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


stage_d = load_module("rr_fz1_stage_e_verify_base", STAGE_D_DRIVER)
audit = load_module("rr_fz1_stage_e_verify_audit", CANDIDATE_ANALYZER)
rr, exact, pilot = stage_d.rr, stage_d.exact, stage_d.pilot


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value))
    os.replace(temporary, path)


def independent_manifest(stored: Mapping[str, object]) -> dict[str, object]:
    """Rebuild proof-critical manifest fields without importing Stage E."""
    if stored.get("schema") != MANIFEST_SCHEMA or stored.get("semantics") != SEMANTICS:
        raise AssertionError("Stage-E manifest schema/semantics mismatch")
    rebuilt = dict(stored)
    hashes = dict(stored["hashes"])
    expected_files = {
        "driver_sha256": STAGE_E_DRIVER,
        "stage_D_driver_sha256": STAGE_D_DRIVER,
        "rr_engine_sha256": ROOT / "src" / "search_rr_target_a_exhaustive.py",
        "exact_engine_sha256": ROOT / "legacy_research" / "work" / "superperm_partial_f1.py",
        "macro_engine_sha256": ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py",
        "candidate_file_sha256": ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_orbits.json",
        "condition_ledger_sha256": ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_condition_ledger.json",
        "candidate_verification_sha256": ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_verified.json",
    }
    for field, path in expected_files.items():
        if hashes.get(field) != sha256_file(path):
            raise AssertionError(f"manifest code/data SHA mismatch: {field}")
    if stored.get("prune_profile") != rr.TARGET_A_SAFE_PROFILE:
        raise AssertionError("Stage E does not use Target-A-safe prune profile")
    if stored.get("prune_registry_hash") != rr.registry_hash(rr.TARGET_A_SAFE_PROFILE):
        raise AssertionError("Stage-E prune registry hash mismatch")
    if not stored.get("candidate_priority_is_ordering_only"):
        raise AssertionError("candidate priority scope is not ordering-only")
    if not stored.get("source_checkpoints_immutable"):
        raise AssertionError("Stage-D sources are not declared immutable")
    for source in stored["sources"]:
        source_path = ROOT / source["path"]
        if sha256_file(source_path) != source["sha256"]:
            raise AssertionError(f"immutable Stage-D source changed: {source['seed_id']}")
    return rebuilt


def expected_provenance(manifest: Mapping[str, object], seed_id: str) -> dict[str, object]:
    source = next(row for row in manifest["sources"] if row["seed_id"] == seed_id)
    return {
        "schema": CHECKPOINT_SCHEMA,
        "semantics": SEMANTICS,
        "manifest_sha256": sha256_json(manifest),
        "source": source,
        "driver_sha256": manifest["hashes"]["driver_sha256"],
        "rr_engine_sha256": manifest["hashes"]["rr_engine_sha256"],
        "candidate_file_sha256": manifest["hashes"]["candidate_file_sha256"],
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": manifest["prune_registry_hash"],
        "additional_cap": int(manifest["additional_expansion_cap_per_seed"]),
    }


def source_roots(source: Mapping[str, object], seed_id: str):
    path = ROOT / source["path"]
    roots = {}
    count = 0
    for index, row in enumerate(audit.iter_top_array(path, "frontier")):
        node_id = f"{seed_id}:stageE:root:{index}"
        roots[node_id] = (
            exact.state_from_json(row["state"]),
            rr.Decoration.from_json(row["decoration"]),
            int(row["depth"]),
            str(row["path_hash"]),
            str(row["node_id"]),
        )
        count += 1
    if count != int(source["frontier_count"]):
        raise AssertionError(f"source frontier cardinality changed: {seed_id}")
    return roots


def verify_branch(manifest: Mapping[str, object], result_row: Mapping[str, object]) -> dict[str, object]:
    seed_id = str(result_row["seed_id"])
    source = next(row for row in manifest["sources"] if row["seed_id"] == seed_id)
    checkpoint = ROOT / result_row["checkpoint"]["path"]
    if sha256_file(checkpoint) != result_row["checkpoint"]["sha256"]:
        raise AssertionError(f"Stage-E checkpoint SHA mismatch: {seed_id}")
    raw = json.loads(checkpoint.read_text(encoding="utf-8"))
    if raw.get("schema") != CHECKPOINT_SCHEMA or not raw.get("complete_frontier_snapshot"):
        raise AssertionError(f"Stage-E checkpoint schema mismatch: {seed_id}")
    if raw.get("provenance") != expected_provenance(manifest, seed_id):
        raise AssertionError(f"Stage-E checkpoint provenance mismatch: {seed_id}")

    roots = source_roots(source, seed_id)
    states = {}
    source_anchor = {}
    recomputed_witnesses = []
    for row in raw["nodes"]:
        node_id = str(row["node_id"])
        parent_id = row["parent_id"]
        if parent_id is None:
            if node_id not in roots:
                raise AssertionError(f"unknown Stage-E root: {node_id}")
            state, dec, depth, path_hash, source_node_id = roots[node_id]
            if row.get("incoming_macro_edge") is not None or int(row["relative_depth"]) != 0:
                raise AssertionError(f"malformed Stage-E root: {node_id}")
            if row.get("source_stage_D_node_id") != source_node_id:
                raise AssertionError(f"Stage-D ancestry mismatch: {node_id}")
            if int(row["depth"]) != depth or row["path_hash"] != path_hash:
                raise AssertionError(f"Stage-E root depth/path mismatch: {node_id}")
            source_anchor[node_id] = source_node_id
        else:
            parent_id = str(parent_id)
            if parent_id not in states:
                raise AssertionError(f"parent-after-child: {node_id}")
            parent_state, parent_dec = states[parent_id]
            edge = pilot.edge_from_json(parent_state, row["incoming_macro_edge"])
            verdict, dec, recognition = rr.evaluate_edge(
                parent_state, parent_dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            if verdict != "child" or dec is None or recognition is not None:
                raise AssertionError(f"stored Stage-E child is not independently legal: {node_id}")
            state = edge.state
            if int(row["depth"]) != int(raw_node_depth[parent_id]) + 1:
                raise AssertionError(f"Stage-E depth mismatch: {node_id}")
            if int(row["relative_depth"]) != int(raw_relative_depth[parent_id]) + 1:
                raise AssertionError(f"Stage-E relative depth mismatch: {node_id}")
            expected_path_hash = sha256_json({"parent": raw_path_hash[parent_id], "edge": rr.edge_json(edge)})
            if row["path_hash"] != expected_path_hash:
                raise AssertionError(f"Stage-E path hash mismatch: {node_id}")
        if rr.state_hash(state) != row["exact_state_hash"]:
            raise AssertionError(f"Stage-E exact-state hash mismatch: {node_id}")
        if dec.to_json() != row["decoration"]:
            raise AssertionError(f"Stage-E decoration mismatch: {node_id}")
        if stage_d.decorated_digest(state, dec) != row["decorated_state_sha256"]:
            raise AssertionError(f"Stage-E decorated digest mismatch: {node_id}")
        states[node_id] = (state, dec)
        raw_node_depth[node_id] = int(row["depth"])
        raw_relative_depth[node_id] = int(row["relative_depth"])
        raw_path_hash[node_id] = str(row["path_hash"])

    frontier_ids = {str(row["node_id"]) for row in raw["frontier"]}
    if len(frontier_ids) != len(raw["frontier"]):
        raise AssertionError(f"duplicate Stage-E frontier record: {seed_id}")
    for row in raw["frontier"]:
        node_id = str(row["node_id"])
        if node_id not in states:
            raise AssertionError(f"frontier node absent from parent DAG: {node_id}")
        state, dec = states[node_id]
        if exact.state_to_json(state) != row["state"] or dec.to_json() != row["decoration"]:
            raise AssertionError(f"frontier literal mismatch: {node_id}")
        if int(row["depth"]) != raw_node_depth[node_id] or int(row["relative_depth"]) != raw_relative_depth[node_id]:
            raise AssertionError(f"frontier depth mismatch: {node_id}")

    witness_child_ids = {
        str(row["child_node_id"])
        for row in raw["witnesses"]
        if row.get("child_node_id") is not None
    }
    expanded_ids = [
        node_id for node_id in states
        if node_id not in frontier_ids and node_id not in witness_child_ids
    ]
    if len(expanded_ids) != int(raw["stats"]["expanded"]):
        raise AssertionError(f"expanded/frontier conservation mismatch: {seed_id}")

    stats = Counter(expanded=len(expanded_ids))
    replayed_r2 = []
    accepted_children = Counter()
    for node_id in expanded_ids:
        state, dec = states[node_id]
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] += 1
            if collision is not None or edge is None:
                stats[f"prune:{collision or 'missing_edge'}"] += 1
                continue
            verdict, after, recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            kind = pilot.edge_kind(edge)
            if kind == "R":
                stats["R2_candidates"] += 1
                if after is None or recognition is None:
                    raise AssertionError("R2 replay lost recognizer metadata")
                record = stage_d.r2_record(
                    seed_id, node_id, raw_path_hash[node_id], state, dec,
                    edge, after, recognition, None, 0,
                )
                replayed_r2.append(record)
                stats[f"R2:{recognition['r2_outcome']}"] += 1
                if record["literal_Target_A"]:
                    stats["Target_A"] += 1
                    if record["target_b"]["target_b_survivor"]:
                        stats["Target_B"] += 1
                    break
                continue
            if verdict != "child" or after is None:
                stats[f"prune:{verdict}"] += 1
                continue
            stats[f"accepted:{kind}"] += 1
            accepted_children[(node_id, sha256_json(rr.edge_json(edge)))] += 1
            classification = stage_d.classify_component_change(state, dec, edge, edge.state, after)
            if kind == "Z3":
                stats["Z3_transitions"] += 1
                stats[classification["classification"]] += 1
            if classification["is_first_component_change_candidate"]:
                recomputed_witnesses.append((node_id, rr.edge_json(edge), classification))
                break

    stored_children = Counter()
    for row in raw["nodes"]:
        if row["parent_id"] is not None:
            stored_children[(str(row["parent_id"]), sha256_json(row["incoming_macro_edge"]))] += 1
    # If a first-event/Target witness stopped the traversal, that witness child
    # is still serialized as a node.  Therefore accepted-child conservation is
    # exact even for early-stop checkpoints.
    if accepted_children != stored_children:
        raise AssertionError(f"accepted child transcript mismatch: {seed_id}")

    ignored = {"checkpoint_count", "max_depth"}
    stored_stats = {k: int(v) for k, v in raw["stats"].items() if k not in ignored and int(v)}
    replay_stats = {k: int(v) for k, v in stats.items() if k not in ignored and int(v)}
    if stored_stats != replay_stats:
        raise AssertionError(f"Stage-E candidate ledger mismatch: {seed_id}")
    if len(replayed_r2) != len(raw["r2_records"]):
        raise AssertionError(f"Stage-E R2 record count mismatch: {seed_id}")
    if Counter(sha256_json(row) for row in replayed_r2) != Counter(sha256_json(row) for row in raw["r2_records"]):
        raise AssertionError(f"Stage-E R2 literal replay mismatch: {seed_id}")
    if len(recomputed_witnesses) != len(raw["witnesses"]):
        raise AssertionError(f"Stage-E component witness count mismatch: {seed_id}")

    exhausted = not frontier_ids and raw.get("stop_reason") is None
    if bool(result_row["naturally_exhausted"]) != exhausted:
        raise AssertionError(f"Stage-E exhaustion status mismatch: {seed_id}")
    if not exhausted and raw.get("stop_reason") is None and int(raw["stats"]["expanded"]) != int(manifest["additional_expansion_cap_per_seed"]):
        raise AssertionError(f"nonempty Stage-E frontier stopped below independent cap: {seed_id}")
    return {
        "seed_id": seed_id,
        "checkpoint_sha256": result_row["checkpoint"]["sha256"],
        "nodes_replayed": len(states),
        "expanded_nodes_replayed": len(expanded_ids),
        "frontier_replayed": len(frontier_ids),
        "accepted_transitions_rechecked": sum(accepted_children.values()),
        "R2_candidates_rechecked": len(replayed_r2),
        "component_change_witnesses": len(recomputed_witnesses),
        "Target_A_rechecked": int(stats["Target_A"]),
        "Target_B_rechecked": int(stats["Target_B"]),
        "naturally_exhausted": exhausted,
    }


# These dictionaries are deliberately module-local scratch space so every
# row's lineage fields are checked without trusting serialized child state.
raw_node_depth: dict[str, int] = {}
raw_relative_depth: dict[str, int] = {}
raw_path_hash: dict[str, str] = {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    independent_manifest(manifest)
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if result.get("schema") != RESULT_SCHEMA or result.get("semantics") != SEMANTICS:
        raise AssertionError("Stage-E result schema/semantics mismatch")
    if result.get("manifest_sha256") != sha256_json(manifest):
        raise AssertionError("Stage-E result/manifest identity mismatch")
    rows = []
    for row in result["branches"]:
        raw_node_depth.clear()
        raw_relative_depth.clear()
        raw_path_hash.clear()
        rows.append(verify_branch(manifest, row))
    aggregate = {
        field: sum(int(row[field]) for row in rows)
        for field in (
            "nodes_replayed", "expanded_nodes_replayed", "frontier_replayed",
            "accepted_transitions_rechecked", "R2_candidates_rechecked",
            "component_change_witnesses", "Target_A_rechecked", "Target_B_rechecked",
        )
    }
    expected_status = (
        "FOUND_TARGET_B" if aggregate["Target_B_rechecked"]
        else "FOUND_TARGET_A" if aggregate["Target_A_rechecked"]
        else "FZ1_EXACT_WITNESS_FOUND" if aggregate["component_change_witnesses"]
        else "FZ1_LOCAL_CANDIDATES_ALL_OBSTRUCTED" if all(row["naturally_exhausted"] for row in rows)
        else "STAGE_E_INCOMPLETE"
    )
    if result.get("overall_status") != expected_status:
        raise AssertionError("Stage-E aggregate status mismatch")
    payload = {
        "schema": "rr-short-ell2-r1-37-fz1-stage-e-independent-verification-v1",
        "verified": True,
        "verification_scope": "literal parent-DAG replay and complete macro-candidate regeneration for every expanded Stage-E node",
        "manifest_sha256": sha256_json(manifest),
        "result_sha256": sha256_file(RESULT),
        "verifier_sha256": sha256_file(Path(__file__)),
        "branches": rows,
        "aggregate": aggregate,
        "overall_status": expected_status,
        "scope_warning": "A capped nonempty frontier is an incomplete exact search, not an impossibility certificate.",
    }
    if args.write:
        atomic_json(VERIFIED, payload)
    if not VERIFIED.exists() or json.loads(VERIFIED.read_text(encoding="utf-8")) != payload:
        raise AssertionError("Stage-E verification output differs; run with --write")
    print(json.dumps({"verified": True, "overall_status": expected_status, **aggregate}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
