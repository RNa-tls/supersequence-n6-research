"""라운드 130 — `(k,G) = (4,2)` 칸 폐쇄 테스트."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_g2_k4_130.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/g2_k4_closure_130.py first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drv():
    return pytest.importorskip("g2_k4_closure_130")


# ---------------------------------------------------------------- S1/S2 derivation
def test_five_subcases_rederived(drv):
    d = drv.subcase_derivation()
    assert d["P"] == 122 and d["O"] == 28 and d["D"] == 18
    assert d["n_subcases"] == 5
    assert d["matches_round_129"] is True


def test_typeA_F1_contributes_nothing_at_k4(drv):
    """§2 — k + x + H <= 2 + F 이므로 F = 1 은 k = 4 에서 불가능하다."""
    assert drv.subcase_derivation()["typeA_F1_contributes"] == 0


def test_all_subcases_force_x_H_zero_and_fout_e_plus_2(drv):
    for r in drv.subcase_derivation()["subcases"]:
        assert r["x"] == 0 and r["H"] == 0 and r["F"] == 2
        assert r["f_out"] == r["e"] + 2
        assert r["S"] == 25 and r["N"] == -1
        assert r["L"] == 871


def test_subcase_shape(drv):
    got = sorted((r["type"], r["e"]) for r in drv.subcase_derivation()["subcases"])
    assert got == [("A", 0), ("A", 1), ("B", 0), ("B", 1), ("B", 2)]


# ------------------------------------------------------------------- S10 split shapes
def test_split_counts(drv):
    assert len(drv.type_a_splits()) == 10
    assert len(drv.type_b_splits()) == 25
    for (a, b, c) in drv.type_a_splits():
        assert a >= 1 and b >= 1 and c >= 1 and a + b + c == 6


def test_run_plan(drv):
    gs = drv.groups()
    from collections import Counter
    c = Counter(g["subcase"] for g in gs)
    assert c == {"A_e0": 10, "A_e1": 10, "B_e0": 25, "B_e2": 25, "B_e1": 100}
    assert len(gs) == 170


def test_free_masks_match_the_proved_patterns(drv):
    for g in drv.groups():
        n = bin(g["freespec"]).count("1")
        assert n == g["fout"], g["label"]
        if g["subcase"] == "A_e0":
            assert g["freespec"] == 0b011 and g["lockspec"] == 0b011
        if g["subcase"] == "B_e0":
            assert g["freespec"] == 0b0101 and g["lockspec"] == 0b0101
        if g["subcase"] == "A_e1":
            assert g["freespec"] == 0b111 and g["lockspec"] == 0b011
        if g["subcase"] in ("B_e1", "B_e2"):
            assert g["lockspec"] == 0, "no locality lock is proved for these"


# ------------------------------------------------------------------ S13 reproduction
def test_engine_reproduces_round_125_node_for_node():
    """새 `G = 2` 엔진을 TARGET=121·mtype=2 로 빌드하면 라운드 125 와 노드까지 같아야 한다."""
    src = ROOT / "src" / "g2_cell_130.c"
    binp = ROOT / "src" / "g2_cell_130_t121.bin"
    if not binp.exists() or binp.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-DTARGET=121", "-o", str(binp), str(src)], check=True)
    cases = [(["2", "25", "25", "0", "0", "0", "1", "4", "5", "1", "1", "1", "26", "26"], 462058),
             (["2", "25", "24", "0", "1", "1", "1", "4", "5", "1", "1", "1", "26", "26"], 487122),
             (["2", "25", "25", "0", "0", "0", "0", "4", "5", "1", "1", "1", "26", "26"], 20584)]
    for args, want in cases:
        out = subprocess.run([str(binp)] + args + ["0", "0", "0", "0", "200000000000",
                                                   "1", "0", "0", "0"],
                             capture_output=True, text=True, check=True)
        got = json.loads(out.stdout.strip().splitlines()[0])
        assert got["nodes"] == want, (args, got["nodes"], want)
        assert got["verdict"] == "UNSAT_COMPLETE"


# ------------------------------------------------------------------- S14 positive control
def test_positive_control_false_rejection_zero(res):
    pc = res["positive_control"]
    assert pc["false_rejection"] == 0
    assert pc["clean"] is True
    assert pc["G2_walks"] == 10625
    assert pc["accepted"] == 10625
    assert pc["breakdown"]["accept:A_nu_order"] == 1138
    assert pc["breakdown"]["accept:A_reverse_order"] == 46
    assert pc["breakdown"]["accept:B"] == 9441


def test_machine_accepts_every_G2_walk(drv):
    m = pytest.importorskip("verify_g2_machine_130")
    assert hasattr(m, "replay_machine")


# ----------------------------------------------------------- S18/S19/S20 run hygiene
def test_no_sat(res):
    assert res["sat_found"] == []


def test_every_completed_run_is_unsat_or_unknown(res):
    for lab, v in res["coverage_matrix"].items():
        assert v in ("UNSAT_COMPLETE", "UNKNOWN_CAP", "NOT_RUN"), (lab, v)


def test_cap_hits_are_reported_as_unknown(res):
    for lab in res["cap_hits"]:
        assert res["coverage_matrix"][lab] == "UNKNOWN_CAP"


def test_closed_subcases_are_fully_unsat(res):
    for s in res["subcases_closed"]:
        d = res["by_subcase"][s]
        assert d["done"] == d["planned"] and d["unsat"] == d["planned"]
        assert d["unknown"] == 0 and d["sat"] == 0


def test_cell_closed_flag_is_honest(res):
    assert res["cell_closed"] == (len(res["subcases_remaining"]) == 0)


# ----------------------------------------------------------------------- S21 ledger
def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_outer_axis_is_G(res):
    assert res["outer_axis"] == "G (never F)"
    assert res["cell"] == "(k,G) = (4,2)"


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."


def test_engine_offers_no_heavy_tails(res):
    assert res["engine"]["heavy_tails_offered"].startswith("none")
    assert res["parameters"]["HW"] == 0 and res["parameters"]["HCAP"] == 0
    assert res["parameters"]["XCAP"] == 0


def test_document_hygiene():
    doc = (ROOT / "research" / "RR_G2_K4_130_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "(k,G)" in doc and "TARGET 122" in doc
