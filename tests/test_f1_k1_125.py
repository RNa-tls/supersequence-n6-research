"""라운드 125 — 일반 `(1,1)` 끝까지 도는 폐쇄 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_f1_k1_125.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/f1_k1_closure_125.py first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows():
    m = pytest.importorskip("verify_f1_k1_rows_125")
    return m.summarise()


@pytest.fixture(scope="module")
def w6():
    m = pytest.importorskip("verify_f1_k1_w6_125")
    return m.w6_split()


# ------------------------------------------------------------------ S1 resource table
def test_budget_identities(rows):
    assert rows["P"] == 121 and rows["O"] == 25 and rows["D"] == 4


def test_recount_matches_round_122(rows):
    """§1: 처음부터 다시 세도 라운드 122 의 50행/61하위경우/9사망이 나온다."""
    assert rows["n_resource_rows"] == 50
    assert rows["n_subcases"] == 61
    assert rows["n_subcases_dead_by_capacity"] == 9
    assert rows["n_subcases_alive"] == 52
    assert rows["n_rows_with_a_live_subcase"] == 44


def test_bounds_are_derived_not_assumed(rows):
    assert rows["max_H"] == 3 and rows["max_e"] == 4 and rows["max_x"] == 3


def test_H4_is_impossible(rows):
    """H = 4 는 f_out = 2, e = x = 0 을 요구하는데 보조정리 E 가 f_out <= 1 을 강제한다."""
    assert all(r["H"] <= 3 for r in rows["resource_rows"])


# --------------------------------------------------------------------- S2 H structure
def test_H_compositions(rows):
    H = rows["H_classification"]
    assert H["0"]["compositions"] == [[]]
    assert H["1"]["compositions"] == [[4]]
    assert sorted(H["2"]["compositions"]) == [[4, 4], [5]]
    assert sorted(H["3"]["compositions"]) == [[4, 4, 4], [5, 4], [6]]


def test_H3_has_exactly_two_rows(rows):
    assert rows["H_classification"]["3"]["n_rows"] == 2
    got = sorted(list(t) for t in rows["H_classification"]["3"]["rows"])
    assert got == [[0, 0, 1], [1, 0, 2]]


def test_weight6_survives_in_exactly_one_subcase(rows):
    live6 = [a for a in rows["alive_subcases"] if a["heavy_weights"] == [6]]
    dead6 = [d for d in rows["dead_subcases"] if d["heavy_weights"] == [6]]
    assert len(live6) == 1 and len(dead6) == 1
    assert (live6[0]["e"], live6[0]["x"], live6[0]["f_out"]) == (1, 0, 2)


# ------------------------------------------------------------------ S15 negative N
def test_negative_N_characterisation(rows):
    neg = rows["negative_N"]
    assert neg["min_N"] == -1
    for r in neg["rows"]:
        assert r["N"] == -1 and r["x"] == 0
        assert (r["e"], r["f_out"]) in {(0, 1), (1, 2)}


def test_every_H3_row_has_x_zero(rows):
    """H = 3 은 N <= -1 을 요구하고, N < 0 은 x = 0 을 강제한다."""
    for a in rows["alive_subcases"] + rows["dead_subcases"]:
        if a["H"] == 3:
            assert a["x"] == 0


# ------------------------------------------------------------- S11/S12 analytic kills
def test_nine_analytic_closures(rows):
    dead = rows["dead_subcases"]
    assert len(dead) == 9
    for d in dead:
        assert d["e"] == 0 and d["segment_capacity"] < 121
        assert d["x"] + len(d["heavy_weights"]) <= 1


def test_e_at_least_one_never_dies_analytically(rows):
    assert all(d["e"] == 0 for d in rows["dead_subcases"])


# ------------------------------------------------------------ S3/S4 heavy catalogue
def test_tail_catalogue_counts(w6):
    assert w6["n_actions"] == 461
    assert w6["n_genuine_weight6"] == 308
    assert w6["n_lighter_duplicates"] == 89
    assert w6["n_illegal_non_joints"] == 64
    assert w6["n_genuine_weight6"] + w6["n_lighter_duplicates"] + \
        w6["n_illegal_non_joints"] == 461


def test_weight6_degeneracy_structure(w6):
    assert w6["lighter_matches_w5_catalogue"] is True
    assert w6["illegal_matches_factorial_minus_indec"] is True
    assert all(w6["w_lt_6_never_degenerates"].values())


def test_engine_offers_the_genuine_308(w6):
    assert w6["engine_offers"] == 308


def test_c_engine_weight6_table_matches_python(w6):
    """C 엔진이 만드는 308개 action 이 파이썬 유도와 순서까지 같아야 한다."""
    import subprocess
    from verify_f1_k2_budget_121 import tails
    binp = ROOT / "src" / "f1_cell_125.bin"
    srcp = ROOT / "src" / "f1_cell_125.c"
    if not binp.exists() or binp.stat().st_mtime < srcp.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(binp), str(srcp)], check=True)
    out = subprocess.run([str(binp), "-6"], capture_output=True, text=True, check=True)
    got = [list(map(int, l.split())) for l in out.stdout.strip().splitlines()]
    t6 = tails(6)
    want = [list(t6[i]) for i in w6["genuine_indices"]]
    assert got == want


def test_heavy_census_is_all_or_nothing(res):
    for w, d in res["heavy_census"].items():
        assert d["all_or_nothing"] is True
        assert d["never_returns_to_source_hexagon"] is True


def test_weight6_is_never_intra_orbit_after_a_full_pass(res):
    """무게-4/5 와 정반대: 진짜 무게-6 은 ell = 5 에서 궤도 내부가 아니다."""
    six = res["heavy_census"]["6"]["intra_orbit"]
    assert six, "expected some intra-orbit weight-6 tails"
    assert all(r["ell"] != 5 for r in six)
    assert sorted({r["ell"] for r in six}) == [1, 2, 3]
    for w in ("4", "5"):
        assert all(r["ell"] == 5 for r in res["heavy_census"][w]["intra_orbit"])


# ------------------------------------------------------------------ S17 reproduction
def test_reproduction_controls_all_match(res):
    ctl = res["controls"]["reproduction"]
    assert len(ctl) == 5
    for c in ctl:
        assert c.get("matches") is True, c["round"]
        assert c["recorded_nodes"] == c["replayed_nodes"]


# ------------------------------------------------------------------- S16/S20 the run
def test_all_52_alive_subcases_have_a_group(res, rows):
    assert res["n_final_groups"] == 52 == rows["n_subcases_alive"]
    assert res["n_runs_planned"] == 260


def test_every_group_ran_all_five_splits(res):
    for g, d in res["by_group"].items():
        assert d["runs"] == 5, g


def test_no_cap_hits(res):
    assert res["cap_hits"] == []


def test_no_sat(res):
    assert res["sat_found"] == []


def test_every_group_closed(res):
    for g, d in res["by_group"].items():
        assert d["closed"] is True, g
        assert d["verdicts"] == ["UNSAT_COMPLETE"], g


def test_cell_closed(res):
    assert res["cell_closed"] is True


def test_no_symmetry_cut_was_used(res):
    assert "none" in res["engine_parameters"]["symmetry_cuts_used"]


def test_engine_length_condition_is_exactly_shcap(res):
    assert res["engine_parameters"]["SHCAP"] == 26
    assert res["engine_parameters"]["ORBCAP"] == 25
    assert res["engine_parameters"]["DCAP"] == 4
    assert res["engine_parameters"]["EXCCAP"] == 5


# ------------------------------------------------------------------- claim hygiene
def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."
    assert "PROVISIONAL" in res["label"] and "NOT INDEPENDENTLY AUDITED" in res["label"]


def test_document_never_claims_the_bound():
    doc = (ROOT / "research" / "RR_F1_K1_END2END_125_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "독립 감사" in doc


def test_document_keeps_the_weight6_correction_box():
    doc = (ROOT / "research" / "RR_F1_K1_END2END_125_CLAUDE.md").read_text(encoding="utf-8")
    assert "정정 상자" in doc and "308" in doc and "461" in doc
