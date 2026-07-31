#!/usr/bin/env python3
"""Read-only independent verifier for the corrected ``short_ell0`` medium run."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v2.json"
SOURCE = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v2" / "short_ell0_pilot.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


short5 = load_module("rr_short_ell0_medium_verify_short5", ROOT / "src" / "search_rr_short5_exact.py")
pilot_verify = load_module("rr_short_ell0_medium_verify_pilot", ROOT / "src" / "verify_rr_short5_corrected_pilot.py")
target_verify = load_module("rr_short_ell0_medium_verify_target", ROOT / "src" / "verify_rr_short5_search.py")
rr = short5.rr


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(payload: Mapping[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if payload.get("source_checkpoint_v2_only") != str(SOURCE.relative_to(ROOT)):
        failures.append("source checkpoint is not the fixed v2 pilot")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if source.get("schema") != "rr-target-a-exhaustive-checkpoint-v2-short-r1":
        failures.append("source checkpoint schema")
    migration = payload.get("migration", {})
    if migration.get("source_sha256") != sha256_file(SOURCE):
        failures.append("source checkpoint SHA")
    target_path = ROOT / str(payload["final_checkpoint"]["path"])
    if not target_path.exists():
        failures.append("final checkpoint missing")
        return {"schema": "rr-short-ell0-medium-v2-verifier-v1", "verified": False, "failures": failures}
    raw = json.loads(target_path.read_text(encoding="utf-8"))
    records = short5.short_root_records()
    record = next(row for row in records if row["root_id"] == "short_ell0")
    manifest = short5.short_root_manifest(records)
    extra = short5.config_extra(manifest)
    result = payload["result"]
    expected = rr.checkpoint_config(record, int(result["config"]["node_limit"]), None, extra)
    if raw.get("schema") != "rr-target-a-exhaustive-checkpoint-v2-short-r1":
        failures.append("final checkpoint schema")
    if raw.get("config") != expected or result.get("config") != expected:
        failures.append("current v2 config identity")
    if not raw.get("complete_frontier_snapshot"):
        failures.append("incomplete checkpoint snapshot")
    if len(raw["frontier"]) != int(result["stats"]["frontier_size"]):
        failures.append("frontier cardinality")
    if len(raw["seen_keys"]) != len(set(raw["seen_keys"])):
        failures.append("duplicate canonical key")
    frontier_r = Counter()
    replays = []
    for item in raw["frontier"]:
        replay = pilot_verify.replay_frontier_item(record, item)
        replays.append(replay)
        frontier_r[int(replay["r_count"])] += 1
        if replay["r_count"] > 1:
            failures.append("R2 child enqueued")
        if not all(replay[key] for key in ("state_ok", "events_ok", "hub_touches_ok", "completer_ok", "branch_ok")):
            failures.append("frontier literal/decorated replay")
    claimed_r = {int(key): value for key, value in payload["final_checkpoint"]["frontier_r_count_distribution"].items()}
    if dict(sorted(frontier_r.items())) != dict(sorted(claimed_r.items())):
        failures.append("frontier r-count telemetry")
    stats = result["stats"]
    required = ("pre_R_nodes", "post_R1_nodes", "R1_transitions", "unique_r1_decorated_keys",
                "R2_candidate_edges", "Target_A_hits", "CH1_events", "CH2_events",
                "provisional_CH0_events", "hub_completions_before_R1", "hub_completions_after_R1",
                "Phi_at_R1", "M_at_R1", "steps_since_R1_expanded", "post_R1_prunes",
                "max_post_R1_depth")
    missing = [key for key in required if key not in stats]
    if missing:
        failures.append("missing telemetry: " + ", ".join(missing))
    if int(stats.get("R1_transitions", 0)) < 1 or int(stats.get("post_R1_nodes", 0)) < 1:
        failures.append("no post-R1 traversal")
    state_key = payload.get("state_key_status", {})
    if state_key.get("status") != "exhaustive tested-universe equivalence" or "not a theorem" not in str(state_key.get("scope")):
        failures.append("state-key scope label")
    audit = state_key.get("audit", {})
    if not audit.get("passed") or int(audit.get("r1_states_examined", 0)) < 1:
        failures.append("post-R1 state-key audit")
    if result["status"] == "INCOMPLETE":
        if not result["interrupted_by_node_limit"] or result["frontier_empty"]:
            failures.append("incomplete status/frontier")
    elif result["status"] == "EXHAUSTED_NO_TARGET_A":
        if not result["frontier_empty"] or result["interrupted_by_node_limit"]:
            failures.append("exhaustion status/frontier")
    elif result["status"] != "FOUND_TARGET_A":
        failures.append("unknown result status")
    boundary_replays = []
    for boundary in result["target_a_boundaries"]:
        replay = target_verify.replay_found(record, boundary)
        boundary_replays.append({key: value for key, value in replay.items() if key != "post_state"})
        if not replay["ok"]:
            failures.append("Target-A literal replay")
    if int(stats.get("Target_A_hits", 0)) != len(result["target_a_boundaries"]):
        failures.append("Target-A count")
    return {
        "schema": "rr-short-ell0-medium-v2-verifier-v1",
        "output_sha256": sha256_file(Path(str(args_input_path))),
        "checkpoint": {"path": str(target_path.relative_to(ROOT)), "sha256": sha256_file(target_path),
                       "frontier_size": len(raw["frontier"]), "frontier_r_count_distribution": dict(sorted(frontier_r.items()))},
        "r1_frontier_states": frontier_r.get(1, 0), "frontier_replays_checked": len(replays),
        "target_a_replays": boundary_replays, "failures": sorted(set(failures)), "verified": not failures,
    }


def main() -> None:
    global args_input_path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OUTPUT)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "rr_short_ell0_medium_v2_verified.json")
    args = parser.parse_args()
    args_input_path = args.input
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = verify(payload)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"verified={result['verified']} failures={len(result['failures'])}")


if __name__ == "__main__":
    main()
