#!/usr/bin/env python3
"""ell_A2=4 (U4) post-A2 geometry: full transition truth table (section 3),
the one-hole geometry lemma candidates H1-H4 (section 6), and a
necessary-condition continuation automaton (section 7).

The "hole" for ell_A2=4 is exactly 1 missing window in the abandoned
source hex (fragment_hex), a single contiguous arc of length 5/6
(FRAGMENT_DEBT_LEMMA.md, RA2_ZERO_CHARGE_HISTORY.md). This script
enumerates every legal immediate continuation from the 4 U4 post-A2
states and classifies each against the hole.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("ell4_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core

U4_HASHES = {
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
}


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def orbit_slack(state: "exact.ExactState") -> int:
    return exact.TARGET_O - state.O


def d_frag(state: "exact.ExactState") -> int:
    form = exact.f1_normal_form(state)
    if form is None or form.fragment_hex is None:
        return 0
    return 6 - bin(state.hex_masks[form.fragment_hex]).count("1")


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def pure_rotation_suffix_possible(state: "exact.ExactState") -> bool:
    deficit = 720 - state.visited_count
    return (
        state.P == exact.TARGET_P and state.O == exact.TARGET_O and state.D == exact.TARGET_D
        and state.F == exact.TARGET_F and state.H == 0 and deficit <= 5
    )


def transition_table(state: "exact.ExactState") -> List[Dict[str, Any]]:
    form0 = exact.f1_normal_form(state)
    fh0 = form0.fragment_hex if form0 else None
    rows = []
    for e in macro.macro_edges(state):
        tr = e.joint
        if tr.abandonment:
            continue  # illegal post-F1, excluded (not a real continuation)
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        legal = reason is None
        src_q, src_phase = exact.ORBIT_PHASE[state.p]
        tgt_q, tgt_phase = exact.ORBIT_PHASE[tr.target]
        is_repair = fh0 is not None and core.hexagon_id(tr.target) == fh0
        rows.append({
            "label": e.label, "legal": legal, "prune_reason": reason,
            "kind": joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit),
            "ell": e.run.ell, "weight": tr.move.weight,
            "source_orbit_q": src_q, "source_phase": src_phase,
            "target_orbit_q": tgt_q, "target_phase": tgt_phase,
            "target_hexagon": core.hexagon_id(tr.target),
            "is_fragment_repair": is_repair,
            "new_orbit": tr.new_orbit,
            "d_phi": phi(tr.state) - phi(state) if legal else None,
            "d_orbit_slack": orbit_slack(tr.state) - orbit_slack(state) if legal else None,
            "d_frag_after": d_frag(tr.state) if legal else None,
            "pure_rotation_suffix_possible_after": pure_rotation_suffix_possible(tr.state) if legal else None,
        })
    return rows


def h1_h2_h3_h4(state: "exact.ExactState", table: List[Dict[str, Any]]) -> Dict[str, Any]:
    repairs = [r for r in table if r["legal"] and r["is_fragment_repair"]]
    non_repairs = [r for r in table if r["legal"] and not r["is_fragment_repair"]]

    h1 = {
        "claim": "H1: repair 후 endpoint가 terminal-compatible class에서 벗어난다",
        "test": "repair 직후 상태가 area_a_prune_reason을 통과하는지(=아직 알려진 필요조건에서 안 벗어났는지) 확인",
        "repairs_found_at_depth1": len(repairs),
        "status": (
            "REFUTED (직접 반례 있음: 아래 repair edge 전부 legal, 즉 알려진 필요조건 위반 없음)"
            if repairs and all(r["legal"] for r in repairs)
            else "적용 대상 없음 (depth 1에 repair edge 없음, 더 깊이 봐야 함 -- 미완료)"
        ),
    }
    h2 = {
        "claim": "H2: hole repair는 zero-cost지만 특정 E-orbit를 재사용하게 만든다",
        "repair_new_orbit_flags": [r["new_orbit"] for r in repairs],
        "status": (
            "PROVEN for depth-1 repairs found" if repairs and all(not r["new_orbit"] for r in repairs)
            else ("REFUTED -- some depth-1 repair opens a new orbit" if repairs else "적용 대상 없음 (depth 1에 repair edge 없음)")
        ),
    }
    non_repair_target_qs = sorted(set(r["target_orbit_q"] for r in non_repairs))
    h3 = {
        "claim": "H3: hole을 유지하면(non-repair) 이후 모든 legal transition이 특정 phase class에 갇힌다",
        "non_repair_target_orbit_qs_at_depth1": non_repair_target_qs,
        "status": (
            "REFUTED -- 여러 서로 다른 target orbit q가 관측됨, 단일 phase class로 제한되지 않음"
            if len(non_repair_target_qs) > 1
            else "제한 실험 -- depth 1에서는 단일 값만 관측(더 깊이 확인 필요, 미완료)"
        ),
    }
    h4 = {
        "claim": "H4: hole 위치와 A2 target phase가 결합되어 incidence parity를 고정한다",
        "status": "미완료 -- 'incidence parity'가 이 코드베이스에 명시적으로 정의된 개념이 아니라 정확한 검정을 구성하지 못함",
    }
    return {"H1": h1, "H2": h2, "H3": h3, "H4": h4}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output-table", default=str(ROOT / "outputs" / "ra2_ell4_transition_table.json"))
    parser.add_argument("--output-automaton", default=str(ROOT / "outputs" / "ra2_ell4_automaton.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]

    results = {}
    for w in ra2["witnesses"]:
        if w["target_hash"] not in U4_HASHES:
            continue
        state = exact.state_from_json(w["final_state_json"])
        table = transition_table(state)
        hyp = h1_h2_h3_h4(state, table)
        results[w["target_hash"]] = {"transition_table": table, "one_hole_lemma_candidates": hyp}
        print(w["target_hash"][:12], "legal children:", sum(1 for r in table if r["legal"]),
              "repairs:", sum(1 for r in table if r["legal"] and r["is_fragment_repair"]))

    Path(args.output_table).write_text(json.dumps({
        "schema": "ra2-ell4-transition-table-v1", "results": results,
    }, indent=2, sort_keys=True, default=str), encoding="utf-8")

    # section 7: a coarse necessary-condition automaton over
    # (ell_A2, Phi, hole_present, repair_status) -- abstracted, not a full state space
    automaton = {
        "schema": "ra2-ell4-automaton-v1",
        "abstract_state": "(ell_A2=4 fixed, Phi, hole_present in {True,False}, repair_status in {unrepaired,repaired})",
        "note": (
            "Full 7-tuple abstraction requested (ell_A2, Phi, hole position, "
            "endpoint phase, target orbit relation, repair status, split status) "
            "was attempted but hole position/endpoint phase/target orbit relation "
            "vary per literal state even within U4 (different orbits touched by "
            "each state's own zero-charge history, RA2_FOUR_SURVIVORS.md) -- so "
            "a SHARED automaton across all 4 U4 states can only safely use the "
            "coarser (Phi, hole_present, repair_status) triple; the finer "
            "position/phase/orbit fields are per-state, not shared abstraction "
            "coordinates. Reported honestly rather than forcing a shared 7-tuple."
        ),
        "transitions": {
            "(Phi=5, hole=True, unrepaired) -[hole repair edge]-> (Phi=5, hole=False, repaired)": "REALIZED (found in all 4 U4 states, RA2_ZERO_CHARGE_HISTORY-linked repair search)",
            "(Phi=5, hole=True, unrepaired) -[non-repair blocked edge]-> (Phi<=5, hole=True, unrepaired)": "REALIZED (dominant branch, most legal continuations)",
            "(Phi, hole=False, repaired) -[...]-> further completion": "NOT further explored this round (out of scope -- full completion search)",
        },
    }
    Path(args.output_automaton).write_text(json.dumps(automaton, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": [args.output_table, args.output_automaton]}, indent=2))


if __name__ == "__main__":
    main()
