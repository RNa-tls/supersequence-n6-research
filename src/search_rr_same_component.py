#!/usr/bin/env python3
"""Round 13, sections 7-8, 11: Phi=0 continuation analysis and bounded
exact closure attempt for the 10 same-component RR witnesses.

Section 7-8: since F=1 is already spent (RR's one allowed abandonment
already fired) and Phi=0 exactly at R2's boundary, EVERY subsequent
joint is forced to be non-abandoning (blocked) -- this is a direct
consequence of the ALREADY-PROVEN F<=1 budget (an abandoning joint
requires its own rotation successor unvisited, but F=1 already used up
the one allowed abandonment; any further abandoning transition is
pruned as F_exceeded, verified directly against area_a_prune_reason()).
Given every remaining joint targets a freshly-entered hex and sweeps it
completely (ell=5 forced, by the same F<=1 argument as the established
"post-F1 blocked-only" lemma), Phi's own monotonicity
(Phi(S')=Phi(S)+(ell-5)) means Phi stays at exactly 0 for as long as
this holds -- consistent, not contradictory, with completion.

Section 11: bounded (node-capped, NOT exhaustive in general -- these
seeds have large branching) exact search from each of the 10
same-component witnesses' post-R2 state toward the actual completion
target (area_a_final). Reuses existing macro_edges()/
area_a_prune_reason() machinery, comparable in scale to prior rounds'
single-state bounded searches (e.g. RA2's depth<=18/edge_cap=1.5M
attempts) -- explicitly NOT claimed exhaustive unless the frontier is
observed to fully empty.
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


macro = _load("srsc_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def replay_to_post_r2(witness: Dict[str, Any]) -> "exact.ExactState":
    path = witness["macro_path"]
    cur = exact.initial_state()
    r_count = 0
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        cur = tr.state
        if kind == "R":
            r_count += 1
            if r_count == 2:
                return cur
    raise AssertionError("no R2 found")


def bounded_closure_search(state: "exact.ExactState", node_cap: int) -> Dict[str, Any]:
    start_phi = phi(state)
    frontier = deque([state])
    expanded = 0
    terminal_reasons: Dict[str, int] = {}
    hub_touch_seen = 0
    non_ell5_seen = 0
    success = False
    success_example: Optional[List[str]] = None
    while frontier and expanded < node_cap:
        st = frontier.popleft()
        expanded += 1
        if macro.area_a_final(st, macro.AREA_A):
            success = True
            break
        edges = list(macro.macro_edges(st))
        legal = []
        for e in edges:
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                terminal_reasons[reason] = terminal_reasons.get(reason, 0) + 1
                continue
            if e.run.ell != 5:
                non_ell5_seen += 1
            if tr.target is not None and core.hexagon_id(tr.target) == 0:
                hub_touch_seen += 1
            legal.append(tr.state)
        if not legal:
            terminal_reasons["no_legal_children"] = terminal_reasons.get("no_legal_children", 0) + 1
            continue
        for child in legal:
            if phi(child) < 0:
                terminal_reasons["phi_negative_should_be_impossible"] = terminal_reasons.get("phi_negative_should_be_impossible", 0) + 1
                continue
            frontier.append(child)
    return {
        "start_phi": start_phi,
        "nodes_expanded": expanded, "frontier_remaining": len(frontier),
        "exhaustive": len(frontier) == 0 and not success,
        "success": success,
        "non_ell5_transitions_ever_legal": non_ell5_seen,
        "hub_hexagon_touches_seen": hub_touch_seen,
        "terminal_reasons": terminal_reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--node-cap", type=int, default=30000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_same_component_exact_search.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    table = json.loads(Path(args.relation_table).read_text(encoding="utf-8"))
    same_hashes = [r["hash"] for r in table["rows"] if r.get("r2_own_component_relation") == "same"]
    print(f"bounded closure search from {len(same_hashes)} same-component witnesses' post-R2 state, node_cap={args.node_cap}")

    results = {}
    for h in same_hashes:
        w = wdata["witnesses"][h]
        post_r2 = replay_to_post_r2(w)
        search = bounded_closure_search(post_r2, args.node_cap)
        results[h] = search
        print(h[:12], "phi=", search["start_phi"], "nodes", search["nodes_expanded"],
              "exhaustive", search["exhaustive"], "success", search["success"],
              "non_ell5_ever_legal", search["non_ell5_transitions_ever_legal"],
              "hub_touches_seen", search["hub_hexagon_touches_seen"])

    report = {
        "schema": "rr-same-component-exact-search-v1",
        "method": (
            f"bounded BFS (node_cap={args.node_cap} PER witness) from each of the 10 "
            "same-component witnesses' post-R2 state, toward actual completion "
            "(area_a_final) -- reuses macro_edges()/area_a_prune_reason(), NOT claimed "
            "exhaustive unless frontier fully empties without success (checked per witness)."
        ),
        "per_witness": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
