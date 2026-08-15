"""라운드 93c — Hall 감사 아카이브가 독립 검증기로 재생되는지 (빠른 조각 검사).

전수 재생은 수 분이 걸리므로, 테스트에서는 앞쪽 상태 조각만 검사한다. 전수 재생은
`python3 src/verify_rr_port_path_hall_archive.py` 로 별도 실행한다.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "outputs" / "rr_port_path_hall_archive"
_spec = importlib.util.spec_from_file_location(
    "verify_rr_port_path_hall_archive", ROOT / "src" / "verify_rr_port_path_hall_archive.py")
V = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = V
_spec.loader.exec_module(V)
SLICE = 40


class HallArchiveReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, geo_rows = V.read_jsonl(ARCHIVE / "geometry.jsonl.gz")
        cls.geo, cls.hex_words = V.build_geometry(geo_rows)
        _, cls.states = V.read_jsonl(ARCHIVE / "states.jsonl.gz")
        _, covers = V.read_jsonl(ARCHIVE / "covers.jsonl.gz")
        cls.summary = json.load(open(ARCHIVE / "summary.json"))
        keep = {s["sid"] for s in cls.states[:SLICE]}
        cls.covers = [c for c in covers if c["sid"] in keep]
        _, sat = V.read_jsonl(ARCHIVE / "sat_witnesses.jsonl.gz")
        cls.sat = {w["sid"]: w for w in sat}

    def test_geometry_is_a_pinned_bijection(self):
        self.assertEqual(len(self.geo), 720)
        ports = {(g["orbit"], g["phase"]) for g in self.geo.values()}
        cells = {(g["hexagon"], g["hex_index"]) for g in self.geo.values()}
        self.assertEqual(len(ports), 720)
        self.assertEqual(len(cells), 720)

    def test_state_rows_are_internally_consistent(self):
        for s in self.states[:SLICE]:
            self.assertEqual(V.check_state(s, self.geo, self.hex_words), [], s["sid"])

    def test_stored_hall_results_match_a_fresh_recomputation(self):
        _, stored = V.read_jsonl(ARCHIVE / "hall_results.jsonl.gz")
        by = {(h["sid"], h["cover_id"]): h for h in stored}
        checked = 0
        for s in self.states[:SLICE]:
            for c in [c for c in self.covers if c["sid"] == s["sid"]]:
                left, _slots, _cand, adjacency = V.hall_graph(
                    s, c["orbits"], self.geo, self.hex_words)
                pair = V.max_matching(left, adjacency)
                h = by[(s["sid"], c["cover_id"])]
                self.assertEqual(h["left"], len(left))
                self.assertEqual(h["deficit"], len(left) - len(pair))
                checked += 1
        self.assertGreater(checked, 0)

    def test_stored_sat_matchings_are_legal_and_injective(self):
        checked = 0
        for s in self.states[:SLICE]:
            w = self.sat.get(s["sid"])
            if not w:
                continue
            cover = next(c for c in self.covers
                         if c["sid"] == s["sid"] and c["cover_id"] == w["cover_id"])
            left, _slots, _cand, adjacency = V.hall_graph(
                s, cover["orbits"], self.geo, self.hex_words)
            used = set()
            for l, sl in w["matching"]:
                ln, sn = tuple(l), tuple(sl)
                self.assertIn(sn, adjacency[ln])
                self.assertNotIn(sn, used)
                used.add(sn)
            self.assertEqual(len(w["matching"]), len(left))
            checked += 1
        self.assertGreater(checked, 0)

    def test_summary_records_the_claude_reproduced_counts(self):
        self.assertEqual(self.summary["aggregate"], {"SAT": 5030, "UNSAT": 1366})
        self.assertEqual(self.summary["unsat_state_min_deficit"],
                         {"1": 1206, "2": 156, "3": 4})


if __name__ == "__main__":
    unittest.main()
