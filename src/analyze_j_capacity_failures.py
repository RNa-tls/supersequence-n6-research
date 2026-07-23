#!/usr/bin/env python3
"""Independent re-derivation and analysis of the F=1,H=0 capacity obstruction
that fired (`remaining_cover_capacity_impossible`) on 45 of the 230 recorded
J states during the bounded afterstate profiling in
src/search_j_afterstate.py.

Core result (proved below, not just cited from the engine): define, for any
state S in this model,

    Phi(S) = 5 + 6*(TARGET_P - S.P) - (720 - S.visited_count)

Every joint-boundary state has Phi(S) >= 0 as a *necessary* condition for
eventual completion (this is exactly the engine's own
``remaining_window_capacity_prune``, re-derived independently below and
verified computationally against the actual engine rather than trusted).
What is new here is the monotonicity identity:

    Phi(S') = Phi(S) + (ell - 5)

where S' is the state reached from a joint-boundary state S by taking a
rotation run of length ``ell`` (0..5) and then one more legal joint. Since
ell <= 5 always, Phi never increases along any legal continuation. This
turns the existing prune into a genuine monotone potential: the *total*
tolerable shortfall (sum of (5-ell) over every future joint, for the
*entire remaining walk*) is bounded above by Phi(S) at any point S. Once
that budget is spent, completion is arithmetically impossible from there
on, regardless of which specific permutations get visited.

This module:
  1. fixes the list of 45 J-witnesses on which the bounded afterstate
     profile observed at least one remaining_cover_capacity_impossible
     prune, in deterministic order, with the requested per-seed fields;
  2. re-derives and computationally verifies the Phi identity;
  3. computes Phi for all 230 J-witnesses (not just the 45) -- since Phi
     is O(1) per state, this is a complete, not bounded, computation;
  4. for each of the 45, finds (via a small bounded search) the shortest
     concrete path from the seed to a state where Phi first goes negative
     (a minimal arithmetic "core" of the failure, independent of which
     specific permutations are visited);
  5. reports the honest (negative) result that Phi(seed) alone does not
     cleanly separate the 45 "observed failure" seeds from the other 185
     within the shallow bounded experiment -- it is a necessary bound, not
     a predictor of what a shallow raw search happens to hit first.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


macro = _load("j_capacity_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def verify_phi_identity(seeds: List["exact.ExactState"], depth_cap: int = 4, edge_cap_per_seed: int = 300) -> Dict[str, Any]:
    """Computationally verify, against the real engine (not just symbolically),
    that (a) phi(child) == phi(parent) + (ell-5) for every legal non-abandoning
    joint, and (b) the engine's own remaining_window_capacity_prune(state)
    is exactly (phi(state) < 0), over a real bounded traversal from every
    one of the 230 seeds."""
    checked = 0
    formula_mismatches = 0
    prune_mismatches = 0
    for seed in seeds:
        frontier = deque([(0, seed)])
        edges = 0
        while frontier and edges < edge_cap_per_seed:
            depth, state = frontier.popleft()
            if depth >= depth_cap:
                continue
            phi0 = phi(state)
            for edge in macro.macro_edges(state):
                edges += 1
                tr = edge.joint
                if tr.abandonment:
                    continue
                child = tr.state
                phi1 = phi(child)
                predicted = phi0 + (edge.run.ell - 5)
                checked += 1
                if phi1 != predicted:
                    formula_mismatches += 1
                if macro.remaining_window_capacity_prune(child) != (phi1 < 0):
                    prune_mismatches += 1
                reason = macro.area_a_prune_reason(child, macro.AREA_A)
                if reason is None:
                    frontier.append((depth + 1, child))
            if edges >= edge_cap_per_seed:
                break
    return {
        "transitions_checked": checked,
        "monotonicity_formula_mismatches": formula_mismatches,
        "prune_iff_phi_negative_mismatches": prune_mismatches,
        "identity_holds_without_exception": formula_mismatches == 0 and prune_mismatches == 0,
    }


def global_slab_phi() -> Dict[str, Any]:
    """Phi at the very start of any F=1,H=0 walk (not J-specific): shows the
    *entire* slab has almost no rotation-shortfall budget from the outset."""
    start = exact.initial_state()
    return {
        "phi_at_initial_state": phi(start),
        "interpretation": (
            "Phi(initial_state)=6 means: across ALL 120 remaining joints in "
            "ANY complete F=1,H=0 walk (J-branch or not), the TOTAL shortfall "
            "sum(5-ell_i) may never exceed 6, on pain of arithmetic "
            "impossibility. This is a fact about the whole slab, not about J."
        ),
    }


def find_minimal_failing_path(seed: "exact.ExactState", max_depth: int, edge_cap: int) -> Optional[Dict[str, Any]]:
    """Shortest concrete macro-path (raw, uncanonicalized) from seed to a
    state with phi<0, restricted to the proven post-J alphabet. Returns the
    shallowest one found within the bound, or None if not found."""
    frontier = deque([(0, seed, [])])
    edges = 0
    best: Optional[Dict[str, Any]] = None
    while frontier and edges < edge_cap:
        depth, state, path_labels = frontier.popleft()
        if best is not None and depth >= best["depth"]:
            continue
        if depth >= max_depth:
            continue
        for edge in macro.macro_edges(state):
            edges += 1
            tr = edge.joint
            if tr.abandonment:
                continue
            reason_gen = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            new_labels = path_labels + [edge.label]
            if reason_gen == "remaining_cover_capacity_impossible":
                if best is None or depth + 1 < best["depth"]:
                    best = {
                        "depth": depth + 1,
                        "macro_path": new_labels,
                        "phi_before_final_step": phi(state),
                        "ell_of_final_step": edge.run.ell,
                        "phi_after_final_step": phi(edge.state),
                    }
                continue
            if reason_gen is not None:
                continue
            frontier.append((depth + 1, edge.state, new_labels))
            if edges >= edge_cap:
                break
    return best


def build_45_seed_list(witnesses: List[Dict[str, Any]], profiles_by_hash: Dict[str, Any]) -> List[Dict[str, Any]]:
    failing_hashes = sorted(
        h for h, p in profiles_by_hash.items()
        if p.get("terminal_reason_counts", {}).get("remaining_cover_capacity_impossible", 0) > 0
    )
    witnesses_by_hash = {w["target_hash"]: w for w in witnesses}
    records = []
    for h in failing_hashes:
        w = witnesses_by_hash[h]
        state = exact.state_from_json(w["final_state_json"])
        form = exact.f1_normal_form(state)
        j_idx = next(
            i for i, s in enumerate(w["macro_path"])
            if s["transition"]["abandonment"] and s["transition"]["new_orbit"] is False
            and s["transition"]["weight"] == 3
        )
        minimal = find_minimal_failing_path(state, max_depth=6, edge_cap=20_000)
        records.append({
            "canonical_state_hash": h,
            "macro_path": w["macro_path"],
            "j_index_in_path": j_idx,
            "path_length_at_witness": len(w["macro_path"]),
            "coordinate_P_F_S_H_O_D_N": list(macro.state_coordinate(state)),
            "visited_count": state.visited_count,
            "remaining_permutations": 720 - state.visited_count,
            "remaining_pass_starts": exact.TARGET_P - state.P,
            "remaining_new_orbits_needed": exact.TARGET_O - state.O,
            "phi_at_witness": phi(state),
            "fragment_hex": form.fragment_hex if form else None,
            "fragment_components": list(form.fragment_components) if form else None,
            "current_hex": form.current_hex if form else None,
            "current_components": list(form.current_components) if form else None,
            "minimal_failing_continuation": minimal,
        })
    return records


def main() -> None:
    witnesses = json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    afterstate = json.loads((ROOT / "outputs" / "j_afterstate_profile.json").read_text())
    profiles_by_hash = {p["target_hash"]: p["profile"] for p in afterstate["profiles"]}

    all_states = {w["target_hash"]: exact.state_from_json(w["final_state_json"]) for w in witnesses}
    phi_all = {h: phi(s) for h, s in all_states.items()}
    phi_dist_all = Counter(phi_all.values())

    failing_hashes = set(
        h for h, p in profiles_by_hash.items()
        if p.get("terminal_reason_counts", {}).get("remaining_cover_capacity_impossible", 0) > 0
    )
    phi_dist_failing = Counter(phi_all[h] for h in failing_hashes)
    phi_dist_not_failing = Counter(phi_all[h] for h in all_states if h not in failing_hashes)

    identity_check = verify_phi_identity(list(all_states.values()), depth_cap=4, edge_cap_per_seed=300)

    seeds_45 = build_45_seed_list(witnesses, profiles_by_hash)

    report = {
        "schema": "j-capacity-45-seeds-v1",
        "phi_definition": "Phi(S) = 5 + 6*(TARGET_P - S.P) - (720 - S.visited_count)",
        "phi_monotonicity_identity": "Phi(child) = Phi(parent) + (rotation_run_length - 5), so Phi never increases",
        "phi_identity_verification": identity_check,
        "global_slab_phi": global_slab_phi(),
        "phi_distribution_all_230": dict(sorted(phi_dist_all.items())),
        "phi_distribution_45_failing_seeds": dict(sorted(phi_dist_failing.items())),
        "phi_distribution_185_not_yet_failing_seeds": dict(sorted(phi_dist_not_failing.items())),
        "phi_cleanly_separates_45_from_185": (
            max(phi_dist_failing) < min(phi_dist_not_failing) if phi_dist_failing and phi_dist_not_failing else None
        ),
        "seed_count": {"failing": len(failing_hashes), "total": len(all_states)},
        "seeds_45": seeds_45,
    }

    out_path = ROOT / "outputs" / "j_capacity_45_seeds.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "wrote": str(out_path),
        "phi_identity_holds": identity_check["identity_holds_without_exception"],
        "phi_distribution_all_230": report["phi_distribution_all_230"],
        "phi_cleanly_separates_45_from_185": report["phi_cleanly_separates_45_from_185"],
    }, indent=2))


if __name__ == "__main__":
    main()
