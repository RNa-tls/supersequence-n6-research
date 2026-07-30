"""Regression tests for the Round-38 independent Round-37 audit."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import verify_rr_round37_envelope_independent as envelope  # noqa: E402
import audit_rr_phase_capacity_callsites as phase  # noqa: E402


class Round37AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.mapping, cls.relevance = envelope.audit()

    def test_33_is_28_plus_5(self):
        counts = self.result["root_counts"]
        self.assertEqual(counts["total"], counts["long_q2_impossible"] + counts["short_unresolved"])
        self.assertEqual(counts["total"], 33)

    def test_every_round35_root_replays_to_round37_root(self):
        rows = self.mapping["rows"]
        self.assertEqual(len(rows), 22)
        self.assertTrue(all(r["classification"] == "LONG_Q2_IMPOSSIBLE" for r in rows))
        self.assertTrue(all(r["matching_evidence"]["independent_replay_state_hash_equal"] for r in rows))

    def test_r27_prefix_6_is_long_q2_impossible(self):
        row = next(r for r in self.mapping["rows"] if r["round35_root_id"] == "R27-prefix-6")
        self.assertEqual(row["round37_root_id"], "long_q1_6")
        self.assertEqual(row["classification"], "LONG_Q2_IMPOSSIBLE")

    def test_independent_m_transition_law(self):
        law = self.result["transition_law"]
        self.assertGreater(law["checked_exact_macro_edges"], 0)
        self.assertEqual(law["expected"]["Z2"], (1, 0, 1))
        self.assertEqual(law["expected"]["R"], (1, 0, 1))
        self.assertEqual(law["expected"]["Z3"], (1, 1, -4))

    def test_long_found_142_phase_regression(self):
        counterexample = phase.counterexample()
        self.assertEqual(counterexample["old_prediction"], 2)
        self.assertEqual(counterexample["engine_realizable_legal_macro_edges"], 3)
        self.assertEqual(counterexample["states"][-1]["landing_hex_popcount"], 5)

    def test_no_long_root_is_resume_worthy_for_q2(self):
        self.assertTrue(all(r["classification"] == "SEARCH_OBSOLETE_BY_Q2_CERTIFICATE"
                            for r in self.relevance["roots"]))

    def test_short_roots_are_not_falsely_closed(self):
        short = [r for r in self.result["rows"] if r["root_id"].startswith("short_")]
        self.assertEqual(len(short), 5)
        self.assertTrue(all(not r["certified_q2_impossible"] and r["envelope_margin_1_upper_bound"] > 0 for r in short))


if __name__ == "__main__":
    unittest.main()
