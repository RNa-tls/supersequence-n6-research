#!/usr/bin/env python3
"""RA2: exact dissection of the zero-charge joint word between the first R
event and the A2 event, for all 24 witnesses (U4 and C20 alike).

Established facts this builds on (from RA2_FOUR_SURVIVORS.md,
FRAGMENT_DEBT_LEMMA.md): fragment_hex is None throughout the R-to-A2
window for every RA2 state (F=0 until A2 fires -- A2 IS the walk's one
allowed abandonment, so no earlier abandonment, visible or the hidden
zero-charge Z2abandon, can occur first; Z2abandon costing F would make A2
itself illegal afterward). So the R-to-A2 zero-charge word can only
contain Z2 and Z3 joints (both abandonment=False) plus rotations -- never
Z2abandon. This is verified computationally below, not just assumed.

Since fragment_hex does not exist yet in this window, "fragment debt" is
tracked here as CURRENT-hex debt: 6 - popcount(hex_masks[current_hex]).
This is exactly the quantity that becomes d_frag the instant A2 fires
(A2's abandonment makes the pre-A2 current hex into the new fragment_hex).
Tracking it across the R-to-A2 word answers directly "at which exact
transition does the eventual fragment-debt value first become fixed".
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

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


macro = _load("zch_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1

U4_HASHES = {
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
}


def current_hex_debt(state: "exact.ExactState") -> int:
    return 6 - bin(state.hex_masks[state.current_hex]).count("1")


def orbit_slack(state: "exact.ExactState") -> int:
    return exact.TARGET_O - state.O


def component_map(state: "exact.ExactState") -> Dict[Any, Any]:
    parent: Dict[Any, Any] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return {node: find(node) for node in list(parent)}


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def dissect(witness: Dict[str, Any]) -> Dict[str, Any]:
    macro_path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    steps = []  # per macro-edge: dict with kind, pre/post state, etc.
    for step in macro_path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        pre_joint = cur
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        post = tr.state
        cur = exact.canonicalize(post)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        steps.append({"ell": ell, "kind": kind, "transition": tr, "pre_joint": pre_joint, "post_raw": post, "post_canon": cur})

    events = [i for i, s in enumerate(steps) if s["kind"] in ("R", "A2", "A3", "J")]
    assert len(events) == 2, f"expected exactly 2 defect events, got {len(events)}"
    r_idx, a2_idx = events
    assert steps[r_idx]["kind"] == "R" and steps[a2_idx]["kind"] == "A2"

    zero_charge_word = []
    roots_cache = {}
    for i in range(r_idx + 1, a2_idx):
        s = steps[i]
        pre = s["pre_joint"]
        tr = s["transition"]
        roots = component_map(pre)
        src_q, src_phase = exact.ORBIT_PHASE[pre.p]
        tgt_q, tgt_phase = exact.ORBIT_PHASE[tr.target]
        src_root = roots.get(("q", src_q))
        tgt_root = roots.get(("q", tgt_q))
        zero_charge_word.append({
            "step_index": i,
            "joint_type": s["kind"],
            "ell": s["ell"],
            "weight": tr.move.weight,
            "source_orbit_q": src_q, "source_phase": src_phase,
            "target_orbit_q": tgt_q, "target_phase": tgt_phase,
            "source_hexagon": core.hexagon_id(pre.p), "target_hexagon": core.hexagon_id(tr.target),
            "component_relation": (
                "same" if src_root is not None and src_root == tgt_root else
                "different" if src_root is not None and tgt_root is not None else "unresolved"
            ),
            "current_hex_before": pre.current_hex, "current_hex_after": tr.state.current_hex,
            "current_hex_debt_before": current_hex_debt(pre), "current_hex_debt_after": current_hex_debt(tr.state),
            "orbit_slack_before": orbit_slack(pre), "orbit_slack_after": orbit_slack(tr.state),
            "endpoint_before": list(pre.p), "endpoint_after": list(tr.target),
            "new_orbit": tr.new_orbit,
        })

    r_state = steps[r_idx]["transition"].state
    a2_pre = steps[a2_idx]["pre_joint"]
    a2_post = steps[a2_idx]["transition"].state

    return {
        "target_hash": witness["target_hash"],
        "group": "U4" if witness["target_hash"] in U4_HASHES else "C20",
        "macro_distance_R_to_A2": a2_idx - r_idx,
        "zero_charge_word_length": a2_idx - r_idx - 1,
        "zero_charge_word": zero_charge_word,
        "debt_right_after_R": current_hex_debt(r_state),
        "debt_right_before_A2": current_hex_debt(a2_pre),
        "debt_locked_by_A2": current_hex_debt(a2_post) if exact.f1_normal_form(a2_post) and exact.f1_normal_form(a2_post).fragment_hex is not None else None,
        "debt_first_reaches_final_value_at_step": next(
            (zc["step_index"] for zc in zero_charge_word if zc["current_hex_debt_after"] == current_hex_debt(a2_pre)),
            r_idx if current_hex_debt(r_state) == current_hex_debt(a2_pre) else None,
        ),
        "all_zero_charge_kinds_are_blocked": all(zc["joint_type"] in ("Z2", "Z3") for zc in zero_charge_word),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_zero_charge_words.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    assert ra2["recovered"] == 24

    records = [dissect(w) for w in ra2["witnesses"]]
    no_abandon_violations = [r["target_hash"] for r in records if not r["all_zero_charge_kinds_are_blocked"]]

    report = {
        "schema": "ra2-zero-charge-words-v1",
        "claim_verified_no_hidden_abandonment_before_A2": {
            "claim": "the R-to-A2 zero-charge word never contains Z2abandon (or any abandoning kind) -- A2 IS the walk's one allowed abandonment, so no earlier one can fire without making A2 itself illegal",
            "violations_found": no_abandon_violations,
            "holds_over_all_24": len(no_abandon_violations) == 0,
        },
        "records": records,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "holds_over_all_24": report["claim_verified_no_hidden_abandonment_before_A2"]["holds_over_all_24"],
        "debt_right_before_A2_by_group": {
            r["target_hash"][:12]: (r["group"], r["debt_right_before_A2"], r["zero_charge_word_length"]) for r in records
        },
    }, indent=2))


if __name__ == "__main__":
    main()
