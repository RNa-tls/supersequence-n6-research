#!/usr/bin/env python3
"""A2 rotation-length (ell_A2) spectrum: theoretical classification plus a
bounded search for the corpus-unobserved value ell_A2=2.

Established facts this builds on (RA2_ZERO_CHARGE_HISTORY.md):
Phi(post-A2) = 1 + ell_A2 = 6 - fragment_debt, exact. ell_A2=5 is
structurally impossible (a full hex's rotation successor is always
already visited, forcing abandonment=False, so A2 -- which requires
abandonment=True -- cannot have ell=5). Observed in the 24-state RA2
corpus: ell_A2 in {0:1, 1:18, 3:1, 4:4} -- ell_A2=2 is unobserved.

This script:
 1. classifies ell_A2=5 as structurally impossible (re-derivation, not
    just citation).
 2. runs a genuine bounded local search (not a blind U4 deepening -- a
    fresh search from R-event configurations, since the question is about
    ell_A2=2's existence anywhere in RA2, not specifically in U4) for a
    witness with ell_A2=2. Reports FOUND (with witness) or NOT FOUND
    WITHIN BOUND -- never conflates "not found in bounded search" with
    "impossible".
 3. for each observed and newly found ell_A2 value, extracts the exact
    post-A2 boundary normal form (endpoint, abandoned arc, target orbit/
    phase, P/F/S/H/O/D/Ndef, Phi, orbit slack).
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


macro = _load("a2rl_macro", "superperm_partial_f1_macro.py")
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


def theoretical_ell5_impossibility() -> Dict[str, Any]:
    return {
        "claim": "ell_A2 = 5 is structurally impossible",
        "status": "PROVEN (re-derived here, not just cited)",
        "argument": (
            "f1_normal_form forces the current hex (F=0 regime) to be a "
            "single contiguous arc. After ell=5 rotations from a fresh "
            "landing, that arc has length 6 = the full hexagon. Its "
            "rotation successor would need to revisit the arc's own start "
            "-- already visited by construction -- forcing "
            "abandonment=False (extend()'s formula). A2 is defined as "
            "abandonment=True, so no move fired at ell=5 can be A2."
        ),
    }


def boundary_normal_form(state: "exact.ExactState", target_hexagon_of_a2: int) -> Dict[str, Any]:
    form = exact.f1_normal_form(state)
    q, phase = exact.ORBIT_PHASE[state.p]
    non_full = [
        {"hex": h, "mask": mask, "components": list(exact.cyclic_components(mask))}
        for h, mask in enumerate(state.hex_masks) if mask not in (0, exact.FULL_HEX)
    ]
    return {
        "endpoint": list(state.p),
        "endpoint_orbit_q": q, "endpoint_phase": phase,
        "fragment_hex": form.fragment_hex if form else None,
        "fragment_components": [list(c) for c in form.fragment_components] if form else None,
        "current_hex": state.current_hex,
        "non_full_hexagon_masks": non_full,
        "P": state.P, "F": state.F, "S": state.S, "H": state.H,
        "O": state.O, "D": state.D, "Ndef": state.Ndef,
        "visited_count": state.visited_count,
        "phi": phi(state), "orbit_slack": orbit_slack(state),
    }


def find_ell2_witness(node_cap: int, max_depth: int) -> Optional[Dict[str, Any]]:
    """Bounded raw BFS from the true initial state, looking for ANY legal
    RA2-consistent path (exactly R then A2, zero-charge word of blocked
    joints in between) where A2's own preceding rotation length is
    exactly 2. Not limited to U4's specific R-event -- this asks whether
    ell_A2=2 exists ANYWHERE in the RA2 family, which is the actual
    question (U4 is a fixed R/A2-identical family; a different R could in
    principle open the door to ell_A2=2)."""
    root = exact.initial_state()

    def joint_kind(weight, abandonment, new_orbit):
        return {
            (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
        }.get((weight, abandonment, new_orbit), "?")

    frontier = deque([(0, root, [], ())])
    expanded = 0
    while frontier and expanded < node_cap:
        depth, state, path, events = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        for e in macro.macro_edges(state):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            new_events = events + (kind,) if kind in ("A2", "A3", "R", "J") else events
            if len(new_events) > 2 or (len(new_events) >= 1 and new_events[0] != "R"):
                continue
            new_path = path + [e.label]
            if new_events == ("R", "A2") and e.run.ell == 2:
                return {
                    "found": True, "depth": depth + 1, "macro_path": new_path,
                    "final_state_json": exact.state_to_json(tr.state), "nodes_expanded": expanded,
                }
            frontier.append((depth + 1, tr.state, new_path, new_events))
    return {"found": False, "nodes_expanded": expanded, "frontier_remaining": len(frontier)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--ell2-search-node-cap", type=int, default=300_000)
    parser.add_argument("--ell2-search-max-depth", type=int, default=6)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_a2_length_spectrum.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    move_by_label_local = move_by_label

    observed = {}
    for w in ra2["witnesses"]:
        path = w["macro_path"]
        a2_label = path[-1]["edge_label"]
        ell = int(a2_label.split(";")[0][len("rot^"):])
        state = exact.state_from_json(w["final_state_json"])
        observed.setdefault(ell, []).append({
            "target_hash": w["target_hash"],
            "boundary_normal_form": boundary_normal_form(state, 0),
        })

    ell5_theory = theoretical_ell5_impossibility()

    print("searching for ell_A2=2 witness (bounded)...")
    ell2_result = find_ell2_witness(args.ell2_search_node_cap, args.ell2_search_max_depth)
    print(json.dumps({k: v for k, v in ell2_result.items() if k != "final_state_json"}, indent=2))

    ell2_normal_form = None
    if ell2_result.get("found"):
        st = exact.state_from_json(ell2_result["final_state_json"])
        ell2_normal_form = boundary_normal_form(st, 0)

    report = {
        "schema": "ra2-a2-length-spectrum-v1",
        "observed_in_24_state_corpus": {str(k): len(v) for k, v in observed.items()},
        "ell5_impossibility": ell5_theory,
        "ell2_search": {k: v for k, v in ell2_result.items() if k != "final_state_json"},
        "ell2_witness_boundary_normal_form": ell2_normal_form,
        "boundary_normal_forms_by_ell": observed,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "ell2_found": ell2_result.get("found")}, indent=2))


if __name__ == "__main__":
    main()
