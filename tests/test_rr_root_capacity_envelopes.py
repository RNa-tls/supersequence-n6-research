"""Round 37 regression tests: the root-level capacity envelope theorem,
the 1,398-boundary ledger, the prune-taxonomy ledger, and the 7-root audit.

These tests protect the round's central new claim -- that Q2-impossibility
can be certified from a root's own state, with no enumeration -- against
silent regression, and guard the specific soundness bug this round found
(true_phase_walk_capacity is not a valid upper bound for this purpose).
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


class TestBoundaryLedger(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_1398_boundary_capacity_ledger.json").read_text(encoding="utf-8"))

    def test_1398_rows_all_distinct_at_state_and_word_level(self):
        self.assertEqual(len(self.d["rows"]), 1398)
        self.assertEqual(self.d["count_units"]["distinct_boundary_states_raw_hash"], 1398)
        self.assertEqual(self.d["count_units"]["distinct_literal_words"], 1398)

    def test_all_fail_the_coarse_bound_only(self):
        hist = self.d["first_failing_theorem_histogram"]
        self.assertEqual(hist, {"coarse_segment_bound": 1398})

    def test_bound_ordering_holds_on_every_row(self):
        for r in self.d["rows"]:
            self.assertGreaterEqual(r["bound_1_coarse_segment"], r["bound_2_initial_phase_port"])
            self.assertGreaterEqual(r["bound_2_initial_phase_port"], r["bound_3_true_phase_walk"])

    def test_all_replay_certificates_match(self):
        self.assertTrue(self.d["all_replay_certificates_match"])
        for r in self.d["rows"]:
            self.assertTrue(r["replay_certificate"]["raw_hash_matches"], r["root_id"])

    def test_ndef_boundary_minus_root_matches_k(self):
        """Ndef(boundary) - Ndef(root) must be exactly 1 for every row (all
        these roots have k=1, one R event needed)."""
        for r in self.d["rows"]:
            self.assertEqual(r["Ndef"] - r["root_Ndef"], 1, r["root_id"])


class TestRootCapacityEnvelopes(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_root_capacity_envelopes.json").read_text(encoding="utf-8"))

    def test_no_envelope_violations(self):
        self.assertEqual(self.d["n_envelope_violations"], 0)

    def test_28_long_roots_certified_q2_impossible(self):
        n = sum(1 for r in self.d["rows"]
               if r["k_required_R_events"] == 1 and r["certified_q2_impossible"])
        self.assertEqual(n, 28)

    def test_5_short_roots_not_certified(self):
        n = sum(1 for r in self.d["rows"]
               if r["k_required_R_events"] == 2 and r["certified_q2_impossible"])
        self.assertEqual(n, 0)

    def test_conservation_law_kinds(self):
        kinds = self.d["conservation_law"]["kinds_observed"]
        for k in ("Z2", "Z3", "R"):
            self.assertIn(k, kinds)
        self.assertEqual(kinds["Z2"]["dM"], 1)
        self.assertEqual(kinds["R"]["dM"], 1)
        self.assertEqual(kinds["Z3"]["dM"], -4)

    def test_rejected_refinement_documented(self):
        self.assertIn("long_found_142", self.d["envelope_theorem"]["rejected_refinement_note"])

    def test_envelope_never_exceeded_by_observation(self):
        for r in self.d["rows"]:
            if r["max_margin_1_observed"] is not None:
                self.assertLessEqual(r["max_margin_1_observed"],
                                     r["envelope_margin_1_upper_bound"], r["root_id"])


class TestPruneLedger(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_q1_q2_prune_ledger.json").read_text(encoding="utf-8"))

    def test_ten_conditions_classified(self):
        self.assertEqual(len(self.d["prune_ledger"]), 10)
        n_safe = sum(1 for r in self.d["prune_ledger"].values() if r["is_q1_safe"])
        n_q2 = sum(1 for r in self.d["prune_ledger"].values() if r["is_q2_only"])
        self.assertEqual(n_safe, 4)
        self.assertEqual(n_q2, 6)

    def test_every_q2_only_reason_has_a_counterexample(self):
        for name, row in self.d["prune_ledger"].items():
            if row["is_q2_only"]:
                self.assertIn("minimal_counterexample", row, name)

    def test_q2_implies_q1_theorem_present(self):
        self.assertEqual(self.d["formal_separation"]["theorem_Q2_implies_Q1"]["grade"], "손증명")


class TestEnumeratorStatuses(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_enumerator_statuses.json").read_text(encoding="utf-8"))

    def test_seven_statuses(self):
        self.assertEqual(len(self.d["status_vocabulary"]), 7)
        self.assertEqual(self.d["frontier_empty_boolean_status"].startswith("RETIRED"), True)

    def test_static_allowlist_passes(self):
        self.assertTrue(self.d["static_allowlist_check"]["passes"])
        self.assertEqual(self.d["static_allowlist_check"]["forbidden_tokens_found"], [])

    def test_runtime_assertion_all_pass(self):
        self.assertTrue(self.d["runtime_assertion_check"]["all_pass"])
        self.assertEqual(len(self.d["runtime_assertion_check"]["rows"]), 10)

    def test_adversarial_test_caught_by_static_check(self):
        self.assertTrue(self.d["adversarial_leakage_test"]["caught_by_static_runtime_assertion"])


class TestIncompleteRootAudit(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_incomplete_root_audit.json").read_text(encoding="utf-8"))

    def test_seven_roots_audited(self):
        self.assertEqual(self.d["n_incomplete_roots"], 7)
        self.assertEqual(len(self.d["audits"]), 7)

    def test_none_interpreted_as_absence(self):
        for row in self.d["audits"].values():
            self.assertFalse(row["interpreted_as_absence"])

    def test_two_of_seven_resolved_by_envelope(self):
        self.assertEqual(self.d["n_resolved_by_envelope_alone"], 2)

    def test_no_root_marked_resume_worthwhile(self):
        decisions = {d["decision"] for d in self.d["continuation_decisions"].values()}
        self.assertNotIn("RESUME_WORTHWHILE", decisions)

    def test_short_family_quotient_not_used_for_merging(self):
        levels = self.d["symmetry_quotient_attempt"]["levels"]
        self.assertFalse(levels["raw"]["collapses"])
        self.assertFalse(levels["canonical"]["collapses"])

    def test_distance_bounds_marked_not_used(self):
        for row in self.d["distance_bounds"].values():
            self.assertIsNone(row["heuristic_upper_estimate_from_siblings"])


if __name__ == "__main__":
    unittest.main()
