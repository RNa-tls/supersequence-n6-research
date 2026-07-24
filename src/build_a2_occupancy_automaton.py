#!/usr/bin/env python3
"""Sections 5-7: orbit-opening history for the two A2-relevant candidate
orbits (ell=4 and ell=0 candidates, in each witness's OWN raw/uncanonicalized
frame -- canonicalize() relabels orbit ids between macro-edges, verified
separately, so tracking "when does orbit X open" across a witness's full
history requires staying in one fixed, never-relabeled frame), plus a small
occupancy automaton built directly from the 5 focus witnesses' exact
histories (U4 x4 + the C20 outlier).

This is NOT a new large-scale search: it replays 5 ALREADY-KNOWN witnesses
(from outputs/u_branch_state_ledger.json, built in earlier rounds) and, at
each first-opening event, does a single bounded local check (enumerate
macro_edges at ONE state) -- never a multi-step continuation search.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
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


macro = _load("baoa_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1
W2_ONLY = [m for m in exact.ALL_MOVES if m.weight == 2][0]

U4_HASHES = [
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
]
OUTLIER_HASH = "e2b44997e7838537176bd6e0e72ea41df259f429863731b696dc76692beeb98c"
FIVE_HASHES = U4_HASHES + [OUTLIER_HASH]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def raw_events_to_pre_a2(witness: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], "exact.ExactState"]:
    """Replay the FULL macro_path in the raw (never-canonicalized) frame,
    recording one event per macro-edge (its rotation length, joint kind,
    target orbit q in this fixed raw frame) up to (not including) the A2
    macro-edge itself. Returns (events, pre_a2_state_raw)."""
    path = witness["macro_path"]
    cur = exact.initial_state()
    events: List[Dict[str, Any]] = []
    for idx, step in enumerate(path):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        probe = cur
        for _ in range(ell):
            tr = exact.extend(probe, W1)
            probe = tr.state
        tr = exact.extend(probe, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        if kind == "A2":
            return events, cur
        target_q = exact.ORBIT_PHASE[tr.target][0] if tr.target is not None else None
        for _ in range(ell):
            tr2 = exact.extend(cur, W1)
            cur = tr2.state
        tr2 = exact.extend(cur, move)
        cur = tr2.state
        events.append({
            "block_index": idx, "ell": ell, "kind": kind,
            "target_orbit_q_raw": target_q,
            "orbit_masks_snapshot_after_block": None,  # filled in second pass (needs final ids)
        })
    raise AssertionError("no A2 event found in witness macro_path")


def annotate_opening_bits(witness: Dict[str, Any], events: List[Dict[str, Any]], ell4_id: int, ell0_id: int) -> None:
    """Second pass: replay again (same raw frame) and record, after each
    committed block, whether orbit_masks[ell4_id] / [ell0_id] are nonzero
    -- this is the DIRECT, robust way to detect an orbit's first-opening
    block regardless of which internal move (rotation or joint) caused it,
    since a plain rotation step can also newly visit a port belonging to
    some other E-orbit and thus flip its existing bit."""
    path = witness["macro_path"]
    cur = exact.initial_state()
    for idx, step in enumerate(path):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        cur = tr.state
        events[idx]["orbit_masks_snapshot_after_block"] = {
            "b_ell4": cur.orbit_masks[ell4_id] != 0,
            "b_ell0": cur.orbit_masks[ell0_id] != 0,
        }
        if idx == len(events) - 1:
            return


def candidate_orbit_ids_raw(pre_a2_raw: "exact.ExactState") -> Tuple[int, int]:
    """ell=4 and ell=0 candidate orbit ids in pre_a2's OWN raw frame."""
    p0 = pre_a2_raw.p
    ids = []
    for ell in (4, 0):
        p_ell = core.compose(p0, core.power(core.SIGMA, ell))
        target = core.word_after(p_ell, W2_ONLY.action if hasattr(W2_ONLY, "action") else None)
        if target is None:
            action = core.tail_action(2, core.tail_permutations(2)[0])
            target = core.word_after(p_ell, action)
        q, _phase = exact.ORBIT_PHASE[target]
        ids.append(q)
    return ids[0], ids[1]  # (ell4_id, ell0_id)


