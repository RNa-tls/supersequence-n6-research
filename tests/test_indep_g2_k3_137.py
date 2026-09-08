#!/usr/bin/env python3
"""독립 (3,2) 라운드의 테스트."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def d():
    return json.loads((ROOT / "outputs" / "rr_indep_g2_k3_137.json").read_text())


# ------------------------------------------------------------------ Theorems I / II
def test_move_orbit_semantics(d):
    m = d["move_semantics"]
    t1 = m["theorem_I"]
    assert t1["short_pass_M2_M3a_hit_nu_target"] is True
    assert t1["M3b_M3c_always_third"] is True
    assert t1["full_pass_M2_M3a_are_intra_run"] is True
    assert "forbidden" in t1["consequence"].lower() or "FORBIDDEN" in t1["consequence"]
    assert m["clean"] is True


def test_phase_offsets_are_plus_one_and_plus_two(d):
    t2 = d["move_semantics"]["theorem_II"]
    assert t2["verified"] is True
    assert t2["offsets"]["M2_plus_1"] == 720 * 6
    assert t2["offsets"]["M3a_plus_2"] == 720 * 6
    assert not any(k.startswith("M2_plus_") and k != "M2_plus_1" for k in t2["offsets"])


# ----------------------------------------------------------------- Theorem III / IV
def test_m3a_contraction(d):
    c = d["m3a_contraction"]
    assert c["cases"] == 3600 and c["clean"] is True and c["violations"] == {}
    assert c["deltas"] == {"P": -4, "O": -1, "D": -1, "S": -1, "H": 0}
    assert "u = number of M3a-type contractions" in c["reproves"]


def test_corollary_IV_sharpens_M_off_target(d):
    assert "M3b or M3c" in d["m3a_contraction"]["corollary_IV"]


# ---------------------------------------------------------------------- Theorem V
def test_capacity_growth_law(d):
    g = d["capacity_growth"]
    assert g["all_match"] is True
    assert "15b" in g["law"]
    assert "EMPIRICAL" in g["status"]      # 일반 증명이 아님을 명시해야 한다


# ------------------------------------------------------------- delta decomposition
def test_delta_decomposition_reproduces_the_row_table(d):
    dd = d["delta_decomposition"]
    assert dd["identity"] == "delta = a + eta"
    assert dd["by_row"] == {"A/e0": ["M"], "A/e1": ["M", "R"], "A/e2": ["R"],
                            "B/e0": ["M"], "B/e1": ["M", "R"], "B/e2": ["M", "R"],
                            "B/e3": ["R"]}


# ------------------------------------------------------------------- n=4 controls
def test_theorems_hold_at_n4(d):
    a = d["n4_adversarial"]
    assert a["move_semantics_clean"] is True
    assert a["m3a_contraction_clean"] is True
    assert "not n=6-specific" in a["verdict"]


# ------------------------------------------------------------------- Theorem VI
def test_one_defect_exclusion_kills_two_rows():
    import indep_g2_k3_137 as M
    r = M.one_defect_exclusion()
    assert r["capacity"]["passes"] == 102
    assert r["capacity"]["capped"] is False
    assert r["capacity"]["nodes"] == 4121832039
    assert r["rows_fully_eliminated"] == ["A/e0", "B/e0"]
    for z in r["unconditional_kills"]:
        assert z["b_prime"] == 0 and z["contraction_guaranteed"] is True


def test_contracted_budget_rule():
    import indep_g2_k3_137 as M
    b = M.contracted_budget()
    assert (b["P_prime"], b["O_prime"], b["D_prime"]) == (117, 26, 13)
    assert b["b_prime_values"] == [0, 1, 2, 3]
    for r in b["rows"]:
        assert r["b_prime"] == (r["e"] - 1 if r["closer_exit"] == "M2 (free)" else r["e"])


def test_e0_rows_cannot_have_a_broken_lock():
    """`e = 0` 이면 반복 run 이 없어 lock 이 깨질 수 없다 — 무조건 축약의 근거."""
    import indep_g2_k3_137 as M
    r = M.one_defect_exclusion()
    e0 = [z for z in r["unconditional_kills"] if z["row"].endswith("e0")]
    assert {z["row"] for z in e0} == {"A/e0", "B/e0"}
    for z in e0:
        assert z["closer_exit"] == "M3b/M3c"


# ---------------------------------------------------- the searcher's own control
def test_searcher_reduces_to_round115_node_for_node():
    binp = ROOT / "src" / "chain_capacity_g1_137.bin"
    src = ROOT / "src" / "chain_capacity_g1_137.c"
    if not binp.exists() or binp.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(binp), str(src)], check=True)
    out = subprocess.run([str(binp), "0", "0", "9", "20000000000", "0"],
                         capture_output=True, text=True, check=True)
    r = json.loads(out.stdout)
    assert r["passes"] == 66 and r["nodes"] == 469852 and r["capped"] is False


def test_one_defect_beats_plain_chain_by_twenty():
    binp = ROOT / "src" / "chain_capacity_g1_137.bin"
    out = subprocess.run([str(binp), "0", "0", "4", "20000000000", "1"],
                         capture_output=True, text=True, check=True)
    r = json.loads(out.stdout)
    assert r["passes"] == 66 and r["capped"] is False        # N*(0,0,4) = 46, so +20


# ------------------------------------------------------------------------- scope
def test_cell_not_closed_and_ledger_untouched(d):
    import indep_g2_k3_137 as M
    r = M.one_defect_exclusion()
    assert len(r["rows_fully_eliminated"]) == 2, "5 of the 7 rows survive"
    assert len(r["not_reached"]) > 0
