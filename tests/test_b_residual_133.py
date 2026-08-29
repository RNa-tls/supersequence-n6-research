#!/usr/bin/env python3
"""라운드 133 — 유형 B 잔여 장애물 라운드의 테스트."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    return json.loads((ROOT / "outputs" / "rr_b_residual_133.json").read_text())


@pytest.fixture(scope="module")
def rep():
    return json.loads((ROOT / "outputs" / "rr_b_133.json").read_text())


# ------------------------------------------------------------- S5 Theorem 133.1
def test_block_collision_theorem_is_S6_invariant(res):
    b = res["block_collision_theorem"]
    for k, v in b.items():
        if k == "class_ledger":
            continue
        assert v["S6_invariant"] is True, k


def test_block_collision_kills_the_expected_families(res):
    b = res["block_collision_theorem"]
    beta = b["B/e=1 P1-beta"]
    assert beta["live_splits"] == 15
    # b1 in {1,5} must be dead for every b0
    for b0 in range(1, 6):
        for b1 in (1, 5):
            assert [b0, b1] in beta["dead_splits"], (b0, b1)
    t = b["B/e=2 Model T"]
    assert t["live_splits"] == 16
    for b1 in range(1, 6):
        assert [1, b1] in t["dead_splits"]


def test_the_thirty_billion_node_class_is_killed_in_one_line(res):
    """`B_e1_b11_P1b` = `(b0, b1) = (1, 1)` 는 정리 133.1 로 즉시 죽어야 한다."""
    assert [1, 1] in res["block_collision_theorem"]["B/e=1 P1-beta"]["dead_splits"]


def test_collision_predicate_never_rejects_a_real_walk(res):
    c = res["n4_collision_control"]
    assert c["false_rejection"] == 0 and c["clean"] is True
    assert c["beta_walks"] > 0 and c["accepted"] == c["beta_walks"]


def test_alpha_branches_are_explicitly_not_killed(res):
    note = res["block_collision_theorem"]["class_ledger"]["note"]
    assert "alpha-type branches" in note and "no collision test applies" in note


# ------------------------------------------------------------- S10/S11/S12 macros
def test_beta_block_has_eleven_passes_and_ten_internal_joints(res):
    m = res["beta_macro"]["macro"]
    assert m["passes"] == 11 and m["internal_joints"] == 10
    assert m["internal_cost"] == 0 and m["deficit_delta"] == 0
    assert m["new_orbits"] == 2 and m["new_runs"] == 3 and m["hexagons"] == 9


def test_alpha_does_not_collapse_to_one_macro(res):
    assert "does NOT collapse" in res["alpha_macro"]["note"]


def test_model_T_not_excluded_by_n4(res):
    assert res["model_t_macro"]["do_not_use_n4_x0_absence"] is True


def test_orbit_words_lie_in_distinct_hexagons(res):
    assert res["orbit_words_distinct_hexagons"] is True


# ------------------------------------------------------- S17/S18 compression verdict
def test_residual_state_is_incompressible(rep):
    c = rep["compression"]
    assert c["full_reduction"] == 1.0, "every block-exit state has a distinct fingerprint"
    assert c["achieved"] is False
    assert c["raw_block_exit_states"] == c["distinct_full_signatures"]


def test_dead_block_class_never_reaches_block_exit(rep):
    i = rep["instrumentation"]
    assert i["dead_block_class_b11"]["block_exit_raw"] == 0
    assert i["live_block_class_b33"]["block_exit_raw"] > 0


def test_deaths_are_mid_depth_not_late(rep):
    b33 = rep["instrumentation"]["live_block_class_b33"]
    busiest = b33["busiest_depths"][0][0]
    assert 30 <= busiest <= 60, "the mass of the search dies in the middle depths"
    assert b33["death_census"]["sterile_no_child"] > b33["death_census"]["chain_capacity"]


# ------------------------------------------------------------------ S15 ORDPIN
def test_ordpin_is_only_a_constant_factor(rep):
    o = rep["ordpin_measurement"]
    assert o["with_pin"]["verdict"] == "UNSAT_COMPLETE"
    assert o["without_pin"]["verdict"] == "UNSAT_COMPLETE"
    assert 1.0 < o["node_reduction"] < 2.0
    assert "engineering value only" in o["verdict"]


# ------------------------------------------------------------------ S21 no sweep
def test_no_sweep_was_launched(rep):
    assert rep["sweep_launched"] is False
    assert rep["structural_reduction"] < rep["target_reduction"]
    assert rep["class_ledger"]["round133_classes"] == 118
    assert rep["class_ledger"]["killed_analytically"] == 32


# ------------------------------------------------------------------ S20 certificate
def test_certificate_is_complete(rep):
    c = rep["certificate"]
    assert c["source_commit"]
    for k in ("engine_132", "engine_133_instrumented", "drivers"):
        assert c[k]
    assert c["engine_132"]["sha256"] and c["engine_133_instrumented"]["sha256"]
    assert len(c["runs"]) >= 3
    for r in c["runs"]:
        assert r["digest"] and r["argv"] and r["verdict"]


def test_instrumented_source_is_inert_without_the_flag():
    """`-DINSTR` 없이 빌드하면 라운드 125 컨트롤을 노드까지 재현해야 한다."""
    src = ROOT / "src" / "g2_cell_133.c"
    binp = ROOT / "src" / "g2_cell_133_t121.bin"
    if not binp.exists() or binp.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-DTARGET=121", "-o", str(binp), str(src)], check=True)
    cases = [(["2", "25", "25", "0", "0", "0", "1", "4", "5", "1", "1", "1", "26", "26"], 462058),
             (["2", "25", "25", "0", "0", "0", "0", "4", "5", "1", "1", "1", "26", "26"], 20584)]
    for args, want in cases:
        out = subprocess.run([str(binp)] + args + ["0", "0", "0", "0", "200000000000",
                                                   "1", "0", "0", "0"],
                             capture_output=True, text=True, check=True)
        assert json.loads(out.stdout.strip().splitlines()[0])["nodes"] == want


# ------------------------------------------------------------------ S23 cell status
def test_cell_not_closed_and_ledger_frozen(rep):
    assert rep["cell_closed"] is False
    assert rep["claude_closed_outer_cells"].startswith("9/55")
    assert rep["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert rep["ledger"]["CLAUDE_FULL_JOINT_Q2"] == "6396/6396"
    assert rep["ledger"]["NR6"] == "ASSUMED"
    assert rep["disclaimer"] == "This project has not proved L6 >= 872"
