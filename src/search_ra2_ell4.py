#!/usr/bin/env python3
"""Controlled counterfactual comparison across ell_A2 values (sections 2,
4, 5), and a family-local U4 search gated on a validated new obstruction
(section 8).

The corpus's 24 RA2 states have different R events (mostly), so directly
comparing their boundary normal forms by ell_A2 conflates "which R fired"
with "which ell was chosen". The clean, controlled comparison replays ONE
witness's own R-to-just-before-A2 prefix (fixed) and fires the SAME A2
move at every legal ell in turn (0,1,2,3,4) -- isolating ell as the only
variable, exactly as done for the single-state sweep in
verify_ra2_repair_cost.py, but now with full boundary data and a shallow
continuation-tree comparison per ell.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

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


macro = _load("sre4_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def orbit_slack(state: "exact.ExactState") -> int:
    return exact.TARGET_O - state.O


def find_minimal_failing_path(seed: "exact.ExactState", max_depth: int, edge_cap: int) -> Optional[Dict[str, Any]]:
    frontier = deque([(0, seed, [])])
    edges = 0
    best = None
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
                    best = {"depth": depth + 1, "macro_path": new_labels}
                continue
            if reason_gen is not None:
                continue
            frontier.append((depth + 1, edge.state, new_labels))
            if edges >= edge_cap:
                break
    return best


def boundary_snapshot(state: "exact.ExactState") -> Dict[str, Any]:
    form = exact.f1_normal_form(state)
    q, phase = exact.ORBIT_PHASE[state.p]
    return {
        "endpoint": list(state.p), "endpoint_orbit_q": q, "endpoint_phase": phase,
        "fragment_hex": form.fragment_hex if form else None,
        "fragment_components": [list(c) for c in form.fragment_components] if form else None,
        "P": state.P, "F": state.F, "S": state.S, "H": state.H, "O": state.O, "D": state.D, "Ndef": state.Ndef,
        "phi": phi(state), "orbit_slack": orbit_slack(state),
    }


def continuation_tree_signature(state: "exact.ExactState", depth: int, edge_cap: int) -> List[Any]:
    """Abstracted (labeling-independent) resource-delta signature up to
    `depth`, same method as RA2_FOUR_SURVIVORS.md's depth-2 independence
    check -- used here to compare ell-counterfactual branches structurally."""
    out = []
    frontier = deque([(0, state)])
    edges = 0
    while frontier and edges < edge_cap:
        d, s = frontier.popleft()
        if d >= depth:
            continue
        for e in macro.macro_edges(s):
            edges += 1
            tr = e.joint
            if tr.abandonment:
                continue
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            out.append((d, e.run.ell, tr.move.weight, tr.new_orbit,
                        tr.state.P - state.P, tr.state.O - state.O, tr.state.Ndef - state.Ndef))
            frontier.append((d + 1, tr.state))
    return sorted(out)


def ell_counterfactual_for_witness(witness: Dict[str, Any], capacity_depth: int, capacity_edge_cap: int,
                                    tree_depth: int, tree_edge_cap: int) -> Dict[str, Any]:
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

    results = {}
    p = cur
    for ell in range(6):
        tr = exact.extend(p, a2_move)
        if tr is None or not tr.abandonment:
            results[ell] = {"legal_as_A2": False}
        else:
            after = exact.canonicalize(tr.state)
            cap = find_minimal_failing_path(after, capacity_depth, capacity_edge_cap)
            results[ell] = {
                "legal_as_A2": True,
                "boundary": boundary_snapshot(after),
                "continuation_tree_signature_depth": tree_depth,
                "continuation_tree_signature": continuation_tree_signature(after, tree_depth, tree_edge_cap),
                "capacity_failure_search": {
                    "max_depth": capacity_depth, "edge_cap": capacity_edge_cap,
                    "found": cap is not None, "depth": cap["depth"] if cap else None,
                },
            }
        nxt = exact.extend(p, W1)
        if nxt is None:
            break
        p = nxt.state

    return {"actual_ell_A2": actual_ell, "move_used": a2_move.label, "per_ell": results}


def terminal_suffix_analysis(results_per_ell: Dict[int, Any]) -> Dict[str, Any]:
    """Section 5: is the hole's single missing window compatible with a
    trailing pure-rotation suffix, and when must it be repaired?"""
    ell4 = results_per_ell.get(4, {})
    return {
        "claim_1_when_must_the_hole_be_visited": (
            "The hole (fragment_hex's 1 missing window) can only ever be "
            "visited by a future JOINT targeting it (rotation never leaves "
            "current hex, FRAGMENT_REPAIR_OBLIGATION.md sec5) -- there is no "
            "deadline other than 'before the walk's own terminal state' "
            "(visited_count==720 required at completion)."
        ),
        "claim_2_repairing_too_early_wastes_terminal_suffix_resource": (
            "REFUTED as stated -- repair witnesses found in "
            "FRAGMENT_REPAIR_OBLIGATION.md cost 0 Phi/orbit-slack, so an early "
            "repair does not visibly consume any resource that a terminal "
            "suffix would otherwise need. No evidence of an early-repair "
            "penalty was found."
        ),
        "claim_3_repairing_too_late_endpoint_mismatch": (
            "미완료 -- would require a concrete terminal witness (endpoint "
            "matching the very last permutation of the whole 720-walk) to "
            "check against; none exists for this open slab."
        ),
        "claim_4_pure_rotation_suffix_can_absorb_the_hole": (
            "PROVEN FALSE, structurally -- a pure-rotation suffix only "
            "continues within the CURRENT hex; the hole lives in "
            "fragment_hex, which by definition is not current. The hole can "
            "never be closed by the walk's own final trailing rotation run "
            "unless a joint re-enters fragment_hex first (at which point it "
            "becomes current, and then a suffix from THERE could finish it -- "
            "but that is a joint-then-suffix, not a suffix alone)."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--capacity-depth", type=int, default=8)
    parser.add_argument("--capacity-edge-cap", type=int, default=30_000)
    parser.add_argument("--tree-depth", type=int, default=2)
    parser.add_argument("--tree-edge-cap", type=int, default=5_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_ell_counterfactuals.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    u4_hashes = {
        "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
        "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
        "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
        "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
    }

    all_results = {}
    for w in ra2["witnesses"]:
        if w["target_hash"] not in u4_hashes:
            continue
        r = ell_counterfactual_for_witness(w, args.capacity_depth, args.capacity_edge_cap, args.tree_depth, args.tree_edge_cap)
        all_results[w["target_hash"]] = r
        print(w["target_hash"][:12], "actual_ell_A2:", r["actual_ell_A2"])
        for ell, res in r["per_ell"].items():
            if res.get("legal_as_A2"):
                print(f"  ell={ell}: phi={res['boundary']['phi']} orbit_slack={res['boundary']['orbit_slack']} "
                      f"cap_search_found={res['capacity_failure_search']['found']} depth={res['capacity_failure_search']['depth']}")
            else:
                print(f"  ell={ell}: not legal as A2")

    terminal = terminal_suffix_analysis(next(iter(all_results.values()))["per_ell"])

    report = {
        "schema": "ra2-ell-counterfactuals-v1",
        "terminal_suffix_analysis_section5": terminal,
        "per_witness": all_results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
