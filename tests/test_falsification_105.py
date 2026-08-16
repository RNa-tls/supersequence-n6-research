"""라운드 105 — 반증 라운드가 찾아낸 전제와 그 검증을 회귀로 고정한다."""

from __future__ import annotations

import importlib.util
import itertools
import json
import random
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


def brute_min_cost(nodes, edges, cost):
    best = None
    for perm in itertools.permutations(nodes):
        if perm[0] not in edges.get(RT, ()):
            continue
        c = cost[(RT, perm[0])]
        ok = True
        for a, b in zip(perm, perm[1:]):
            if b not in edges.get(a, ()):
                ok = False
                break
            c += cost[(a, b)]
        if ok and (best is None or c < best):
            best = c
    return best


def random_instance(rng, n, restrict):
    nodes = [("v", i) for i in range(n)]
    edges, cost = {}, {}
    for x in [RT] + nodes:
        outs = [y for y in nodes if y != x and rng.random() < 0.5]
        if not outs:
            continue
        edges[x] = set(outs)
        if restrict:
            zero = rng.choice(outs) if rng.random() < 0.7 else None
            for y in outs:
                cost[(x, y)] = 0 if y is zero else 1
        else:
            for y in outs:
                cost[(x, y)] = rng.randint(0, 1)
    return nodes, edges, cost


class ComponentBoundPrecondition(unittest.TestCase):
    def test_solver_matches_brute_force_when_cost0_outdegree_is_at_most_one(self):
        """전제가 성립하면 솔버는 전수 열거와 정확히 일치한다."""
        rng = random.Random(2025)
        checked = 0
        for t in range(160):
            nodes, edges, cost = random_instance(rng, rng.randint(3, 6), restrict=True)
            star = brute_min_cost(nodes, edges, cost)
            for B in range(0, len(nodes) + 2):
                v, _s, w = P.weighted_hamilton(nodes, edges, cost, B, node_cap=200_000)
                truth = "SAT" if (star is not None and star <= B) else "UNSAT"
                self.assertNotEqual(v, "UNKNOWN")
                self.assertEqual(v, truth)
                if v == "SAT":
                    self.assertLessEqual(w["total_cost"], B)
                checked += 1
        self.assertGreater(checked, 500)

    def test_precondition_is_asserted_when_violated(self):
        """비용-0 유출 차수가 2 이면 하한이 불건전하므로 assert 로 막는다."""
        x, a, b, c = ("v", 3), ("v", 0), ("v", 1), ("v", 2)
        edges = {RT: {x}, x: {a}, a: {b, c}, b: {c}, c: {b}}
        cost = {(RT, x): 0, (x, a): 0, (a, b): 0, (a, c): 0, (b, c): 1, (c, b): 1}
        with self.assertRaises(AssertionError):
            P.weighted_hamilton([x, a, b, c], edges, cost, B=1)

    def test_real_instances_satisfy_the_precondition(self):
        data = json.loads((ROOT / "outputs" / "rr_falsification_105.json").read_text())
        self.assertEqual(data["two_L2_implementations"].get("MISMATCH", 0), 0)


class EngineFacts(unittest.TestCase):
    def test_H_can_never_decrease(self):
        data = json.loads((ROOT / "outputs" / "rr_falsification_105.json").read_text())
        self.assertTrue(data["H_monotone"])
        self.assertTrue(data["S_monotone"])

    def test_ell5_never_abandons_but_shorter_ell_always_does(self):
        data = json.loads((ROOT / "outputs" / "rr_falsification_105.json").read_text())
        scan = data["abandonment_scan"]
        self.assertEqual(data["abandonment_true_for_ell5"], 0)
        self.assertIn("ell=5 abandonment=False", scan)
        for e in range(5):
            self.assertIn(f"ell={e} abandonment=True", scan)


class Controls(unittest.TestCase):
    def test_ten_thousand_positive_controls_had_no_false_unsat(self):
        data = json.loads((ROOT / "outputs" / "rr_falsification_105.json").read_text())
        ctrl = data["synthetic_positive_controls"]
        self.assertEqual(ctrl["instances"], 10000)
        self.assertEqual(ctrl["false_unsat"], 0)
        self.assertEqual(ctrl["verdicts"].get("UNSAT", 0), 0)

    def test_witness_bounds_never_exceed_actual_cost(self):
        data = json.loads((ROOT / "outputs" / "rr_falsification_105.json").read_text())
        wb = data["witness_bound_check"]
        self.assertEqual(wb["violations_L_gt_E"], 0)
        for row in wb["rows"]:
            self.assertLessEqual(row["L2"], row["E"])
            self.assertLessEqual(row["L1"], row["E"])

    def test_margin_fragility_is_recorded(self):
        """붕괴가 아슬아슬하다는 사실을 회귀로 남긴다."""
        data = json.loads((ROOT / "outputs" / "rr_falsification_105.json").read_text())
        hist = {int(k): v for k, v in data["root_margin_histogram"].items()}
        self.assertLessEqual(data["min_root_margin"], 0)
        self.assertGreater(hist.get(1, 0), 1000)


if __name__ == "__main__":
    unittest.main()
