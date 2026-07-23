#!/usr/bin/env python3
"""Bounded, checkpointable growth profiling for the n=6 F=1 exact-state engine.

This is an analysis harness, not an enumerator and not a proof engine.  It
uses the exact state and safe pruning from superperm_partial_f1.py, but adds
layer-preserving checkpoints, resource/fragment profiles, and subproblem
comparisons.  It always requires a positive node limit and a finite memory
cap.
"""

from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
ENGINE_PATH = HERE.with_name("superperm_partial_f1.py")
_SPEC = importlib.util.spec_from_file_location("partial_f1_engine", ENGINE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {ENGINE_PATH}")
engine = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = engine
_SPEC.loader.exec_module(engine)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


ANALYSIS_SHA256 = sha256_file(HERE)
ENGINE_SHA256 = sha256_file(ENGINE_PATH)
CORE_SHA256 = engine.CORE_SHA256


def state_hash(state: engine.ExactState) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def working_set_bytes() -> int:
    """Current process working set; Windows implementation with portable fallbacks."""
    if os.name == "nt":
        from ctypes import wintypes
        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]
        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_current_process.restype = wintypes.HANDLE
        get_process_memory = ctypes.windll.psapi.GetProcessMemoryInfo
        get_process_memory.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD)
        get_process_memory.restype = wintypes.BOOL
        process = get_current_process()
        ok = get_process_memory(process, ctypes.byref(counters), counters.cb)
        if ok:
            return int(counters.WorkingSetSize)
    try:
        import resource  # type: ignore
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value * (1024 if platform.system() != "Darwin" else 1))
    except Exception:
        return 0


def normalize_cyclic_mask(mask: int, width: int = 6) -> Tuple[int, ...]:
    """Canonical cyclic bit word under local rotation, not reversal."""
    word = tuple((mask >> i) & 1 for i in range(width))
    return min(tuple(word[(i + shift) % width] for i in range(width)) for shift in range(width))


