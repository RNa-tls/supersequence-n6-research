#!/usr/bin/env python3
"""Independent audit for Round-47 short_ell0 Target-A/Target-B ledger.

This verifier intentionally replays the *literal R2 joint source* after its
rotation run.  It was written after finding that the Round-46 hierarchy
analysis passed the macro-entry state to the Target-A component recognizer.
Those two words need not be in the same E-orbit.  Consequently this verifier
does not trust the stored R6 label or its stored recognizer object.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
HIERARCHY = ROOT / "outputs" / "rr_short_ell0_repair_hierarchy.json"
WITNESSES = ROOT / "outputs" / "rr_short_ell0_repair_witnesses.json"
CLASSES = ROOT / "outputs" / "rr_short_ell0_target_a_classes.json"
KNOWN = ROOT / "outputs" / "rr_short_ell0_known18_comparison.json"
LEDGER = ROOT / "outputs" / "rr_short_ell0_target_b_ledger.json"
OUT = ROOT / "outputs" / "rr_short_ell0_target_b_verified.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fair = load("rr47_verify_fair", ROOT / "src" / "search_rr_short_ell0_repair_fair.py")
split, rr, exact, core = fair.split, fair.rr, fair.exact, fair.core
macro = rr.macro
MOVE = {move.label: move for move in exact.ALL_MOVES}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def state_hash(state) -> str:
    return rr.state_hash(state)


def state_from_json(data: Mapping[str, object]):
    hm = [0] * exact.HEX_COUNT
    om = [0] * exact.ORBIT_COUNT
    for i, mask in data["hex_masks"]:  # type: ignore[index]
        hm[int(i)] = int(mask)
    for i, mask in data["orbit_masks"]:  # type: ignore[index]
        om[int(i)] = int(mask)
    return exact.ExactState(tuple(int(v) for v in data["p"]), tuple(hm), tuple(om),  # type: ignore[index]
                            int(data["F"]), int(data["S"]), int(data["H"]))


def edge_for_data(state, data: Mapping[str, object]):
    ell = int(data["rotation_length"])
    label = str(data["joint"])
    runs = [run for run in macro.rotation_runs(state) if run.ell == ell]
    if len(runs) != 1:
        raise AssertionError("serialized run is ambiguous or absent")
    joint = exact.extend(runs[0].state, MOVE[label])
    if joint is None:
        raise AssertionError("serialized R2 is collision-illegal")
    edge = macro.MacroEdge(runs[0], joint)
    if edge.label != data["label"]:
        raise AssertionError("serialized R2 label mismatch")
    return edge


def replay_branch(branch: Mapping[str, object], root_child: Mapping[str, object]):
    root_state, root_dec, *_ = split.replay_trace(split.record(), root_child["literal_macro_trace"])
    nodes = {str(row["node_id"]): row for row in branch["nodes"]}  # type: ignore[index]
    cache: dict[str, tuple[Any, Any]] = {}

    def replay(node_id: str):
        if node_id in cache:
            return cache[node_id]
        node = nodes[node_id]
        if node["parent_id"] is None:
            state, dec = root_state, root_dec
        else:
            parent_state, parent_dec = replay(str(node["parent_id"]))
            edge = edge_for_data(parent_state, node["incoming_macro_edge"])  # type: ignore[arg-type]
            state = edge.state
            dec = rr.advance_decoration(edge.run.state, edge.joint, parent_dec)
        if state_hash(state) != node["exact_state_hash"]:
            raise AssertionError(f"parent-DAG literal replay mismatch: {node_id}")
        if dec.to_json() != node["decoration"]:
            raise AssertionError(f"parent-DAG decoration mismatch: {node_id}")
        cache[node_id] = (state, dec)
        return cache[node_id]

    for node_id in nodes:
        replay(node_id)
    return cache


def literal_target_a(pre_joint_state, transition, before, after) -> dict[str, object]:
    """Independent Target-A predicate; source is exactly the R2 joint source."""
    source_q, source_phase = exact.ORBIT_PHASE[pre_joint_state.p]
    target_q, target_phase = exact.ORBIT_PHASE[transition.target]
    parent, find = rr.incidence_components(pre_joint_state)
    source_root = find(("q", source_q)) if ("q", source_q) in parent else None
    target_root = find(("q", target_q)) if ("q", target_q) in parent else None
    conditions = {
        "exactly_two_R_events": before.r_count == 1 and after.r_count == 2,
        "immediately_after_R2": rr.joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit) == "R",
        "F_def_equals_1": transition.state.F == 1,
        "H_equals_0": transition.state.H == 0,
        "hub_touch_count_le_2": after.hub_touch_count <= 2,
        "same_component": source_root is not None and source_root == target_root,
    }
    return {"is_target_a": all(conditions.values()), "conditions": conditions,
            "source_orbit": source_q, "source_phase": source_phase,
            "target_orbit": target_q, "target_phase": target_phase}


def b_plus_r_bound(state) -> tuple[int, int]:
    need = exact.TARGET_P - state.P + 1
    q, _ = exact.ORBIT_PHASE[state.p]
    used = state.orbit_masks[q].bit_count()
    return need, 1 + (5 - used) + 5 * max(exact.TARGET_O - state.O, 0) + 4 * max(macro.AREA_A.n_limit - state.Ndef, 0)


def independent_flow(state, node_cap: int, seconds: float):
    stats = {"nodes": 0, "truncated": False, "depth": 0, "max_depth": 0,
             "max_visited": state.visited_count, "leaf_states": 0, "prunes": Counter(), "ells": set()}

    def dfs(st):
        stats["nodes"] += 1
        if stats["nodes"] > node_cap or time.monotonic() > deadline:
            stats["truncated"] = True
            return None
        if macro.rotation_runs(st)[-1].state.visited_count == 720:
            return []
        stats["max_depth"] = max(stats["max_depth"], stats["depth"])
        stats["max_visited"] = max(stats["max_visited"], st.visited_count)
        alive = False
        for edge in macro.macro_edges(st):
            reason = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            if reason is not None:
                stats["prunes"][reason] += 1
                continue
            need, bound = b_plus_r_bound(edge.state)
            if need > bound:
                stats["prunes"]["round32_B_plus_R"] += 1
                continue
            alive = True
            stats["ells"].add(edge.run.ell)
            stats["depth"] += 1
            got = dfs(edge.state)
            stats["depth"] -= 1
            if got is not None:
                return [edge.label] + got
            if stats["truncated"]:
                return None
        if not alive:
            stats["leaf_states"] += 1
        return None

    deadline = time.monotonic() + seconds
    path = dfs(state)
    verdict = "FOUND_ENGINE_CONTINUATION" if path is not None else ("INCOMPLETE" if stats["truncated"] else "EXHAUSTED_NO_PATH")
    return {"verdict": verdict, "nodes": stats["nodes"], "truncated": stats["truncated"],
            "max_depth": stats["max_depth"], "max_visited": stats["max_visited"],
            "leaf_states": stats["leaf_states"], "prunes": dict(sorted(stats["prunes"].items())),
            "surviving_ells": sorted(stats["ells"]), "solution": path}


def ast_helper_free(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return not any(isinstance(node, ast.Name) and node.id == "true_phase_walk_capacity" for node in ast.walk(tree))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", type=Path, default=CLASSES)
    ap.add_argument("--known", type=Path, default=KNOWN)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--output", type=Path, default=OUT)
    ap.add_argument("--node-cap", type=int, default=20_000)
    ap.add_argument("--seconds", type=float, default=30.0)
    args = ap.parse_args()
    hierarchy = json.loads(HIERARCHY.read_text(encoding="utf-8"))
    source = json.loads(WITNESSES.read_text(encoding="utf-8"))
    frozen = json.loads(args.classes.read_text(encoding="utf-8"))
    known = json.loads(args.known.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    if not ast_helper_free(ROOT / "src" / "analyze_rr_short_ell0_target_b.py"):
        raise AssertionError("analysis path reaches suspect helper")
    claims = [row for row in hierarchy["paths"] if row["maximum_level"] == "R6"]
    if len(claims) != 38_406 or len(frozen["claimed_R6_witnesses"]) != len(claims):
        raise AssertionError("stored-R6 claim count mismatch")
    roots = {str(row["branch_id"]): row for row in hierarchy["frozen_R1_children"]}
    by_branch: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in claims:
        by_branch[str(row["branch_id"])].append(row)
    actual: list[tuple[str, Any, Any, dict[str, object]]] = []
    false_count = 0
    source_disagreements = Counter()
    witness_truth = {}
    serial = 0
    for branch_id, rows in sorted(by_branch.items()):
        replayed = replay_branch(source["branches"][branch_id], roots[branch_id])
        for row in rows:
            state, dec = replayed[str(row["r2_predecessor_node_id"])]
            edge = edge_for_data(state, row["r2_edge"])
            after = rr.advance_decoration(edge.run.state, edge.joint, dec)
            check = literal_target_a(edge.run.state, edge.joint, dec, after)
            wid = f"short_ell0_target_a_{serial:05d}"
            serial += 1
            stored_source = (int(row["future_R2_source_orbit"]), int(row["future_R2_source_phase"]))
            literal_source = (check["source_orbit"], check["source_phase"])
            if stored_source != literal_source:
                source_disagreements["macro_entry_source_not_joint_source"] += 1
            witness_truth[wid] = check["is_target_a"]
            if check["is_target_a"]:
                actual.append((wid, edge.state, after, check))
            else:
                false_count += 1
    if serial != len(claims):
        raise AssertionError("claim traversal incomplete")
    claimed_rows = {str(row["witness_id"]): row for row in frozen["claimed_R6_witnesses"]}
    if set(claimed_rows) != set(witness_truth):
        raise AssertionError("frozen witness id universe mismatch")
    for wid, truth in witness_truth.items():
        if bool(claimed_rows[wid]["exact_target_a_replay"]) != bool(truth):
            raise AssertionError(f"frozen exact Target-A classification mismatch: {wid}")
    actual_ids = [wid for wid, _state, _dec, _check in actual]
    if frozen["exact_Target_A_witness_ids"] != actual_ids:
        raise AssertionError("exact Target-A witness ordering mismatch")
    # The frozen audit should expose its mismatch, rather than laundering the
    # original hierarchy count into a later Target-B ledger.
    if int(frozen["counts"]["stored_R6_replay_mismatches"]) != false_count:
        raise AssertionError("stored mismatch count wrong")
    if int(frozen["counts"]["exact_Target_A_literal_replays"]) != len(actual):
        raise AssertionError("actual Target-A count wrong")
    flow_rows = []
    for wid, state, _dec, _check in actual:
        result = independent_flow(state, args.node_cap, args.seconds)
        flow_rows.append({"witness_id": wid, **result})
    ledger_hist = Counter(row["final_status"] for row in ledger["rows"])
    expected_hist = Counter(row["verdict"] for row in flow_rows)
    if ledger_hist != expected_hist:
        raise AssertionError((ledger_hist, expected_hist))
    for ledger_row, result in zip(ledger["rows"], flow_rows):
        recorded = ledger_row["exact_flow"]
        if recorded is None:
            raise AssertionError("Target-B flow was not run")
        for key in ("verdict", "nodes", "truncated", "max_depth", "max_visited", "leaf_states", "prunes", "surviving_ells"):
            if recorded[key] != result[key]:
                raise AssertionError(f"independent flow mismatch on {key}")
    if len(known["canonical_class_comparison"]) != len(actual):
        raise AssertionError("known18 class count mismatch")
    payload = {
        "schema": "rr-short-ell0-target-b-independent-verifier-v1",
        "status": "VERIFICATION_FAILURE" if false_count else "VERIFIED",
        "scope": "literal joint-source R2 audit + helper-free exact Area-A Target-B flow",
        "stored_R6_claims": len(claims),
        "literal_joint_source_target_a_hits": len(actual),
        "stored_R6_replay_mismatches": false_count,
        "source_coordinate_disagreements": dict(source_disagreements),
        "Target_B_flow": flow_rows,
        "canonical_and_known18_mapping_verified": True,
        "helper_free_ast_check": True,
        "input_sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in (HIERARCHY, WITNESSES, args.classes, args.known, args.ledger)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
