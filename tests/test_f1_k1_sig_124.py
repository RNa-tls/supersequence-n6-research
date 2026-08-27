"""라운드 124 — 일반 `(1,1)` 뿌리의 미래-동치 서명 압축 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "outputs" / "rr_f1_k1_sig_124.json"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run src/f1_k1_sig_124.py first")
    return json.loads(RES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def verify():
    return pytest.importorskip("verify_f1_k1_sig_124")


# --------------------------------------------------- geometry (S3, structural lemma)
def test_every_orbit_meets_five_distinct_hexagons(verify):
    """phase 단사성이 육각형 단사성의 따름정리라는 라운드 124 보조정리."""
    f = verify.orbit_hexagon_facts()
    assert f["orbits"] == 144 and f["hexagons"] == 120
    assert f["orbits_without_5_distinct_hexagons"] == 0
    assert f["orbits_without_5_distinct_phases"] == 0
    assert f["phase_injectivity_implied_by_hexagon_injectivity"] is True


def test_every_hexagon_meets_six_distinct_orbits(verify):
    assert verify.orbit_hexagon_facts()["hexagons_not_meeting_6_orbits"] == 0


def test_geometry_sizes(verify):
    hexid, orbid, phse, oword = verify.geometry()
    assert len(set(hexid)) == 120 and len(set(orbid)) == 144
    assert sorted(hexid.count(h) for h in set(hexid))[0] == 6
    assert sorted(orbid.count(q) for q in set(orbid))[0] == 5
    # (orbit, phase) -> word is a bijection onto the 720 words
    assert len({oword[q][p] for q in range(144) for p in range(5)}) == 720


# ------------------------------------------------------------- run bookkeeping (S18)
def test_every_config_completed(res):
    assert res["configs_capped"] == []
    assert res["probe_overflow_configs"] == []
    assert res["runs"] == 10


def test_no_probe_overflow_anywhere(res):
    for row in res["by_config"].values():
        assert row["probe_overflow"] == 0
        assert row["verdict"] == "COMPLETE"


# -------------------------------------------------------- the compression ladder (S18)
def test_signature_counts_never_exceed_root_counts(res):
    """건전한 서명은 뿌리를 병합할 수만 있고 늘릴 수는 없다."""
    for label, row in res["by_config"].items():
        assert row["distinct_root_signatures"] <= row["roots"], label
        assert row["distinct_coarse_signatures"] <= row["distinct_root_signatures"], label
        assert row["floor_signatures"] <= row["distinct_coarse_signatures"], label
        assert row["distinct_prefix_signatures"] <= row["prefix_states"], label


def test_no_meaningful_compression(res):
    """핵심 음성 결과: 어떤 서명도 x1.2 를 넘지 못한다."""
    c = res["compression"]
    assert c["best_sound_fine"] < 1.2
    assert c["best_sound_coarse"] < 1.2
    assert c["best_ceiling"] < 1.2


def test_ceiling_bounds_every_sound_signature(res):
    """건전하지 않은 CEILING 이 모든 건전 서명의 압축률 상한이다."""
    c = res["compression"]
    assert c["best_ceiling"] >= c["best_sound_fine"]
    assert c["best_ceiling"] >= c["best_sound_coarse"]


def test_rigid_cell_does_not_compress_at_all(res):
    """S13: 강체 셀은 모든 뿌리가 서로 다른 미래 상태를 갖는다."""
    r = res["by_config"]["rigid_e0_x0_H0"]
    assert r["roots"] == 17545
    assert r["distinct_root_signatures"] == 17545
    assert r["distinct_coarse_signatures"] == 17545
    assert r["floor_signatures"] == 17545
    assert r["root_compression"] == 1.0


def test_only_the_H_axis_produces_any_collapse(res):
    """S14: e 축은 압축이 전혀 없고, H 축만이 압축을 만든다."""
    for label in ("rigid_e0_x0_H0", "e1_x0_H0", "e2_x0_H0"):
        assert res["by_config"][label]["root_compression"] == 1.0
    assert res["by_config"]["e0_x0_H1"]["root_compression"] > 1.0
    assert res["by_config"]["e0_x0_H2"]["root_compression"] > \
        res["by_config"]["e0_x0_H1"]["root_compression"]


# ------------------------------------------------------------------- frontier DP (S17)
def test_frontier_dp_buys_nothing(res):
    assert res["frontier_dp"]["measured_prefix_compression"] < 1.2
    for row in res["by_config"].values():
        assert row["prefix_compression"] < 1.2


# ------------------------------------------------------------- positive controls (S20)
def test_positive_controls_all_agree(res):
    pc = res["positive_controls"]
    assert pc["false_rejection"] == 0
    assert pc["all_agree"] is True
    assert len(pc["results"]["replays"]) >= 3
    for label, r in pc["results"]["replays"].items():
        assert r["dumped"] == r["c_roots"], label
        assert r["python_distinct_fine"] == r["c_distinct_fine"], label
        assert r["python_distinct_coarse"] == r["c_distinct_coarse"], label
        assert r["python_distinct_ceiling"] == r["c_ceiling"], label


def test_control_includes_a_cell_where_coarse_is_strictly_coarser(res):
    """몫 구조까지 실제로 검사하는 셀이 대조에 들어 있어야 한다."""
    reps = res["positive_controls"]["results"]["replays"]
    assert any(r["python_distinct_coarse"] < r["python_distinct_fine"] for r in reps.values())


def test_python_replay_of_the_rigid_cell(verify):
    """C 를 믿지 않고 파이썬이 직접 덤프를 다시 센다."""
    r = verify.replay(x=0, e=0, h=0)
    assert r["dumped"] == 17545
    assert r["python_distinct_fine"] == 17545
    assert r["python_distinct_coarse"] == 17545
    assert r["python_distinct_ceiling"] == 17545
    assert r["reported"]["roots"] == 17545
    assert r["reported"]["verdict"] == "COMPLETE"
    assert r["x_within_budget"] and r["cost_within_budget"]
    assert r["every_orbit_phase_mask_nonzero"]


# ------------------------------------------------------- reproduction control (R123)
def test_reproduces_round_123_rigid_numbers(res):
    rc = res["reproduction_control"]
    assert rc["matches"] is True
    assert rc["rigid_roots_round124"] == rc["rigid_roots_round123"] == 17545
    assert rc["rigid_prefix_states_round124"] == rc["rigid_prefix_states_round123"] == 3425
    assert rc["rigid_max_q_round124"] == rc["rigid_max_q_round123"] == 46


def test_rigid_max_q_still_equals_NTAB_4(res):
    assert res["by_config"]["rigid_e0_x0_H0"]["max_prefix_q"] == 46


# ------------------------------------------------------------- claim hygiene (S22)
def test_cell_11_stays_open_and_no_new_closure(res):
    st = res["cell_status"]
    assert st["status"] == "OPEN"
    assert st["closed_by_this_round"] is False
    assert st["F2_started"] is False
    assert st["claude_closed_outer_cells"] == "8/55"


def test_ledgers_unchanged(res):
    assert res["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert res["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"] == 6396
    assert res["ledger"]["unchanged_by_this_round"] is True


def test_disclaimer_present(res):
    assert res["disclaimer"] == "This project has not proved L6 >= 872."
    assert "PROVISIONAL" in res["label"] and "NOT INDEPENDENTLY AUDITED" in res["label"]


def test_document_never_claims_the_bound():
    doc = (ROOT / "research" / "RR_F1_K1_SIG_124_CLAUDE.md").read_text(encoding="utf-8")
    assert "This project has not proved" in doc
    assert "L₆ ≥ 872" not in doc.replace("**This project has not proved `L₆ ≥ 872`.**", "")
    assert "독립 감사" in doc


def test_document_marks_the_ceiling_signature_as_unsound():
    doc = (ROOT / "research" / "RR_F1_K1_SIG_124_CLAUDE.md").read_text(encoding="utf-8")
    assert "진단 전용" in doc or "건전하지 않" in doc
