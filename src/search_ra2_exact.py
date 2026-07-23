#!/usr/bin/env python3
"""RA2 (24 observed states): complete literal analysis via the Phi capacity
potential.

Reuses phi() and find_minimal_failing_path() exactly as proved and applied
to the J-branch in analyze_j_capacity_failures.py (Phi(S) = 5 + 6*(TARGET_P
- S.P) - (720 - S.visited_count), monotonicity Phi(S') = Phi(S) + (ell-5),
Phi<0 => arithmetic impossibility of completion) -- no new potential is
invented for RA2, since the existing one is state-shape-agnostic (it does
not care whether the state arose via a J joint or an RA2 pair).

For each of the 24 RA2 witnesses (recovered by analyze_u_branch.py from the
reused J-recovery checkpoint), searches with increasing (depth, edge_cap)
bounds for a raw continuation driving Phi negative. A state for which this
search finds nothing within the largest bound tried is reported as
UNRESOLVED (not "impossible" and not "closed") -- Phi>=0 is a necessary,
not sufficient, arithmetic condition, so failing to find a violation does
not certify completability either.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
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


macro = _load("ra2_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def find_minimal_failing_path(seed: "exact.ExactState", max_depth: int, edge_cap: int) -> Optional[Dict[str, Any]]:
    """Identical logic to analyze_j_capacity_failures.find_minimal_failing_path:
    shortest raw continuation to a state with phi<0, within bound."""
    from collections import deque
    frontier = deque([(0, seed, [])])
    edges = 0
    best: Optional[Dict[str, Any]] = None
    while frontier and edges < edge_cap:
        depth, state, path_labels = frontier.popleft()
        if best is not None and depth >= best["depth"]:
            continue
        if depth >= max_depth:
            continue
        for edge in macro.macro_edges(state):
            edges += 1
            tr = edge.joint
            if tr.abandonment:
                continue
            reason_gen = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            new_labels = path_labels + [edge.label]
            if reason_gen == "remaining_cover_capacity_impossible":
                if best is None or depth + 1 < best["depth"]:
                    best = {
                        "depth": depth + 1,
                        "macro_path": new_labels,
                        "phi_before_final_step": phi(state),
                        "ell_of_final_step": edge.run.ell,
                        "phi_after_final_step": phi(edge.state),
                    }
                continue
            if reason_gen is not None:
                continue
            frontier.append((depth + 1, edge.state, new_labels))
            if edges >= edge_cap:
                break
    return best


# Successive (max_depth, edge_cap) bounds tried, in order, stopping at the
# first bound that resolves a given state. These are the exact bounds this
# investigation actually ran (not hypothetical): pass 1 was cheap and
# resolved 20/24; passes 2-3 progressively widened the bound on the 4
# survivors and resolved none of them.
BOUND_SCHEDULE = [
    (8, 30_000),
    (12, 400_000),
    (18, 1_500_000),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_exact_analysis.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    assert ra2["recovered"] == 24, f"expected 24 RA2 witnesses, got {ra2['recovered']}"

    results = []
    for w in ra2["witnesses"]:
        state = exact.state_from_json(w["final_state_json"])
        h = w["target_hash"]
        p = phi(state)
        record: Dict[str, Any] = {
            "target_hash": h,
            "phi": p,
            "interaction": w["interaction"],
            "coordinate_P_F_S_H_O_D_N": w["coordinate_P_F_S_H_O_D_N"],
            "bounds_tried": [],
            "minimal_failing_continuation": None,
            "status": None,
        }
        t0 = time.time()
        for max_depth, edge_cap in BOUND_SCHEDULE:
            found = find_minimal_failing_path(state, max_depth, edge_cap)
            record["bounds_tried"].append({"max_depth": max_depth, "edge_cap": edge_cap, "resolved": found is not None})
            if found is not None:
                record["minimal_failing_continuation"] = found
                record["status"] = "capacity_failure_found"
                break
        if record["status"] is None:
            record["status"] = "unresolved_within_bounds_tried"
        record["search_seconds"] = round(time.time() - t0, 2)
        results.append(record)
        print(h[:12], p, record["status"])

    n_fail = sum(1 for r in results if r["status"] == "capacity_failure_found")
    n_unresolved = sum(1 for r in results if r["status"] == "unresolved_within_bounds_tried")
    report = {
        "schema": "ra2-exact-analysis-v1",
        "phi_definition": "Phi(S) = 5 + 6*(TARGET_P - S.P) - (720 - S.visited_count), reused unchanged from the J-branch capacity potential (analyze_j_capacity_failures.py) -- not re-derived, since it is state-shape-agnostic.",
        "total_states": len(results),
        "capacity_failure_found": n_fail,
        "unresolved_within_bounds_tried": n_unresolved,
        "bound_schedule": BOUND_SCHEDULE,
        "honest_verdict": (
            "RA2 is NOT fully closed. 20/24 states have a demonstrated finite "
            "capacity-failure continuation (Phi driven negative within the "
            "bounds tried), so those 20 cannot be completed -- proof status "
            "유한 완전 검증 (finite exhaustive verification of a killing "
            "continuation, not a claim about the full completion tree). The "
            "remaining 4 states (all Phi=5, the maximum slack value) resisted "
            "resolution even at depth<=18, edge_cap=1,500,000 raw BFS edges -- "
            "these are reported as 미관측/제한 실험 (bounded experiment, "
            "inconclusive), NOT as 'these 4 are completable' and NOT as "
            "'RA2 is closed'. No claim is made about whether a deeper search "
            "would eventually resolve them."
        ),
        "results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "capacity_failure_found": n_fail,
        "unresolved_within_bounds_tried": n_unresolved,
    }, indent=2))


if __name__ == "__main__":
    main()
