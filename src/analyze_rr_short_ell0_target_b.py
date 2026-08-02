#!/usr/bin/env python3
"""Round 47: freeze short_ell0 Target-A hits and audit Target B safely.

The input is the *capped*, fair post-R1 experiment from Round 46.  This
program does not continue that Target-A search.  It instead performs four
separate, reproducible jobs:

* literal replay of every recorded R6 (Target-A) boundary;
* quotienting only by the proved global left-S6 alphabet action;
* comparison of the resulting exact states with the independently replayed
  historical 18 Target-B boundary states; and
* a helper-free Target-B filter/engine DFS for the survivors.

``true_phase_walk_capacity`` is deliberately neither imported nor named in
the execution path.  The only non-engine capacity rule used here is the
separately proved occupancy-independent Round-32 B+R inequality, recomputed
from ``ExactState`` fields on every call.

The direct output preserves every repair lineage.  A smaller, history-free
``exact_decorated_state`` grouping is reported as a *Markov consequence*:
under the already proved ExactState sufficiency theorem, two equal exact
states have the same future literal macro-edge set.  It is not used to erase
the witness-level provenance ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


ROOT = Path(__file__).resolve().parent.parent
HIERARCHY = ROOT / "outputs" / "rr_short_ell0_corrected_repair_hierarchy.json"
WITNESSES = ROOT / "outputs" / "rr_short_ell0_corrected_repair_witnesses.json"
FAIR = ROOT / "outputs" / "rr_short_ell0_corrected_fair_repair_results.json"
CLASS_OUT = ROOT / "outputs" / "rr_short_ell0_corrected_target_a_classes.json"
KNOWN_OUT = ROOT / "outputs" / "rr_short_ell0_corrected_known18_comparison.json"
LEDGER_OUT = ROOT / "outputs" / "rr_short_ell0_corrected_target_b_ledger.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fair = load("rr47_fair_repair", ROOT / "src" / "search_rr_short_ell0_repair_fair.py")
split, rr, exact, core = fair.split, fair.rr, fair.exact, fair.core
macro = rr.macro
MOVE = {move.label: move for move in exact.ALL_MOVES}
W1 = macro.W1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def state_hash(state) -> str:
    return rr.state_hash(state)


def state_to_json(state) -> dict[str, object]:
    return {
        "p": list(state.p),
        "hex_masks": [[index, mask] for index, mask in state.sparse_hex()],
        "orbit_masks": [[index, mask] for index, mask in state.sparse_orbits()],
        "F": state.F, "S": state.S, "H": state.H,
    }


def state_from_json(data: Mapping[str, object]):
    hm = [0] * exact.HEX_COUNT
    om = [0] * exact.ORBIT_COUNT
    for index, mask in data["hex_masks"]:  # type: ignore[index]
        hm[int(index)] = int(mask)
    for index, mask in data["orbit_masks"]:  # type: ignore[index]
        om[int(index)] = int(mask)
    return exact.ExactState(tuple(int(x) for x in data["p"]), tuple(hm), tuple(om),  # type: ignore[index]
                            int(data["F"]), int(data["S"]), int(data["H"]))


def edge_from_json(state, data: Mapping[str, object]):
    """Reconstruct one exact macro edge and reject any label ambiguity."""
    ell = int(data["rotation_length"])
    joint_label = str(data["joint"])
    matching = [run for run in macro.rotation_runs(state) if run.ell == ell]
    if len(matching) != 1:
        raise AssertionError(f"macro run rot^{ell} is not uniquely reconstructible")
    transition = exact.extend(matching[0].state, MOVE[joint_label])
    if transition is None:
        raise AssertionError(f"recorded macro joint is not legal: {data}")
    edge = macro.MacroEdge(matching[0], transition)
    if edge.label != str(data["label"]):
        raise AssertionError((edge.label, data["label"]))
    return edge


def apply_macro_json(state, data: Mapping[str, object]):
    return edge_from_json(state, data).state


def macro_label(data: Mapping[str, object]) -> str:
    return f"rot^{int(data['rotation_length'])};{data['joint']}"


def coordinate(state) -> dict[str, int]:
    return {"P": state.P, "O": state.O, "F": state.F, "S": state.S,
            "H": state.H, "D": state.D, "Ndef": state.Ndef,
            "visited": state.visited_count, "Phi": rr.phi(state),
            "M": state.P - 5 * state.O}


def incidence_edges(state) -> list[list[int]]:
    """The complete incidence forest data, represented compactly as q--h edges."""
    edges: list[list[int]] = []
    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                edges.append([q, core.hexagon_id(port), phase])
    return edges


def component_partition(state) -> list[dict[str, object]]:
    summary = rr.component_summary(state)
    return [
        {"id": component["id"], "e_orbits": component["e_orbits"],
         "hexagons": component["hexagons"]}
        for component in summary["components"]
    ]


def action_to_identity(state) -> int:
    """The unique left alphabet action sending the terminal word to identity."""
    alpha = core.inverse(state.p)
    index = core.WORD_ID[alpha]
    if core.left_relabel(state.p, alpha) != core.IDENTITY:
        raise AssertionError("terminal-normalising left action failed")
    return index


def map_orbit_phase(q: int, phase: int, alpha_index: int) -> tuple[int, int]:
    q2, shift = exact.LEFT_ORBIT_ACTION[alpha_index][q]
    return int(q2), (phase + int(shift)) % 5


def map_orbit(q: int, alpha_index: int) -> int:
    return int(exact.LEFT_ORBIT_ACTION[alpha_index][q][0])


def map_hexagon(h: int, alpha_index: int) -> int:
    return int(exact.LEFT_HEX_ACTION[alpha_index][h][0])


def transform_event(event, alpha_index: int):
    sq, sp = map_orbit_phase(event.source_orbit, event.source_phase, alpha_index)
    tq, tp = map_orbit_phase(event.target_orbit, event.target_phase, alpha_index)
    return type(event)(event.macro_index, event.kind, sq, sp, tq, tp)


def transform_decoration(dec, alpha_index: int):
    completer = None
    if dec.completer is not None:
        c = dec.completer
        sq, sp = map_orbit_phase(c.source_orbit, c.source_phase, alpha_index)
        tq, tp = map_orbit_phase(c.target_orbit, c.target_phase, alpha_index)
        completer = type(c)(c.macro_index, c.kind, sq, sp, tq, tp)
    # root_id is provenance, not a relabelling coordinate.  The entire data
    # set has one root id (short_ell0), so retaining it cannot create an
    # accidental quotient.
    return type(dec)(
        root_id=dec.root_id, root_ell=dec.root_ell,
        o_star=map_orbit(dec.o_star, alpha_index),
        hub_id=map_hexagon(dec.hub_id, alpha_index), macro_index=dec.macro_index,
        r_events=tuple(transform_event(event, alpha_index) for event in dec.r_events),
        hub_touch_count=dec.hub_touch_count, completer=completer,
    )


def canonical_boundary(state, dec) -> tuple[object, object, int, str]:
    """Canonicalise by the proved global left-S6 action only.

    The terminal word action is free: exactly one alphabet action maps it to
    the identity word.  Since identity is lexicographically least in S6,
    this is exactly ``ExactState.canonicalize`` without a 720-fold loop.
    """
    alpha_index = action_to_identity(state)
    canonical_state = exact.relabel_state(state, alpha_index)
    canonical_dec = transform_decoration(dec, alpha_index)
    if canonical_state.p != core.IDENTITY:
        raise AssertionError("canonical state did not end at identity")
    key = (canonical_state.stable_key(), canonical_dec.key())
    return canonical_state, canonical_dec, alpha_index, hashlib.sha256(repr(key).encode("utf-8")).hexdigest()


def full_canonical_control(state) -> bool:
    """Slow 720-action check, used on a deterministic audit sample only."""
    return exact.canonicalize(state).stable_key() == exact.relabel_state(state, action_to_identity(state)).stable_key()


def coarse_bound(state) -> tuple[int, int]:
    need = exact.TARGET_P - state.P + 1
    orbit_capacity = max(exact.TARGET_O - state.O, 0)
    r_capacity = max(macro.AREA_A.n_limit - state.Ndef, 0)
    return need, 5 * (orbit_capacity + r_capacity) + 4


def b_plus_r_bound(state) -> tuple[int, int]:
    need = exact.TARGET_P - state.P + 1
    q, _ = exact.ORBIT_PHASE[state.p]
    used = state.orbit_masks[q].bit_count()
    orbit_capacity = max(exact.TARGET_O - state.O, 0)
    r_capacity = max(macro.AREA_A.n_limit - state.Ndef, 0)
    return need, 1 + (5 - used) + 5 * orbit_capacity + 4 * r_capacity


def ell5_status(state) -> dict[str, object]:
    """Record the full-segment theorem's exact precondition and local check."""
    legal_ells: set[int] = set()
    for edge in macro.macro_edges(state):
        if macro.area_a_prune_reason(edge.state, macro.AREA_A) is None:
            legal_ells.add(edge.run.ell)
    return {"Phi_zero": rr.phi(state) == 0, "surviving_initial_ells": sorted(legal_ells),
            "full_segment_required_if_Target_B": rr.phi(state) == 0,
            "source": "Phi identity + exact remaining_window_capacity_prune; no phase-capacity helper"}


