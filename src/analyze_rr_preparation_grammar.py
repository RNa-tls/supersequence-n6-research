#!/usr/bin/env python3
"""Round 21, sections 1, 2, 4, 5, 6, 7, 8: preparation-word extraction,
the symbolic alphabet, the insertion/deletion analysis, and the base
normal forms.

DEPTH CONVENTION (section 5 requires this be fixed and stated once):
  depth_from_word_start      = total macro-edges in the word so far,
                               counting the abandonment edge as 1.
  depth_from_abandonment_root = macro-edges AFTER the abandonment.
  Relation: depth_from_word_start = depth_from_abandonment_root + 1.
Both are stored on every record. All parity statements name their
convention explicitly.

WORD DECOMPOSITION (section 1):
    A_ell   W   R2
  A_ell : the abandonment edge (rotation offset ell inside the hub)
  W     : the preparation word, every macro-edge strictly between A and R2
  R2    : the second R event
The hub completer C is an edge INSIDE W. Round 20 asserted C is always
W's last edge; that is TRUE for ell=4 (9/9) and FALSE for ell=0 (0/3),
where C is second-to-last and W's final edge is the hub-exit edge. This
script measures the position rather than assuming it.
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


macro = _load("arpg_macro", "superperm_partial_f1_macro.py")
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


def symbolic_label(step: Dict[str, Any], o_star: int, hub: int, is_completer: bool) -> str:
    """Section 2's alphabet, defined without reference to literal orbit ids
    except through O* (itself defined invariantly as the nearest residual
    orbit of the hub at the word's abandonment offset)."""
    if is_completer:
        return "C"
    k = step["kind"]
    if k == "R":
        return "Rh" if step["tgt"][0] == o_star else "Rx"
    if step["new_orbit"]:
        return "F"
    if step["src_hex"] == hub:
        return "Xh"          # hub-exit zero-charge edge
    return "E"


def legal_trailing(state) -> List[str]:
    return sorted(f"rot^{e.run.ell};{e.joint.move.label}" for e in macro.macro_edges(state)
                  if macro.area_a_prune_reason(e.joint.state, macro.AREA_A) is None)


def abandonment_root(init, ell: int):
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    return exact.extend(cur, W2_10).state


def enumerate_preparations(root_state, hub: int, ell: int, depth_ceiling: int) -> Dict[str, Any]:
    o_star = HEX0_POSITION_ORBIT[ell + 1] if ell + 1 < 6 else None
    frontier = deque([(root_state, 0, None, None, 0, [])])
    seen = {root_state.stable_key()}
    found: List[Dict[str, Any]] = []
    expanded = 0

    while frontier:
        state, rc, r1t, completer_idx, depth, trace = frontier.popleft()
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
            shex = core.hexagon_id(pre.p)
            step = {"label": f"rot^{edge.run.ell};{tr.move.label}", "ell": edge.run.ell,
                    "joint": tr.move.label, "kind": kind, "new_orbit": tr.new_orbit,
                    "src": [sq, sph], "tgt": [tq, tph], "src_hex": shex, "tgt_hex": thex}
            n_completer_idx = completer_idx
            if thex == hub and completer_idx is None:
                n_completer_idx = depth + 1
            nrc, nr1t = rc, r1t
            if kind == "R":
                nrc = rc + 1
                if nrc == 1:
                    nr1t = tq
                elif nrc == 2 and tr.state.F == 1 and tr.state.H == 0:
                    parent, find = component_roots(pre)
                    sr = find(("q", sq)) if ("q", sq) in parent else None
                    tg = find(("q", tq)) if ("q", tq) in parent else None
                    if sr is not None and sr == tg:
                        W = trace  # preparation word: everything between A and R2
                        cidx = n_completer_idx
                        syms = [symbolic_label(s, o_star, hub, i + 1 == cidx) for i, s in enumerate(W)]
                        found.append({
                            "raw_state_hash": state_hash(tr.state),
                            "abandonment_ell": ell, "o_star": o_star,
                            "depth_from_abandonment_root": depth + 1,
                            "depth_from_word_start": depth + 2,
                            "preparation_length": len(W),
                            "completer_index_within_preparation": cidx,
                            "edges_before_completer": (cidx - 1) if cidx else None,
                            "edges_after_completer_within_preparation": (len(W) - cidx) if cidx else None,
                            "completer_to_r2_macro_distance": (depth + 1) - cidx if cidx else None,
                            "completer_is_last_preparation_edge": (cidx == len(W)) if cidx else None,
                            "symbolic_preparation_word": syms,
                            "kind_signature": [s["kind"] for s in W],
                            "ell_profile": [s["ell"] for s in W] + [edge.run.ell],
                            "phi_cost_profile": [5 - s["ell"] for s in W] + [5 - edge.run.ell],
                            "fresh_orbit_openings": sum(1 for s in W if s["new_orbit"]),
                            "r1_target_orbit": r1t, "r2_source_orbit": sq, "r2_source_phase": sph,
                            "r2_target_orbit": tq, "r2_target_phase": tph,
                            "chaining": r1t == sq,
                            "phi": 5 + 6 * (exact.TARGET_P - tr.state.P) - (720 - tr.state.visited_count),
                            "O": tr.state.O, "S": tr.state.S,
                            "legal_trailing_edges": legal_trailing(tr.state),
                            "preparation_trace": W,
                        })
            if nrc > 2:
                continue
            k = tr.state.stable_key()
            if k in seen:
                continue
            seen.add(k)
            frontier.append((tr.state, nrc, nr1t, n_completer_idx, depth + 1, trace + [step]))

    for f in found:
        f["legal_trailing_edge_count"] = len(f["legal_trailing_edges"])
    return {"abandonment_ell": ell, "o_star": o_star, "depth_ceiling": depth_ceiling,
            "expanded": expanded, "frontier_empty": True,
            "same_component_count": len(found),
            "preparations": sorted(found, key=lambda f: (f["preparation_length"], f["raw_state_hash"]))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ell4-depth", type=int, default=8)
    parser.add_argument("--ell0-depth", type=int, default=7)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    args = parser.parse_args()

    init = exact.initial_state()
    hub = core.hexagon_id(init.p)

    per_ell = {}
    for ell, dc in ((0, args.ell0_depth), (1, args.ell0_depth), (2, args.ell0_depth),
                    (3, args.ell0_depth), (4, args.ell4_depth)):
        r = enumerate_preparations(abandonment_root(init, ell), hub, ell, dc)
        per_ell[str(ell)] = r
        print(f"ell={ell} (O*={r['o_star']}, depth<={dc}): same={r['same_component_count']}")
        for f in r["preparations"]:
            print(f"   {f['raw_state_hash'][:12]} |W|={f['preparation_length']} "
                  f"C@{f['completer_index_within_preparation']} before_C={f['edges_before_completer']} "
                  f"C->R2={f['completer_to_r2_macro_distance']} "
                  f"sym={''.join(f['symbolic_preparation_word'])} "
                  f"ells={f['ell_profile']} phi={f['phi']} trail={f['legal_trailing_edge_count']}")

    # ---- parity measurements, both conventions ----
    parity = {}
    for ell, r in per_ell.items():
        ps = r["preparations"]
        if not ps:
            parity[ell] = {"n": 0}
            continue
        parity[ell] = {
            "n": len(ps),
            "depth_from_word_start": sorted({f["depth_from_word_start"] for f in ps}),
            "depth_from_word_start_parity": sorted({f["depth_from_word_start"] % 2 for f in ps}),
            "depth_from_abandonment_root": sorted({f["depth_from_abandonment_root"] for f in ps}),
            "depth_from_abandonment_root_parity": sorted({f["depth_from_abandonment_root"] % 2 for f in ps}),
            "preparation_length": sorted({f["preparation_length"] for f in ps}),
            "preparation_length_parity": sorted({f["preparation_length"] % 2 for f in ps}),
            "edges_before_completer": sorted({f["edges_before_completer"] for f in ps}),
            "edges_before_completer_parity": sorted({f["edges_before_completer"] % 2 for f in ps}),
            "completer_to_r2_macro_distance": sorted({f["completer_to_r2_macro_distance"] for f in ps}),
            "completer_is_last_prep_edge": sorted({f["completer_is_last_preparation_edge"] for f in ps}),
            "phi": sorted({f["phi"] for f in ps}),
            "nonzero_phi_cost_edges": sorted({tuple(sorted(c for c in f["phi_cost_profile"] if c)) for f in ps}),
        }
    print("\n=== parity, BOTH conventions ===")
    for ell, p in parity.items():
        if p["n"] == 0:
            print(f"  ell={ell}: no same-component states")
            continue
        print(f"  ell={ell}: word_start={p['depth_from_word_start']} (parity {p['depth_from_word_start_parity']}) | "
              f"root={p['depth_from_abandonment_root']} (parity {p['depth_from_abandonment_root_parity']})")
        print(f"          |W|={p['preparation_length']} (parity {p['preparation_length_parity']}) | "
              f"before_C={p['edges_before_completer']} (parity {p['edges_before_completer_parity']}) | "
              f"C->R2={p['completer_to_r2_macro_distance']} | C_is_last={p['completer_is_last_prep_edge']}")
        print(f"          nonzero phi-cost edges: {p['nonzero_phi_cost_edges']}")

    report = {
        "schema": "rr-preparation-words-v1",
        "depth_convention": {
            "depth_from_word_start": "total macro-edges including the abandonment edge",
            "depth_from_abandonment_root": "macro-edges strictly after the abandonment",
            "relation": "word_start = root + 1",
        },
        "word_decomposition": "A_ell W R2 ; the hub completer C is an edge inside W",
        "symbolic_alphabet": {
            "Rh": "R event whose target orbit is O* (the nearest residual orbit)",
            "Rx": "R event targeting some other orbit",
            "F": "fresh Z3 orbit opening",
            "E": "existing-orbit zero-charge transition, source outside the hub",
            "Xh": "zero-charge transition whose SOURCE lies in the hub (hub-exit edge)",
            "C": "the hub completer edge (whatever its kind)",
        },
        "hub_id": hub,
        "results_by_ell": per_ell,
        "parity_measurements": parity,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", args.output)


if __name__ == "__main__":
    main()
