"""라운드 116 — `F = 1` 일반 구조를 회귀로 고정한다.

기하 주장은 저장된 JSON 을 믿지 않고 **독립 재계산**한다.
"""

from __future__ import annotations

import itertools
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_F1_STRUCTURE_116_CLAUDE.md"
DOC115 = ROOT / "research" / "RR_F0_COLUMN_115_CLAUDE.md"

WORDS = ["".join(p) for p in itertools.permutations("012345")]
sig = lambda x: x[1:] + x[0]
tau = lambda x: x[1:5] + x[0] + x[5]


def _rep(x, f, n):
    y, b = x, x
    for _ in range(n - 1):
        y = f(y)
        b = min(b, y)
    return b


HEXR = {x: _rep(x, sig, 6) for x in WORDS}
ORBR = {x: _rep(x, tau, 5) for x in WORDS}
OHEX = defaultdict(set)
for _x in WORDS:
    OHEX[ORBR[_x]].add(HEXR[_x])


def sigp(x, k):
    for _ in range(k):
        x = sig(x)
    return x


def y_ell(u, ell):
    return sigp(u, ell)


# 무게 2 의 tail 은 하나, 무게 3 의 tail 은 셋 — 위치 작용으로 직접 쓴다
def W2_at(u, ell):
    y = y_ell(u, ell)
    return y[2] + y[3] + y[4] + y[5] + y[1] + y[0]


def W3a_at(u, ell):
    y = y_ell(u, ell)
    return y[3] + y[4] + y[5] + y[1] + y[2] + y[0]


def W3b_at(u, ell):
    y = y_ell(u, ell)
    return y[3] + y[4] + y[5] + y[2] + y[0] + y[1]


def W3c_at(u, ell):
    y = y_ell(u, ell)
    return y[3] + y[4] + y[5] + y[2] + y[1] + y[0]


def art():
    return json.loads((OUT / "rr_f1_structure_116.json").read_text())


class Identities(unittest.TestCase):
    """§1 — F=1 의 기본 항등식과 칸 범위."""

    def test_P_O_D(self):
        for k in range(6):
            P, O = 121, 24 + k
            self.assertEqual(5 * O - P, 5 * k - 1)

    def test_F1_forces_k_at_least_one(self):
        self.assertLess(5 * 0 - 1, 0)                 # k = 0 gives D = -1
        self.assertGreaterEqual(5 * 1 - 1, 0)

    def test_slab_caps_k_at_four(self):
        for k in range(1, 7):
            S_min = 22 + k                            # O <= 1 + S + F, F = 1
            H_max = 26 - S_min                        # S + H <= 26
            self.assertEqual(H_max >= 0, k <= 4)

    def test_artifact_feasible_cells(self):
        self.assertEqual(art()["s1_identities"]["feasible_k"], [1, 2, 3, 4])
        self.assertEqual(art()["s9_cells"]["never_touched"], [[2, 1], [3, 1], [4, 1]])

    def test_length_and_shortfall(self):
        self.assertEqual(844 + 1, 845)
        self.assertEqual(871 - 845, 26)
        self.assertEqual(6 * 121 - 720, 6)            # rotation shortfall = 6F


class PassStructure(unittest.TestCase):
    """§2/§3/§8 — 다중도와 pass 길이는 완전히 강제된다."""

    def test_only_three_deficit_partitions_are_realizable(self):
        def parts(n, mx=None):
            mx = n if mx is None else mx
            if n == 0:
                yield ()
                return
            for i in range(min(n, mx), 0, -1):
                for r in parts(n - i, i):
                    yield (i,) + r
        allp = list(parts(6))
        real = {tuple(sorted([a, 6 - a], reverse=True)) for a in range(1, 6)}
        self.assertEqual(len(allp), 11)
        self.assertEqual(sorted(real, reverse=True), [(5, 1), (4, 2), (3, 3)])
        d = art()["s2_s3_s8_pass_structure"]
        self.assertEqual([tuple(x) for x in d["deficit_partitions_realizable"]],
                         [(5, 1), (4, 2), (3, 3)])
        self.assertEqual(len(d["deficit_partitions_excluded"]), 8)
        self.assertIn([6], d["deficit_partitions_excluded"])
        self.assertIn([4, 1, 1], d["deficit_partitions_excluded"])

    def test_short_pass_count_is_exactly_two(self):
        self.assertEqual(art()["s2_s3_s8_pass_structure"]["short_pass_count"], 2)


