"""라운드 115 — `F=0` 열 폐쇄를 회귀로 고정한다.

핵심 수치는 저장된 JSON 을 믿지 않고 **독립 파이썬 재구현**으로 다시 계산한다
(작은 예산만; 큰 칸은 C 탐색기 아티팩트와 닫힌 형태의 일치를 검사한다).
"""

from __future__ import annotations

import itertools
import json
import subprocess
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_F0_COLUMN_115_CLAUDE.md"

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
HEXES = sorted(set(HEXR.values()))
ORBS = sorted(set(ORBR.values()))
HID = {h: i for i, h in enumerate(HEXES)}
HB = {x: 1 << HID[HEXR[x]] for x in WORDS}


def phase(x):
    y = ORBR[x]
    for i in range(5):
        if y == x:
            return i
        y = tau(y)
    raise AssertionError


PH = {x: phase(x) for x in WORDS}
WORD_AT = {(ORBR[x], PH[x]): x for x in WORDS}
OHEX = defaultdict(set)
for _x in WORDS:
    OHEX[ORBR[_x]].add(HEXR[_x])


def y5(v):
    y = v
    for _ in range(5):
        y = sig(y)
    return y


W3a = lambda v: (lambda y: y[3] + y[4] + y[5] + y[1] + y[2] + y[0])(y5(v))
W3b = lambda v: (lambda y: y[3] + y[4] + y[5] + y[2] + y[0] + y[1])(y5(v))
W3c = lambda v: (lambda y: y[3] + y[4] + y[5] + y[2] + y[1] + y[0])(y5(v))
SUCC = {x: (W3c(x), W3b(x)) for x in WORDS}
PCT = [bin(i).count("1") for i in range(32)]


_NCACHE = {}


def nstar(bcap, gcap, scap, start=WORDS[0]):
    """C 탐색기와 독립인 파이썬 재구현 — 한 사슬의 최대 pass 수 (변이 + 되돌리기)."""
    key = (bcap, gcap, scap, start)
    if key in _NCACHE:
        return _NCACHE[key]
    best = [0]
    used = {}

    def payable(tokens, skip):
        d = sorted((5 - PCT[m] for q, m in used.items() if q != skip and m != 31),
                   reverse=True)
        rest = d[tokens:] if tokens else d
        return sum(rest) <= scap

    def go(u, q, hexm, b, passes):
        if payable(gcap, None) and passes > best[0]:
            best[0] = passes
        # C 탐색기와 같은 낙관적 가지치기 — 실제 walk 의 가지는 자르지 않는다
        if not payable(gcap + (bcap - b), q):
            return
        p = PH[u]
        m = used[q]
        for np_ in range(5):
            if m >> np_ & 1:
                continue
            w = WORD_AT[(q, np_)]
            if hexm & HB[w]:
                continue
            extra = 0 if np_ == (p + 1) % 5 else 1
            if b + extra > bcap:
                continue
            used[q] = m | (1 << np_)
            go(w, q, hexm | HB[w], b + extra, passes + 1)
            used[q] = m
        for w in SUCC[u]:
            if hexm & HB[w]:
                continue
            nq = ORBR[w]
            fresh = nq not in used
            nb = b + (0 if fresh else 1)
            if nb > bcap:
                continue
            prev = used.get(nq, 0)
            used[nq] = prev | (1 << PH[w])
            go(w, nq, hexm | HB[w], nb, passes + 1)
            if fresh:
                del used[nq]
            else:
                used[nq] = prev

    q0 = ORBR[start]
    used[q0] = 1 << PH[start]
    go(start, q0, HB[start], 0, 1)
    _NCACHE[key] = best[0]
    return best[0]


def col():
    return json.loads((OUT / "rr_f0_column_115.json").read_text())


def geo():
    return json.loads((OUT / "rr_f0_geometry_115.json").read_text())


def joint():
    return json.loads((OUT / "rr_joint_residual_115.json").read_text())


class Geometry(unittest.TestCase):
    """§1/§2 — F=0 기하는 전부 720/144/120 전수 사실이다."""

    def test_every_orbit_meets_five_distinct_hexagons(self):
        self.assertEqual({len(v) for v in OHEX.values()}, {5})
        self.assertEqual(len(ORBS), 144)
        self.assertEqual(len(HEXES), 120)

    def test_every_hexagon_meets_six_distinct_orbits(self):
        ho = defaultdict(set)
        for x in WORDS:
            ho[HEXR[x]].add(ORBR[x])
        self.assertEqual({len(v) for v in ho.values()}, {6})

    def test_orbit_pairs_share_zero_one_or_two_hexagons(self):
        c = Counter()
        for i, a in enumerate(ORBS):
            for b in ORBS[i + 1:]:
                c[len(OHEX[a] & OHEX[b])] += 1
        self.assertEqual(dict(c), {0: 8856, 1: 1080, 2: 360})
        self.assertEqual(sum(k * v for k, v in c.items()), 120 * 15)

    def test_D_equals_the_hexagon_overlap_excess_when_F_is_zero(self):
        for row in geo()["s1_f0_identities"]:
            self.assertTrue(row["D_equals_5k"])
            self.assertTrue(row["D_equals_overlap"])
            self.assertEqual(row["O"], 24 + row["k"])


