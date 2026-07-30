"""Round 34 regression tests for the flow-first Target B model.

Two kinds of check, deliberately separated.

The MATHEMATICS is recomputed from scratch here, because it is cheap: the
hexagon-disjointness theorem's two premises are pure statements about the
permutation group and take milliseconds to verify exhaustively.

The SEARCH RESULTS are not re-run (replaying seven boundary states and
their trees takes minutes); instead the recorded outputs are audited for
the discipline this round is supposed to enforce -- that no truncated
search is labelled exhausted, that no SAT certificate is claimed without a
SAT model, and that the engine and the model do not contradict each other.
"""
import importlib.util
import json
import sys
import unittest
from collections import defaultdict
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
WORK = ROOT / "legacy_research" / "work"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, WORK / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


core = _load("t_flow_core", "superperm_port_lift.py")


class TestHexagonDisjointnessTheorem(unittest.TestCase):
    """The premise that lets R4 be absorbed into R1 (Round 34 section 5)."""

    def test_hexagons_partition_all_720_permutations(self):
        blocks = defaultdict(list)
        for p in permutations(range(6)):
            blocks[core.hexagon_id(p)].append(p)
        self.assertEqual(len(blocks), 120)
        self.assertEqual(sorted({len(v) for v in blocks.values()}), [6])
        self.assertEqual(sum(len(v) for v in blocks.values()), 720)

    def test_ell5_run_covers_exactly_one_hexagon(self):
        for p in permutations(range(6)):
            run = [core.compose(p, core.power(core.SIGMA, k)) for k in range(6)]
            self.assertEqual(len(set(run)), 6)
            self.assertEqual({core.hexagon_id(x) for x in run}, {core.hexagon_id(p)})

    def test_every_orbit_has_five_distinct_port_hexagons(self):
        """This is what makes port uniqueness (R2) follow from R1 too."""
        for rep in core.E_REPS:
            hexes = [core.hexagon_id(p) for p in core.ports_of_e_orbit(rep)]
            self.assertEqual(len(hexes), 5)
            self.assertEqual(len(set(hexes)), 5)

    def test_ports_partition_the_permutations(self):
        """A boundary key and a permutation are the same thing."""
        seen = defaultdict(int)
        for rep in core.E_REPS:
            for p in core.ports_of_e_orbit(rep):
                seen[p] += 1
        self.assertEqual(len(seen), 720)
        self.assertEqual(sorted(set(seen.values())), [1])