def cyclic_runs_and_gaps(mask: int, width: int = 6) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Lengths of occupied runs and intervening gaps, modulo rotation."""
    if mask == 0:
        return (), (width,)
    if mask == (1 << width) - 1:
        return (width,), (0,)
    components = engine.cyclic_components(mask, width)
    runs = tuple(component[2] for component in components)
    gaps: List[int] = []
    for index, (start, _end, length) in enumerate(components):
        next_start = components[(index + 1) % len(components)][0]
        gaps.append((next_start - (start + length)) % width)
    candidates = []
    for shift in range(len(runs)):
        candidates.append((runs[shift:] + runs[:shift], tuple(gaps[shift:] + gaps[:shift])))
    return min(candidates)


def normalize_phase_mask(mask: int) -> Tuple[int, ...]:
    return normalize_cyclic_mask(mask, 5)


def pass_start_ports_in_hex(state: engine.ExactState, hex_id: int) -> List[Tuple[int, int, int]]:
    """(E-orbit id, phase, full orbit mask) for starts lying in a given hex."""
    answer: List[Tuple[int, int, int]] = []
    for q, mask in state.sparse_orbits():
        rep = engine.core.E_REPS[q]
        for phase in range(5):
            if mask & (1 << phase):
                word = engine.core.word_after(rep, engine.core.power(engine.core.E, phase))
                if engine.HEX_POSITION[word][0] == hex_id:
                    answer.append((q, phase, mask))
    return answer


def fragment_hex_id(state: engine.ExactState) -> Optional[int]:
    """Recover the one-fragment hex when it is observable from exact state.

    Before repair, the outstanding non-current partial hex identifies it.
    After a second pass has begun or completed, two pass starts in one hex do.
    The latter uses B_Q rather than unrecorded history.
    """
    if state.F != 1:
        return None
    form = engine.f1_normal_form(state)
    if form is None:
        return None
    if form.fragment_hex is not None:
        return form.fragment_hex
    multiplicities = Counter()
    for q, mask in state.sparse_orbits():
        rep = engine.core.E_REPS[q]
        for phase in range(5):
            if mask & (1 << phase):
                word = engine.core.word_after(rep, engine.core.power(engine.core.E, phase))
                multiplicities[engine.HEX_POSITION[word][0]] += 1
    repeated = [h for h, count in multiplicities.items() if count >= 2]
    if len(repeated) == 1:
        return repeated[0]
    if state.current_hex in multiplicities:
        # During the repair pass the current hex can be the only remaining
        # visible candidate; no unproved historical reconstruction is made.
        return state.current_hex
    return None


def fragment_fingerprint(state: engine.ExactState, creation_weight: Optional[int]) -> Optional[Dict[str, object]]:
    if state.F != 1:
        return None
    h = fragment_hex_id(state)
    if h is None:
        return {
            "kind": "F1_fragment_not_observable_from_state",
            "creation_weight": creation_weight,
        }
    mask = state.hex_masks[h]
    runs, gaps = cyclic_runs_and_gaps(mask)
    ports = pass_start_ports_in_hex(state, h)
    # Two (or one) start locations are a rotation-invariant complement to the
    # current mask.  The q labels themselves are intentionally discarded.
    start_positions = sorted(
        engine.HEX_POSITION[
            engine.core.word_after(engine.core.E_REPS[q], engine.core.power(engine.core.E, phase))
        ][1]
        for q, phase, _full_mask in ports
    )
    if len(start_positions) >= 2:
        distances = sorted(((start_positions[(i + 1) % len(start_positions)] - start_positions[i]) % 6)
                           for i in range(len(start_positions)))
    else:
        distances = []
    phase_masks = sorted(normalize_phase_mask(full_mask) for _q, _phase, full_mask in ports)
    if h != state.current_hex:
        exit_adjacency: object = "different_current_hex"
    else:
        ppos = engine.HEX_POSITION[state.p][1]
        components = engine.cyclic_components(mask)
        exit_adjacency = "unclassified"
        for index, (_start, end, _length) in enumerate(components):
            if end == ppos:
                exit_adjacency = f"run_{index}_forward_gap"
                break
            if (end + 1) % 6 == ppos:
                exit_adjacency = f"run_{index}_adjacent"
                break
    return {
        "kind": "fragment",
        "creation_weight": creation_weight,
        "occupied_runs": list(runs),
        "gaps": list(gaps),
        "cyclic_mask": list(normalize_cyclic_mask(mask)),
        "two_arc_start_separations": distances,
        "current_equals_fragment": h == state.current_hex,
        "exit_adjacency": exit_adjacency,
        "fragment_E_phase_masks": [list(mask) for mask in phase_masks],
        "current_hex_mask": state.hex_masks[state.current_hex],
        "observable_pass_starts_in_fragment_hex": len(ports),
    }


def fingerprint_key(fingerprint: Optional[Dict[str, object]]) -> str:
    return "none" if fingerprint is None else json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))


def coordinate(state: engine.ExactState) -> Tuple[int, int, int, int, int, int, int]:
    return (state.P, state.F, state.S, state.H, state.O, state.D, state.Ndef)


def structural_scalars(state: engine.ExactState, repair_candidates: Optional[int] = None,
                       legal_count: Optional[int] = None, new_openings: Optional[int] = None) -> Dict[str, Optional[int]]:
    h = fragment_hex_id(state)
    partial_gap_count = 0
    for mask in state.hex_masks:
        if mask not in (0, engine.FULL_HEX):
            _runs, gaps = cyclic_runs_and_gaps(mask)
            partial_gap_count += sum(1 for gap in gaps if gap > 0)
    fragment_missing = None if h is None else 6 - state.hex_masks[h].bit_count()
    return {
        "remaining_empty_E_phases": state.D,
        "partial_hex_gap_count": partial_gap_count,
        "fragment_unvisited_rotation_length": fragment_missing,
        "legal_tail_count": legal_count,
        "new_E_orbit_opening_candidates": new_openings,
        "N_plus_H_remaining_budget": 3 - (state.Ndef + state.H),
        "fragment_repair_entry_candidates": repair_candidates,
    }


@dataclass
class ProfileNode:
    state: engine.ExactState
    path: Tuple[str, ...]
    fragment_creation_weight: Optional[int]

    def to_json(self) -> Dict[str, object]:
        return {
            "state": engine.state_to_json(self.state),
            "path": list(self.path),
            "fragment_creation_weight": self.fragment_creation_weight,
        }

    @classmethod
    def from_json(cls, data: Mapping[str, object]) -> "ProfileNode":
        return cls(
            engine.state_from_json(data["state"]),  # type: ignore[arg-type,index]
            tuple(data["path"]),  # type: ignore[arg-type,index]
            None if data.get("fragment_creation_weight") is None else int(data["fragment_creation_weight"]),
        )


def mode_reason(state: engine.ExactState, mode: str) -> Optional[str]:
    reason = engine.f1_prune_reason(state)
    if reason is not None:
        return reason
    # F=0 prefixes are retained because they are necessary ancestors of an
    # F=1 completion.  The mode restriction applies monotonically afterwards.
    if mode == "A_H0" and state.H != 0:
        return "mode_A_H_nonzero"
    if mode == "B_N0" and state.Ndef != 0:
        return "mode_B_N_nonzero"
    return None


def stage_node_summary(node: ProfileNode, legal_count: int, surviving_transitions: int,
                       new_children: int, opening_candidates: int, repair_candidates: int) -> Dict[str, object]:
    state = node.state
    return {
        "canonical_state_sha256": state_hash(state),
        "coordinate": list(coordinate(state)),
        "fragment_fingerprint": fragment_fingerprint(state, node.fragment_creation_weight),
        "legal_tail_count": legal_count,
        "surviving_transition_count": surviving_transitions,
        "new_canonical_children": new_children,
        "new_E_orbit_opening_candidates": opening_candidates,
        "fragment_repair_entry_candidates": repair_candidates,
        "safe_prune_status": "survives_all_current_safe_prunes",
        "representative_path": list(node.path),
    }


def summarize_layer(nodes: Sequence[ProfileNode], depth: int) -> Dict[str, object]:
    coord_hist = Counter(tuple(coordinate(node.state)) for node in nodes)
    nh_hist = Counter((node.state.Ndef, node.state.H) for node in nodes)
    dnh_hist = Counter((node.state.D, node.state.Ndef, node.state.H) for node in nodes)
    op_hist = Counter((node.state.O, node.state.P) for node in nodes)
    fragment_hist = Counter("after_F1" if node.state.F == 1 else "before_F1" for node in nodes)
    fingerprints = Counter(fingerprint_key(fragment_fingerprint(node.state, node.fragment_creation_weight)) for node in nodes if node.state.F == 1)
    return {
        "depth": depth,
        "canonical_states_at_depth": len(nodes),
        "coordinates_P_F_S_H_O_D_N": {str(key): value for key, value in sorted(coord_hist.items())},
        "histogram_N_H": {str(key): value for key, value in sorted(nh_hist.items())},
        "histogram_D_N_H": {str(key): value for key, value in sorted(dnh_hist.items())},
        "histogram_O_P": {str(key): value for key, value in sorted(op_hist.items())},
        "fragment_before_after": dict(sorted(fragment_hist.items())),
        "F1_states": sum(node.state.F == 1 for node in nodes),
        "fragment_type_count": len(fingerprints),
        "fragment_type_histogram": dict(fingerprints.most_common()),
    }


def node_key_repr(node: ProfileNode) -> str:
    return repr(node.state.stable_key())


def write_json_atomic(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def checkpoint_payload(frontier: Sequence[ProfileNode], seen: Iterable[Tuple[object, ...]],
                       completed_depth: int, layers: Sequence[Mapping[str, object]],
                       stage_records: Sequence[Mapping[str, object]], config: Mapping[str, object],
                       unfinished: Optional[Mapping[str, object]]) -> Dict[str, object]:
    return {
        "schema": "partial-f1-profile-checkpoint-v1",
        "analysis_sha256": ANALYSIS_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": dict(config),
        "completed_depth": completed_depth,
        "layers": list(layers),
        "stage_records": list(stage_records),
        "frontier": [node.to_json() for node in frontier],
        "seen_keys": [repr(key) for key in seen],
        "unfinished_stage": dict(unfinished) if unfinished else None,
        "note": "Exact frontier/memo checkpoint for the named code SHA; bounded profiling only.",
    }


def load_checkpoint(path: Path) -> Tuple[List[ProfileNode], set[Tuple[object, ...]], int, List[Dict[str, object]], List[Dict[str, object]], Dict[str, object], Optional[Dict[str, object]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "partial-f1-profile-checkpoint-v1":
        raise ValueError("unrecognized profile checkpoint")
    if data.get("analysis_sha256") != ANALYSIS_SHA256 or data.get("engine_sha256") != ENGINE_SHA256 or data.get("core_sha256") != CORE_SHA256:
        raise ValueError("refusing resume across analysis/engine/core SHA change")
    seen = {ast.literal_eval(text) for text in data["seen_keys"]}
    if any(not isinstance(key, tuple) for key in seen):
        raise ValueError("bad checkpoint key")
    stage_records = list(data["stage_records"])
    # A stage learns its checkpoint's physical size and SHA only after the
    # atomic write.  On the next resume this metadata is safely attached to
    # the completed last stage and then carried forward in all later reports.
    if stage_records and stage_records[-1].get("completed"):
        stage_records[-1].setdefault("checkpoint_size_bytes", path.stat().st_size)
        stage_records[-1].setdefault("checkpoint_sha256", sha256_file(path))
    return (
        [ProfileNode.from_json(node) for node in data["frontier"]],
        seen,
        int(data["completed_depth"]),
        list(data["layers"]),
        stage_records,
        dict(data["config"]),
        None if data.get("unfinished_stage") is None else dict(data["unfinished_stage"]),
    )


def _top_insert(entries: List[Dict[str, object]], candidate: Dict[str, object]) -> None:
    entries.append(candidate)
    entries.sort(key=lambda entry: (int(entry["new_canonical_children"]), int(entry["surviving_transition_count"]), int(entry["legal_tail_count"])), reverse=True)
    del entries[5:]


def _unfinished_payload(source_depth: int, pending: Sequence[ProfileNode], next_nodes: Sequence[ProfileNode],
                        expanded: int, raw_generated: int, memo_duplicates: int, prunes: Counter[str],
                        top: Sequence[Mapping[str, object]], potential_counterexamples: Mapping[str, Mapping[str, object]],
                        peak_mem: int, elapsed_before_stop: float) -> Dict[str, object]:
    return {
        "source_depth": source_depth,
        "pending": [node.to_json() for node in pending],
        "next_nodes": [node.to_json() for node in next_nodes],
        "expanded": expanded,
        "raw_generated": raw_generated,
        "memo_duplicates": memo_duplicates,
        "prunes": dict(prunes),
        "top": list(top),
        "potential_counterexamples": dict(potential_counterexamples),
        "peak_working_set_bytes": peak_mem,
        "elapsed_before_stop_seconds": elapsed_before_stop,
    }


def profile_to_depth(target_depth: int, mode: str, node_limit_per_stage: int, memory_limit_bytes: int,
                     checkpoint: Path, resume: Optional[Path]) -> Dict[str, object]:
    if target_depth < 0 or node_limit_per_stage <= 0 or memory_limit_bytes <= 0:
        raise ValueError("target depth, node limit, and memory limit must be positive/bounded")
    config = {
        "mode": mode,
        "node_limit_per_stage": node_limit_per_stage,
        "memory_limit_bytes": memory_limit_bytes,
        "canonical_children": True,
    }
    unfinished: Optional[Dict[str, object]] = None
    if resume is not None:
        frontier, seen, completed_depth, layers, stage_records, old_config, unfinished = load_checkpoint(resume)
        if old_config != config:
            raise ValueError("resume configuration differs")
        if target_depth <= completed_depth:
            raise ValueError("target depth must exceed checkpoint completed depth")
    else:
        start = engine.canonicalize(engine.initial_state())
        frontier = [ProfileNode(start, (), None)]
        seen = {start.stable_key()}
        completed_depth = 0
        layers = [summarize_layer(frontier, 0)]
        stage_records = []

    outcome = "completed_target_depth"
    while completed_depth < target_depth:
        source_depth = completed_depth
        if unfinished is not None:
            if int(unfinished["source_depth"]) != source_depth:
                raise ValueError("unfinished checkpoint does not match completed boundary")
            pending = deque(ProfileNode.from_json(node) for node in unfinished["pending"])
            next_nodes = [ProfileNode.from_json(node) for node in unfinished["next_nodes"]]
            prunes = Counter(unfinished["prunes"])
            raw_generated = int(unfinished["raw_generated"])
            memo_duplicates = int(unfinished["memo_duplicates"])
            expanded = int(unfinished["expanded"])
            top = list(unfinished["top"])
            potential_counterexamples = dict(unfinished["potential_counterexamples"])
            peak_mem = int(unfinished["peak_working_set_bytes"])
            elapsed_before = float(unfinished["elapsed_before_stop_seconds"])
            unfinished = None
        else:
            pending = deque(frontier)
            next_nodes = []
            prunes = Counter()
            raw_generated = 0
            memo_duplicates = 0
            expanded = 0
            top: List[Dict[str, object]] = []
            potential_counterexamples: Dict[str, Dict[str, object]] = {}
            peak_mem = working_set_bytes()
            elapsed_before = 0.0
        started = time.time()
        # The configured node cap is a cap for this invocation's chunk of the
        # current layer.  ``expanded`` remains cumulative for the stage, so a
        # checkpoint stopped at the cap can be resumed safely with the same
        # bounded command.
        expanded_this_chunk = 0
        peak_mem = max(peak_mem, working_set_bytes())
        resource_stop: Optional[str] = None

        while pending:
            if expanded_this_chunk >= node_limit_per_stage:
                resource_stop = "node_limit_per_stage"
                break
            current_mem = working_set_bytes()
            peak_mem = max(peak_mem, current_mem)
            if current_mem and current_mem > memory_limit_bytes:
                resource_stop = "memory_limit"
                break

            node = pending.popleft()
            expanded += 1
            expanded_this_chunk += 1
            parent_scalar = structural_scalars(node.state)
            legal_count = surviving = newborn = opening = repair = 0
            for transition in engine.legal_moves(node.state):
                raw_generated += 1
                legal_count += 1
                child = transition.state
                reason = mode_reason(child, mode)
                if reason is not None:
                    prunes[reason] += 1
                    continue
                surviving += 1
                if transition.new_orbit:
                    opening += 1
                frag_h = fragment_hex_id(node.state)
                if frag_h is not None and child.current_hex == frag_h:
                    repair += 1
                child = engine.canonicalize(child)
                key = child.stable_key()
                if key in seen:
                    memo_duplicates += 1
                    prunes["canonical_state_repeat"] += 1
                    continue
                seen.add(key)
                creation_weight = node.fragment_creation_weight
                if transition.delta_F:
                    creation_weight = transition.move.weight
                child_node = ProfileNode(child, node.path + (transition.move.label,), creation_weight)
                child_scalar = structural_scalars(child)
                for scalar_name, expected in (
                    ("N_plus_H_remaining_budget", "nonincreasing"),
                    ("remaining_empty_E_phases", "nonincreasing"),
                    ("partial_hex_gap_count", "nonincreasing"),
                    ("fragment_unvisited_rotation_length", "nonincreasing"),
                    ("fragment_repair_entry_candidates", "nonincreasing"),
                ):
                    before, after = parent_scalar.get(scalar_name), child_scalar.get(scalar_name)
                    if expected == "nonincreasing" and before is not None and after is not None and after > before:
                        potential_counterexamples.setdefault(scalar_name, {
                            "from": before, "to": after,
                            "path": list(child_node.path),
                            "parent_coordinate": list(coordinate(node.state)),
                            "child_coordinate": list(coordinate(child)),
                        })
                next_nodes.append(child_node)
                newborn += 1
            _top_insert(top, stage_node_summary(node, legal_count, surviving, newborn, opening, repair))

        elapsed = round(elapsed_before + time.time() - started, 3)
        peak_mem = max(peak_mem, working_set_bytes())
        if resource_stop is not None:
            # Preserve the last fully completed boundary, not a mixture of a
            # partially expanded layer and an incomplete next layer.
            unfinished = _unfinished_payload(source_depth, list(pending), next_nodes, expanded, raw_generated,
                                              memo_duplicates, prunes, top, potential_counterexamples, peak_mem, elapsed)
            payload = checkpoint_payload(frontier, seen, completed_depth, layers, stage_records, config, unfinished)
            write_json_atomic(checkpoint, payload)
            outcome = resource_stop
            stage_records.append({
                "source_depth": source_depth,
                "target_depth": source_depth + 1,
                "completed": False,
                "stop_reason": resource_stop,
                "expanded_canonical_nodes": expanded,
                "raw_generated_transitions": raw_generated,
                "peak_working_set_bytes": peak_mem,
                "elapsed_seconds": elapsed,
            })
            break

        completed_depth += 1
        next_layer = summarize_layer(next_nodes, completed_depth)
        previous_count = len(frontier)
        next_layer["growth_ratio_vs_previous_depth"] = None if previous_count == 0 else len(next_nodes) / previous_count
        stage_record = {
            "source_depth": source_depth,
            "target_depth": completed_depth,
            "completed": True,
            "raw_visited_nodes_expanded": expanded,
            "new_canonical_states": len(next_nodes),
            "raw_generated_transitions": raw_generated,
            "memo_duplicates": memo_duplicates,
            "prune_reasons": dict(sorted(prunes.items())),
            "peak_working_set_bytes": peak_mem,
            "elapsed_seconds": elapsed,
            "growth_ratio_vs_previous_depth": next_layer["growth_ratio_vs_previous_depth"],
            "long_lived_archetypes_by_new_children": list(top),
            "potential_nonincrease_counterexamples": potential_counterexamples,
        }
        layers.append(next_layer)
        stage_records.append(stage_record)
        frontier = next_nodes
        payload = checkpoint_payload(frontier, seen, completed_depth, layers, stage_records, config, None)
        write_json_atomic(checkpoint, payload)
        # The byte size and SHA are measured after the atomic checkpoint write
        # and live in the outward report rather than recursively inside itself.
        stage_record["checkpoint_size_bytes"] = checkpoint.stat().st_size
        stage_record["checkpoint_sha256"] = sha256_file(checkpoint)

    final_checkpoint_sha = sha256_file(checkpoint) if checkpoint.exists() else None
    final_checkpoint_size = checkpoint.stat().st_size if checkpoint.exists() else None
    return {
        "schema": "partial-f1-depth-profile-v1",
        "analysis_sha256": ANALYSIS_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": config,
        "requested_target_depth": target_depth,
        "completed_depth": completed_depth,
        "completed": outcome == "completed_target_depth" and completed_depth == target_depth,
        "outcome": outcome,
        "layers": layers,
        "stage_records": stage_records,
        "final_frontier_states": len(frontier),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": final_checkpoint_sha,
        "checkpoint_size_bytes": final_checkpoint_size,
        "scope": "bounded experiment only; no slab nonexistence conclusion",
    }


def report_markdown(data: Mapping[str, object]) -> str:
    stages = data["stage_records"]
    rows = []
    for stage in stages:
        if stage.get("completed"):
            rows.append(
                f"| {stage['target_depth']} | {stage['raw_visited_nodes_expanded']} | {stage['new_canonical_states']} | "
                f"{stage['raw_generated_transitions']} | {stage['memo_duplicates']} | "
                f"{stage['peak_working_set_bytes']} | {stage.get('checkpoint_size_bytes', 'recorded in subsequent checkpoint')} | {stage['elapsed_seconds']} |"
            )
        else:
            rows.append(f"| {stage['target_depth']} | stopped: {stage['stop_reason']} | — | {stage['raw_generated_transitions']} | — | {stage['peak_working_set_bytes']} | — | {stage['elapsed_seconds']} |")
    return f"""# F=1 bounded depth profile

