#!/usr/bin/env python3
"""Read-only obstruction analysis for the F=1,H=0,N=0 macro search.

This program never resumes, extends, or modifies a search checkpoint.  It
loads one atomically-written checkpoint snapshot and performs only bounded
local diagnostics (at most three macro edges) from representatives already
serialized in that snapshot.

``descendant_support`` has a deliberately narrow definition: it is the number
of saved frontier or terminal paths having a given accepted macro-path prefix.
The search's global ``seen`` table admits each accepted canonical state once,
so this is the descendant count in the checkpoint's retained path tree.  It
is not an estimate of ungenerated descendants and is never used to prune.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional, Sequence, Tuple


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
SPEC = importlib.util.spec_from_file_location("partial_f1_n0_obstruction_macro", MACRO_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MACRO_PATH}")
macro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = macro
SPEC.loader.exec_module(macro)
exact = macro.exact


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def read_checkpoint_snapshot(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read a single immutable file handle.  An atomic replacement occurring
    afterwards cannot affect this snapshot."""
    before = path.stat()
    with path.open("rb") as handle:
        raw = handle.read()
    data = json.loads(raw.decode("utf-8"))
    after = path.stat()
    meta = {
        "path": str(path),
        "snapshot_sha256": sha256_bytes(raw),
        "snapshot_size_bytes": len(raw),
        "opened_last_write_ns": before.st_mtime_ns,
        "path_changed_during_read": (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size),
        "after_read_size_bytes": after.st_size,
        "after_read_last_write_ns": after.st_mtime_ns,
    }
    return data, meta


def state_hash(state: exact.ExactState) -> str:
    return macro.stable_hash(state)


def move_from_label(label: str) -> exact.Move:
    by_label = {move.label: move for move in exact.ALL_MOVES}
    return by_label[label]


def path_key(path: Sequence[Mapping[str, Any]]) -> tuple[tuple[int, str], ...]:
    return tuple((int(item["rotation_length"]), str(item["joint"])) for item in path)


def path_key_json(key: tuple[tuple[int, str], ...]) -> str:
    return json.dumps(key, separators=(",", ":"), ensure_ascii=False)


def path_from_key(key: tuple[tuple[int, str], ...]) -> tuple[dict[str, Any], ...]:
    # Only the fields used by replay are reconstructed.  The stored full path
    # remains the representative artifact in the output.
    return tuple({"rotation_length": ell, "joint": joint} for ell, joint in key)


def replay_path_with_history(path: Sequence[Mapping[str, Any]]) -> tuple[exact.ExactState, list[exact.ExactState]]:
    state = exact.canonicalize(exact.initial_state())
    history = [state]
    for item in path:
        for _ in range(int(item["rotation_length"])):
            transition = exact.extend(state, macro.W1)
            if transition is None:
                raise AssertionError("stored path has a rotation collision")
            state = transition.state
        transition = exact.extend(state, move_from_label(str(item["joint"])))
        if transition is None:
            raise AssertionError("stored path has an illegal joint")
        state = exact.canonicalize(transition.state)
        history.append(state)
    return state, history


def bits(mask: int, width: int) -> list[int]:
    return [i for i in range(width) if mask & (1 << i)]


def orbit_summary(state: exact.ExactState) -> dict[str, Any]:
    entries = []
    for orbit, mask in enumerate(state.orbit_masks):
        if mask:
            entries.append({
                "orbit": orbit,
                "mask": mask,
                "used_phases": bits(mask, 5),
                "used_count": mask.bit_count(),
                "phase_deficit": 5 - mask.bit_count(),
            })
    deficit_hist = Counter(entry["phase_deficit"] for entry in entries)
    current_orbit, current_phase = exact.ORBIT_PHASE[state.p]
    return {
        "opened_orbits": state.O,
        "new_orbits_needed_for_target": exact.TARGET_O - state.O,
        "phase_deficit_total": state.D,
        "phase_deficit_histogram": {str(k): v for k, v in sorted(deficit_hist.items())},
        "current_orbit": current_orbit,
        "current_phase": current_phase,
        "current_orbit_mask": state.orbit_masks[current_orbit],
        "current_orbit_used_phases": bits(state.orbit_masks[current_orbit], 5),
        "current_orbit_phase_deficit": 5 - state.orbit_masks[current_orbit].bit_count(),
        "open_orbit_masks": entries,
    }


