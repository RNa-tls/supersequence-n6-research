"""라운드 113 — hub defect 정리와 그 빠듯한 양성 대조를 회귀로 고정한다.

핵심 보조정리는 저장된 JSON 이 아니라 **720 단어 전수 계산**으로 다시 확인한다.
"""

from __future__ import annotations

import itertools
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_HUB_DEFECT_113_CLAUDE.md"

WORDS = ["".join(p) for p in itertools.permutations("012345")]


def sig(x):
    return x[1:] + x[0]


def tau(x):
    return x[1:5] + x[0] + x[5]


def orbrep(x):
    y, b = x, x
    for _ in range(4):
        y = tau(y)
        b = min(b, y)
    return b


def hexrep(x):
    y, b = x, x
    for _ in range(5):
        y = sig(y)
        b = min(b, y)
    return b


def jts(v):
    y = v
    for _ in range(5):
        y = sig(y)
    return {"W2": y[2] + y[3] + y[4] + y[5] + y[1] + y[0],
            "W3a": y[3] + y[4] + y[5] + y[1] + y[2] + y[0],
            "W3b": y[3] + y[4] + y[5] + y[2] + y[0] + y[1],
            "W3c": y[3] + y[4] + y[5] + y[2] + y[1] + y[0]}


def masks():
    hexes = sorted({hexrep(x) for x in WORDS})
    hid = {h: i for i, h in enumerate(hexes)}
    m = {}
    for x in WORDS:
        m.setdefault(orbrep(x), 0)
        m[orbrep(x)] |= 1 << hid[hexrep(x)]
    return m


MASK = masks()


def art():
    return json.loads((OUT / "rr_hub_defect_113.json").read_text())


class LightMoveClassification(unittest.TestCase):
    """§3 — 네 경량 이동의 궤도 거동."""

    def test_W2_is_tau_and_W3a_is_phase_plus_two(self):
        for u in WORDS[:200]:
            j = jts(u)
            self.assertEqual(j["W2"], tau(u))
            self.assertEqual(j["W3a"], tau(tau(u)))

    def test_W3b_is_never_usable_at_00(self):
        bad = sum(1 for u in WORDS
                  if not (MASK[orbrep(u)] & MASK[orbrep(jts(u)["W3b"])]))
        self.assertEqual(bad, 0)          # 720/720 이 육각형을 공유한다

    def test_W3c_is_always_hexagon_disjoint(self):
        ok = sum(1 for u in WORDS
                 if not (MASK[orbrep(u)] & MASK[orbrep(jts(u)["W3c"])]))
        self.assertEqual(ok, 720)

    def test_W3a_from_a_block_end_returns_to_a_visited_entry(self):
        back = sum(1 for u in WORDS
                   if jts(tau(tau(tau(tau(u)))))["W3a"] == tau(u))
        self.assertEqual(back, 720)


class BlockChainTheorem(unittest.TestCase):
    """§4 — D-사슬은 서로 다른 궤도를 정확히 4개까지만 담는다."""

    @staticmethod
    def D(u):
        v = u
        for _ in range(4):
            v = tau(v)
        return jts(v)["W3c"]

    def test_chain_holds_exactly_four_distinct_orbits(self):
        def maxchain(u0):
            u, used, mask = u0, [], 0
            for _ in range(40):
                q = orbrep(u)
                if q in used or (mask & MASK[q]):
                    return len(used)
                used.append(q)
                mask |= MASK[q]
                u = self.D(u)
            return len(used)

        dist = Counter(maxchain(u) for u in WORDS)
        self.assertEqual(dict(dist), {4: 720})

    def test_the_arithmetic_of_the_theorem(self):
        M = 4
        t = -(-24 // M)
        self.assertEqual(t, 6)                 # 사슬 >= 6
        self.assertEqual(t - 1, 5)             # 무거운 연결자 >= 5  => H >= 5
        self.assertEqual(23 + (t - 1), 28)     # cost >= 28
        self.assertEqual(844 + 0 + 28, 872)    # L >= 872


class GreedyPositiveControl(unittest.TestCase):
    """§5 — greedy 873 이 하한을 등호로 달성한다."""

    def setUp(self):
        from src.construct import greedy_construct
        s = greedy_construct(6)
        self.s = s if isinstance(s, str) else "".join(map(str, s))

    def blocks_and_chains(self):
        s, n = self.s, 6
        pos = [i for i in range(len(s) - n + 1) if len(set(s[i:i + n])) == n]
        words = [s[i:i + n] for i in pos]
        wt = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
        ent = [0] + [i + 1 for i, x in enumerate(wt) if x >= 2]
        starts = [words[i] for i in ent]
        blocks, cur = [], [starts[0]]
        for a in range(len(ent) - 1):
            if wt[ent[a] + 5] == 2:
                cur.append(starts[a + 1])
            else:
                blocks.append(cur)
                cur = [starts[a + 1]]
        blocks.append(cur)
        chains, cc = [], [blocks[0]]
        for i in range(len(blocks) - 1):
            if jts(blocks[i][-1])["W3c"] == blocks[i + 1][0]:
                cc.append(blocks[i + 1])
            else:
                chains.append(cc)
                cc = [blocks[i + 1]]
        chains.append(cc)
        return blocks, chains

    def test_it_is_a_24_block_walk_with_full_tau_runs(self):
        blocks, _ = self.blocks_and_chains()
        self.assertEqual(len(blocks), 24)
        self.assertEqual({len(b) for b in blocks}, {5})
        for b in blocks:
            self.assertEqual(len({orbrep(x) for x in b}), 1)
            self.assertTrue(all(b[i + 1] == tau(b[i]) for i in range(4)))

    def test_the_bound_is_attained_exactly(self):
        _, chains = self.blocks_and_chains()
        self.assertEqual(len(chains), 6)
        self.assertEqual([len(c) for c in chains], [4, 4, 4, 4, 4, 4])
        self.assertEqual(len(chains) - 1, 5)          # 무거운 연결자 정확히 5개
        self.assertTrue(all(len(c) <= 4 for c in chains))


class RemainingGap(unittest.TestCase):
    """§6 — 남은 구간과 과대근사의 실패를 기록으로 고정한다."""

    def test_open_range_is_r_25_to_28(self):
        g = art()["remaining_gap_at_00"]
        self.assertEqual(g["open"], "r in [25, 28]")
        self.assertIn("r = 24", g["settled"][0])

    def test_over_approximation_is_recorded_as_useless(self):
        o = art()["remaining_gap_at_00"]["over_approximation_fails"]
        self.assertIn("useless", o["verdict"])


class LedgerDiscipline(unittest.TestCase):
    def test_ledgers_untouched_and_no_cell_closed(self):
        a = art()
        self.assertEqual(a["ledger"]["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(a["ledger"]["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)
        self.assertEqual(a["cells"]["closed_this_round"], 0)

    def test_document_scope(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("NR6", txt)
        self.assertIn("4,782", txt)
        self.assertNotIn("L6 >= 872 proved", txt)


if __name__ == "__main__":
    unittest.main()
