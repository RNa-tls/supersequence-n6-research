"""라운드 97 — 강제-간선 전파(D4a/D4b), 분리자 재현(D1), Hamilton 파일럿의 건전성 검사.

전수 스윕은 수 분이 걸리므로 여기서는 규칙별 최소 반례와 양성 대조 축소판만 돌린다.
전수 재현은 `python3 src/probe_rr_forced_edge.py export` 다.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "probe_rr_forced_edge", ROOT / "src" / "probe_rr_forced_edge.py")
F = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = F
_spec.loader.exec_module(F)
R = F.ROOTV


def g(pairs):
    edges = {}
    for a, b in pairs:
        edges.setdefault(a, set()).add(b)
    return edges


class Propagation(unittest.TestCase):
    def test_pass_on_explicit_path(self):
        nodes = [("v", i) for i in range(4)]
        edges = g([(R, nodes[0]), (nodes[0], nodes[1]), (nodes[1], nodes[2]),
                   (nodes[2], nodes[3])])
        self.assertEqual(F.d4a_verdict(nodes, edges)[0], "PASS")
        self.assertEqual(F.d4b_verdict(nodes, edges)[0], "PASS")

    def test_no_incoming_is_a_contradiction(self):
        nodes = [("v", 0), ("v", 1)]
        edges = g([(R, nodes[0])])          # v1 은 유입이 없다
        verdict, why, _ = F.d4a_verdict(nodes, edges)
        self.assertEqual((verdict, why), ("FAIL", "no_incoming"))

    def test_deleting_a_competing_root_edge_empties_an_indegree(self):
        # R1 이 R→v0 을 강제하면 R2 가 R→v1 을 지우고 v1 의 유입이 비어 R3 이 발동한다.
        nodes = [("v", 0), ("v", 1)]
        edges = g([(R, nodes[0]), (R, nodes[1])])
        verdict, why, _ = F.d4a_verdict(nodes, edges)
        self.assertEqual((verdict, why), ("FAIL", "no_incoming"))

    def test_two_terminals_is_a_contradiction(self):
        a, b, t1, t2 = ("v", 0), ("v", 1), ("t", 1), ("t", 2)
        edges = g([(R, a), (R, b), (a, b), (b, a),
                   (a, t1), (b, t1), (a, t2), (b, t2)])   # 유출 0 인 의무가 2개
        verdict, why, _ = F.d4a_verdict([a, b, t1, t2], edges)
        self.assertEqual((verdict, why), ("FAIL", "two_terminals"))

    def test_forced_proper_subtour(self):
        # a,b 는 서로만 유입이 있어 a→b→a 가 강제되고 ROOT 를 포함하지 않는다.
        a, b, c, d = ("v", 0), ("v", 1), ("v", 2), ("v", 3)
        edges = g([(R, c), (c, d), (d, c), (a, b), (b, a)])
        verdict, why, cert = F.d4a_verdict([a, b, c, d], edges)
        self.assertEqual(verdict, "FAIL")
        self.assertIn(why, ("forced_proper_subtour", "no_incoming"))

    def test_separator_rejects_three_components(self):
        # 별 모양: 절단점 하나를 빼면 성분이 3개 → spanning path 불가
        hub = ("v", 0)
        leaves = [("v", i) for i in (1, 2, 3)]
        edges = g([(R, hub)] + [(hub, x) for x in leaves])
        verdict, sep, comp = F.d1_verdict([hub] + leaves, edges)
        self.assertEqual(verdict, "FAIL")
        self.assertEqual(sep, hub)
        self.assertGreaterEqual(comp, 3)


class Controls(unittest.TestCase):
    def test_no_false_rejection_on_random_rooted_hamilton(self):
        res = F.run_control(trials=120, seed=5)
        self.assertEqual(res["false_rejections"], {"d1": 0, "d4a": 0, "d4b": 0})

    def test_pilot_never_reports_false_unsat(self):
        res = F.run_pilot_control(trials=60, seed=11)
        self.assertEqual(res["false_unsat"], 0)

    def test_pilot_decides_a_tiny_unsat(self):
        a, b = ("v", 0), ("v", 1)
        edges = g([(R, a), (R, b)])         # a,b 사이 간선이 없으니 경로가 없다
        self.assertEqual(F.hamilton_pilot([a, b], edges)[0], "UNSAT")

    def test_pilot_cap_is_unknown_not_unsat(self):
        self.assertEqual(F.hamilton_pilot(*F.random_rooted_hamilton(
            __import__("random").Random(3), 30, extra_ratio=3), node_cap=1)[0], "UNKNOWN")


class Ledger(unittest.TestCase):
    def test_ledger_rows_are_all_cover_closures(self):
        import gzip
        path = ROOT / "outputs" / "rr_forced_edge_ledger.jsonl.gz"
        with gzip.open(path, "rt") as fh:
            header = json.loads(fh.readline())
            rows = [json.loads(line) for line in fh]
        self.assertEqual(header["schema"], "rr_forced_edge/1")
        self.assertTrue(all(r["all_surviving_covers_fail"] for r in rows))
        self.assertTrue(all(r["state_verdict"] == "UNSAT" for r in rows))
        by_layer = {}
        for r in rows:
            by_layer.setdefault(r["layer"], []).append(r["sid"])
        self.assertEqual({k: len(v) for k, v in by_layer.items()},
                         {"d1": 4, "d4a": 2, "d4b": 4})
        self.assertEqual(set(by_layer["d1"]) & set(by_layer["d4b"]), set())


if __name__ == "__main__":
    unittest.main()
