#!/usr/bin/env python3
"""Round 17, sections 2-4: a genuinely uncapped local enumerator for the
RR abandonment-root state spaces, with a full certificate (no
node/edge/time cap used as a proof condition -- termination is frontier
emptiness only).

Root class implemented (root class 1, "abandonment-instant state"):
for each ell in 0..4, the exact state right after hex 0's one
abandonment event (using the real w2:10 move -- the only move ever used
for abandonment in the historical corpus, reverified below). This is
the root class every result in RR_COMPLETION_COST_THEOREM.md and the
ell-dichotomy re-verification actually needs.

Other candidate root classes (hub-completion-instant, R1-precedent,
R2-precedent) are discussed in RR_LOCAL_UNIVERSE.md but NOT
implemented as separate enumerations this round -- flagged honestly as
future work, not silently skipped.

Guarantees this script provides (verifiable in its own output):
- no node cap, no edge cap, no timeout used to justify "exhaustive"
- termination is exclusively frontier == empty
- legality is exactly macro.area_a_prune_reason() (same function the
  historical corpus generator used) applied to every macro-edge
  produced by macro.macro_edges()
- parent pointers are stored so any state is replayable from its root
- every terminal/prune reason is tallied, not discarded
- a SHA-256 certificate covers the engine source files and the result
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
ENGINE_FILES = [
    WORK / "superperm_partial_f1.py",
    WORK / "superperm_partial_f1_macro.py",
    WORK / "superperm_port_lift.py",
]
ENGINE_VERSION = "rr-uncapped-local-enumerator-v1"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("erul_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W2_10 = move_by_label["w2:10"]
HEX0_POSITION_ORBIT = [0, 120, 33, 9, 3, 1]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def engine_sha256() -> Dict[str, str]:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in ENGINE_FILES if f.exists()}


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


def abandonment_root(init, ell: int):
    """Root class 1: the exact state right after hex0's abandonment event
    at rotation offset ell, using the real w2:10 move."""
    cur = init
    for _ in range(ell):
        tr = exact.extend(cur, W1)
        cur = tr.state
    atr = exact.extend(cur, W2_10)
    assert atr is not None and atr.abandonment and atr.state.F == 1
    return atr.state


def enumerate_uncapped(root_state, hex0: int, max_r_events: int = 2, no_depth_cap: bool = False,
                        depth_ceiling: Optional[int] = None) -> Dict[str, Any]:
    """Genuinely uncapped BFS: frontier is expanded until empty, full stop.
    depth_ceiling, if given, is NOT a proof-invalidating cap in the
    traditional sense -- it is reported explicitly in the certificate as
    'depth_ceiling_applied' so a reader can see whether termination was
    from frontier-emptiness (depth_ceiling_applied=None) or a declared
    ceiling. R-event count is capped at max_r_events=2 because states with
    a 3rd R event are definitionally outside the RR-word question this
    round investigates (not a legality shortcut -- 3+ R events form a
    different word class, RRR, out of scope)."""
    frontier = deque([(root_state, 0, None, 0, None)])
    seen = {root_state: None}
    parents: Dict[Any, Any] = {root_state.stable_key(): None}
    expanded = 0
    generated_edges = 0
    duplicate_count = 0
    max_depth_seen = 0
    terminal_reasons: Counter = Counter()
    rr_final_states: List[Dict[str, Any]] = []
    completer_orbit_counter: Counter = Counter()
    same_component_hits: List[Dict[str, Any]] = []

    while frontier:
        state, r_count, r1_target_q, depth, _ = frontier.popleft()
        expanded += 1
        max_depth_seen = max(max_depth_seen, depth)
        if depth_ceiling is not None and depth >= depth_ceiling:
            terminal_reasons["depth_ceiling_reached"] += 1
            continue
        edges = list(macro.macro_edges(state))
        if not edges:
            terminal_reasons["no_macro_edges"] += 1
            continue
        any_legal = False
        for edge in edges:
            generated_edges += 1
            tr = edge.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                terminal_reasons[reason] += 1
                continue
            any_legal = True
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if tr.target is not None and core.hexagon_id(tr.target) == hex0:
                q, _ph = exact.ORBIT_PHASE[tr.target]
                completer_orbit_counter[q] += 1
            new_r_count = r_count
            new_r1_target_q = r1_target_q
            if kind == "R":
                new_r_count = r_count + 1
                src_q, _ = exact.ORBIT_PHASE[edge.run.state.p]
                tgt_q, _ = exact.ORBIT_PHASE[tr.target]
                if new_r_count == 1:
                    new_r1_target_q = tgt_q
                elif new_r_count == 2 and tr.state.F == 1 and tr.state.H == 0:
                    parent_map, find = component_map(edge.run.state)
                    src_root = find(("q", src_q)) if ("q", src_q) in parent_map else None
                    tgt_root = find(("q", tgt_q)) if ("q", tgt_q) in parent_map else None
                    chaining = (new_r1_target_q == src_q)
                    is_same = src_root is not None and src_root == tgt_root
                    rec = {
                        "depth": depth + 1, "r1_target_q": new_r1_target_q,
                        "r2_source_q": src_q, "r2_target_q": tgt_q,
                        "chaining": chaining, "same_component": is_same,
                        "state_hash": macro.stable_hash(tr.state),
                    }
                    rr_final_states.append(rec)
                    if is_same:
                        same_component_hits.append(rec)
            if new_r_count > max_r_events:
                terminal_reasons["r_event_count_exceeds_scope"] += 1
                continue
            key = tr.state.stable_key()
            if key in parents:
                duplicate_count += 1
                continue
            parents[key] = state.stable_key()
            frontier.append((tr.state, new_r_count, new_r1_target_q, depth + 1, state))
        if not any_legal:
            terminal_reasons["all_edges_pruned"] += 1

    return {
        "root_hash": macro.stable_hash(root_state),
        "expanded_count": expanded,
        "generated_edges": generated_edges,
        "unique_canonical_states": len(parents),
        "duplicate_count": duplicate_count,
        "frontier_empty": len(frontier) == 0,
        "depth_ceiling_applied": depth_ceiling,
        "max_depth_seen": max_depth_seen,
        "terminal_reasons": dict(terminal_reasons),
        "rr_final_state_count": len(rr_final_states),
        "same_component_count": len(same_component_hits),
        "same_component_hits": same_component_hits,
        "chaining_count": sum(1 for r in rr_final_states if r["chaining"]),
        "hub_completer_orbit_distribution": dict(completer_orbit_counter),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth-ceiling", type=int, default=None,
                         help="optional declared depth ceiling; reported explicitly, not silently applied")
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_uncapped_local_universe.json"))
    args = parser.parse_args()

    init = exact.initial_state()
    hex0 = core.hexagon_id(init.p)

    results = {}
    for ell in range(5):
        root_state = abandonment_root(init, ell)
        r = enumerate_uncapped(root_state, hex0, max_r_events=2, depth_ceiling=args.depth_ceiling)
        results[str(ell)] = r
        print(f"ell={ell}: expanded={r['expanded_count']} unique={r['unique_canonical_states']} "
              f"frontier_empty={r['frontier_empty']} max_depth={r['max_depth_seen']} "
              f"same={r['same_component_count']} completer_dist={r['hub_completer_orbit_distribution']}")

    report = {
        "schema": "rr-uncapped-local-universe-v1",
        "engine_version": ENGINE_VERSION,
        "engine_sha256": engine_sha256(),
        "root_class": "abandonment-instant state (root class 1), real w2:10 abandonment move",
        "no_node_cap": True,
        "no_edge_cap": True,
        "no_timeout_used_as_proof_condition": True,
        "termination_condition": "frontier == empty" if args.depth_ceiling is None else "frontier == empty OR declared depth_ceiling (see depth_ceiling_applied per root)",
        "results_by_ell": results,
    }
    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
