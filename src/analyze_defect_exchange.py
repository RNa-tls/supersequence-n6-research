#!/usr/bin/env python3
"""RA2 <-> A2R defect-order exchange: corpus construction, adjacent
exchange truth table, zero-charge-word-mediated bubble-sort exchange, and
obstruction classification.

Definitions (four exchange strength levels, weakest to strongest):
 1. literal commutation: firing A2's exact move then R's exact move (same
    move objects, in swapped order) from the same starting boundary
    reaches a state whose literal p equals the original's literal p.
 2. canonical-state commutation: the two orders reach the SAME canonical
    (left-S6-relabeled) state.
 3. continuation-equivalence commutation: the two orders reach states
    with isomorphic future legal-continuation trees (need not be
    literally/canonically identical, but the same completion prospects).
 4. defect-ledger-only commutation: the two orders merely produce the
    same MULTISET of resource deltas (P/F/S/H/O/D/Ndef totals) -- the
    weakest notion, ignoring literal state entirely.

This script tests levels 1-2 directly (computable); level 3 is tested via
the depth-2 abstracted-signature method already validated in
RA2_FOUR_SURVIVORS.md; level 4 is immediate from Phi/debt bookkeeping.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
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


macro = _load("ade_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
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


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def locate_events(witness: Dict[str, Any]) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Replay the witness and return (r_idx, a2_idx, steps) where steps[i]
    holds {pre_joint, transition, ell, kind} for every macro-edge."""
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    steps = []
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        pre_joint = cur
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        cur = exact.canonicalize(tr.state)
        steps.append({"ell": ell, "pre_joint": pre_joint, "transition": tr, "kind": joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)})
    r_idx = next(i for i, s in enumerate(steps) if s["kind"] == "R")
    a2_idx = next(i for i, s in enumerate(steps) if s["kind"] == "A2")
    return r_idx, a2_idx, steps


def depth2_signature(state: "exact.ExactState", edge_cap: int = 3000) -> List[Any]:
    out = []
    frontier = deque([(0, state)])
    edges = 0
    while frontier and edges < edge_cap:
        d, s = frontier.popleft()
        if d >= 2:
            continue
        for e in macro.macro_edges(s):
            edges += 1
            tr = e.joint
            if tr.abandonment:
                continue
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            out.append((d, e.run.ell, tr.move.weight, tr.new_orbit, tr.state.P - state.P, tr.state.O - state.O, tr.state.Ndef - state.Ndef))
            frontier.append((d + 1, tr.state))
    return sorted(out)


def adjacent_exchange_test(witness: Dict[str, Any]) -> Dict[str, Any]:
    """Section 3: for witnesses where R and A2 are macro-adjacent
    (zero_charge_word_length == 0), test whether firing A2's exact move
    then R's exact move, from the SAME pre-R boundary, is legal and what
    it reaches."""
    r_idx, a2_idx, steps = locate_events(witness)
    adjacent = (a2_idx == r_idx + 1)
    result: Dict[str, Any] = {"r_idx": r_idx, "a2_idx": a2_idx, "adjacent": adjacent}
    if not adjacent:
        return result

    pre_r = steps[r_idx]["pre_joint"]  # state right before R fires (after its own rotation run)
    r_tr = steps[r_idx]["transition"]
    a2_step = steps[a2_idx]
    a2_move = a2_step["transition"].move
    a2_ell = a2_step["ell"]

    # Attempt: from pre_r, run a2_ell rotations, then fire A2's exact move (swapped order)
    p = pre_r
    ok = True
    for _ in range(a2_ell):
        step = exact.extend(p, W1)
        if step is None:
            ok = False
            break
        p = step.state
    if not ok:
        result["swap_legal"] = False
        result["reason"] = "rotation collision before A2's own ell could be replayed from R's boundary"
        return result

    tr_a2_first = exact.extend(p, a2_move)
    if tr_a2_first is None or not tr_a2_first.abandonment:
        result["swap_legal"] = False
        result["reason"] = "A2's own move is not a legal abandonment from R's pre-boundary"
        return result

    # then attempt R's own move from there
    r_move = r_tr.move
    tr_r_second = exact.extend(tr_a2_first.state, r_move)
    if tr_r_second is None:
        result["swap_legal_A2_only"] = True
        result["swap_legal_full"] = False
        result["reason"] = "A2 succeeded but R's own move is illegal immediately after (collision or target already visited)"
        return result

    original_final = exact.canonicalize(steps[a2_idx]["transition"].state)
    swapped_final = exact.canonicalize(tr_r_second.state)
    result["swap_legal_full"] = True
    result["original_canonical_hash"] = macro.stable_hash(original_final)
    result["swapped_canonical_hash"] = macro.stable_hash(swapped_final)
    result["level2_canonical_state_commutation"] = result["original_canonical_hash"] == result["swapped_canonical_hash"]
    if result["level2_canonical_state_commutation"]:
        result["level1_literal_commutation"] = list(original_final.p) == list(swapped_final.p)
    else:
        sig_orig = depth2_signature(original_final)
        sig_swap = depth2_signature(swapped_final)
        result["level3_continuation_equivalence"] = sig_orig == sig_swap
    return result