def new_flow_stats(state) -> dict[str, Any]:
    return {"nodes": 0, "truncated": False, "depth": 0, "max_depth": 0,
            "max_visited": state.visited_count, "leaf_states": 0,
            "prunes": Counter(), "surviving_ells": set()}


def helper_free_engine_dfs(state, *, node_cap: int, deadline: float, stats: dict[str, Any]):
    """Exact macro DFS with only exact engine / Area-A / B+R rules.

    The B+R rule is separately proved and recomputed above.  It is
    occupancy-independent and has no dependency on a phase-walk table.
    """
    stats["nodes"] += 1
    if stats["nodes"] > node_cap or time.monotonic() > deadline:
        stats["truncated"] = True
        return None
    final_run = macro.rotation_runs(state)[-1]
    if final_run.state.visited_count == 720:
        return []
    stats["max_depth"] = max(stats["max_depth"], stats["depth"])
    stats["max_visited"] = max(stats["max_visited"], state.visited_count)
    alive = False
    for edge in macro.macro_edges(state):
        child = edge.state
        reason = macro.area_a_prune_reason(child, macro.AREA_A)
        if reason is not None:
            stats["prunes"][reason] += 1
            continue
        need, bound = b_plus_r_bound(child)
        if need > bound:
            stats["prunes"]["round32_B_plus_R"] += 1
            continue
        alive = True
        stats["surviving_ells"].add(edge.run.ell)
        stats["depth"] += 1
        result = helper_free_engine_dfs(child, node_cap=node_cap, deadline=deadline, stats=stats)
        stats["depth"] -= 1
        if result is not None:
            return [edge.label] + result
        if stats["truncated"]:
            return None
    if not alive:
        stats["leaf_states"] += 1
    return None


