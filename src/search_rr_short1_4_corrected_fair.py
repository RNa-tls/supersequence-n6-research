#!/usr/bin/env python3
"""Corrected v5 fair admission pilots for ``short_ell1`` through ``short_ell4``.

This is a fresh traversal namespace.  It deliberately does not load a v1--v4
checkpoint or hierarchy artifact.  First, each bare short root receives a
small pre-R admission traversal; every observed legal R1 edge is replayed and
frozen as a provenance subroot.  Secondly, every frozen child receives the
same positive cap in an independent branch-local checkpoint.

The cap is an observational device: nonempty frontiers are always reported as
``INCOMPLETE``.  R2 predicates consume the literal joint source
``edge.run.state`` through the typed wrapper supplied by the Round-48 engine.
"""
from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs" / "rr_short1_4_corrected_fair_results.json"
CLASSES = ROOT / "outputs" / "rr_short1_4_target_a_classes.json"
PROFILES = ROOT / "outputs" / "rr_short5_cross_root_profiles.json"
CHECKPOINT_ROOT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "corrected_v5"

SCHEMA = "rr-short1-4-corrected-fair-v5-literal-r2-source"
CHECKPOINT_SCHEMA = "rr-short1-4-corrected-fair-checkpoint-v5-literal-r2-source"
ADMISSION_SCHEMA = "rr-short1-4-r1-admission-v5-literal-r2-source"
R2_SEMANTICS = "R2_LITERAL_JOINT_SOURCE_V1"
ROOT_IDS = ("short_ell1", "short_ell2", "short_ell3", "short_ell4")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


short5 = load("rr_short14_short5", ROOT / "src" / "search_rr_short5_exact.py")
rr = short5.rr
exact, core = rr.exact, rr.core
repair = load("rr_short14_repair", ROOT / "src" / "search_rr_short_ell0_repair_fair.py")
target_b = load("rr_short14_target_b", ROOT / "src" / "analyze_rr_short_ell0_target_b.py")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def working_set_bytes() -> int:
    """Current-process working set on Windows; zero only on an OS API failure."""
    try:
        class COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]
        counters = COUNTERS()
        counters.cb = ctypes.sizeof(COUNTERS)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            return int(counters.WorkingSetSize)
    except (AttributeError, OSError):
        pass
    return 0


def root_records() -> dict[str, dict[str, object]]:
    records = {str(row["root_id"]): row for row in short5.short_root_records()}
    if set(ROOT_IDS) - set(records):
        raise AssertionError("Round-37 short-root manifest is incomplete")
    return {root_id: records[root_id] for root_id in ROOT_IDS}


def replay_trace(root: Mapping[str, object], trace: list[Mapping[str, object]]):
    state, dec = rr.initial_decoration(root)
    for item in trace:
        label = str(item["label"])
        edge = next((candidate for candidate, collision in rr.iter_raw_macro_candidates(state)
                     if collision is None and candidate is not None and candidate.label == label), None)
        if edge is None:
            raise AssertionError(f"literal trace edge unavailable: {label}")
        dec = rr.advance_decoration(edge.run.state, edge.joint, dec)
        state = edge.state
    return state, dec


def edge_kind(edge) -> str:
    return rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit)


def component_summary_json(state) -> dict[str, object]:
    """Drop tuple-keyed lookup tables; retain independently replayable components."""
    summary = rr.component_summary(state)
    return {"component_count": summary["component_count"], "components": summary["components"]}


def prefix_relation(traces: list[list[Mapping[str, object]]]) -> dict[str, object]:
    if not traces:
        return {"present": False, "deepest_trace": [], "relations": []}
    serial = lambda trace: [str(item["label"]) for item in trace]
    deepest = max(traces, key=lambda trace: (len(trace), tuple(serial(trace))))
    deepest_labels = serial(deepest)
    return {
        "present": all(serial(trace) == deepest_labels[:len(trace)] for trace in traces),
        "deepest_trace": deepest,
        "relations": [
            {"trace": trace, "is_prefix_of_deepest": serial(trace) == deepest_labels[:len(trace)]}
            for trace in traces
        ],
    }


