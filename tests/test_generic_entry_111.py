"""라운드 111 — 일반 entry 정리를 회귀로 고정한다.

저장된 JSON 을 믿지 않고 **실제 초순열 문자열에서 다시 계산**한다.
"""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_GENERIC_ENTRY_111_CLAUDE.md"


def analyse(s: str, n: int):
    """비반복 walk 의 entry 좌표와 자유-호 그래프 G0 를 문자열에서 직접 만든다."""
    fact = 1
    for i in range(1, n + 1):
        fact *= i
    hexes = fact // n
    pos = [i for i in range(len(s) - n + 1) if len(set(s[i:i + n])) == n]
    words = [s[i:i + n] for i in pos]
    if len(words) != len(set(words)) or len(words) != fact:
        return None
    w = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]

    def sig(x):
        return x[1:] + x[0]

    def tau(x):
        return x[1:n - 1] + x[0] + x[n - 1]

    def T1(y):
        return y[2:] + y[1] + y[0]

    def orb(x):
        y, b = x, x
        for _ in range(n - 2):
            y = tau(y)
            b = min(b, y)
        return b

    ent = [0]
    for i, wt in enumerate(w):
        if wt >= 2:
            ent.append(i + 1)
    ell = []
    for a, i in enumerate(ent):
        end = ent[a + 1] - 1 if a + 1 < len(ent) else len(words) - 1
        ell.append(end - i)
    starts = [words[i] for i in ent]
    visited = {words[0]}
    F = 0
    for i, wt in enumerate(w):
        if wt >= 2 and sig(words[i]) not in visited:
            F += 1
        visited.add(words[i + 1])
    S = sum(1 for x in w if x >= 3)
    H = sum(max(x - 3, 0) for x in w)
    per = Counter(orb(x) for x in starts)
    P = len(starts)
    sset = {x: a for a, x in enumerate(starts)}
    succ = {}
    for a, u in enumerate(starts):
        y = u
        for _ in range(ell[a]):
            y = sig(y)
        t = T1(y)
        if t in sset and sset[t] != a:
            succ[a] = sset[t]
    par = list(range(P))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for a, b in succ.items():
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    return {"n": n, "L": len(s), "P": P, "F": F, "S": S, "H": H, "O": len(per),
            "hexes": hexes, "fact": fact, "c": len({find(a) for a in range(P)}),
            "ell": ell, "shortfall": sum((n - 1) - e for e in ell),
            "base": n + fact - 3 + hexes}


def witness():
    return (ROOT / "data" / "verified_872_witness.txt").read_text().strip()


def greedy(n):
    from src.construct import greedy_construct
    s = greedy_construct(n)
    return s if isinstance(s, str) else "".join(map(str, s))


def art():
    return json.loads((OUT / "rr_generic_entry_111.json").read_text())


class FreeArcMap(unittest.TestCase):
    """§4 — 자유 호는 ell=5 일 때 정확히 tau 다."""

    def test_free_arc_equals_tau_exactly_at_full_rotation(self):
        import itertools
        for ell in range(6):
            same = True
            for p in itertools.islice(itertools.permutations("012345"), 30):
                u = "".join(p)
                y = u
                for _ in range(ell):
                    y = y[1:] + y[0]
                free = y[2:] + y[1] + y[0]
                if free != u[1:5] + u[0] + u[5]:
                    same = False
                    break
            self.assertEqual(same, ell == 5, f"ell={ell}")

    def test_only_one_weight_two_tail_exists(self):
        import importlib.util as iu
        import sys
        spec = iu.spec_from_file_location(
            "superperm_port_lift", ROOT / "legacy_research" / "work" / "superperm_port_lift.py")
        core = iu.module_from_spec(spec)
        sys.modules["superperm_port_lift"] = core
        spec.loader.exec_module(core)
        self.assertEqual([len(core.tail_permutations(w)) for w in range(1, 7)],
                         [1, 1, 3, 13, 71, 461])


class ShortfallIdentity(unittest.TestCase):
    """§5 — sum(5 - ell) = 6F, 따라서 F=0 이면 ell 이 강제된다."""

    def test_rotation_shortfall_equals_6F_at_n6(self):
        for s in (witness(), greedy(6)):
            d = analyse(s, 6)
            self.assertEqual(d["shortfall"], 6 * d["F"])

    def test_F_zero_forces_every_pass_full(self):
        d = analyse(greedy(6), 6)
        self.assertEqual(d["F"], 0)
        self.assertTrue(all(e == 5 for e in d["ell"]))
        self.assertEqual(d["P"], 120)


