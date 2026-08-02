#!/usr/bin/env python3
"""Round 44: exact provenance split of the four `short_ell0` R1 children.

This is deliberately a *read-only replay* of the historical 100,250-node v3
prefix.  It never resumes, overwrites, or otherwise consumes the combined v3
checkpoint as an input frontier.  Instead it reconstructs the literal root,
propagates an explicit R1-origin tag after the first R event, and writes four
separate v4 branch snapshots.  A positive node limit is always INCOMPLETE.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Mapping, Optional


ROOT = Path(__file__).resolve().parent.parent
V3_OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v3.json"
V3_CHECKPOINT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v3" / "short_ell0_medium.json"
ROUND43_GEOMETRY = ROOT / "outputs" / "rr_short_ell0_v3_geometry_failures.json"
BRANCH_OUTPUT = ROOT / "outputs" / "rr_short_ell0_r1_branches.json"
PRODUCTIVE_OUTPUT = ROOT / "outputs" / "rr_short_ell0_productive_branch_candidates.json"
PRETARGET_OUTPUT = ROOT / "outputs" / "rr_short_ell0_pre_target_a_results.json"
CHECKPOINT_ROOT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_split_v4"
BRANCH_SCHEMA = "rr-target-a-exhaustive-checkpoint-v4-short-r1-origin"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


short5 = load("rr_r1_split_short5", ROOT / "src" / "search_rr_short5_exact.py")
rr = short5.rr
exact, core, macro = rr.exact, rr.core, rr.macro


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def record() -> dict[str, object]:
    rows = [row for row in short5.short_root_records() if row["root_id"] == "short_ell0"]
    if len(rows) != 1:
        raise AssertionError("short_ell0 root is not unique")
    return rows[0]


def replay_trace(root: Mapping[str, object], trace: list[Mapping[str, object]]):
    state, dec = rr.initial_decoration(root)
    before_final = None
    edge_final = None
    for item in trace:
        label = str(item["label"])
        edge = next((edge for edge, collision in rr.iter_raw_macro_candidates(state)
                     if collision is None and edge is not None and edge.label == label), None)
        if edge is None:
            raise AssertionError(f"literal trace edge disappeared: {label}")
        before_final = (state, dec)
        dec = rr.advance_decoration(edge.run.state, edge.joint, dec)
        state = edge.state
        edge_final = edge
    if before_final is None or edge_final is None:
        raise AssertionError("empty R1 trace")
    return state, dec, before_final[0], before_final[1], edge_final


def frozen_r1_children(root: Mapping[str, object]) -> list[dict[str, object]]:
    historical = json.loads(V3_OUTPUT.read_text(encoding="utf-8"))
    events = historical["result"]["stats"]["R1_events"]
    rows = []
    for index, (event_id, event) in enumerate(sorted(events.items())):
        state, dec, pre_macro, before, edge = replay_trace(root, event["literal_macro_trace"])
        regenerated_id, regenerated = rr.r1_event_export(edge, before, dec,
                                                          tuple(event["literal_macro_trace"][:-1]))
        if regenerated_id != event_id or regenerated != event:
            raise AssertionError(f"R1 literal replay mismatch: {event_id}")
        if dec.r_count != 1 or dec.r1 is None:
            raise AssertionError("frozen R1 child has wrong R count")
        origin_id = f"short_ell0_r1_{index}"
        origin_hash = sha256_bytes(repr((origin_id, event_id, rr.decorated_key(state, dec))).encode("utf-8"))
        rows.append({
            "branch_id": origin_id, "branch_origin_hash": origin_hash,
            "r1_event_id": event_id, "literal_macro_trace": event["literal_macro_trace"],
            # Keep the full literal certificate locally.  In particular, the
            # branch artifact must not require a reader to chase an event ID
            # back into the historical v3 JSON merely to obtain the concrete
            # R1 source and target permutations.
            "literal_R1_event": regenerated,
            "exact_state": exact.state_to_json(state), "exact_state_hash": rr.state_hash(state),
            "decorated_key": repr(rr.decorated_key(state, dec)),
            "r1": asdict(dec.r1), "ell": edge.run.ell, "joint_label": edge.joint.move.label,
            "Phi": rr.phi(state), "M": state.P - 5 * state.O,
            "coordinate": {"P": state.P, "O": state.O, "F": state.F, "H": state.H, "Ndef": state.Ndef},
            "hub": {"id": dec.hub_id, "mask": rr.hub_mask(state, dec),
                    "popcount": rr.hub_mask(state, dec).bit_count()},
            "completer": None if dec.completer is None else asdict(dec.completer),
            "event_order_class": dec.event_order_class,
            "historical_checkpoint_ancestry": historical["result"]["checkpoint_lineage"],
        })
    if len(rows) != 4 or len({row["r1_event_id"] for row in rows}) != 4:
        raise AssertionError("expected four distinct frozen R1 children")
    return rows


def r1_origin_id(edge, before, after, trace: tuple[dict[str, object], ...], by_event: Mapping[str, Mapping[str, object]]) -> str:
    event_id, _event = rr.r1_event_export(edge, before, after, trace)
    try:
        return str(by_event[event_id]["branch_id"])
    except KeyError as exc:
        raise AssertionError(f"unfrozen R1 event in v3 transcript: {event_id}") from exc


def incidence_edges(state) -> list[dict[str, int]]:
    rows = []
    for orbit, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[orbit])[phase]
                rows.append({"orbit": orbit, "phase": phase, "hexagon": core.hexagon_id(port)})
    return rows


def component_ref(summary: Mapping[str, object], node: tuple[str, int]):
    component = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    if component is None:
        return None
    return {"id": component["id"], "class": component["class"],
            "e_orbits": component["e_orbits"], "hexagons": component["hexagons"]}


def last_trace_event(trace: tuple[dict[str, object], ...], *, orbits: set[int], hexagons: set[int]):
    for index in range(len(trace) - 1, -1, -1):
        event = trace[index]
        if int(event["target"][0]) in orbits or int(event["target_hexagon"]) in hexagons:
            return {"macro_index": index + 1, **event}
    return None


def class_b_record(state, dec, edge, trace: tuple[dict[str, object], ...], *, depth: int,
                   predecessor_table: dict[str, dict[str, object]]) -> dict[str, object]:
    pre = edge.run.state
    sq, sph = exact.ORBIT_PHASE[pre.p]
    tq, tph = exact.ORBIT_PHASE[edge.joint.target]
    summary = rr.component_summary(pre)
    source = component_ref(summary, ("q", sq))
    target = component_ref(summary, ("q", tq))
    r1target = component_ref(summary, ("q", dec.r1.target_orbit)) if dec.r1 else None
    if source is None or target is None or source["id"] == target["id"]:
        raise AssertionError("Class B requires present, distinct R2 endpoint components")
    pre_hash = rr.state_hash(pre)
    if pre_hash not in predecessor_table:
        source_orbits = set(source["e_orbits"])
        target_orbits = set(target["e_orbits"])
        source_hexagons = set(source["hexagons"])
        target_hexagons = set(target["hexagons"])
        predecessor_table[pre_hash] = {
            "exact_state_hash": pre_hash,
            "exact_state": exact.state_to_json(pre),
            "incidence_forest_edges": incidence_edges(pre),
            "component_forest": {"component_count": summary["component_count"],
                                 "components": summary["components"]},
            "last_event_changing_either_component": last_trace_event(
                trace, orbits=source_orbits | target_orbits,
                hexagons=source_hexagons | target_hexagons),
            "last_event_touching_r2_source_orbit": last_trace_event(
                trace, orbits={sq}, hexagons=set()),
            "last_event_touching_r1_target_orbit": last_trace_event(
                trace, orbits={dec.r1.target_orbit} if dec.r1 else set(), hexagons=set()),
        }
    hub = component_ref(summary, ("h", dec.hub_id))
    return {
        "candidate_id": sha256_bytes(repr((pre_hash, edge.label, dec.key())).encode("utf-8")),
        "depth": depth, "predecessor_ref": pre_hash,
        "candidate_macro_label": edge.label,
        "r1_target_orbit": None if dec.r1 is None else dec.r1.target_orbit,
        "r1_target_component": r1target,
        "r2_source_orbit": sq, "r2_source_phase": sph, "r2_source_component": source,
        "r2_target_orbit": tq, "r2_target_phase": tph, "r2_target_component": target,
        "completer": None if dec.completer is None else asdict(dec.completer),
        "hub_relation": {
            "hub_component": hub,
            "hub_equals_r1_target_component": hub is not None and r1target is not None and hub["id"] == r1target["id"],
            "hub_equals_r2_source_component": hub is not None and hub["id"] == source["id"],
        },
    }


def predicate_before_r2(joint_source_state, edge, dec, after) -> dict[str, object]:
    """Exact focused predecessor predicate; R2 is inspected but never enqueued."""
    if joint_source_state != edge.run.state:
        raise AssertionError("focused R2 predicate must receive literal joint source")
    recognition = rr.target_a_recognizer(joint_source_state, edge.joint, dec, after)
    summary = rr.component_summary(joint_source_state)
    sq, _ = exact.ORBIT_PHASE[joint_source_state.p]
    r1_component = None if dec.r1 is None else component_ref(summary, ("q", dec.r1.target_orbit))
    source_component = component_ref(summary, ("q", sq))
    conditions = {
        "r2_source_in_incidence_forest": source_component is not None,
        "r1_target_and_r2_source_same_component": (
            r1_component is not None and source_component is not None and r1_component["id"] == source_component["id"]),
        "exactly_two_R_after_edge": bool(recognition["conditions"]["exactly_two_R_events"]),
        "R2_joint": bool(recognition["conditions"]["immediately_after_R2"]),
        "F_equals_1": bool(recognition["conditions"]["F_def_equals_1"]),
        "H_equals_0": bool(recognition["conditions"]["H_equals_0"]),
        "hub_touch_at_most_2": bool(recognition["conditions"]["hub_touch_count_le_2"]),
        "R2_endpoint_same_component": bool(recognition["conditions"]["same_component"]),
    }
    return {"is_pre_target_a": all(conditions.values()), "conditions": conditions,
            "recognizer": recognition}


def raw_w3_score(state) -> int:
    """Relaxed metric: usable w=3 macro candidates, regardless of R/Z3 type."""
    score = 0
    for run in macro.rotation_runs(state):
        for move in macro.NONROT_H0:
            if move.weight != 3:
                continue
            if exact.extend(run.state, move) is not None:
                score += 1
    return score


def state_brief(state, dec, trace, depth: int) -> dict[str, object]:
    return {
        "depth": depth, "exact_state_hash": rr.state_hash(state),
        "decorated_key": repr(rr.decorated_key(state, dec)),
        "coordinate": {"P": state.P, "O": state.O, "F": state.F, "H": state.H, "Ndef": state.Ndef},
        "relaxed_metric": {
            "name": "usable_w3_macro_candidates_ignoring_R_vs_Z3_tag",
            "value": raw_w3_score(state),
        },
        "trace": list(trace),
    }


def empty_branch_stats(branches: list[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    return {str(branch["branch_id"]): {
        "expanded_nodes": 0, "generated_edges": 0, "unique_decorated_states": 0,
        "max_depth": 0, "frontier_size": 0, "R2_candidate_count": 0,
        "source_orbit_pass_count": 0, "same_component_pass_count": 0,
        "Target_A_hits": 0, "prune_histogram": {}, "raw_R2_collision_attempts": 0,
        "sampled_post_r1_states": [],
    } for branch in branches}


def write_branch_checkpoint(branch: Mapping[str, object], *, frontier, seen_texts, stats,
                            parent_checkpoint_sha: str, combined_limit: int) -> dict[str, object]:
    origin = str(branch["branch_id"])
    path = CHECKPOINT_ROOT / origin / "frontier.json"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite v4 branch checkpoint: {path}")
    config = {
        "schema": BRANCH_SCHEMA, "branch_origin_id": origin,
        "branch_origin_hash": branch["branch_origin_hash"],
        "root_id": "short_ell0", "combined_prefix_node_limit": combined_limit,
        "parent_combined_checkpoint_sha256": parent_checkpoint_sha,
        "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
    }
    payload = {
        "schema": BRANCH_SCHEMA, "config": config, "branch_origin": branch,
        "frontier": [{"depth": depth, "state": exact.state_to_json(state),
                      "decoration": dec.to_json(), "trace": list(trace),
                      "branch_origin_id": origin}
                     for depth, state, dec, trace in frontier],
        "seen_keys": sorted(seen_texts), "stats": stats,
        "complete_frontier_snapshot": True,
        "classification": "PREFIX_SNAPSHOT_INCOMPLETE",
    }
    atomic_json(path, payload)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
            "frontier_size": len(frontier), "seen_size": len(seen_texts),
            "schema": BRANCH_SCHEMA}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-limit", type=int, default=100_250)
    parser.add_argument("--no-checkpoints", action="store_true")
    args = parser.parse_args()
    if args.node_limit <= 0:
        raise ValueError("this audit requires a positive bounded replay limit")
    if not V3_OUTPUT.exists() or not V3_CHECKPOINT.exists() or not ROUND43_GEOMETRY.exists():
        raise FileNotFoundError("Round-42/43 artifacts are required")
    root = record()
    branches = frozen_r1_children(root)
    by_event = {str(row["r1_event_id"]): row for row in branches}
    by_id = {str(row["branch_id"]): row for row in branches}
    historical_checkpoint = json.loads(V3_CHECKPOINT.read_text(encoding="utf-8"))
    historical_payload = json.loads(V3_OUTPUT.read_text(encoding="utf-8"))
    expected_geo = json.loads(ROUND43_GEOMETRY.read_text(encoding="utf-8"))["replay_equivalence"]

    state, dec = rr.initial_decoration(root)
    frontier: list[tuple[int, object, object, tuple[dict[str, object], ...], Optional[str]]] = [(0, state, dec, tuple(), None)]
    seen: dict[tuple[object, ...], Optional[str]] = {rr.decorated_key(state, dec): None}
    branch_seen: dict[str, set[str]] = {name: set() for name in by_id}
    branch_frontier: dict[str, list[tuple[int, object, object, tuple[dict[str, object], ...]]]] = {
        name: [] for name in by_id
    }
    branch_stats = empty_branch_stats(branches)
    branch_expansion_hash = {name: hashlib.sha256() for name in by_id}
    combined_hash = hashlib.sha256()
    class_a: Counter[str] = Counter()
    class_b: list[dict[str, object]] = []
    predecessor_table: dict[str, dict[str, object]] = {}
    pre_target: list[dict[str, object]] = []
    expanded = 0
    pre_r_expanded = 0
    while frontier and expanded < args.node_limit:
        depth, state, dec, trace, origin = frontier.pop()
        state_digest = rr.state_hash(state)
        combined_hash.update(f"{expanded}:{origin or 'PRE_R'}:{state_digest}\n".encode("ascii"))
        expanded += 1
        if origin is None:
            if dec.r_count != 0:
                raise AssertionError("post-R1 state lacks branch origin")
            pre_r_expanded += 1
        else:
            if dec.r_count != 1:
                raise AssertionError("branch-origin state is not post-R1")
            if origin not in by_id:
                raise AssertionError("unknown branch origin")
            stats = branch_stats[origin]
            stats["expanded_nodes"] = int(stats["expanded_nodes"]) + 1
            stats["max_depth"] = max(int(stats["max_depth"]), depth)
            branch_expansion_hash[origin].update(f"{state_digest}\n".encode("ascii"))
            if len(stats["sampled_post_r1_states"]) < 16:
                stats["sampled_post_r1_states"].append(state_brief(state, dec, trace, depth))

        child_entries = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            if collision is not None:
                if origin is not None:
                    stats = branch_stats[origin]
                    stats["generated_edges"] = int(stats["generated_edges"]) + 1
                    hist = Counter(stats["prune_histogram"]); hist[collision] += 1
                    stats["prune_histogram"] = dict(sorted(hist.items()))
                continue
            assert edge is not None
            edge_kind = rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit)
            if origin is not None:
                stats = branch_stats[origin]
                stats["generated_edges"] = int(stats["generated_edges"]) + 1
            verdict, child_dec, recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
            step = rr.edge_json(edge)
            if origin is not None and edge_kind == "R" and dec.r_count == 1:
                stats = branch_stats[origin]
                stats["R2_candidate_count"] = int(stats["R2_candidate_count"]) + 1
                assert recognition is not None
                endpoint = recognition["r2_endpoint_presence"]
                if endpoint["source_orbit_present_in_pre_r2_forest"]:
                    stats["source_orbit_pass_count"] = int(stats["source_orbit_pass_count"]) + 1
                    if recognition["same_component"]:
                        stats["same_component_pass_count"] = int(stats["same_component_pass_count"]) + 1
                    else:
                        class_b.append(class_b_record(state, dec, edge, trace, depth=depth + 1,
                                                      predecessor_table=predecessor_table))
                else:
                    class_a[str(recognition["geometry_failure_reason"])] += 1
                focused = predicate_before_r2(edge.run.state, edge, dec, child_dec)
                if focused["is_pre_target_a"]:
                    pre_target.append({"branch_id": origin, "depth": depth + 1,
                                       "pre_state_hash": rr.state_hash(edge.run.state),
                                       "candidate_macro_label": edge.label,
                                       "predicate": focused})
                if verdict == "FOUND_TARGET_A":
                    stats["Target_A_hits"] = int(stats["Target_A_hits"]) + 1
            if verdict == "child":
                assert child_dec is not None
                child_origin = origin
                if dec.r_count == 0 and child_dec.r_count == 1:
                    child_origin = r1_origin_id(edge, dec, child_dec, trace, by_event)
                elif child_dec.r_count == 1 and child_origin is None:
                    raise AssertionError("post-R1 child lacks branch origin")
                key = rr.decorated_key(edge.state, child_dec)
                previous_origin = seen.get(key, "UNSEEN")
                if previous_origin != "UNSEEN":
                    if previous_origin != child_origin:
                        raise AssertionError("decorated state has multiple R1 origins")
                    if origin is not None:
                        hist = Counter(branch_stats[origin]["prune_histogram"])
                        hist["decorated_memo_duplicate"] += 1
                        branch_stats[origin]["prune_histogram"] = dict(sorted(hist.items()))
                    continue
                seen[key] = child_origin
                if child_origin is not None:
                    branch_seen[child_origin].add(repr(key))
                child_entries.append((depth + 1, edge.state, child_dec, trace + (step,), child_origin))
            else:
                if origin is not None:
                    hist = Counter(branch_stats[origin]["prune_histogram"])
                    hist[verdict] += 1
                    branch_stats[origin]["prune_histogram"] = dict(sorted(hist.items()))
        child_entries.sort(key=lambda item: item[3][-1]["label"], reverse=True)
        frontier.extend(child_entries)

    # Every still-live state is part of exactly one branch or of the pre-R
    # prefix.  The branch checkpoints include only the r_count=1 portions.
    for depth, state, dec, trace, origin in frontier:
        if dec.r_count == 1:
            if origin is None:
                raise AssertionError("frontier post-R1 state lacks origin")
            branch_frontier[origin].append((depth, state, dec, trace))
        elif origin is not None:
            raise AssertionError("pre-R frontier state retained a branch origin")
    for origin, keys in branch_seen.items():
        branch_stats[origin]["unique_decorated_states"] = len(keys)
        branch_stats[origin]["frontier_size"] = len(branch_frontier[origin])
        branch_stats[origin]["expansion_trace_hash"] = branch_expansion_hash[origin].hexdigest()
        if int(branch_stats[origin]["R2_candidate_count"]) == 0:
            # This is intentionally a bounded observation: initial child and
            # frontier states are ranked by a clearly labelled relaxed score.
            candidates = []
            initial = next(row for row in branches if row["branch_id"] == origin)
            initial_state = exact.state_from_json(initial["exact_state"])
            initial_dec = rr.Decoration.from_json({
                "root_id": "short_ell0", "root_ell": 0, "o_star": 120, "hub_id": rr.HUB,
                "macro_index": initial["r1"]["macro_index"], "r_events": [initial["r1"]],
                "hub_touch_count": initial["hub"]["popcount"], "completer": initial["completer"],
            })
            candidates.append(state_brief(initial_state, initial_dec, tuple(initial["literal_macro_trace"]),
                                          len(initial["literal_macro_trace"])))
            candidates.extend(state_brief(s, d, t, dep) for dep, s, d, t in branch_frontier[origin])
            candidates.sort(key=lambda row: (-int(row["relaxed_metric"]["value"]), -int(row["depth"]),
                                               str(row["exact_state_hash"])))
            branch_stats[origin]["nearest_to_R2_relaxed"] = candidates[:10]
            branch_stats[origin]["zero_candidate_interpretation"] = (
                "current bounded prefix has no legal R2 candidate; this is INSUFFICIENT_DATA, not impossibility")

    if expanded != args.node_limit or not frontier:
        raise AssertionError("this Round-44 replay is expected to stop only at its positive cap")
    # This must match the fixed Round-42 prefix exactly; it establishes that
    # origin capture is additive rather than a different traversal.
    combined_seen_post_r1 = {repr(key) for key, origin in seen.items() if origin is not None}
    combined_historical_post_r1 = {
        text for text in historical_checkpoint["seen_keys"]
        if len(rr.decode_key(text)[1][4]) == 1
    }
    # A small smoke replay is useful for catching schema/replay regressions,
    # but it is not a transcript comparison.  The actual Round-44 run uses
    # the frozen 100,250-node cap and must reproduce every historical datum.
    full_prefix = args.node_limit == int(expected_geo["expanded"])
    if full_prefix:
        if combined_seen_post_r1 != combined_historical_post_r1:
            raise AssertionError("branch union does not reproduce combined post-R1 memo set")
        if sum(int(s["R2_candidate_count"]) for s in branch_stats.values()) != 49_440:
            raise AssertionError("branch R2 totals do not match Round-42")
    productive = [name for name, stats in branch_stats.items() if int(stats["R2_candidate_count"]) > 0]
    if full_prefix and len(productive) != 1:
        raise AssertionError(f"expected one productive R1 branch, got {productive}")
    productive_id = productive[0] if len(productive) == 1 else None

    checkpoint_summaries = {}
    if not args.no_checkpoints:
        for branch in branches:
            origin = str(branch["branch_id"])
            checkpoint_summaries[origin] = write_branch_checkpoint(
                branch, frontier=branch_frontier[origin], seen_texts=branch_seen[origin],
                stats=branch_stats[origin], parent_checkpoint_sha=sha256_file(V3_CHECKPOINT),
                combined_limit=args.node_limit)

    branches_payload = {
        "schema": "rr-short-ell0-r1-branch-split-v4-v1",
        "scope": "exact bounded replay of the historical 100250-expansion Target-A-safe v3 prefix",
        "classification": "INCOMPLETE", "combined_v3_checkpoint_read_only": {
            "path": str(V3_CHECKPOINT.relative_to(ROOT)), "sha256": sha256_file(V3_CHECKPOINT)},
        "branch_schema": BRANCH_SCHEMA, "frozen_r1_children": branches,
        "combined_transcript": {
            "expanded": expanded, "pre_R_expanded": pre_r_expanded,
            "combined_origin_sequence_hash": combined_hash.hexdigest(),
            "post_r1_seen_count": len(combined_seen_post_r1),
            "post_r1_seen_hash": sha256_bytes("\n".join(sorted(combined_seen_post_r1)).encode("utf-8")),
            "historical_post_r1_seen_hash": sha256_bytes("\n".join(sorted(combined_historical_post_r1)).encode("utf-8")),
            "union_matches_historical_post_r1_seen": combined_seen_post_r1 == combined_historical_post_r1,
            "frontier_size": len(frontier),
        },
        "branch_stats": branch_stats, "productive_branch_id": productive_id,
        "branch_checkpoints": checkpoint_summaries,
    }
    productive_payload = {
        "schema": "rr-short-ell0-productive-r1-candidates-v1",
        "scope": "all legal R2 candidates in the exact bounded v3 transcript",
        "productive_branch_id": productive_id,
        "R2_candidate_count": (0 if productive_id is None
                                else branch_stats[productive_id]["R2_candidate_count"]),
        "class_A": {"definition": "R2 source orbit absent from pre-R2 incidence forest",
                    "counts": dict(sorted(class_a.items())), "count": sum(class_a.values())},
        "class_B": {"definition": "R2 source present; R2 endpoint components differ",
                    "count": len(class_b), "candidates": class_b,
                    "predecessor_states": predecessor_table},
    }
    pre_status = "FOUND_PRE_TARGET_A" if pre_target else "INCOMPLETE"
    pretarget_payload = {
        "schema": "rr-short-ell0-focused-pre-target-a-v1",
        "classification": pre_status,
        "scope": "focused predicate scan over the exact bounded combined v3 transcript; positive cap forbids exhaustion",
        "predicate": [
            "R2 source orbit is in the pre-R2 incidence forest",
            "R1 target and R2 source are in the same pre-R2 component",
            "R2 source and target are in the same pre-R2 component",
            "exactly-two-R, R2-joint, F=1, H=0, hub-touch<=2 after the inspected R2 edge",
        ],
        "candidates_examined": 49_440,
        "found_pre_target_a": pre_target,
        "frontier_nonempty": True,
        "reason_not_exhausted": "positive 100250 expansion cap",
    }
    atomic_json(BRANCH_OUTPUT, branches_payload)
    atomic_json(PRODUCTIVE_OUTPUT, productive_payload)
    atomic_json(PRETARGET_OUTPUT, pretarget_payload)
    print(json.dumps({"classification": pre_status, "productive_branch": productive_id,
                      "r2": sum(int(s["R2_candidate_count"]) for s in branch_stats.values()),
                      "class_a": sum(class_a.values()), "class_b": len(class_b),
                      "branches": {name: stats["R2_candidate_count"] for name, stats in branch_stats.items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
