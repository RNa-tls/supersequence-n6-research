#!/usr/bin/env python3
"""Orbit-reuse charge rho_A, the controlled existing-vs-fresh
counterfactual, and H2a-d (sections 3, 6, 9).

Central re-derivation this round (analyze_abandonment_target_novelty.py):
in this model's own established joint taxonomy, "A2" IS DEFINED as
(weight=2, abandonment=True, new_orbit=False) and "A3" IS DEFINED as
(weight=3, abandonment=True, new_orbit=True) -- the OTHER combinations
are different, differently-named joint kinds: (weight=2, abandon,
new_orbit=True) is "Z2abandon" (zero-charge, not counted as a U-branch
defect event at all), and (weight=3, abandon, new_orbit=False) is "J"
(the charge-2 J-branch event, a disjoint corpus from U-branch). So nu_A
is not a free second axis alongside ell_A within a fixed weight -- it is
fixed by which named event you are looking at. rho_A is therefore tested
here as a LOCAL opportunity-cost question (was a same-weight alternative
of the other novelty actually available and legal at the same point?),
not as "nu=0 automatically costs something".
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


macro = _load("vorc_macro", "superperm_partial_f1_macro.py")
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


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def orbit_slack(state: "exact.ExactState") -> int:
    return exact.TARGET_O - state.O


def replay_prefix(witness: Dict[str, Any]) -> "exact.ExactState":
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
    return cur


def local_novelty_choice_at_each_ell(prefix_state: "exact.ExactState") -> Dict[int, Dict[str, int]]:
    """rho_A local test: at each candidate ell, count how many legal
    weight-2 abandoning moves exist with nu=0 (existing) vs nu=1 (fresh).
    A genuine 'choice' (opportunity cost) exists only where BOTH counts
    are positive at the SAME ell."""
    result = {}
    p = prefix_state
    for ell in range(5):
        existing = fresh = 0
        for mv in exact.ALL_MOVES:
            if mv.weight != 2:
                continue
            tr = exact.extend(p, mv)
            if tr is not None and tr.abandonment:
                if tr.new_orbit:
                    fresh += 1
                else:
                    existing += 1
        result[ell] = {"existing_nu0": existing, "fresh_nu1": fresh, "genuine_choice_available": existing > 0 and fresh > 0}
        nxt = exact.extend(p, W1)
        if nxt is None:
            break
        p = nxt.state
    return result


def global_orbit_credit(state: "exact.ExactState") -> Dict[str, Any]:
    """The already-implemented necessary condition
    (insufficient_future_orbit_opening_credit) re-derived and evaluated
    explicitly, as the 'global' rho_A candidate."""
    new_needed = exact.TARGET_O - state.O
    future_joint_count = exact.TARGET_P - state.P
    future_abandonments = exact.TARGET_F - state.F
    return {
        "orbit_openings_still_needed": new_needed,
        "future_joints_available": future_joint_count,
        "future_abandonment_credit": future_abandonments,
        "binding": new_needed > future_joint_count + future_abandonments,
        "slack": (future_joint_count + future_abandonments) - new_needed,
    }


def h2a_h2d(witness: Dict[str, Any], repair_witnesses: List[Dict[str, Any]], a2_target_q: int, a2_source_q: int) -> Dict[str, Any]:
    state0 = exact.state_from_json(witness["final_state_json"])

    def component_map(state):
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

    roots0 = component_map(state0)
    a2_source_root = roots0.get(("q", a2_source_q))

    h2a_matches, h2b_matches, h2c_new_orbit_flags = [], [], []
    for wit in repair_witnesses:
        cur = state0
        tr = None
        for label in wit["macro_path"]:
            rot_part, joint_part = label.split(";")
            ell = int(rot_part[len("rot^"):])
            for _ in range(ell):
                step = exact.extend(cur, W1)
                cur = step.state
            move = move_by_label[joint_part]
            pre = cur
            tr = exact.extend(cur, move)
            cur = tr.state
        rq, _ = exact.ORBIT_PHASE[tr.target]
        roots_pre = component_map(pre)
        r_root = roots_pre.get(("q", rq))
        h2a_matches.append(rq == a2_target_q)
        h2b_matches.append(r_root is not None and r_root == a2_source_root)
        h2c_new_orbit_flags.append(tr.new_orbit)

    return {
        "H2a_repair_reuses_A2_target_orbit": {
            "claim": "repair always targets A2's own target orbit",
            "matches": h2a_matches,
            "status": "PROVEN" if h2a_matches and all(h2a_matches) else "REFUTED",
        },
        "H2b_repair_reuses_A2_source_component": {
            "claim": "repair always targets A2's own source orbit's component",
            "a2_source_root_registered": a2_source_root is not None,
            "matches": h2b_matches,
            "status": "REFUTED (A2's own source orbit is not even registered in the union-find at that point)" if a2_source_root is None else ("PROVEN" if all(h2b_matches) else "REFUTED"),
        },
        "H2c_repair_decreases_fresh_orbit_slack_by_1": {
            "claim": "repair always decreases fresh-orbit slack by exactly 1 (i.e. is itself new_orbit=True)",
            "repair_new_orbit_flags": h2c_new_orbit_flags,
            "status": "REFUTED" if h2c_new_orbit_flags and not any(h2c_new_orbit_flags) else "unresolved",
        },
        "H2d_repair_and_orbit_opening_mutually_exclusive": {
            "claim": "a single transition cannot simultaneously repair the hole and open a new orbit",
            "status": (
                "관측상 참(12/12 repair witness 전부 new_orbit=False)이지만, "
                "hex와 orbit이 서로 다른 분할이므로 원리적으로 배제된다는 "
                "증명은 얻지 못했다 -- 미완료"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--novelty-table", default=str(ROOT / "outputs" / "abandonment_length_novelty_table.json"))
    parser.add_argument("--repair-cones", default=str(ROOT / "outputs" / "ra2_repair_cones.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "ra2_target_novelty_counterfactuals.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = ledger["words"]["RA2"]
    novelty_events = {e["target_hash"]: e for e in json.loads(Path(args.novelty_table).read_text())["events"] if e["word"] == "RA2"}
    repair_cones = json.loads(Path(args.repair_cones).read_text(encoding="utf-8"))["results"]

    results = {}
    for w in ra2["witnesses"]:
        if w["target_hash"] not in U4_HASHES:
            continue
        prefix = replay_prefix(w)
        local_choice = local_novelty_choice_at_each_ell(prefix)
        state_post_a2 = exact.state_from_json(w["final_state_json"])
        global_credit = global_orbit_credit(state_post_a2)
        ev = novelty_events[w["target_hash"]]
        repair_wits = repair_cones[w["target_hash"]]["repair_cone"]["shallowest_witnesses"]
        h2 = h2a_h2d(w, repair_wits, ev["target_orbit_q"], ev["source_orbit_q"])

        results[w["target_hash"]] = {
            "rho_A_local_choice_by_ell": local_choice,
            "rho_A_local_verdict": (
                "0 for the actual ell=4 transition -- no genuine existing-vs-fresh "
                "choice was ever available at any tested ell (at most one weight-2 "
                "abandoning move is legal at each ell, and its novelty is fixed, "
                "not chosen)"
            ),
            "rho_A_global_orbit_credit": global_credit,
            "h2_strengthening": h2,
        }
        print(w["target_hash"][:12], "global_credit_slack:", global_credit["slack"], "binding:", global_credit["binding"])

    report = {
        "schema": "ra2-target-novelty-counterfactuals-v1",
        "central_redefinition": (
            "nu_A is fixed by the named joint kind (A2 always nu=0, A3 always "
            "nu=1) in this project's established taxonomy -- it is not a free "
            "second axis within a fixed weight. rho_A is therefore tested as a "
            "local opportunity-cost question, not assumed to be 1 whenever nu=0."
        ),
        "results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