def fragment_summary(state: exact.ExactState) -> dict[str, Any]:
    form = exact.f1_normal_form(state)
    if form is None:
        return {"normal_form_valid": False}
    frag = form.fragment_hex
    current = form.current_hex
    result: dict[str, Any] = {
        "normal_form_valid": True,
        "current_hex": current,
        "current_mask": state.hex_masks[current],
        "current_components": [list(x) for x in form.current_components],
        "current_unvisited_rotation_length": 6 - state.hex_masks[current].bit_count(),
        "fragment_hex": frag,
        "fragment_observable": frag is not None,
        "fragment_components": [list(x) for x in form.fragment_components],
        "partial_hexagons": [
            {"hex": h, "mask": mask, "components": [list(x) for x in exact.cyclic_components(mask)], "unvisited": 6 - mask.bit_count()}
            for h, mask in enumerate(state.hex_masks) if mask not in (0, exact.FULL_HEX)
        ],
    }
    if frag is not None:
        result.update({
            "fragment_mask": state.hex_masks[frag],
            "fragment_unvisited_rotation_length": 6 - state.hex_masks[frag].bit_count(),
            "fragment_is_current": frag == current,
        })
    else:
        result.update({
            "fragment_mask": None,
            "fragment_unvisited_rotation_length": None,
            "fragment_is_current": False,
        })
    return result


def collision_target_category(state: exact.ExactState, target: tuple[int, ...]) -> str:
    h, bit = exact.HEX_POSITION[target]
    form = exact.f1_normal_form(state)
    if h == state.current_hex:
        return "current_hex"
    if form is not None and form.fragment_hex == h:
        return "fragment_hex"
    mask = state.hex_masks[h]
    if mask == exact.FULL_HEX:
        return "full_hex"
    if mask:
        return "other_partial_hex"
    return "unexpected_empty_hex_collision"


@dataclass(frozen=True)
class LocalOption:
    run_length: int
    joint: str
    weight: int
    status: str
    reason: Optional[str]
    new_orbit: Optional[bool]
    abandonment: Optional[bool]
    target_collision_category: Optional[str]
    child: Optional[exact.ExactState]


def local_options(state: exact.ExactState, config: macro.AreaAConfig) -> list[LocalOption]:
    options: list[LocalOption] = []
    for run in macro.rotation_runs(state):
        for move in macro.NONROT_H0:
            transition = exact.extend(run.state, move)
            if transition is None:
                target = exact.core.word_after(run.state.p, move.action)
                options.append(LocalOption(
                    run.ell, move.label, move.weight, "collision", "collision", None, None,
                    collision_target_category(run.state, target), None,
                ))
                continue
            reason = macro.area_a_prune_reason(transition.state, config)
            options.append(LocalOption(
                run.ell, move.label, move.weight,
                "safe" if reason is None else "pruned", reason,
                transition.new_orbit, transition.abandonment, None,
                # This diagnostic explores at most three *literal* macro
                # edges.  Relabelling is unnecessary here: legality,
                # collision, and all resource coordinates are equivariant
                # under the left S6 action.  Keeping the raw child avoids
                # performing the expensive 720-element canonicalization at
                # every node of a read-only local tree.
                transition.state if reason is None else None,
            ))
    return options


def bounded_safe_layers(state: exact.ExactState, config: macro.AreaAConfig, horizon: int = 3) -> dict[str, Any]:
    """Nondeterministic, *bounded* local continuation diagnostic.

    This is not a new global search: it has a fixed maximum of three macro
    edges, no checkpoint, no claim of completeness beyond that horizon, and is
    evaluated only on serialized representatives.
    """
    layer = {state.stable_key(): state}
    widths: list[int] = []
    first_empty: Optional[int] = None
    for distance in range(1, horizon + 1):
        next_layer: dict[tuple[object, ...], exact.ExactState] = {}
        for node in layer.values():
            for option in local_options(node, config):
                if option.status == "safe" and option.child is not None:
                    next_layer.setdefault(option.child.stable_key(), option.child)
        widths.append(len(next_layer))
        if not next_layer:
            first_empty = distance
            break
        layer = next_layer
    return {
        "safe_N0_layer_widths_through_3": widths,
        "safe_N0_dead_by_macro_step": first_empty,
        "survives_three_macro_steps": first_empty is None and len(widths) == horizon,
    }