def full_reorder_search(witness: Dict[str, Any], node_cap: int, max_extra_depth: int) -> Dict[str, Any]:
    """Section 4: from the true initial state, ask whether A2 could have
    fired BEFORE R at all (i.e. is a fully-reordered A2R-consistent
    prefix reachable), bounded -- reusing the same raw-BFS method as
    search_a2r_minimum_depth.py, capped shallow since this is a per-witness
    check, not a fresh large search."""
    root = exact.initial_state()
    frontier = deque([(0, root, ())])
    expanded = 0
    while frontier and expanded < node_cap:
        depth, state, events = frontier.popleft()
        if depth >= max_extra_depth:
            continue
        expanded += 1
        for e in macro.macro_edges(state):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if kind == "A2":
                return {"a2_first_reachable_within_bound": True, "depth": depth + 1, "nodes_expanded": expanded}
            new_events = events + (kind,) if kind in ("A2", "A3", "R", "J") else events
            if new_events:
                continue  # only extend prefixes with zero counted events so far
            frontier.append((depth + 1, tr.state, new_events))
    return {"a2_first_reachable_within_bound": False, "nodes_expanded": expanded, "frontier_remaining": len(frontier)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_a2r_exchange_table.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]

    # section 4's "can A2 fire before R at all" is boundary-independent
    # (depends only on the initial state, not on the specific witness) --
    # compute it once, reusing the exact same fact already established in
    # A2_ROTATION_LENGTH_CLASSIFICATION.md / search_a2r_minimum_depth.py.
    global_a2_first = full_reorder_search(ra2["witnesses"][0], node_cap=50_000, max_extra_depth=5)

    results = {}
    for w in ra2["witnesses"]:
        adj = adjacent_exchange_test(w)
        results[w["target_hash"]] = {
            "group": "U4" if w["target_hash"] in U4_HASHES else "C20",
            "adjacent_exchange_test": adj,
        }
        print(w["target_hash"][:12], adj.get("adjacent"), adj.get("swap_legal_full", adj.get("swap_legal")))

    report = {
        "schema": "ra2-a2r-exchange-table-v1",
        "exchange_level_definitions": {
            "1_literal_commutation": "swapped order reaches the identical literal endpoint permutation",
            "2_canonical_state_commutation": "swapped order reaches the same canonical (left-S6) state",
            "3_continuation_equivalence": "swapped order's canonical state has an isomorphic depth-2 abstracted continuation signature",
            "4_defect_ledger_only": "swapped order merely matches total P/F/S/H/O/D/Ndef deltas (weakest, not separately computed -- implied by Phi/debt bookkeeping already established)",
        },
        "global_a2_first_from_true_initial_state": global_a2_first,
        "adjacent_exchange_results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "global_a2_first": global_a2_first}, indent=2))


if __name__ == "__main__":
    main()
