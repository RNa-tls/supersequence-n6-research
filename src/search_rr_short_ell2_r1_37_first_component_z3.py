#!/usr/bin/env python3
"""Round 58: exact search for the first R1-component-changing Z3.

The six incomplete Round-56 all-13 branches are immutable inputs.  Their 84
frontier states are copied into a new checkpoint namespace and searched with
independent per-seed budgets.  Priority changes traversal order only; every
literal macro candidate is generated and only the proved Target-A-safe prune
registry is used.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
import os
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parent.parent
ALL13_RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_pilot_results.json"
ALL13_VERIFIED = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_verified.json"
ROUND57_MANIFEST = ROOT / "outputs" / "rr_short_ell2_r1_37_dangerous_entry_manifest.json"
DANGEROUS = ROOT / "outputs" / "rr_short_ell2_r1_37_dangerous_entries.json"
BACKWARD = ROOT / "outputs" / "rr_short_ell2_r1_37_backward_realizability.json"
GRAPH = ROOT / "outputs" / "rr_short_ell2_r1_37_deep_z3_graph.json"
Z2_CERT = ROOT / "outputs" / "rr_short_ell2_r1_37_z2_lemma_certificate.json"
WATCH = ROOT / "outputs" / "rr_short_ell2_r1_37_z3_watchlist.json"
PHASE = ROOT / "outputs" / "rr_short_ell2_r1_37_watchlist_phase_edges.json"
CLOSURE = ROOT / "outputs" / "rr_short_ell2_r1_37_z3_transition_closure.json"

CHECKPOINT_ROOT = (
    ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_37_first_component_z3_v1"
)
MANIFEST_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
RESULT_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
WITNESS_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_witnesses.json"
STATS_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_component_change_stats.json"

CHECKPOINT_SCHEMA = "rr-short-ell2-r1-37-first-component-z3-checkpoint-v1"
MANIFEST_SCHEMA = "rr-short-ell2-r1-37-first-component-z3-manifest-v1"
RESULT_SCHEMA = "rr-short-ell2-r1-37-first-component-z3-results-v1"
EVENT_SEMANTICS = "FIRST_COMPONENT_CHANGING_Z3_LITERAL_V1"
STAGE_DELTAS = {"A": 25_000, "B": 50_000, "C": 100_000, "D": 250_000, "E": 500_000}
STAGE_ORDER = tuple(STAGE_DELTAS)
SOURCE_IDS = (
    "short_ell2_r1_37:236166", "short_ell2_r1_37:12", "short_ell2_r1_37:6",
    "short_ell2_r1_37:3", "short_ell2_r1_37:303321", "short_ell2_r1_37:13",
)
FZ_LEVELS = tuple(f"FZ{i}" for i in range(7))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


all13 = load_module("rr_first_component_all13", ROOT / "src" / "search_rr_short_ell2_r1_37_all13_pilot.py")
rr, exact, pilot, audit, core = all13.rr, all13.exact, all13.pilot, all13.audit, all13.audit.core


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def checkpoint_path(seed_id: str) -> Path:
    return CHECKPOINT_ROOT / ("seed_" + seed_id.rsplit(":", 1)[1]) / "checkpoint.json"


def progress_path(seed_id: str) -> Path:
    return CHECKPOINT_ROOT / ("seed_" + seed_id.rsplit(":", 1)[1]) / "progress.json"


def component(summary: Mapping[str, object], node: tuple[str, int]) -> dict[str, object] | None:
    return summary["node_component"].get(node)  # type: ignore[index,union-attr]


def component_nodes(item: Mapping[str, object] | None) -> frozenset[tuple[str, int]]:
    if item is None:
        return frozenset()
    return frozenset(
        [("q", int(value)) for value in item["e_orbits"]]
        + [("h", int(value)) for value in item["hexagons"]]
    )


def r1_and_hub_components(state, dec) -> tuple[dict[str, object], dict[str, object] | None, dict[str, object] | None]:
    if dec.r1 is None:
        raise AssertionError("post-R1 state lost R1 provenance")
    summary = rr.component_summary(state)
    r1 = component(summary, ("q", int(dec.r1.target_orbit)))
    hub = component(summary, ("h", int(dec.hub_id)))
    return summary, r1, hub


def z2_hub_route(state, dec) -> bool:
    _summary, r1, hub = r1_and_hub_components(state, dec)
    if r1 is None or hub is None:
        return False
    hub_hexes = set(int(value) for value in hub["hexagons"])
    for orbit in r1["e_orbits"]:
        for port in core.ports_of_e_orbit(core.E_REPS[int(orbit)]):
            if core.hexagon_id(port) in hub_hexes:
                return True
    return False


def classify_component_change(parent_state, parent_dec, edge, child_state, child_dec) -> dict[str, object]:
    kind = pilot.edge_kind(edge)
    pre_summary, pre_r1, pre_hub = r1_and_hub_components(parent_state, parent_dec)
    post_summary, post_r1, post_hub = r1_and_hub_components(child_state, child_dec)
    pre_nodes, post_nodes = component_nodes(pre_r1), component_nodes(post_r1)
    pre_hub_nodes, post_hub_nodes = component_nodes(pre_hub), component_nodes(post_hub)
    if not pre_nodes or not pre_hub_nodes or pre_nodes == pre_hub_nodes:
        raise AssertionError("search state is outside the separated pre-R2 component scope")
    strictly_enlarged = post_nodes > pre_nodes
    merged_hub = bool(post_nodes and post_nodes == post_hub_nodes)
    changed = kind == "Z3" and strictly_enlarged
    classification = "FZ0"
    if changed:
        if merged_hub:
            classification = "FZ3"
        elif z2_hub_route(child_state, child_dec):
            classification = "FZ2"
        else:
            classification = "FZ1"
    absorbed = []
    if changed:
        added = post_nodes - pre_nodes
        for item in pre_summary["components"]:
            nodes = component_nodes(item)
            if nodes and nodes <= added:
                absorbed.append({"id": item["id"], "nodes": [list(node) for node in sorted(nodes)]})
    return {
        "edge_kind": kind,
        "classification": classification,
        "is_first_component_change_candidate": changed,
        "r1_component_strictly_enlarged": strictly_enlarged,
        "r1_hub_merged": merged_hub,
        "later_z2_hub_route_geometry": z2_hub_route(child_state, child_dec) if changed else False,
        "pre_r1_component": {"id": None if pre_r1 is None else pre_r1["id"], "nodes": [list(x) for x in sorted(pre_nodes)]},
        "post_r1_component": {"id": None if post_r1 is None else post_r1["id"], "nodes": [list(x) for x in sorted(post_nodes)]},
        "pre_hub_component": {"id": None if pre_hub is None else pre_hub["id"], "nodes": [list(x) for x in sorted(pre_hub_nodes)]},
        "post_hub_component": {"id": None if post_hub is None else post_hub["id"], "nodes": [list(x) for x in sorted(post_hub_nodes)]},
        "absorbed_pre_components": absorbed,
        "pre_component_count": int(pre_summary["component_count"]),
        "post_component_count": int(post_summary["component_count"]),
    }


def decorated_digest(state, dec) -> str:
    return sha256_json(repr(rr.decorated_key(state, dec)))


def source_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    result = json.loads(ALL13_RESULT.read_text(encoding="utf-8"))
    branches = {str(row["state_id"]): row for row in result["branches"]}
    if set(SOURCE_IDS) - set(branches):
        raise AssertionError("one of the six prescribed source branches is absent")
    starts: list[dict[str, object]] = []
    sources: list[dict[str, object]] = []
    for seed_id in SOURCE_IDS:
        branch = branches[seed_id]
        if branch["naturally_exhausted"] or branch["status"] != "INCOMPLETE":
            raise AssertionError(f"source branch is not an incomplete survivor: {seed_id}")
        path = ROOT / branch["checkpoint"]["path"]
        actual_sha = sha256_file(path)
        if actual_sha != branch["checkpoint"]["sha256"]:
            raise AssertionError(f"source checkpoint SHA mismatch: {seed_id}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("schema") != all13.CHECKPOINT_SCHEMA or len(raw["frontier"]) != int(branch["frontier_size"]):
            raise AssertionError(f"source checkpoint schema/frontier mismatch: {seed_id}")
        sources.append({
            "seed_id": seed_id, "checkpoint_path": branch["checkpoint"]["path"],
            "checkpoint_sha256": actual_sha, "checkpoint_schema": raw["schema"],
            "frontier_count": len(raw["frontier"]), "source_config_sha256": raw["provenance"]["config_sha256"],
        })
        for index, row in enumerate(raw["frontier"]):
            state = exact.state_from_json(row["state"])
            dec = rr.Decoration.from_json(row["decoration"])
            if dec.r_count != 1 or state.F != 1 or state.H != 0:
                raise AssertionError("source frontier left the Target-A-safe scope")
            _summary, r1, hub = r1_and_hub_components(state, dec)
            if set(r1["e_orbits"]) != {91} or set(r1["hexagons"]) != {40, 92}:
                raise AssertionError("source already contains a component-changing Z3")
            if component_nodes(r1) == component_nodes(hub):
                raise AssertionError("source already merged R1 and hub components")
            starts.append({
                "seed_id": seed_id, "source_frontier_index": index,
                "source_node_id": row["node_id"], "source_path_hash": row["path_hash"],
                "source_depth": int(row["depth"]), "source_relative_depth": int(row["relative_depth"]),
                "state": row["state"], "decoration": row["decoration"],
                "exact_state_hash": rr.state_hash(state), "decorated_state_sha256": decorated_digest(state, dec),
                "component_digest": rr.component_digest(state),
            })
    return starts, sources


def build_manifest() -> dict[str, object]:
    starts, sources = source_rows()
    exact_decorated = {row["decorated_state_sha256"] for row in starts}
    canonical = set()
    components = set()
    for row in starts:
        state = exact.state_from_json(row["state"])
        dec = rr.Decoration.from_json(row["decoration"])
        _cs, _cd, canonical_hash = audit.canonical_state_decoration(state, dec)
        canonical.add(canonical_hash)
        components.add(rr.component_digest(state))
    if len(starts) != 84 or len(exact_decorated) != 84:
        raise AssertionError("84-source exact decorated deduplication failed")
    fixed = [
        ROUND57_MANIFEST, ALL13_RESULT, ALL13_VERIFIED, GRAPH, Z2_CERT, WATCH,
        PHASE, CLOSURE, DANGEROUS, BACKWARD,
    ]
    rows = [{"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in fixed]
    return {
        "schema": MANIFEST_SCHEMA,
        "scope": "six incomplete short_ell2_r1_37 all-13 families; new namespace only",
        "event_semantics": EVENT_SEMANTICS,
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "driver_sha256": sha256_file(Path(__file__)),
        "rr_engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "exact_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1.py"),
        "macro_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py"),
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
        "stage_deltas": STAGE_DELTAS,
        "frozen_artifacts": rows,
        "source_checkpoints": sources,
        "start_domain": {
            "literal_records": len(starts), "exact_decorated_states": len(exact_decorated),
            "proved_left_s6_classes": len(canonical), "component_signature_count": len(components),
            "deduplicated_records": len(starts),
            "start_records_sha256": sha256_json(starts),
            "records": starts,
        },
    }


def checkpoint_provenance(manifest: Mapping[str, object], seed_id: str) -> dict[str, object]:
    source = next(row for row in manifest["source_checkpoints"] if row["seed_id"] == seed_id)
    payload = {
        "seed_id": seed_id, "source_checkpoint": source,
        "manifest_sha256": sha256_json(manifest), "driver_sha256": sha256_file(Path(__file__)),
        "rr_engine_sha256": manifest["rr_engine_sha256"], "exact_engine_sha256": manifest["exact_engine_sha256"],
        "macro_engine_sha256": manifest["macro_engine_sha256"], "prune_profile": manifest["prune_profile"],
        "prune_registry_hash": manifest["prune_registry_hash"], "event_semantics": EVENT_SEMANTICS,
        "stage_deltas": STAGE_DELTAS, "budget_transfer": False,
    }
    return {**payload, "config_sha256": sha256_json(payload)}


def danger_pairs() -> tuple[set[tuple[int, int]], set[int]]:
    raw = json.loads(DANGEROUS.read_text(encoding="utf-8"))
    pairs, orbits = set(), set()
    for row in raw["direct_z3_entries"]:
        pairs.add((int(row["source_orbit"]), int(row["source_phase"])))
        orbits.add(int(row["source_orbit"]))
    for row in raw["next_z2_entries"]:
        pairs.add((int(row["preceding_source_orbit"]), int(row["preceding_source_phase"])))
        orbits.add(int(row["preceding_source_orbit"]))
    return pairs, orbits


DANGER_PAIRS, DANGER_ORBITS = danger_pairs()


def priority_for_state(state, dec, *, depth: int, serial: int, component_changed: bool) -> tuple[int, ...]:
    legal = 0
    legal_z3 = 0
    immediate_change = 0
    for edge, collision in rr.iter_raw_macro_candidates(state):
        if collision is not None or edge is None:
            continue
        verdict, after, _recognition = rr.evaluate_edge(state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
        if verdict != "child" or after is None:
            continue
        legal += 1
        if pilot.edge_kind(edge) == "Z3":
            legal_z3 += 1
            if not component_changed and classify_component_change(state, dec, edge, edge.state, after)["is_first_component_change_candidate"]:
                immediate_change += 1
    orbit, phase_value = exact.ORBIT_PHASE[state.p]
    dangerous_distance = 0 if (orbit, phase_value) in DANGER_PAIRS else 1 if orbit in DANGER_ORBITS else 2
    z2_route = z2_hub_route(state, dec)
    # Min-heap: component-changing one-step witnesses first, then exact Z3
    # availability, possible later-Z2 geometry, dangerous-table proximity,
    # small branching, and deeper states.  No term is a prune.
    return (
        0 if component_changed else 1,
        0 if immediate_change else 1,
        -immediate_change, -legal_z3,
        0 if z2_route else 1,
        dangerous_distance, legal, -depth, serial,
    )


def serialize_frontier(frontier: list[tuple]) -> list[dict[str, object]]:
    rows = []
    for priority, serial, depth, relative_depth, state, dec, node_id, path_hash, first_change_id, max_level in frontier:
        rows.append({
            "priority": list(priority), "serial": serial, "depth": depth, "relative_depth": relative_depth,
            "state": exact.state_to_json(state), "decoration": dec.to_json(), "node_id": node_id,
            "path_hash": path_hash, "first_component_change_id": first_change_id, "max_fz_level": max_level,
        })
    return rows


def load_frontier(rows: Iterable[Mapping[str, object]]) -> list[tuple]:
    result = []
    for row in rows:
        result.append((
            tuple(int(value) for value in row["priority"]), int(row["serial"]), int(row["depth"]),
            int(row["relative_depth"]), exact.state_from_json(row["state"]),
            rr.Decoration.from_json(row["decoration"]), str(row["node_id"]), str(row["path_hash"]),
            row.get("first_component_change_id"), int(row.get("max_fz_level", 0)),
        ))
    heapq.heapify(result)
    return result


def node_record(*, node_id: str, parent_id: str | None, incoming_edge, state, dec, depth: int,
                relative_depth: int, path_hash: str, start_record_id: str | None,
                first_change_id: str | None, max_level: int) -> dict[str, object]:
    return {
        "node_id": node_id, "parent_id": parent_id,
        "incoming_macro_edge": None if incoming_edge is None else rr.edge_json(incoming_edge),
        "exact_state_hash": rr.state_hash(state), "decorated_state_sha256": decorated_digest(state, dec),
        "decoration": dec.to_json(), "depth": depth, "relative_depth": relative_depth,
        "path_hash": path_hash, "start_record_id": start_record_id,
        "first_component_change_id": first_change_id, "max_fz_level": max_level,
    }


def initialize_seed(manifest: Mapping[str, object], seed_id: str) -> dict[str, object]:
    records = [row for row in manifest["start_domain"]["records"] if row["seed_id"] == seed_id]
    if not records:
        raise AssertionError(f"seed has no start records: {seed_id}")
    frontier, nodes = [], {}
    next_serial = 0
    for index, row in enumerate(records):
        state = exact.state_from_json(row["state"])
        dec = rr.Decoration.from_json(row["decoration"])
        node_id = f"{seed_id}:fz:root:{index}"
        path_hash = sha256_json({"source_path_hash": row["source_path_hash"], "state": row["exact_state_hash"]})
        depth = int(row["source_depth"])
        priority = priority_for_state(state, dec, depth=depth, serial=next_serial, component_changed=False)
        item = (priority, next_serial, depth, 0, state, dec, node_id, path_hash, None, 0)
        next_serial += 1
        frontier.append(item)
        nodes[node_id] = node_record(
            node_id=node_id, parent_id=None, incoming_edge=None, state=state, dec=dec, depth=depth,
            relative_depth=0, path_hash=path_hash, start_record_id=str(row["source_node_id"]),
            first_change_id=None, max_level=0,
        )
    heapq.heapify(frontier)
    return {
        "frontier": frontier, "nodes": nodes, "witnesses": [], "r2_records": [],
        "stats": Counter(expanded=0, generated_edges=0, checkpoint_count=0),
        "next_serial": next_serial, "next_node": 0, "completed_stages": [],
    }


def checkpoint_payload(manifest, seed_id, engine) -> dict[str, object]:
    return {
        "schema": CHECKPOINT_SCHEMA, "complete_frontier_snapshot": True,
        "provenance": checkpoint_provenance(manifest, seed_id), "seed_id": seed_id,
        "completed_stages": list(engine["completed_stages"]),
        "frontier": serialize_frontier(engine["frontier"]), "nodes": list(engine["nodes"].values()),
        "witnesses": engine["witnesses"], "r2_records": engine["r2_records"],
        "stats": dict(engine["stats"]), "next_serial": engine["next_serial"], "next_node": engine["next_node"],
    }


def load_checkpoint(manifest: Mapping[str, object], seed_id: str) -> dict[str, object]:
    path = checkpoint_path(seed_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != CHECKPOINT_SCHEMA or not raw.get("complete_frontier_snapshot"):
        raise ValueError("foreign or partial first-component checkpoint")
    if raw.get("provenance") != checkpoint_provenance(manifest, seed_id) or raw.get("seed_id") != seed_id:
        raise ValueError("first-component checkpoint provenance mismatch")
    return {
        "frontier": load_frontier(raw["frontier"]),
        "nodes": {str(row["node_id"]): row for row in raw["nodes"]},
        "witnesses": list(raw["witnesses"]), "r2_records": list(raw["r2_records"]),
        "stats": Counter(raw["stats"]), "next_serial": int(raw["next_serial"]),
        "next_node": int(raw["next_node"]), "completed_stages": list(raw["completed_stages"]),
    }


def stage_target(stage: str) -> int:
    target = 0
    for name in STAGE_ORDER:
        target += STAGE_DELTAS[name]
        if name == stage:
            return target
    raise ValueError(stage)


def event_record(seed_id: str, node_id: str, child_id: str, path_hash: str, edge, parent_state,
                 parent_dec, child_state, child_dec, classification: Mapping[str, object]) -> dict[str, object]:
    return {
        "seed_id": seed_id, "predecessor_node_id": node_id, "child_node_id": child_id,
        "path_hash": path_hash, "edge": rr.edge_json(edge),
        "pre_state_hash": rr.state_hash(parent_state), "post_state_hash": rr.state_hash(child_state),
        "pre_state": exact.state_to_json(parent_state), "post_state": exact.state_to_json(child_state),
        "pre_decoration": parent_dec.to_json(), "post_decoration": child_dec.to_json(),
        "component_change": dict(classification),
        "resources_before": {name: int(getattr(parent_state, name)) for name in ("P", "O", "F", "H", "Ndef", "D")},
        "resources_after": {name: int(getattr(child_state, name)) for name in ("P", "O", "F", "H", "Ndef", "D")},
    }


def r2_record(seed_id: str, node_id: str, path_hash: str, state, dec, edge, after, recognition,
              first_change_id: str | None, max_level: int) -> dict[str, object]:
    row = {
        "seed_id": seed_id, "predecessor_node_id": node_id, "path_hash": path_hash,
        "edge": rr.edge_json(edge), "macro_entry_state_hash": rr.state_hash(state),
        "literal_joint_source_state_hash": rr.state_hash(edge.run.state),
        "post_R2_state_hash": rr.state_hash(edge.state), "recognizer": recognition,
        "first_component_change_id": first_change_id, "incoming_max_fz_level": max_level,
        "literal_Target_A": bool(recognition["is_target_a"]),
    }
    if recognition["is_target_a"]:
        row["boundary_state"] = exact.state_to_json(edge.state)
        row["target_b"] = all13.target_b_analysis(edge.state)
    return row


def checkpoint_and_progress(manifest, seed_id, engine, stage: str, started_wall: float) -> None:
    path = checkpoint_path(seed_id)
    atomic_json(path, checkpoint_payload(manifest, seed_id, engine))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("provenance") != checkpoint_provenance(manifest, seed_id):
        raise AssertionError("atomic checkpoint provenance failed readback")
    stats = engine["stats"]
    progress = {
        "schema": "rr-short-ell2-r1-37-first-component-z3-progress-v1",
        "seed_id": seed_id, "stage": stage, "timestamp": time.time(),
        "wall_seconds_this_invocation": time.monotonic() - started_wall,
        "expansions": int(stats["expanded"]), "unique_exact_state_digests": len({row["decorated_state_sha256"] for row in engine["nodes"].values()}),
        "frontier": len(engine["frontier"]), "memory_note": "external working set captured by supervisor/final report",
        "checkpoint_bytes": path.stat().st_size,
        "FZ_counts": {level: int(stats[level]) for level in FZ_LEVELS},
        "closest_structural_distance_to_FZ1": 0 if stats["FZ1"] + stats["FZ2"] + stats["FZ3"] else min((item[0][1] for item in engine["frontier"]), default=None),
    }
    atomic_json(progress_path(seed_id), progress)


def run_seed(manifest: Mapping[str, object], seed_id: str, stage: str, *, checkpoint_every: int) -> dict[str, object]:
    path = checkpoint_path(seed_id)
    engine = load_checkpoint(manifest, seed_id) if path.exists() else initialize_seed(manifest, seed_id)
    if stage in engine["completed_stages"]:
        return summarize_seed(seed_id, engine, path, stage)
    prior_names = STAGE_ORDER[:STAGE_ORDER.index(stage)]
    if any(name not in engine["completed_stages"] for name in prior_names):
        raise ValueError(f"cannot skip an iterative stage for {seed_id}: {engine['completed_stages']} -> {stage}")
    target = stage_target(stage)
    started = time.monotonic()
    last_checkpoint = int(engine["stats"]["expanded"])
    while engine["frontier"] and int(engine["stats"]["expanded"]) < target:
        priority, _serial, depth, relative_depth, state, dec, node_id, path_hash, first_change_id, max_level = heapq.heappop(engine["frontier"])
        engine["stats"]["expanded"] += 1
        engine["stats"]["max_depth"] = max(int(engine["stats"]["max_depth"]), depth)
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            engine["stats"]["generated_edges"] += 1
            if collision is not None or edge is None:
                engine["stats"][f"prune:{collision or 'missing_edge'}"] += 1
                continue
            verdict, after, recognition = rr.evaluate_edge(state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
            kind = pilot.edge_kind(edge)
            if kind == "R":
                engine["stats"]["R2_candidates"] += 1
                if after is None or recognition is None:
                    raise AssertionError("R2 candidate lacks exact recognizer")
                row = r2_record(seed_id, node_id, path_hash, state, dec, edge, after, recognition, first_change_id, max_level)
                engine["r2_records"].append(row)
                engine["stats"][f"R2:{recognition['r2_outcome']}"] += 1
                if row["literal_Target_A"]:
                    engine["stats"]["FZ5"] += 1
                    if row["target_b"]["target_b_survivor"]:
                        engine["stats"]["FZ6"] += 1
                continue
            if verdict != "child" or after is None:
                engine["stats"][f"prune:{verdict}"] += 1
                continue
            child_state = edge.state
            engine["stats"][f"accepted:{kind}"] += 1
            child_level = max_level
            classification = (
                classify_component_change(state, dec, edge, child_state, after)
                if first_change_id is None else {
                    "edge_kind": kind, "classification": "POST_FIRST_EVENT",
                    "is_first_component_change_candidate": False,
                }
            )
            if kind == "Z3":
                engine["stats"]["Z3_transitions"] += 1
                if first_change_id is None:
                    engine["stats"][classification["classification"]] += 1
            engine["next_node"] += 1
            child_id = f"{seed_id}:fz:{engine['next_node']}"
            child_path_hash = sha256_json({"parent": path_hash, "edge": rr.edge_json(edge)})
            child_first = first_change_id
            if first_change_id is None and classification["is_first_component_change_candidate"]:
                child_first = child_id
                child_level = int(str(classification["classification"])[2:])
                witness = event_record(seed_id, node_id, child_id, child_path_hash, edge, state, dec, child_state, after, classification)
                witness["witness_id"] = child_id
                engine["witnesses"].append(witness)
            if first_change_id is not None or child_first is not None:
                if audit.exact_bridge(state, dec, child_state, after):
                    if kind == "Z2":
                        child_level = max(child_level, 4)
                        engine["stats"]["FZ4"] += 1
                    elif kind == "Z3":
                        child_level = max(child_level, 3)
            child_depth, child_relative = depth + 1, relative_depth + 1
            engine["next_serial"] += 1
            serial = engine["next_serial"]
            child_priority = priority_for_state(
                child_state, after, depth=child_depth, serial=serial,
                component_changed=child_first is not None,
            )
            engine["nodes"][child_id] = node_record(
                node_id=child_id, parent_id=node_id, incoming_edge=edge, state=child_state, dec=after,
                depth=child_depth, relative_depth=child_relative, path_hash=child_path_hash,
                start_record_id=None, first_change_id=child_first, max_level=child_level,
            )
            children.append((child_priority, serial, child_depth, child_relative, child_state, after,
                             child_id, child_path_hash, child_first, child_level))
        for child in children:
            heapq.heappush(engine["frontier"], child)
        if int(engine["stats"]["expanded"]) - last_checkpoint >= checkpoint_every or time.monotonic() - started >= 600:
            engine["stats"]["checkpoint_count"] += 1
            checkpoint_and_progress(manifest, seed_id, engine, stage, started)
            last_checkpoint = int(engine["stats"]["expanded"])
            started = time.monotonic()
    if stage not in engine["completed_stages"]:
        engine["completed_stages"].append(stage)
    engine["stats"]["checkpoint_count"] += 1
    checkpoint_and_progress(manifest, seed_id, engine, stage, started)
    return summarize_seed(seed_id, engine, path, stage)


def summarize_seed(seed_id: str, engine, path: Path, stage: str) -> dict[str, object]:
    stats = engine["stats"]
    exhausted = not engine["frontier"]
    status = "EXHAUSTED_NO_FIRST_COMPONENT_Z3" if exhausted and not engine["witnesses"] else "INCOMPLETE"
    if engine["witnesses"]:
        status = "FIRST_COMPONENT_Z3_WITNESS_FOUND"
    if stats["FZ6"]:
        status = "FOUND_TARGET_B"
    elif stats["FZ5"]:
        status = "FOUND_TARGET_A"
    return {
        "seed_id": seed_id, "stage": stage, "completed_stages": list(engine["completed_stages"]),
        "status": status, "expansions": int(stats["expanded"]), "unique_exact_state_digests": len({row["decorated_state_sha256"] for row in engine["nodes"].values()}),
        "frontier_size": len(engine["frontier"]), "max_depth": int(stats["max_depth"]),
        "naturally_exhausted": exhausted, "Z3_transitions": int(stats["Z3_transitions"]),
        "first_component_change_witnesses": len(engine["witnesses"]),
        "FZ_counts": {level: int(stats[level]) for level in FZ_LEVELS},
        "R2_candidates": int(stats["R2_candidates"]), "literal_Target_A": int(stats["FZ5"]),
        "Target_B": int(stats["FZ6"]), "prune_histogram": {
            key.split("prune:", 1)[1]: int(value) for key, value in sorted(stats.items()) if key.startswith("prune:")
        },
        "checkpoint": {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "bytes": path.stat().st_size},
    }


def aggregate(manifest: Mapping[str, object], stage: str, rows: list[Mapping[str, object]]) -> None:
    counts = Counter()
    for row in rows:
        counts.update(row["FZ_counts"])
    result = {
        "schema": RESULT_SCHEMA, "scope": "six independent seed families; capped branches remain INCOMPLETE",
        "event_semantics": EVENT_SEMANTICS, "manifest_sha256": sha256_json(manifest),
        "stage": stage, "stage_cumulative_target_per_nonexhausted_seed": stage_target(stage),
        "start_state_count": int(manifest["start_domain"]["literal_records"]),
        "branches": rows,
        "aggregate": {
            "expansions": sum(int(row["expansions"]) for row in rows),
            "unique_exact_state_digest_sum": sum(int(row["unique_exact_state_digests"]) for row in rows),
            "frontier": sum(int(row["frontier_size"]) for row in rows),
            "Z3_transitions": sum(int(row["Z3_transitions"]) for row in rows),
            "first_component_change_witnesses": sum(int(row["first_component_change_witnesses"]) for row in rows),
            "FZ_counts": {level: int(counts[level]) for level in FZ_LEVELS},
            "Target_A": sum(int(row["literal_Target_A"]) for row in rows),
            "Target_B": sum(int(row["Target_B"]) for row in rows),
        },
        "overall_status": (
            "FIRST_COMPONENT_Z3_WITNESS_FOUND" if any(row["first_component_change_witnesses"] for row in rows)
            else "FIRST_COMPONENT_Z3_SEARCH_INCOMPLETE" if any(row["frontier_size"] for row in rows)
            else "FIRST_COMPONENT_Z3_IMPOSSIBLE_PROVED"
        ),
    }
    witnesses = []
    for row in rows:
        raw = json.loads((ROOT / row["checkpoint"]["path"]).read_text(encoding="utf-8"))
        witnesses.extend(raw["witnesses"])
    atomic_json(RESULT_OUT, result)
    atomic_json(WITNESS_OUT, {
        "schema": "rr-short-ell2-r1-37-first-component-z3-witnesses-v1",
        "event_semantics": EVENT_SEMANTICS, "witness_count": len(witnesses), "witnesses": witnesses,
    })
    atomic_json(STATS_OUT, {
        "schema": "rr-short-ell2-r1-37-component-change-stats-v1", "stage": stage,
        "aggregate": result["aggregate"], "per_seed": rows,
        "negative_scope": "zero events in a nonempty capped branch are observations only",
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initialize-only", action="store_true")
    parser.add_argument("--stage", choices=STAGE_ORDER, default="A")
    parser.add_argument("--seed-id", choices=SOURCE_IDS)
    parser.add_argument("--checkpoint-every", type=int, default=10_000)
    args = parser.parse_args()
    if args.checkpoint_every <= 0:
        raise ValueError("checkpoint interval must be positive")
    manifest = build_manifest()
    if MANIFEST_OUT.exists():
        stored = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        if stored != manifest:
            raise AssertionError("frozen first-component manifest changed")
    else:
        atomic_json(MANIFEST_OUT, manifest)
    selected = (args.seed_id,) if args.seed_id else SOURCE_IDS
    rows = []
    for seed_id in selected:
        path = checkpoint_path(seed_id)
        if args.initialize_only:
            if not path.exists():
                engine = initialize_seed(manifest, seed_id)
                checkpoint_and_progress(manifest, seed_id, engine, "INITIALIZED", time.monotonic())
            else:
                engine = load_checkpoint(manifest, seed_id)
            row = summarize_seed(seed_id, engine, path, "INITIALIZED")
        else:
            row = run_seed(manifest, seed_id, args.stage, checkpoint_every=args.checkpoint_every)
        rows.append(row)
        print(json.dumps({"seed_id": seed_id, "status": row["status"], "expansions": row["expansions"],
                          "frontier": row["frontier_size"], "fz": row["first_component_change_witnesses"]}, sort_keys=True))
    if not args.initialize_only:
        if len(selected) == len(SOURCE_IDS):
            aggregate(manifest, args.stage, rows)
        else:
            prior = json.loads(RESULT_OUT.read_text(encoding="utf-8"))["branches"] if RESULT_OUT.exists() else []
            merged = {str(row["seed_id"]): row for row in prior}
            merged.update({str(row["seed_id"]): row for row in rows})
            if set(merged) == set(SOURCE_IDS):
                aggregate(manifest, args.stage, [merged[name] for name in SOURCE_IDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
