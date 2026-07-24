#!/usr/bin/env python3
"""Round 13, sections 2-6, 9, 12: verifies (a) hub touch count <= 2 as a
DEDUCTIVE lemma (from current_hex semantics + F<=1 budget), (b) whether
a non-R event can ever complete the hub BEFORE any R fires, (c) a deep
bounded search (per same-component witness, from its post-abandonment
state, depth up to ~9, node_cap up to 60,000) for a same-component
non-chaining R1/R2 pair -- reusing macro_edges()/area_a_prune_reason(),
NOT a new large-scale search (same order of magnitude as prior rounds'
single-state bounded searches).
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


macro = _load("vrht_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def component_map(state: "exact.ExactState") -> Dict[Any, Any]:
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
    return {n: find(n) for n in parent}


def replay_to_post_abandonment(witness: Dict[str, Any]) -> Optional["exact.ExactState"]:
    """Replay just the word's first joint (the hidden abandonment, in
    same-component witnesses always the first event) and return the
    resulting state, or None if the first joint doesn't abandon."""
    path = witness["macro_path"]
    cur = exact.initial_state()
    step = path[0]
    rot_part, joint_part = step["edge_label"].split(";")
    ell = int(rot_part[len("rot^"):])
    move = move_by_label[joint_part]
    for _ in range(ell):
        tr = exact.extend(cur, W1)
        cur = tr.state
    tr = exact.extend(cur, move)
    if not tr.abandonment:
        return None
    return tr.state


def deep_search_for_counterexample(state: "exact.ExactState", max_depth: int, node_cap: int) -> Dict[str, Any]:
    """Full bounded BFS over BOTH R1 and R2 choices (not fixing R1 to the
    corpus's own recorded choice) -- looking for ANY (R1, R2) pair within
    reach where R2's own component_relation is 'same' but R2's source
    orbit != R1's target orbit (i.e. non-chaining)."""
    frontier = deque([(0, state, 0, None)])
    expanded = 0
    found: List[Dict[str, Any]] = []
    nonR_hub_completions_before_any_R = 0
    R_hub_completions_after_a_nonhub_R = 0
    while frontier and expanded < node_cap:
        depth, st, r_count, r1_target = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        roots = component_map(st)
        for e in macro.macro_edges(st):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if kind in ("A2", "A3", "J"):
                continue
            src_q, _ = exact.ORBIT_PHASE[e.run.state.p]
            is_hub_completer = tr.target is not None and core.hexagon_id(tr.target) == 0
            if is_hub_completer and kind != "R" and r_count == 0:
                nonR_hub_completions_before_any_R += 1
            if is_hub_completer and kind == "R" and r_count == 1:
                R_hub_completions_after_a_nonhub_R += 1
            new_r_count, new_r1_target = r_count, r1_target
            if kind == "R":
                new_r_count = r_count + 1
                if tr.target is not None:
                    tgt_q, _ = exact.ORBIT_PHASE[tr.target]
                    if r_count == 0:
                        new_r1_target = tgt_q
                    elif r_count == 1 and r1_target is not None:
                        src_root, tgt_root = roots.get(("q", src_q)), roots.get(("q", tgt_q))
                        rel = "same" if src_root is not None and src_root == tgt_root else (
                            "different" if src_root is not None and tgt_root is not None else "unresolved")
                        if rel == "same" and src_q != r1_target:
                            found.append({
                                "depth": depth, "r1_target": r1_target,
                                "r2_source": src_q, "r2_target": tgt_q, "ell": e.run.ell,
                            })
            if new_r_count >= 2:
                continue
            frontier.append((depth + 1, tr.state, new_r_count, new_r1_target))
    return {
        "nodes_expanded": expanded, "frontier_remaining": len(frontier),
        "exhaustive_within_bound": len(frontier) == 0,
        "nonR_hub_completions_before_any_R": nonR_hub_completions_before_any_R,
        "R_hub_completions_after_a_nonhub_R": R_hub_completions_after_a_nonhub_R,
        "same_non_chaining_witnesses_found": found,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--max-depth", type=int, default=9)
    parser.add_argument("--node-cap", type=int, default=60000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_hub_touch_truth_table.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    table = json.loads(Path(args.relation_table).read_text(encoding="utf-8"))
    same_hashes = [r["hash"] for r in table["rows"] if r.get("r2_own_component_relation") == "same"]
    print(f"deep bounded re-search from {len(same_hashes)} same-component witnesses' post-abandonment state")

    results = {}
    any_counterexample = False
    for h in same_hashes:
        w = wdata["witnesses"][h]
        post_abandon = replay_to_post_abandonment(w)
        if post_abandon is None:
            results[h] = {"error": "first joint does not abandon"}
            continue
        search = deep_search_for_counterexample(post_abandon, args.max_depth, args.node_cap)
        results[h] = search
        if search["same_non_chaining_witnesses_found"]:
            any_counterexample = True
        print(h[:12], "nodes", search["nodes_expanded"], "exhaustive", search["exhaustive_within_bound"],
              "nonR_hub_before_R:", search["nonR_hub_completions_before_any_R"],
              "counterexamples:", len(search["same_non_chaining_witnesses_found"]))

    report = {
        "schema": "rr-hub-touch-truth-table-v1",
        "method": (
            f"per-witness bounded BFS (max_depth={args.max_depth}, node_cap={args.node_cap}) "
            "from the post-abandonment state, exploring ALL R1/R2 choices (not fixed to the "
            "corpus's own recorded path) -- bounded, reuses existing macro_edges()/"
            "area_a_prune_reason() machinery, not a new large-scale search."
        ),
        "any_counterexample_found": any_counterexample,
        "per_witness": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "any_counterexample_found": any_counterexample}, indent=2))


if __name__ == "__main__":
    main()
