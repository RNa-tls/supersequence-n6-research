#!/usr/bin/env python3
"""라운드 135 감사의 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def a():
    return json.loads((ROOT / "outputs" / "rr_r135_audit_136.json").read_text())


@pytest.fixture(scope="module")
def v():
    return json.loads((ROOT / "outputs" / "rr_r135_verdict_136.json").read_text())


# ------------------------------------------------------------------- S1 resource table
def test_cell_numbers_derived_independently(a):
    rt = a["resource_table"]
    assert (rt["P"], rt["O"], rt["D"]) == (122, 27, 13)
    assert rt["all_L_within_budget"] is True


def test_exactly_25_rows_18_plus_7(a):
    rt = a["resource_table"]
    assert rt["n_rows"] == 25
    assert {int(k): v for k, v in rt["by_delta"].items()} == {0: 18, 1: 7}
    assert rt["by_type_F"] == {"A/F1": 3, "A/F2": 9, "B/F2": 13}


def test_survivors_are_exactly_the_delta1_rows(a):
    rt = a["resource_table"]
    assert len(rt["delta1_rows"]) == 7
    for r in rt["delta1_rows"]:
        assert r["delta"] == 1 and r["x"] == 0 and r["H"] == 0 and r["F"] == 2


def test_F1_forces_delta_x_H_zero(a):
    for r in a["resource_table"]["rows"]:
        if r["F"] == 1:
            assert (r["delta"], r["x"], r["H"]) == (0, 0, 0)


# ------------------------------------------------------------ S2/S3/S4 contraction
def test_partial_arc_lemma_clean(a):
    p = a["partial_arc_contraction"]
    assert p["cases"] == 10800
    assert p["violations"] == {} and p["clean"] is True
    assert p["deltas"] == {"P": -5, "O": -1, "D": 0, "S": 0, "H": 0}


def test_type_A_both_orders_valid(a):
    assert a["partial_arc_contraction"]["type_A"]["both_orders_valid"] is True


# ------------------------------------------------------------------- S5 accounting
def test_contracted_accounting_consistent(a):
    ca = a["contracted_accounting"]
    assert ca["formula"]["P"] == "112 + u" and ca["formula"]["O"] == 25
    assert ca["formula"]["D"] == "13 - u"
    assert ca["all_b_consistent"] is True
    assert {int(k) for k in ca["b_values"]} <= {0, 1}


# ------------------------------------------------------------- S6/S7 H=0 exclusions
def test_all_thirteen_H0_rows_excluded(a):
    ce = a["capacity_exclusions"]
    assert ce["n_rows"] == 13 and ce["all_excluded"] is True
    for r in ce["rows"]:
        assert r["per_u"] and all(z["excluded"] for z in r["per_u"])
        assert all(z["uncapped"] for z in r["per_u"])


def test_capacity_values_and_the_106_finding(a, v):
    caps = a["capacity_exclusions"]["capacities_used"]
    assert caps["N*(0,0,13)"] == [83, False] or tuple(caps["N*(0,0,13)"]) == (83, False)
    assert tuple(caps["N*(1,0,13)"]) == (98, False), "tight cell computed fresh by the audit"
    assert tuple(caps["N*(1,0,15)"]) == (106, False), "the reported 106 is the s=15 cell"
    note = v["verdicts"]["H0_capacity_exclusions"]["audit_note"]
    assert "N*(1,0,15)" in note and "98" in note


# --------------------------------------------------------------------- S8/S10 H=1
def test_H1_means_one_weight4_joint(a):
    h = a["h1_unique_heavy"]
    assert h["proved"] is True and len(h["rules_out"]) == 4


def test_equality_only_at_4_and_9(a):
    eq = a["equality_classification"]
    assert eq["max_total"] == 112
    assert eq["unique_up_to_orientation"] is True
    assert eq["both_orientations_present"] is True
    assert eq["forces_both_chains_extremal"] is True
    assert eq["all_cells_uncapped"] is True


# ------------------------------------------------------------------ S11/S12 census
def test_extremal_census_reproduces_1_and_12(a):
    ec = a["extremal_census"]
    assert ec["matches_round115"] is True
    assert ec["extremal_chains_s4"] == 1 and ec["extremal_chains_s9"] == 12
    assert ec["orbits_s4"] == 10 and ec["deficit_s4"] == 4
    assert ec["orbits_s9"] == 15 and ec["deficit_s9"] == 9
    # the Python reimplementation must match the C node counts exactly
    assert ec["nodes"] == {"s4": 3555, "s9": 469852}


def test_312_seams_all_fail(a):
    se = a["seam_exhaustion"]
    assert se["combinations"] == 312 and se["matches_312"] is True
    assert se["all_fail"] is True and se["survivors"] == []
    assert "SURVIVES" not in se["outcome"]
    assert sum(se["outcome"].values()) == 312


def test_orbit_and_pass_totals_leave_no_slack(a):
    ec = a["extremal_census"]
    assert ec["orbits_s4"] + ec["orbits_s9"] == 25
    assert ec["N_star_0_0_4"] + ec["N_star_0_0_9"] == 112


# ------------------------------------------------------------------- S14 limitation
def test_delta1_is_a_scope_limit_not_a_compute_limit(a):
    d = a["delta1_limitation"]
    assert d["is_a_theorem_scope_limit"] is True
    assert d["is_a_compute_limit"] is False
    assert "says nothing about whether they are realisable" in d["does_not_imply_feasible"]


# --------------------------------------------------------------- S15/S16/S17/S18
def test_lineage_and_regression_are_partial_for_repo_reasons(v):
    for k in ("regression_suite_18_of_18", "lineage"):
        assert v["verdicts"][k]["verdict"] == "PARTIAL"
        assert "repository" in v["verdicts"][k]["evidence"] or \
               "absent" in v["verdicts"][k]["evidence"]


def test_all_mathematical_verdicts_confirmed(v):
    math_keys = [k for k in v["verdicts"]
                 if k not in ("regression_suite_18_of_18", "lineage")]
    assert len(math_keys) == 12
    for k in math_keys:
        assert v["verdicts"][k]["verdict"] == "CONFIRMED", k


def test_overall_is_partial(v):
    assert v["overall"] == "PARTIAL"
    assert "absent from the repository" in v["overall_reason"]


def test_scope_leaves_cell_open_and_ledger_frozen(v):
    s = v["scope"]
    assert "OPEN" in s["cell_status"] and "7 delta=1" in s["cell_status"]
    assert s["outer_ledger"].startswith("10/55")
    assert s["NR6"] == "ASSUMED"
    assert s["does_not_prove"] == "L6 >= 872"
    assert v["disclaimer"] == "This project has not proved L6 >= 872"
