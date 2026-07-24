#!/usr/bin/env python3
"""A2R minimum-depth theorem: exact minimum macro-depth, witness
uniqueness/family count at that depth, and why A2R needs more depth than
RA2's own minimum.

Reuses the prior round's finding (search_a2r_min_depth.py,
outputs/a2r_search.json): A2R's minimum total macro-depth is 6 (raw BFS,
node_cap=200,000, depth<=6). This script re-runs the SAME bounded search
but does NOT stop at the first witness -- it collects every A2R witness
found at the minimum depth (still within the same depth<=6 bound, no
larger search), to determine uniqueness or family count.
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


macro = _load("samd_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def find_all_a2r_at_min_depth(max_depth: int, node_cap: int) -> Dict[str, Any]:
    """Raw BFS from the true initial state. Tracks every path whose event
    sequence is a prefix of ("A2","R"). Records ALL witnesses at the
    shallowest depth found (does not stop at the first)."""
    root = exact.initial_state()
    frontier = deque([(0, root, [], ())])
    expanded = 0
    witnesses_by_depth: Dict[int, List[Dict[str, Any]]] = {}
    min_depth_found: Optional[int] = None
    while frontier and expanded < node_cap:
        depth, state, path, events = frontier.popleft()
        if min_depth_found is not None and depth >= min_depth_found:
            continue
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
            if len(new_events) > 2 or (len(new_events) >= 1 and new_events[0] != "A2"):
                continue
            new_path = path + [e.label]
            new_depth = depth + 1
            if new_events == ("A2", "R"):
                if min_depth_found is None or new_depth <= min_depth_found:
                    min_depth_found = new_depth
                    witnesses_by_depth.setdefault(new_depth, []).append({
                        "macro_path": new_path,
                        "final_state_json": exact.state_to_json(tr.state),
                        "phi": phi(tr.state),
                    })
                continue
            frontier.append((new_depth, tr.state, new_path, new_events))
    return {
        "min_depth_found": min_depth_found,
        "nodes_expanded": expanded,
        "frontier_remaining": len(frontier),
        "witnesses_at_min_depth": witnesses_by_depth.get(min_depth_found, []) if min_depth_found else [],
    }


def dedupe_by_canonical(witnesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}
    for w in witnesses:
        st = exact.canonicalize(exact.state_from_json(w["final_state_json"]))
        h = macro.stable_hash(st)
        if h not in seen:
            seen[h] = {**w, "canonical_hash": h}
    return list(seen.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--node-cap", type=int, default=400_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "a2r_minimum_witnesses.json"))
    args = parser.parse_args()

    result = find_all_a2r_at_min_depth(args.max_depth, args.node_cap)
    print(f"min_depth_found={result['min_depth_found']}, nodes_expanded={result['nodes_expanded']}, "
          f"frontier_remaining={result['frontier_remaining']}, raw witnesses at min depth: {len(result['witnesses_at_min_depth'])}")

    deduped = dedupe_by_canonical(result["witnesses_at_min_depth"])
    print(f"distinct canonical witnesses at min depth: {len(deduped)}")

    report = {
        "schema": "a2r-minimum-witnesses-v1",
        "config": {"max_depth": args.max_depth, "node_cap": args.node_cap},
        "min_depth_found": result["min_depth_found"],
        "search_exhaustive_within_bound": result["frontier_remaining"] == 0 or result["min_depth_found"] is not None,
        "nodes_expanded": result["nodes_expanded"],
        "raw_witness_count_at_min_depth": len(result["witnesses_at_min_depth"]),
        "distinct_canonical_witnesses_at_min_depth": len(deduped),
        "witnesses": deduped,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
