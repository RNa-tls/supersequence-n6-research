"""라운드 121 — `(k,F) = (2,1)` 자원 분류 · 무게-4/5 census · 탐색 결과 테스트."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BUD = OUT / "rr_f1_k2_budget_121.json"
RES = OUT / "rr_f1_k2_121.json"


@pytest.fixture(scope="module")
def bud():
    if not BUD.exists():
        pytest.skip("run src/verify_f1_k2_budget_121.py first")
    return json.loads(BUD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/f1_k2_closure_121.py first")
    return json.loads(RES.read_text(encoding="utf-8"))


# ----------------------------------------------------------------- budget (S1, S2)
def test_cell_constants(bud):
    b = bud["budget"]
    assert (b["O"], b["P"], b["D"]) == (26, 121, 9)
    assert b["SH_cap"] == 26


def test_H_at_most_2_is_derived_not_assumed(bud):
    assert bud["summary"]["max_H"] == 2


def test_x_plus_H_at_most_2(bud):
    assert bud["summary"]["max_x_plus_H"] == 2


def test_e_at_most_3(bud):
    assert bud["summary"]["max_e"] == 3


def test_exactly_24_rows_and_26_subcases(bud):
    assert bud["summary"]["n_distinct_rows"] == 24
    assert bud["summary"]["n_subcases"] == 26


def test_every_row_satisfies_lemma_E_and_the_budget(bud):
    for r in bud["budget"]["rows"]:
        assert r["f_out"] <= 1 + r["e"]
        assert r["e"] + r["x"] + r["H"] <= 1 + r["f_out"]
        assert r["S"] == 25 + r["e"] + r["x"] - r["f_out"]
        assert r["S"] + r["H"] <= 26


# ----------------------------------------------------------------- H compositions (S3)
def test_tail_catalogue_is_550(bud):
    c = bud["tail_catalogue"]
    assert c["counts_by_weight"] == {"1": 1, "2": 1, "3": 3, "4": 13, "5": 71, "6": 461}
    assert c["total"] == 550


def test_only_four_heavy_multisets_are_possible(bud):
    got = {tuple(m) for m in bud["summary"]["heavy_weight_multisets_needed"]}
    assert got == {(), (4,), (4, 4), (5,)}


# ----------------------------------------------------------------- census (S4)
def test_weight4_and_weight5_tail_counts(bud):
    assert bud["weight4"]["n_tails"] == 13
    assert bud["weight5"]["n_tails"] == 71


def test_all_heavy_tails_have_exactly_their_weight(bud):
    assert bud["weight4"]["all_weights_exact"] is True
    assert bud["weight5"]["all_weights_exact"] is True


def test_heavy_tails_are_intra_orbit_only_at_ell5(bud):
    assert bud["weight4"]["intra_orbit_only_at_ell5"] is True
    assert bud["weight5"]["intra_orbit_only_at_ell5"] is True


def test_heavy_tails_never_return_to_the_source_hexagon(bud):
    assert bud["weight4"]["never_returns_to_source_hexagon"] is True
    assert bud["weight5"]["never_returns_to_source_hexagon"] is True


def test_exactly_one_intra_orbit_tail_of_each_heavy_weight(bud):
    assert bud["weight4"]["intra_orbit_at_ell5"] == ["W4_0"]
    assert bud["weight5"]["intra_orbit_at_ell5"] == ["W5_0"]


def test_no_heavy_tail_is_only_partially_intra_orbit(bud):
    """균질성 — 720 단어에서 전부이거나 전무다."""
    assert bud["weight4"]["partially_intra_at_ell5"] == []
    assert bud["weight5"]["partially_intra_at_ell5"] == []


def test_three_structural_classes_for_each_heavy_weight(bud):
    assert bud["weight4"]["n_classes"] == 3
    assert bud["weight5"]["n_classes"] == 3


def test_W4_0_shifts_phase_by_3_and_W5_0_by_4(bud):
    assert bud["weight4"]["per_tail"]["W4_0"]["phase_shift_when_intra"]["5"] == {"3": 720}
    assert bud["weight5"]["per_tail"]["W5_0"]["phase_shift_when_intra"]["5"] == {"4": 720}


def test_round_118_hexagon_overlap_census_is_corrected(bud):
    """라운드 118 은 '12개가 0, 1개가 2' 라고 적었다.  실제는 1개가 5, 3개가 1, 9개가 0 이다."""
    ov = {}
    for name, r in bud["weight4"]["per_tail"].items():
        k = list(r["source_target_hexagon_overlap"]["5"].keys())
        assert len(k) == 1, name          # homogeneous over all 720 words
        ov[k[0]] = ov.get(k[0], 0) + 1
    assert ov == {"5": 1, "1": 3, "0": 9}
    assert "2" not in ov


# ----------------------------------------------------------------- analytic kill (S8)
def test_two_rows_die_by_segment_capacity_alone(bud):
    dead = bud["summary"]["dead_by_capacity"]
    assert bud["summary"]["n_dead"] == 2
    got = {(d["e"], d["x"], d["f_out"], d["H"]) for d in dead}
    assert got == {(0, 0, 0, 0), (0, 0, 1, 0)}
    for d in dead:
        assert d["segments"] == 3 and d["segment_capacity"] < 121


# ----------------------------------------------------------------- engine (S16, S17)
@pytest.mark.parametrize("args,expect", [
    # Round 117 (4,1) sub-case A b=1
    (["1", "26", "28", "0", "1", "0", "1", "0", "0", "0", "-1", "0", "0", "0", "0",
      "-1", "0", "0", "0", "-1", "1", "999", "0", "0"], 8_538_340_341),
    # Round 118 G1 b=1
    (["1", "26", "27", "1", "1", "0", "0", "0", "27", "0", "-1", "0", "0", "0", "0",
      "-1", "0", "0", "0", "-1", "1", "999", "0", "0"], 750_682_008),
    # Round 118 G3 b=1
    (["1", "26", "27", "0", "2", "1", "2", "5", "28", "0", "14", "0", "0", "0", "0",
      "-1", "0", "0", "0", "-1", "1", "999", "0", "0"], 976_708_569),
])
@pytest.mark.slow
def test_engine_reproduces_prior_round_node_counts(args, expect):
    binp = ROOT / "src" / "f1_cell_121.bin"
    if not binp.exists():
        pytest.skip("build src/f1_cell_121.c first")
    r = subprocess.run([str(binp)] + args + ["60000000000"],
                       capture_output=True, text=True, check=True, timeout=3600)
    d = json.loads(r.stdout.splitlines()[0])
    assert d["verdict"] == "UNSAT_COMPLETE"
    assert d["nodes"] == expect


def test_engine_knows_71_weight5_tails():
    """무게-5 tail 이 71개가 아니면 build() 가 죽는다."""
    binp = ROOT / "src" / "f1_cell_121.bin"
    if not binp.exists():
        pytest.skip("build src/f1_cell_121.c first")
    r = subprocess.run([str(binp), "1", "0", "26", "0", "0", "0", "0", "0", "26", "0",
                        "-1", "0", "0", "0", "0", "-1", "0", "0", "0", "-1", "2", "1",
                        "0", "0", "1000"], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0
    assert "weight-5 tail count" not in r.stderr


# ----------------------------------------------------------------- results (S22)
def test_groups_cover_every_row(res):
    assert res["rows_total"] == 24


def test_no_cap_hit_counts_as_closure(res):
    for r in res["rows"]:
        if r["verdict"] == "UNKNOWN_CAP":
            assert r["nodes"] >= res["node_cap"]


def test_no_sat_witness(res):
    assert res["sat_found"] is False
    assert all("witness" not in r for r in res["rows"])


def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_canonical_form_only_on_f_out_2_groups(res):
    for r in res["rows"]:
        if r["f_out_row"] == 2:
            assert r["symcut"] == 1 and r["pmax"] == 60
        else:
            assert r["symcut"] == 0 and r["pmax"] == 0


def test_gap_bound_only_on_e1_f2_groups(res):
    for r in res["rows"]:
        expect = 5 if (r["e"] == 1 and r["f_out_row"] == 2) else 0
        assert r["ygap"] == expect


def test_engine_settings_are_the_k2_ones(res):
    for r in res["rows"]:
        assert r["orbcap"] == 26
        assert r["dcap"] == 9
        assert r["exccap"] == 10
        assert r["shcap"] == 26
        assert r["fod"] == 1
        assert r["seam"] == 0 and r["revonly"] == 0 and r["yfresh"] == 0


def test_disclaimer(bud, res):
    assert bud["disclaimer"] == "This project has not proved L6 >= 872."
    assert res["disclaimer"] == "This project has not proved L6 >= 872."
