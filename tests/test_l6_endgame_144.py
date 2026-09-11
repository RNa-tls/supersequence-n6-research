#!/usr/bin/env python3
"""회귀 시험 — L6 엔드게임 라운드 144 (독립 검증).

이 시험들은 어느 것도 `L6 >= 872` 를 주장하지 않는다.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import l6_master_identity_144 as MI          # noqa: E402
import l6_sigma_deficit_144 as SD            # noqa: E402
import l6_marked_capacity_144 as MC          # noqa: E402
import l6_coupled_144 as CP                  # noqa: E402
import l6_chain_rows_144 as CR               # noqa: E402
import l6_incidence_144 as IN                # noqa: E402

TABLE = ROOT / "outputs" / "rr_l6_marked_capacity_table_144.json"


def test_master_identity_is_a_rearrangement():
    r = MI.symbolic_check()
    assert r["mismatches"] == 0 and r["combinations"] == 15625
    assert MI.fo_identity_from_word_level()["mismatches"] == 0


def test_budget_row_counts():
    b = MI.budgets()
    assert b["870"]["n_rows"] == 20 and b["871"]["n_rows"] == 35
    assert b["869"]["n_rows"] == 10


def test_sigma_deficit_transform():
    r = SD.transform_identity()
    assert r["violations"] == 0 and r["checked"] == 720


def test_sigma_deficit_forbidden_pattern():
    r = SD.forbidden_pattern(max_fours=6)
    assert r["violations"] == 0 and r["cases"] > 1000


def test_sigma_deficit_is_sharp():
    r = SD.sharpness()
    assert [x["slack"] for x in r] == [0, 0]
    assert [(x["A"], x["D"]) for x in r] == [(1, 1), (2, 2)]
    assert all(x["distinct_ports"] for x in r)


def test_joint_catalogue_is_the_literal_overlap_catalogue():
    assert MC.catalogue_check()["violations"] == 0


def test_companion_hex_lemma():
    assert MC.companion_lemma()["violations"] == 0


def test_unmarked_capacity_reproduces_the_old_N_star():
    c = MC.capacity(0, 6, "AB")
    assert c["capped"] is False
    got = [c["table"][f"{d}|00"] for d in range(7)]
    assert got == [20, 20, 33, 33, 46, 46, 49]


def test_full_endpoint_blocks_are_forced_at_zero_deficit():
    """b=0, D=0 에서는 끝 블록이 부분일 수 없다 — 결합 논증의 핵심."""
    c = MC.capacity(0, 1, "AB")
    assert c["table"]["0|10"] == -1 and c["table"]["0|01"] == -1
    assert c["table"]["0|11"] == -1


def test_c_checker_agrees_with_python():
    exe = ROOT / "outputs" / "l6cap_144.exe"
    if not exe.exists():
        return
    out = json.loads(subprocess.run([str(exe), "0", "8", "AB"],
                                    capture_output=True, text=True).stdout)
    py = MC.capacity(0, 8, "AB")
    assert out["nodes"] == py["nodes"] and out["capped"] is False
    for k, v in py["table"].items():
        assert out["table"][k] == v


def test_pruned_checker_agrees_with_unpruned():
    exe = ROOT / "outputs" / "l6cap_p_144.exe"
    ub = ROOT / "outputs" / "rr_l6_capacity_ub_144.txt"
    if not (exe.exists() and ub.exists()):
        return
    a = json.loads(subprocess.run([str(exe), "0", "12", "AB", "0", str(ub)],
                                  capture_output=True, text=True).stdout)
    assert a["pruned"] is True and a["capped"] is False
    assert [a["table"][f"12|{m}"] for m in ("00", "10", "01", "11")] == \
        [83, 73, 73, 68]


def test_piece_model_closes_length_869():
    if not TABLE.exists():
        return
    CP.load_caps()
    r = CP.run(2, coupled=True)
    assert r["surviving_with_fallback_cell"] == 0
    assert r["surviving"] == 0, r["surviving_rows"][:3]


def test_independent_fragment_capacities_are_NOT_enough_at_869():
    """비결합(조각 독립) 상한만으로는 869 가 닫히지 않음을 명시적으로 기록."""
    if not TABLE.exists():
        return
    CP.load_caps()
    r = CP.run(2, coupled=False)
    assert r["surviving"] > 0


def test_chain_searcher_reproduces_the_piece_capacity_at_a_zero():
    """amax=bmax=emax=0 인 사슬은 육각 단순 조각과 같은 대상이어야 한다."""
    exe = ROOT / "outputs" / "l6chain_144.exe"
    if not exe.exists():
        return
    c = json.loads(subprocess.run([str(exe), "0", "6", "0", "0", "0"],
                                  capture_output=True, text=True).stdout)
    assert c["capped"] is False and c["nodes"] == 157364
    assert [c["table"][str(d)] for d in range(7)] == [20, 20, 33, 33, 46, 46, 49]


def test_A_edges_buy_nothing_below_deficit_six():
    """동반 육각 보조정리의 직접 귀결: D<=5 에서 sigma 이음매는 이득이 없다."""
    exe = ROOT / "outputs" / "l6chain_144.exe"
    if not exe.exists():
        return
    c = json.loads(subprocess.run([str(exe), "0", "5", "4", "0", "0"],
                                  capture_output=True, text=True).stdout)
    assert c["capped"] is False
    assert [c["table"][str(d)] for d in range(6)] == [20, 20, 33, 33, 46, 46]


def test_shadow_theorem_geometry():
    assert MC.shadow_theorem()["holds"] is True


def test_incidence_theorem():
    r = IN.check(1500)
    assert r["bound_violations"] == 0 and r["parity_violations"] == 0


def test_left_S6_symmetry_is_proved_not_assumed():
    assert MC.s6_symmetry()["holds"] is True


def test_chain_model_closes_867_to_870():
    if not (ROOT / "outputs" / "rr_l6_chain_capacity_144.json").exists():
        return
    CR.load_cache()
    for t in (0, 1, 2, 3):
        CR.REQUESTED.clear()
        CR._best.cache_clear()
        r = CR.run(t)
        assert r["surviving"] == 0, (t, r["surviving_rows"][:2])
        assert len(CR.REQUESTED) == 0, (t, sorted(CR.REQUESTED)[:5])


if __name__ == "__main__":
    import traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception:
                fails += 1
                print("FAIL", name)
                traceback.print_exc()
    print("failures:", fails)
    sys.exit(1 if fails else 0)
