#!/usr/bin/env python3
"""Read-only verification for the Round-46 post-repair-source search."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / "outputs" / "rr_short_ell0_corrected_fair_repair_results.json"
HIERARCHY = ROOT / "outputs" / "rr_short_ell0_corrected_repair_hierarchy.json"
WITNESSES = ROOT / "outputs" / "rr_short_ell0_corrected_repair_witnesses.json"
OUT = ROOT / "outputs" / "rr_short_ell0_corrected_repair_verified.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


search = load("rr_repair_verify_search", ROOT / "src" / "search_rr_short_ell0_repair_fair.py")
split, rr, exact = search.split, search.rr, search.exact


def edge_for_label(state, label):
    for edge, collision in rr.iter_raw_macro_candidates(state):
        if collision is None and edge is not None and edge.label == label:
            return edge
    raise AssertionError(f"literal macro edge unavailable: {label}")


def node_trace(nodes, node_id, root_trace):
    chain = []
    while True:
        node = nodes[node_id]
        if node["parent_id"] is None:
            break
        chain.append(node["incoming_macro_edge"])
        node_id = node["parent_id"]
    return list(root_trace) + list(reversed(chain))


def replay(trace):
    state, dec = rr.initial_decoration(split.record())
    for step in trace:
        edge = edge_for_label(state, step["label"])
        dec = rr.advance_decoration(edge.run.state, edge.joint, dec)
        state = edge.state
    return state, dec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--hierarchy", type=Path, default=HIERARCHY)
    parser.add_argument("--witnesses", type=Path, default=WITNESSES)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = json.loads(args.result.resolve().read_text(encoding="utf-8"))
    hierarchy = json.loads(args.hierarchy.resolve().read_text(encoding="utf-8"))
    witnesses = json.loads(args.witnesses.resolve().read_text(encoding="utf-8"))
    if not (result["schema"] == hierarchy["schema"] == witnesses["schema"] == search.SCHEMA):
        raise AssertionError("repair output schema disagreement")
    if result["prune_profile"] != rr.TARGET_A_SAFE_PROFILE:
        raise AssertionError("completion-only prune profile enabled")
    children = {row["branch_id"]: row for row in result["frozen_R1_children"]}
    if set(result["branches"]) != set(children) or set(witnesses["branches"]) != set(children):
        raise AssertionError("not exactly the four frozen R1 subroots")
    budget = int(result["per_branch_budget"])
    if not result["equal_budget_verified"]:
        raise AssertionError("fairness flag false")
    for branch_id, branch in result["branches"].items():
        if int(branch["stats"]["expanded"]) != budget:
            raise AssertionError("unequal positive branch budget")
        if branch["naturally_exhausted"]:
            raise AssertionError("a capped branch is unexpectedly labelled exhausted")
    # Verify every serialized repair event's exact type / no-hidden-R data.
    all_events = {}
    for branch_id, blob in witnesses["branches"].items():
        nodes = {row["node_id"]: row for row in blob["nodes"]}
        if len(nodes) != len(blob["nodes"]):
            raise AssertionError("duplicate provenance node id")
        for event in blob["repair_events"]:
            if event["repair_type"] not in {"Z2", "Z3_fresh"}:
                raise AssertionError("invalid repair category")
            before = rr.Decoration.from_json(event["decoration_before"])
            after = rr.Decoration.from_json(event["decoration_after"])
            if before.r_count != 1 or after.r_count != 1:
                raise AssertionError("repair consumed an R or has hidden R")
            if event["repair_type"] == "Z3_fresh" and event["incidence_membership_before"]["repair_source"]:
                raise AssertionError("Z3 fresh was already open")
            if event["event_id"] in all_events:
                raise AssertionError("repair event id reused across branches")
            all_events[event["event_id"]] = event
    levels = Counter()
    failures = Counter()
    r4_or_higher = []
    for path in hierarchy["paths"]:
        if not path["repair_event_ids"]:
            raise AssertionError("repair hierarchy path lacks a repair")
        if any(event_id not in all_events for event_id in path["repair_event_ids"]):
            raise AssertionError("repair hierarchy refers to unknown event")
        maximum = path["maximum_level"]
        if maximum not in {"R0", "R1", "R2", "R3", "R4", "R5", "R6"}:
            raise AssertionError("invalid success hierarchy level")
        levels[maximum] += 1
        failures[path["failure_reason"]] += 1
        if maximum in {"R4", "R5", "R6"}:
            r4_or_higher.append(path)
    if dict(sorted(levels.items())) != dict(sorted(hierarchy["hierarchy_counts"].items())):
        raise AssertionError("hierarchy count does not equal path partition")
    if dict(sorted(failures.items())) != dict(sorted(hierarchy["failure_counts"].items())):
        raise AssertionError("failure count does not equal path partition")
    # Literal replay for EVERY R4+ path, as requested.  Cache each provenance
    # node's literal state once: many R2 candidates share a predecessor, and
    # rebuilding a 25k-node map for every boundary is purely verifier overhead
    # rather than independent evidence.
    node_maps = {branch_id: {row["node_id"]: row for row in blob["nodes"]}
                 for branch_id, blob in witnesses["branches"].items()}
    replay_cache = {}

    def replay_node(branch_id, node_id):
        token = (branch_id, node_id)
        if token in replay_cache:
            return replay_cache[token]
        node = node_maps[branch_id][node_id]
        if node["parent_id"] is None:
            answer = replay(children[branch_id]["literal_macro_trace"])
        else:
            state, dec = replay_node(branch_id, node["parent_id"])
            edge = edge_for_label(state, node["incoming_macro_edge"]["label"])
            answer = (edge.state, rr.advance_decoration(edge.run.state, edge.joint, dec))
        if rr.state_hash(answer[0]) != node["exact_state_hash"]:
            raise AssertionError("literal provenance parent chain reconstructs wrong state")
        replay_cache[token] = answer
        return answer

    for path in r4_or_higher:
        branch_id = path["branch_id"]
        state, dec = replay_node(branch_id, path["r2_predecessor_node_id"])
        edge = edge_for_label(state, path["r2_edge"]["label"])
        after = rr.advance_decoration(edge.run.state, edge.joint, dec)
        joint_source = edge.run.state
        recognition = rr.target_a_recognizer(joint_source, edge.joint, dec, after)
        if recognition != path["recognizer"]:
            raise AssertionError("post-repair R2 recognizer replay disagreement")
        source, phase = exact.ORBIT_PHASE[joint_source.p]
        if (source, phase) != (path["future_R2_source_orbit"], path["future_R2_source_phase"]):
            raise AssertionError("future R2 source orbit was not the literal post-repair source")
        if path["literal_macro_entry"]["state_hash"] != rr.state_hash(state):
            raise AssertionError("stored macro-entry provenance mismatch")
        if path["literal_joint_source"]["state_hash"] != rr.state_hash(joint_source):
            raise AssertionError("stored literal joint source mismatch")
        if path["literal_macro_entry"]["state_hash"] == path["literal_joint_source"]["state_hash"]:
            raise AssertionError("regression fixture requires a nontrivial R2 rotation run")
        if path["maximum_level"] == "R6" and not recognition["is_target_a"]:
            raise AssertionError("R6 is not a literal Target-A hit")
    payload = {"schema": "rr-short-ell0-repair-search-independent-verifier-v1",
               "status": "VERIFIED_BOUNDED_REPAIR_SEARCH",
               "scope": "equal positive cap; no absence conclusion",
               "equal_budget_verified": True,
               "repair_types_verified": ["Z2", "Z3_fresh"],
               "repair_event_count": len(all_events),
               "hierarchy_counts": dict(sorted(levels.items())),
               "failure_counts": dict(sorted(failures.items())),
               "R4_plus_literal_replays": len(r4_or_higher),
               "Target_A_hits_literal_replayed": levels["R6"],
               "no_completion_only_prunes": True}
    args.output.resolve().write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
