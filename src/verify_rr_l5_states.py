#!/usr/bin/env python3
"""Round 19, sections 2, 3, 5, 6, 7, 8, 11: the L5 state ledger, the
H3-vs-N2 split, the same-component => chaining re-verification inside
the root-local universe, the chaining predicate with ablations, and the
per-ell state-level counts.

Every count in this script is at the POST-R2 STATE level unless a field
name says "word". Round 18 established that mixing the two units is the
single error that produced the 9-vs-5 confusion, so the unit is carried
in every field name here.
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


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("vrl5_macro", "superperm_partial_f1_macro.py")
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


def legal_trailing(state) -> List[Dict[str, Any]]:
    out = []
    for edge in macro.macro_edges(state):
        if macro.area_a_prune_reason(edge.joint.state, macro.AREA_A) is None:
            tr = edge.joint
            tq, tph = exact.ORBIT_PHASE[tr.target]
            out.append({
                "label": f"rot^{edge.run.ell};{tr.move.label}", "ell": edge.run.ell,
                "kind": joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit),
                "target_hexagon": core.hexagon_id(tr.target), "target_orbit": tq, "target_phase": tph,
            })
    return sorted(out, key=lambda d: d["label"])


def abandonment_root(init, ell: int):
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    return exact.extend(cur, W2_10).state


def enumerate_with_paths(root_state, hex0: int, ell: int, depth_ceiling: int) -> Dict[str, Any]:
    """Raw-dedup BFS (safe for completeness -- Round 18) that records, for
    every same-component post-R2 state, the full macro-edge path and all
    boundary data needed for the ledger and the predicate ablations."""
    frontier = deque([(root_state, 0, None, None, 0, [])])
    seen = {root_state.stable_key()}
    post_r2: Dict[str, Dict[str, Any]] = {}
    rr_final_state_keys = set()
    chaining_state_keys = set()
    same_state_keys = set()
    same_nonchaining_state_keys = set()
    all_rr_boundaries: List[Dict[str, Any]] = []

    while frontier:
        state, rc, r1t, r1s, depth, path = frontier.popleft()
        if depth >= depth_ceiling:
            continue
        for edge in macro.macro_edges(state):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            label = f"rot^{edge.run.ell};{tr.move.label}"
            nrc, nr1t, nr1s = rc, r1t, r1s
            if kind == "R":
                nrc = rc + 1
                src_q, src_ph = exact.ORBIT_PHASE[edge.run.state.p]
                tgt_q, tgt_ph = exact.ORBIT_PHASE[tr.target]
                if nrc == 1:
                    nr1t, nr1s = tgt_q, src_q
                elif nrc == 2 and tr.state.F == 1 and tr.state.H == 0:
                    pm, find = component_map(edge.run.state)
                    sr = find(("q", src_q)) if ("q", src_q) in pm else None
                    tg = find(("q", tgt_q)) if ("q", tgt_q) in pm else None
                    chaining = (r1t == src_q)
                    is_same = sr is not None and sr == tg
                    sk = tr.state.stable_key()
                    rr_final_state_keys.add(sk)
                    if chaining:
                        chaining_state_keys.add(sk)
                    if is_same:
                        same_state_keys.add(sk)
                        if not chaining:
                            same_nonchaining_state_keys.add(sk)
                    # boundary record for the predicate ablation (event level)
                    hub_component = find(("h", hex0)) if ("h", hex0) in pm else None
                    all_rr_boundaries.append({
                        "same_component": is_same, "chaining": chaining,
                        "r1_target_orbit": r1t, "r1_source_orbit": r1s,
                        "r2_source_orbit": src_q, "r2_target_orbit": tgt_q,
                        "r2_source_phase": src_ph, "r2_target_phase": tgt_ph,
                        "r2_source_root_is_hub_component": sr is not None and sr == hub_component,
                        "r2_target_root_is_hub_component": tg is not None and tg == hub_component,
                        "r2_source_orbit_is_1": src_q == 1,
                        "r1_target_equals_r2_source": r1t == src_q,
                        "r1_target_equals_r2_target": r1t == tgt_q,
                        "depth_from_abandonment_root": depth + 1,
                    })
                    if is_same:
                        h = state_hash(tr.state)
                        if h not in post_r2:
                            post_r2[h] = {
                                "raw_state_hash": h,
                                "canonical_state_hash": state_hash(exact.canonicalize(tr.state)),
                                "abandonment_ell": ell,
                                "depth_from_abandonment_root": depth + 1,
                                "depth_from_word_start": depth + 2,
                                "min_word_macro_edges_to_reach": depth + 2,
                                "path_from_abandonment_root": path + [label],
                                "r1_source_orbit": r1s, "r1_target_orbit": r1t,
                                "r2_source_orbit": src_q, "r2_source_phase": src_ph,
                                "r2_target_orbit": tgt_q, "r2_target_phase": tgt_ph,
                                "r2_target_hexagon": core.hexagon_id(tr.target),
                                "chaining": chaining, "same_component": is_same,
                                "endpoint": list(tr.state.p),
                                "F": tr.state.F, "S": tr.state.S, "H": tr.state.H,
                                "O": tr.state.O, "D": tr.state.D, "P": tr.state.P,
                                "Ndef": tr.state.Ndef, "visited_count": tr.state.visited_count,
                                "phi": 5 + 6 * (exact.TARGET_P - tr.state.P) - (720 - tr.state.visited_count),
                                "visited_orbit_ids": sorted(q for q, m in enumerate(tr.state.orbit_masks) if m),
                                "legal_trailing_edges": legal_trailing(tr.state),
                                "distinct_paths_reaching_it": 0,
                            }
                        post_r2[h]["distinct_paths_reaching_it"] += 1
            if nrc > 2:
                continue
            k = tr.state.stable_key()
            if k in seen:
                continue
            seen.add(k)
            frontier.append((tr.state, nrc, nr1t, nr1s, depth + 1, path + [label]))

    for v in post_r2.values():
        v["legal_trailing_edge_count"] = len(v["legal_trailing_edges"])
        v["pure_rotation_suffix_possible"] = any(e["ell"] == 5 for e in v["legal_trailing_edges"])

    return {
        "abandonment_ell": ell,
        "root_raw_hash": state_hash(root_state),
        "frontier_empty": True,
        "depth_ceiling": depth_ceiling,
        "post_r2_state_count_rr_final": len(rr_final_state_keys),
        "post_r2_state_count_chaining": len(chaining_state_keys),
        "post_r2_state_count_same_component": len(same_state_keys),
        "post_r2_state_count_same_and_nonchaining": len(same_nonchaining_state_keys),
        "same_component_states": sorted(post_r2.values(),
                                         key=lambda r: (r["depth_from_abandonment_root"], r["raw_state_hash"])),
        "rr_boundary_records_event_level": all_rr_boundaries,
    }


def predicate_ablation(boundaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Section 7: which boundary predicate exactly characterizes chaining
    inside this universe? Tests each candidate for necessity and
    sufficiency, at the EVENT level (one record per R2 boundary)."""
    candidates = {
        "r1_target_equals_r2_source": lambda b: b["r1_target_equals_r2_source"],
        "same_component": lambda b: b["same_component"],
        "r2_source_orbit_is_1": lambda b: b["r2_source_orbit_is_1"],
        "r2_source_root_is_hub_component": lambda b: b["r2_source_root_is_hub_component"],
        "r2_target_root_is_hub_component": lambda b: b["r2_target_root_is_hub_component"],
        "r1_target_equals_r2_target": lambda b: b["r1_target_equals_r2_target"],
        "same_component AND r2_source_orbit_is_1": lambda b: b["same_component"] and b["r2_source_orbit_is_1"],
        "r2_source_root_is_hub AND r2_target_root_is_hub": lambda b: b["r2_source_root_is_hub_component"] and b["r2_target_root_is_hub_component"],
    }
    out = {}
    for name, fn in candidates.items():
        tp = fp = fn_ = tn = 0
        fp_ex = fn_ex = None
        for b in boundaries:
            p, c = fn(b), b["chaining"]
            if p and c:
                tp += 1
            elif p and not c:
                fp += 1
                fp_ex = fp_ex or b
            elif not p and c:
                fn_ += 1
                fn_ex = fn_ex or b
            else:
                tn += 1
        out[name] = {
            "true_positive": tp, "false_positive": fp, "false_negative": fn_, "true_negative": tn,
            "sufficient_for_chaining": fp == 0 and tp > 0,
            "necessary_for_chaining": fn_ == 0,
            "iff_chaining": fp == 0 and fn_ == 0 and tp > 0,
            "false_positive_example": fp_ex, "false_negative_example": fn_ex,
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth-ceiling", type=int, default=6)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_l5_state_ledger.json"))
    args = parser.parse_args()

    init = exact.initial_state()
    hex0 = core.hexagon_id(init.p)

    per_ell = {}
    for ell in range(5):
        r = enumerate_with_paths(abandonment_root(init, ell), hex0, ell, args.depth_ceiling)
        per_ell[str(ell)] = r
        print(f"ell={ell}: rr_final_states={r['post_r2_state_count_rr_final']} "
              f"chaining_states={r['post_r2_state_count_chaining']} "
              f"same_states={r['post_r2_state_count_same_component']} "
              f"same_and_nonchaining={r['post_r2_state_count_same_and_nonchaining']}")

    # ---- Section 6: same-component => chaining, state level AND event level ----
    all_boundaries = [b for r in per_ell.values() for b in r["rr_boundary_records_event_level"]]
    ev_same = [b for b in all_boundaries if b["same_component"]]
    ev_violations = [b for b in ev_same if not b["chaining"]]
    st_violations = sum(r["post_r2_state_count_same_and_nonchaining"] for r in per_ell.values())
    print(f"\nSection 6 -- same-component => chaining:")
    print(f"  event level: {len(ev_same) - len(ev_violations)}/{len(ev_same)} hold, violations={len(ev_violations)}")
    print(f"  state level: violations={st_violations}")

    # ---- Section 7: predicate ablation ----
    abl = predicate_ablation(all_boundaries)
    print(f"\nSection 7 -- chaining predicate ablation (event level, {len(all_boundaries)} R2 boundaries):")
    for name, d in abl.items():
        flag = "IFF" if d["iff_chaining"] else ("suff" if d["sufficient_for_chaining"] else ("nec" if d["necessary_for_chaining"] else "-"))
        print(f"  {flag:5s} {name:52s} tp={d['true_positive']:4d} fp={d['false_positive']:4d} fn={d['false_negative']:4d}")

    # ---- Section 2/3: L5 ledger and the H3/N2 split (ell=4) ----
    l5 = per_ell["4"]["same_component_states"]
    h3 = [s for s in l5 if s["depth_from_word_start"] <= 6]
    n2 = [s for s in l5 if s["depth_from_word_start"] > 6]
    print(f"\nSection 2/3 -- ell=4: L5 has {len(l5)} states; H3={len(h3)} (word depth<=6), N2={len(n2)} (word depth>6)")
    for tag, group in (("H3", h3), ("N2", n2)):
        for s in group:
            print(f"  {tag} {s['raw_state_hash'][:12]} depth_root={s['depth_from_abandonment_root']} "
                  f"word_edges={s['depth_from_word_start']} R1({s['r1_source_orbit']}->{s['r1_target_orbit']}) "
                  f"R2({s['r2_source_orbit']}->{s['r2_target_orbit']}) phi={s['phi']} "
                  f"O={s['O']} S={s['S']} trailing={s['legal_trailing_edge_count']} path={s['path_from_abandonment_root']}")

    report = {
        "schema": "rr-l5-state-ledger-v1",
        "counting_unit": "POST-R2 STATE (never word) unless a field name says otherwise",
        "depth_ceiling": args.depth_ceiling,
        "per_ell": per_ell,
        "section6_same_implies_chaining": {
            "event_level_antecedent_count": len(ev_same),
            "event_level_violations": len(ev_violations),
            "event_level_violation_examples": ev_violations[:3],
            "state_level_violations": st_violations,
            "holds": len(ev_violations) == 0 and st_violations == 0,
            "proof_status": "root-local exhaustive (NOT a global RR theorem, NOT a hand proof)",
        },
        "section7_chaining_predicate_ablation": abl,
        "section2_l5_ledger_ell4": l5,
        "section3_h3_n2_split": {"H3": h3, "N2": n2},
    }
    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
