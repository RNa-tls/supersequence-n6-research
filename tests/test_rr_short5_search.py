"""Round-40 controls for the five bare short-root Target-A searches.

These tests audit mapping, key identity, and no-helper provenance.  They do
not start a continuation search; the proof runs are invoked explicitly by the
short5 driver with node-limit zero.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_short5():
    path = ROOT / "src" / "search_rr_short5_exact.py"
    spec = importlib.util.spec_from_file_location("test_short5_driver", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


short5 = load_short5()


class Short5RootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = short5.short_root_records()

    def test_exactly_the_five_bare_round37_roots_are_mapped(self):
        self.assertEqual([record["root_id"] for record in self.records],
                         [f"short_ell{i}" for i in range(5)])
        self.assertEqual([record["literal_joint_word"] for record in self.records],
                         [[] for _ in range(5)])
        self.assertEqual([record["r_count"] for record in self.records], [0] * 5)
        for record in self.records:
            state, decoration = short5.rr.initial_decoration(record)
            self.assertEqual(short5.rr.state_hash(state), record["post_return_state_hash"])
            self.assertEqual(decoration.r_count, 0)

    def test_manifest_matches_frozen_round37_paths(self):
        round37 = json.loads((ROOT / "outputs" / "rr_round37_envelope_independent_verification.json")
                             .read_text(encoding="utf-8"))
        paths = {row["root_id"]: row["root_literal_path"] for row in round37["rows"]}
        for record in self.records:
            self.assertEqual(record["round37_literal_path"], paths[record["root_id"]])

    def test_short_state_key_audit_passes(self):
        audit = short5.audit_short_state_key(self.records)
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["roots_checked"], 5)
        # This is the regression for the former scope-completeness bug: the
        # audited universe must actually enter r_count=1, not only verify the
        # pre-R states from which it is reachable.
        self.assertGreater(audit["r1_states_examined"], 0)
        self.assertGreater(audit["r_count_histogram"].get(1, 0), 0)
        self.assertGreater(audit["post_R1_deliberate_duplicate_groups"], 0)
        self.assertEqual(audit["post_R1_key_collision_mismatches"], [])
        self.assertEqual(audit["key_collision_mismatches"], [])
        self.assertEqual(audit["json_roundtrip_failures"], [])

    def test_legal_first_r_edge_is_enqueued_for_every_short_root(self):
        for record in self.records:
            state, decoration = short5.rr.initial_decoration(record)
            candidates = []
            for edge, collision in short5.rr.iter_raw_macro_candidates(state):
                if collision is not None or edge is None:
                    continue
                if short5.rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment,
                                        edge.joint.new_orbit) != "R":
                    continue
                verdict, after, recognition = short5.rr.evaluate_edge(state, decoration, edge)
                candidates.append((verdict, after, recognition))
            self.assertTrue(candidates, record["root_id"])
            accepted = [(after, recognition) for verdict, after, recognition in candidates
                        if verdict == "child"]
            self.assertTrue(accepted, record["root_id"])
            for after, recognition in accepted:
                self.assertIsNone(recognition)
                self.assertIsNotNone(after)
                self.assertEqual(after.r_count, 1)

    def test_long_root_r2_is_recognized_on_edge_and_never_enqueued(self):
        records = short5.rr.load_audited_roots(
            ROOT / "outputs" / "rr_target_a_22_root_ledger.json",
            ROOT / "outputs" / "rr_long_excursion_prefixes.json",
        )
        found_terminal = False
        for record in records:
            state, decoration = short5.rr.initial_decoration(record)
            self.assertEqual(decoration.r_count, 1)
            for edge, collision in short5.rr.iter_raw_macro_candidates(state):
                if collision is not None or edge is None:
                    continue
                if short5.rr.joint_kind(edge.joint.move.weight, edge.joint.abandonment,
                                        edge.joint.new_orbit) != "R":
                    continue
                verdict, after, recognition = short5.rr.evaluate_edge(state, decoration, edge)
                if verdict in {"FOUND_TARGET_A", "r2_not_target"}:
                    self.assertIsNotNone(after)
                    self.assertEqual(after.r_count, 2)
                    self.assertIsNotNone(recognition)
                    found_terminal = True
                    break
            if found_terminal:
                break
        self.assertTrue(found_terminal)

    def test_checkpoint_scope_extension_is_identity_bearing(self):
        manifest = short5.short_root_manifest(self.records)
        config = short5.rr.checkpoint_config(self.records[0], 0, None, short5.config_extra(manifest))
        self.assertEqual(config["root_universe"], "round37-short5-bare-abandonment-r1-complete-v2")
        self.assertEqual(config["checkpoint_payload_schema"],
                         "rr-target-a-exhaustive-checkpoint-v2-short-r1")
        self.assertIn("short5_manifest_sha256", config)
        with self.assertRaises(ValueError):
            short5.rr.checkpoint_config(self.records[0], 0, None, {"root_id": "bad"})

    def test_v1_aggregate_cannot_be_reused_by_the_r1_complete_driver(self):
        manifest = short5.short_root_manifest(self.records)
        manifest_sha = short5.sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            stale = Path(folder) / "old.json"
            stale.write_text(json.dumps({"short5_manifest_sha256": "v1-stale"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                short5.read_prior_results(stale, manifest_sha)

    def test_v1_checkpoint_is_rejected_by_the_r1_complete_driver(self):
        manifest = short5.short_root_manifest(self.records)
        v2_config = short5.rr.checkpoint_config(self.records[0], 0, None,
                                                 short5.config_extra(manifest))
        v1_config = short5.rr.checkpoint_config(self.records[0], 0, None)
        state, decoration = short5.rr.initial_decoration(self.records[0])
        stats = {"expanded": 0, "generated_edges": 0, "exact_states": [], "memo_hits": 0,
                 "prunes": {}, "CH1_nodes": 0, "CH2_nodes": 0, "undecided_nodes": 0,
                 "other_nodes": 0, "branch_transitions": {}, "max_macro_depth": 0,
                 "checkpoint_count": 0}
        with tempfile.TemporaryDirectory() as folder:
            stale = Path(folder) / "v1.json"
            short5.rr.write_checkpoint(stale, v1_config, [(0, state, decoration, tuple())],
                                       {short5.rr.decorated_key(state, decoration)}, stats, [], [])
            with self.assertRaisesRegex(ValueError, "checkpoint payload schema mismatch"):
                short5.rr.load_checkpoint(stale, v2_config)

    def test_v2_resume_preserves_an_enqueued_r1_frontier(self):
        manifest = short5.short_root_manifest(self.records)
        extra = short5.config_extra(manifest)
        record = self.records[0]
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "v2.json"
            first = short5.rr.search_root(record, node_limit=1, checkpoint=checkpoint,
                                          checkpoint_every=1, checkpoint_config_extra=extra)
            config = short5.rr.checkpoint_config(record, 1, None, extra)
            frontier_a, _seen_a, _stats_a, _bounds_a, _lineage_a = short5.rr.load_checkpoint(checkpoint, config)
            self.assertEqual(first["status"], "INCOMPLETE")
            self.assertTrue(any(dec.r_count == 1 for _depth, _state, dec, _trace in frontier_a))
            resumed = short5.rr.search_root(record, node_limit=1, checkpoint=checkpoint,
                                            checkpoint_every=1, resume=checkpoint,
                                            checkpoint_config_extra=extra)
            frontier_b, _seen_b, _stats_b, _bounds_b, _lineage_b = short5.rr.load_checkpoint(checkpoint, config)
            self.assertEqual(resumed["status"], "INCOMPLETE")
            self.assertEqual([(depth, short5.rr.decorated_key(state, dec), trace)
                              for depth, state, dec, trace in frontier_a],
                             [(depth, short5.rr.decorated_key(state, dec), trace)
                              for depth, state, dec, trace in frontier_b])

    def test_post_r1_telemetry_is_additive_and_present(self):
        """The medium-run observables must not be hidden in uncheckpointed locals."""
        manifest = short5.short_root_manifest(self.records)
        result = short5.rr.search_root(self.records[0], node_limit=8, checkpoint=None,
                                       checkpoint_config_extra=short5.config_extra(manifest))
        self.assertEqual(result["status"], "INCOMPLETE")
        stats = result["stats"]
        for key in ("Phi_at_R1", "M_at_R1", "steps_since_R1_expanded",
                    "hub_completions_before_R1", "hub_completions_after_R1",
                    "CH1_events", "CH2_events", "provisional_CH0_events"):
            self.assertIn(key, stats)
        self.assertGreaterEqual(int(stats["R1_transitions"]), 1)
        self.assertTrue(stats["Phi_at_R1"])
        self.assertTrue(stats["M_at_R1"])
        self.assertTrue(stats["steps_since_R1_expanded"])

    def test_short_driver_does_not_reference_the_phase_helper(self):
        tree = ast.parse((ROOT / "src" / "search_rr_short5_exact.py").read_text(encoding="utf-8"))
        names = {node.func.id for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("true_phase_walk_capacity", names)


if __name__ == "__main__":
    unittest.main()
