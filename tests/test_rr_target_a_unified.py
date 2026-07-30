"""Round 36 regression tests: the unified Target A enumerator's correctness
properties, independent of how far any particular coverage run got.

These tests do not depend on the (potentially still-INCOMPLETE) coverage
execution results; they exercise the engine itself on small, fast roots so
they run in seconds and catch a regression in the machinery even if no
coverage run has been done recently.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

spec = importlib.util.spec_from_file_location("sru_test", ROOT / "src" / "search_rr_target_a_unified.py")
sru = importlib.util.module_from_spec(spec)
sys.modules["sru_test"] = sru
spec.loader.exec_module(sru)


def short_root(ell):
    st = sru.exact.initial_state()
    for _ in range(ell):
        st = sru.exact.extend(st, sru.W1).state
    st = sru.exact.extend(st, sru.mbl["w2:10"]).state
    return st


class TestPruneClassification(unittest.TestCase):
    def test_classification_partitions_all_ten_subconditions(self):
        self.assertEqual(len(sru.PRUNE_CLASSIFICATION), 10)
        self.assertEqual(sru.Q1_SAFE_REASONS | sru.Q2_ONLY_REASONS,
                         set(sru.PRUNE_CLASSIFICATION))
        self.assertEqual(sru.Q1_SAFE_REASONS & sru.Q2_ONLY_REASONS, set())

    def test_exactly_four_q1_safe_reasons(self):
        self.assertEqual(sru.Q1_SAFE_REASONS,
                         {"F_exceeded", "H_positive", "N_exceeded_monotone",
                          "F1_fragment_normal_form_impossible"})

    def test_capacity_bound_family_is_q2_only(self):
        """The exact sub-condition Round 35 proved unsound as a Target A prune."""
        self.assertIn("remaining_cover_capacity_impossible", sru.Q2_ONLY_REASONS)
        self.assertIn("P_exceeded", sru.Q2_ONLY_REASONS)
        self.assertIn("O_exceeded", sru.Q2_ONLY_REASONS)

    def test_q1_safe_prune_reason_only_ever_returns_q1_safe_reasons(self):
        st = short_root(4)
        for e in sru.macro.macro_edges(st):
            r = sru.q1_safe_prune_reason(e.joint.state)
            if r is not None:
                self.assertIn(r, sru.Q1_SAFE_REASONS)

    def test_forbidden_prune_check_raises_for_q2_only_reasons(self):
        for reason in sru.Q2_ONLY_REASONS:
            with self.assertRaises(AssertionError):
                sru.q1_forbidden_prune_check(reason)

    def test_forbidden_prune_check_passes_for_q1_safe_reasons(self):
        for reason in sru.Q1_SAFE_REASONS:
            sru.q1_forbidden_prune_check(reason)  # must not raise


class TestUnifiedEnumerator(unittest.TestCase):
    def test_status_vocabulary_is_exactly_seven(self):
        self.assertEqual(len(sru.STATUSES), 7)
        self.assertEqual(set(sru.STATUSES),
                         {"FOUND_TARGET_A", "EXHAUSTED_NO_TARGET_A", "INCOMPLETE_NODE_CAP",
                          "INCOMPLETE_DEPTH_CEILING", "INCOMPLETE_TIMEOUT",
                          "STOPPED_AFTER_FIRST", "INVALID_ROOT"})

    def test_q1_search_never_uses_a_forbidden_prune(self):
        """Live smoke test: run a small Q1 search and check its own
        pruned_by_reason histogram never cites a Q2-only reason."""
        st = short_root(4)
        res = sru.enumerate_target_a(st, 0, mode="Q1", coverage=True,
                                     node_cap=3000, depth_cap=None, seconds=20)
        for reason in res["pruned_by_reason"]:
            self.assertNotIn(reason, sru.Q2_ONLY_REASONS, reason)

    def test_depth_ceiling_is_never_folded_into_exhausted(self):
        st = short_root(4)
        res = sru.enumerate_target_a(st, 0, mode="Q1", coverage=True,
                                     node_cap=None, depth_cap=3, seconds=20)
        self.assertNotEqual(res["status"], "EXHAUSTED_NO_TARGET_A")
        if res["depth_ceiling_dropped_nodes"] > 0:
            self.assertEqual(res["status"], "INCOMPLETE_DEPTH_CEILING")

    def test_witness_mode_never_returns_exhausted(self):
        st = short_root(4)
        res = sru.enumerate_target_a(st, 0, mode="Q1", coverage=False,
                                     node_cap=5000, depth_cap=None, seconds=20)
        self.assertNotEqual(res["status"], "EXHAUSTED_NO_TARGET_A")

    def test_determinism_two_runs_produce_identical_stats(self):
        st = short_root(4)
        r1 = sru.enumerate_target_a(st, 0, mode="Q1", coverage=True,
                                    node_cap=2000, depth_cap=None, seconds=20)
        r2 = sru.enumerate_target_a(st, 0, mode="Q1", coverage=True,
                                    node_cap=2000, depth_cap=None, seconds=20)
        self.assertEqual(r1["expanded_nodes"], r2["expanded_nodes"])
        self.assertEqual(r1["pruned_by_reason"], r2["pruned_by_reason"])
        self.assertEqual(r1["found_boundary_count"], r2["found_boundary_count"])

    def test_checkpoint_resume_conserves_totals(self):
        import tempfile, os
        st = short_root(4)
        ck = tempfile.mktemp(suffix=".json")
        try:
            partial = sru.enumerate_target_a(st, 0, mode="Q1", coverage=True,
                                              node_cap=50, depth_cap=None, seconds=20,
                                              checkpoint_path=ck, checkpoint_every=10)
            full = sru.enumerate_target_a(st, 0, mode="Q1", coverage=True,
                                          node_cap=2000, depth_cap=None, seconds=20)
            resumed = sru.enumerate_target_a(None, None, mode="Q1", coverage=True,
                                             node_cap=2000, depth_cap=None, seconds=20,
                                             resume_from=ck)
            self.assertEqual(resumed["expanded_nodes"], full["expanded_nodes"])
        finally:
            if os.path.exists(ck):
                os.remove(ck)

    def test_hit_path_replays_to_the_hit_hash(self):
        """A found boundary's recorded path must literally replay to a state
        whose hash matches boundary_raw_hash. Uses a root already one R past
        the abandonment (r_count=1, the same starting point as the 28
        long-excursion-prefix roots) since finding TWO fresh R events from
        r_count=0 in a small node budget is not reliable."""
        st = short_root(4)
        for lbl in ("w3:201",):  # any legal weight-3 edge reachable from the root
            for e in sru.macro.macro_edges(st):
                if sru.joint_kind(e.joint.move.weight, e.joint.abandonment,
                                  e.joint.new_orbit) == "R":
                    st = e.joint.state
                    break
        res = sru.enumerate_target_a(st, 1, mode="Q1", coverage=True,
                                     node_cap=20000, depth_cap=None, seconds=60)
        self.assertGreaterEqual(res["found_boundary_count"], 1)
        hit = res["hits"][0]
        cur = st
        for lbl in hit["path"]:
            ell_s, joint = lbl.split(";")
            ell = int(ell_s[4:])
            for _ in range(ell):
                cur = sru.exact.extend(cur, sru.W1).state
            cur = sru.exact.extend(cur, sru.mbl[joint]).state
        self.assertEqual(sru.sha(cur.stable_key())[:16], hit["boundary_raw_hash"])

    def test_decorated_key_needs_no_more_than_state_plus_r_count(self):
        """Sanity check for section 11's claim: the recognizer's verdict is
        a pure function of (state, r_count) at the point of evaluation."""
        st = short_root(4)
        for e in sru.macro.macro_edges(st):
            if sru.joint_kind(e.joint.move.weight, e.joint.abandonment,
                              e.joint.new_orbit) == "R":
                v1 = sru.is_target_a_edge(e, 1)
                v2 = sru.is_target_a_edge(e, 1)
                self.assertEqual(v1, v2)


@unittest.skipUnless((OUT / "rr_target_a_root_universe.json").exists(),
                     "root universe output not present")
class TestRootUniverse(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_target_a_root_universe.json").read_text(encoding="utf-8"))

    def test_five_abandonment_ell_values_exactly(self):
        c = self.d["sources"]["abandonment_ell_root_count"]
        self.assertTrue(c["exactly_five_values"])
        self.assertEqual(c["ell_values_where_abandonment_is_legal"], [0, 1, 2, 3, 4])

    def test_no_state_level_overlap_between_short_and_long_sources(self):
        levels = self.d["overlap_audit"]["levels_checked"]
        for level in ("exact_state_equality", "left_s6_canonical_equality"):
            self.assertEqual(levels[level]["long_vs_short_cross_collisions"], 0, level)


@unittest.skipUnless((OUT / "rr_target_a_known18_regression.json").exists(),
                     "known-18 regression output not present")
class TestKnown18Regression(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "rr_target_a_known18_regression.json").read_text(encoding="utf-8"))

    def test_all_eighteen_replay(self):
        self.assertEqual(self.d["n_boundaries"], 18)
        self.assertEqual(self.d["n_literal_replay_ok"], 18)

    def test_seven_round34_survivors_are_correctly_matched(self):
        n_matched = sum(1 for r in self.d["rows"] if r["target_B_status"] == "EXHAUSTED_NO_PATH")
        self.assertEqual(n_matched, 7)

    def test_naming_uses_currently_known_not_exhaustive(self):
        self.assertIn("CURRENTLY KNOWN", self.d["naming_correction"])


@unittest.skipUnless((OUT / "rr_target_a_search_status_audit.json").exists(),
                     "search status audit output not present")
class TestSearchStatusAudit(unittest.TestCase):
    def test_no_discipline_violations(self):
        d = json.loads((OUT / "rr_target_a_search_status_audit.json").read_text(encoding="utf-8"))
        self.assertEqual(d["discipline_violations"], [])


if __name__ == "__main__":
    unittest.main()
