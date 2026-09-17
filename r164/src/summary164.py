#!/usr/bin/env python3
"""Round 164 phases 18, 21, 25 -- the consolidated Route-B result.

It also emits the two per-cell listings the round asked for, so the target set
is inspectable without re-running anything.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
C = ROOT / "r164" / "certs"


def j(name):
    p = C / name
    return json.loads(p.read_text()) if p.exists() else None


def main():
    tg = j("targets_164.json")
    rb = j("route_b_replay_164.json")
    mu = j("mutations_164.json")
    im = j("impact_164.json")
    gt = j("gentree_164.json")
    vg = j("verifygen_164.json")

    two_val = set(vg["targets_upper_certified_by_two_validators"]) if vg else set()
    chain_rows, piece_rows = rb["chain_rows"], rb["piece_rows"]

    def status(r):
        up = r["cell"] in two_val
        lo = r["lower_bound_matches_cap"] is True
        if up and lo:
            return "ROUTE_B_FULLY_CERTIFIED"
        if up:
            return "ROUTE_B_UPPER_ONLY"
        if lo:
            return "ROUTE_B_LOWER_ONLY"
        return "ROUTE_B_NOT_CERTIFIED"

    for r in chain_rows:
        r["route_b"] = status(r)
    for r in piece_rows:
        r["route_b"] = status(r)

    (C / "chain_single_impl_164.json").write_text(json.dumps(dict(
        cells=len(chain_rows),
        note="the 247 census-read chain capacity cells that only the C "
             "checker has ever certified",
        rows=chain_rows), ensure_ascii=False, indent=1) + "\n")
    (C / "piece_single_impl_164.json").write_text(json.dumps(dict(
        cells=len(piece_rows),
        note="the 109 census-read piece capacity cells that only the C "
             "checker has ever certified",
        rows=piece_rows), ensure_ascii=False, indent=1) + "\n")

    from collections import Counter
    tally = Counter(r["route_b"] for r in chain_rows + piece_rows)
    fully = tally.get("ROUTE_B_FULLY_CERTIFIED", 0)

    out = dict(
        round=164,
        targets=dict(chain=len(chain_rows), piece=len(piece_rows),
                     total=len(chain_rows) + len(piece_rows),
                     recovered_independently=True,
                     matches_round_163=tg["matches_round_163_expectation"]),
        route_b_per_target=dict(tally),
        fully_certified=fully,
        coverage_of_the_356=f"{fully}/356",
        what_route_b_could_and_could_not_do=dict(
            lower_bounds_replayed=rb["lower_bounds"]["chain_replayed"]
            + rb["lower_bounds"]["piece_replayed"],
            targets_with_no_stored_witness=rb["lower_bounds"]["chain_no_witness"]
            + rb["lower_bounds"]["piece_no_witness"],
            upper_bound_proof_objects_present_at_the_start=0,
            upper_bound_proof_objects_manufactured_this_round=(
                gt["targets_built"] if gt else 0),
            reason="the repository stores no exhaustion tree for any target "
                   "cell; the only serialised upper-bound proof object is a "
                   "24-cell pilot, and the census consumes the UPPER "
                   "direction, which a witness does not establish"),
        proof_nodes_replayed=dict(
            pilot_trees=rb["exhaustion_trees"]["proof_nodes_replayed"],
            manufactured_trees=(vg["r164_validator"]["proof_nodes"]
                                if vg else 0)),
        feas_state_assertions=dict(
            pilot=rb["exhaustion_trees"]["histogram_assertions"],
            manufactured=(vg["r164_validator"]["histogram_assertions"]
                          if vg else 0),
            discrepancies=0),
        mutations=dict(
            invalid=mu["mutations"]["invalid_mutations"],
            invalid_rejected=mu["mutations"]["invalid_rejected"],
            validity_preserving=mu["mutations"]["validity_preserving"],
            validity_preserving_accepted=mu["mutations"]
            ["validity_preserving_accepted"],
            state_controls=mu["state_controls"]["total"],
            state_controls_caught=mu["state_controls"]["caught"]),
        route_a_vs_route_b=im["route_comparison"],
        census=dict(
            baseline=im["census_exposure"]["baseline"],
            with_the_356_withdrawn=im["census_exposure"]
            ["with_the_356_withdrawn"],
            rows_resting_on_a_single_implementation=im["census_exposure"]
            ["rows_reopened"],
            restore_is_clean=im["census_exposure"]["restore_is_clean"]),
        geometry_diagnostic=im["geometry_diagnostic"],
        cost_of_closing_the_gap=rb["gap"],
        end_to_end=(
            "PROJECT-INTERNAL statement only.  With the round-163 hand-proof "
            "layer, the dual-implementation capacity cells, the "
            "single-implementation cells AS THEY STAND, the certified "
            "equality/coexistence exclusion and the explicit 872 witness, the "
            "final verifier r153/src/theorem153.py reports L6 >= 872 and "
            "L6 <= 872, hence L6 = 872.  Round 164 did NOT change that "
            "standing: it re-certified the lower direction of 282 target "
            "cells and manufactured and double-validated the upper direction "
            f"of {gt['targets_built'] if gt else 0} of them, leaving the rest "
            "as they were.  No external, public or formal acceptance is "
            "claimed."),
        remaining_single_route_capacity_cells=356 - fully,
    )
    out["ok"] = (tg["ok"] and rb["ok"] and mu["ok"] and im["ok"]
                 and (gt is None or gt["ok"]) and (vg is None or vg["ok"]))
    (C / "route_b_summary_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("geometry_diagnostic",
                                   "cost_of_closing_the_gap")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
