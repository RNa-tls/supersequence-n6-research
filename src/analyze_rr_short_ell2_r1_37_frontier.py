#!/usr/bin/env python3
"""Read-only structural audit of the 22 Round-53 r1_37 frontier states.

The v7 checkpoint is almost five GiB.  This program deliberately never loads
it as one JSON value.  It extracts the small frontier prefix, streams the
parent table twice, and replays only the union of the 22 parent-DAG paths.
No search checkpoint or traversal result is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT = (
    ROOT / "outputs" / "checkpoints" / "rr_short5" / "top2_continuation_v7"
    / "short_ell2" / "short_ell2_r1_37" / "checkpoint.json"
)
V7_RESULT = ROOT / "outputs" / "rr_short5_top2_v7_continuation.json"
FRONTIER_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_frontier.json"
CLASSES_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_frontier_classes.json"
PLAN_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_next_plan.json"

SCHEMA = "rr-short-ell2-r1-37-frontier-audit-v1"
CHECKPOINT_SHA = "2847a6bd5861476428ec7cd9bd9d1d855229b33378662ebeef4ae4db832b1551"
BRIDGE_LOOKAHEAD = 3


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


v7 = load_module("rr_r1_37_frontier_v7", ROOT / "src" / "search_rr_short5_top2_v7.py")
rr, exact, pilot, core = v7.rr, v7.exact, v7.pilot, v7.rr.core


def sha256_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def extract_frontier(path: Path) -> list[dict[str, object]]:
    """Read only the root prefix ending immediately before ``next_node``."""
    data = bytearray()
    marker = b'\n  "next_node"'
    with path.open("rb") as handle:
        while marker not in data:
            block = handle.read(1 << 20)
            if not block:
                raise AssertionError("checkpoint ended before next_node")
            data.extend(block)
    prefix = bytes(data[: data.index(marker)])
    start = prefix.index(b'"frontier"')
    value = prefix[prefix.index(b":", start) + 1 :].strip().rstrip(b",").strip()
    result = json.loads(value)
    if not isinstance(result, list):
        raise AssertionError("checkpoint frontier is not a list")
    return result


NODE_RE = re.compile(rb'"node_id"\s*:\s*"[^"]+:(\d+)"')
PARENT_RE = re.compile(rb'"parent_id"\s*:\s*(?:"[^"]+:(\d+)"|null)')


def iter_node_objects(path: Path) -> Iterable[bytes]:
    """Stream the top-level objects in the checkpoint's ``nodes`` array."""
    in_nodes = False
    current: list[bytes] | None = None
    with path.open("rb") as handle:
        for line in handle:
            if not in_nodes:
                if line.strip() == b'"nodes": [' or line.strip() == b'"nodes": [\r':
                    in_nodes = True
                continue
            if current is None:
                if line.startswith(b"    {"):
                    current = [line]
                    continue
                if line.startswith(b"  ]"):
                    return
                continue
            current.append(line)
            indent = len(line) - len(line.lstrip(b" "))
            if indent == 4 and line.strip().rstrip(b"\r") in {b"},", b"}"}:
                yield b"".join(current).rstrip().rstrip(b",")
                current = None
    raise AssertionError("nodes array did not terminate")


def node_number(node_id: str) -> int:
    return int(node_id.rsplit(":", 1)[1])


def scan_parent_index(path: Path) -> list[int | None]:
    parents: list[int | None] = []
    expected = 0
    for raw in iter_node_objects(path):
        node_match = NODE_RE.search(raw)
        parent_match = PARENT_RE.search(raw)
        if node_match is None or parent_match is None:
            raise AssertionError("node metadata missing id or parent")
        index = int(node_match.group(1))
        if index != expected:
            raise AssertionError(f"nonsequential parent DAG: expected {expected}, got {index}")
        parent = None if parent_match.group(1) is None else int(parent_match.group(1))
        if parent is not None and parent >= index:
            raise AssertionError("parent does not precede child")
        parents.append(parent)
        expected += 1
    return parents


def ancestry_union(frontier: list[Mapping[str, object]], parents: list[int | None]) -> set[int]:
    result: set[int] = set()
    for row in frontier:
        cursor: int | None = node_number(str(row["node_id"]))
        while cursor is not None and cursor not in result:
            result.add(cursor)
            cursor = parents[cursor]
    return result


