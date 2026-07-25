#!/usr/bin/env python3
"""Round 20, sections 12, 13, 14: the ell=0 family growth, the ell=4
depth stability question, and the ell=0 decorated preparation automaton.

Uses raw-state dedup, which Round 19 proved gives numerically identical
results to canonical dedup in this universe (duplicate count 0, every
stabilizer size 1), and is fast enough to reach depth 8.

Section 12's depth-8 run is a COVERAGE run under the round's stated
conditions: root-local, no node/edge cap, terminates only on
frontier-empty. If it fails to exhaust it is reported as bounded
observation, not as evidence of anything.
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


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("arel0_macro", "superperm_partial_f1_macro.py")
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


def state_hash(state) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def component_roots(state):
    parent: Dict[Any, Any] = {}

    def find(n):
        parent.setdefault(n, n)
        if parent[n] != n:
            parent[n] = find(parent[n])
        return parent[n]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for ph in range(5):
            if mask & (1 << ph):
                union(("q", q), ("h", core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[ph])))
    return parent, find


def legal_trailing(state) -> List[str]:
    return sorted(f"rot^{e.run.ell};{e.joint.move.label}" for e in macro.macro_edges(state)
                  if macro.area_a_prune_reason(e.joint.state, macro.AREA_A) is None)


def abandonment_root(init, ell: int):
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    return exact.extend(cur, W2_10).state


def enumerate_same_component(root_state, hub: int, ell: int, depth_ceiling: int,
                              node_cap: Optional[int] = None) -> Dict[str, Any]:
    """Raw-dedup BFS collecting every same-component R2 boundary with its
    full preparation trace. Terminates on frontier-empty unless node_cap
    is supplied (in which case the result is bounded observation)."""
    frontier = deque([(root_state, 0, None, None, 0, 0, [])])
    seen = {root_state.stable_key()}
    expanded = 0
    cap_hit = False
    same: List[Dict[str, Any]] = []
    rr_final = 0
    chaining = 0

    while frontier:
        if node_cap is not None and expanded >= node_cap:
            cap_hit = True
            break
        state, rc, r1t, completer, fresh, depth, trace = frontier.popleft()
        expanded += 1
        if depth >= depth_ceiling:
            continue
        for edge in macro.macro_edges(state):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            pre = edge.run.state
            sq, sph = exact.ORBIT_PHASE[pre.p]
            tq, tph = exact.ORBIT_PHASE[tr.target]
            thex = core.hexagon_id(tr.target)
            n_fresh = fresh + (1 if tr.new_orbit else 0)
            n_comp = completer
            if thex == hub and completer is None:
                n_comp = {"macro_index": depth + 1, "orbit": tq, "phase": tph, "kind": kind,
                          "is_r1": (rc == 0 and kind == "R")}
            step = {"label": f"rot^{edge.run.ell};{tr.move.label}", "kind": kind,
                    "src": [sq, sph], "tgt": [tq, tph], "tgt_hex": thex,
                    "new_orbit": tr.new_orbit}
            nrc, nr1t = rc, r1t
            if kind == "R":
                nrc = rc + 1
                if nrc == 1:
                    nr1t = tq
                elif nrc == 2 and tr.state.F == 1 and tr.state.H == 0:
                    rr_final += 1
                    parent, find = component_roots(pre)
                    sr = find(("q", sq)) if ("q", sq) in parent else None
                    tg = find(("q", tq)) if ("q", tq) in parent else None
                    is_chain = (r1t == sq)
                    if is_chain:
                        chaining += 1
                    if sr is not None and sr == tg:
                        same.append({
                            "raw_state_hash": state_hash(tr.state),
                            "abandonment_ell": ell,
                            "depth_from_abandonment_root": depth + 1,
                            "depth_from_word_start": depth + 2,
                            "preparation_length": depth,
                            "r1_target_orbit": r1t,
                            "r2_source_orbit": sq, "r2_source_phase": sph,
                            "r2_target_orbit": tq, "r2_target_phase": tph,
                            "chaining": is_chain,
                            "hub_completer_orbit": (n_comp or {}).get("orbit"),
                            "hub_completer_phase": (n_comp or {}).get("phase"),
                            "hub_completer_kind": (n_comp or {}).get("kind"),
                            "hub_completer_is_r1": (n_comp or {}).get("is_r1"),
                            "hub_completer_macro_index": (n_comp or {}).get("macro_index"),
                            "fresh_orbit_openings": fresh,
                            "phi": 5 + 6 * (exact.TARGET_P - tr.state.P) - (720 - tr.state.visited_count),
                            "O": tr.state.O, "S": tr.state.S,
                            "kind_signature": [s["kind"] for s in trace] + [kind],
                            "trace": trace + [step],
                            "legal_trailing_edges": legal_trailing(tr.state),
                            "r1_r2_macro_distance": (depth + 1) - ((n_comp or {}).get("macro_index") or 0),
                        })
            if nrc > 2:
                continue
            k = tr.state.stable_key()
            if k in seen:
                continue
            seen.add(k)
            frontier.append((tr.state, nrc, nr1t, n_comp, n_fresh, depth + 1, trace + [step]))

    for s in same:
        s["legal_trailing_edge_count"] = len(s["legal_trailing_edges"])
    return {
        "abandonment_ell": ell, "depth_ceiling": depth_ceiling,
        "expanded": expanded, "frontier_empty": not cap_hit and len(frontier) == 0,
        "node_cap_hit": cap_hit,
        "rr_final_boundaries": rr_final, "chaining_boundaries": chaining,
        "same_component_boundaries": len(same),
        "distinct_same_component_states": len({s["raw_state_hash"] for s in same}),
        "same_component": sorted(same, key=lambda s: (s["depth_from_abandonment_root"], s["raw_state_hash"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ell0-depths", default="6,7")
    parser.add_argument("--ell4-depth8", action="store_true")
    parser.add_argument("--node-cap", type=int, default=None)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_ell0_depth7_families.json"))
    args = parser.parse_args()

    init = exact.initial_state()
    hub = core.hexagon_id(init.p)

    # ---- section 13: ell=0 growth ----
    ell0 = {}
    for d in [int(x) for x in args.ell0_depths.split(",")]:
        r = enumerate_same_component(abandonment_root(init, 0), hub, 0, d)
        ell0[str(d)] = r
        print(f"ell=0 depth<={d}: expanded={r['expanded']} frontier_empty={r['frontier_empty']} "
              f"same_states={r['distinct_same_component_states']}")
        for s in r["same_component"]:
            print(f"   {s['raw_state_hash'][:12]} prep={s['preparation_length']} "
                  f"R1t={s['r1_target_orbit']} R2({s['r2_source_orbit']},{s['r2_source_phase']})->"
                  f"({s['r2_target_orbit']},{s['r2_target_phase']}) "
                  f"completer=({s['hub_completer_orbit']},{s['hub_completer_phase']},{s['hub_completer_kind']},"
                  f"isR1={s['hub_completer_is_r1']}) fresh={s['fresh_orbit_openings']} phi={s['phi']} "
                  f"kinds={s['kind_signature']}")

    out: Dict[str, Any] = {
        "schema": "rr-ell0-family-growth-v1",
        "hub_id": hub,
        "ell0_by_depth": ell0,
    }

    # ---- section 12: ell=4 depth-8 coverage run ----
    if args.ell4_depth8:
        r8 = enumerate_same_component(abandonment_root(init, 4), hub, 4, 8, node_cap=args.node_cap)
        print(f"\nell=4 depth<=8: expanded={r8['expanded']} frontier_empty={r8['frontier_empty']} "
              f"cap_hit={r8['node_cap_hit']} same_states={r8['distinct_same_component_states']}")
        for s in r8["same_component"]:
            print(f"   {s['raw_state_hash'][:12]} prep={s['preparation_length']} fresh={s['fresh_orbit_openings']} "
                  f"O={s['O']} kinds={s['kind_signature']}")
        out["ell4_depth8"] = r8
        out["ell4_depth8_status"] = ("root-local exhaustive" if r8["frontier_empty"]
                                      else "bounded observation (frontier did NOT exhaust)")

    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", args.output)


if __name__ == "__main__":
    main()
