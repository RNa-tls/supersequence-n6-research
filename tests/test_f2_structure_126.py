"""라운드 126 — 일반 `F = 2` 구조 분류 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_f2_structure_126.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/verify_f2_structure_126.py first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mod():
    return pytest.importorskip("verify_f2_structure_126")


# ------------------------------------------------------------------ S1 identities
def test_identities_at_F2(mod):
    d = mod.identities(6, 2)
    assert d["P"] == 122
    assert d["total_deficit"] == 12
    assert d["L_at_F"] == "846 + S + H"
    assert d["master"] == "L = 867 + k + F + e + x + H - f_out"
    assert d["master_at_F"] == "L = 869 + k + e + x + H - f_out"
    assert d["k_min"] == 1


def test_master_identity_matches_the_872_witness(mod):
    """실제 초순열에서 master 항등식이 성립한다 (k=5, F=25, S=3, H=0)."""
    k, F, S, H, O = 5, 25, 3, 0, 29
    N = S + F - O
    assert 868 + k + N + H == 872
    # S = (r-1) + x - f_out with r = O + e  =>  e + x - f_out = S - (O - 1) = -25
    assert 867 + k + F + (S - (O - 1)) + H == 872


def test_master_identity_matches_the_greedy_873(mod):
    k, F, S, H, O = 0, 0, 23, 6, 24
    assert 867 + k + F + (S - (O - 1)) + H == 873


def test_k_at_least_one_is_derived_not_assumed(mod):
    """F <= (n-1)k 에서 나온다 — F=1 의 패턴을 가정한 것이 아니다."""
    assert mod.identities(6, 2)["k_min"] == 1
    assert mod.identities(6, 6)["k_min"] == 2
    assert mod.identities(6, 0)["k_min"] == 0


# ------------------------------------------------------------- S2 multiplicity types
def test_exactly_two_multiplicity_types(mod):
    t = mod.multiplicity_types(2)
    assert len(t) == 2
    assert [x["entry_counts"] for x in t] == [[3], [2, 2]]
    assert [x["m"] for x in t] == [1, 2]
    assert [x["n_short_passes"] for x in t] == [3, 4]


def test_taxonomy_is_a_partition_of_F(mod):
    for F in range(0, 7):
        types = mod.multiplicity_types(F)
        for t in types:
            assert sum(e - 1 for e in t["entry_counts"]) == F
        assert len(types) == len(list(mod.partitions(F)))


# --------------------------------------------------------------- S3/S4 short passes
def test_all_passes_of_a_multiply_entered_hexagon_are_short(mod):
    for row in mod.short_pass_structure(6, 2):
        for h in row["per_hexagon"]:
            assert h["all_passes_short"] is True


def test_short_pass_count_is_F_plus_m(mod):
    rows = mod.short_pass_structure(6, 2)
    assert [r["n_short_passes"] for r in rows] == [3, 4]
    for r in rows:
        assert r["n_short_passes"] == 2 + r["m"]


def test_deficit_and_split_shapes(mod):
    rows = mod.short_pass_structure(6, 2)
    assert all(r["total_deficit"] == 12 and r["deficit_check"] for r in rows)
    assert [r["n_split_shapes"] for r in rows] == [10, 25]


def test_length_partitions(mod):
    a, b = mod.short_pass_structure(6, 2)
    assert a["per_hexagon"][0]["length_partitions"] == [(2, 2, 2), (3, 2, 1), (4, 1, 1)]
    assert b["per_hexagon"][0]["length_partitions"] == [(3, 3), (4, 2), (5, 1)]


# ------------------------------------------------------ S5/S6 free-successor structure
@pytest.mark.parametrize("n", [4, 5, 6])
def test_free_successor_local_lemmas(mod, n):
    d = mod.free_successor_identity(n)
    assert d["unique_legal_weight2_successor_is_T1"] is True
    assert d["identity_T1_sigma_n1_equals_tau"] is True
    assert d["free_successor_formula_holds"] is True
    assert d["short_pass_free_successor_always_changes_orbit"] is True
    assert d["hexagons_whose_words_miss_distinct_orbits"] == 0
    assert d["words_at_omega2"]["always_exactly_two"] is True
    assert d["words_at_omega2"]["other_is_always_sigma_squared"] is True


@pytest.mark.parametrize("n", [4, 5, 6])
def test_same_hexagon_never_consecutive(mod, n):
    d = mod.same_hexagon_never_consecutive(n)
    assert d["omega_equals_rotation_count"] is True
    assert d["every_intermediate_window_is_a_permutation"] is True


# --------------------------------------------------------------- S8/S9 cells and H
def test_feasible_k_cells(res):
    c = res["feasible_cells"]
    assert c["k_feasible_unconditional"] == [1, 2, 3, 4, 5]
    assert c["k_feasible_if_f_out_le_F_plus_e"] == [1, 2, 3, 4]
    assert c["k_feasible_if_theorem_A"] == [1, 2, 3, 4]
    assert c["n_cells_conditional"] == 4


def test_max_H(res):
    c = res["feasible_cells"]
    assert c["max_H_unconditional"] == 4
    assert c["max_H_conditional"] == 3
    assert c["max_H_by_type"]["A"] == 3          # type A never exceeds 3
    assert c["max_H_by_type"]["B"] == 4


def test_the_single_open_configuration(res):
    """모든 차이가 유형 B, f_out=4, e=1 한 설정에서 온다."""
    c = res["feasible_cells"]
    assert all(t == "B" and f == 4 and e == 1 for (t, f, e, x) in c["open_configuration"])
    assert c["theorem_A_open_configuration"] == [["B", 4, 1, 0]]


def test_k_plus_x_plus_H_le_4_needs_the_stronger_bound(res):
    c = res["feasible_cells"]
    assert c["k_plus_x_plus_H_max_conditional"] == 4
    assert c["k_plus_x_plus_H_max_if_theorem_A"] == 5


def test_heavy_catalogue_uses_the_round_125_correction(res):
    cat = res["heavy_tails"]["catalogue"]
    assert cat["w6_genuine"] == 308
    assert cat["w6_raw_indecomposable"] == 461
    assert cat["w4"] == 13 and cat["w5"] == 71


def test_H4_compositions(res):
    comps = res["heavy_tails"]["compositions"]["4"]
    assert sorted(comps) == [[4, 4, 4, 4], [5, 4, 4], [5, 5], [6, 4]]


# ------------------------------------------------------------------ S10 falsification
def test_n4_exhaustive_has_zero_violations(res):
    f = res["n4_falsification"]
    assert f["legal_only"] is True
    assert f["violations"] == {}
    assert f["all_claims_survive"] is True
    assert f["walks"] > 20000
    assert f["F_distribution"]["F=2"] > 5000


def test_f_out_conjecture_survives_and_is_tight(res):
    fa = res["f_out_bounds"]["falsification"]
    assert fa["holds"] is True
    assert fa["open_case_observed"] == 0
    assert fa["typeB_fout4_min_e_observed"] == 2
    mn = fa["min_e_by_F_and_fout"]
    for key, e in mn.items():
        F = int(key.split("_")[0][1:])
        f = int(key.split("_f")[1])
        assert f <= F + e, key
    # tightness where the sample is rich
    assert mn["F1_f2"] == 1 and mn["F2_f3"] == 1 and mn["F2_f4"] == 2


def test_legality_correction_recorded(res):
    lc = res["legality_correction"]
    imp = lc["impact"]
    assert imp["legal"]["walks"] < imp["superset"]["walks"]
    assert imp["legal"]["first_pass_full_pct"] > 50
    assert imp["legal"]["both_ends_full_pct"] > 40
    assert "SUPERSET" in lc["rounds_120_122_n4_controls"]


def test_superset_breaks_exactly_the_two_legality_dependent_claims(mod):
    r = mod.n4_falsify(34, legal_only=False)
    assert set(r["violations"]) <= {"same-hexagon passes never consecutive",
                                    "free successor = tau(entry(nu(p)))"}
    good = mod.n4_falsify(34, legal_only=True)
    assert good["violations"] == {}


# ------------------------------------------------------------------- claim hygiene
def test_no_giant_search(res):
    assert res["no_giant_search"] is True


def test_cell_status_unchanged(res):
    st = res["cell_status"]
    assert st["claude_closed_outer_cells"] == "9/55 (unchanged)"
    assert st["F2_column"].startswith("OPEN")
    assert st["F2_cells_conditional"] == 4


def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."
    assert "PROVISIONAL" in res["label"] and "NOT INDEPENDENTLY AUDITED" in res["label"]


def test_document_hygiene():
    doc = (ROOT / "research" / "RR_F2_STRUCTURE_126_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "독립 감사" in doc
    assert "보조정리 E′" in doc and "308" in doc
