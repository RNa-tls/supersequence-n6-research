"""Independent read-only verifier for the short_ell0 Target-A scope audit."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rr = load("rr_scope_verify_engine", ROOT / "src" / "search_rr_target_a_exhaustive.py")
runner = load("rr_scope_verify_runner", ROOT / "src" / "run_rr_short_ell0_scope_audit.py")
short5 = load("rr_scope_verify_short5", ROOT / "src" / "search_rr_short5_exact.py")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, default=ROOT / "outputs" / "rr_short_ell0_prune_differential.json", nargs="?")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "rr_short_ell0_scope_audit_verified.json")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    record = payload["root"]
    safe = payload["target_a_safe_profile"]
    legacy = payload["legacy_area_a_q2_profile"]
    divergence = payload["first_o_exceeded_divergence"]
    checks = {
        "profiles_distinct": safe["config"]["prune_profile"] != legacy["config"]["prune_profile"],
        "safe_registry_has_scope_tags": all("scope" in row for row in rr.TARGET_A_PRUNE_REGISTRY),
        "q2_registry_not_target_a_registry": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE) != rr.registry_hash(rr.LEGACY_AREA_A_PROFILE),
        "safe_run_bounded_incomplete": safe["status"] == "INCOMPLETE" and not safe["frontier_empty"],
        "r2_failure_accounting": (
            sum(int(v) for v in safe["stats"].get("R2_primary_failures", {}).values()) +
            int(safe["stats"]["Target_A_hits"]) == int(safe["stats"]["R2_candidate_edges"])
        ),
        "old_v2_checkpoint_rejected": False,
        "divergence_literal_replay": False,
        "divergence_is_o_only": False,
    }
    manifest = short5.short_root_manifest(short5.short_root_records())
    extra = short5.config_extra(manifest)
    checkpoint = Path(payload["new_checkpoint"]["path"])
    # The checkpoint was produced by the Round-41 semantic engine.  Later
    # telemetry-only source edits deliberately change its source hash, so the
    # historical artifact must be parsed against its recorded identity rather
    # than falsely treated as a resumable current-engine checkpoint.
    raw_checkpoint = json.loads(checkpoint.read_text(encoding="utf-8"))
    checks["v3_checkpoint_readable"] = (
        raw_checkpoint.get("schema") == "rr-target-a-exhaustive-checkpoint-v3-short-r1-target-a" and
        raw_checkpoint.get("config", {}).get("prune_profile") == rr.TARGET_A_SAFE_PROFILE and
        bool(raw_checkpoint.get("complete_frontier_snapshot")) and
        len(raw_checkpoint.get("frontier", [])) == int(payload["new_checkpoint"]["frontier_size"])
    )
    checks["checkpoint_seen_count"] = len(raw_checkpoint.get("seen_keys", [])) == int(payload["new_checkpoint"]["seen_size"])
    old_v2 = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v2" / "short_ell0_medium.json"
    if old_v2.exists():
        try:
            # Any v2 payload must remain invalid for the current Target-A
            # schema; the precise current engine hash is immaterial here.
            current = rr.checkpoint_config(record, int(payload["node_limit"]), None, extra,
                                           prune_profile=rr.TARGET_A_SAFE_PROFILE)
            rr.load_checkpoint(old_v2, current)
        except ValueError:
            checks["old_v2_checkpoint_rejected"] = True
    if divergence["status"] == "EXACT_COUNTEREXAMPLE":
        state, dec = runner.replay_trace(record, divergence["literal_macro_trace"])
        child = rr.exact.state_from_json(divergence["child_state"])
        checks["divergence_literal_replay"] = state.stable_key() == child.stable_key()
        checks["divergence_is_o_only"] = (
            int(divergence["coordinate"]["O"]) > rr.exact.TARGET_O and
            divergence["legacy_verdict"] == f"{rr.LEGACY_AREA_A_PROFILE}:O_exceeded" and
            divergence["target_a_safe_verdict"] == "child"
        )
    else:
        checks["divergence_literal_replay"] = True
        checks["divergence_is_o_only"] = True
    result = {
        "schema": "rr-target-a-prune-scope-independent-verifier-v1",
        "input": str(args.input), "input_sha256": rr.sha256_file(args.input),
        "checks": checks, "passed": all(checks.values()),
        "grade": "independent read-only verification of bounded scope-audit artifacts",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
