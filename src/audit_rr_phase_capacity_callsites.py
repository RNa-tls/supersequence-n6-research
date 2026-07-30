#!/usr/bin/env python3
"""Round-38 scope audit for the rejected ``true_phase_walk_capacity`` bound.

This file reproduces the counterexample by literal engine replay and reports
call sites by historical result.  It makes no source or artefact changes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import verify_rr_round37_envelope_independent as audit

ROOT, R37 = audit.ROOT, audit.R37


def git_grep(rev: str) -> list[str]:
    out = subprocess.check_output(["git", "grep", "-n", "true_phase_walk_capacity", rev, "--", ":!outputs/*"], cwd=ROOT, text=True, encoding="utf-8")
    return [x for x in out.splitlines() if x]


def git_file_matches(rev: str, pattern: str) -> list[str]:
    result = subprocess.run(["git", "grep", "-il", "-E", pattern, rev, "--", ".", ":!legacy_research/*"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr)
    return [x for x in result.stdout.splitlines() if x]


def counterexample() -> dict[str, Any]:
    prefixes = audit.git_json("outputs/rr_long_excursion_prefixes.json")
    ledger = audit.git_json("outputs/rr_1398_boundary_capacity_ledger.json")
    root, _, _, _ = audit.replay_root("long_found_142", prefixes)
    row = next(r for r in ledger["rows"] if r["root_id"] == "long_found_142")
    boundary = audit.replay_macro_path(root, row["replay_certificate"]["path"])
    prediction = audit.old_phase_capacity(boundary)
    assert prediction == 2
    extension = ("rot^0;w3:120", "rot^3;w2:10", "rot^4;w2:10")
    states = []
    current = boundary
    for label in extension:
        current = audit.replay_macro_path(current, (label,))
        h = audit.core.hexagon_id(current.p)
        q, phase = audit.exact.ORBIT_PHASE[current.p]
        states.append({"label": label, "P": current.P, "O": current.O,
                       "Ndef": current.Ndef, "current_permutation": list(current.p),
                       "orbit": q, "phase": phase, "landing_hexagon": h,
                       "landing_hex_mask": current.hex_masks[h],
                       "landing_hex_popcount": current.hex_masks[h].bit_count()})
    assert len(states) == 3 and states[-1]["landing_hex_popcount"] == 5
    return {"identifier": "long_found_142", "boundary_path": row["replay_certificate"]["path"],
            "boundary_raw_hash": row["raw_boundary_hash"],
            "old_prediction": prediction, "engine_realizable_legal_macro_edges": 3,
            "extension": list(extension), "states": states,
            "scope": ("This refutes interpreting the helper as an upper bound on arbitrary future legal macro edges. "
                      "It does not by itself refute a separately proved bound restricted to a full-hexagon segment model.")}


def historical_assessment() -> list[dict[str, str]]:
    """Updated after the independent all-18 replay in Round 39."""
    return [
        {"historical_result": "Rounds 30–32 Target-B results", "classification": "NOT_AFFECTED",
         "reason": "No direct true_phase_walk_capacity call exists before its Round-33 introduction."},
        {"historical_result": "Round 33 generic initial phase-walk capacity theorem", "classification": "RETRACTION_REQUIRED",
         "reason": "The published generic 'true capacity' wording is too broad: the replayed three-edge continuation exceeds value 2. Its seven-row numerical refinement removed zero survivors, so no earlier exclusion count changes, but the theorem needs a full-segment precondition or withdrawal."},
        {"historical_result": "Round 31 port-count 9 -> 8 reduction", "classification": "RETAINED_BY_INDEPENDENT_ARGUMENT",
         "reason": "It uses c(q0), the count of unvisited-port hexagons, not the suspect ordered phase-walk helper; the corrected 18-ledger recomputes it."},
        {"historical_result": "Round 32 B+R 8 -> 7 reduction", "classification": "RETAINED_BY_INDEPENDENT_ARGUMENT",
         "reason": "The occupancy-independent re-entry penalty is recomputed directly from ExactState and independently closes the same ell0/P4 boundary."},
        {"historical_result": "Round 33 phase-derived margin table and any 2-capacity pruning", "classification": "RETRACTION_REQUIRED",
         "reason": "The helper's value 2 cannot be published as a generic future macro capacity. It was redundant for the seven selected flow roots."},
        {"historical_result": "Round 34 segment-successor metadata/capacity profiles", "classification": "RETRACTION_REQUIRED",
         "reason": "The serialized initial_capacity_max is helper-derived and must be marked descriptive/rebuilt. It is not used by the replacement proof."},
        {"historical_result": "Round 34 flow-first exact semantics and seven exhaustions", "classification": "RETAINED_EXACTLY",
         "reason": "The helper was used only for processing order. Round 39 independently replays all 18 states and reruns exact macro DFS plus B+R; all seven historical roots again exhaust."},
        {"historical_result": "Round 34 area-A-only bounded runs", "classification": "RETAINED_EXACTLY",
         "reason": "They are explicitly incomplete engine-only diagnostics and have no helper-derived prune or proof role."},
        {"historical_result": "Round 35 Target-A exact traversal", "classification": "NOT_AFFECTED",
         "reason": "The Root-local Q1 traversal uses literal exact transitions and no true_phase_walk_capacity call."},
        {"historical_result": "Round 37 1,398 coarse boundary exclusions", "classification": "RETAINED_BY_INDEPENDENT_PROOF",
         "reason": "Round-38 replays every boundary and recomputes bound_1 < B+1. Every row already fails the coarse theorem, independent of bound_3."},
        {"historical_result": "Round 37 root-level envelope theorem", "classification": "RETAINED_BY_INDEPENDENT_PROOF",
         "reason": "The independent envelope uses only M=P−5O, k, Ndef, and the occupancy-independent four-preserving-run bound; it does not call the rejected helper."},
    ]


def audit_callsites() -> dict[str, Any]:
    references = {rev: git_grep(rev) for rev in ("a0ca357", "d664019", "51dcab7", R37)}
    indirect = {
        "serialized_helper_table": ["outputs/rr_target_b_unsat_certificates.json"],
        "derived_capacity_profile": ["src/build_rr_segment_successors.py", "outputs/rr_segment_successor_index.json"],
        "ordering_only_consumer": ["src/search_rr_target_b_flow.py"],
        "documentation_and_tests_with_phase_capacity_language": git_file_matches("51dcab7", "phase-walk capacity|true_phase_walk_capacity|initial_capacity_max"),
        "engine_flow_certificate": ["src/verify_rr_target_b_flow.py", "outputs/rr_flow_certificates.json"],
        "full_block_and_port_count_material": ["research/RR_TARGET_B_FULL_BLOCK_THEOREM.md", "research/RR_TARGET_B_REFINED_CAPACITY.md"],
    }
    ce = counterexample()
    provenance = [
        {"claim": "28 long roots are Q2-impossible by root envelope", "origin": "CLAUDE", "origin_commit": R37,
         "verification": "CODEX_VERIFIED", "verification_commit": "Round 38 working tree", "exact_scope": "Q2 / completion-compatible Target-A only"},
        {"claim": "all 28 long roots have Q1 witnesses", "origin": "CLAUDE", "origin_commit": R37,
         "verification": "CODEX_COUNTEREXAMPLE", "verification_commit": "Round 38 working tree", "exact_scope": "1398 ledger witnesses only 26 roots; Q1 is not proved for long_q1_140 or long_q1_178"},
        {"claim": "true_phase_walk_capacity is a generic legal future capacity upper bound", "origin": "HISTORICAL", "origin_commit": "a0ca357",
         "verification": "CODEX_COUNTEREXAMPLE", "verification_commit": "Round 38 working tree", "exact_scope": "refuted by long_found_142 (2 predicted, 3 legal macro edges)"},
        {"claim": "all 1398 Round-37 stored boundaries fail the coarse theorem", "origin": "CLAUDE", "origin_commit": R37,
         "verification": "CODEX_VERIFIED", "verification_commit": "Round 38 working tree", "exact_scope": "word-level 1398 row ledger; independent literal replay"},
        {"claim": "the 22 Round-35 long searches remain Q2-relevant", "origin": "HISTORICAL", "origin_commit": "51dcab7",
         "verification": "CODEX_COUNTEREXAMPLE", "verification_commit": "Round 38 working tree", "exact_scope": "obsolete for Q2 under the verified envelope; still meaningful only as Q1 enumeration infrastructure"},
        {"claim": "the seven Round-34 flow roots exhaust independently of phase capacity", "origin": "HISTORICAL", "origin_commit": "d664019",
         "verification": "CODEX_VERIFIED", "verification_commit": "Round 39 working tree", "exact_scope": "replayed among all 18 boundaries with exact macro DFS and Round-32 B+R only"},
    ]
    return {"schema": "rr-round39-phase-capacity-scope-audit-v2", "counterexample": ce,
            "source_references": references, "indirect_dependency_inventory": indirect, "historical_assessment": historical_assessment(),
            "claim_provenance": provenance,
            "required_action": "Do not use true_phase_walk_capacity as a generic future-macro capacity bound. Revalidate Round-34 full-segment consumers before relying on them."}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_round38_claim_provenance.json"))
    ap.add_argument("--affected-out", default=str(ROOT / "outputs" / "rr_phase_capacity_affected_results.json"))
    a = ap.parse_args()
    data = audit_callsites()
    Path(a.out).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    Path(a.affected_out).write_text(json.dumps({
        "schema": "rr-phase-capacity-affected-results-v2",
        "direct_and_indirect_references": data["source_references"],
        "historical_results": data["historical_assessment"],
        "counterexample_identifier": data["counterexample"]["identifier"],
        "replacement": "outputs/rr_target_b_18_boundary_corrected_ledger.json",
        "note": "The corrected ledger is generated separately by src/verify_rr_target_b_without_phase_capacity.py without phase helper use.",
    }, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"counterexample_prediction": data["counterexample"]["old_prediction"], "legal_edges": 3}, indent=2))


if __name__ == "__main__":
    main()