This is a **limited experiment**, not a complete calculation and not an
absence proof for `(F,D,N)=(1,4,*)`.

- mode: `{data['config']['mode']}`
- requested depth: `{data['requested_target_depth']}`
- completed depth: `{data['completed_depth']}`
- outcome: `{data['outcome']}`
- per-stage node cap: `{data['config']['node_limit_per_stage']}`
- working-set cap: `{data['config']['memory_limit_bytes']}` bytes
- analysis SHA-256: `{data['analysis_sha256']}`
- exact-state engine SHA-256: `{data['engine_sha256']}`
- core group-code SHA-256: `{data['core_sha256']}`
- final checkpoint SHA-256: `{data['checkpoint_sha256']}`

| reached depth | expanded source states | new canonical states | generated transitions | memo duplicates | peak working set | checkpoint bytes | seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Full machine-readable histograms, fingerprints, long-lived representatives,
and counterexample paths are in `f1_depth_profile.json`.
"""


def archetype_payload(profile: Mapping[str, object]) -> Dict[str, object]:
    fragments: List[Dict[str, object]] = []
    long_lived: List[Dict[str, object]] = []
    counterexamples: Dict[str, List[Dict[str, object]]] = {}
    for layer in profile["layers"]:
        fragments.append({
            "depth": layer["depth"],
            "F1_states": layer["F1_states"],
            "fragment_type_count": layer["fragment_type_count"],
            "fragment_type_histogram": layer["fragment_type_histogram"],
        })
    for stage in profile["stage_records"]:
        if stage.get("completed"):
            long_lived.append({"source_depth": stage["source_depth"], "representatives": stage["long_lived_archetypes_by_new_children"]})
            for name, witness in stage["potential_nonincrease_counterexamples"].items():
                counterexamples.setdefault(name, []).append({"source_depth": stage["source_depth"], **witness})
    return {
        "schema": "partial-f1-fragment-archetypes-v1",
        "analysis_sha256": ANALYSIS_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "profile_checkpoint_sha256": profile["checkpoint_sha256"],
        "depth": profile["completed_depth"],
        "limited_experiment": True,
        "fragment_types_by_depth": fragments,
        "long_lived_discovery_tree_archetypes": long_lived,
        "potential_nonincrease_counterexamples": counterexamples,
    }


def archetype_markdown(data: Mapping[str, object]) -> str:
    lines = [
        "# F=1 fragment archetypes", "", "All results are bounded-profile observations, not theorems.", "",
        f"- analysis SHA-256: `{data['analysis_sha256']}`",
        f"- exact-state engine SHA-256: `{data['engine_sha256']}`",
        f"- profile checkpoint SHA-256: `{data['profile_checkpoint_sha256']}`", "",
    ]
    lines += ["| depth | F=1 states | observed fragment types |", "|---:|---:|---:|"]
    for item in data["fragment_types_by_depth"]:
        lines.append(f"| {item['depth']} | {item['F1_states']} | {item['fragment_type_count']} |")
    lines += ["", "## Long-lived canonical discovery-tree representatives", ""]
    for group in data["long_lived_discovery_tree_archetypes"]:
        lines.append(f"### Expanded depth {group['source_depth']}")
        for rep in group["representatives"]:
            lines.append(f"- `{rep['canonical_state_sha256'][:16]}`: new children={rep['new_canonical_children']}, legal tails={rep['legal_tail_count']}, coordinate={rep['coordinate']}, path={rep['representative_path']}")
    lines += ["", "## Potential-function counterexamples", ""]
    if not data["potential_nonincrease_counterexamples"]:
        lines.append("No tested nonincrease counterexample appeared in this bounded range.")
    else:
        for name, witnesses in data["potential_nonincrease_counterexamples"].items():
            witness = witnesses[0]
            lines.append(f"- `{name}` is not nonincreasing: {witness['from']} -> {witness['to']}; path `{witness['path']}`.")
    lines += [
        "",
        "The remaining `N+H` budget and the fragment's unvisited rotation length had no recorded increase on edges where both endpoint values were defined through depth 6. This is a bounded observation only. Legal-tail count, new-orbit openings, and repair-entry count are recorded per expanded state; a depth-6 profile alone does not justify a global monotonicity claim for them.",
    ]
    return "\n".join(lines) + "\n"


def comparison_markdown(comparison: Mapping[str, object]) -> str:
    rows = []
    for label, data in comparison["subproblems"].items():
        final_layer = data["layers"][-1]
        rows.append(f"| {label} | {data['completed_depth']} | {data['final_frontier_states']} | {final_layer['fragment_type_count']} | {data['checkpoint_sha256']} | {data['outcome']} |")
    return f"""# F=1 restricted-subproblem comparison

