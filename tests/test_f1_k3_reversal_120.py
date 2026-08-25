"""라운드 120 — 뒤집기 대칭과 `(3,1)` 마지막 두 분기에 대한 테스트."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
REV = OUT / "rr_f1_reversal_120.json"
BII = OUT / "rr_f1_k3_bii_120.json"


@pytest.fixture(scope="module")
def rev():
    if not REV.exists():
        pytest.skip("run src/verify_f1_reversal_120.py first")
    return json.loads(REV.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bii():
    if not BII.exists():
        pytest.skip("run src/f1_k3_bii_120.py first")
    return json.loads(BII.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- reversal theorem
def test_all_reversal_checks_pass(rev):
    assert rev["all_checks_pass"] is True


def test_rho_conjugates_sigma(rev):
    assert rev["n6"]["A1_rho_sigma"] is True


def test_joint_weight_is_preserved_by_reversal(rev):
    assert rev["n6"]["A2_weight_preserved_pairs"] == 720 * 719
    assert rev["n6"]["A2_violations"] == 0


def test_R_is_an_involution_on_words_and_on_orbits(rev):
    assert rev["n6"]["A3_R_involution"] is True
    assert rev["n6"]["A3_orbit_map_is_involution"] is True


def test_reversal_preserves_the_orbit_partition(rev):
    """이 라운드의 핵심 — 라운드 119 §8 의 반대."""
    assert rev["n6"]["A3_orbits_scattered"] == 0
    assert rev["n6"]["A3_orbit_map_is_bijection"] is True


def test_reversal_preserves_hexagons(rev):
    assert rev["n6"]["A4_hexagons_scattered"] == 0
    assert rev["n6"]["A4_hexagon_map_is_bijection"] is True


def test_passes_map_to_passes(rev):
    assert rev["n6"]["A5_pass_image_checks"] == 720 * 6
    assert rev["n6"]["A5_violations"] == 0


def test_rule_R1_full_to_full_intra_orbit_preserved(rev):
    assert rev["n6"]["R1_full_full_checks"] == 720 * 17
    assert rev["n6"]["R1_violations"] == 0


def test_rule_R2_full_to_short_image_always_leaves_the_orbit(rev):
    assert rev["n6"]["R2_full_to_short_checks"] == 720 * 17 * 5
    assert rev["n6"]["R2_violations_image_stayed_in_orbit"] == 0


def test_rule_R3_short_to_full_weight2_image_is_tau(rev):
    assert rev["n6"]["R3_short_to_full_W2_checks"] == 720 * 5
    assert rev["n6"]["R3_violations_image_left_orbit"] == 0


def test_base_fact_every_move_leaves_the_orbit_below_ell_5(rev):
    assert rev["n6_base_fact"]["holds"] is True
    assert rev["n6_base_fact"]["intra_orbit_below_ell5"] == 0


def test_R2_is_n6_specific_and_the_n4_control_shows_why(rev):
    """n=4 에서는 밑바탕 census 가 거짓이고, 그래서 R2 도 깨진다.
    이것이 R2 가 우연이 아니라 census 를 따라간다는 대조다."""
    assert rev["n4_base_fact"]["holds"] is False
    assert rev["n4_control"]["R2_violations"] > 0


# ---------------------------------------------------------------- n = 4 end to end
def test_n4_reversal_is_a_valid_involution_preserving_everything(rev):
    c = rev["n4_control"]
    assert c["walks"] > 10000
    assert c["bad_valid"] == 0
    assert c["bad_invariants"] == 0
    assert c["bad_L"] == 0
    assert c["bad_involution"] == 0
    assert c["R1_violations"] == 0
    assert c["R3_violations"] == 0


# ---------------------------------------------------------------- weight-4 correction
def test_round_118_weight4_census_is_corrected(rev):
    w = rev["weight4_classes"]
    assert w["round_118_claim_status"].startswith("FALSE")
    assert w["per_tail"]["W4_0"]["intra_orbit_at_ell5"] == 720
    for name, row in w["per_tail"].items():
        if name == "W4_0":
            continue
        assert row["intra_orbit_at_ell5"] == 0


def test_all_weight4_tails_leave_the_orbit_below_ell5_and_never_return_to_the_hexagon(rev):
    w = rev["weight4_classes"]
    assert w["all_change_orbit_below_ell5"] is True
    assert w["none_returns_to_source_hexagon"] is True


def test_weight4_collapses_to_two_structural_classes(rev):
    assert rev["weight4_classes"]["n_classes"] == 2


# ---------------------------------------------------------------- engine regression
def test_engine_reproduces_round_119_node_count_exactly():
    """새 프룬을 끄면 (exccap=-1) 라운드 119 의 C2 b=1 노드 수와 정확히 같아야 한다."""
    binp = ROOT / "src" / "f1_cell_120.bin"
    if not binp.exists():
        pytest.skip("build src/f1_cell_120.c first")
    r = subprocess.run([str(binp), "1", "26", "27", "0", "2", "1", "2", "5", "28", "1",
                        "14", "0", "0", "2", "0", "-1", "0", "0", "0", "60000000000"],
                       capture_output=True, text=True, check=True, timeout=1200)
    d = json.loads(r.stdout.splitlines()[0])
    assert d["verdict"] == "UNSAT_COMPLETE"
    assert d["nodes"] == 1_053_024_770


# ---------------------------------------------------------------- B_ii / C1 accounting
def test_c1_is_closed_without_search(bii):
    assert bii["c1_closed_by_reversal"] is True
    c1 = [c for c in bii["case_map"] if c["branch"] == "C1"]
    assert len(c1) == 3
    assert all(c["needs_search"] is False for c in c1)


def test_only_one_b_ii_subcase_needs_search(bii):
    need = [c for c in bii["case_map"] if c["needs_search"]]
    assert len(need) == 1
    assert need[0]["branch"] == "B_ii"


def test_b_ii_runs_are_all_complete_and_unsat(bii):
    assert bii["runs"] == 5
    assert bii["verdicts"] == {"UNSAT_COMPLETE": 5}
    assert {r["b"] for r in bii["rows"]} == {1, 2, 3, 4, 5}


def test_b_ii_run_parameters_encode_the_canonical_form(bii):
    for r in bii["rows"]:
        assert r["seam"] == 1
        assert r["symcut"] == 1
        assert r["pmax"] == 59
        assert r["ecap"] == 2 and r["xcap"] == 0 and r["foutmin"] == 2 and r["hcap"] == 0
        assert r["rmax"] == 29


def test_round_119_baseline_was_capped_and_is_now_complete(bii):
    assert bii["round_119_baseline"]["verdict"] == "UNKNOWN_CAP"
    b1 = [r for r in bii["rows"] if r["b"] == 1][0]
    assert b1["verdict"] == "UNSAT_COMPLETE"


def test_no_sat_witness_anywhere(bii):
    assert all("witness" not in r for r in bii["rows"])


def test_cell_31_closed(bii):
    assert bii["b_ii_closed"] is True
    assert bii["cell_closed"] is True


def test_ledgers_unchanged(bii):
    assert bii["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert bii["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert bii["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(rev, bii):
    assert rev["disclaimer"] == "This project has not proved L6 >= 872."
    assert bii["disclaimer"] == "This project has not proved L6 >= 872."


# ------------------------------------------------- seam hexagon collision (section 16.1)
def test_seam_collision_forbids_t_prime_ge_2_at_b5(rev):
    c = rev["seam_hexagon_collisions"]
    assert c["per_b"]["5"]["pre_X_vs_R_Y_start"] == 720
    assert c["t_prime_ge_2_impossible_at"] == [5]


def test_seam_collision_forbids_t_ge_2_at_b1(rev):
    c = rev["seam_hexagon_collisions"]
    assert c["per_b"]["1"]["pre_Y_vs_R_X_start"] == 720
    assert c["t_ge_2_impossible_at"] == [1]


def test_splits_2_3_4_have_no_forced_seam_collision(rev):
    assert rev["seam_hexagon_collisions"]["free_splits"] == [2, 3, 4]


def test_orbit_words_lie_in_five_distinct_hexagons(rev):
    assert rev["seam_hexagon_collisions"]["orbit_words_in_distinct_hexagons"] is True


def test_b5_run_is_shallow_for_the_reason_the_lemma_gives(bii, rev):
    """b=5 는 pass 59(= pmax)에서 멎는다 — 보조정리가 t' >= 2 를 금지하기 때문이지 버그가 아니다."""
    b5 = [r for r in bii["rows"] if r["b"] == 5][0]
    assert b5["verdict"] == "UNSAT_COMPLETE"
    assert b5["best_passes"] <= b5["pmax"]
    assert 5 in rev["seam_hexagon_collisions"]["t_prime_ge_2_impossible_at"]
