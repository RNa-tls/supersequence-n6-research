#!/usr/bin/env python3
"""RA2: exact field-by-field comparison of C20 (proved incomplete via the
Phi capacity potential) vs U4 (the 4 states unresolved even at
depth<=18, edge_cap=1,500,000 in search_ra2_exact.py).

For every one of the 24 RA2 states, computes the same set of fields at
four points: immediately before/after the first event (R), and
immediately before/after the second event (A2). All fields are derived
directly from the exact engine (exact.ExactState, exact.f1_normal_form,
macro.macro_edges) -- nothing is data-fit or estimated.

"Split hexagon" is not a distinct field anywhere in this codebase (grep
confirms). Consistent with this project's own prior usage
(research/J_BRANCH_CLOSURE_STATUS.md J5: "'split hexagon'이 J의
target/source와 정확히 어떤 관계인지에 대한 이번 코퍼스의 명시적 정의를
찾지 못했다"), this script treats "split hexagon" as an alias for
exact.f1_normal_form(state).fragment_hex -- the unique non-current
partial hexagon -- and says so explicitly in every record, rather than
inventing a new, unverified concept.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
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


macro = _load("ra2s_macro", "superperm_partial_f1_macro.py")
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


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def pure_rotation_suffix_possible(state: "exact.ExactState") -> bool:
    """Completion is reachable via trailing rotations alone (no further
    joints) iff every non-P/O/D/F/H resource is already at target and the
    remaining unvisited windows (all necessarily within current_hex) number
    at most 5 (one rotation run's worth)."""
    deficit = 720 - state.visited_count
    return (
        state.P == exact.TARGET_P
        and state.O == exact.TARGET_O
        and state.D == exact.TARGET_D
        and state.F == exact.TARGET_F
        and state.H == 0
        and deficit <= 5
    )


def snapshot(state: "exact.ExactState") -> Dict[str, Any]:
    form = exact.f1_normal_form(state)
    non_full_hex = [
        {"hex": h, "mask": mask, "components": list(exact.cyclic_components(mask))}
        for h, mask in enumerate(state.hex_masks)
        if mask not in (0, exact.FULL_HEX)
    ]
    q, phase = exact.ORBIT_PHASE[state.p]
    edges = list(macro.macro_edges(state))
    legal_ell5 = sum(1 for e in edges if e.run.ell == 5)
    legal_positive_charge = sum(1 for e in edges if (e.joint.state.Ndef - state.Ndef) != 0)
    return {
        "endpoint_permutation": list(state.p),
        "endpoint_orbit_q": q,
        "endpoint_orbit_phase": phase,
        "current_hex": state.current_hex,
        "fragment_hex_aka_split_hex": form.fragment_hex if form else None,
        "fragment_components": [list(c) for c in form.fragment_components] if form else None,
        "P": state.P, "F": state.F, "S": state.S, "H": state.H,
        "O": state.O, "D": state.D, "N_charge_Ndef": state.Ndef,
        "visited_count": state.visited_count,
        "phi": phi(state),
        "remaining_orbit_count": exact.TARGET_O - state.O,
        "remaining_deficit_windows": 720 - state.visited_count,
        "non_full_hexagon_masks": non_full_hex,
        "legal_macro_children_total": len(edges),
        "legal_ell5_children": legal_ell5,
        "legal_positive_charge_children": legal_positive_charge,
        "pure_rotation_suffix_possible": pure_rotation_suffix_possible(state),
    }


def event_orbit(pre_joint_state: "exact.ExactState", transition: "exact.Transition") -> Dict[str, Any]:
    source_q, source_phase = exact.ORBIT_PHASE[pre_joint_state.p]
    target_q, target_phase = exact.ORBIT_PHASE[transition.target]
    return {
        "source_orbit_q": source_q, "source_phase": source_phase,
        "target_orbit_q": target_q, "target_phase": target_phase,
        "target_hexagon": core.hexagon_id(transition.target),
        "weight": transition.move.weight,
        "abandonment": transition.abandonment,
        "new_orbit": transition.new_orbit,
    }


def component_map(state: "exact.ExactState") -> Any:
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
    roots = {node: find(node) for node in list(parent)}
    return roots


def analyze_one(word_witness: Dict[str, Any]) -> Dict[str, Any]:
    macro_path = word_witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    events = []  # list of (index, pre_joint_state, transition, post_state)
    for idx, step in enumerate(macro_path):
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
        delta_n = post.Ndef - pre_joint.Ndef
        if delta_n != 0:
            events.append({"index": idx, "pre_joint": pre_joint, "transition": tr, "post": post})

    if len(events) != 2:
        return {"error": f"expected 2 positive-charge events, found {len(events)}"}

    r_event, a2_event = events[0], events[1]
    final_state = exact.state_from_json(word_witness["final_state_json"])
    roots_final = component_map(final_state)
    r_src_root = roots_final.get(("q", exact.ORBIT_PHASE[r_event["pre_joint"].p][0]))
    r_tgt_root = roots_final.get(("q", exact.ORBIT_PHASE[r_event["transition"].target][0]))
    a2_src_root = roots_final.get(("q", exact.ORBIT_PHASE[a2_event["pre_joint"].p][0]))
    a2_tgt_root = roots_final.get(("q", exact.ORBIT_PHASE[a2_event["transition"].target][0]))

    return {
        "target_hash": word_witness["target_hash"],
        "group": "U4" if word_witness["target_hash"] in U4_HASHES else "C20",
        "macro_distance_R_to_A2": a2_event["index"] - r_event["index"],
        "R_event": event_orbit(r_event["pre_joint"], r_event["transition"]),
        "A2_event": event_orbit(a2_event["pre_joint"], a2_event["transition"]),
        "before_R": snapshot(r_event["pre_joint"]),
        "after_R": snapshot(r_event["post"]),
        "before_A2": snapshot(a2_event["pre_joint"]),
        "after_A2_final": snapshot(final_state),
        "component_relation_at_final": {
            "R_source_target_same_component": r_src_root is not None and r_src_root == r_tgt_root,
            "A2_source_target_same_component": a2_src_root is not None and a2_src_root == a2_tgt_root,
            "R_target_A2_target_same_component": r_tgt_root is not None and r_tgt_root == a2_tgt_root,
            "R_target_A2_source_same_component": r_tgt_root is not None and r_tgt_root == a2_src_root,
        },
    }


def diff_c20_u4(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract fields that are constant within C20 XOR constant within U4
    (always-true-in-one, never-true-in-other), by walking every leaf scalar
    field in the flattened record."""
    def flatten(d, prefix=""):
        out = {}
        for k, v in d.items():
            key = f"{prefix}{k}"
            if isinstance(v, dict):
                out.update(flatten(v, key + "."))
            elif isinstance(v, list):
                out[key] = json.dumps(v, sort_keys=True)
            else:
                out[key] = v
        return out

    flat = [(r["group"], flatten({k: v for k, v in r.items() if k not in ("target_hash", "group")})) for r in records]
    all_keys = set()
    for _, f in flat:
        all_keys.update(f.keys())

    findings = []
    for key in sorted(all_keys):
        c20_vals = set(f.get(key, "<missing>") for g, f in flat if g == "C20")
        u4_vals = set(f.get(key, "<missing>") for g, f in flat if g == "U4")
        if len(c20_vals) == 1 and len(u4_vals) == 1 and c20_vals != u4_vals:
            findings.append({"field": key, "C20_value": list(c20_vals)[0], "U4_value": list(u4_vals)[0], "kind": "both_constant_and_different"})
        elif len(c20_vals) == 1 and c20_vals.isdisjoint(u4_vals):
            findings.append({"field": key, "C20_value": list(c20_vals)[0], "U4_values": sorted(u4_vals), "kind": "C20_constant_U4_never_matches"})
        elif len(u4_vals) == 1 and u4_vals.isdisjoint(c20_vals):
            findings.append({"field": key, "U4_value": list(u4_vals)[0], "C20_values": sorted(c20_vals), "kind": "U4_constant_C20_never_matches"})
    return {"discriminating_fields": findings}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output-comparison", default=str(ROOT / "outputs" / "ra2_24_comparison.json"))
    parser.add_argument("--output-survivors", default=str(ROOT / "outputs" / "ra2_four_survivors.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    assert ra2["recovered"] == 24

    records = [analyze_one(w) for w in ra2["witnesses"]]
    for r in records:
        if "error" in r:
            raise AssertionError(r)

    diff = diff_c20_u4(records)

    report = {
        "schema": "ra2-24-comparison-v1",
        "note_on_split_hexagon": (
            "This codebase has no distinct 'split hexagon' field (confirmed "
            "by grep across legacy_research/work/*.py); consistent with this "
            "project's earlier documented usage, 'split hexagon' is treated "
            "as an alias for f1_normal_form(state).fragment_hex."
        ),
        "records": records,
        "c20_vs_u4_diff": diff,
    }
    Path(args.output_comparison).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")

    survivors = {
        "schema": "ra2-four-survivors-v1",
        "records": [r for r in records if r["group"] == "U4"],
    }
    Path(args.output_survivors).write_text(json.dumps(survivors, indent=2, sort_keys=True, default=str), encoding="utf-8")

    print(json.dumps({
        "wrote": [args.output_comparison, args.output_survivors],
        "discriminating_fields_found": len(diff["discriminating_fields"]),
        "discriminating_fields": [f["field"] + ":" + f["kind"] for f in diff["discriminating_fields"]],
    }, indent=2))


if __name__ == "__main__":
    main()
