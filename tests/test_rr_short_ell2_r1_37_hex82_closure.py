from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import analyze_rr_short_ell2_r1_37_hex82_closure as analyzer
import verify_rr_short_ell2_r1_37_hex82_closure as verifier


class Hex82ClosureTests(unittest.TestCase):
    def test_five_literal_routes_and_unique_registration_predecessor(self) -> None:
        routes, entries = analyzer.route_specifications()
        self.assertEqual(
            [(row["candidate_orbit"], row["candidate_phase"], row["target_hex_position"]) for row in routes],
            [(42, 1, 2), (78, 3, 4), (82, 0, 0), (83, 4, 5), (128, 2, 1)],
        )
        self.assertEqual(len(entries), 90)
        manifest = json.loads(analyzer.MANIFEST.read_text(encoding="utf-8"))
        obligation = analyzer.registration_obligation(manifest)
        self.assertEqual(obligation["unique_w2_source_word"], [2, 4, 5, 1, 3, 0])
        self.assertTrue(obligation["all_84_roots_hex40_full"])
        self.assertEqual(obligation["roots_terminal_at_unique_source"], 0)
        self.assertEqual(obligation["roots_with_q91_p2_registered"], 0)

    def test_serialized_closure_and_mitm_conservation(self) -> None:
        backward = json.loads(analyzer.BACKWARD_OUT.read_text(encoding="utf-8"))
        mitm = json.loads(analyzer.MITM_OUT.read_text(encoding="utf-8"))
        self.assertEqual(backward["route_classes"], 5)
        self.assertEqual(backward["deduplicated_predecessor_classes"], 1)
        self.assertEqual(backward["provenance_consistent_classes"], 0)
        self.assertEqual(backward["exact_reachable_classes"], 0)
        self.assertEqual(sum(row["counts"]["M1_orbit_phase_macro_match"] for row in mitm["per_route"]), 155_538)
        self.assertEqual(mitm["M1_orbit_phase_matches"], 155_538)
        self.assertEqual(mitm["M2_structural_state_matches"], 0)
        self.assertEqual(mitm["M4_exact_legal_noncolliding_C4"], 0)
        self.assertEqual(mitm["M5_FZ1_witnesses"], 0)

    def test_independent_static_reconstruction(self) -> None:
        route_rows, _entries = verifier.independently_build_entries()
        result = verifier.verify_static_certificate(route_rows)
        self.assertEqual(result["q91_p2"], [5, 1, 3, 0, 4, 2])
        self.assertEqual(result["unique_z2_source"], [2, 4, 5, 1, 3, 0])
        self.assertEqual(result["anchor_count"], 84)


if __name__ == "__main__":
    unittest.main()
