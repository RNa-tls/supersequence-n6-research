#!/usr/bin/env python3
"""Rotation-run compression for the exact n=6 partial-F=1 engine.

This is deliberately a *quotient of transition sequences*, not a quotient of
the exact Markov state.  A macro edge consists of a (possibly empty) maximal
consecutive run of literal w=1 rotations, followed by one literal w=2 or w=3
joint.  The run length is retained.  Hence a joint is allowed before the next
rotation would collide; retaining every legal run length is what makes the
compression complete.

The intended first target is the small Area-A subcase

    F=1, H=0, N=0, P=121, O=25, D=4.

``profile`` is bounded.  ``enumerate`` permits node-limit zero only for the
selected small subcase and is checkpointable; a memory limit can still stop it
cleanly without turning an interrupted calculation into a conclusion.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
ENGINE_PATH = HERE.with_name("superperm_partial_f1.py")
_SPEC = importlib.util.spec_from_file_location("partial_f1_exact_engine", ENGINE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {ENGINE_PATH}")
exact = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = exact
_SPEC.loader.exec_module(exact)

core = exact.core
N = exact.N
TARGET_F = exact.TARGET_F
TARGET_P = exact.TARGET_P
TARGET_O = exact.TARGET_O
TARGET_D = exact.TARGET_D
W1 = next(move for move in exact.ALL_MOVES if move.weight == 1)
NONROT_H0 = tuple(move for move in exact.ALL_MOVES if move.weight in (2, 3))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CODE_SHA256 = sha256_file(HERE)
ENGINE_SHA256 = sha256_file(ENGINE_PATH)
CORE_SHA256 = exact.CORE_SHA256


def stable_hash(state: exact.ExactState) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def sparse_mask_delta(before: Sequence[int], after: Sequence[int]) -> Tuple[Tuple[int, int], ...]:
    """New bits in a mask vector, encoded sparsely and auditably."""
    return tuple((i, after[i] & ~before[i]) for i in range(len(before)) if after[i] != before[i])


@dataclass(frozen=True)
class RotationRun:
    """One legal literal w=1 run from a joint-boundary exact state.

    ``ell`` counts successful literal rotations.  The list of runs from a
    state contains every ell from zero through the first collision, inclusive.
    A compressed walk chooses one of them only together with a following deep
    joint (or, at the very end, as its final rotation-only suffix).
    """

    ell: int
    state: exact.ExactState
    stopped_by_rotation_collision: bool
    delta_hex_bits: Tuple[Tuple[int, int], ...]
    delta_orbit_bits: Tuple[Tuple[int, int], ...]
    delta_F: int
    delta_S: int
    delta_H: int

    @property
    def p_out(self) -> core.Perm:
        return self.state.p

    @property
    def literal_labels(self) -> Tuple[str, ...]:
        return (W1.label,) * self.ell


@dataclass(frozen=True)
class MacroEdge:
    """A rotation run followed by one literal nonrotation joint."""

    run: RotationRun
    joint: exact.Transition

    @property
    def state(self) -> exact.ExactState:
        return self.joint.state

    @property
    def literal_labels(self) -> Tuple[str, ...]:
        return self.run.literal_labels + (self.joint.move.label,)

    @property
    def label(self) -> str:
        return f"rot^{self.run.ell};{self.joint.move.label}"


def rotation_runs(state: exact.ExactState) -> Tuple[RotationRun, ...]:
    """Enumerate all legal consecutive literal w=1 prefixes.

    A repeated intermediate permutation window terminates the enumeration;
    it is never silently skipped.  The returned endpoint of each run is
    literally replayed by ``exact.extend`` and all resource deltas are zero,
    because a rotation neither begins a pass nor ends one.
    """
    cursor = state
    out: List[RotationRun] = []
    ell = 0
    while True:
        out.append(
            RotationRun(
                ell=ell,
                state=cursor,
                stopped_by_rotation_collision=False,
                delta_hex_bits=sparse_mask_delta(state.hex_masks, cursor.hex_masks),
                delta_orbit_bits=sparse_mask_delta(state.orbit_masks, cursor.orbit_masks),
                delta_F=cursor.F - state.F,
                delta_S=cursor.S - state.S,
                delta_H=cursor.H - state.H,
            )
        )
        step = exact.extend(cursor, W1)
        if step is None:
            last = out[-1]
            out[-1] = RotationRun(
                ell=last.ell,
                state=last.state,
                stopped_by_rotation_collision=True,
                delta_hex_bits=last.delta_hex_bits,
                delta_orbit_bits=last.delta_orbit_bits,
                delta_F=last.delta_F,
                delta_S=last.delta_S,
                delta_H=last.delta_H,
            )
            return tuple(out)
        cursor = step.state
        ell += 1
        if ell > N - 1:
            raise AssertionError("a rotation run exceeded one hexagon")


def macro_edges(state: exact.ExactState) -> Iterator[MacroEdge]:
    for run in rotation_runs(state):
        for move in NONROT_H0:
            joint = exact.extend(run.state, move)
            if joint is not None:
                yield MacroEdge(run, joint)


@dataclass(frozen=True)
class AreaAConfig:
    """A safe restriction of the F=1,D=4 slab.

    ``n_limit`` is an upper bound.  The exact chosen small subcase uses zero;
    the bounded Area-A profile uses three.  No rule below assumes an unproved
    normal form for the fragment.
    """

    n_limit: int
    name: str


AREA_A = AreaAConfig(3, "A_F1_H0_Nle3")
SMALL_N0 = AreaAConfig(0, "small_F1_H0_N0")
SMALL_N1 = AreaAConfig(1, "small_F1_H0_Nle1")


def remaining_window_capacity_prune(state: exact.ExactState) -> bool:
    """Necessary maximum-cover test at a macro joint boundary.

    The current pass can add at most five rotations.  Each of the remaining
    ``TARGET_P-P`` future pass starts adds one joint window and then at most
    five rotations, hence at most six windows.  This ignores all collisions,
    so it can only be a safe (weak) pruning test.
    """
    remaining_starts = TARGET_P - state.P
    if remaining_starts < 0:
        return True
    max_new_windows = 5 + 6 * remaining_starts
    return 720 - state.visited_count > max_new_windows


def area_a_prune_reason(state: exact.ExactState, config: AreaAConfig) -> Optional[str]:
    """Only necessary conditions for Area A; the label is a certificate kind."""
    if state.F > TARGET_F:
        return "F_exceeded"
    if state.H > 0:
        return "H_positive"
    if state.P > TARGET_P:
        return "P_exceeded"
    if state.O > TARGET_O:
        return "O_exceeded"
    # For a legal tail, Delta N=dS+dF-new_orbit is nonnegative: w=3 has
    # dS=1, and w=2 can open a new orbit only after an abandonment (dF=1).
    # The blocked-w2 lemma supplies the latter implication.  Thus an already
    # exceeded N limit cannot be repaired later.
    if state.Ndef > config.n_limit:
        return "N_exceeded_monotone"
    if not exact.arithmetic_D_reachable(state):
        return "final_D_impossible"
    if 720 - state.visited_count < TARGET_P - state.P:
        return "remaining_pass_starts_exceed_remaining_windows"
    if remaining_window_capacity_prune(state):
        return "remaining_cover_capacity_impossible"
    if exact.f1_normal_form(state) is None:
        return "F1_fragment_normal_form_impossible"
    # At most one new orbit can be opened by every remaining future joint,
    # plus a possible as-yet unused abandonment accounting credit.  This is a
    # deliberately loose necessary condition.
    new_needed = TARGET_O - state.O
    future_joint_count = TARGET_P - state.P
    future_abandonments = TARGET_F - state.F
    if new_needed > future_joint_count + future_abandonments:
        return "insufficient_future_orbit_opening_credit"
    return None


def area_a_final(state: exact.ExactState, config: AreaAConfig) -> bool:
    return (
        state.visited_count == 720
        and state.P == TARGET_P
        and state.O == TARGET_O
        and state.D == TARGET_D
        and state.F == TARGET_F
        and state.H == 0
        and state.Ndef <= config.n_limit
    )


def state_coordinate(state: exact.ExactState) -> Tuple[int, int, int, int, int, int, int]:
    return (state.P, state.F, state.S, state.H, state.O, state.D, state.Ndef)


def macro_path_to_json(path: Sequence[MacroEdge]) -> List[Dict[str, object]]:
    return [
        {
            "rotation_length": edge.run.ell,
            "rotation_stopped_by_collision": edge.run.stopped_by_rotation_collision,
            "joint": edge.joint.move.label,
            "literal_labels": list(edge.literal_labels),
        }
        for edge in path
    ]


def replay_macro_path(path: Sequence[Mapping[str, object]], canonical_children: bool = True) -> exact.ExactState:
    """Independent-format literal replay for serialized macro labels."""
    state = exact.canonicalize(exact.initial_state()) if canonical_children else exact.initial_state()
    by_label = {move.label: move for move in exact.ALL_MOVES}
    for item in path:
        ell = int(item["rotation_length"])
        for _ in range(ell):
            tr = exact.extend(state, W1)
            if tr is None:
                raise AssertionError("serialized macro has an intermediate rotation collision")
            state = tr.state
        move = by_label[str(item["joint"])]
        if move.weight == 1:
            raise AssertionError("macro joint cannot be a rotation")
        tr = exact.extend(state, move)
        if tr is None:
            raise AssertionError("serialized macro joint is illegal")
        state = tr.state
        if canonical_children:
            state = exact.canonicalize(state)
    return state


def fragment_fingerprint(state: exact.ExactState) -> Optional[Tuple[object, ...]]:
    """A relabelling-invariant, lossless-in-context F<=1 fragment descriptor."""
    form = exact.f1_normal_form(state)
    if form is None or form.fragment_hex is None:
        return None
    # The state is canonical before this is called.  The descriptor therefore
    # uses its canonical local coordinates but keeps every arc/end-point datum.
    h = form.fragment_hex
    q_masks = tuple(mask for q, mask in form.orbit_masks if any(
        exact.HEX_POSITION[word][0] == h
        for word in core.orbit(core.E_REPS[q], core.E)
    ))
    return (
        "fragment",
        tuple(form.fragment_components),
        form.current_hex == h,
        tuple(form.current_components),
        tuple(q_masks),
        state.hex_masks[state.current_hex],
    )


def _literal_first_joint_control(config: AreaAConfig) -> Dict[str, object]:
    """Compare an independently expanded first literal run with macro edges."""
    start = exact.canonicalize(exact.initial_state())
    literal: Dict[Tuple[object, ...], Dict[str, object]] = {}
    literal_prunes: Counter[str] = Counter()
    cursor = start
    ell = 0
    while True:
        for move in NONROT_H0:
            joint = exact.extend(cursor, move)
            if joint is None:
                literal_prunes["joint_collision"] += 1
                continue
            reason = area_a_prune_reason(joint.state, config)
            if reason is not None:
                literal_prunes[reason] += 1
                continue
            child = exact.canonicalize(joint.state)
            literal[child.stable_key()] = {
                "coordinate": state_coordinate(child),
                "fragment": fragment_fingerprint(child),
                "literal_labels": [W1.label] * ell + [move.label],
            }
        nxt = exact.extend(cursor, W1)
        if nxt is None:
            break
        cursor = nxt.state
        ell += 1

    macro: Dict[Tuple[object, ...], Dict[str, object]] = {}
    macro_prunes: Counter[str] = Counter()
    for edge in macro_edges(start):
        reason = area_a_prune_reason(edge.state, config)
        if reason is not None:
            macro_prunes[reason] += 1
            continue
        child = exact.canonicalize(edge.state)
        macro[child.stable_key()] = {
            "coordinate": state_coordinate(child),
            "fragment": fragment_fingerprint(child),
            "literal_labels": list(edge.literal_labels),
        }
    same_keys = set(literal) == set(macro)
    same_records = same_keys and all(literal[key] == macro[key] for key in literal)
    if not same_records or literal_prunes != macro_prunes:
        raise AssertionError("literal/macro first-joint control failed")
    return {
        "literal_macro_first_joint_frontier_equal": same_keys,
        "coordinates_fingerprints_and_representative_literals_equal": same_records,
        "literal_prunes": dict(sorted(literal_prunes.items())),
        "macro_prunes": dict(sorted(macro_prunes.items())),
        "frontier_size": len(literal),
        "max_rotation_run_from_initial": ell,
    }


def macro_sanity(config: AreaAConfig = AREA_A) -> Dict[str, object]:
    start = exact.canonicalize(exact.initial_state())
    runs = rotation_runs(start)
    # A full hexagon gives five successful rotations and makes the sixth a
    # literal repeated-window collision.  This is both a positive and a
    # negative control for the macro's intermediate-membership rule.
    collision_rejected = exact.extend(runs[-1].state, W1) is None
    zero_resources = all(
        run.delta_F == 0 and run.delta_S == 0 and run.delta_H == 0 and not run.delta_orbit_bits
        for run in runs
    )

    # Left relabelling commutes with sigma.  Test every label at an F=1
    # literal prefix, including equality of the canonical macro-child set.
    f1 = next(edge.state for edge in macro_edges(start) if edge.joint.move.weight == 2)
    labels0 = {(edge.run.ell, edge.joint.move.label) for edge in macro_edges(f1)}
    equivariant = True
    canonical_child_equivariant = True
    base_children = {
        exact.canonicalize(edge.state).stable_key()
        for edge in macro_edges(f1)
        if area_a_prune_reason(edge.state, config) is None
    }
    for alpha_index in range(len(core.ALL_WORDS)):
        image = exact.relabel_state(f1, alpha_index)
        labels = {(edge.run.ell, edge.joint.move.label) for edge in macro_edges(image)}
        if labels != labels0:
            equivariant = False
            break
        children = {
            exact.canonicalize(edge.state).stable_key()
            for edge in macro_edges(image)
            if area_a_prune_reason(edge.state, config) is None
        }
        if children != base_children:
            canonical_child_equivariant = False
            break

    first_joint = _literal_first_joint_control(config)
    return {
        "schema": "partial-f1-macro-sanity-v1",
        "macro_sha256": CODE_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "scope": "finite transition controls only; no Area-A existence conclusion",
        "initial_run_lengths": [run.ell for run in runs],
        "initial_maximal_run_ends_by_collision": runs[-1].stopped_by_rotation_collision,
        "intermediate_rotation_collision_rejected": collision_rejected,
        "rotation_resource_deltas_are_zero": zero_resources,
        "left_S6_macro_legal_tail_equivariance_720": equivariant,
        "canonicalization_preserves_legal_macro_tail_set_720": canonical_child_equivariant,
        "first_joint_control": first_joint,
    }


def write_json_atomic(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _key_from_repr(text: str) -> Tuple[object, ...]:
    import ast
    key = ast.literal_eval(text)
    if not isinstance(key, tuple):
        raise ValueError("invalid serialized exact-state key")
    return key


def checkpoint_payload(
    frontier: Sequence[Tuple[int, exact.ExactState, Tuple[Dict[str, object], ...]]],
    seen: Iterable[Tuple[object, ...]],
    stats: Mapping[str, object],
    config: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "schema": "partial-f1-macro-checkpoint-v1",
        "macro_sha256": CODE_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": dict(config),
        "stats": dict(stats),
        "frontier": [
            {"depth": depth, "state": exact.state_to_json(state), "path": list(path)}
            for depth, state, path in frontier
        ],
        "seen_keys": [repr(key) for key in seen],
        "note": "Exact resume requires identical macro, exact-engine, and core SHA-256 values.",
    }


def load_checkpoint(path: Path) -> Tuple[deque[Tuple[int, exact.ExactState, Tuple[Dict[str, object], ...]]], set[Tuple[object, ...]], Dict[str, object], Dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "partial-f1-macro-checkpoint-v1":
        raise ValueError("unrecognized macro checkpoint")
    if (data.get("macro_sha256"), data.get("engine_sha256"), data.get("core_sha256")) != (CODE_SHA256, ENGINE_SHA256, CORE_SHA256):
        raise ValueError("refusing resume across code SHA change")
    frontier = deque(
        (int(item["depth"]), exact.state_from_json(item["state"]), tuple(item.get("path", [])))
        for item in data["frontier"]
    )
    seen = {_key_from_repr(text) for text in data["seen_keys"]}
    return frontier, seen, dict(data["stats"]), dict(data["config"])


def _working_set_bytes() -> int:
    """Current Windows working set, with a conservative zero fallback."""
    try:
        import ctypes

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
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        )
        return int(counters.WorkingSetSize) if ok else 0
    except Exception:
        return 0


def _terminal_certificate(
    state: exact.ExactState,
    config: AreaAConfig,
    attempted: Counter[str],
    path: Tuple[Dict[str, object], ...],
) -> Dict[str, object]:
    return {
        "state_hash": stable_hash(state),
        "coordinate": state_coordinate(state),
        "visited": state.visited_count,
        "classification": "no_legal_tail" if not attempted else "all_outgoing_children_rejected",
        "rejections": dict(sorted(attempted.items())),
        "state": exact.state_to_json(state),
        "path": list(path),
        "final_target": area_a_final(state, config),
    }


def run_macro_search(
    config: AreaAConfig,
    max_depth: Optional[int],
    node_limit: int,
    memory_limit_bytes: int,
    checkpoint: Optional[Path],
    checkpoint_every: int,
    resume: Optional[Path],
    retain_terminal_certificates: bool,
) -> Dict[str, object]:
    """Breadth-first macro search with only exact/safe acceptance tests.

    A positive ``max_depth`` makes this a bounded diagnostic.  ``None`` is
    permitted only for the named small N=0/N<=1 subcases; it is the requested
    checkpointable exhaustive calculation, subject to a clean memory stop.
    """
    if node_limit < 0:
        raise ValueError("node limit must be nonnegative")
    if max_depth is None and config.name not in {SMALL_N0.name, SMALL_N1.name}:
        raise ValueError("unbounded mode is reserved for a selected small subcase")
    search_config = {
        "name": config.name,
        "n_limit": config.n_limit,
        "max_macro_depth": max_depth,
        "node_limit": node_limit,
        "memory_limit_bytes": memory_limit_bytes,
        "canonical_children": True,
    }
    if resume is not None:
        frontier, seen, stats, old = load_checkpoint(resume)
        if old != search_config:
            raise ValueError("resume config differs from requested macro search")
    else:
        start = exact.canonicalize(exact.initial_state())
        frontier = deque([(0, start, tuple())])
        seen = {start.stable_key()}
        stats = {
            "expanded": 0,
            "generated_macro_edges": 0,
            "generated_literal_transitions": 0,
            "accepted": 1,
            "memo_duplicates": 0,
            "prunes": {},
            "depth_counts": {"0": 1},
            "terminal_certificates": [],
            "success_certificates": [],
            "max_working_set_bytes": _working_set_bytes(),
        }
    prunes: Counter[str] = Counter(stats.get("prunes", {}))
    depth_counts: Counter[str] = Counter(stats.get("depth_counts", {}))
    terminals: List[Dict[str, object]] = list(stats.get("terminal_certificates", []))
    successes: List[Dict[str, object]] = list(stats.get("success_certificates", []))
    start_time = time.time()
    stopped_by_memory = False
    hit_node_limit = False
    while frontier:
        if node_limit and int(stats["expanded"]) >= node_limit:
            hit_node_limit = True
            break
        working = _working_set_bytes()
        stats["max_working_set_bytes"] = max(int(stats.get("max_working_set_bytes", 0)), working)
        if memory_limit_bytes and working and working > memory_limit_bytes:
            stopped_by_memory = True
            break
        depth, state, path = frontier.popleft()
        if max_depth is not None and depth >= max_depth:
            continue
        stats["expanded"] = int(stats["expanded"]) + 1
        if area_a_final(state, config):
            successes.append({
                "state_hash": stable_hash(state),
                "coordinate": state_coordinate(state),
                "state": exact.state_to_json(state),
                "path": list(path),
            })
            continue
        local_rejections: Counter[str] = Counter()
        legal_child_count = 0
        for run in rotation_runs(state):
            stats["generated_literal_transitions"] = int(stats["generated_literal_transitions"]) + run.ell
            for move in NONROT_H0:
                joint = exact.extend(run.state, move)
                stats["generated_macro_edges"] = int(stats["generated_macro_edges"]) + 1
                stats["generated_literal_transitions"] = int(stats["generated_literal_transitions"]) + 1
                if joint is None:
                    local_rejections["collision"] += 1
                    prunes["collision"] += 1
                    continue
                edge = MacroEdge(run, joint)
                child = edge.state
                reason = area_a_prune_reason(child, config)
                if reason is not None:
                    local_rejections[reason] += 1
                    prunes[reason] += 1
                    continue
                child = exact.canonicalize(child)
                key = child.stable_key()
                if key in seen:
                    local_rejections["memo_duplicate"] += 1
                    prunes["memo_duplicate"] += 1
                    stats["memo_duplicates"] = int(stats["memo_duplicates"]) + 1
                    continue
                legal_child_count += 1
                seen.add(key)
                child_path = path + (macro_path_to_json((edge,))[0],)
                frontier.append((depth + 1, child, child_path))
                stats["accepted"] = int(stats["accepted"]) + 1
                depth_counts[str(depth + 1)] += 1
        # A finished walk may end with a rotation-only suffix; test all legal
        # suffixes exactly before declaring the joint-boundary state dead.
        rotation_only_success = False
        for run in rotation_runs(state):
            if area_a_final(run.state, config):
                rotation_only_success = True
                successes.append({
                    "state_hash": stable_hash(run.state),
                    "coordinate": state_coordinate(run.state),
                    "state": exact.state_to_json(run.state),
                    "path": list(path),
                    "final_rotation_length": run.ell,
                })
        if legal_child_count == 0 and not rotation_only_success and retain_terminal_certificates:
            terminals.append(_terminal_certificate(state, config, local_rejections, path))
        if checkpoint is not None and int(stats["expanded"]) % checkpoint_every == 0:
            stats["prunes"] = dict(sorted(prunes.items()))
            stats["depth_counts"] = dict(sorted(depth_counts.items()))
            stats["terminal_certificates"] = terminals
            stats["success_certificates"] = successes
            write_json_atomic(checkpoint, checkpoint_payload(list(frontier), seen, stats, search_config))

    stats["prunes"] = dict(sorted(prunes.items()))
    stats["depth_counts"] = dict(sorted(depth_counts.items()))
    stats["terminal_certificates"] = terminals
    stats["success_certificates"] = successes
    stats["elapsed_seconds_this_invocation"] = round(time.time() - start_time, 3)
    stats["frontier_remaining"] = len(frontier)
    stats["seen"] = len(seen)
    stats["max_working_set_bytes"] = max(int(stats.get("max_working_set_bytes", 0)), _working_set_bytes())
    completed = not frontier and not hit_node_limit and not stopped_by_memory
    result: Dict[str, object] = {
        "schema": "partial-f1-macro-search-v1",
        "macro_sha256": CODE_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": search_config,
        "stats": stats,
        "completed": completed,
        "hit_node_limit": hit_node_limit,
        "stopped_by_memory_limit": stopped_by_memory,
        "limited_experiment": max_depth is not None or node_limit != 0 or stopped_by_memory,
        "checkpoint": str(checkpoint) if checkpoint else None,
        "warning": (
            "No nonexistence conclusion is licensed unless completed=true, "
            "max_macro_depth=null, node_limit=0, and an independent replay verifier passes."
        ),
    }
    if checkpoint is not None:
        write_json_atomic(checkpoint, checkpoint_payload(list(frontier), seen, stats, search_config))
    return result


def markdown_macro(report: Mapping[str, object]) -> str:
    sanity = report["sanity"]
    return f"""# F=1 rotation macro-transition controls

