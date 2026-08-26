"""라운드 122 — 일반 `(1,1)` / Q2 다리 테스트."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BR = ROOT / "outputs" / "rr_f1_k1_bridge_122.json"


@pytest.fixture(scope="module")
def br():
    if not BR.exists():
        pytest.skip("run src/verify_f1_k1_bridge_122.py first")
    return json.loads(BR.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ budget (S1)
def test_cell_constants(br):
    b = br["budget"]
    assert (b["O"], b["P"], b["D"]) == (25, 121, 4)
    assert b["SH_cap"] == 26


def test_S_and_N_formulas_hold_on_every_row(br):
    for r in br["budget"]["rows"]:
        assert r["S"] == 24 + r["e"] + r["x"] - r["f_out"]
        assert r["N"] == r["e"] + r["x"] - r["f_out"]
        assert r["N"] + r["H"] <= 2          # L <= 871
        assert r["f_out"] <= 1 + r["e"]      # Lemma E


def test_x_plus_H_at_most_3(br):
    assert br["summary"]["max_x_plus_H"] == 3


def test_H_can_reach_3_at_k1(br):
    """`(2,1)` 은 H<=2 였다.  `k=1` 에서는 3 까지 가고 무게-6 tail 이 들어온다."""
    assert br["summary"]["max_H"] == 3
    assert [6] in br["summary"]["heavy_multisets"]


def test_row_counts(br):
    s = br["summary"]
    assert s["n_distinct_rows"] == 50
    assert s["n_subcases"] == 61
    assert s["n_dead"] == 9
    assert s["n_live_rows"] == 44


def test_off_by_one_direction_is_favourable(br):
    o = br["summary"]["off_by_one"]
    assert "L <= 871" in o["generic_requirement"]
    assert "L <= 872" in o["historical_final_target"]
    assert "superset" in o["relation"]


# ----------------------------------------------------------------- archive (S3)
def test_archive_has_6396_states(br):
    a = br["archive"]
    assert a["n_states"] == 6396
    assert a["header_states"] == 6396


def test_every_archive_state_has_F1_H0_Ndef0(br):
    inv = br["archive"]["invariants"]
    assert inv["all_F_equal_1"] is True
    assert inv["all_H_zero"] is True
    assert inv["all_Ndef_zero"] is True


def test_every_archive_state_is_an_early_prefix(br):
    """결정적: 아카이브는 walk 시작에서 13~14 pass 떨어진 접두다."""
    assert br["archive"]["invariants"]["all_P_in_13_14"] is True
    assert set(br["archive"]["P"]) == {"13", "14"}


def test_archive_counter_identities(br):
    inv = br["archive"]["invariants"]
    assert inv["all_D_equals_5O_minus_P"] is True
    assert inv["all_K_equals_25_minus_O"] is True
    assert inv["b_plus_c_always_5"] is True
    assert br["archive"]["S_equals_O_minus_1"] == {"0": 6396}


def test_every_archive_state_comes_from_a_short_root(br):
    a = br["archive"]
    assert a["invariants"]["all_roots_are_short"] is True
    assert set(a["roots"]) == {f"short_ell{i}" for i in range(5)}
    assert sum(a["roots"].values()) == 6396


# ------------------------------------------------------------ RR alphabet (S2)
def test_rr_alphabet_has_exactly_four_kinds(br):
    al = br["rr_alphabet"]
    assert al["n_inside"] == 4
    assert set(al["inside"]) == {"Z2", "Z2abandon", "R", "Z3"}


def test_every_heavy_joint_is_outside_the_rr_alphabet(br):
    """무게 >= 4 이음매는 Q2 탐색이 단 하나도 보지 않는다."""
    assert br["rr_alphabet"]["every_heavy_joint_is_outside"] is True


def test_A2_A3_and_J_are_outside_too(br):
    names = {r["name"] for r in br["rr_alphabet"]["rows"] if not r["inside_RR_alphabet"]}
    assert any(n.startswith("A2") for n in names)
    assert any(n.startswith("A3") for n in names)
    assert any(n.startswith("J") for n in names)


def test_many_live_rows_carry_a_heavy_joint(br):
    assert br["summary"]["rows_with_H_ge_1"] == 22


# ------------------------------------------------------- n = 4 control (S10)
def test_F1_does_not_force_the_first_pass_to_be_short(br):
    """구체적 반례 가족 — 이것이 다리가 서지 않는 이유다."""
    c = br["n4_first_pass_control"]
    assert c["F1_walks"] == 5764
    assert c["first_pass_full"] == 4139
    assert c["first_pass_full"] > c["first_pass_short"]


def test_reversal_cannot_rescue_walks_with_both_ends_full(br):
    c = br["n4_first_pass_control"]
    assert c["both_ends_full"] == 2667
    assert c["both_ends_full"] > 0


# --------------------------------------------------------------- accounting
def test_no_cell_is_claimed_closed_by_this_round(br):
    assert br["round"] == 122
    assert br["cell"] == [1, 1]
    assert "NOT INDEPENDENTLY AUDITED" in br["label"]


def test_disclaimer(br):
    assert br["disclaimer"] == "This project has not proved L6 >= 872."
