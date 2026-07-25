#!/usr/bin/env python3
"""Round 18, section 5: tests whether the root-local state representation
used by the Round 17 enumerator is Markov-complete for the
same-component question -- i.e. whether two exact histories that compress
to the same local state can ever yield different same-component
outcomes.

Method: re-run the ell=0..4 root-local enumerations twice, with two
different duplicate-detection keys:
  (a) 'state_only'          -- state.stable_key() alone (Round 17's key)
  (b) 'state_plus_history'  -- (state.stable_key(), r_count, r1_target_orbit)

If (b) finds strictly more RR-final / same-component results than (a),
then r_count and r1_target_orbit are history fields the local state
does NOT carry, and Round 17's universe was undercounting. If the two
agree exactly on every ell, the representation is Markov-complete for
this question over this universe (a finite, checkable claim -- not a
proof for arbitrary universes).

This directly tests the specific bug hypothesis raised when the 9-vs-5
ell=4 discrepancy was found. Result: the hypothesis is REFUTED (both
keys agree exactly); the discrepancy has a different, fully-established
cause -- see src/audit_rr_ell4_discrepancy.py.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict

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


macro = _load("vlsc_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W2_10 = move_by_label["w2:10"]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


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
    return parent, find


def run(ell: int, dedup_mode: str, depth_ceiling: int = 6) -> Dict[str, Any]:
    init = exact.initial_state()
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    root = exact.extend(cur, W2_10).state

    def make_key(state, rc, r1t):
        return state.stable_key() if dedup_mode == "state_only" else (state.stable_key(), rc, r1t)

    frontier = deque([(root, 0, None, 0)])
    seen = {make_key(root, 0, None)}
    same_hits = []
    rr_final = 0
    expanded = 0
    collisions_with_differing_history = 0
    history_by_state: Dict[Any, set] = {}

    while frontier:
        st, rc, r1t, d = frontier.popleft()
        expanded += 1
        if d >= depth_ceiling:
            continue
        for edge in macro.macro_edges(st):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            nrc, nr1t = rc, r1t
            if kind == "R":
                nrc = rc + 1
                src_q, _ = exact.ORBIT_PHASE[edge.run.state.p]
                tgt_q, _ = exact.ORBIT_PHASE[tr.target]
                if nrc == 1:
                    nr1t = tgt_q
                elif nrc == 2 and tr.state.F == 1 and tr.state.H == 0:
                    rr_final += 1
                    pm, find = component_map(edge.run.state)
                    sr = find(("q", src_q)) if ("q", src_q) in pm else None
                    tg = find(("q", tgt_q)) if ("q", tgt_q) in pm else None
                    if sr is not None and sr == tg:
                        same_hits.append({
                            "depth": d + 1, "r1_target_q": nr1t, "r2_source_q": src_q,
                            "chaining": nr1t == src_q, "state_hash": macro.stable_hash(tr.state),
                        })
            if nrc > 2:
                continue
            # diagnostic: does this exact state ever appear with >1 distinct history?
            sk = tr.state.stable_key()
            history_by_state.setdefault(sk, set()).add((nrc, nr1t))
            if len(history_by_state[sk]) > 1:
                collisions_with_differing_history += 1
            key = make_key(tr.state, nrc, nr1t)
            if key in seen:
                continue
            seen.add(key)
            frontier.append((tr.state, nrc, nr1t, d + 1))

    multi_history_states = sum(1 for v in history_by_state.values() if len(v) > 1)
    return {
        "expanded": expanded,
        "unique_keys": len(seen),
        "rr_final": rr_final,
        "same_component_count": len(same_hits),
        "distinct_same_component_states": len(set(h["state_hash"] for h in same_hits)),
        "states_reached_with_more_than_one_history": multi_history_states,
        "same_hits": same_hits,
    }


def main() -> None:
    results = {}
    all_agree = True
    for ell in range(5):
        a = run(ell, "state_only")
        b = run(ell, "state_plus_history")
        agree = (a["rr_final"] == b["rr_final"]
                 and a["same_component_count"] == b["same_component_count"]
                 and a["distinct_same_component_states"] == b["distinct_same_component_states"])
        all_agree = all_agree and agree
        results[str(ell)] = {"state_only": a, "state_plus_history": b, "agree": agree}
        print(f"ell={ell}: state_only(rr_final={a['rr_final']}, same={a['same_component_count']}) "
              f"vs state_plus_history(rr_final={b['rr_final']}, same={b['same_component_count']}) "
              f"agree={agree} | states_with_multiple_histories={b['states_reached_with_more_than_one_history']}")

    print(f"\nMarkov-completeness for the same-component question over this universe: "
          f"{'CONFIRMED (both keys agree on every ell)' if all_agree else 'REFUTED (history fields matter)'}")

    report = {
        "schema": "rr-local-state-completeness-v1",
        "question": "Can two exact histories compressing to the same local state yield different same-component outcomes?",
        "method": "re-run each root-local enumeration with dedup key = state.stable_key() alone vs (state.stable_key(), r_count, r1_target_orbit)",
        "per_ell": results,
        "all_agree": all_agree,
        "verdict": (
            "Markov-complete for the same-component question over this root-local universe "
            "(유한 완전 검증 over the depth-ceiling-6 universe): both dedup keys produce "
            "identical RR-final and same-component counts on all 5 ell branches. The "
            "specific bug hypothesis raised when the 9-vs-5 ell=4 gap was found -- that "
            "Round 17's dedup key silently dropped r_count/r1_target history and thereby "
            "undercounted -- is REFUTED. Scope note: this is a finite check over this "
            "universe, NOT a proof that the representation is Markov-complete in general."
        ) if all_agree else "NOT Markov-complete -- history fields change outcomes",
        "proof_status": "root-local exhaustive (depth ceiling 6, frontier empty, both dedup modes)",
    }
    out = ROOT / "outputs" / "rr_local_state_completeness.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
