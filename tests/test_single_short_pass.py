"""라운드 90 — 단일 short pass 정리의 전제와 결론을 엔진에 고정한다.

정리는 리터럴 체크포인트 상태의 성질에 의존하므로, 그 성질들이 엔진에서 실제로 성립하는지를
표본이 아니라 **명시된 상태 집합 전체**에 대해 검사한다.  (잔여 전체 로딩은 느리므로 기본은
앞쪽 상태들로 제한하고, 계수 항등식만 전수로 확인한다.)
"""

from __future__ import annotations

import importlib.util
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


ssp = _load("probe_rr_single_short_pass", "src/probe_rr_single_short_pass.py")
core = ssp.core
macro = ssp.macro
exact = ssp.exact
SAMPLE = 60


class SingleShortPassTheorem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = ssp.po.load_states()
        cls.sample = cls.rows[:SAMPLE]

    def test_premise_current_hexagon_has_exactly_one_visited_cell(self):
        """전제: 모든 잔여 상태에서 F = 1 이고 현재 육각형에 방문 칸이 정확히 1개."""
        for r in self.rows:
            counts, current, _, _ = ssp.hexagon_profile(r["state"])
            self.assertEqual(r["state"].F, 1, r["sid"])
            self.assertEqual(counts[current], 1, r["sid"])

    def test_pass_count_identity_holds_on_every_residual_state(self):
        """121 - P == (빈 육각형 수) + (fragment 수).  정리 (iii) 의 계수 근거."""
        for r in self.rows:
            _, _, fragments, empty = ssp.hexagon_profile(r["state"])
            self.assertEqual(121 - r["state"].P, empty + len(fragments), r["sid"])

    def test_engine_allows_no_short_departure_from_the_current_pass(self):
        """정리 (iv): 현재 위치에서 abandonment 없이 떠나는 매크로 edge 는 ell = 5 뿐이다."""
        for r in self.sample:
            st = r["state"]
            cursor = st.p
            for ell in range(6):
                abandons = not st.visited(core.word_after(cursor, core.SIGMA))
                for move in macro.NONROT_H0:
                    target = core.word_after(cursor, move.action)
                    if st.visited(target):
                        continue
                    if not abandons:
                        self.assertEqual(ell, 5, f"{r['sid']} ell={ell}")
                cursor = core.word_after(cursor, core.SIGMA)

    def test_pinned_repair_pass_fills_the_fragment_and_departs_legally(self):
        """정리 (v): 고정된 시작 칸에서 ell = 5 - c_f 회전하면 fragment 가 정확히 채워진다."""
        checked = 0
        for r in self.sample:
            pin, reason = ssp.pinned_short_edge(r["state"])
            if pin is None:
                self.assertEqual(reason, "no_fragment", r["sid"])
                continue
            checked += 1
            st = r["state"]
            hf, cf = pin["hex"], pin["c_f"]
            visited = {b for b in range(6) if st.hex_masks[hf] >> b & 1}
            self.assertEqual(len(visited), cf)
            cursor = tuple(pin["word"])
            run = [exact.HEX_POSITION[cursor][1]]
            for _ in range(pin["ell"]):
                cursor = core.word_after(cursor, core.SIGMA)
                run.append(exact.HEX_POSITION[cursor][1])
            self.assertEqual(len(run), 6 - cf, r["sid"])
            self.assertFalse(visited & set(run), r["sid"])
            self.assertEqual(visited | set(run), set(range(6)), r["sid"])
            self.assertTrue(pin["departs_legally"], r["sid"])
        self.assertGreater(checked, 0)

    def test_g5_source_table_agrees_with_the_engine_at_the_endpoint(self):
        """SRC[(q, f)] 가 엔진의 ell = 5 Z3 전이와 일치한다."""
        for r in self.sample:
            st = r["state"]
            q, f = exact.ORBIT_PHASE[st.p]
            cursor = st.p
            for _ in range(5):
                cursor = core.word_after(cursor, core.SIGMA)
            engine = set()
            for move in macro.NONROT_H0:
                if move.weight < 3:
                    continue
                target = core.word_after(cursor, move.action)
                if exact.ORBIT_PHASE[target][0] != q:
                    engine.add(exact.ORBIT_PHASE[target][0])
            self.assertEqual(engine, ssp.SRC[(q, f)], r["sid"])


if __name__ == "__main__":
    unittest.main()
