#!/usr/bin/env python3
"""Five-state focused comparison: U4's 4 states plus the one C20 outlier
(e2b44997e783) that shares U4's critical-restart signature. Sections 1,
5, 6 of this round's request: a unified exact ledger, the full ell-sweep
at the A2 boundary (is ell_A2=4 forced or free for U4?), and a depth<=6
continuation-tree comparison among exactly these 5 states.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
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


macro = _load("r5s_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1

U4_HASHES = [
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
]
OUTLIER_HASH = "e2b44997e7838537176bd6e0e72ea41df259f429863731b696dc76692beeb98c"
FIVE_HASHES = U4_HASHES + [OUTLIER_HASH]


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


def full_ledger_entry(witness: Dict[str, Any]) -> Dict[str, Any]:
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    steps = []
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        pre_joint = cur
        move = move_by_label[joint_part]
        roots_pre = component_map(pre_joint)
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        steps.append({"ell": ell, "kind": kind, "pre_joint": pre_joint, "transition": tr, "roots_pre": roots_pre})
        cur = exact.canonicalize(tr.state)

    r_idx = next(i for i, s in enumerate(steps) if s["kind"] == "R")
    a2_idx = next(i for i, s in enumerate(steps) if s["kind"] == "A2")
    critical_idx = a2_idx - 1  # the block immediately preceding A2

    r_step = steps[r_idx]
    a2_step = steps[a2_idx]
    crit_step = steps[critical_idx] if critical_idx > r_idx else None

    r_src_q, r_src_phase = exact.ORBIT_PHASE[r_step["pre_joint"].p]
    r_tgt_q, r_tgt_phase = exact.ORBIT_PHASE[r_step["transition"].target]
    a2_src_q, a2_src_phase = exact.ORBIT_PHASE[a2_step["pre_joint"].p]
    a2_tgt_q, a2_tgt_phase = exact.ORBIT_PHASE[a2_step["transition"].target]

    final_state = exact.state_from_json(witness["final_state_json"])
    form = exact.f1_normal_form(final_state)

    crit_info = None
    if crit_step is not None:
        c_src_q, c_src_phase = exact.ORBIT_PHASE[crit_step["pre_joint"].p]
        c_tgt_q, c_tgt_phase = exact.ORBIT_PHASE[crit_step["transition"].target]
        c_roots = crit_step["roots_pre"]
        crit_info = {
            "index": critical_idx, "kind": crit_step["kind"], "ell": crit_step["ell"],
            "source_orbit_q": c_src_q, "source_phase": c_src_phase,
            "target_orbit_q": c_tgt_q, "target_phase": c_tgt_phase,
            "component_relation": (
                "same" if c_roots.get(("q", c_src_q)) is not None and c_roots.get(("q", c_src_q)) == c_roots.get(("q", c_tgt_q)) else
                "different" if c_roots.get(("q", c_src_q)) is not None and c_roots.get(("q", c_tgt_q)) is not None else "unresolved"
            ),
        }

    edges = list(macro.macro_edges(final_state))
    legal_children = [e for e in edges if not e.joint.abandonment and macro.area_a_prune_reason(e.joint.state, macro.AREA_A) is None]

    return {
        "target_hash": witness["target_hash"],
        "group": "U4" if witness["target_hash"] in U4_HASHES else "C20_outlier",
        "r_idx": r_idx, "critical_idx": critical_idx, "a2_idx": a2_idx,
        "r_target_orbit_q": r_tgt_q, "r_target_phase": r_tgt_phase,
        "r_source_orbit_q": r_src_q, "r_source_phase": r_src_phase,
        "critical_restart": crit_info,
        "a2_ell": a2_step["ell"],
        "a2_source_orbit_q": a2_src_q, "a2_source_phase": a2_src_phase,
        "a2_target_orbit_q": a2_tgt_q, "a2_target_phase": a2_tgt_phase,
        "endpoint_before_A2": list(a2_step["pre_joint"].p),
        "endpoint_after_A2": list(a2_step["transition"].target),
        "fragment_hex": form.fragment_hex if form else None,
        "fragment_components": [list(c) for c in form.fragment_components] if form else None,
        "P": final_state.P, "S": final_state.S, "O": final_state.O, "D": final_state.D,
        "F": final_state.F, "H": final_state.H, "Ndef": final_state.Ndef,
        "phi": phi(final_state), "orbit_slack": orbit_slack(final_state), "d_frag": d_frag(final_state),
        "post_A2_legal_children_count": len(legal_children),
        "post_A2_legal_children_ells": sorted(e.run.ell for e in legal_children),
    }


def ell_sweep_at_a2_boundary(witness: Dict[str, Any]) -> Dict[str, Any]:
    """For each state, replay up to (not including) A2's own macro-edge,
    then enumerate EVERY legal continuation (any weight, any ell) from
    that exact boundary -- not just weight-2 abandoning ones -- to see
    whether ell_A2=4 was the ONLY legal abandoning choice, or one of
    several, and what else was available."""
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    for step in path[:-1]:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        cur = exact.canonicalize(tr.state)

    pre_a2 = cur
    sweep = []
    p = pre_a2
    for ell in range(6):
        options = []
        for mv in exact.ALL_MOVES:
            tr = exact.extend(p, mv)
            if tr is None:
                continue
            reason = None
            if not tr.abandonment:
                reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            kind = joint_kind(mv.weight, tr.abandonment, tr.new_orbit)
            legal_here = (reason is None) if not tr.abandonment else True  # abandonment legality vs F budget checked separately
            if tr.abandonment and exact.TARGET_F < (p.F + 1):
                legal_here = False
            options.append({"move": mv.label, "kind": kind, "weight": mv.weight, "new_orbit": tr.new_orbit, "legal": legal_here})
        a2_options = [o for o in options if o["kind"] == "A2" and o["legal"]]
        sweep.append({"ell": ell, "a2_options": a2_options, "total_legal_options": sum(1 for o in options if o["legal"])})
        nxt = exact.extend(p, W1)
        if nxt is None:
            break
        p = nxt.state
    return {"sweep": sweep}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output-ledger", default=str(ROOT / "outputs" / "ra2_five_state_ledger.json"))
    parser.add_argument("--output-tree", default=str(ROOT / "outputs" / "ra2_five_state_tree_comparison.json"))
    parser.add_argument("--tree-depth", type=int, default=6)
    parser.add_argument("--tree-edge-cap", type=int, default=30_000)
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = {w["target_hash"]: w for w in ledger["words"]["RA2"]["witnesses"]}

    entries = {}
    sweeps = {}
    for h in FIVE_HASHES:
        w = ra2[h]
        entries[h] = full_ledger_entry(w)
        sweeps[h] = ell_sweep_at_a2_boundary(w)
        print(h[:12], entries[h]["group"], "a2_ell:", entries[h]["a2_ell"], "critical:", entries[h]["critical_restart"])

    Path(args.output_ledger).write_text(json.dumps({
        "schema": "ra2-five-state-ledger-v1", "entries": entries, "ell_sweeps": sweeps,
    }, indent=2, sort_keys=True, default=str), encoding="utf-8")

    # depth<=6 continuation tree comparison among the 5 states
    tree_results = {}
    for h in FIVE_HASHES:
        state = exact.state_from_json(ra2[h]["final_state_json"])
        frontier = deque([(0, state)])
        edges = 0
        depth_stats = {d: {"legal_children": 0, "ells": [], "capacity_fail": 0, "collision": 0, "repairs": 0} for d in range(args.tree_depth)}
        form0 = exact.f1_normal_form(state)
        fh0 = form0.fragment_hex if form0 else None
        while frontier and edges < args.tree_edge_cap:
            d, s = frontier.popleft()
            if d >= args.tree_depth:
                continue
            for e in macro.macro_edges(s):
                edges += 1
                tr = e.joint
                if tr.abandonment:
                    continue
                reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
                depth_stats[d]["ells"].append(e.run.ell)
                if reason == "remaining_cover_capacity_impossible":
                    depth_stats[d]["capacity_fail"] += 1
                    continue
                if reason is not None:
                    continue
                depth_stats[d]["legal_children"] += 1
                if fh0 is not None and core.hexagon_id(tr.target) == fh0:
                    depth_stats[d]["repairs"] += 1
                frontier.append((d + 1, tr.state))
                if edges >= args.tree_edge_cap:
                    break
        tree_results[h] = {d: v for d, v in depth_stats.items()}
        print(h[:12], "tree scan done, edges used:", edges)

    Path(args.output_tree).write_text(json.dumps({
        "schema": "ra2-five-state-tree-comparison-v1", "config": {"depth": args.tree_depth, "edge_cap": args.tree_edge_cap},
        "results": tree_results,
    }, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": [args.output_ledger, args.output_tree]}, indent=2))


if __name__ == "__main__":
    main()
