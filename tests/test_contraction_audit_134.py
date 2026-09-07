#!/usr/bin/env python3
"""라운드 134 — 축약 증명 감사의 테스트."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def a():
    return json.loads((ROOT / "outputs" / "rr_contraction_audit_134.json").read_text())


@pytest.fixture(scope="module")
def v():
    return json.loads((ROOT / "outputs" / "rr_contraction_verdict_134.json").read_text())


# --------------------------------------------------------- S2/S3/S4/S5 the lemma
def test_single_block_lemma_clean_on_all_3600_cases(a):
    s = a["single_block_lemma"]
    assert s["cases"] == 3600
    assert s["violations"] == {} and s["clean"] is True
    assert s["deltas"] == {"P": -5, "O": -1, "D": 0, "S": 0, "H": 0}


def test_small_n_control(a):
    s = a["small_n_control"]
    assert s["n"] == 4 and s["cases"] == 72 and s["clean"] is True
    assert s["deltas"]["P"] == -3 and s["deltas"]["O"] == -1 and s["deltas"]["D"] == 0


def test_seam_replay_preserves_both_external_joints(a):
    s = a["seam_replay"]
    assert s["pairs"] >= 4000 and s["violations"] == {} and s["clean"] is True


# ------------------------------------------------------------ S6/S7/S8 structures
def test_alpha_blocks_are_disjoint_and_order_independent(a):
    c = a["double_contraction"]["alpha"]["counts"]
    assert c["disjoint_blocks"] == 100 and "OVERLAP" not in c
    assert c["shape_ok"] == 200


def test_model_T_overlaps_are_exactly_the_impossible_ones(a):
    c = a["double_contraction"]["modelT"]["counts"]
    assert c.get("OVERLAP", 0) == 2, "the audit must not hide the overlapping cases"
    r = a["required_side_condition"]
    assert r["model_T_overlapping_configs"] == 2
    assert r["all_overlaps_have_T0_eq_T1"] is True
    assert r["overlaps_that_could_actually_exist"] == 0


def test_beta_requires_inner_first(a):
    c = a["double_contraction"]["beta"]["counts"]
    assert c["outer_is_11_passes"] == 100
    assert c["outer_first_invalid"] == 100
    assert c["outer_becomes_locked_block"] == 100
    assert c["inner_shape_ok"] == 100
    assert c["T0_ne_T1"] == 100


# ---------------------------------------------------------------- S9/S10 parameters
def test_contracted_parameters_recomputed(a):
    p = a["parameters"]
    assert p["contracted"] == {"P": 112, "O": 26, "D": 18, "S": 25, "H": 0}
    assert all(p["matches_astra"].values())
    assert p["e_plus_x"] == 0 and p["forces_e_and_x_zero"] is True


def test_identity_has_no_endpoint_correction(a):
    p = a["parameters"]
    assert "PARTIAL chain" in p["identity"] and "no endpoint term" in p["identity"]
    assert any("f_out' = 0" in step for step in p["identity_derivation"])


# ------------------------------------------------------- S11/S12 Round-115 inclusion
def test_m3a_is_always_same_orbit(a):
    m = a["m3a_orbit_fact"]
    assert m["M3a_omega3_sameorbitTrue"] == 720
    assert m["M3b_omega3_sameorbitFalse"] == 720
    assert m["M3c_omega3_sameorbitFalse"] == 720
    assert m["M2_omega2_sameorbitTrue"] == 720
    # the excluded connector must never appear as an inter-run move
    assert "M3a_omega3_sameorbitFalse" not in m


def test_round115_model_uses_only_two_connectors(a):
    r = a["round115_inclusion"]
    assert r["connectors_in_model"] is True
    assert r["all_satisfied"] is True
    joined = " ".join(c["hypothesis"] for c in r["checks"])
    assert "per-CHAIN, not per-complete-cover" in joined
    assert "RELAXATION" in joined


# --------------------------------------------------------------- S13/S14 provenance
def test_N_star_replay_is_exhaustive_not_capped(v):
    r = v["verdicts"]["N_star_provenance_and_replay"]["replay"]
    assert r["s18"]["passes"] == 103 and r["s18"]["capped"] is False
    assert r["s20"]["passes"] == 103 and r["s20"]["capped"] is False
    assert r["s20"]["nodes"] == 2465729298


def test_N_star_replay_reproduces_live():
    """저장 JSON 이 아니라 바이너리를 실제로 다시 돌려 확인한다 (작은 셀)."""
    binp = ROOT / "src" / "chain_capacity_115.bin"
    src = ROOT / "src" / "chain_capacity_115.c"
    if not binp.exists() or binp.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(binp), str(src)], check=True)
    out = subprocess.run([str(binp), "0", "0", "10", "20000000000"],
                         capture_output=True, text=True, check=True)
    d = json.loads(out.stdout)
    assert d["capped"] is False
    assert d["passes"] < 112, "even a looser cell must stay below the contracted 112"


# ------------------------------------------------------------------- S16/S18/S20/S21
def test_gap_independence(a):
    g = a["gap_independence"]
    assert g["gap_appears_in_argument"] is False and len(g["why"]) >= 3


def test_counterexample_search_recorded(a):
    cs = a["counterexamples"]
    assert len(cs) >= 2
    assert any("reclassified" in c.get("resolution", "") for c in cs)
    assert all(c.get("excluded_by_lock_hypothesis", True) for c in cs)


def test_all_ten_verdicts_confirmed(v):
    assert v["overall"] == "CONFIRMED"
    assert len(v["verdicts"]) == 10
    for k, val in v["verdicts"].items():
        assert val["verdict"] in ("CONFIRMED", "PARTIAL", "REFUTED")
        assert val["verdict"] == "CONFIRMED", k


def test_critical_failure_rule_satisfied(v):
    c = v["critical_failure_rule"]
    assert c["A_external_context_preserving_contraction"] == "CONFIRMED"
    assert c["B_round115_model_inclusion"] == "CONFIRMED"
    assert c["may_close"] is True


def test_audit_records_the_missing_hypothesis(v):
    f = v["verdicts"]["model_T_double_contraction"]["audit_finding"]
    assert "OMITS" in f and "T_0 != T_1" in f
    assert any("T_0 != T_1" in s for s in v["contraction_lemma"]["side_conditions"])


def test_lemma_is_about_shape_not_lock(v):
    assert "SHAPE, not about" in v["contraction_lemma"]["note"]


# --------------------------------------------------------------------- S19/S23 scope
def test_scope_is_only_nr6_conditional_cell_closure(v):
    s = v["scope"]
    assert s["establishes"].startswith("NR6-conditional closure")
    assert "L6 >= 872" in s["does_not_establish"]
    assert "NR6" in s["does_not_establish"]
    assert s["NR6"] == "ASSUMED"


def test_ledger_moves_to_ten_of_fifty_five_only(v):
    L = v["ledger"]
    assert L["OUTER_CELLS_CLOSED"] == "10/55 (k,G)"
    assert L["previous"] == "9/55"
    assert L["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert L["CLAUDE_FULL_JOINT_Q2"] == "6396/6396"
    assert L["NR6"] == "ASSUMED"
    assert v["disclaimer"] == "This project has not proved L6 >= 872"