Status: finite transition controls only.  This document does not state an
Area-A nonexistence result.

## Exact compression

A macro edge retains every legal rotation-run length `ell=0,...,ell_max` and
then records one literal nonrotation joint.  It therefore does **not** assume
that a pass must rotate until a collision before taking a deep joint.  Each
literal prefix factors uniquely into these runs and joints; a rotation-only
suffix is tested separately at termination.  Every run is replayed with the
exact `extend` routine, so an intermediate repeated permutation window ends
the run and cannot be skipped.

The rotation component has `(Delta F, Delta S, Delta H)=(0,0,0)` and changes
only its own hexagon mask.  Left value relabelling commutes with the right
rotation, hence canonical child quotienting is applied only after the literal
joint and preserves the legal macro-tail set.

## Finite controls

```json
{json.dumps(sanity, ensure_ascii=False, indent=2)}
```

Classification: the facts in this file are literal finite checks or direct
consequences of the exact transition definition.  They are not a whole-slab
enumeration.
"""


def macro_profile_payload(config: AreaAConfig, depths: Sequence[int], node_limit: int, memory_limit_mib: int, checkpoint_dir: Path) -> Dict[str, object]:
    stages: List[Dict[str, object]] = []
    previous_frontier: Optional[int] = None
    for depth in depths:
        cp = checkpoint_dir / f"{config.name}_macro_depth{depth}.checkpoint.json"
        report = run_macro_search(
            config=config,
            max_depth=depth,
            node_limit=node_limit,
            memory_limit_bytes=memory_limit_mib * 1024 * 1024,
            checkpoint=cp,
            checkpoint_every=max(1, min(500, node_limit or 500)),
            resume=None,
            retain_terminal_certificates=False,
        )
        stats = report["stats"]
        frontier = int(stats["frontier_remaining"])
        stages.append({
            "macro_depth": depth,
            "completed": report["completed"],
            "limited_experiment": report["limited_experiment"],
            "canonical_seen": stats["seen"],
            "frontier_remaining": frontier,
            "growth_ratio_frontier": None if previous_frontier in (None, 0) else frontier / previous_frontier,
            "generated_macro_edges": stats["generated_macro_edges"],
            "generated_literal_transitions": stats["generated_literal_transitions"],
            "memo_duplicates": stats["memo_duplicates"],
            "prunes": stats["prunes"],
            "peak_working_set_bytes": stats["max_working_set_bytes"],
            "checkpoint": str(cp),
            "checkpoint_sha256": sha256_file(cp),
            "checkpoint_size_bytes": cp.stat().st_size,
            "elapsed_seconds": stats["elapsed_seconds_this_invocation"],
        })
        previous_frontier = frontier
        if not report["completed"]:
            break
    return {
        "schema": "partial-f1-area-a-macro-profile-v1",
        "macro_sha256": CODE_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": {"name": config.name, "n_limit": config.n_limit, "node_limit": node_limit, "memory_limit_mib": memory_limit_mib},
        "stages": stages,
        "limited_experiment": True,
        "warning": "Bounded macro-depth profile only; not a slab-exhaustion result.",
    }


def cmd_sanity(args: argparse.Namespace) -> None:
    report = macro_sanity(AREA_A)
    write_json_atomic(Path(args.output), report)
    Path(args.markdown).write_text(markdown_macro({"sanity": report}), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _config_from_args(args: argparse.Namespace) -> AreaAConfig:
    if args.subcase == "A":
        return AREA_A
    if args.subcase == "N0":
        return SMALL_N0
    if args.subcase == "N1":
        return SMALL_N1
    raise ValueError("unknown subcase")


def cmd_profile(args: argparse.Namespace) -> None:
    config = _config_from_args(args)
    depths = tuple(int(x) for x in args.depths.split(",") if x.strip())
    report = macro_profile_payload(config, depths, args.node_limit, args.memory_limit_mib, Path(args.checkpoint_dir))
    write_json_atomic(Path(args.output), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_enumerate(args: argparse.Namespace) -> None:
    config = _config_from_args(args)
    depth = None if args.unbounded else args.max_depth
    report = run_macro_search(
        config=config,
        max_depth=depth,
        node_limit=args.node_limit,
        memory_limit_bytes=args.memory_limit_mib * 1024 * 1024,
        checkpoint=Path(args.checkpoint) if args.checkpoint else None,
        checkpoint_every=args.checkpoint_every,
        resume=Path(args.resume) if args.resume else None,
        retain_terminal_certificates=True,
    )
    write_json_atomic(Path(args.output), report)
    print(json.dumps({k: report[k] for k in ("completed", "hit_node_limit", "stopped_by_memory_limit", "config")}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("sanity", help="finite literal/macro and canonicalization controls")
    p.add_argument("--output", default=str(ROOT / "outputs" / "f1_macro_sanity.json"))
    p.add_argument("--markdown", default=str(ROOT / "PARTIAL_F1_MACRO_TRANSITIONS.md"))
    p.set_defaults(func=cmd_sanity)
    p = sub.add_parser("profile", help="bounded macro-depth profile")
    p.add_argument("--subcase", choices=("A", "N0", "N1"), default="A")
    p.add_argument("--depths", default="1,2,3,4,5,6,7,8")
    p.add_argument("--node-limit", type=int, default=20000)
    p.add_argument("--memory-limit-mib", type=int, default=1024)
    p.add_argument("--checkpoint-dir", default=str(ROOT / "outputs" / "f1_macro_checkpoints"))
    p.add_argument("--output", default=str(ROOT / "outputs" / "f1_area_a_profile.json"))
    p.set_defaults(func=cmd_profile)
    p = sub.add_parser("enumerate", help="checkpointable macro state search")
    p.add_argument("--subcase", choices=("A", "N0", "N1"), default="N0")
    p.add_argument("--unbounded", action="store_true")
    p.add_argument("--max-depth", type=int, default=8)
    p.add_argument("--node-limit", type=int, default=0)
    p.add_argument("--memory-limit-mib", type=int, default=0)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--checkpoint-every", type=int, default=250)
    p.add_argument("--resume")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_enumerate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