def admission(root: Mapping[str, object], budget: int) -> dict[str, object]:
    """Bounded, pre-R-only root admission; it never schedules a post-R1 node."""
    state, dec = rr.initial_decoration(root)
    if dec.r_count != 0:
        raise AssertionError("bare short root did not start before R1")
    frontier = [(0, state, dec, tuple())]
    seen = {rr.decorated_key(state, dec)}
    stats = Counter(expanded=0, generated_edges=0)
    r1_events: dict[str, dict[str, object]] = {}
    max_depth = 0
    while frontier and stats["expanded"] < budget:
        depth, state, dec, trace = frontier.pop()
        if dec.r_count != 0:
            raise AssertionError("admission scheduled a post-R1 state")
        stats["expanded"] += 1
        max_depth = max(max_depth, depth)
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] += 1
            if collision is not None:
                stats[f"prune:{collision}"] += 1
                continue
            assert edge is not None
            kind = edge_kind(edge)
            verdict, child_dec, _recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            if kind == "R":
                if verdict != "child" or child_dec is None or child_dec.r_count != 1:
                    raise AssertionError("literal R1 child was not admitted")
                event_id, event = rr.r1_event_export(edge, dec, child_dec, trace)
                prior = r1_events.get(event_id)
                if prior is not None and prior != event:
                    raise AssertionError("R1 event id collision")
                r1_events[event_id] = event
                stats["R1_events"] += 1
                continue
            if verdict != "child":
                stats[f"prune:{verdict}"] += 1
                continue
            if child_dec is None or child_dec.r_count != 0:
                raise AssertionError("pre-R admission accepted an invalid child")
            key = rr.decorated_key(edge.state, child_dec)
            if key in seen:
                stats["memo_duplicates"] += 1
                continue
            seen.add(key)
            children.append((depth + 1, edge.state, child_dec, trace + (rr.edge_json(edge),)))
        children.sort(key=lambda row: tuple(item["label"] for item in row[3]), reverse=True)
        frontier.extend(children)
    traces = [list(event["literal_macro_trace"]) for _event_id, event in sorted(r1_events.items())]
    child_rows = []
    for index, (event_id, event) in enumerate(sorted(r1_events.items())):
        trace = list(event["literal_macro_trace"])
        child_state, child_dec = replay_trace(root, trace)
        if child_dec.r_count != 1 or child_dec.r1 is None:
            raise AssertionError("frozen R1 replay did not produce exactly one R")
        # Reconstruct the last macro edge and replay the exported event byte-for-byte.
        pre_state, pre_dec = replay_trace(root, trace[:-1])
        last = next((edge for edge, collision in rr.iter_raw_macro_candidates(pre_state)
                     if collision is None and edge is not None and edge.label == trace[-1]["label"]), None)
        if last is None:
            raise AssertionError("frozen R1 last edge disappeared")
        replay_id, replay_event = rr.r1_event_export(last, pre_dec, child_dec, tuple(trace[:-1]))
        if replay_id != event_id or replay_event != event:
            raise AssertionError("R1 event literal replay mismatch")
        branch_id = f"{root['root_id']}_r1_{index}"
        origin_hash = sha256_bytes(repr((branch_id, event_id, rr.decorated_key(child_state, child_dec))).encode("utf-8"))
        child_rows.append({
            "branch_id": branch_id, "branch_origin_hash": origin_hash,
            "r1_event_id": event_id, "literal_macro_trace": trace,
            "literal_R1_event": event, "exact_state": exact.state_to_json(child_state),
            "exact_state_hash": rr.state_hash(child_state),
            "decorated_key": repr(rr.decorated_key(child_state, child_dec)),
            "r1": asdict(child_dec.r1), "ell": last.run.ell, "joint_label": last.joint.move.label,
            "Phi": rr.phi(child_state), "M": child_state.P - 5 * child_state.O,
            "coordinate": {"P": child_state.P, "O": child_state.O, "F": child_state.F,
                           "H": child_state.H, "Ndef": child_state.Ndef},
            "hub": {"id": child_dec.hub_id, "mask": rr.hub_mask(child_state, child_dec),
                    "popcount": rr.hub_mask(child_state, child_dec).bit_count()},
            "completer": None if child_dec.completer is None else asdict(child_dec.completer),
            "event_order_class": child_dec.event_order_class,
        })
    return {
        "schema": ADMISSION_SCHEMA,
        "root_id": root["root_id"], "budget": budget, "expanded": stats["expanded"],
        "frontier_size": len(frontier), "naturally_exhausted": not frontier,
        "max_depth": max_depth, "stats": dict(sorted(stats.items())),
        "frozen_R1_children": child_rows,
        "preparation_spine": prefix_relation(traces),
        "scope": "bounded pre-R admission; frozen R1 children are observed children only",
    }