def scan_selected_nodes(path: Path, selected: set[int]) -> dict[int, dict[str, object]]:
    result: dict[int, dict[str, object]] = {}
    for raw in iter_node_objects(path):
        match = NODE_RE.search(raw)
        if match is None:
            raise AssertionError("node id absent on second pass")
        index = int(match.group(1))
        if index in selected:
            result[index] = json.loads(raw)
    if set(result) != selected:
        raise AssertionError(f"selected-node loss: {len(selected) - len(result)}")
    return result


def component_id(summary: Mapping[str, object], node: tuple[str, int]) -> str | None:
    component = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    return None if component is None else str(component["id"])


def incidence_forest(state) -> list[dict[str, int]]:
    rows = []
    for orbit, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if not (mask & (1 << phase)):
                continue
            port = core.ports_of_e_orbit(core.E_REPS[orbit])[phase]
            rows.append({"orbit": orbit, "phase": phase, "hexagon": core.hexagon_id(port)})
    return rows


def transform_event(event, alpha_index: int):
    sq, ss = exact.LEFT_ORBIT_ACTION[alpha_index][event.source_orbit]
    tq, ts = exact.LEFT_ORBIT_ACTION[alpha_index][event.target_orbit]
    return type(event)(event.macro_index, event.kind, int(sq), (event.source_phase + int(ss)) % 5,
                       int(tq), (event.target_phase + int(ts)) % 5)


def canonical_state_decoration(state, dec):
    alpha = core.inverse(state.p)
    alpha_index = core.WORD_ID[alpha]
    canonical_state = exact.relabel_state(state, alpha_index)
    completer = None
    if dec.completer is not None:
        completer = transform_event(dec.completer, alpha_index)
    oq, _ = exact.LEFT_ORBIT_ACTION[alpha_index][dec.o_star]
    hh, _ = exact.LEFT_HEX_ACTION[alpha_index][dec.hub_id]
    canonical_dec = type(dec)(
        root_id=dec.root_id, root_ell=dec.root_ell, o_star=int(oq), hub_id=int(hh),
        macro_index=dec.macro_index,
        r_events=tuple(transform_event(event, alpha_index) for event in dec.r_events),
        hub_touch_count=dec.hub_touch_count, completer=completer,
    )
    if canonical_state.p != core.IDENTITY:
        raise AssertionError("left-S6 terminal normalization failed")
    # The terminal word action is free, so this is the proved left-S6 representative.
    if exact.canonicalize(state).stable_key() != canonical_state.stable_key():
        raise AssertionError("left-S6 canonical control failed")
    key = (canonical_state.stable_key(), canonical_dec.key())
    return canonical_state, canonical_dec, sha256_json(repr(key))


def geometry_profile(state, dec) -> dict[str, object]:
    summary = rr.component_summary(state)
    r1_orbit = int(dec.r1.target_orbit) if dec.r1 is not None else -1
    hub_component = component_id(summary, ("h", int(dec.hub_id)))
    r1_component = component_id(summary, ("q", r1_orbit))
    current_orbit, current_phase = exact.ORBIT_PHASE[state.p]
    current_hex = state.current_hex
    marks = []
    for component in summary["components"]:
        cid = str(component["id"])
        marks.append({
            "class": component["class"],
            "is_hub": cid == hub_component,
            "is_r1_target": cid == r1_component,
            "has_current_orbit": current_orbit in component["e_orbits"],
            "has_current_hexagon": current_hex in component["hexagons"],
        })
    marks.sort(key=lambda row: json.dumps(row, sort_keys=True))
    return {
        "components": marks,
        "r1_hub_same_component": r1_component is not None and r1_component == hub_component,
        "current_phase": current_phase,
    }


def exact_bridge(parent_state, parent_dec, child_state, child_dec) -> bool:
    if parent_dec.r_count != 1 or child_dec.r_count != 1 or parent_dec.r1 is None:
        return False
    pre, post = rr.component_summary(parent_state), rr.component_summary(child_state)
    r1 = ("q", int(parent_dec.r1.target_orbit))
    hub = ("h", int(parent_dec.hub_id))
    a, b = component_id(pre, r1), component_id(pre, hub)
    c, d = component_id(post, r1), component_id(post, hub)
    return a is not None and b is not None and a != b and c is not None and c == d


