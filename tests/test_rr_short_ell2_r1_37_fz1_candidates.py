from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


audit = load_module(
    "rr_fz1_candidate_test_audit",
    ROOT / "src" / "analyze_rr_short_ell2_r1_37_fz1_candidates.py",
)


class FZ1CandidateTableTests(unittest.TestCase):
    def test_fixed_candidate_table(self) -> None:
        payload, candidates = audit.build_candidate_table()
        self.assertEqual(
            sorted(candidates),
            [36, 40, 41, 42, 72, 74, 78, 82, 83, 90,
             92, 93, 95, 96, 98, 102, 120, 126, 128, 129],
        )
        self.assertEqual(payload["r1_phase_linked_hexagons"], [40, 82, 90, 91, 92])
        self.assertEqual(payload["hub_touching_candidate_orbits"], [96, 120, 126, 128, 129])
        self.assertEqual(payload["all_orbit_adjacency_degree_histogram"], {20: 144})

    def test_r4_is_not_exact_candidate_corpus(self) -> None:
        payload = json.loads(
            (ROOT / "outputs" / "rr_short_ell2_r1_37_r4_candidate_crosscheck.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["r4_entry_count"], 22)
        self.assertEqual(payload["entries_matching_any_of_20_candidates"], 0)
        self.assertEqual(payload["entries_matching_candidate_phase"], 0)

    def test_144_z3_pigeonhole_claim_is_not_certified(self) -> None:
        payload = json.loads(
            (ROOT / "outputs" / "rr_short_ell2_r1_37_144z3_bound_audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["verdict"], "NOT_PROVED_BY_ORBIT_PIGEONHOLE")
        self.assertTrue(payload["exact_revisit_examples"])


if __name__ == "__main__":
    unittest.main()
