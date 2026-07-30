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
    """Deliberately conservative: a source reference is not waved through."""
    return [
        {"historical_result": "Rounds 30–32 Target-B results", "classification": "NOT_AFFECTED",
         "reason": "No direct true_phase_walk_capacity call exists before its Round-33 introduction."},
        {"historical_result": "Round 33 initial phase-walk refinement theorem", "classification": "RETRACTION_REQUIRED",
         "reason": "The published generic 'true capacity' wording is too broad: the replayed three-edge continuation exceeds value 2. Its seven-row numerical refinement removed zero survivors, so no earlier exclusion count changes, but the theorem needs a full-segment precondition or withdrawal."},
        {"historical_result": "Round 34 segment-successor static capacity profiles", "classification": "INCOMPLETE_AUDIT",
         "reason": "build_rr_segment_successors.py imports the helper-derived capacity table. A new proof that its full-segment model excludes the counterexample's partial landing, or a rerun without that assumption, is required before retaining every profile conclusion."},
        {"historical_result": "Round 34 flow-first Target-B ordering/results", "classification": "INCOMPLETE_AUDIT",
         "reason": "search_rr_target_b_flow.py reads the same table. It may be used only for ordering, but the audited artefact chain has not been recomputed with the narrowed theorem."},
        {"historical_result": "Round 35 Target-A exact traversal", "classification": "NOT_AFFECTED",
         "reason": "The Root-local Q1 traversal uses literal exact transitions and no true_phase_walk_capacity call."},
        {"historical_result": "Round 37 1,398 coarse boundary exclusions", "classification": "RETAINED_BY_INDEPENDENT_PROOF",
         "reason": "Round-38 replays every boundary and recomputes bound_1 < B+1. Every row already fails the coarse theorem, independent of bound_3."},
        {"historical_result": "Round 37 root-level envelope theorem", "classification": "RETAINED_BY_INDEPENDENT_PROOF",
         "reason": "The independent envelope uses only M=P−5O, k, Ndef, and the occupancy-independent four-preserving-run bound; it does not call the rejected helper."},
    ]


def audit_callsites() -> dict[str, Any]:
    references = {rev: git_grep(rev) for rev in ("a0ca357", "d664019", "51dcab7", R37)}
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
    ]
    return {"schema": "rr-round38-phase-capacity-scope-audit-v1", "counterexample": ce,
            "source_references": references, "historical_assessment": historical_assessment(),
            "claim_provenance": provenance,
            "required_action": "Do not use true_phase_walk_capacity as a generic future-macro capacity bound. Revalidate Round-34 full-segment consumers before relying on them."}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_round38_claim_provenance.json")); a = ap.parse_args()
    data = audit_callsites()
    Path(a.out).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"counterexample_prediction": data["counterexample"]["old_prediction"], "legal_edges": 3}, indent=2))


if __name__ == "__main__":
    main()
