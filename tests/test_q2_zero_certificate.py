"""라운드 106 — 인증서·검증기·대조 실험을 회귀로 고정한다.

원장 규칙: 이 테스트들은 **감사 원장(4,782)을 건드리지 않는다.**  라운드-106 잠정 결과가
사라지거나 조용히 약해지는 것을 막는 것이 목적이다.
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


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


C = _load("certify_rr_q2_zero", "src/certify_rr_q2_zero.py")
V = _load("verify_rr_q2_zero", "src/verify_rr_q2_zero.py")


def cert():
    return json.loads((OUT / "rr_q2_zero_certificate.json").read_text())


def ctrl():
    return json.loads((OUT / "rr_q2_zero_controls.json").read_text())


class Theorem1(unittest.TestCase):
    """정리 1 — `c` 대 `c−1` 의 경우 분리가 코드에 실제로 들어 있는가."""

    def test_root_bound_distinguishes_the_two_cases(self):
        out0 = [0, 0]                       # 비용-0 호 없음 → 성분 2개
        self.assertEqual(C.root_lower_bound(out0, r0=0), 2)
        self.assertEqual(C.root_lower_bound(out0, r0=0b01), 1)

    def test_zero_cost_chain_is_one_component(self):
        out0 = [0b10, 0]                    # 0 → 1 사슬
        self.assertEqual(C.root_lower_bound(out0, r0=0), 1)
        self.assertEqual(C.root_lower_bound(out0, r0=0b01), 0)

    def test_precondition_violation_stops_the_solver(self):
        """비용-0 유출 차수 2 는 하한을 불건전하게 만든다 — 반드시 멈춰야 한다."""
        out0 = [0b0110, 0, 0, 0]
        out1 = [0, 0b1000, 0b1000, 0]
        stats = Counter()
        with self.assertRaises(AssertionError):
            C.solve(out0, out1, r0=0b0001, r1=0, B=2, stats=stats)
        self.assertEqual(stats["precondition_violations"], 1)

    def test_verifier_rejects_outdegree_violation_too(self):
        adj = {"a": [(0, "b"), (0, "c")], "b": [], "c": []}
        with self.assertRaises(SystemExit):
            V.zero_succ(adj)


class GeometryTheorem(unittest.TestCase):
    def test_four_targets_live_in_four_distinct_hexagons(self):
        audit = {}
        C.geometry(audit)                   # 위반이면 AssertionError 로 죽는다
        self.assertEqual(audit["geometry_contexts"], 4320)
        self.assertEqual(audit["geometry_archive_mismatches"], 0)
        self.assertTrue(audit["hexagon_is_rotation_class"])


class BudgetTheorem(unittest.TestCase):
    def test_K_equals_25_minus_O_on_every_state(self):
        d = cert()["audit"]
        self.assertEqual(d["K_equals_25_minus_O_violations"], 0)

    def test_budget_is_far_below_the_number_of_obligations(self):
        hist = {int(k): v for k, v in cert()["audit"]["budget_histogram"].items()}
        self.assertEqual(min(hist), 18)
        self.assertEqual(max(hist), 25)
        self.assertEqual(sum(hist.values()), 6396)


class FullRecomputation(unittest.TestCase):
    def test_population_is_the_hall_superset_not_the_filtered_archive(self):
        d = cert()
        self.assertEqual(d["audit"]["hall_passing_pairs"], 27095)
        self.assertEqual(d["audit"]["hall_passing_states"], 5030)
        self.assertEqual(d["wa_input_pairs"], 27095)

    def test_archive_population_subtotals_reproduce_round_100(self):
        """상위집합 계산이 아카이브 모집단으로 제한하면 4,230 / 15,781 을 그대로 낸다."""
        d = cert()
        self.assertEqual(d["wa_states_in_archive_pop"], 4230)
        self.assertEqual(d["wa_pairs_in_archive_pop"], 15781)

    def test_every_assignment_is_unsat_with_no_cap_hit(self):
        d = cert()
        self.assertEqual(d["assignments"], 184661)
        self.assertEqual(d["assignment_verdicts"], {"UNSAT": 184661})
        self.assertEqual(d["cap_hits"], 0)

    def test_no_precondition_violation_static_or_dynamic(self):
        d = cert()
        self.assertEqual(d["precondition_violations"], 0)
        self.assertGreater(d["precondition_checks"], 10_000_000)
        self.assertGreater(d["dynamic_precondition_checks"], 50_000_000)

    def test_state_survivors_are_zero_but_only_provisionally(self):
        d = cert()
        self.assertEqual(d["state_survivors"], 0)
        self.assertEqual(d["state_survivors_archive_pop"], 0)
        self.assertEqual(d["pair_verdicts"], {"FAIL": 17350})

    def test_branching_pairs_never_approached_the_node_cap(self):
        """캡은 **호출당** 2,000,000 이다 (라운드 107 정정).  가장 비싼 쌍도 12,611 노드."""
        d = cert()
        self.assertEqual(d["pairs_needing_branching"], 5771)
        self.assertTrue(d["node_cap_is_per_call"])
        self.assertLess(d["search_nodes_max_per_pair"], d["node_cap"] // 100)


class CertificateFile(unittest.TestCase):
    def test_certificate_rows_match_the_summary(self):
        with gzip.open(OUT / "rr_q2_zero_certificate.jsonl.gz", "rt") as fh:
            head = json.loads(fh.readline())
            rows = [json.loads(line) for line in fh]
        self.assertEqual(head["rows"], len(rows))
        self.assertEqual(len(rows), 17350)
        self.assertEqual(Counter(r["verdict"] for r in rows), {"FAIL": 17350})
        reasons = Counter(r["reason"] for r in rows)
        self.assertEqual(reasons["root_bound"] + reasons["exhaustive_search"], 17350)

    def test_independent_verifier_reports_zero_remaining(self):
        d = json.loads((OUT / "rr_q2_zero_verify.json").read_text())
        self.assertEqual(d["errors"], {})
        self.assertEqual(d["missing_certificate_rows"], 0)
        self.assertEqual(d["remaining_states"], 0)
        self.assertEqual(d["states_walked"], 5030)
        self.assertEqual(d["stats"]["assignment_UNSAT"], 184661)
        self.assertNotIn("assignment_UNKNOWN", d["stats"])


class Controls(unittest.TestCase):
    def test_small_instances_agree_with_exhaustive_enumeration(self):
        d = ctrl()["s13_small_exact"]
        self.assertEqual(d["verdict_mismatches"], 0)
        self.assertEqual(d["root_bound_violations"], 0)
        self.assertGreater(d["verdict_checks"], 20_000)

    def test_positive_controls_never_produce_a_false_unsat(self):
        d = ctrl()["s14_positive_controls"]
        self.assertEqual(d["false_unsat"], 0)
        self.assertEqual(d["verdicts"], {"SAT": 8000})
        self.assertEqual(d["prefix_bound_violations"], 0)
        self.assertGreater(d["prefix_bound_checks"], 20_000)

    def test_dynamic_lower_bound_never_exceeds_the_true_optimum(self):
        d = ctrl()["s11_dynamic_soundness"]
        self.assertEqual(d["violations"], 0)
        self.assertGreater(d["residuals_compared_to_true_optimum"], 500)
        self.assertEqual(ctrl()["s11b_deep_prefixes"]["violations"], 0)

    def test_a_solver_that_never_uses_theorem_1_confirms_the_hard_cases(self):
        rows = ctrl()["s12_alternative_solvers"]["rows"]
        self.assertEqual(rows.get("MISMATCH_nomemo", 0), 0)
        self.assertEqual(rows.get("MISMATCH_nobound", 0), 0)
        self.assertGreaterEqual(rows.get("nobound=UNSAT", 0), 40)

    def test_conventions_are_pinned(self):
        d = ctrl()["s15_conventions"]
        self.assertEqual(d["expectation_mismatches"], 0)
        self.assertTrue(d["K_equals_25_minus_O"])


class Fragility(unittest.TestCase):
    """구제 진단.

    라운드 106 은 "`B+1` 이면 2,271 상태가 되살아난다" 고 적었다.  라운드 107 이 그것을
    철회했다 — 누적 노드 캡 때문에 생긴 인공물이었다.  호출당 캡으로 고친 뒤에는 `B+1`
    에서도 잔여가 0 이다.  이 테스트는 **정정된 사실**을 고정한다.
    """

    def test_budget_plus_one_and_plus_two_still_close_everything(self):
        for delta, name in ((1, "rr_q2_rescue_b1.json"), (2, "rr_q2_rescue_b2.json")):
            d = json.loads((OUT / name).read_text())
            self.assertEqual(d["budget_delta"], delta)
            self.assertEqual(d["cap_hits"], 0, name)
            self.assertEqual(d["assignment_verdicts"], {"UNSAT": 184661}, name)
            self.assertEqual(d["state_survivors"], 0, name)

    def test_the_root_bound_weakens_as_the_budget_grows(self):
        """여유가 어디서 오는지 기록한다 — 뿌리 하한은 약해지고 분기가 대신 일한다."""
        base = cert()["pairs_closed_by_root_bound"]
        b1 = json.loads((OUT / "rr_q2_rescue_b1.json").read_text())
        b2 = json.loads((OUT / "rr_q2_rescue_b2.json").read_text())
        self.assertGreater(base, b1["pairs_closed_by_root_bound"])
        self.assertGreater(b1["pairs_closed_by_root_bound"], b2["pairs_closed_by_root_bound"])
        self.assertGreater(b2["search_nodes_total"], 10 * cert()["search_nodes_total"])

    def test_no_sat_witness_ever_appears(self):
        """캡 도달은 UNSAT 도 SAT 도 아니다 — SAT 은 한 번도 나오지 않아야 한다."""
        for name in ("rr_q2_rescue_b1.json", "rr_q2_zero_certificate.json",
                     "rr_q2_minimal_chain.json", "rr_q2_no_hall.json"):
            d = json.loads((OUT / name).read_text())
            self.assertEqual(d["assignment_verdicts"].get("SAT", 0), 0, name)

    def test_the_retraction_is_recorded_in_the_document(self):
        txt = (ROOT / "research" / "RR_Q2_ZERO_CERTIFICATE_CLAUDE.md").read_text()
        self.assertIn("정정 상자", txt)
        self.assertIn("철회", txt)


class LedgerDiscipline(unittest.TestCase):
    def test_document_never_claims_the_lower_bound(self):
        txt = (ROOT / "research" / "RR_Q2_ZERO_CERTIFICATE_CLAUDE.md").read_text()
        self.assertIn("This project has not proved `L₆ ≥ 872`.", txt)
        self.assertIn("4,782", txt)
        for banned in ("L₆ = 872 가 증명", "무조건적 Q2 정리가 성립"):
            self.assertNotIn(banned, txt)

    def test_audited_ledger_is_untouched_by_this_round(self):
        d = cert()
        self.assertNotIn("audited", json.dumps(d).lower().replace("unaudited", ""))


if __name__ == "__main__":
    unittest.main()
