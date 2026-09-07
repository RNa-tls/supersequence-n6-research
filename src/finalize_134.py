#!/usr/bin/env python3
"""라운드 134 — 감사 판정 JSON 과 master 원장 갱신."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
sys.path.insert(0, str(ROOT / "src"))


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    a = json.loads((OUT / "rr_contraction_audit_134.json").read_text())
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = None
    V = "CONFIRMED"
    verdicts = {
        "single_locked_block_contraction_lemma": dict(
            verdict=V,
            evidence="3,600 n=6 blocks (720 words x 5 splits) and 72 n=4 blocks, zero "
                     "violations; entrance v and exit sigma^5(v) identical, five internal "
                     "joints all omega=2, dP = -5, dO = -1, dD = dS = dH = 0"),
        "external_context_preservation": dict(
            verdict=V,
            evidence="omega and legal_joint are pure functions of the ordered boundary "
                     "word pair, and contraction preserves both boundary words verbatim; "
                     "4,800 seam-replay pairs (all four successor move types) show no "
                     "weight change and identical literal seam text"),
        "alpha_double_contraction": dict(
            verdict=V,
            evidence="the two locked blocks are disjoint in all 100 configurations, each "
                     "has the required shape, and the order is irrelevant"),
        "model_T_double_contraction": dict(
            verdict=V,
            evidence="both blocks contractible; the 2/100 configurations whose blocks "
                     "overlap all have T_0 = T_1 and are impossible (ten passes in a "
                     "five-slot orbit)",
            audit_finding="Astra's stated argument OMITS the hypothesis T_0 != T_1, which "
                          "is load-bearing for 'O decreases by exactly 2'. It is true and "
                          "provable in one line, and this audit supplies that proof."),
        "beta_nested_contraction": dict(
            verdict=V,
            evidence="before contraction the outer structure is 11 passes, so outer-first "
                     "is not even applicable (100/100); after contracting the inner block "
                     "the outer is EXACTLY a locked 6-pass block - opener_0 followed by "
                     "tau^1(c0)..tau^5(c0) = closer_0 filling all five phases (100/100)"),
        "contracted_parameter_accounting": dict(
            verdict=V,
            evidence="recomputed independently from P=122, O=28, D=18, S=25, H=0: "
                     "P'=112, O'=26, D'=5*26-112=18, S'=25, H'=0"),
        "full_pass_chain_identity": dict(
            verdict=V,
            evidence="S' = (r'-1-f_out') + x' by counting joints; every contracted pass is "
                     "FULL and a full pass's omega=2 successor is tau(entry) in the same "
                     "orbit, so f_out' = 0, giving S' = O' - 1 + e' + x' with NO endpoint "
                     "correction - valid for a partial chain. 25 = 26 - 1 + e' + x' forces "
                     "e' = x' = 0 since both are non-negative"),
        "round115_model_inclusion": dict(
            verdict=V,
            evidence="11-point checklist all satisfied. The decisive fact: M3a is ALWAYS "
                     "same-orbit (720/720), so it is an intra-run x-arc and never an "
                     "inter-run connector; R115's two-connector chain model (W3b = M3b, "
                     "W3c = M3c) is therefore complete, and with x' = 0 the contracted "
                     "object contains no M3a joint, so all 25 of its omega=3 joints are "
                     "chain connectors and the whole 112-pass object is ONE chain. "
                     "chain_capacity_115.c bounds a CHAIN and never requires a complete "
                     "120-pass cover, so no completeness condition is imported"),
        "N_star_provenance_and_replay": dict(
            verdict=V,
            evidence="N*(0,0,20) = 103 with capped=false - exhaustively proved, not "
                     "observed. Independently replayed: N*(0,0,18) = 103 in 626,824,474 "
                     "nodes and N*(0,0,20) = 103 in 2,465,729,298 nodes, both capped=false "
                     "and node-for-node identical to the stored table",
            replay=dict(s18=dict(passes=103, nodes=626824474, capped=False),
                        s20=dict(passes=103, nodes=2465729298, capped=False))),
        "final_112_gt_103_contradiction": dict(
            verdict=V,
            evidence="both quantities count FULL PASSES in a single chain: R115's `passes` "
                     "counter and the contracted P'. 112 > 103, and the contracted object "
                     "satisfies b=0, g=0 and deficit sum 18 <= 20, so it lies in the "
                     "bounded class. Contradiction"),
    }
    rep = dict(
        round=134, kind="PROOF AUDIT",
        audit_of="Astra/Codex locked-block contraction proof closing type-B (k,G) = (4,2)",
        overall="CONFIRMED",
        verdicts=verdicts,
        critical_failure_rule=dict(
            A_external_context_preserving_contraction="CONFIRMED",
            B_round115_model_inclusion="CONFIRMED",
            may_close=True),
        contraction_lemma=dict(
            statement=("Let a walk contain a LOCKED BLOCK: a short pass (v, b) followed by "
                       "five passes filling all five phases of orb(sigma^b(v)), the last of "
                       "which is (sigma^b(v), 6-b). Replacing the six passes by the single "
                       "full pass (v, 6) yields a walk with the same boundary words, hence "
                       "the same external joints, and with P -> P-5, O -> O-1, D, S, H "
                       "unchanged."),
            side_conditions=["orb(sigma^b(v)) != orb(v)  (verified in all 3,600 cases)",
                             "T_0 != T_1 for the two blocks  (Astra omitted this; proved "
                             "here: two five-phase runs cannot share a five-slot orbit)"],
            note=("the lemma is about SHAPE, not about the Round-131/132 lock holding - "
                  "this matters because in beta the outer lock is BROKEN yet the outer "
                  "structure acquires the locked-block shape after the inner contraction")),
        parameter_table=a["parameters"],
        round115_checklist=a["round115_inclusion"]["checks"],
        m3a_fact=a["m3a_orbit_fact"],
        local_suite=dict(n6_single_block_cases=a["single_block_lemma"]["cases"],
                         n4_control_cases=a["small_n_control"]["cases"],
                         seam_replay_pairs=a["seam_replay"]["pairs"],
                         all_clean=(a["single_block_lemma"]["clean"]
                                    and a["small_n_control"]["clean"]
                                    and a["seam_replay"]["clean"])),
        gap_independence=a["gap_independence"],
        counterexample_search=a["counterexamples"],
        required_side_condition=a["required_side_condition"],
        scope=dict(
            establishes="NR6-conditional closure of the outer cell (k,G) = (4,2)",
            does_not_establish=["L6 >= 872", "NR6"],
            NR6="ASSUMED"),
        ledger={"OUTER_CELLS_CLOSED": "10/55 (k,G)",
                "previous": "9/55",
                "cell_closed_by": "Astra contraction proof, independently audited by "
                                  "Claude in Round 134",
                "INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_Q2": "6396/6396",
                "NR6": "ASSUMED"},
        certificate=dict(
            source_commit=commit, gcc="gcc -O2",
            chain_capacity_115_c=sha(ROOT / "src" / "chain_capacity_115.c"),
            chain_capacity_115_bin=sha(ROOT / "src" / "chain_capacity_115.bin"),
            auditor_module=sha(ROOT / "src" / "audit_contraction_134.py"),
            replay_command="./chain_capacity_115.bin 0 0 {18,20} 20000000000"),
        label="ROUND-134 AUDIT - CLAUDE INDEPENDENT REVIEW OF AN ASTRA PROOF",
        disclaimer="This project has not proved L6 >= 872")
    (OUT / "rr_contraction_verdict_134.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1))

    m = OUT / "superpermutation_n6_master_status.json"
    d = json.loads(m.read_text())
    d["round_134_contraction_audit"] = rep
    m.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(dict(overall=rep["overall"],
                          verdicts={k: v["verdict"] for k, v in verdicts.items()},
                          ledger=rep["ledger"]["OUTER_CELLS_CLOSED"],
                          keys=len(d)), indent=1))


if __name__ == "__main__":
    main()
