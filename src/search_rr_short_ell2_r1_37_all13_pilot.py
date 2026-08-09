#!/usr/bin/env python3
"""Round 56: exact, branch-local pilot for all 13 r1_37 frontier roots.

The immutable Round-53/v7 checkpoint is read only to recover the exact stored
frontier states.  Each selected state is then searched in a fresh, independent
checkpoint namespace with no budget transfer.  A cap with nonempty frontier
is always INCOMPLETE.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_pilot_plan.json"
FRONTIER_AUDIT = ROOT / "outputs" / "rr_short_ell2_r1_37_frontier.json"
SOURCE_CHECKPOINT = (
    ROOT / "outputs" / "checkpoints" / "rr_short5" / "top2_continuation_v7"
    / "short_ell2" / "short_ell2_r1_37" / "checkpoint.json"
)
CHECKPOINT_ROOT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_37_all13_v8"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_pilot_results.json"
BRIDGE_LEDGER = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_bridge_ledger.json"

CHECKPOINT_SCHEMA = "rr-short-ell2-r1-37-all13-checkpoint-v8"
RESULT_SCHEMA = "rr-short-ell2-r1-37-all13-pilot-v1"
BRIDGE_SCHEMA = "rr-short-ell2-r1-37-all13-bridge-ledger-v1"
SOURCE_CHECKPOINT_SHA = "2847a6bd5861476428ec7cd9bd9d1d855229b33378662ebeef4ae4db832b1551"
R2_SEMANTICS = "R2_LITERAL_JOINT_SOURCE_V1"
B_LEVELS = tuple(f"B{i}" for i in range(7))


def load_module(name: str, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module("rr_all13_frontier_audit", ROOT / "src" / "analyze_rr_short_ell2_r1_37_frontier.py")
v7, rr, exact, pilot = audit.v7, audit.rr, audit.exact, audit.pilot
target_b = pilot.target_b


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def edge_from_json(state, data: Mapping[str, object]):
    return pilot.edge_from_json(state, data)


def safe_state_dir(state_id: str) -> str:
    return "state_" + state_id.rsplit(":", 1)[1]


def checkpoint_path(state_id: str) -> Path:
    return CHECKPOINT_ROOT / safe_state_dir(state_id) / "checkpoint.json"


def source_frontier() -> dict[str, Mapping[str, object]]:
    rows = audit.extract_frontier(SOURCE_CHECKPOINT)
    return {str(row["node_id"]): row for row in rows}


def plan_rows() -> list[dict[str, object]]:
    raw = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = [dict(row) for row in raw["state_selection_ledger"]]
    if len(rows) != 13 or len({str(row["state_id"]) for row in rows}) != 13:
        raise AssertionError("all-13 plan is incomplete")
    if any(int(row["planned_additional_expansion_cap"]) != 10_000 for row in rows):
        raise AssertionError("all-13 plan has unequal caps")
    return rows


def initial_state(plan_row: Mapping[str, object], stored: Mapping[str, object]):
    state = exact.state_from_json(stored["state"])
    dec = rr.Decoration.from_json(stored["decoration"])
    if rr.state_hash(state) != plan_row["exact_state_hash"]:
        raise AssertionError(f"starting state hash mismatch: {plan_row['state_id']}")
    if dec.r_count != 1 or state.F != 1 or state.H != 0 or state.Ndef != 1:
        raise AssertionError("starting state left approved Target-A-safe slab")
    return state, dec


def provenance(plan_row: Mapping[str, object], *, cap: int, checkpoint_every: int) -> dict[str, object]:
    payload = {
        "state_id": plan_row["state_id"],
        "starting_state_hash": plan_row["exact_state_hash"],
        "parent_replay_hash": plan_row["parent_replay_hash"],
        "source_checkpoint_path": str(SOURCE_CHECKPOINT.relative_to(ROOT)),
        "source_checkpoint_sha256": SOURCE_CHECKPOINT_SHA,
        "frontier_audit_sha256": sha256_file(FRONTIER_AUDIT),
        "plan_sha256": sha256_file(PLAN),
        "runner_sha256": sha256_file(Path(__file__)),
        "rr_engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "exact_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1.py"),
        "macro_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py"),
        "recognizer_semantics": R2_SEMANTICS,
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "additional_cap": cap,
        "checkpoint_every": checkpoint_every,
        "budget_transfer": False,
    }
    return {**payload, "config_sha256": sha256_json(payload)}


def node_record(node_id: str, parent_id: str | None, edge, state, dec, *,
                depth: int, relative_depth: int, path_hash: str) -> dict[str, object]:
    return {
        "node_id": node_id, "parent_id": parent_id,
        "incoming_macro_edge": None if edge is None else rr.edge_json(edge),
        "exact_state_hash": rr.state_hash(state), "decoration": dec.to_json(),
        "depth": depth, "relative_depth": relative_depth, "path_hash": path_hash,
    }


def serialize_frontier(frontier) -> list[dict[str, object]]:
    return [
        {"depth": depth, "relative_depth": relative_depth,
         "state": exact.state_to_json(state), "decoration": dec.to_json(),
         "node_id": node_id, "path_hash": path_hash}
        for depth, relative_depth, state, dec, node_id, path_hash in frontier
    ]


def checkpoint_payload(*, prov, plan_row, root_state, root_dec, frontier, nodes,
                       r2_records, bridge_records, stats, next_node) -> dict[str, object]:
    return {
        "schema": CHECKPOINT_SCHEMA, "complete_frontier_snapshot": True,
        "provenance": prov, "state_plan": dict(plan_row),
        "starting_state": exact.state_to_json(root_state),
        "starting_decoration": root_dec.to_json(),
        "frontier": serialize_frontier(frontier), "nodes": list(nodes.values()),
        "r2_records": r2_records, "bridge_records": bridge_records,
        "stats": dict(stats), "next_node": next_node,
    }


def load_checkpoint(path: Path, expected_provenance: Mapping[str, object], plan_row: Mapping[str, object]):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != CHECKPOINT_SCHEMA or not raw.get("complete_frontier_snapshot"):
        raise ValueError("foreign or incomplete all13 checkpoint")
    if raw.get("provenance") != dict(expected_provenance) or raw.get("state_plan") != dict(plan_row):
        raise ValueError("all13 checkpoint provenance/config mismatch")
    frontier = [
        (int(row["depth"]), int(row["relative_depth"]), exact.state_from_json(row["state"]),
         rr.Decoration.from_json(row["decoration"]), str(row["node_id"]), str(row["path_hash"]))
        for row in raw["frontier"]
    ]
    nodes = {str(row["node_id"]): row for row in raw["nodes"]}
    return (frontier, nodes, list(raw["r2_records"]), list(raw["bridge_records"]),
            Counter(raw["stats"]), int(raw["next_node"]), raw)


def component_merge(parent_state, parent_dec, child_state, child_dec) -> bool:
    return audit.exact_bridge(parent_state, parent_dec, child_state, child_dec)


_KNOWN18: dict[str, list[str]] | None = None


def known18_map() -> dict[str, list[str]]:
    global _KNOWN18
    if _KNOWN18 is None:
        result: dict[str, list[str]] = {}
        for row in target_b.historical_18():
            state = row["state"]
            alpha = target_b.action_to_identity(state)
            canonical = exact.relabel_state(state, alpha)
            result.setdefault(rr.state_hash(canonical), []).append(str(row["known_id"]))
        _KNOWN18 = result
    return _KNOWN18


def target_b_analysis(boundary_state) -> dict[str, object]:
    alpha = target_b.action_to_identity(boundary_state)
    canonical = exact.relabel_state(boundary_state, alpha)
    canonical_hash = rr.state_hash(canonical)
    known = known18_map().get(canonical_hash, [])
    if known:
        return {
            "canonical_state_hash": canonical_hash,
            "known18_classification": "PROVED_LEFT_S6_EQUIVALENT",
            "known18_matches": known,
            "status": "KNOWN18_HELPER_FREE_CERTIFICATE_REUSED",
            "certificate": "outputs/rr_target_b_18_boundary_corrected_ledger.json",
            "phase_helper_used": False,
            "target_b_survivor": False,
        }
    stage = target_b.target_b_stage(canonical)
    if stage["status"] == "REQUIRES_EXACT_HELPER_FREE_DFS":
        stage["exact_flow"] = target_b.run_flow(canonical, node_cap=2_000_000, seconds=3600.0)
        stage["final_status"] = stage["exact_flow"]["verdict"]
    else:
        stage["exact_flow"] = None
        stage["final_status"] = stage["status"]
    return {
        "canonical_state_hash": canonical_hash,
        "known18_classification": "GENUINELY_NEW_AGAINST_KNOWN18",
        "known18_matches": [], "phase_helper_used": False,
        "target_b_survivor": bool(stage.get("exact_flow") and stage["exact_flow"]["verdict"] == "FOUND_ENGINE_CONTINUATION"),
        **stage,
    }


def r2_record(state, dec, edge, after_dec, recognition, *, node_id: str,
              relative_depth: int, path_hash: str) -> dict[str, object]:
    record = {
        "predecessor_node_id": node_id, "predecessor_path_hash": path_hash,
        "timing": "immediate" if relative_depth == 0 else "later",
        "relative_depth": relative_depth, "edge": rr.edge_json(edge),
        "macro_entry_state_hash": rr.state_hash(state),
        "literal_joint_source_state_hash": rr.state_hash(edge.run.state),
        "post_R2_state_hash": rr.state_hash(edge.state),
        "decoration_before": dec.to_json(), "decoration_after": after_dec.to_json(),
        "recognizer": recognition, "literal_Target_A": bool(recognition["is_target_a"]),
    }
    if recognition["is_target_a"]:
        record["boundary_state"] = exact.state_to_json(edge.state)
        record["target_b"] = target_b_analysis(edge.state)
    return record


def empty_level_counter() -> Counter[str]:
    return Counter({level: 0 for level in B_LEVELS})


def run_state(plan_row: Mapping[str, object], stored: Mapping[str, object], *,
              cap: int, checkpoint_every: int, resume: bool, initialize_only: bool) -> dict[str, object]:
    state_id = str(plan_row["state_id"])
    root_state, root_dec = initial_state(plan_row, stored)
    prov = provenance(plan_row, cap=cap, checkpoint_every=checkpoint_every)
    path = checkpoint_path(state_id)
    if path.exists() and not resume:
        raise FileExistsError(f"refusing to overwrite all13 checkpoint: {path}")
    if resume:
        frontier, nodes, r2_records, bridge_records, stats, next_node, _ = load_checkpoint(path, prov, plan_row)
    else:
        root_node = f"{state_id}:pilot:0"
        root_path_hash = sha256_json({
            "parent_replay_hash": plan_row["parent_replay_hash"],
            "starting_state_hash": plan_row["exact_state_hash"],
        })
        depth = int(plan_row["depth"])
        frontier = [(depth, 0, root_state, root_dec, root_node, root_path_hash)]
        nodes = {root_node: node_record(root_node, None, None, root_state, root_dec,
                                       depth=depth, relative_depth=0, path_hash=root_path_hash)}
        r2_records, bridge_records = [], []
        stats = Counter(expanded=0, generated_edges=0, checkpoint_count=0)
        stats.update(empty_level_counter())
        next_node = 1
        payload = checkpoint_payload(
            prov=prov, plan_row=plan_row, root_state=root_state, root_dec=root_dec,
            frontier=frontier, nodes=nodes, r2_records=r2_records,
            bridge_records=bridge_records, stats=stats, next_node=next_node,
        )
        atomic_json(path, payload)
        persisted = json.loads(path.read_text(encoding="utf-8"))
        if persisted.get("provenance") != prov or persisted.get("schema") != CHECKPOINT_SCHEMA:
            raise AssertionError("initial all13 checkpoint persistence failed")
    if initialize_only:
        return summarize_state(path, plan_row, frontier, nodes, r2_records, bridge_records, stats, prov)

    started = time.monotonic()
    while frontier and stats["expanded"] < cap:
        depth, relative_depth, state, dec, node_id, path_hash = frontier.pop()
        stats["expanded"] += 1
        stats["max_depth"] = max(int(stats["max_depth"]), depth)
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] += 1
            if collision is not None or edge is None:
                stats[f"prune:{collision or 'missing_edge'}"] += 1
                continue
            verdict, after_dec, recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            kind = pilot.edge_kind(edge)
            if kind == "R":
                if after_dec is None or recognition is None or after_dec.r_count != 2:
                    raise AssertionError("R2 candidate missing literal-source recognition")
                if recognition["source_state_semantic_tag"] != R2_SEMANTICS:
                    raise AssertionError("R2 candidate used wrong semantic source")
                record = r2_record(state, dec, edge, after_dec, recognition,
                                   node_id=node_id, relative_depth=relative_depth, path_hash=path_hash)
                r2_records.append(record)
                timing = record["timing"]
                stats[f"R2:{timing}:total"] += 1
                stats[f"R2:{timing}:outcome:{recognition['r2_outcome']}"] += 1
                if recognition["is_target_a"]:
                    stats["literal_Target_A"] += 1
                    level = "B6" if record["target_b"]["target_b_survivor"] else "B5"
                    stats[level] += 1
                    if level == "B6":
                        stats["Target_B_survivor"] += 1
                continue
            if verdict != "child":
                stats[f"prune:{verdict}"] += 1
                continue
            if after_dec is None or after_dec.r_count != 1:
                raise AssertionError("accepted child left post-R1/pre-R2 universe")
            child_state = edge.state
            child_id = f"{state_id}:pilot:{next_node}"
            next_node += 1
            edge_data = rr.edge_json(edge)
            child_path_hash = sha256_json({"parent_path_hash": path_hash, "edge": edge_data})
            child_depth, child_relative = depth + 1, relative_depth + 1
            nodes[child_id] = node_record(
                child_id, node_id, edge, child_state, after_dec,
                depth=child_depth, relative_depth=child_relative, path_hash=child_path_hash,
            )
            stats[f"accepted:{kind}"] += 1
            if component_merge(state, dec, child_state, after_dec):
                witness = v7.bridge_record(
                    state, dec, edge, child_state, after_dec,
                    child_id=child_id, parent_id=node_id,
                )
                if witness is None:
                    raise AssertionError("component merge lacked bridge witness")
                level = "B2"
                if witness["future_R2_source_admissible"]:
                    level = "B3"
                if level == "B3" and witness["terminal_geometry_available"]:
                    level = "B4"
                witness["maximum_level"] = level
                witness["path_hash"] = child_path_hash
                bridge_records.append(witness)
                stats[level] += 1
                stats["component_merge"] += 1
                if witness["template_match"]:
                    stats["bridge_template"] += 1
            else:
                stats["B0"] += 1
            children.append((child_depth, child_relative, child_state, after_dec, child_id, child_path_hash))
        children.sort(key=lambda row: row[4], reverse=True)
        frontier.extend(children)
        if stats["expanded"] % checkpoint_every == 0:
            stats["checkpoint_count"] += 1
            stats["elapsed_seconds"] += time.monotonic() - started
            atomic_json(path, checkpoint_payload(
                prov=prov, plan_row=plan_row, root_state=root_state, root_dec=root_dec,
                frontier=frontier, nodes=nodes, r2_records=r2_records,
                bridge_records=bridge_records, stats=stats, next_node=next_node,
            ))
            started = time.monotonic()
    stats["elapsed_seconds"] += time.monotonic() - started
    stats["checkpoint_count"] += 1
    atomic_json(path, checkpoint_payload(
        prov=prov, plan_row=plan_row, root_state=root_state, root_dec=root_dec,
        frontier=frontier, nodes=nodes, r2_records=r2_records,
        bridge_records=bridge_records, stats=stats, next_node=next_node,
    ))
    return summarize_state(path, plan_row, frontier, nodes, r2_records, bridge_records, stats, prov)


def summarize_state(path: Path, plan_row: Mapping[str, object], frontier, nodes,
                    r2_records, bridge_records, stats, prov) -> dict[str, object]:
    level_counts = {level: int(stats[level]) for level in B_LEVELS}
    exhausted = not frontier
    status = "EXHAUSTED_NO_BRIDGE" if exhausted and not bridge_records else "INCOMPLETE"
    if bridge_records:
        status = "FOUND_COMPONENT_MERGE"
    if stats["literal_Target_A"]:
        status = "FOUND_TARGET_A"
    if stats["Target_B_survivor"]:
        status = "FOUND_TARGET_B"
    r2_outcomes = {
        timing: {
            key.split(f"R2:{timing}:outcome:", 1)[1]: int(value)
            for key, value in stats.items() if key.startswith(f"R2:{timing}:outcome:")
        }
        for timing in ("immediate", "later")
    }
    return {
        "state_id": plan_row["state_id"], "starting_state_hash": plan_row["exact_state_hash"],
        "parent_replay_hash": plan_row["parent_replay_hash"], "status": status,
        "additional_cap": int(prov["additional_cap"]), "expansions": int(stats["expanded"]),
        "frontier_size": len(frontier), "max_depth": int(stats["max_depth"]),
        "naturally_exhausted": exhausted, "node_count": len(nodes),
        "component_merge_count": len(bridge_records),
        "bridge_count": sum(bool(row["template_match"]) for row in bridge_records),
        "B0_B6_maximum_level_counts": level_counts,
        "R2_outcomes": r2_outcomes, "R2_record_count": len(r2_records),
        "literal_Target_A_count": int(stats["literal_Target_A"]),
        "Target_B_survivor_count": int(stats["Target_B_survivor"]),
        "stats": dict(sorted(stats.items())),
        "checkpoint": {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                       "sha256": sha256_file(path), "schema": CHECKPOINT_SCHEMA},
        "provenance_sha256": sha256_json(prov),
    }


def write_aggregate(rows: list[Mapping[str, object]], planned_ids: list[str]) -> None:
    by_id = {str(row["state_id"]): dict(row) for row in rows}
    ordered = [by_id[state_id] for state_id in planned_ids if state_id in by_id]
    status_counts = Counter(str(row["status"]) for row in ordered)
    overall = "ALL13_PILOT_PARTIAL"
    if len(ordered) == 13 and all(row["naturally_exhausted"] for row in ordered):
        overall = "ALL13_PILOT_ALL_EXHAUSTED"
    if any(row["component_merge_count"] for row in ordered):
        overall = "FOUND_COMPONENT_MERGE"
    if any(row["literal_Target_A_count"] for row in ordered):
        overall = "FOUND_TARGET_A"
    if any(row["Target_B_survivor_count"] for row in ordered):
        overall = "FOUND_TARGET_B"
    aggregate_levels = Counter()
    for row in ordered:
        aggregate_levels.update(row["B0_B6_maximum_level_counts"])
    result = {
        "schema": RESULT_SCHEMA, "overall_status": overall,
        "scope": "independent all-13 capped pilot; cap with nonempty frontier is INCOMPLETE",
        "planned_state_count": 13, "completed_state_records": len(ordered),
        "total_maximum_expansions": 130_000, "budget_transfer": False,
        "status_counts": dict(sorted(status_counts.items())),
        "aggregate": {
            "expansions": sum(int(row["expansions"]) for row in ordered),
            "frontier_size": sum(int(row["frontier_size"]) for row in ordered),
            "component_merges": sum(int(row["component_merge_count"]) for row in ordered),
            "bridges": sum(int(row["bridge_count"]) for row in ordered),
            "literal_Target_A": sum(int(row["literal_Target_A_count"]) for row in ordered),
            "Target_B_survivors": sum(int(row["Target_B_survivor_count"]) for row in ordered),
            "B0_B6": {level: int(aggregate_levels[level]) for level in B_LEVELS},
        },
        "branches": ordered,
        "inputs": {"plan_sha256": sha256_file(PLAN), "frontier_audit_sha256": sha256_file(FRONTIER_AUDIT),
                   "source_checkpoint_sha256": SOURCE_CHECKPOINT_SHA},
    }
    bridge = {
        "schema": BRIDGE_SCHEMA, "overall_status": overall,
        "branches": [
            {"state_id": row["state_id"], "component_merge_count": row["component_merge_count"],
             "bridge_count": row["bridge_count"], "B0_B6": row["B0_B6_maximum_level_counts"],
             "checkpoint_sha256": row["checkpoint"]["sha256"]}
            for row in ordered
        ],
        "aggregate": result["aggregate"],
        "full_witness_location": "per-state v8 checkpoints: bridge_records and r2_records",
    }
    atomic_json(RESULT, result)
    atomic_json(BRIDGE_LEDGER, bridge)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cap", type=int, default=10_000)
    parser.add_argument("--checkpoint-every", type=int, default=1_000)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--initialize-only", action="store_true")
    parser.add_argument("--state-id")
    args = parser.parse_args()
    if args.cap != 10_000 or args.checkpoint_every <= 0:
        raise ValueError("Round-56 gate requires the approved 10,000 independent cap")
    if SOURCE_CHECKPOINT.stat().st_size != 4_884_573_885:
        raise AssertionError("immutable v7 checkpoint size changed")
    planned = plan_rows()
    selected = [row for row in planned if args.state_id is None or row["state_id"] == args.state_id]
    if args.state_id is not None and len(selected) != 1:
        raise ValueError("unknown state id")
    stored = source_frontier()
    prior_rows = []
    if RESULT.exists() and args.resume:
        prior_rows = json.loads(RESULT.read_text(encoding="utf-8"))["branches"]
    completed = {str(row["state_id"]): row for row in prior_rows}
    for row in selected:
        state_id = str(row["state_id"])
        if state_id not in stored:
            raise AssertionError(f"planned state absent from immutable frontier: {state_id}")
        result = run_state(
            row, stored[state_id], cap=args.cap, checkpoint_every=args.checkpoint_every,
            resume=args.resume and checkpoint_path(state_id).exists(), initialize_only=args.initialize_only,
        )
        completed[state_id] = result
        write_aggregate(list(completed.values()), [str(item["state_id"]) for item in planned])
        print(json.dumps({"state_id": state_id, "status": result["status"],
                          "expansions": result["expansions"], "frontier": result["frontier_size"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
