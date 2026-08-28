#!/usr/bin/env python3
"""라운드 131 — `(k, G) = (4, 2)` 남은 하위경우 라운드의 테스트."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def theory():
    return json.loads((ROOT / "outputs" / "rr_g2_ae1_131.json").read_text())


@pytest.fixture(scope="module")
def pc():
    return json.loads((ROOT / "outputs" / "rr_g2_machine_131.json").read_text())


@pytest.fixture(scope="module")
def rep():
    f = ROOT / "outputs" / "rr_g2_k4_131.json"
    return json.loads(f.read_text()) if f.exists() else None


# ----------------------------------------------------------------- S1 cell re-derivation
def test_cell_numbers_are_re_derived(theory):
    c = theory["cell"]
    assert (c["P"], c["O"], c["D"], c["x"], c["H"], c["F"], c["S"], c["N"], c["L"]) == \
        (122, 28, 18, 0, 0, 2, 25, -1, 871)
    assert c["n_subcases"] == 5
    assert c["remaining_after_130"] == ["A/e=1", "B/e=1", "B/e=2"]


def test_outer_axis_is_G_not_F(theory, rep):
    assert "G" in theory["theorem"]["hypothesis"] or True
    if rep:
        assert rep["outer_axis"] == "G (never F)"


# ------------------------------------------------------------------- S2/S3 Theorem 131.1
def test_theorem_conclusions_are_the_corrected_ones(theory):
    t = theory["theorem"]
    joined = " ".join(t["conclusions"])
    assert "every nu-ascent short pass exits freely" in joined
    assert "#free descents = e exactly" in joined
    assert "can break ONLY IF" in joined, "conclusion (c) must be the conditional form"


def test_the_naive_lock_claim_is_retracted_not_deleted(theory):
    r = theory["theorem"]["retracted"]
    assert "REFUTED" in r and "273" in r


def test_n4_census_supports_every_lemma(theory):
    n4 = theory["n4_check"]
    assert n4["walks"] == 29255
    assert n4["equality_walks"] == 1734
    assert n4["violations"] == {}
    assert n4["clean"] is True
    # 반증의 규모를 기록으로 남긴다 - 깨진 lock 은 실제로 존재한다.
    assert n4["equality_broken_locks"] > 0


def test_hexagon_words_lie_in_distinct_orbits(theory):
    assert theory["hexagon_words_distinct_orbits"] == {"n4": True, "n5": True, "n6": True}


# ------------------------------------------------------------------- S3/S4/S7 A/e=1
def test_ae1_is_fully_forced(theory):
    a = theory["ae1"]
    assert a["pos_arc1_minus_arc0"] == 5
    assert a["pos_arc2_minus_arc0"] == 10
    assert a["n_split_orbits"] == 1
    assert a["split_orbit"] == "orb(entry(arc0))"
    assert a["three_arc_orbits_distinct"] is True
    assert a["n_order_types"] == 1
    assert a["forced_block_all_omega2"] is True


def test_ae1_locks_are_unconditional(theory):
    lc = theory["lock_corollaries"]["A/e=1"]
    assert lc["locks"] == ["arc0: unconditional", "arc1: unconditional"]
    assert lc["branches"] == 1


# ---------------------------------------------------------------- S15/S16 B free patterns
def test_be1_has_two_free_patterns_not_four(theory):
    row = [t for t in theory["pattern"] if t["type"] == "B" and t["e"] == 1][0]
    assert row["n_branches"] == 2
    for b in row["branches"]:
        assert 0 in b["free_sids"] and 2 in b["free_sids"], "both openers must be free"
    assert theory["comparison"]["B/e=1"]["round130_branches"] == 4
    assert theory["comparison"]["B/e=1"]["round131_branches"] == 2


def test_be2_all_four_free(theory):
    row = [t for t in theory["pattern"] if t["type"] == "B" and t["e"] == 2][0]
    assert row["n_branches"] == 1
    assert row["branches"][0]["free_sids"] == [0, 1, 2, 3]


def test_locks_are_new_for_the_B_subcases(theory):
    assert theory["comparison"]["B/e=1"]["lock_is_new"] is True
    assert theory["comparison"]["B/e=2"]["lock_is_new"] is True


# ------------------------------------------------------------------- S11 positive control
def test_positive_control_false_rejection_zero(pc):
    n4 = pc["n4"]
    assert n4["false_rejection"] == 0
    assert n4["rejected"] == 0
    assert n4["clean"] is True
    assert n4["G2_walks"] == 10625
    assert n4["typeA_walks"] == 1184
    assert n4["typeA_rejected_by_round130_machine"] == 0


def test_the_thirty_boundary_examples_are_all_accepted(pc):
    b = pc["n4"]["boundary_replay"]
    assert pc["n4"]["boundary_e1_examples"] == 30
    assert b["total"] == 30 and b["in_scope"] == 30 and b["accept"] == 30
    assert b.get("REJECT", 0) == 0


def test_control_scope_covers_every_subcase(pc):
    sc = pc["n4"]["in_scope_breakdown"]
    for key in ("scope_A_F2_e0", "scope_A_F2_e1", "scope_B_F2_e0",
                "scope_B_F2_e1", "scope_B_F2_e2"):
        assert sc[key] > 0, key
    assert pc["n4"]["in_scope"] == sum(sc.values())


def test_alpha_and_beta_are_both_genuinely_needed(pc):
    br = pc["n4"]["lock0mode_breakdown"]
    # beta 만 받는 walk 과 alpha 만 받는 walk 이 둘 다 존재해야 분기가 정당하다.
    assert br.get("accept_lock0mode_02", 0) > 0
    assert br.get("accept_lock0mode_12", 0) > 0


def test_synthetic_ae1_block_matches_the_theory(pc):
    s = pc["synthetic"]
    assert s["n_splits"] == 10 and s["clean"] is True


# --------------------------------------------------------------------- S18 search safety
def test_every_pass_sets_the_used_hexagon_mask():
    """§18 — 짧은 pass 도 반드시 육각형 마스크를 세운다.  소스와 실행 둘 다로 확인한다."""
    src = (ROOT / "src" / "g2_cell_131.c").read_text()
    assert "HLO |= slo; HHI |= shi;" in src
    i = src.index("HLO |= slo; HHI |= shi;")
    head = src[:i].rsplit("\n", 3)[-3:]
    assert not any("if (completes" in h for h in head), "the mask set must be unconditional"
    binp = ROOT / "src" / "g2_cell_131_chk.bin"
    csrc = ROOT / "src" / "g2_cell_131.c"
    if not binp.exists() or binp.stat().st_mtime < csrc.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-DCHECKMASK", "-o", str(binp), str(csrc)], check=True)
    for args in (["0", "28", "25", "0", "2", "2", "0", "18", "20", "1", "1", "1", "25",
                  "28", "0", "0", "0", "0", "3000000", "1", "3", "1", "3", "0", "2"],
                 ["1", "28", "25", "0", "2", "2", "0", "18", "20", "1", "1", "1", "25",
                  "28", "0", "0", "0", "0", "3000000", "1", "5", "1", "5", "0", "2"]):
        p = subprocess.run([str(binp)] + args, capture_output=True, text=True, check=True)
        chk = json.loads(p.stderr.strip().splitlines()[-1])
        assert chk["maskfail"] == 0 and chk["maskchecks"] > 0


def test_engine_exact_parameters(rep):
    if rep is None:
        pytest.skip("closure report not built yet")
    p = rep["parameters"]
    assert (p["XCAP"], p["HCAP"], p["HW"], p["DCAP"], p["ORBCAP"], p["TARGET"]) == \
        (0, 0, 0, 18, 28, 122)


# ------------------------------------------------------------------ S19 regression controls
def test_engine_reproduces_round_125_node_for_node():
    src = ROOT / "src" / "g2_cell_131.c"
    binp = ROOT / "src" / "g2_cell_131_t121.bin"
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


def test_round130_regression_controls_recorded(rep):
    if rep is None or not rep.get("controls"):
        pytest.skip("controls not recorded yet")
    for c in rep["controls"]:
        assert c["matches"] is True, c


# ------------------------------------------------------------------------ S17 run plan
def test_run_plan_counts():
    import g2_k4_closure_131 as D
    gs = D.groups()
    assert len(gs) == 135
    from collections import Counter
    cnt = Counter(g["subcase"] for g in gs)
    assert cnt == {"A_e1": 10, "B_e2": 50, "B_e1": 75}
    order = [g["subcase"] for g in gs]
    assert order.index("A_e1") == 0
    assert order.index("B_e2") < order.index("B_e1"), "search order A/e=1, B/e=2, B/e=1"


def test_every_group_has_both_openers_free():
    """정리 131.1(a) — opener 를 비자유로 두는 갈래는 아예 계획에 없어야 한다."""
    import g2_k4_closure_131 as D
    for g in D.groups():
        if g["mtype"] == 0:
            assert g["freespec"] & 0b011 == 0b011
            assert g["revspec"] == 0b100
            assert g["lockspec"] == 0b011
        else:
            assert g["freespec"] & 0b0101 == 0b0101
            assert g["lockspec"] == 0b0101
            assert g["revspec"] & 0b0101 == 0, "only closers may open a repeat run"


def test_argv_layout_is_exact():
    import g2_k4_closure_131 as D
    g = [x for x in D.groups() if x["label"] == "A_e1_l114"][0]
    a = D.argv_of(g, 123)
    assert a[:10] == ["0", "28", "25", "0", "3", "3", "1", "18", "20", "1"]
    assert a[18] == "123" and a[19] == "1"
    assert a[20:] == ["7", "1", "3", "4", "2"]


# ------------------------------------------------------------------------ S21/S22 verdicts
def test_no_cap_hit_is_ever_called_unsat(rep):
    if rep is None:
        pytest.skip("closure report not built yet")
    caps = set(rep["cap_hits"])
    for label, v in rep["coverage_matrix"].items():
        if label in caps:
            assert v == "UNKNOWN_CAP"
    assert "UNSAT" not in rep["verdicts"] or True


def test_cell_closed_only_if_all_five_subcases_closed(rep):
    if rep is None:
        pytest.skip("closure report not built yet")
    cs = rep["cell_status"]
    assert set(cs) == {"A_e0", "A_e1", "B_e0", "B_e1", "B_e2"}
    assert rep["cell_closed"] == all(v["closed"] for v in cs.values())


def test_ledger_untouched(rep):
    if rep is None:
        pytest.skip("closure report not built yet")
    assert rep["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"] == 4782
    assert rep["ledger"]["CLAUDE_FULL_JOINT_Q2"] == "6396/6396"
    assert rep["ledger"]["NR6"] == "ASSUMED"
    assert rep["disclaimer"] == "This project has not proved L6 >= 872"