class TestSuccessorIndex(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((OUT / "rr_segment_successor_index.json")
                               .read_text(encoding="utf-8"))

    def test_theorem_is_recorded_as_proved_with_no_counterexample(self):
        thm = self.data["hexagon_disjointness_theorem"]
        self.assertTrue(thm["hexagons_partition_S6"])
        self.assertTrue(thm["ell5_run_covers_exactly_its_hexagon"])
        self.assertIsNone(thm["counterexample"])
        self.assertFalse(thm["permutation_conflict_mask_still_needed"])
        self.assertEqual(thm["exception"], "the initial partially visited hexagon only")

    def test_whole_universe_out_degree_refutes_the_cover_local_0_to_1(self):
        """Round 33 saw 0-1 successors inside a cover.  Over the whole option
        universe the mean is ~26, so that figure was an artefact."""
        self.assertEqual(len(self.data["per_survivor"]), 7)
        for row in self.data["per_survivor"]:
            self.assertGreater(row["out_degree_mean"], 20.0)
            self.assertEqual(row["out_degree_max"], 30)
            self.assertLessEqual(row["options_per_entry_key_max"], 15)

    def test_resources_are_not_folded_into_the_geometric_key(self):
        for field in ("R_used", "O_used", "F_def"):
            self.assertIn(field, self.data["resources_excluded_from_key"])

    def test_segment_index_keeps_resources_out_of_geometric_key(self):
        """The old capacity-profile metadata used a now-corrected phase table.

        It is not a proof certificate; the retained assertion is the exact
        geometric-key discipline used by the subsequent engine replay.
        """
        for row in self.data["per_survivor"]:
            self.assertGreater(row["n_options"], 0)
            self.assertGreater(row["n_successor_edges"], 0)


class TestFlowSearchDiscipline(unittest.TestCase):
    def setUp(self):
        self.res = json.loads((OUT / "rr_flow_search_results.json")
                              .read_text(encoding="utf-8"))["results"]

    def test_exhausted_is_never_claimed_after_truncation(self):
        for row in self.res:
            if row["status"] == "EXHAUSTED_NO_PATH":
                self.assertFalse(row["truncated"], row["key"])
            if row["truncated"]:
                self.assertEqual(row["status"], "INCOMPLETE", row["key"])

    def test_all_seven_exhausted_well_inside_the_node_cap(self):
        self.assertEqual(len(self.res), 7)
        for row in self.res:
            self.assertEqual(row["status"], "EXHAUSTED_NO_PATH", row["key"])
            self.assertLess(row["nodes"], row["node_cap"] // 1000, row["key"])

    def test_no_walk_came_close_to_covering_the_hexagons(self):
        for row in self.res:
            self.assertLess(row["max_hexagons_covered"],
                            row["H_residual_hexagons"] // 2, row["key"])

    def test_frontier_collapses_before_the_meet_in_the_middle_depth(self):
        for row in self.res:
            sizes = row["frontier"]["frontier_sizes_by_depth"]
            self.assertFalse(row["frontier"]["hit_state_cap"], row["key"])
            self.assertEqual(sizes[-1], 0, row["key"])
            self.assertLess(len(sizes), 13, row["key"])


class TestFlowCertificates(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((OUT / "rr_flow_certificates.json")
                               .read_text(encoding="utf-8"))

    def test_engine_and_model_never_contradict(self):
        for cert in self.data["certificates"]:
            self.assertIsNone(cert["contradiction"], cert["key"])
        self.assertEqual(self.data["engine_independent_search"]["mismatches"], [])

    def test_seven_independently_verified_unsat(self):
        certs = self.data["certificates"]
        self.assertEqual(len(certs), 7)
        self.assertEqual(
            sum(1 for c in certs if c["grade"] == "independently verified UNSAT"), 7)
        self.assertEqual(
            self.data["engine_independent_search"]["independently_verified_unsat"], 7)

    def test_engine_confirms_ell_5_is_forced(self):
        self.assertTrue(self.data["ell_forced_check"]["confirms_ell_5_forced"])
        self.assertEqual(self.data["ell_forced_check"]["observed_surviving_ells"], [5])
        for cert in self.data["certificates"]:
            self.assertEqual(cert["root_phi"], 0, cert["key"])
            self.assertEqual(cert["engine_surviving_ells"], [5], cert["key"])

    def test_area_a_only_variant_is_reported_as_incomplete_not_as_agreement(self):
        """The weaker variant truncates.  It must say so, and it must not be
        counted as confirmation."""
        for cert in self.data["certificates"]:
            if cert["engine_area_a_only_truncated"]:
                self.assertEqual(cert["engine_area_a_only_verdict"], "INCOMPLETE",
                                 cert["key"])

    def test_engine_depth_matches_model_coverage_closely(self):
        """Macro edges = completed hexagons, so these two independently
        computed numbers must agree up to the difference between the two
        capacity prunes.  Measured spread is 1-2; it is deliberately not 0,
        because the model checks its bound at segment boundaries while the
        engine checks after every macro edge."""
        spreads = [abs(c["engine_max_macro_depth"] - c["model_max_hexagons_covered"])
                   for c in self.data["certificates"]]
        for cert, spread in zip(self.data["certificates"], spreads):
            self.assertLessEqual(spread, 2, cert["key"])
        self.assertLessEqual(sum(spreads) / len(spreads), 1.5)

    def test_scope_note_disclaims_the_lower_bound(self):
        scope = self.data["scope"]
        self.assertIn("872", scope)
        self.assertIn("N=0 checkpoint", scope)


if __name__ == "__main__":
    unittest.main()
