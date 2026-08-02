"""Regression controls for the official corrected short_ell0 ledger."""
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "outputs" / "rr_short_ell0_official_ledger.json"


class TestOfficialShortEll0Ledger(unittest.TestCase):
    def test_historical_claims_cannot_be_relabelled_as_literal_hits(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        counts = ledger["count_unit_ledger"]
        self.assertEqual(counts["historical_macro_entry_target_a_claims"], 38_406)
        self.assertEqual(counts["literal_source_same_component_false_positives"], 38_405)
        self.assertEqual(counts["literal_target_a_hits"], 1)
        self.assertNotEqual(counts["historical_macro_entry_target_a_claims"],
                            counts["literal_target_a_hits"])

    def test_scope_is_closed_only_for_the_observed_prefix(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        status = ledger["official_status"]
        self.assertEqual(status["corrected_fair_prefix"],
                         "ALL_OBSERVED_TARGET_A_TARGET_B_CLOSED")
        self.assertEqual(status["global_short_ell0"], "OPEN / INCOMPLETE")
        self.assertFalse(status["bounded_run_may_be_presented_as_exhaustion"])


if __name__ == "__main__":
    unittest.main()