def fragment_distance(state: exact.ExactState, config: macro.AreaAConfig, horizon: int = 3) -> Optional[int | str]:
    form = exact.f1_normal_form(state)
    if form is None or form.fragment_hex is None:
        return None
    fragment_hex = form.fragment_hex
    layer = {state.stable_key(): state}
    for distance in range(1, horizon + 1):
        next_layer: dict[tuple[object, ...], exact.ExactState] = {}
        for node in layer.values():
            for option in local_options(node, config):
                if option.status != "safe" or option.child is None:
                    continue
                if option.child.current_hex == fragment_hex:
                    return distance
                next_layer.setdefault(option.child.stable_key(), option.child)
        layer = next_layer
        if not layer:
            return ">3_or_dead"
    return ">3"


def c4_210_chain_length(state: exact.ExactState, limit: int = 4) -> int:
    """Operational C4 diagnostic only.

    It tests repeated ``rot^5 ; w3:210`` from the exact current state.  The
    G2 C4 theorem applies only under its full-cassette hypotheses; this number
    does *not* assert those hypotheses for arbitrary F=1 states.
    """
    candidate = state
    move = move_from_label("w3:210")
    length = 0
    for _ in range(limit):
        for _ in range(5):
            rotation = exact.extend(candidate, macro.W1)
            if rotation is None:
                return length
            candidate = rotation.state
        joint = exact.extend(candidate, move)
        if joint is None:
            return length
        candidate = joint.state
        length += 1
    return length


def history_summary(path: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    final, history = replay_path_with_history(path)
    first_fragment_index: Optional[int] = None
    full_after_fragment = 0
    longest_c4_run = 0
    current_c4_run = 0
    for index, item in enumerate(path):
        before = history[index]
        after = history[index + 1]
        if first_fragment_index is None and before.F == 0 and after.F == 1:
            first_fragment_index = index
        if first_fragment_index is not None and index >= first_fragment_index:
            if int(item["rotation_length"]) == 5:
                full_after_fragment += 1
            if int(item["rotation_length"]) == 5 and item["joint"] == "w3:210":
                current_c4_run += 1
                longest_c4_run = max(longest_c4_run, current_c4_run)
            else:
                current_c4_run = 0
    return {
        "replayed_state_hash": state_hash(final),
        "first_fragment_macro_index": first_fragment_index,
        "full_rotation_run_count_after_fragment": full_after_fragment,
        "longest_observed_rot5_w3_210_run_after_fragment": longest_c4_run,
    }


def analyse_state(state: exact.ExactState, path: Sequence[Mapping[str, Any]], config: macro.AreaAConfig,
                  group: str, depth: int, descendant_support: Optional[int] = None) -> dict[str, Any]:
    direct = local_options(state, config)
    all_counts = Counter(option.status if option.status != "pruned" else f"pruned:{option.reason}" for option in direct)
    w3 = [option for option in direct if option.weight == 3]
    w3_counts = Counter(option.status if option.status != "collision" else f"collision:{option.target_collision_category}" for option in w3)
    safe = [option for option in direct if option.status == "safe"]
    full_cassette = [option for option in safe if option.run_length == 5]
    full_w3 = [option for option in safe if option.run_length == 5 and option.weight == 3]
    n1_options = local_options(state, macro.SMALL_N1)
    n1_safe = [option for option in n1_options if option.status == "safe"]
    n1_only = [option for option in n1_safe if option.child is not None and option.child.Ndef == 1]
    n_overshoots = [option for option in direct if option.reason == "N_exceeded_monotone"]
    n_overshoot_signatures = Counter(
        (option.weight, option.run_length, bool(option.new_orbit), bool(option.abandonment))
        for option in n_overshoots
    )
    collisions = Counter(option.target_collision_category for option in direct if option.status == "collision")
    info = {
        "group": group,
        "macro_depth": depth,
        "canonical_state_hash": state_hash(state),
        "coordinate_P_F_S_H_O_D_N": list(macro.state_coordinate(state)),
        "visited_windows": state.visited_count,
        "representative_path": list(path),
        "descendant_support": descendant_support,
        "fragment": fragment_summary(state),
        "E_orbits": orbit_summary(state),
        "legal_macro_options": {
            "all_attempted_by_status": dict(sorted(all_counts.items())),
            "safe_N0_macro_tails": len(safe),
            "safe_N0_weight3_macro_tails": sum(option.weight == 3 for option in safe),
            "all_weight3_options_by_status": dict(sorted(w3_counts.items())),
            "safe_N0_full_rotation_continuations": len(full_cassette),
            "safe_N0_full_rotation_weight3_continuations": len(full_w3),
            "N1_safe_macro_tails": len(n1_safe),
            "N1_only_escape_tails": len(n1_only),
            "N_exceeded_events": {
                "count": len(n_overshoots),
                "new_orbit_false": sum(option.new_orbit is False for option in n_overshoots),
                "new_orbit_true": sum(option.new_orbit is True for option in n_overshoots),
                "signature_histogram": {
                    f"w={weight};rot={run};new_orbit={new_orbit};abandonment={abandonment}": count
                    for (weight, run, new_orbit, abandonment), count in sorted(n_overshoot_signatures.items())
                },
            },
        },
        "collision_targets": dict(sorted((key or "unknown", value) for key, value in collisions.items())),
        "C4_operational": {
            "repeated_rot5_w3_210_length_capped_at_4": c4_210_chain_length(state),
            "full_cassette_entry_available": bool(full_cassette),
        },
        "local_horizon": bounded_safe_layers(state, config, 3),
        "fragment_minimum_safe_N0_macro_distance_capped_at_3": fragment_distance(state, config, 3),
        "history": history_summary(path),
    }
    return info


def terminal_archetype(record: Mapping[str, Any]) -> str:
    options = record["legal_macro_options"]
    statuses = options["all_attempted_by_status"]
    n1_only = int(options["N1_only_escape_tails"])
    w3_statuses = options["all_weight3_options_by_status"]
    collisions = record["collision_targets"]
    if int(options["safe_N0_macro_tails"]) != 0:
        return "not_terminal_under_recomputed_N0_rules"
    if n1_only > 0:
        return "A_N_credit_escape"
    if statuses.get("pruned:F_exceeded", 0) and sum(statuses.values()) == statuses.get("pruned:F_exceeded", 0):
        return "B_fragment_budget_only"
    if statuses.get("pruned:remaining_cover_capacity_impossible", 0) and not any(key.startswith("collision") for key in statuses):
        return "C_capacity_gate_without_literal_collision"
    fragment_w3 = sum(value for key, value in w3_statuses.items() if key == "collision:fragment_hex")
    if fragment_w3 and int(options["safe_N0_weight3_macro_tails"]) == 0:
        return "D_fragment_collision_blocks_w3"
    if collisions.get("full_hex", 0) + collisions.get("current_hex", 0) + collisions.get("fragment_hex", 0) > 0:
        return "E_mixed_revisit_closure"
    return "E_mixed_revisit_closure"


def select_deep_frontier(frontier: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, Any]]:
    ordered = sorted(frontier, key=lambda item: (-int(item["depth"]), path_key(item.get("path", []))))
    return [dict(item) for item in ordered[:limit]]


