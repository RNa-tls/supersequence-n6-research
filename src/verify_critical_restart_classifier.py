#!/usr/bin/env python3
"""Sections 2, 3, 4, 7: verify the combined classifier (critical-restart
signature + ell_A2=4) against all 24 RA2 states, find the minimal
difference between U4 and the C20 outlier, test the ancestry theorem
candidates C1-C4, and attempt an escape-transition lemma.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
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


macro = _load("vcrc_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1

U4_HASHES = {
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
}


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def component_map(state: "exact.ExactState") -> Dict[Any, Any]:
    parent: Dict[Any, Any] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return {node: find(node) for node in list(parent)}


def classify_witness(witness: Dict[str, Any]) -> Dict[str, Any]:
    """NOTE on a methodological correction made this round: an earlier
    version of this check (and last round's analyze_restart_blocks.py)
    computed a per-block "component_relation" using
    ORBIT_PHASE(pre-ROTATION state) as the block's "source". Because
    canonicalize() resets the walk's position to the literal identity
    after every macro-edge, that pre-rotation position is ALWAYS the
    identity (ORBIT_PHASE = (0,0)) regardless of which block is being
    looked at -- a canonicalization artifact, not a genuine per-block
    "source". This function instead uses the direct, unambiguous, and
    label-independent comparison: does the critical restart's LITERAL
    target E-orbit index equal R's own literal target E-orbit index?
    This was verified to reproduce the same 9-vs-5 split as before (see
    RA2_FIVE_STATE_COMPARISON.md for the side-by-side check), so the
    earlier finding survives despite the definitional issue -- but this
    is the more defensible formulation and the one used everywhere in
    this round's outputs."""
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    steps = []
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        target_q, _ = exact.ORBIT_PHASE[tr.target]
        steps.append({"ell": ell, "kind": kind, "target_q": target_q})
        cur = exact.canonicalize(tr.state)

    r_idx = next(i for i, s in enumerate(steps) if s["kind"] == "R")
    a2_idx = next(i for i, s in enumerate(steps) if s["kind"] == "A2")
    a2_ell = steps[a2_idx]["ell"]
    r_target_q = steps[r_idx]["target_q"]

    critical_idx = a2_idx - 1
    has_critical = critical_idx > r_idx
    signature_unrelated = False
    if has_critical:
        signature_unrelated = steps[critical_idx]["target_q"] != r_target_q

    predicted_u4 = signature_unrelated and a2_ell == 4
    actual_u4 = witness["target_hash"] in U4_HASHES
    return {
        "target_hash": witness["target_hash"], "actual_u4": actual_u4,
        "has_critical_restart": has_critical, "signature_unrelated": signature_unrelated,
        "a2_ell": a2_ell, "predicted_u4": predicted_u4,
        "outcome": (
            "TP" if predicted_u4 and actual_u4 else
            "FP" if predicted_u4 and not actual_u4 else
            "FN" if not predicted_u4 and actual_u4 else "TN"
        ),
    }


def ancestry_theorem_checks(five_ledger: Dict[str, Any]) -> Dict[str, Any]:
    entries = five_ledger["entries"]
    checks = {}
    for h, e in entries.items():
        crit = e["critical_restart"]
        checks[h] = {
            "C1_critical_orbit_is_A2_source_direct_parent": crit["target_orbit_q"] == e["a2_source_orbit_q"],
            "C2_critical_creates_A2_weight2_overlap": None,  # see note below
            "C3_LCA_increases_vs_reuse_case": None,  # requires reuse-case comparison, see doc
            "C4_ancestry_edge_unrepaired_at_ell4": None,
        }
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--five-state-ledger", default=str(ROOT / "outputs" / "ra2_five_state_ledger.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_combined_classifier.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]["witnesses"]

    results = [classify_witness(w) for w in ra2]
    counts = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    for r in results:
        counts[r["outcome"]] += 1
        print(r["target_hash"][:12], r["outcome"], "a2_ell=", r["a2_ell"], "signature_unrelated=", r["signature_unrelated"])

    five_ledger = json.loads(Path(args.five_state_ledger).read_text(encoding="utf-8"))
    ancestry = ancestry_theorem_checks(five_ledger)

    # minimal difference between outlier and U4: literal field-by-field diff already
    # shows (from analyze_ra2_five_states.py output) that critical_restart is IDENTICAL
    # across all 5 states; only a2_ell differs (0 for outlier, 4 for U4 all).
    outlier_hash = "e2b44997e7838537176bd6e0e72ea41df259f429863731b696dc76692beeb98c"
    outlier_entry = five_ledger["entries"][outlier_hash]
    u4_entries = {h: e for h, e in five_ledger["entries"].items() if e["group"] == "U4"}
    def crit_key(e):
        c = e["critical_restart"]
        return (c["kind"], c["ell"], c["source_orbit_q"], c["source_phase"], c["target_orbit_q"], c["target_phase"])

    minimal_diff = {
        "critical_restart_identical_across_all_5": all(
            crit_key(e) == crit_key(outlier_entry) for e in u4_entries.values()
        ),
        "only_differing_field": "a2_ell (outlier=0, U4=4 uniformly)",
        "outlier_a2_ell": outlier_entry["a2_ell"],
        "u4_a2_ells": {h: e["a2_ell"] for h, e in u4_entries.items()},
    }

    report = {
        "schema": "ra2-combined-classifier-v1",
        "classifier": "predicted_U4 = (critical_restart_signature == unrelated_fresh_orbit) AND (a2_ell == 4)",
        "corpus_size": 24,
        "confusion_matrix": counts,
        "classifier_status": (
            "corpus exact classifier (24/24, 0 FP, 0 FN)"
            if counts["FP"] == 0 and counts["FN"] == 0 else "NOT exact -- see per-witness results"
        ),
        "minimal_difference_outlier_vs_U4": minimal_diff,
        "ancestry_theorem_checks_partial": ancestry,
        "per_witness_results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "confusion_matrix": counts, "minimal_diff": minimal_diff}, indent=2))


if __name__ == "__main__":
    main()


