"""라운드 101 — 단어 도메인 census 와 국소 일관성 층(W-C/W-D)의 건전성."""

from __future__ import annotations

import gzip
import importlib.util
import json
import random
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


C = _load("probe_rr_word_csp", "src/probe_rr_word_csp.py")


class Domains(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.word_of, cls.orbit, cls.hexm, cls.jt, cls.states, cls.covers = C.load()
        cls.rows = C.wa_pairs()

    def test_wa_survivor_counts(self):
        self.assertEqual(len(self.rows), 15781)
        self.assertEqual(len({r["sid"] for r in self.rows}), 4230)

    def test_domains_never_exceed_two(self):
        rng = random.Random(3)
        sample = rng.sample(self.rows, 300)
        seen = Counter()
        for r in sample:
            ctx = C.context(self.states[r["sid"]],
                            self.covers[(r["sid"], r["cover_id"])]["orbits"],
                            self.orbit, self.hexm, self.jt)
            for words in ctx["cand"].values():
                self.assertGreaterEqual(len(words), 1)
                self.assertLessEqual(len(words), 2)
                seen[len(words)] += 1
        self.assertGreater(seen[1], 10 * seen[2])      # singleton 이 압도적

    def test_word_next_stays_a_partial_function_on_live_domains(self):
        rng = random.Random(5)
        for r in rng.sample(self.rows, 40):
            ctx = C.context(self.states[r["sid"]],
                            self.covers[(r["sid"], r["cover_id"])]["orbits"],
                            self.orbit, self.hexm, self.jt)
            owner = C._owner(ctx["cand"])
            for node, words in ctx["cand"].items():
                for u in words:
                    succ = C._succ(ctx, self.jt, owner, node, u)
                    self.assertLessEqual(len(succ), 4)
                    self.assertNotIn(node, succ)       # 자기 육각형으로는 못 간다


class Layers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.word_of, cls.orbit, cls.hexm, cls.jt, cls.states, cls.covers = C.load()

    def _ctx(self, sid, cid):
        return C.context(self.states[sid], self.covers[(sid, cid)]["orbits"],
                         self.orbit, self.hexm, self.jt)

    def test_lift_passing_witnesses_are_not_rejected(self):
        """거짓 거부 0 — 실제로 들어올려진 증인은 모든 층을 통과해야 한다."""
        with gzip.open(ROOT / "outputs" / "rr_word_lift_witnesses.jsonl.gz", "rt") as fh:
            fh.readline()
            passers = [json.loads(x) for x in fh]
        passers = [w for w in passers if w["lift"] == "LIFT_PASS"]
        gid = {}
        with gzip.open(ROOT / "outputs" / "rr_exact_hamilton_graphs.jsonl.gz", "rt") as fh:
            fh.readline()
            for line in fh:
                g = json.loads(line)
                gid[g["sid"]] = g["cover_id"]
        self.assertGreaterEqual(len(passers), 27)
        for w in passers[:12]:
            ctx = self._ctx(w["sid"], gid[w["sid"]])
            self.assertEqual(C.arc_consistency(ctx, self.jt)[0], "PASS", w["sid"])
            self.assertEqual(C.hall_matching(ctx, self.jt)[0], "PASS", w["sid"])
            for step in w["chain"]:
                self.assertIn(step["word_id"], ctx["cand"][tuple(step["node"])])

    def test_archive_rows_match_a_recomputation(self):
        path = ROOT / "outputs" / "rr_word_lift_archive" / "wc_wd.jsonl.gz"
        with gzip.open(path, "rt") as fh:
            header = json.loads(fh.readline())
            rows = [json.loads(x) for _i, x in zip(range(40), fh)]
        self.assertEqual(header["schema"], "rr_word_lift_archive.wc_wd/1")
        self.assertIn("depends_on", header)
        for row in rows:
            ctx = self._ctx(row["sid"], row["cover_id"])
            verdict = C.arc_consistency(ctx, self.jt)[0]
            if verdict == "PASS":
                verdict = C.hall_matching(ctx, self.jt)[0]
            self.assertEqual(verdict, row["pair_verdict"], row["sid"])

    def test_round101_closed_no_state(self):
        with gzip.open(ROOT / "outputs" / "rr_word_csp_ledger.jsonl.gz", "rt") as fh:
            header = json.loads(fh.readline())
            rows = [json.loads(x) for x in fh]
        self.assertEqual(header["state_closures"], 0)
        self.assertEqual(rows, [])
        self.assertEqual(header["pair_verdicts"].get("W_C_TWO_TERMINALS"), 5)


if __name__ == "__main__":
    unittest.main()
