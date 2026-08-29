#!/usr/bin/env python3
"""라운드 132 — `(k, G) = (4, 2)` 유형 B hard core 라운드의 테스트."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def th():
    return json.loads((ROOT / "outputs" / "rr_b_hardcore_132.json").read_text())


@pytest.fixture(scope="module")
def pc():
    return json.loads((ROOT / "outputs" / "rr_b_machine_132.json").read_text())


@pytest.fixture(scope="module")
def rep():
    f = ROOT / "outputs" / "rr_b_132.json"
    return json.loads(f.read_text()) if f.exists() else None


# ------------------------------------------------------------------- S1 notation
def test_lock_target_never_equals_own_repeat_orbit(th):
    assert th["notation"]["T_ne_Q"].startswith("T_X != Q_X always")


# ------------------------------------------------------------------- S2 B/e=1 patterns
def test_be1_has_exactly_two_free_patterns(th):
    p = th["be1_patterns"]
    assert p["n_patterns"] == 2
    assert p["forced_free"] == ["opener_0", "opener_1"]
    assert len(p["empty_by_theorem"]) == 2
    for pat in p["patterns"]:
        assert 0 in pat["free_sids"] and 2 in pat["free_sids"]


# ------------------------------------------------------------------- S3 exchange
def test_hg_exchange_and_reversal_are_not_symmetries(th):
    e = th["exchange"]
    assert e["hg_relabel_is_a_symmetry"] is False
    assert e["reversal_usable"] is False
    assert e["reversal_changes_invariants"] > 0
    assert e["verdict"].startswith("RETAIN BOTH")


# ------------------------------------------------------------------- S4/S5 Theorem 132.1
def test_theorem_132_1_allows_a_prune(th):
    t = th["theorem_132_1"]
    assert "unconditionally" in t["statement"]
    assert "PRUNE" in t["consequence"]


def test_lock_table_is_complete(th):
    rows = th["lock_table"]
    assert len(rows) == 2
    assert {r["branches"] for r in rows} == {1, 2}
    for r in rows:
        assert r["opener1_lock"].startswith("UNCONDITIONAL")


# ------------------------------------------------------------------- S7/S13/S14 orders
def test_alpha_chain_and_beta_nest(th):
    o = th["order_types"]
    assert o["alpha"]["shape"] == ("opener_0 < closer_0 = opener_0 + 5 < opener_1 "
                                   "< closer_1 = opener_1 + 5")
    b = o["beta"]
    assert b["shape"].endswith("closer_0 = opener_0 + 10")
    assert b["U_range"] == [1, 2, 3, 4]
    assert b["forced_block_all_omega2"] is True
    assert "FULL" in b["extra"]


# --------------------------------------------------------------- S9/S10/S11 models
def test_model_T_is_not_collapsed_away(th):
    m = th["models"]
    assert m["do_not_assume_distinct"] is True
    assert m["model_T"]["possible"] is True
    assert m["model_T"]["n_shapes"] == 1
    assert len(m["model_T"]["ruled_out"]) == 4
    assert m["model_T"]["both_locks"] == "unconditional"


def test_D_beta1_is_analytically_dead(th):
    assert "IMPOSSIBLE" in th["models"]["model_D"]["D_beta1"]
    assert th["models"]["model_D"]["n_live_sub"] == 2


# ------------------------------------------------------------------- S12 audit
def test_alpha_beta_audit_used_the_source_not_the_json(th):
    a = th["audit"]
    assert "not the round-131 JSON" in a["source"]
    assert a["minimal"] is False
    assert a["be2_branches_in_driver"] > 0
    assert any("Model T" in f for f in a["findings"])


# ------------------------------------------------------------------- S16 budget
def test_zero_slack_accounting_closes_for_every_e(th):
    b = th["budget"]
    assert b["omega3_joints"] == 25 and b["omega2_joints"] == 96
    assert b["all_consistent"] is True
    # 정직한 음성 결과를 기록으로 남긴다.
    assert b["one_unit_contradiction_found"] is False


# ------------------------------------------------------------------- S19 split shapes
def test_split_shapes_are_not_grouped_without_proof(th):
    r = th["run_counts"]
    assert r["split_shapes_grouped"] is False
    assert r["be1_round131"] == 75 and r["be1_round132"] == 75
    assert r["be2_round131"] == 50 and r["be2_round132"] == 75


# ------------------------------------------------------------------- n=4 verification
def test_n4_theory_checks_clean(th):
    n4 = th["n4_checks"]
    assert n4["violations"] == {} and n4["clean"] is True
    assert n4["typeB_x0_equality"] == 25
    assert n4["beta_walks"] > 0
    # D-beta1 (opener_0 locked, opener_1 broken) must never appear.
    assert "e2_lock10" not in n4["lock_census"]
    assert "e1_lock10" not in n4["lock_census"]


def test_positive_control_false_rejection_zero(pc):
    assert pc["false_rejection"] == 0 and pc["clean"] is True
    assert pc["rejected_model"] == 0 and pc["rejected_ordpin"] == 0
    assert pc["typeB_equality"] > 400
    # 세 모형이 전부 실제로 채워져 있어야 분기가 최소이면서 망라적이다.
    for k in ("model_0", "model_1", "model_3"):
        assert pc["model_breakdown"][k] > 0


# ------------------------------------------------------------------- S22/S23 controls
def test_engine_reproduces_round_125_node_for_node():
    src = ROOT / "src" / "g2_cell_132.c"
    binp = ROOT / "src" / "g2_cell_132_t121.bin"
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


def test_ordpin_off_keeps_round131_semantics():
    """`ORDPIN = 0` 이고 `MTYPE = 0` 이면 라운드 131 과 동작이 같아야 한다 (소스 수준)."""
    c = (ROOT / "src" / "g2_cell_132.c").read_text()
    assert "if (ORDPIN == 1 && MTYPE != 0)" in c
    assert "if (MTYPE != 0 && pend == 2 && risky) goto undo;" in c
    assert "static int REVSPEC, LOCK0MODE, ORDPIN;" in c


def test_recorded_controls_all_match(rep):
    if rep is None or not rep.get("controls"):
        pytest.skip("round-132 report not built yet")
    for c in rep["controls"]:
        assert c["matches"] is True, c


# ------------------------------------------------------------------- S25 verdicts
def test_no_cap_hit_is_ever_called_unsat(rep):
    if rep is None:
        pytest.skip("round-132 report not built yet")
    for r in rep.get("pilots", []):
        if r["nodes"] >= r["nodecap"]:
            assert r["verdict"] == "UNKNOWN_CAP"


def test_ledger_untouched(rep):
    if rep is None:
        pytest.skip("round-132 report not built yet")
    assert rep["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert rep["ledger"]["CLAUDE_FULL_JOINT_Q2"] == "6396/6396"
    assert rep["ledger"]["NR6"] == "ASSUMED"
    assert rep["disclaimer"] == "This project has not proved L6 >= 872"