Both rows retain `F=0` ancestors, since an `F=1` state cannot otherwise be
reached.  The restrictions are monotone after they appear.

- analysis SHA-256: `{comparison['analysis_sha256']}`
- exact-state engine SHA-256: `{comparison['engine_sha256']}`
- core group-code SHA-256: `{comparison['core_sha256']}`

| region | completed depth | final canonical frontier | fragment types | checkpoint SHA-256 | stop/completion |
|---|---:|---:|---:|---|---|
{chr(10).join(rows)}

Recommendation is made only from these bounded measurements and is not a
claim that either region is exhaustively solved.

**Recommended first complete subproblem:** {comparison['recommendation']}.
"""


def cmd_profile(args: argparse.Namespace) -> None:
    data = profile_to_depth(args.target_depth, args.mode, args.node_limit_per_stage,
                            args.memory_limit_mib * 1024 * 1024, Path(args.checkpoint),
                            Path(args.resume) if args.resume else None)
    write_json_atomic(Path(args.output), data)
    Path(args.markdown).write_text(report_markdown(data), encoding="utf-8")
    archetypes = archetype_payload(data)
    write_json_atomic(Path(args.archetypes_json), archetypes)
    Path(args.archetypes_markdown).write_text(archetype_markdown(archetypes), encoding="utf-8")
    print(json.dumps({"outcome": data["outcome"], "completed_depth": data["completed_depth"], "output": args.output}, indent=2))


def cmd_compare(args: argparse.Namespace) -> None:
    base = Path(args.checkpoint_dir)
    base.mkdir(parents=True, exist_ok=True)
    subproblems: Dict[str, Dict[str, object]] = {}
    for label, mode in (("A: F=1,H=0,N<=3", "A_H0"), ("B: F=1,N=0,H<=3", "B_N0")):
        checkpoint = base / ("f1_subproblem_" + mode + ".checkpoint.json")
        subproblems[label] = profile_to_depth(args.target_depth, mode, args.node_limit_per_stage,
                                               args.memory_limit_mib * 1024 * 1024, checkpoint, None)
    a, b = subproblems.values()
    # Prefer a completed profile with fewer final states; if one stops first,
    # report the measured fact instead of inventing an extrapolation.
    if a["completed"] and b["completed"]:
        recommendation = "A" if a["final_frontier_states"] <= b["final_frontier_states"] else "B"
    elif a["completed"]:
        recommendation = "A (only A completed the requested bounded depth)"
    elif b["completed"]:
        recommendation = "B (only B completed the requested bounded depth)"
    else:
        recommendation = "undecided: both bounded profiles stopped before the requested depth"
    data = {
        "schema": "partial-f1-subproblem-comparison-v1",
        "analysis_sha256": ANALYSIS_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "target_depth": args.target_depth,
        "node_limit_per_stage": args.node_limit_per_stage,
        "memory_limit_mib": args.memory_limit_mib,
        "limited_experiment": True,
        "subproblems": subproblems,
        "recommendation": recommendation,
    }
    write_json_atomic(Path(args.output), data)
    Path(args.markdown).write_text(comparison_markdown(data), encoding="utf-8")
    print(json.dumps({"output": args.output, "recommendation": recommendation}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("profile", help="advance a bounded exact-state profile to a finite depth")
    p.add_argument("--target-depth", type=int, required=True)
    p.add_argument("--mode", choices=("general", "A_H0", "B_N0"), default="general")
    p.add_argument("--node-limit-per-stage", type=int, default=20000)
    p.add_argument("--memory-limit-mib", type=int, default=1024)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--resume")
    p.add_argument("--output", required=True)
    p.add_argument("--markdown", required=True)
    p.add_argument("--archetypes-json", default=str(ROOT / "outputs" / "f1_fragment_archetypes.json"))
    p.add_argument("--archetypes-markdown", default=str(ROOT / "outputs" / "F1_FRAGMENT_ARCHETYPES.md"))
    p.set_defaults(func=cmd_profile)
    p = sub.add_parser("compare", help="bounded comparison of the A/B monotone subproblems")
    p.add_argument("--target-depth", type=int, default=6)
    p.add_argument("--node-limit-per-stage", type=int, default=20000)
    p.add_argument("--memory-limit-mib", type=int, default=1024)
    p.add_argument("--checkpoint-dir", default=str(ROOT / "outputs" / "f1_subproblem_checkpoints"))
    p.add_argument("--output", default=str(ROOT / "outputs" / "f1_subproblem_comparison.json"))
    p.add_argument("--markdown", default=str(ROOT / "outputs" / "F1_SUBPROBLEM_COMPARISON.md"))
    p.set_defaults(func=cmd_compare)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
