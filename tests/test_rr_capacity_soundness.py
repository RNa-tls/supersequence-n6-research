"""Round 38 regression tests: the capacity-helper firewall, the corrected
root ledger, and the five short roots.

The brief names seven required tests; each has a dedicated method below:
  1. long_found_142 regression
  2. helper precondition violation
  3. all retained historical eliminations independently reproduced
  4. 33 = 28 + 5 root ledger
  5. 7 audited continuation roots = 2 newly closed + 5 unresolved
  6. no heuristic bound used as proof
  7. interruption never reported as absence
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


class TestLongFound142Regression(unittest.TestCase):
    """Required test 1: the exact counterexample, recomputed live from the
    engine -- not read back from JSON."""

    @classmethod
    def setUpClass(cls):
        cls.aud = _load("t38_aud", "src/audit_rr_capacity_helpers.py")
        cls.prefixes = json.loads(
            (OUT / "rr_long_excursion_prefixes.json").read_text(encoding="utf-8"))

    def test_helper_undercounts_by_exactly_one_port(self):
        ce = self.aud.formalize_counterexample(self.prefixes)
        self.assertEqual(ce["helper_predicted_ports"], 3)
        self.assertEqual(ce["engine_achieved_ports"], 4)
        self.assertEqual(ce["undercount"], 1)

    def test_precondition_is_genuinely_violated_at_that_root(self):
        st = self.aud.replay_long_root(142, self.prefixes)
        self.assertNotEqual(self.aud.phi(st), 0,
                            "the counterexample is only meaningful where Phi != 0")

    def test_the_undercounted_port_lands_in_a_partially_visited_hexagon(self):
        ce = self.aud.formalize_counterexample(self.prefixes)
        offsets = {o["offset"]: o for o in ce["port_occupancy_from_entry_phase"]}
        self.assertEqual(offsets[3]["hexagon_popcount"], 5,
                         "offset 3 must be the 5-of-6-visited hexagon the helper rejects")
        self.assertFalse(offsets[3]["port_already_pass_start"])

    def test_round37_misstatement_is_recorded_as_corrected(self):
        ce = self.aud.formalize_counterexample(self.prefixes)
        corr = ce["round_37_misstatement_corrected"]
        self.assertIn("2", corr["as_published"])
        self.assertIn("3", corr["actual"])
        self.assertIn("4", corr["actual"])


class TestHelperPreconditionViolation(unittest.TestCase):
    """Required test 2: the firewall must raise, not merely be documented."""

    @classmethod
    def setUpClass(cls):
        cls.aud = _load("t38_aud2", "src/audit_rr_capacity_helpers.py")
        cls.prefixes = json.loads(
            (OUT / "rr_long_excursion_prefixes.json").read_text(encoding="utf-8"))
        cls.preps = json.loads((OUT / "rr_preparation_words.json").read_text(encoding="utf-8"))

    def test_full_segment_helper_raises_at_nonzero_phi(self):
        st = self.aud.replay_long_root(142, self.prefixes)
        with self.assertRaises(self.aud.CapacityPreconditionError):
            self.aud.guarded_true_phase_walk_capacity(st, self.aud.WORDS)

    def test_full_segment_helper_is_allowed_at_phi_zero(self):
        st = self.aud.replay_survivor_state(4, self.preps["results_by_ell"]["4"]["preparations"][0])
        self.assertEqual(self.aud.phi(st), 0)
        v = self.aud.guarded_true_phase_walk_capacity(st, self.aud.WORDS)
        self.assertIsInstance(v, int)

    def test_single_landing_helpers_carry_no_freshness_requirement(self):
        for name in ("coarse_segment_bound", "capacity_slack__port_availability",
                     "root_envelope"):
            h = self.aud.HELPER_TAXONOMY[name]
            self.assertEqual(h["class"], "SOUND_FOR_SINGLE_LANDING")
            self.assertFalse(h["requires_full_hexagon_freshness"], name)

    def test_no_helper_is_left_unclassified(self):
        for name, h in self.aud.HELPER_TAXONOMY.items():
            self.assertIn(h["class"],
                          {"SOUND_FOR_FULL_SEGMENT", "SOUND_FOR_SINGLE_LANDING",
                           "SOUND_UNDER_EXPLICIT_PRECONDITION", "UNSOUND", "UNKNOWN"}, name)
            self.assertNotEqual(h["class"], "UNKNOWN", name)


class TestHistoricalEliminationsReproduced(unittest.TestCase):
    """Required test 3: every retained elimination has an INDEPENDENT,
    freshness-free replacement proof -- not merely a matching answer."""

    def setUp(self):
        self.d = json.loads((OUT / "rr_capacity_callsite_audit.json").read_text(encoding="utf-8"))

    def test_nothing_was_retracted(self):
        self.assertEqual(self.d["n_retracted"], 0)
        self.assertEqual(self.d["n_retained"], 9)

    def test_all_18_boundaries_satisfy_the_precondition(self):
        rows = self.d["historical_eliminations"]
        self.assertEqual(len(rows), 18)
        for r in rows:
            self.assertTrue(r["precondition_Phi_eq_0_holds"], r["raw_hash"])
            self.assertEqual(r["Phi"], 0)

    def test_every_retained_elimination_has_a_freshness_free_proof(self):
        """The load-bearing check: no result may be retained merely because
        the freshness-dependent answer happened to match."""
        for r in self.d["historical_eliminations"]:
            if r["recorded_verdict"] != "CAPACITY_IMPOSSIBLE":
                continue
            self.assertTrue(r["freshness_INDEPENDENT_eliminates"],
                            f"{r['provenance']} retained without an independent proof")

    def test_both_provenances_are_covered(self):
        provs = {r["provenance"] for r in self.d["historical_eliminations"]}
        self.assertIn("short_family", provs)
        self.assertEqual(sum(1 for r in self.d["historical_eliminations"]
                             if r["provenance"].startswith("long_found_")), 6)


class TestRootLedgerCounts(unittest.TestCase):
    """Required tests 4 and 5: the corrected count units."""

    def setUp(self):
        self.env = json.loads((OUT / "rr_root_capacity_envelopes.json").read_text(encoding="utf-8"))
        self.audit = json.loads((OUT / "rr_incomplete_root_audit.json").read_text(encoding="utf-8"))
        self.resumed = json.loads(
            (OUT / "rr_target_a_resumed_frontiers.json").read_text(encoding="utf-8"))["results"]

    def test_33_equals_28_plus_5_q2_split(self):
        rows = self.env["rows"]
        self.assertEqual(len(rows), 33)
        closed = sum(1 for r in rows if r["certified_q2_impossible"])
        unresolved = sum(1 for r in rows if not r["certified_q2_impossible"])
        self.assertEqual(closed, 28)
        self.assertEqual(unresolved, 5)
        self.assertEqual(closed + unresolved, 33)

    def test_33_equals_26_plus_7_q1_split(self):
        statuses = [r["status"] for r in self.resumed.values()]
        self.assertEqual(len(statuses), 33)
        found = sum(1 for s in statuses if s == "FOUND_TARGET_A")
        timeout = sum(1 for s in statuses if s == "INCOMPLETE_TIMEOUT")
        self.assertEqual(found, 26)
        self.assertEqual(timeout, 7)
        self.assertEqual(found + timeout, 33)

    def test_7_audited_equals_2_newly_closed_plus_5_unresolved(self):
        self.assertEqual(self.audit["n_incomplete_roots"], 7)
        self.assertEqual(self.audit["n_resolved_by_envelope_alone"], 2)
        env_res = self.audit["envelope_theorem_resolution"]
        still_open = sum(1 for r in env_res.values() if not r["certified_q2_impossible"])
        self.assertEqual(still_open, 5)
        self.assertEqual(self.audit["n_resolved_by_envelope_alone"] + still_open, 7)

    def test_the_two_newly_closed_are_the_long_q1_roots(self):
        env_res = self.audit["envelope_theorem_resolution"]
        closed = {k for k, v in env_res.items() if v["certified_q2_impossible"]}
        self.assertEqual(closed, {"long_q1_140", "long_q1_178"})


class TestShortRoots(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads((OUT / "rr_short_root_ledger.json").read_text(encoding="utf-8"))
        self.defects = json.loads(
            (OUT / "rr_short_root_defect_bounds.json").read_text(encoding="utf-8"))
        self.res = json.loads(
            (OUT / "rr_short_root_resource_results.json").read_text(encoding="utf-8"))

    def test_five_roots_not_merged(self):
        self.assertEqual(self.ledger["n_roots"], 5)
        self.assertEqual(self.ledger["distinct_raw_state_hashes"], 5)
        self.assertEqual(self.ledger["distinct_canonical_decorated_hashes"], 5)
        self.assertFalse(self.ledger["merged_on_resource_signature"])

    def test_margin_decomposition_is_an_exact_identity(self):
        for row in self.ledger["rows"]:
            d = self.ledger["margin_decomposition"][row["root_id"]]
            self.assertEqual(d["identity_total"], row["root_envelope_margin"])
            self.assertEqual(
                d["M_root"] + d["preserving_slack"] + d["reentry_slack"]
                + d["terminal_slack"] + d["residual_R_cap_slack"],
                d["identity_total"])
            self.assertEqual(row["root_envelope_margin"], 14)

    def test_initial_capacity_is_five_not_zero(self):
        """Guards the entry_already_occupied bug: the walk stands on its own
        entry port, which must not be counted as a blocker."""
        for key, r in self.defects["rows"].items():
            self.assertEqual(r["initial_segment_capacity"], 5, key)
            self.assertEqual(r["initial_segment_defect"], 0, key)

    def test_defect_theorem_does_not_close_any_root(self):
        self.assertEqual(self.defects["n_roots_closed_by_defect_theorem"], 0)
        for key, r in self.defects["rows"].items():
            self.assertFalse(r["D_min_exceeds_margin"], key)

    def test_resource_model_feasible_so_unresolved(self):
        for r in self.res["rows"]:
            self.assertTrue(r["resource_model_feasible"], r["root_id"])
            self.assertEqual(r["classification"], "STRUCTURAL_SURVIVOR", r["root_id"])

    def test_feasibility_never_reported_as_a_witness(self):
        for r in self.res["rows"]:
            self.assertIn("UNRESOLVED", r["feasibility_is_not_a_witness"].upper())
        self.assertEqual(self.res["model"]["interpretation"]["feasible"],
                         "UNRESOLVED -- never a continuation witness")


class TestNoHeuristicUsedAsProof(unittest.TestCase):
    """Required test 6."""

    def setUp(self):
        self.res = json.loads(
            (OUT / "rr_short_root_resource_results.json").read_text(encoding="utf-8"))
        self.audit = json.loads((OUT / "rr_incomplete_root_audit.json").read_text(encoding="utf-8"))

    def test_cost_benefit_note_is_explicitly_labelled_heuristic(self):
        note = self.res["heuristic_cost_benefit_note"]
        self.assertIn("HEURISTIC", note["label"])
        self.assertIn("not a proof", note["label"])
        self.assertIn("never used to prune", note["label"])

    def test_no_root_closed_without_a_certificate(self):
        """A root may be classified impossible only via the envelope or the
        resource model -- never via the heuristic."""
        for r in self.res["rows"]:
            if r["classification"] in ("ROOT_ENVELOPE_IMPOSSIBLE",
                                       "SYMBOLIC_RESOURCE_IMPOSSIBLE"):
                self.assertTrue(r["envelope_certifies_impossible"]
                                or not r["resource_model_feasible"]
                                or r["D_min_exceeds_margin"], r["root_id"])

    def test_sibling_derived_distance_estimates_were_not_used(self):
        for row in self.audit["distance_bounds"].values():
            self.assertIsNone(row["heuristic_upper_estimate_from_siblings"])


class TestInterruptionNeverAbsence(unittest.TestCase):
    """Required test 7."""

    def setUp(self):
        self.audit = json.loads((OUT / "rr_incomplete_root_audit.json").read_text(encoding="utf-8"))
        self.resumed = json.loads(
            (OUT / "rr_target_a_resumed_frontiers.json").read_text(encoding="utf-8"))["results"]

    def test_no_timeout_row_is_interpreted_as_absence(self):
        for key, row in self.audit["audits"].items():
            self.assertFalse(row["interpreted_as_absence"], key)

    def test_no_timed_out_root_claims_exhaustion(self):
        for key, r in self.resumed.items():
            if r["status"] == "INCOMPLETE_TIMEOUT":
                self.assertFalse(r["frontier_emptied_naturally"], key)
            if r["status"] == "EXHAUSTED_NO_TARGET_A":
                self.assertTrue(r["frontier_emptied_naturally"], key)

    def test_zero_hits_at_a_timeout_root_is_not_a_zero_boundary_claim(self):
        """The 5 short roots found 0 boundaries -- that must be recorded as
        a budget fact, with the root still classified a survivor."""
        res = json.loads((OUT / "rr_short_root_resource_results.json").read_text(encoding="utf-8"))
        for r in res["rows"]:
            self.assertEqual(r["continuation_search_status"], "INCOMPLETE_TIMEOUT")
            self.assertEqual(r["classification"], "STRUCTURAL_SURVIVOR")


if __name__ == "__main__":
    unittest.main()
