#!/usr/bin/env python3
"""Round 59 Stage E: candidate-priority continuation of seed_3 and seed_6.

The immutable Stage-D frontiers are copied into a fresh namespace.  Candidate
distance changes heap order only; literal generation and the Target-A-safe
prune profile are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
SOURCE_RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
CANDIDATE_FILE = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_orbits.json"
LEDGER_FILE = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_condition_ledger.json"
AUDIT_VERIFIED = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_verified.json"
CHECKPOINT_ROOT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_37_fz1_stage_e_v1"
MANIFEST_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_stage_e_manifest.json"
RESULT_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_stage_e_results.json"

SCHEMA = "rr-short-ell2-r1-37-fz1-stage-e-checkpoint-v1"
MANIFEST_SCHEMA = "rr-short-ell2-r1-37-fz1-stage-e-manifest-v1"
RESULT_SCHEMA = "rr-short-ell2-r1-37-fz1-stage-e-results-v1"
SEMANTICS = "FZ1_CANDIDATE_DISTANCE_ORDER_ONLY_TARGET_A_SAFE_V1"
SEEDS = ("short_ell2_r1_37:6", "short_ell2_r1_37:3")
CAP = 500_000


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


stage_d = load_module(
    "rr_fz1_stage_e_base",
    ROOT / "src" / "search_rr_short_ell2_r1_37_first_component_z3.py",
)
audit = load_module(
    "rr_fz1_stage_e_audit",
    ROOT / "src" / "analyze_rr_short_ell2_r1_37_fz1_candidates.py",
)
rr, exact, pilot = stage_d.rr, stage_d.exact, stage_d.pilot


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value))
    temporary.replace(path)


def checkpoint_path(seed_id: str) -> Path:
    return CHECKPOINT_ROOT / f"seed_{seed_id.rsplit(':', 1)[1]}" / "checkpoint.json"


def progress_path(seed_id: str) -> Path:
    return checkpoint_path(seed_id).with_name("progress.json")


def source_rows() -> dict[str, Mapping[str, object]]:
    result = json.loads(SOURCE_RESULT.read_text(encoding="utf-8"))
    rows = {str(row["seed_id"]): row for row in result["branches"]}
    if not set(SEEDS) <= set(rows):
        raise AssertionError("Stage-D seed_3/seed_6 rows absent")
    return rows


def build_manifest() -> dict[str, object]:
    verified = json.loads(AUDIT_VERIFIED.read_text(encoding="utf-8"))
    if not verified.get("verified"):
        raise AssertionError("candidate audit is not independently verified")
    sources = []
    for seed_id, row in source_rows().items():
        if seed_id not in SEEDS:
            continue
        path = ROOT / row["checkpoint"]["path"]
        if sha256_file(path) != row["checkpoint"]["sha256"]:
            raise AssertionError(f"Stage-D source SHA mismatch: {seed_id}")
        frontier_count = sum(1 for _ in audit.iter_top_array(path, "frontier"))
        if frontier_count != int(row["frontier_size"]):
            raise AssertionError(f"Stage-D source frontier mismatch: {seed_id}")
        sources.append({
            "seed_id": seed_id,
            "path": row["checkpoint"]["path"],
            "sha256": row["checkpoint"]["sha256"],
            "bytes": path.stat().st_size,
            "frontier_count": frontier_count,
            "stage_D_expansions": int(row["expansions"]),
        })
    sources.sort(key=lambda row: SEEDS.index(str(row["seed_id"])))
    return {
        "schema": MANIFEST_SCHEMA,
        "semantics": SEMANTICS,
        "scope": "only Stage-D seed_6 and seed_3; independent additional cap per seed",
        "additional_expansion_cap_per_seed": CAP,
        "source_checkpoints_immutable": True,
        "candidate_priority_is_ordering_only": True,
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
        "sources": sources,
        "hashes": {
            "driver_sha256": sha256_file(Path(__file__)),
            "stage_D_driver_sha256": sha256_file(ROOT / "src" / "search_rr_short_ell2_r1_37_first_component_z3.py"),
            "rr_engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
            "exact_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1.py"),
            "macro_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py"),
            "candidate_file_sha256": sha256_file(CANDIDATE_FILE),
            "condition_ledger_sha256": sha256_file(LEDGER_FILE),
            "candidate_verification_sha256": sha256_file(AUDIT_VERIFIED),
        },
    }


def provenance(manifest: Mapping[str, object], seed_id: str) -> dict[str, object]:
    source = next(row for row in manifest["sources"] if row["seed_id"] == seed_id)
    return {
        "schema": SCHEMA,
        "semantics": SEMANTICS,
        "manifest_sha256": sha256_json(manifest),
        "source": source,
        "driver_sha256": manifest["hashes"]["driver_sha256"],
        "rr_engine_sha256": manifest["hashes"]["rr_engine_sha256"],
        "candidate_file_sha256": manifest["hashes"]["candidate_file_sha256"],
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": manifest["prune_registry_hash"],
        "additional_cap": CAP,
    }


def candidate_priority(state, dec, candidates, *, depth: int, serial: int) -> tuple[int, ...]:
    attempts, legal = audit.classify_candidate_attempts(
        state, dec, candidates, count_all_legal=True
    )
    best = max((int(str(row["level"])[1:]) for row in attempts), default=0)
    # Candidate distance is the only semantic ordering coordinate.  Legal
    # branching, depth, and serial are deterministic tie-breakers only.
    return (6 - best, legal, -depth, serial)


def serialize_frontier(frontier: list[tuple]) -> list[dict[str, object]]:
    rows = []
    for priority, serial, depth, relative_depth, state, dec, node_id, path_hash in frontier:
        rows.append({
            "priority": list(priority), "serial": serial, "depth": depth,
            "relative_depth": relative_depth, "state": exact.state_to_json(state),
            "decoration": dec.to_json(), "node_id": node_id, "path_hash": path_hash,
        })
    return rows


def deserialize_frontier(rows) -> list[tuple]:
    frontier = [(
        tuple(int(x) for x in row["priority"]), int(row["serial"]), int(row["depth"]),
        int(row["relative_depth"]), exact.state_from_json(row["state"]),
        rr.Decoration.from_json(row["decoration"]), str(row["node_id"]), str(row["path_hash"]),
    ) for row in rows]
    heapq.heapify(frontier)
    return frontier


def node_record(node_id: str, parent_id: str | None, edge, state, dec, depth: int,
                relative_depth: int, path_hash: str, source_node_id: str | None) -> dict[str, object]:
    return {
        "node_id": node_id,
        "parent_id": parent_id,
        "incoming_macro_edge": None if edge is None else rr.edge_json(edge),
        "exact_state_hash": rr.state_hash(state),
        "decorated_state_sha256": stage_d.decorated_digest(state, dec),
        "decoration": dec.to_json(),
        "depth": depth,
        "relative_depth": relative_depth,
        "path_hash": path_hash,
        "source_stage_D_node_id": source_node_id,
    }


def initialize(manifest: Mapping[str, object], seed_id: str, candidates) -> dict[str, object]:
    source = next(row for row in manifest["sources"] if row["seed_id"] == seed_id)
    path = ROOT / source["path"]
    frontier, nodes = [], {}
    serial = 0
    for index, row in enumerate(audit.iter_top_array(path, "frontier")):
        state = exact.state_from_json(row["state"])
        dec = rr.Decoration.from_json(row["decoration"])
        node_id = f"{seed_id}:stageE:root:{index}"
        priority = candidate_priority(state, dec, candidates, depth=int(row["depth"]), serial=serial)
        frontier.append((priority, serial, int(row["depth"]), 0, state, dec, node_id, str(row["path_hash"])))
        nodes[node_id] = node_record(
            node_id, None, None, state, dec, int(row["depth"]), 0,
            str(row["path_hash"]), str(row["node_id"]),
        )
        serial += 1
    if len(frontier) != int(source["frontier_count"]):
        raise AssertionError("Stage-E source frontier admission mismatch")
    heapq.heapify(frontier)
    return {
        "frontier": frontier, "nodes": nodes, "witnesses": [], "r2_records": [],
        "stats": Counter(expanded=0, generated_edges=0, checkpoint_count=0),
        "next_serial": serial, "next_node": 0, "stop_reason": None,
    }


def checkpoint_payload(manifest, seed_id, engine) -> dict[str, object]:
    return {
        "schema": SCHEMA, "complete_frontier_snapshot": True,
        "provenance": provenance(manifest, seed_id), "seed_id": seed_id,
        "frontier": serialize_frontier(engine["frontier"]),
        "nodes": list(engine["nodes"].values()), "witnesses": engine["witnesses"],
        "r2_records": engine["r2_records"], "stats": dict(engine["stats"]),
        "next_serial": engine["next_serial"], "next_node": engine["next_node"],
        "stop_reason": engine["stop_reason"],
    }


def write_checkpoint(manifest, seed_id, engine) -> None:
    path = checkpoint_path(seed_id)
    atomic_json(path, checkpoint_payload(manifest, seed_id, engine))
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw["provenance"] != provenance(manifest, seed_id) or len(raw["frontier"]) != len(engine["frontier"]):
        raise AssertionError("Stage-E atomic checkpoint readback failed")
    atomic_json(progress_path(seed_id), {
        "schema": "rr-short-ell2-r1-37-fz1-stage-e-progress-v1",
        "seed_id": seed_id, "timestamp": time.time(),
        "additional_expansions": int(engine["stats"]["expanded"]),
        "frontier": len(engine["frontier"]), "stop_reason": engine["stop_reason"],
        "checkpoint_sha256": sha256_file(path), "checkpoint_bytes": path.stat().st_size,
    })


def load_checkpoint(manifest, seed_id) -> dict[str, object]:
    raw = json.loads(checkpoint_path(seed_id).read_text(encoding="utf-8"))
    if raw.get("schema") != SCHEMA or raw.get("provenance") != provenance(manifest, seed_id):
        raise ValueError("foreign or stale Stage-E checkpoint")
    return {
        "frontier": deserialize_frontier(raw["frontier"]),
        "nodes": {str(row["node_id"]): row for row in raw["nodes"]},
        "witnesses": list(raw["witnesses"]), "r2_records": list(raw["r2_records"]),
        "stats": Counter(raw["stats"]), "next_serial": int(raw["next_serial"]),
        "next_node": int(raw["next_node"]), "stop_reason": raw.get("stop_reason"),
    }


def run_seed(manifest, seed_id: str, candidates, checkpoint_every: int) -> dict[str, object]:
    path = checkpoint_path(seed_id)
    engine = load_checkpoint(manifest, seed_id) if path.exists() else initialize(manifest, seed_id, candidates)
    last = int(engine["stats"]["expanded"])
    while engine["frontier"] and int(engine["stats"]["expanded"]) < CAP and engine["stop_reason"] is None:
        _priority, _serial, depth, relative_depth, state, dec, node_id, path_hash = heapq.heappop(engine["frontier"])
        engine["stats"]["expanded"] += 1
        engine["stats"]["max_depth"] = max(int(engine["stats"]["max_depth"]), depth)
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            engine["stats"]["generated_edges"] += 1
            if collision is not None or edge is None:
                engine["stats"][f"prune:{collision or 'missing_edge'}"] += 1
                continue
            verdict, after, recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            kind = pilot.edge_kind(edge)
            if kind == "R":
                engine["stats"]["R2_candidates"] += 1
                record = stage_d.r2_record(seed_id, node_id, path_hash, state, dec, edge, after, recognition, None, 0)
                engine["r2_records"].append(record)
                engine["stats"][f"R2:{recognition['r2_outcome']}"] += 1
                if record["literal_Target_A"]:
                    engine["stats"]["Target_A"] += 1
                    if record["target_b"]["target_b_survivor"]:
                        engine["stats"]["Target_B"] += 1
                        engine["stop_reason"] = "FOUND_TARGET_B"
                    else:
                        engine["stop_reason"] = "FOUND_TARGET_A"
                    break
                continue
            if verdict != "child" or after is None:
                engine["stats"][f"prune:{verdict}"] += 1
                continue
            engine["stats"][f"accepted:{kind}"] += 1
            classification = stage_d.classify_component_change(state, dec, edge, edge.state, after)
            if kind == "Z3":
                engine["stats"]["Z3_transitions"] += 1
                engine["stats"][classification["classification"]] += 1
            engine["next_node"] += 1
            child_id = f"{seed_id}:stageE:{engine['next_node']}"
            child_path_hash = sha256_json({"parent": path_hash, "edge": rr.edge_json(edge)})
            child_depth, child_relative = depth + 1, relative_depth + 1
            record = node_record(child_id, node_id, edge, edge.state, after, child_depth, child_relative, child_path_hash, None)
            engine["nodes"][child_id] = record
            if classification["is_first_component_change_candidate"]:
                witness = stage_d.event_record(
                    seed_id, node_id, child_id, child_path_hash, edge, state, dec,
                    edge.state, after, classification,
                )
                witness["witness_id"] = child_id
                engine["witnesses"].append(witness)
                engine["stop_reason"] = "FOUND_COMPONENT_CHANGING_Z3"
                break
            engine["next_serial"] += 1
            serial = engine["next_serial"]
            priority = candidate_priority(edge.state, after, candidates, depth=child_depth, serial=serial)
            children.append((priority, serial, child_depth, child_relative, edge.state, after, child_id, child_path_hash))
        for child in children:
            heapq.heappush(engine["frontier"], child)
        if int(engine["stats"]["expanded"]) - last >= checkpoint_every:
            engine["stats"]["checkpoint_count"] += 1
            write_checkpoint(manifest, seed_id, engine)
            last = int(engine["stats"]["expanded"])
        if engine["stop_reason"] is not None:
            break
    engine["stats"]["checkpoint_count"] += 1
    write_checkpoint(manifest, seed_id, engine)
    exhausted = not engine["frontier"] and engine["stop_reason"] is None
    status = (
        engine["stop_reason"] if engine["stop_reason"] is not None
        else "EXHAUSTED_NO_FZ1" if exhausted else "INCOMPLETE"
    )
    return {
        "seed_id": seed_id, "status": status,
        "additional_expansions": int(engine["stats"]["expanded"]),
        "frontier": len(engine["frontier"]), "naturally_exhausted": exhausted,
        "max_depth": int(engine["stats"]["max_depth"]),
        "FZ_counts": {level: int(engine["stats"][level]) for level in stage_d.FZ_LEVELS},
        "component_change_witnesses": len(engine["witnesses"]),
        "Target_A": int(engine["stats"]["Target_A"]), "Target_B": int(engine["stats"]["Target_B"]),
        "R2_candidates": int(engine["stats"]["R2_candidates"]),
        "prune_histogram": {k.split("prune:", 1)[1]: int(v) for k, v in sorted(engine["stats"].items()) if k.startswith("prune:")},
        "checkpoint": {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "bytes": path.stat().st_size},
    }


def write_result(manifest, rows) -> None:
    payload = {
        "schema": RESULT_SCHEMA, "semantics": SEMANTICS,
        "manifest_sha256": sha256_json(manifest), "additional_cap_per_seed": CAP,
        "branches": rows,
        "aggregate": {
            "additional_expansions": sum(int(row["additional_expansions"]) for row in rows),
            "frontier": sum(int(row["frontier"]) for row in rows),
            "component_change_witnesses": sum(int(row["component_change_witnesses"]) for row in rows),
            "Target_A": sum(int(row["Target_A"]) for row in rows),
            "Target_B": sum(int(row["Target_B"]) for row in rows),
        },
        "overall_status": (
            "FOUND_TARGET_B" if any(row["Target_B"] for row in rows)
            else "FOUND_TARGET_A" if any(row["Target_A"] for row in rows)
            else "FZ1_EXACT_WITNESS_FOUND" if any(row["component_change_witnesses"] for row in rows)
            else "FZ1_LOCAL_CANDIDATES_ALL_OBSTRUCTED" if all(row["naturally_exhausted"] for row in rows)
            else "STAGE_E_INCOMPLETE"
        ),
        "interpretation": "A nonempty capped frontier is INCOMPLETE; zero events there are observations only.",
    }
    atomic_json(RESULT_OUT, payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-id", choices=SEEDS)
    parser.add_argument("--initialize-only", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=10_000)
    args = parser.parse_args()
    candidate_payload, candidates = audit.build_candidate_table()
    stored_candidates = json.loads(CANDIDATE_FILE.read_text(encoding="utf-8"))
    if stored_candidates["candidate_orbits"] != candidate_payload["candidate_orbits"]:
        raise AssertionError("candidate table changed before Stage E")
    manifest = build_manifest()
    if MANIFEST_OUT.exists() and json.loads(MANIFEST_OUT.read_text(encoding="utf-8")) != manifest:
        raise AssertionError("Stage-E manifest changed")
    if not MANIFEST_OUT.exists():
        atomic_json(MANIFEST_OUT, manifest)
    selected = (args.seed_id,) if args.seed_id else SEEDS
    rows = []
    for seed_id in selected:
        if args.initialize_only:
            engine = initialize(manifest, seed_id, candidates)
            write_checkpoint(manifest, seed_id, engine)
            row = {"seed_id": seed_id, "status": "INITIALIZED", "additional_expansions": 0, "frontier": len(engine["frontier"])}
        else:
            row = run_seed(manifest, seed_id, candidates, args.checkpoint_every)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        if row["status"].startswith("FOUND"):
            break
    if not args.initialize_only:
        if len(rows) == len(SEEDS):
            write_result(manifest, rows)
        elif RESULT_OUT.exists():
            old = json.loads(RESULT_OUT.read_text(encoding="utf-8"))
            merged = {str(row["seed_id"]): row for row in old["branches"]}
            merged.update({str(row["seed_id"]): row for row in rows})
            if set(merged) == set(SEEDS):
                write_result(manifest, [merged[seed] for seed in SEEDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
