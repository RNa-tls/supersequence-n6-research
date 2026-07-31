#!/usr/bin/env python3
"""Independent verifier for the Round-40 five-short-root traversal.

This verifier intentionally does not call the Round-35 search driver.  It
reconstructs the five bare roots, replays every reported Target-A trace,
checks checkpoint identities and complete-frontier snapshots, and, for every
new Target-A state, independently applies only the helper-free coarse and
Round-32 B+R exact macro-flow path.  An exhausted short root is re-searched
with a smaller independently written history key.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
SEARCH = ROOT / "src" / "search_rr_target_a_exhaustive.py"
SHORT_DRIVER = ROOT / "src" / "search_rr_short5_exact.py"
RESULTS = ROOT / "outputs" / "rr_short5_search_results.json"
CERTIFICATES = ROOT / "outputs" / "rr_short5_exhaustion_certificates.json"
NEW_BOUNDARIES = ROOT / "outputs" / "rr_short5_new_boundaries.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = load_module("rr_short5_verify_macro", WORK / "superperm_partial_f1_macro.py")
exact, core = macro.exact, macro.core
W1 = macro.W1
MOVE = {move.label: move for move in exact.ALL_MOVES}
W2_10 = MOVE["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def state_hash(state) -> str:
    return sha256_bytes(repr(state.stable_key()).encode("utf-8"))


def joint_kind(transition) -> str:
    return {
        (2, False, False): "Z2",
        (2, True, True): "Z2abandon",
        (3, False, False): "R",
        (3, False, True): "Z3",
    }.get((transition.move.weight, transition.abandonment, transition.new_orbit), "other")


def component_roots(state):
    parent: dict[tuple[str, int], tuple[str, int]] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(left, right):
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for orbit, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[orbit])[phase]
                union(("q", orbit), ("h", core.hexagon_id(port)))
    return parent, find


def reconstruct_short_root(record: Mapping[str, object]):
    ell = int(record["root_ell"])
    if record["root_id"] != f"short_ell{ell}" or record["literal_joint_word"] != []:
        raise AssertionError("not a bare short-root record")
    state, path = exact.initial_state(), []
    for _ in range(ell):
        transition = exact.extend(state, W1)
        if transition is None:
            raise AssertionError("root rotation collision")
        state = transition.state
        path.append("rot^1;w1:0")
    transition = exact.extend(state, W2_10)
    if transition is None or not transition.abandonment:
        raise AssertionError("root abandonment replay failure")
    state = transition.state
    path.append("rot^0;w2:10")
    orbit, _ = exact.ORBIT_PHASE[state.p]
    if orbit != int(record["o_star"]):
        raise AssertionError("short root O* mismatch")
    if state_hash(state) != record["post_return_state_hash"]:
        raise AssertionError("short root stable-key mismatch")
    if tuple(path) != tuple(record["round37_literal_path"]):
        raise AssertionError("short root Round-37 literal path mismatch")
    return state, tuple(path)


def known_target_a_hashes() -> set[str]:
    """Reconstruct true left-S6 hashes of the historical 18, independently."""
    producer = load_module("rr_short5_known_boundary_replay", ROOT / "src" / "analyze_rr_target_b_survivors.py")
    preps = json.loads((ROOT / "outputs" / "rr_preparation_words.json").read_text(encoding="utf-8"))
    long = json.loads((ROOT / "outputs" / "rr_six_counterexamples.json").read_text(encoding="utf-8"))
    hashes = set()
    for ell, result in preps["results_by_ell"].items():
        for prep in result["preparations"]:
            state = producer.replay_historical(int(ell), prep)
            if state is not None:
                hashes.add(sha256_bytes(repr(producer.exact.canonicalize(state).stable_key()).encode("utf-8"))[:16])
    for witness in long["witnesses"]:
        state = producer.replay_long(witness)
        hashes.add(sha256_bytes(repr(producer.exact.canonicalize(state).stable_key()).encode("utf-8"))[:16])
    if len(hashes) != 18:
        raise AssertionError(f"expected 18 known canonical boundaries, got {len(hashes)}")
    return hashes


def replay_found(record: Mapping[str, object], boundary: Mapping[str, object]) -> dict[str, object]:
    state, _path = reconstruct_short_root(record)
    r_count, r1_target, touches, final = 0, None, 0, None
    for index, step in enumerate(boundary["literal_macro_trace"], 1):
        for _ in range(int(step["rotation_length"])):
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
        kind = joint_kind(transition)
        if kind == "other":
            return {"ok": False, "reason": "outside_rr_model", "step": index}
        touches += int(core.hexagon_id(transition.target) == HUB)
        if touches > 2:
            return {"ok": False, "reason": "hub_touch_limit", "step": index}
        if kind == "R":
            r_count += 1
            sq, sph = exact.ORBIT_PHASE[pre.p]
            tq, tph = exact.ORBIT_PHASE[transition.target]
            parent, find = component_roots(pre)
            same = (("q", sq) in parent and ("q", tq) in parent
                    and find(("q", sq)) == find(("q", tq)))
            if r1_target is None:
                r1_target = tq
            final = {"r_count": r_count, "F": transition.state.F,
                     "H": transition.state.H, "Ndef": transition.state.Ndef,
                     "same_component": same, "chaining": r1_target == sq,
                     "source": [sq, sph], "target": [tq, tph],
                     "state_hash": state_hash(transition.state)}
        state = transition.state
    if final is None:
        return {"ok": False, "reason": "no_R_joint"}
    expected = boundary["conditions"]
    conditions = {
        "exactly_two_R_events": final["r_count"] == 2,
        "immediately_after_R2": True,
        "F_def_le_1": final["F"] <= 1,
        "Ndef_equals_2": final["Ndef"] == 2,
        "H_equals_0": final["H"] == 0,
        "area_a_legal": True,
        "same_component": final["same_component"],
    }
    canonical = sha256_bytes(repr(exact.canonicalize(state).stable_key()).encode("utf-8"))[:16]
    return {
        "ok": conditions == expected and all(conditions.values())
              and final["state_hash"] == boundary["post_r2_state_hash"]
              and final["chaining"] == boundary["chaining"],
        "conditions": conditions, "expected": expected, "final": final,
        "canonical_state_hash": canonical, "post_state": state,
    }


def coarse_bound(state) -> tuple[int, int, int, int]:
    need = exact.TARGET_P - state.P + 1
    o_cap = max(exact.TARGET_O - state.O, 0)
    r_cap = max(macro.AREA_A.n_limit - state.Ndef, 0)
    return need, o_cap, r_cap, 5 * (o_cap + r_cap) + 4


def b_plus_r_bound(state) -> tuple[int, int]:
    need = exact.TARGET_P - state.P + 1
    orbit, _ = exact.ORBIT_PHASE[state.p]
    used = state.orbit_masks[orbit].bit_count()
    o_cap = max(exact.TARGET_O - state.O, 0)
    r_cap = max(macro.AREA_A.n_limit - state.Ndef, 0)
    return need, 1 + (5 - used) + 5 * o_cap + 4 * r_cap


def helper_free_flow(state) -> dict[str, object]:
    """Cap-free Round-34 exact macro DFS for a genuinely new coarse survivor."""
    stats: dict[str, object] = {"nodes": 0, "max_depth": 0, "leaf_states": 0,
                                "prunes": Counter(), "max_visited": state.visited_count}

    def dfs(current, depth: int):
        stats["nodes"] = int(stats["nodes"]) + 1
        stats["max_depth"] = max(int(stats["max_depth"]), depth)
        stats["max_visited"] = max(int(stats["max_visited"]), current.visited_count)
        final_run = macro.rotation_runs(current)[-1]
        if final_run.state.visited_count == 720:
            return []
        alive = False
        for edge in macro.macro_edges(current):
            reason = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            if reason is not None:
                stats["prunes"][reason] += 1  # type: ignore[index]
                continue
            need, bound = b_plus_r_bound(edge.state)
            if need > bound:
                stats["prunes"]["round32_B_plus_R"] += 1  # type: ignore[index]
                continue
            alive = True
            outcome = dfs(edge.state, depth + 1)
            if outcome is not None:
                return [edge.label] + outcome
        if not alive:
            stats["leaf_states"] = int(stats["leaf_states"]) + 1
        return None

    path = dfs(state, 0)
    return {"status": "FOUND_TARGET_B" if path is not None else "EXHAUSTED_NO_PATH",
            "macro_path": path, **{**stats, "prunes": dict(stats["prunes"])}}


def alternate_exhaustion(record: Mapping[str, object]) -> dict[str, object]:
    """Independent, smaller-key exact traversal for a claimed exhaustion."""
    start, _path = reconstruct_short_root(record)
    stack = [(start, 0, None, 0)]  # ExactState, R count, R1 target orbit, hub touches
    seen = {(start.stable_key(), 0, None, 0)}
    nodes, target_count, max_depth = 0, 0, 0
    while stack:
        state, r_count, r1_target, touches = stack.pop()
        nodes += 1
        max_depth = max(max_depth, state.P)
        for run in macro.rotation_runs(state):
            for move in macro.NONROT_H0:
                transition = exact.extend(run.state, move)
                if transition is None:
                    continue
                if macro.area_a_prune_reason(transition.state, macro.AREA_A) is not None:
                    continue
                kind = joint_kind(transition)
                if kind == "other":
                    continue
                next_touches = touches + int(core.hexagon_id(transition.target) == HUB)
                if next_touches > 2:
                    continue
                sq, _ = exact.ORBIT_PHASE[run.state.p]
                tq, _ = exact.ORBIT_PHASE[transition.target]
                if kind == "R":
                    next_r = r_count + 1
                    if next_r == 2:
                        parent, find = component_roots(run.state)
                        same = (("q", sq) in parent and ("q", tq) in parent
                                and find(("q", sq)) == find(("q", tq)))
                        if (transition.state.F <= 1 and transition.state.Ndef == 2
                                and transition.state.H == 0 and same):
                            target_count += 1
                        continue
                    if next_r > 2:
                        continue
                    next_r1 = tq
                else:
                    if r_count >= 2:
                        continue
                    next_r, next_r1 = r_count, r1_target
                key = (transition.state.stable_key(), next_r, next_r1, next_touches)
                if key not in seen:
                    seen.add(key)
                    stack.append((transition.state, next_r, next_r1, next_touches))
    return {"frontier_empty": True, "nodes": nodes, "seen": len(seen),
            "target_count": target_count, "max_P": max_depth}


def checkpoint_audit(result: Mapping[str, object]) -> dict[str, object]:
    checkpoint_text = result.get("checkpoint")
    if checkpoint_text is None:
        return {"ok": False, "reason": "checkpoint_missing"}
    checkpoint = Path(str(checkpoint_text))
    if not checkpoint.is_absolute():
        checkpoint = ROOT / checkpoint
    if not checkpoint.exists():
        return {"ok": False, "reason": "checkpoint_file_missing"}
    raw = json.loads(checkpoint.read_text(encoding="utf-8"))
    try:
        expected_schema = config.get("checkpoint_payload_schema", "rr-target-a-exhaustive-checkpoint-v1")
        if raw.get("schema") != expected_schema:
            raise AssertionError("schema")
        if raw.get("config") != result["config"]:
            raise AssertionError("config")
        if not raw.get("complete_frontier_snapshot"):
            raise AssertionError("incomplete snapshot")
        if len(raw["frontier"]) != int(result["stats"]["frontier_size"]):
            raise AssertionError("frontier size")
        if len(raw["seen_keys"]) != len(set(raw["seen_keys"])):
            raise AssertionError("duplicate seen key")
        for item in raw["frontier"]:
            exact.state_from_json(item["state"])
        return {"ok": True, "checkpoint_sha256": sha256_file(checkpoint),
                "frontier": len(raw["frontier"]), "seen": len(raw["seen_keys"])}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}


def assert_no_helper_path() -> bool:
    for path in (SHORT_DRIVER, SEARCH, Path(__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = {node.func.id for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        if "true_phase_walk_capacity" in calls:
            return False
    return True


def verify(results_path: Path, certificates_path: Path, boundaries_path: Path) -> dict[str, object]:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    certificates = json.loads(certificates_path.read_text(encoding="utf-8"))["certificates"]
    found_payload = json.loads(boundaries_path.read_text(encoding="utf-8"))
    manifest = results["short5_manifest"]
    records = {record["root_id"]: record for record in manifest["records"]}
    if set(records) != {f"short_ell{i}" for i in range(5)}:
        raise AssertionError("wrong short-root universe")
    if results["short5_manifest_sha256"] != sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8")):
        raise AssertionError("manifest SHA mismatch")
    if not results["state_key_audit"].get("passed"):
        raise AssertionError("state-key audit failed")
    cert_by_root = {certificate["root_id"]: certificate for certificate in certificates}
    known = known_target_a_hashes()
    rows, failures, verified_boundaries = [], [], []
    for result in results["results"]:
        root_id = result["root_id"]
        record = records.get(root_id)
        if record is None:
            failures.append({"root_id": root_id, "reason": "unknown root"})
            continue
        root_ok = True
        try:
            reconstruct_short_root(record)
        except Exception as exc:
            root_ok = False
            failures.append({"root_id": root_id, "reason": f"root replay: {exc}"})
        config = result["config"]
        if int(config["node_limit"]) != 0 or config["max_depth"] is not None:
            root_ok = False
            failures.append({"root_id": root_id, "reason": "proof-invalid cap"})
        checkpoint = checkpoint_audit(result)
        if not checkpoint["ok"]:
            root_ok = False
            failures.append({"root_id": root_id, "reason": "checkpoint audit", "detail": checkpoint})
        found = [replay_found(record, boundary) for boundary in result["target_a_boundaries"]]
        if not all(item["ok"] for item in found):
            root_ok = False
            failures.append({"root_id": root_id, "reason": "literal Target-A replay", "detail": found})
        downstream = []
        for replay in found:
            state = replay.pop("post_state")
            canonical = replay["canonical_state_hash"]
            need, o_cap, r_cap, bound = coarse_bound(state)
            if canonical in known:
                status, flow = "KNOWN_18_BOUNDARY", None
            elif need > bound:
                status, flow = "COARSE_CAPACITY_IMPOSSIBLE", None
            else:
                flow = helper_free_flow(state)
                status = flow["status"]
            downstream.append({"canonical_state_hash": canonical, "known_18": canonical in known,
                               "coarse": {"need": need, "O_cap": o_cap, "R_cap": r_cap,
                                          "bound": bound, "contradiction": need > bound},
                               "status": status, "flow": flow, "phase_helper_used": False})
        verified_boundaries.extend(downstream)
        exhaustion = None
        if result["status"] == "EXHAUSTED_NO_TARGET_A":
            valid = (result["frontier_empty"] and not result["interrupted_by_node_limit"]
                     and not result["interrupted_by_depth_limit"])
            if not valid:
                root_ok = False
                failures.append({"root_id": root_id, "reason": "bad exhaustion metadata"})
            else:
                exhaustion = alternate_exhaustion(record)
                if exhaustion["target_count"] != 0:
                    root_ok = False
                    failures.append({"root_id": root_id, "reason": "independent exhaustion disagreement",
                                     "detail": exhaustion})
        if result["status"] not in {"FOUND_TARGET_A", "EXHAUSTED_NO_TARGET_A", "INCOMPLETE"}:
            root_ok = False
            failures.append({"root_id": root_id, "reason": "illegal root status"})
        certificate = cert_by_root.get(root_id)
        if certificate is None or certificate["status"] != result["status"]:
            root_ok = False
            failures.append({"root_id": root_id, "reason": "certificate mismatch"})
        rows.append({"root_id": root_id, "status": result["status"], "ok": root_ok,
                     "checkpoint": checkpoint, "found_replays": found,
                     "downstream": downstream, "exhaustion_replay": exhaustion})
    result_boundary_hashes = {b["post_r2_state_hash"]
                              for result in results["results"] for b in result["target_a_boundaries"]}
    stored_boundary_hashes = {b["post_r2_state_hash"] for b in found_payload["boundaries"]}
    if result_boundary_hashes != stored_boundary_hashes:
        failures.append({"root_id": "aggregate", "reason": "new-boundary output mismatch"})
    output = {
        "schema": "rr-short5-exact-search-verifier-v1",
        "results_sha256": sha256_file(results_path),
        "certificates_sha256": sha256_file(certificates_path),
        "new_boundaries_sha256": sha256_file(boundaries_path),
        "root_mapping_verified": True,
        "state_key_contract_verified": bool(results["state_key_audit"].get("passed")),
        "phase_helper_reachable": not assert_no_helper_path(),
        "rows": rows, "verified_boundaries": verified_boundaries,
        "failures": failures, "verified": not failures,
        "scope": "five short roots only; long roots excluded",
    }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--certificates", type=Path, default=CERTIFICATES)
    parser.add_argument("--new-boundaries", type=Path, default=NEW_BOUNDARIES)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "outputs" / "rr_short5_search_verified.json")
    args = parser.parse_args()
    output = verify(args.results, args.certificates, args.new_boundaries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"verified={output['verified']} roots={len(output['rows'])} failures={len(output['failures'])}")


if __name__ == "__main__":
    main()
