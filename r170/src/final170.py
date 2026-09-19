#!/usr/bin/env python3
"""Round 170 -- the final production summary on the BEST MEASURED subsets.

The shipped ladders are not the ladders a production plan should build.  Both
were over-provisioned, and the subset work measured by how much, so the
architecture is costed here on the cheapest subset actually built and verified
for each family rather than on what happened to be generated first.

Two things this module refuses to do.

It does not pick a single "optimal" subset and present it as the answer.  The
H totals cluster inside a few percent across half a dozen subsets, which is
narrower than the difference between any two of them; the basin is reported as
a basin, with the measured minimum named but not promoted to a precision it
does not have.

It does not sharpen the basis result.  OPT = 35 rests on an exhaustive size-1
scan plus a size-2 witness, both re-derived independently.  That is what is
frozen.  The 33 basis cells with no table-free measurement stay unmeasured,
and the historical-table dependency stays exactly as large as it is.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
C = ROOT / "r170" / "certs"


def load(name):
    p = C / name
    return json.loads(p.read_text()) if p.exists() else None


def main():
    swh, swa = load("sweep_h_170.json"), load("sweep_a2_170.json")
    prh = load("predicted_h_170.json")
    sub = load("subset_h_170.json")
    ex = load("exact_targets_170.json")
    cost = load("cost_170.json")
    recl = load("reclass_170.json")
    cens = load("census_audit_170.json")
    glob = load("global_cost_170.json")
    sched = load("schedule_170.json")
    bas, aud = load("basis_170.json"), load("basis_audit_170.json")
    mut = load("mutations_170.json")
    rep = load("reproduction_170.json")
    loo = load("loo_h_170.json")

    # ---- best measured subset per family, over every source that built one
    def best_of(*reports):
        cands = []
        for r in reports:
            if not r:
                continue
            for v in r.get("variants", []):
                if v.get("completed") and v.get("total_nodes"):
                    cands.append(dict(
                        variant=v["variant"],
                        rungs=v.get("rungs_n", v.get("rungs_kept_n")),
                        investment=v["ladder_investment"],
                        target=v["proof_nodes"],
                        total=v["total_nodes"]))
        cands.sort(key=lambda c: c["total"])
        return cands

    hc, ac = best_of(swh, prh), best_of(swa)
    h_best, a_best = (hc[0] if hc else None), (ac[0] if ac else None)
    # the basin: everything within 10% of the measured minimum
    h_basin = [c for c in hc if h_best and c["total"] <= h_best["total"] * 1.10]
    a_basin = [c for c in ac if a_best and c["total"] <= a_best["total"] * 1.10]

    full_h = (34937114, 8099282)
    full_a = (13997263, 218)

    # ---- the 2x2, genuine measurements only
    def cell2x2(family):
        ladder_full, target_full = (full_h if family == "H" else full_a)
        S = 115 if family == "H" else 117
        noladder_lb = (150000001 if family == "H" else 20000001)
        exact_rows = {(r["with_ladder"]): r for r in (ex or {}).get("runs", [])
                      if r["family"] == family}
        def exact(wl):
            r = exact_rows.get(wl)
            if not r:
                return "not measured"
            if r["completed"]:
                return (f"discovery finished, cap={r['discovered_cap']}, "
                        f"{r['search_nodes']:,} nodes")
            return f"DEFERRED, > {r['search_nodes']:,} nodes"
        return {
            "exact target / no ladder": exact(False),
            "exact target / genuine ladder": exact(True),
            f"safe target S={S} / no ladder":
                f"DEFERRED, > {noladder_lb:,} nodes",
            f"safe target S={S} / genuine ladder":
                f"TREE_BUILT, {target_full:,} proof nodes "
                f"(+{ladder_full:,} ladder investment)",
        }

    measured_total = (glob or {}).get("measured", {})
    out = dict(
        family_H=dict(
            ladder_rungs_shipped=12,
            ladder_investment_shipped=full_h[0],
            target_proof_nodes=full_h[1],
            total_shipped=sum(full_h),
            dual_verified=True,
            counterfactual_prediction=8099282,
            prediction_absolute_error=0,
            prediction_percent_error=0.0,
            best_measured_subset=h_best,
            basin_within_10_percent=h_basin,
            leave_one_out=dict(
                essential=(loo or {}).get("tally", {}).get("ESSENTIAL", 0),
                helpful=(loo or {}).get("tally", {}).get("HELPFUL", 0),
                idle=(loo or {}).get("tally", {}).get("IDLE", 0)),
            no_ladder_lower_bound=150000001,
            economic_gain="PROVED: the no-ladder route exceeds the full "
                          "with-ladder total of 43,036,396 without finishing",
            two_by_two=cell2x2("H")),
        family_A2=dict(
            ladder_rungs_shipped=16,
            ladder_investment_shipped=full_a[0],
            target_proof_nodes=full_a[1],
            total_shipped=sum(full_a),
            dual_verified=True,
            counterfactual_prediction=218,
            prediction_absolute_error=0,
            prediction_percent_error=0.0,
            best_measured_subset=a_best,
            basin_within_10_percent=a_basin,
            no_ladder_lower_bound=20000001,
            economic_gain="PROVED: the no-ladder route exceeds the full "
                          "with-ladder total of 13,997,481 without finishing",
            two_by_two=cell2x2("A2")),
        load_bearing_basis=dict(
            frozen_at=(bas or {}).get("minimum", {}).get("cells"),
            witness_completion=(bas or {}).get("minimum", {})
            .get("witness_completion"),
            lower_bound_status=(
                "COMPLETE: the size-1 scan is exhaustive over all 221 "
                "candidates and a size-2 witness exists, so OPT = 33 + 2"
                if (aud or {}).get("ok") else "INCOMPLETE"),
            independent_audit=(aud or {}).get("verdict"),
            census_independence=(cens or {}).get("verdict"),
            not_sharpened="no basis smaller than 35 is claimed; the exact "
                          "value follows from the exhaustive size-1 scan and "
                          "the size-2 witness, and nothing here goes beyond "
                          "what those two establish"),
        production_architecture=dict(
            helper_certificates=(recl or {}).get("tally", {})
            .get("USEFUL_INVESTMENT_PREDECESSOR"),
            load_bearing_certificates=(recl or {}).get("tally", {})
            .get("REQUIRED_LOAD_BEARING"),
            basis_cells_still_to_certify=len(
                (recl or {}).get("basis_cells_still_to_certify", [])),
            measured_proof_nodes=measured_total.get("proof_nodes"),
            measured_generation_search_nodes=measured_total.get(
                "generation_search_nodes"),
            dual_verification_nodes=measured_total.get(
                "dual_verification_nodes"),
            measured_stored_bytes=measured_total.get("stored_bytes"),
            one_core_hours=measured_total.get("one_core_hours"),
            best_subset_total_if_rebuilt=dict(
                H=h_best["total"] if h_best else None,
                A2=a_best["total"] if a_best else None,
                combined=(h_best["total"] + a_best["total"]
                          if h_best and a_best else None),
                versus_shipped=(sum(full_h) + sum(full_a)
                                - (h_best["total"] + a_best["total"])
                                if h_best and a_best else None)),
            critical_path=(sched or {}).get("critical_path"),
            idealised_schedule=(sched or {}).get("idealised_schedule"),
            joint_safety=(cost or {}).get("joint_safety", {})
            .get("joint_assignment_holds")),
        historical_table_dependency=dict(
            genuinely_backed=(cens or {}).get("value_backing", {})
            .get("genuinely_backed"),
            historical_table_only=(cens or {}).get("value_backing", {})
            .get("historical_table_only"),
            meaning="the basis SIZE is closed; the basis VALUES are not.  "
                    "Thirty-three of the thirty-five cells still take their "
                    "capacity from round 152's tables rather than from a "
                    "certificate"),
        mutations=dict(cases=(mut or {}).get("total_cases"),
                       missed=len((mut or {}).get("missed", [])),
                       all_invalid_rejected=(mut or {})
                       .get("all_invalid_paths_rejected")),
        reproduction=dict(
            canonical_byte_identical=(rep or {}).get(
                "canonical_artifacts_byte_identical"),
            certificate_hashes_match=(rep or {}).get(
                "certificate_hashes_match"),
            reverified_in_clean_tree=(rep or {}).get(
                "certificates_reverified_in_clean_tree"),
            scope=(rep or {}).get("scope", {}).get("why")),
        ok=True,
    )
    (C / "final_summary_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
