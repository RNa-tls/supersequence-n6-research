#!/usr/bin/env python3
"""Round 20, sections 1, 3: the decorated boundary state.

Round 19 proved deductively that a post-R2 ExactState alone cannot decide
chaining (it records which (orbit,phase) pairs are visited but not which
edge was R1). This script defines the DECORATION that must be carried
alongside, enumerates every R2 boundary in the root-local universe with
its full decoration, and canonicalizes the (state, decoration) pair
under left-S6 with the decoration transported through the same alpha.

INVARIANT FIELD DEFINITIONS (section 1 requires these be invariant, not
implementation indices):

  abandonment_ell        rotation offset, within the distinguished hub
                         hexagon, at which the word's unique abandonment
                         joint fires. Invariant: it is the number of
                         pure-rotation steps from the hub's anchor
                         position before the joint.
  hub_id                 the distinguished hexagon = hexagon_id(p_0).
                         Fixed per root; carried for completeness.
  r1_source_orbit/phase  the E-orbit and phase of R1's source
                         permutation. Invariant under nothing -- these
                         are raw ids, which is exactly why section 3's
                         transport is required.
  r1_target_orbit/phase  same for R1's target.
  r1_macro_index         number of macro-edges from the abandonment root
                         to R1 inclusive. Invariant (a count, not an
                         array index).
  r2_source_orbit/phase, r2_target_orbit/phase, r2_macro_index: same.
  hub_completer_*        the event providing the hub's SECOND touch:
                         its macro index, target orbit/phase, joint kind,
                         and whether it coincides with R1.
  r1_target_hub_distance BFS distance from node ("q", R1_target) to
                         ("h", hub) in the orbit/hexagon incidence graph
                         at the PRE-R2 state. Invariant (graph distance).
                         This is the "hub ancestry" coordinate.
  r2_source_hub_distance, r2_target_hub_distance: same for R2's endpoints.
  r2_meet_is_hub         whether the hub node lies on every shortest
                         ("q",R2_s)->("q",R2_t) path, i.e. the LCA-style
                         coordinate of section 6. Invariant.
  r1_boundary_orientation sign of (r2_source_phase - hub_completer_phase)
                         reduced to {-1,0,+1}: the "path orientation"
                         coordinate. Invariant given the phase convention.
  fresh_orbit_openings   number of Z3 (new-orbit) joints strictly before
                         R2. Invariant (a count).
  preparation_family     derived label: "no-fresh-opening" if
                         fresh_orbit_openings == 0 else "fresh-opening".
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
ENGINE_FILES = [WORK / "superperm_partial_f1.py", WORK / "superperm_partial_f1_macro.py",
                WORK / "superperm_port_lift.py"]


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("erdl_macro", "superperm_partial_f1_macro.py")
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


def engine_sha256() -> Dict[str, str]:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in ENGINE_FILES if f.exists()}


def state_hash(state) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def incidence_adjacency(state) -> Dict[Any, set]:
    """The orbit/hexagon incidence graph of a state (undirected)."""
    adj: Dict[Any, set] = {}
    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                h = core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[phase])
                adj.setdefault(("q", q), set()).add(("h", h))
                adj.setdefault(("h", h), set()).add(("q", q))
    return adj


def bfs_distances(adj: Dict[Any, set], source) -> Dict[Any, int]:
    if source not in adj:
        return {}
    dist = {source: 0}
    dq = deque([source])
    while dq:
        n = dq.popleft()
        for m in adj.get(n, ()):
            if m not in dist:
                dist[m] = dist[n] + 1
                dq.append(m)
    return dist


def component_roots(state):
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
                union(("q", q), ("h", core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[phase])))
    return parent, find


def legal_trailing(state) -> List[Dict[str, Any]]:
    out = []
    for edge in macro.macro_edges(state):
        if macro.area_a_prune_reason(edge.joint.state, macro.AREA_A) is None:
            tr = edge.joint
            tq, tph = exact.ORBIT_PHASE[tr.target]
            out.append({"label": f"rot^{edge.run.ell};{tr.move.label}", "ell": edge.run.ell,
                        "joint": tr.move.label,
                        "kind": joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit),
                        "new_orbit": tr.new_orbit,
                        "target_hexagon": core.hexagon_id(tr.target),
                        "target_orbit": tq, "target_phase": tph})
    return sorted(out, key=lambda d: d["label"])


# ---------------- decorated canonicalization (section 3) ----------------

ORBIT_FIELDS = ("r1_source_orbit", "r1_target_orbit", "r2_source_orbit", "r2_target_orbit",
                "hub_completer_orbit")
HEX_FIELDS = ("hub_id", "r1_target_hexagon", "r2_target_hexagon", "hub_completer_hexagon")


def canonical_alphas(state) -> Tuple[Any, List[int]]:
    best_key = None
    best: List[int] = []
    for a in range(len(core.ALL_WORDS)):
        k = exact.relabel_sparse_key(state, a)
        if best_key is None or k < best_key:
            best_key, best = k, [a]
        elif k == best_key:
            best.append(a)
    return best_key, best


def transport_decoration(dec: Dict[str, Any], alpha: int) -> Tuple:
    """Transport every orbit id and hexagon id in the decoration through
    left-S6 element alpha. Phases, counts, distances, orientations and
    booleans are ALL invariant under left relabeling (left value
    relabeling commutes with right position actions), so they pass
    through unchanged -- this is asserted here and checked empirically by
    the tie-consistency test in verify_rr_decorated_markov.py."""
    out = []
    for f in ORBIT_FIELDS:
        v = dec.get(f)
        out.append(None if v is None else exact.LEFT_ORBIT_ACTION[alpha][v][0])
    for f in HEX_FIELDS:
        v = dec.get(f)
        out.append(None if v is None else exact.LEFT_HEX_ACTION[alpha][v][0])
    for f in INVARIANT_FIELDS:
        out.append(dec.get(f))
    return tuple(out)


INVARIANT_FIELDS = (
    "abandonment_ell", "r1_source_phase", "r1_target_phase", "r1_macro_index",
    "r2_source_phase", "r2_target_phase", "r2_macro_index",
    "hub_completer_macro_index", "hub_completer_phase", "hub_completer_kind",
    "hub_completer_is_r1", "r1_target_hub_distance", "r2_source_hub_distance",
    "r2_target_hub_distance", "r2_meet_is_hub", "r1_boundary_orientation",
    "fresh_orbit_openings", "preparation_family",
)


def canonical_decorated_key(state, dec: Dict[str, Any]):
    best_key, alphas = canonical_alphas(state)
    variants = [transport_decoration(dec, a) for a in alphas]
    chosen = min(range(len(variants)), key=lambda i: variants[i])
    return (best_key, variants[chosen]), alphas[chosen], len(alphas), variants


def abandonment_root(init, ell: int):
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    return exact.extend(cur, W2_10).state


def enumerate_decorated(root_state, hub: int, ell: int, depth_ceiling: int) -> Dict[str, Any]:
    """BFS recording, for EVERY R2 boundary, the full decoration."""
    # search node: (state, r_count, r1_info, hub_touched, completer_info, fresh_count, depth, path)
    frontier = deque([(root_state, 0, None, False, None, 0, 0, [])])
    seen = {root_state.stable_key()}
    boundaries: List[Dict[str, Any]] = []

    while frontier:
        state, rc, r1info, hub_touched, completer, fresh, depth, path = frontier.popleft()
        if depth >= depth_ceiling:
            continue
        for edge in macro.macro_edges(state):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            label = f"rot^{edge.run.ell};{tr.move.label}"
            pre = edge.run.state
            sq, sph = exact.ORBIT_PHASE[pre.p]
            tq, tph = exact.ORBIT_PHASE[tr.target]
            thex = core.hexagon_id(tr.target)
            n_depth = depth + 1
            n_fresh = fresh + (1 if tr.new_orbit else 0)
            n_hub_touched, n_completer = hub_touched, completer
            if thex == hub and not hub_touched:
                n_hub_touched = True
                n_completer = {"macro_index": n_depth, "orbit": tq, "phase": tph,
                               "hexagon": thex, "kind": kind, "is_r1": (rc == 0 and kind == "R")}
            nrc, nr1 = rc, r1info
            if kind == "R":
                nrc = rc + 1
                if nrc == 1:
                    nr1 = {"source_orbit": sq, "source_phase": sph, "target_orbit": tq,
                           "target_phase": tph, "target_hexagon": thex, "macro_index": n_depth}
                elif nrc == 2 and tr.state.F == 1 and tr.state.H == 0:
                    adj = incidence_adjacency(pre)
                    parent, find = component_roots(pre)
                    hub_node = ("h", hub)
                    d_from_hub = bfs_distances(adj, hub_node)
                    sr = find(("q", sq)) if ("q", sq) in parent else None
                    tg = find(("q", tq)) if ("q", tq) in parent else None
                    hub_root = find(hub_node) if hub_node in parent else None
                    same_component = sr is not None and sr == tg
                    # LCA-style: does every shortest path between the two
                    # endpoints pass through the hub node?
                    d_src = bfs_distances(adj, ("q", sq))
                    meet_is_hub = (
                        ("q", tq) in d_src and hub_node in d_src and ("q", tq) in d_from_hub
                        and d_src[("q", tq)] == d_src[hub_node] + d_from_hub[("q", tq)]
                    )
                    comp_phase = (n_completer or {}).get("phase")
                    orient = 0 if comp_phase is None else (1 if sph > comp_phase else (-1 if sph < comp_phase else 0))
                    dec = {
                        "abandonment_ell": ell, "hub_id": hub,
                        "r1_source_orbit": (nr1 or {}).get("source_orbit"),
                        "r1_source_phase": (nr1 or {}).get("source_phase"),
                        "r1_target_orbit": (nr1 or {}).get("target_orbit"),
                        "r1_target_phase": (nr1 or {}).get("target_phase"),
                        "r1_target_hexagon": (nr1 or {}).get("target_hexagon"),
                        "r1_macro_index": (nr1 or {}).get("macro_index"),
                        "r2_source_orbit": sq, "r2_source_phase": sph,
                        "r2_target_orbit": tq, "r2_target_phase": tph,
                        "r2_target_hexagon": thex, "r2_macro_index": n_depth,
                        "hub_completer_macro_index": (n_completer or {}).get("macro_index"),
                        "hub_completer_orbit": (n_completer or {}).get("orbit"),
                        "hub_completer_phase": (n_completer or {}).get("phase"),
                        "hub_completer_hexagon": (n_completer or {}).get("hexagon"),
                        "hub_completer_kind": (n_completer or {}).get("kind"),
                        "hub_completer_is_r1": (n_completer or {}).get("is_r1"),
                        "r1_target_hub_distance": d_from_hub.get(("q", (nr1 or {}).get("target_orbit"))),
                        "r2_source_hub_distance": d_from_hub.get(("q", sq)),
                        "r2_target_hub_distance": d_from_hub.get(("q", tq)),
                        "r2_meet_is_hub": meet_is_hub,
                        "r1_boundary_orientation": orient,
                        "fresh_orbit_openings": fresh,
                        "preparation_family": "no-fresh-opening" if fresh == 0 else "fresh-opening",
                    }
                    ck, chosen_alpha, stab, variants = canonical_decorated_key(tr.state, dec)
                    boundaries.append({
                        "raw_state_hash": state_hash(tr.state),
                        "canonical_state_hash": state_hash(exact.canonicalize(tr.state)),
                        "canonical_decorated_hash": hashlib.sha256(repr(ck).encode()).hexdigest(),
                        "chosen_alpha": chosen_alpha, "stabilizer_size": stab,
                        "tie_variant_count": len(set(variants)),
                        "decoration": dec,
                        "chaining": (nr1 or {}).get("target_orbit") == sq,
                        "same_component": same_component,
                        "r2_source_root_is_hub": sr is not None and sr == hub_root,
                        "r2_target_root_is_hub": tg is not None and tg == hub_root,
                        "depth_from_abandonment_root": n_depth,
                        "depth_from_word_start": n_depth + 1,
                        "path_from_abandonment_root": path + [label],
                        "legal_trailing_edges": legal_trailing(tr.state),
                        "phi": 5 + 6 * (exact.TARGET_P - tr.state.P) - (720 - tr.state.visited_count),
                        "O": tr.state.O, "S": tr.state.S, "F": tr.state.F, "H": tr.state.H,
                        "endpoint": list(tr.state.p),
                    })
            if nrc > 2:
                continue
            k = tr.state.stable_key()
            if k in seen:
                continue
            seen.add(k)
            frontier.append((tr.state, nrc, nr1, n_hub_touched, n_completer, n_fresh, n_depth,
                              path + [label]))

    for b in boundaries:
        b["legal_trailing_edge_count"] = len(b["legal_trailing_edges"])
    same = [b for b in boundaries if b["same_component"]]
    return {
        "abandonment_ell": ell,
        "frontier_empty": True, "depth_ceiling": depth_ceiling,
        "boundary_count_event_level": len(boundaries),
        "distinct_raw_states": len({b["raw_state_hash"] for b in boundaries}),
        "distinct_canonical_states": len({b["canonical_state_hash"] for b in boundaries}),
        "distinct_canonical_decorated": len({b["canonical_decorated_hash"] for b in boundaries}),
        "same_component_boundary_count": len(same),
        "chaining_boundary_count": sum(1 for b in boundaries if b["chaining"]),
        "stabilizer_sizes": dict(Counter(b["stabilizer_size"] for b in boundaries)),
        "tie_variant_counts": dict(Counter(b["tie_variant_count"] for b in boundaries)),
        "same_component_boundaries": sorted(same, key=lambda b: (b["depth_from_abandonment_root"], b["raw_state_hash"])),
        "all_boundaries": boundaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth-ceiling", type=int, default=6)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_decorated_l5_ledger.json"))
    args = parser.parse_args()

    init = exact.initial_state()
    hub = core.hexagon_id(init.p)
    results = {}
    for ell in range(5):
        r = enumerate_decorated(abandonment_root(init, ell), hub, ell, args.depth_ceiling)
        results[str(ell)] = r
        print(f"ell={ell}: boundaries={r['boundary_count_event_level']} "
              f"raw_states={r['distinct_raw_states']} canon_states={r['distinct_canonical_states']} "
              f"canon_decorated={r['distinct_canonical_decorated']} "
              f"same={r['same_component_boundary_count']} chaining={r['chaining_boundary_count']} "
              f"stab={r['stabilizer_sizes']}")

    report = {
        "schema": "rr-decorated-l5-ledger-v1",
        "engine_sha256": engine_sha256(),
        "hub_id": hub,
        "depth_ceiling": args.depth_ceiling,
        "decoration_fields_orbit_transported": list(ORBIT_FIELDS),
        "decoration_fields_hex_transported": list(HEX_FIELDS),
        "decoration_fields_invariant": list(INVARIANT_FIELDS),
        "results_by_ell": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", args.output)


if __name__ == "__main__":
    main()
