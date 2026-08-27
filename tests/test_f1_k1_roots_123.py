"""라운드 123 — 일반 `(1,1)` 뿌리 열거 테스트."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_f1_k1_roots_123.json"


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/f1_k1_roots_123.py first")
    return json.loads(RES.read_text(encoding="utf-8"))


# ------------------------------------------------------------ completeness (S9)
def test_all_thirteen_maximal_cells_completed(res):
    assert res["configs_capped"] == []
    for e, x, h in res["cells"]:
        assert f"e{e}_x{x}_H{h}" in res["configs_complete"]


def test_cells_are_the_maximal_exception_budgets(res):
    """e + x + H = 4, e<=4, x<=3, H<=3 인 극대 셀이 정확히 13개다."""
    cells = {tuple(c) for c in res["cells"]}
    expect = {(e, x, h) for e in range(5) for x in range(4) for h in range(4)
              if e + x + h == 4}
    assert cells == expect
    assert len(cells) == 13


def test_every_feasible_budget_is_dominated_by_a_cell(res):
    """합집합 완전성의 핵심: e+x+H<=4 인 모든 예산이 어떤 극대 셀에 componentwise 지배된다."""
    cells = [tuple(c) for c in res["cells"]]
    for e in range(5):
        for x in range(4):
            for h in range(4):
                if e + x + h > 4:
                    continue
                assert any(e <= ce and x <= cx and h <= ch for ce, cx, ch in cells)


def test_root_family_is_complete(res):
    assert res["root_family_complete"] is True


# ------------------------------------------------------------ prefix bound (S14)
def test_rigid_prefix_bound_is_46(res):
    pb = res["prefix_bound"]
    assert pb["rigid_max_q"] == 46


def test_rigid_bound_matches_R115_chain_capacity(res):
    """해석(NTAB[4]=46)과 전수 열거가 독립적으로 일치한다."""
    pb = res["prefix_bound"]
    assert pb["NTAB_4"] == 46
    assert pb["matches_R115_chain_capacity"] is True


def test_rigid_prefix_family_is_tiny(res):
    r = res["by_config"]["rigid_e0_x0_H0"]
    assert r["verdict"] == "COMPLETE"
    assert r["nodes"] == 3425
    assert r["roots"] == 17545


def test_prefix_length_is_bounded_below_the_trivial_119(res):
    assert res["max_q_over_cells"] <= 119
    assert res["max_q_over_cells"] == 114


# ------------------------------------------------------------ heavy tails (S11)
def test_all_three_heavy_weights_are_included(res):
    h = res["heavy_tails_included"]
    assert h == {"weight4": 13, "weight5": 71, "weight6": 461, "total": 545}


def test_engine_verifies_the_461_weight6_tails():
    binp = ROOT / "src" / "f1_k1_roots_123.bin"
    if not binp.exists():
        pytest.skip("build src/f1_k1_roots_123.c first")
    r = subprocess.run([str(binp), "1", "0", "26", "25", "0", "0", "0", "4", "5", "1", "100"],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0
    assert "weight-6 tail count" not in r.stderr
    assert "weight-5 tail count" not in r.stderr


def test_roots_by_H_reaches_3(res):
    """H=3 (무게-6 하나) 뿌리가 실제로 나온다 — 와일드카드로 뭉치지 않았다."""
    r = res["by_config"]["e0_x1_H3"]
    assert r["roots_by_H"][3] > 0


# --------------------------------------------------------- q>0 acceptance (S15)
def test_q_positive_roots_exist(res):
    """라운드 122 의 '양 끝 full' 현상을 새 뿌리 구성이 받아들인다 - 거짓 기각 0."""
    for lbl, r in res["by_config"].items():
        assert r["max_prefix_q"] >= 46      # every cell realises long full prefixes


def test_q_zero_short_first_is_still_included(res):
    """역사적 short_ell0..4 에 해당하는 q=0 다섯 뿌리를 잃지 않았다."""
    for lbl, r in res["by_config"].items():
        assert r["roots_q0"] == 5


def test_b_split_is_a_free_factor_of_five(res):
    for lbl, r in res["by_config"].items():
        assert len(set(r["roots_by_b"])) == 1        # all five splits equally many
        assert sum(r["roots_by_b"]) == r["roots"]


# ------------------------------------------------------------------- settings
def test_engine_settings_are_the_k1_ones(res):
    for lbl, r in res["by_config"].items():
        assert r["orbcap"] == 25
        assert r["dcap"] == 4
        assert r["exccap"] == 5
        assert r["costcap"] == 26
        assert r["fod"] == 1


def test_no_cell_closes_and_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."
