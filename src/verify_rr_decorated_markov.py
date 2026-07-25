#!/usr/bin/env python3
"""Round 20, sections 2, 4, 5, 6, 15: minimality ablation of the
decorated boundary state, its Markov-completeness, and the decorated
predicates for chaining and same-component.

WHY THE ABLATION IS DESIGNED THIS WAY (this matters -- the naive design
is vacuous):

Round 19 established that in this universe all 2,234 post-R2 ExactStates
are reached by exactly one boundary each. Consequently ANY key that
contains the full ExactState separates every boundary, so "remove a
decoration field and check for collisions" would report "no collision"
for every field -- a vacuous result that would wrongly suggest every
decoration field is unnecessary.

So the ablation here drops the ExactState and asks the sharp question
instead: does the DECORATION ALONE determine chaining, same-component,
and the legal-trailing-edge signature? Then, field by field, does
removing that field break the determination? A break is an EXACT
COUNTERCASE (two boundaries agreeing on the reduced decoration but
disagreeing on a relation), which is genuine evidence of necessity.
Fields whose removal breaks nothing are reported as "necessity
undetermined in this universe" -- never as "unnecessary".
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

ALL_FIELDS = [
    "abandonment_ell", "hub_id",
    "r1_source_orbit", "r1_source_phase", "r1_target_orbit", "r1_target_phase",
    "r1_target_hexagon", "r1_macro_index",
    "r2_source_orbit", "r2_source_phase", "r2_target_orbit", "r2_target_phase",
    "r2_target_hexagon", "r2_macro_index",
    "hub_completer_macro_index", "hub_completer_orbit", "hub_completer_phase",
    "hub_completer_hexagon", "hub_completer_kind", "hub_completer_is_r1",
    "r1_target_hub_distance", "r2_source_hub_distance", "r2_target_hub_distance",
    "r2_meet_is_hub", "r1_boundary_orientation", "fresh_orbit_openings",
    "preparation_family",
]

TARGETS = {
    "chaining": lambda b: b["chaining"],
    "same_component": lambda b: b["same_component"],
    "trailing_edge_signature": lambda b: tuple(e["label"] for e in b["legal_trailing_edges"]),
}


def key_of(b: Dict[str, Any], fields: List[str]) -> Tuple:
    d = b["decoration"]
    return tuple(d.get(f) for f in fields)


def determination_test(boundaries: List[Dict[str, Any]], fields: List[str]) -> Dict[str, Any]:
    """Does the given decoration subset determine each target relation?"""
    out = {}
    for tname, tfn in TARGETS.items():
        groups: Dict[Tuple, set] = defaultdict(set)
        example: Dict[Tuple, list] = defaultdict(list)
        for b in boundaries:
            k = key_of(b, fields)
            groups[k].add(tfn(b))
            if len(example[k]) < 2:
                example[k].append(b)
        bad = {k: v for k, v in groups.items() if len(v) > 1}
        ex = None
        if bad:
            k0 = next(iter(bad))
            ex = {
                "reduced_key": list(k0),
                "conflicting_values": sorted(str(x) for x in bad[k0]),
                "boundary_a": {"raw_state_hash": example[k0][0]["raw_state_hash"],
                                "path": example[k0][0]["path_from_abandonment_root"],
                                tname: str(tfn(example[k0][0]))},
                "boundary_b": {"raw_state_hash": example[k0][1]["raw_state_hash"],
                                "path": example[k0][1]["path_from_abandonment_root"],
                                tname: str(tfn(example[k0][1]))} if len(example[k0]) > 1 else None,
            }
        out[tname] = {
            "determined": len(bad) == 0,
            "distinct_keys": len(groups),
            "conflicting_key_count": len(bad),
            "exact_counterexample": ex,
        }
    return out


def predicate_eval(boundaries, name, fn, target_fn):
    tp = fp = fneg = tn = 0
    fp_ex = fn_ex = None
    for b in boundaries:
        p, t = fn(b), target_fn(b)
        if p and t:
            tp += 1
        elif p and not t:
            fp += 1
            if fp_ex is None:
                fp_ex = {"raw_state_hash": b["raw_state_hash"], "path": b["path_from_abandonment_root"]}
        elif not p and t:
            fneg += 1
            if fn_ex is None:
                fn_ex = {"raw_state_hash": b["raw_state_hash"], "path": b["path_from_abandonment_root"]}
        else:
            tn += 1
    return {"predicate": name, "true_positive": tp, "false_positive": fp,
            "false_negative": fneg, "true_negative": tn,
            "sufficient": fp == 0 and tp > 0, "necessary": fneg == 0,
            "iff": fp == 0 and fneg == 0 and tp > 0,
            "false_positive_example": fp_ex, "false_negative_example": fn_ex}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "rr_decorated_l5_ledger.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_decorated_ablation.json"))
    args = parser.parse_args()

    data = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    boundaries = [b for r in data["results_by_ell"].values() for b in r["all_boundaries"]]
    print(f"total R2 boundaries (event level): {len(boundaries)}")

    # ---- section 3 check: does the tie choice ever change a relation? ----
    stab = defaultdict(int)
    tievar = defaultdict(int)
    for b in boundaries:
        stab[b["stabilizer_size"]] += 1
        tievar[b["tie_variant_count"]] += 1
    print(f"stabilizer sizes: {dict(stab)}; distinct transported variants per boundary: {dict(tievar)}")

    # ---- section 4/2: full decoration determination ----
    full = determination_test(boundaries, ALL_FIELDS)
    print("\nFULL decoration (no ExactState) determines:")
    for t, d in full.items():
        print(f"  {t:26s} determined={d['determined']} distinct_keys={d['distinct_keys']} conflicts={d['conflicting_key_count']}")

    # ---- section 2: per-field ablation ----
    ablation = {}
    print("\nPer-field ablation (drop one field, re-test determination):")
    for f in ALL_FIELDS:
        reduced = [x for x in ALL_FIELDS if x != f]
        res = determination_test(boundaries, reduced)
        broke = [t for t, d in res.items() if not d["determined"]]
        ablation[f] = {"broke_targets": broke, "detail": res}
        status = ("NECESSARY for " + ",".join(broke)) if broke else "necessity undetermined in this universe"
        print(f"  drop {f:28s} -> {status}")

    # ---- minimal sufficient subset (greedy) ----
    keep = list(ALL_FIELDS)
    for f in list(ALL_FIELDS):
        trial = [x for x in keep if x != f]
        res = determination_test(boundaries, trial)
        if all(d["determined"] for d in res.values()):
            keep = trial
    minimal = determination_test(boundaries, keep)
    print(f"\nGreedy minimal determining subset ({len(keep)} fields): {keep}")
    print(f"  determines all targets: {all(d['determined'] for d in minimal.values())}")

    # ---- section 5: non-trivial chaining predicates ----
    chain_preds = {
        "DEFINITION r1_target==r2_source (excluded as trivial)":
            lambda b: b["decoration"]["r1_target_orbit"] == b["decoration"]["r2_source_orbit"],
        "completer_orbit==r1_target AND r2 fires at completion point":
            lambda b: (b["decoration"]["hub_completer_orbit"] == b["decoration"]["r1_target_orbit"]
                       and b["decoration"]["r2_source_orbit"] == b["decoration"]["hub_completer_orbit"]
                       and b["decoration"]["r2_source_phase"] == b["decoration"]["hub_completer_phase"]),
        "completer_orbit == r1_target_orbit":
            lambda b: b["decoration"]["hub_completer_orbit"] == b["decoration"]["r1_target_orbit"],
        "r2 source is the hub completion point":
            lambda b: (b["decoration"]["r2_source_orbit"] == b["decoration"]["hub_completer_orbit"]
                       and b["decoration"]["r2_source_phase"] == b["decoration"]["hub_completer_phase"]),
        "r1_target_hub_distance == r2_source_hub_distance == 1":
            lambda b: b["decoration"]["r1_target_hub_distance"] == 1 and b["decoration"]["r2_source_hub_distance"] == 1,
        "same_component (Round 19 result, for comparison)":
            lambda b: b["same_component"],
    }
    print("\nSection 5 -- chaining predicates:")
    chain_res = []
    for n, f in chain_preds.items():
        r = predicate_eval(boundaries, n, f, TARGETS["chaining"])
        chain_res.append(r)
        tag = "IFF " if r["iff"] else ("suff" if r["sufficient"] else ("nec " if r["necessary"] else "-   "))
        print(f"  {tag} {n:58s} tp={r['true_positive']:4d} fp={r['false_positive']:4d} fn={r['false_negative']:4d}")

    # ---- section 6: same-component decorated predicates ----
    same_preds = {
        "r2_meet_is_hub (LCA form)": lambda b: b["decoration"]["r2_meet_is_hub"],
        "both hub distances finite": lambda b: (b["decoration"]["r2_source_hub_distance"] is not None
                                                 and b["decoration"]["r2_target_hub_distance"] is not None),
        "both roots are hub component (Round 19)": lambda b: b["r2_source_root_is_hub"] and b["r2_target_root_is_hub"],
    }
    print("\nSection 6 -- same-component predicates:")
    same_res = []
    for n, f in same_preds.items():
        r = predicate_eval(boundaries, n, f, TARGETS["same_component"])
        same_res.append(r)
        tag = "IFF " if r["iff"] else ("suff" if r["sufficient"] else ("nec " if r["necessary"] else "-   "))
        print(f"  {tag} {n:48s} tp={r['true_positive']:4d} fp={r['false_positive']:4d} fn={r['false_negative']:4d}")

    report = {
        "schema": "rr-decorated-ablation-v1",
        "ablation_design_note": (
            "The ExactState is deliberately EXCLUDED from every key. Including it "
            "would make the ablation vacuous, because in this universe each of the "
            "2,234 post-R2 ExactStates is reached by exactly one boundary, so any "
            "key containing the state separates everything regardless of decoration."
        ),
        "boundary_count_event_level": len(boundaries),
        "stabilizer_sizes": dict(stab),
        "transported_variant_counts": dict(tievar),
        "full_decoration_determination": full,
        "per_field_ablation": ablation,
        "greedy_minimal_subset": keep,
        "greedy_minimal_determination": minimal,
        "section5_chaining_predicates": chain_res,
        "section6_same_component_predicates": same_res,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", args.output)


if __name__ == "__main__":
    main()
