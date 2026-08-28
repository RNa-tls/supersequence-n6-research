"""라운드 128 — `F` / `G` 분리와 기초 수리 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_fg_repair_128.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/verify_fg_repair_128.py summarise first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mod():
    return pytest.importorskip("verify_fg_repair_128")


# --------------------------------------------------------------- S15 counterexample
def test_codex_counterexample_is_real(mod):
    d = mod.dissect(mod.CODEX_N4)
    assert d["all_24_exactly_once"] is True
    assert d["all_joints_legal"] is True
    assert d["P"] == 9 and d["G"] == 3 and d["F_by_ascents"] == 2 and d["J"] == 1
    assert d["multiplicity_partition"] == [2, 1]


def test_the_two_F_definitions_agree(mod):
    """상승 세기 = 레거시 엔진의 abandonment 정의를 한 걸음씩 재생한 값."""
    d = mod.dissect(mod.CODEX_N4)
    assert d["F_definitions_agree"] is True
    assert d["F_by_engine_definition"] == 2


def test_old_identities_fail_on_the_counterexample(mod):
    d = mod.dissect(mod.CODEX_N4)
    assert d["L_matches_G_identity"] is True
    assert d["L_matches_F_identity"] is False
    assert d["D_equals_5k_minus_G"] is True
    assert d["D_equals_5k_minus_F"] is False
    assert d["master_with_G_matches"] is True


def test_J_equals_descent_excess(mod):
    d = mod.dissect(mod.CODEX_N4)
    assert d["J_equals_sum_descents_minus_hexagons"] is True
    assert d["sum_descents"] == 7 and d["n_hexagons"] == 6
    assert d["descents_by_hexagon"]["0"] == 2      # the tripled hexagon


# ------------------------------------------------------------------- S2 F/G theory
def test_fg_theory_statements(mod):
    t = mod.fg_theory()
    assert t["G_le_1_implies_F_eq_G"] is True
    assert t["G2_typeB_implies_F_eq_G"] is True
    assert t["G2_typeA_allows_F_eq_1"] is True
    assert t["F0_iff_G0"] is True
    assert "e_h >= 3" in t["J_positive_requires"] or "THREE" in t["J_positive_requires"]


# ------------------------------------------------------------------ S16 (F,G) census
def test_census_matches_codex_numbers(res):
    c = res["n4_census"]
    assert c["walks"] == 29255
    assert c["G_gt_F"] == 2088
    assert c["by_F"]["2"] == 10916
    assert c["by_G"]["2"] == 10625
    assert c["partitions_for_F2"] == {"(1, 1)": 9441, "(2,)": 1138, "(2, 1)": 337}


def test_census_confirms_the_theory(res):
    c = res["n4_census"]
    assert c["fg_theory_holds"] is True
    assert c["corrected_identities_hold"] is True
    assert c["old_identities_fail"] is True
    for bad in ("F <= G", "F = 0 <=> G = 0", "G <= 1 => F = G",
                "every e_h <= 2 => F = G", "J > 0 requires some e_h >= 3",
                "F >= m (m = #multiply-entered hexagons)", "J <= G - m"):
        assert bad not in c["violations"], bad


def test_G1_column_is_entirely_F1(res):
    c = res["n4_census"]
    assert c["FG_matrix"]["F1_G1"] == c["by_G"]["1"]
    assert c["partitions_for_G1"] == {"(1,)": 5999}


def test_F1_with_G2_exists_and_is_always_a_tripled_hexagon(res):
    c = res["n4_census"]
    assert c["FG_matrix"]["F1_G2"] == 46
    assert c["partitions_for_F1"] == {"(1,)": 5999, "(2,)": 46}


# --------------------------------------------------------------- S3/S5 identities/table
def test_corrected_identities_named(mod):
    ci = mod.corrected_identities(6)
    assert ci["P"]["corrected"] == "P = n!/n + G"
    assert ci["L"]["corrected"] == "L = 844 + G + S + H"
    assert ci["D"]["corrected"] == "D = (n-1)k - G"
    assert ci["N"]["corrected"] == "N = S + G - O"
    assert "G" in ci["master"]["corrected"] and "F" not in ci["master"]["corrected"].split("+ G")[0]
    assert ci["cells"]["corrected"].startswith("55 cells indexed by (k, G)")


def test_slab_table_recount_is_55_as_kG(mod):
    t = mod.slab_table(6)
    assert t["total_cells"] == 55
    assert t["matches_historical_55"] is True
    assert t["index"].startswith("(k, G)")
    assert t["theorem_A_proved_for"] == "G in {0, 1, 2}"


# ------------------------------------------------------------------ S6/S7/S8/S9 audits
def test_F0_column_survives(res):
    a = res["f0_audit"]
    assert a["answer"].startswith("YES")
    assert "SURVIVES" in a["classification"]


def test_F1_audit_is_honest(res):
    a = res["f1_audit"]
    assert a["answer"].startswith("YES")
    assert "G = 2 column" in a["but"]
    assert "exhaustive" in a["conclusion"]


def test_rounds_scope_table_has_no_generic_F_round(res):
    tab = res["rounds_scope_table"]
    codes = [v[0] for k, v in tab.items() if not k.startswith("_")]
    assert "A" not in codes, "no round ever covered generic project F"
    assert tab["115"][0] == "C" and tab["125"][0] == "B" and tab["126"][0] == "C"


def test_engine_audit_facts(res):
    e = res["engine_audit"]
    assert "abandon" in e["fact"] and "no engine" in e["fact"]
    assert "121" in e["target"]
    assert e["round_125_true_name"].startswith("(k, G) = (1, 1) closed")


def test_engines_really_have_no_abandonment_and_target_121():
    """산문이 아니라 코드를 직접 확인한다 (§9)."""
    for f in ("f1_cell_118.c", "f1_cell_119.c", "f1_cell_120.c", "f1_cell_121.c",
              "f1_cell_125.c", "f1_k1_roots_123.c", "f1_k1_sig_124.c"):
        src = (ROOT / "src" / f).read_text(encoding="utf-8", errors="replace")
        assert "#define TARGET 121" in src, f
        assert "abandon" not in src, f


def test_round_115_targets_P_120():
    src = (ROOT / "src" / "verify_f0_geometry_115.py").read_text(encoding="utf-8")
    assert "P = 120" in src


# ----------------------------------------------------------------- S17 Round 127 salvage
def test_round_127_salvaged_without_F_or_G(res):
    s = res["round_127_salvage"]
    assert s["uses_F"] is False and s["uses_G"] is False
    assert s["corrected_scope"].startswith("G = 2")
    assert len(s["withdrawn_corollaries"]) == 4


# ------------------------------------------------------------------------ S18 ledger
def test_ledger_status_repaired(res):
    l = res["ledger_status"]
    assert "G, not F" in l["outer_cell_ledger"]
    assert l["closed_cells"].startswith("9 of 55 (k, G) cells")
    assert l["audited_4782"].startswith("unchanged")
    assert "G = 1" in l["q2_6396"]


def test_ledger_numbers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."


# ------------------------------------------------------------------- documents
def test_repair_document_hygiene():
    doc = (ROOT / "research" / "RR_FG_REPAIR_128_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "정리 128.1" in doc and "따름정리 128.2" in doc
    assert "(k, G)" in doc


def test_historical_documents_were_corrected_not_deleted():
    """§21 — 역사 문서를 조용히 다시 쓰지 않는다."""
    for f, marker in (("RR_F2_STRUCTURE_126_CLAUDE.md", "라운드 128 정정"),
                      ("RR_F2_GAP_127_CLAUDE.md", "라운드 128 정정"),
                      ("RR_F1_K1_END2END_125_CLAUDE.md", "라운드 128 정정")):
        doc = (ROOT / "research" / f).read_text(encoding="utf-8")
        assert marker in doc, f