def state_key_audit(root: Mapping[str, object], children: list[Mapping[str, object]]) -> dict[str, object]:
    """Lossless-key local regression, including all frozen post-R1 roots."""
    groups: dict[tuple[object, ...], list[tuple[object, object]]] = defaultdict(list)
    inspected = 0
    for child in children:
        state, dec = replay_trace(root, list(child["literal_macro_trace"]))
        queue = [(0, state, dec)]
        while queue:
            depth, state, dec = queue.pop()
            inspected += 1
            key = rr.decorated_key(state, dec)
            restored = exact.state_from_json(exact.state_to_json(state))
            restored_dec = rr.Decoration.from_json(dec.to_json())
            if rr.decorated_key(restored, restored_dec) != key:
                raise AssertionError("post-R1 JSON roundtrip changed decorated key")
            groups[key].extend(((state, dec), (state, dec)))
            if depth < 2:
                for edge, collision in rr.iter_raw_macro_candidates(state):
                    if collision is not None or edge is None:
                        continue
                    verdict, after, _recognition = rr.evaluate_edge(
                        state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
                    )
                    if verdict == "child" and after is not None:
                        queue.append((depth + 1, edge.state, after))
    mismatches = []
    for key, samples in groups.items():
        signatures = {rr.successor_signature(state, dec, prune_profile=rr.TARGET_A_SAFE_PROFILE)
                      for state, dec in samples}
        if len(signatures) != 1:
            mismatches.append(sha256_bytes(repr(key).encode("utf-8")))
    return {
        "grade": "exhaustive tested-universe equivalence; not a theorem",
        "scope": "all admitted R1 children and their accepted successors through depth 2",
        "states_examined": inspected, "duplicate_key_groups": len(groups),
        "mismatches": mismatches, "passed": not mismatches,
    }


def branch_config(root: Mapping[str, object], child: Mapping[str, object], budget: int) -> dict[str, object]:
    return {
        "schema": "rr-short1-4-corrected-fair-config-v5",
        "checkpoint_payload_schema": CHECKPOINT_SCHEMA,
        # JSON-stable identity is required because the verifier reads the
        # same root record back from an aggregate JSON result.
        "root_id": root["root_id"], "root_hash": sha256_json(root),
        "branch_id": child["branch_id"], "branch_origin_hash": child["branch_origin_hash"],
        "r1_event_id": child["r1_event_id"], "budget": budget,
        "scheduler": "independent-equal-positive-cap-v5",
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
        "recognizer_semantics": R2_SEMANTICS,
        "macro_entry_semantics": rr.R2_MACRO_ENTRY_PROVENANCE_TAG,
        "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "repair_driver_sha256": sha256_file(ROOT / "src" / "search_rr_short_ell0_repair_fair.py"),
        "pilot_driver_sha256": sha256_file(Path(__file__)),
    }


def serialize_frontier(frontier):
    return [{"depth": depth, "state": exact.state_to_json(state), "decoration": dec.to_json(),
             "node_id": node_id, "lineage": list(lineage)}
            for depth, state, dec, node_id, lineage in frontier]


def checkpoint_payload(config, root, child, frontier, seen, nodes, repairs, r2_paths, stats, next_node, next_repair):
    return {
        "schema": CHECKPOINT_SCHEMA, "config": config, "root": dict(root), "child": dict(child),
        "frontier": serialize_frontier(frontier), "seen_keys": sorted(repr(key) for key in seen),
        "nodes": list(nodes.values()), "repair_events": list(repairs.values()), "r2_paths": r2_paths,
        "stats": dict(stats), "next_node": next_node, "next_repair": next_repair,
        "complete_frontier_snapshot": True,
    }


def load_checkpoint(path: Path, config: Mapping[str, object], root: Mapping[str, object], child: Mapping[str, object]):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("v1-v4 or foreign checkpoint schema rejected by v5 runner")
    if raw.get("config") != dict(config):
        raise ValueError("checkpoint config/engine/recognizer semantics mismatch")
    if raw.get("root") != dict(root) or raw.get("child") != dict(child):
        raise ValueError("checkpoint root or R1 provenance mismatch")
    if not raw.get("complete_frontier_snapshot"):
        raise ValueError("checkpoint lacks a complete atomic frontier")
    frontier = [(int(row["depth"]), exact.state_from_json(row["state"]),
                 rr.Decoration.from_json(row["decoration"]), str(row["node_id"]),
                 tuple(str(value) for value in row["lineage"])) for row in raw["frontier"]]
    seen = {ast.literal_eval(text) for text in raw["seen_keys"]}
    if not all(isinstance(key, tuple) for key in seen):
        raise ValueError("checkpoint contains malformed decorated key")
    nodes = {str(row["node_id"]): row for row in raw["nodes"]}
    repairs = {str(row["event_id"]): row for row in raw["repair_events"]}
    return (frontier, seen, nodes, repairs, list(raw["r2_paths"]), Counter(raw["stats"]),
            int(raw["next_node"]), int(raw["next_repair"]))