def one_step_alternatives(state: "exact.ExactState", avoid_orbit_q: int) -> Dict[str, Any]:
    """Bounded, single-position check: at this exact state, how many
    legal macro-edges exist, and how many of them do NOT target
    avoid_orbit_q? This is NOT a multi-step search -- one macro_edges()
    call at one state."""
    edges = macro.macro_edges(state)
    total = 0
    avoiding = 0
    for e in edges:
        tr = e.joint
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        if reason is not None:
            continue
        total += 1
        if tr.target is None:
            avoiding += 1
            continue
        q, _phase = exact.ORBIT_PHASE[tr.target]
        if q != avoid_orbit_q:
            avoiding += 1
    return {"total_legal_alternatives_at_this_state": total, "alternatives_avoiding_this_orbit": avoiding}


def analyze_witness(h: str, witness: Dict[str, Any]) -> Dict[str, Any]:
    events, pre_a2_raw = raw_events_to_pre_a2(witness)
    ell4_id, ell0_id = candidate_orbit_ids_raw(pre_a2_raw)
    annotate_opening_bits(witness, events, ell4_id, ell0_id)

    init_masks = exact.initial_state().orbit_masks
    existing_at_word_start = {"b_ell4": init_masks[ell4_id] != 0, "b_ell0": init_masks[ell0_id] != 0}

    def first_opening(bit_key: str) -> Optional[Dict[str, Any]]:
        """Returns the first block where this bit flips 0->1 DURING the
        tracked history. Returns None both when the bit was already true
        at the true word start (initial_state(), before block 0 -- no
        'opening' event exists, it's a free resource) and when it never
        becomes true anywhere in the tracked history -- distinguished by
        existing_at_word_start / the trace's final value."""
        prev = existing_at_word_start[bit_key]
        for ev in events:
            cur_bit = ev["orbit_masks_snapshot_after_block"][bit_key]
            if cur_bit and not prev:
                return ev
            prev = cur_bit
        return None

    open_ell4 = first_opening("b_ell4")
    open_ell0 = first_opening("b_ell0")

    # replay again, this time stopping right BEFORE the identified opening
    # event, to do the single bounded one-step-alternatives check
    def state_before_block(block_index: Optional[int]) -> Optional["exact.ExactState"]:
        if block_index is None:
            return None
        path = witness["macro_path"]
        cur = exact.initial_state()
        for idx, step in enumerate(path):
            if idx == block_index:
                return cur
            rot_part, joint_part = step["edge_label"].split(";")
            ell = int(rot_part[len("rot^"):])
            move = move_by_label[joint_part]
            for _ in range(ell):
                tr = exact.extend(cur, W1)
                cur = tr.state
            tr = exact.extend(cur, move)
            cur = tr.state
        return None

    result: Dict[str, Any] = {
        "group": "U4" if h in U4_HASHES else "C20_outlier",
        "ell4_candidate_orbit_id_raw": ell4_id,
        "ell0_candidate_orbit_id_raw": ell0_id,
        "existing_at_true_word_start_before_any_tracked_block": existing_at_word_start,
        "events_before_a2": events,
        "first_opening_of_ell4_candidate_during_tracked_history": open_ell4,
        "first_opening_of_ell0_candidate_during_tracked_history": open_ell0,
    }
    if open_ell4 is not None:
        st = state_before_block(open_ell4["block_index"])
        result["ell4_opening_one_step_alternatives"] = one_step_alternatives(st, ell4_id) if st else None
    if open_ell0 is not None:
        st = state_before_block(open_ell0["block_index"])
        result["ell0_opening_one_step_alternatives"] = one_step_alternatives(st, ell0_id) if st else None
    return result