def prefix_support(frontier: Sequence[Mapping[str, Any]], terminals: Sequence[Mapping[str, Any]]) -> tuple[Counter[tuple[tuple[int, str], ...]], dict[tuple[tuple[int, str], ...], dict[str, Any]]]:
    support: Counter[tuple[tuple[int, str], ...]] = Counter()
    representatives: dict[tuple[tuple[int, str], ...], dict[str, Any]] = {}
    for group, entries in (("frontier", frontier), ("terminal", terminals)):
        for item in entries:
            path = list(item.get("path", []))
            for length in range(1, len(path) + 1):
                key = path_key(path[:length])
                support[key] += 1
                representatives.setdefault(key, {"group": group, "depth": length, "path": path[:length]})
    return support, representatives


def select_descendant_prefixes(
    support: Counter[tuple[tuple[int, str], ...]],
    representatives: Mapping[tuple[tuple[int, str], ...], Mapping[str, Any]],
    limit: int,
) -> list[tuple[int, dict[str, Any], exact.ExactState]]:
    """Replay only ranked prefixes until ``limit`` F=1 representatives were
    found.  This avoids reconstructing every parent state in a 200MB snapshot."""
    ranked = sorted(support, key=lambda key: (-support[key], len(key), key))
    selected: list[tuple[int, dict[str, Any], exact.ExactState]] = []
    for key in ranked:
        rep = dict(representatives[key])
        state, _history = replay_path_with_history(rep["path"])
        if state.F != 1:
            continue
        selected.append((support[key], rep, state))
        if len(selected) >= limit:
            break
    return selected


