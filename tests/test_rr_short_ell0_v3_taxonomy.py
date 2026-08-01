"""Round-43 controls for the non-semantic R2 geometry instrumentation."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rr = load("rr_taxonomy_test_engine", ROOT / "src" / "search_rr_target_a_exhaustive.py")
short5 = load("rr_taxonomy_test_short5", ROOT / "src" / "search_rr_short5_exact.py")


class TestRound43Taxonomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = next(row for row in short5.short_root_records() if row["root_id"] == "short_ell0")
        cls.extra = short5.config_extra(short5.short_root_manifest(short5.short_root_records()))

    def test_geometry_categories_are_exact_and_no_residual_is_emitted(self):
        self.assertEqual(
            rr.geometry_failure_reason(source_present=False, target_present=False),
            "r2_wrong_source_orbit")
        self.assertEqual(
            rr.geometry_failure_reason(source_present=True, target_present=False),
            "r2_wrong_target_orbit")
        with self.assertRaises(AssertionError):
            rr.geometry_failure_reason(source_present=True, target_present=True)
        self.assertEqual(len(rr.GEOMETRY_FAILURE_VOCABULARY),
                         len(set(rr.GEOMETRY_FAILURE_VOCABULARY)))
        self.assertIn("other_asserted_reason", rr.GEOMETRY_FAILURE_VOCABULARY)

    def test_capture_is_additive_on_a_small_deterministic_prefix(self):
        plain = rr.search_root(self.record, node_limit=250, checkpoint=None,
                               checkpoint_config_extra=self.extra,
                               prune_profile=rr.TARGET_A_SAFE_PROFILE)
        captured = rr.search_root(self.record, node_limit=250, checkpoint=None,
                                  checkpoint_config_extra=self.extra,
                                  prune_profile=rr.TARGET_A_SAFE_PROFILE,
                                  capture_r2_diagnostics=True,
                                  capture_frontier_snapshot=True)
        fields = ("expanded", "generated_edges", "memo_hits", "prunes", "R1_transitions",
                  "R2_candidate_edges", "Target_A_hits", "pre_R_nodes", "post_R1_nodes",
                  "R2_outcomes")
        self.assertEqual({key: plain["stats"][key] for key in fields},
                         {key: captured["stats"][key] for key in fields})
        counts = captured["stats"]["geometry_failure_counts"]
        self.assertEqual(sum(counts.values()),
                         captured["stats"]["R2_outcomes"]["recognizer_geometry_failure"])
        self.assertEqual(len(captured["stats"]["geometry_failure_records"]),
                         captured["stats"]["R2_outcomes"]["recognizer_geometry_failure"])
        self.assertEqual(len(captured["stats"]["same_component_failure_records"]),
                         captured["stats"]["R2_outcomes"]["not_same_component"])

    def test_committed_taxonomy_outputs_have_required_partition(self):
        geometry_path = ROOT / "outputs" / "rr_short_ell0_v3_geometry_failures.json"
        frontier_path = ROOT / "outputs" / "rr_short_ell0_v3_frontier_export.json"
        components_path = ROOT / "outputs" / "rr_short_ell0_v3_component_failures.json"
        if not all(path.exists() for path in (geometry_path, frontier_path, components_path)):
            self.skipTest("Round-43 deterministic replay outputs not generated yet")
        geo = json.loads(geometry_path.read_text(encoding="utf-8"))
        front = json.loads(frontier_path.read_text(encoding="utf-8"))
        comps = json.loads(components_path.read_text(encoding="utf-8"))
        self.assertEqual(sum(geo["geometry_failure_counts"].values()), 44_021)
        self.assertEqual(geo["record_count"], 44_021)
        self.assertEqual(front["record_count"], 85)
        self.assertEqual(comps["record_count"], 5_419)
        self.assertEqual(len(geo["records"]) + len(comps["records"]), 49_440)
        self.assertTrue(geo["replay_equivalence"]["same_expansion_sequence"])
        self.assertTrue(geo["replay_equivalence"]["same_frontier"])
        self.assertTrue(geo["replay_equivalence"]["same_seen_key_set"])

    def test_v3_prefix_has_no_completion_only_prune(self):
        medium = json.loads((ROOT / "outputs" / "rr_short_ell0_medium_v3.json")
                            .read_text(encoding="utf-8"))
        self.assertTrue(all(value == 0 for value in medium["disabled_prune_counts"].values()))


if __name__ == "__main__":
    unittest.main()