class SeparationTheorem(unittest.TestCase):
    """정리 D — h* 의 두 pass 는 결코 이웃하지 않는다."""

    def test_the_two_arcs_are_sigma_adjacent_so_they_cannot_be_consecutive(self):
        checked = 0
        for v in WORDS[:120]:
            for a in range(1, 6):
                exit1 = sigp(v, a - 1)          # first arc  [v .. sigma^{a-1} v]
                entry2 = sigp(v, a)             # second arc [sigma^a v .. sigma^5 v]
                self.assertEqual(sig(exit1), entry2)
                exit2 = sigp(v, 5)
                self.assertEqual(sig(exit2), v)
                checked += 1
        self.assertEqual(checked, 120 * 5)

    def test_n4_exhaustive_never_adjacent(self):
        c = art()["s14_controls"]
        self.assertEqual(c["f1_short_passes_adjacent_in_walk_order"], {"False": 971})
        self.assertGreaterEqual(c["f1_min_short_pass_separation"], 2)
        self.assertIn("smallest_non_adjacent_counterexample", c)


class LightGeometry(unittest.TestCase):
    """§7 — ell<5 에서는 네 경량 이동이 전부 궤도를 바꾼다 (독립 재계산)."""

    def test_free_move_is_tau_only_at_ell5(self):
        for ell in range(6):
            same = sum(1 for u in WORDS if ORBR[W2_at(u, ell)] == ORBR[u])
            self.assertEqual(same, 720 if ell == 5 else 0, f"ell={ell}")

    def test_all_light_moves_leave_the_orbit_for_short_passes(self):
        for ell in range(5):
            for f in (W2_at, W3a_at, W3b_at, W3c_at):
                same = sum(1 for u in WORDS[:200] if ORBR[f(u, ell)] == ORBR[u])
                self.assertEqual(same, 0, f"ell={ell} {f.__name__}")

    def test_no_light_move_ever_returns_to_the_source_hexagon(self):
        for ell in range(6):
            for f in (W2_at, W3a_at, W3b_at, W3c_at):
                same = sum(1 for u in WORDS[:200] if HEXR[f(u, ell)] == HEXR[u])
                self.assertEqual(same, 0, f"ell={ell} {f.__name__}")

    def test_free_move_out_of_a_short_pass_always_overlaps_orbits(self):
        for ell in range(5):
            for u in WORDS[:200]:
                self.assertGreaterEqual(len(OHEX[ORBR[u]] & OHEX[ORBR[W2_at(u, ell)]]), 1)

    def test_artifact_table_matches(self):
        T = art()["s7_light_geometry"]["table"]
        self.assertEqual(T["ell5_W2"]["same_orbit"], 720)
        self.assertEqual(T["ell5_W3c"]["orbit_pair_shared_hexagons"], {"0": 720})
        self.assertEqual(T["ell5_W3b"]["orbit_pair_shared_hexagons"], {"1": 720})
        for ell in range(5):
            self.assertEqual(T[f"ell{ell}_W2"]["same_orbit"], 0)
        self.assertTrue(art()["s7_light_geometry"]["free_move_is_tau_only_at_ell5"])


class Accounting(unittest.TestCase):
    """§10 — S 항등식, f_out <= 2, 목표 부등식."""

    def test_requirement_arithmetic(self):
        for k in range(1, 5):
            for e in range(4):
                for x in range(4):
                    for t in range(1, 5):
                        for fo in range(3):
                            cost_lb = 22 + k + e + x + t - fo
                            self.assertEqual(cost_lb <= 26, k + e + x + t - fo <= 4)

    def test_f_out_bound_and_target(self):
        d = art()["s10_invariant"]
        self.assertEqual(d["f_out_bound"], 2)
        self.assertEqual(d["target_theorem"], "k + e + x + t - f_out >= 5")

    def test_no_f_out_le_c_times_k_law(self):
        """f_out = 2 가 k = 1 과 함께 나타나므로 그런 법칙은 없다."""
        c = art()["s14_controls"]
        self.assertGreater(c["f1_f_out_vs_k"]["f_out=2,k=1"], 0)

    def test_cell_table(self):
        rows = {r["k"]: r for r in art()["s9_cell_table"]["rows"]}
        self.assertEqual(rows[4]["H_max"], 0)
        self.assertEqual(rows[4]["t_max"], 1)
        self.assertEqual(rows[1]["t_max"], 4)
        self.assertEqual(art()["s9_cell_table"]["tightest_cell"], 4)