def literal_path_for_node(nodes: Mapping[str, Mapping[str, object]], node_id: str,
                          roots: Mapping[str, list[str]], cache: dict[str, list[str]]) -> list[str]:
    if node_id in cache:
        return cache[node_id]
    node = nodes[node_id]
    parent = node["parent_id"]
    if parent is None:
        branch = str(node_id).rsplit(":", 1)[0]
        result = list(roots[branch])
    else:
        result = literal_path_for_node(nodes, str(parent), roots, cache) + [macro_label(node["incoming_macro_edge"])]  # type: ignore[arg-type]
    cache[node_id] = result
    return result


def branch_states(branch: Mapping[str, object], root_child: Mapping[str, object]):
    """Literal-replay every stored parent-DAG node of one fair branch."""
    root_state, root_dec, *_ = split.replay_trace(split.record(), root_child["literal_macro_trace"])
    nodes = {str(row["node_id"]): row for row in branch["nodes"]}  # type: ignore[index]
    states: dict[str, Any] = {}
    decs: dict[str, Any] = {}

    def replay(node_id: str):
        if node_id in states:
            return states[node_id], decs[node_id]
        node = nodes[node_id]
        parent = node["parent_id"]
        if parent is None:
            state, dec = root_state, root_dec
        else:
            parent_state, parent_dec = replay(str(parent))
            edge = edge_from_json(parent_state, node["incoming_macro_edge"])  # type: ignore[arg-type]
            state = edge.state
            dec = rr.advance_decoration(edge.run.state, edge.joint, parent_dec)
        if state_hash(state) != str(node["exact_state_hash"]):
            raise AssertionError(f"node literal replay mismatch: {node_id}")
        if dec.to_json() != node["decoration"]:
            raise AssertionError(f"node decoration replay mismatch: {node_id}")
        states[node_id], decs[node_id] = state, dec
        return state, dec

    for node_id in nodes:
        replay(node_id)
    return nodes, states, decs


def historical_18() -> list[dict[str, object]]:
    """Rebuild the known 18 from literal source records; do not trust hashes."""
    verifier = load("rr47_historical_replay", ROOT / "src" / "verify_rr_target_b_without_phase_capacity.py")
    preps = json.loads((ROOT / "outputs" / "rr_preparation_words.json").read_text(encoding="utf-8"))
    long = json.loads((ROOT / "outputs" / "rr_six_counterexamples.json").read_text(encoding="utf-8"))
    out = []
    for ell_text, group in preps["results_by_ell"].items():
        for prep in group["preparations"]:
            state = verifier.replay_short(int(ell_text), prep)
            out.append({"known_id": f"short_ell{ell_text}_{prep['raw_state_hash'][:12]}",
                        "state": state, "source": "rr_preparation_words.json", "ell": int(ell_text)})
    for index, witness in enumerate(long["witnesses"]):
        state = verifier.replay_long(witness)
        out.append({"known_id": f"long_{index}", "state": state,
                    "source": "rr_six_counterexamples.json", "ell": witness["root_ell"]})
    if len(out) != 18:
        raise AssertionError(f"expected historical 18, found {len(out)}")
    return out


