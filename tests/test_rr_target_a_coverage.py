"""Round 35 regression tests: the Q1/Q2 split and the coverage discipline.

The single most important thing to protect here is that the capacity bound
never leaks into the Target A question.  It makes the completability search
finite, and it is verified to delete a genuine known Target A boundary, so a
future edit that used it for Q1 would silently produce a false coverage
claim.  Several tests exist only to make that impossible to do quietly.
"""
import json
import unittest
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"


class TestRootLedger(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_22_incomplete_roots.json").read_text(encoding="utf-8"))

    def test_twenty_two_roots_are_fixed(self):
        self.assertEqual(self.d["n_incomplete_roots"], 22)
        self.assertEqual(self.d["n_found_roots"], 6)

    def test_phi_at_every_root_is_ell_plus_one(self):
        for r in self.d["roots"]:
            self.assertEqual(r["phi"], r["root_ell"] + 1, r["prefix_index"])

    def test_every_root_has_exactly_one_R_spent(self):
        for r in self.d["roots"]:
            self.assertEqual(r["r_count"], 1, r["prefix_index"])
            self.assertEqual(r["remaining_R_budget"], 1, r["prefix_index"])
            self.assertEqual(r["F_def"], 1, r["prefix_index"])

    def test_no_state_level_quotient_collapses_the_roots(self):
        inc = [r for r in self.d["roots"] if r["old_status"] == "INCOMPLETE"]
        for key in ("raw_state_hash", "left_s6_canonical_hash",
                    "decorated_continuation_hash"):
            self.assertEqual(len({r[key] for r in inc}), 22, key)
        self.assertEqual(len({tuple(r["resource_signature"]) for r in inc}), 8)
        self.assertEqual(len({r["symbolic_excursion_class"] for r in inc}), 3)

    def test_capacity_bound_kills_no_root_that_reaches_target_a(self):
        for r in self.d["roots"]:
            if r["old_status"] == "FOUND":
                self.assertFalse(r["capacity_dead_at_root"], r["prefix_index"])

    def test_fourteen_roots_are_capacity_dead_at_the_root(self):
        inc = [r for r in self.d["roots"] if r["old_status"] == "INCOMPLETE"]
        self.assertEqual(sum(1 for r in inc if r["capacity_dead_at_root"]), 14)

    def test_hub_is_incomplete_at_every_root(self):
        """Why the CH1/CH2 split cannot be made at the root."""
        for r in self.d["roots"]:
            self.assertFalse(r["hub_complete"], r["prefix_index"])


class TestSearchDiscipline(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_target_a_search_results.json").read_text(encoding="utf-8"))

    def test_q2_exhausted_all_twenty_two_naturally(self):
        rows = self.d["results"]
        self.assertEqual(len(rows), 22)
        for r in rows:
            q2 = r["Q2_completable_target_a"]
            self.assertEqual(q2["status"], "EXHAUSTED_NO_TARGET_A", r["prefix_index"])
            self.assertTrue(q2["frontier_emptied_naturally"], r["prefix_index"])
            self.assertFalse(q2["truncated_by_node_cap"], r["prefix_index"])
            self.assertFalse(q2["truncated_by_time"], r["prefix_index"])

    def test_q1_is_reported_incomplete_and_never_as_coverage(self):
        for r in self.d["results"]:
            self.assertEqual(r["Q1_any_target_a"]["status"], "INCOMPLETE", r["prefix_index"])
        self.assertEqual(self.d["Q1_status_histogram"], {"INCOMPLETE": 22})

    def test_exhausted_is_never_claimed_after_truncation(self):
        for r in self.d["results"]:
            for q in ("Q1_any_target_a", "Q2_completable_target_a"):
                s = r[q]
                if s["status"] == "EXHAUSTED_NO_TARGET_A":
                    self.assertTrue(s["frontier_emptied_naturally"], (r["prefix_index"], q))

    def test_q1_never_used_the_capacity_bound(self):
        """The bound must not appear in any Q1 prune histogram."""
        for r in self.d["results"]:
            self.assertNotIn("capacity_bound_Q2_only",
                             r["Q1_any_target_a"]["prune_histogram"], r["prefix_index"])

    def test_no_new_boundary_so_the_pipeline_did_not_fire(self):
        self.assertEqual(self.d["new_completable_target_a_boundaries"], 0)
        self.assertEqual(self.d["section_14_pipeline"], [])


class TestCoverageCertificate(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_target_a_coverage_certificate.json").read_text(encoding="utf-8"))

    def test_bound_is_refuted_as_a_target_a_prune(self):
        c = self.d["check_1_capacity_bound_scope"]
        self.assertEqual(c["known_boundaries_checked"], 12)
        self.assertGreaterEqual(
            c["boundaries_whose_own_path_the_bound_would_have_pruned"], 1,
            "if this ever reaches 0 the Q1/Q2 split must be re-justified, not dropped")

    def test_all_twelve_known_short_boundaries_re_recognized(self):
        c = self.d["check_2_known_boundary_replay"]
        self.assertEqual(c["short_boundaries_replayed"], 12)
        self.assertEqual(c["re_recognized"], 12)
        self.assertEqual(c["total_known"], 18)

    def test_r2_edge_ell_differs_by_branch(self):
        """Why no single backward predecessor filter exists."""
        d = self.d["check_2_known_boundary_replay"]["R2_edge_ell_by_branch"]
        self.assertEqual(d, {"ell0_R2edge_ell5": 3, "ell4_R2edge_ell0": 9})

    def test_short_family_enumeration_was_actually_truncated(self):
        c = self.d["check_3_short_family_truncation"]
        self.assertEqual(len(c), 5)
        for k, v in c.items():
            self.assertTrue(v["was_actually_truncated"], k)
            self.assertGreater(v["states_dropped_at_the_ceiling"], 0, k)

    def test_outcome_is_C_and_coverage_is_claimed_only_for_q2(self):
        s = self.d["section_16_outcome"]
        self.assertEqual(s["outcome"], "C")
        self.assertTrue(s["Q2_all_frontiers_natural"])
        self.assertIn("ONLY for Q2", s["root_local_coverage_claim"])
        self.assertEqual(s["grades"]["Q1"], "bounded incomplete")

    def test_closure_audit_lists_the_open_gaps(self):
        gaps = self.d["section_17_closure_audit"]
        self.assertGreaterEqual(sum(1 for g in gaps if g["status"].startswith("OPEN")), 5)
        self.assertTrue(any("stop-on-first" in g["gap"] for g in gaps))
        self.assertTrue(any("depth ceiling" in g["gap"] for g in gaps))

    def test_lower_bound_is_not_claimed_to_move(self):
        self.assertTrue(any("872" in s for s in self.d["what_this_does_not_say"]))


if __name__ == "__main__":
    unittest.main()
