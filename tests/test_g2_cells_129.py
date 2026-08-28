"""라운드 129 — 일반 `G = 2` 칸 분해 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_g2_cells_129.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/verify_g2_cells_129.py summarise first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mod():
    return pytest.importorskip("verify_g2_cells_129")


# ------------------------------------------------------------------- S1 identities
def test_G2_identities(mod):
    d = mod.identities()
    assert d["G"] == 2 and d["P"] == 122
    assert d["L"].startswith("844 + G + S + H")
    assert "846 + S + H" in d["L"]
    assert d["D"].startswith("5O - P = 5k - G = 5k - 2")
    assert d["N"] == "S + G - O = S - 22 - k"
    assert "869 + k + e + x + H - f_out" in d["master"]
    assert d["core"] == "L <= 871  <=>  k + e + x + H - f_out <= 2"
    assert d["no_F_substitution"] is True


def test_outer_axis_is_G_not_F(res):
    assert res["outer_axis"] == "G (never F)"
    assert res["column"] == "G = 2"


# ---------------------------------------------------------------- S2/S5 internal F
def test_typeB_forces_F_equals_2(mod):
    d = mod.internal_F()
    assert d["typeB"]["F"] == [2]
    assert d["typeB"]["J"] == 0 and d["typeB"]["d_forced"] == 1


def test_typeA_allows_F_1_or_2(mod):
    d = mod.internal_F()
    assert d["typeA"]["F"] == [1, 2]
    assert d["typeA"]["n_orderings_with_F1"] == 3
    assert d["typeA"]["n_orderings_with_F2"] == 3
    assert d["typeA"]["F_is_local"] is True


def test_typeA_ordering_table_is_exhaustive(mod):
    d = mod.internal_F()["typeA"]["orderings"]
    assert len(d) == 6
    for r in d:
        assert r["F"] + r["d"] == 3
        assert r["J"] == 2 - r["F"]


def test_three_internal_models(mod):
    assert "A/F=1, A/F=2, B/F=2" in mod.internal_F()["conclusion"]


# --------------------------------------------------------- S3/S4 multiplicity types
def test_multiplicity_types(mod):
    t = mod.multiplicity_types()
    a, b = t[0], t[1]
    assert a["type"] == "A" and a["excess_partition"] == [2] and a["m"] == 1
    assert a["n_short_passes"] == 3 and a["n_ordered_splits"] == 10
    assert b["type"] == "B" and b["excess_partition"] == [1, 1] and b["m"] == 2
    assert b["n_short_passes"] == 4 and b["n_ordered_splits"] == 25
    assert a["total_deficit"] == 12 and b["total_deficit"] == 12


def test_short_pass_count_is_G_plus_m(mod):
    for t in mod.multiplicity_types():
        assert t["n_short_passes"] == 2 + t["m"]


# ------------------------------------------------------------ S6/S12/S13 free exits
def test_free_exit_bounds(mod):
    f = mod.free_exit_bounds()
    assert f["typeA"]["f_out_max"] == 3 and f["typeB"]["f_out_max"] == 4
    assert f["typeA"]["sharper"] == "f_out <= F + e"
    assert f["typeA"]["stronger_generic_bound_exists"] is False
    assert f["typeB"]["table"]["4"].startswith("e >= 2")
    assert f["typeB"]["table"]["3"].startswith("e >= 1")
    assert f["unified"].startswith("for all of G = 2:  f_out <= F + e")


# --------------------------------------------------------------- S7/S8/S9 the cells
def test_theorem_A_and_master_inequality(res):
    t = res["theorem_A"]
    assert t["theorem_A"] == "O <= 1 + S + G   <=>   f_out <= G + e + x"
    assert t["k_plus_x_plus_H_le"] == 4
    assert t["matches_expected_4"] is True
    assert t["refined_by_model"]["A_F1"] == 3


def test_exactly_four_cells(res):
    c = res["cells"]
    assert c["k_feasible"] == [1, 2, 3, 4]
    assert c["k_with_live_subcases"] == [1, 2, 3, 4]
    assert c["n_cells"] == 4


def test_max_H_is_3(res):
    assert res["cells"]["max_H_overall"] == 3
    assert res["cells"]["per_cell"]["1"]["max_H"] == 3
    assert res["cells"]["per_cell"]["4"]["max_H"] == 0


# --------------------------------------------------------------- S10/S17 rows and kills
def test_row_counts(res):
    c = res["cells"]
    assert c["n_subcases_total"] == 300
    assert c["n_dead_total"] == 22
    assert c["n_alive_total"] == 278
    assert c["per_cell"]["4"]["n_alive"] == 5
    assert c["per_cell"]["3"]["n_alive"] == 25
    assert c["per_cell"]["2"]["n_alive"] == 78
    assert c["per_cell"]["1"]["n_alive"] == 170


def test_all_analytic_kills_are_at_k1_with_e0(res):
    for d in res["cells"]["dead_examples"]:
        assert d["k"] == 1 and d["e"] == 0
        assert d["capacity"] < 122


def test_cell_4_2_has_no_typeA_F1(res):
    """정리 129.1 의 구체적 성과."""
    assert "A_F1" not in res["cells"]["per_cell"]["4"]["by_model"]
    assert res["cells"]["per_cell"]["4"]["by_model"]["A_F2"] == 2
    assert res["cells"]["per_cell"]["4"]["by_model"]["B_F2"] == 3


def test_cell_4_2_forces_x_and_H_zero(mod):
    live = [r for r in mod.rows(1, 6, True) if r["k"] == 4 and not r["dead"]]
    assert len(live) == 5
    for r in live:
        assert r["x"] == 0 and r["H"] == 0 and r["S"] == 25
        assert r["f_out"] == r["e"] + 2


# ------------------------------------------------------------------- S11 heavy tails
def test_heavy_catalogue_uses_308(res):
    h = res["heavy_catalogue"]
    assert h["weight6_genuine"] == 308
    assert h["weight6_raw_indecomposable"] == 461
    assert h["weight4"] == 13 and h["weight5"] == 71


def test_weight6_only_in_cell_1_2(res):
    per = res["cells"]["per_cell"]
    assert [6] in per["1"]["heavy_multisets"]
    for k in ("2", "3", "4"):
        assert [6] not in per[k]["heavy_multisets"]


# ------------------------------------------------------------------ S14 n=4 validation
def test_n4_validation_is_clean(res):
    v = res["n4_validation"]
    assert v["clean"] is True
    assert v["violations"] == {}
    assert v["G2_walks"] == 10625
    assert v["typeA_total"] == 1184 and v["typeB_total"] == 9441


def test_n4_typeB_is_always_F2(res):
    v = res["n4_validation"]
    assert v["by_type_and_F"] == {"A_F1": 46, "A_F2": 1138, "B_F2": 9441}


def test_n4_cyclic_rotation_rule_is_exact(res):
    r = res["n4_validation"]["typeA_cyclic_rotation_rule"]
    assert r == {"F1_isRotationFalse": 46, "F2_isRotationTrue": 1138}


def test_n4_free_exit_bounds_are_tight(res):
    v = res["n4_validation"]
    assert v["typeB_min_e_by_fout"] == {"0": 0, "1": 0, "2": 0, "3": 1, "4": 2}
    a = v["typeA_min_e_by_fout_and_F"]
    assert a["f1_F1"] == 1 and a["f2_F1"] == 2      # tight: min e = f_out - F
    assert a["f3_F2"] == 1


# --------------------------------------------------------------------- S15/S16 planning
def test_engine_reuse_audit(res):
    e = res["engine_reuse"]
    assert any("308" in s for s in e["reusable_unchanged"])
    assert any("122" in s for s in e["reusable_after_P_and_D_update"])
    assert any("SHCAP" in s and "25" in s for s in e["reusable_after_P_and_D_update"])
    assert any("sstate" in s for s in e["G1_specific_must_be_rewritten"])


def test_recommended_first_cell(res):
    o = res["cell_ordering"]
    assert o["recommended_first"] == "(k,G) = (4,2)"
    assert o["hardest"] == "(k,G) = (1,2)"
    assert o["ranked"][0]["cell"] == "(k,G) = (4,2)"
    assert o["ranked"][0]["live_subcases"] == 5


# ------------------------------------------------------------------- S18/S19 hygiene
def test_no_giant_sweep_and_no_cell_closed(res):
    assert res["no_giant_sweep"] is True
    assert res["cells_closed_this_round"] == 0
    assert "9/55" in res["ledger_note"] and "(k, G)" in res["ledger_note"]


def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."


def test_document_hygiene():
    doc = (ROOT / "research" / "RR_G2_CELLS_129_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "정리 129.1" in doc and "(k,G)" in doc
    assert "308" in doc
