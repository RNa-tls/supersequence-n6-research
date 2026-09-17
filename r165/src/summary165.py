#!/usr/bin/env python3
"""Round 165 phases 11, 14, 15, 19 -- the consolidated basis result.

Also fixes the three sets the round asked to be distinguished, checks the
equality rows survive the basis, and records which artefacts are deterministic
(the minimisation ones) and which are measurements (the pilots, whose runtimes
ARE the deliverable and therefore vary).
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
import hidden163 as H                                             # noqa: E402
import closure165 as CL                                           # noqa: E402

C = ROOT / "r165" / "certs"

# Phase 11: how an independent upper bound could realistically be obtained.
DIVERSITY = {
    "A_independent_clean_room_DFS": dict(
        feasible="yes, but it is Route A again",
        evidence="round 164 wrote one and reproduced Route A's node counts "
                 "exactly on 51 cells; it re-does the search, so it buys a "
                 "second implementation but no proof object"),
    "B_memoized_dynamic_programming": dict(
        feasible="no",
        evidence="r165/certs/dp_pilot_165.json -- a recurrence that keeps the "
                 "per-orbit phase cap and the token/deficit arithmetic but "
                 "drops the hexagon identity returns 120 for every cell, the "
                 "analytic bound, with a median gap of 19 against the "
                 "certified capacities.  The certified values come from the "
                 "transition geometry, which is what a DP must drop"),
    "C_SAT_encoding_with_UNSAT_proof": dict(
        feasible="yes for the PIECE model, demonstrated",
        evidence="r165/certs/sat_pilot_165.json and drat_check_165.json -- "
                 "the encoding agrees with Route A on four validation "
                 "instances, the cheapest basis piece cell is UNSAT in 1,096 "
                 "s, and two cells are DRAT-verified end to end by drat-trim. "
                 " Proofs are large: 5.23 GB for the two validation cells"),
    "D_exact_cover_or_graph_formulation": dict(
        feasible="not attempted",
        evidence="no pilot, so no claim"),
    "E_analytic_domination": dict(
        feasible="no",
        evidence="r165/certs/minimum_basis_165.json -- only 6 of the 355 "
                 "cells have a dominating dual-certified cell at all, and "
                 "none of those bounds is as tight as the cell's own; the "
                 "exposure falls from 181 rows to 180"),
    "F_exhaustion_tree_plus_small_verifier": dict(
        feasible="yes, demonstrated, and the most compact",
        evidence="round 164 manufactured and double-validated one basis "
                 "cell's tree; at 2.29 bytes per proof node the cheapest "
                 "basis piece cell would need about 12 MB, against 5.75 GB "
                 "for the same cell's DRAT proof"),
}


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    graph = json.loads((C / "row_closure_graph_165.json").read_text())
    mini = json.loads((C / "minimum_basis_165.json").read_text())
    wt = json.loads((C / "weighted_basis_165.json").read_text())
    sat = json.loads((C / "sat_pilot_165.json").read_text())
    drat = json.loads((C / "drat_check_165.json").read_text())
    dp = json.loads((C / "dp_pilot_165.json").read_text())

    ess = set(graph["essential_cells"])

    # ---------- phase 15: the census under the basis, layer by layer
    H.load()
    CERT0, PCERT0 = dict(H.CERT), dict(H.PCERT)
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    vg = json.loads((ROOT / "r164" / "certs"
                     / "verifygen_164.json").read_text())
    done = {tuple(int(x) for x in s.split("|"))
            for s in vg["targets_upper_certified_by_two_validators"]}
    red_chain = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]
                 if tuple(c) not in done
                 and "|".join(map(str, c)) not in ess]
    red_piece = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"]
                 if tuple(c) not in done
                 and "|".join(map(str, c)) not in ess]
    groups = CL.grouped()
    CL.withdraw(red_chain, red_piece)
    res = CL.evaluate(groups)
    CL.restore(CERT0, PCERT0)
    per_layer = {}
    for (t, k), v in res.items():
        per_layer.setdefault(f"L{867 + t}", Counter())[v["verdict"]] += 1
    per_layer = {k: dict(v) for k, v in sorted(per_layer.items())}
    eq_keys = [k for k, v in res.items() if v["verdict"] == "EQUALITY"]

    out = dict(
        round=165,
        inputs={p: sha(p) for p in
                ("r164/certs/targets_164.json",
                 "r164/certs/verifygen_164.json",
                 "r165/certs/row_closure_graph_165.json",
                 "r165/certs/minimum_basis_165.json",
                 "r165/certs/weighted_basis_165.json")},
        three_sets=dict(
            SINGLE_ROUTE_STORED=graph["remaining_single_route"]["total"],
            SINGLE_ROUTE_LOAD_BEARING=graph["individually_essential"],
            MINIMUM_SECOND_ROUTE_BASIS=mini["minimum_basis"]["size"],
            note="the second and third coincide here: every individually "
                 "essential cell must be in every sufficient basis, and the "
                 "essential set is itself sufficient, so the minimum basis IS "
                 "the load-bearing set and its optimality is proved"),
        exposed_rows=dict(
            without_any_single_route_cell=graph["exposed_rows"],
            after_analytic_domination=mini["exposure"]["with_domination"],
            rescued_by_domination=mini["exposure"]
            ["rows_rescued_by_domination"]),
        minimum_basis=mini["minimum_basis"],
        weighted=dict(
            minimum_cost_basis=wt["minimum_cost_basis"],
            route_a_nodes_for_the_basis=wt["cost"]
            ["route_a_nodes_for_the_basis"],
            route_a_nodes_for_all_355=wt["cost"]["route_a_nodes_for_all_355"],
            saving=wt["cost"]["saving"]),
        prerequisite_structure={
            k: v for k, v in wt["prerequisite_structure"].items()
            if k != "transitive_closure_sizes"},
        failure_sensitivity={
            k: v for k, v in wt["failure_sensitivity"].items()
            if k != "most_fragile_cells"},
        equality_rows=dict(
            census_under_the_basis=per_layer,
            L871_strict=per_layer.get("L871", {}).get("STRICTLY_CLOSED"),
            L871_equality=per_layer.get("L871", {}).get("EQUALITY"),
            equality_rows_are_exactly_two=len(eq_keys) == 2,
            equality_row_keys=[list(k[1]) for k in eq_keys],
            matches_the_known_census=(
                per_layer.get("L871", {}).get("STRICTLY_CLOSED") == 1154
                and per_layer.get("L871", {}).get("EQUALITY") == 2)),
        algorithm_diversity=DIVERSITY,
        sat_pilot=dict(
            model="piece",
            correctness_checks_agree=sat["all_correctness_checks_agree"],
            cheapest_basis_piece_cell=sat["cheapest_basis_piece_cell"],
            scaling=dict(
                cell=sat["scaling_probe"]["cell"],
                cap=sat["scaling_probe"]["cap"],
                result=sat["scaling_probe"]["result"],
                clauses=sat["scaling_probe"]["total_clauses"],
                proof_bytes=sat["scaling_probe"]["proof_bytes"]),
            drat_verified=drat["all_verified"],
            drat_cells=[r["cell"] for r in drat["cells"]],
            drat_total_proof_bytes=drat["totals"]["proof_bytes"],
            solver=drat["solver"],
            pysat_cadical_proof_defect=drat["solver_note"]),
        dp_pilot=dict(sound=dp["all_bounds_sound"], any_tight=dp["any_tight"],
                      median_gap=dp["median_gap"],
                      conclusion=dp["conclusion"]),
        artifacts=dict(
            deterministic=["r165/certs/row_closure_graph_165.json",
                           "r165/certs/minimum_basis_165.json",
                           "r165/certs/weighted_basis_165.json",
                           "r165/certs/dp_pilot_165.json",
                           "r165/certs/basis_summary_165.json"],
            measurements=["r165/certs/sat_pilot_165.json",
                          "r165/certs/drat_check_165.json"],
            note="the pilots record solver and checker RUNTIMES, which are "
                 "the point of a pilot and vary between runs; they are "
                 "labelled measurements and are excluded from the "
                 "byte-identical reproduction requirement.  The minimisation "
                 "artefacts carry no clock at all"),
        round_166_recommendation=dict(
            strategy="EXTREE_BASIS_CERTIFICATION",
            why=[
                "the basis is 288 cells, proved minimal, not 355",
                "of the six diversity options only two are demonstrated: "
                "exhaustion trees and SAT on the piece model",
                "for the same cell an exhaustion tree is about 12 MB against "
                "5.75 GB of DRAT, roughly 460x smaller, and round 164 already "
                "has a generator and two independent validators",
                "SAT covers only the piece model; the chain model's "
                "(source, target) resource rules need ~32M clauses per "
                "instance, so it cannot carry the 179 chain basis cells",
                "the certificate order gives shared prerequisites: 17 of 51 "
                "trees cite nothing and the most cited cell is the cheapest "
                "one, so a prefix pays for many cells at once"],
            scope="start with the cheapest basis cells in certificate order "
                  "and report how far a fixed node budget reaches, rather "
                  "than committing to all 288",
            not_recommended=dict(
                SAT_UNSAT_BASIS_CERTIFICATION="proof sizes are 460x the tree "
                                              "format and the chain model is "
                                              "out of reach",
                INDEPENDENT_DP_BASIS_CERTIFICATION="the pilot returns the "
                                                   "analytic bound and "
                                                   "nothing better",
                certify_all_355="67 of them are provably unnecessary")),
    )
    out["ok"] = (out["equality_rows"]["matches_the_known_census"]
                 and out["equality_rows"]["equality_rows_are_exactly_two"]
                 and mini["minimum_basis"]["proved_optimal"])
    (C / "basis_summary_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "algorithm_diversity",
                                   "prerequisite_structure")},
                     ensure_ascii=False, indent=1)[:3000])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
