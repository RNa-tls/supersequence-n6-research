"""라운드 112 — 예리화된 자유-성분 하한과 그 한계를 회귀로 고정한다.

실제 초순열 문자열에서 다시 계산한다.  특히 §9 tradeoff 의 **반례**를 잃지 않도록 고정한다.
"""

from __future__ import annotations

import itertools
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_SHARP_FREE_BOUND_112_CLAUDE.md"


def build(s: str, n: int = 6):
    pos = [i for i in range(len(s) - n + 1) if len(set(s[i:i + n])) == n]
    words = [s[i:i + n] for i in pos]
    w = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]

    def sig(x):
        return x[1:] + x[0]

    def T1(y):
        return y[2:] + y[1] + y[0]

    def hexof(x):
        return min(x[j:] + x[:j] for j in range(n))

    ent = [0]
    for i, wt in enumerate(w):
        if wt >= 2:
            ent.append(i + 1)
    ell = []
    for a, i in enumerate(ent):
        end = ent[a + 1] - 1 if a + 1 < len(ent) else len(words) - 1
        ell.append(end - i)
    starts = [words[i] for i in ent]
    idx = {x: a for a, x in enumerate(starts)}
    succ = {}
    for a, u in enumerate(starts):
        y = u
        for _ in range(ell[a]):
            y = sig(y)
        t = T1(y)
        if t in idx and idx[t] != a:
            succ[a] = idx[t]
    V = len(starts)
    indeg = Counter(succ.values())
    par = list(range(V))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for a, b in succ.items():
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    comp = {}
    for v in range(V):
        comp.setdefault(find(v), []).append(v)
    Zb = sum(1 for vs in comp.values()
             if all(v in succ for v in vs) and all(indeg[v] == 1 for v in vs))
    I0 = sum(1 for v in range(V) if indeg[v] == 0)
    visited = {words[0]}
    F = 0
    for i, wt in enumerate(w):
        if wt >= 2 and sig(words[i]) not in visited:
            F += 1
        visited.add(words[i + 1])
    eh = Counter(hexof(x) for x in starts)
    return {"L": len(s), "V": V, "c": len(comp), "I0": I0, "Z_bare": Zb, "p": I0 + Zb,
            "F": F, "S": sum(1 for x in w if x >= 3),
            "H": sum(max(x - 3, 0) for x in w),
            "ell": ell, "e_h": eh,
            "short": sum(1 for e in ell if e < 5),
            "m": sum(1 for v in eh.values() if v >= 2)}


def witness():
    return build((ROOT / "data" / "verified_872_witness.txt").read_text().strip())


def greedy873():
    from src.construct import greedy_construct
    s = greedy_construct(6)
    return build(s if isinstance(s, str) else "".join(map(str, s)))


def art():
    return json.loads((OUT / "rr_sharp_free_bound_112.json").read_text())


class ShortPassGeometry(unittest.TestCase):
    """§1 — ell=5 만 궤도를 보존하고, ell<5 는 항상 궤도를 바꾼다."""

    def test_only_full_rotation_keeps_the_E_orbit(self):
        def tau(x):
            return x[1:5] + x[0] + x[5]

        def orbrep(x):
            y, b = x, x
            for _ in range(4):
                y = tau(y)
                b = min(b, y)
            return b

        for ell in range(6):
            same = 0
            for p in itertools.islice(itertools.permutations("012345"), 120):
                u = "".join(p)
                y = u
                for _ in range(ell):
                    y = y[1:] + y[0]
                g = y[2:] + y[1] + y[0]
                if orbrep(g) == orbrep(u):
                    same += 1
            self.assertEqual(same, 120 if ell == 5 else 0, f"ell={ell}")

    def test_geometry_census_recorded(self):
        rows = art()["s1_s10_geometry"]["rows"]
        self.assertEqual(len(rows), 6)
        for r in rows:
            self.assertEqual(r["same_E_orbit"], 720 if r["ell"] == 5 else 0)
            self.assertEqual(r["same_hexagon"], 0)


