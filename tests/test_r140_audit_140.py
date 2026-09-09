#!/usr/bin/env python3
"""라운드 140 감사 회귀 시험.  Astra 의 코드는 쓰지 않는다."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import audit_r140_g3_140 as G3                                    # noqa: E402
import audit_r140_splice_140 as SP                                # noqa: E402
import audit_r140_envelopes_140 as EN                             # noqa: E402


def load(name):
    return json.loads((ROOT / "outputs" / name).read_text())


class TheoremA(unittest.TestCase):
    """PART I — 보편 자유-이탈 정리."""

    def test_identity_2_1_exhaustive(self):
        r = load("rr_r140_theoremA_140.json")["identity_2_1"]
        self.assertEqual(r["per_n"], {"4": 24, "5": 120, "6": 720})
        self.assertEqual(r["failure_count"], 0)

    def test_nr4_census_and_histogram(self):
        r = load("rr_r140_theoremA_140.json")["nr4"]
        self.assertEqual(r["count"], 29255)
        self.assertEqual([r["G_histogram"][str(i)] for i in range(7)],
                         [827, 5999, 10625, 7545, 3384, 629, 246])

    def test_no_violation_of_any_identity(self):
        r = load("rr_r140_theoremA_140.json")["nr4"]
        for k in ("theoremA_violations", "identity_2_2_violations",
                  "O_bound_violations", "S_identity_violations",
                  "Ord_subset_Rpt_violations", "old_theorem_violations"):
            self.assertEqual(r[k], 0, k)

    def test_bound_is_attained_and_delta_ge_J_is_refuted(self):
        r = load("rr_r140_theoremA_140.json")["nr4"]
        self.assertGreater(r["delta_ge_J_counterexamples"], 0)


class Injection(unittest.TestCase):
    """§5-§8 — 하중을 지는 단사."""

    def test_no_failures(self):
        r = load("rr_r140_injection_140.json")
        self.assertEqual(r["words_checked"], 29255)
        self.assertEqual(r["failures"], {})

    def test_multi_hexagon_obligations_actually_exercised(self):
        r = load("rr_r140_injection_140.json")
        self.assertGreater(r["words_with_obligations_from_2plus_hexagons"], 1000)
        self.assertGreater(r["words_with_obligations_from_3plus_hexagons"], 100)

    def test_bound_tight_on_some_words(self):
        self.assertGreater(load("rr_r140_injection_140.json")["tight_words"], 0)


class Classification(unittest.TestCase):
    """§11-§13 — G=3 다중도/F 분류."""

    def test_41_supports_and_2935_decorated(self):
        r = G3.incidence_theorem(3)
        self.assertEqual(r["total_supports"], 41)
        self.assertEqual(r["by_type"], {"4": 6, "32": 20, "222": 15})
        self.assertEqual(r["decorated_total"], 2935)
        self.assertEqual(r["decorated_by_F"], {1: 10, 2: 540, 3: 2385})

    def test_F_distributions(self):
        r = G3.incidence_theorem(3)["by_type_F"]
        self.assertEqual(r["4"], {1: 1, 2: 4, 3: 1})
        self.assertEqual(r["32"], {2: 10, 3: 10})
        self.assertEqual(r["222"], {3: 15})

    def test_incidence_theorem_K_plus_R(self):
        r = G3.incidence_theorem(3)
        self.assertTrue(r["K_plus_R_le_G_plus_1"])
        self.assertTrue(r["K_parity_matches_G_plus_1"])
        self.assertEqual(r["K_values"], [2, 4])
        self.assertEqual(r["KR_distribution"],
                         {"(2,0)": 1, "(2,1)": 8, "(2,2)": 21, "(4,0)": 11})


class Resources(unittest.TestCase):
    """§14-§15 — 516 자원 행."""

    def test_516_and_580(self):
        r = G3.resource_summary(3)
        self.assertEqual(r["arithmetic_total"], 516)
        self.assertEqual(r["heavy_refined_total"], 580)
        self.assertTrue(r["per_k_matches"])
        self.assertTrue(r["per_k_refined_matches"])
        self.assertEqual(r["length_violations"], 0)

    def test_identities(self):
        r = G3.resource_summary(3)["identities"]
        self.assertEqual(r["P"], 123)
        self.assertEqual(r["D_by_k"], {1: 2, 2: 7, 3: 12, 4: 17})


class Splicing(unittest.TestCase):
    """§16-§20, §26."""

    def test_endpoint_identity(self):
        r = SP.endpoint_identity()
        self.assertEqual(r["failure_count"], 0)
        self.assertEqual(r["total"], 40296)

    def test_joint_preservation(self):
        self.assertEqual(SP.joint_preservation()["failure_count"], 0)

    def test_composition_bound(self):
        self.assertEqual(SP.composition_bound()["violations"], 0)

    def test_move_taxonomy_supports_model_inclusion(self):
        r = SP.move_taxonomy()
        self.assertEqual(r["legal_weight2"], ["w2/10"])
        self.assertEqual(r["legal_weight3"], ["w3/120", "w3/201", "w3/210"])
        self.assertTrue(r["no_partial"])


class Envelopes(unittest.TestCase):
    """§28 — 40 봉투."""

    def test_40_envelopes_37_strict_3_equality(self):
        r = load("rr_r140_envelopes_140.json")
        self.assertEqual(r["total_envelopes"], 40)
        self.assertEqual(r["by_k"], {"1": 26, "2": 10, "3": 3, "4": 1})
        self.assertEqual(r["strict"], 37)
        self.assertEqual(r["equality"], 3)
        self.assertEqual(r["open"], 0)

    def test_equality_rows_are_the_three_expected(self):
        eq = load("rr_r140_envelopes_140.json")["equality_rows"]
        self.assertEqual(sorted((e["k"], e["s"]) for e in eq),
                         [(1, 2), (2, 1), (3, 0)])
        for e in eq:
            self.assertEqual((e["K"], e["c"], e["H"], e["heavy"], e["max_pieces"],
                              e["b"], e["D_sum"], e["required_passes"]),
                             (4, 3, 1, [4], 2, 0, 12, 108))


class Seams(unittest.TestCase):
    """§29-§32 — 52 등호 이음매."""

    def test_convolution_completeness(self):
        r = load("rr_r140_seams_140.json")
        self.assertEqual(r["convolution_max"], 108)
        self.assertEqual(sorted(map(tuple, r["convolution_argmax"])),
                         [(4, 8), (8, 4)])

    def test_extremal_counts_and_52_seams(self):
        r = load("rr_r140_seams_140.json")
        self.assertEqual(r["extremal_counts"], {"4": 1, "8": 2})
        self.assertEqual(r["total_seams"], 52)
        self.assertEqual(r["hexagon_collisions"], 52)
        self.assertEqual(r["survivor_count"], 0)

    def test_collision_is_literal_not_orbit_artefact(self):
        r = load("rr_r140_seams_140.json")
        self.assertGreater(r["seams_with_shared_orbit_also_hex_colliding"], 0)


class TightCell(unittest.TestCase):
    """§33 — (4,3) 은 N*(0,0,17) < 108 하나에 달려 있다."""

    def test_capacity_value_replayed_and_strict(self):
        f = ROOT / "outputs" / "rr_r139_capacity_b0_d17_139.json"
        if not f.exists():
            self.skipTest("N*(0,0,17) not computed in this environment")
        d = json.loads(f.read_text())
        self.assertFalse(d["capped"])
        self.assertLess(d["N"]["17"], 108)


class Discipline(unittest.TestCase):
    def test_no_872_claim_and_ledger(self):
        doc = (ROOT / "research" / "RR_R140_AUDIT_140_CLAUDE.md").read_text()
        self.assertIn("`L6 >= 872` 를 증명하지 않았다", doc)
        self.assertNotIn("L6 = 872", doc)
        self.assertIn("17/55", doc)
        self.assertIn("ASSUMED", doc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
