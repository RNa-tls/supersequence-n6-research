#!/usr/bin/env python3
"""Consolidates the U4-specific defect-exchange findings (sections 6-7 of
this round) into outputs/u4_exchange_obstructions.json, and verifies the
exchange-distance chi computation directly against the ledger.

Reuses data already produced by analyze_defect_exchange.py and
search_a2r_minimum_depth.py -- no new search.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent

U4_HASHES = {
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--a2r-min", default=str(ROOT / "outputs" / "a2r_minimum_witnesses.json"))
    parser.add_argument("--exchange-table", default=str(ROOT / "outputs" / "ra2_a2r_exchange_table.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "u4_exchange_obstructions.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]["witnesses"]
    a2r_min = json.loads(Path(args.a2r_min).read_text(encoding="utf-8"))
    exchange_table = json.loads(Path(args.exchange_table).read_text(encoding="utf-8"))

    a2r_min_depth = a2r_min["min_depth_found"]

    results: Dict[str, Any] = {}
    depth_by_group = {"U4": [], "C20": []}
    for w in ra2:
        h = w["target_hash"]
        group = "U4" if h in U4_HASHES else "C20"
        depth_to_a2 = len(w["macro_path"])
        chi = a2r_min_depth - depth_to_a2
        depth_by_group[group].append(depth_to_a2)
        entry: Dict[str, Any] = {
            "group": group,
            "depth_to_A2_in_this_RA2_witness": depth_to_a2,
            "a2r_global_minimum_depth": a2r_min_depth,
            "chi_exchange_distance": chi,
        }
        if h in U4_HASHES:
            entry["adjacent_exchange_applicable"] = False
            entry["note"] = "U4 states are non-adjacent (zero_charge_word_length in {1,2}); the adjacent-exchange truth table (RA2_A2R_EXCHANGE_THEOREM.md) does not classify them."
        else:
            adj = exchange_table["adjacent_exchange_results"].get(h, {}).get("adjacent_exchange_test", {})
            entry["adjacent_exchange_applicable"] = adj.get("adjacent", False)
            if adj.get("adjacent"):
                entry["adjacent_exchange_legal"] = adj.get("swap_legal_full", adj.get("swap_legal"))
                entry["obstruction"] = adj.get("reason")
        results[h] = entry

    report = {
        "schema": "u4-exchange-obstructions-v1",
        "a2r_global_minimum_depth": a2r_min_depth,
        "chi_distribution_by_group": {g: sorted(set(a2r_min_depth - d for d in ds)) for g, ds in depth_by_group.items()},
        "chi_distinguishes_U4_from_C20": (
            sorted(set(a2r_min_depth - d for d in depth_by_group["U4"]))
            != sorted(set(a2r_min_depth - d for d in depth_by_group["C20"]))
        ),
        "honest_verdict": (
            "chi (exchange distance, defined as A2R's global minimum depth minus "
            "how deep this RA2 witness itself needed to reach A2) does NOT "
            "distinguish U4 from C20 -- both groups span the same {0,1} range. "
            "U4's 4 states are additionally outside the adjacent-exchange truth "
            "table's scope entirely (non-adjacent). Defect-order exchange, as "
            "explored this round, gives no new obstruction separating U4 from "
            "C20 -- see U4_EXCHANGE_OBSTRUCTION.md."
        ),
        "results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "chi_distinguishes_U4_from_C20": report["chi_distinguishes_U4_from_C20"],
        "chi_distribution_by_group": report["chi_distribution_by_group"],
    }, indent=2))


if __name__ == "__main__":
    main()
