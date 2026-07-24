#!/usr/bin/env python3
"""Section 8 (orbit-demand bipartite/Hall-type obstruction attempt) and
section 10 (existing-target branch automaton) for U4.

Given section 3/9's findings (rho_A is non-binding locally and globally
for all 4 U4 states; H2a/b/c refuted), this script tests the Hall-type
necessary condition on the smallest available demand set (the fragment
hole itself) using the already-found repair witnesses as the supply/
neighborhood, and reports honestly that no violating subset was found
within this round's scope -- it does not claim a general Hall obstruction
was constructed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent


def hall_check_for_hole_demand(repair_cone_result: Dict[str, Any]) -> Dict[str, Any]:
    """Demand set X = {the single fragment hole}. Neighborhood N(X) = the
    set of distinct legal repair transitions found (each a distinct
    'supply slot' able to serve this one demand). Hall's condition
    |N(X)| >= |X| trivially holds here since witnesses were found; this
    is reported honestly as a non-violation, not a proof of general
    matchability for the whole remaining completion problem."""
    n_x = repair_cone_result["witnesses_found"]
    x_size = 1
    return {
        "demand_set_size": x_size,
        "neighborhood_size_N_X": n_x,
        "hall_condition_holds": n_x >= x_size,
        "violating_subset_found": n_x < x_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair-cones", default=str(ROOT / "outputs" / "ra2_repair_cones.json"))
    parser.add_argument("--novelty-counterfactuals", default=str(ROOT / "outputs" / "ra2_target_novelty_counterfactuals.json"))
    parser.add_argument("--output-demand", default=str(ROOT / "outputs" / "ra2_orbit_demand_analysis.json"))
    parser.add_argument("--output-automaton", default=str(ROOT / "outputs" / "ra2_existing_target_automaton.json"))
    args = parser.parse_args()

    cones = json.loads(Path(args.repair_cones).read_text(encoding="utf-8"))["results"]
    novelty = json.loads(Path(args.novelty_counterfactuals).read_text(encoding="utf-8"))["results"]

    demand_results = {}
    for h, cone in cones.items():
        hall = hall_check_for_hole_demand(cone["repair_cone"])
        demand_results[h] = {
            "hole_demand_hall_check": hall,
            "global_orbit_credit_slack": novelty[h]["rho_A_global_orbit_credit"]["slack"],
        }
        print(h[:12], "Hall holds for hole demand:", hall["hall_condition_holds"], "global slack:", novelty[h]["rho_A_global_orbit_credit"]["slack"])

    report_demand = {
        "schema": "ra2-orbit-demand-analysis-v1",
        "scope_note": (
            "This round modeled only the smallest available demand set (the "
            "single fragment hole) against its found repair witnesses as "
            "'supply'. No violating subset (|N(X)| < |X|) was found for any "
            "U4 state -- Hall's condition holds trivially here. A full "
            "bipartite model of ALL remaining completion demand (every "
            "unvisited hexagon phase) against ALL remaining legal target "
            "slots was NOT constructed this round -- that is a much larger "
            "undertaking (effectively the full completion search) and was "
            "out of scope given the no-large-search constraint. Reported "
            "honestly as INCOMPLETE, not as a proof that no obstruction "
            "exists at a larger scale."
        ),
        "results": demand_results,
    }
    Path(args.output_demand).write_text(json.dumps(report_demand, indent=2, sort_keys=True, default=str), encoding="utf-8")

    automaton = {
        "schema": "ra2-existing-target-automaton-v1",
        "abstract_state": "(ell_A=4 fixed, nu_A=0 fixed [forced by being A2], Phi, fresh_orbit_slack, hole_repaired, terminal_demand_class)",
        "classification_of_U4": (
            "'특정 fresh-opening word 필요' -- U4의 4개 상태는 즉시 불가능하지도, "
            "repair 이후 불가능하지도 않다(repair witness 다수 존재, 전부 legal 필요조건 통과). "
            "그렇다고 소수의 exact subcase로 완전히 닫히지도 않는다(개별 상태의 세부 지오메트리가 "
            "서로 독립임이 이미 증명됨, RA2_FOUR_SURVIVORS.md). 가장 정직한 분류는 "
            "'여전히 대형 geometry search가 필요함'이다 -- 이번 라운드가 시도한 국소적 "
            "obstruction(rho_A, Hall-type, H2a-d)이 전부 non-binding이거나 반증됐으므로, "
            "U4를 닫기 위한 다음 단계는 이번 방법론(국소 rotation-length/orbit-novelty geometry)의 "
            "연장이 아니라 다른 종류의 논증이 필요하다는 것이 이번 라운드의 주된 결론이다."
        ),
        "transitions": {
            "(Phi=5, hole=True) -[repair]-> (Phi=5, hole=False)": "REALIZED, cheap, non-binding",
            "(Phi=5, hole=True) -[non-repair]-> (Phi<=5, hole=True)": "REALIZED, dominant branch",
            "(any, hole=False) -[...]-> terminal": "미탐구 (전체 완주 탐색 범위 밖)",
        },
    }
    Path(args.output_automaton).write_text(json.dumps(automaton, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": [args.output_demand, args.output_automaton]}, indent=2))


if __name__ == "__main__":
    main()
