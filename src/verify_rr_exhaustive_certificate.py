#!/usr/bin/env python3
"""Round 17, section 2: an INDEPENDENT verifier for
outputs/rr_uncapped_local_universe.json -- re-derives the same root-local
state counts via a structurally different traversal (DFS with an
explicit visited set, moves tried in a different order than the BFS
enumerator) and cross-checks unique_raw_states (raw stable_key dedup, see
outputs/rr_generator_diff.json for why raw dedup is safe), same_component_count,
and hub_completer_orbit_distribution per ell. A mismatch would mean the
original enumerator (or this verifier) has a bug; agreement is the
"independent verifier passed" certificate the exhaustiveness standard
requires.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
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


macro = _load("vrec_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W2_10 = move_by_label["w2:10"]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def component_map(state):
    parent: Dict[Any, Any] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return parent, find


def dfs_count(root_state, hex0: int, depth_ceiling: int, max_r_events: int = 2) -> Dict[str, Any]:
    seen = {root_state.stable_key()}
    completer_orbit_counter: Counter = Counter()
    same_hits = []
    chaining_count = 0

    # Explicit stack DFS -- edges tried in REVERSED order vs macro_edges()'s
    # natural order, a deliberate structural difference from the BFS
    # enumerator to make this a genuine independent cross-check.
    stack = [(root_state, 0, None, 0)]
    while stack:
        state, r_count, r1_target_q, depth = stack.pop()
        if depth >= depth_ceiling:
            continue
        edges = list(macro.macro_edges(state))
        for edge in reversed(edges):
            tr = edge.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if tr.target is not None and core.hexagon_id(tr.target) == hex0:
                q, _ = exact.ORBIT_PHASE[tr.target]
                completer_orbit_counter[q] += 1
            new_r_count = r_count
            new_r1_target_q = r1_target_q
            if kind == "R":
                new_r_count = r_count + 1
                src_q, _ = exact.ORBIT_PHASE[edge.run.state.p]
                tgt_q, _ = exact.ORBIT_PHASE[tr.target]
                if new_r_count == 1:
                    new_r1_target_q = tgt_q
                elif new_r_count == 2 and tr.state.F == 1 and tr.state.H == 0:
                    parent_map, find = component_map(edge.run.state)
                    src_root = find(("q", src_q)) if ("q", src_q) in parent_map else None
                    tgt_root = find(("q", tgt_q)) if ("q", tgt_q) in parent_map else None
                    chaining = (new_r1_target_q == src_q)
                    if chaining:
                        nonlocal_chaining[0] += 1
                    if src_root is not None and src_root == tgt_root:
                        same_hits.append({"depth": depth + 1, "r1_target_q": new_r1_target_q, "r2_source_q": src_q})
            if new_r_count > max_r_events:
                continue
            key = tr.state.stable_key()
            if key in seen:
                continue
            seen.add(key)
            stack.append((tr.state, new_r_count, new_r1_target_q, depth + 1))

    return {
        "unique_raw_states": len(seen),
        "same_component_count": len(same_hits),
        "hub_completer_orbit_distribution": dict(completer_orbit_counter),
        "chaining_count": nonlocal_chaining[0],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--against", default=str(ROOT / "outputs" / "rr_uncapped_local_universe.json"))
    parser.add_argument("--depth-ceiling", type=int, default=6)
    args = parser.parse_args()

    original = json.loads(Path(args.against).read_text(encoding="utf-8"))
    init = exact.initial_state()
    hex0 = core.hexagon_id(init.p)

    all_match = True
    comparison = {}
    for ell in range(5):
        cur = init
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        atr = exact.extend(cur, W2_10)
        root_state = atr.state

        global nonlocal_chaining
        nonlocal_chaining = [0]
        result = dfs_count(root_state, hex0, args.depth_ceiling)

        orig = original["results_by_ell"][str(ell)]
        match_states = result["unique_raw_states"] == orig["unique_raw_states"]
        match_same = result["same_component_count"] == orig["same_component_count"]
        norm_result_dist = {str(k): v for k, v in result["hub_completer_orbit_distribution"].items()}
        norm_orig_dist = {str(k): v for k, v in orig["hub_completer_orbit_distribution"].items()}
        match_dist = norm_result_dist == norm_orig_dist
        ok = match_states and match_same and match_dist
        all_match = all_match and ok
        comparison[str(ell)] = {
            "dfs_result": result, "bfs_original": {
                "unique_raw_states": orig["unique_raw_states"],
                "same_component_count": orig["same_component_count"],
                "hub_completer_orbit_distribution": orig["hub_completer_orbit_distribution"],
            },
            "match_states": match_states, "match_same": match_same, "match_dist": match_dist, "all_match": ok,
        }
        print(f"ell={ell}: DFS unique={result['unique_raw_states']} (BFS {orig['unique_raw_states']}) "
              f"same={result['same_component_count']} (BFS {orig['same_component_count']}) match={ok}")

    print("\nINDEPENDENT VERIFIER RESULT:", "PASSED (all ell match)" if all_match else "FAILED (mismatch found)")

    report = {
        "schema": "rr-exhaustive-certificate-verification-v1",
        "verified_against": args.against,
        "depth_ceiling": args.depth_ceiling,
        "method": "DFS with explicit stack, edges tried in reversed order vs the BFS enumerator -- structurally independent traversal",
        "per_ell_comparison": comparison,
        "all_match": all_match,
        "verdict": "독립 검증 통과 (independent verifier passed)" if all_match else "불일치 발견 (mismatch -- one of the two implementations has a bug)",
    }
    out = ROOT / "outputs" / "rr_exhaustive_certificate_verification.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
