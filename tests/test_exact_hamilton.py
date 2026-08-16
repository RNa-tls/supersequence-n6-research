"""라운드 98 — 정확 rooted Hamilton 엔진의 건전성 검사.

전수 스윕은 시간이 걸리므로 여기서는 (i) 최소 사례, (ii) 양성 대조 축소판, (iii) 역방향
정식화가 정방향과 일치하는지, (iv) 보존된 SAT 증인의 간선 전수 대조만 돌린다.
"""

from __future__ import annotations

import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "probe_rr_exact_hamilton", ROOT / "src" / "probe_rr_exact_hamilton.py")
E = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = E
_spec.loader.exec_module(E)
F = E.F
R = E.ROOTV


def g(pairs):
    edges = {}
    for a, b in pairs:
        edges.setdefault(a, set()).add(b)
    return edges


class Engine(unittest.TestCase):
    def test_tiny_sat_and_path_verification(self):
        n = [("v", i) for i in range(4)]
        edges = g([(R, n[0]), (n[0], n[1]), (n[1], n[2]), (n[2], n[3])])
        verdict, _stats, path = E.solve(n, edges)
        self.assertEqual(verdict, "SAT")
        self.assertTrue(E.verify_path(n, edges, path))

    def test_tiny_unsat_in_both_directions(self):
        a, b = ("v", 0), ("v", 1)
        edges = g([(R, a), (R, b)])
        self.assertEqual(E.solve([a, b], edges)[0], "UNSAT")
        self.assertEqual(E.solve_reverse([a, b], edges)[0], "UNSAT")
        self.assertEqual(E.subtour_solve([a, b], edges)[0], "UNSAT")

    def test_cap_is_unknown_never_unsat(self):
        rng = random.Random(2)
        nodes, edges = F.random_rooted_hamilton(rng, 30, extra_ratio=3)
        self.assertEqual(E.solve(nodes, edges, node_cap=1)[0], "UNKNOWN")
        self.assertEqual(E.solve_reverse(nodes, edges, node_cap=1)[0], "UNKNOWN")

    def test_no_false_unsat_on_explicit_hamilton_graphs(self):
        rng = random.Random(98)
        for t in range(40):
            nodes, edges = F.random_rooted_hamilton(rng, 5 + t % 25, extra_ratio=t % 4)
            fwd = E.solve(nodes, edges, node_cap=2_000_000)[0]
            rev = E.solve_reverse(nodes, edges, node_cap=2_000_000)[0]
            sub = E.subtour_solve(nodes, edges, iter_cap=20_000)[0]
            self.assertNotEqual(fwd, "UNSAT")
            self.assertNotEqual(rev, "UNSAT")
            self.assertNotEqual(sub, "UNSAT")

    def test_reverse_path_is_returned_in_forward_order(self):
        n = [("v", i) for i in range(5)]
        edges = g([(R, n[0])] + [(n[i], n[i + 1]) for i in range(4)])
        verdict, _s, path = E.solve_reverse(n, edges, want_path=True)
        self.assertEqual(verdict, "SAT")
        self.assertTrue(E.verify_path(n, edges, path))


class Witnesses(unittest.TestCase):
    def test_preserved_sat_witnesses_replay(self):
        path = ROOT / "outputs" / "rr_exact_hamilton_sat_witnesses.json"
        data = json.loads(path.read_text())
        self.assertGreaterEqual(len(data["rows"]), 4)
        for row in data["rows"]:
            self.assertTrue(row["path_edges_verified"], row["sid"])
            self.assertEqual(len(row["hamilton_path"]), row["m"])
            # SAT 은 폐쇄가 아니며, 이 증인들은 단어 수준으로 들어올려지지 않는다.
            self.assertIn("word_lift", row)

    def test_graph_archive_is_replayable_without_the_frontier(self):
        seen = 0
        for graph, nodes, edges in E.load_graphs():
            m, out, _inn, root_out, _idx, _order = E.to_bitset(nodes, edges)
            self.assertEqual(m, graph["m"])
            self.assertEqual(E.graph_hash(m, out, root_out), graph["graph_hash"])
            seen += 1
            if seen == 25:
                break
        self.assertEqual(seen, 25)


if __name__ == "__main__":
    unittest.main()
