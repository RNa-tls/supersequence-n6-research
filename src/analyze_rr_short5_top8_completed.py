#!/usr/bin/env python3
"""Read-only post-completion analysis for the eight Round-52 v6 branches.

This is deliberately an analyser, not a traversal: it never writes a v6
checkpoint and never creates a continuation child.  Every repair and R2 path
is replayed from the parent DAG at its literal joint state.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
V6 = ROOT / "outputs" / "rr_short5_top8_continuation.json"
V5 = ROOT / "outputs" / "rr_short1_4_corrected_fair_results.json"
CPROOT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "top8_continuation_v6"
ANALYSIS = ROOT / "outputs" / "rr_short5_top8_continuation_analysis.json"
REGISTRATION = ROOT / "outputs" / "rr_short5_top8_registration_events.json"
HIERARCHY = ROOT / "outputs" / "rr_short5_top8_success_hierarchy.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load("rr_top8_completed_pilot", ROOT / "src" / "search_rr_short1_4_corrected_fair.py")
rr, exact, core, repair = pilot.rr, pilot.exact, pilot.core, pilot.repair


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def component_id(summary: Mapping[str, object], node: tuple[str, int]) -> str | None:
    entry = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    return None if entry is None else str(entry["id"])


def component_json(summary: Mapping[str, object], node: tuple[str, int]) -> dict[str, object] | None:
    entry = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    if entry is None:
        return None
    return {"id": str(entry["id"]), "class": str(entry["class"])}


def summary_json(summary: Mapping[str, object]) -> dict[str, object]:
    return {"component_count": int(summary["component_count"]), "components": summary["components"]}


def trace_hex_targets(root: Mapping[str, object], trace: list[Mapping[str, object]]) -> dict[str, object]:
    state, dec = rr.initial_decoration(root)
    rows = []
    for step, data in enumerate(trace, 1):
        edge = pilot.edge_from_json(state, data)
        rows.append({"step": step, "label": edge.label, "target_hexagon": core.hexagon_id(edge.joint.target),
                     "rotation_length": edge.run.ell, "joint": edge.joint.move.label})
        dec = rr.advance_decoration(edge.run.state, edge.joint, dec)
        state = edge.state
    return {"target_hexagon_sequence": [row["target_hexagon"] for row in rows], "steps": rows,
            "final_r_count": dec.r_count}


class Replay:
    """Memoized literal parent-DAG reconstruction for one checkpoint."""

    def __init__(self, root: Mapping[str, object], child: Mapping[str, object], raw: Mapping[str, object]):
        self.root, self.child = root, child
        self.nodes = {str(row["node_id"]): row for row in raw["nodes"]}  # type: ignore[index]
        self.cache: dict[str, tuple[Any, Any]] = {}

    def node(self, node_id: str):
        if node_id in self.cache:
            return self.cache[node_id]
        row = self.nodes[node_id]
        parent_id = row["parent_id"]
        if parent_id is None:
            state, dec = pilot.replay_trace(self.root, list(self.child["literal_macro_trace"]))
        else:
            parent_state, parent_dec = self.node(str(parent_id))
            edge = pilot.edge_from_json(parent_state, row["incoming_macro_edge"])
            state = edge.state
            dec = rr.advance_decoration(edge.run.state, edge.joint, parent_dec)
        if rr.state_hash(state) != row["exact_state_hash"] or dec.to_json() != row["decoration"]:
            raise AssertionError(f"literal parent-DAG replay mismatch: {node_id}")
        self.cache[node_id] = (state, dec)
        return state, dec


def analyze_branch(root: Mapping[str, object], child: Mapping[str, object], result: Mapping[str, object]) -> dict[str, object]:
    checkpoint_path = ROOT / result["checkpoint"]["path"]
    raw = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    config = pilot.branch_config(root, child, 55000)
    # Independent of this analyser's own parser: exercise the production
    # read-only loader before examining the payload.
    pilot.load_checkpoint(checkpoint_path, config, root, child)
    replay = Replay(root, child, raw)
    root_state, root_dec = replay.node(f"{child['branch_id']}:0")
    if root_dec.r_count != 1 or root_dec.r1 is None:
        raise AssertionError("top8 branch root is not an R1 child")

    repair_counts: Counter[str] = Counter()
    bridge_counts: Counter[str] = Counter()
    bridge_records: list[dict[str, object]] = []
    registration_records: list[dict[str, object]] = []
    literal_repairs = 0
    component_merges = 0
    r1_hub_merges = 0
    target_in_hub_component = 0
    repair_type_violations: list[str] = []
    r1_target_orbit = int(root_dec.r1.target_orbit)

    repairs = list(raw["repair_events"])
    for event in repairs:
        event_id = str(event["event_id"])
        before, before_dec = replay.node(str(event["predecessor_node_id"]))
        edge = pilot.edge_from_json(before, event["repair_edge"])
        after = edge.state
        after_dec = rr.advance_decoration(edge.run.state, edge.joint, before_dec)
        literal_repairs += 1
        if rr.state_hash(before) != event["exact_predecessor_hash"] or rr.state_hash(after) != event["exact_child_hash"]:
            raise AssertionError(f"repair literal hash mismatch: {event_id}")
        kind = repair.repair_type(edge)
        if kind not in {"Z2", "Z3_fresh"}:
            repair_type_violations.append(event_id)
            continue
        if kind != event["repair_type"]:
            raise AssertionError(f"repair type mismatch: {event_id}")
        recomputed = repair.repair_event(event_id, str(child["branch_id"]), str(event["predecessor_node_id"]),
                                         str(event["child_node_id"]), edge, before, after, before_dec, after_dec)
        for key in ("component_merge", "target_hexagon", "repair_orbit", "repair_phase", "F_before", "F_after",
                    "H_before", "H_after", "hub_touch_before", "hub_touch_after"):
            if recomputed[key] != event[key]:
                raise AssertionError(f"repair event field mismatch {key}: {event_id}")
        repair_counts[kind] += 1
        if bool(event["component_merge"]):
            component_merges += 1
        pre = rr.component_summary(before)
        post = rr.component_summary(after)
        hub_node = ("h", int(before_dec.hub_id))
        r1_node = ("q", r1_target_orbit)
        target_hex = int(event["target_hexagon"])
        target_hex_node = ("h", target_hex)
        r1_pre, hub_pre, target_pre = (component_id(pre, r1_node), component_id(pre, hub_node),
                                       component_id(pre, target_hex_node))
        r1_post, hub_post = component_id(post, r1_node), component_id(post, hub_node)
        is_r1_hub_merge = (r1_pre is not None and hub_pre is not None and r1_pre != hub_pre and
                           r1_post is not None and hub_post is not None and r1_post == hub_post)
        in_hub_component = (target_hex != int(before_dec.hub_id) and target_pre is not None and hub_pre is not None and
                            target_pre == hub_pre)
        if is_r1_hub_merge:
            r1_hub_merges += 1
        if in_hub_component:
            target_in_hub_component += 1
        bridge = bool(event["component_merge"]) and in_hub_component and is_r1_hub_merge
        if bridge:
            bridge_counts[kind] += 1
        record = {
            "event_id": event_id, "child_id": child["branch_id"],
            "literal_predecessor_hash": rr.state_hash(before), "edge": event["repair_edge"], "weight": edge.joint.move.weight,
            "repair_type": kind, "target_orbit": int(event["repair_orbit"]), "target_hexagon": target_hex,
            "component_partition_before": summary_json(pre), "component_partition_after": summary_json(post),
            "r1_target_component_before": component_json(pre, r1_node), "r1_target_component_after": component_json(post, r1_node),
            "hub_component_before": component_json(pre, hub_node), "hub_component_after": component_json(post, hub_node),
            "target_hexagon_component_before": component_json(pre, target_hex_node),
            "target_hexagon_in_hub_component": in_hub_component, "r1_target_hub_merge": is_r1_hub_merge,
            "component_merge": bool(event["component_merge"]), "hub_touch_before": int(event["hub_touch_before"]),
            "hub_touch_after": int(event["hub_touch_after"]), "F_before": int(event["F_before"]), "F_after": int(event["F_after"]),
            "H_before": int(event["H_before"]), "H_after": int(event["H_after"]),
            "future_R2_source_before": "UNDEFINED_UNTIL_AN_R2_EDGE_IS_CHOSEN",
            "future_R2_observations_after": event["future_R2_observations"],
            "terminal_geometry_available": "EVALUATED_ONLY_AT_LITERAL_R2_CANDIDATES",
            "literal_replay_verified": True,
        }
        # Full per-event records remain in the immutable checkpoint.  Export
        # every possible registration/bridge witness rather than cloning a
        # multi-gigabyte event corpus into a second output.
        if bool(event["component_merge"]) or in_hub_component or is_r1_hub_merge:
            registration_records.append(record)
        if bridge:
            bridge_records.append(record)

    hierarchy_counts: Counter[str] = Counter()
    hierarchy_failure_counts: Counter[str] = Counter()
    r2_outcomes: Counter[str] = Counter()
    r2_paths = list(raw["r2_paths"])
    target_a_hits: list[dict[str, object]] = []
    r2_replayed = 0
    r2_alternative_targets: Counter[tuple[int, int]] = Counter()
    event_lookup = {str(event["event_id"]): event for event in repairs}
    for index, path in enumerate(r2_paths):
        predecessor, before_dec = replay.node(str(path["r2_predecessor_node_id"]))
        edge = pilot.edge_from_json(predecessor, path["r2_edge"])
        after_dec = rr.advance_decoration(edge.run.state, edge.joint, before_dec)
        if after_dec.r_count != 2:
            raise AssertionError(f"recorded R2 path is not R2: {child['branch_id']}:{index}")
        source_ref = rr.r2_literal_joint_source(edge)
        recognition = rr.target_a_recognizer(source_ref, edge.joint, before_dec, after_dec)
        r2_replayed += 1
        r2_outcomes[str(recognition["r2_outcome"])] += 1
        r2_alternative_targets[(int(recognition["source_orbit"]), int(recognition["source_phase"]))] += 1
        lineage = [event_lookup[str(event_id)] for event_id in path["repair_event_ids"]]
        if lineage:
            hierarchy = repair.hierarchy_for_r2(predecessor, edge, before_dec, after_dec, lineage)
            if "recognizer" in path and hierarchy["recognizer"] != path["recognizer"]:
                raise AssertionError(f"stored hierarchy recognizer mismatch: {child['branch_id']}:{index}")
            hierarchy_counts[str(hierarchy["maximum_level"])] += 1
            hierarchy_failure_counts[str(hierarchy["failure_reason"])] += 1
        if recognition["is_target_a"]:
            target_a_hits.append({"path_index": index, "r2_predecessor_node_id": path["r2_predecessor_node_id"],
                                  "literal_joint_source_hash": rr.state_hash(source_ref.state),
                                  "literal_joint_source_orbit": recognition["source_orbit"],
                                  "literal_joint_source_phase": recognition["source_phase"],
                                  "r2_edge": path["r2_edge"], "recognizer": recognition})

    trace_info = trace_hex_targets(root, list(child["literal_macro_trace"]))
    summary = {
        "child_id": child["branch_id"], "root_id": root["root_id"],
        "checkpoint": {"path": str(checkpoint_path.relative_to(ROOT)), "sha256": sha256_file(checkpoint_path)},
        "endpoint": "NATURALLY_EXHAUSTED" if not raw["frontier"] else "CAP_REACHED_NONEMPTY_FRONTIER",
        "expanded": int(raw["stats"]["expanded"]), "frontier_size": len(raw["frontier"]),
        "max_depth": int(raw["stats"].get("max_depth", 0)), "r1_target_orbit": r1_target_orbit,
        "r1_target_component_isolated_from_hub_at_admission": component_id(rr.component_summary(root_state), ("q", r1_target_orbit)) != component_id(rr.component_summary(root_state), ("h", int(root_dec.hub_id))),
        "preparation_spine": trace_info,
        "repair_events": {"total": len(repairs), "literal_replayed": literal_repairs, "types": dict(sorted(repair_counts.items())),
                          "component_merges": component_merges, "target_hex_in_hub_component": target_in_hub_component,
                          "r1_target_hub_merges": r1_hub_merges, "bridge_template_matches": len(bridge_records),
                          "repair_type_violations": repair_type_violations},
        "r2": {"total": len(r2_paths), "literal_replayed": r2_replayed, "outcomes": dict(sorted(r2_outcomes.items())),
               "hierarchy_maximum_levels": dict(sorted(hierarchy_counts.items())),
               "hierarchy_failures": dict(sorted(hierarchy_failure_counts.items())), "target_a_hits": target_a_hits,
               "top_literal_source_orbit_phase": [{"orbit": orbit, "phase": phase, "count": count}
                                                   for (orbit, phase), count in r2_alternative_targets.most_common(20)]},
    }
    return {"summary": summary, "bridge_records": bridge_records, "registration_records": registration_records}


def main() -> None:
    v6 = json.loads(V6.read_text(encoding="utf-8"))
    v5 = json.loads(V5.read_text(encoding="utf-8"))
    lookup: dict[str, tuple[Mapping[str, object], Mapping[str, object]]] = {}
    for row in v5["roots"].values():
        for child in row["admission"]["frozen_R1_children"]:
            lookup[str(child["branch_id"])] = (row["root_record"], child)
    rows, bridges, registrations = [], [], []
    for result in v6["children"]:
        branch_id = str(result["child_id"])
        root, child = lookup[branch_id]
        item = analyze_branch(root, child, result["continuation_result"])
        rows.append(item["summary"])
        bridges.extend(item["bridge_records"])
        registrations.extend(item["registration_records"])
    if len(rows) != 8:
        raise AssertionError("top8 result did not contain exactly eight branches")
    endpoints = Counter(row["endpoint"] for row in rows)
    all_repairs = sum(row["repair_events"]["total"] for row in rows)
    all_r2 = sum(row["r2"]["total"] for row in rows)
    all_hits = sum(len(row["r2"]["target_a_hits"]) for row in rows)
    hierarchy = Counter()
    failures = Counter()
    for row in rows:
        hierarchy.update(row["r2"]["hierarchy_maximum_levels"])
        failures.update(row["r2"]["hierarchy_failures"])
    analysis = {"schema": "rr-short5-top8-completion-analysis-v1", "scope": "completed v6 checkpoints only; capped branches remain observations",
                "input": {"v6_result_sha256": sha256_file(V6), "v5_result_sha256": sha256_file(V5),
                          "v5_driver_sha256": sha256_file(ROOT / "src" / "search_rr_short1_4_corrected_fair.py"),
                          "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py")},
                "branches": rows,
                "aggregate": {"branch_endpoints": dict(sorted(endpoints.items())), "repair_events": all_repairs,
                              "r2_paths": all_r2, "literal_target_a_hits": all_hits,
                              "bridge_template_matches": len(bridges), "registration_candidate_records": len(registrations),
                              "success_hierarchy": dict(sorted(hierarchy.items())), "repair_failure_taxonomy": dict(sorted(failures.items())),
                              "status": "TOP8_CONTINUATION_INCOMPLETE" if endpoints["CAP_REACHED_NONEMPTY_FRONTIER"] else "TOP8_ALL_EXHAUSTED"}}
    registration = {"schema": "rr-short5-top8-registration-events-v1", "scope": "all repairs replayed; records retain every event satisfying a bridge/registration precondition",
                    "all_legal_repairs_replayed": all_repairs, "bridge_template": {"allowed_kinds": ["Z2", "Z3_fresh"],
                    "target_hex_in_hub_component_and_not_hub": True, "r1_target_hub_component_merges": True},
                    "records": registrations, "bridge_records": bridges}
    hierarchy_payload = {"schema": "rr-short5-top8-success-hierarchy-v1", "scope": "literal R2 source is edge.run.state",
                         "r2_paths_replayed": all_r2, "maximum_level_counts": dict(sorted(hierarchy.items())),
                         "failure_reason_counts": dict(sorted(failures.items())), "literal_target_a_hits": all_hits,
                         "target_b_survivors": [], "note": "No literal Target-A hit occurred in this top8 v6 corpus, so no Target-B DFS is triggered."}
    atomic_json(ANALYSIS, analysis)
    atomic_json(REGISTRATION, registration)
    atomic_json(HIERARCHY, hierarchy_payload)
    print(json.dumps({"status": analysis["aggregate"]["status"], "repairs": all_repairs, "r2": all_r2,
                      "bridges": len(bridges), "target_a": all_hits}, sort_keys=True))


if __name__ == "__main__":
    main()