class GenericEntryTheorem(unittest.TestCase):
    """§7 — L >= base + F + c(G0), 그리고 S+H >= c-1."""

    def test_component_bound_on_named_walks(self):
        for s, n in ((witness(), 6), (greedy(6), 6), (greedy(5), 5),
                     (greedy(4), 4), (greedy(3), 3)):
            d = analyse(s, n)
            self.assertGreaterEqual(d["S"] + d["H"], d["c"] - 1, n)
            self.assertGreaterEqual(d["L"], d["base"] + d["F"] + d["c"], n)

    def test_the_872_witness_attains_equality(self):
        d = analyse(witness(), 6)
        self.assertEqual(d["F"], 25)
        self.assertEqual(d["c"], 4)
        self.assertEqual(d["F"] + d["c"], 29)
        self.assertEqual(d["base"], 843)
        self.assertEqual(d["base"] + d["F"] + d["c"], 872)
        self.assertEqual(d["L"], 872)

    def test_F0_component_bound_recovers_the_houston_constant(self):
        """F=0 이면 c >= O 이고 L >= 844 + (O-1) = 867 + k."""
        d = analyse(greedy(6), 6)
        self.assertEqual(d["F"], 0)
        self.assertGreaterEqual(d["c"], d["O"])
        self.assertGreaterEqual(d["L"], 867 + (d["O"] - 24))


class SmallNFalsification(unittest.TestCase):
    """§12 — 169개 n=4 walk 표본에서의 결과."""

    def test_equality_form_of_theorem_A_is_refuted(self):
        a = art()["verification"]["n4_sample_aggregate"]
        self.assertEqual(a["walks"], 169)
        self.assertEqual(a["O_le_1_plus_S_plus_F"], 169)      # 부등식은 산다
        self.assertLess(a["O_eq_1_plus_S_plus_F"], 169)       # 등식은 죽는다
        self.assertEqual(a["O_eq_1_plus_S_plus_F"], 84)

    def test_the_generic_theorem_survives_the_whole_sample(self):
        a = art()["verification"]["n4_sample_aggregate"]
        self.assertEqual(a["S_plus_H_ge_c_minus_1"], 169)
        self.assertEqual(a["L_ge_base_plus_F_plus_c"], 169)
        self.assertEqual(a["P_eq_hexes_plus_F"], 169)
        self.assertEqual(a["L_identity"], 169)

    def test_the_sample_actually_contains_positive_F(self):
        a = art()["verification"]["n4_sample_aggregate"]
        self.assertGreater(sum(v for k, v in a["F_values"].items() if int(k) > 0), 0)


class CellCensus(unittest.TestCase):
    """§8/§9 — 55칸 중 하나도 닫히지 않았다."""

    def test_no_cell_is_killed_by_the_generic_bound(self):
        c = json.loads((OUT / "rr_generic_entry_cells_111.json").read_text())
        self.assertEqual(c["total"], 55)
        self.assertEqual(c["arithmetically_feasible"], 55)
        self.assertEqual(c["killed_by_generic_component_bound"], 0)

    def test_archive_represents_exactly_one_cell(self):
        c = json.loads((OUT / "rr_generic_entry_cells_111.json").read_text())
        self.assertEqual(c["archive_F_values"], [1])
        self.assertEqual(c["archive_cell"], {"k": 1, "F": 1})
        self.assertEqual(c["archive_states_in_other_cells"], 0)

    def test_k_zero_forces_F_zero_and_a_saturated_orbit_structure(self):
        cells = json.loads((OUT / "rr_generic_entry_cells_111.json").read_text())["cells"]
        k0 = [r for r in cells if r["k"] == 0]
        self.assertEqual(len(k0), 1)                 # F <= 5k = 0
        self.assertEqual(k0[0]["F"], 0)
        self.assertEqual(k0[0]["D"], 0)
        self.assertEqual(k0[0]["O"], 24)


class LedgerDiscipline(unittest.TestCase):
    def test_ledger_untouched(self):
        a = art()["ledger"]
        self.assertEqual(a["INDEPENDENTLY_AUDITED_Q2_RESIDUAL"], 4782)
        self.assertEqual(a["CLAUDE_FULL_JOINT_UNSAT_COMPLETE"], 6396)
        self.assertEqual(a["OUTER_CELLS_CLOSED_THIS_ROUND"], 0)

    def test_document_scope(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)
        self.assertIn("F + c(G₀) ≥ 29", txt)
        self.assertNotIn("L6 >= 872 proved", txt)


if __name__ == "__main__":
    unittest.main()
