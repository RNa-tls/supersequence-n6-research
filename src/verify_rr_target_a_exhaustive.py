#!/usr/bin/env python3
"""Independent-format verifier for Round-35 Target-A root results.

FOUND boundaries are replayed literally from the root corpus without using the
search traversal.  An exhausted root additionally requires a cap-free empty
frontier manifest.  ``--replay-exhausted`` performs an alternate LIFO search
to re-establish natural exhaustion; it is intentionally opt-in because a
genuine exhaustive root may be expensive.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = load_module("round35_verify_macro", WORK / "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
MOVE = {move.label: move for move in exact.ALL_MOVES}
W2_10 = MOVE["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def state_hash(state) -> str:
    return sha256_bytes(repr(state.stable_key()).encode("utf-8"))


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get(
                (weight, abandonment, new_orbit), "other")


def component_roots(state):
    parent: dict[tuple[str, int], tuple[str, int]] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return parent, find


def reconstruct_root(record: Mapping[str, object]):
    state = exact.initial_state()
    for _ in range(int(record["root_ell"])):
        transition = exact.extend(state, W1)
        if transition is None:
            raise AssertionError("root rotation collision")
        state = transition.state
    transition = exact.extend(state, W2_10)
    if transition is None:
        raise AssertionError("root abandonment transition collision")
    state = transition.state
    r_count = 0
    r1_target = None
    hub_touches = 0
    for label in record["literal_joint_word"]:  # type: ignore[index]
        for _ in range(5):
            transition = exact.extend(state, W1)
            if transition is None:
                raise AssertionError("root stored rotation collision")
            state = transition.state
        pre = state
        transition = exact.extend(state, MOVE[str(label)])
        if transition is None:
            raise AssertionError("root stored joint collision")
        kind = joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit)
        if kind == "R":
            r_count += 1
            if r_count == 1:
                r1_target = exact.ORBIT_PHASE[transition.target][0]
        if core.hexagon_id(transition.target) == HUB:
            hub_touches += 1
        state = transition.state
    if state_hash(state) != record["post_return_state_hash"]:
        raise AssertionError("root replay state hash mismatch")
    return state, r_count, r1_target, hub_touches


def literal_boundary_replay(record: Mapping[str, object], boundary: Mapping[str, object]) -> dict[str, object]:
    state, r_count, r1_target, hub_touches = reconstruct_root(record)
    trace = boundary["literal_macro_trace"]
    final = None
    for index, step in enumerate(trace, 1):
        ell = int(step["rotation_length"])
        for _ in range(ell):
            transition = exact.extend(state, W1)
            if transition is None:
                return {"ok": False, "reason": "rotation_collision", "step": index}
            state = transition.state
        pre = state
        transition = exact.extend(state, MOVE[str(step["joint"])])
        if transition is None:
            return {"ok": False, "reason": "joint_collision", "step": index}
        if macro.area_a_prune_reason(transition.state, macro.AREA_A) is not None:
            return {"ok": False, "reason": "area_a_prune", "step": index}
        kind = joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit)
        if core.hexagon_id(transition.target) == HUB:
            hub_touches += 1
        if hub_touches > 2:
            return {"ok": False, "reason": "hub_touch_limit", "step": index}
        if kind == "R":
            r_count += 1
            sq, sph = exact.ORBIT_PHASE[pre.p]
            tq, tph = exact.ORBIT_PHASE[transition.target]
            parent, find = component_roots(pre)
            sr = find(("q", sq)) if ("q", sq) in parent else None
            tr = find(("q", tq)) if ("q", tq) in parent else None
            final = {
                "r_count": r_count, "F": transition.state.F, "H": transition.state.H,
                "Ndef": transition.state.Ndef, "area_a": macro.area_a_prune_reason(transition.state, macro.AREA_A),
                "same_component": sr is not None and sr == tr,
                "chaining": r1_target == sq,
                "state_hash": state_hash(transition.state), "source": [sq, sph], "target": [tq, tph],
            }
        state = transition.state
    if final is None:
        return {"ok": False, "reason": "trace_has_no_R"}
    expected = boundary["conditions"]
    actual_conditions = {
        "exactly_two_R_events": final["r_count"] == 2,
        "immediately_after_R2": True,
        "F_def_le_1": final["F"] <= 1,
        "Ndef_equals_2": final["Ndef"] == 2,
        "H_equals_0": final["H"] == 0,
        "area_a_legal": final["area_a"] is None,
        "same_component": final["same_component"],
    }
    return {
        "ok": actual_conditions == expected and all(actual_conditions.values())
              and final["state_hash"] == boundary["post_r2_state_hash"]
              and final["chaining"] == boundary["chaining"],
        "actual_conditions": actual_conditions, "expected_conditions": expected,
        "final": final,
    }


def alternate_exhaustion(record: Mapping[str, object]) -> dict[str, object]:
    """Alternate direct LIFO traversal for an already claimed exhausted root.

    This intentionally does not share the search driver's decorated-key
    constructor or successor classifier.  It preserves the history fields
    required by the recognizer and re-derives the Target-A predicate inline.
    """
    start, r_count, r1_target, hub_touches = reconstruct_root(record)
    stack = [(start, r_count, r1_target, hub_touches, 0)]
    seen = {(start.stable_key(), r_count, r1_target, hub_touches, 0)}
    nodes, target_count = 0, 0
    while stack:
        state, rc, r1, touches, depth = stack.pop()
        nodes += 1
        candidates = []
        for run in macro.rotation_runs(state):
            for move in macro.NONROT_H0:
                tr = exact.extend(run.state, move)
                if tr is not None:
                    candidates.append((run, tr))
        for run, tr in reversed(candidates):
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if kind == "other":
                continue
            next_touches = touches + int(core.hexagon_id(tr.target) == HUB)
            if next_touches > 2:
                continue
            sq, _ = exact.ORBIT_PHASE[run.state.p]
            tq, _ = exact.ORBIT_PHASE[tr.target]
            if kind == "R":
                nrc = rc + 1
                if nrc == 2:
                    parent, find = component_roots(run.state)
                    sr = find(("q", sq)) if ("q", sq) in parent else None
                    tg = find(("q", tq)) if ("q", tq) in parent else None
                    if (tr.state.F <= 1 and tr.state.Ndef == 2 and tr.state.H == 0
                            and sr is not None and sr == tg):
                        target_count += 1
                continue
            if rc >= 2:
                continue
            key = (tr.state.stable_key(), rc, r1, next_touches, depth + 1)
            if key not in seen:
                seen.add(key)
                stack.append((tr.state, rc, r1, next_touches, depth + 1))
    return {"frontier_empty": True, "nodes": nodes, "seen": len(seen),
            "target_count": target_count}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path,
                        default=ROOT / "outputs" / "rr_target_a_exhaustive_results.json")
    parser.add_argument("--certificates", type=Path,
                        default=ROOT / "outputs" / "rr_target_a_exhaustion_certificates.json")
    parser.add_argument("--ledger", type=Path,
                        default=ROOT / "outputs" / "rr_target_a_22_root_ledger.json")
    parser.add_argument("--prefixes", type=Path,
                        default=ROOT / "outputs" / "rr_long_excursion_prefixes.json")
    parser.add_argument("--replay-exhausted", action="store_true")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "outputs" / "rr_target_a_exhaustive_verified.json")
    args = parser.parse_args()
    results = json.loads(args.results.read_text(encoding="utf-8"))
    certs = json.loads(args.certificates.read_text(encoding="utf-8"))["certificates"]
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    prefixes = json.loads(args.prefixes.read_text(encoding="utf-8"))["prefixes"]
    roots = {}
    for row in ledger["roots"]:
        rec = dict(prefixes[int(row["prefix_index"])])
        rec["root_id"] = row["root_id"]
        roots[rec["root_id"]] = rec
    certificate_by_root = {cert["root_id"]: cert for cert in certs}
    rows, failures = [], []
    for result in results["results"]:
        root_id = result["root_id"]
        record = roots.get(root_id)
        if record is None:
            failures.append({"root_id": root_id, "reason": "unknown_root"})
            continue
        cert = certificate_by_root.get(root_id)
        if cert is None:
            failures.append({"root_id": root_id, "reason": "missing_certificate_manifest"})
            continue
        root_ok = True
        try:
            reconstruct_root(record)
        except Exception as exc:  # independent verifier must report, not hide
            root_ok = False
            failures.append({"root_id": root_id, "reason": f"root_replay:{exc}"})
        found = [literal_boundary_replay(record, boundary) for boundary in result["target_a_boundaries"]]
        if not all(item["ok"] for item in found):
            root_ok = False
            failures.append({"root_id": root_id, "reason": "literal_found_replay_failed", "detail": found})
        exhaustion = None
        if result["status"] == "EXHAUSTED_NO_TARGET_A":
            required = (result["frontier_empty"] and not result["interrupted_by_node_limit"]
                        and not result["interrupted_by_depth_limit"]
                        and int(result["config"]["node_limit"]) == 0
                        and result["config"]["max_depth"] is None)
            if not required:
                root_ok = False
                failures.append({"root_id": root_id, "reason": "invalid_exhaustion_metadata"})
            if args.replay_exhausted and required:
                exhaustion = alternate_exhaustion(record)
                if not exhaustion["frontier_empty"] or exhaustion["target_count"] != 0:
                    root_ok = False
                    failures.append({"root_id": root_id, "reason": "independent_exhaustion_disagrees", "detail": exhaustion})
        if (result["status"] == "INCOMPLETE" and result["frontier_empty"]
                and not result["interrupted_by_node_limit"]
                and not result["interrupted_by_depth_limit"]):
            root_ok = False
            failures.append({"root_id": root_id, "reason": "incomplete_but_frontier_empty"})
        if cert["status"] != result["status"] or cert["final_empty_frontier"] != result["frontier_empty"]:
            root_ok = False
            failures.append({"root_id": root_id, "reason": "certificate_manifest_mismatch"})
        rows.append({"root_id": root_id, "status": result["status"], "ok": root_ok,
                     "found_replays": found, "exhaustion_replay": exhaustion})
    output = {
        "schema": "rr-target-a-exhaustive-verifier-v1",
        "results_sha256": sha256_bytes(args.results.read_bytes()),
        "certificates_sha256": sha256_bytes(args.certificates.read_bytes()),
        "replay_exhausted": args.replay_exhausted,
        "rows": rows, "failures": failures, "verified": not failures,
        "scope": ("FOUND traces are independently literal-replayed. Exhaustion is independently "
                  "re-searched only when --replay-exhausted is explicitly supplied."),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(f"verified={output['verified']} roots={len(rows)} failures={len(failures)}")


if __name__ == "__main__":
    main()
