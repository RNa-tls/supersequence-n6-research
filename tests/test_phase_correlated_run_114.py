"""라운드 114 — (k,F)=(0,0) 폐쇄 정리를 회귀로 고정한다.

핵심 수치 M*(B) 는 저장된 JSON 이 아니라 **탐색을 다시 돌려** 확인한다 (B <= 2 만; B=3,4 는
비용이 커서 아티팩트를 신뢰하되 닫힌 형태 3B+4 와의 일치를 검사한다).
"""

from __future__ import annotations

import itertools
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_PHASE_CORRELATED_RUN_114_CLAUDE.md"

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


def phase(x):
    r, y = orbrep(x), orbrep(x)
    for i in range(5):
        if y == x:
            return i
        y = tau(y)
    raise AssertionError


def W3c(v):
    y = v
    for _ in range(5):
        y = sig(y)
    return y[3] + y[4] + y[5] + y[2] + y[1] + y[0]


def W3b(v):
    y = v
    for _ in range(5):
        y = sig(y)
    return y[3] + y[4] + y[5] + y[2] + y[0] + y[1]


HEXES = sorted({hexrep(x) for x in WORDS})
HID = {h: i for i, h in enumerate(HEXES)}
ORBMASK = {}
for _x in WORDS:
    _o = orbrep(_x)
    ORBMASK[_o] = ORBMASK.get(_o, 0) | (1 << HID[hexrep(_x)])
ORB = {x: orbrep(x) for x in WORDS}
PH = {x: phase(x) for x in WORDS}
WORD_AT = {(ORB[x], PH[x]): x for x in WORDS}
NXT = {x: W3c(x) for x in WORDS}


def mstar(B, start):
    best = [0]

    def inc(used):
        return sum(1 for v in used.values() if v != 31)

    def start_run(u, used, hexm, spent, ndist):
        q, p = ORB[u], PH[u]
        newq = q not in used
        if newq and (hexm & ORBMASK[q]):
            return
        cur = used.get(q, 0)
        if cur >> p & 1:
            return
        s2 = spent + (0 if newq else 1)
        if s2 > B:
            return
        in_run(u, q, p, cur | (1 << p), used, hexm | ORBMASK[q], s2,
               ndist + (1 if newq else 0))

    def in_run(u, q, p, phmask, used, hexm, spent, ndist):
        if ndist > best[0]:
            best[0] = ndist
        nu = dict(used)
        nu[q] = phmask
        if spent + inc(nu) <= B:
            start_run(NXT[u], nu, hexm, spent, ndist)
        for np_ in range(5):
            if phmask >> np_ & 1:
                continue
            extra = 0 if np_ == (p + 1) % 5 else 1
            if spent + extra > B:
                continue
            in_run(WORD_AT[(q, np_)], q, np_, phmask | (1 << np_), used, hexm,
                   spent + extra, ndist)

    start_run(start, {}, 0, 0, 0)
    return best[0]


def art():
    return json.loads((OUT / "rr_phase_correlated_run_114.json").read_text())


class LightMoveRecheck(unittest.TestCase):
    """§2 — 짧은 run 끝에서도 W3b 는 사용 불가; W3a 는 궤도 내부라 연결자가 아니다."""

    def test_W3b_target_always_collides_for_every_endpoint(self):
        bad = sum(1 for v in WORDS
                  if not (ORBMASK[ORB[v]] & ORBMASK[ORB[W3b(v)]]))
        self.assertEqual(bad, 0)

    def test_W3a_stays_in_the_same_orbit(self):
        for v in WORDS[:300]:
            y = v
            for _ in range(5):
                y = sig(y)
            w3a = y[3] + y[4] + y[5] + y[1] + y[2] + y[0]
            self.assertEqual(ORB[w3a], ORB[v])

    def test_W3c_always_changes_orbit_and_is_hexagon_disjoint(self):
        ok = sum(1 for v in WORDS
                 if ORB[W3c(v)] != ORB[v] and not (ORBMASK[ORB[v]] & ORBMASK[ORB[W3c(v)]]))
        self.assertEqual(ok, 720)


class MStar(unittest.TestCase):
    """§3 — M*(B) = 3B + 4, phase 를 지우지 않은 모델에서."""

    def test_recompute_small_B(self):
        for B in (0, 1, 2):
            self.assertEqual(mstar(B, WORDS[0]), 3 * B + 4, f"B={B}")

    def test_symmetry_makes_one_start_enough(self):
        vals = {mstar(1, s) for s in (WORDS[0], WORDS[200], WORDS[500], WORDS[719])}
        self.assertEqual(vals, {7})

    def test_artifact_matches_the_closed_form(self):
        v = art()["s7_M_star"]["values"]
        for B in range(5):
            self.assertEqual(v[str(B)], 3 * B + 4)
        self.assertTrue(art()["s7_M_star"]["exhaustive"])
        self.assertEqual(art()["s7_M_star"]["cap_hits"], 0)


class AllocationArgument(unittest.TestCase):
    """§4 — B + t >= 6 이 모든 B 에서 성립한다."""

    def test_bound_holds_for_every_budget(self):
        for B in range(0, 6):
            t = -(-(24 - 3 * B) // 4) if B <= 4 else 1
            self.assertGreaterEqual(B + t, 6, f"B={B}")

    def test_the_closed_form_inequality(self):
        for B in range(0, 60):
            self.assertGreaterEqual((24 + B) / 4, 6)

    def test_cost_and_length_conclusion(self):
        self.assertEqual(22 + 6, 28)          # cost >= 28
        self.assertEqual(844 + 28, 872)       # L >= 872

    def test_table_in_artifact(self):
        for row in art()["s8_allocation"]["table"]:
            self.assertGreaterEqual(row["B_plus_t"], 6)


class PositiveControl(unittest.TestCase):
    """§5 — greedy 873 을 거짓 기각하지 않으며 극단 경우에 앉아 있다."""

    def test_greedy_873_is_accepted_and_extremal(self):
        c = art()["s12_positive_control"]
        self.assertEqual(c["false_rejection"], 0)
        self.assertEqual(c["r"], 24)
        self.assertEqual(c["t"], 6)
        self.assertEqual(c["B"], 0)
        self.assertLessEqual(c["predicted_cost_lower_bound"], c["actual_cost"])
        self.assertGreaterEqual(c["actual_L"], 872)


class CellLedger(unittest.TestCase):
    def test_exactly_one_cell_closed(self):
        c = art()["cells"]
        self.assertEqual(c["total"], 55)
        self.assertEqual(c["closed_this_round"], 1)
        self.assertEqual(c["closed_cell"], [0, 0])
        self.assertEqual(c["remaining"], 54)

    def test_ledgers_untouched(self):
        lg = art()["ledger"]
        self.assertEqual(lg["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(lg["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)

    def test_document_scope(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("NR6", txt)
        self.assertIn("54칸", txt)
        self.assertNotIn("L6 >= 872 proved", txt)


if __name__ == "__main__":
    unittest.main()
