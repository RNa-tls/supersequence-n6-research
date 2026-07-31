#!/usr/bin/env python3
"""Independent literal verifier for the bounded R1-complete short-root pilot."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
PILOT = ROOT / "outputs" / "rr_short5_corrected_pilot.json"
EXPECTED_SCHEMA = "rr-target-a-exhaustive-checkpoint-v2-short-r1"
EXPECTED_UNIVERSE = "round37-short5-bare-abandonment-r1-complete-v2"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = load_module("rr_short5_pilot_verify_macro", WORK / "superperm_partial_f1_macro.py")
exact, core = macro.exact, macro.core
MOVE = {move.label: move for move in exact.ALL_MOVES}
W1 = macro.W1
W2_10 = MOVE["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root_state(record: Mapping[str, object]):
    state = exact.initial_state()
    for _ in range(int(record["root_ell"])):
        transition = exact.extend(state, W1)
        if transition is None:
            raise AssertionError("root rotation collision")
        state = transition.state
    transition = exact.extend(state, W2_10)
    if transition is None or not transition.abandonment:
        raise AssertionError("root abandonment failed")
    return transition.state


def parse_label(label: str) -> tuple[int, str]:
    rotation, joint = label.split(";", 1)
    return int(rotation.removeprefix("rot^").split("^", 1)[0]), joint


def expected_branch(events: list[dict[str, object]], completer: Mapping[str, object] | None) -> str:
    if completer is None:
        return "UNDECIDED"
    r1 = events[0] if events else None
    if (r1 is not None and completer["kind"] == "R"
            and int(completer["macro_index"]) == int(r1["macro_index"])):
        return "CH1"
    if (r1 is not None and completer["kind"] == "Z2"
            and int(r1["macro_index"]) < int(completer["macro_index"])):
        return "CH2"
    return "OTHER_OR_UNDECIDED"


def replay_frontier_item(record: Mapping[str, object], item: Mapping[str, object]) -> dict[str, object]:
    state = root_state(record)
    events: list[dict[str, object]] = []
    completer = None
    hub_touches = 0
    for index, step in enumerate(item["trace"], 1):
        label = str(step["label"])
        rotations, joint_label = parse_label(label)
        if rotations != int(step["rotation_length"]) or joint_label != str(step["joint"]):
            raise AssertionError("trace label mismatch")
        for _ in range(rotations):
            rotation = exact.extend(state, W1)
            if rotation is None:
                raise AssertionError("trace rotation collision")
            state = rotation.state
        pre = state
        transition = exact.extend(state, MOVE[joint_label])
        if transition is None:
            raise AssertionError("trace joint collision")
        source_orbit, source_phase = exact.ORBIT_PHASE[pre.p]
        target_orbit, target_phase = exact.ORBIT_PHASE[transition.target]
        kind = {(2, False, False): "Z2", (2, True, True): "Z2abandon",
                (3, False, False): "R", (3, False, True): "Z3"}.get(
                    (transition.move.weight, transition.abandonment, transition.new_orbit), "other")
        if kind == "R":
            events.append({"macro_index": index, "kind": kind, "source_orbit": source_orbit,
                           "source_phase": source_phase, "target_orbit": target_orbit,
                           "target_phase": target_phase})
        if core.hexagon_id(transition.target) == HUB:
            hub_touches += 1
            if completer is None:
                completer = {"macro_index": index, "kind": kind, "source_orbit": source_orbit,
                             "source_phase": source_phase, "target_orbit": target_orbit,
                             "target_phase": target_phase}
        state = transition.state
    stored_state = exact.state_from_json(item["state"])
    decoration = item["decoration"]
    state_ok = state.stable_key() == stored_state.stable_key()
    events_ok = events == decoration["r_events"]
    return {
        "state_ok": state_ok,
        "events_ok": events_ok,
        "r_count": len(events),
        "metadata": events,
        "hub_touches_ok": hub_touches == int(decoration["hub_touch_count"]),
        "completer_ok": completer == decoration["completer"],
        "branch_ok": expected_branch(events, completer) == decoration["branch"],
    }


def audit_checkpoint(record: Mapping[str, object], checkpoint_path: Path) -> dict[str, object]:
    raw = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    failures = []
    if raw.get("schema") != EXPECTED_SCHEMA:
        failures.append("schema")
    config = raw.get("config", {})
    if config.get("checkpoint_payload_schema") != EXPECTED_SCHEMA:
        failures.append("config payload schema")
    if config.get("root_universe") != EXPECTED_UNIVERSE:
        failures.append("root universe")
    if not raw.get("complete_frontier_snapshot"):
        failures.append("incomplete snapshot")
    replays = []
    for item in raw["frontier"]:
        replay = replay_frontier_item(record, item)
        if replay["r_count"] > 1:
            failures.append("R2 child enqueued")
        if not all(replay[key] for key in ("state_ok", "events_ok", "hub_touches_ok", "completer_ok", "branch_ok")):
            failures.append("frontier literal/decoration mismatch")
        replays.append(replay)
    r1_replays = [row for row in replays if row["r_count"] == 1]
    return {
        "path": str(checkpoint_path.relative_to(ROOT)),
        "sha256": sha256_file(checkpoint_path),
        "frontier_size": len(raw["frontier"]),
        "r1_frontier_states": len(r1_replays),
        "r1_metadata": [row["metadata"] for row in r1_replays],
        "all_r1_have_exactly_one_prior_event": all(row["r_count"] == 1 for row in r1_replays),
        "no_R2_child": not any(row["r_count"] > 1 for row in replays),
        "replays": replays,
        "failures": sorted(set(failures)),
        "verified": not failures,
    }


def verify(payload: Mapping[str, object]) -> dict[str, object]:
    record = next(row for row in payload["short5_manifest"]["records"]
                  if row["root_id"] == payload["selected_root"])
    seed_path = ROOT / payload["r1_seed"]["checkpoint"]["path"]
    pilot_path = ROOT / payload["pilot"]["checkpoint"]["path"]
    seed = audit_checkpoint(record, seed_path)
    pilot = audit_checkpoint(record, pilot_path)
    result = payload["pilot"]["result"]
    stats = result["stats"]
    failures = []
    if payload.get("classification") != "INCOMPLETE" or result.get("status") != "INCOMPLETE":
        failures.append("pilot status")
    if not result.get("interrupted_by_node_limit") or int(result["stats"]["frontier_size"]) < 1:
        failures.append("frontier/status mismatch")
    if int(stats.get("R1_transitions", 0)) < 1 or int(stats.get("post_R1_nodes", 0)) < 1:
        failures.append("R1 not traversed")
    if seed["r1_frontier_states"] < 1 or not seed["all_r1_have_exactly_one_prior_event"]:
        failures.append("R1 seed absent or malformed")
    if not seed["no_R2_child"] or not pilot["no_R2_child"]:
        failures.append("R2 child enqueued")
    if not payload["state_key_audit"].get("passed") or int(payload["state_key_audit"].get("r1_states_examined", 0)) < 1:
        failures.append("post-R1 key audit")
    if seed["failures"] or pilot["failures"]:
        failures.append("checkpoint replay")
    return {
        "schema": "rr-short5-corrected-pilot-verifier-v1",
        "selected_root": record["root_id"],
        "seed_checkpoint": seed,
        "pilot_checkpoint": pilot,
        "telemetry": {key: stats[key] for key in (
            "pre_R_nodes", "R1_transitions", "post_R1_nodes", "CH1_nodes", "CH2_nodes",
            "R2_candidate_edges", "Target_A_hits", "max_post_R1_depth",
            "unique_r1_decorated_keys", "pre_R_prunes", "post_R1_prunes")},
        "failures": failures,
        "verified": not failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=PILOT)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "outputs" / "rr_short5_corrected_pilot_verified.json")
    args = parser.parse_args()
    payload = json.loads(args.pilot.read_text(encoding="utf-8"))
    result = verify(payload)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"verified={result['verified']} failures={len(result['failures'])}")


if __name__ == "__main__":
    main()
