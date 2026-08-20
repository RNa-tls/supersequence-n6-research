"""라운드 108 — (H5) 해소 라운드의 사실들을 회귀로 고정한다.

감사 원장(4,782)은 건드리지 않는다.
"""

from __future__ import annotations

import gzip
import importlib.util as iu
import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DOC = ROOT / "research" / "RR_H5_RESOLUTION_CLAUDE.md"


def _load(name, rel):
    spec = iu.spec_from_file_location(name, ROOT / rel)
    mod = iu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FJ = _load("certify_rr_full_joint", "src/certify_rr_full_joint.py")
core = FJ.core


def lit():
    return json.loads((OUT / "rr_heavy_joint_literal.json").read_text())


class TailAlphabet(unittest.TestCase):
    """§5/§9 — 이동 집합과 비용 공식."""

    def test_indecomposable_tail_counts(self):
        self.assertEqual([len(core.tail_permutations(w)) for w in range(1, 7)],
                         [1, 1, 3, 13, 71, 461])
        self.assertEqual(len(FJ.TAILS) + 1, 550)

    def test_cost_formula_values(self):
        self.assertEqual([FJ.cost_of(w) for w in range(1, 7)], [0, 0, 1, 2, 3, 4])

    def test_only_one_tail_has_cost_zero_among_joints(self):
        """정리 Z — 비용-0 joint 는 weight-2 tail 하나뿐이다."""
        free = [w for w, _a in FJ.TAILS if FJ.cost_of(w) == 0]
        self.assertEqual(free, [2])

    def test_cost_formula_is_exact_against_the_literal_engine(self):
        d = lit()
        self.assertGreater(d["event_table_transitions_checked"], 10_000)
        self.assertEqual(d["cost_formula_mismatches"], 0)
        self.assertTrue(d["cost_formula_is_exact_for_S_plus_H"])


class HSemantics(unittest.TestCase):
    """§2/§3 — H 의 정의와 단순 단조성 경로가 왜 무효인가."""

    def test_every_archived_state_has_H_zero(self):
        with gzip.open(ROOT / "outputs" / "rr_port_path_hall_archive" / "states.jsonl.gz",
                       "rt") as fh:
            fh.readline()
            st = [json.loads(line) for line in fh]
        self.assertEqual(Counter(s["H"] for s in st), {0: 6396})

    def test_the_target_allows_H_up_to_three(self):
        """`final_target` 은 H = 0 을 요구하지 않는다 — 단순 경로는 여기서 깨진다."""
        src = (ROOT / "legacy_research" / "work" / "superperm_partial_f1.py").read_text()
        self.assertIn("state.Ndef + state.H <= TARGET_BUDGET", src)
        self.assertNotIn("state.H == 0", src)
        self.assertIn("if state.H > TARGET_BUDGET", src)

    def test_area_A_prunes_H_positive_only_for_the_boundary(self):
        src = (ROOT / "src" / "search_rr_target_a_unified.py").read_text()
        self.assertIn("if state.H > 0:", src)
        self.assertIn("the R2-boundary CHILD has H == 0 exactly", src)


class H5Local(unittest.TestCase):
    """§6 — H5-local 은 리터럴 반례로 거짓이다."""

    def test_a_legal_heavy_joint_prefix_exists(self):
        ce = lit()["h5_local_counterexample"]
        self.assertIsNotNone(ce)
        self.assertGreaterEqual(ce["weight"], 4)
        self.assertTrue(ce["target_is_an_obligation_entry_word"])
        self.assertIsNone(ce["engine_prune_reason_after"])
        self.assertLessEqual(ce["after"]["Ndef_plus_H"], 3)

    def test_heavy_moves_are_plentiful(self):
        h = lit()["heavy_legal_moves_by_weight"]
        self.assertGreater(sum(h.values()), 1000)


class H5Replacement(unittest.TestCase):
    """§12 — 지배(치환) 경로도 거짓이다."""

    def test_heavy_arcs_join_component_pairs_light_arcs_cannot(self):
        d = json.loads((OUT / "rr_heavy_dominance.json").read_text())
        self.assertGreater(d["component_pairs_joined_only_by_heavy_arcs"],
                           d["component_pairs_joined_by_a_light_arc"])
        self.assertGreater(d["heavy_only_arc_fraction"], 0.9)


class PositiveControls(unittest.TestCase):
    """§14 — 완전-joint 생성기가 엔진의 전이를 빠뜨리지 않는다."""

    def test_no_engine_transition_is_missing_from_the_model(self):
        d = lit()
        self.assertGreater(d["positive_control_engine_transitions"], 1000)
        self.assertEqual(d["positive_control_missing_from_model"], 0)


