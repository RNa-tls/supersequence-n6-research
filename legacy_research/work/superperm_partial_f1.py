#!/usr/bin/env python3
"""Exact, bounded state engine for the n=6 F=1 partial-cassette slab.

This module is deliberately *not* an unbounded enumerator.  It provides the
finite transition system, left-S6 quotient, safe necessary pruning rules and
checkpointable, depth-limited census required before any such enumeration is
attempted.  The intended target slab is

    F = 1, D = 4, N + H <= 3, P = 121, O = 25.

All conventions are imported from ``superperm_port_lift.py``.  In particular,
a move is an indecomposable overlap tail, and a state stores every visited
permutation window, grouped by rotation hexagon.

Run ``sanity`` first.  ``census`` always requires a positive node limit; it is
only a bounded diagnostic, never an exhaustive proof command.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
import tracemalloc
from collections import Counter, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
CORE_PATH = HERE.with_name("superperm_port_lift.py")
_SPEC = importlib.util.spec_from_file_location("superperm_port_lift_core", CORE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {CORE_PATH}")
core = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = core
_SPEC.loader.exec_module(core)


N = core.N
HEX_COUNT = len(core.ROT_REPS)       # 120
ORBIT_COUNT = len(core.E_REPS)       # 144
FULL_HEX = (1 << N) - 1              # 0b111111
FULL_ORBIT = (1 << (N - 1)) - 1      # 0b11111
TARGET_F = 1
TARGET_P = 121
TARGET_O = 25
TARGET_D = 4
TARGET_BUDGET = 3                    # N + H


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CODE_SHA256 = sha256_file(HERE)
CORE_SHA256 = sha256_file(CORE_PATH)


def _bit_count(mask: int) -> int:
    return mask.bit_count()


def _mask_rotate(mask: int, width: int, shift: int) -> int:
    """Move bit i to i+shift modulo width."""
    shift %= width
    if shift == 0:
        return mask
    out = 0
    for i in range(width):
        if mask & (1 << i):
            out |= 1 << ((i + shift) % width)
    return out


# Fixed word-to-local-coordinate maps.  They make M_H and B_Q literal
# membership oracles, rather than summaries inferred from a history.
HEX_POSITION: Dict[core.Perm, Tuple[int, int]] = {}
for h, rep in enumerate(core.ROT_REPS):
    for i, word in enumerate(core.orbit(rep, core.SIGMA)):
        HEX_POSITION[word] = (h, i)

ORBIT_PHASE: Dict[core.Perm, Tuple[int, int]] = {}
for q, rep in enumerate(core.E_REPS):
    for i, word in enumerate(core.orbit(rep, core.E)):
        ORBIT_PHASE[word] = (q, i)

if len(HEX_POSITION) != 720 or len(ORBIT_PHASE) != 720:
    raise AssertionError("coordinate maps must cover S_6 exactly")


class Move(NamedTuple):
    weight: int
    pi: Tuple[int, ...]
    action: core.Perm

    @property
    def label(self) -> str:
        return f"w{self.weight}:{''.join(map(str, self.pi))}"


ALL_MOVES: Tuple[Move, ...] = tuple(
    Move(w, pi, core.tail_action(w, pi))
    for w in range(1, N + 1)
    for pi in core.tail_permutations(w)
)
# The same endpoint permutation can be reached by tails of different declared
# lengths.  A walk records the *literal appended tail*, not the endpoint's
# maximal-overlap shortcut, so replay must key by both its observed weight and
# its right action.  (For example a length-six indecomposable tail may have an
# endpoint which also admits a shorter overlap representation.)
MOVE_BY_WEIGHT_ACTION: Dict[Tuple[int, core.Perm], Move] = {
    (move.weight, move.action): move for move in ALL_MOVES
}
if len(ALL_MOVES) != 550:
    raise AssertionError("expected 1+1+3+13+71+461 indecomposable tails")


@dataclass(frozen=True)
class ExactState:
    """The exact Markov state Omega for an n=6 walk prefix.

    ``hex_masks[h]`` contains exactly the visited permutation windows in the
    h-th rotation hexagon.  ``orbit_masks[q]`` contains exactly the pass-start
    phases already used in the q-th E-orbit.  Counters use the convention
    S=1 at the initial one-window prefix.
    """

    p: core.Perm
    hex_masks: Tuple[int, ...]
    orbit_masks: Tuple[int, ...]
    F: int
    S: int
    H: int

    def __post_init__(self) -> None:
        if len(self.hex_masks) != HEX_COUNT or len(self.orbit_masks) != ORBIT_COUNT:
            raise ValueError("wrong mask-vector length")
        if any(mask < 0 or mask > FULL_HEX for mask in self.hex_masks):
            raise ValueError("invalid hex mask")
        if any(mask < 0 or mask > FULL_ORBIT for mask in self.orbit_masks):
            raise ValueError("invalid E-orbit mask")
        h, bit = HEX_POSITION[self.p]
        if not (self.hex_masks[h] & (1 << bit)):
            raise ValueError("terminal permutation is not marked visited")

    @property
    def visited_count(self) -> int:
        return sum(_bit_count(mask) for mask in self.hex_masks)

    @property
    def P(self) -> int:
        return sum(_bit_count(mask) for mask in self.orbit_masks)

    @property
    def O(self) -> int:
        return sum(mask != 0 for mask in self.orbit_masks)

    @property
    def D(self) -> int:
        return sum((N - 1) - _bit_count(mask) for mask in self.orbit_masks if mask)

    @property
    def Ndef(self) -> int:
        return self.S + self.F - self.O

    @property
    def current_hex(self) -> int:
        return HEX_POSITION[self.p][0]

    def visited(self, word: core.Perm) -> bool:
        h, bit = HEX_POSITION[word]
        return bool(self.hex_masks[h] & (1 << bit))

    def sparse_hex(self) -> Tuple[Tuple[int, int], ...]:
        return tuple((i, mask) for i, mask in enumerate(self.hex_masks) if mask)

    def sparse_orbits(self) -> Tuple[Tuple[int, int], ...]:
        return tuple((i, mask) for i, mask in enumerate(self.orbit_masks) if mask)

    def stable_key(self) -> Tuple[object, ...]:
        return (self.p, self.sparse_hex(), self.sparse_orbits(), self.F, self.S, self.H)


@dataclass(frozen=True)
class Transition:
    move: Move
    target: core.Perm
    abandonment: bool
    delta_F: int
    delta_S: int
    delta_H: int
    new_orbit: bool
    state: ExactState


def initial_state(p: core.Perm = core.IDENTITY) -> ExactState:
    hm = [0] * HEX_COUNT
    om = [0] * ORBIT_COUNT
    h, bit = HEX_POSITION[p]
    q, phase = ORBIT_PHASE[p]
    hm[h] |= 1 << bit
    om[q] |= 1 << phase
    return ExactState(p, tuple(hm), tuple(om), F=0, S=1, H=0)


def extend(state: ExactState, move: Move) -> Optional[Transition]:
    """Apply one tail, or return None if its sole new window is repeated.

    Indecomposability is the reason an overlap tail creates no intervening
    permutation window.  Thus the target below is the complete membership
    test for the appended tail.
    """
    target = core.word_after(state.p, move.action)
    if state.visited(target):
        return None

    hm = list(state.hex_masks)
    om = list(state.orbit_masks)
    h, bit = HEX_POSITION[target]
    hm[h] |= 1 << bit

    abandonment = False
    new_orbit = False
    dF = dS = dH = 0
    if move.weight >= 2:
        # The old pass ends at p.  Its rotation successor is precisely the
        # obstruction deciding blocked versus abandonment.
        abandonment = not state.visited(core.word_after(state.p, core.SIGMA))
        dF = int(abandonment)
        dS = int(move.weight >= 3)
        dH = max(move.weight - 3, 0)
        q, phase = ORBIT_PHASE[target]
        if om[q] & (1 << phase):
            # This would imply target was previously visited, but keeping the
            # assertion makes the B_Q layer independently auditable.
            raise AssertionError("reused pass-start phase without repeated window")
        new_orbit = om[q] == 0
        om[q] |= 1 << phase

    nxt = ExactState(
        target,
        tuple(hm),
        tuple(om),
        F=state.F + dF,
        S=state.S + dS,
        H=state.H + dH,
    )
    return Transition(move, target, abandonment, dF, dS, dH, new_orbit, nxt)


def legal_moves(state: ExactState) -> Iterator[Transition]:
    for move in ALL_MOVES:
        transition = extend(state, move)
        if transition is not None:
            yield transition


def cyclic_components(mask: int, width: int = N) -> Tuple[Tuple[int, int, int], ...]:
    """Directed sigma-components as (start,end,length), excluding full mask."""
    full = (1 << width) - 1
    if mask == 0 or mask == full:
        return ()
    components: List[Tuple[int, int, int]] = []
    for start in range(width):
        if (mask & (1 << start)) and not (mask & (1 << ((start - 1) % width))):
            length = 1
            while mask & (1 << ((start + length) % width)):
                length += 1
            components.append((start, (start + length - 1) % width, length))
    return tuple(components)


@dataclass(frozen=True)
class F1NormalForm:
    """Lossless F<=1 quotient of hex masks for reachable prefix states.

    ``fragment_hex`` is the unique non-current partial hexagon, if present.
    ``current_components`` is indispensable: the proposed tuple
    (p,U,H*,I1,I2,B,F,S,H) omits it whenever the live pass occupies a distinct
    partial hexagon.  Components are directed sigma-arcs, encoded by their
    local start/end/length coordinates.
    """

    p: core.Perm
    full_hexagons: Tuple[int, ...]
    fragment_hex: Optional[int]
    fragment_components: Tuple[Tuple[int, int, int], ...]
    current_hex: int
    current_components: Tuple[Tuple[int, int, int], ...]
    orbit_masks: Tuple[Tuple[int, int], ...]
    F: int
    S: int
    H: int


def f1_normal_form(state: ExactState) -> Optional[F1NormalForm]:
    """Return the exact F<=1 normal form, or None when its structural
    invariant is violated.

    A walk prefix has at most one abandoned, non-current partial hexagon per
    abandonment.  With F<=1 there can therefore be only one such hexagon, and
    the total number of directed partial arcs is at most F+1 (the live arc
    plus a possible abandoned arc).  This is a necessary prefix invariant,
    not an unproved pruning heuristic.
    """
    if state.F > 1:
        return None
    current = state.current_hex
    partial = [h for h, mask in enumerate(state.hex_masks) if mask not in (0, FULL_HEX)]
    noncurrent = [h for h in partial if h != current]
    if len(noncurrent) > 1:
        return None
    total_components = sum(len(cyclic_components(state.hex_masks[h])) for h in partial)
    if total_components > state.F + 1:
        return None
    fragment = noncurrent[0] if noncurrent else None
    full = tuple(h for h, mask in enumerate(state.hex_masks) if mask == FULL_HEX)
    return F1NormalForm(
        p=state.p,
        full_hexagons=full,
        fragment_hex=fragment,
        fragment_components=cyclic_components(state.hex_masks[fragment]) if fragment is not None else (),
        current_hex=current,
        current_components=cyclic_components(state.hex_masks[current]),
        orbit_masks=state.sparse_orbits(),
        F=state.F,
        S=state.S,
        H=state.H,
    )


def restore_f1_normal_form(form: F1NormalForm) -> ExactState:
    """Inverse of ``f1_normal_form`` on its declared domain."""
    hm = [0] * HEX_COUNT
    for h in form.full_hexagons:
        hm[h] = FULL_HEX

    def add_components(h: int, components: Sequence[Tuple[int, int, int]]) -> None:
        for start, _end, length in components:
            for k in range(length):
                hm[h] |= 1 << ((start + k) % N)

    if form.fragment_hex is not None:
        add_components(form.fragment_hex, form.fragment_components)
    add_components(form.current_hex, form.current_components)
    om = [0] * ORBIT_COUNT
    for q, mask in form.orbit_masks:
        om[q] = mask
    return ExactState(form.p, tuple(hm), tuple(om), form.F, form.S, form.H)


# The left S_6 action on local coordinates.  Values commute with all position
# actions, but canonical representatives may choose rotated/E-shifted reps,
# hence the recorded local phase shifts.
LEFT_HEX_ACTION: List[Tuple[Tuple[int, int], ...]] = []
LEFT_ORBIT_ACTION: List[Tuple[Tuple[int, int], ...]] = []
for alpha in core.ALL_WORDS:
    hex_map: List[Tuple[int, int]] = []
    for rep in core.ROT_REPS:
        image = core.left_relabel(rep, alpha)
        h2 = core.hexagon_id(image)
        shift = core.rotation_distance(core.ROT_REPS[h2], image)
        hex_map.append((h2, shift))
    orbit_map: List[Tuple[int, int]] = []
    for rep in core.E_REPS:
        image = core.left_relabel(rep, alpha)
        q2 = core.e_orbit_id(image)
        shift = 0
        cursor = core.E_REPS[q2]
        while cursor != image:
            cursor = core.word_after(cursor, core.E)
            shift += 1
            if shift >= N - 1:
                raise AssertionError("E-coordinate lookup failed")
        orbit_map.append((q2, shift))
    LEFT_HEX_ACTION.append(tuple(hex_map))
    LEFT_ORBIT_ACTION.append(tuple(orbit_map))


def relabel_state(state: ExactState, alpha_index: int) -> ExactState:
    alpha = core.ALL_WORDS[alpha_index]
    hm = [0] * HEX_COUNT
    om = [0] * ORBIT_COUNT
    for h, mask in state.sparse_hex():
        h2, shift = LEFT_HEX_ACTION[alpha_index][h]
        hm[h2] = _mask_rotate(mask, N, shift)
    for q, mask in state.sparse_orbits():
        q2, shift = LEFT_ORBIT_ACTION[alpha_index][q]
        om[q2] = _mask_rotate(mask, N - 1, shift)
    return ExactState(core.left_relabel(state.p, alpha), tuple(hm), tuple(om), state.F, state.S, state.H)


def relabel_sparse_key(state: ExactState, alpha_index: int) -> Tuple[object, ...]:
    """Serialization of a translate without allocating two dense mask arrays.

    This is mathematically identical to ``relabel_state(...).stable_key()``.
    Canonicalization calls it 720 times per child, so avoiding the temporary
    120+144 arrays matters before any deeper bounded census is attempted.
    """
    alpha = core.ALL_WORDS[alpha_index]
    hex_entries = tuple(sorted(
        (h2, _mask_rotate(mask, N, shift))
        for h, mask in state.sparse_hex()
        for h2, shift in (LEFT_HEX_ACTION[alpha_index][h],)
    ))
    orbit_entries = tuple(sorted(
        (q2, _mask_rotate(mask, N - 1, shift))
        for q, mask in state.sparse_orbits()
        for q2, shift in (LEFT_ORBIT_ACTION[alpha_index][q],)
    ))
    return (core.left_relabel(state.p, alpha), hex_entries, orbit_entries, state.F, state.S, state.H)


def canonicalize(state: ExactState) -> ExactState:
    """The lexicographically least left-S6 translate of a state.

    This is a child quotient only.  It never assumes a strict
    canonical-parent property, so it cannot remove a complete orbit merely
    because a prefix was reached in another order.
    """
    best_key: Optional[Tuple[object, ...]] = None
    best_alpha: Optional[int] = None
    for alpha_index in range(len(core.ALL_WORDS)):
        key = relabel_sparse_key(state, alpha_index)
        if best_key is None or key < best_key:
            best_key, best_alpha = key, alpha_index
    assert best_alpha is not None
    return relabel_state(state, best_alpha)


def arithmetic_D_reachable(state: ExactState) -> bool:
    """Necessary arithmetic condition for P=121,D=4.

    Every remaining pass start changes D by +4 (new E-orbit) or -1 (old
    E-orbit).  If r pass starts remain, D_final=D-r+5a for some integer
    0<=a<=r.  Ignoring all geometric restrictions makes this only weaker,
    hence safe for pruning.
    """
    r = TARGET_P - state.P
    if r < 0:
        return False
    numerator = TARGET_D - state.D + r
    return numerator % 5 == 0 and 0 <= numerator // 5 <= r


def f1_prune_reason(state: ExactState) -> Optional[str]:
    """Return a *necessary-condition* prune reason, otherwise None."""
    if state.F > TARGET_F:
        return "F_exceeded"
    if state.P > TARGET_P:
        return "P_exceeded"
    if state.O > TARGET_O:
        return "O_exceeded"
    if state.H > TARGET_BUDGET or state.Ndef + state.H > TARGET_BUDGET:
        return "N_plus_H_exceeded"
    if not arithmetic_D_reachable(state):
        return "D_congruence_or_capacity"
    # At least one fresh permutation is required for every future pass start.
    if 720 - state.visited_count < TARGET_P - state.P:
        return "remaining_windows_below_remaining_pass_starts"
    # One fragment permits one abandoned non-current partial hexagon.  The
    # component form additionally catches a third directed arc, which could
    # only be created by a second abandonment.
    if f1_normal_form(state) is None:
        return "partial_hex_requires_more_than_one_fragment"
    # Theorem A's local opening accounting: future new E-orbits can arise at
    # most once per future deep strand start and once per remaining abandonment.
    new_needed = TARGET_O - state.O
    max_future_deep = max(0, (27 - state.H) - state.S)
    max_future_abandonments = TARGET_F - state.F
    if new_needed > max_future_deep + max_future_abandonments:
        return "insufficient_remaining_opening_credit"
    return None


def final_target(state: ExactState) -> bool:
    return (
        state.visited_count == 720
        and state.F == TARGET_F
        and state.P == TARGET_P
        and state.O == TARGET_O
        and state.D == TARGET_D
        and state.Ndef + state.H <= TARGET_BUDGET
    )


def state_to_json(state: ExactState) -> Dict[str, object]:
    return {
        "p": list(state.p),
        "hex_masks": [[h, mask] for h, mask in state.sparse_hex()],
        "orbit_masks": [[q, mask] for q, mask in state.sparse_orbits()],
        "F": state.F,
        "S": state.S,
        "H": state.H,
    }


def state_from_json(data: Mapping[str, object]) -> ExactState:
    hm = [0] * HEX_COUNT
    om = [0] * ORBIT_COUNT
    for h, mask in data["hex_masks"]:  # type: ignore[index]
        hm[int(h)] = int(mask)
    for q, mask in data["orbit_masks"]:  # type: ignore[index]
        om[int(q)] = int(mask)
    return ExactState(tuple(data["p"]), tuple(hm), tuple(om), int(data["F"]), int(data["S"]), int(data["H"]))  # type: ignore[arg-type,index]


def write_json_atomic(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def checkpoint_payload(
    frontier: Sequence[Tuple[int, ExactState]],
    seen: Iterable[Tuple[object, ...]],
    stats: Mapping[str, object],
    config: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "schema": "partial-f1-checkpoint-v1",
        "code_sha256": CODE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": dict(config),
        "stats": dict(stats),
        "frontier": [{"depth": depth, "state": state_to_json(state)} for depth, state in frontier],
        # Full states, not just their keys, are retained in frontier.  The
        # keys below are enough to preserve canonical memoization exactly.
        "seen_keys": [repr(key) for key in seen],
        "note": "Checkpoint is exact for this code SHA. Resume rejects SHA changes.",
    }


def _key_from_repr(text: str) -> Tuple[object, ...]:
    # Checkpoints are local trusted artifacts, never an input format exposed to
    # the network.  literal_eval preserves tuples unlike JSON.  Kept separate
    # to make the trust boundary explicit.
    import ast
    value = ast.literal_eval(text)
    if not isinstance(value, tuple):
        raise ValueError("bad checkpoint state key")
    return value


def load_checkpoint(path: Path) -> Tuple[deque[Tuple[int, ExactState]], set[Tuple[object, ...]], Dict[str, object], Dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "partial-f1-checkpoint-v1":
        raise ValueError("unrecognized checkpoint schema")
    if data.get("code_sha256") != CODE_SHA256 or data.get("core_sha256") != CORE_SHA256:
        raise ValueError("refusing resume across code SHA change")
    frontier = deque((int(item["depth"]), state_from_json(item["state"])) for item in data["frontier"])
    seen = {_key_from_repr(text) for text in data["seen_keys"]}
    return frontier, seen, dict(data["stats"]), dict(data["config"])


def run_census(
    max_depth: int,
    node_limit: int,
    checkpoint: Optional[Path],
    checkpoint_every: int,
    resume: Optional[Path],
) -> Dict[str, object]:
    """Bounded canonical reachable-state census; deliberately no exhaustive mode."""
    if node_limit <= 0:
        raise ValueError("node_limit must be positive; this command is intentionally bounded")
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    config = {"max_depth": max_depth, "node_limit": node_limit, "canonical_children": True}
    if resume is not None:
        frontier, seen, stats, old_config = load_checkpoint(resume)
        if old_config != config:
            raise ValueError("resume configuration differs from requested census")
        stats = dict(stats)
    else:
        start = canonicalize(initial_state())
        frontier = deque([(0, start)])
        seen = {start.stable_key()}
        stats = {
            "expanded": 0,
            "generated": 0,
            "accepted": 1,
            "prunes": {},
            "depth_counts": {"0": 1},
            "N_plus_H_accepted": {"0": 1},
            "fragment_shape_accepted": {"fragment=0;current=1": 1},
        }

    prune_counts: Counter[str] = Counter(stats.get("prunes", {}))  # type: ignore[arg-type]
    depth_counts: Counter[str] = Counter(stats.get("depth_counts", {}))  # type: ignore[arg-type]
    budget_counts: Counter[str] = Counter(stats.get("N_plus_H_accepted", {}))  # type: ignore[arg-type]
    fragment_shapes: Counter[str] = Counter(stats.get("fragment_shape_accepted", {}))  # type: ignore[arg-type]
    started = time.time()
    tracemalloc.start()
    while frontier and int(stats["expanded"]) < node_limit:
        depth, state = frontier.popleft()
        if depth >= max_depth:
            continue
        stats["expanded"] = int(stats["expanded"]) + 1
        for transition in legal_moves(state):
            stats["generated"] = int(stats["generated"]) + 1
            child = transition.state
            reason = f1_prune_reason(child)
            if reason is not None:
                prune_counts[reason] += 1
                continue
            child = canonicalize(child)
            key = child.stable_key()
            if key in seen:
                prune_counts["canonical_state_repeat"] += 1
                continue
            seen.add(key)
            frontier.append((depth + 1, child))
            stats["accepted"] = int(stats["accepted"]) + 1
            depth_counts[str(depth + 1)] += 1
            budget_counts[str(child.Ndef + child.H)] += 1
            form = f1_normal_form(child)
            assert form is not None
            fragment_shapes[
                f"fragment={len(form.fragment_components)};current={len(form.current_components)}"
            ] += 1
        if checkpoint is not None and int(stats["expanded"]) % checkpoint_every == 0:
            stats["prunes"] = dict(sorted(prune_counts.items()))
            stats["depth_counts"] = dict(sorted(depth_counts.items()))
            stats["N_plus_H_accepted"] = dict(sorted(budget_counts.items()))
            stats["fragment_shape_accepted"] = dict(sorted(fragment_shapes.items()))
            write_json_atomic(checkpoint, checkpoint_payload(list(frontier), seen, stats, config))

    stats["prunes"] = dict(sorted(prune_counts.items()))
    stats["depth_counts"] = dict(sorted(depth_counts.items()))
    stats["frontier_remaining"] = len(frontier)
    stats["seen"] = len(seen)
    stats["elapsed_seconds"] = round(time.time() - started, 3)
    stats["tracemalloc_peak_bytes"] = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    stats["N_plus_H_accepted"] = dict(sorted(budget_counts.items()))
    stats["fragment_shape_accepted"] = dict(sorted(fragment_shapes.items()))
    stats["completed_depth_bound"] = not frontier
    stats["hit_node_limit"] = bool(frontier) and int(stats["expanded"]) >= node_limit
    result: Dict[str, object] = {
        "schema": "partial-f1-census-v1",
        "code_sha256": CODE_SHA256,
        "core_sha256": CORE_SHA256,
        "config": config,
        "stats": stats,
        "N_plus_H_accepted": stats["N_plus_H_accepted"],
        "fragment_shape_accepted": stats["fragment_shape_accepted"],
        "checkpoint": str(checkpoint) if checkpoint else None,
        "warning": "bounded diagnostic only; it makes no existence or nonexistence conclusion for the slab",
    }
    if checkpoint is not None:
        write_json_atomic(checkpoint, checkpoint_payload(list(frontier), seen, stats, config))
    return result


def _replay_standard() -> Dict[str, object]:
    raw = (ROOT / "outputs" / "standard_6.txt").read_text(encoding="utf-8")
    symbols = [char for char in raw if char.isdigit()]
    # The archived standard construction is already encoded over 0..5.
    word = tuple(int(char) for char in symbols)
    # A superpermutation word contains non-permutation six-windows between
    # successive permutation occurrences.  The walk consists only of the 720
    # valid occurrence windows, exactly as in core.cmd_verify_word.
    occurrences = tuple(
        (i, word[i : i + N])
        for i in range(len(word) - N + 1)
        if len(set(word[i : i + N])) == N
    )
    windows = tuple(window for _i, window in occurrences)
    state = initial_state(windows[0])
    for (left_position, source), (right_position, target) in zip(occurrences, occurrences[1:]):
        if state.p != source:
            raise AssertionError("replay terminal mismatch")
        action = core.compose(core.inverse(source), target)
        move = MOVE_BY_WEIGHT_ACTION.get((right_position - left_position, action))
        if move is None:
            raise AssertionError("successive standard windows are not an indecomposable tail")
        transition = extend(state, move)
        if transition is None or transition.target != target:
            raise AssertionError("exact engine rejected standard transition")
        state = transition.state
    return {
        "windows": len(windows),
        "visited": state.visited_count,
        "P": state.P,
        "F": state.F,
        "S": state.S,
        "H": state.H,
        "O": state.O,
        "D": state.D,
        "N": state.Ndef,
        "matches_expected": (state.visited_count, state.P, state.F, state.S, state.H, state.O, state.D, state.Ndef)
        == (720, 120, 0, 24, 6, 24, 0, 0),
    }


def _synthetic_controls() -> Dict[str, object]:
    start = initial_state()
    w2 = next(move for move in ALL_MOVES if move.weight == 2)
    frag = extend(start, w2)
    assert frag is not None and frag.abandonment and frag.state.F == 1

    # A rotation cycle supplies a concrete repeated-window negative control.
    state = start
    for _ in range(5):
        r = extend(state, ALL_MOVES[0])
        assert r is not None
        state = r.state
    rotation_collision = extend(state, ALL_MOVES[0]) is None

    # Canonicalization is an equivariant quotient: legal tail labels are not
    # changed by value relabelling because left relabelling commutes with every
    # right tail action.  Test all 720 relabels on an F=1 prefix.
    labels = {t.move.label for t in legal_moves(frag.state)}
    equivariant = True
    sparse_transport_exact = True
    for alpha_index in range(len(core.ALL_WORDS)):
        image = relabel_state(frag.state, alpha_index)
        if {t.move.label for t in legal_moves(image)} != labels:
            equivariant = False
            break
        if relabel_sparse_key(frag.state, alpha_index) != image.stable_key():
            sparse_transport_exact = False
            break
    restored = restore_f1_normal_form(f1_normal_form(frag.state))

    # Minimal mask-level counterexample for dropping M_H.  Both states have
    # the same p, B_Q and resources.  Their only difference is whether p*sigma
    # has already been visited.  The next rotation is legal in one and illegal
    # in the other.  This is an exact-state countermodel, deliberately not
    # advertised as two complete walk-prefix witnesses.
    p = start.p
    q = core.word_after(p, core.SIGMA)
    hq, bq = HEX_POSITION[q]
    hm_a = list(start.hex_masks)
    hm_b = list(start.hex_masks)
    hm_b[hq] |= 1 << bq
    state_a = ExactState(p, tuple(hm_a), start.orbit_masks, 0, 1, 0)
    state_b = ExactState(p, tuple(hm_b), start.orbit_masks, 0, 1, 0)
    mask_counterexample = extend(state_a, ALL_MOVES[0]) is not None and extend(state_b, ALL_MOVES[0]) is None

    return {
        "synthetic_F1_prefix": {
            "move": w2.label,
            "F": frag.state.F,
            "P": frag.state.P,
            "D": frag.state.D,
            "abandonment": frag.abandonment,
        },
        "rotation_repeat_collision_rejected": rotation_collision,
        "D_identity": frag.state.D == 5 * frag.state.O - frag.state.P,
        "normal_form_round_trip": restored == frag.state,
        "left_S6_legal_tail_equivariance_720": equivariant,
        "sparse_canonical_transport_matches_dense_720": sparse_transport_exact,
        "mask_layer_counterexample": mask_counterexample,
        "mask_counterexample_scope": "exact-state countermodel; not claimed as a pair of complete walk prefixes",
    }


def sanity_report() -> Dict[str, object]:
    # An indecomposable tail has no intervening permutation window.  Its
    # declared appended length is therefore the correct walk weight even if
    # source and endpoint happen to admit a different maximal-overlap string.
    def no_intermediate_window(move: Move) -> bool:
        source = core.IDENTITY
        for d in range(1, move.weight):
            candidate = source[d:] + tuple(source[i] for i in move.pi[:d])
            if len(set(candidate)) == N:
                return False
        return True

    tail_weight_ok = all(no_intermediate_window(move) for move in ALL_MOVES)
    standard = _replay_standard()
    controls = _synthetic_controls()
    initial = initial_state()
    report = {
        "schema": "partial-f1-state-sanity-v1",
        "code_sha256": CODE_SHA256,
        "core_sha256": CORE_SHA256,
        "finite_group": {
            "hexagons": HEX_COUNT,
            "E_orbits": ORBIT_COUNT,
            "tail_count_by_weight": {str(w): len(core.tail_permutations(w)) for w in range(1, N + 1)},
            "all_literal_tails_have_no_intermediate_permutation_window": tail_weight_ok,
        },
        "initial": {"P": initial.P, "O": initial.O, "D": initial.D, "N": initial.Ndef},
        "standard_873_replay": standard,
        "controls": controls,
        "status": "pass" if tail_weight_ok and standard["matches_expected"] and all(
            value is True for key, value in controls.items() if isinstance(value, bool)
        ) else "fail",
        "scope": "transition engine and quotient sanity only; no F=1 slab enumeration was run",
    }
    return report


def markdown_sanity(report: Mapping[str, object], census: Optional[Mapping[str, object]] = None) -> str:
    standard = report["standard_873_replay"]
    controls = report["controls"]
    census_section = ""
    if census is not None:
        stats = census["stats"]
        census_section = f"""