def build_automaton(per_witness: Dict[str, Any]) -> Dict[str, Any]:
    """Section 6: a small abstract automaton over (block_index, b_ell4,
    b_ell0) reconstructed directly from the 5 witnesses' exact event
    sequences (not a fresh state-space enumeration)."""
    traces = {}
    for h, data in per_witness.items():
        seq = []
        for ev in data["events_before_a2"]:
            snap = ev["orbit_masks_snapshot_after_block"]
            seq.append({"block_index": ev["block_index"], "kind": ev["kind"], "b_ell4": snap["b_ell4"], "b_ell0": snap["b_ell0"]})
        final_bits = seq[-1] if seq else {"b_ell4": False, "b_ell0": False}
        traces[h] = {
            "group": data["group"], "trace": seq,
            "final_bits_at_pre_a2": {"b_ell4": final_bits["b_ell4"], "b_ell0": final_bits["b_ell0"]},
        }
    return traces


def fire_a2(pre_a2_raw: "exact.ExactState", legal_ell: int) -> "exact.ExactState":
    cur = pre_a2_raw
    for _ in range(legal_ell):
        tr = exact.extend(cur, W1)
        cur = tr.state
    tr = exact.extend(cur, W2_ONLY)
    return tr.state


def post_a2_tree_stats(state: "exact.ExactState", ell4_id: int, ell0_id: int, max_depth: int, node_cap: int) -> Dict[str, Any]:
    """Section 8: small BOUNDED (depth<=max_depth, node_cap-limited)
    exhaustive tree exploration starting right after A2 fires -- reuses
    the same macro_edges()/area_a_prune_reason() building blocks as every
    prior round's bounded searches, no new large-scale search."""
    from collections import deque
    per_depth: Dict[int, Dict[str, Any]] = {}
    frontier = deque([(0, state)])
    expanded = 0
    terminal_reached = False
    while frontier and expanded < node_cap:
        depth, st = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        bucket = per_depth.setdefault(depth, {
            "states_expanded": 0, "legal_children_total": 0, "ell_counts": {},
            "capacity_fail_leaves": 0, "fresh_orbit_openings": 0,
            "candidate_orbit_reuse_ell4": 0, "candidate_orbit_reuse_ell0": 0,
        })
        bucket["states_expanded"] += 1
        legal = 0
        for e in macro.macro_edges(st):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            legal += 1
            if macro.area_a_final(tr.state, macro.AREA_A):
                terminal_reached = True
            ell_key = str(e.run.ell)
            bucket["ell_counts"][ell_key] = bucket["ell_counts"].get(ell_key, 0) + 1
            if tr.new_orbit:
                bucket["fresh_orbit_openings"] += 1
            if tr.target is not None:
                q, _phase = exact.ORBIT_PHASE[tr.target]
                if q == ell4_id:
                    bucket["candidate_orbit_reuse_ell4"] += 1
                if q == ell0_id:
                    bucket["candidate_orbit_reuse_ell0"] += 1
            frontier.append((depth + 1, tr.state))
        bucket["legal_children_total"] += legal
        if legal == 0:
            bucket["capacity_fail_leaves"] += 1
    return {
        "per_depth": {str(k): v for k, v in per_depth.items()},
        "nodes_expanded": expanded, "frontier_remaining": len(frontier),
        "exhaustive_within_cap": len(frontier) == 0,
        "any_terminal_reached": terminal_reached,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output-histories", default=str(ROOT / "outputs" / "a2_orbit_opening_histories.json"))
    parser.add_argument("--output-automaton", default=str(ROOT / "outputs" / "a2_occupancy_automaton.json"))
    parser.add_argument("--output-capacity-comparison", default=str(ROOT / "outputs" / "u4_two_bit_capacity_comparison.json"))
    parser.add_argument("--post-a2-max-depth", type=int, default=3)
    parser.add_argument("--post-a2-node-cap", type=int, default=4000)
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = {w["target_hash"]: w for w in ledger["words"]["RA2"]["witnesses"]}

    per_witness = {}
    for h in FIVE_HASHES:
        per_witness[h] = analyze_witness(h, ra2[h])
        d = per_witness[h]
        print(h[:12], d["group"], "existing_at_start", d["existing_at_true_word_start_before_any_tracked_block"],
              "ell4 first-open block", d["first_opening_of_ell4_candidate_during_tracked_history"] and d["first_opening_of_ell4_candidate_during_tracked_history"]["block_index"],
              "ell0 first-open block", d["first_opening_of_ell0_candidate_during_tracked_history"] and d["first_opening_of_ell0_candidate_during_tracked_history"]["block_index"])

    histories_report = {
        "schema": "a2-orbit-opening-histories-v1",
        "method": (
            "each witness replayed in its OWN raw (never-canonicalized) frame "
            "from initial_state to the A2 fresh-landing boundary -- verified "
            "separately that canonicalize() relabels orbit_masks indices "
            "between macro-edges, so tracking a fixed orbit id's opening "
            "history is only valid within one continuously-unrelabeled frame. "
            "The 'one_step_alternatives' field is a SINGLE bounded "
            "macro_edges() enumeration at the state immediately before the "
            "opening event -- it checks whether an immediate different move "
            "could avoid opening this orbit, NOT whether a full alternate "
            "continuation to an equivalent boundary exists (that would "
            "require a real search, which this round does not run)."
        ),
        "per_witness": per_witness,
    }
    Path(args.output_histories).write_text(json.dumps(histories_report, indent=2, sort_keys=True, default=str), encoding="utf-8")

    # Section 8: post-A2 bounded tree comparison. Reuse the recorded
    # legal_ells from the round-9/10 candidate tables (no new search there).
    tables_path = ROOT / "outputs" / "a2_rotation_candidate_tables.json"
    tables_data = json.loads(tables_path.read_text(encoding="utf-8"))
    capacity_comparison = {}
    for h in FIVE_HASHES:
        legal_ells = tables_data["tables_by_witness"][h]["legal_ells"]
        assert len(legal_ells) == 1, f"expected unique legal ell for {h}, got {legal_ells}"
        legal_ell = legal_ells[0]
        events, pre_a2_raw = raw_events_to_pre_a2(ra2[h])
        ell4_id, ell0_id = candidate_orbit_ids_raw(pre_a2_raw)
        post_state = fire_a2(pre_a2_raw, legal_ell)
        stats = post_a2_tree_stats(post_state, ell4_id, ell0_id, args.post_a2_max_depth, args.post_a2_node_cap)
        capacity_comparison[h] = {
            "group": per_witness[h]["group"], "legal_ell_fired": legal_ell,
            "post_a2_tree_stats": stats,
        }
        print(h[:12], per_witness[h]["group"], "post-A2 depth0 legal_children",
              stats["per_depth"].get("0", {}).get("legal_children_total"))

    capacity_report = {
        "schema": "u4-two-bit-capacity-comparison-v1",
        "method": (
            f"bounded exhaustive tree exploration (max_depth={args.post_a2_max_depth}, "
            f"node_cap={args.post_a2_node_cap} per witness) starting from the "
            "state immediately after A2 fires at each witness's own unique "
            "legal ell (4 for U4, 0 for the outlier) -- small, bounded, "
            "reused macro_edges()/area_a_prune_reason() machinery, NOT a new "
            "large-scale search."
        ),
        "per_witness": capacity_comparison,
    }
    Path(args.output_capacity_comparison).write_text(json.dumps(capacity_report, indent=2, sort_keys=True, default=str), encoding="utf-8")

    automaton = build_automaton(per_witness)
    automaton_report = {
        "schema": "a2-occupancy-automaton-v1",
        "note": (
            "This automaton is reconstructed directly from the 5 EXACT "
            "witnesses' event sequences (not a fresh enumeration of the "
            "reachable state space). It is sound as a record of what "
            "actually happened in these 5 witnesses, but it is NOT a "
            "complete cover of all realizable (b_ell4,b_ell0) histories at "
            "depth 0..3 -- promoting any depth<4 all-false observation here "
            "to a general i_min(A2)=4 lower bound is NOT justified by this "
            "data alone (doing so would require the same exhaustive "
            "state-space search this round was explicitly told not to "
            "repeat). Labeled '미완료' for that purpose; usable only as a "
            "'corpus exact observation' about these 5 witnesses."
        ),
        "traces": automaton,
    }
    Path(args.output_automaton).write_text(json.dumps(automaton_report, indent=2, sort_keys=True, default=str), encoding="utf-8")

    print(json.dumps({"wrote": [args.output_histories, args.output_automaton, args.output_capacity_comparison]}, indent=2))


if __name__ == "__main__":
    main()
