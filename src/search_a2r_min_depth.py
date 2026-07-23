#!/usr/bin/env python3
"""A2R: theoretical status and minimum-depth search.

A2R = A2 (abandonment, weight 2, existing-orbit target) followed by R
(blocked, weight 3, existing-orbit target), with only zero-charge joints
between them. Zero instances were observed among the 25,660 F=1,H=0,N=2
depth<=6 bounded-frontier states this corpus recorded -- but, per this
corpus's own PARTIAL_F1_N2_TWO_DEFECT_LEMMA.md, that was never claimed to
be a proof of impossibility, only non-observation.

Resource-budget check (cheap, done first): A2 spends the walk's one
allowed abandonment (F: 0->1). R requires abandonment=False, which is
just "the natural rotation successor of the current position happens to
already be visited" -- nothing in the F/N budget forbids this occurring
AFTER an A2. So A2R is not excluded by the same argument that kills
A2A2/A2A3/A3A2/A3A3 (those need a second abandonment; A2R does not). This
is not a proof A2R is reachable, only that the easy F-budget argument does
not rule it out -- so if A2R is impossible, the reason must be more subtle
(specific to which E-orbit/hexagon state an A2 leaves behind).

This script: (1) BFS-searches from the initial state for canonical states
whose defect history is exactly the single event A2 (i.e. "word=A2" at
the N=1 level, the natural predecessor state family to look for A2R
starts), then (2) from each, searches for the shallowest reachable R event
completing an A2R word, within stated bounds.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
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


macro = _load("a2r_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def find_a2_only_states(max_depth: int, node_cap: int) -> List["exact.ExactState"]:
    """Canonical-memoized BFS from the identity for states whose entire
    positive-charge history is exactly one A2 event (i.e. genuine
    'word=A2' states, the natural starting points for A2R)."""
    root = exact.canonicalize(exact.initial_state())
    root_hash = macro.stable_hash(root)
    seen = {root_hash}
    frontier = deque([(0, root, ())])  # (depth, state, event_kinds_so_far)
    found: List["exact.ExactState"] = []
    expanded = 0
    while frontier and expanded < node_cap:
        depth, state, events = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        for edge in macro.macro_edges(state):
            tr = edge.joint
            # area_a_prune_reason already checks F_exceeded internally, so
            # it is safe to call unconditionally (covers abandoning and
            # non-abandoning joints alike).
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            new_events = events + (kind,) if kind in ("A2", "A3", "R", "J") else events
            if len(new_events) > 1:
                continue  # more than one positive event already -- not an "A2-only" prefix
            canon = exact.canonicalize(tr.state)
            ch = macro.stable_hash(canon)
            if ch in seen:
                continue
            seen.add(ch)
            if new_events == ("A2",):
                found.append(canon)
            frontier.append((depth + 1, canon, new_events))
    return found


def search_for_r_from(state: "exact.ExactState", max_depth: int, edge_cap: int) -> Optional[Dict[str, Any]]:
    """From an A2-only state, raw BFS for the shallowest reachable R event
    (word A2R). Also tracks whether the search space was exhausted
    (CLOSED-like) within bound, or merely capped (INCOMPLETE)."""
    frontier = deque([(0, state, [])])
    edges = 0
    while frontier:
        if edges >= edge_cap:
            return {"found": False, "reason": "edge_cap_hit", "frontier_remaining": len(frontier)}
        depth, s, path = frontier.popleft()
        if depth >= max_depth:
            continue
        any_child = False
        for edge in macro.macro_edges(s):
            any_child = True
            edges += 1
            tr = edge.joint
            if tr.abandonment:
                continue  # F budget already spent by the A2; any further abandonment is illegal
            if phi(tr.state) < 0:
                continue
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            new_path = path + [edge.label]
            if kind == "R":
                return {"found": True, "depth": depth + 1, "macro_path": new_path}
            frontier.append((depth + 1, tr.state, new_path))
        if edges >= edge_cap:
            return {"found": False, "reason": "edge_cap_hit", "frontier_remaining": len(frontier)}
    return {"found": False, "reason": "frontier_exhausted_no_R_found", "frontier_remaining": 0}


def raw_bfs_minimum_a2r_depth(max_depth: int, node_cap: int) -> Optional[Dict[str, Any]]:
    """Raw (uncanonicalized) BFS from the true initial state for the
    shallowest total macro-depth at which the word A2R (exactly the two
    positive-charge events A2 then R, in that order, with only zero-charge
    joints between/around them) first occurs. This is a direct minimum-depth
    witness search, independent of the canonical-memoized find_a2_only_states
    path above -- canonicalization is expensive (~20-25 states/sec) and
    unnecessary for a single existence witness, so this uses the raw engine
    (~3,300 edges/sec) instead, matching the corpus's own recorded depth<=6
    bound so the result is directly comparable to the 0-observed-in-corpus
    fact this is investigating."""
    root = exact.initial_state()
    frontier = deque([(0, root, [], ())])  # (depth, state, path_labels, event_kinds)
    expanded = 0
    while frontier and expanded < node_cap:
        depth, state, path_labels, events = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        for edge in macro.macro_edges(state):
            tr = edge.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            new_events = events + (kind,) if kind in ("A2", "A3", "R", "J") else events
            if len(new_events) > 2:
                continue
            if tuple(new_events[:1]) not in ((), ("A2",)):
                continue  # only keep prefixes consistent with the target word A2R
            new_path = path_labels + [edge.label]
            if new_events == ("A2", "R"):
                return {
                    "found": True,
                    "depth": depth + 1,
                    "macro_path": new_path,
                    "final_state_json": exact.state_to_json(tr.state),
                    "nodes_expanded": expanded,
                }
            frontier.append((depth + 1, tr.state, new_path, new_events))
    return {"found": False, "nodes_expanded": expanded, "frontier_remaining": len(frontier)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a2-search-depth", type=int, default=6)
    parser.add_argument("--a2-search-node-cap", type=int, default=20000)
    parser.add_argument("--r-search-depth", type=int, default=10)
    parser.add_argument("--r-search-edge-cap", type=int, default=100000)
    parser.add_argument("--max-a2-roots", type=int, default=20)
    parser.add_argument("--raw-bfs-max-depth", type=int, default=6)
    parser.add_argument("--raw-bfs-node-cap", type=int, default=200000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "a2r_search.json"))
    args = parser.parse_args()

    t0 = time.time()
    a2_states = find_a2_only_states(args.a2_search_depth, args.a2_search_node_cap)
    print(f"found {len(a2_states)} distinct canonical 'word=A2' states within depth<={args.a2_search_depth}, "
          f"node_cap={args.a2_search_node_cap} ({time.time()-t0:.1f}s)")

    results = []
    for state in a2_states[: args.max_a2_roots]:
        h = macro.stable_hash(state)
        r = search_for_r_from(state, args.r_search_depth, args.r_search_edge_cap)
        results.append({"a2_state_hash": h, "phi": phi(state), "result": r})
        print(h[:12], r)

    found_any = any(r["result"]["found"] for r in results)

    t1 = time.time()
    raw_bfs_result = raw_bfs_minimum_a2r_depth(args.raw_bfs_max_depth, args.raw_bfs_node_cap)
    print(f"raw BFS minimum-depth A2R search: {raw_bfs_result.get('found')} "
          f"(depth={raw_bfs_result.get('depth')}, {time.time()-t1:.1f}s)")

    report = {
        "schema": "a2r-search-v1",
        "config": vars(args),
        "a2_only_states_found": len(a2_states),
        "a2_roots_searched": len(results),
        "a2r_found_in_any_root": found_any,
        "results": results,
        "raw_bfs_minimum_depth_search": raw_bfs_result,
        "resource_budget_argument": (
            "A2 spends the walk's one allowed abandonment (F: 0->1). R requires "
            "abandonment=False only, which the F/N budget does not forbid after "
            "an A2. So A2R is NOT excluded by the same argument that kills "
            "A2A2/A2A3/A3A2/A3A3. Non-observation in the depth<=6 corpus and in "
            "this bounded search is not a proof of impossibility."
        ),
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "a2r_found_in_any_root": found_any}, indent=2))


if __name__ == "__main__":
    main()
