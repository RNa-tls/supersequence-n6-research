"""Small, deterministic Target-A prune-scope differential for ``short_ell0``.

This is deliberately a pilot, not a continuation proof run.  It compares the
historical Area-A/Q2 completion bundle against the semantic Target-A registry,
stores a v3 checkpoint only for the latter, and preserves the historical v2
checkpoint untouched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs" / "rr_short_ell0_prune_differential.json"
SCOPE_OUTPUT = ROOT / "outputs" / "rr_short_ell0_scope_audit.json"
REGISTRY_OUTPUT = ROOT / "outputs" / "rr_target_a_prune_registry.json"
CHECKPOINT = (ROOT / "outputs" / "checkpoints" / "rr_short5" /
              "r1_complete_v3_target_a" / "short_ell0_scope_audit.json")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rr = load("rr_scope_audit_engine", ROOT / "src" / "search_rr_target_a_exhaustive.py")
short5 = load("rr_scope_audit_short5", ROOT / "src" / "search_rr_short5_exact.py")


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temporary.replace(path)


def replay_trace(record: Mapping[str, object], trace: list[Mapping[str, object]]):
    """Literal-replay a serialized macro trace and return exact terminal data."""
    state, dec = rr.initial_decoration(record)
    for item in trace:
        label = str(item["label"])
        found = None
        for edge, collision in rr.iter_raw_macro_candidates(state):
            if collision is None and edge is not None and edge.label == label:
                found = edge
                break
        if found is None:
            raise AssertionError(f"literal trace edge is absent: {label}")
        dec = rr.advance_decoration(found.run.state, found.joint, dec)
        state = found.state
    return state, dec


def first_o_divergence(record: Mapping[str, object], limit: int) -> dict[str, object]:
    """Search the common legacy prefix for the first edge legacy prunes by O.

    No inference follows from failing to find one at the cap.  On success the
    returned child is a literal legal exact state; it witnesses precisely why
    an O completion cap cannot be claimed as a semantic Target-A invariant.
    """
    state0, dec0 = rr.initial_decoration(record)
    stack = [(0, state0, dec0, tuple())]
    seen = {rr.decorated_key(state0, dec0)}
    expanded = 0
    while stack and expanded < limit:
        depth, state, dec, trace = stack.pop()
        expanded += 1
        children = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            if collision is not None or edge is None:
                continue
            legacy, legacy_dec, _ = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.LEGACY_AREA_A_PROFILE)
            safe, safe_dec, _ = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
            step = rr.edge_json(edge)
            if legacy == f"{rr.LEGACY_AREA_A_PROFILE}:O_exceeded" and safe == "child":
                assert safe_dec is not None
                child_trace = list(trace + (step,))
                replayed_state, replayed_dec = replay_trace(record, child_trace)
                if replayed_state.stable_key() != edge.state.stable_key() or replayed_dec != safe_dec:
                    raise AssertionError("first divergent state failed literal replay")
                return {
                    "status": "EXACT_COUNTEREXAMPLE",
                    "expanded_common_prefix_nodes": expanded,
                    "depth": depth + 1,
                    "legacy_verdict": legacy,
                    "target_a_safe_verdict": safe,
                    "parent_state": rr.exact.state_to_json(state),
                    "parent_decoration": dec.to_json(),
                    "edge": step,
                    "literal_macro_trace": child_trace,
                    "child_state": rr.exact.state_to_json(edge.state),
                    "child_decoration": safe_dec.to_json(),
                    "coordinate": {"P": edge.state.P, "O": edge.state.O, "D": edge.state.D,
                                   "Ndef": edge.state.Ndef, "F": edge.state.F, "H": edge.state.H},
                    "interpretation": (
                        "The child is exact-engine legal and lies in the semantic Target-A prefix "
                        "universe, but the legacy completion bundle rejects it only because O>25. "
                        "This is not a Target-A boundary and does not assert a Target-A witness."
                    ),
                }
            # Continue only the shared child set: this makes the reported
            # divergence deterministic and attributable to the legacy gate.
            if legacy == "child" and safe == "child":
                assert legacy_dec is not None and safe_dec is not None
                if legacy_dec != safe_dec:
                    raise AssertionError("profiles changed decoration on a shared child")
                key = rr.decorated_key(edge.state, safe_dec)
                if key not in seen:
                    seen.add(key)
                    children.append((depth + 1, edge.state, safe_dec, trace + (step,)))
        children.sort(key=lambda row: row[3][-1]["label"], reverse=True)
        stack.extend(children)
    return {"status": "INCOMPLETE", "expanded_common_prefix_nodes": expanded,
            "frontier_size": len(stack), "node_limit": limit,
            "interpretation": "No O-only divergence found within this bounded common-prefix replay."}


def selected_record() -> dict[str, object]:
    records = short5.short_root_records()
    return next(record for record in records if record["root_id"] == "short_ell0")


def area_a_retention_table() -> list[dict[str, object]]:
    """The source-level decomposition of ``macro.area_a_prune_reason``.

    The table is deliberately explicit rather than inferred from pilot prune
    counts: a sub-prune remains Q2-only even when that pilot did not happen to
    trigger it.
    """
    q2 = "q2_target_b_completion_only"
    return [
        {"name": "F_exceeded", "condition": "F>1", "monotone": True,
         "target_a": "RETAINED", "scope": "target_a_safe_proved",
         "justification": "Target A requires F_def=1 and F is monotone."},
        {"name": "H_positive", "condition": "H>0", "monotone": True,
         "target_a": "RETAINED", "scope": "target_a_safe_proved",
         "justification": "Target A requires H=0 and H is monotone."},
        {"name": "P_exceeded", "condition": "P>121", "monotone": True,
         "target_a": "DISABLED", "scope": q2,
         "justification": "P=121 is a Target-B completion coordinate, not a Target-A boundary condition."},
        {"name": "O_exceeded", "condition": "O>25", "monotone": True,
         "target_a": "DISABLED", "scope": q2,
         "justification": "O=25 is a Target-B completion coordinate; Target A has no upper O bound."},
        {"name": "N_exceeded_monotone", "condition": "Ndef>AreaA.n_limit", "monotone": True,
         "target_a": "DISABLED", "scope": q2,
         "justification": "The Ndef limit belongs to Area A/Q2, not Target A."},
        {"name": "final_D_impossible", "condition": "not arithmetic_D_reachable(state)", "monotone": False,
         "target_a": "DISABLED", "scope": q2,
         "justification": "D=4 is a Target-B terminal coordinate."},
        {"name": "remaining_pass_starts_exceed_remaining_windows", "condition": "720-visited < 121-P", "monotone": False,
         "target_a": "DISABLED", "scope": q2,
         "justification": "This budgets completion to P=121."},
        {"name": "remaining_cover_capacity_impossible", "condition": "remaining_window_capacity_prune(state)", "monotone": False,
         "target_a": "DISABLED", "scope": q2,
         "justification": "This budgets completion windows to Target B."},
        {"name": "F1_fragment_normal_form_impossible", "condition": "f1_normal_form(state) is None", "monotone": True,
         "target_a": "RETAINED", "scope": "target_a_safe_proved",
         "justification": "Exact F<=1 prefix invariant, independent of completion coordinates."},
        {"name": "insufficient_future_orbit_opening_credit", "condition": "25-O > (121-P)+(1-F)", "monotone": False,
         "target_a": "DISABLED", "scope": q2,
         "justification": "It is a future-credit argument for completing O=25."},
        {"name": "exact_permutation_collision", "condition": "exact.extend returns None", "monotone": True,
         "target_a": "RETAINED", "scope": "universally_safe",
         "justification": "A nonrepeat walk cannot traverse the candidate."},
        {"name": "rr_r_budget", "condition": "more than two R events", "monotone": True,
         "target_a": "RETAINED", "scope": "target_a_scope_reduction",
         "justification": "The scoped RR root language stops at R2; R2 is recognized on the edge."},
        {"name": "hub_touch_count", "condition": "hub target touches >2 under F<=1", "monotone": True,
         "target_a": "RETAINED", "scope": "universally_safe_under_F_le_1",
         "justification": "RR_HUB_TOUCH_COUNT theorem."},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-limit", type=int, default=250)
    parser.add_argument("--checkpoint-every", type=int, default=50)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--scope-output", type=Path, default=SCOPE_OUTPUT)
    parser.add_argument("--registry-output", type=Path, default=REGISTRY_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    args = parser.parse_args()
    if args.node_limit <= 0:
        raise ValueError("this audit driver requires a positive pilot cap")

    record = selected_record()
    manifest = short5.short_root_manifest(short5.short_root_records())
    extra = short5.config_extra(manifest)
    # A fresh v3 file is intentional.  The v2 medium checkpoint must never
    # be resumed after this registry change.
    if args.checkpoint.exists():
        args.checkpoint.unlink()
    legacy = rr.search_root(record, node_limit=args.node_limit, checkpoint=None,
                            checkpoint_config_extra=extra,
                            prune_profile=rr.LEGACY_AREA_A_PROFILE)
    safe = rr.search_root(record, node_limit=args.node_limit, checkpoint=args.checkpoint,
                          checkpoint_every=args.checkpoint_every, checkpoint_config_extra=extra,
                          prune_profile=rr.TARGET_A_SAFE_PROFILE)
    divergence = first_o_divergence(record, args.node_limit)
    safe_config = rr.checkpoint_config(record, args.node_limit, None, extra,
                                       prune_profile=rr.TARGET_A_SAFE_PROFILE)
    frontier, seen, _stats, _bounds, _lineage = rr.load_checkpoint(args.checkpoint, safe_config)
    audit = short5.audit_short_state_key([record], depth_limit=2)
    payload = {
        "schema": "rr-short-ell0-target-a-prune-differential-v1",
        "grade": "bounded deterministic diagnostic; no exhaustiveness claim",
        "root": record, "node_limit": args.node_limit,
        "legacy_area_a_q2_profile": legacy,
        "target_a_safe_profile": safe,
        "first_o_exceeded_divergence": divergence,
        "new_checkpoint": {"path": str(args.checkpoint), "schema": safe_config["checkpoint_payload_schema"],
                           "prune_profile": safe_config["prune_profile"],
                           "frontier_size": len(frontier), "seen_size": len(seen),
                           "sha256": rr.sha256_file(args.checkpoint)},
        "post_r1_state_key_audit": audit,
        "old_medium_run_status": "PREMATURELY_PRUNED_INVALID_FOR_TARGET_A_COVERAGE",
        "conclusion": "INCOMPLETE",
    }
    scope = {
        "schema": "rr-short-ell0-scope-audit-v1",
        "status": "TARGET_A_COMPLETENESS_GAP_CONFIRMED",
        "old_medium_run": {
            "path": "outputs/rr_short_ell0_medium_v2.json",
            "status_for_target_a": "PREMATURELY_PRUNED_INVALID_FOR_TARGET_A_COVERAGE",
            "reason": "used LEGACY_AREA_A_PROFILE containing O_exceeded before semantic R2 recognition",
        },
        "corrected_pilot": {"status": safe["status"], "node_limit": args.node_limit,
                            "checkpoint_schema": safe_config["checkpoint_payload_schema"]},
        "differential": {"first_divergence_status": divergence["status"],
                         "target_a_profile": rr.TARGET_A_SAFE_PROFILE,
                         "legacy_profile": rr.LEGACY_AREA_A_PROFILE},
    }
    registry = {
        "schema": "rr-target-a-prune-registry-v1",
        "target_a_profile": rr.TARGET_A_SAFE_PROFILE,
        "legacy_area_a_profile": rr.LEGACY_AREA_A_PROFILE,
        "target_a_registry_hash": rr.registry_hash(rr.TARGET_A_SAFE_PROFILE),
        "legacy_registry_hash": rr.registry_hash(rr.LEGACY_AREA_A_PROFILE),
        "enabled_target_a_prunes": rr.TARGET_A_PRUNE_REGISTRY,
        "area_a_prune_reason_retention_table": area_a_retention_table(),
        "historical_sources": [
            "legacy_research/work/superperm_partial_f1_macro.py::area_a_prune_reason",
            "research/RR_TARGET_A_DEFINITION.md",
            "research/RR_TARGET_B_DEFINITION.md",
            "research/RR_ROUND35_VS_ROUND37_RECONCILIATION_CODEX.md",
        ],
    }
    atomic_json(args.output, payload)
    atomic_json(args.scope_output, scope)
    atomic_json(args.registry_output, registry)
    print(json.dumps({"output": str(args.output), "scope_output": str(args.scope_output),
                      "divergence": divergence["status"], "safe_status": safe["status"]}, indent=2))


if __name__ == "__main__":
    main()
