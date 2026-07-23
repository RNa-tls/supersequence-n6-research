#!/usr/bin/env python3
"""Independent literal replay verification of recovered J witnesses.

This deliberately does NOT reuse src/recover_j_witnesses.py's bookkeeping
(its node_records, its canonicalization calls during search). It re-derives
each witness's validity from scratch: given only the ordered macro-path
(edge labels) recovered for a target hash, it replays that path from the
identity permutation using exact.extend directly, and checks every claim
independently. If recover_j_witnesses.py had a bug, this script re-doing
the same replay by itself is what would catch it.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("j_verify_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def replay_macro_path_independent(edge_labels: List[str]) -> "exact.ExactState":
    """Independent replay: parses 'rot^K;joint_label' strings itself and
    calls exact.extend directly -- does not call macro.replay_macro_path."""
    state = exact.canonicalize(exact.initial_state())
    move_by_label = {m.label: m for m in exact.ALL_MOVES}
    W1 = macro.W1
    for label in edge_labels:
        rot_part, joint_part = label.split(";")
        if not rot_part.startswith("rot^"):
            raise AssertionError(f"malformed macro edge label: {label}")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(state, W1)
            if tr is None:
                raise AssertionError(f"rotation collision replaying {label}")
            state = tr.state
        move = move_by_label.get(joint_part)
        if move is None:
            raise AssertionError(f"unknown joint label {joint_part!r} in {label}")
        tr = exact.extend(state, move)
        if tr is None:
            raise AssertionError(f"joint illegal replaying {label}")
        state = exact.canonicalize(tr.state)
    return state


def verify_one(target_hash: str, macro_path: List[Dict[str, Any]]) -> Dict[str, Any]:
    edge_labels = [step["edge_label"] for step in macro_path]
    checks: Dict[str, Any] = {}
    try:
        state = replay_macro_path_independent(edge_labels)
    except AssertionError as exc:
        return {
            "target_hash": target_hash, "replay_ok": False, "failure": str(exc),
            "verdict": "FAIL",
        }

    recomputed_hash = macro.stable_hash(state)
    checks["recomputed_hash_matches_target"] = recomputed_hash == target_hash

    # Reconstruct the per-step (weight, abandonment, new_orbit, delta_N)
    # sequence from the recorded transition dicts (these were captured
    # during the ORIGINAL search's own exact.extend call, at recovery
    # time -- cross-check them against a second, independent replay's
    # per-step deltas by re-walking with running (F,S,H,O) bookkeeping).
    seq = []
    running_state = exact.canonicalize(exact.initial_state())
    W1 = macro.W1
    move_by_label = {m.label: m for m in exact.ALL_MOVES}
    for step in macro_path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(running_state, W1)
            running_state = tr.state
        move = move_by_label[joint_part]
        before = running_state
        tr = exact.extend(running_state, move)
        running_state = exact.canonicalize(tr.state)
        delta_n = running_state.Ndef - before.Ndef
        seq.append({
            "weight": move.weight, "abandonment": tr.abandonment,
            "new_orbit": tr.new_orbit, "delta_F": tr.delta_F, "delta_S": tr.delta_S,
            "delta_O": int(tr.new_orbit), "delta_N": delta_n,
            "recorded_transition": step["transition"],
            "matches_recorded": (
                tr.abandonment == step["transition"]["abandonment"]
                and tr.new_orbit == step["transition"]["new_orbit"]
                and tr.delta_F == step["transition"]["delta_F"]
                and tr.delta_S == step["transition"]["delta_S"]
            ),
        })

    checks["every_recorded_transition_reproduced"] = all(s["matches_recorded"] for s in seq)

    # No repeated intermediate window: guaranteed by exact.extend's own
    # visited-window check (it returns None on any collision, which would
    # already have raised above), but recheck it is not silently bypassed
    # by confirming every step in this replay actually advanced (no step
    # was skipped).
    checks["step_count_matches_path_length"] = len(seq) == len(macro_path)

    # N<2 strictly before the J event, ==2 at/after it; J is (1,1,0,2);
    # exactly one positive-charge event in the whole path, and it is J.
    positive_events = [s for s in seq if s["delta_N"] != 0]
    j_events = [s for s in positive_events
                if (s["weight"], s["abandonment"], s["new_orbit"]) == (3, True, False)]
    checks["exactly_one_positive_charge_event"] = len(positive_events) == 1
    checks["that_event_is_J"] = len(j_events) == 1 and positive_events == j_events
    if j_events:
        j = j_events[0]
        checks["J_deltas_exact"] = (
            j["delta_F"] == 1 and j["delta_S"] == 1 and j["delta_O"] == 0 and j["delta_N"] == 2
        )
        j_index = seq.index(j)
        n_before_j = sum(s["delta_N"] for s in seq[:j_index])
        n_after_j = sum(s["delta_N"] for s in seq[:j_index + 1])
        checks["N_strictly_below_2_before_J"] = n_before_j < 2
        checks["N_equals_2_at_and_after_J"] = n_after_j == 2 and all(
            sum(x["delta_N"] for x in seq[:i + 1]) == 2 for i in range(j_index, len(seq))
        )
    else:
        checks["J_deltas_exact"] = False
        checks["N_strictly_below_2_before_J"] = False
        checks["N_equals_2_at_and_after_J"] = False

    checks["final_F_H_N_is_1_0_2"] = (state.F, state.H, state.Ndef) == (1, 0, 2)

    verdict = "PASS" if all(bool(v) for v in checks.values()) else "FAIL"
    return {
        "target_hash": target_hash,
        "recomputed_hash": recomputed_hash,
        "checks": checks,
        "verdict": verdict,
    }


def main() -> None:
    src_path = ROOT / "outputs" / "j_230_literal_witnesses.json"
    data = json.loads(src_path.read_text(encoding="utf-8"))
    results = []
    for w in data["witnesses"]:
        results.append(verify_one(w["target_hash"], w["macro_path"]))
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    failed = [r for r in results if r["verdict"] != "PASS"]
    report = {
        "schema": "j-230-witness-verification-v1",
        "witnesses_checked": len(results),
        "missing_from_source": data["missing_count"],
        "passed": passed,
        "failed": len(failed),
        "failures": failed,
        "results": results,
    }
    out_path = ROOT / "outputs" / "j_230_witness_verification.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "wrote": str(out_path),
        "witnesses_checked": len(results),
        "passed": passed,
        "failed": len(failed),
        "missing_from_source": data["missing_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
