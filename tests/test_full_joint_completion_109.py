"""라운드 109 — 166개 잔여 상태의 완전-joint 마무리를 회귀로 고정한다.

감사 원장(4,782)은 건드리지 않는다.  이 테스트들이 지키는 것은 세 가지다:
캡 도달이 폐쇄로 새지 않을 것, (H5) 가 다시 기어들어오지 않을 것,
그리고 판정이 frontier-empty 에서만 나올 것.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
AUD = OUT / "rr_h5_audit"


def stages():
    out = {}
    for st, f in ((1, "rr_round109_stage1.jsonl"), (2, "rr_round109_stage2.jsonl"),
                  (3, "rr_round109_stage3.jsonl")):
        for line in open(OUT / f):
            r = json.loads(line)
            out[r["sid"]] = {**r, "stage": st}
    return out


def summary():
    return json.loads((OUT / "rr_round109_summary.json").read_text())


class FrozenInput(unittest.TestCase):
    def test_the_166_are_frozen_and_hashed(self):
        d = json.loads((AUD / "round109_input_states.json").read_text())
        self.assertEqual(d["count"], 166)
        self.assertEqual(len(set(d["sids"])), 166)
        h = hashlib.sha256("\n".join(sorted(d["sids"])).encode()).hexdigest()
        self.assertEqual(h, d["sha256_of_sorted_sids"])
        self.assertEqual(h, "d5d93ab87b37eec6077e995c2f2fadcb692"
                             "da408f2fb6d0d48245c629e156b85")

    def test_they_were_unknown_only_because_of_the_cap(self):
        v = json.loads((AUD / "round109_input_states.json").read_text())["verified"]
        self.assertTrue(v["subset_of_6396_population"])
        self.assertTrue(v["subset_of_1353_conditional"])
        self.assertTrue(v["disjoint_from_5043_robust"])
        self.assertEqual(v["states_with_a_SAT_pair"], 0)
        self.assertEqual(v["states_with_no_UNKNOWN_pair"], 0)
        self.assertEqual(v["states_with_a_stored_witness"], 0)


class RegressionControl(unittest.TestCase):
    def test_the_old_cap_still_reproduces_unknown(self):
        rows = [json.loads(l) for l in open(OUT / "rr_round109_regression.jsonl")]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["cap"] == 2500 for r in rows))
        self.assertTrue(all(r["verdict"] == "UNKNOWN_CAP" for r in rows))

    def test_the_same_states_close_once_the_cap_is_raised(self):
        rows = [json.loads(l) for l in open(OUT / "rr_round109_calib.jsonl")]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["cap"] == 50000 for r in rows))
        self.assertTrue(all(r["verdict"] == "UNSAT_COMPLETE" for r in rows))


class StagedRuns(unittest.TestCase):
    def test_every_frozen_state_has_exactly_one_final_verdict(self):
        d = stages()
        frozen = set(json.loads((AUD / "round109_input_states.json").read_text())["sids"])
        self.assertEqual(set(d), frozen)
        self.assertEqual(len(d), 166)

    def test_all_166_are_unsat_complete(self):
        self.assertEqual(Counter(r["verdict"] for r in stages().values()),
                         {"UNSAT_COMPLETE": 166})

    def test_caps_were_per_call_and_escalated(self):
        self.assertEqual([s["cap"] for s in summary()["stages"]], [50000, 400000, 3000000])
        self.assertEqual([s["unsat_complete"] for s in summary()["stages"]], [104, 47, 15])
        self.assertEqual([s["unknown"] for s in summary()["stages"]], [62, 15, 0])


class SoundnessGuards(unittest.TestCase):
    def test_no_verdict_rests_on_a_non_empty_frontier(self):
        for r in stages().values():
            self.assertTrue(r["frontier_exhausted"], r["sid"])
            self.assertEqual(r["unknown"], 0, r["sid"])

    def test_H5_is_never_used_and_all_550_tails_are_live(self):
        for f in ("rr_round109_stage1.jsonl", "rr_round109_stage2.jsonl",
                  "rr_round109_stage3.jsonl", "rr_round109_regression.jsonl",
                  "rr_round109_calib.jsonl"):
            for line in open(OUT / f):
                r = json.loads(line)
                self.assertFalse(r["h5_used"], f)
                self.assertEqual(r["tails"], 550, f)

    def test_no_SAT_and_no_witness_anywhere(self):
        for f in ("rr_round109_stage1.jsonl", "rr_round109_stage2.jsonl",
                  "rr_round109_stage3.jsonl"):
            for line in open(OUT / f):
                r = json.loads(line)
                self.assertEqual(r["sat"], 0)
                self.assertNotEqual(r["verdict"], "SAT")
                self.assertNotIn("sat_witness", r)

    def test_a_cap_hit_is_never_counted_as_a_closure(self):
        """1·2 단계의 UNKNOWN_CAP 은 폐쇄로 세지 않고 다음 단계로 넘어갔다."""
        s1 = [json.loads(l) for l in open(OUT / "rr_round109_stage1.jsonl")]
        s2 = [json.loads(l) for l in open(OUT / "rr_round109_stage2.jsonl")]
        k1 = {r["sid"] for r in s1 if r["verdict"] == "UNKNOWN_CAP"}
        self.assertEqual(len(k1), 62)
        self.assertEqual({r["sid"] for r in s2}, k1)
        for r in s1 + s2:
            if r["verdict"] == "UNKNOWN_CAP":
                self.assertGreater(r["unknown"], 0)
                self.assertFalse(r["frontier_exhausted"])


class Certificate(unittest.TestCase):
    def test_certificate_covers_every_state_with_an_empty_frontier(self):
        with gzip.open(OUT / "rr_round109_certificate.jsonl.gz", "rt") as fh:
            head = json.loads(fh.readline())
            rows = [json.loads(l) for l in fh]
        self.assertEqual(head["rows"], 166)
        self.assertTrue(head["all_unsat_complete"])
        self.assertFalse(head["model"]["h5_used"])
        self.assertEqual(head["model"]["tails"], 550)
        self.assertEqual(len(rows), 166)
        self.assertTrue(all(r["frontier_exhausted"] for r in rows))

    def test_population_totals(self):
        q = summary()["q2_full_joint"]
        self.assertEqual(q["from_round_108"] + q["from_round_109"], 6396)
        self.assertEqual(q["unsat_complete"], 6396)
        self.assertEqual(q["unknown"], 0)
        self.assertEqual(q["sat"], 0)


class LedgerDiscipline(unittest.TestCase):
    def test_audited_ledger_is_untouched(self):
        self.assertEqual(summary()["ledger"]["INDEPENDENTLY_AUDITED"], 4782)

    def test_document_keeps_the_scope_disclaimer(self):
        txt = (ROOT / "research" / "RR_FULL_JOINT_COMPLETION_109_CLAUDE.md").read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)
        self.assertIn("Q1/NR6", txt)
        self.assertNotIn("L6 >= 872 proved", txt)
        # 감사 주장을 하지 않는다는 문장이 명시적으로 들어 있어야 한다
        self.assertIn("어떤 값도 독립 감사됐다고 부르지 않는다", txt)
        self.assertIn("독립 감사를 받지 않았다", txt)


if __name__ == "__main__":
    unittest.main()
