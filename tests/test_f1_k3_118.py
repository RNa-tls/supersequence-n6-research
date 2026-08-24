"""라운드 118 — `(3,1)` 예산 표와 부분 배제를 회귀로 고정한다.

이 라운드는 **칸을 닫지 않았다.**  세 하위경우가 열려 있다는 사실 자체를 테스트로 못박는다.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_F1_K3_118_CLAUDE.md"

WORDS = ["".join(p) for p in itertools.permutations("012345")]
sig = lambda x: x[1:] + x[0]
tau = lambda x: x[1:5] + x[0] + x[5]


def _rep(x, f, n):
    y, b = x, x
    for _ in range(n - 1):
        y = f(y)
        b = min(b, y)
    return b


HEXR = {x: _rep(x, sig, 6) for x in WORDS}
ORBR = {x: _rep(x, tau, 5) for x in WORDS}
OHEX = defaultdict(set)
for _x in WORDS:
    OHEX[ORBR[_x]].add(HEXR[_x])


def art():
    return json.loads((OUT / "rr_f1_k3_118.json").read_text())


def core():
    spec = importlib.util.spec_from_file_location(
        "core118", ROOT / "legacy_research" / "work" / "superperm_port_lift.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["core118"] = m
    spec.loader.exec_module(m)
    return m


class Budget(unittest.TestCase):
    """§1 — (3,1) 의 자원 경우를 독립 재유도한다."""

    def rows(self):
        out = []
        for e in range(8):
            for x in range(8):
                for fo in range(3):
                    if fo > 1 + e:                    # Lemma E (Round 117)
                        continue
                    S = 26 + e + x - fo               # S = 23 + k + e + x - f_out, k = 3
                    H = 26 - S                        # S + H <= 26  (L = 845 + S + H <= 871)
                    if H < 0:
                        continue
                    out.append((e, x, fo, S, H, 27 + e, H + 1))
        return sorted(out)

    def test_exactly_seven_resource_rows(self):
        self.assertEqual(self.rows(), [
            (0, 0, 0, 26, 0, 27, 1),
            (0, 0, 1, 25, 1, 27, 2),
            (0, 1, 1, 26, 0, 27, 1),
            (1, 0, 1, 26, 0, 28, 1),
            (1, 0, 2, 25, 1, 28, 2),
            (1, 1, 2, 26, 0, 28, 1),
            (2, 0, 2, 26, 0, 29, 1)])

    def test_H_is_at_most_one_and_x_at_most_one(self):
        for (e, x, fo, S, H, r, t) in self.rows():
            self.assertLessEqual(H, 1)
            self.assertLessEqual(x, 1)
            if H == 1:
                self.assertEqual(x, 0)
                self.assertEqual(fo, 1 + e)

    def test_nine_subcases_when_H_is_split_out(self):
        n = sum(1 + (H == 1) for (_e, _x, _f, _S, H, _r, _t) in self.rows())
        self.assertEqual(n, 9)

    def test_identities(self):
        self.assertEqual(5 * 3 - 1, 14)                # D = 5k - 1
        self.assertEqual(24 + 3, 27)                   # O
        self.assertEqual(845 + 26, 871)                # L = 845 + S + H
        self.assertEqual(5 * 27 - 121, 14)             # orbit deficit


class HeavyMoveCensus(unittest.TestCase):
    """§6 — 허브세 1 은 정확히 무게-4 이고 13개다."""

    def test_thirteen_weight4_tails_matching_the_engine(self):
        c = core()
        eng = sorted(tuple(c.tail_action(4, pi)) for pi in c.tail_permutations(4))
        mine = []
        for pi in itertools.permutations(range(4)):
            ok, mx = True, -1
            for j in range(3):
                mx = max(mx, pi[j])
                if mx == j:
                    ok = False
                    break
            if ok:
                mine.append(tuple([4, 5] + list(pi)))
        self.assertEqual(len(eng), 13)
        self.assertEqual(eng, sorted(mine))

    def test_every_weight4_move_changes_orbit_and_leaves_the_hexagon(self):
        c = core()
        ap = lambda s: tuple(int(ch) for ch in s)
        as_ = lambda p: "".join(str(v) for v in p)
        shared = Counter()
        for pi in c.tail_permutations(4):
            act = c.tail_action(4, pi)
            for u in WORDS[:120]:
                t = as_(c.word_after(ap(u), act))
                self.assertNotEqual(ORBR[t], ORBR[u])
                self.assertNotEqual(HEXR[t], HEXR[u])
                shared[len(OHEX[ORBR[u]] & OHEX[ORBR[t]])] += 1
        self.assertEqual(set(shared), {0, 2})

    def test_hub_tax_one_means_exactly_one_weight_four_joint(self):
        cost = lambda w: (1 if w >= 3 else 0) + max(w - 3, 0)
        hub = lambda w: max(w - 3, 0)
        self.assertEqual([hub(w) for w in range(1, 7)], [0, 0, 0, 1, 2, 3])
        self.assertEqual(cost(4), 2)


class ForcedGeometryScope(unittest.TestCase):
    """§11 — 라운드 117 의 강제 5-간격이 어디까지 살아남는가."""

    def test_gap_five_needs_x_zero_and_e_one(self):
        """블록은 phase +1 (tau) 과 +2 (W3a) 로 +4 를 만들어야 한다."""
        def blocks(xcap):
            out = set()
            for b in range(0, xcap + 1):
                a = 4 - 2 * b
                if a >= 0:
                    out.add(a + b + 1)               # passes in the block
            return out
        self.assertEqual(blocks(0), {5})
        self.assertEqual(blocks(1), {4, 5})

    def test_artifact_records_the_scope(self):
        txt = DOC.read_text()
        self.assertIn("정확히 5", txt)
        self.assertIn("4 또는 5", txt)
        self.assertIn("강제되지 않는다", txt)


class Search(unittest.TestCase):
    """§8/§9 — 판정과 캡 규율."""

    def test_twenty_runs_all_exhaustive(self):
        d = art()
        self.assertEqual(d["cell"], [3, 1])
        self.assertEqual(d["runs"], 20)
        self.assertEqual(d["verdicts"], {"UNSAT_COMPLETE": 20})
        for r in d["rows"]:
            self.assertNotEqual(r["verdict"], "UNKNOWN_CAP")
            self.assertNotIn("witness", r)

    def test_four_groups_closed_over_all_five_splits(self):
        d = art()
        self.assertEqual(sorted(d["groups_closed"]),
                         ["G1_e0_H0", "G2_e1_x0_f1_H0", "G3_e1_x0_f2_H0", "G6_H1_e0"])
        for g in d["groups_closed"]:
            self.assertTrue(d["by_group"][g]["closed"])
            self.assertEqual(d["by_group"][g]["runs"], 5)
        self.assertEqual({b for r in d["rows"] for b in [r["b"]]}, {1, 2, 3, 4, 5})

    def test_the_cell_is_NOT_closed(self):
        d = art()
        self.assertFalse(d["cell_closed"])
        self.assertEqual(len(d["open_subcases"]), 3)
        self.assertEqual([o["label"] for o in d["open_subcases"]],
                         ["G4_e1_x1_f2_H0", "G5_e2_x0_f2_H0", "G7_H1_e1_x0_f2"])
        for o in d["open_subcases"]:
            self.assertTrue(o["reason"])

    def test_the_search_is_not_vacuous(self):
        d = art()
        self.assertGreater(d["max_passes_reached"], 100)
        self.assertLess(d["max_passes_reached"], 121)
        self.assertGreater(d["total_nodes"], 5 * 10 ** 10)

    def test_H1_group_actually_used_the_heavy_move(self):
        """hcap=1 실행이 실제로 무게-4 후속을 달았는지 — hcap=0 보다 노드가 많다."""
        d = art()
        h1 = [r for r in d["rows"] if r["group"] == "G6_H1_e0"]
        h0 = [r for r in d["rows"] if r["group"] == "G1_e0_H0"]
        self.assertTrue(all(r["hcap"] == 1 for r in h1))
        self.assertTrue(all(r["hcap"] == 0 for r in h0))
        self.assertGreater(sum(r["nodes"] for r in h1), sum(r["nodes"] for r in h0))


class LedgerDiscipline(unittest.TestCase):
    def test_no_cell_closure_is_claimed(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("닫히지 않았다", txt)
        self.assertIn("6 / 55", txt)
        for banned in ("(3,1) 칸을 닫았다", "L6 >= 872 proved"):
            self.assertNotIn(banned, txt)

    def test_audit_status_is_recorded(self):
        txt = DOC.read_text()
        self.assertIn("PARTIAL", txt)
        self.assertIn("독립 감사 없음", txt)

    def test_ledgers_untouched(self):
        lg = art()["ledger"]
        self.assertEqual(lg["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(lg["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)
        self.assertTrue(lg["unchanged_by_this_round"])


if __name__ == "__main__":
    unittest.main()
