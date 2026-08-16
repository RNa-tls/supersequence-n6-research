"""라운드 100 — 독립 재구현(문자열 기하)과 라운드-99 결과의 일치 검사."""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "outputs" / "rr_word_lift_archive"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("replay_rr_word_lift", "src/replay_rr_word_lift.py")


class StringGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _h, cls.geo = R.read_jsonl(R.ARCHIVE / "geometry.jsonl.gz")
        cls.word_of, cls.id_of, cls.klass, cls.jt, cls.agree = R.build_geometry(cls.geo)

    def test_hexagon_is_the_cyclic_rotation_class(self):
        self.assertTrue(self.agree)

    def test_string_rule_matches_the_archive_everywhere(self):
        res = R.cross_check_joint_targets(self.geo, self.jt)
        self.assertEqual(res["contexts"], 4320)
        self.assertEqual(res["mismatches"], 0)

    def test_geometry_theorem_has_no_violations(self):
        res = R.geometry_theorem(self.geo, self.klass, self.jt)
        self.assertEqual(res["not_four_distinct"], 0)
        self.assertEqual(res["target_in_source_class"], 0)

    def test_structural_proof_argument_on_a_symbolic_word(self):
        """구조적 증명이 쓰는 여섯 비교를 기호 수준에서 확인한다."""
        x = "abcdef"
        t = R.joint_words(x)
        def succ(w):
            return {w[i]: w[(i + 1) % 6] for i in range(6)}
        base = succ(x)
        ss = [succ(y) for y in t]
        for s in ss:                       # x 와 구분: x5 의 상이 다르다
            self.assertNotEqual(s[x[5]], base[x[5]])
        for i in range(4):                 # 서로 구분
            for j in range(i + 1, 4):
                self.assertNotEqual(ss[i], ss[j])


class ReplayAgreement(unittest.TestCase):
    def test_archive_summary_matches_round99_counts(self):
        summary = json.loads((ARCH / "summary.json").read_text())
        self.assertEqual(summary["pair_verdicts"]["PASS"], 15781)
        self.assertEqual(summary["state_verdicts"]["SAT"], 4230)
        self.assertEqual(summary["state_closures"], 564)
        self.assertEqual(summary["joint_target_cross_check"]["mismatches"], 0)

    def test_new_closure_set_is_exactly_the_round99_552(self):
        audited = {"6273274c", "cca008e3", "7921d0cb", "714d11e1",
                   "06316dbd", "0e05f78b", "3671f68a", "58187879",
                   "5b288103", "63bf8513", "fec4a172", "77fbaf89"}
        with gzip.open(ARCH / "closures.jsonl.gz", "rt") as fh:
            fh.readline()
            new = {json.loads(line)["sid"] for line in fh}
        with gzip.open(ROOT / "outputs" / "rr_word_lift_static_ledger.jsonl.gz", "rt") as fh:
            fh.readline()
            old = {json.loads(line)["sid"] for line in fh}
        new_only = {s for s in new if s[:8] not in audited}
        old_only = {s for s in old if s[:8] not in audited}
        self.assertEqual(len(new_only), 552)
        self.assertEqual(new_only, old_only)

    def test_every_closure_row_has_all_covers_failing(self):
        with gzip.open(ARCH / "closures.jsonl.gz", "rt") as fh:
            fh.readline()
            for line in fh:
                row = json.loads(line)
                self.assertTrue(row["all_surviving_covers_fail"])
                self.assertTrue(all(p["pair_verdict"] != "PASS" for p in row["per_cover"]))
                self.assertEqual(row["surviving_covers"], len(row["per_cover"]))

    def test_memo_control_found_no_decisive_disagreement(self):
        data = json.loads((ROOT / "outputs" / "rr_word_lift_integrated_pilot.json").read_text())
        self.assertEqual(data["decisive_disagreements"], 0)
        for row in data["rows"]:
            a, b = row["memo"]["verdict"], row["no_memo"]["verdict"]
            if "UNKNOWN" not in (a, b):
                self.assertEqual(a, b, row["sid"])


if __name__ == "__main__":
    unittest.main()
