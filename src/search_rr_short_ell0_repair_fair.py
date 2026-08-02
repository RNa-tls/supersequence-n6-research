#!/usr/bin/env python3
"""Round 46: fair post-R1 repair search for ``short_ell0``.

This is intentionally separate from the historical combined LIFO run and
from the first fair transcript.  Its repair context is provenance, not a
fixed old R2-source label: a later R2 candidate is judged at its actual
post-repair source orbit.  The four literal R1 children each receive the
same positive cap, hence every nonempty branch is explicitly INCOMPLETE.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
# Historical v1 artifacts used macro entry as the R2 source.  They are kept
# immutable for the correction audit, while every v2 result is written under
# a distinct name.
RESULT = ROOT / "outputs" / "rr_short_ell0_corrected_fair_repair_results.json"
HIERARCHY = ROOT / "outputs" / "rr_short_ell0_corrected_repair_hierarchy.json"
WITNESSES = ROOT / "outputs" / "rr_short_ell0_corrected_repair_witnesses.json"
SCHEMA = "rr-short-ell0-fair-repair-v2-literal-r2-source"
CHECKPOINT_SCHEMA = "rr-short-ell0-fair-repair-checkpoint-v2-literal-r2-source"
LEGACY_SCHEMA = "rr-short-ell0-fair-repair-v1-post-repair-source"
REPAIR_TYPES = ("Z2", "Z3_fresh")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


split = load("rr_repair_fair_split", ROOT / "src" / "search_rr_short_ell0_r1_split.py")
rr, exact, core = split.rr, split.exact, split.rr.core


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def component(summary: Mapping[str, object], node: tuple[str, int]):
    value = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    if value is None:
        return None
    return {"id": value["id"], "class": value["class"]}


def component_equal(left, right) -> bool:
    return left is not None and right is not None and left["id"] == right["id"]


def repair_type(edge) -> str | None:
    """The Claude template's exact two-kind repair alphabet.

    An attempted weight-three re-entry is definitionally ``R`` because its
    target orbit is already open; it therefore cannot enter this function as
    a Z3 repair.  The assertion makes that exclusion executable.
    """
    kind = rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit)
    if kind == "Z2":
        return "Z2"
    if kind == "Z3":
        if not edge.joint.new_orbit:
            raise AssertionError("Z3 re-entry is definitionally an R, not a repair")
        return "Z3_fresh"
    return None


def node_record(node_id: str, parent_id: str | None, edge_json, state, dec, repair_ids):
    return {
        "node_id": node_id, "parent_id": parent_id, "incoming_macro_edge": edge_json,
        "exact_state_hash": rr.state_hash(state), "decoration": dec.to_json(),
        "repair_ids": list(repair_ids),
    }


def repair_event(event_id: str, branch_id: str, parent_id: str, child_id: str, edge, before, after, dec_before, dec_after):
    old_sq, old_sph = exact.ORBIT_PHASE[before.p]
    tq, tph = exact.ORBIT_PHASE[edge.joint.target]
    pre, post = rr.component_summary(before), rr.component_summary(after)
    # The incidence edge added by this joint belongs to the *target* E-orbit
    # (the new pass start), not to the terminal word's old orbit.  This is
    # precisely the distinction needed for fresh Z3: ``tq`` is absent before
    # the edge, while the old source orbit need not be.
    source_pre, target_pre = component(pre, ("q", tq)), component(pre, ("h", core.hexagon_id(edge.joint.target)))
    source_post, target_post = component(post, ("q", tq)), component(post, ("h", core.hexagon_id(edge.joint.target)))
    merged = (source_pre is not None and target_pre is not None and
              not component_equal(source_pre, target_pre) and component_equal(source_post, target_post))
    kind = repair_type(edge)
    if kind is None:
        raise AssertionError("non-repair event passed to repair_event")
    if kind == "Z3_fresh" and source_pre is not None:
        raise AssertionError("fresh Z3 had a registered source orbit")
    return {
        "event_id": event_id, "branch_id": branch_id, "predecessor_node_id": parent_id,
        "child_node_id": child_id, "exact_predecessor_hash": rr.state_hash(before),
        "exact_child_hash": rr.state_hash(after), "repair_edge": rr.edge_json(edge), "repair_type": kind,
        "repair_timing": {"strictly_after_R1": dec_before.r_count == 1,
                          "macro_index_before": dec_before.macro_index,
                          "macro_index_after": dec_after.macro_index},
        "old_source_orbit": old_sq, "old_source_phase": old_sph,
        "repair_orbit": tq, "repair_phase": tph,
        "target_hexagon": core.hexagon_id(edge.joint.target),
        "target_hexagon_is_hub": core.hexagon_id(edge.joint.target) == dec_before.hub_id,
        "pre_component_count": pre["component_count"], "post_component_count": post["component_count"],
        "source_component_before": source_pre, "target_component_before": target_pre,
        "source_component_after": source_post, "target_component_after": target_post,
        "component_merge": merged,
        "incidence_membership_before": {"repair_source": source_pre is not None,
                                          "target_hexagon": target_pre is not None},
        "incidence_membership_after": {"repair_source": source_post is not None,
                                         "target_hexagon": target_post is not None},
        "hub_touch_before": dec_before.hub_touch_count, "hub_touch_after": dec_after.hub_touch_count,
        "F_before": before.F, "F_after": after.F, "H_before": before.H, "H_after": after.H,
        "decoration_before": dec_before.to_json(), "decoration_after": dec_after.to_json(),
        "completer_before": None if dec_before.completer is None else dec_before.completer.__dict__,
        "completer_after": None if dec_after.completer is None else dec_after.completer.__dict__,
        "future_R2_observations": [],
    }


def hierarchy_for_r2(macro_entry_state, edge, dec_before, dec_after, repair_events):
    """Classify an R2 edge at its literal source, not macro entry.

    ``edge.run.state`` is the state obtained after the edge's rotation run.
    Its word is the actual source of the joint and therefore controls both
    incidence membership and same-component.  Macro entry remains in the
    serialized record strictly as provenance.
    """
    joint_source_state = edge.run.state
    recognition = rr.target_a_recognizer(joint_source_state, edge.joint, dec_before, dec_after)
    source_orbit, source_phase = exact.ORBIT_PHASE[joint_source_state.p]
    target_orbit, target_phase = exact.ORBIT_PHASE[edge.joint.target]
    summary = rr.component_summary(joint_source_state)
    r1_component = component(summary, ("q", dec_before.r1.target_orbit)) if dec_before.r1 else None
    source_component = component(summary, ("q", source_orbit))
    endpoints = recognition["r2_endpoint_presence"]
    r0 = bool(repair_events)
    r1 = any(bool(event["component_merge"]) for event in repair_events)
    r2 = bool(endpoints["source_orbit_present_in_pre_r2_forest"])
    r3 = r2 and bool(recognition["same_component"])
    terminal_geometry = (joint_source_state.F <= 1 and joint_source_state.H == 0 and dec_before.hub_touch_count <= 2 and
                         bool(endpoints["target_orbit_present_in_pre_r2_forest"]))
    r4 = r3 and terminal_geometry
    r5 = r4 and bool(recognition["is_target_a"])
    r6 = bool(recognition["is_target_a"])
    levels = [r0, r1, r2, r3, r4, r5, r6]
    maximum = f"R{max(index for index, value in enumerate(levels) if value)}"
    if r6:
        failure = "TARGET_A_HIT"
    elif not r1:
        failure = "repair_not_component_merging"
    elif not r2:
        failure = "new_source_orbit_absent"
    elif not r3:
        failure = "component_mismatch_remains"
    elif joint_source_state.F > 1:
        failure = "F_exceeded"
    elif joint_source_state.H > 0:
        failure = "H_positive"
    elif dec_before.hub_touch_count > 2:
        failure = "hub_touch_violation"
    elif not terminal_geometry:
        failure = "terminal_geometry_lost"
    else:
        failure = "other_asserted_reason"
    return {
        "maximum_level": maximum, "levels": {f"R{i}": value for i, value in enumerate(levels)},
        "failure_reason": failure, "recognizer": recognition,
        "predicate_state_roles": {
            "target_a_recognizer": "literal_joint_source",
            "incidence_forest_membership": "literal_joint_source",
            "same_component": "literal_joint_source",
        },
        "literal_macro_entry": {
            "state_hash": rr.state_hash(macro_entry_state), "word": list(macro_entry_state.p),
        },
        "post_rotation_run_state": {
            "state_hash": rr.state_hash(joint_source_state), "word": list(joint_source_state.p),
        },
        "literal_joint_source": {
            "state_hash": rr.state_hash(joint_source_state), "word": list(joint_source_state.p),
            "orbit": source_orbit, "phase": source_phase,
        },
        "literal_joint_target": {
            "state_hash": rr.state_hash(edge.state), "word": list(edge.joint.target),
            "orbit": target_orbit, "phase": target_phase,
        },
        "future_R2_source_orbit": source_orbit, "future_R2_source_phase": source_phase,
        "future_R2_target_orbit": target_orbit, "future_R2_target_phase": target_phase,
        "future_source_component": source_component, "R1_target_component": r1_component,
        "terminal_geometry_available": terminal_geometry,
    }


def run_branch(child: Mapping[str, object], budget: int):
    branch_id = str(child["branch_id"])
    root_state, root_dec, *_ = split.replay_trace(split.record(), child["literal_macro_trace"])
    root_id = f"{branch_id}:0"
    frontier = [(len(child["literal_macro_trace"]), root_state, root_dec, root_id, tuple())]
    # Repair lineage is deliberately part of the key.  It is a refinement of
    # the raw decorated key, so no repaired history is lost to a history-free
    # memo merge while checking the post-repair-source predicate.
    seen = {(rr.decorated_key(root_state, root_dec), tuple())}
    nodes = {root_id: node_record(root_id, None, None, root_state, root_dec, tuple())}
    repairs: dict[str, dict[str, object]] = {}
    r2_paths: list[dict[str, object]] = []
    stats = Counter()
    stats["expanded"] = 0
    next_node = 1
    next_repair = 0
    max_depth = 0
    while frontier and stats["expanded"] < budget:
        depth, state, dec, node_id, lineage = frontier.pop()
        if dec.r_count != 1:
            raise AssertionError("post-R1 fair branch enqueued invalid R count")
        stats["expanded"] += 1
        max_depth = max(max_depth, depth)
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] += 1
            if collision is not None:
                stats[f"prune:{collision}"] += 1
                if lineage:
                    stats[f"post_repair_prune:{collision}"] += 1
                continue
            assert edge is not None
            kind = rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit)
            verdict, after_dec, recognition = rr.evaluate_edge(state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
            if kind == "R":
                if after_dec is None or dec.r_count != 1 or after_dec.r_count != 2:
                    raise AssertionError("R2 candidate does not have exactly one prior R")
                stats["R2_candidates"] += 1
                if not lineage:
                    stats["R2_without_repair"] += 1
                    continue
                related = [repairs[event_id] for event_id in lineage]
                hierarchy = hierarchy_for_r2(state, edge, dec, after_dec, related)
                if recognition != hierarchy["recognizer"]:
                    raise AssertionError("evaluate_edge and hierarchy disagree on literal R2 source")
                for event in related:
                    event["future_R2_observations"].append({
                        "r2_predecessor_node_id": node_id,
                        "source_orbit": hierarchy["future_R2_source_orbit"],
                        "source_phase": hierarchy["future_R2_source_phase"],
                        "maximum_level": hierarchy["maximum_level"],
                    })
                row = {"branch_id": branch_id, "r2_predecessor_node_id": node_id,
                       "r2_edge": rr.edge_json(edge), "repair_event_ids": list(lineage),
                       "decoration_before_R2": dec.to_json(), "decoration_after_R2": after_dec.to_json(),
                       **hierarchy}
                r2_paths.append(row)
                stats[f"hierarchy:{hierarchy['maximum_level']}"] += 1
                stats[f"failure:{hierarchy['failure_reason']}"] += 1
                if hierarchy["maximum_level"] >= "R3":
                    stats["R3_or_higher"] += 1
                if hierarchy["levels"]["R5"]:
                    stats["pre_Target_A_predecessors"] += 1
                if hierarchy["maximum_level"] == "R6":
                    stats["Target_A_hits"] += 1
                continue
            if verdict != "child":
                stats[f"prune:{verdict}"] += 1
                if lineage:
                    stats[f"post_repair_prune:{verdict}"] += 1
                continue
            assert after_dec is not None and after_dec.r_count == 1
            repair = repair_type(edge)
            next_lineage = lineage
            child_id = f"{branch_id}:{next_node}"
            next_node += 1
            nodes[child_id] = node_record(child_id, node_id, rr.edge_json(edge), edge.state, after_dec, lineage)
            if repair is not None:
                event_id = f"{branch_id}:repair:{next_repair}"
                next_repair += 1
                repairs[event_id] = repair_event(event_id, branch_id, node_id, child_id, edge, state, edge.state, dec, after_dec)
                next_lineage = lineage + (event_id,)
                nodes[child_id]["repair_ids"] = list(next_lineage)
                stats[f"repair:{repair}"] += 1
                if repairs[event_id]["component_merge"]:
                    stats["repair:component_merge"] += 1
                if repairs[event_id]["incidence_membership_after"]["repair_source"]:
                    stats["repair:source_orbit_present_after"] += 1
                if component_equal(repairs[event_id]["source_component_after"], repairs[event_id]["target_component_after"]):
                    stats["repair:same_component_after"] += 1
                if edge.state.F <= 1 and edge.state.H == 0 and after_dec.hub_touch_count <= 2:
                    stats["repair:terminal_geometry_preserving"] += 1
            key = (rr.decorated_key(edge.state, after_dec), next_lineage)
            if key in seen:
                stats["memo_duplicates"] += 1
                del nodes[child_id]
                if repair is not None:
                    del repairs[event_id]
                continue
            seen.add(key)
            children.append((depth + 1, edge.state, after_dec, child_id, next_lineage))
        children.sort(key=lambda item: item[3], reverse=True)
        frontier.extend(children)
    exhausted = not frontier
    classification = "FOUND_TARGET_A" if stats["Target_A_hits"] else ("FOUND_PRE_TARGET_A" if stats["R3_or_higher"] else "INCOMPLETE")
    transcript = [
        (node["node_id"], node["parent_id"],
         None if node["incoming_macro_edge"] is None else node["incoming_macro_edge"]["label"],
         node["exact_state_hash"], repr(node["decoration"]), tuple(node["repair_ids"]))
        for node in sorted(nodes.values(), key=lambda value: value["node_id"])
    ]
    frontier_digest = hashlib.sha256(repr(sorted(
        (depth, rr.state_hash(state), repr(dec.to_json()), node_id, lineage)
        for depth, state, dec, node_id, lineage in frontier)).encode("utf-8")).hexdigest()
    return {
        "branch_id": branch_id, "classification": classification, "budget": budget,
        "frontier_size": len(frontier), "seen_size": len(seen), "max_depth": max_depth,
        "stats": dict(sorted(stats.items())), "nodes": list(nodes.values()),
        "repair_events": list(repairs.values()), "r2_paths": r2_paths,
        "traversal_transcript_sha256": hashlib.sha256(repr(transcript).encode("utf-8")).hexdigest(),
        "frontier_sha256": frontier_digest,
        "naturally_exhausted": exhausted,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=25_000)
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--hierarchy", type=Path, default=HIERARCHY)
    parser.add_argument("--witnesses", type=Path, default=WITNESSES)
    args = parser.parse_args()
    if args.budget <= 0:
        raise ValueError("positive equal budget required")
    children = split.frozen_r1_children(split.record())
    branches = {str(child["branch_id"]): run_branch(child, args.budget) for child in children}
    hierarchy_counts = Counter()
    failure_counts = Counter()
    repair_type_counts = Counter()
    merge_counts = Counter()
    for row in branches.values():
        for event in row["repair_events"]:
            # A repair that has not yet led to a legal R2 boundary in this
            # capped traversal is still a repaired path at level R0/R1.  It
            # receives the required explicit ``no_legal_R2`` outcome rather
            # than disappearing from the hierarchy accounting.
            if not event["future_R2_observations"]:
                event["event_hierarchy"] = {"maximum_level": "R1" if event["component_merge"] else "R0",
                                             "failure_reason": "no_legal_R2"}
            else:
                event["event_hierarchy"] = {"maximum_level": max(
                    observation["maximum_level"] for observation in event["future_R2_observations"]),
                    "failure_reason": "observed_future_R2"}
        for path in row["r2_paths"]:
            hierarchy_counts[path["maximum_level"]] += 1
            failure_counts[path["failure_reason"]] += 1
        for event in row["repair_events"]:
            repair_type_counts[event["repair_type"]] += 1
            if event["component_merge"]:
                merge_counts[event["repair_type"]] += 1
    found_target = sum(int(row["stats"].get("Target_A_hits", 0)) for row in branches.values())
    found_r3 = sum(int(row["stats"].get("R3_or_higher", 0)) for row in branches.values())
    overall = "FOUND_TARGET_A" if found_target else ("FOUND_R3_REPAIR" if found_r3 else "FAIR_REPAIR_SEARCH_INCOMPLETE")
    common = {"schema": SCHEMA, "checkpoint_schema": CHECKPOINT_SCHEMA,
              "classification": overall, "scope": "four fresh independent R1 subroots; exact positive cap, hence no absence claim",
              "recognizer_semantics": {
                  "R2_source": "edge.run.state (literal post-rotation joint source)",
                  "legacy_v1_outputs": "INVALID_R2_SOURCE_SEMANTICS",
              },
              "per_branch_budget": args.budget, "frozen_R1_children": children,
              "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
              "driver_sha256": sha256_file(Path(__file__)),
              "prune_profile": rr.TARGET_A_SAFE_PROFILE,
              "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE)}
    result = {**common, "branches": {name: {key: value for key, value in row.items() if key not in {"nodes", "repair_events", "r2_paths"}}
                                            for name, row in branches.items()},
              "equal_budget_verified": all(int(row["stats"]["expanded"]) == args.budget for row in branches.values())}
    hierarchy = {**common, "hierarchy_counts": dict(sorted(hierarchy_counts.items())),
                 "failure_counts": dict(sorted(failure_counts.items())),
                 "repair_type_counts": dict(sorted(repair_type_counts.items())),
                 "component_merging_repairs_by_type": dict(sorted(merge_counts.items())),
                 "paths": [path for row in branches.values() for path in row["r2_paths"]]}
    witnesses = {**common, "provenance_format": "node parent-pointer DAG; exact predecessor is reconstructed from R1 root plus incoming edge chain",
                 "branches": {name: {"nodes": row["nodes"], "repair_events": row["repair_events"]} for name, row in branches.items()}}
    atomic_json(args.result.resolve(), result)
    atomic_json(args.hierarchy.resolve(), hierarchy)
    atomic_json(args.witnesses.resolve(), witnesses)
    print(json.dumps({"classification": overall, "budget": args.budget,
                      "branches": {name: {"expanded": row["stats"]["expanded"], "repairs": len(row["repair_events"]),
                                           "R2": row["stats"].get("R2_candidates", 0), "Target_A": row["stats"].get("Target_A_hits", 0)}
                                   for name, row in branches.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