def checkpoint_path(root_id: str, branch_id: str) -> Path:
    return CHECKPOINT_ROOT / root_id / branch_id / "checkpoint.json"


def run_branch(root: Mapping[str, object], child: Mapping[str, object], budget: int, *,
               checkpoint_every: int, resume: bool) -> dict[str, object]:
    config = branch_config(root, child, budget)
    path = checkpoint_path(str(root["root_id"]), str(child["branch_id"]))
    if path.exists() and not resume:
        raise FileExistsError(f"refusing to overwrite v5 checkpoint without --resume: {path}")
    if resume:
        frontier, seen, nodes, repairs, r2_paths, stats, next_node, next_repair = load_checkpoint(path, config, root, child)
    else:
        root_state, root_dec = replay_trace(root, list(child["literal_macro_trace"]))
        if root_dec.r_count != 1:
            raise AssertionError("frozen branch root is not a literal R1 state")
        root_node = f"{child['branch_id']}:0"
        frontier = [(len(child["literal_macro_trace"]), root_state, root_dec, root_node, tuple())]
        seen = {(rr.decorated_key(root_state, root_dec), tuple())}
        nodes = {root_node: repair.node_record(root_node, None, None, root_state, root_dec, tuple())}
        repairs, r2_paths = {}, []
        stats = Counter(expanded=0, generated_edges=0, peak_working_set_bytes=working_set_bytes())
        next_node, next_repair = 1, 0

    started = time.monotonic()
    max_depth = max((depth for depth, *_rest in frontier), default=0)
    while frontier and stats["expanded"] < budget:
        depth, state, dec, node_id, lineage = frontier.pop()
        if dec.r_count != 1:
            raise AssertionError("post-R1 branch enqueued wrong R count")
        stats["expanded"] += 1
        max_depth = max(max_depth, depth)
        if stats["expanded"] % 64 == 0:
            stats["peak_working_set_bytes"] = max(int(stats["peak_working_set_bytes"]), working_set_bytes())
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] += 1
            if collision is not None:
                stats[f"prune:{collision}"] += 1
                continue
            assert edge is not None
            kind = edge_kind(edge)
            verdict, after_dec, recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            if kind == "R":
                if after_dec is None or after_dec.r_count != 2 or recognition is None:
                    raise AssertionError("R2 candidate lacked literal boundary metadata")
                stats["literal_Target_A_candidates"] += 1
                stats[f"r2_outcome:{recognition['r2_outcome']}"] += 1
                if recognition["source_state_semantic_tag"] != R2_SEMANTICS:
                    raise AssertionError("R2 recognizer did not consume typed literal joint source")
                if lineage:
                    related = [repairs[event_id] for event_id in lineage]
                    hierarchy = repair.hierarchy_for_r2(state, edge, dec, after_dec, related)
                    if hierarchy["recognizer"] != recognition:
                        raise AssertionError("repair hierarchy and exact literal recognizer disagree")
                    for event in related:
                        event["future_R2_observations"].append({
                            "r2_predecessor_node_id": node_id,
                            "source_orbit": hierarchy["future_R2_source_orbit"],
                            "source_phase": hierarchy["future_R2_source_phase"],
                            "maximum_level": hierarchy["maximum_level"],
                        })
                    r2_paths.append({"branch_id": child["branch_id"], "r2_predecessor_node_id": node_id,
                                     "r2_edge": rr.edge_json(edge), "repair_event_ids": list(lineage),
                                     "decoration_before_R2": dec.to_json(), "decoration_after_R2": after_dec.to_json(),
                                     **hierarchy})
                    stats[f"hierarchy:{hierarchy['maximum_level']}"] += 1
                    stats[f"failure:{hierarchy['failure_reason']}"] += 1
                else:
                    stats["R2_without_repair"] += 1
                if recognition["is_target_a"]:
                    stats["literal_Target_A_hits"] += 1
                    r2_paths.append({"branch_id": child["branch_id"], "r2_predecessor_node_id": node_id,
                                     "r2_edge": rr.edge_json(edge), "repair_event_ids": list(lineage),
                                     "decoration_before_R2": dec.to_json(), "decoration_after_R2": after_dec.to_json(),
                                     "literal_Target_A": True, "recognizer": recognition,
                                     "incidence_forest": component_summary_json(edge.run.state)})
                continue
            if verdict != "child":
                stats[f"prune:{verdict}"] += 1
                continue
            if after_dec is None or after_dec.r_count != 1:
                raise AssertionError("non-R child left post-R1 branch")
            repair_kind = repair.repair_type(edge)
            child_id = f"{child['branch_id']}:{next_node}"
            next_node += 1
            next_lineage = lineage
            nodes[child_id] = repair.node_record(child_id, node_id, rr.edge_json(edge), edge.state, after_dec, lineage)
            if repair_kind is not None:
                event_id = f"{child['branch_id']}:repair:{next_repair}"
                next_repair += 1
                repairs[event_id] = repair.repair_event(event_id, str(child["branch_id"]), node_id, child_id,
                                                        edge, state, edge.state, dec, after_dec)
                next_lineage = lineage + (event_id,)
                nodes[child_id]["repair_ids"] = list(next_lineage)
                stats[f"repair:{repair_kind}"] += 1
                if repairs[event_id]["component_merge"]:
                    stats["repair:component_merge"] += 1
            key = (rr.decorated_key(edge.state, after_dec), next_lineage)
            if key in seen:
                stats["memo_duplicates"] += 1
                del nodes[child_id]
                if repair_kind is not None:
                    del repairs[event_id]
                continue
            seen.add(key)
            children.append((depth + 1, edge.state, after_dec, child_id, next_lineage))
        children.sort(key=lambda row: row[3], reverse=True)
        frontier.extend(children)
        if stats["expanded"] % checkpoint_every == 0:
            stats["max_depth"] = max_depth
            stats["checkpoint_count"] += 1
            stats["peak_working_set_bytes"] = max(int(stats["peak_working_set_bytes"]), working_set_bytes())
            atomic_json(path, checkpoint_payload(config, root, child, frontier, seen, nodes, repairs, r2_paths,
                                                  stats, next_node, next_repair))
    stats["max_depth"] = max_depth
    stats["peak_working_set_bytes"] = max(int(stats["peak_working_set_bytes"]), working_set_bytes())
    stats["elapsed_seconds_this_invocation"] = time.monotonic() - started
    stats["checkpoint_count"] += 1
    atomic_json(path, checkpoint_payload(config, root, child, frontier, seen, nodes, repairs, r2_paths,
                                          stats, next_node, next_repair))
    return {
        "branch_id": child["branch_id"], "branch_origin_hash": child["branch_origin_hash"],
        "budget": budget, "expanded": int(stats["expanded"]), "frontier_size": len(frontier),
        "naturally_exhausted": not frontier, "max_depth": max_depth, "seen_size": len(seen),
        "stats": dict(sorted(stats.items())), "checkpoint": {"path": str(path.relative_to(ROOT)),
                                                                  "sha256": sha256_file(path),
                                                                  "bytes": path.stat().st_size},
        # Complete provenance is retained in the v5 checkpoint.  Keep the
        # aggregate result small enough to be a durable index rather than a
        # second multi-gigabyte copy of every parent-DAG node.
        "node_count": len(nodes), "repair_event_count": len(repairs), "r2_path_count": len(r2_paths),
    }


