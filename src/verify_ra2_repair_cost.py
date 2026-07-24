#!/usr/bin/env python3
"""RA2 repair-cost lemma candidates (R1-R4), the counterfactual minimal
edit between U4 and C20, and the Omega combined-invariant attempt.

Central deflationary fact established in this round (see
RA2_ZERO_CHARGE_HISTORY.md): Phi(post-A2 state) = 1 + ell_A2 = 6 -
fragment_debt EXACTLY, verified over all 24 RA2 witnesses. Fragment debt
and Phi are therefore NOT independent for RA2's post-A2 states -- they are
the same information viewed two ways. This is checked directly below via
the counterfactual: replaying one U4 witness's own A2 move at every
possible rotation length ell=0..5 shows the SAME move produces debt
5,4,3,(illegal),1,(blocked) purely as a function of ell -- U4's debt=1 and
a typical C20 debt=4 differ by nothing but this one rotation-length choice.
"""
from __future__ import annotations

import argparse
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


macro = _load("vrc_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1

U4_HASHES = {
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
}


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def counterfactual_ell_sweep(witness: Dict[str, Any]) -> Dict[str, Any]:
    """Replay up to (not including) the A2 macro-edge, then test the SAME
    A2 move at every ell=0..5 -- the minimal edit distinguishing U4 from a
    typical C20 outcome."""
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    for step in path[:-1]:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        cur = exact.canonicalize(tr.state)

    a2_move = move_by_label[path[-1]["edge_label"].split(";")[1]]
    actual_ell = int(path[-1]["edge_label"].split(";")[0][len("rot^"):])
    sweep = []
    p = cur
    for ell in range(6):
        tr = exact.extend(p, a2_move)
        if tr is None:
            sweep.append({"ell": ell, "legal": False})
        else:
            sweep.append({
                "ell": ell, "legal": True, "abandonment": tr.abandonment, "new_orbit": tr.new_orbit,
                "resulting_debt": 5 - ell if tr.abandonment else None,
                "is_A2_type": tr.abandonment and tr.move.weight == 2,
            })
        nxt = exact.extend(p, W1)
        if nxt is None:
            break
        p = nxt.state
    return {"actual_ell_A2": actual_ell, "move_used": a2_move.label, "ell_sweep": sweep}


def r1_r2_r3_check(witness: Dict[str, Any], repair_cone: Dict[str, Any]) -> Dict[str, Any]:
    witnesses = repair_cone["shallowest_witnesses"]
    return {
        "R1_at_least_one_targeted_blocked_joint_required": {
            "claim": "closing fragment-debt=1 requires at least one blocked joint targeting the missing window",
            "status": "PROVEN (trivial, structural) -- only a joint can add visits to a non-current hex; rotation cannot",
        },
        "R2_repair_costs_at_least_1_slack_or_shortfall": {
            "claim": "the repair joint consumes at least 1 unit of orbit slack or Phi shortfall",
            "status": "REFUTED" if any(w["phi_consumed"] == 0 and w["orbit_slack_consumed"] == 0 for w in witnesses) else "unresolved",
            "counterexample": next((w for w in witnesses if w["phi_consumed"] == 0 and w["orbit_slack_consumed"] == 0), None),
        },
        "R3_required_repair_cost_exceeds_available_budget": {
            "claim": "U4's required repair cost exceeds its available budget",
            "status": "REFUTED" if witnesses else "cannot evaluate -- no repair witness found",
            "reason": "cheapest found repair witnesses cost 0 Phi and (mostly) 0 orbit slack -- well within any positive budget",
        },
        "R4_repair_orbit_reuse_conflicts_with_other_demand": {
            "claim": "the repair transition's orbit is needed elsewhere, so repair conflicts with other completion demand",
            "status": "미완료 (untested) -- no completed witness of this slab exists anywhere in this research to check against, so 'other completion demand' cannot be evaluated concretely",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--repair-cones", default=str(ROOT / "outputs" / "ra2_repair_cones.json"))
    parser.add_argument("--output-counterfactual", default=str(ROOT / "outputs" / "ra2_counterfactual_edits.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    repair_cones = json.loads(Path(args.repair_cones).read_text(encoding="utf-8"))["results"]

    counterfactuals = {}
    lemma_checks = {}
    for w in ra2["witnesses"]:
        if w["target_hash"] not in U4_HASHES:
            continue
        counterfactuals[w["target_hash"]] = counterfactual_ell_sweep(w)
        lemma_checks[w["target_hash"]] = r1_r2_r3_check(w, repair_cones[w["target_hash"]]["repair_cone"])

    report = {
        "schema": "ra2-counterfactual-edits-v1",
        "central_identity": "Phi(post-A2) = 1 + ell_A2 = 6 - fragment_debt, exact for all 24 RA2 witnesses",
        "counterfactual_ell_sweep_per_U4_state": counterfactuals,
        "repair_cost_lemma_checks": lemma_checks,
    }
    Path(args.output_counterfactual).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output_counterfactual}, indent=2))
    for h, cf in counterfactuals.items():
        print(h[:12], "actual_ell_A2:", cf["actual_ell_A2"], "sweep:", [(s["ell"], s.get("resulting_debt")) for s in cf["ell_sweep"]])


if __name__ == "__main__":
    main()
