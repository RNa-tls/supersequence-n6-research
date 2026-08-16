"""라운드 99 — 단어 lift 의 기하 정리와 lift DP/탐색의 건전성.

전수 재검증은 `python3 src/verify_rr_word_lift.py` 로 따로 돈다.
"""

from __future__ import annotations

import gzip
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


W = _load("probe_rr_word_lift", "src/probe_rr_word_lift.py")
V = _load("verify_rr_word_lift", "src/verify_rr_word_lift.py")


class GeometryTheorem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geo, cls.hexw, cls.byid, cls.cov = W._load()

    def test_four_joint_targets_lie_in_four_distinct_hexagons(self):
        res = W.geometry_census(self.geo)
        self.assertEqual(res["contexts"], 4320)
        self.assertEqual(res["distinct_target_hexagons"], {4: 4320})
        self.assertEqual(res["max_targets_in_one_hexagon"], 1)
        self.assertEqual(res["targets_in_source_hexagon"], 0)
        self.assertTrue(res["word_next_is_a_partial_function"])

    def test_word_next_is_a_partial_function_on_real_contexts(self):
        seen = 0
        for graph, _nodes, _edges in __import__("probe_rr_exact_hamilton").load_graphs():
            ctx = W.lift_context(self.byid[graph["sid"]],
                                 self.cov[(graph["sid"], graph["cover_id"])]["orbits"],
                                 self.geo, self.hexw)
            for node, words in ctx["cand"].items():
                for w in words:
                    got = W.word_next(ctx, self.geo, w, ctx["ell"][node])
                    self.assertLessEqual(len(got), 4)
                    self.assertEqual(len(got), len(set(got)))
            seen += 1
            if seen == 5:
                break
        self.assertEqual(seen, 5)


class LiftSoundness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geo, cls.hexw, cls.byid, cls.cov = W._load()

    def test_engine_built_chains_are_accepted_by_the_dp(self):
        """§7 양성 대조: 엔진 전이로 만든 합법 사슬을 DP 가 거부하면 모델이 틀린 것이다."""
        import random
        EH = __import__("probe_rr_exact_hamilton")
        rng = random.Random(7)
        checked = 0
        for graph, _nodes, _edges in EH.load_graphs():
            ctx = W.lift_context(self.byid[graph["sid"]],
                                 self.cov[(graph["sid"], graph["cover_id"])]["orbits"],
                                 self.geo, self.hexw)
            u, ell = ctx["root_word"], ctx["root_ell"]
            chain, used, obl = [], set(), set()
            while True:
                opts = [(n, v) for n, v in W.word_next(ctx, self.geo, u, ell).items()
                        if n not in obl and v not in used]
                if not opts:
                    break
                n, v = rng.choice(opts)
                chain.append((n, v))
                used.add(v)
                obl.add(n)
                u, ell = v, ctx["ell"][n]
            if len(chain) < 3:
                continue
            res = W.lift_path(ctx, self.geo, [list(n) for n, _v in chain])
            self.assertEqual(res["lift"], "LIFT_PASS", graph["sid"])
            self.assertEqual([c["word_id"] for c in res["chain"]], [v for _n, v in chain])
            self.assertEqual(max(res["widths"]), 1)      # 결정적 lift
            checked += 1
            if checked == 6:
                break
        self.assertEqual(checked, 6)

    def test_static_closures_have_all_covers_failing(self):
        path = ROOT / "outputs" / "rr_word_lift_static_ledger.jsonl.gz"
        with gzip.open(path, "rt") as fh:
            header = json.loads(fh.readline())
            rows = [json.loads(line) for line in fh]
        self.assertEqual(header["schema"], "rr_word_lift_static/1")
        self.assertTrue(all(r["all_surviving_covers_fail"] for r in rows))
        for r in rows:
            self.assertTrue(all(p["pair_verdict"] != "PASS" for p in r["per_cover"]), r["sid"])
        self.assertEqual(len(rows), header["state_closed"])

    def test_independent_verifier_agrees_on_a_slice(self):
        geo, hex_words, states, covers = V.load()
        path = ROOT / "outputs" / "rr_word_lift_static_ledger.jsonl.gz"
        with gzip.open(path, "rt") as fh:
            fh.readline()
            rows = [json.loads(line) for _i, line in zip(range(15), fh)]
        for row in rows:
            st = states[row["sid"]]
            for per in row["per_cover"]:
                cand, owner, ell, p = V.build(
                    st, covers[(row["sid"], per["cover_id"])]["orbits"], geo, hex_words)
                got, _cert = V.verdict_for(geo, cand, owner, ell, p)
                self.assertEqual(got, per["pair_verdict"], row["sid"])


if __name__ == "__main__":
    unittest.main()
