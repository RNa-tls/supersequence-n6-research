"""라운드 107 — 증명 골격의 각 보조정리가 주장하는 사실을 회귀로 고정한다.

이 테스트들은 **문서의 명제와 코드/데이터가 어긋나면** 실패한다.  감사 원장(4,782)은 건드리지
않는다.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
ARCHIVE = OUT / "rr_port_path_hall_archive"
DOC = ROOT / "research" / "RR_Q2_ZERO_PROOF_SKELETON_CLAUDE.md"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


C = _load("certify_rr_q2_zero", "src/certify_rr_q2_zero.py")
X = _load("extract_rr_counterexample", "src/extract_rr_counterexample.py")


def states():
    with gzip.open(ARCHIVE / "states.jsonl.gz", "rt") as fh:
        fh.readline()
        return [json.loads(line) for line in fh]


class Definitions(unittest.TestCase):
    """§1 — 정의가 데이터와 맞는가."""

    def test_hexagons_and_orbits_have_the_stated_shape(self):
        with gzip.open(ARCHIVE / "geometry.jsonl.gz", "rt") as fh:
            fh.readline()
            geo = [json.loads(line) for line in fh]
        self.assertEqual(len(geo), 720)
        self.assertEqual(Counter(Counter(g["hexagon"] for g in geo).values()), {6: 120})
        self.assertEqual(Counter(Counter(g["orbit"] for g in geo).values()), {5: 144})

    def test_each_hexagon_meets_six_distinct_orbits(self):
        with gzip.open(ARCHIVE / "geometry.jsonl.gz", "rt") as fh:
            fh.readline()
            geo = [json.loads(line) for line in fh]
        per = {}
        for g in geo:
            per.setdefault(g["hexagon"], set()).add(g["orbit"])
        self.assertEqual(Counter(len(v) for v in per.values()), {6: 120})

    def test_orbit_is_the_first_five_letter_rotation_class(self):
        with gzip.open(ARCHIVE / "geometry.jsonl.gz", "rt") as fh:
            fh.readline()
            geo = [json.loads(line) for line in fh]
        by_orbit = {}
        for g in geo:
            by_orbit.setdefault(g["orbit"], []).append(g["word"])
        for words in by_orbit.values():
            base = sorted(words)[0]
            expect = {base[k:5] + base[:k] + base[5] for k in range(5)}
            self.assertEqual(set(words), expect)


class Lemma5DeltaF(unittest.TestCase):
    """§5 — `ΔF = 0` 이 목표 조건에서 직접 나온다는 근거."""

    def test_every_archive_state_already_has_F_equal_to_the_target(self):
        self.assertEqual(Counter(s["F"] for s in states()), {1: 6396})

    def test_F_is_monotone_in_the_engine(self):
        src = (ROOT / "legacy_research" / "work" / "superperm_partial_f1.py").read_text()
        self.assertIn("dF = int(abandonment)", src)
        self.assertIn("F=state.F + dF", src)
        self.assertIn("TARGET_F = 1", src)
        self.assertIn("state.F == TARGET_F", src)


class Lemma6Budget(unittest.TestCase):
    """§6 — 예산 정리의 산술."""

    def test_all_states_sit_at_Ndef_plus_H_equal_zero(self):
        st = states()
        self.assertEqual(Counter(s["H"] for s in st), {0: 6396})
        self.assertTrue(all(s["S"] + s["F"] - s["O"] == 0 for s in st))

    def test_budget_reduces_to_three_plus_K(self):
        for s in states():
            ndef = s["S"] + s["F"] - s["O"]
            self.assertEqual(3 + s["K"] - ndef - s["H"], 3 + s["K"])
            self.assertEqual(s["K"], 25 - s["O"])

    def test_engine_update_rules_match_the_event_table(self):
        src = (ROOT / "legacy_research" / "work" / "superperm_partial_f1.py").read_text()
        self.assertIn("dS = int(move.weight >= 3)", src)
        self.assertIn("dH = max(move.weight - 3, 0)", src)
        self.assertIn("return self.S + self.F - self.O", src)
        self.assertIn("state.Ndef + state.H <= TARGET_BUDGET", src)
        self.assertIn("TARGET_BUDGET = 3", src)
        self.assertIn("TARGET_O = 25", src)


class Lemma7ComponentBound(unittest.TestCase):
    """§7 — 보존한 반례가 실제로 반례인가."""

    def test_preserved_counterexample_is_genuine(self):
        d = json.loads((OUT / "rr_outdegree_counterexample.json").read_text())
        out0, out1 = d["out0"], d["out1"]
        m = d["m"]
        # 가설 위반이 실제로 있다
        self.assertTrue(any(t and t & (t - 1) for t in out0))
        # 구현이 세는 성분 수가 참 성분 수보다 크다
        full = (1 << m) - 1
        self.assertEqual(X.hat_c(out0, full), d["hat_c"])
        self.assertEqual(X.true_c(out0, full), d["true_c"])
        self.assertGreater(d["hat_c"], d["true_c"])
        # 그리고 그 때문에 하한이 참 최소비용을 넘는다 — 불건전
        r0 = 1 if d["root_zero_cost_entry"] else 0
        r1 = 0 if d["root_zero_cost_entry"] else 1
        self.assertEqual(X.min_cost1_arcs(out0, out1, r0, r1, m), d["true_min_cost1_arcs"])
        self.assertGreater(d["implementation_bound"], d["true_min_cost1_arcs"])

    def test_true_component_count_still_gives_a_sound_bound_there(self):
        """정리 자체는 참이다 — 참 성분 수로 세면 하한이 참값을 넘지 않는다."""
        d = json.loads((OUT / "rr_outdegree_counterexample.json").read_text())
        sound = d["true_c"] - 1 if d["root_zero_cost_entry"] else d["true_c"]
        self.assertLessEqual(sound, d["true_min_cost1_arcs"])


class NodeCapSemantics(unittest.TestCase):
    """§11 정정 — 캡은 호출 하나당이며, 한 번의 캡 도달이 다음 호출을 오염시키지 않는다."""

    def test_cap_is_per_call_and_does_not_leak(self):
        # 작은 UNSAT 인스턴스: 정점 3개, ROOT 는 0 으로만, 0 에서 나가는 호 없음
        out0 = [0, 0, 0]
        out1 = [0, 0, 0]
        stats = Counter()
        first = C.solve(out0, out1, r0=0, r1=0b001, B=5, stats=stats, node_cap=1)
        self.assertEqual(first, "UNSAT")            # 분기 자체가 없다
        stats["nodes"] = 10 ** 9                    # 실행 전체 카운터를 오염시켜 본다
        second = C.solve(out0, out1, r0=0, r1=0b001, B=5, stats=stats, node_cap=1000)
        self.assertEqual(second, "UNSAT")           # 여전히 결론이 난다

    def test_certificate_records_the_per_call_cap(self):
        d = json.loads((OUT / "rr_q2_zero_certificate.json").read_text())
        self.assertTrue(d["node_cap_is_per_call"])
        self.assertEqual(d["cap_hits"], 0)


class MinimalChain(unittest.TestCase):
    """§0 / §12 — W-A 와 (P) 전파 없이도 같은 결론."""

    def test_weighted_condition_alone_closes_every_hall_passing_pair(self):
        d = json.loads((OUT / "rr_q2_minimal_chain.json").read_text())
        self.assertTrue(d["minimal_chain"])
        self.assertEqual(d["wa_pairs"], 27095)
        self.assertEqual(d["wa_states"], 5030)
        self.assertEqual(d["assignments"], 251159)
        self.assertEqual(d["assignment_verdicts"], {"UNSAT": 251159})
        self.assertEqual(d["cap_hits"], 0)
        self.assertEqual(d["state_survivors"], 0)

    def test_domains_never_exceed_size_two_even_before_propagation(self):
        d = json.loads((OUT / "rr_q2_minimal_chain.json").read_text())
        self.assertEqual(set(d["domain_size_histogram"]), {"1", "2"})

    def test_hall_filter_is_not_needed_either(self):
        """Hall 까지 빼고 cover 90,396 전부에서 출발해도 잔여 0."""
        d = json.loads((OUT / "rr_q2_no_hall.json").read_text())
        self.assertEqual(d["wa_input_pairs"], 90396)
        self.assertEqual(d["wa_states"], 6396)
        self.assertEqual(d["assignments"], 707007)
        self.assertEqual(d["assignment_verdicts"], {"UNSAT": 707007})
        self.assertEqual(d["cap_hits"], 0)
        self.assertEqual(d["state_survivors"], 0)


class OmittedArcs(unittest.TestCase):
    """§0-B — 모델이 weight >= 4 joint 호를 생략한다는 사실과 그 여파."""

    def test_heavy_joints_really_connect_two_obligations(self):
        d = json.loads((OUT / "rr_omitted_arcs.json").read_text())
        self.assertEqual(d["weight_ge_4_moves"], 545)
        self.assertTrue(d["T1_is_weight2_and_others_weight3"])
        self.assertGreater(d["omitted_arcs_found"], 0)
        self.assertGreater(d["omitted_arc_cost_histogram"]["2"], 0)

    def test_root_bound_closures_are_split_out_and_counted(self):
        """뿌리 하한만으로 닫힌 상태는 joint weight 제한과 무관하게 배제된다."""
        with gzip.open(OUT / "rr_q2_no_hall_certificate.jsonl.gz", "rt") as fh:
            fh.readline()
            rows = [json.loads(line) for line in fh]
        per = {}
        for r in rows:
            per.setdefault(r["sid"], []).append(r["reason"])
        robust = [s for s, v in per.items() if all(x == "root_bound" for x in v)]
        self.assertEqual(len(per), 6396)
        self.assertEqual(len(robust), 5043)
        self.assertEqual(len(per) - len(robust), 1353)

    def test_zero_cost_arcs_stay_T1_only_under_the_full_move_set(self):
        """비용 0 인 joint 는 weight <= 2 뿐이고, 나머지 weight-2 이동은 같은 육각형이다."""
        import importlib.util as iu
        spec = iu.spec_from_file_location(
            "superperm_port_lift",
            ROOT / "legacy_research" / "work" / "superperm_port_lift.py")
        core = iu.module_from_spec(spec)
        sys.modules["superperm_port_lift"] = core
        spec.loader.exec_module(core)
        counts = [len(core.tail_permutations(w)) for w in range(1, 7)]
        self.assertEqual(counts, [1, 1, 3, 13, 71, 461])     # 합 550
        y = tuple(int(c) for c in "012345")
        light = ["".join(map(str, core.word_after(y, core.tail_action(w, pi))))
                 for w in (2, 3) for pi in core.tail_permutations(w)]
        # weight <= 3 인 joint 는 정확히 T1..T4 넷이고, 그중 비용 0 은 T1 하나다
        self.assertEqual(tuple(light), C.joint_words("012345"))


class DocumentDiscipline(unittest.TestCase):
    def test_proof_skeleton_has_the_required_sections(self):
        txt = DOC.read_text()
        for needed in ("정리 A", "정리 B", "보조정리 7", "보조정리 8",
                       "THEOREM 1 (unconditional-in-joint-weight partial exclusion)",
                       "THEOREM 2 (conditional Q2 exclusion)",
                       "독립 검증자가 확인해야 할 것"):
            self.assertIn(needed, txt)

    def test_the_unstated_hypothesis_is_recorded(self):
        """§0-B / (H5) — 무거운 joint 가 생략됐다는 사실을 문서가 숨기지 않는다."""
        txt = DOC.read_text()
        self.assertIn("(H5)", txt)
        self.assertIn("5,043", txt)
        self.assertIn("1,353", txt)

    def test_proof_skeleton_keeps_the_wording_rules(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)
        self.assertNotIn("L6 >= 872 proved", txt)

    def test_theorem_statement_does_not_mention_the_length(self):
        txt = DOC.read_text()
        for name in ("THEOREM 1 (unconditional-in-joint-weight partial exclusion)",
                     "THEOREM 2 (conditional Q2 exclusion)"):
            start = txt.index(name)
            end = txt.index("**Proof.**", start)
            self.assertNotIn("872", txt[start:end])


if __name__ == "__main__":
    unittest.main()