class HeavyBudgetLemma(unittest.TestCase):
    """§4.1 — 무거운-호 예산 보조정리를 작은 예로 고정한다."""

    def test_zero_slack_forbids_every_heavy_arc(self):
        # 정점 3개, 비용-0 호 없음 -> c = 3.  무료 진입 없음 -> L2 = 3.  B = 3 -> s = 0.
        out0 = [0, 0, 0]
        self.assertEqual(FJ.root_bound(out0, 0), 3)
        self.assertEqual(FJ.root_bound(out0, 0b001), 2)

    def test_exit_bound_never_falls_below_the_component_bound(self):
        out = [[0, 0, 0], [0b110, 0b001, 0b010], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        rem = 0b111
        cb = FJ.components(out[0], rem) - 1
        self.assertGreaterEqual(FJ.exit_bound(out, 0, rem & ~1), cb - 1)


class DocumentDiscipline(unittest.TestCase):
    def test_document_states_all_three_H5_versions(self):
        txt = DOC.read_text()
        for needed in ("H5-local", "H5-target", "H5-replacement", "정리 Z", "정리 R"):
            self.assertIn(needed, txt)

    def test_wording_rules(self):
        txt = DOC.read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)


class AuditPackage(unittest.TestCase):
    def test_audit_package_is_self_describing(self):
        m = json.loads((OUT / "rr_h5_audit" / "h5_manifest.json").read_text())
        self.assertEqual(m["H5_statements"]["needed_by_the_round_107_certificate"],
                         "H5-target (또는 그보다 강한 H5-local)")
        t = json.loads((OUT / "rr_h5_audit" / "tail_generator.json").read_text())
        self.assertEqual(t["total_including_rotation"], 550)
        self.assertEqual(t["count_by_weight"],
                         {"2": 1, "3": 3, "4": 13, "5": 71, "6": 461})
        c = json.loads((OUT / "rr_h5_audit" / "conditional_states.json").read_text())
        r = json.loads((OUT / "rr_h5_audit" / "robust_states.json").read_text())
        self.assertEqual(c["count"], 1353)
        self.assertEqual(r["count"], 5043)
        self.assertEqual(len(set(c["sids"]) & set(r["sids"])), 0)


if __name__ == "__main__":
    unittest.main()


class FullJointRecomputation(unittest.TestCase):
    """§10/§16 — (H5) 를 쓰지 않은 완전-joint 재계산."""

    def cert(self):
        return json.loads((OUT / "rr_full_joint_certificate.json").read_text())

    def test_population_is_the_round_107_conditional_block(self):
        d = self.cert()
        self.assertEqual(d["robust_states_round107"], 5043)
        self.assertEqual(d["conditional_states_round107"], 1353)
        self.assertEqual(d["states_processed"], 1353)
        self.assertEqual(d["tails_used"], 550)

    def test_no_assignment_is_ever_satisfiable(self):
        d = self.cert()
        self.assertEqual(d["assignment_verdicts"].get("SAT", 0), 0)
        self.assertEqual(d["pair_verdicts"].get("SAT", 0), 0)
        self.assertEqual(d["heavy_edges_in_surviving_paths"], {})

    def test_most_assignments_need_no_H5_at_all(self):
        """s <= 0 이면 무거운 호를 하나도 쓸 수 없다 — (H5) 가 정리인 구간."""
        d = self.cert()
        hist = {int(k): v for k, v in d["root_slack_histogram"].items()}
        zero_or_less = sum(v for k, v in hist.items() if k <= 0)
        self.assertEqual(d["assignments_with_zero_or_negative_slack"], zero_or_less)
        self.assertGreater(zero_or_less / d["assignments"], 0.75)
        self.assertEqual(d["assignments_where_H5_is_a_theorem"], hist[0])

    def test_survivors_are_cap_unknown_not_sat(self):
        d = self.cert()
        self.assertEqual(d["state_survivors"], 166)
        self.assertEqual(d["cap_hits"], d["assignment_verdicts"]["UNKNOWN"])
        self.assertGreater(d["cap_hits"], 0)

    def test_the_H5_independent_residual_shrank_from_1353(self):
        d = self.cert()
        closed = d["conditional_states_round107"] - d["state_survivors"]
        self.assertEqual(closed, 1187)
        self.assertLess(d["state_survivors"], d["conditional_states_round107"])

    def test_leftover_state_list_is_exported(self):
        p = json.loads((OUT / "rr_h5_audit" / "phase1_unknown_states.json").read_text())
        self.assertEqual(p["count"], 166)
        self.assertEqual(len(p["sids"]), 166)