## Bounded canonical census (diagnostic only)

The recorded depth-limited run had configuration `{json.dumps(census['config'])}`.
It completed its stated depth bound: `{stats['completed_depth_bound']}`; it
hit a node limit: `{stats['hit_node_limit']}`.

```json
{json.dumps({
    'depth_counts': stats['depth_counts'],
    'accepted': stats['accepted'],
    'generated': stats['generated'],
    'prunes': stats['prunes'],
    'N_plus_H_accepted': census['N_plus_H_accepted'],
    'fragment_shape_accepted': census['fragment_shape_accepted'],
    'tracemalloc_peak_bytes': stats['tracemalloc_peak_bytes'],
}, indent=2)}
```

This is a depth-two finite validation of the state engine, not an enumeration
of the `F=1,D=4` slab.
"""
    return f"""# F=1 exact-state sanity report

Status: **{report['status']}**.  This report validates the transition engine,
the left-`S_6` quotient, and bounded-search prerequisites.  It does **not**
claim an enumeration of `(F,D,N)=(1,4,*)`.

## Fixed finite data

- hexagons: {report['finite_group']['hexagons']}
- `E`-orbits: {report['finite_group']['E_orbits']}
- indecomposable tails by weight: `{report['finite_group']['tail_count_by_weight']}`
- every literal tail has no intervening permutation window: `{report['finite_group']['all_literal_tails_have_no_intermediate_permutation_window']}`