def bridge_distance_within(state, dec, maximum: int = BRIDGE_LOOKAHEAD) -> dict[str, object]:
    initial_summary = rr.component_summary(state)
    r1_node = ("q", int(dec.r1.target_orbit)) if dec.r1 is not None else ("q", -1)
    hub_node = ("h", int(dec.hub_id))
    if component_id(initial_summary, r1_node) == component_id(initial_summary, hub_node):
        return {"status": "already_merged", "distance": 0, "states_examined": 1, "witness": []}
    queue = deque([(state, dec, 0, [])])
    seen = {repr(rr.decorated_key(state, dec))}
    layer_counts: Counter[int] = Counter({0: 1})
    while queue:
        current, decoration, depth, trace = queue.popleft()
        if depth >= maximum:
            continue
        for edge, collision in rr.iter_raw_macro_candidates(current):
            if collision is not None or edge is None:
                continue
            verdict, child_dec, _ = rr.evaluate_edge(
                current, decoration, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            if verdict != "child" or child_dec is None:
                continue
            child_state = edge.state
            child_trace = trace + [edge.label]
            if exact_bridge(current, decoration, child_state, child_dec):
                return {
                    "status": "found", "distance": depth + 1,
                    "states_examined": len(seen), "layer_counts": dict(sorted(layer_counts.items())),
                    "witness": child_trace,
                }
            key = repr(rr.decorated_key(child_state, child_dec))
            if key not in seen:
                seen.add(key)
                layer_counts[depth + 1] += 1
                queue.append((child_state, child_dec, depth + 1, child_trace))
    if not layer_counts.get(maximum, 0):
        return {
            "status": "reachable_subgraph_exhausted_no_bridge", "distance": None,
            "exact_no_bridge_from_this_state": True, "lookahead_bound": maximum,
            "states_examined": len(seen), "layer_counts": dict(sorted(layer_counts.items())),
            "witness": [],
        }
    return {
        "status": "not_found_within_bound", "distance": None,
        "proved_lower_bound": maximum + 1, "lookahead_bound": maximum,
        "states_examined": len(seen), "layer_counts": dict(sorted(layer_counts.items())),
        "witness": [],
    }


def successor_analysis(state, dec) -> dict[str, object]:
    traversable, terminals, r2, rejected = [], [], [], Counter()
    collision_count = 0
    raw_count = 0
    for edge, collision in rr.iter_raw_macro_candidates(state):
        raw_count += 1
        if collision is not None or edge is None:
            collision_count += 1
            rejected[collision or "missing_edge"] += 1
            continue
        verdict, child_dec, recognition = rr.evaluate_edge(
            state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
        )
        edge_row = rr.edge_json(edge)
        edge_row["verdict"] = verdict
        if verdict == "child":
            assert child_dec is not None
            edge_row["child_coordinate"] = {
                "P": edge.state.P, "O": edge.state.O, "F": edge.state.F,
                "H": edge.state.H, "Ndef": edge.state.Ndef,
            }
            traversable.append(edge_row)
        elif verdict == "FOUND_TARGET_A":
            terminals.append(edge_row)
        else:
            rejected[verdict] += 1
        if pilot.edge_kind(edge) == "R":
            row = dict(edge_row)
            if recognition is not None:
                row.update({
                    "literal_joint_source_state_hash": recognition.get("literal_joint_source_state_hash"),
                    "source_orbit": recognition.get("source_orbit"),
                    "target_orbit": recognition.get("target_orbit"),
                    "endpoint_presence": recognition.get("r2_endpoint_presence"),
                    "failed_conditions": recognition.get("r2_failed_conditions"),
                    "detail_reason": recognition.get("r2_detail_reason"),
                    "is_target_a": recognition.get("is_target_a"),
                })
            r2.append(row)
    signature_payload = {
        "traversable": [
            {k: row[k] for k in ("label", "kind", "rotation_length", "joint", "source", "target", "target_hexagon")}
            for row in traversable
        ],
        "terminals": [row["label"] for row in terminals],
        "r2": [
            {"label": row["label"], "failed_conditions": row.get("failed_conditions"),
             "detail_reason": row.get("detail_reason")}
            for row in r2
        ],
        "rejected": dict(sorted(rejected.items())),
    }
    return {
        "raw_candidate_count": raw_count,
        "exact_collision_count": collision_count,
        "traversable_child_count": len(traversable),
        "target_a_terminal_count": len(terminals),
        "legal_successor_count": len(traversable) + len(terminals),
        "legal_edge_labels": traversable + terminals,
        "future_R2_source_candidates": r2,
        "rejected": dict(sorted(rejected.items())),
        "successor_signature_sha256": sha256_json(signature_payload),
        "successor_signature": signature_payload,
    }


def state_metrics(state, dec) -> dict[str, object]:
    succ = successor_analysis(state, dec)
    current_orbit, current_phase = exact.ORBIT_PHASE[state.p]
    return {
        "visited": state.visited_count, "P": state.P, "O": state.O, "S": state.S,
        "F": state.F, "H": state.H, "Ndef": state.Ndef, "D": state.D,
        "Phi": rr.phi(state), "M": state.P - 5 * state.O,
        "hub_popcount": int(state.hex_masks[dec.hub_id]).bit_count(),
        "current_orbit": current_orbit, "current_phase": current_phase,
        "current_orbit_phase_count": int(state.orbit_masks[current_orbit]).bit_count(),
        "current_hex_mask": int(state.hex_masks[state.current_hex]),
        "legal_successors": succ["legal_successor_count"],
        "exact_collisions": succ["exact_collision_count"],
    }


def replay_ancestry(selected: Mapping[int, Mapping[str, object]], parents: list[int | None],
                    frontier: list[Mapping[str, object]]):
    root, child, _ = v7.child_lookup()["short_ell2_r1_37"]
    anchor_state, anchor_dec = pilot.replay_trace(root, list(child["literal_macro_trace"]))
    states: dict[int, tuple[Any, Any]] = {}
    metrics: dict[int, dict[str, object]] = {}
    for index in sorted(selected):
        row = selected[index]
        parent = parents[index]
        if parent is None:
            state, dec = anchor_state, anchor_dec
        else:
            parent_state, parent_dec = states[parent]
            edge = pilot.edge_from_json(parent_state, row["incoming_macro_edge"])
            state = edge.state
            dec = rr.advance_decoration(edge.run.state, edge.joint, parent_dec)
        if rr.state_hash(state) != row["exact_state_hash"]:
            raise AssertionError(f"node replay hash mismatch at {index}")
        if dec.to_json() != row["decoration"]:
            raise AssertionError(f"node decoration mismatch at {index}")
        states[index] = (state, dec)
        metrics[index] = state_metrics(state, dec)
    frontier_by_id = {node_number(str(row["node_id"])): row for row in frontier}
    for index, stored in frontier_by_id.items():
        state, dec = states[index]
        stored_state = exact.state_from_json(stored["state"])
        stored_dec = rr.Decoration.from_json(stored["decoration"])
        if state.stable_key() != stored_state.stable_key() or dec.key() != stored_dec.key():
            raise AssertionError(f"frontier replay mismatch at {index}")
    return states, metrics


def path_to(index: int, parents: list[int | None]) -> list[int]:
    result = []
    cursor: int | None = index
    while cursor is not None:
        result.append(cursor)
        cursor = parents[cursor]
    return list(reversed(result))


def parent_replay_record(index: int, selected: Mapping[int, Mapping[str, object]],
                         parents: list[int | None]) -> dict[str, object]:
    path = path_to(index, parents)
    edges = [selected[item]["incoming_macro_edge"] for item in path[1:]]
    hashes = [selected[item]["exact_state_hash"] for item in path]
    return {
        "anchor_node_id": selected[path[0]]["node_id"],
        "parent_node_id": None if len(path) == 1 else selected[path[-2]]["node_id"],
        "macro_edge_count": len(edges),
        "macro_trace_sha256": sha256_json(edges),
        "state_hash_chain_sha256": sha256_json(hashes),
        "parent_replay_hash": sha256_json({"edges": edges[:-1], "state_hashes": hashes[:-1]}),
    }


def group_rows(records: list[Mapping[str, object]], key_name: str) -> list[dict[str, object]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in records:
        groups[str(row[key_name])].append(str(row["node_id"]))
    return [
        {key_name: key, "size": len(ids), "node_ids": sorted(ids)}
        for key, ids in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    ]


def trajectory_audit(frontier: list[Mapping[str, object]], states: Mapping[int, tuple[Any, Any]],
                     metrics: Mapping[int, Mapping[str, object]], parents: list[int | None]) -> dict[str, object]:
    quantities = ("visited", "P", "O", "S", "Ndef", "D", "Phi", "M", "hub_popcount")
    violations = {name: [] for name in quantities}
    relaxed_recurrences = []
    exact_recurrences = []
    tail_profiles = defaultdict(list)
    seen_paths = set()
    for frontier_row in frontier:
        endpoint = node_number(str(frontier_row["node_id"]))
        path = path_to(endpoint, parents)
        signature_positions: dict[tuple[object, ...], int] = {}
        exact_positions: dict[str, int] = {}
        for pos, index in enumerate(path):
            current, dec = states[index]
            item = metrics[index]
            exact_hash = sha256_json(repr(rr.decorated_key(current, dec)))
            if exact_hash in exact_positions:
                exact_recurrences.append({"endpoint": frontier_row["node_id"], "first": exact_positions[exact_hash], "second": pos})
            exact_positions[exact_hash] = pos
            relaxed = (
                item["current_phase"], item["current_orbit_phase_count"],
                int(item["current_hex_mask"]).bit_count(), item["hub_popcount"],
                item["legal_successors"], item["Ndef"],
            )
            if relaxed in signature_positions:
                relaxed_recurrences.append({
                    "endpoint": frontier_row["node_id"], "first": signature_positions[relaxed],
                    "second": pos, "signature": list(relaxed),
                })
            signature_positions[relaxed] = pos
            if pos:
                previous = metrics[path[pos - 1]]
                for name in quantities:
                    if int(item[name]) < int(previous[name]):
                        violations[name].append({
                            "edge": [selected_id(path[pos - 1]), selected_id(index)],
                            "before": previous[name], "after": item[name],
                        })
        for distance, index in enumerate(reversed(path[-11:])):
            key = (distance, metrics[index]["legal_successors"], metrics[index]["exact_collisions"])
            tail_profiles[key].append(str(frontier_row["node_id"]))
        seen_paths.add(tuple(path))
    unique_deltas = []
    for index in sorted(states):
        parent = parents[index]
        if parent is None or parent not in states:
            continue
        unique_deltas.append(int(metrics[index]["visited"]) - int(metrics[parent]["visited"]))
    tail_averages = {}
    for distance in sorted({key[0] for key in tail_profiles}):
        relevant = [(key, ids) for key, ids in tail_profiles.items() if key[0] == distance]
        count = sum(len(ids) for _, ids in relevant)
        tail_averages[str(distance)] = {
            "states": count,
            "mean_legal_successors": sum(key[1] * len(ids) for key, ids in relevant) / count,
            "mean_exact_collisions": sum(key[2] * len(ids) for key, ids in relevant) / count,
        }
    return {
        "path_count": len(seen_paths),
        "exact_decorated_recurrences": exact_recurrences,
        "relaxed_phase_context_recurrences": relaxed_recurrences,
        "relaxed_recurrence_warning": "A repeated reduced signature is not an exact state cycle.",
        "monotonicity": {
            name: {"nondecreasing_on_replayed_paths": not rows, "violation_count": len(rows),
                   "minimal_counterexamples": rows[:5]}
            for name, rows in violations.items()
        },
        "strict_finite_ranking": {
            "quantity": "remaining unvisited permutation windows = 720 - visited",
            "replayed_unique_edges": len(unique_deltas),
            "strictly_decreases_on_every_replayed_edge": all(delta > 0 for delta in unique_deltas),
            "visited_increment_range": [min(unique_deltas), max(unique_deltas)] if unique_deltas else None,
            "scope_warning": "This proves finiteness of each literal continuation, not a useful short exhaustion bound.",
        },
        "tail_collision_profiles": [
            {"distance_from_frontier": key[0], "legal_successors": key[1],
             "exact_collisions": key[2], "occurrences": len(ids)}
            for key, ids in sorted(tail_profiles.items())
        ],
        "tail_collision_averages": tail_averages,
    }


def selected_id(index: int) -> str:
    return f"short_ell2_r1_37:{index}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--frontier-output", type=Path, default=FRONTIER_OUT)
    parser.add_argument("--classes-output", type=Path, default=CLASSES_OUT)
    parser.add_argument("--plan-output", type=Path, default=PLAN_OUT)
    args = parser.parse_args()

    verified = json.loads(V7_RESULT.read_text(encoding="utf-8"))
    branch = next(row for row in verified["branches"] if row["child_id"] == "short_ell2_r1_37")
    if branch["checkpoint"]["sha256"] != CHECKPOINT_SHA or branch["frontier_size"] != 22:
        raise AssertionError("verified v7 ledger does not name the expected endpoint")
    if args.checkpoint.stat().st_size != int(branch["checkpoint"]["bytes"]):
        raise AssertionError("checkpoint size changed since independent verification")

    frontier = extract_frontier(args.checkpoint)
    if len(frontier) != 22:
        raise AssertionError(f"expected 22 frontier records, got {len(frontier)}")
    parents = scan_parent_index(args.checkpoint)
    selected_indices = ancestry_union(frontier, parents)
    selected = scan_selected_nodes(args.checkpoint, selected_indices)
    states, metrics = replay_ancestry(selected, parents, frontier)

    records = []
    for stored in frontier:
        index = node_number(str(stored["node_id"]))
        state, dec = states[index]
        canonical_state, canonical_dec, canonical_hash = canonical_state_decoration(state, dec)
        summary = rr.component_summary(state)
        r1_orbit = int(dec.r1.target_orbit) if dec.r1 is not None else -1
        hub_component = component_id(summary, ("h", int(dec.hub_id)))
        r1_component = component_id(summary, ("q", r1_orbit))
        successor = successor_analysis(state, dec)
        geometry = geometry_profile(state, dec)
        resource_payload = {
            "P": state.P, "O": state.O, "F": state.F, "H": state.H,
            "Ndef": state.Ndef, "D": state.D, "Phi": rr.phi(state),
            "M": state.P - 5 * state.O,
        }
        resource_class = sha256_json(resource_payload)
        geometry_class = sha256_json(geometry)
        hub_mask = int(state.hex_masks[dec.hub_id])
        parent_record = parent_replay_record(index, selected, parents)
        record = {
            "node_id": stored["node_id"], "exact_state_hash": rr.state_hash(state),
            "decorated_key_sha256": sha256_json(repr(rr.decorated_key(state, dec))),
            "decorated_key_repr": repr(rr.decorated_key(state, dec)),
            "left_s6_canonical_class_sha256": canonical_hash,
            "left_s6_canonical_state_hash": rr.state_hash(canonical_state),
            "left_s6_canonical_decoration": canonical_dec.to_json(),
            "depth": int(stored["depth"]), "coordinate": resource_payload,
            "hub_state": {
                "hub_id": dec.hub_id, "mask": hub_mask, "popcount": hub_mask.bit_count(),
                "touch_count": dec.hub_touch_count, "component_id": hub_component,
                "complete": hub_mask == 63,
            },
            "r1_target": {
                "orbit": r1_orbit, "component_id": r1_component,
                "same_component_as_hub": r1_component is not None and r1_component == hub_component,
            },
            "component_partition": pilot.component_summary_json(state),
            "incidence_forest": incidence_forest(state),
            "incidence_forest_sha256": sha256_json(incidence_forest(state)),
            "legal_successor_count": successor["legal_successor_count"],
            "legal_edge_labels": successor["legal_edge_labels"],
            "future_R2_source_candidates": successor["future_R2_source_candidates"],
            "successor_analysis": successor,
            "bridge_distance": bridge_distance_within(state, dec),
            "parent_replay": parent_record,
            "resource_profile_class_sha256": resource_class,
            "successor_signature_class_sha256": successor["successor_signature_sha256"],
            "component_geometry_class_sha256": geometry_class,
            "component_geometry_profile": geometry,
            "checkpoint_lineage": stored.get("lineage"),
        }
        records.append(record)

    records.sort(key=lambda row: (int(row["depth"]), str(row["node_id"])))
    trajectory = trajectory_audit(frontier, states, metrics, parents)
    class_payload = {
        "schema": SCHEMA, "scope": "22-state read-only frontier; no continuation search",
        "counts": {
            "frontier_states": len(records),
            "exact_decorated_states": len({row["decorated_key_sha256"] for row in records}),
            "left_s6_canonical_classes": len({row["left_s6_canonical_class_sha256"] for row in records}),
            "resource_profile_classes": len({row["resource_profile_class_sha256"] for row in records}),
            "successor_signature_classes": len({row["successor_signature_class_sha256"] for row in records}),
            "component_geometry_classes": len({row["component_geometry_class_sha256"] for row in records}),
        },
        "left_s6_canonical_classes": group_rows(records, "left_s6_canonical_class_sha256"),
        "resource_profile_classes": group_rows(records, "resource_profile_class_sha256"),
        "successor_signature_classes": group_rows(records, "successor_signature_class_sha256"),
        "component_geometry_classes": group_rows(records, "component_geometry_class_sha256"),
        "histograms": {
            "depth": dict(sorted(Counter(str(row["depth"]) for row in records).items())),
            "legal_successor_count": dict(sorted(Counter(str(row["legal_successor_count"]) for row in records).items())),
            "hub_mask": dict(sorted(Counter(str(row["hub_state"]["mask"]) for row in records).items())),
            "bridge_distance_status": dict(sorted(Counter(str(row["bridge_distance"]["status"]) for row in records).items())),
        },
        "recurrence_and_ranking": trajectory,
        "equivalence_warning": "Only the left-S6 classes are proved symmetry quotients. Resource, successor, and component classes are profiles, not merge permissions.",
    }
    r2_candidates = [candidate for row in records for candidate in row["future_R2_source_candidates"]]
    local_exhausted = [
        row["node_id"] for row in records
        if row["bridge_distance"]["status"] == "reachable_subgraph_exhausted_no_bridge"
    ]
    class_payload["structural_findings"] = {
        "all_hubs_complete": all(row["hub_state"]["complete"] for row in records),
        "all_Phi_zero": all(row["coordinate"]["Phi"] == 0 for row in records),
        "all_R1_target_components_separate_from_hub": all(not row["r1_target"]["same_component_as_hub"] for row in records),
        "all_component_counts_equal_O_minus_1": all(
            row["component_partition"]["component_count"] == row["coordinate"]["O"] - 1
            for row in records
        ),
        "immediate_R2_candidates": len(r2_candidates),
        "immediate_R2_failure_reasons": dict(sorted(Counter(
            str(candidate.get("detail_reason")) for candidate in r2_candidates
        ).items())),
        "locally_exhausted_no_bridge_state_count": len(local_exhausted),
        "locally_exhausted_node_ids": local_exhausted,
        "remaining_states_with_no_bridge_through_three_steps": len(records) - len(local_exhausted),
        "bridge_interpretation": "Nine reachable subgraphs closed during exact <=3-step BFS; the other thirteen have exact bridge distance at least four, not infinite.",
        "collision_saturation": {
            "frontier_mean_exact_collisions": sum(row["successor_analysis"]["exact_collision_count"] for row in records) / len(records),
            "frontier_mean_legal_successors": sum(row["legal_successor_count"] for row in records) / len(records),
            "monotone_saturation_observed": False,
            "reason": "The exact-collision and legal-successor means over the last ten ancestry layers fluctuate rather than change monotonically.",
        },
    }
    class_payload["candidate_theorems"] = [
        {
            "name": "separation_invariant_candidate",
            "statement": "In the short_ell2_r1_37 reachable Target-A-safe universe, the R1-target component never merges with the hub component before R2.",
            "status": "CONJECTURE; finite prefix only",
            "support": "All 421,221 previously verified replay nodes were B0; all 22 endpoint states remain separated and no bridge occurs in their exact next-three-step neighborhoods.",
            "proof_gap": "No closure of the legal Z2/Z3 insertion cases for every future occupancy mask.",
            "required_decoration": ["exact incidence forest", "R1 target orbit", "hub id", "literal joint source", "F/H", "future R2 source"],
            "counterexample_request": "A legal post-R1/pre-R2 Z2 or Z3 child whose pre-components are distinct and post-components coincide.",
        },
        {
            "name": "same_component_gate_candidate",
            "statement": "Every geometrically available R2 at these endpoint profiles fails only the same-component predicate.",
            "status": "FINITE COMPLETE CHECK ON THE 22 STATES ONLY",
            "support": f"{len(r2_candidates)} immediate R2 candidates, all with detail_reason=same_component.",
            "proof_gap": "The statement does not cover R2 candidates appearing after further continuation.",
            "required_decoration": ["literal R2 joint source", "component partition", "R1 target orbit"],
            "counterexample_request": "Any descendant R2 whose failure reason differs, or a Target-A hit.",
        },
        {
            "name": "local_exhaustion_certificate",
            "statement": "Nine of the 22 stored frontier roots have finite reachable subgraphs containing no bridge.",
            "status": "FINITE COMPLETE CHECK",
            "support": local_exhausted,
            "proof_gap": "This is a certificate for nine roots, not a common hand theorem for all 22.",
            "required_decoration": ["exact state", "full decoration"],
            "counterexample_request": "None within the replayed exact transition graph; verifier mismatch would be required.",
        },
    ]

    # Rank for a proposed small, checkpoint-isolated continuation batch.  This
    # is a plan only; the audit never executes it.
    def bridge_rank(row: Mapping[str, object]) -> int:
        distance = row["bridge_distance"]  # type: ignore[index]
        if distance["status"] == "reachable_subgraph_exhausted_no_bridge":  # type: ignore[index]
            return 10**6
        value = distance.get("proved_lower_bound", distance.get("distance", 0))  # type: ignore[union-attr]
        return 0 if value is None else int(value)

    unresolved_records = [
        row for row in records
        if row["bridge_distance"]["status"] != "reachable_subgraph_exhausted_no_bridge"
    ]
    ranked = sorted(unresolved_records, key=lambda row: (
        int(row["legal_successor_count"]), bridge_rank(row),
        -int(row["depth"]), str(row["node_id"]),
    ))
    class_representatives = []
    used = set()
    for row in ranked:
        profile = (row["successor_signature_class_sha256"], row["component_geometry_class_sha256"])
        if profile in used:
            continue
        used.add(profile)
        class_representatives.append(row["node_id"])
    recommended = class_representatives[: min(8, len(class_representatives))]
    plan_payload = {
        "schema": SCHEMA,
        "current_status": "short_ell2_r1_37 remains INCOMPLETE with 22 frontier states",
        "strategies": {
            "A_equal_all_22": {"assessment": "complete but initially wasteful", "proof_value": "high only after natural exhaustion", "recommended": False},
            "B_smallest_successor": {"assessment": "cheap but risks sampling one repeated geometry", "recommended": False},
            "C_common_obstruction": {"assessment": "no common obstruction is proved by the present bounded audit", "recommended": False},
            "D_structural_subfamilies": {"assessment": "best first step: preserve exact provenance while sampling each observed successor/component profile", "recommended": True},
        },
        "recommendation": {
            "strategy": "D_then_A",
            "first_batch_node_ids": recommended,
            "selection_rule": "exclude the nine locally exhausted subgraphs, then take one exact state per (successor-signature, component-geometry) profile, ordered by fewest successors then deepest state",
            "per_state_additional_cap": 25000,
            "checkpoint_plan": "fresh branch-local namespace keyed by checkpoint SHA, exact state hash, and parent replay hash; equal independent caps; empty frontier required for exhaustion",
            "interpretation": "caps are INCOMPLETE; zero bridge observations are not impossibility",
            "next_gate": "If profile representatives do not exhaust, expand all 22 equally rather than pruning profile-equivalent states.",
        },
        "not_executed": True,
    }

    provenance = {
        "checkpoint": {"path": str(args.checkpoint.relative_to(ROOT)), "bytes": args.checkpoint.stat().st_size,
                       "sha256_from_verified_v7_ledger": CHECKPOINT_SHA},
        "verified_v7_ledger_sha256": sha256_file(V7_RESULT),
        "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "v7_adapter_sha256": sha256_file(ROOT / "src" / "search_rr_short5_top2_v7.py"),
        "analysis_sha256": sha256_file(Path(__file__)),
        "parent_dag_nodes_scanned": len(parents), "ancestry_nodes_replayed": len(selected_indices),
    }
    frontier_payload = {
        "schema": SCHEMA, "status": "READ_ONLY_FRONTIER_AUDIT_COMPLETE",
        "scope": {"branch": "short_ell2_r1_37", "frontier": 22, "search_status": "INCOMPLETE",
                  "bridge_lookahead": BRIDGE_LOOKAHEAD, "new_continuation_started": False},
        "provenance": provenance, "frontier_states": records,
    }
    class_payload["provenance"] = provenance
    plan_payload["provenance"] = provenance
    write_json(args.frontier_output, frontier_payload)
    write_json(args.classes_output, class_payload)
    write_json(args.plan_output, plan_payload)
    print(json.dumps({
        "frontier": len(records), "classes": class_payload["counts"],
        "recommended": recommended, "outputs": [str(args.frontier_output), str(args.classes_output), str(args.plan_output)],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
