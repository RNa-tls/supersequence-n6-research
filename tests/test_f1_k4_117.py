"""라운드 117 — `(4,1)` 예산·보조정리 E·all-light 탐색을 회귀로 고정한다.

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
DOC = ROOT / "research" / "RR_F1_K4_117_CLAUDE.md"

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
    for _ in range(k % 6):
        x = sig(x)
    return x


W2 = lambda y: y[2] + y[3] + y[4] + y[5] + y[1] + y[0]
W3a = lambda y: y[3] + y[4] + y[5] + y[1] + y[2] + y[0]
W3b = lambda y: y[3] + y[4] + y[5] + y[2] + y[0] + y[1]
W3c = lambda y: y[3] + y[4] + y[5] + y[2] + y[1] + y[0]
MOVES = (W2, W3a, W3b, W3c)


def ctrl():
    return json.loads((OUT / "rr_f1_k4_controls_117.json").read_text())


def search():
    return json.loads((OUT / "rr_f1_k4_117.json").read_text())


class Budget(unittest.TestCase):
    """§1 — (4,1) 예산은 보조정리 E 만으로 정확히 두 하위경우가 된다."""

    def test_k4_budget_recomputed(self):
        subs = []
        for e in range(6):
            for x in range(6):
                for fo in range(3):
                    if fo > 1 + e:                       # Lemma E
                        continue
                    S = 23 + 4 + e + x - fo              # S = 23 + k + e + x - f_out
                    H = 26 - S                           # S + H <= 26  (L <= 871)
                    if H < 0:
                        continue
                    subs.append((e, x, fo, S, H, 28 + e))
        self.assertEqual(sorted(subs), [(0, 0, 1, 26, 0, 28), (1, 0, 2, 26, 0, 29)])

    def test_H_is_zero_and_t_is_one(self):
        for (e, x, fo, S, H, r) in [(0, 0, 1, 26, 0, 28), (1, 0, 2, 26, 0, 29)]:
            self.assertEqual(H, 0)
            self.assertEqual(S, 26)
            self.assertEqual(845 + S + H, 871)

    def test_artifact_agrees(self):
        got = [(r["e"], r["x"], r["f_out"], r["S"], r["H"], r["r"])
               for r in ctrl()["s1_k4_subcases"]]
        self.assertEqual(sorted(got), [(0, 0, 1, 26, 0, 28), (1, 0, 2, 26, 0, 29)])

    def test_cell_H_bounds_for_the_whole_F1_column(self):
        b = ctrl()["s12_cell_budgets"]
        self.assertEqual({k: v["H_max"] for k, v in b.items()},
                         {"1": 3, "2": 2, "3": 1, "4": 0})


class LemmaE(unittest.TestCase):
    """§6 — f_out <= 1 + e 의 기하학적 엔진을 독립 재계산한다."""

    def test_the_pairing_identity(self):
        """A 의 자유 후속 = tau(entry_B),  B 의 자유 후속 = tau(entry_A)."""
        n = 0
        for v in WORDS[:240]:
            for b in range(1, 6):
                eA, eB = v, sigp(v, b)
                xA, xB = sigp(v, b - 1), sigp(v, 5)
                self.assertEqual(W2(xA), tau(eB))
                self.assertEqual(W2(xB), tau(eA))
                n += 1
        self.assertEqual(n, 240 * 5)

    def test_artifact_full_720_by_5(self):
        d = ctrl()["s4_s6_lemmas"]
        self.assertEqual(d["cases"], 3600)
        self.assertEqual(d["free_successor_of_A_equals_tau_entry_B"], 3600)
        self.assertEqual(d["free_successor_of_B_equals_tau_entry_A"], 3600)

    def test_theorem_D_sigma_adjacency(self):
        d = ctrl()["s4_s6_lemmas"]
        self.assertEqual(d["sigma_adjacency_of_the_two_arcs"], 3600)
        for v in WORDS[:120]:
            for b in range(1, 6):
                self.assertEqual(sig(sigp(v, b - 1)), sigp(v, b))
                self.assertEqual(sig(sigp(v, 5)), v)

    def test_lemma_E_is_F1_specific(self):
        c = ctrl()["s10_control_n4"]
        self.assertEqual(c["lemma_E_violations_F1"], 0)
        self.assertEqual(c["f_out_2_with_e_0_at_F1"], 0)
        self.assertGreater(c["lemma_E_violations_all_F"], 0)
        self.assertNotIn("1", c["lemma_E_violations_by_F"])

    def test_lemma_E_proves_theorem_A_at_F1(self):
        """O <= 1 + S + F  at F = 1  <=>  f_out <= 1 + e + x, implied by Lemma E."""
        for e in range(4):
            for x in range(4):
                for fo in range(3):
                    if fo <= 1 + e:
                        self.assertLessEqual(fo, 1 + e + x)
        self.assertEqual(ctrl()["s10_control_n4"]["O_le_1_plus_S_plus_F_violations"], 0)


class Geometry(unittest.TestCase):
    """§5/§10 — 탐색기가 쓰는 이동 기하를 독립 재계산한다."""

    def test_W2_at_ell5_is_tau(self):
        self.assertTrue(all(W2(sigp(u, 5)) == tau(u) for u in WORDS))

    def test_short_pass_exits_always_leave_the_orbit(self):
        for ell in range(5):
            for f in MOVES:
                self.assertEqual(
                    sum(1 for u in WORDS[:200] if ORBR[f(sigp(u, ell))] == ORBR[u]), 0)

    def test_no_light_move_returns_to_the_source_hexagon(self):
        for ell in range(6):
            for f in MOVES:
                self.assertEqual(
                    sum(1 for u in WORDS[:200] if HEXR[f(sigp(u, ell))] == HEXR[u]), 0)

    def test_full_pass_geometry_is_the_F0_one(self):
        u = WORDS[0]
        y = sigp(u, 5)
        self.assertEqual(ORBR[W2(y)], ORBR[u])
        self.assertEqual(ORBR[W3a(y)], ORBR[u])
        self.assertNotEqual(ORBR[W3b(y)], ORBR[u])
        self.assertEqual(len(OHEX[ORBR[u]] & OHEX[ORBR[W3b(y)]]), 1)
        self.assertEqual(len(OHEX[ORBR[u]] & OHEX[ORBR[W3c(y)]]), 0)

    def test_artifact_move_tables(self):
        d = ctrl()["s10_control_move_tables"]
        for q in ("move_targets_are_permutations", "W2_at_ell5_is_tau",
                  "short_pass_exits_always_leave_the_orbit",
                  "no_light_move_returns_to_the_source_hexagon"):
            self.assertTrue(d[q], q)


class PositiveControls(unittest.TestCase):
    """§10 — 거짓 기각 0."""

    def test_all_three_splits_have_accepted_fragments(self):
        rows = ctrl()["s10_control_fragments"]
        self.assertEqual(len(rows), 5)
        for r in rows:
            self.assertTrue(r["accepted"], r["b"])
            self.assertTrue(r["distinct_hexagons"], r["b"])
            self.assertTrue(r["second_visit_word_is_sigma_b_of_first"], r["b"])
            self.assertEqual(r["second_visit_length"], 6 - r["b"])
        self.assertEqual(sorted({tuple(sorted(r["split"])) for r in rows}),
                         [(1, 5), (2, 4), (3, 3)])

    def test_n4_exhaustive_still_embeds(self):
        c = ctrl()["s10_control_n4"]
        self.assertEqual(c["n4_walks"], 2598)
        self.assertEqual(c["n4_F1"], 971)
        self.assertEqual(c["O_le_1_plus_S_plus_F_violations"], 0)


class Search(unittest.TestCase):
    """§9 — (4,1) all-light 탐색: 판정과 캡 규율."""

    def test_every_run_is_exhaustive(self):
        d = search()
        self.assertEqual(d["cell"], [4, 1])
        self.assertEqual(d["runs"], 10)
        self.assertEqual(d["verdicts"], {"UNSAT_COMPLETE": 10})
        self.assertTrue(d["all_unsat_complete"])
        for r in d["rows"]:
            self.assertNotEqual(r["verdict"], "UNKNOWN_CAP", r)
            self.assertNotIn("witness", r)

    def test_both_subcases_and_all_five_splits_are_covered(self):
        d = search()
        keys = {(r["subcase"], r["b"]) for r in d["rows"]}
        self.assertEqual(len(keys), 10)
        self.assertEqual({s for s, _ in keys},
                         {"A_e0_x0_fout1", "B1_e1_x0_fout2"})
        self.assertEqual({b for _, b in keys}, {1, 2, 3, 4, 5})

    def test_the_search_is_not_vacuous(self):
        """가지치기가 공허하지 않다 — 실제로 100 pass 를 넘겨 탐색한다."""
        d = search()
        self.assertGreater(d["max_passes_reached"], 100)
        self.assertLess(d["max_passes_reached"], 121)

    def test_parameters_match_the_budget(self):
        d = search()
        self.assertEqual(d["costcap"], 26)
        self.assertEqual(d["orbcap"], 28)
        for r in d["rows"]:
            self.assertEqual(r["xcap"], 0)
            if r["subcase"].startswith("A"):
                self.assertEqual((r["foutcap"], r["ecap"]), (1, 0))
            else:
                self.assertEqual((r["foutcap"], r["ecap"]), (2, 1))
                self.assertEqual(r["foutmin"], 2)
                self.assertEqual(r["ygap"], 5)

    def test_provenance_of_the_subcase_A_rows_is_recorded(self):
        d = search()
        self.assertIn("SUPERSET", d["provenance_note"])
        self.assertTrue(d["cell_closed"])
        self.assertIn("NOT INDEPENDENTLY AUDITED", d["label"])


class LedgerDiscipline(unittest.TestCase):
    def test_document_scope(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("NR6", txt)
        for banned in ("L6 >= 872 proved", "F=1 열을 닫았다"):
            self.assertNotIn(banned, txt)

    def test_q2_zero_is_not_counted_as_generic_closure(self):
        txt = DOC.read_text()
        self.assertIn("Q2", txt)
        self.assertIn("(1,1)", txt)

    def test_ledgers_untouched(self):
        lg = ctrl()["ledger"]
        self.assertEqual(lg["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(lg["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)
        self.assertTrue(lg["unchanged_by_this_round"])


if __name__ == "__main__":
    unittest.main()