def historical_known_by_canonical() -> dict[str, list[dict[str, object]]]:
    rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in target_b.historical_18():
        state = item["state"]
        alpha = target_b.action_to_identity(state)
        canonical = exact.relabel_state(state, alpha)
        row = {key: value for key, value in item.items() if key != "state"}
        row["raw_state_hash"] = rr.state_hash(state)
        row["canonical_state_hash"] = rr.state_hash(canonical)
        rows[row["canonical_state_hash"]].append(row)
    if sum(len(group) for group in rows.values()) != 18:
        raise AssertionError("known-18 literal reconstruction is incomplete")
    return rows


def materialize_classes(roots: Mapping[str, Mapping[str, object]], *, flow_node_cap: int,
                        flow_seconds: float) -> tuple[dict[str, object], dict[str, object]]:
    """Freeze literal hits, compare only by proved left-S6, then close Target B safely."""
    known = historical_known_by_canonical()
    witnesses = []
    raw_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    decorated_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    canonical_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    ordinal = 0
    for root_id, row in roots.items():
        root = row["root_record"]
        children = {str(child["branch_id"]): child for child in row["admission"]["frozen_R1_children"]}
        for branch_summary in row["branches"]:
            checkpoint_path_abs = ROOT / branch_summary["checkpoint"]["path"]
            checkpoint = json.loads(checkpoint_path_abs.read_text(encoding="utf-8"))
            if checkpoint.get("schema") != CHECKPOINT_SCHEMA or not checkpoint.get("complete_frontier_snapshot"):
                raise AssertionError("v5 branch evidence checkpoint is invalid")
            branch_id = str(branch_summary["branch_id"])
            nodes = {str(node["node_id"]): node for node in checkpoint["nodes"]}
            r2_paths = checkpoint["r2_paths"]
            cache: dict[str, tuple[Any, Any, list[dict[str, object]]]] = {}
            def replay_node(node_id: str):
                if node_id in cache:
                    return cache[node_id]
                node = nodes[node_id]
                if node["parent_id"] is None:
                    state, dec = replay_trace(root, list(children[branch_id]["literal_macro_trace"]))
                    trace = list(children[branch_id]["literal_macro_trace"])
                else:
                    parent_state, parent_dec, parent_trace = replay_node(str(node["parent_id"]))
                    edge = edge_from_json(parent_state, node["incoming_macro_edge"])
                    state = edge.state
                    dec = rr.advance_decoration(edge.run.state, edge.joint, parent_dec)
                    trace = parent_trace + [node["incoming_macro_edge"]]
                if rr.state_hash(state) != node["exact_state_hash"] or dec.to_json() != node["decoration"]:
                    raise AssertionError("Target-A parent-DAG literal replay mismatch")
                cache[node_id] = (state, dec, trace)
                return cache[node_id]
            for path in r2_paths:
                if not path.get("literal_Target_A"):
                    continue
                state, dec, trace = replay_node(str(path["r2_predecessor_node_id"]))
                edge = edge_from_json(state, path["r2_edge"])
                after = rr.advance_decoration(edge.run.state, edge.joint, dec)
                recognition = rr.target_a_recognizer(rr.r2_literal_joint_source(edge), edge.joint, dec, after)
                if not recognition["is_target_a"]:
                    raise AssertionError("stored literal Target-A hit does not replay")
                canonical_state, canonical_dec, action, decorated_hash = target_b.canonical_boundary(edge.state, after)
                canonical_state_hash = rr.state_hash(canonical_state)
                raw_hash = rr.state_hash(edge.state)
                exact_matches = [item for item in known.get(canonical_state_hash, []) if item["raw_state_hash"] == raw_hash]
                symmetry_matches = known.get(canonical_state_hash, [])
                known_class = ("EXACT_KNOWN18_MATCH" if exact_matches else
                               "SYMMETRY_EQUIVALENT_TO_KNOWN18" if symmetry_matches else "GENUINELY_NEW")
                witness = {
                    "witness_id": f"{root_id}_target_a_{ordinal:05d}", "root_id": root_id,
                    "branch_id": branch_id, "literal_macro_trace": trace + [path["r2_edge"]],
                    "parent_dag_replay_hash": raw_hash, "R1_event": after.to_json()["r_events"][0],
                    "R2_event": after.to_json()["r_events"][1],
                    "completer_event": after.to_json()["completer"], "CH_class": after.branch,
                    "event_order_class": after.event_order_class, "boundary_state_hash": raw_hash,
                    "exact_decorated_boundary_hash": sha256_bytes(repr((edge.state.stable_key(), after.key())).encode("utf-8")),
                    "canonical_boundary_key": decorated_hash, "canonical_state_hash": canonical_state_hash,
                    "left_action_to_identity": list(core.ALL_WORDS[action]),
                    "literal_joint_source": {"state_hash": rr.state_hash(edge.run.state),
                                             "orbit": recognition["source_orbit"], "phase": recognition["source_phase"],
                                             "semantic_tag": recognition["source_state_semantic_tag"]},
                    "recognizer": recognition, "incidence_forest": component_summary_json(edge.run.state),
                    "component_partition": component_summary_json(edge.run.state)["components"],
                    "coordinate": {"P": edge.state.P, "O": edge.state.O, "F": edge.state.F, "H": edge.state.H,
                                   "Ndef": edge.state.Ndef, "Phi": rr.phi(edge.state), "M": edge.state.P - 5 * edge.state.O},
                    "known18_comparison": {"classification": known_class,
                                           "matches": symmetry_matches},
                    "canonical_state": target_b.state_to_json(canonical_state),
                    "canonical_decoration": canonical_dec.to_json(),
                }
                ordinal += 1
                witnesses.append(witness)
                raw_groups[raw_hash].append(witness)
                decorated_groups[decorated_hash].append(witness)
                canonical_groups[canonical_state_hash].append(witness)
    classes = []
    for canonical_state_hash, group in sorted(canonical_groups.items()):
        rep = group[0]
        state = target_b.state_from_json(rep["canonical_state"])
        comparison = rep["known18_comparison"]
        if comparison["classification"] != "GENUINELY_NEW":
            target_b_ledger = {"status": "KNOWN18_HELPER_FREE_CERTIFICATE_REUSED",
                               "reference": "outputs/rr_target_b_18_boundary_corrected_ledger.json",
                               "phase_helper_used": False}
        else:
            stage = target_b.target_b_stage(state)
            if stage["status"] == "REQUIRES_EXACT_HELPER_FREE_DFS":
                stage["exact_flow"] = target_b.run_flow(state, node_cap=flow_node_cap, seconds=flow_seconds)
                stage["final_status"] = stage["exact_flow"]["verdict"]
            else:
                stage["exact_flow"] = None
                stage["final_status"] = stage["status"]
            target_b_ledger = {"phase_helper_used": False, **stage}
        classes.append({"canonical_state_hash": canonical_state_hash,
                        "representative_witness_id": rep["witness_id"],
                        "literal_witness_count": len(group), "root_distribution": dict(Counter(x["root_id"] for x in group)),
                        "decorated_boundary_key_count": len({x["canonical_boundary_key"] for x in group}),
                        "known18_comparison": comparison, "target_b": target_b_ledger})
    payload = {
        "schema": "rr-short1-4-target-a-classes-v5-literal-r2-source", "scope": "capped corrected pilots only",
        "literal_target_a_witnesses": witnesses,
        "canonical_state_classes": classes,
        "counts": {"literal_Target_A_hits": len(witnesses), "raw_exact_states": len(raw_groups),
                   "exact_decorated_boundary_states": len(decorated_groups), "canonical_state_classes": len(classes),
                   "known18_orbit_classes": sum(c["known18_comparison"]["classification"] != "GENUINELY_NEW" for c in classes),
                   "new_state_classes": sum(c["known18_comparison"]["classification"] == "GENUINELY_NEW" for c in classes)},
        "phase_helper_used": False,
    }
    return payload, {"classes": classes, "witnesses": witnesses}


