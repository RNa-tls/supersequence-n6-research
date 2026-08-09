import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


class C4CollisionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((OUT / "rr_short_ell2_r1_37_c4_collision_ledger.json").read_text())
        cls.classes = json.loads((OUT / "rr_short_ell2_r1_37_c4_collision_classes.json").read_text())
        cls.touch = json.loads((OUT / "rr_short_ell2_r1_37_c4_first_touch_audit.json").read_text())
        cls.closure = json.loads((OUT / "rr_short_ell2_r1_37_c4_predecessor_closure.json").read_text())
        cls.verified = json.loads((OUT / "rr_short_ell2_r1_37_c4_verified.json").read_text())

    def test_count_and_taxonomy_conservation(self):
        self.assertEqual(self.ledger["C4_attempts"], 253537)
        self.assertEqual(self.ledger["mechanism_histogram"]["K0"], 253537)
        self.assertEqual(sum(self.ledger["mechanism_histogram"].values()), 253537)
        self.assertEqual(self.touch["classification"]["T2"], 253537)
        self.assertEqual(sum(self.touch["classification"].values()), 253537)

    def test_signature_counts_and_full_histories(self):
        self.assertEqual(self.ledger["exact_collision_signatures"], 86)
        self.assertEqual(self.ledger["left_s6_canonical_collision_signatures"], 17)
        for group in (self.classes["exact_signatures"], self.classes["left_s6_canonical_signatures"]):
            for row in group:
                self.assertTrue(row["representative"]["macro_history_suffix"]["full_stored_suffix"])

    def test_monotone_subcase_and_unresolved_routes(self):
        for h in ("40", "90", "91", "92"):
            self.assertEqual(self.closure["root_hex_mask_histograms"][h], {"63": 84})
        self.assertEqual(len(self.closure["remaining_hex82_case"]["unresolved_local_phase_routes"]), 5)
        self.assertFalse(self.closure["complete_finite_C4_prerequisite_closure"])

    def test_independent_verifier(self):
        self.assertTrue(self.verified["verified"])
        self.assertIn("T2:", self.verified["theorem_level"])


if __name__ == "__main__":
    unittest.main()
