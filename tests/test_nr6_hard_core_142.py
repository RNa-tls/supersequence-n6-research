#!/usr/bin/env python3
"""NR6 하드 코어 회귀 시험 — 재정식화, 결함 항등식, TRIM 이분법, ARC 보조정리."""
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from nr6_geometry_142 import Geo, sanity                          # noqa: E402
from nr6_walk_model_142 import repeat_bound                       # noqa: E402
from nr6_trim_142 import dichotomy_proof_check                    # noqa: E402
from nr6_master_ineq_142 import slack, analyse_walk               # noqa: E402


class Geometry(unittest.TestCase):
    def test_metric_and_geodesic_uniqueness(self):
        for n in (3, 4):
            r = sanity(n)
            self.assertTrue(r["triangle"], n)
            self.assertTrue(r["chain_decomposition"], n)
            self.assertTrue(r["geodesic_unique"], n)

    def test_n6_clean_outdegrees(self):
        g = Geo(6)
        from collections import Counter
        c = Counter()
        for p in range(0, 720, 60):
            for q in range(720):
                if p != q and g.clean(p, q):
                    c[g.W[p][q]] += 1
        per = {w: v // 12 for w, v in c.items()}
        self.assertEqual(per, {1: 1, 2: 1, 3: 3, 4: 13, 5: 71, 6: 308})


class DefectIdentity(unittest.TestCase):
    def test_base_values(self):
        for n, base in ((3, 9), (4, 32), (5, 147), (6, 844)):
            self.assertEqual(n + math.factorial(n) + math.factorial(n - 1) - 2, base)

    def test_slack_matches_known_repeat_bounds(self):
        self.assertEqual(slack(6, 871), 27)
        self.assertEqual(slack(6, 867), 23)
        self.assertEqual(slack(5, 153), 6)
        self.assertEqual(slack(4, 33), 1)
        self.assertEqual(slack(3, 9), 0)

    def test_repeat_bound_agrees_with_slack(self):
        for n, L in ((3, 9), (4, 33), (5, 153), (6, 871)):
            self.assertEqual(repeat_bound(n, L), slack(n, L))

    def test_L6_ge_872_is_exactly_D_ge_28(self):
        self.assertEqual(872 - 844, 28)
        self.assertEqual(slack(6, 871), 27)


class TrimDichotomy(unittest.TestCase):
    def test_dichotomy_holds_small_n(self):
        for n in (3, 4, 5):
            r = dichotomy_proof_check(n)
            self.assertEqual(r["violations"], 0, n)
            self.assertTrue(r["dichotomy_holds"], n)

    def test_blocked_exactly_below_weight_n(self):
        r = dichotomy_proof_check(5)
        for k, v in r["by_weight"].items():
            w = int(k[1])
            blocked = k.endswith("True")
            self.assertEqual(blocked, w <= 4, k)


class ExhaustiveSearch(unittest.TestCase):
    """C 탐색기를 다시 빌드해 소형 통제를 재현한다."""

    @classmethod
    def setUpClass(cls):
        cls.exe = ROOT / "outputs" / "nr_clean_walk_142.exe"
        cls.exe.parent.mkdir(exist_ok=True)
        subprocess.run(["cc", "-O3", "-o", str(cls.exe),
                        str(ROOT / "src" / "nr_clean_walk_142.c")], check=True)

    def run_case(self, n, b):
        out = subprocess.run([str(self.exe), str(n), str(b), "100000000000"],
                             capture_output=True, text=True, check=True)
        return json.loads(out.stdout.strip().splitlines()[-1])

    def test_n3_minimum_is_unique_and_clean(self):
        r = self.run_case(3, 6)
        self.assertEqual(r["capped"], 0)
        self.assertEqual(r["solutions_by_repeats"], {"0": 1})

    def test_n4_length_32_is_unsat(self):
        r = self.run_case(4, 28)
        self.assertEqual(r["capped"], 0)
        self.assertEqual(r["solutions_by_repeats"], {})

    def test_n4_minimum_is_unique_and_clean(self):
        r = self.run_case(4, 29)
        self.assertEqual(r["capped"], 0)
        self.assertEqual(r["solutions_by_repeats"], {"0": 1})

    def test_n4_repeats_appear_only_above_minimum(self):
        r = self.run_case(4, 30)
        self.assertEqual(r["solutions_by_repeats"], {"0": 19, "1": 5})


class Discipline(unittest.TestCase):
    def test_report_scope(self):
        doc = (ROOT / "research" / "RR_NR6_HARD_CORE_142_CLAUDE.md").read_text()
        self.assertIn("L6 >= 872` 를 증명하지 않았다", doc)
        self.assertNotIn("L6 = 872 를 증명", doc)
        self.assertIn("FABLE_NR6_HARD_CORE", doc)
        self.assertIn("NR-UNIVERSAL", doc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