## Positive control: standard length 873

```json
{json.dumps(standard, indent=2)}
```

## Exact-state controls

```json
{json.dumps(controls, indent=2)}
```

`mask_layer_counterexample` is intentionally only a state-level countermodel:
it proves that pass-start masks cannot replace the hexagon membership oracle.
It is not presented as two complete no-repeat walk prefixes.

{census_section}

Code SHA-256: `{report['code_sha256']}`  
Core SHA-256: `{report['core_sha256']}`
"""


def cmd_sanity(args: argparse.Namespace) -> None:
    report = sanity_report()
    output = Path(args.output)
    write_json_atomic(output, report)
    census: Optional[Mapping[str, object]] = None
    census_path = Path(args.census)
    if census_path.exists():
        candidate = json.loads(census_path.read_text(encoding="utf-8"))
        if candidate.get("code_sha256") == report["code_sha256"]:
            census = candidate
    Path(args.markdown).write_text(markdown_sanity(report, census), encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output), "markdown": args.markdown}, indent=2))


def cmd_census(args: argparse.Namespace) -> None:
    report = run_census(args.max_depth, args.node_limit, Path(args.checkpoint) if args.checkpoint else None,
                        args.checkpoint_every, Path(args.resume) if args.resume else None)
    write_json_atomic(Path(args.output), report)
    print(json.dumps({"output": args.output, "stats": report["stats"]}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("sanity", help="run finite transition/canonicalization controls; no enumeration")
    p.add_argument("--output", default=str(ROOT / "outputs" / "f1_state_sanity.json"))
    p.add_argument("--markdown", default=str(ROOT / "outputs" / "F1_STATE_SANITY_REPORT.md"))
    p.add_argument("--census", default=str(ROOT / "outputs" / "f1_depth2_census.json"),
                   help="include this same-code bounded census in the Markdown report when present")
    p.set_defaults(func=cmd_sanity)
    p = sub.add_parser("census", help="bounded canonical state census; node limit must be positive")
    p.add_argument("--max-depth", type=int, default=2)
    p.add_argument("--node-limit", type=int, default=1000)
    p.add_argument("--checkpoint")
    p.add_argument("--checkpoint-every", type=int, default=100)
    p.add_argument("--resume")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_census)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
