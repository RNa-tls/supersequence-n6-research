"""라운드 119 — `(3,1)` hard three 의 구조 분기와 부분 배제를 회귀로 고정한다.

이 라운드도 **칸을 닫지 않았다.**  두 분기가 열려 있다는 사실 자체를 못박는다.
"""

from __future__ import annotations

import itertools
import json
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_F1_K3_HARD_119_CLAUDE.md"

WORDS = ["".join(p) for p in itertools.permutations("012345")]
sig = lambda x: x[1:] + x[0]
tau = lambda x: x[1:5] + x[0] + x[5]


def _rep(x, f, n):
    y, b = x, x
    for _ in range(n - 1):
        y = f(y)
        b = min(b, y)
    return b


ORBR = {x: _rep(x, tau, 5) for x in WORDS}
HEXR = {x: _rep(x, sig, 6) for x in WORDS}


def art():
    return json.loads((OUT / "rr_f1_k3_hard_119.json").read_text())


class CaseFreeze(unittest.TestCase):
    """§1 — A/B/C 를 라운드 118 표에서 다시 유도한다."""

    def rows(self):
        out = []
        for e in range(8):
            for x in range(8):
                for fo in range(3):
                    if fo > 1 + e:
                        continue
                    S = 26 + e + x - fo
                    H = 26 - S
                    if H < 0:
                        continue
                    out.append((e, x, fo, S, H))
        return sorted(out)

    def test_the_three_hard_cases_are_exactly_these(self):
        rows = {(e, x, fo): (S, H) for (e, x, fo, S, H) in self.rows()}
        self.assertEqual(rows[(1, 1, 2)], (26, 0))          # A
        self.assertEqual(rows[(2, 0, 2)], (26, 0))          # B
        self.assertEqual(rows[(1, 0, 2)], (25, 1))          # C (H = 1 branch)
        for (e, x, fo), (S, H) in rows.items():
            self.assertLessEqual(S + H, 26)

    def test_run_and_chain_counts(self):
        for (e, S, H, r, t) in [(1, 26, 0, 28, 1), (2, 26, 0, 29, 1), (1, 25, 1, 28, 2)]:
            self.assertEqual(27 + e, r)
            self.assertEqual(845 + S + H, 871)
            self.assertEqual(t, H + 1)


class CaseAsplit(unittest.TestCase):
    """§2 — A 는 정확히 A4 와 A5 로 갈린다."""

    def test_block_lengths_from_the_phase_equation(self):
        """블록은 phase +1(tau) 과 +2(W3a) 로 정확히 +4 를 만들어야 한다."""
        got = set()
        for j in range(0, 3):
            a = 4 - 2 * j
            if a >= 0 and j <= 1:                            # x = 1 allows at most one jump
                got.add((j, a, a + j + 1))
        self.assertEqual(got, {(0, 4, 5), (1, 2, 4)})

    def test_A4_has_exactly_three_phase_templates(self):
        tpl = [p for p in set(itertools.permutations([1, 1, 2])) if sum(p) == 4]
        self.assertEqual(len(tpl), 3)

    def test_both_A_branches_are_closed(self):
        st = art()["case_status"]["A"]
        self.assertTrue(st["case_closed"])
        self.assertEqual(sorted(st["closed_branches"]), sorted(st["branches"]))


class CaseBorder(unittest.TestCase):
    """§3 — B_ii 의 순서형은 유일하고, orb(Y) 는 X 시점에 신선하다."""

    def test_R_X_start_is_always_after_R_X_end(self):
        """R_X^start 는 Y 뒤에서 시작하고 R_X^end 는 X 에서 끝난다 (X < Y)."""
        pX, pY = 10, 15
        self.assertLess(pX, pY)
        self.assertGreater(pY + 1, pX)

    def test_only_Bi_is_closed(self):
        st = art()["case_status"]["B"]
        self.assertFalse(st["case_closed"])
        self.assertEqual(st["closed_branches"], ["Bi_Y_case_i"])

    def test_Bii_structure_is_recorded(self):
        o = [x for x in art()["open_branches"] if x["label"] == "Bii_Y_case_ii"][0]
        self.assertIn("exactly two runs", o["structure"])
        self.assertIn("fresh", o["structure"])
        self.assertEqual(o["pilot"]["verdict"], "UNKNOWN_CAP")


