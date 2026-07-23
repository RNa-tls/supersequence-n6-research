#!/usr/bin/env python3
"""Charge-budget-constrained decisive-event search over the 74 J states that
survived the depth<=6 bounded capacity search in
outputs/j_capacity_extension_profile.json.

This does not start a new full Area-A search: it runs independently,
per-seed, capped by a total edge budget across all 74 seeds (not an
unbounded/checkpointed long-running process), and prunes any transition
that would make the running total charge exceed the seed's own Phi budget
(exactly equivalent to, and implemented via, recomputing Phi and checking
Phi>=0 -- see research/SHORTFALL_BUDGET_THEOREM.md for why these are the
same check). Raw (uncanonicalized) traversal, matching
search_j_afterstate.py's speed tradeoff.

Decisive events tracked, per the request:
  1. Phi<0 (budget exhausted) -- the same mechanism as
     analyze_j_capacity_failures.py, now searched deeper/wider
  2. literal collision terminal (no legal macro edge at all)
  3. complete success (area_a_final)
  4. reaching the depth/edge cap unresolved (reported honestly as such,
     not as evidence of anything)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, deque
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


macro = _load("j_budget_search_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def search_one_seed(seed_state: "exact.ExactState", max_depth: int, edge_budget: int) -> Dict[str, Any]:
    frontier: deque = deque([(0, seed_state)])
    edges_used = 0
    depth_survivor_counts: Counter = Counter({0: 1})
    terminal_reason_counts: Counter = Counter()
    completions_found = 0
    max_depth_reached = 0
    minimal_failure: Optional[Dict[str, Any]] = None
    path_by_key: Dict[Any, List[str]] = {seed_state.stable_key(): []}
    cap_hit = False

    while frontier:
        if edges_used >= edge_budget:
            cap_hit = True
            break
        depth, state = frontier.popleft()
        if depth >= max_depth:
            continue
        any_child = False
        for edge in macro.macro_edges(state):
            any_child = True
            edges_used += 1
            if edges_used > edge_budget:
                cap_hit = True
                break
            tr = edge.joint
            if tr.abandonment:
                terminal_reason_counts["would_require_new_abandonment_impossible"] += 1
                continue
            child = tr.state
            child_phi = phi(child)
            labels = path_by_key.get(state.stable_key(), []) + [edge.label]
            if child_phi < 0:
                terminal_reason_counts["remaining_cover_capacity_impossible"] += 1
                if minimal_failure is None or depth + 1 < minimal_failure["depth"]:
                    minimal_failure = {"depth": depth + 1, "macro_path": labels, "phi_after": child_phi}
                continue
            reason = macro.area_a_prune_reason(child, macro.AREA_A)
            if reason is not None:
                terminal_reason_counts[reason] += 1
                continue
            path_by_key[child.stable_key()] = labels
            depth_survivor_counts[depth + 1] += 1
            if depth + 1 > max_depth_reached:
                max_depth_reached = depth + 1
            if macro.area_a_final(child, macro.AREA_A):
                completions_found += 1
                continue
            frontier.append((depth + 1, child))
        if not any_child:
            terminal_reason_counts["no_legal_macro_edge_literal_terminal"] += 1

    return {
        "edges_used": edges_used,
        "cap_hit": cap_hit,
        "depth_survivor_counts": dict(sorted(depth_survivor_counts.items())),
        "terminal_reason_counts": dict(sorted(terminal_reason_counts.items())),
        "max_depth_reached": max_depth_reached,
        "completions_found": completions_found,
        "minimal_capacity_failure_found": minimal_failure,
        "scope": "bounded, raw, single-seed; not a completeness or impossibility result",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-depth", type=int, default=12)
    parser.add_argument("--total-edge-budget", type=int, default=1_000_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "j_budget_search.json"))
    args = parser.parse_args()

    witnesses = {
        w["target_hash"]: exact.state_from_json(w["final_state_json"])
        for w in json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    }
    extension = json.loads((ROOT / "outputs" / "j_capacity_extension_profile.json").read_text())
    survivor_hashes = sorted(
        p["target_hash"] for p in extension["per_seed"] if not p["minimal_failing_continuation_found"]
    )
    if len(survivor_hashes) != 74:
        raise AssertionError(f"expected 74 survivors, found {len(survivor_hashes)}")

    per_seed_budget = max(args.total_edge_budget // len(survivor_hashes), 1000)
    results = []
    t0 = time.time()
    total_edges_used = 0
    for h in survivor_hashes:
        if total_edges_used >= args.total_edge_budget:
            results.append({"target_hash": h, "skipped_total_budget_exhausted": True})
            continue
        remaining = args.total_edge_budget - total_edges_used
        budget_this_seed = min(per_seed_budget, remaining)
        profile = search_one_seed(witnesses[h], args.max_depth, budget_this_seed)
        total_edges_used += profile["edges_used"]
        results.append({"target_hash": h, "profile": profile})

    elapsed = time.time() - t0
    resolved = [r for r in results if "profile" in r and (
        r["profile"]["completions_found"] > 0 or r["profile"]["minimal_capacity_failure_found"] is not None
    )]
    report = {
        "schema": "j-budget-search-v1",
        "config": {"max_depth": args.max_depth, "total_edge_budget": args.total_edge_budget,
                   "per_seed_edge_budget": per_seed_budget, "checkpoint": None},
        "seeds_searched": len(survivor_hashes),
        "elapsed_seconds": round(elapsed, 1),
        "total_edges_used": total_edges_used,
        "seeds_resolved_within_bound": len(resolved),
        "seeds_still_unresolved": len(survivor_hashes) - len(resolved),
        "results": results,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "wrote": str(out_path), "elapsed_seconds": report["elapsed_seconds"],
        "total_edges_used": total_edges_used,
        "seeds_resolved_within_bound": report["seeds_resolved_within_bound"],
        "seeds_still_unresolved": report["seeds_still_unresolved"],
    }, indent=2))


if __name__ == "__main__":
    main()
