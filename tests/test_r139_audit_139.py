#!/usr/bin/env python3
"""라운드 139 감사 회귀 시험.  Astra 의 코드는 쓰지 않는다."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import audit_r139_master_139 as M                                # noqa: E402
import audit_r139_rows_139 as R                                  # noqa: E402


def load(name):
    return json.loads((ROOT / "outputs" / name).read_text())


class SpliceIdentity(unittest.TestCase):
    def test_5016_endpoint_identities(self):
        r = M.splice_endpoint_identity()
        self.assertEqual(r["total"], 5016)
        self.assertEqual(r["per_n"], {4: 96, 5: 600, 6: 4320})
        self.assertEqual(r["failure_count"], 0)

    def test_joint_fully_preserved(self):
        r = M.splice_preserves_literal_joint()
        self.assertEqual(r["failure_count"], 0)
        self.assertGreater(r["triples_checked"], 40000)


class Topology(unittest.TestCase):
    def test_five_support_cases(self):
        r = M.topology_five_cases()
        self.assertEqual(r["case_count"], 5)
        self.assertEqual(r["circuits_by_case"],
                         {"A_F2": 2, "A_F1": 0, "B_disjoint": 2,
                          "B_nested": 2, "B_crossing": 0})
        self.assertTrue(r["subdivision_invariant"])

    def test_hex_simple_exactly_in_three_component_cases(self):
        self.assertTrue(M.topology_five_cases()["hex_simple_iff_three_components"])


class ResourceAndMaster(unittest.TestCase):
    def test_resource_identities(self):
        r = M.resource_and_master()
        self.assertTrue(r["all_D_equal_5k_minus_2"])
        self.assertTrue(r["budget_S_plus_H_le_25"])
        self.assertTrue(r["master_consequences_sound"])
        self.assertTrue(r["k_plus_H_le_2_plus_c"])

    def test_k3_k4_agree_with_earlier_audits(self):
        rows = {x["k"]: x for x in M.resource_and_master()["resource_rows"]}
        self.assertEqual(rows[3]["D"], 13)      # 라운드 137/138 감사와 일치
        self.assertEqual(rows[4]["D"], 18)      # 라운드 131 과 일치
        self.assertEqual(rows[2]["D"], 8)
        self.assertEqual(rows[1]["D"], 3)


class RowSpaces(unittest.TestCase):
    def test_k2_is_73_rows_78_tuples(self):
        t = R.table(2)
        self.assertEqual(t["distinct_rows"], 73)
        self.assertEqual(t["heavy_refined_tuples"], 78)
        self.assertEqual(t["q_histogram"], {0: 8, 1: 27, 2: 38})

    def test_k1_row_space_derived(self):
        t = R.table(1)
        self.assertEqual((t["O"], t["D"]), (25, 3))
        self.assertEqual(t["distinct_rows"], 162)

    def test_every_row_maps_into_an_envelope(self):
        r = R.row_to_envelope_identity()
        self.assertEqual(r["violations"], 0)
        self.assertTrue(r["all_rows_fit_an_envelope"])


class Capacities(unittest.TestCase):
    EXPECT = {(0, 3): 33, (0, 8): 62, (1, 3): 48, (1, 8): 77,
              (2, 3): 63, (2, 8): 92, (3, 3): 78}
    NODES = {(0, 3): 1221, (0, 8): 186282, (1, 3): 63036, (1, 8): 9936486,
             (2, 3): 1696230, (2, 8): 271115024, (3, 3): 34921301}

    def test_values_and_node_counts_match_producer(self):
        for (b, d), val in self.EXPECT.items():
            f = ROOT / "outputs" / f"rr_r139_capacity_b{b}_d{d}_139.json"
            if not f.exists():
                continue
            r = json.loads(f.read_text())
            self.assertFalse(r["capped"], f"({b},{d}) capped")
            self.assertEqual(r["N"][str(d)], val, f"N*({b},0,{d})")
            self.assertEqual(r["nodes"], self.NODES[(b, d)], f"nodes ({b},{d})")

    def test_new_values_present(self):
        for b, d in ((2, 3), (2, 8), (3, 3)):
            self.assertTrue((ROOT / "outputs"
                             / f"rr_r139_capacity_b{b}_d{d}_139.json").exists(),
                            f"new load-bearing value ({b},{d}) missing")


class EqualitySeams(unittest.TestCase):
    def test_E2_all_312_collide(self):
        e = load("rr_r139_seams_audit_139.json")["E2"]
        self.assertFalse(e["capped"])
        self.assertEqual((e["extremal_count_d4"], e["extremal_count_d9"]), (1, 12))
        self.assertEqual(e["total_seams"], 312)
        self.assertEqual(e["survivor_count"], 0)

    def test_E3_all_second_seams_collide(self):
        e = load("rr_r139_seams_audit_139.json")["E3"]
        self.assertEqual(e["first_seams"], 78)
        self.assertEqual(e["first_survivors"], 8)
        self.assertEqual(e["second_seams"], 104)
        self.assertEqual(e["second_survivors"], 0)
        self.assertTrue(e["E3_eliminated"])

    def test_13_legal_w4_tails(self):
        self.assertEqual(load("rr_r139_seams_audit_139.json")
                         ["w4_legal_tails_per_window"], 13)


class Controls(unittest.TestCase):
    def test_1510_controls_replayed_clean(self):
        r = load("rr_r139_controls_audit_139.json")
        self.assertEqual(r["controls_checked"], 1510)
        self.assertEqual(r["failures"], {})
        self.assertTrue(r["full_agreement"])


class CounterexampleSearch(unittest.TestCase):
    def test_nothing_refuted(self):
        r = load("rr_r139_counterex_139.json")
        self.assertFalse(r["any_refuted"])
        for k in ("A_wrong_successor", "B_uncharged_shared_orbit",
                  "C_double_counted_defect", "D_missing_H2",
                  "E_typeA_outside_normal_form", "F_k1_outside_envelopes"):
            self.assertFalse(r[k]["refuted"], k)

    def test_H2_classification_complete(self):
        d = load("rr_r139_counterex_139.json")["D_missing_H2"]
        self.assertEqual(sorted(d["multisets"]), sorted([[5], [4, 4]]))
        self.assertTrue(d["complete"])


class Discipline(unittest.TestCase):
    def test_no_872_claim_and_ledger_scope(self):
        doc = (ROOT / "research" / "RR_R139_MASTER_AUDIT_139_CLAUDE.md").read_text()
        self.assertIn("`L6 >= 872` 를 증명하지 않았다", doc)
        self.assertNotIn("L6 = 872", doc)
        self.assertIn("13/55", doc)
        self.assertIn("ASSUMED", doc)
        self.assertIn("CLAUDE_ROUND139_MASTER_CONFIRMED", doc)

    def test_no_capacity_run_was_capped(self):
        import glob
        n = 0
        for f in glob.glob(str(ROOT / "outputs" / "rr_r139_capacity_b*_139.json")):
            self.assertFalse(json.loads(Path(f).read_text())["capped"], f)
            n += 1
        self.assertGreaterEqual(n, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