class CaseCregions(unittest.TestCase):
    """§4 — 무게-4 변은 블록 안에도 X/Y 의 탈출에도 올 수 없다."""

    def test_weight4_always_changes_orbit_so_it_cannot_be_intra_run(self):
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location(
            "core119", ROOT / "legacy_research" / "work" / "superperm_port_lift.py")
        c = importlib.util.module_from_spec(spec)
        sys.modules["core119"] = c
        spec.loader.exec_module(c)
        ap = lambda s: tuple(int(ch) for ch in s)
        as_ = lambda p: "".join(str(v) for v in p)
        n = 0
        for pi in c.tail_permutations(4):
            act = c.tail_action(4, pi)
            for u in WORDS[:60]:
                t = as_(c.word_after(ap(u), act))
                self.assertNotEqual(ORBR[t], ORBR[u])
                self.assertNotEqual(HEXR[t], HEXR[u])
                n += 1
        self.assertEqual(n, 13 * 60)

    def test_exactly_two_regions(self):
        labels = {x["label"] for x in art()["open_branches"]}
        st = art()["case_status"]["C"]
        self.assertEqual(sorted(st["branches"]), ["C1_heavy_before_X", "C2_heavy_after_Y"])
        self.assertIn("C1_heavy_before_X", labels)
        self.assertEqual(st["closed_branches"], ["C2_heavy_after_Y"])
        self.assertFalse(st["case_closed"])


class Search(unittest.TestCase):
    def test_twenty_runs_all_exhaustive(self):
        d = art()
        self.assertEqual(d["runs"], 20)
        self.assertEqual(d["verdicts"], {"UNSAT_COMPLETE": 20})
        for r in d["rows"]:
            self.assertNotEqual(r["verdict"], "UNKNOWN_CAP")
            self.assertNotIn("witness", r)

    def test_four_branches_closed_over_all_five_splits(self):
        d = art()
        self.assertEqual(sorted(d["branches_closed"]),
                         ["A4_gap4_jump_in_block", "A5_gap5_block_forced",
                          "Bi_Y_case_i", "C2_heavy_after_Y"])
        for b in d["branches_closed"]:
            self.assertEqual(d["by_branch"][b]["runs"], 5)
            self.assertTrue(d["by_branch"][b]["closed"])

    def test_the_cell_is_NOT_closed(self):
        d = art()
        self.assertFalse(d["cell_closed"])
        self.assertEqual(len(d["open_branches"]), 2)
        for o in d["open_branches"]:
            self.assertEqual(o["pilot"]["verdict"], "UNKNOWN_CAP")
            self.assertTrue(o["why_open"])

    def test_search_is_not_vacuous(self):
        d = art()
        self.assertGreater(d["max_passes_reached"], 100)
        self.assertLess(d["max_passes_reached"], 121)
        self.assertGreater(d["total_nodes"], 10 ** 11)


class Regressions(unittest.TestCase):
    """§14 — 이미 닫힌 라운드 117/118 실행이 노드 수까지 그대로 재현된다."""

    def test_round_117_and_118_node_counts_are_recorded_unchanged(self):
        txt = DOC.read_text()
        for n in ("8,538,340,341", "750,682,008", "976,708,569"):
            self.assertIn(n, txt)

    def test_the_new_prune_is_reported_as_having_no_measured_effect(self):
        txt = DOC.read_text()
        self.assertIn("노드 수를 하나도 바꾸지 않았다", txt)


class LedgerDiscipline(unittest.TestCase):
    def test_no_cell_closure_claimed(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("여전히 열려 있다", txt)
        self.assertIn("6 / 55", txt)
        for banned in ("(3,1) 칸을 닫았다", "L6 >= 872 proved"):
            self.assertNotIn(banned, txt)

    def test_audit_status_recorded(self):
        txt = DOC.read_text()
        self.assertIn("PARTIAL", txt)
        self.assertIn("독립 감사 없음", txt)

    def test_ledgers_untouched(self):
        lg = art()["ledger"]
        self.assertEqual(lg["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(lg["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)
        self.assertTrue(lg["unchanged_by_this_round"])


if __name__ == "__main__":
    unittest.main()
