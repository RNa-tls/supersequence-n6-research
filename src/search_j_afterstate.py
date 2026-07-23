#!/usr/bin/env python3
"""Bounded decisive-event profiling from J-afterstate seeds.

Restricted to the joint alphabet the post-J theorems (J-1, J-2, J-3 in
research/J_COMPLETION_OBSTRUCTION.md) already prove is the only one
possible: rotations, Z2_blocked_w2_existing, Z3_blocked_w3_new, and at most
one R_blocked_w3_existing. This is enforced simply by reusing
``area_a_prune_reason(state, AREA_A)`` (which already implements the F and
N budget checks correctly) plus an explicit per-path R-usage counter, not
by a separate re-implementation of the budget logic.

A "decisive event" for this profiling is any of:
  - using the one allowed R (R_used)
  - hitting a positive-charge-budget-violating prune (would need charge
    the walk cannot afford)
  - a capacity-impossibility prune
  - a literal collision terminal (no legal macro edge at all)
  - full completion (area_a_final)

This does NOT run a new large-scale Area-A search: each seed's profiling
is capped by --edge-cap and --max-depth, defaulting to small, clearly
bounded values, and is reported honestly as a bounded experiment.
"""
from __future__ import annotations

import argparse
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


macro = _load("j_afterstate_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def profile_from_seed(seed_state: "exact.ExactState", max_depth: int, edge_cap: int) -> Dict[str, Any]:
    # frontier entries: (depth, state, r_used_count)
    frontier: deque = deque([(0, seed_state, 0)])
    edges_expanded = 0
    depth_frontier_counts: Counter = Counter({0: 1})
    depth_canonical_counts: Counter = Counter()
    terminal_reason_counts: Counter = Counter()
    r_used_terminal_states = 0
    r_unused_terminal_states = 0
    max_live_depth = 0
    completions_found = 0
    example_completion_path: Optional[List[str]] = None
    path_by_key: Dict[Any, List[str]] = {seed_state.stable_key(): []}
    cap_hit = False

    while frontier:
        if edges_expanded >= edge_cap:
            cap_hit = True
            break
        depth, state, r_used = frontier.popleft()
        if depth >= max_depth:
            continue
        any_child = False
        for edge in macro.macro_edges(state):
            any_child = True
            edges_expanded += 1
            if edges_expanded > edge_cap:
                cap_hit = True
                break
            tr = edge.joint
            is_R = (tr.move.weight, tr.abandonment, tr.new_orbit) == (3, False, False)
            new_r_used = r_used + (1 if is_R else 0)
            if tr.abandonment:
                terminal_reason_counts["would_require_new_abandonment_impossible"] += 1
                continue
            if new_r_used > 1:
                terminal_reason_counts["would_use_second_R_impossible"] += 1
                continue
            reason = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            if reason is not None:
                terminal_reason_counts[reason] += 1
                continue
            child = exact.canonicalize(edge.state)
            key = child.stable_key()
            labels = path_by_key.get(state.stable_key(), []) + [edge.label]
            path_by_key[key] = labels
            depth_frontier_counts[depth + 1] += 1
            depth_canonical_counts[depth + 1] += 1
            if depth + 1 > max_live_depth:
                max_live_depth = depth + 1
            if macro.area_a_final(child, macro.AREA_A):
                completions_found += 1
                if example_completion_path is None:
                    example_completion_path = labels
                if new_r_used >= 1:
                    r_used_terminal_states += 1
                else:
                    r_unused_terminal_states += 1
                continue
            frontier.append((depth + 1, child, new_r_used))
        if not any_child:
            terminal_reason_counts["no_legal_macro_edge_literal_terminal"] += 1

    return {
        "seed_coordinate": list(macro.state_coordinate(seed_state)),
        "config": {"max_depth": max_depth, "edge_cap": edge_cap},
        "edges_expanded": edges_expanded,
        "cap_hit": cap_hit,
        "depth_frontier_counts": dict(sorted(depth_frontier_counts.items())),
        "terminal_reason_counts": dict(sorted(terminal_reason_counts.items())),
        "max_live_depth_reached": max_live_depth,
        "completions_found": completions_found,
        "completions_using_R": r_used_terminal_states,
        "completions_not_using_R": r_unused_terminal_states,
        "example_completion_macro_path": example_completion_path,
        "scope": (
            "bounded, capped profiling from ONE seed state only; "
            "not an exhaustive completeness or impossibility result"
        ),
    }


def load_seed_states(witnesses_path: Path, limit: Optional[int]) -> List[Tuple[str, "exact.ExactState"]]:
    data = json.loads(witnesses_path.read_text(encoding="utf-8"))
    seeds = []
    for w in data["witnesses"][: limit if limit is not None else None]:
        state = exact.state_from_json(w["final_state_json"])
        seeds.append((w["target_hash"], state))
    return seeds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "j_230_literal_witnesses.json"))
    parser.add_argument("--limit", type=int, default=None, help="profile only the first N recovered seeds")
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--edge-cap", type=int, default=20_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "j_afterstate_profile.json"))
    args = parser.parse_args()

    witnesses_path = Path(args.witnesses)
    if witnesses_path.exists():
        seeds = load_seed_states(witnesses_path, args.limit)
    else:
        seeds = []

    profiles = []
    for target_hash, state in seeds:
        profiles.append({"target_hash": target_hash, "profile": profile_from_seed(state, args.max_depth, args.edge_cap)})

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "schema": "j-afterstate-profile-v1",
        "seeds_profiled": len(profiles),
        "profiles": profiles,
    }, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "seeds_profiled": len(profiles)}, indent=2))


if __name__ == "__main__":
    main()
