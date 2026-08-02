"""Unit controls for the post-repair-source instrumentation."""
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
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


repair = load("rr_repair_fair_test", ROOT / "src" / "search_rr_short_ell0_repair_fair.py")


class TestRound46RepairFair(unittest.TestCase):
    def test_two_kind_repair_alphabet_is_explicit(self):
        self.assertEqual(repair.REPAIR_TYPES, ("Z2", "Z3_fresh"))

    def test_frozen_origins_are_exactly_four_r1_children(self):
        children = repair.split.frozen_r1_children(repair.split.record())
        self.assertEqual([row["branch_id"] for row in children], [
            "short_ell0_r1_0", "short_ell0_r1_1", "short_ell0_r1_2", "short_ell0_r1_3",
        ])
        self.assertTrue(all(row["r1"]["kind"] == "R" for row in children))

    def test_hierarchy_has_one_maximum_label(self):
        self.assertEqual({f"R{i}" for i in range(7)}, {"R0", "R1", "R2", "R3", "R4", "R5", "R6"})

    def test_r2_literal_joint_source_regression_fixture(self):
        """Macro entry can be same-component while the literal R2 source is not."""
        fixture = json.loads((ROOT / "tests" / "fixtures" /
                              "rr_r2_literal_source_counterexample.json").read_text(encoding="utf-8"))
        state, dec = repair.rr.initial_decoration(repair.split.record())

        def edge_for(step):
            matches = [edge for edge, collision in repair.rr.iter_raw_macro_candidates(state)
                       if collision is None and edge is not None and edge.label == step["label"]]
            self.assertEqual(len(matches), 1)
            return matches[0]

        for step in fixture["literal_macro_trace"][:-1]:
            edge = edge_for(step)
            dec = repair.rr.advance_decoration(edge.run.state, edge.joint, dec)
            state = edge.state
        r2 = edge_for(fixture["literal_macro_trace"][-1])
        after = repair.rr.advance_decoration(r2.run.state, r2.joint, dec)
        at_macro_entry = repair.rr.target_a_recognizer(state, r2.joint, dec, after)
        at_joint_source = repair.rr.target_a_recognizer(r2.run.state, r2.joint, dec, after)
        expected = fixture["expected"]
        self.assertEqual(repair.rr.state_hash(state), expected["macro_entry_hash"])
        self.assertEqual(repair.rr.state_hash(r2.run.state), expected["joint_source_hash"])
        self.assertTrue(at_macro_entry["conditions"]["same_component"])
        self.assertFalse(at_joint_source["conditions"]["same_component"])
        hierarchy = repair.hierarchy_for_r2(state, r2, dec, after, [{"component_merge": False}])
        self.assertEqual(hierarchy["recognizer"], at_joint_source)
        self.assertEqual(hierarchy["literal_joint_source"]["state_hash"], expected["joint_source_hash"])

    def test_literal_source_schema_firewall(self):
        self.assertNotEqual(repair.SCHEMA, repair.LEGACY_SCHEMA)
        self.assertIn("literal-r2-source", repair.SCHEMA)
        self.assertIn("literal-r2-source", repair.CHECKPOINT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
