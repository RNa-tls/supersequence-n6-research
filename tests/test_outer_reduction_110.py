"""라운드 110 — 바깥 환원의 계수 항등식과 정정을 회귀로 고정한다.

이 테스트들은 **실제 초순열 문자열에서 직접** 항등식을 다시 계산한다.  저장된 JSON 을
믿지 않고, 문자열이 저장소에 있는 한 언제든 재검증된다.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_OUTER_REDUCTION_110_CLAUDE.md"


def coords(s: str, n: int):
    """비반복 walk 의 (L, P, F, S, H, O, D, k, N) 을 문자열에서 직접 센다."""
    fact = 1
    for i in range(1, n + 1):
        fact *= i
    pos = [i for i in range(len(s) - n + 1) if len(set(s[i:i + n])) == n]
    words = [s[i:i + n] for i in pos]
    assert len(words) == len(set(words)) == fact, "non-repeating walk 이 아니다"
    w = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]

    def sigma(x):
        return x[1:] + x[0]

    def tau(x):
        return x[1:n - 1] + x[0] + x[n - 1]

    def orb(x):
        y, b = x, x
        for _ in range(n - 2):
            y = tau(y)
            b = min(b, y)
        return b

    visited = {words[0]}
    F = 0
    starts = [words[0]]
    for i, wt in enumerate(w):
        if wt >= 2:
            if sigma(words[i]) not in visited:
                F += 1
            starts.append(words[i + 1])
        visited.add(words[i + 1])
    per = {}
    for x in starts:
        per[orb(x)] = per.get(orb(x), 0) + 1
    O = len(per)
    return {"L": len(s), "n": n, "fact": fact, "hexes": fact // n,
            "J": sum(1 for x in w if x >= 2),
            "S": sum(1 for x in w if x >= 3),
            "H": sum(max(x - 3, 0) for x in w),
            "F": F, "P": len(starts), "O": O,
            "D": sum((n - 1) - v for v in per.values())}


def witness():
    return (ROOT / "data" / "verified_872_witness.txt").read_text().strip()


def greedy(n):
    from src.construct import greedy_construct
    s = greedy_construct(n)
    return s if isinstance(s, str) else "".join(map(str, s))


class CountingIdentity(unittest.TestCase):
    """§10.1 — 계수 증명의 각 단계."""

    def test_L_equals_725_plus_J_S_H_on_the_872_witness(self):
        d = coords(witness(), 6)
        self.assertEqual(d["L"], 872)
        self.assertEqual(d["L"], 725 + d["J"] + d["S"] + d["H"])

    def test_P_equals_J_plus_one_and_hexes_plus_F(self):
        for s, n in ((witness(), 6), (greedy(6), 6), (greedy(5), 5), (greedy(4), 4)):
            d = coords(s, n)
            self.assertEqual(d["P"], d["J"] + 1, n)
            self.assertEqual(d["P"], d["hexes"] + d["F"], n)

    def test_the_general_length_identity_holds_for_n_3_to_6(self):
        for s, n in ((witness(), 6), (greedy(6), 6), (greedy(5), 5),
                     (greedy(4), 4), (greedy(3), 3)):
            d = coords(s, n)
            self.assertEqual(
                d["L"], n + d["fact"] - 2 + d["hexes"] + d["F"] + d["S"] + d["H"], n)

    def test_D_equals_5k_minus_F_at_n6(self):
        for s in (witness(), greedy(6)):
            d = coords(s, 6)
            self.assertEqual(d["D"], 5 * (d["O"] - 24) - d["F"])


class KoRecordCorrections(unittest.TestCase):
    """§0 — 기초 기록의 두 항등식이 실제 초순열에서 거짓임을 고정한다."""

    def test_original_length_identity_is_wrong_on_both_real_superpermutations(self):
        for s in (witness(), greedy(6)):
            d = coords(s, 6)
            k = d["O"] - 24
            N = d["S"] + d["F"] - d["O"]
            self.assertNotEqual(867 + k + N + d["H"], d["L"])      # KO-RECORD
            self.assertEqual(868 + k + N + d["H"], d["L"])          # 정정형

    def test_original_theorem_A_is_wrong_and_the_corrected_one_is_tight(self):
        for s in (witness(), greedy(6)):
            d = coords(s, 6)
            self.assertGreater(d["O"], d["S"] + d["F"])             # O <= S+F 는 거짓
            self.assertEqual(d["O"], 1 + d["S"] + d["F"])           # 정정형은 등호

    def test_the_master_status_document_carries_a_correction_box(self):
        txt = (ROOT / "research" / "SUPERPERMUTATION_N6_MASTER_STATUS.md").read_text()
        self.assertIn("정정 상자 — 이 항등식은", txt)
        self.assertIn("L = 844 + F + S + H = 868 + (k + N + H)", txt)
        self.assertIn("L = 867 + (k + N + H)", txt)                 # 원문 보존


class SlabArithmetic(unittest.TestCase):
    """§10.3 — 정정된 슬랩 표."""

    def test_the_872_witness_sits_one_cell_above_the_target_band(self):
        d = coords(witness(), 6)
        k = d["O"] - 24
        N = d["S"] + d["F"] - d["O"]
        self.assertEqual(k + N + d["H"], 4)          # L = 872
        self.assertEqual(868 + 4, 872)

    def test_slab_table_totals(self):
        t = json.loads((OUT / "rr_outer_reduction_110.json").read_text())["corrected_slab_table"]
        self.assertEqual(sum(r["cells"] for r in t["rows"]), t["total_cells"])
        self.assertEqual(t["total_cells"] - t["covered_by_Q2"], t["uncovered_cells"])
        self.assertEqual(t["total_cells"], 55)
        self.assertEqual(t["covered_by_Q2"], 1)
        self.assertEqual(t["uncovered_cells"], 54)
        for r in t["rows"]:
            self.assertEqual(r["F_range"][1], 5 * r["k"])           # F <= 5k
            self.assertEqual(r["H_max"], 4 - r["k"])                # k + H <= 4
            self.assertEqual(r["N_plus_H_max"], 3 - r["k"])         # k + N + H <= 3


class NR6SmallN(unittest.TestCase):
    """§4 — NR 정규화가 최소 길이 바로 위에서 깨진다는 사실."""

    def test_minimum_length_forces_non_repeating_but_one_more_does_not(self):
        d = json.loads((OUT / "rr_outer_reduction_110.json").read_text())["nr6_small_n_exhaustive"]
        self.assertEqual(d["n3_L9"]["repeating_solutions"], 0)
        self.assertEqual(d["n4_L33"]["repeating_solutions"], 0)
        self.assertGreater(d["n4_L34"]["repeating_solutions"], 0)
        self.assertIsNotNone(d["n4_L34"]["smallest_repeating"])
        self.assertEqual(d["n4_L34"]["smallest_repeating"]["length"], 34)

    def test_the_preserved_repeating_example_really_is_one(self):
        d = json.loads((OUT / "rr_outer_reduction_110.json").read_text())["nr6_small_n_exhaustive"]
        ex = d["n4_L34"]["smallest_repeating"]
        s, n = ex["string"], 4
        wins = [s[i:i + n] for i in range(len(s) - n + 1)]
        perm = [w for w in wins if len(set(w)) == n]
        self.assertEqual(len(set(perm)), 24)             # 초순열이다
        self.assertGreater(len(perm), 24)                # 그러나 반복이 있다
        self.assertEqual(len(perm), ex["windows"])


class OuterGapsAndDiscipline(unittest.TestCase):
    def test_three_independent_outer_gaps_are_recorded(self):
        g = json.loads((OUT / "rr_outer_reduction_110.json").read_text())["outer_gaps"]
        self.assertEqual(len(g), 3)
        self.assertEqual({x["name"] for x in g}, {"NR6", "F reduction", "k reduction"})
        self.assertEqual(g[0]["status"], "ASSUMED")
        self.assertTrue(all(x["status"] in ("ASSUMED", "OPEN") for x in g))

    def test_ledger_untouched(self):
        d = json.loads((OUT / "rr_outer_reduction_110.json").read_text())
        self.assertEqual(d["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(d["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)

    def test_document_keeps_the_scope_disclaimer(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)
        self.assertNotIn("L6 >= 872 proved", txt)


if __name__ == "__main__":
    unittest.main()
