#!/usr/bin/env python3
"""Independent read-only verifier for the Round-42 v3 medium run."""
from __future__ import annotations

import argparse
import importlib.util
import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import types
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v3.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


short5 = load("rr_medium_v3_verify_short5", ROOT / "src" / "search_rr_short5_exact.py")
runner = load("rr_medium_v3_verify_runner", ROOT / "src" / "run_rr_short_ell0_medium_v3.py")


def load_frozen_round42_engine():
    """Verify the historical checkpoint against the exact code it hashes.

    Later diagnostic-only instrumentation changes the source SHA by design;
    it must not make a valid Round-42 certificate unverifiable or tempt a
    caller to resume that checkpoint under changed code.
    """
    frozen = subprocess.run(
        ["git", "show", "785ddab:src/search_rr_target_a_exhaustive.py"],
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    module = types.ModuleType("rr_medium_v3_verify_frozen_round42")
    module.__file__ = str(ROOT / "src" / "search_rr_target_a_exhaustive.py")
    sys.modules[module.__name__] = module
    exec(compile(frozen, module.__file__, "exec"), module.__dict__)
    return module, hashlib.sha256(frozen).hexdigest()


rr, FROZEN_ENGINE_SHA256 = load_frozen_round42_engine()


def replay_r1(record, event: dict[str, object]) -> bool:
    state, dec = rr.initial_decoration(record)
    for item in event["literal_macro_trace"]:
        label = str(item["label"])
        edge = next((edge for edge, collision in rr.iter_raw_macro_candidates(state)
                     if collision is None and edge is not None and edge.label == label), None)
        if edge is None:
            return False
        dec_after = rr.advance_decoration(edge.run.state, edge.joint, dec)
        state_after = edge.state
        if edge.label == event["macro_label"] and dec.r_count == 0 and dec_after.r_count == 1:
            event_id, regenerated = rr.r1_event_export(edge, dec, dec_after, tuple(event["literal_macro_trace"][:-1]))
            return event_id == event["event_id"] and regenerated == event
        state, dec = state_after, dec_after
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OUTPUT)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "rr_short_ell0_medium_v3_verified.json")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = payload["result"]
    stats = result["stats"]
    failures: list[str] = []
    records = short5.short_root_records()
    record = next(row for row in records if row["root_id"] == "short_ell0")
    checkpoint = ROOT / payload["final_checkpoint"]["path"]
    raw = json.loads(checkpoint.read_text(encoding="utf-8"))
    # The checkpoint is a historical certificate.  Its embedded config is its
    # identity; recomputing manifest/source hashes from a newer worktree would
    # be a category error.  Validate the frozen code hash directly instead.
    config = raw.get("config", {})
    source_key = "src\\search_rr_target_a_exhaustive.py"
    if result["config"] != config or payload.get("prune_profile") != rr.TARGET_A_SAFE_PROFILE:
        failures.append("Target-A-safe config identity")
    if config["checkpoint_payload_schema"] != "rr-target-a-exhaustive-checkpoint-v3-short-r1-target-a":
        failures.append("v3 checkpoint schema")
    if config.get("engine_hashes", {}).get(source_key) != FROZEN_ENGINE_SHA256 or \
            config.get("recognizer_hash") != FROZEN_ENGINE_SHA256:
        failures.append("frozen Round-42 engine hash")
    if payload.get("prune_registry_hash") != rr.registry_hash(rr.TARGET_A_SAFE_PROFILE):
        failures.append("Target-A registry hash")
    if raw.get("schema") != config["checkpoint_payload_schema"] or raw.get("config") != config:
        failures.append("checkpoint config/schema")
    if not raw.get("complete_frontier_snapshot"):
        failures.append("checkpoint incomplete snapshot")
    if len(raw["frontier"]) != int(stats["frontier_size"]):
        failures.append("frontier count")
    if len(raw["seen_keys"]) != len(set(raw["seen_keys"])):
        failures.append("duplicate decorated state key")
    r_frontier = Counter(len(item["decoration"]["r_events"]) for item in raw["frontier"])
    claimed = {int(key): value for key, value in payload["final_checkpoint"]["frontier_r_count_distribution"].items()}
    if dict(r_frontier) != claimed:
        failures.append("frontier r-count distribution")
    disabled_tokens = ("P_exceeded", "O_exceeded", "N_exceeded", "final_D", "remaining_",
                       "future_orbit", "area_a:", rr.LEGACY_AREA_A_PROFILE)
    disabled_seen = {reason: count for reason, count in stats["prunes"].items()
                     if any(token in reason for token in disabled_tokens)}
    if disabled_seen or any(value != 0 for value in payload["disabled_prune_counts"].values()):
        failures.append("completion-only prune enabled")
    if payload.get("enabled_prune_counts") != runner.enabled_prune_counts(stats):
        failures.append("enabled-prune count ledger")
    outcomes = stats["R2_outcomes"]
    if set(outcomes) != set(rr.R2_OUTCOME_VOCABULARY):
        failures.append("R2 outcome vocabulary")
    if sum(int(value) for value in outcomes.values()) != int(stats["R2_candidate_edges"]):
        failures.append("R2 outcome partition")
    if int(outcomes["TARGET_A_HIT"]) != int(stats["Target_A_hits"]):
        failures.append("Target-A/R2 outcome count")
    event_failures = [event_id for event_id, event in stats["R1_events"].items()
                      if not replay_r1(record, event)]
    if event_failures:
        failures.append("R1 metadata literal replay")
    # A same-limit resume in a temporary copy must preserve the exact
    # frontier/memo snapshot; it may append a checkpoint lineage item only.
    with tempfile.TemporaryDirectory() as folder:
        trial = Path(folder) / "resume.json"
        shutil.copy2(checkpoint, trial)
        before = json.loads(trial.read_text(encoding="utf-8"))
        saved_config_factory = rr.checkpoint_config
        # `search_root` otherwise derives a config from the *current* manifest
        # filesystem.  Bind it to the historical certificate only for this
        # copied, same-limit replay; no on-disk source checkpoint is modified.
        rr.checkpoint_config = lambda *_args, **_kwargs: dict(config)
        try:
            resumed = rr.search_root(record, node_limit=int(result["config"]["node_limit"]), checkpoint=trial,
                                     checkpoint_every=1, resume=trial,
                                     prune_profile=rr.TARGET_A_SAFE_PROFILE)
        finally:
            rr.checkpoint_config = saved_config_factory
        after = json.loads(trial.read_text(encoding="utf-8"))
        if before["frontier"] != after["frontier"] or before["seen_keys"] != after["seen_keys"]:
            failures.append("checkpoint/resume equivalence")
        if resumed["status"] != "INCOMPLETE" or not resumed["interrupted_by_node_limit"]:
            failures.append("same-limit resume status")
    if result["status"] == "INCOMPLETE":
        if result["frontier_empty"] or not result["interrupted_by_node_limit"]:
            failures.append("incomplete frontier/status")
    elif result["status"] == "EXHAUSTED_NO_TARGET_A":
        if not result["frontier_empty"]:
            failures.append("exhaustion frontier/status")
    elif result["status"] != "FOUND_TARGET_A":
        failures.append("unknown status")
    verification = {
        "schema": "rr-short-ell0-medium-v3-independent-verifier-v1",
        "input": str(args.input), "input_sha256": rr.sha256_file(args.input),
        "checkpoint": {"path": str(checkpoint.relative_to(ROOT)), "sha256": rr.sha256_file(checkpoint),
                       "frontier_r_count_distribution": dict(r_frontier)},
        "frozen_engine": {"commit": "785ddab", "sha256": FROZEN_ENGINE_SHA256},
        "r1_events_verified": len(stats["R1_events"]), "r1_event_failures": event_failures,
        "r2_outcome_ledger": outcomes, "disabled_prunes_observed": disabled_seen,
        "failures": sorted(set(failures)), "verified": not failures,
    }
    args.output.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    print(f"verified={verification['verified']} failures={len(verification['failures'])}")
    if not verification["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
