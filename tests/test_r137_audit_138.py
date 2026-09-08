#!/usr/bin/env python3
"""라운드 137 감사 회귀 시험.

Astra 의 코드는 쓰지 않는다.  `src/audit_r137_138.py` 의 독립 검증들을 다시 돌리고,
무거운 탐색 결과는 커밋된 JSON 에 대해 검사한다.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import audit_r137_138 as A                                       # noqa: E402

ASTRA_C0 = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83]
ASTRA_R = {0: 20, 2: 8, 6: 24, 8: 22, 9: 21, 10: 40, 11: 39, 12: 48, 13: 47}
ASTRA_R_CHAINS = {0: 4, 1: 0, 2: 3, 3: 0, 4: 0, 5: 0, 6: 48, 7: 0,
                  8: 26, 9: 21, 10: 216, 11: 684, 12: 1711, 13: 2346}


def load(name):
    return json.loads((ROOT / "outputs" / name).read_text())


class RowArithmetic(unittest.TestCase):
    def test_seven_rows_rederived(self):
        r = A.row_arithmetic()
        self.assertTrue(r["all_rows_reproduced"])
        self.assertEqual((r["P"], r["O"], r["D"]), (122, 27, 13))
        self.assertEqual([x["f_out"] for x in r["rows"]], [1, 2, 3, 1, 2, 3, 4])
        for row in r["rows"]:
            self.assertEqual(row["f_out"], row["e"] + 1)
            self.assertEqual(row["S"], 25)
            self.assertEqual(row["N"], 0)
            self.assertEqual(row["L"], 871)
            self.assertEqual(row["delta"], 1)
        self.assertEqual(r["passes_after_one_ordinary_block"], 117)


class PositionalIdentities(unittest.TestCase):
    def test_10800(self):
        r = A.paid_tail_identities()
        self.assertEqual(r["checked"], 10800)
        self.assertEqual(r["failures"], {})
        self.assertTrue(r["normalized_agree"])
        self.assertTrue(r["full_pass_120_intra_720_of_720"])


class ConnectorLegality(unittest.TestCase):
    """가장 중요한 시험: 경량 연결자가 정확히 둘이라는 것."""

    def test_exactly_one_w2_and_three_w3(self):
        r = A.connector_legality()
        self.assertEqual(r["legal_weight2_moves"], ["w2/10"])
        self.assertEqual(r["legal_weight3_moves"],
                         ["w3/120", "w3/201", "w3/210"])
        self.assertTrue(r["matches_round126_catalogue"])

    def test_021_and_102_are_illegal(self):
        r = A.connector_legality()
        for tail in ("w3/021", "w3/102", "w3/012", "w2/01"):
            self.assertEqual(r["table"][tail]["legal_of_720"], 0, tail)

    def test_no_partially_legal_tail(self):
        self.assertTrue(A.connector_legality()["no_partially_legal_tail"])


class Symmetry(unittest.TestCase):
    def test_renaming_is_an_automorphism(self):
        r = A.renaming_symmetry()
        self.assertEqual(r["total_violations"], 0)
        self.assertTrue(r["transitive_on_words"])
        self.assertTrue(r["normalization_justified"])


class Extraction(unittest.TestCase):
    def test_external_context_preserved(self):
        r = A.extraction_replay()
        self.assertEqual(r["pairs_checked"], 3600)
        self.assertEqual(r["failure_count"], 0)
        self.assertTrue(r["every_hexagon_meets_6_distinct_orbits"])

    def test_gap_parameter_identities(self):
        r = A.gap_parameter_identities()
        self.assertTrue(r["all_identities_hold"])
        self.assertEqual(r["required_total_passes"], 117)


class Capacities(unittest.TestCase):
    def test_C0_independent(self):
        b = load("rr_r137_audit_138.json")["B_C0"]
        self.assertFalse(b["capped"])
        self.assertEqual([b["C0"][str(d)] for d in range(14)], ASTRA_C0)

    def test_root_return_maxima_and_chain_counts(self):
        r = load("rr_r137_rootreturn_audit_138.json")
        for d, v in ASTRA_R.items():
            self.assertEqual(r["R"][str(d)], v, f"R({d})")
        for d in (1, 3, 4, 5, 7):
            self.assertIsNone(r["R"][str(d)], f"R({d}) must be empty")
        for d, v in ASTRA_R_CHAINS.items():
            self.assertEqual(r["chains_all"][str(d)], v, f"chains({d})")

    def test_both_convolutions_fall_short_of_117(self):
        c = load("rr_r137_audit_138.json")["CD_convolutions"]
        self.assertEqual(c["M"]["maximum"], 112)
        self.assertEqual(sorted(c["M"]["argmax"]), [4, 9])
        self.assertEqual(c["R"]["maximum"], 103)
        self.assertEqual(c["R"]["argmax"], [0])
        self.assertTrue(c["both_contradict"])


class Controls(unittest.TestCase):
    def test_835_controls_replayed_clean(self):
        r = load("rr_r137_controls_audit_138.json")["replay"]
        self.assertEqual(r["rows_checked"], 835)
        self.assertEqual(r["kinds"], {"4/M_FRESH_GAP": 53, "6/M_FRESH_GAP": 268,
                                      "6/R_ROOT_RETURN_GAP": 514})
        self.assertEqual(r["failures"], {})
        self.assertTrue(r["privacy_holds_on_all_controls"])

    def test_privacy_is_load_bearing(self):
        """공유 궤도 하나로 M 모순이 사라진다 — 그래서 판정이 PARTIAL 이다."""
        s = load("rr_r137_controls_audit_138.json")["privacy_sensitivity"]
        s0, s1 = s["cases"]
        self.assertEqual(s0["deficit_budget"], 13)
        self.assertTrue(s0["M_still_contradicts"])
        self.assertEqual(s1["deficit_budget"], 18)
        self.assertFalse(s1["M_still_contradicts"])


class Discipline(unittest.TestCase):
    def test_no_872_claim_and_ledger_unchanged(self):
        doc = (ROOT / "research" / "RR_R137_AUDIT_138_CLAUDE.md").read_text()
        self.assertIn("`L6 >= 872` 를 증명하지 않았다", doc)
        self.assertNotIn("L6 = 872", doc)
        self.assertIn("10/55", doc)
        self.assertIn("CLAUDE_ROUND137_CLOSURE_PARTIAL", doc)
        self.assertIn("ASSUMED", doc)

    def test_no_capacity_run_was_capped(self):
        self.assertFalse(load("rr_r137_audit_138.json")["B_C0"]["capped"])
        self.assertNotIn("capped", load("rr_r137_rootreturn_audit_138.json"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
