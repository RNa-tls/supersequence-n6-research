#!/usr/bin/env python3
"""Round 45: equal-budget R1-local continuations for ``short_ell0``.

The historical combined v3 frontier is deliberately not an input here.  The
four R1 children are reconstructed literally and each begins from its own
one-state frontier.  A repair-mask refines (never quotients) the raw decorated
state key so the focused "some Z2/Z3 occurred after R1" predicate cannot be
lost to memoization.
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
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
FAIR_OUTPUT = ROOT / "outputs" / "rr_short_ell0_fair_r1_results.json"
REPAIR_OUTPUT = ROOT / "outputs" / "rr_short_ell0_repair_candidates.json"
CHECKPOINT_ROOT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_split_v4_fair"
SCHEMA = "rr-short-ell0-fair-r1-checkpoint-v4-repair-mask"
REPAIR_TYPES = ("Z2_merge", "Z2_nonmerge", "Z3_fresh_attachment", "Z3_reentry")
REPAIR_BITS = {name: 1 << index for index, name in enumerate(REPAIR_TYPES)}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


split = load("rr_fair_r1_split", ROOT / "src" / "search_rr_short_ell0_r1_split.py")
rr, exact = split.rr, split.exact


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def child_decoration(child: Mapping[str, object]):
    _state, dec, _pre, _before, _edge = split.replay_trace(split.record(), child["literal_macro_trace"])
    return dec


def component_for(summary: Mapping[str, object], node: tuple[str, int]):
    value = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    if value is None:
        return None
    return {"id": value["id"], "class": value["class"]}


def component_count(state) -> int:
    return int(rr.component_summary(state)["component_count"])


def classify_repair(edge) -> tuple[str | None, dict[str, object] | None]:
    """Classify an accepted Z2/Z3 event at its literal pre-joint state.

    ``Z2_merge`` is deliberately an exact incidence condition: both endpoint
    orbits are present in different pre-joint components and become equal in
    the post-joint component summary.  Every other admitted Z2 is retained as
    ``Z2_nonmerge`` rather than silently treated as a repair.
    """
    kind = rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit)
    if kind not in {"Z2", "Z3"}:
        return None, None
    before = edge.run.state
    after = edge.state
    sq, sph = exact.ORBIT_PHASE[before.p]
    tq, tph = exact.ORBIT_PHASE[edge.joint.target]
    pre = rr.component_summary(before)
    post = rr.component_summary(after)
    source = component_for(pre, ("q", sq))
    target = component_for(pre, ("q", tq))
    post_source = component_for(post, ("q", sq))
    post_target = component_for(post, ("q", tq))
    if kind == "Z2":
        merged = (source is not None and target is not None and source["id"] != target["id"] and
                  post_source is not None and post_target is not None and
                  post_source["id"] == post_target["id"])
        repair_type = "Z2_merge" if merged else "Z2_nonmerge"
    else:
        repair_type = "Z3_fresh_attachment" if target is None else "Z3_reentry"
    event = {
        "type": repair_type, "kind": kind, "macro_label": edge.label,
        "source_orbit": sq, "source_phase": sph, "target_orbit": tq, "target_phase": tph,
        "pre_component_count": pre["component_count"], "post_component_count": post["component_count"],
        "source_component_pre": source, "target_component_pre": target,
        "source_component_post": post_source, "target_component_post": post_target,
    }
    return repair_type, event


def repair_mask_names(mask: int) -> list[str]:
    return [name for name in REPAIR_TYPES if mask & REPAIR_BITS[name]]


def fair_key(state, dec, repair_mask: int) -> tuple[object, ...]:
    """A conservative refinement of the already raw decorated state key."""
    return (rr.decorated_key(state, dec), repair_mask)


def config(child: Mapping[str, object], budget: int) -> dict[str, object]:
    return {
        "schema": SCHEMA, "root_id": "short_ell0", "branch_id": child["branch_id"],
        "branch_origin_hash": child["branch_origin_hash"], "r1_event_id": child["r1_event_id"],
        "per_branch_expansion_budget": budget,
        "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "driver_sha256": sha256_file(Path(__file__)),
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
        "state_key": "(raw-decorated-key,repair-type-mask)-refinement",
    }


def serialize_frontier(frontier):
    return [{
        "depth": depth, "state": exact.state_to_json(state), "decoration": dec.to_json(),
        "trace": list(trace), "repair_mask": repair_mask, "repair_events": list(repair_events),
    } for depth, state, dec, trace, repair_mask, repair_events in frontier]


def write_checkpoint(path: Path, child: Mapping[str, object], conf: Mapping[str, object], frontier, seen, stats,
                     *, repair_r2_records, repairable_records, target_a_records):
    payload = {
        "schema": SCHEMA, "config": dict(conf), "branch_origin": dict(child),
        "frontier": serialize_frontier(frontier), "seen_keys": sorted(repr(key) for key in seen),
        "stats": stats, "complete_frontier_snapshot": True,
        # These lists are evidence, rather than state needed to decide a
        # successor.  They nevertheless travel with the checkpoint so a
        # resumed fair branch cannot silently lose its repair/R2 ledger.
        "repair_R2_records": repair_r2_records,
        "repairable_records": repairable_records,
        "target_a_records": target_a_records,
        "classification": "INCOMPLETE" if frontier else "EXHAUSTED_NO_RESULT",
    }
    atomic_json(path, payload)
    return sha256_file(path)


def load_checkpoint(path: Path, child: Mapping[str, object], conf: Mapping[str, object]):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != SCHEMA or raw.get("config") != dict(conf):
        raise ValueError("checkpoint schema/config/engine mismatch")
    if raw.get("branch_origin", {}).get("branch_origin_hash") != child["branch_origin_hash"]:
        raise ValueError("checkpoint branch origin mismatch")
    if not raw.get("complete_frontier_snapshot"):
        raise ValueError("checkpoint has no complete frontier snapshot")
    frontier = []
    for item in raw["frontier"]:
        state = exact.state_from_json(item["state"])
        dec = rr.Decoration.from_json(item["decoration"])
        if dec.r_count != 1 or dec.r1 is None:
            raise ValueError("fair checkpoint contains an R-count other than one")
        frontier.append((int(item["depth"]), state, dec, tuple(item["trace"]), int(item["repair_mask"]),
                         tuple(item["repair_events"])))
    seen = {rr.decode_key(text) for text in raw["seen_keys"]}
    evidence = {
        "repair_R2_records": list(raw.get("repair_R2_records", [])),
        "repairable_records": list(raw.get("repairable_records", [])),
        "target_a_records": list(raw.get("target_a_records", [])),
    }
    return frontier, seen, dict(raw["stats"]), evidence, raw


def failure_reason(recognition: Mapping[str, object], dec, after) -> str:
    conditions = recognition["conditions"]
    endpoints = recognition["r2_endpoint_presence"]
    if not bool(conditions["hub_touch_count_le_2"]):
        return "hub_touch_count_failure"
    if not bool(conditions["F_def_equals_1"]):
        return "F_exceeded"
    if not bool(endpoints["source_orbit_present_in_pre_r2_forest"]):
        return "source_orbit_lost"
    if not bool(endpoints["target_orbit_present_in_pre_r2_forest"]):
        return "terminal_geometry_destroyed"
    if not bool(conditions["same_component"]):
        return "same_component_still_false"
    return "other_explicit_reason"


def repair_predicate(joint_source_state, edge, dec, after, repair_mask: int) -> dict[str, object]:
    if joint_source_state != edge.run.state:
        raise AssertionError("repair predicate must receive literal R2 joint source")
    recognition = rr.target_a_recognizer(rr.r2_literal_joint_source(edge), edge.joint, dec, after)
    summary = rr.component_summary(joint_source_state)
    source_orbit, _phase = exact.ORBIT_PHASE[joint_source_state.p]
    r1_component = component_for(summary, ("q", dec.r1.target_orbit)) if dec.r1 else None
    r2_source_component = component_for(summary, ("q", source_orbit))
    endpoints = recognition["r2_endpoint_presence"]
    terminal_geometry_legal = bool(endpoints["source_orbit_present_in_pre_r2_forest"]) and bool(
        endpoints["target_orbit_present_in_pre_r2_forest"]) and bool(recognition["same_component"])
    conditions = {
        "repair_strictly_between_R1_R2": repair_mask != 0,
        "no_extra_R_before_R2": dec.r_count == 1 and after.r_count == 2,
        "r2_source_orbit_present": r2_source_component is not None,
        "r1_target_and_r2_source_same_component": (
            r1_component is not None and r2_source_component is not None and
            r1_component["id"] == r2_source_component["id"]),
        "terminal_geometry_legal": terminal_geometry_legal,
        "F_equals_1": bool(recognition["conditions"]["F_def_equals_1"]),
        "H_equals_0": bool(recognition["conditions"]["H_equals_0"]),
        "hub_touch_at_most_2": bool(recognition["conditions"]["hub_touch_count_le_2"]),
    }
    return {"is_repairable_predecessor": all(conditions.values()), "conditions": conditions,
            "recognizer": recognition, "r1_target_component": r1_component,
            "r2_source_component": r2_source_component}


def record_repair_r2(branch_id: str, *, depth: int, edge, dec, after, repair_mask: int,
                     repair_events, trace, records, failure_counts, found):
    predicate = repair_predicate(edge.run.state, edge, dec, after, repair_mask)
    recognition = predicate["recognizer"]
    reason = "TARGET_A_HIT" if recognition["is_target_a"] else failure_reason(recognition, dec, after)
    row = {
        "branch_id": branch_id, "depth": depth + 1, "pre_state_hash": rr.state_hash(edge.run.state),
        "candidate_macro_label": edge.label, "repair_mask": repair_mask,
        "repair_types": repair_mask_names(repair_mask), "repair_events": list(repair_events),
        "literal_macro_trace": list(trace + (rr.edge_json(edge),)),
        "decoration_before_R2": dec.to_json(), "decoration_after_R2": after.to_json(),
        "recognizer": recognition, "repair_predicate": predicate, "failure_reason": reason,
        "r1": None if dec.r1 is None else {
            "macro_index": dec.r1.macro_index, "source_orbit": dec.r1.source_orbit,
            "target_orbit": dec.r1.target_orbit, "target_phase": dec.r1.target_phase,
        },
    }
    records.append(row)
    failure_counts[reason] += 1
    if predicate["is_repairable_predecessor"]:
        found.append(row)


def initial_stats() -> dict[str, object]:
    return {
        "expanded": 0, "generated_edges": 0, "memo_duplicates": 0, "max_depth": 0,
        "R2_candidates": 0, "source_orbit_pass_count": 0, "same_component_pass_count": 0,
        "Target_A_hits": 0, "repairable_predecessors": 0, "prune_histogram": {},
        "post_repair_prune_histogram": {}, "repair_event_counts": {},
        "repair_R2_failure_counts": {}, "repair_R2_candidate_count": 0,
        "raw_decorated_key_count": 0, "augmented_key_count": 0,
        "first_post_R1_completer": None,
    }


def run_branch(child: Mapping[str, object], *, budget: int, checkpoint_root: Path,
               checkpoint_every: int, resume: bool) -> dict[str, object]:
    branch_id = str(child["branch_id"])
    conf = config(child, budget)
    checkpoint = checkpoint_root / branch_id / "checkpoint.json"
    if resume:
        frontier, seen, stats, evidence, raw_checkpoint = load_checkpoint(checkpoint, child, conf)
        checkpoint_lineage = [sha256_file(checkpoint)]
    else:
        if checkpoint.exists():
            raise FileExistsError(f"refusing to overwrite checkpoint {checkpoint}")
        state, dec, _pre, _before, _edge = split.replay_trace(split.record(), child["literal_macro_trace"])
        frontier = [(len(child["literal_macro_trace"]), state, dec, tuple(child["literal_macro_trace"]), 0, tuple())]
        seen = {fair_key(state, dec, 0)}
        stats = initial_stats()
        evidence = {"repair_R2_records": [], "repairable_records": [], "target_a_records": []}
        checkpoint_lineage = []
    prunes = Counter(stats.get("prune_histogram", {}))
    post_repair_prunes = Counter(stats.get("post_repair_prune_histogram", {}))
    repair_events_counter = Counter(stats.get("repair_event_counts", {}))
    repair_r2_failures = Counter(stats.get("repair_R2_failure_counts", {}))
    repair_r2_records: list[dict[str, object]] = list(evidence["repair_R2_records"])
    repairable_records: list[dict[str, object]] = list(evidence["repairable_records"])
    target_a_records: list[dict[str, object]] = list(evidence["target_a_records"])
    raw_keys: set[str] = set()
    # On resume, preserve accounting already stored in the final result only;
    # this driver is used here from fresh R1 children.  A resume never calls a
    # cap exhaustion result "exhausted" and retains complete state data.
    while frontier and int(stats["expanded"]) < budget:
        depth, state, dec, trace, repair_mask, repair_events = frontier.pop()
        if dec.r_count != 1:
            raise AssertionError("fair branch attempted to traverse past R2")
        stats["expanded"] = int(stats["expanded"]) + 1
        stats["max_depth"] = max(int(stats["max_depth"]), depth)
        raw_keys.add(repr(rr.decorated_key(state, dec)))
        child_entries = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] = int(stats["generated_edges"]) + 1
            if collision is not None:
                prunes[collision] += 1
                if repair_mask:
                    post_repair_prunes["literal_collision"] += 1
                continue
            assert edge is not None
            kind = rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit)
            verdict, child_dec, recognition = rr.evaluate_edge(state, dec, edge,
                                                               prune_profile=rr.TARGET_A_SAFE_PROFILE)
            if kind == "R":
                # With an R1 child as root this is an R2 boundary, never a
                # child.  The assertion is the no-hidden-third-R control.
                if dec.r_count != 1 or child_dec is None or child_dec.r_count != 2:
                    raise AssertionError("R2 boundary did not have exactly one preceding R")
                stats["R2_candidates"] = int(stats["R2_candidates"]) + 1
                assert recognition is not None
                endpoints = recognition["r2_endpoint_presence"]
                if endpoints["source_orbit_present_in_pre_r2_forest"]:
                    stats["source_orbit_pass_count"] = int(stats["source_orbit_pass_count"]) + 1
                if recognition["same_component"]:
                    stats["same_component_pass_count"] = int(stats["same_component_pass_count"]) + 1
                if verdict == "FOUND_TARGET_A":
                    stats["Target_A_hits"] = int(stats["Target_A_hits"]) + 1
                    target_a_records.append({
                        "branch_id": branch_id, "depth": depth + 1,
                        "pre_state_hash": rr.state_hash(edge.run.state),
                        "candidate_macro_label": edge.label,
                        "literal_macro_trace": list(trace + (rr.edge_json(edge),)),
                        "decoration_before_R2": dec.to_json(),
                        "decoration_after_R2": child_dec.to_json(),
                        "post_r2_state": exact.state_to_json(edge.state),
                        "recognizer": recognition, "repair_mask": repair_mask,
                        "repair_types": repair_mask_names(repair_mask),
                        "repair_events": list(repair_events),
                        "canonical_comparison_and_helper_free_target_b": rr.dispatch_target_b(
                            recognition, edge.state),
                    })
                if repair_mask:
                    stats["repair_R2_candidate_count"] = int(stats["repair_R2_candidate_count"]) + 1
                    record_repair_r2(branch_id, depth=depth, edge=edge, dec=dec, after=child_dec,
                                     repair_mask=repair_mask, repair_events=repair_events, trace=trace,
                                     records=repair_r2_records, failure_counts=repair_r2_failures,
                                     found=repairable_records)
                continue
            if verdict != "child":
                prunes[verdict] += 1
                if repair_mask:
                    if verdict == "hub_touch_count_exceeded":
                        post_repair_prunes["hub_touch_count_failure"] += 1
                    elif verdict.endswith(":F_exceeded"):
                        post_repair_prunes["F_exceeded"] += 1
                    else:
                        post_repair_prunes["other_explicit_reason"] += 1
                continue
            assert child_dec is not None
            next_mask = repair_mask
            next_events = repair_events
            repair_type, repair_event = classify_repair(edge)
            if repair_type is not None:
                next_mask |= REPAIR_BITS[repair_type]
                next_events = repair_events + ({"macro_index": child_dec.macro_index, **repair_event},)
                repair_events_counter[repair_type] += 1
            if child_dec.r_count != 1:
                raise AssertionError("non-R child changed R count")
            if dec.completer is None and child_dec.completer is not None and stats["first_post_R1_completer"] is None:
                stats["first_post_R1_completer"] = {"macro_index": child_dec.completer.macro_index,
                    "kind": child_dec.completer.kind, "event_order_class": child_dec.event_order_class}
            key = fair_key(edge.state, child_dec, next_mask)
            if key in seen:
                stats["memo_duplicates"] = int(stats["memo_duplicates"]) + 1
                prunes["augmented_memo_duplicate"] += 1
                continue
            seen.add(key)
            child_entries.append((depth + 1, edge.state, child_dec,
                                  trace + (rr.edge_json(edge),), next_mask, next_events))
        child_entries.sort(key=lambda item: item[3][-1]["label"], reverse=True)
        frontier.extend(child_entries)
        if checkpoint_every and int(stats["expanded"]) % checkpoint_every == 0:
            stats["prune_histogram"] = dict(sorted(prunes.items()))
            stats["post_repair_prune_histogram"] = dict(sorted(post_repair_prunes.items()))
            stats["repair_event_counts"] = dict(sorted(repair_events_counter.items()))
            stats["repair_R2_failure_counts"] = dict(sorted(repair_r2_failures.items()))
            stats["raw_decorated_key_count"] = len(raw_keys)
            stats["augmented_key_count"] = len(seen)
            stats["repairable_predecessors"] = len(repairable_records)
            checkpoint_lineage.append(write_checkpoint(
                checkpoint, child, conf, frontier, seen, stats,
                repair_r2_records=repair_r2_records, repairable_records=repairable_records,
                target_a_records=target_a_records))
    stats["prune_histogram"] = dict(sorted(prunes.items()))
    stats["post_repair_prune_histogram"] = dict(sorted(post_repair_prunes.items()))
    stats["repair_event_counts"] = dict(sorted(repair_events_counter.items()))
    stats["repair_R2_failure_counts"] = dict(sorted(repair_r2_failures.items()))
    stats["raw_decorated_key_count"] = len(raw_keys)
    stats["augmented_key_count"] = len(seen)
    stats["repairable_predecessors"] = len(repairable_records)
    # This run is exhausted only when the independently owned frontier is
    # naturally empty before its equal per-branch cap.
    exhausted = not frontier
    if stats["Target_A_hits"]:
        classification = "FOUND_TARGET_A"
    elif repairable_records:
        classification = "FOUND_REPAIRABLE_PREDECESSOR"
    elif exhausted:
        classification = "EXHAUSTED_NO_RESULT"
    else:
        classification = "INCOMPLETE"
    checkpoint_lineage.append(write_checkpoint(
        checkpoint, child, conf, frontier, seen, stats,
        repair_r2_records=repair_r2_records, repairable_records=repairable_records,
        target_a_records=target_a_records))
    return {
        "branch_id": branch_id, "classification": classification, "budget": budget,
        "stats": stats, "frontier_size": len(frontier), "seen_size": len(seen),
        "checkpoint": {"path": str(checkpoint.relative_to(ROOT)), "sha256": sha256_file(checkpoint),
                       "schema": SCHEMA, "lineage": checkpoint_lineage},
        "repair_R2_records": repair_r2_records, "repairable_records": repairable_records,
        "target_a_records": target_a_records,
    }


def spine(children: list[Mapping[str, object]], branch_results: Mapping[str, Mapping[str, object]]):
    # The preparation spine is the trace preceding the child's own R1 macro,
    # not the full trace (which ends with different R1 edges).
    deepest = max(children, key=lambda child: len(child["literal_macro_trace"]) - 1)
    deep_prep = list(deepest["literal_macro_trace"][:-1])
    rows = []
    for child in children:
        trace = list(child["literal_macro_trace"])
        prep = trace[:-1]
        dec = child_decoration(child)
        c = dec.completer
        if c is None:
            completion_at_r1 = "not_completed_by_R1"
        elif c.macro_index < dec.r1.macro_index:
            completion_at_r1 = "before_R1"
        elif c.macro_index == dec.r1.macro_index:
            completion_at_r1 = "by_R1"
        else:
            raise AssertionError("completer after R1 cannot be present in frozen child")
        later = branch_results[str(child["branch_id"])]["stats"]["first_post_R1_completer"]
        rows.append({
            "branch_id": child["branch_id"],
            "preceding_Z2_preparation_edges": sum(1 for edge in prep if edge["kind"] == "Z2"),
            "R1_source_phase": child["r1"]["source_phase"], "R1_target_phase": child["r1"]["target_phase"],
            "hub_completion_at_R1": completion_at_r1,
            "first_hub_completion_after_R1_observed": later,
            "preparation_trace": prep,
            "preparation_is_prefix_of_deepest": prep == deep_prep[:len(prep)],
            "full_R1_trace_is_prefix_of_deepest": trace == list(deepest["literal_macro_trace"])[:len(trace)],
        })
    if not all(row["preparation_is_prefix_of_deepest"] for row in rows):
        raise AssertionError("preparation-spine prefix relation failed")
    return {"deepest_branch_id": deepest["branch_id"], "deepest_preparation_trace": deep_prep, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=25_000)
    parser.add_argument("--checkpoint-every", type=int, default=5_000)
    parser.add_argument("--checkpoint-root", type=Path, default=CHECKPOINT_ROOT)
    parser.add_argument("--output", type=Path, default=FAIR_OUTPUT)
    parser.add_argument("--repair-output", type=Path, default=REPAIR_OUTPUT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.budget <= 0:
        raise ValueError("fair branch budget must be positive")
    # Relative CLI paths are convenient for the supplied examples, but every
    # serialized provenance path is relative to ``ROOT``.  Resolve once at
    # the boundary so a run cannot fail only while writing its final evidence.
    checkpoint_root = args.checkpoint_root.resolve()
    output = args.output.resolve()
    repair_output = args.repair_output.resolve()
    children = split.frozen_r1_children(split.record())
    results = {}
    for child in children:
        results[str(child["branch_id"])] = run_branch(
            child, budget=args.budget, checkpoint_root=checkpoint_root,
            checkpoint_every=args.checkpoint_every, resume=args.resume)
    spine_data = spine(children, results)
    # The aggregate is created only after every child has received its own
    # equal cap (or became naturally exhausted earlier).
    classifications = [result["classification"] for result in results.values()]
    overall = ("FOUND_TARGET_A" if "FOUND_TARGET_A" in classifications else
               "FOUND_REPAIR_PATTERN" if "FOUND_REPAIRABLE_PREDECESSOR" in classifications else
               "FAIR_R1_SEARCH_COMPLETE" if all(name == "EXHAUSTED_NO_RESULT" for name in classifications) else
               "FAIR_R1_SEARCH_INCOMPLETE")
    fair = {
        "schema": "rr-short-ell0-fair-r1-results-v1", "classification": overall,
        "scope": "four independent equal-budget R1-local Target-A-safe traversals; no combined v3 resume",
        "per_branch_budget": args.budget, "fairness": {
            "method": "four independent fresh R1 subroots", "all_branches_received_equal_budget":
                all(int(row["stats"]["expanded"]) == args.budget or row["frontier_size"] == 0
                    for row in results.values()),
        },
        "frozen_R1_children": children, "spine": spine_data,
        "branches": {name: {key: value for key, value in row.items() if key not in {"repair_R2_records", "repairable_records"}}
                     for name, row in results.items()},
        "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "driver_sha256": sha256_file(Path(__file__)),
    }
    repair = {
        "schema": "rr-short-ell0-repair-pattern-candidates-v1", "classification": overall,
        "scope": "R2 boundaries reached from fair R1-local prefixes with at least one accepted Z2/Z3 event after R1",
        "repair_types": list(REPAIR_TYPES),
        "by_branch": {name: {"R2_after_repair": row["stats"]["repair_R2_candidate_count"],
                              "failure_counts": row["stats"]["repair_R2_failure_counts"],
                              "records": row["repair_R2_records"],
                              "repairable_predecessors": row["repairable_records"],
                              "target_A_hits": row["target_a_records"]}
                      for name, row in results.items()},
    }
    atomic_json(output, fair)
    atomic_json(repair_output, repair)
    print(json.dumps({"classification": overall, "budget": args.budget,
                      "branches": {name: {"expanded": row["stats"]["expanded"],
                                           "R2": row["stats"]["R2_candidates"],
                                           "repair_R2": row["stats"]["repair_R2_candidate_count"],
                                           "Target_A": row["stats"]["Target_A_hits"]}
                                   for name, row in results.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
