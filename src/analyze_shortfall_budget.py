#!/usr/bin/env python3
"""Finite classification of future shortfall-charge words for the 230 J
states (and, in detail, the 74 that survived the bounded capacity-failure
search in outputs/j_capacity_extension_profile.json).

Given a joint-boundary state S with Phi(S)=B, every future joint-boundary
sequence must have total charge sum(5-ell_i) <= B (research/J_CAPACITY_OBSTRUCTION.md,
now corrected and fully re-derived in research/SHORTFALL_BUDGET_THEOREM.md).
Since each nonzero charge value is an integer in {1,...,5} (ell in
{0,...,4}), and the total is at most B, the number of nonzero-charge
joints is at most B, and the abstract "charge multiset" (which joints,
if any, have less than a full ell=5 rotation, and by how much) ranges
over exactly the integer partitions of every value from 0 to B into parts
of size <=5 -- a small, finite, fully enumerable set for every B actually
observed (B in {0,1,2,4,5} across all 230 states).

This is deliberately an ARITHMETIC classification, not a geometric one: it
does not know or care WHICH joint (by orbit/hexagon identity) carries a
given charge, only how much charge exists and how many joints could carry
it. This is exactly the finite reduction requested -- "the infinite space
of future schedules" collapses to a handful of abstract charge-multiset
families per state.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

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


macro = _load("shortfall_words_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def partitions(total: int, max_part: int = 5) -> List[Tuple[int, ...]]:
    """All partitions of `total` into positive parts <= max_part, as sorted
    descending tuples. partitions(0) == [()] (the empty partition)."""
    if total == 0:
        return [()]
    out: List[Tuple[int, ...]] = []

    def rec(remaining: int, largest: int, current: List[int]) -> None:
        if remaining == 0:
            out.append(tuple(current))
            return
        for p in range(min(largest, remaining), 0, -1):
            current.append(p)
            rec(remaining - p, p, current)
            current.pop()

    rec(total, max_part, [])
    return out


def charge_word_families(budget: int) -> Dict[str, Any]:
    """Every abstract charge-multiset family compatible with a given budget:
    the disjoint union, over total_charge = 0..budget, of all partitions
    of total_charge into parts 1..5."""
    families = []
    for total_charge in range(0, budget + 1):
        for part in partitions(total_charge, max_part=5):
            families.append({
                "total_charge": total_charge,
                "nonzero_charge_multiset": list(part),
                "num_nonzero_charge_joints": len(part),
                "corresponding_ell_values": [5 - c for c in part],
            })
    return {
        "budget": budget,
        "family_count": len(families),
        "families": families,
    }


def survivor_classification(state: "exact.ExactState", target_hash: str) -> Dict[str, Any]:
    b = phi(state)
    n = exact.TARGET_P - state.P
    n_new = exact.TARGET_O - state.O
    n_existing = n - n_new
    r_budget = exact.TARGET_BUDGET - state.H - state.Ndef  # max further R events (N budget)
    families = charge_word_families(b)
    form = exact.f1_normal_form(state)
    return {
        "target_hash": target_hash,
        "phi": b,
        "remaining_joints_total": n,
        "remaining_new_orbit_joints_required": n_new,
        "remaining_existing_orbit_joints_required": n_existing,
        "max_further_R_events": max(r_budget, 0),
        "num_charge_word_families": families["family_count"],
        "charge_word_families": families["families"],
        "fragment_hex": form.fragment_hex if form else None,
        "current_hex": form.current_hex if form else None,
        "classification": (
            "no_charge_word_possible" if families["family_count"] == 0 else
            "exactly_one_charge_word_family" if families["family_count"] == 1 else
            "multiple_charge_word_families"
        ),
    }


def main() -> None:
    witnesses = {
        w["target_hash"]: exact.state_from_json(w["final_state_json"])
        for w in json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    }
    extension = json.loads((ROOT / "outputs" / "j_capacity_extension_profile.json").read_text())
    survivor_hashes = [
        p["target_hash"] for p in extension["per_seed"] if not p["minimal_failing_continuation_found"]
    ]
    if len(survivor_hashes) != 74:
        raise AssertionError(f"expected 74 survivors, found {len(survivor_hashes)}")

    # Section 3: the abstract charge-word family catalogue, one per distinct
    # budget value actually observed across all 230 states (not per-state --
    # the family CATALOGUE depends only on the scalar budget B).
    all_phis = sorted({phi(s) for s in witnesses.values()})
    catalogue = {str(b): charge_word_families(b) for b in all_phis}

    # Section 5: full per-survivor classification.
    survivors = [survivor_classification(witnesses[h], h) for h in survivor_hashes]
    classification_counts = Counter(s["classification"] for s in survivors)

    charge_words_out = {
        "schema": "shortfall-charge-words-v1",
        "budgets_observed_across_all_230": all_phis,
        "charge_word_family_catalogue_by_budget": catalogue,
        "note": (
            "Family count depends only on the scalar budget B, not on any "
            "other state detail -- this is the full finite reduction of "
            "'all possible future shortfall words' for every B that occurs."
        ),
    }
    (ROOT / "outputs" / "shortfall_charge_words.json").write_text(
        json.dumps(charge_words_out, indent=2, sort_keys=True), encoding="utf-8"
    )

    survivor_out = {
        "schema": "j-74-survivor-classification-v1",
        "survivor_count": len(survivors),
        "classification_counts": dict(classification_counts),
        "survivors": survivors,
    }
    (ROOT / "outputs" / "j_74_survivor_classification.json").write_text(
        json.dumps(survivor_out, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(json.dumps({
        "wrote": ["outputs/shortfall_charge_words.json", "outputs/j_74_survivor_classification.json"],
        "budgets_observed": all_phis,
        "family_counts_by_budget": {str(b): catalogue[str(b)]["family_count"] for b in all_phis},
        "survivor_classification_counts": dict(classification_counts),
    }, indent=2))


if __name__ == "__main__":
    main()