class ShortPassCount(unittest.TestCase):
    """§12 — 짧은 pass 수는 F + m 이고 2F 로 묶인다."""

    def test_per_hexagon_shortfall_identity(self):
        for d in (witness(), greedy873()):
            per = {}
            # ell 은 pass 순서, e_h 는 육각형별 진입 수 — 총합으로 확인한다
            self.assertEqual(sum(5 - e for e in d["ell"]), 6 * d["F"])

    def test_short_equals_F_plus_m_and_is_bounded_by_2F(self):
        for d in (witness(), greedy873()):
            self.assertEqual(d["short"], d["F"] + d["m"])
            self.assertLessEqual(d["short"], 2 * d["F"])
            self.assertLessEqual(d["m"], d["F"])

    def test_bound_is_tight_on_the_872_witness(self):
        d = witness()
        self.assertEqual(d["short"], 50)
        self.assertEqual(d["F"], 25)
        self.assertEqual(d["short"], 2 * d["F"])


class PathCover(unittest.TestCase):
    """§5/§6 — p = I0 + Z_bare, 그리고 F=0 에서는 p = c."""

    def test_path_cover_formula_and_no_gain_on_real_walks(self):
        for d in (witness(), greedy873()):
            self.assertEqual(d["p"], d["I0"] + d["Z_bare"])
            self.assertGreaterEqual(d["p"], d["c"])
            self.assertEqual(d["p"], d["c"])          # 두 walk 모두 이득 없음

    def test_F0_walk_has_injective_free_map(self):
        d = greedy873()
        self.assertEqual(d["F"], 0)
        self.assertEqual(d["I0"], 0)
        self.assertEqual(d["c"], 24)
        self.assertEqual(d["Z_bare"], 24)


class TightnessDiagnosis(unittest.TestCase):
    """§7/§8/§11 — 개수 하한은 빠듯하고, 남는 것은 전부 H 다."""

    def test_arc_count_bound_is_exactly_tight_on_both_walks(self):
        for d in (witness(), greedy873()):
            self.assertEqual(d["S"], d["c"] - 1)

    def test_the_whole_residual_gap_is_H(self):
        for d in (witness(), greedy873()):
            self.assertEqual((d["S"] + d["H"]) - (d["c"] - 1), d["H"])

    def test_872_witness_is_accepted_with_equality(self):
        d = witness()
        self.assertEqual(d["F"], 25)
        self.assertEqual(d["c"], 4)
        self.assertEqual(d["S"] + d["H"], d["c"] - 1)
        self.assertEqual(843 + d["F"] + d["c"], d["L"])

    def test_F0_bound_reproduces_the_houston_constant(self):
        d = greedy873()
        self.assertGreaterEqual(d["S"] + d["H"], d["c"] - 1)
        self.assertEqual(844 + d["F"] + (d["c"] - 1), 867)


class TradeoffRefuted(unittest.TestCase):
    """§9 — F + Q >= 29 는 거짓이다.  반례를 잃지 않도록 고정한다."""

    def test_greedy_873_refutes_F_plus_c_ge_29(self):
        d = greedy873()
        self.assertEqual(d["F"], 0)
        self.assertEqual(d["c"], 24)
        self.assertLess(d["F"] + d["c"], 29)

    def test_path_cover_does_not_rescue_it(self):
        d = greedy873()
        self.assertLess(d["F"] + d["p"], 29)

    def test_the_872_witness_does_satisfy_it(self):
        d = witness()
        self.assertEqual(d["F"] + d["c"], 29)

    def test_refutation_is_recorded(self):
        a = art()["s9_tradeoff_REFUTED"]
        self.assertEqual(a["verdict"], "FALSE")
        self.assertIn("greedy", a["counterexample"])


class CellsAndLedger(unittest.TestCase):
    def test_no_cell_closed_this_round(self):
        a = art()
        self.assertEqual(a["s13_cells"]["cells_closed_this_round"], 0)
        self.assertEqual(a["s13_cells"]["total_cells"], 55)
        self.assertEqual(a["sharpened_component_bound"]["maximum_over_cells"]["value"], 28)

    def test_00_cell_exact_cover_exists(self):
        a = art()["s7_f0_calibration"]["exact_cover_test"]
        self.assertEqual(a["answer"], "YES — solutions exist (search nodes 25)")

    def test_ledgers_untouched(self):
        a = art()["ledger"]
        self.assertEqual(a["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(a["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)

    def test_document_scope(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)
        self.assertIn("반증", txt)
        self.assertNotIn("L6 >= 872 proved", txt)


if __name__ == "__main__":
    unittest.main()