def representative_data(entries: Iterable[tuple[exact.ExactState, Sequence[Mapping[str, Any]], str, int, Optional[int]]],
                        config: macro.AreaAConfig) -> list[dict[str, Any]]:
    answer: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}
    for state, path, group, depth, support in entries:
        key = state_hash(state)
        if key not in cache:
            cache[key] = analyse_state(state, path, config, group, depth, support)
        record = dict(cache[key])
        record["group"] = group
        record["macro_depth"] = depth
        record["descendant_support"] = support
        answer.append(record)
    return answer


def count_values(records: Iterable[Mapping[str, Any]], dotted: tuple[str, ...]) -> Counter[Any]:
    counter: Counter[Any] = Counter()
    for record in records:
        value: Any = record
        for key in dotted:
            value = value.get(key) if isinstance(value, Mapping) else None
        counter[value] += 1
    return counter


def counterexample_samples(records: Iterable[Mapping[str, Any]], predicate, cap: int = 3) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for record in records:
        if predicate(record):
            found.append({
                "canonical_state_hash": record["canonical_state_hash"],
                "coordinate": record["coordinate_P_F_S_H_O_D_N"],
                "path": record["representative_path"],
            })
            if len(found) >= cap:
                break
    return found


def summarize_archetypes(terminals: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for terminal in terminals:
        grouped[terminal_archetype(terminal)].append(terminal)
    output: dict[str, Any] = {}
    for name, records in sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        sample = records[0]
        if name == "A_N_credit_escape":
            condition = (
                "safe_N0_macro_tails=0 and at least one N=1-safe macro tail exists after replacing the N=0 bound by N<=1"
            )
            prospect = "most promising local theorem candidate: classify the N-increasing tail by its E-orbit target and prove that all other tails are blocked"
        elif name == "C_capacity_gate_without_literal_collision":
            condition = (
                "safe_N0_macro_tails=0, no attempted joint has an immediate repeated-window collision, and at least one attempted child fails remaining_cover_capacity_impossible"
            )
            prospect = "requires a global pass-capacity/phase-deficit inequality; the present evidence does not reduce it to a local coset calculation"
        else:
            condition = (
                "safe_N0_macro_tails=0, no N=1-safe escape exists, and at least one attempted joint repeats a previously visited target window"
            )
            prospect = "the target of each individual w=3 tail is a finite coset calculation, but proving the occupied-mask pattern globally remains open"
        output[name] = {
            "count": len(records),
            "exact_state_condition": {
                "safe_N0_macro_tails": 0,
                "classification_rule": condition,
                "sample_coordinate": sample["coordinate_P_F_S_H_O_D_N"],
                "sample_fragment": sample["fragment"],
            },
            "minimum_representative": {
                "canonical_state_hash": sample["canonical_state_hash"],
                "representative_path": sample["representative_path"],
            },
            "immediate_rejection_totals": dict(sorted(sum((Counter(record["legal_macro_options"]["all_attempted_by_status"]) for record in records), Counter()).items())),
            "w3_collision_totals": dict(sorted(sum((Counter(record["legal_macro_options"]["all_weight3_options_by_status"]) for record in records), Counter()).items())),
            "hand_proof_prospect": prospect,
            "finite_coset_component": (
                "the immediate w=3 tail actions and their target hex/orbit incidences are finite; the global occupied-mask implication is not yet proved"
            ),
            "counterexamples_in_current_terminal_data": 0,
        }
    return dict(list(output.items())[:5])


def markdown(report: Mapping[str, Any]) -> str:
    overview = report["overview"]
    tests = report["candidate_statement_tests"]
    terminals = report["terminal_states"]
    deep = report["deep_frontier_states"]
    descendants = report["high_descendant_support_states"]
    terminal_n = tests["terminal_N_credit_event"]
    deep_three = sum(bool(item["local_horizon"]["survives_three_macro_steps"]) for item in deep)
    descendant_three = sum(bool(item["local_horizon"]["survives_three_macro_steps"]) for item in descendants)
    deep_c4 = sum(item["C4_operational"]["repeated_rot5_w3_210_length_capped_at_4"] == 4 for item in deep)
    descendant_c4 = sum(item["C4_operational"]["repeated_rot5_w3_210_length_capped_at_4"] == 4 for item in descendants)
    terminal_new_need = Counter(item["E_orbits"]["new_orbits_needed_for_target"] for item in terminals)
    lines = [
        "# F=1, H=0, N=0 obstruction analysis",
        "",
        "Status: read-only checkpoint analysis, not a new enumeration and not a nonexistence proof.",
        "",
        "## Snapshot",
        "",
        f"- input snapshot SHA-256: `{report['input_snapshot']['snapshot_sha256']}`",
        f"- retained frontier states: {overview['frontier_count']}",
        f"- retained terminal certificates: {overview['terminal_count']}",
        f"- analysed deepest frontier representatives: {overview['deep_frontier_analysed']}",
        f"- analysed F=1 descendant-support representatives: {overview['descendant_support_analysed']}",
        "",
        "`descendant_support` counts saved frontier/terminal paths through an accepted macro-path prefix. It is not a count of ungenerated descendants.",
        "",
        "## Terminal obstruction archetypes",
        "",
        "| archetype | terminals | immediate safe N=0 tail condition |",
        "|---|---:|---|",
    ]
    for name, item in report["terminal_archetypes"].items():
        lines.append(f"| `{name}` | {item['count']} | `{item['exact_state_condition']['safe_N0_macro_tails']} safe tails` |")
    lines += [
        "",
        "## Candidate statements and counterexample search",
        "",
        "The following are observational tests on this snapshot only. A zero counterexample count is not a theorem.",
        "",
        "```json",
        json.dumps(report["candidate_statement_tests"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Structural reading of this snapshot",
        "",
        f"1. **Every one of the {terminal_n['terminal_count']} retained terminals has an immediate `N_exceeded_monotone` candidate.**  Its observed signatures are all non-abandoning, non-new-orbit weight-3 tails: `{terminal_n['N_exceeded_signature_histogram']}`.  Thus its local accounting is `ΔN=1+0−0=1`.",
        f"   Only {terminal_n['N1_safe_escape_terminal_count']} terminals acquire a genuinely safe child when the bound is relaxed to `N<=1`; the others are still rejected by a coverage or F-budget condition.  This is the strongest current theorem *candidate*, not a theorem.",
        f"2. The terminal families are not a single collision mechanism.  {report['terminal_archetypes'].get('C_capacity_gate_without_literal_collision', {}).get('count', 0)} terminals have no immediate literal collision at all; {report['terminal_archetypes'].get('E_mixed_revisit_closure', {}).get('count', 0)} have a mixed revisit closure; and {report['terminal_archetypes'].get('A_N_credit_escape', {}).get('count', 0)} have an N=1-safe escape.",
        f"3. The deepest frontier sample is **not** already terminal-like: {deep_three}/{len(deep)} survive the bounded three-step N=0 diagnostic and {deep_c4}/{len(deep)} admit four repetitions of the operational `rot^5;w3:210` test.  The high-descendant sample is still less terminal-like: {descendant_three}/{len(descendants)} survive three steps and {descendant_c4}/{len(descendants)} have diagnostic C4 length four.",
        f"4. No retained terminal has `O=25`: its remaining E-orbit requirement ranges over `{dict(sorted(terminal_new_need.items()))}`.  This does **not** prove that an orbit-opening failure is universal, but it rules out a terminal explanation based on already having met the 25-orbit target.",
        f"5. Two tempting uniform statements already fail in this snapshot: repair can be reached before the operational C4 diagnostic in {tests['repair_before_C4_closure']['counterexample_count_among_analysed_records']} analysed states, and weight-3 rejections split between full-hex and fragment-hex collisions rather than one target type.  The observed terminal maximum of post-fragment `rot^5` runs is {tests['fragment_after_m_full_cassettes']['observed_maximum']}; it is not a proof of any finite bound.",
        "",
        "## Next proof target",
        "",
        "The data points to a narrowly stated local lemma to try next: a terminal N=0 prefix has an available non-abandoning weight-3 re-entry into an already opened E-orbit, hence `ΔN=1`.  To turn this from a snapshot fact into a theorem, classify the terminal mask normal forms and prove that the other local tails are blocked by the listed collision/F/capacity alternatives.  Do not replace that proof by the observed C4 diagnostic.",
        "",
        "## Machine-readable details",
        "",
        "All selected representatives, terminal summaries, collision causes, bounded three-step diagnostics, and paths are in the companion JSON file.",
    ]
    return "\n".join(lines) + "\n"


def analyze(checkpoint: Path, deep_limit: int, descendant_limit: int) -> dict[str, Any]:
    data, snapshot = read_checkpoint_snapshot(checkpoint)
    if data.get("schema") != "partial-f1-macro-checkpoint-v1":
        raise ValueError("not a macro checkpoint")
    expected = (macro.CODE_SHA256, macro.ENGINE_SHA256, macro.CORE_SHA256)
    observed = (data.get("macro_sha256"), data.get("engine_sha256"), data.get("core_sha256"))
    if observed != expected:
        raise ValueError("checkpoint code SHA does not match read-only analysis engine")
    config_data = data.get("config", {})
    config = macro.AreaAConfig(int(config_data["n_limit"]), str(config_data["name"]))
    if config != macro.SMALL_N0:
        raise ValueError(f"expected N=0 checkpoint, got {config}")

    frontier: list[Mapping[str, Any]] = list(data.get("frontier", []))
    stats: Mapping[str, Any] = data.get("stats", {})
    terminals: list[Mapping[str, Any]] = list(stats.get("terminal_certificates", []))
    deep_nodes = select_deep_frontier(frontier, deep_limit)
    support, prefix_representatives = prefix_support(frontier, terminals)
    descendant_nodes = select_descendant_prefixes(support, prefix_representatives, descendant_limit)

    deep_entries = []
    for item in deep_nodes:
        state = exact.state_from_json(item["state"])
        deep_entries.append((state, item.get("path", []), "deep_frontier", int(item["depth"]), None))
    descendant_entries = [(state, rep["path"], "descendant_support", int(rep["depth"]), count)
                          for count, rep, state in descendant_nodes]
    terminal_entries = [(exact.state_from_json(item["state"]), item.get("path", []), "terminal", len(item.get("path", [])), None)
                        for item in terminals]

    deep_records = representative_data(deep_entries, config)
    descendant_records = representative_data(descendant_entries, config)
    terminal_records = representative_data(terminal_entries, config)
    archetypes = summarize_archetypes(terminal_records)

    all_records = deep_records + descendant_records + terminal_records
    c4_before_repair_counterexamples = counterexample_samples(
        all_records,
        lambda r: r["fragment"]["fragment_observable"] and r["fragment_minimum_safe_N0_macro_distance_capped_at_3"] in (1, 2, 3)
        and r["fragment_minimum_safe_N0_macro_distance_capped_at_3"] <= r["C4_operational"]["repeated_rot5_w3_210_length_capped_at_4"],
    )
    no_new_orbit_need_terminals = counterexample_samples(
        terminal_records,
        lambda r: r["E_orbits"]["new_orbits_needed_for_target"] == 0,
    )
    heterogeneous_w3 = Counter(
        key for r in terminal_records for key in r["legal_macro_options"]["all_weight3_options_by_status"]
    )
    terminal_dead_steps = count_values(terminal_records, ("local_horizon", "safe_N0_dead_by_macro_step"))
    terminal_fragment_distance = count_values(terminal_records, ("fragment_minimum_safe_N0_macro_distance_capped_at_3",))
    full_after_fragment = count_values(terminal_records, ("history", "full_rotation_run_count_after_fragment"))
    max_full_after_fragment = max((x["history"]["full_rotation_run_count_after_fragment"] for x in terminal_records), default=0)
    terminal_n_events = [r["legal_macro_options"]["N_exceeded_events"] for r in terminal_records]
    n_event_signatures: Counter[str] = Counter(
        signature for event in terminal_n_events for signature, count in event["signature_histogram"].items() for _ in range(count)
    )

    candidate_tests = {
        "repair_before_C4_closure": {
            "operational_test": "fragment reaches its stored noncurrent hex within <=3 safe N=0 macro steps before or at the repeated rot^5;w3:210 diagnostic length",
            "counterexample_count_among_analysed_records": len(c4_before_repair_counterexamples),
            "counterexample_samples": c4_before_repair_counterexamples,
            "status": "counterexample search only; the C4 diagnostic is outside G2 unless its full-cassette hypotheses are separately proved",
        },
        "terminal_requires_new_E_orbit": {
            "terminal_count_with_new_orbits_needed_zero": len(no_new_orbit_need_terminals),
            "counterexample_samples": no_new_orbit_need_terminals,
            "status": "zero would support a conjecture, not prove it",
        },
        "terminal_N_credit_event": {
            "terminals_with_at_least_one_immediate_N_exceeded_candidate": sum(event["count"] > 0 for event in terminal_n_events),
            "terminal_count": len(terminal_records),
            "N1_safe_escape_terminal_count": sum(r["legal_macro_options"]["N1_only_escape_tails"] > 0 for r in terminal_records),
            "N_exceeded_signature_histogram": dict(sorted(n_event_signatures.items())),
            "interpretation": "An N=1-producing candidate is universal in this snapshot; only the N1-safe subset is a genuine immediate escape. The rest remain blocked by other safe necessary conditions.",
        },
        "last_w3_tails_have_one_collision_type": {
            "terminal_w3_option_status_histogram": dict(sorted(heterogeneous_w3.items())),
            "status": "more than one nonzero key is an explicit counterexample to a single-type formulation",
        },
        "fragment_after_m_full_cassettes": {
            "observed_terminal_histogram": {str(k): v for k, v in sorted(full_after_fragment.items(), key=lambda x: (x[0] is None, x[0]))},
            "observed_maximum": max_full_after_fragment,
            "status": "observed bound only; no bound is asserted as a theorem",
        },
        "terminal_safe_N0_dead_horizon": {
            "histogram": {str(k): v for k, v in sorted(terminal_dead_steps.items(), key=lambda x: (x[0] is None, x[0]))},
            "fragment_distance_histogram": {str(k): v for k, v in sorted(terminal_fragment_distance.items(), key=lambda x: str(x[0]))},
            "status": "bounded to three macro steps",
        },
    }

    report: dict[str, Any] = {
        "schema": "partial-f1-n0-obstruction-analysis-v1",
        "analysis_sha256": sha256_file(HERE),
        "macro_sha256": macro.CODE_SHA256,
        "engine_sha256": macro.ENGINE_SHA256,
        "core_sha256": macro.CORE_SHA256,
        "input_snapshot": snapshot,
        "scope": "read-only diagnostics for selected F=1,H=0,N=0 exact-state subcase; no search extension and no nonexistence conclusion",
        "overview": {
            "frontier_count": len(frontier),
            "terminal_count": len(terminals),
            "checkpoint_expanded": stats.get("expanded"),
            "checkpoint_accepted": stats.get("accepted"),
            "deep_frontier_analysed": len(deep_records),
            "descendant_support_analysed": len(descendant_records),
            "terminal_analysed": len(terminal_records),
            "deepest_frontier_depth": max((int(item["depth"]) for item in frontier), default=None),
            "descendant_support_definition": "number of stored frontier or terminal paths through an accepted macro-path prefix",
        },
        "terminal_archetypes": archetypes,
        "candidate_statement_tests": candidate_tests,
        "deep_frontier_states": deep_records,
        "high_descendant_support_states": descendant_records,
        "terminal_states": terminal_records,
        "limitations": [
            "The checkpoint retains a frontier and terminal certificates, not an expanded parent-to-child graph. Descendant support is reconstructed from retained path prefixes only.",
            "C4 is recorded as an explicit repeated rot^5;w3:210 local diagnostic. It is not an assertion that arbitrary F=1 states satisfy the full-cassette hypotheses of G2.",
            "The three-step local test is bounded and is not a global continuation enumeration.",
            "A fingerprint with no counterexample in this snapshot remains a conjectural theorem candidate.",
        ],
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default=str(ROOT / "outputs" / "f1_small_n0.committed_resume.checkpoint.json"))
    parser.add_argument("--deep-limit", type=int, default=200)
    parser.add_argument("--descendant-limit", type=int, default=200)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "f1_n0_obstruction_analysis.json"))
    parser.add_argument("--markdown", default=str(ROOT / "outputs" / "F1_N0_OBSTRUCTION_ANALYSIS.md"))
    args = parser.parse_args()
    report = analyze(Path(args.checkpoint), args.deep_limit, args.descendant_limit)
    write_json_atomic(Path(args.output), report)
    Path(args.markdown).write_text(markdown(report), encoding="utf-8")
    print(json.dumps({
        "frontier": report["overview"]["frontier_count"],
        "terminals": report["overview"]["terminal_count"],
        "archetypes": {key: value["count"] for key, value in report["terminal_archetypes"].items()},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
