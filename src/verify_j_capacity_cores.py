#!/usr/bin/env python3
"""Independent verification of the 45 capacity-failure core certificates in
outputs/j_capacity_45_seeds.json.

Does NOT reuse src/analyze_j_capacity_failures.py's own bookkeeping: replays
each seed's macro-path and each minimal-failing-continuation from scratch
(exact.extend directly), recomputing Phi at every step itself, and checks:

  - the recomputed canonical hash matches the recorded seed hash
  - Phi(seed) matches the recorded phi_at_witness
  - walking the recorded minimal_failing_continuation step by step, Phi
    stays >= 0 for every step except the last, and goes negative exactly
    at the last step (not earlier -- i.e. it really is *minimal*)
  - the last step's (ell, resulting Phi) satisfies Phi_after ==
    Phi_before + (ell-5), independently recomputed
  - the engine's own remaining_window_capacity_prune agrees that the final
    state is capacity-impossible, and disagrees (returns False) for every
    earlier state in the path
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


macro = _load("j_capacity_verify_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def replay_labels(state: "exact.ExactState", labels: List[str]) -> List["exact.ExactState"]:
    """Return the state after each macro-edge label, in order (raw, uncanonicalized:
    this matches how src/search_j_afterstate.py and analyze_j_capacity_failures.py
    generated these paths)."""
    move_by_label = {m.label: m for m in exact.ALL_MOVES}
    W1 = macro.W1
    out = []
    cur = state
    for label in labels:
        rot_part, joint_part = label.split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            if tr is None:
                raise AssertionError(f"rotation collision replaying {label}")
            cur = tr.state
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        if tr is None:
            raise AssertionError(f"joint illegal replaying {label}")
        cur = tr.state
        out.append(cur)
    return out


def verify_one(record: Dict[str, Any], witness_state: "exact.ExactState") -> Dict[str, Any]:
    checks: Dict[str, Any] = {}
    recomputed_seed_hash = macro.stable_hash(exact.canonicalize(witness_state))
    checks["seed_hash_matches"] = recomputed_seed_hash == record["canonical_state_hash"]
    checks["phi_at_witness_matches"] = phi(witness_state) == record["phi_at_witness"]

    mfc = record["minimal_failing_continuation"]
    states = replay_labels(witness_state, mfc["macro_path"])
    phis = [phi(witness_state)] + [phi(s) for s in states]

    checks["phi_nonnegative_before_last_step"] = all(p >= 0 for p in phis[:-1])
    checks["phi_negative_only_at_last_step"] = phis[-1] < 0
    checks["prune_agrees_only_at_last_step"] = (
        all(not macro.remaining_window_capacity_prune(s) for s in states[:-1])
        and macro.remaining_window_capacity_prune(states[-1])
    )
    last_label = mfc["macro_path"][-1]
    ell = int(last_label.split(";")[0][len("rot^"):])
    checks["ell_matches_recorded"] = ell == mfc["ell_of_final_step"]
    checks["phi_transition_identity_holds"] = phis[-1] == phis[-2] + (ell - 5)
    checks["recorded_phi_after_matches"] = phis[-1] == mfc["phi_after_final_step"]
    checks["recorded_phi_before_matches"] = phis[-2] == mfc["phi_before_final_step"]
    checks["depth_matches"] = len(mfc["macro_path"]) == mfc["depth"]

    verdict = "PASS" if all(bool(v) for v in checks.values()) else "FAIL"
    return {"canonical_state_hash": record["canonical_state_hash"], "checks": checks, "verdict": verdict}


def main() -> None:
    data = json.loads((ROOT / "outputs" / "j_capacity_45_seeds.json").read_text(encoding="utf-8"))
    witnesses = {
        w["target_hash"]: w
        for w in json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text(encoding="utf-8"))["witnesses"]
    }
    results = []
    for record in data["seeds_45"]:
        h = record["canonical_state_hash"]
        witness_state = exact.state_from_json(witnesses[h]["final_state_json"])
        results.append(verify_one(record, witness_state))

    passed = sum(1 for r in results if r["verdict"] == "PASS")
    failed = [r for r in results if r["verdict"] != "PASS"]
    report = {
        "schema": "j-capacity-core-verification-v1",
        "checked": len(results),
        "passed": passed,
        "failed": len(failed),
        "failures": failed,
        "results": results,
    }
    out_path = ROOT / "outputs" / "j_capacity_core_certificates.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "checked": len(results), "passed": passed, "failed": len(failed)}, indent=2))


if __name__ == "__main__":
    main()
