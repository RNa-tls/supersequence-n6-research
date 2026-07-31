"""Round-35 controls for the decorated Target-A traversal.

These are transition/certificate controls, not a claim that the 22 roots have
already been exhaustively searched.  Positive node limits below deliberately
produce INCOMPLETE output and exercise checkpoint discipline.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_search():
    path = ROOT / "src" / "search_rr_target_a_exhaustive.py"
    spec = importlib.util.spec_from_file_location("test_round35_search", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rr = load_search()


class TestRound35Roots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = rr.load_audited_roots(
            ROOT / "outputs" / "rr_target_a_22_root_ledger.json",
            ROOT / "outputs" / "rr_long_excursion_prefixes.json",
        )

    def test_exactly_22_audited_roots_reconstruct(self):
        self.assertEqual(len(self.records), 22)
        self.assertEqual([r["root_id"] for r in self.records],
                         sorted((r["root_id"] for r in self.records),
                                key=lambda x: int(x.rsplit("-", 1)[1])))
        for record in self.records:
            state, decoration = rr.initial_decoration(record)
            self.assertEqual(rr.state_hash(state), record["post_return_state_hash"])
            self.assertEqual(decoration.r_count, 1)

    def test_frozen_old_bounded_histogram_is_6_22_0(self):
        data = json.loads((ROOT / "outputs" / "rr_long_prefix_extension_results.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(data["status_histogram"], {"FOUND": 6, "INCOMPLETE": 22})
        self.assertEqual(sum(r["status"] == "EXHAUSTED_IMPOSSIBLE" for r in data["results"]), 0)

    def test_key_audit_passes_for_all_roots(self):
        audit = rr.run_key_audit(self.records)
        self.assertTrue(audit["passed"])
        self.assertTrue(audit["r1_target_required_for_chaining_reporting"])
        self.assertEqual(audit["roots_checked"], 22)


class TestRound35Recognizer(unittest.TestCase):
    @staticmethod
    def known_record():
        data = json.loads((ROOT / "outputs" / "rr_long_excursion_prefixes.json")
                          .read_text(encoding="utf-8"))
        record = dict(data["prefixes"][4])
        record["root_id"] = "known-R27-prefix-4"
        return record

    def test_known_found_witness_is_discoverable_and_known(self):
        result = rr.search_root(self.known_record(), node_limit=8, checkpoint=None)
        self.assertEqual(result["status"], "INCOMPLETE")  # the artificial cap is not proof mode
        self.assertGreaterEqual(len(result["target_a_boundaries"]), 1)
        boundary = result["target_a_boundaries"][0]
        self.assertTrue(boundary["is_target_a"])
        self.assertTrue(all(boundary["conditions"].values()))
        self.assertEqual(boundary["target_b_dispatch"]["classification"], "KNOWN_BOUNDARY")

    def test_wrong_r_count_is_not_target_a(self):
        record = self.known_record()
        state, decoration = rr.initial_decoration(record)
        old = json.loads((ROOT / "outputs" / "rr_long_prefix_extension_results.json")
                         .read_text(encoding="utf-8"))
        witness = next(r for r in old["results"] if r["prefix_index"] == 4)["same_component_witnesses"][0]
        for step in witness["extension_trace"]:
            ell = int(step["label"].split(";", 1)[0].split("^")[1])
            label = step["label"].split(";", 1)[1]
            for _ in range(ell):
                state = rr.exact.extend(state, rr.W1).state
            transition = rr.exact.extend(state, rr.MOVE[label])
            after = rr.advance_decoration(state, transition, decoration)
            if rr.joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit) == "R":
                no_r1 = rr.Decoration(decoration.root_id, decoration.root_ell, decoration.o_star,
                                      decoration.hub_id, decoration.macro_index, (),
                                      decoration.hub_touch_count, decoration.completer)
                miss = rr.target_a_recognizer(state, transition, no_r1, after)
                self.assertFalse(miss["is_target_a"])
                self.assertFalse(miss["conditions"]["exactly_two_R_events"])
                return
            decoration, state = after, transition.state
        self.fail("known trace did not reach R2")

    def test_non_r_boundary_is_not_target_a(self):
        record = self.known_record()
        state, decoration = rr.initial_decoration(record)
        edge = next(edge for edge, collision in rr.iter_raw_macro_candidates(state)
                    if collision is None and edge.joint.move.label == "w2:10")
        after = rr.advance_decoration(edge.run.state, edge.joint, decoration)
        miss = rr.target_a_recognizer(edge.run.state, edge.joint, decoration, after)
        self.assertFalse(miss["is_target_a"])
        self.assertFalse(miss["conditions"]["immediately_after_R2"])

    def test_ch_branch_classifier_and_real_ch2_update(self):
        # The two branch formulas are pure decoration invariants.  CH1 is a
        # same-index R completion; CH2 is a later Z2 completion after R1.
        r1 = rr.REvent(5, "R", 1, 0, 2, 0)
        ch1 = rr.Decoration("synthetic", 0, 0, rr.HUB, 5, (r1,), 1,
                            rr.Completer(5, "R", 1, 0, 2, 0))
        ch2 = rr.Decoration("synthetic", 0, 0, rr.HUB, 6, (r1,), 1,
                            rr.Completer(6, "Z2", 3, 1, 4, 2))
        self.assertEqual(ch1.branch, "CH1")
        self.assertEqual(ch2.branch, "CH2")

        records = rr.load_audited_roots(
            ROOT / "outputs" / "rr_target_a_22_root_ledger.json",
            ROOT / "outputs" / "rr_long_excursion_prefixes.json",
        )
        record = next(row for row in records if row["root_id"] == "R27-prefix-6")
        state, decoration = rr.initial_decoration(record)
        edge = next(edge for edge, collision in rr.iter_raw_macro_candidates(state)
                    if collision is None and edge.label == "rot^5;w2:10")
        after = rr.advance_decoration(edge.run.state, edge.joint, decoration)
        self.assertEqual(after.branch, "CH2")


class TestRound35CheckpointAndDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = rr.load_audited_roots(
            ROOT / "outputs" / "rr_target_a_22_root_ledger.json",
            ROOT / "outputs" / "rr_long_excursion_prefixes.json",
        )[0]

    def test_interruption_is_incomplete_and_checkpoint_is_parseable(self):
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "root.json"
            result = rr.search_root(self.record, node_limit=1, checkpoint=checkpoint,
                                    checkpoint_every=1)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertTrue(result["interrupted_by_node_limit"])
            self.assertFalse(result["frontier_empty"])
            config = rr.checkpoint_config(self.record, 1, None)
            frontier, seen, _stats, _boundaries, _lineage = rr.load_checkpoint(checkpoint, config)
            self.assertEqual(len(frontier), result["stats"]["frontier_size"])
            self.assertEqual(len(seen), result["stats"]["unique_decorated_keys"])

    def test_checkpoint_resume_matches_fresh_bounded_diagnostic(self):
        # A depth bound is explicitly diagnostic.  It gives a finite root for
        # testing the resume parser without calling a capped result exhaustive.
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "root.json"
            config = rr.checkpoint_config(self.record, 0, 1)
            state, decoration = rr.initial_decoration(self.record)
            rr.write_checkpoint(checkpoint, config, [(0, state, decoration, tuple())],
                                {rr.decorated_key(state, decoration)},
                                {"expanded": 0, "exact_states": [repr(state.stable_key())],
                                 "memo_hits": 0, "prunes": {}, "CH1_nodes": 0,
                                 "CH2_nodes": 0, "undecided_nodes": 0, "other_nodes": 0,
                                 "branch_transitions": {}, "max_macro_depth": 0,
                                 "checkpoint_count": 0}, [], [])
            resumed = rr.search_root(self.record, node_limit=0, max_depth=1,
                                     checkpoint=checkpoint, checkpoint_every=1,
                                     resume=checkpoint)
            fresh = rr.search_root(self.record, node_limit=0, max_depth=1,
                                   checkpoint=None)
            self.assertEqual(resumed["status"], "INCOMPLETE")
            self.assertEqual(resumed["stats"]["expanded"], fresh["stats"]["expanded"])
            self.assertEqual(resumed["stats"]["unique_decorated_keys"],
                             fresh["stats"]["unique_decorated_keys"])

    def test_registry_has_no_heuristic_prune(self):
        names = {row["name"] for row in rr.PRUNE_REGISTRY}
        self.assertNotIn("beam", names)
        self.assertNotIn("heuristic_depth", names)
        self.assertIn("exact_permutation_collision", names)
        self.assertIn("area_a_necessary_conditions", names)


if __name__ == "__main__":
    unittest.main()