def edge_from_json(state, data: Mapping[str, object]):
    runs = [run for run in rr.macro.rotation_runs(state) if run.ell == int(data["rotation_length"])]
    if len(runs) != 1:
        raise AssertionError("serialized macro rotation run is ambiguous")
    move = {move.label: move for move in exact.ALL_MOVES}[str(data["joint"])]
    transition = exact.extend(runs[0].state, move)
    if transition is None:
        raise AssertionError("serialized macro joint is collision-illegal")
    edge = rr.macro.MacroEdge(runs[0], transition)
    if edge.label != data["label"]:
        raise AssertionError("serialized macro label mismatch")
    return edge


def summarize_roots(roots: Mapping[str, Mapping[str, object]], class_payload: Mapping[str, object]) -> dict[str, object]:
    by_root = defaultdict(list)
    for witness in class_payload["literal_target_a_witnesses"]:
        by_root[str(witness["root_id"])].append(witness)
    rows = []
    for root_id, item in roots.items():
        hits = by_root[root_id]
        new = any(w["known18_comparison"]["classification"] == "GENUINELY_NEW" for w in hits)
        if new:
            status = "ROOT_HAS_NEW_TARGET_A"
        elif hits:
            status = "ROOT_ALL_OBSERVED_TARGET_A_CLOSED"
        elif not item["admission"]["frozen_R1_children"]:
            status = "ROOT_ADMISSION_INCOMPLETE"
        else:
            status = "ROOT_NO_TARGET_A_IN_PREFIX"
        branches = item["branches"]
        rows.append({
            "root_id": root_id, "status": status,
            "admitted_R1_children": len(item["admission"]["frozen_R1_children"]),
            "admission": {key: item["admission"][key] for key in ("budget", "expanded", "frontier_size", "naturally_exhausted", "max_depth", "preparation_spine")},
            "state_key_audit": item["state_key_audit"],
            "fair_branches": [{key: branch[key] for key in ("branch_id", "expanded", "frontier_size", "naturally_exhausted", "max_depth", "seen_size", "checkpoint")}
                              for branch in branches],
            "telemetry": {
                "legal_repair_events": sum(int(branch["repair_event_count"]) for branch in branches),
                "repaired_R2_paths": sum(int(branch["r2_path_count"]) for branch in branches),
                "literal_Target_A_candidates": sum(int(branch["stats"].get("literal_Target_A_candidates", 0)) for branch in branches),
                "literal_Target_A_hits": len(hits),
                "failure_taxonomy": dict(sum((Counter({key.removeprefix("r2_outcome:"): int(value)
                                                         for key, value in branch["stats"].items() if key.startswith("r2_outcome:")})
                                               for branch in branches), Counter())),
                "prunes": dict(sum((Counter({key.removeprefix("prune:"): int(value)
                                               for key, value in branch["stats"].items() if key.startswith("prune:")})
                                    for branch in branches), Counter())),
                "peak_memory_bytes": max((int(branch["stats"].get("peak_working_set_bytes", 0)) for branch in branches), default=0),
            },
        })
    return {"schema": "rr-short5-cross-root-profiles-v5", "scope": "corrected capped fair pilots; frequencies are not theorems",
            "roots": rows,
            "cross_root": {
                "R1_child_counts": {row["root_id"]: row["admitted_R1_children"] for row in rows},
                "preparation_spine_presence": {row["root_id"]: row["admission"]["preparation_spine"]["present"] for row in rows},
                "literal_Target_A_frequency": {row["root_id"]: row["telemetry"]["literal_Target_A_hits"] for row in rows},
                "known18_absorption_rate": {row["root_id"]: sum(w["known18_comparison"]["classification"] != "GENUINELY_NEW" for w in by_root[row["root_id"]])
                                            for row in rows},
                "new_boundary_classes": int(class_payload["counts"]["new_state_classes"]),
            }}


