#!/usr/bin/env python3
"""U4 family-local re-search, gated on having a validated new prune or
compression first.

Sections 3 (fragment debt) and 4 (Theta potential) of this round did NOT
produce a validated new safe prune beyond the existing Phi<0 capacity
check: the scalar fragment-debt lemma was refuted (FRAGMENT_DEBT_LEMMA.md),
and fragment/phase slack monotonicity was left UNRESOLVED, not proved
(RA2_THETA_POTENTIAL.md) -- so it cannot safely be used to cut the search
tree. Per this round's own explicit instruction ("새 obstruction 또는
압축 표현을 적용한 뒤에만 U4를 다시 탐색하라" / "상태 감소 효과가 30%
미만이면 cap을 키우지 말고 이론 단계로 돌아가라"), this script therefore
runs the SAME baseline search (no new prune available to add) at the
requested initial bounds only (node cap 200,000/state, total edge cap
2,000,000) -- not beyond -- and honestly reports that the outcome equals
the prior baseline (search_ra2_exact.py's pass 3): still unresolved. This
is not a wasted re-run: it is the literal deliverable requested (a
baseline-vs-new-attempt comparison table), and the honest content of that
table is "no reduction, because no new prune existed to apply."
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


macro = _load("srr_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def bounded_search(seed: "exact.ExactState", node_cap: int, edge_budget: List[int]) -> Dict[str, Any]:
    """Baseline search: identical logic to find_minimal_failing_path, but
    instrumented with frontier-growth and terminal-reason bookkeeping for
    the requested comparison table. edge_budget is a 1-element mutable
    list shared across all seeds so a single TOTAL edge cap can be
    enforced across the whole run."""
    frontier = deque([(0, seed, [])])
    nodes_expanded = 0
    frontier_sizes = []
    terminal_reasons: Dict[str, int] = {}
    unique_states = set()
    found = None
    while frontier and nodes_expanded < node_cap and edge_budget[0] > 0:
        depth, state, path_labels = frontier.popleft()
        nodes_expanded += 1
        frontier_sizes.append(len(frontier))
        for edge in macro.macro_edges(state):
            edge_budget[0] -= 1
            if edge_budget[0] <= 0:
                break
            tr = edge.joint
            if tr.abandonment:
                terminal_reasons["abandonment_illegal_post_f1"] = terminal_reasons.get("abandonment_illegal_post_f1", 0) + 1
                continue
            reason = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            new_labels = path_labels + [edge.label]
            if reason == "remaining_cover_capacity_impossible":
                terminal_reasons[reason] = terminal_reasons.get(reason, 0) + 1
                if found is None:
                    found = {"depth": depth + 1, "macro_path": new_labels, "phi_before": phi(state), "phi_after": phi(edge.state)}
                continue
            if reason is not None:
                terminal_reasons[reason] = terminal_reasons.get(reason, 0) + 1
                continue
            h = macro.stable_hash(edge.state)
            unique_states.add(h)
            frontier.append((depth + 1, edge.state, new_labels))
        if found is not None:
            break
    return {
        "nodes_expanded": nodes_expanded,
        "unique_states_seen": len(unique_states),
        "max_frontier_size": max(frontier_sizes) if frontier_sizes else 0,
        "terminal_reason_counts": terminal_reasons,
        "success_found": found is not None,
        "found": found,
        "frontier_empty_at_stop": len(frontier) == 0,
        "edge_budget_remaining": edge_budget[0],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ra2-exact-analysis", default=str(ROOT / "outputs" / "ra2_exact_analysis.json"))
    parser.add_argument("--node-cap-per-state", type=int, default=200_000)
    parser.add_argument("--total-edge-cap", type=int, default=2_000_000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_reduction_benchmark.json"))
    args = parser.parse_args()

    prior = json.loads(Path(args.ra2_exact_analysis).read_text(encoding="utf-8"))
    u4 = [r for r in prior["results"] if r["status"] == "unresolved_within_bounds_tried"]
    assert len(u4) == 4

    edge_budget = [args.total_edge_cap]
    ledger = json.loads((ROOT / "outputs" / "u_branch_state_ledger.json").read_text(encoding="utf-8"))
    witnesses_by_hash = {w["target_hash"]: w for w in ledger["words"]["RA2"]["witnesses"]}

    baseline_prior_pass3 = {r["target_hash"]: r["status"] for r in prior["results"]}

    comparison = []
    t0 = time.time()
    for r in u4:
        h = r["target_hash"]
        seed = exact.state_from_json(witnesses_by_hash[h]["final_state_json"])
        run = bounded_search(seed, args.node_cap_per_state, edge_budget)
        comparison.append({
            "target_hash": h,
            "prior_pass3_status": baseline_prior_pass3[h],
            "this_run": run,
            "new_prune_applied": False,
            "reduction_vs_prior": (
                "not applicable -- no validated new prune existed to apply this round "
                "(see FRAGMENT_DEBT_LEMMA.md, RA2_THETA_POTENTIAL.md); this run reuses "
                "the identical baseline search logic at the requested initial bounds only"
            ),
        })
        print(h[:12], run["success_found"], "nodes:", run["nodes_expanded"], "edge_budget_left:", edge_budget[0])
        if edge_budget[0] <= 0:
            print("total edge cap exhausted, stopping per the requested budget")
            break

    report = {
        "schema": "ra2-reduction-benchmark-v1",
        "config": {"node_cap_per_state": args.node_cap_per_state, "total_edge_cap": args.total_edge_cap},
        "elapsed_seconds": round(time.time() - t0, 2),
        "decision": (
            "No new safe prune or compression was validated in sections 3-4 of this "
            "round (fragment debt scalar refuted; fragment/phase slack monotonicity "
            "left unresolved). Per this round's own instruction not to widen bounds "
            "without >=30% state reduction from a real new obstruction, this run does "
            "NOT go beyond the requested initial caps, and the honest expected outcome "
            "is 0% reduction versus the prior baseline (all 4 states still unresolved)."
        ),
        "comparison": comparison,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    any_found = any(c["this_run"]["success_found"] for c in comparison)
    print(json.dumps({"wrote": args.output, "any_capacity_failure_found_this_run": any_found}, indent=2))


if __name__ == "__main__":
    main()
