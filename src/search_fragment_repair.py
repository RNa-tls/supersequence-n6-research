#!/usr/bin/env python3
"""Fragment repair: exact transition classification (sections 3+5) and a
bounded "repair cone" search for U4 (section 6) -- search only until
fragment debt first reaches 0, not full completion.

Central fact this reuses (proved and verified exactly over all 24 RA2
witnesses in analyze_ra2_zero_charge_history.py / RA2_ZERO_CHARGE_HISTORY.md):
while F=0, every legal joint requires its OWN current hex to already be
FULL (a direct consequence of f1_normal_form's single-contiguous-arc
constraint plus the abandonment formula) -- so the zero-charge word before
A2 always uses ell=5 throughout, and the eventual fragment debt is fixed
entirely by A2's own preceding rotation length: debt = 5 - ell_A2, and
Phi(post-A2) = 1 + ell_A2 = 6 - debt exactly (verified 24/24).

Terminal fragment condition (section 5, re-derived from area_a_final):
completion requires visited_count == 720, i.e. EVERY hexagon full,
including whatever is currently the fragment. A pure-rotation suffix can
only ever complete the CURRENT hex (rotation never leaves the current
hex), so a fragment can only be closed by a future JOINT re-entering it
-- fragment debt must reach exactly 0 before the walk's own terminal
state, and cannot be "absorbed" by the final endpoint or by any
rotation-only mechanism.
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


macro = _load("sfr_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def d_frag(state: "exact.ExactState") -> int:
    form = exact.f1_normal_form(state)
    if form is None or form.fragment_hex is None:
        return 0
    return 6 - bin(state.hex_masks[form.fragment_hex]).count("1")


def orbit_slack(state: "exact.ExactState") -> int:
    return exact.TARGET_O - state.O


def classify_transition(before: "exact.ExactState", edge) -> str:
    """Classify a legal macro-edge by its effect on fragment debt."""
    d0 = d_frag(before)
    d1 = d_frag(edge.joint.state)
    if d0 == 0 and d1 == 0:
        return "fragment_irrelevant"
    if d1 < d0:
        return "debt_decrease"
    if d1 > d0:
        return "debt_increase"
    return "debt_unchanged"


def repair_cone_search(seed: "exact.ExactState", node_cap: int) -> Dict[str, Any]:
    """BFS from a post-A2 (debt>0) state, terminating each branch at the
    first of: debt==0 (a repair witness), Phi<0, debt>=2 more than the
    start (a debt-increase event, tracked but not necessarily terminal),
    a legality prune, or no legal children. Reports the shallowest
    witness(es) found, NOT overall completion feasibility."""
    d_start = d_frag(seed)
    frontier = deque([(0, seed, [])])
    nodes = 0
    witnesses = []
    terminal_reasons: Dict[str, int] = {}
    debt_increase_events = 0
    while frontier and nodes < node_cap:
        depth, state, path = frontier.popleft()
        nodes += 1
        any_child = False
        for e in macro.macro_edges(state):
            tr = e.joint
            if tr.abandonment:
                terminal_reasons["abandonment_illegal_post_f1"] = terminal_reasons.get("abandonment_illegal_post_f1", 0) + 1
                continue
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                terminal_reasons[reason] = terminal_reasons.get(reason, 0) + 1
                continue
            any_child = True
            new_path = path + [e.label]
            d1 = d_frag(tr.state)
            if d1 == 0:
                witnesses.append({
                    "macro_distance": depth + 1,
                    "macro_path": new_path,
                    "phi_consumed": phi(state) - phi(tr.state),
                    "orbit_slack_consumed": orbit_slack(state) - orbit_slack(tr.state),
                    "phi_after_repair": phi(tr.state),
                    "orbit_slack_after_repair": orbit_slack(tr.state),
                })
                continue
            if d1 > d_start:
                debt_increase_events += 1
                terminal_reasons["debt_increase_pruned"] = terminal_reasons.get("debt_increase_pruned", 0) + 1
                continue
            frontier.append((depth + 1, tr.state, new_path))
        if not any_child:
            terminal_reasons["no_legal_children"] = terminal_reasons.get("no_legal_children", 0) + 1
    return {
        "d_frag_start": d_start,
        "nodes_expanded": nodes,
        "witnesses_found": len(witnesses),
        "shallowest_witnesses": sorted(witnesses, key=lambda w: w["macro_distance"])[:3],
        "terminal_reason_counts": terminal_reasons,
        "debt_increase_events_seen": debt_increase_events,
        "frontier_exhausted": len(frontier) == 0,
    }


def classification_summary(seed: "exact.ExactState", depth: int, edge_cap: int) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    frontier = deque([(0, seed)])
    edges = 0
    while frontier and edges < edge_cap:
        d, s = frontier.popleft()
        if d >= depth:
            continue
        for e in macro.macro_edges(s):
            tr = e.joint
            if tr.abandonment:
                continue
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            edges += 1
            cls = classify_transition(s, e)
            counts[cls] = counts.get(cls, 0) + 1
            frontier.append((d + 1, tr.state))
            if edges >= edge_cap:
                break
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--node-cap", type=int, default=100_000)
    parser.add_argument("--classification-depth", type=int, default=3)
    parser.add_argument("--classification-edge-cap", type=int, default=20_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_repair_cones.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    u4_hashes = {
        "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
        "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
        "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
        "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
    }

    results = {}
    for w in ra2["witnesses"]:
        if w["target_hash"] not in u4_hashes:
            continue
        state = exact.state_from_json(w["final_state_json"])
        cone = repair_cone_search(state, args.node_cap)
        cls = classification_summary(state, args.classification_depth, args.classification_edge_cap)
        results[w["target_hash"]] = {"repair_cone": cone, "transition_classification_depth3": cls}
        print(w["target_hash"][:12], "witnesses:", cone["witnesses_found"], "nodes:", cone["nodes_expanded"])

    report = {
        "schema": "ra2-repair-cones-v1",
        "terminal_fragment_condition": (
            "area_a_final requires visited_count==720 (every hexagon full); "
            "a pure-rotation suffix can only complete the CURRENT hex (rotation "
            "never leaves current), so a fragment must be re-entered by a future "
            "joint and its debt driven to exactly 0 -- it cannot be skipped, "
            "absorbed by the endpoint, or left for the trailing rotation suffix."
        ),
        "results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
