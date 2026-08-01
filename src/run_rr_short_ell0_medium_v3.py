#!/usr/bin/env python3
"""Round 42: medium semantic-Target-A continuation for ``short_ell0``.

This driver resumes only the v3, Target-A-safe 250-node pilot.  The source
checkpoint is immutable.  A hash-bound migration changes only the node cap,
current instrumentation version, and additive telemetry after replaying the
pilot in memory and proving the old/current live-frontier successor signatures
agree.  It never enables the Area-A/Q2 completion bundle.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v3_target_a" /
          "short_ell0_scope_audit.json")
TARGET = (ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v3" /
          "short_ell0_medium.json")
OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v3.json"
DIFFERENTIAL = ROOT / "outputs" / "rr_short_ell0_v2_v3_differential.json"
REPORT = ROOT / "research" / "RR_SHORT_ELL0_MEDIUM_V3_TARGET_A_CODEX.md"
ROUND41_REV = "d90b69a"
V2_OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v2.json"
V2_CHECKPOINT = (ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v2" /
                 "short_ell0_medium.json")
SCOPE_DIFFERENTIAL = ROOT / "outputs" / "rr_short_ell0_prune_differential.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


short5 = load_module("rr_short_ell0_medium_v3_short5", ROOT / "src" / "search_rr_short5_exact.py")
rr = short5.rr


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(temporary, path)


def git_show(revision: str, name: str) -> bytes:
    completed = subprocess.run(["git", "show", f"{revision}:{name}"], cwd=ROOT, check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return completed.stdout


def old_engine() -> object:
    source = git_show(ROUND41_REV, "src/search_rr_target_a_exhaustive.py")
    module = types.ModuleType("rr_short_ell0_v3_source_engine")
    module.__file__ = str(ROOT / "src" / "search_rr_target_a_exhaustive.py")
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def record_for_ell0() -> dict[str, object]:
    rows = [row for row in short5.short_root_records() if row["root_id"] == "short_ell0"]
    if len(rows) != 1:
        raise AssertionError("short_ell0 root mapping is not unique")
    return rows[0]


def projection(stats: Mapping[str, object]) -> dict[str, object]:
    """Counters invariant under purely additive telemetry instrumentation."""
    names = (
        "expanded", "generated_edges", "memo_hits", "prunes", "CH1_nodes", "CH2_nodes",
        "undecided_nodes", "other_nodes", "branch_transitions", "max_macro_depth",
        "pre_R_nodes", "post_R1_nodes", "R1_transitions", "R2_candidate_edges",
        "Target_A_hits", "pre_R_prunes", "post_R1_prunes", "max_post_R1_depth",
        "unique_r1_decorated_keys",
    )
    # Prior v3 stored primary recognizer labels before the exhaustive outcome
    # ledger was introduced.  The exact R2 edge count itself is retained.
    return {name: stats.get(name) for name in names}


def source_validation(record: Mapping[str, object], source_raw: Mapping[str, object], extra: Mapping[str, object]) -> dict[str, object]:
    config = source_raw.get("config", {})
    if source_raw.get("schema") != "rr-target-a-exhaustive-checkpoint-v3-short-r1-target-a":
        raise AssertionError("source is not a v3 Target-A-safe checkpoint")
    if config.get("root_id") != "short_ell0" or int(config.get("node_limit", -1)) != 250:
        raise AssertionError("source is not the committed short_ell0 250-node pilot")
    if config.get("prune_profile") != rr.TARGET_A_SAFE_PROFILE:
        raise AssertionError("source checkpoint used a non-semantic prune profile")
    if config.get("prune_registry_hash") != rr.registry_hash(rr.TARGET_A_SAFE_PROFILE):
        raise AssertionError("source checkpoint has a different Target-A registry")
    if not source_raw.get("complete_frontier_snapshot"):
        raise AssertionError("source does not certify a complete frontier snapshot")

    old = old_engine()
    old_hash = sha256_bytes(git_show(ROUND41_REV, "src/search_rr_target_a_exhaustive.py"))
    search_key = str((ROOT / "src" / "search_rr_target_a_exhaustive.py").relative_to(ROOT))
    if config.get("engine_hashes", {}).get(search_key) != old_hash:
        raise AssertionError("source checkpoint does not identify Round-41 engine")
    current_hashes = rr.code_hashes()
    for key, value in config["engine_hashes"].items():
        if key != search_key and current_hashes.get(key) != value:
            raise AssertionError(f"non-search engine differs from source checkpoint: {key}")
    mismatches = []
    for index, item in enumerate(source_raw["frontier"]):
        old_state = old.exact.state_from_json(item["state"])
        old_dec = old.Decoration.from_json(item["decoration"])
        state = rr.exact.state_from_json(item["state"])
        dec = rr.Decoration.from_json(item["decoration"])
        if repr(old.successor_signature(old_state, old_dec)) != repr(rr.successor_signature(state, dec)):
            mismatches.append(index)
    if mismatches:
        raise RuntimeError("STATE_KEY_UNSOUND: changed successor signature on source frontier")

    # Replaying the 250-node prefix creates only additive telemetry (R1 event
    # records and the total R2 outcome ledger).  Its semantic counters must
    # match the immutable pilot before being copied into the migrated payload.
    replay = rr.search_root(record, node_limit=250, checkpoint=None,
                            checkpoint_config_extra=extra,
                            prune_profile=rr.TARGET_A_SAFE_PROFILE)
    if replay["status"] != "INCOMPLETE" or not replay["interrupted_by_node_limit"]:
        raise AssertionError("pilot telemetry replay did not stop at its cap")
    if projection(replay["stats"]) != projection(source_raw["stats"]):
        raise AssertionError("telemetry replay changed the 250-node traversal")
    return {
        "source_engine_revision": ROUND41_REV,
        "source_engine_sha256": old_hash,
        "current_engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "source_frontier_states_compared": len(source_raw["frontier"]),
        "successor_signature_mismatches": mismatches,
        "replayed_prefix_expansions": replay["stats"]["expanded"],
        "additive_telemetry": {
            "R1_events": replay["stats"]["R1_events"],
            "R2_outcomes": replay["stats"]["R2_outcomes"],
            "R2_primary_failures": replay["stats"]["R2_primary_failures"],
            "event_order_class_events": replay["stats"]["event_order_class_events"],
        },
    }


def migrate_checkpoint(source_raw: Mapping[str, object], source_sha: str, config: Mapping[str, object],
                       additive: Mapping[str, object], target: Path) -> dict[str, object]:
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing v3 medium checkpoint: {target}")
    payload = copy.deepcopy(dict(source_raw))
    payload["schema"] = rr.checkpoint_payload_schema(config)
    payload["config"] = dict(config)
    payload["stats"] = dict(source_raw["stats"])
    payload["stats"].update(additive)
    payload["checkpoint_lineage"] = list(source_raw["checkpoint_lineage"]) + [source_sha]
    payload["complete_frontier_snapshot"] = True
    atomic_json(target, payload)
    rr.load_checkpoint(target, config)
    target_raw = json.loads(target.read_text(encoding="utf-8"))
    if target_raw["frontier"] != source_raw["frontier"] or target_raw["seen_keys"] != source_raw["seen_keys"]:
        raise AssertionError("checkpoint migration changed frontier or memo set")
    return {
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": source_sha,
        "target": str(target.relative_to(ROOT)), "initial_target_sha256": sha256_file(target),
        "source_expanded": source_raw["stats"]["expanded"],
        "source_frontier": len(source_raw["frontier"]), "source_seen": len(source_raw["seen_keys"]),
        "frontier_and_memo_preserved": True,
    }


def checkpoint_summary(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    r_counts = Counter(len(item["decoration"]["r_events"]) for item in raw["frontier"])
    return {
        "path": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
        "schema": raw["schema"], "frontier_size": len(raw["frontier"]),
        "seen_size": len(raw["seen_keys"]),
        "frontier_r_count_distribution": dict(sorted(r_counts.items())),
        "complete_frontier_snapshot": bool(raw.get("complete_frontier_snapshot")),
    }


def state_distributions(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    o_hist: Counter[int] = Counter()
    p_hist: Counter[int] = Counter()
    for text in raw["seen_keys"]:
        state_key = rr.decode_key(text)[0]
        # stable_key = (p, sparse_hex, sparse_orbits, F, S, H)
        sparse_orbits = state_key[2]
        o_hist[len(sparse_orbits)] += 1
        p_hist[sum(int(mask).bit_count() for _orbit, mask in sparse_orbits)] += 1
    return {"O_distribution_seen_states": dict(sorted(o_hist.items())),
            "P_distribution_seen_states": dict(sorted(p_hist.items()))}


def v2_v3_differential(v3_checkpoint: Path, result: Mapping[str, object]) -> dict[str, object]:
    old = json.loads(V2_OUTPUT.read_text(encoding="utf-8")) if V2_OUTPUT.exists() else None
    raw_v3 = json.loads(v3_checkpoint.read_text(encoding="utf-8"))
    v3_keys = set(raw_v3["seen_keys"])
    v2_keys: set[str] | None = None
    if V2_CHECKPOINT.exists():
        v2_keys = set(json.loads(V2_CHECKPOINT.read_text(encoding="utf-8"))["seen_keys"])
    scope = json.loads(SCOPE_DIFFERENTIAL.read_text(encoding="utf-8"))
    return {
        "schema": "rr-short-ell0-v2-v3-differential-v1",
        "warning": "Different prune profiles induce different traversal samples; hit rates are not comparable.",
        "first_divergence": scope["first_o_exceeded_divergence"],
        "v2_summary": None if old is None else {
            "expanded": old["result"]["stats"]["expanded"],
            "frontier": old["result"]["stats"]["frontier_size"],
            "R1_transitions": old["result"]["stats"]["R1_transitions"],
            "R2_candidates": old["result"]["stats"]["R2_candidate_edges"],
            "O_exceeded_prunes": old["result"]["stats"]["prunes"].get("area_a:O_exceeded", 0),
        },
        "v3_summary": {
            "expanded": result["stats"]["expanded"], "frontier": result["stats"]["frontier_size"],
            "R1_transitions": result["stats"]["R1_transitions"],
            "R2_candidates": result["stats"]["R2_candidate_edges"],
            "Target_A_hits": result["stats"]["Target_A_hits"],
        },
        "v3_seen_state_distribution": state_distributions(v3_checkpoint),
        "seen_key_comparison": None if v2_keys is None else {
            "v2_count": len(v2_keys), "v3_count": len(v3_keys),
            "extra_states_admitted_by_v3": len(v3_keys - v2_keys),
            "v2_only_states": len(v2_keys - v3_keys),
            "intersection": len(v2_keys & v3_keys),
            "v2_frontier_hash": sha256_bytes("\n".join(sorted(v2_keys)).encode("utf-8")),
            "v3_frontier_hash": sha256_bytes("\n".join(sorted(v3_keys)).encode("utf-8")),
        },
    }


def assert_disabled_prunes_zero(stats: Mapping[str, object]) -> dict[str, int]:
    disabled_tokens = ("P_exceeded", "O_exceeded", "N_exceeded", "final_D", "remaining_",
                       "future_orbit", "area_a:", rr.LEGACY_AREA_A_PROFILE)
    observed = {reason: int(count) for reason, count in stats.get("prunes", {}).items()
                if any(token in reason for token in disabled_tokens)}
    if observed:
        raise AssertionError(f"completion-only prune leaked into Target-A run: {observed}")
    return {name: 0 for name in (
        "P_exceeded", "O_exceeded", "Ndef_cap", "D4_reachability",
        "Phi_window_capacity", "future_orbit_credit",
    )}


def enabled_prune_counts(stats: Mapping[str, object]) -> dict[str, int]:
    prunes = stats.get("prunes", {})
    return {
        "exact_permutation_collision": int(prunes.get("exact_permutation_collision", 0)),
        "F_exceeded": int(prunes.get(f"{rr.TARGET_A_SAFE_PROFILE}:F_exceeded", 0)),
        "H_positive": int(prunes.get(f"{rr.TARGET_A_SAFE_PROFILE}:H_positive", 0)),
        "F1_fragment_normal_form_impossible": int(
            prunes.get(f"{rr.TARGET_A_SAFE_PROFILE}:F1_fragment_normal_form_impossible", 0)),
        "rr_R_budget": int(prunes.get("rr_R_budget_exceeded", 0)),
        "hub_touch_count": int(prunes.get("hub_touch_count_exceeded", 0)),
    }


def write_report(payload: Mapping[str, object]) -> None:
    result = payload["result"]
    stats = result["stats"]
    lines = [
        "# Round 42: `short_ell0` medium Target-A-safe v3 run",
        "",
        f"Status: **{result['status']}**.  The positive node cap makes this diagnostic only unless the frontier is empty.",
        "",
        "## Scope",
        "",
        "- Resumed only the immutable semantic v3 250-node pilot.",
        "- No v1/v2 checkpoint and no other root was used.",
        "- `target_a_semantic_v1` is the only enabled profile; Area-A/Q2 completion gates are disabled.",
        "",
        "## Telemetry",
        "",
        "| quantity | value |", "|---|---:|",
    ]
    rows = [
        ("expansions", stats["expanded"]), ("frontier", stats["frontier_size"]),
        ("pre-R / post-R1 nodes", f"{stats['pre_R_nodes']} / {stats['post_R1_nodes']}"),
        ("R1 transitions / exported events", f"{stats['R1_transitions']} / {len(stats['R1_events'])}"),
        ("R2 candidates / Target-A hits", f"{stats['R2_candidate_edges']} / {stats['Target_A_hits']}"),
        ("max depth / max post-R1 depth", f"{stats['max_macro_depth']} / {stats['max_post_R1_depth']}"),
        ("frontier r-counts", payload["final_checkpoint"]["frontier_r_count_distribution"]),
    ]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    lines += [
        "", "## Exact enabled-prune counts", "",
        f"`{payload['enabled_prune_counts']}`", "",
        f"Additional exact/model exits: `{stats['prunes']}`", "",
        "Completion-only gates are asserted absent: " + repr(payload["disabled_prune_counts"]),
        "", "## R2 outcome ledger", "", f"`{stats['R2_outcomes']}`", "",
        "`wrong_Ndef` is intentionally zero: Ndef is not a Target-A condition.  It remains in the fixed vocabulary to make this distinction auditable.",
        "", "## Differential", "",
        "The v2/v3 comparison is descriptive only because the two profiles traverse different samples.  The first O-only divergent literal state and seen-state P/O distributions are in the JSON ledger.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--additional-expansions", type=int, default=100_000)
    parser.add_argument("--checkpoint-every", type=int, default=5_000)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--checkpoint", type=Path, default=TARGET)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--differential", type=Path, default=DIFFERENTIAL)
    parser.add_argument("--resume-existing", action="store_true",
                        help="resume only the committed medium v3 checkpoint; never consume .tmp")
    args = parser.parse_args()
    if args.additional_expansions < 1 or args.checkpoint_every < 1:
        raise ValueError("positive additional-expansions and checkpoint-every are required")
    if args.source.resolve() != SOURCE.resolve() or args.checkpoint.resolve() != TARGET.resolve():
        raise ValueError("this driver has one fixed v3 source and one fresh v3 target path")
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    if TARGET.exists() and not args.resume_existing:
        raise FileExistsError("medium v3 checkpoint already exists; use --resume-existing after validation")

    record = record_for_ell0()
    records = short5.short_root_records()
    manifest = short5.short_root_manifest(records)
    extra = short5.config_extra(manifest)
    source_raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    validation = source_validation(record, source_raw, extra)
    source_sha = sha256_file(SOURCE)
    total_limit = int(source_raw["stats"]["expanded"]) + args.additional_expansions
    config = rr.checkpoint_config(record, total_limit, None, extra,
                                  prune_profile=rr.TARGET_A_SAFE_PROFILE)
    if TARGET.exists():
        # A tool/supervisor interruption can leave a newer ``.tmp`` payload.
        # It is evidence only, never an input.  Preserve it before the next
        # atomic checkpoint write can reuse that filename.
        temporary = TARGET.with_suffix(TARGET.suffix + ".tmp")
        preserved_tmp = None
        if temporary.exists():
            preserved_tmp = TARGET.with_suffix(TARGET.suffix + ".interrupted.tmp")
            if preserved_tmp.exists():
                raise FileExistsError(f"refusing to overwrite preserved atomic payload: {preserved_tmp}")
            shutil.copy2(temporary, preserved_tmp)
        rr.load_checkpoint(TARGET, config)
        current = json.loads(TARGET.read_text(encoding="utf-8"))
        migration = {
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": source_sha,
            "target": str(TARGET.relative_to(ROOT)), "resumed_from_committed_checkpoint": True,
            "committed_expanded": current["stats"]["expanded"],
            "committed_frontier": len(current["frontier"]),
            "preserved_noninput_tmp": None if preserved_tmp is None else str(preserved_tmp.relative_to(ROOT)),
        }
    else:
        migration = migrate_checkpoint(source_raw, source_sha, config, validation["additive_telemetry"], TARGET)

    state_key = short5.audit_short_state_key(records)
    if not state_key["passed"]:
        raise RuntimeError("STATE_KEY_UNSOUND")
    result = rr.search_root(record, node_limit=total_limit, checkpoint=TARGET,
                            checkpoint_every=args.checkpoint_every, resume=TARGET,
                            checkpoint_config_extra=extra, prune_profile=rr.TARGET_A_SAFE_PROFILE)
    disabled = assert_disabled_prunes_zero(result["stats"])
    enabled = enabled_prune_counts(result["stats"])
    final_checkpoint = checkpoint_summary(TARGET)
    if result["status"] == "INCOMPLETE" and result["frontier_empty"]:
        raise AssertionError("incomplete result unexpectedly has empty frontier")
    if result["status"] != "INCOMPLETE" and not result["frontier_empty"]:
        raise AssertionError("completed result has nonempty frontier")
    if sum(result["stats"]["R2_outcomes"].values()) != result["stats"]["R2_candidate_edges"]:
        raise AssertionError("R2 ledger is not a partition")
    differential = v2_v3_differential(TARGET, result)
    atomic_json(args.differential, differential)
    payload: dict[str, object] = {
        "schema": "rr-short-ell0-medium-v3-target-a-result-v1",
        "classification": result["status"],
        "scope": "short_ell0 only; semantic Target-A traversal; 100,000 additional expansions after v3 pilot unless naturally exhausted",
        "attribution": {"search_implementation": "CODEX", "mathematical_envelope_facts": "CLAUDE, CODEX_VERIFIED", "new_discovered_boundaries": "CODEX_FINDING"},
        "prune_profile": rr.TARGET_A_SAFE_PROFILE,
        "prune_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
        "source_validation": validation, "migration": migration,
        "result": result, "final_checkpoint": final_checkpoint,
        "disabled_prune_counts": disabled,
        "enabled_prune_counts": enabled,
        "state_key_status": {"status": "exhaustive tested-universe equivalence", "audit": state_key,
                             "scope": "finite tested universe, not a theorem"},
        "phase_helper_used": False,
        "differential_path": str(args.differential.relative_to(ROOT)),
    }
    atomic_json(args.output, payload)
    write_report(payload)
    print(json.dumps({"status": result["status"], "expanded": result["stats"]["expanded"],
                      "frontier": result["stats"]["frontier_size"], "r1": result["stats"]["R1_transitions"],
                      "r2": result["stats"]["R2_candidate_edges"], "target_a": result["stats"]["Target_A_hits"]}, sort_keys=True))


if __name__ == "__main__":
    main()
