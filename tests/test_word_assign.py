"""라운드 102 — 이진 단어 배정 열거와 W-E 층의 건전성."""

from __future__ import annotations

import gzip
import importlib.util
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


W = _load("probe_rr_word_assign", "src/probe_rr_word_assign.py")
C = W.C


class Assignments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.word_of, cls.orbit, cls.hexm, cls.jt, cls.states, cls.covers = C.load()
        cls.rows = C.wa_pairs()

    def test_binary_dimension_never_exceeds_four(self):
        rng = random.Random(11)
        for r in rng.sample(self.rows, 250):
            ctx = C.context(self.states[r["sid"]],
                            self.covers[(r["sid"], r["cover_id"])]["orbits"],
                            self.orbit, self.hexm, self.jt)
            k = sum(1 for v in ctx["cand"].values() if len(v) == 2)
            self.assertLessEqual(k, 4)

    def test_assignment_count_is_two_to_the_k(self):
        rng = random.Random(13)
        for r in rng.sample(self.rows, 25):
            ctx = C.context(self.states[r["sid"]],
                            self.covers[(r["sid"], r["cover_id"])]["orbits"],
                            self.orbit, self.hexm, self.jt)
            cand = W.propagate_domains(ctx, self.jt)
            if cand is None:
                continue
            k = sum(1 for v in cand.values() if len(v) == 2)
            got = list(W.assignments(cand))
            self.assertEqual(len(got), 2 ** k)
            for A, _binary in got:
                self.assertEqual(len(A), len(cand))
                for h, u in A.items():
                    self.assertIn(u, cand[h])

    def test_graph_edges_use_exact_word_compatibility(self):
        rng = random.Random(17)
        for r in rng.sample(self.rows, 15):
            ctx = C.context(self.states[r["sid"]],
                            self.covers[(r["sid"], r["cover_id"])]["orbits"],
                            self.orbit, self.hexm, self.jt)
            cand = W.propagate_domains(ctx, self.jt)
            if cand is None:
                continue
            A, _b = next(W.assignments(cand))
            nodes, edges = W.graph_of(A, ctx, self.jt)
            for h, targets in edges.items():
                if h == W.ROOTV:
                    continue
                for g in targets:
                    self.assertIn(A[g], self.jt[A[h]][ctx["ell"][h]])
                    self.assertNotEqual(h, g)

    def test_propagation_only_removes_unsupported_words(self):
        """전파는 지지 없는 후보만 지운다 — 남은 도메인은 항상 원래 도메인의 부분집합."""
        rng = random.Random(19)
        for r in rng.sample(self.rows, 30):
            ctx = C.context(self.states[r["sid"]],
                            self.covers[(r["sid"], r["cover_id"])]["orbits"],
                            self.orbit, self.hexm, self.jt)
            cand = W.propagate_domains(ctx, self.jt)
            if cand is None:
                continue
            for h, ws in cand.items():
                self.assertTrue(ws <= ctx["cand"][h])


class Ledger(unittest.TestCase):
    def test_we_archive_is_consistent(self):
        path = ROOT / "outputs" / "rr_word_assign_we.jsonl.gz"
        with gzip.open(path, "rt") as fh:
            header = json.loads(fh.readline())
            rows = [json.loads(line) for line in fh]
        self.assertEqual(header["schema"], "rr_word_assign_we/1")
        self.assertIn("depends_on", header)
        closures = [r for r in rows if r.get("record") == "state_closures"]
        self.assertEqual(len(closures), 1)
        self.assertEqual(len(closures[0]["sids"]), header["state_closures"])
        detail = [r for r in rows if "record" not in r]
        self.assertEqual(len(detail), header["pairs"])
        for r in detail:
            if r["verdict"] == "FAIL" and "surviving" in r:
                self.assertEqual(r["surviving"], 0)
            if r["verdict"] == "PASS":
                self.assertGreater(r["surviving"], 0)

    def test_exact_stage_reports_no_extra_closure(self):
        data = json.loads((ROOT / "outputs" / "rr_word_assign_exact.json").read_text())
        unsat = [r for r in data["rows"] if r["cover_verdict"] == "LITERAL_GRAPH_UNSAT"]
        for r in unsat:
            # 이번 라운드의 UNSAT 은 전부 정적으로 죽은 배정들이었다
            self.assertTrue(all(a["verdict"] == "UNSAT_STATIC"
                                for a in r["assignment_verdicts"]), r["sid"])
        sat = [r for r in data["rows"] if r["cover_verdict"] == "LITERAL_GRAPH_SAT"]
        for r in sat:
            self.assertIn("hamilton_witness", r)
            w = r["hamilton_witness"]
            self.assertEqual(len(w["obligation_order"]), len(w["word_order"]))


if __name__ == "__main__":
    unittest.main()