class LightMoves(unittest.TestCase):
    """§3/§4 — W3b 만 k>0 에서 상태가 바뀐다."""

    def test_W3a_always_stays_in_the_orbit(self):
        self.assertEqual(sum(1 for v in WORDS if ORBR[W3a(v)] == ORBR[v]), 720)

    def test_W3c_is_always_hexagon_disjoint(self):
        self.assertEqual(
            sum(1 for v in WORDS
                if ORBR[W3c(v)] != ORBR[v] and not (OHEX[ORBR[v]] & OHEX[ORBR[W3c(v)]])),
            720)

    def test_W3b_always_shares_exactly_one_hexagon(self):
        c = Counter(len(OHEX[ORBR[v]] & OHEX[ORBR[W3b(v)]]) for v in WORDS)
        self.assertEqual(dict(c), {1: 720})

    def test_W3b_orbit_digraph_is_five_regular_with_no_two_cycles(self):
        arcs = {(ORBR[v], ORBR[W3b(v)]) for v in WORDS}
        self.assertEqual(len(arcs), 720)
        self.assertEqual(sum(1 for (a, b) in arcs if (b, a) in arcs), 0)
        self.assertEqual(set(Counter(a for a, _ in arcs).values()), {5})
        self.assertEqual(set(Counter(b for _, b in arcs).values()), {5})

    def test_one_hexagon_can_carry_six_W3b_arcs_not_one(self):
        """§5 — '이동 하나당 결함 토큰 하나' 는 거짓이다."""
        g = geo()["s2_light_moves"]
        self.assertEqual(g["W3b_arcs_per_hexagon"], [6])
        self.assertEqual(list(g["W3b_per_hexagon_structure"].values()), [120])


class Rigidity(unittest.TestCase):
    """§6 — s=0 강성의 대수적 이유."""

    def test_block_map_has_order_four_on_every_word(self):
        def t4(u):
            y = u
            for _ in range(4):
                y = tau(y)
            return y

        D = lambda u: W3c(t4(u))
        for u in WORDS[:120]:
            self.assertEqual(D(D(D(D(u)))), u)
        self.assertEqual(geo()["s6_rigidity"]["D_order_distribution"], {"4": 720})
        self.assertEqual(geo()["s6_rigidity"]["full_block_chain_orbits"], {"4": 720})


class ChainCapacity(unittest.TestCase):
    """§7 — N* 를 독립 재구현으로 다시 계산한다."""

    def test_recompute_small_cells(self):
        for (b, g, s), want in {(0, 0, 0): 20, (1, 0, 0): 35, (2, 0, 0): 50,
                                (0, 1, 0): 33, (0, 0, 2): 33, (0, 0, 4): 46}.items():
            self.assertEqual(nstar(b, g, s), want, f"({b},{g},{s})")

    def test_artifact_matches_the_independent_recomputation(self):
        T = col()["table"]
        for (b, g, s) in ((0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 2), (0, 0, 4)):
            self.assertEqual(T[f"{b},{g},{s}"]["passes"], nstar(b, g, s))

    def test_zero_shortfall_axis_reproduces_round_114_M_star(self):
        T = col()["table"]
        for b in range(5):
            self.assertEqual(T[f"{b},0,0"]["orbits"], 3 * b + 4)
            self.assertEqual(T[f"{b},0,0"]["passes"], 5 * (3 * b + 4))

    def test_capacity_saturates_and_k4_dies_on_it(self):
        T = col()["table"]
        self.assertEqual(T["0,0,20"]["passes"], 103)
        self.assertEqual(T["0,0,20"]["orbits"], 24)
        self.assertFalse(T["0,0,20"]["capped"])
        self.assertLess(T["0,0,20"]["passes"], 120)

    def test_no_cell_hit_the_node_cap(self):
        d = col()
        self.assertEqual(d["capped_cells"], 0)
        self.assertEqual(d["cells"], 91)
        self.assertTrue(all(not v["capped"] for v in d["table"].values()))


