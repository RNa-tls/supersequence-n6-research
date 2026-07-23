#!/usr/bin/env python3
"""Complete formalization and boundary-condition audit of the Phi shortfall
potential introduced in research/J_CAPACITY_OBSTRUCTION.md.

This module exists to answer, precisely and with computational verification
against the real engine (not just symbolic argument), every question in
section 1-2 of the request that produced it:

  1. exact definition of ell, the set of its possible values, its value for
     each joint type, whether the identity holds at the literal level (it
     does NOT -- Phi oscillates during a rotation run and only decreases at
     joint boundaries), whether it holds at the true completion boundary
     (a subtlety: completion can occur via a trailing rotation-only suffix
     after the last joint, not necessarily at a joint boundary itself), and
     whether Phi>=0 (the engine's existing threshold) is already the
     TIGHT bound achievable from pure (P, visited_count) counting alone, or
     whether it can be improved (it cannot -- see verify_tight_bound below,
     which corrects an initial over-strong claim made and then retracted
     during this analysis).

Everything here is either a direct algebraic consequence of the exact-state
engine's own definitions, or a claim computationally verified against real
transitions -- nothing is asserted on the strength of "the corpus already
believes this."
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter, deque
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


macro = _load("shortfall_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def charge(ell: int) -> int:
    return 5 - ell


def section_1_boundary_facts() -> Dict[str, Any]:
    """Items 1-5 of the request: ell's definition/range, per-type behavior,
    and the exact (P, visited_count) values at the true completion state."""
    return {
        "ell_definition": (
            "RotationRun.ell = number of consecutive successful literal w=1 "
            "rotations taken immediately after a joint fires, before either "
            "hitting the hexagon size limit (N-1=5) or an already-visited "
            "window (collision). Defined in superperm_partial_f1_macro.py::rotation_runs."
        ),
        "ell_possible_values": list(range(0, exact.N)),  # 0..5
        "ell_is_a_property_of_the_run_not_the_joint_type": (
            "ell is chosen by the walker (any value from 0 up to the "
            "run's own collision point is legal) independently of which "
            "joint (Z2/Z3/R/A2/A3/J) eventually fires at the end of that "
            "run. There is therefore no fixed 'ell for R' vs 'ell for Z3' "
            "-- see section_2_charge_table for what IS type-dependent."
        ),
        "TARGET_P": exact.TARGET_P,
        "TARGET_O": exact.TARGET_O,
        "TARGET_D": exact.TARGET_D,
        "TARGET_F": exact.TARGET_F,
        "terminal_visited_count": 720,
        "phi_at_true_final_state": phi_symbolic_at(n=0, deficit=0),
        "final_state_note": (
            "area_a_final requires visited_count==720 AND P==TARGET_P "
            "simultaneously (plus O,D,F,H,Ndef conditions that do not enter "
            "Phi). Substituting n=TARGET_P-P=0 and deficit=720-visited=0 "
            "into Phi's definition gives Phi=5 at the exact final state, "
            "for ANY target constants -- not a fact special to F=1's "
            "P=121,O=25; it is a pure consequence of Phi's algebraic form."
        ),
    }


def phi_symbolic_at(n: int, deficit: int) -> int:
    return 5 + 6 * n - deficit


def section_2_charge_table() -> List[Dict[str, Any]]:
    """Per-joint-type charge behavior: since ell is independent of joint
    type, 'the charge of a Z2 joint' is not a fixed number -- what IS fixed
    is each type's effect on (F,S,O,N) given its own weight/abandonment/
    new_orbit triple (already established in analyze_j_completion.py's
    truth_table), reproduced here alongside the charge formula for
    completeness."""
    rows = []
    for weight, abandonment, new_orbit, kind in [
        (2, False, False, "Z2_blocked_w2_existing"),
        (2, True, False, "A2_abandon_w2_existing"),
        (2, True, True, "Z2_abandon_w2_new"),
        (3, False, False, "R_blocked_w3_existing"),
        (3, False, True, "Z3_blocked_w3_new"),
        (3, True, False, "J_abandon_w3_existing_charge2"),
        (3, True, True, "A3_abandon_w3_new"),
    ]:
        rows.append({
            "kind": kind,
            "weight": weight,
            "abandonment": abandonment,
            "new_orbit": new_orbit,
            "delta_F": int(abandonment),
            "delta_N": int(weight >= 3) + int(abandonment) - int(new_orbit),
            "delta_P_from_this_joint": 1,
            "charge_c_5_minus_ell": (
                "independent of joint type -- determined solely by the "
                "rotation run length ell preceding this joint, any value "
                "0..5 is legal for any joint type (subject to collision)"
            ),
        })
    return rows


def verify_macro_literal_consistency(seeds: List["exact.ExactState"], samples: int = 30) -> Dict[str, Any]:
    """Verify, for real macro edges, that Phi tracked at the LITERAL level
    (recomputing Phi after every single w=1 rotation, not just at joint
    boundaries) increases by exactly 1 per rotation and then drops by
    exactly (ell+1-6)=(ell-5) at the joint -- i.e. Phi is NOT monotone at
    the literal level (it goes up during a run), only at the macro
    joint-boundary level."""
    checked = 0
    literal_increase_mismatches = 0
    net_effect_mismatches = 0
    examples = []
    for seed in seeds[:samples]:
        edges = list(macro.macro_edges(seed))
        if not edges:
            continue
        edge = max(edges, key=lambda e: e.run.ell)
        cur = seed
        phi0 = phi(cur)
        literal_trace = [phi0]
        for _ in range(edge.run.ell):
            tr = exact.extend(cur, macro.W1)
            cur = tr.state
            literal_trace.append(phi(cur))
        for i in range(1, len(literal_trace)):
            checked += 1
            if literal_trace[i] != literal_trace[i - 1] + 1:
                literal_increase_mismatches += 1
        tr = exact.extend(cur, edge.joint.move)
        cur = tr.state
        final_phi = phi(cur)
        predicted = phi0 + (edge.run.ell - 5)
        if final_phi != predicted:
            net_effect_mismatches += 1
        if len(examples) < 3:
            examples.append({
                "edge_label": edge.label, "ell": edge.run.ell,
                "literal_phi_trace_during_rotation": literal_trace,
                "phi_after_joint": final_phi, "predicted_via_macro_identity": predicted,
            })
    return {
        "literal_steps_checked": checked,
        "literal_increase_by_exactly_1_mismatches": literal_increase_mismatches,
        "net_macro_effect_mismatches": net_effect_mismatches,
        "phi_is_monotone_only_at_joint_boundaries_not_literal_level": literal_increase_mismatches == 0 and checked > 0,
        "examples": examples,
    }


def verify_tight_bound() -> Dict[str, Any]:
    """Documents (and corrects) the boundary-case reasoning explicitly,
    since it is easy to get wrong -- an earlier pass in this analysis
    incorrectly concluded completion requires Phi>=5 throughout, which
    would have meant 229 of 230 J states (all with Phi<5) are already
    arithmetically dead. That conclusion was WRONG and is retracted here,
    with the correct argument in its place: completion need not occur at a
    joint boundary -- it can occur mid-rotation, via a trailing
    rotation-only suffix after the LAST joint ever fires. At that last
    joint-boundary state S_k, n(S_k)=0 (P already equals TARGET_P), and the
    remaining deficit must be closed by <=5 more plain rotations with no
    further joint -- i.e. deficit(S_k)<=5, i.e. Phi(S_k)>=0. This is
    EXACTLY the engine's existing threshold. So Phi>=0 is already the
    tight necessary condition obtainable from this counting argument alone;
    it is not improvable to some higher threshold without genuinely new
    (geometric) information."""
    return {
        "retracted_incorrect_claim": (
            "Phi(joint-boundary state) must be >=5 for eventual completion, "
            "because Phi is non-increasing and must equal exactly 5 at the "
            "state where n=0 and deficit=0 simultaneously."
        ),
        "why_it_was_wrong": (
            "It assumed completion always occurs exactly at a state where "
            "both n=0 AND deficit=0 hold simultaneously. In fact the walk "
            "can complete via a trailing rotation-only suffix taken AFTER "
            "the last joint (n already 0, deficit not yet 0), closing the "
            "remaining deficit purely by rotation, no further joint needed."
        ),
        "corrected_conclusion": (
            "At the last-ever joint-boundary state S_k, n(S_k)=0. The walk "
            "completes iff deficit(S_k) can be closed by a rotation-only "
            "suffix of length <=5, i.e. deficit(S_k)<=5, i.e. "
            "5+6*0-deficit(S_k)>=0, i.e. Phi(S_k)>=0 -- exactly the "
            "engine's existing remaining_window_capacity_prune threshold."
        ),
        "verdict": (
            "Phi>=0 is already the TIGHT necessary condition obtainable "
            "from (P, visited_count) counting alone. No scalar improvement "
            "of this specific bound was found; strengthening it further "
            "requires information this counting argument does not capture "
            "(which specific permutations collide), i.e. genuine geometry."
        ),
    }


def total_remaining_joint_count_is_independent_of_charge(state: "exact.ExactState") -> Dict[str, Any]:
    """Section 4's core question ('does an all-zero-charge run go on
    forever, unbounded?') has a one-line answer that does not need any new
    group theory: every joint (zero-charge or not) increments P by exactly
    1, and P is capped at TARGET_P. So the TOTAL number of remaining
    joints, charge or no charge, is EXACTLY TARGET_P - state.P -- a fixed,
    finite number completely independent of how much charge is spent. A
    long all-zero-charge run does not "run forever"; it simply uses up
    the joint budget at the same rate as any other run, one joint at a
    time, converging Phi's "n" term downward regardless of ell."""
    n = exact.TARGET_P - state.P
    n_new_orbit_required = exact.TARGET_O - state.O
    n_existing_orbit_required = n - n_new_orbit_required
    return {
        "remaining_joint_count_n": n,
        "remaining_new_orbit_joints_required_exactly": n_new_orbit_required,
        "remaining_existing_orbit_joints_required": n_existing_orbit_required,
        "argument": (
            "n is fixed and finite (TARGET_P - P), decreasing by exactly 1 "
            "per joint regardless of that joint's charge. Zero-charge "
            "joints do not exempt themselves from this count -- they still "
            "consume one of the n remaining joint slots. This alone bounds "
            "any zero-charge run's length by n, with no need for a "
            "separate collision/cycle argument."
        ),
    }


def main() -> None:
    witnesses = json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    seeds = [exact.state_from_json(w["final_state_json"]) for w in witnesses]

    report = {
        "schema": "shortfall-potential-verification-v1",
        "section_1_boundary_facts": section_1_boundary_facts(),
        "section_2_charge_table": section_2_charge_table(),
        "macro_literal_consistency_check": verify_macro_literal_consistency(seeds),
        "tight_bound_analysis": verify_tight_bound(),
        "zero_charge_run_bound_example": total_remaining_joint_count_is_independent_of_charge(seeds[0]),
    }
    out_path = ROOT / "outputs" / "shortfall_potential_verification.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": str(out_path),
        "phi_is_monotone_only_at_joint_boundaries": report["macro_literal_consistency_check"][
            "phi_is_monotone_only_at_joint_boundaries_not_literal_level"],
        "tight_bound_verdict": report["tight_bound_analysis"]["verdict"],
    }, indent=2))


if __name__ == "__main__":
    main()