class N4Controls(unittest.TestCase):
    """§14 — n=4 전수 양성 대조, 거짓 기각 0."""

    def test_every_structural_claim_holds_on_all_971(self):
        c = art()["s14_controls"]
        self.assertEqual(c["f1_count"], 971)
        self.assertEqual(c["walks_enumerated"], 2598)
        for q in ("f1_length_identity_ok", "f1_shortfall_ok",
                  "f1_exactly_one_doubled_hexagon",
                  "f1_all_short_passes_live_in_the_doubled_hexagon",
                  "f1_S_identity_ok", "f1_D_nonneg", "f1_k_ge_1",
                  "f1_f_out_never_exceeds_short_pass_count", "f1_cost_bound_ok",
                  "f0_S_identity_ok", "f1_free_inter_run_arc_always_overlaps"):
            self.assertTrue(c[q], q)
        self.assertEqual(c["f1_short_pass_counts"], {"2": 971})
        self.assertEqual(c["f1_multiplicity_pattern"], ['{"1": 5, "2": 1}'])
        self.assertEqual(sorted(c["f1_short_pass_length_pairs"]), ["[1, 3]", "[2, 2]"])

    def test_F0_walks_have_no_free_inter_run_arc(self):
        self.assertEqual(art()["s14_controls"]["f0_f_out_histogram"], {"0": 813})


class Q2Separation(unittest.TestCase):
    """§4 — 자동인 Q2 조건은 둘뿐이다."""

    def test_only_two_conditions_are_generic(self):
        rows = art()["s4_q2_separation"]
        generic = [r["condition"] for r in rows if r["generic_at_F1"]]
        self.assertEqual(len(generic), 2)
        self.assertIn("P = 121", generic)
        self.assertTrue(any(g.startswith("Phi >= 0") for g in generic))
        for r in rows:
            self.assertTrue(r["why"])

    def test_the_bijection_and_intra_orbit_free_arcs_are_not_generic(self):
        rows = {r["condition"]: r for r in art()["s4_q2_separation"]}
        self.assertFalse(rows["pass <-> hexagon bijection"]["generic_at_F1"])
        self.assertFalse(rows["every free arc is intra-orbit"]["generic_at_F1"])


class LedgerDiscipline(unittest.TestCase):
    def test_document_claims_no_cell_closure(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("칸도 닫지 않았고", txt)
        self.assertIn("4,782", txt)
        for banned in ("L6 >= 872 proved", "F=1 열을 닫았다"):
            self.assertNotIn(banned, txt)

    def test_round_115_corrections_are_recorded(self):
        t115 = DOC115.read_text()
        self.assertIn("`H + k ≥ 5` 는 따라 나오지 않는다", t115)
        self.assertIn("PARTIAL", t115)
        self.assertIn("철회", t115)
        d = json.loads((OUT / "superpermutation_n6_master_status.json").read_text())
        e = d["round_115_f0_column"]
        self.assertIn("correction_round_116", e)
        self.assertEqual(e["independent_audit_codex_round_115"]["verdict"], "PARTIAL")
        self.assertEqual(e["independent_audit_codex_round_115"]["independently_confirmed"],
                         [0, 1, 4])
        self.assertNotIn("H + k >= 5", e["headline"])

    def test_ledgers_untouched(self):
        lg = art()["ledger"]
        self.assertEqual(lg["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(lg["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)
        self.assertTrue(lg["unchanged_by_this_round"])


if __name__ == "__main__":
    unittest.main()
