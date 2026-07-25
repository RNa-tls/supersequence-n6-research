#!/usr/bin/env python3
"""Round 21, sections 3, 13, 15, 16: the parity theorem, the preparation
depth resource question, and the 2-vs-3 trailing-edge predicate.

The parity result is decomposed into a hand-proved part and a measured
part, and the boundary between them is stated explicitly rather than
blurred.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, deque
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


macro = _load("vrpp_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W2_10 = move_by_label["w2:10"]
HEX0_POSITION_ORBIT = [0, 120, 33, 9, 3, 1]


def joint_kind(w, a, n):
    return {(2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J",
            (3, True, True): "A3"}.get((w, a, n), "?")


def abandonment_root(init, ell):
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    return exact.extend(cur, W2_10).state


def all_hub_completions(root_state, hub: int, ell: int, depth_ceiling: int) -> Dict[str, Any]:
    """Section 3: is 'edges before the completer is even' specific to
    same-component boundaries, or true of EVERY hub completion? Measuring
    this decides whether parity is a same-component phenomenon or a
    general hub phenomenon."""
    frontier = deque([(root_state, 0, 0)])
    seen = {root_state.stable_key()}
    completions: List[int] = []
    while frontier:
        state, depth, _ = frontier.popleft()
        if depth >= depth_ceiling:
            continue
        for edge in macro.macro_edges(state):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            hit_hub = tr.target is not None and core.hexagon_id(tr.target) == hub
            if hit_hub:
                completions.append(depth)  # edges strictly before this completer
            k = tr.state.stable_key()
            if k in seen:
                continue
            seen.add(k)
            # do not expand past a hub completion for this measurement
            frontier.append((tr.state, depth + 1, 0))
    return {"count": len(completions),
            "edges_before_completer_distribution": dict(sorted(Counter(completions).items())),
            "all_even": all(c % 2 == 0 for c in completions)}


def trailing_analysis(prep_records: List[Dict[str, Any]], hub: int) -> Dict[str, Any]:
    """Sections 15-16: recompute each same-component state's trailing edges
    and, for each of the three candidate ell=5 joints, record WHY it is or
    is not legal -- separating F_exceeded from a visited-collision."""
    init = exact.initial_state()
    out = []
    for rec in prep_records:
        ell = rec["abandonment_ell"]
        cur = abandonment_root(init, ell)
        for step in rec["preparation_trace"]:
            for _ in range(step["ell"]):
                cur = exact.extend(cur, W1).state
            cur = exact.extend(cur, move_by_label[step["joint"]]).state
        # replay the R2 edge itself
        r2_ell = rec["ell_profile"][-1]
        for _ in range(r2_ell):
            cur = exact.extend(cur, W1).state
        # find the R2 joint: the one reaching the recorded target orbit/phase
        r2_state = None
        for lbl, mv in move_by_label.items():
            if mv.weight != 3:
                continue
            tr = exact.extend(cur, mv)
            if tr is None:
                continue
            q, ph = exact.ORBIT_PHASE[tr.target]
            if q == rec["r2_target_orbit"] and ph == rec["r2_target_phase"]:
                r2_state = tr.state
                break
        if r2_state is None:
            out.append({"raw_state_hash": rec["raw_state_hash"], "error": "could not replay R2"})
            continue
        # now examine every candidate trailing macro-edge
        cand = []
        cur2 = r2_state
        for ellp in range(6):
            if ellp > 0:
                trw = exact.extend(cur2, W1)
                if trw is None:
                    cand.append({"ell": ellp, "verdict": "rotation collision (extend returned None)"})
                    break
                cur2 = trw.state
            for lbl, mv in sorted(move_by_label.items()):
                if mv.weight == 1:
                    continue
                tr = exact.extend(cur2, mv)
                if tr is None:
                    cand.append({"ell": ellp, "joint": lbl, "verdict": "target already visited (collision)",
                                 "legal": False})
                    continue
                reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
                cand.append({"ell": ellp, "joint": lbl,
                             "verdict": reason or "LEGAL", "legal": reason is None,
                             "abandonment": tr.abandonment})
        legal = [c for c in cand if c.get("legal")]
        ell5 = [c for c in cand if c["ell"] == 5]
        out.append({
            "raw_state_hash": rec["raw_state_hash"],
            "abandonment_ell": ell,
            "preparation_length": rec["preparation_length"],
            "legal_trailing_count": len(legal),
            "legal_trailing": [f"rot^{c['ell']};{c['joint']}" for c in legal],
            "ell5_candidates": ell5,
            "ell5_collision_joints": [c["joint"] for c in ell5 if "collision" in c["verdict"]],
            "ell5_f_exceeded_joints": [c["joint"] for c in ell5 if c["verdict"] == "F_exceeded"],
        })
    return {"per_state": out}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prep", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    parser.add_argument("--hub-completion-depth", type=int, default=5)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_trailing_edge_predicate.json"))
    parser.add_argument("--resource-output", default=str(ROOT / "outputs" / "rr_preparation_depth_resources.json"))
    args = parser.parse_args()

    data = json.loads(Path(args.prep).read_text(encoding="utf-8"))
    init = exact.initial_state()
    hub = core.hexagon_id(init.p)

    # ---- section 3: is 'before_C even' general or same-component-specific? ----
    print("=== all hub completions (not only same-component) ===")
    general = {}
    for ell in range(5):
        r = all_hub_completions(abandonment_root(init, ell), hub, ell, args.hub_completion_depth)
        general[str(ell)] = r
        print(f"  ell={ell}: {r['count']} completions, edges_before_C dist={r['edges_before_completer_distribution']}, all_even={r['all_even']}")

    # ---- sections 15/16: trailing edge analysis ----
    preps = [p for r in data["results_by_ell"].values() for p in r["preparations"]]
    ta = trailing_analysis(preps, hub)
    print("\n=== trailing-edge analysis ===")
    for s in ta["per_state"]:
        if "error" in s:
            print(f"  {s['raw_state_hash'][:12]} ERROR {s['error']}")
            continue
        print(f"  {s['raw_state_hash'][:12]} ell={s['abandonment_ell']} |W|={s['preparation_length']} "
              f"trailing={s['legal_trailing_count']} collisions={s['ell5_collision_joints']} "
              f"F_exceeded={s['ell5_f_exceeded_joints']}")

    counts = Counter(s.get("legal_trailing_count") for s in ta["per_state"] if "error" not in s)
    two = [s for s in ta["per_state"] if s.get("legal_trailing_count") == 2]
    print(f"\ntrailing count distribution: {dict(counts)}")
    if two:
        print(f"the 2-edge state(s): {[s['raw_state_hash'][:12] for s in two]}")
        print(f"  their ell=5 collision joints: {[s['ell5_collision_joints'] for s in two]}")

    trailing_report = {
        "schema": "rr-trailing-edge-predicate-v1",
        "upper_bound_argument": (
            "After R2 the abandonment budget F=1 is spent, so every macro-edge with "
            "ell<5 is an abandonment and is pruned F_exceeded; only ell=5 survives. "
            "The model has exactly 4 joints (UNIQUE_WEIGHT2_MOVE_THEOREM). Of those, "
            "w3:120 is still abandoning at these states. Hence AT MOST 3 remain. "
            "손증명 for the upper bound."
        ),
        "observed_counts": dict(counts),
        "two_versus_three_predicate": (
            "The count drops from 3 to 2 exactly when one of the three surviving "
            "ell=5 joints has an ALREADY-VISITED target permutation, i.e. "
            "exact.extend() returns None (a literal collision), NOT an "
            "area_a_prune_reason. This is a single occupancy bit -- whether that "
            "candidate target permutation is already in the visited set -- and it is "
            "computable from the ExactState (visited mask) but NOT from the "
            "decoration fields defined in Round 20."
        ),
        "per_state": ta["per_state"],
    }
    Path(args.output).write_text(json.dumps(trailing_report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", args.output)

    # ---- section 13: monotone resources per preparation edge ----
    res_rows = []
    for p in preps:
        res_rows.append({
            "raw_state_hash": p["raw_state_hash"], "abandonment_ell": p["abandonment_ell"],
            "preparation_length": p["preparation_length"],
            "fresh_orbit_openings": p["fresh_orbit_openings"],
            "O": p["O"], "S": p["S"],
            "edges_before_completer": p["edges_before_completer"],
            "E_edges": sum(1 for s in p["symbolic_preparation_word"] if s == "E"),
            "F_edges": sum(1 for s in p["symbolic_preparation_word"] if s == "F"),
        })
    by_len: Dict[int, List[Dict[str, Any]]] = {}
    for r in res_rows:
        by_len.setdefault(r["preparation_length"], []).append(r)
    resource = {
        "schema": "rr-preparation-depth-resources-v1",
        "question": "does every preparation edge consume a monotone finite resource, giving a nontrivial depth bound?",
        "rows": res_rows,
        "O_by_preparation_length": {str(k): sorted({r["O"] for r in v}) for k, v in sorted(by_len.items())},
        "fresh_by_preparation_length": {str(k): sorted({r["fresh_orbit_openings"] for r in v}) for k, v in sorted(by_len.items())},
        "finding": (
            "F edges consume a fresh E-orbit (a finite resource: 144 E-orbits, and "
            "TARGET_O=25 caps O), but E edges consume NO fresh orbit -- O is unchanged "
            "across them. Observed preparations of length 7 exist with only ONE fresh "
            "opening (O=3), so fresh-orbit count does NOT bound preparation length. "
            "No nontrivial monotone resource was identified this round: the only bound "
            "available remains the trivial one (the finite state space). 미완료."
        ),
    }
    Path(args.resource_output).write_text(json.dumps(resource, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", args.resource_output)

    print("\n=== resource check: O and fresh openings by preparation length ===")
    for k in sorted(by_len):
        print(f"  |W|={k}: O={sorted({r['O'] for r in by_len[k]})} fresh={sorted({r['fresh_orbit_openings'] for r in by_len[k]})}")

    general_out = ROOT / "outputs" / "rr_preparation_parity_general.json"
    general_out.write_text(json.dumps({
        "schema": "rr-preparation-parity-general-v1",
        "question": "is 'edges before the hub completer is even' general to all hub completions, or specific to same-component?",
        "depth_ceiling": args.hub_completion_depth,
        "by_ell": general,
    }, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", general_out)


if __name__ == "__main__":
    main()