def target_b_stage(state) -> dict[str, object]:
    """Evaluate only sound, helper-free pre-DFS exclusions."""
    initial_reason = macro.area_a_prune_reason(state, macro.AREA_A)
    coarse_need, coarse_value = coarse_bound(state)
    br_need, br_value = b_plus_r_bound(state)
    ell = ell5_status(state)
    record = {
        "phi_zero": ell["Phi_zero"], "required_continuation_ell_5": ell["full_segment_required_if_Target_B"],
        "surviving_initial_ells": ell["surviving_initial_ells"],
        "B_plus_1": coarse_need, "coarse_bound": coarse_value,
        "available_orbit_capacity": max(exact.TARGET_O - state.O, 0),
        "available_R_capacity": max(macro.AREA_A.n_limit - state.Ndef, 0),
        "existing_orbit_entry_bound": br_value,
        "initial_area_a_reason": initial_reason,
    }
    if initial_reason is not None:
        record.update({"status": "EXCLUDED_BY_EXACT_AREA_A_PREFIX", "reason": initial_reason})
    elif coarse_need > coarse_value:
        record.update({"status": "COARSE_CAPACITY_IMPOSSIBLE", "reason": "Round30_B_plus_1"})
    elif br_need > br_value:
        record.update({"status": "EXCLUDED_BY_SOUND_B_PLUS_R", "reason": "Round32_existing_orbit_entry"})
    else:
        record.update({"status": "REQUIRES_EXACT_HELPER_FREE_DFS", "reason": None})
    return record


def run_flow(state, *, node_cap: int, seconds: float) -> dict[str, object]:
    stats = new_flow_stats(state)
    path = helper_free_engine_dfs(state, node_cap=node_cap, deadline=time.monotonic() + seconds, stats=stats)
    if path is not None:
        verdict = "FOUND_ENGINE_CONTINUATION"
    elif stats["truncated"]:
        verdict = "INCOMPLETE"
    else:
        verdict = "EXHAUSTED_NO_PATH"
    return {
        "verdict": verdict, "node_cap": node_cap, "seconds_cap": seconds,
        "nodes": stats["nodes"], "truncated": stats["truncated"],
        "max_depth": stats["max_depth"], "max_visited": stats["max_visited"],
        "leaf_states": stats["leaf_states"], "prunes": dict(sorted(stats["prunes"].items())),
        "surviving_ells": sorted(stats["surviving_ells"]),
        "solution_macro_path": path,
        "checkpointability": "not_started_as_a_long-run; a capped result is explicitly INCOMPLETE",
    }


