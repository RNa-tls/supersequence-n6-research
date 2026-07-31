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
        self.assertEqual(audit["key_collision_mismatches"], [])
        self.assertEqual(audit["json_roundtrip_failures"], [])

    def test_checkpoint_scope_extension_is_identity_bearing(self):
        manifest = short5.short_root_manifest(self.records)
        config = short5.rr.checkpoint_config(self.records[0], 0, None, short5.config_extra(manifest))
        self.assertEqual(config["root_universe"], "round37-short5-bare-abandonment-v1")
        self.assertIn("short5_manifest_sha256", config)
        with self.assertRaises(ValueError):
            short5.rr.checkpoint_config(self.records[0], 0, None, {"root_id": "bad"})

    def test_short_driver_does_not_reference_the_phase_helper(self):
        tree = ast.parse((ROOT / "src" / "search_rr_short5_exact.py").read_text(encoding="utf-8"))
        names = {node.func.id for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("true_phase_walk_capacity", names)


if __name__ == "__main__":
    unittest.main()
