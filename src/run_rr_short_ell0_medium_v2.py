#!/usr/bin/env python3
"""Round 40: bounded medium continuation from the corrected ell0 v2 pilot.

This program never reads a pre-R/v1 checkpoint and never names any root
other than ``short_ell0``.  The old 250-expansion checkpoint is hash-bound to
the pilot's node limit, so changing the limit requires an explicit *identity
preserving* v2 lineage migration: the literal frontier, memo set, traces,
boundaries, and all semantic counters are asserted byte-for-byte unchanged;
only the config identity and additive telemetry fields change.

The positive 100,000-additional-expansion budget makes this a diagnostic
run.  Its status is ``INCOMPLETE`` unless its exact frontier naturally empties.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v2" / "short_ell0_pilot.json"
TARGET = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v2" / "short_ell0_medium.json"
OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v2.json"
REPORT = ROOT / "research" / "RR_SHORT_ELL0_MEDIUM_RUN_CODEX.md"
ROUND35 = ROOT / "src" / "search_rr_target_a_exhaustive.py"
PILOT_REV = "5e13395"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


short5 = load_module("rr_short_ell0_medium_short5", ROOT / "src" / "search_rr_short5_exact.py")
rr = short5.rr


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_sha(payload: Mapping[str, object]) -> str:
    return sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(temporary, path)


def git_show(revision: str, name: str) -> bytes:
    completed = subprocess.run(["git", "show", f"{revision}:{name}"], cwd=ROOT,
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return completed.stdout


def load_historical_round35() -> object:
    """Load the exact pilot-revision engine only for read-only equivalence checks."""
    source = git_show(PILOT_REV, "src/search_rr_target_a_exhaustive.py")
    module = types.ModuleType("rr_short_ell0_medium_round35_at_pilot")
    module.__file__ = str(ROUND35)
    sys.modules[module.__name__] = module
    exec(compile(source, str(ROUND35), "exec"), module.__dict__)
    return module


def record_for_ell0() -> dict[str, object]:
    records = short5.short_root_records()
    matches = [row for row in records if row["root_id"] == "short_ell0"]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one ell0 root, got {len(matches)}")
    return matches[0]


def _semantic_stat_projection(stats: Mapping[str, object]) -> dict[str, object]:
    """Fields whose equality proves the 250-node remeasurement did not search differently."""
    keys = (
        "expanded", "generated_edges", "memo_hits", "prunes", "CH1_nodes", "CH2_nodes",
        "undecided_nodes", "other_nodes", "branch_transitions", "max_macro_depth",
        "pre_R_nodes", "post_R1_nodes", "R1_transitions", "R2_candidate_edges",
        "Target_A_hits", "pre_R_prunes", "post_R1_prunes", "max_post_R1_depth",
        "unique_r1_decorated_keys",
    )
    return {key: stats.get(key) for key in keys}


def baseline_telemetry(record: Mapping[str, object], source_raw: Mapping[str, object], extra: Mapping[str, object]) -> dict[str, object]:
    """Deterministically remeasure the already completed 250-node pilot in memory.

    This is not a continuation and writes no file.  It only supplies additive
    post-R telemetry that the pre-instrumentation pilot checkpoint could not
    have stored.  Its semantic counters must match the committed source.
    """
    prior_expanded = int(source_raw["stats"]["expanded"])
    replay = rr.search_root(dict(record), node_limit=prior_expanded, max_depth=None,
                            checkpoint=None, checkpoint_config_extra=extra)
    if replay["status"] != "INCOMPLETE" or not replay["interrupted_by_node_limit"]:
        raise AssertionError("pilot telemetry remeasurement did not stop at the source cap")
    expected = _semantic_stat_projection(source_raw["stats"])
    observed = _semantic_stat_projection(replay["stats"])
    if expected != observed:
        raise AssertionError("pilot telemetry remeasurement changed traversal semantics")
    # Keep the committed operational counters (especially checkpoint lineage
    # counters) intact.  Only fields unavailable in the old pilot are
    # backfilled from this deterministic, no-write remeasurement.
    return {key: replay["stats"][key] for key in (
        "Phi_at_R1", "M_at_R1", "steps_since_R1_expanded",
        "hub_completions_before_R1", "hub_completions_after_R1",
        "CH1_events", "CH2_events", "provisional_CH0_events",
    )}


def assert_historical_frontier_equivalence(source_raw: Mapping[str, object]) -> dict[str, object]:
    """Compare old and current one-step signatures on every live pilot state."""
    historical = load_historical_round35()
    historical_hash = sha256_bytes(git_show(PILOT_REV, "src/search_rr_target_a_exhaustive.py"))
    config = source_raw["config"]
    engine_hashes = config["engine_hashes"]
    source_key = str(ROUND35.relative_to(ROOT))
    if engine_hashes.get(source_key) != historical_hash or config.get("recognizer_hash") != historical_hash:
        raise AssertionError("source checkpoint does not identify the declared pilot engine")
    current_hashes = rr.code_hashes()
    for key, value in engine_hashes.items():
        if key != source_key and current_hashes.get(key) != value:
            raise AssertionError(f"non-search engine hash changed since pilot: {key}")
    mismatches = []
    for index, item in enumerate(source_raw["frontier"]):
        old_state = historical.exact.state_from_json(item["state"])
        old_dec = historical.Decoration.from_json(item["decoration"])
        new_state = rr.exact.state_from_json(item["state"])
        new_dec = rr.Decoration.from_json(item["decoration"])
        if repr(historical.successor_signature(old_state, old_dec)) != repr(rr.successor_signature(new_state, new_dec)):
            mismatches.append(index)
    return {
        "pilot_revision": PILOT_REV,
        "historical_engine_sha256": historical_hash,
        "current_engine_sha256": sha256_file(ROUND35),
        "frontier_states_compared": len(source_raw["frontier"]),
        "one_step_signature_mismatches": mismatches,
        "passed": not mismatches,
        "scope": "all live states in the committed r1_complete_v2 pilot frontier",
    }


def migrate_v2_checkpoint(source_raw: Mapping[str, object], source_sha: str,
                          record: Mapping[str, object], config: Mapping[str, object],
                          enriched_stats: Mapping[str, object], target: Path) -> dict[str, object]:
    """Write a new v2 identity with no mutation of semantic search data."""
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing medium checkpoint: {target}")
    before = {
        "frontier": source_raw["frontier"], "seen_keys": source_raw["seen_keys"],
        "boundaries": source_raw["boundaries"], "checkpoint_lineage": source_raw["checkpoint_lineage"],
    }
    payload = copy.deepcopy(dict(source_raw))
    payload["schema"] = rr.checkpoint_payload_schema(config)
    payload["config"] = dict(config)
    payload["stats"] = dict(source_raw["stats"])
    payload["stats"].update(enriched_stats)
    # Preserve the old frontier lineage and append a verifiable pointer to the
    # immutable source, rather than modifying the source checkpoint itself.
    payload["checkpoint_lineage"] = list(source_raw["checkpoint_lineage"]) + [source_sha]
    payload["complete_frontier_snapshot"] = True
    if {"frontier": payload["frontier"], "seen_keys": payload["seen_keys"],
        "boundaries": payload["boundaries"],
        "checkpoint_lineage": payload["checkpoint_lineage"][:-1]} != before:
        raise AssertionError("v2 migration altered semantic checkpoint content")
    atomic_json(target, payload)
    rr.load_checkpoint(target, config)
    target_raw = json.loads(target.read_text(encoding="utf-8"))
    if target_raw["frontier"] != source_raw["frontier"] or target_raw["seen_keys"] != source_raw["seen_keys"]:
        raise AssertionError("migrated checkpoint did not preserve frontier or memo keys")
    return {
        "source_checkpoint": str(SOURCE.relative_to(ROOT)), "source_sha256": source_sha,
        "target_checkpoint": str(target.relative_to(ROOT)), "target_initial_sha256": sha256_file(target),
        "source_expanded": int(source_raw["stats"]["expanded"]),
        "source_frontier": len(source_raw["frontier"]), "source_seen": len(source_raw["seen_keys"]),
        "target_config_sha256": json_sha(config),
        "semantic_frontier_and_memo_preserved": True,
        "migration_kind": "v2 config/telemetry lineage only; no v1 input",
    }


def checkpoint_summary(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    r_hist = Counter(len(item["decoration"]["r_events"]) for item in raw["frontier"])
    # The checkpoint itself is the diagnostic artifact and deliberately keeps
    # all raw exact keys.  Duplicating its two large raw-key arrays into the
    # public run summary would obscure the requested telemetry and turn a
    # small result ledger into a hundreds-of-megabytes second checkpoint.
    summary_fields = (
        "expanded", "generated_edges", "memo_hits", "checkpoint_count",
        "pre_R_nodes", "post_R1_nodes", "R1_transitions", "R2_candidate_edges",
        "Target_A_hits", "unique_r1_decorated_keys", "max_post_R1_depth",
        "CH1_nodes", "CH2_nodes", "undecided_nodes", "other_nodes",
        "CH1_events", "CH2_events", "provisional_CH0_events",
        "hub_completions_before_R1", "hub_completions_after_R1",
    )
    return {
        "path": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
        "schema": raw["schema"], "frontier_size": len(raw["frontier"]),
        "seen_size": len(raw["seen_keys"]), "frontier_r_count_distribution": dict(sorted(r_hist.items())),
        "stats": {key: raw["stats"].get(key) for key in summary_fields},
        "complete_frontier_snapshot": raw.get("complete_frontier_snapshot"),
    }


def process_boundaries(boundaries: list[Mapping[str, object]]) -> list[dict[str, object]]:
    """Exact replay, canonical comparison, and only helper-free Target-B work."""
    if not boundaries:
        return []
    verifier = load_module("rr_short_ell0_medium_target_b_verify", ROOT / "src" / "verify_rr_short5_search.py")
    record = record_for_ell0()
    triaged = {row["post_r2_state_hash"]: row for row in short5.postprocess_boundaries(boundaries)}
    rows = []
    for boundary in boundaries:
        replay = verifier.replay_found(record, boundary)
        if not replay["ok"]:
            raise AssertionError("Target-A boundary literal replay failed")
        state = replay.pop("post_state")
        triage = triaged[str(boundary["post_r2_state_hash"])]["target_b_helper_free_triage"]
        downstream: dict[str, object] = {"triage": triage, "phase_helper_used": False}
        if triage["status"] == "FLOW_REQUIRED":
            downstream["helper_free_exact_macro_dfs"] = verifier.helper_free_flow(state)
        rows.append({
            "boundary": dict(boundary), "literal_replay": replay,
            "R1": boundary["decoration_before_R2"]["r_events"][0],
            "R2": boundary["decoration_after_R2"]["r_events"][1],
            "same_component": boundary["same_component"], "chaining": boundary["chaining"],
            "hub_completer_timing": boundary["decoration_after_R2"]["completer"],
            "canonical_comparison_and_target_b": downstream,
        })
    return rows


def write_report(payload: Mapping[str, object]) -> None:
    result = payload["result"]
    stats = result["stats"]
    lines = [
        "# Round 40 — `short_ell0` corrected medium run",
        "",
        "Status: **{}**.  This is a cap-bounded diagnostic run, so it is not an exhaustion claim unless the frontier is empty.".format(result["status"]),
        "",
        "## Scope and checkpoint lineage",
        "",
        "- Only `short_ell0` was run; no other short or long root was started.",
        "- Source: `{}` (v2 R1-complete pilot only).".format(payload["migration"]["source_checkpoint"]),
        "- Target: `{}`.".format(payload["migration"]["target_checkpoint"]),
        "- The migration preserved literal frontier and memo keys, then changed only the hash-bound node-limit/config identity and additive telemetry.",
        "- The current and pilot engine one-step signatures agree on every source-frontier state: {} mismatches of {}.".format(
            len(payload["pilot_frontier_equivalence"]["one_step_signature_mismatches"]),
            payload["pilot_frontier_equivalence"]["frontier_states_compared"]),
        "",
        "## Telemetry",
        "",
        "| quantity | value |",
        "|---|---:|",
    ]
    rows = [
        ("total expansions", stats["expanded"]), ("pre-R nodes", stats["pre_R_nodes"]),
        ("post-R1 nodes", stats["post_R1_nodes"]), ("R1 transitions", stats["R1_transitions"]),
        ("unique r_count=1 decorated states", stats["unique_r1_decorated_keys"]),
        ("R2 candidate edges", stats["R2_candidate_edges"]), ("Target-A hits", stats["Target_A_hits"]),
        ("CH1 / CH2 / provisional CH0 events", "{} / {} / {}".format(
            stats["CH1_events"], stats["CH2_events"], stats["provisional_CH0_events"])),
        ("hub completion before / after R1", "{} / {}".format(
            stats["hub_completions_before_R1"], stats["hub_completions_after_R1"])),
        ("maximum post-R1 depth", stats["max_post_R1_depth"]),
        ("frontier r-count distribution", payload["final_checkpoint"]["frontier_r_count_distribution"]),
    ]
    lines.extend("| {} | {} |".format(label, value) for label, value in rows)
    lines += [
        "",
        "`CH0` is a provisional analysis label only; it is not a semantic branch classification or a prune.",
        "",
        "## Histograms",
        "",
        "- `Phi_at_R1`: `{}`".format(stats["Phi_at_R1"]),
        "- `M_at_R1` (`M=P-5O` on the accepted R1 child): `{}`".format(stats["M_at_R1"]),
        "- expanded-node `steps_since_R1`: `{}`".format(stats["steps_since_R1_expanded"]),
        "- post-R1 prunes: `{}`".format(stats["post_R1_prunes"]),
        "",
        "## Key and verification scope",
        "",
        "- State-key status: **exhaustive tested-universe equivalence** — finite tested-universe evidence only, not a theorem.",
        "- Independent verifier: `{}`.".format(payload.get("verification_path", "pending")),
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--additional-expansions", type=int, default=100_000)
    parser.add_argument("--checkpoint-every", type=int, default=5_000)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--checkpoint", type=Path, default=TARGET)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.additional_expansions < 1 or args.checkpoint_every < 1:
        raise ValueError("positive additional-expansions and checkpoint-every are required")
    if args.source.resolve() != SOURCE.resolve():
        raise ValueError("medium run may resume exclusively from the fixed r1_complete_v2 ell0 pilot")
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    if args.checkpoint.resolve() == SOURCE.resolve():
        raise ValueError("refusing to overwrite the immutable pilot checkpoint")

    record = record_for_ell0()
    manifest = short5.short_root_manifest(short5.short_root_records())
    extra = short5.config_extra(manifest)
    source_raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_sha = sha256_file(SOURCE)
    if source_raw.get("schema") != "rr-target-a-exhaustive-checkpoint-v2-short-r1":
        raise AssertionError("source is not an R1-complete v2 checkpoint")
    if source_raw["config"].get("root_id") != "short_ell0" or source_raw["config"].get("node_limit") != 250:
        raise AssertionError("source checkpoint is not the selected ell0 pilot")
    if not source_raw.get("complete_frontier_snapshot"):
        raise AssertionError("source does not certify a complete pilot frontier")
    equivalence = assert_historical_frontier_equivalence(source_raw)
    if not equivalence["passed"]:
        raise RuntimeError("STATE_KEY_UNSOUND: pilot/current successor mismatch")
    enriched_stats = baseline_telemetry(record, source_raw, extra)
    prior = int(source_raw["stats"]["expanded"])
    total_limit = prior + args.additional_expansions
    config = rr.checkpoint_config(record, total_limit, None, extra)
    migration = migrate_v2_checkpoint(source_raw, source_sha, record, config, enriched_stats, args.checkpoint)

    state_key_audit = short5.audit_short_state_key(short5.short_root_records())
    if not state_key_audit["passed"]:
        raise RuntimeError("STATE_KEY_UNSOUND")
    result = rr.search_root(record, node_limit=total_limit, max_depth=None,
                            checkpoint=args.checkpoint, checkpoint_every=args.checkpoint_every,
                            resume=args.checkpoint, checkpoint_config_extra=extra)
    final_checkpoint = checkpoint_summary(args.checkpoint)
    boundaries = process_boundaries(result["target_a_boundaries"])
    state_key = {
        "status": "exhaustive tested-universe equivalence",
        "scope": ("finite tested universe (five short roots through accepted depth-2 successors, including R1); "
                  "not a theorem"),
        "audit": state_key_audit,
    }
    payload: dict[str, object] = {
        "schema": "rr-short-ell0-medium-v2-result-v1",
        "classification": result["status"],
        "scope": ("short_ell0 only; exactly 100,000 additional expansions after the committed v2 pilot, "
                  "unless the frontier naturally exhausts"),
        "attribution": {"search_implementation": "CODEX", "mathematical_envelope_facts": "CLAUDE, CODEX_VERIFIED", "new_discovered_boundaries": "CODEX_FINDING"},
        "source_checkpoint_v2_only": str(SOURCE.relative_to(ROOT)),
        "migration": migration, "pilot_frontier_equivalence": equivalence,
        "result": result, "final_checkpoint": final_checkpoint,
        "state_key_status": state_key, "verified_target_a_hits": boundaries,
        "verification_path": "outputs/rr_short_ell0_medium_v2_verified.json",
        "CH0_note": "provisional analysis label only; event semantics not upgraded to a theorem",
        "phase_helper_used": False,
    }
    atomic_json(args.output, payload)
    write_report(payload)
    print(json.dumps({"status": result["status"], "expanded": result["stats"]["expanded"],
                      "frontier": result["stats"]["frontier_size"], "r1": result["stats"]["R1_transitions"],
                      "r2": result["stats"]["R2_candidate_edges"], "target_a": result["stats"]["Target_A_hits"]}, sort_keys=True))


if __name__ == "__main__":
    main()