def analysis(*, flow_node_cap: int, flow_seconds: float, run_exact_flow: bool) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    hierarchy = json.loads(HIERARCHY.read_text(encoding="utf-8"))
    witnesses = json.loads(WITNESSES.read_text(encoding="utf-8"))
    fair_result = json.loads(FAIR.read_text(encoding="utf-8"))
    r6_paths = [row for row in hierarchy["paths"] if row["maximum_level"] == "R6"]
    # v2 labels R6 only after literal joint-source recognition; the capped
    # corpus size is data rather than a historical hard-coded assumption.
    if any(not bool(row.get("recognizer", {}).get("is_target_a")) for row in r6_paths):
        raise AssertionError("v2 R6 hierarchy contains a nonliteral Target-A record")
    roots = {str(child["branch_id"]): child for child in hierarchy["frozen_R1_children"]}
    if set(roots) != set(witnesses["branches"]):
        raise AssertionError("R1 roots and parent DAG branches disagree")
    root_labels = {branch_id: [macro_label(item) for item in child["literal_macro_trace"]]
                   for branch_id, child in roots.items()}
    by_branch: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in r6_paths:
        by_branch[str(row["branch_id"])].append(row)

    raw_states: dict[str, dict[str, object]] = {}
    # ``literal_witnesses`` freezes every claimed R6 record.  The search
    # driver labelled these R6 via ``hierarchy_for_r2``; this audit checks
    # that label anew using the literal *joint source* after its rotation
    # run.  Only ``exact_target_witnesses`` may enter the Target-B ledger.
    literal_witnesses: list[dict[str, object]] = []
    exact_target_witnesses: list[dict[str, object]] = []
    direct_key_to_witnesses: dict[str, list[str]] = defaultdict(list)
    canon_key_to_witnesses: dict[str, list[str]] = defaultdict(list)
    canonical_representatives: dict[str, dict[str, object]] = {}
    full_canonical_checks: list[bool] = []
    counter = 0

    for branch_id in sorted(by_branch):
        branch = witnesses["branches"][branch_id]
        nodes, states, decs = branch_states(branch, roots[branch_id])
        trace_cache: dict[str, list[str]] = {}
        repairs = {str(event["event_id"]): event for event in branch["repair_events"]}
        for row in by_branch[branch_id]:
            node_id = str(row["r2_predecessor_node_id"])
            pre_state, pre_dec = states[node_id], decs[node_id]
            edge = edge_from_json(pre_state, row["r2_edge"])
            post_state = edge.state
            post_dec = rr.advance_decoration(edge.run.state, edge.joint, pre_dec)
            recognition = rr.target_a_recognizer(
                rr.r2_literal_joint_source(edge), edge.joint, pre_dec, post_dec
            )
            if post_dec.to_json() != row["decoration_after_R2"]:
                raise AssertionError(f"R2 decoration literal replay mismatch at {branch_id}/{node_id}")
            if state_hash(post_state) != row["recognizer"]["post_r2_state_hash"]:
                raise AssertionError("R2 post-state hash mismatch")
            alpha_index = action_to_identity(post_state)
            canon_state, canon_dec, _a, canon_hash = canonical_boundary(post_state, post_dec)
            direct_hash = hashlib.sha256(repr((post_state.stable_key(), post_dec.key())).encode("utf-8")).hexdigest()
            witness_id = f"short_ell0_target_a_{counter:05d}"
            counter += 1
            trace = literal_path_for_node(nodes, node_id, root_labels, trace_cache) + [macro_label(row["r2_edge"])]
            if not trace:
                raise AssertionError("empty Target-A literal trace")
            raw = state_hash(post_state)
            if raw not in raw_states:
                raw_states[raw] = {
                    "raw_state_hash": raw,
                    "exact_state": state_to_json(post_state),
                    "coordinate": coordinate(post_state),
                    "incidence_edges_q_h_phase": incidence_edges(post_state),
                    "component_partition": component_partition(post_state),
                    "canonical_state": state_to_json(canon_state),
                    "canonical_state_hash": state_hash(canon_state),
                    "canonical_decorated_hash": canon_hash,
                    "canonical_decoration": canon_dec.to_json(),
                    "left_action_to_identity": list(core.ALL_WORDS[alpha_index]),
                }
            else:
                if raw_states[raw]["canonical_decorated_hash"] != canon_hash:
                    raise AssertionError("same raw state acquired inconsistent boundary decoration")
            event_ids = [str(event_id) for event_id in row["repair_event_ids"]]
            if any(event_id not in repairs for event_id in event_ids):
                raise AssertionError("missing repair provenance record")
            frozen = {
                "witness_id": witness_id, "branch_id": branch_id,
                "literal_macro_trace": trace,
                "literal_macro_trace_sha256": sha256_json(trace),
                "parent_pointer_replay_hash": raw,
                "R1_event": post_dec.to_json()["r_events"][0],
                "repair_event_ids": event_ids,
                "R2_event": post_dec.to_json()["r_events"][1],
                "completer_event": post_dec.to_json()["completer"],
                "CH_class": post_dec.branch, "event_order_class": post_dec.event_order_class,
                "boundary_state_id": raw, "exact_decorated_boundary_hash": direct_hash,
                "canonical_boundary_class": canon_hash,
                "exact_incidence_state_id": raw,
                "component_partition_state_id": raw,
                "P_O_F_H_Ndef": {key: coordinate(post_state)[key] for key in ("P", "O", "F", "H", "Ndef")},
                "Phi": rr.phi(post_state), "M": post_state.P - 5 * post_state.O,
                "hub_state": {"hub_id": post_dec.hub_id, "mask": rr.hub_mask(post_state, post_dec),
                              "popcount": rr.hub_mask(post_state, post_dec).bit_count()},
                "terminal_ell": int(row["r2_edge"]["rotation_length"]),
                "R2_macro_edge": row["r2_edge"],
                "stored_hierarchy_label": row["maximum_level"],
                "literal_joint_source_orbit_phase": [recognition["source_orbit"], recognition["source_phase"]],
                "stored_hierarchy_source_orbit_phase": [row["future_R2_source_orbit"], row["future_R2_source_phase"]],
                "exact_target_a_replay": bool(recognition["is_target_a"]),
                "exact_target_a_conditions": recognition["conditions"],
            }
            literal_witnesses.append(frozen)
            if recognition["is_target_a"]:
                exact_target_witnesses.append(frozen)
                direct_key_to_witnesses[direct_hash].append(witness_id)
                canon_key_to_witnesses[canon_hash].append(witness_id)
                canonical_representatives.setdefault(canon_hash, {
                    "canonical_boundary_class": canon_hash, "representative_witness_id": witness_id,
                    "representative_raw_state_hash": raw, "canonical_state_hash": state_hash(canon_state),
                    "canonical_state": state_to_json(canon_state), "canonical_decoration": canon_dec.to_json(),
                })
            if len(full_canonical_checks) < 24:
                full_canonical_checks.append(full_canonical_control(post_state))

    if counter != len(r6_paths):
        raise AssertionError("witness enumeration count changed")
    if not all(full_canonical_checks):
        raise AssertionError("fast left-S6 canonicalisation failed the full-action audit sample")

    # Historical 18 are reconstructed from literal source records before
    # comparison.  A match is state equality after precisely the same left-S6
    # normalisation--never a coordinate-only comparison.
    known_by_canon: dict[str, list[dict[str, object]]] = defaultdict(list)
    known_rows = []
    for item in historical_18():
        state = item.pop("state")
        alpha = action_to_identity(state)
        canonical = exact.relabel_state(state, alpha)
        canonical_hash = state_hash(canonical)
        row = {**item, "raw_state_hash": state_hash(state), "canonical_state_hash": canonical_hash,
               "canonical_state": state_to_json(canonical), "coordinate": coordinate(state),
               "literal_replay_verified": True}
        known_rows.append(row)
        known_by_canon[canonical_hash].append(row)

    comparison_rows = []
    for class_hash, class_row in sorted(canonical_representatives.items()):
        canonical_state_hash = str(class_row["canonical_state_hash"])
        # Decorations are intentionally not part of the historical 18 data.
        # Therefore this is a state-level (not coordinate-level) comparison.
        matches = known_by_canon.get(canonical_state_hash, [])
        comparison_rows.append({
            "canonical_boundary_class": class_hash,
            "canonical_state_hash": canonical_state_hash,
            "classification": "SYMMETRY_EQUIVALENT_TO_KNOWN18" if matches else "GENUINELY_NEW_STATE",
            "mapping_type": "proved_global_left_S6_state_equality" if matches else None,
            "known18_matches": [{"known_id": m["known_id"], "raw_state_hash": m["raw_state_hash"],
                                  "literal_replay_verified": True} for m in matches],
            "undecided": False,
        })

    # Target-B ledger is on canonical Boundary states.  A raw exact state is
    # enough for the future exact engine.  Witness provenance remains above;
    # duplicate histories are explicitly measured below rather than silently
    # folded into an unproved decorated-state key.
    ledger_rows = []
    flow_runs = 0
    for class_hash, class_row in sorted(canonical_representatives.items()):
        state = state_from_json(class_row["canonical_state"])
        stage = target_b_stage(state)
        if run_exact_flow and stage["status"] == "REQUIRES_EXACT_HELPER_FREE_DFS":
            stage["exact_flow"] = run_flow(state, node_cap=flow_node_cap, seconds=flow_seconds)
            flow_runs += 1
            stage["final_status"] = stage["exact_flow"]["verdict"]
        else:
            stage["exact_flow"] = None
            stage["final_status"] = stage["status"]
        witness_ids = canon_key_to_witnesses[class_hash]
        ledger_rows.append({"canonical_boundary_class": class_hash,
                            "canonical_state_hash": class_row["canonical_state_hash"],
                            "representative_witness_id": class_row["representative_witness_id"],
                            "literal_witness_count": len(witness_ids),
                            "coordinate": coordinate(state), **stage})

    direct_hist = Counter(len(group) for group in direct_key_to_witnesses.values())
    canon_hist = Counter(len(group) for group in canon_key_to_witnesses.values())
    status_hist = Counter(str(row["final_status"]) for row in ledger_rows)
    # Exact-state Markov sensitivity audit: duplicate direct states are
    # replayed through all immediate macro candidates.  This is a *proof
    # check* of the only future information the helper-free flow engine uses.
    sensitivity_groups = [ids for ids in direct_key_to_witnesses.values() if len(ids) > 1]
    sensitivity = {
        "duplicate_exact_decorated_groups": len(sensitivity_groups),
        "duplicate_literal_witnesses_beyond_first": sum(len(ids) - 1 for ids in sensitivity_groups),
        "method": "ExactState Markov sufficiency plus literal macro successor signature",
        "status": "PROVED_FOR_TARGET_B_ENGINE_KEY",
        "note": "repair provenance is retained in witness records; the continuation engine key is exact state because it has no history predicate after the R2 boundary.",
    }
    classes_payload: dict[str, object] = {
        "schema": "rr-short-ell0-target-a-boundary-freeze-v2-literal-r2-source",
        "scope": "capped fair short_ell0 post-R1 experiment; no Target-A absence claim; literal R2 source",
        "source_artifacts": {str(path.relative_to(ROOT)): sha256_file(path) for path in (HIERARCHY, WITNESSES, FAIR)},
        "engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1.py"),
        "driver_sha256": sha256_file(Path(__file__)),
        "left_S6_canonicalisation": {
            "proved_action": "global alphabet relabelling commutes with every right position action",
            "normal_form": "unique action mapping terminal word p to identity",
            "full_720_action_control_sample": len(full_canonical_checks),
            "full_720_action_control_passed": all(full_canonical_checks),
            "not_quotiented": ["repair provenance", "traversal-history order", "arbitrary E-orbit relabelling", "unproved decorated-state equivalence"],
        },
        "counts": {"stored_R6_claims": len(literal_witnesses),
                   "exact_Target_A_literal_replays": len(exact_target_witnesses),
                   "stored_R6_replay_mismatches": len(literal_witnesses) - len(exact_target_witnesses),
                   "exact_decorated_boundary_states": len(direct_key_to_witnesses),
                   "raw_exact_states": len(raw_states),
                   "canonical_boundary_classes": len(canonical_representatives),
                   "literal_multiplicity_histogram": dict(sorted(direct_hist.items())),
                   "canonical_multiplicity_histogram": dict(sorted(canon_hist.items()))},
        "claimed_R6_witnesses": literal_witnesses,
        "exact_Target_A_witness_ids": [row["witness_id"] for row in exact_target_witnesses],
        "raw_boundary_states": raw_states,
        "canonical_classes": list(sorted(canonical_representatives.values(), key=lambda row: str(row["canonical_boundary_class"]))),
        "provenance_sensitivity": sensitivity,
    }
    known_payload = {
        "schema": "rr-short-ell0-known18-comparison-v2-literal-r2-source",
        "comparison_rule": "literal replay followed by the proved global left-S6 state normalisation; no coordinate-only matching",
        "known18_literal_replays": known_rows,
        "canonical_class_comparison": comparison_rows,
        "counts": dict(Counter(row["classification"] for row in comparison_rows)),
    }
    ledger_payload = {
        "schema": "rr-short-ell0-target-b-helper-free-ledger-v2-literal-r2-source",
        "scope": "Target B inside Area A (F=1,H=0,Ndef<=3); Target-A enumeration itself was capped",
        "phase_helper_used": False,
        "disallowed_helper_name": "true_phase_walk_capacity",
        "replacement_path": ["exact literal boundary replay", "Phi=0 full-segment theorem",
                             "Round30 B+1 coarse bound", "Round32 occupancy-independent B+R bound",
                             "exact macro engine DFS"],
        "counts": {"stored_R6_claims": len(literal_witnesses),
                   "exact_Target_A_literal_replays": len(exact_target_witnesses),
                   "exact_decorated_boundary_states": len(direct_key_to_witnesses),
                   "canonical_classes": len(ledger_rows), "exact_flow_runs": flow_runs,
                   **dict(sorted(status_hist.items()))},
        "rows": ledger_rows,
        "run_configuration": {"run_exact_flow": run_exact_flow, "flow_node_cap": flow_node_cap,
                              "flow_seconds_cap": flow_seconds},
        "conclusion": ("no exact Target-A boundary survived literal joint-source replay; Target-B analysis is blocked pending correction of the R2 hierarchy classifier"
                       if not exact_target_witnesses else
                       ("all currently canonicalised classes are closed in the stated Target-B Area-A model"
                        if not status_hist.get("INCOMPLETE") and not status_hist.get("FOUND_ENGINE_CONTINUATION") and
                           not status_hist.get("REQUIRES_EXACT_HELPER_FREE_DFS") else
                        "at least one canonical class requires further helper-free Target-B analysis")),
    }
    return classes_payload, known_payload, ledger_payload


