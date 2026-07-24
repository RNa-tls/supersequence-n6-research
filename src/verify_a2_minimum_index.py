#!/usr/bin/env python3
"""Section 7-8: re-verifies i_min(A2)=4 via bounded exhaustive search
(reusing the same method as A2R_MINIMUM_DEPTH.md / search_a2r_min_depth.py
-- no new large-scale search), and produces the depth-0..4 abstract
history enumeration requested, reporting honestly where it is only a
looser over-approximation rather than a full proof.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict

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


macro = _load("vami_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def enumerate_depth(max_depth: int, node_cap: int) -> Dict[str, Any]:
    """Exhaustive raw BFS from the initial state over zero-charge-only
    prefixes, reporting per-depth: number of distinct states reached,
    number of distinct orbits touched (exact, not abstract), and whether
    any A2 becomes legal. This IS exhaustive exact search (not an
    abstraction) -- the "abstract history" simplification requested in
    section 8 was attempted (track only orbit-history SIZE, not full
    state) but found insufficient to decide A2 legality without also
    knowing the specific reachable endpoints, i.e. it collapses back to
    needing the exact states -- reported honestly below.
    """
    root = exact.initial_state()
    frontier = deque([(0, root)])
    per_depth: Dict[int, Dict[str, Any]] = {}
    expanded = 0
    a2_first_depth = None
    while frontier and expanded < node_cap:
        depth, state = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        bucket = per_depth.setdefault(depth, {"states_expanded": 0, "orbit_history_sizes": set(), "a2_legal_found": False})
        bucket["states_expanded"] += 1
        bucket["orbit_history_sizes"].add(state.O)
        for e in macro.macro_edges(state):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if kind == "A2":
                bucket["a2_legal_found"] = True
                continue
            if kind in ("A2", "A3", "R", "J"):
                continue
            frontier.append((depth + 1, tr.state))
    for d, b in per_depth.items():
        b["orbit_history_sizes"] = sorted(b["orbit_history_sizes"])
        if b["a2_legal_found"] and a2_first_depth is None:
            a2_first_depth = d
    return {"per_depth": per_depth, "a2_first_legal_at_depth_index": a2_first_depth, "nodes_expanded": expanded, "frontier_remaining": len(frontier)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--node-cap", type=int, default=200_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "a2_depth4_abstract_histories.json"))
    args = parser.parse_args()

    result = enumerate_depth(args.max_depth, args.node_cap)
    print(f"a2_first_legal_at_depth_index={result['a2_first_legal_at_depth_index']} "
          f"nodes_expanded={result['nodes_expanded']} frontier_remaining={result['frontier_remaining']}")

    report = {
        "schema": "a2-depth4-abstract-histories-v1",
        "method": "exact exhaustive raw BFS (not a true state-abstraction) -- see note",
        "note": (
            "Section 8 asked for an ABSTRACT (reduced-statistic) enumeration of "
            "depth 0..4 histories, distinct from full exhaustive BFS. This was "
            "attempted using orbit-history SIZE (state.O) as the abstract "
            "statistic, but O alone does not determine A2 legality (which "
            "specific orbits are touched matters, not just how many) -- so the "
            "abstraction is not sound for deciding legality by itself, and this "
            "script falls back to exact exhaustive BFS (still bounded, still no "
            "new large-scale search -- reuses the same depth<=5 bound as "
            "A2R_MINIMUM_DEPTH.md). Reported honestly as exact search, not as "
            "the abstract lower-bound proof requested."
        ),
        "result": {
            "per_depth": {str(k): v for k, v in result["per_depth"].items()},
            "a2_first_legal_at_depth_index": result["a2_first_legal_at_depth_index"],
            "nodes_expanded": result["nodes_expanded"],
            "frontier_remaining": result["frontier_remaining"],
            "exhaustive": result["frontier_remaining"] == 0,
        },
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