def main() -> None:
    global CHECKPOINT_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=5_000)
    parser.add_argument("--admission-budget", type=int, default=250)
    parser.add_argument("--checkpoint-every", type=int, default=1_000)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--flow-node-cap", type=int, default=20_000)
    parser.add_argument("--flow-seconds", type=float, default=30.0)
    parser.add_argument("--checkpoint-root", type=Path, default=CHECKPOINT_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--classes", type=Path, default=CLASSES)
    parser.add_argument("--profiles", type=Path, default=PROFILES)
    args = parser.parse_args()
    if args.budget <= 0 or args.admission_budget <= 0 or args.checkpoint_every <= 0:
        raise ValueError("all pilot budgets and checkpoint interval must be positive")
    CHECKPOINT_ROOT = args.checkpoint_root.resolve()
    if "true_phase_walk_capacity" in (ROOT / "src" / "analyze_rr_short_ell0_target_b.py").read_text(encoding="utf-8"):
        # Mentioning a helper in a docstring is harmless, but an executable
        # import/call would not be.  The exact check is repeated by verifier.
        import ast as _ast
        tree = _ast.parse((ROOT / "src" / "analyze_rr_short_ell0_target_b.py").read_text(encoding="utf-8"))
        if any(isinstance(node, _ast.Name) and node.id == "true_phase_walk_capacity" for node in _ast.walk(tree)):
            raise AssertionError("suspect phase-capacity helper reached v5 Target-B path")
    collected = {}
    for root_id, root in root_records().items():
        admission_row = admission(root, args.admission_budget)
        children = admission_row["frozen_R1_children"]
        key_audit = state_key_audit(root, children)
        if not key_audit["passed"]:
            raise RuntimeError("STATE_KEY_UNSOUND")
        branches = [run_branch(root, child, args.budget, checkpoint_every=args.checkpoint_every,
                               resume=args.resume) for child in children]
        collected[root_id] = {"root_record": root, "admission": admission_row,
                              "state_key_audit": key_audit, "branches": branches}
    class_payload, _detail = materialize_classes(collected, flow_node_cap=args.flow_node_cap,
                                                  flow_seconds=args.flow_seconds)
    profiles = summarize_roots(collected, class_payload)
    result = {"schema": SCHEMA, "scope": "fresh v5 corrected fair pilots; all positive caps are INCOMPLETE for absence purposes",
              "checkpoint_schema": CHECKPOINT_SCHEMA, "recognizer_semantics": R2_SEMANTICS,
              "macro_entry_semantics": rr.R2_MACRO_ENTRY_PROVENANCE_TAG,
              "prune_profile": rr.TARGET_A_SAFE_PROFILE,
              "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
              "budget_per_R1_child": args.budget, "admission_budget_per_root": args.admission_budget,
              "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
              "driver_sha256": sha256_file(Path(__file__)),
              "roots": {root_id: {"root_record": item["root_record"], "admission": item["admission"],
                                  "state_key_audit": item["state_key_audit"], "branches": item["branches"]}
                        for root_id, item in collected.items()},
              "equal_budget_verified": all(branch["expanded"] == args.budget or branch["naturally_exhausted"]
                                            for item in collected.values() for branch in item["branches"]),
              "all_nonempty_capped_frontiers_are_incomplete": True}
    atomic_json(args.output.resolve(), result)
    atomic_json(args.classes.resolve(), class_payload)
    atomic_json(args.profiles.resolve(), profiles)
    print(json.dumps({"roots": {row["root_id"]: row["status"] for row in profiles["roots"]},
                      "classes": class_payload["counts"], "budget": args.budget}, sort_keys=True))


if __name__ == "__main__":
    main()
