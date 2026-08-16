"""라운드 103 — literal 엔진 재생과 W-E 독립 재생의 검사."""

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


L = _load("replay_rr_literal_engine", "src/replay_rr_literal_engine.py")


class Engine(unittest.TestCase):
    def test_joint_weights_split_one_cheap_three_expensive(self):
        """T1 은 weight 2, T2/T3/T4 는 weight 3 — 이번 라운드가 찾은 좌표의 근거."""
        core = L.core
        x = "012345"
        xp = tuple(int(c) for c in x)
        targets = [x[2] + x[3] + x[4] + x[5] + x[1] + x[0],
                   x[3] + x[4] + x[5] + x[1] + x[2] + x[0],
                   x[3] + x[4] + x[5] + x[2] + x[0] + x[1],
                   x[3] + x[4] + x[5] + x[2] + x[1] + x[0]]
        weights = []
        for t in targets:
            tp = tuple(int(c) for c in t)
            ws = [m.weight for m in L.JOINTS if core.word_after(xp, m.action) == tp]
            weights.append(min(ws))
        self.assertEqual(weights, [2, 3, 3, 3])

    def test_state_reconstruction_round_trips(self):
        states = L.load_states()
        for sid, rec in list(states.items())[:5]:
            st = L.exact_state(rec)
            self.assertEqual("".join(map(str, st.p)), rec["p"])
            self.assertEqual(st.P, rec["P"])
            self.assertEqual(st.O, rec["O"])
            self.assertEqual(st.D, rec["D"])

    def test_ndef_identity(self):
        states = L.load_states()
        for sid, rec in list(states.items())[:5]:
            st = L.exact_state(rec)
            self.assertEqual(st.Ndef, st.S + st.F - st.O)


class Replays(unittest.TestCase):
    def test_all_preserved_witnesses_replayed_literally(self):
        data = json.loads((ROOT / "outputs" / "rr_literal_replay.json").read_text())
        self.assertEqual(data["witnesses"], 22)
        self.assertEqual(data["verdicts"], {"LITERAL_REPLAY_PASS": 22})
        for row in data["rows"]:
            self.assertEqual(row["verdict"], "LITERAL_REPLAY_PASS")
            self.assertGreaterEqual(row["steps_replayed"], 100)

    def test_witnesses_hit_the_counter_targets_but_not_the_budget(self):
        """반드시 함께 기록한다 — 카운터는 맞지만 N+H 예산은 어긴다."""
        data = json.loads((ROOT / "outputs" / "rr_literal_replay.json").read_text())
        for row in data["rows"]:
            end = row["end"]
            self.assertEqual((end["F"], end["P"], end["O"], end["D"]), (1, 121, 25, 4))

    def test_independent_we_replay_matches_round_102(self):
        rep = json.loads((ROOT / "outputs" / "rr_word_assign_replay.json").read_text())
        self.assertEqual(rep["pairs"], 15781)
        self.assertEqual(rep["assignments"], 173409)
        self.assertEqual(rep["pair_verdicts"], {"PASS": 10552, "FAIL": 5229})
        self.assertEqual(rep["assignments_killed_by_layer"],
                         {"A": 100174, "B2": 31434, "D4": 6188, "D1": 37})
        self.assertEqual(rep["state_closures"], 178)
        self.assertEqual(rep["k_raw"],
                         {"0": 233, "1": 289, "2": 1698, "3": 5667, "4": 7894})

    def test_178_sid_set_is_stable_and_disjoint_from_the_552(self):
        import gzip
        new = set(json.loads((ROOT / "outputs" / "rr_word_assign_178_sids.json").read_text()))
        self.assertEqual(len(new), 178)
        with gzip.open(ROOT / "outputs" / "rr_word_lift_static_ledger.jsonl.gz", "rt") as fh:
            fh.readline()
            wa_closed = {json.loads(line)["sid"] for line in fh}
        self.assertEqual(new & wa_closed, set())


if __name__ == "__main__":
    unittest.main()
