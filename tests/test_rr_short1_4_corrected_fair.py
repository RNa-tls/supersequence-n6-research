"""Small v5 controls for the corrected short-ell1--ell4 pilot driver.

The multi-thousand-expansion fair pilot is intentionally validated by its
independent replay verifier, not reproduced by the ordinary unit suite.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load("rr_short14_corrected_fair_test", ROOT / "src" / "search_rr_short1_4_corrected_fair.py")


class TestRound50CorrectedFairPilot(unittest.TestCase):
    def test_v5_namespace_is_distinct_from_legacy_checkpoints(self):
        self.assertIn("v5", pilot.CHECKPOINT_SCHEMA)
        self.assertIn("literal-r2-source", pilot.CHECKPOINT_SCHEMA)
        self.assertNotIn("v4", pilot.CHECKPOINT_SCHEMA)
        self.assertEqual(pilot.R2_SEMANTICS, "R2_LITERAL_JOINT_SOURCE_V1")

    def test_every_bare_root_has_a_literal_first_r_child(self):
        for root_id, root in pilot.root_records().items():
            state, dec = pilot.rr.initial_decoration(root)
            r_edges = []
            for edge, collision in pilot.rr.iter_raw_macro_candidates(state):
                if collision is None and edge is not None and pilot.edge_kind(edge) == "R":
                    verdict, after, _recognition = pilot.rr.evaluate_edge(
                        state, dec, edge, prune_profile=pilot.rr.TARGET_A_SAFE_PROFILE
                    )
                    r_edges.append((verdict, after))
            self.assertTrue(r_edges, root_id)
            self.assertTrue(all(verdict == "child" and after is not None and after.r_count == 1
                                for verdict, after in r_edges), root_id)

    def test_admission_freezes_replayable_post_r1_provenance(self):
        # One expansion is enough to exercise the literal direct-R admission
        # without importing a historical checkpoint or running a pilot branch.
        for root_id, root in pilot.root_records().items():
            row = pilot.admission(root, 1)
            self.assertEqual(row["schema"], pilot.ADMISSION_SCHEMA)
            self.assertGreaterEqual(len(row["frozen_R1_children"]), 1, root_id)
            child = row["frozen_R1_children"][0]
            state, dec = pilot.replay_trace(root, child["literal_macro_trace"])
            self.assertEqual(dec.r_count, 1)
            self.assertEqual(pilot.rr.state_hash(state), child["exact_state_hash"])


if __name__ == "__main__":
    unittest.main()