class ColumnClosure(unittest.TestCase):
    """§8/§9/§12 — 열 전체가 닫혔다."""

    def test_the_grid_closes_k_0_1_and_4(self):
        p = col()["per_k"]
        for k in ("0", "1", "4"):
            self.assertTrue(p[k]["cell_closed"], f"k={k}")
            self.assertLess(p[k]["worst"], 120)

    def test_the_grid_leaves_exactly_three_residual_subcases(self):
        p = col()["per_k"]
        self.assertEqual(p["2"]["open"], 2)
        self.assertEqual(p["3"]["open"], 1)
        self.assertEqual(sum(p[str(k)]["open"] for k in range(5)), 3)
        for k in ("2", "3"):
            for r in p[k]["open_rows"]:
                self.assertFalse(r["has_unknown_cell"])
                self.assertEqual(r["x"], 0)

    def test_the_joint_search_kills_all_three_residuals(self):
        d = joint()
        self.assertTrue(d["all_residual_closed"])
        for v in d["residual"].values():
            self.assertFalse(v["found"])
            self.assertFalse(v["capped"])
            self.assertGreater(v["nodes"], 1_000_000_000)

    def test_the_joint_search_is_not_vacuous(self):
        d = joint()
        self.assertEqual(d["false_rejection"], 0)
        self.assertEqual(len(d["positive_control"]), 6)
        for c in d["positive_control"]:
            self.assertTrue(c["found"])
        self.assertEqual(d["negative_disagreements"], 0)


class Accounting(unittest.TestCase):
    """§7.1 — 길이 회계 산술."""

    def test_length_requirement(self):
        self.assertEqual(844 + 27, 871)
        self.assertEqual(844 + 28, 872)
        for k in range(5):
            for e in range(5):
                for x in range(5):
                    for t in range(1, 6):
                        cost_lb = 22 + k + e + x + t
                        self.assertEqual(cost_lb <= 27, k + e + x + t <= 5)

    def test_H_plus_k_plus_e_plus_x_at_least_five(self):
        """정리의 tradeoff 형태: t >= 1 이고 k+e+x+t >= 6 이면 H+k+e+x >= 5."""
        for k in range(5):
            for e in range(5):
                for x in range(5):
                    for t in range(1, 8):
                        if k + e + x + t < 6:
                            continue
                        self.assertGreaterEqual((t - 1) + k + e + x, 5)


class PositiveControl(unittest.TestCase):
    """§10 — greedy 873 을 거짓 기각하지 않으며 상한을 정확히 달성한다."""

    def test_lemma_A_holds_on_the_real_walk(self):
        c = geo()["s12_positive_control"]
        self.assertEqual(c["F"], 0)
        self.assertEqual(c["P"], 120)
        self.assertEqual(c["pass_lengths"], [6])
        self.assertTrue(c["pass_hexagon_bijection"])
        self.assertEqual(c["entry_hexagons_distinct"], 120)

    def test_the_chain_capacity_bound_is_attained(self):
        c = geo()["s12_positive_control"]
        self.assertEqual(c["chain_pass_counts"], [20] * 6)
        self.assertEqual(c["max_chain_passes"], col()["table"]["0,0,0"]["passes"])

    def test_the_real_walk_satisfies_the_theorem_with_no_false_rejection(self):
        c = geo()["s12_positive_control"]
        self.assertEqual(c["k_plus_e_x_t"], 6)
        self.assertGreaterEqual(c["k_plus_e_x_t"], 6)
        self.assertGreaterEqual(c["H"] + c["k"] + c["e"] + c["x"], 5)
        self.assertTrue(c["length_identity_ok"])
        self.assertTrue(c["S_identity_ok"])
        self.assertGreaterEqual(c["L"], 872)


class LedgerDiscipline(unittest.TestCase):
    def test_document_never_claims_the_lower_bound(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("NR6", txt)
        self.assertIn("50칸", txt)
        for banned in ("L6 >= 872 proved", "L₆ = 872 가 증명"):
            self.assertNotIn(banned, txt)

    def test_the_round_114_correction_is_recorded_not_deleted(self):
        txt = DOC.read_text()
        self.assertIn("정정 상자", txt)
        self.assertIn("라운드 114 의 결론(`(k,F)=(0,0)` 폐쇄)은 그대로 성립한다", txt)
        self.assertTrue((ROOT / "research" / "RR_PHASE_CORRELATED_RUN_114_CLAUDE.md").exists())

    def test_ledgers_untouched(self):
        txt = DOC.read_text()
        self.assertIn("4,782", txt)
        self.assertIn("6,396 / 6,396", txt)


if __name__ == "__main__":
    unittest.main()
