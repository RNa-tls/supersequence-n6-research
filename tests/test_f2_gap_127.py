"""라운드 127 — `F = 2` 유형 B 자유 탈출 구멍 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_f2_gap_127.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/verify_f2_gap_127.py summarise first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mod():
    return pytest.importorskip("verify_f2_gap_127")


# ------------------------------------------------------------------- S9 order types
def test_all_order_types_eliminated(mod):
    d = mod.order_type_elimination()
    assert d["combinations_checked"] == 96
    assert d["orders_surviving"] == 0
    assert d["all_eliminated"] is True
    for lab in d["detail"].values():
        assert lab["orders_surviving"] == 0


# --------------------------------------------------------- S10/S11 dependency digraph
def test_one_split_token_is_unsatisfiable(mod):
    d = mod.minimum_split_tokens()
    assert d["with_one_token"]["satisfiable"] is False
    assert d["with_one_token"]["feasible_orders"] == 0


def test_two_split_tokens_are_satisfiable_so_the_bound_is_tight(mod):
    d = mod.minimum_split_tokens()
    assert d["with_two_tokens"]["satisfiable"] is True
    assert d["with_two_tokens"]["feasible_orders"] == 24
    assert d["minimum_required"] == 2
    assert d["bound_is_tight"] is True


# ------------------------------------------------------- S7/S8 geometry is not the block
@pytest.mark.parametrize("n", [4, 5, 6])
def test_two_hexagons_can_share_an_orbit(mod, n):
    d = mod.shared_orbit_geometry(n)
    assert d["geometry_forbids_sharing"] is False
    assert d["hexagon_pairs_sharing_an_orbit"] > 0
    assert d["orbit_meets_hexagons"] == [n - 1]
    assert d["words_per_orbit_per_hexagon"] == [1]


def test_n6_sharing_counts(res):
    g = res["shared_orbit_geometry"]["6"]
    assert g["n_hexagons"] == 120 and g["n_orbits"] == 144
    assert g["distinct_hexagon_pairs"] == 7140
    assert g["hexagon_pairs_sharing_an_orbit"] == 1080


# ---------------------------------------------------------------- S12 local enumeration
@pytest.mark.parametrize("n", [4, 5, 6])
def test_local_enumeration_has_no_survivors(mod, n):
    d = mod.local_enumerator(n)
    assert d["survivors"] == 0
    assert d["exceptional_configuration_exists"] is False


def test_geometry_alone_would_allow_configurations(res):
    """기하만으로는 살아남는 것이 있다 — 죽이는 것은 순서다."""
    d = res["local_enumeration"]["6"]
    assert d["geometry_alone_allows"] == 400
    assert d["killed_by_order"] == 400
    assert d["survivors"] == 0
    assert d["same_run_branch_always_vacuous"] is True


def test_local_state_space_is_fully_reduced(res):
    d = res["local_enumeration"]["6"]
    assert d["fixed_entry_word"] == 0          # S6 reduction
    assert d["stages"]["1_with_case_labelling"] == 71400


# --------------------------------------------------------------------- S13/S14 controls
def test_n4_control_is_clean(res):
    c = res["n4_control"]
    assert c["legal_only"] is True             # S14: legality stays on
    assert c["walks"] > 20000
    assert c["violations"] == {}
    assert c["clean"] is True


def test_n4_never_shows_the_exceptional_configuration(res):
    c = res["n4_control"]
    assert c["exceptional_instances"] == 0
    assert "1" not in c["typeB_fout4_by_e"]
    assert min(int(k) for k in c["typeB_fout4_by_e"]) == 2


def test_n4_typeB_fout4_count_is_56(res):
    """라운드 126 문서의 79 는 전사 오류였다 — 아티팩트의 56 이 옳다."""
    c = res["n4_control"]
    assert c["typeB_fout4_total"] == 56
    assert c["typeB_fout4_by_e"] == {"2": 34, "3": 20, "4": 2}


def test_the_intermediate_proof_step_is_verified_on_real_walks(res):
    """§4.1 'e=1 이면 완전 자유 육각형마다 경우 (ii) 가 정확히 하나' 가 실측된다."""
    c = res["n4_control"]
    assert c["all_free_repeated_hexagons"] > 10000
    assert "e = 1 => exactly one case (ii) per all-free hexagon" not in c["violations"]
    assert "Lemma E': at least one case (ii)" not in c["violations"]


def test_n5_walk_control_was_stopped_over_budget(res):
    n5 = res["n5_control"]
    assert n5["status"] == "NOT_RUN_OVER_BUDGET"
    assert "local" in n5["reason"]
    assert "local_enumerator(5)" in n5["substituted_by"]


# --------------------------------------------------------------------- S15 consequences
def test_consequences(res):
    c = res["consequences"]
    assert c["k_feasible"] == [1, 2, 3, 4]
    assert c["n_cells"] == 4
    assert c["max_H"] == 3
    assert c["max_k_plus_x_plus_H"] == 4
    assert c["matches_the_55_cell_table"] is True


def test_theorem_A_status_is_honest(res):
    t = res["theorem_A_status"]
    assert t["F=1"].startswith("PROVED")
    assert t["F=2 type A"].startswith("PROVED")
    assert t["F=2 type B"].startswith("PROVED")
    assert t["F=2 overall"] == "PROVED"
    assert t["F>=3"].startswith("NOT PROVED")


# ------------------------------------------------------------------- S16 no counterexample
def test_no_counterexample_anywhere(res):
    assert all(v["survivors"] == 0 for v in res["local_enumeration"].values())
    assert res["n4_control"]["exceptional_instances"] == 0


# ------------------------------------------------------------------- S19 claim hygiene
def test_no_cells_closed(res):
    assert res["no_cells_closed"] is True
    assert res["cell_status"]["claude_closed_outer_cells"] == "9/55 (unchanged)"
    assert res["cell_status"]["F2_column"].startswith("OPEN")


def test_round_126_correction_recorded(res):
    c = res["round_126_correction"]
    assert "79" in c and "56" in c and "transcription error" in c


def test_round_126_document_was_corrected_not_deleted():
    doc = (ROOT / "research" / "RR_F2_STRUCTURE_126_CLAUDE.md").read_text(encoding="utf-8")
    assert "라운드 127 정정" in doc
    assert "79" in doc          # the retracted number is preserved, not silently removed
    assert "56개" in doc


def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."
    assert "PROVISIONAL" in res["label"] and "NOT INDEPENDENTLY AUDITED" in res["label"]


def test_document_hygiene():
    doc = (ROOT / "research" / "RR_F2_GAP_127_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "독립 감사" in doc
    assert "정리 127.1" in doc and "정정 상자" in doc
