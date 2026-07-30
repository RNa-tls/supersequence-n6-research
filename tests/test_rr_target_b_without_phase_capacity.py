"""Round-39 regressions for the helper-free Target-B re-audit."""
from __future__ import annotations

import ast
import inspect
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import verify_rr_target_b_without_phase_capacity as recheck  # noqa: E402
import verify_rr_round37_envelope_independent as envelope  # noqa: E402


def _load_flow_module():
    import importlib.util
    path = ROOT / "src" / "search_rr_target_b_flow.py"
    spec = importlib.util.spec_from_file_location("rr39_flow_audit", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TargetBWithoutPhaseCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = recheck.rebuild_rows(node_cap=8_000_000, seconds=180.0)

    def test_all_eighteen_boundaries_are_replayed_once(self):
        self.assertEqual(len(self.rows), 18)
        self.assertEqual(len({r["canonical_state_hash"] for r in self.rows}), 18)

    def test_corrected_sequence_is_coarse_nine_then_exact_nine(self):
        hist = Counter(r["corrected_final_status"] for r in self.rows)
        self.assertEqual(hist, {"COARSE_CAPACITY_IMPOSSIBLE": 9, "EXHAUSTED_NO_PATH": 9})

    def test_historical_seven_flow_roots_reexhaust(self):
        seven = [r for r in self.rows if r["old_flow_certificate"] == "EXHAUSTED_NO_PATH"]
        self.assertEqual(len(seven), 7)
        self.assertTrue(all(r["corrected_final_status"] == "EXHAUSTED_NO_PATH" for r in seven))

    def test_phase_only_eliminations_are_closed_without_phase_helper(self):
        phase_rows = [r for r in self.rows if r["old_phase_port"] and r["old_phase_port"]["contradiction"]]
        self.assertEqual(len(phase_rows), 1)
        self.assertEqual(phase_rows[0]["corrected_final_status"], "EXHAUSTED_NO_PATH")
        self.assertTrue(phase_rows[0]["round32_B_plus_R"]["contradiction"])

    def test_replacement_proof_path_has_no_helper_call(self):
        tree = ast.parse(inspect.getsource(recheck))
        called = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("true_phase_walk_capacity", called)

    def test_round37_envelope_audit_path_does_not_call_old_phase_function(self):
        self.assertNotIn("old_phase_capacity", inspect.getsource(envelope.audit))

    def test_flow_search_semantics_do_not_call_phase_helper(self):
        flow = _load_flow_module()
        self.assertNotIn("true_phase_walk_capacity", inspect.getsource(flow.FlowSearch))


if __name__ == "__main__":
    unittest.main()
