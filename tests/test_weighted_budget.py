"""라운드 104 — 예산 정리와 가중 경로 조건의 건전성 검사."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


P = _load("probe_rr_weighted_path", "src/probe_rr_weighted_path.py")
RT = P.ROOTV


def g(pairs, costs):
    edges, cost = {}, {}
    for (a, b), c in zip(pairs, costs):
        edges.setdefault(a, set()).add(b)
        cost[(a, b)] = c
    return edges, cost


class Budget(unittest.TestCase):
    def test_budget_formula(self):
        st = {"S": 5, "F": 1, "O": 6, "H": 0, "K": 21}
        B, ndef = P.budget(st)
        self.assertEqual(ndef, 0)
        self.assertEqual(B, 24)

    def test_identity_holds_on_every_preserved_witness(self):
        data = json.loads((ROOT / "outputs" / "rr_weighted_witnesses.json").read_text())
        self.assertTrue(data["identity_holds"])
        for row in data["rows"]:
            self.assertEqual(row["stored_path_cost_E"] - row["B"],
                             row["final_Ndef_plus_H"] - 3, row["sid"])
            self.assertGreater(row["stored_path_cost_E"], row["B"])


class WeightedSearch(unittest.TestCase):
    def test_cheap_path_is_found_within_budget(self):
        n = [("v", i) for i in range(4)]
        edges, cost = g([(RT, n[0]), (n[0], n[1]), (n[1], n[2]), (n[2], n[3])],
                        [0, 0, 0, 0])
        v, _s, w = P.weighted_hamilton(n, edges, cost, B=0)
        self.assertEqual(v, "SAT")
        self.assertEqual(w["total_cost"], 0)

    def test_budget_rejects_an_expensive_only_path(self):
        n = [("v", i) for i in range(3)]
        edges, cost = g([(RT, n[0]), (n[0], n[1]), (n[1], n[2])], [1, 1, 1])
        self.assertEqual(P.weighted_hamilton(n, edges, cost, B=2)[0], "UNSAT")
        self.assertEqual(P.weighted_hamilton(n, edges, cost, B=3)[0], "SAT")

    def test_component_lower_bound_is_never_an_overestimate(self):
        """비용-0 성분 하한은 실제 최소 비용을 넘지 않아야 한다 (건전성)."""
        n = [("v", i) for i in range(5)]
        # 비용-0 사슬 두 개 + 비싼 연결
        edges, cost = g([(RT, n[0]), (n[0], n[1]), (n[1], n[2]),
                         (n[2], n[3]), (n[3], n[4])],
                        [0, 0, 0, 1, 0])
        v, _s, w = P.weighted_hamilton(n, edges, cost, B=1)
        self.assertEqual(v, "SAT")
        self.assertEqual(w["total_cost"], 1)
        self.assertEqual(P.weighted_hamilton(n, edges, cost, B=0)[0], "UNSAT")

    def test_zero_cost_deficiency_bound(self):
        n = [("v", i) for i in range(3)]
        edges, cost = g([(RT, n[0]), (n[0], n[1]), (n[1], n[2])], [0, 0, 1])
        self.assertGreaterEqual(P.zero_cost_deficiency(n, edges, cost), 0)


class Sweep(unittest.TestCase):
    def test_sweep_artifact_is_internally_consistent(self):
        d = json.loads((ROOT / "outputs" / "rr_weighted_sweep.json").read_text())
        self.assertEqual(d["pairs"], 15781)
        self.assertEqual(sum(d["pair_verdicts"].values()), 15781)
        self.assertEqual(d["assignment_verdicts"].get("SAT", 0), 0)
        self.assertEqual(d["assignment_verdicts"].get("UNKNOWN", 0), 0)
        self.assertEqual(d["witness_recheck"], {"UNSAT": 22})
        self.assertEqual(len(d["closed_sids"]), d["state_closures"])

    def test_positive_control_had_no_false_unsat(self):
        d = json.loads((ROOT / "outputs" / "rr_weighted_sweep.json").read_text())
        ctrl = d["positive_control"]
        self.assertEqual(ctrl.get("budget=cost -> UNSAT", 0), 0)
        self.assertGreaterEqual(ctrl.get("budget=cost -> SAT", 0), 1)


if __name__ == "__main__":
    unittest.main()