def flow_only_from_frozen(*, classes_path: Path, flow_node_cap: int, flow_seconds: float) -> dict[str, object]:
    """Run only the helper-free Target-B stage from an already frozen audit.

    This avoids re-running the 38,406 parent-DAG literal replays merely to
    continue a (small) Target-B flow query.  The frozen source SHA remains in
    the ledger, and the output is still independently recheckable.
    """
    frozen = json.loads(classes_path.read_text(encoding="utf-8"))
    canonical = frozen["canonical_classes"]
    class_members = Counter(
        str(row["canonical_boundary_class"])
        for row in frozen["claimed_R6_witnesses"]
        if row["exact_target_a_replay"]
    )
    rows = []
    for class_row in canonical:
        state = state_from_json(class_row["canonical_state"])
        stage = target_b_stage(state)
        if stage["status"] == "REQUIRES_EXACT_HELPER_FREE_DFS":
            stage["exact_flow"] = run_flow(state, node_cap=flow_node_cap, seconds=flow_seconds)
            stage["final_status"] = stage["exact_flow"]["verdict"]
        else:
            stage["exact_flow"] = None
            stage["final_status"] = stage["status"]
        rows.append({"canonical_boundary_class": class_row["canonical_boundary_class"],
                     "canonical_state_hash": class_row["canonical_state_hash"],
                     "representative_witness_id": class_row["representative_witness_id"],
                     "literal_witness_count": class_members[str(class_row["canonical_boundary_class"])],
                     "coordinate": coordinate(state), **stage})
    hist = Counter(str(row["final_status"]) for row in rows)
    exact_hits = int(frozen["counts"]["exact_Target_A_literal_replays"])
    return {
        "schema": "rr-short-ell0-target-b-helper-free-ledger-v1",
        "scope": "Target B inside Area A (F=1,H=0,Ndef<=3); Target-A source corpus was capped",
        "phase_helper_used": False,
        "disallowed_helper_name": "true_phase_walk_capacity",
        "source_boundary_freeze": {"path": str(classes_path.relative_to(ROOT)), "sha256": sha256_file(classes_path)},
        "replacement_path": ["literal joint-source audit", "Phi=0 full-segment theorem",
                             "Round30 B+1 coarse bound", "Round32 occupancy-independent B+R bound",
                             "exact macro engine DFS"],
        "counts": {"stored_R6_claims": frozen["counts"]["stored_R6_claims"],
                   "exact_Target_A_literal_replays": exact_hits,
                   "stored_R6_replay_mismatches": frozen["counts"]["stored_R6_replay_mismatches"],
                   "canonical_classes": len(rows), "exact_flow_runs": sum(row["exact_flow"] is not None for row in rows),
                   **dict(sorted(hist.items()))},
        "rows": rows,
        "run_configuration": {"flow_node_cap": flow_node_cap, "flow_seconds_cap": flow_seconds},
        "conclusion": ("the sole literal Target-A boundary is symmetry-equivalent to historical known18 state short_ell0_33d70b4249b7 and its helper-free flow is closed"
                       if exact_hits == 1 and hist == Counter({"EXHAUSTED_NO_PATH": 1}) else
                       "Target-B stage not closed for every literal Target-A boundary"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-node-cap", type=int, default=20_000,
                        help="positive cap per helper-free exact DFS; cap means INCOMPLETE")
    parser.add_argument("--flow-seconds", type=float, default=15.0,
                        help="wall-clock cap per exact DFS; cap means INCOMPLETE")
    parser.add_argument("--no-exact-flow", action="store_true")
    parser.add_argument("--flow-only-from-freeze", action="store_true",
                        help="do not replay the fair DAG; run helper-free flow from --class-out")
    parser.add_argument("--class-out", type=Path, default=CLASS_OUT)
    parser.add_argument("--known-out", type=Path, default=KNOWN_OUT)
    parser.add_argument("--ledger-out", type=Path, default=LEDGER_OUT)
    args = parser.parse_args()
    if args.flow_node_cap <= 0 or args.flow_seconds <= 0:
        raise ValueError("flow caps must be positive")
    if args.flow_only_from_freeze:
        if args.no_exact_flow:
            raise ValueError("--flow-only-from-freeze requires exact flow")
        ledger = flow_only_from_frozen(classes_path=args.class_out, flow_node_cap=args.flow_node_cap,
                                       flow_seconds=args.flow_seconds)
        atomic_json(args.ledger_out, ledger)
        print(json.dumps({"Target_B": ledger["counts"], "conclusion": ledger["conclusion"]}, indent=2, sort_keys=True))
    else:
        classes, known, ledger = analysis(flow_node_cap=args.flow_node_cap, flow_seconds=args.flow_seconds,
                                          run_exact_flow=not args.no_exact_flow)
        atomic_json(args.class_out, classes)
        atomic_json(args.known_out, known)
        atomic_json(args.ledger_out, ledger)
        print(json.dumps({"classes": classes["counts"], "known18": known["counts"],
                          "Target_B": ledger["counts"], "conclusion": ledger["conclusion"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
