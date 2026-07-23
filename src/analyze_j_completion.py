#!/usr/bin/env python3
"""Independent analysis of the F=1,H=0 charge-2 "J" joint.

J = an abandonment (F=1,H=0) tail of weight >= 3 whose target lands in an
E-orbit that is *already in use*. Among the eight boolean
(weight in {2,3}) x abandonment x new_orbit combinations, J is the unique
one with delta_N = 2 (see ``truth_table()`` below).

This module reuses the actual exact-state engine shipped in
``legacy_research/work/`` (``superperm_partial_f1.py`` and
``superperm_partial_f1_macro.py``). That is a deliberate choice, not a
shortcut: the engine *is* the definition of F/S/H/O/N and of what counts as
an abandonment, a new orbit, a legal tail, etc. Re-implementing it from
scratch would not make the analysis more independent -- it would just risk
introducing a second, inconsistent definition of the same objects. What
*is* independent here is the reasoning built on top of it: nothing below
trusts a conclusion written in ``legacy_research/work/analyze_f1_n2_defects.py``
without re-deriving or re-checking it against the engine directly.

Honesty note on data availability (read before trusting any "230" claim):
``legacy_research/outputs/f1_n2_depth6_decomposition.json`` and
``f1_n2_defect_words.json`` record, for 229 of the 230 stored J instances,
only derived summary fields (a state hash, ``deficit_phase_type``,
``legal_macro_tail_count``) -- not the literal walk that produced them.
Exactly ONE concrete literal J path is stored (the "representative").
Every literal-replay / bounded-continuation claim in this module is
therefore scoped to that one seed. The other 229 are analysed only through
their recorded summary fields, in ``src/verify_j_normal_forms.py``.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
OUTPUTS = ROOT / "legacy_research" / "outputs"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("j_completion_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core

KIND_NAMES = {
    (2, False, False): "Z2_blocked_w2_existing",
    (2, False, True): "forbidden_blocked_w2_new",
    (2, True, False): "A2_abandon_w2_existing",
    (2, True, True): "Z2_abandon_w2_new",
    (3, False, False): "R_blocked_w3_existing",
    (3, False, True): "Z3_blocked_w3_new",
    (3, True, False): "J_abandon_w3_existing_charge2",
    (3, True, True): "A3_abandon_w3_new",
}


def truth_table() -> List[Dict[str, Any]]:
    """The 8-row joint truth table, re-derived from the definitions alone.

    delta_N = 1_{weight>=3} + 1_{abandonment} - 1_{new_orbit} is an
    algebraic identity (N := S+F-O, and a joint changes S,F,O by exactly
    these three indicators), not something that needs a search to check.
    """
    rows = []
    for weight, abandonment, new_orbit in itertools.product((2, 3), (False, True), (False, True)):
        dF, dS, dO = int(abandonment), int(weight >= 3), int(new_orbit)
        dN = dS + dF - dO
        rows.append({
            "weight": weight, "abandonment": abandonment, "new_orbit": new_orbit,
            "delta_F": dF, "delta_S": dS, "delta_O": dO, "delta_N": dN,
            "kind": KIND_NAMES[(weight, abandonment, new_orbit)],
        })
    return rows


def charge_two_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if r["delta_N"] == 2]


def negative_charge_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if r["delta_N"] < 0]


def bounded_raw_reachability_check(max_depth: int, node_cap: int) -> Dict[str, Any]:
    """Bounded (uncanonicalized) BFS from the identity, tallying which of the
    8 (weight,abandonment,new_orbit) combos are ever actually witnessed among
    genuinely legal joints.

    This is deliberately NOT a claim of exhaustiveness or a proof that the
    forbidden row is impossible -- it is a real, bounded, honestly-reported
    empirical check against the actual engine. Left-S6 relabelling
    (independently proved equivariant in ``exact.py``'s own sanity suite)
    preserves the (weight,abandonment,new_orbit) triple, so skipping
    canonicalization here does not bias which combos can appear -- it only
    changes how many redundant copies of each are counted.
    """
    start = exact.initial_state()
    seen = {start.stable_key()}
    frontier = deque([(0, start)])
    combo_counts: Counter = Counter()
    combo_examples: Dict[Tuple[int, bool, bool], Dict[str, Any]] = {}
    expanded = 0
    t0 = time.time()
    while frontier and expanded < node_cap:
        depth, state = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        for edge in macro.macro_edges(state):
            tr = edge.joint
            key = (tr.move.weight, tr.abandonment, tr.new_orbit)
            combo_counts[key] += 1
            if key not in combo_examples:
                combo_examples[key] = {"depth": depth, "label": edge.label}
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            ck = tr.state.stable_key()
            if ck in seen:
                continue
            seen.add(ck)
            frontier.append((depth + 1, tr.state))
    elapsed = time.time() - t0
    forbidden = (2, False, True)
    return {
        "expanded": expanded,
        "distinct_raw_states_reached": len(seen),
        "frontier_remaining": len(frontier),
        "max_depth": max_depth,
        "node_cap": node_cap,
        "elapsed_seconds": round(elapsed, 2),
        "observed_combo_counts": {
            f"{KIND_NAMES[k]}": {"weight": k[0], "abandonment": k[1], "new_orbit": k[2],
                                   "count": v, "first_example": combo_examples[k]}
            for k, v in sorted(combo_counts.items())
        },
        "forbidden_row_observed": forbidden in combo_counts,
        "note": (
            "Absence of the forbidden row here is a bounded empirical check, "
            "not a proof. It is consistent with (does not itself establish) "
            "the 'blocked-w2 lemma' this corpus cites from prior work."
        ),
    }


def load_literal_j_representative() -> Dict[str, Any]:
    data = json.loads((OUTPUTS / "f1_n2_depth6_decomposition.json").read_text(encoding="utf-8"))
    return data["representatives_by_word"]["J"]


def replay_j_representative() -> Dict[str, Any]:
    """Literal, step-by-step replay of the ONE stored J path, independent of
    ``analyze_f1_n2_defects.py``'s own replay helpers: this calls
    ``exact.extend`` directly, not any wrapper that already knows the answer.
    """
    rep = load_literal_j_representative()
    path = rep["path"]
    W1 = macro.W1
    # canonical_children=True to match the original recorded convention
    # (checkpoint_header.config.canonical_children == true): the search
    # dedups by canonical form between macro steps, so matching state
    # hashes against the stored record requires the same convention.
    state = exact.canonicalize(exact.initial_state())
    step_records = []
    for item in path:
        ell = int(item["rotation_length"])
        for _ in range(ell):
            tr = exact.extend(state, W1)
            if tr is None:
                raise AssertionError("literal J representative: rotation collision during replay")
            state = tr.state
        label = str(item["joint"])
        move = next(m for m in exact.ALL_MOVES if m.label == label)
        before = state
        tr = exact.extend(state, move)
        if tr is None:
            raise AssertionError("literal J representative: joint illegal during replay")
        state = exact.canonicalize(tr.state)
        step_records.append({
            "label": item["joint"],
            "rotation_length": ell,
            "weight": move.weight,
            "abandonment": tr.abandonment,
            "new_orbit": tr.new_orbit,
            "delta_F": tr.delta_F,
            "delta_S": tr.delta_S,
            "delta_O": int(tr.new_orbit),
            "delta_N": (state.Ndef - before.Ndef),
            "kind": KIND_NAMES[(move.weight, tr.abandonment, tr.new_orbit)],
        })
    final_coordinate = macro.state_coordinate(state)
    stored_coordinate = tuple(rep["coordinate"])
    last = step_records[-1]
    return {
        "stored_state_hash": rep["state_hash"],
        "recomputed_state_hash": macro.stable_hash(state),
        "state_hash_matches": rep["state_hash"] == macro.stable_hash(state),
        "final_coordinate_P_F_S_H_O_D_N": list(final_coordinate),
        "stored_coordinate_matches": list(final_coordinate) == list(stored_coordinate),
        "steps": step_records,
        "last_step_is_J": last["kind"] == "J_abandon_w3_existing_charge2",
        "last_step_deltas_match_J_row": (
            last["delta_F"] == 1 and last["delta_S"] == 1
            and last["delta_O"] == 0 and last["delta_N"] == 2
        ),
        "final_state": state,
    }


def post_j_budget(state: "exact.ExactState") -> Dict[str, Any]:
    """The 'post-J rigid budget' theorem's quantities for a concrete state.

    Once J occurs, F == exact.TARGET_F (the abandonment budget for the whole
    walk is exhausted): every remaining joint for the rest of the walk must
    have abandonment=False, on pain of F_exceeded pruning and unreachable
    completion (exact.final_target requires state.F == TARGET_F exactly).

    Every remaining *new*-orbit opening must therefore come from the unique
    zero-charge, non-abandoning, new-orbit joint type, Z3_blocked_w3_new
    (weight=3, abandonment=False, new_orbit=True, delta_N=0) -- R
    (weight=3, abandonment=False, new_orbit=False) targets an *existing*
    orbit by definition and contributes no new orbit.

    Given the overall slab target is Ndef+H <= exact.TARGET_BUDGET (an
    upper bound, not an exact value) and H=0 throughout this branch, the
    remaining budget for further N-increasing joints is
    ``TARGET_BUDGET - state.Ndef``. Since no further abandonment is
    possible, that remaining budget can only be spent on R events (the only
    surviving delta_N=+1 joint type); everything else must be delta_N=0.
    """
    remaining_joints = exact.TARGET_P - state.P
    remaining_new_orbits = exact.TARGET_O - state.O
    remaining_existing_orbit_joints = remaining_joints - remaining_new_orbits
    remaining_n_budget = exact.TARGET_BUDGET - state.H - state.Ndef
    # Sanity check of the D=5O-P identity's forward consequence: every
    # remaining new-orbit joint contributes +4 to D=5O-P, every remaining
    # existing-orbit joint contributes -1. This must reconcile current D
    # with TARGET_D given the O,P targets, purely arithmetically.
    predicted_D_change = 4 * remaining_new_orbits - remaining_existing_orbit_joints
    actual_D_change_needed = exact.TARGET_D - state.D
    return {
        "coordinate_P_F_S_H_O_D_N": list(macro.state_coordinate(state)),
        "abandonment_budget_remaining": exact.TARGET_F - state.F,
        "no_further_abandonment_possible": (exact.TARGET_F - state.F) == 0,
        "remaining_joints_total": remaining_joints,
        "remaining_new_orbit_joints_required": remaining_new_orbits,
        "remaining_existing_orbit_joints_required": remaining_existing_orbit_joints,
        "remaining_n_budget_for_R_events": remaining_n_budget,
        "arithmetic_consistency_check": {
            "predicted_D_change_from_counts": predicted_D_change,
            "actual_D_change_needed_for_TARGET_D": actual_D_change_needed,
            "consistent": predicted_D_change == actual_D_change_needed,
        },
        "forced_joint_alphabet_for_remainder": {
            "Z3_blocked_w3_new": remaining_new_orbits,
            "R_blocked_w3_existing": f"at most {remaining_n_budget}",
            "Z2_blocked_w2_existing": (
                f"remaining_existing_orbit_joints - (0..{remaining_n_budget} of them being R)"
            ),
            "A2_A3_J_or_Z2_abandon_w2_new": "impossible (abandonment budget exhausted)",
        },
    }


def bounded_continuation_from_seed(
    seed_state: "exact.ExactState",
    macro_depth_cap: int,
    edge_cap: int,
) -> Dict[str, Any]:
    """A bounded, single-seed continuation search from the (already-replayed)
    post-J state. This is NOT a new Area-A search: it starts from one fixed
    literal state, is capped hard on edges expanded and additional macro
    depth, uses no checkpoint, and is a separate one-shot process. It is a
    restricted experiment, not a completeness or impossibility proof for J.
    """
    frontier = deque([(0, seed_state)])
    edges_expanded = 0
    depth_survivor_counts: Counter = Counter({0: 1})
    prune_counts: Counter = Counter()
    immediate_terminal_states = 0
    forced_defect_states = 0  # states whose only legal macro edges are all pruned
    max_survivor_depth = 0
    longest_path_labels: List[str] = []
    path_by_state: Dict[Any, List[str]] = {seed_state.stable_key(): []}

    while frontier and edges_expanded < edge_cap:
        depth, state = frontier.popleft()
        if depth >= macro_depth_cap:
            continue
        any_legal_child = False
        any_child_at_all = False
        for edge in macro.macro_edges(state):
            any_child_at_all = True
            edges_expanded += 1
            reason = macro.area_a_prune_reason(edge.state, macro.AREA_A)
            if reason is not None:
                prune_counts[reason] += 1
                continue
            any_legal_child = True
            depth_survivor_counts[depth + 1] += 1
            key = edge.state.stable_key()
            labels = path_by_state.get(state.stable_key(), []) + [edge.label]
            path_by_state[key] = labels
            if depth + 1 > max_survivor_depth:
                max_survivor_depth = depth + 1
                longest_path_labels = labels
            frontier.append((depth + 1, edge.state))
            if edges_expanded >= edge_cap:
                break
        if not any_child_at_all:
            immediate_terminal_states += 1
        elif not any_legal_child:
            forced_defect_states += 1

    return {
        "config": {"macro_depth_cap": macro_depth_cap, "edge_cap": edge_cap, "checkpoint": None},
        "edges_expanded": edges_expanded,
        "cap_hit": edges_expanded >= edge_cap,
        "depth_survivor_counts": dict(sorted(depth_survivor_counts.items())),
        "prune_counts": dict(sorted(prune_counts.items())),
        "immediate_terminal_states": immediate_terminal_states,
        "states_with_only_pruned_children": forced_defect_states,
        "max_survivor_depth_reached": max_survivor_depth,
        "example_longest_surviving_macro_label_path": longest_path_labels,
        "scope": "single-seed bounded experiment from the one literal J representative; not a completeness or impossibility result",
    }


def build_report() -> Dict[str, Any]:
    rows = truth_table()
    c2 = charge_two_rows(rows)
    neg = negative_charge_rows(rows)
    reach = bounded_raw_reachability_check(max_depth=7, node_cap=60_000)
    replay = replay_j_representative()
    budget = post_j_budget(replay["final_state"])
    continuation = bounded_continuation_from_seed(
        replay["final_state"], macro_depth_cap=4, edge_cap=100_000
    )
    replay_out = {k: v for k, v in replay.items() if k != "final_state"}
    return {
        "schema": "j-completion-analysis-v1",
        "engine_code_sha256": exact.CODE_SHA256,
        "engine_core_sha256": exact.CORE_SHA256,
        "macro_code_sha256": macro.CODE_SHA256,
        "truth_table": rows,
        "unique_charge_two_row": c2,
        "charge_two_uniqueness_proved": len(c2) == 1 and c2[0]["kind"] == "J_abandon_w3_existing_charge2",
        "negative_charge_rows": neg,
        "bounded_reachability_check": reach,
        "literal_J_representative_replay": replay_out,
        "post_J_budget_theorem": budget,
        "bounded_continuation_from_J_seed": continuation,
    }


def main() -> None:
    report = build_report()
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "j_completion_analysis.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
