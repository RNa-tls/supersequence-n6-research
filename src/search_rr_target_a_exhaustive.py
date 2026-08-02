#!/usr/bin/env python3
"""Round 35: checkpointable exact Target-A traversal.

This is deliberately a *root-local Target-A boundary* search.  It starts
only from the 22 audited capped Round-27 prefix roots and never expands past
the prospective second R joint.  It is not a Target-B or NR6 completion
search.

The exact engine state retains every visited window.  The extra decoration is
only the RR boundary history which ExactState cannot recover: R-event order,
R1 endpoints, and the hub-completer event.  Component ancestry and the hub
mask are recomputed from ExactState at every candidate boundary.

No node cap is a proof condition.  ``--node-limit 0`` is cap-free; an
interruption or a positive limit leaves the root ``INCOMPLETE`` with an exact
checkpoint, never ``EXHAUSTED_NO_TARGET_A``.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
PREFIXES = ROOT / "outputs" / "rr_long_excursion_prefixes.json"
LEDGER = ROOT / "outputs" / "rr_target_a_22_root_ledger.json"
KNOWN_TARGET_B = ROOT / "outputs" / "rr_target_b_survivors.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = _load("round35_macro", WORK / "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
roots = _load("round35_roots", ROOT / "src" / "build_rr_long_excursion_roots.py")

W1 = macro.W1
MOVE = {move.label: move for move in exact.ALL_MOVES}
W2_10 = MOVE["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)
ENGINE_FILES = (
    ROOT / "legacy_research" / "work" / "superperm_partial_f1.py",
    ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py",
    ROOT / "src" / "search_rr_target_a_exhaustive.py",
    ROOT / "src" / "build_rr_long_excursion_roots.py",
)
CHECKPOINT_SCHEMA_V1 = "rr-target-a-exhaustive-checkpoint-v1"
TARGET_A_SAFE_PROFILE = "target_a_semantic_v1"
LEGACY_AREA_A_PROFILE = "legacy_area_a_q2_comparison_v1"
R2_LITERAL_JOINT_SOURCE_TAG = "R2_LITERAL_JOINT_SOURCE_V1"
R2_MACRO_ENTRY_PROVENANCE_TAG = "R2_MACRO_ENTRY_PROVENANCE_ONLY_V1"


@dataclass(frozen=True)
class R2SemanticState:
    """A state plus its non-interchangeable R2 semantic role.

    Macro entry is useful provenance, but it is not the source of a joint
    following a nonempty rotation run.  New source-sensitive code should pass
    ``r2_literal_joint_source(edge)`` to the recognizer.  Raw states remain
    accepted only for historical replay controls and are labelled as such in
    the recognizer output.
    """
    state: Any
    semantic_tag: str


def r2_literal_joint_source(edge) -> R2SemanticState:
    return R2SemanticState(edge.run.state, R2_LITERAL_JOINT_SOURCE_TAG)


def r2_macro_entry_provenance(state) -> R2SemanticState:
    return R2SemanticState(state, R2_MACRO_ENTRY_PROVENANCE_TAG)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def state_hash(state) -> str:
    return sha256_bytes(repr(state.stable_key()).encode("utf-8"))


def code_hashes() -> dict[str, str]:
    return {str(path.relative_to(ROOT)): sha256_file(path) for path in ENGINE_FILES}


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    """The only labels allowed by the inherited Round-27 RR model."""
    return {
        (2, False, False): "Z2",
        (2, True, True): "Z2abandon",
        (3, False, False): "R",
        (3, False, True): "Z3",
    }.get((weight, abandonment, new_orbit), "other")


@dataclass(frozen=True)
class REvent:
    macro_index: int
    kind: str
    source_orbit: int
    source_phase: int
    target_orbit: int
    target_phase: int


@dataclass(frozen=True)
class Completer:
    macro_index: int
    kind: str
    source_orbit: int
    source_phase: int
    target_orbit: int
    target_phase: int


@dataclass(frozen=True)
class Decoration:
    """History not recoverable from ExactState for this boundary question.

    ``hub_id`` and the current hub mask are distinguished-root data.  The
    latter is intentionally *not* copied here: it is a deterministic function
    of ExactState and is included in the key through ExactState itself.
    """

    root_id: str
    root_ell: int
    o_star: int
    hub_id: int
    macro_index: int
    r_events: tuple[REvent, ...]
    hub_touch_count: int
    completer: Optional[Completer]

    @property
    def r_count(self) -> int:
        return len(self.r_events)

    @property
    def r1(self) -> Optional[REvent]:
        return self.r_events[0] if self.r_events else None

    @property
    def branch(self) -> str:
        """CH1/CH2 only once the complete event information exists."""
        c = self.completer
        r1 = self.r1
        if c is None:
            return "UNDECIDED"
        if c.kind == "R" and r1 is not None and c.macro_index == r1.macro_index:
            return "CH1"
        if c.kind == "Z2" and r1 is not None and r1.macro_index < c.macro_index:
            return "CH2"
        return "OTHER_OR_UNDECIDED"

    @property
    def event_order_class(self) -> str:
        """Analysis-only timing class for the first hub-completing event.

        This deliberately does *not* create a third proof branch.  In
        particular, a completion before R1 is an event-order observation, not
        a CH0 alternative to the proved CH1/CH2 recognizers.
        """
        c = self.completer
        r1 = self.r1
        if c is None:
            return "UNDECIDED"
        if r1 is None or c.macro_index < r1.macro_index:
            return "PRE_R_COMPLETER_EVENT_ORDER"
        if c.kind == "R" and c.macro_index == r1.macro_index:
            return "CH1"
        if c.kind == "Z2" and r1.macro_index < c.macro_index:
            return "CH2"
        return "OTHER_POST_R_COMPLETER_EVENT_ORDER"

    def key(self) -> tuple[object, ...]:
        return (
            self.root_ell, self.o_star, self.hub_id, self.macro_index,
            tuple((event.macro_index, event.kind, event.source_orbit, event.source_phase,
                   event.target_orbit, event.target_phase) for event in self.r_events),
            self.hub_touch_count,
            None if self.completer is None else (
                self.completer.macro_index, self.completer.kind,
                self.completer.source_orbit, self.completer.source_phase,
                self.completer.target_orbit, self.completer.target_phase,
            ),
        )

    def to_json(self) -> dict[str, object]:
        return {
            "root_id": self.root_id, "root_ell": self.root_ell,
            "o_star": self.o_star, "hub_id": self.hub_id,
            "macro_index": self.macro_index, "r_events": [asdict(e) for e in self.r_events],
            "hub_touch_count": self.hub_touch_count,
            "completer": None if self.completer is None else asdict(self.completer),
            "branch": self.branch,
            "event_order_class": self.event_order_class,
        }

    @staticmethod
    def from_json(data: Mapping[str, object]) -> "Decoration":
        rs = tuple(REvent(**{k: v for k, v in event.items()})
                   for event in data["r_events"])  # type: ignore[index,union-attr]
        comp_data = data.get("completer")
        comp = None if comp_data is None else Completer(**comp_data)  # type: ignore[arg-type]
        return Decoration(
            root_id=str(data["root_id"]), root_ell=int(data["root_ell"]),
            o_star=int(data["o_star"]), hub_id=int(data["hub_id"]),
            macro_index=int(data["macro_index"]), r_events=rs,
            hub_touch_count=int(data["hub_touch_count"]), completer=comp,
        )


TARGET_A_PRUNE_REGISTRY = [
    {
        "name": "exact_permutation_collision",
        "statement": "exact.extend rejects an already visited permutation window",
        "source": "legacy_research/work/superperm_partial_f1.py::extend",
        "implementation": "iter_raw_macro_candidates",
        "test": "test_collision_is_counted_and_not_expanded",
        "scope": "universally_safe",
    },
    {
        "name": "F_exceeded",
        "statement": "Target A requires F_def=1 at the R2 child; F_def is monotone",
        "source": "research/RR_TARGET_A_DEFINITION.md §2; ExactState.extend",
        "implementation": "target_a_prune_reason",
        "test": "test_target_a_profile_rejects_F_and_H_only_from_the_budget_bundle",
        "scope": "target_a_safe_proved",
    },
    {
        "name": "H_positive",
        "statement": "Target A requires H=0 at the R2 child; H is monotone",
        "source": "research/RR_TARGET_A_DEFINITION.md §2; ExactState.extend",
        "implementation": "target_a_prune_reason",
        "test": "test_target_a_profile_rejects_F_and_H_only_from_the_budget_bundle",
        "scope": "target_a_safe_proved",
    },
    {
        "name": "F1_fragment_normal_form_impossible",
        "statement": "with F_def<=1, more than one abandoned partial hexagon or more than F+1 arcs is impossible",
        "source": "legacy_research/work/superperm_partial_f1.py::f1_normal_form",
        "implementation": "target_a_prune_reason",
        "test": "test_target_a_profile_uses_exact_f1_prefix_invariant",
        "scope": "target_a_safe_proved",
    },
    {
        "name": "rr_r_budget",
        "statement": ("the scoped RR word has at most two R events; a bare short root may enqueue "
                      "R1, while R2 is a boundary and never a child"),
        "source": "src/search_rr_long_prefix_extensions.py::search",
        "implementation": "evaluate_edge",
        "test": "test_legal_first_r_edge_is_enqueued_for_every_short_root; test_long_root_r2_is_recognized_on_edge_and_never_enqueued",
        "scope": "target_a_scope_reduction",
    },
    {
        "name": "hub_touch_count",
        "statement": "with F <= 1, no hexagon can be a joint target more than twice",
        "source": "research/RR_HUB_TOUCH_COUNT.md",
        "implementation": "advance_decoration",
        "test": "test_hub_touch_counter_is_monotone",
        "scope": "universally_safe_under_F_le_1",
    },
]
# Backwards-compatible public name.  It now denotes the *Target-A-only*
# registry, never the larger Q2/Area-A completion bundle.
PRUNE_REGISTRY = TARGET_A_PRUNE_REGISTRY


LEGACY_AREA_A_PRUNE_REGISTRY = [
    {
        "name": "area_a_necessary_conditions",
        "statement": "The complete P/O/D/N/Phi/window completion bundle used by historical Area-A/Q2 traversals.",
        "scope": "q2_target_b_completion_only",
        "implementation": "macro.area_a_prune_reason",
    },
]


def registry_for_profile(profile: str) -> list[dict[str, object]]:
    if profile == TARGET_A_SAFE_PROFILE:
        return TARGET_A_PRUNE_REGISTRY
    if profile == LEGACY_AREA_A_PROFILE:
        return LEGACY_AREA_A_PRUNE_REGISTRY
    raise ValueError(f"unknown prune profile {profile!r}")


def registry_hash(profile: str = TARGET_A_SAFE_PROFILE) -> str:
    return sha256_bytes(json.dumps(registry_for_profile(profile), sort_keys=True).encode("utf-8"))


def target_a_prune_reason(state) -> Optional[str]:
    """Necessary prefix restrictions for the semantic Target-A predicate only.

    Target A asks for an R2 child with ``F_def=1``, ``H=0``, and the
    same-component property.  Its roots already have ``F_def=1``.  Since F
    and H never decrease, only their exceeded values can be discarded before
    an R2.  The F<=1 partial-hexagon normal form is likewise a prefix
    invariant.  In contrast, P/O/D/N/Phi and remaining-completion capacity
    are Q2/Target-B data and are intentionally absent here.
    """
    if state.F > exact.TARGET_F:
        return "F_exceeded"
    if state.H > 0:
        return "H_positive"
    if exact.f1_normal_form(state) is None:
        return "F1_fragment_normal_form_impossible"
    return None


def prune_reason_for_profile(state, profile: str) -> Optional[str]:
    """Select a hash-bound prune profile; legacy Area A is audit-only."""
    if profile == TARGET_A_SAFE_PROFILE:
        return target_a_prune_reason(state)
    if profile == LEGACY_AREA_A_PROFILE:
        return macro.area_a_prune_reason(state, macro.AREA_A)
    raise ValueError(f"unknown prune profile {profile!r}")


def phi(state) -> int:
    return 5 + 6 * (exact.TARGET_P - state.P) - (720 - state.visited_count)


def incidence_components(state):
    """Fresh union-find from ExactState; no history summary is trusted."""
    parent: dict[tuple[str, int], tuple[str, int]] = {}

    def find(node: tuple[str, int]) -> tuple[str, int]:
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(left: tuple[str, int], right: tuple[str, int]) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for orbit, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[orbit])[phase]
                union(("q", orbit), ("h", core.hexagon_id(port)))
    return parent, find


def component_digest(state) -> str:
    parent, find = incidence_components(state)
    groups: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for node in parent:
        groups.setdefault(find(node), []).append(node)
    normal = tuple(sorted(tuple(sorted(nodes)) for nodes in groups.values()))
    return sha256_bytes(repr(normal).encode("utf-8"))


def hub_mask(state, decoration: Decoration) -> int:
    return int(state.hex_masks[decoration.hub_id])


def advance_decoration(state_before_run, transition, dec: Decoration) -> Decoration:
    """Pure history update from an exact macro joint.

    The source coordinates come from the literal state after the rotation run,
    never from a cached event record.  This is the update function exercised
    by the state-key audit.
    """
    source_orbit, source_phase = exact.ORBIT_PHASE[state_before_run.p]
    target_orbit, target_phase = exact.ORBIT_PHASE[transition.target]
    kind = joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit)
    index = dec.macro_index + 1
    events = dec.r_events
    if kind == "R":
        events = events + (REvent(index, kind, source_orbit, source_phase,
                                  target_orbit, target_phase),)
    touch_count = dec.hub_touch_count
    completer = dec.completer
    if core.hexagon_id(transition.target) == dec.hub_id:
        touch_count += 1
        if completer is None:
            completer = Completer(index, kind, source_orbit, source_phase,
                                  target_orbit, target_phase)
    return Decoration(
        root_id=dec.root_id, root_ell=dec.root_ell, o_star=dec.o_star,
        hub_id=dec.hub_id, macro_index=index, r_events=events,
        hub_touch_count=touch_count, completer=completer,
    )


def initial_decoration(record: Mapping[str, object]) -> tuple[object, Decoration]:
    """Literal reconstruction of a root and all decoration, including R1."""
    state = exact.initial_state()
    ell = int(record["root_ell"])
    for _ in range(ell):
        rotation = exact.extend(state, W1)
        if rotation is None:
            raise AssertionError("abandonment-root rotation unexpectedly collides")
        state = rotation.state
    abandonment = exact.extend(state, W2_10)
    if abandonment is None:
        raise AssertionError("abandonment root is illegal")
    state = abandonment.state
    dec = Decoration(
        root_id=str(record["root_id"]), root_ell=ell, o_star=int(record["o_star"]),
        hub_id=HUB, macro_index=0, r_events=(), hub_touch_count=0, completer=None,
    )
    for label in record["literal_joint_word"]:  # type: ignore[index]
        before = state
        for _ in range(5):
            rotation = exact.extend(state, W1)
            if rotation is None:
                raise AssertionError("stored root rotation failed literal replay")
            state = rotation.state
        joint = exact.extend(state, MOVE[str(label)])
        if joint is None:
            raise AssertionError("stored root joint failed literal replay")
        dec = advance_decoration(state, joint, dec)
        state = joint.state
        if before is state:
            raise AssertionError("nonrotation root joint did not advance")
    if state_hash(state) != str(record["post_return_state_hash"]):
        raise AssertionError(f"root replay hash mismatch: {record['root_id']}")
    if dec.r_count != int(record["r_count"]):
        raise AssertionError(f"R-count mismatch: {record['root_id']}")
    return state, dec


def iter_raw_macro_candidates(state) -> Iterator[tuple[Optional[object], Optional[str]]]:
    """Yield every literal macro candidate, including rejected joint collisions."""
    for run in macro.rotation_runs(state):
        for move in macro.NONROT_H0:
            joint = exact.extend(run.state, move)
            if joint is None:
                yield None, "exact_permutation_collision"
            else:
                yield macro.MacroEdge(run, joint), None


def edge_json(edge) -> dict[str, object]:
    pre = edge.run.state
    sq, sph = exact.ORBIT_PHASE[pre.p]
    tq, tph = exact.ORBIT_PHASE[edge.joint.target]
    return {
        "label": edge.label, "rotation_length": edge.run.ell,
        "joint": edge.joint.move.label,
        "kind": joint_kind(edge.joint.move.weight, edge.joint.abandonment, edge.joint.new_orbit),
        "source": [sq, sph], "target": [tq, tph],
        "target_hexagon": core.hexagon_id(edge.joint.target),
    }


R2_OUTCOME_VOCABULARY = (
    "TARGET_A_HIT", "wrong_R_count", "wrong_Ndef", "wrong_Fdef",
    "wrong_boundary_timing", "not_same_component", "recognizer_geometry_failure",
    "hub_touch_failure", "exact_collision", "other_explicit_reason",
)

# The historical ``recognizer_geometry_failure`` outcome was deliberately
# conservative: it meant only that at least one of the two R2 E-orbits was
# absent from the *pre-R2* incidence forest.  It was never a mathematical
# predicate in its own right.  Keep that parent outcome for backwards
# compatibility with existing v3 ledgers, but require every occurrence to
# carry exactly one member of this deterministic child taxonomy.  The zero
# entries are intentional: they make the complete decision order auditable,
# rather than silently conflating an unobserved case with an omitted case.
GEOMETRY_FAILURE_VOCABULARY = (
    "no_completer",
    "completer_wrong_target_orbit",
    "completer_wrong_target_phase",
    "r2_wrong_source_orbit",
    "r2_wrong_target_orbit",
    "r2_wrong_ell",
    "r2_wrong_joint",
    "wrong_hub_residual_position",
    "wrong_event_order",
    "chaining_failure",
    "terminal_boundary_mismatch",
    "other_asserted_reason",
)


def component_summary(state) -> dict[str, object]:
    """Return a deterministic, history-free incidence-component summary.

    Component identifiers are hashes of the complete sorted node set, never
    union-find roots.  Thus they are stable across path compression order and
    can be exported as independent evidence for an R2 relation test.
    """
    parent, find = incidence_components(state)
    groups: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for node in parent:
        groups.setdefault(find(node), []).append(node)
    node_component: dict[tuple[str, int], dict[str, object]] = {}
    components: list[dict[str, object]] = []
    for nodes in sorted((tuple(sorted(group)) for group in groups.values())):
        e_orbits = tuple(node[1] for node in nodes if node[0] == "q")
        hexagons = tuple(node[1] for node in nodes if node[0] == "h")
        identifier = sha256_bytes(repr(nodes).encode("utf-8"))[:16]
        component = {
            "id": identifier,
            "class": {"e_orbits": len(e_orbits), "hexagons": len(hexagons),
                      "incidences": len(nodes)},
            "e_orbits": list(e_orbits), "hexagons": list(hexagons),
        }
        components.append(component)
        for node in nodes:
            node_component[node] = component
    return {
        "component_count": len(components),
        "components": components,
        "node_component": node_component,
    }


def _component_ref(summary: Mapping[str, object], node: tuple[str, int]) -> Optional[dict[str, object]]:
    component = summary["node_component"].get(node)  # type: ignore[index,union-attr]
    if component is None:
        return None
    return {"id": component["id"], "class": component["class"]}


def geometry_failure_reason(*, source_present: bool, target_present: bool) -> str:
    """Classify the former opaque geometry exit, with no residual bucket.

    This function is called *only* at the old opaque exit.  Its precondition
    is therefore ``not source_present or not target_present``.  If both are
    missing, source absence takes priority; the target absence is retained as
    an orthogonal flag in the serialized record.  Every remaining taxonomy
    member is a declared-but-unobserved normal-form diagnostic, not an
    alternative hidden under a generic label.  Reaching the final branch is a
    programming error, so ``other_asserted_reason`` is never emitted.
    """
    if not source_present:
        return "r2_wrong_source_orbit"
    if not target_present:
        return "r2_wrong_target_orbit"
    raise AssertionError("geometry taxonomy invoked without a missing R2 incidence endpoint")


def geometry_failure_record(joint_source_state, edge, before: Decoration, after: Decoration,
                            *, depth: Optional[int] = None) -> dict[str, object]:
    """Serialize enough endpoint evidence to independently reclassify one exit."""
    transition = edge.joint
    sq, sph = exact.ORBIT_PHASE[joint_source_state.p]
    tq, tph = exact.ORBIT_PHASE[transition.target]
    parent, _find = incidence_components(joint_source_state)
    source_present = ("q", sq) in parent
    target_present = ("q", tq) in parent
    reason = geometry_failure_reason(source_present=source_present, target_present=target_present)
    candidate_key = (state_hash(joint_source_state), transition.move.label, edge.run.ell,
                     sq, sph, tq, tph, before.key())
    return {
        "candidate_id": sha256_bytes(repr(candidate_key).encode("utf-8")),
        "depth": depth,
        "literal_joint_source_state_hash": state_hash(joint_source_state),
        "macro_label": f"rot^{edge.run.ell};{transition.move.label}",
        "source_orbit": sq, "source_phase": sph,
        "target_orbit": tq, "target_phase": tph,
        "source_orbit_present_in_pre_r2_forest": source_present,
        "target_orbit_present_in_pre_r2_forest": target_present,
        "primary_reason": reason,
        # Preserve overlap information instead of pretending a primary label
        # is a causal proof.  The independent verifier checks these flags.
        "secondary_missing_endpoint_flags": {
            "source_missing": not source_present,
            "target_missing": not target_present,
        },
        "r1": None if before.r1 is None else asdict(before.r1),
        "completer": None if after.completer is None else asdict(after.completer),
        "event_order_class": after.event_order_class,
    }


def same_component_failure_record(macro_entry_state, edge, before: Decoration, after: Decoration,
                                  *, depth: int) -> dict[str, object]:
    """Detailed, immutable evidence for one `not_same_component` R2 edge."""
    transition = edge.joint
    # A macro candidate may rotate before executing its joint.  Target-A
    # geometry is evaluated at the literal joint source, never macro entry.
    # Retain macro-entry only for provenance, so callers cannot silently use
    # it for the source-orbit predicate.
    joint_source_state = edge.run.state
    sq, sph = exact.ORBIT_PHASE[joint_source_state.p]
    tq, tph = exact.ORBIT_PHASE[transition.target]
    pre = component_summary(joint_source_state)
    post = component_summary(transition.state)
    source = _component_ref(pre, ("q", sq))
    target = _component_ref(pre, ("q", tq))
    post_source = _component_ref(post, ("q", sq))
    post_target = _component_ref(post, ("q", tq))
    if source is None or target is None:
        raise AssertionError("same-component failure record requires both pre-R2 endpoints")
    if source["id"] == target["id"]:
        raise AssertionError("same-component failure record received a same-component R2")
    r1_target = None if before.r1 is None else _component_ref(pre, ("q", before.r1.target_orbit))
    would_merge = (post_source is not None and post_target is not None and
                   post_source["id"] == post_target["id"])
    candidate_key = (state_hash(joint_source_state), transition.move.label, edge.run.ell,
                     sq, sph, tq, tph, before.key())
    return {
        "candidate_id": sha256_bytes(repr(candidate_key).encode("utf-8")),
        "depth": depth,
        "macro_entry_state_hash": state_hash(macro_entry_state),
        "literal_joint_source_state_hash": state_hash(joint_source_state),
        "macro_label": f"rot^{edge.run.ell};{transition.move.label}",
        "r1_target_orbit": None if before.r1 is None else before.r1.target_orbit,
        "r1_target_component": r1_target,
        "r2_source_orbit": sq, "r2_source_phase": sph,
        "r2_source_component": source,
        "r2_target_orbit": tq, "r2_target_phase": tph,
        "r2_target_component": target,
        "component_count_pre_r2": pre["component_count"],
        "component_count_post_r2": post["component_count"],
        "candidate_edge_would_merge_components": would_merge,
        "exact_relation_checked": (
            "pre-R2 incidence forest: component(q,R2.source) == component(q,R2.target)"),
        "pre_r2_component_digest": component_digest(joint_source_state),
        "post_r2_component_digest": component_digest(transition.state),
        "chaining": before.r1 is not None and before.r1.target_orbit == sq,
        "event_order_class": after.event_order_class,
    }


def r1_event_export(edge, before: Decoration, after: Decoration,
                    trace: tuple[dict[str, object], ...]) -> tuple[str, dict[str, object]]:
    """Serialize an accepted R1 event without treating Phi/M as a prune.

    The literal predecessor is the state *after* the macro rotation run and
    immediately before its R joint.  This removes any ambiguity about whether
    a reported coordinate was measured at macro entry or at the R event.
    """
    predecessor = edge.run.state
    child = edge.state
    source_orbit, source_phase = exact.ORBIT_PHASE[predecessor.p]
    target_orbit, target_phase = exact.ORBIT_PHASE[child.p]
    event_key = (state_hash(predecessor), edge.label, source_orbit, source_phase,
                 target_orbit, target_phase)
    event_id = sha256_bytes(repr(event_key).encode("utf-8"))
    coordinates = lambda state: {
        "P": state.P, "O": state.O, "Ndef": state.Ndef,
        "F": state.F, "H": state.H,
    }
    return event_id, {
        "event_id": event_id,
        "literal_predecessor_word": list(predecessor.p),
        "literal_predecessor_state_hash": state_hash(predecessor),
        "macro_label": edge.label,
        "ell": edge.run.ell,
        "source_permutation": list(predecessor.p),
        "target_permutation": list(child.p),
        "source_orbit": source_orbit, "source_phase": source_phase,
        "target_orbit": target_orbit, "target_phase": target_phase,
        "Phi_before": phi(predecessor), "Phi_after": phi(child),
        "M_before": predecessor.P - 5 * predecessor.O,
        "M_after": child.P - 5 * child.O,
        "coordinate_before": coordinates(predecessor),
        "coordinate_after": coordinates(child),
        "hub_popcount_before": hub_mask(predecessor, before).bit_count(),
        "hub_popcount_after": hub_mask(child, after).bit_count(),
        "completer_timing": None if after.completer is None else asdict(after.completer),
        "event_order_class": after.event_order_class,
        "resulting_decorated_key": repr(decorated_key(child, after)),
        "literal_macro_trace": list(trace + (edge_json(edge),)),
    }


def target_a_recognizer(joint_source_state, transition, before: Decoration, after: Decoration) -> dict[str, object]:
    """Exact boundary recognizer.  Same-component and chaining are outputs.

    The recognizer does not impose either relation as an acceptance condition;
    only the former is the historical Target-A property.  Target B/C are not
    considered here.
    """
    # ``joint_source_state`` is specifically the state after the macro
    # rotation run and immediately before ``transition``.  Using macro entry
    # here changes R2's source orbit and invalidates the literal boundary
    # predicate.
    if isinstance(joint_source_state, R2SemanticState):
        if joint_source_state.semantic_tag != R2_LITERAL_JOINT_SOURCE_TAG:
            raise ValueError("Target-A R2 recognizer requires literal joint-source semantics")
        source_state_tag = joint_source_state.semantic_tag
        joint_source_state = joint_source_state.state
    else:
        # Compatibility is intentionally diagnostic-only.  New boundary code
        # must use the wrapper above; regression fixtures use this branch to
        # demonstrate why macro entry is invalid.
        source_state_tag = "LEGACY_UNTAGGED_STATE_ARGUMENT"
    sq, sph = exact.ORBIT_PHASE[joint_source_state.p]
    tq, tph = exact.ORBIT_PHASE[transition.target]
    parent, find = incidence_components(joint_source_state)
    source_root = find(("q", sq)) if ("q", sq) in parent else None
    target_root = find(("q", tq)) if ("q", tq) in parent else None
    source_present = source_root is not None
    target_present = target_root is not None
    same_component = source_root is not None and source_root == target_root
    r1 = before.r1
    chaining = r1 is not None and r1.target_orbit == sq
    # This is intentionally diagnostic only.  Area A is the Q2/Target-B
    # completion envelope, while Target A is an R2 boundary predicate.
    area_reason = macro.area_a_prune_reason(transition.state, macro.AREA_A)
    conditions = {
        "exactly_two_R_events": before.r_count == 1 and after.r_count == 2,
        "immediately_after_R2": joint_kind(transition.move.weight, transition.abandonment,
                                             transition.new_orbit) == "R",
        "F_def_equals_1": transition.state.F == 1,
        "H_equals_0": transition.state.H == 0,
        "hub_touch_count_le_2": after.hub_touch_count <= 2,
        "same_component": same_component,
    }
    target = all(conditions.values())
    failure_order = (
        "exactly_two_R_events", "immediately_after_R2", "F_def_equals_1",
        "H_equals_0", "hub_touch_count_le_2", "same_component",
    )
    failed_conditions = [name for name in failure_order if not conditions[name]]
    if target:
        r2_outcome = "TARGET_A_HIT"
        primary_failure = None
    elif not conditions["exactly_two_R_events"]:
        r2_outcome = "wrong_R_count"
        primary_failure = r2_outcome
    elif not conditions["immediately_after_R2"]:
        r2_outcome = "wrong_boundary_timing"
        primary_failure = r2_outcome
    elif not conditions["F_def_equals_1"]:
        r2_outcome = "wrong_Fdef"
        primary_failure = r2_outcome
    elif not conditions["H_equals_0"]:
        # The requested R2 ledger has no separate H entry.  Preserve the
        # exact reason in ``r2_detail_reason`` without inventing a semantic
        # Ndef condition for Target A.
        r2_outcome = "other_explicit_reason"
        primary_failure = r2_outcome
    elif not conditions["hub_touch_count_le_2"]:
        r2_outcome = "hub_touch_failure"
        primary_failure = r2_outcome
    elif source_root is None or target_root is None:
        r2_outcome = "recognizer_geometry_failure"
        primary_failure = r2_outcome
    elif not conditions["same_component"]:
        r2_outcome = "not_same_component"
        primary_failure = r2_outcome
    else:  # Defensive: the outcome vocabulary must remain total.
        r2_outcome = "other_explicit_reason"
        primary_failure = r2_outcome
    return {
        "is_target_a": target,
        "conditions": conditions,
        "area_a_reason": area_reason,
        "source_orbit": sq, "source_phase": sph,
        "target_orbit": tq, "target_phase": tph,
        "same_component": same_component,
        "chaining": chaining,
        "CH_branch": after.branch,
        "event_order_class": after.event_order_class,
        "r2_primary_failure": primary_failure,
        "r2_outcome": r2_outcome,
        "geometry_failure_reason": (
            geometry_failure_reason(source_present=source_present, target_present=target_present)
            if source_root is None or target_root is None else None),
        "r2_endpoint_presence": {
            "source_orbit_present_in_pre_r2_forest": source_present,
            "target_orbit_present_in_pre_r2_forest": target_present,
        },
        "r2_failed_conditions": failed_conditions,
        "r2_detail_reason": (
            "H_positive" if not conditions["H_equals_0"] else
            None if target else ",".join(failed_conditions)
        ),
        "q2_area_a_reason_diagnostic": area_reason,
        "literal_joint_source_state_hash": state_hash(joint_source_state),
        "source_state_semantic_tag": source_state_tag,
        "component_digest": component_digest(joint_source_state),
        "pre_hub_mask": hub_mask(joint_source_state, before),
        "post_r2_state_hash": state_hash(transition.state),
        "phi": phi(transition.state),
        "coordinate": {
            "P": transition.state.P, "F_def": transition.state.F,
            "S": transition.state.S, "H": transition.state.H,
            "O": transition.state.O, "D": transition.state.D,
            "Ndef": transition.state.Ndef, "visited": transition.state.visited_count,
        },
        "Target_B_or_C_tested": False,
    }


def decorated_key(state, dec: Decoration) -> tuple[object, ...]:
    """Conservative raw key.  No unproved history quotient is used."""
    return (state.stable_key(), dec.key())


def evaluate_edge(state, dec: Decoration, edge, *,
                  prune_profile: str = TARGET_A_SAFE_PROFILE) -> tuple[str, Optional[Decoration], Optional[dict[str, object]]]:
    """Classify a literal candidate without mutating global traversal state."""
    transition = edge.joint
    child_dec = advance_decoration(edge.run.state, transition, dec)
    kind = joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit)
    if kind == "other":
        return "outside_RR_joint_model", None, None
    if kind == "R":
        # A long-prefix root has already recorded R1, but a bare short root
        # has not.  The latter must be allowed to enter the R1 state before a
        # prospective R2 can be recognized.  Treating every R edge as an R2
        # terminal silently searched only the pre-R subspace of short roots.
        if dec.r_count == 0:
            if child_dec.r_count != 1:
                raise AssertionError("R1 child did not increment the R counter")
            if child_dec.hub_touch_count > 2:
                return "hub_touch_count_exceeded", None, None
            reason = prune_reason_for_profile(transition.state, prune_profile)
            if reason is not None:
                return f"{prune_profile}:{reason}", None, None
            return "child", child_dec, None
        if dec.r_count == 1:
            if child_dec.r_count != 2:
                raise AssertionError("R2 boundary did not increment the R counter")
            recognizer = target_a_recognizer(
                r2_literal_joint_source(edge), transition, dec, child_dec
            )
            return ("FOUND_TARGET_A" if recognizer["is_target_a"] else "r2_not_target"), child_dec, recognizer
        if child_dec.r_count > 2:
            return "rr_R_budget_exceeded", None, None
        return "rr_R_budget_exceeded", None, None
    if child_dec.r_count >= 2:
        return "rr_R_budget_exceeded", None, None
    if child_dec.hub_touch_count > 2:
        return "hub_touch_count_exceeded", None, None
    reason = prune_reason_for_profile(transition.state, prune_profile)
    if reason is not None:
        return f"{prune_profile}:{reason}", None, None
    return "child", child_dec, None


def successor_signature(state, dec: Decoration, *,
                        prune_profile: str = TARGET_A_SAFE_PROFILE) -> tuple[tuple[object, ...], ...]:
    """Deterministic one-step signature for state-key soundness tests."""
    rows = []
    for edge, collision in iter_raw_macro_candidates(state):
        if collision:
            rows.append(("collision", collision))
            continue
        assert edge is not None
        kind, child_dec, recognition = evaluate_edge(state, dec, edge, prune_profile=prune_profile)
        if kind == "child":
            assert child_dec is not None
            rows.append((edge.label, kind, decorated_key(edge.state, child_dec)))
        elif kind == "FOUND_TARGET_A":
            assert recognition is not None
            rows.append((edge.label, kind, tuple(sorted(recognition["conditions"].items()))))
        else:
            rows.append((edge.label, kind))
    return tuple(sorted(rows, key=repr))


def load_audited_roots(ledger_path: Path, prefixes_path: Path) -> list[dict[str, object]]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    prefixes = json.loads(prefixes_path.read_text(encoding="utf-8"))["prefixes"]
    rows = []
    for entry in ledger["roots"]:
        if entry["old_round27_status"] != "INCOMPLETE":
            continue
        record = dict(prefixes[int(entry["prefix_index"])])
        record["root_id"] = entry["root_id"]
        if record["root_ell"] != entry["root_ell"] or record["literal_joint_word"] != entry["literal_joint_word"]:
            raise AssertionError(f"ledger/prefix disagreement for {entry['root_id']}")
        rows.append(record)
    rows.sort(key=lambda r: int(str(r["root_id"]).rsplit("-", 1)[1]))
    if len(rows) != 22:
        raise AssertionError(f"expected exactly 22 audited roots, found {len(rows)}")
    return rows


def checkpoint_config(record: Mapping[str, object], node_limit: int, max_depth: Optional[int],
                      config_extra: Optional[Mapping[str, object]] = None, *,
                      prune_profile: str = TARGET_A_SAFE_PROFILE) -> dict[str, object]:
    """Return the complete, hash-bound checkpoint identity.

    ``config_extra`` is deliberately an additive provenance hook for a
    separately named root universe.  It changes the checkpoint identity, so
    a short-root checkpoint can never be resumed as a historical long-prefix
    checkpoint (or conversely).  The core traversal does not inspect it.
    """
    config: dict[str, object] = {
        "schema": "rr-target-a-exhaustive-config-v1",
        "root_id": record["root_id"],
        "root_literal_hash": sha256_bytes(repr((record["root_ell"], record["literal_joint_word"])).encode("utf-8")),
        "node_limit": node_limit, "max_depth": max_depth,
        "traversal": "deterministic-LIFO-by-reversed-label",
        "engine_hashes": code_hashes(),
        "prune_profile": prune_profile,
        "prune_registry_hash": registry_hash(prune_profile),
        "recognizer_hash": sha256_bytes(Path(__file__).read_bytes()),
    }
    if config_extra:
        collision = set(config).intersection(config_extra)
        if collision:
            raise ValueError(f"checkpoint config extension overwrites core keys: {sorted(collision)}")
        config.update(dict(config_extra))
    return config


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def checkpoint_payload_schema(config: Mapping[str, object]) -> str:
    """Return the explicit payload schema bound into a checkpoint config.

    Historical long-prefix checkpoints use v1 by default.  A separately
    versioned traversal, such as the corrected bare-short-root R1 search,
    must supply an explicit schema in its additive config.  This prevents a
    compatible-looking old JSON file from being resumed under changed state
    semantics.
    """
    schema = config.get("checkpoint_payload_schema", CHECKPOINT_SCHEMA_V1)
    if not isinstance(schema, str) or not schema:
        raise ValueError("invalid checkpoint payload schema in configuration")
    return schema


def serialize_frontier(frontier: Sequence[tuple[int, object, Decoration, tuple[dict[str, object], ...]]]) -> list[dict[str, object]]:
    return [{
        "depth": depth, "state": exact.state_to_json(state),
        "decoration": dec.to_json(), "trace": list(trace),
    } for depth, state, dec, trace in frontier]


def decode_key(text: str) -> tuple[object, ...]:
    value = ast.literal_eval(text)
    if not isinstance(value, tuple):
        raise ValueError("bad decorated state key in checkpoint")
    return value


def write_checkpoint(path: Path, config: Mapping[str, object],
                     frontier: Sequence[tuple[int, object, Decoration, tuple[dict[str, object], ...]]],
                     seen: Iterable[tuple[object, ...]], stats: Mapping[str, object],
                     boundaries: Sequence[Mapping[str, object]], lineage: Sequence[str]) -> str:
    payload = {
        "schema": checkpoint_payload_schema(config), "config": dict(config),
        "frontier": serialize_frontier(frontier),
        "seen_keys": sorted(repr(key) for key in seen), "stats": dict(stats),
        "boundaries": list(boundaries), "checkpoint_lineage": list(lineage),
        "complete_frontier_snapshot": True,
    }
    atomic_json(path, payload)
    return sha256_file(path)


def load_checkpoint(path: Path, config: Mapping[str, object]):
    raw = json.loads(path.read_text(encoding="utf-8"))
    expected_schema = checkpoint_payload_schema(config)
    if raw.get("schema") != expected_schema:
        raise ValueError(f"checkpoint payload schema mismatch: expected {expected_schema!r}")
    if raw.get("config") != dict(config):
        raise ValueError("checkpoint configuration, code hash, or root differs")
    if not raw.get("complete_frontier_snapshot"):
        raise ValueError("checkpoint does not certify a complete frontier snapshot")
    frontier = []
    for item in raw["frontier"]:
        frontier.append((int(item["depth"]), exact.state_from_json(item["state"]),
                         Decoration.from_json(item["decoration"]), tuple(item["trace"])))
    seen = {decode_key(text) for text in raw["seen_keys"]}
    return frontier, seen, dict(raw["stats"]), list(raw["boundaries"]), list(raw["checkpoint_lineage"])


def boundary_canonical_hash(state) -> str:
    return state_hash(exact.canonicalize(state))[:16]


_KNOWN_CANONICAL_HASHES: Optional[set[str]] = None


def known_boundary_canonical_hashes() -> set[str]:
    """Reconstruct the existing 18 boundary states before canonical comparison.

    ``rr_target_b_survivors.json`` labels its stored hashes
    ``canonical_state_hash`` but, in its producer, the field is the raw-state
    hash.  A true left-S6 comparison must therefore replay the 12 historical
    and six long records, then canonicalize each exact state here.  This is
    small, deterministic preprocessing, not a Target-B re-search.
    """
    global _KNOWN_CANONICAL_HASHES
    if _KNOWN_CANONICAL_HASHES is not None:
        return _KNOWN_CANONICAL_HASHES
    producer = _load("round35_known_boundary_replay", ROOT / "src" / "analyze_rr_target_b_survivors.py")
    preps = json.loads((ROOT / "outputs" / "rr_preparation_words.json").read_text(encoding="utf-8"))
    long = json.loads((ROOT / "outputs" / "rr_six_counterexamples.json").read_text(encoding="utf-8"))
    hashes = set()
    for ell, result in preps["results_by_ell"].items():
        for prep in result["preparations"]:
            state = producer.replay_historical(int(ell), prep)
            if state is not None:
                hashes.add(sha256_bytes(repr(producer.exact.canonicalize(state).stable_key()).encode("utf-8"))[:16])
    for witness in long["witnesses"]:
        state = producer.replay_long(witness)
        hashes.add(sha256_bytes(repr(producer.exact.canonicalize(state).stable_key()).encode("utf-8"))[:16])
    if len(hashes) != 18:
        raise AssertionError(f"expected 18 reconstructed known canonical Target-A states, got {len(hashes)}")
    _KNOWN_CANONICAL_HASHES = hashes
    return hashes


def coarse_capacity(state) -> dict[str, object]:
    """Round-30 B+R capacity theorem, recomputed from the exact boundary."""
    B = exact.TARGET_P - state.P
    o_cap = exact.TARGET_O - state.O
    r_cap = max(macro.AREA_A.n_limit - state.Ndef, 0)
    bound = 5 * (o_cap + r_cap) + 4
    return {"B": B, "O_cap": o_cap, "R_cap": r_cap, "bound": bound,
            "verdict": "CAPACITY_IMPOSSIBLE" if B > bound else "CAPACITY_SURVIVOR"}


def dispatch_target_b(boundary: Mapping[str, object], state) -> dict[str, object]:
    canonical = boundary_canonical_hash(state)
    if canonical in known_boundary_canonical_hashes():
        return {"classification": "KNOWN_BOUNDARY", "canonical_state_hash": canonical,
                "target_b_rerun": False, "reason": "known boundary: preserve prior elimination provenance"}
    coarse = coarse_capacity(state)
    if coarse["verdict"] == "CAPACITY_IMPOSSIBLE":
        return {"classification": "NEW_BOUNDARY", "canonical_state_hash": canonical,
                "coarse_capacity": coarse, "phase_refinement": "NOT_NEEDED",
                "r_reuse_penalty": "NOT_NEEDED", "flow_first": "NOT_NEEDED"}
    # Generic arbitrary-boundary implementations of R31/R32 need their own
    # validated input normal form.  Do not silently reuse their historical
    # corpus scripts here; retain the boundary for that explicit next stage.
    return {"classification": "NEW_BOUNDARY", "canonical_state_hash": canonical,
            "coarse_capacity": coarse, "phase_refinement": "PENDING_GENERIC_VALIDATION",
            "r_reuse_penalty": "PENDING_GENERIC_VALIDATION", "flow_first": "NOT_DISPATCHED"}


def search_root(record: Mapping[str, object], *, node_limit: int = 0,
                max_depth: Optional[int] = None, checkpoint: Optional[Path] = None,
                checkpoint_every: int = 1000, resume: Optional[Path] = None,
                checkpoint_config_extra: Optional[Mapping[str, object]] = None,
                prune_profile: str = TARGET_A_SAFE_PROFILE,
                capture_r2_diagnostics: bool = False,
                capture_frontier_snapshot: bool = False) -> dict[str, object]:
    """Exact root-local traversal.  Positive node/max-depth stops are incomplete."""
    config = checkpoint_config(record, node_limit, max_depth, checkpoint_config_extra,
                               prune_profile=prune_profile)
    if resume is not None:
        frontier, seen, stats, boundaries, lineage = load_checkpoint(resume, config)
        lineage = lineage + [sha256_file(resume)]
    else:
        start, decoration = initial_decoration(record)
        frontier = [(0, start, decoration, tuple())]
        seen = {decorated_key(start, decoration)}
        stats: dict[str, object] = {
            "expanded": 0, "generated_edges": 0, "exact_states": {repr(start.stable_key())},
            "memo_hits": 0, "prunes": {}, "CH1_nodes": 0, "CH2_nodes": 0,
            "undecided_nodes": 0, "other_nodes": 0, "branch_transitions": {},
            "max_macro_depth": 0, "checkpoint_count": 0,
            "pre_R_nodes": 0, "post_R1_nodes": 0, "R1_transitions": 0,
            "R2_candidate_edges": 0, "Target_A_hits": 0,
            "pre_R_prunes": {}, "post_R1_prunes": {}, "max_post_R1_depth": 0,
            "r1_decorated_keys": [], "Phi_at_R1": {}, "M_at_R1": {},
            "steps_since_R1_expanded": {}, "hub_completions_before_R1": 0,
            "hub_completions_after_R1": 0, "CH1_events": 0, "CH2_events": 0,
            # CH0 is deliberately an observational residual label.  It does
            # not affect the RR recognizer, pruning, or decorated state key.
            "provisional_CH0_events": 0,
            "event_order_class_events": {}, "R2_primary_failures": {},
            "R2_outcomes": {}, "R1_events": {}, "geometry_failure_counts": {},
            "geometry_failure_records": [], "same_component_failure_records": [],
        }
        boundaries: list[dict[str, object]] = []
        lineage: list[str] = []
    # A checkpoint written by this driver contains every field below.  Default
    # values also make the reader robust for a deliberately minimal synthetic
    # checkpoint used by the resume control, without relaxing SHA/config
    # validation or changing any traversal semantics.
    for field, default in {
        "expanded": 0, "generated_edges": 0, "exact_states": [], "memo_hits": 0,
        "prunes": {}, "CH1_nodes": 0, "CH2_nodes": 0, "undecided_nodes": 0,
        "other_nodes": 0, "branch_transitions": {}, "max_macro_depth": 0,
        "checkpoint_count": 0, "pre_R_nodes": 0, "post_R1_nodes": 0,
        "R1_transitions": 0, "R2_candidate_edges": 0, "Target_A_hits": 0,
        "pre_R_prunes": {}, "post_R1_prunes": {}, "max_post_R1_depth": 0,
        "r1_decorated_keys": [], "Phi_at_R1": {}, "M_at_R1": {},
        "steps_since_R1_expanded": {}, "hub_completions_before_R1": 0,
        "hub_completions_after_R1": 0, "CH1_events": 0, "CH2_events": 0,
        "provisional_CH0_events": 0, "event_order_class_events": {},
        "R2_primary_failures": {}, "R2_outcomes": {}, "R1_events": {},
        "geometry_failure_counts": {}, "geometry_failure_records": [],
        "same_component_failure_records": [],
    }.items():
        stats.setdefault(field, default)
    prunes = Counter(stats.get("prunes", {}))
    pre_r_prunes = Counter(stats.get("pre_R_prunes", {}))
    post_r1_prunes = Counter(stats.get("post_R1_prunes", {}))
    branch_transitions = Counter(stats.get("branch_transitions", {}))
    exact_states = set(stats.get("exact_states", set()))
    r1_decorated_keys = set(stats.get("r1_decorated_keys", []))
    phi_at_r1 = Counter(stats.get("Phi_at_R1", {}))
    m_at_r1 = Counter(stats.get("M_at_R1", {}))
    steps_since_r1 = Counter(stats.get("steps_since_R1_expanded", {}))
    event_order_classes = Counter(stats.get("event_order_class_events", {}))
    r2_primary_failures = Counter(stats.get("R2_primary_failures", {}))
    r2_outcomes = Counter(stats.get("R2_outcomes", {}))
    r1_events = dict(stats.get("R1_events", {}))
    geometry_failure_counts = Counter(stats.get("geometry_failure_counts", {}))
    geometry_failure_records = list(stats.get("geometry_failure_records", []))
    same_component_failure_records = list(stats.get("same_component_failure_records", []))
    if resume is None and decoration.r_count == 1:
        r1_decorated_keys.add(repr(decorated_key(start, decoration)))

    def record_prune(reason: str, current_decoration: Decoration) -> None:
        prunes[reason] += 1
        if current_decoration.r_count == 0:
            pre_r_prunes[reason] += 1
        elif current_decoration.r_count == 1:
            post_r1_prunes[reason] += 1

    def persist_telemetry() -> None:
        stats["prunes"] = dict(sorted(prunes.items()))
        stats["pre_R_prunes"] = dict(sorted(pre_r_prunes.items()))
        stats["post_R1_prunes"] = dict(sorted(post_r1_prunes.items()))
        stats["branch_transitions"] = dict(sorted(branch_transitions.items()))
        stats["exact_states"] = sorted(exact_states)
        stats["r1_decorated_keys"] = sorted(r1_decorated_keys)
        stats["unique_r1_decorated_keys"] = len(r1_decorated_keys)
        stats["Phi_at_R1"] = dict(sorted(phi_at_r1.items(), key=lambda item: int(item[0])))
        stats["M_at_R1"] = dict(sorted(m_at_r1.items(), key=lambda item: int(item[0])))
        stats["steps_since_R1_expanded"] = dict(
            sorted(steps_since_r1.items(), key=lambda item: int(item[0])))
        stats["event_order_class_events"] = dict(sorted(event_order_classes.items()))
        stats["R2_primary_failures"] = dict(sorted(r2_primary_failures.items()))
        stats["R2_outcomes"] = {name: int(r2_outcomes[name]) for name in R2_OUTCOME_VOCABULARY}
        stats["R1_events"] = dict(sorted(r1_events.items()))
        if capture_r2_diagnostics:
            stats["geometry_failure_counts"] = {
                name: int(geometry_failure_counts[name]) for name in GEOMETRY_FAILURE_VOCABULARY}
            stats["geometry_failure_records"] = geometry_failure_records
            stats["same_component_failure_records"] = same_component_failure_records
    started = time.time()
    interrupted = False
    bounded_depth = False
    while frontier:
        if node_limit and int(stats["expanded"]) >= node_limit:
            interrupted = True
            break
        depth, state, dec, trace = frontier.pop()
        if max_depth is not None and depth >= max_depth:
            bounded_depth = True
            continue
        stats["expanded"] = int(stats["expanded"]) + 1
        stats["max_macro_depth"] = max(int(stats["max_macro_depth"]), depth)
        if dec.r_count == 0:
            stats["pre_R_nodes"] = int(stats["pre_R_nodes"]) + 1
        elif dec.r_count == 1:
            stats["post_R1_nodes"] = int(stats["post_R1_nodes"]) + 1
            stats["max_post_R1_depth"] = max(int(stats["max_post_R1_depth"]), depth)
            assert dec.r1 is not None
            steps_since_r1[str(dec.macro_index - dec.r1.macro_index)] += 1
        bucket = {"CH1": "CH1_nodes", "CH2": "CH2_nodes", "UNDECIDED": "undecided_nodes"}.get(
            dec.branch, "other_nodes")
        stats[bucket] = int(stats[bucket]) + 1
        child_entries = []
        for edge, collision in iter_raw_macro_candidates(state):
            stats["generated_edges"] = int(stats["generated_edges"]) + 1
            if collision is not None:
                record_prune(collision, dec)
                continue
            assert edge is not None
            edge_kind = joint_kind(edge.joint.move.weight, edge.joint.abandonment,
                                   edge.joint.new_orbit)
            if edge_kind == "R" and dec.r_count == 1:
                stats["R2_candidate_edges"] = int(stats["R2_candidate_edges"]) + 1
            verdict, child_dec, recognition = evaluate_edge(
                state, dec, edge, prune_profile=prune_profile)
            trace_step = edge_json(edge)
            if verdict == "child":
                assert child_dec is not None
                old_branch = dec.branch
                new_branch = child_dec.branch
                if old_branch != new_branch:
                    branch_transitions[f"{old_branch}->{new_branch}"] += 1
                key = decorated_key(edge.state, child_dec)
                if key in seen:
                    stats["memo_hits"] = int(stats["memo_hits"]) + 1
                    record_prune("decorated_memo_duplicate", dec)
                    continue
                seen.add(key)
                if child_dec.r_count == 1:
                    r1_decorated_keys.add(repr(key))
                    if dec.r_count == 0 and edge_kind == "R":
                        stats["R1_transitions"] = int(stats["R1_transitions"]) + 1
                        # Values are measured on the accepted post-R1 child.
                        # M = P - 5O is an analysis coordinate only.
                        phi_at_r1[str(phi(edge.state))] += 1
                        m_at_r1[str(edge.state.P - 5 * edge.state.O)] += 1
                        event_id, event = r1_event_export(edge, dec, child_dec, trace)
                        existing = r1_events.get(event_id)
                        if existing is not None and existing != event:
                            raise AssertionError("R1 event identifier collision")
                        r1_events[event_id] = event
                if dec.completer is None and child_dec.completer is not None:
                    # Count completion only once the child has survived all
                    # exact, Area-A, and memo gates and is actually queued.
                    if dec.r_count == 0:
                        stats["hub_completions_before_R1"] = int(
                            stats["hub_completions_before_R1"]) + 1
                    else:
                        stats["hub_completions_after_R1"] = int(
                            stats["hub_completions_after_R1"]) + 1
                    if child_dec.branch == "CH1":
                        stats["CH1_events"] = int(stats["CH1_events"]) + 1
                    elif child_dec.branch == "CH2":
                        stats["CH2_events"] = int(stats["CH2_events"]) + 1
                    else:
                        stats["provisional_CH0_events"] = int(
                            stats["provisional_CH0_events"]) + 1
                    event_order_classes[child_dec.event_order_class] += 1
                exact_states.add(repr(edge.state.stable_key()))
                child_entries.append((depth + 1, edge.state, child_dec, trace + (trace_step,)))
                continue
            if verdict == "FOUND_TARGET_A":
                assert child_dec is not None and recognition is not None
                if recognition["r2_outcome"] != "TARGET_A_HIT":
                    raise AssertionError("Target-A R2 has non-hit outcome")
                r2_outcomes["TARGET_A_HIT"] += 1
                stats["Target_A_hits"] = int(stats["Target_A_hits"]) + 1
                boundary = dict(recognition)
                boundary.update({
                    "root_id": record["root_id"], "extension_depth": depth + 1,
                    "literal_macro_trace": list(trace + (trace_step,)),
                    "decoration_before_R2": dec.to_json(),
                    "decoration_after_R2": child_dec.to_json(),
                    "post_r2_state": exact.state_to_json(edge.state),
                })
                boundary["target_b_dispatch"] = dispatch_target_b(boundary, edge.state)
                boundaries.append(boundary)
                continue
            if verdict == "r2_not_target":
                assert recognition is not None
                primary = recognition["r2_primary_failure"]
                if primary is None:
                    raise AssertionError("non-target R2 has no primary recognizer failure")
                r2_primary_failures[str(primary)] += 1
                outcome = str(recognition["r2_outcome"])
                if outcome not in R2_OUTCOME_VOCABULARY or outcome == "TARGET_A_HIT":
                    raise AssertionError("non-target R2 has invalid outcome")
                r2_outcomes[outcome] += 1
                if capture_r2_diagnostics:
                    if outcome == "recognizer_geometry_failure":
                        reason = recognition["geometry_failure_reason"]
                        if reason not in GEOMETRY_FAILURE_VOCABULARY:
                            raise AssertionError("opaque geometry exit has no exact taxonomy reason")
                        geometry_failure_counts[str(reason)] += 1
                        geometry_failure_records.append(geometry_failure_record(
                            edge.run.state, edge, dec, child_dec, depth=depth + 1))
                    elif outcome == "not_same_component":
                        same_component_failure_records.append(same_component_failure_record(
                            edge.run.state, edge, dec, child_dec, depth=depth + 1))
            record_prune(verdict, dec)
        # Stack uses reverse lexical successor order but the resulting pop order
        # is stable lexical; recording it in config makes certificates replayable.
        child_entries.sort(key=lambda item: item[3][-1]["label"], reverse=True)
        frontier.extend(child_entries)
        if checkpoint is not None and checkpoint_every > 0 and int(stats["expanded"]) % checkpoint_every == 0:
            persist_telemetry()
            digest = write_checkpoint(checkpoint, config, frontier, seen, stats, boundaries, lineage)
            lineage.append(digest)
            stats["checkpoint_count"] = int(stats["checkpoint_count"]) + 1
    persist_telemetry()
    if sum(r2_outcomes.values()) != int(stats["R2_candidate_edges"]):
        raise AssertionError("R2 outcome ledger does not partition R2 candidates")
    if capture_r2_diagnostics:
        if sum(geometry_failure_counts.values()) != r2_outcomes["recognizer_geometry_failure"]:
            raise AssertionError("geometry taxonomy does not partition opaque geometry exits")
        if len(geometry_failure_records) != r2_outcomes["recognizer_geometry_failure"]:
            raise AssertionError("geometry failure evidence count mismatch")
        if len(same_component_failure_records) != r2_outcomes["not_same_component"]:
            raise AssertionError("same-component failure evidence count mismatch")
    stats["elapsed_seconds_this_invocation"] = round(time.time() - started, 3)
    if checkpoint is not None:
        digest = write_checkpoint(checkpoint, config, frontier, seen, stats, boundaries, lineage)
        lineage.append(digest)
        stats["checkpoint_count"] = int(stats["checkpoint_count"]) + 1
    completed = not frontier and not interrupted and not bounded_depth
    if not completed:
        status = "INCOMPLETE"
    elif boundaries:
        status = "FOUND_TARGET_A"
    else:
        status = "EXHAUSTED_NO_TARGET_A"
    # The checkpoint retains full state diagnostics for resume auditing.  The
    # final public result reports the required cardinality only; serializing
    # every stable key there would duplicate the checkpoint and obscure the
    # root-level certificate summary.
    public_stats = dict(stats)
    public_stats.pop("exact_states", None)
    public_stats.pop("r1_decorated_keys", None)
    result = {
        "schema": "rr-target-a-exhaustive-root-result-v1",
        "status": status, "root_id": record["root_id"],
        "root_literal_hash": config["root_literal_hash"], "config": config,
        "stats": {**public_stats, "unique_exact_states": len(exact_states),
                  "unique_decorated_keys": len(seen), "frontier_size": len(frontier)},
        "frontier_empty": not frontier, "interrupted_by_node_limit": interrupted,
        "interrupted_by_depth_limit": bounded_depth, "checkpoint": None if checkpoint is None else str(checkpoint),
        "checkpoint_lineage": lineage, "target_a_boundaries": boundaries,
        "terminal_counts": {"target_a_boundaries": len(boundaries),
                            "non_target_R2": prunes.get("r2_not_target", 0)},
        "final_result_digest": None,
    }
    if capture_frontier_snapshot:
        # Intended only for bounded audit replays.  This exports the requested
        # terminal frontier (not a large resumable checkpoint) and binds it to
        # a deterministic LIFO search transcript comparison.
        result["diagnostic_frontier_snapshot"] = serialize_frontier(frontier)
        result["diagnostic_frontier_hash"] = sha256_bytes(
            json.dumps(result["diagnostic_frontier_snapshot"], sort_keys=True).encode("utf-8"))
        result["diagnostic_seen_key_hash"] = sha256_bytes(
            "\n".join(sorted(repr(key) for key in seen)).encode("utf-8"))
    digest_payload = dict(result)
    digest_payload["final_result_digest"] = None
    result["final_result_digest"] = sha256_bytes(json.dumps(digest_payload, sort_keys=True, default=str).encode("utf-8"))
    return result


def run_key_audit(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """A tested-universe, not universal, memo-key audit.

    Each of the 22 root states and every first accepted child is duplicated
    deliberately.  Equal proposed keys must give an equal full one-step
    signature.  This catches mutable or omitted history in the implemented
    update, while honestly not proving equivalence for all possible histories.
    """
    examples = []
    groups: dict[tuple[object, ...], list[tuple[object, Decoration]]] = {}
    for record in records:
        state, dec = initial_decoration(record)
        samples = [(state, dec)]
        for edge, collision in iter_raw_macro_candidates(state):
            if collision or edge is None:
                continue
            verdict, child_dec, _ = evaluate_edge(state, dec, edge)
            if verdict == "child" and child_dec is not None:
                samples.append((edge.state, child_dec))
        for sample in samples:
            key = decorated_key(*sample)
            groups.setdefault(key, []).extend([sample, sample])  # deliberate collision
    mismatches = []
    for key, samples in groups.items():
        signatures = {successor_signature(state, dec) for state, dec in samples}
        if len(signatures) != 1:
            mismatches.append(sha256_bytes(repr(key).encode("utf-8")))
    # The recorded six witnesses demonstrate why the R1 target cannot be
    # dropped when chaining is part of reporting: mutate that one field on a
    # fixed state and its later chaining classification changes.
    historical = json.loads((ROOT / "outputs" / "rr_long_prefix_extension_results.json").read_text(encoding="utf-8"))
    known = next(row for row in historical["results"] if row["status"] == "FOUND")
    prefix_data = json.loads(PREFIXES.read_text(encoding="utf-8"))["prefixes"]
    known_record = dict(prefix_data[int(known["prefix_index"])])
    known_record["root_id"] = "known-witness-audit"
    state, dec = initial_decoration(known_record)
    changed = False
    for step in known["same_component_witnesses"][0]["extension_trace"]:
        ell = int(step["label"].split(";")[0].split("^")[1])
        label = step["label"].split(";", 1)[1]
        for _ in range(ell):
            state = exact.extend(state, W1).state
        transition = exact.extend(state, MOVE[label])
        if transition is None:
            raise AssertionError("stored witness failed during key audit")
        after = advance_decoration(state, transition, dec)
        if joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit) == "R":
            mutated_r1 = REvent(dec.r1.macro_index, dec.r1.kind, dec.r1.source_orbit,
                                dec.r1.source_phase, (dec.r1.target_orbit + 1) % 144,
                                dec.r1.target_phase)
            mutated = Decoration(dec.root_id, dec.root_ell, dec.o_star, dec.hub_id,
                                 dec.macro_index, (mutated_r1,), dec.hub_touch_count, dec.completer)
            changed = target_a_recognizer(state, transition, dec, after)["chaining"] != \
                      target_a_recognizer(state, transition, mutated, after)["chaining"]
            break
        dec, state = after, transition.state
    return {
        "schema": "rr-target-a-state-key-audit-v1",
        "grade": "exhaustive tested-universe equivalence; not an exact key theorem",
        "roots_checked": len(records), "deliberate_duplicate_groups": len(groups),
        "key_collision_mismatches": mismatches,
        "passed": not mismatches,
        "r1_target_required_for_chaining_reporting": changed,
        "note": ("ExactState determines legality and component computation. R1 target is retained "
                 "because the same exact continuation can have different chaining reporting if it is altered."),
    }


def root_certificate(result: Mapping[str, object]) -> dict[str, object]:
    """A certificate manifest; independent replay is performed by the verifier."""
    return {
        "schema": "rr-target-a-exhaustion-certificate-v1",
        "root_id": result["root_id"], "status": result["status"],
        "root_literal_hash": result["root_literal_hash"], "config": result["config"],
        "total_expanded_states": result["stats"]["expanded"],
        "total_memo_hits": result["stats"]["memo_hits"],
        "terminal_counts": result["terminal_counts"], "prune_counts": result["stats"]["prunes"],
        "final_empty_frontier": result["frontier_empty"],
        "interrupted": result["interrupted_by_node_limit"] or result["interrupted_by_depth_limit"],
        "checkpoint_lineage": result["checkpoint_lineage"],
        "deterministic_traversal": result["config"]["traversal"],
        "search_result_digest": result["final_result_digest"],
        "warning": ("This manifest becomes an exhaustion certificate only when status is "
                    "EXHAUSTED_NO_TARGET_A, final_empty_frontier is true, interruption is false, "
                    "and the independent verifier replays it."),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--prefixes", type=Path, default=PREFIXES)
    parser.add_argument("--root-id", action="append", default=[])
    parser.add_argument("--node-limit", type=int, default=0)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--checkpoint-dir", type=Path, default=ROOT / "outputs" / "checkpoints" / "rr_target_a")
    parser.add_argument("--checkpoint-every", type=int, default=1000)
    parser.add_argument("--resume", type=Path, default=None,
                        help="resume exactly one selected root from its checkpoint")
    parser.add_argument("--audit-state-key", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "rr_target_a_exhaustive_results.json")
    parser.add_argument("--certificates", type=Path, default=ROOT / "outputs" / "rr_target_a_exhaustion_certificates.json")
    parser.add_argument("--new-boundaries", type=Path, default=ROOT / "outputs" / "rr_target_a_new_boundaries.json")
    args = parser.parse_args()
    if args.node_limit < 0 or args.checkpoint_every < 1:
        raise ValueError("node limit must be >=0 and checkpoint interval must be positive")
    all_audited_records = load_audited_roots(args.ledger, args.prefixes)
    records = list(all_audited_records)
    if args.root_id:
        wanted = set(args.root_id)
        records = [record for record in records if record["root_id"] in wanted]
        if not records or {record["root_id"] for record in records} != wanted:
            raise ValueError("--root-id must name audited roots exactly")
    # Key soundness is a property of the implementation and the audited root
    # universe, not just the pilot root selected for traversal.
    audit = run_key_audit(all_audited_records) if args.audit_state_key else None
    if audit is not None and not audit["passed"]:
        raise RuntimeError("STATE_KEY_UNSOUND: state-key audit failed")
    all_results = []
    for record in records:
        resume = args.resume
        if resume is not None and len(records) != 1:
            raise ValueError("--resume requires exactly one --root-id")
        checkpoint = args.checkpoint_dir / f"{record['root_id']}.json"
        result = search_root(record, node_limit=args.node_limit, max_depth=args.max_depth,
                             checkpoint=checkpoint, checkpoint_every=args.checkpoint_every,
                             resume=resume)
        all_results.append(result)
        print(f"{record['root_id']}: {result['status']} expanded={result['stats']['expanded']} "
              f"frontier={result['stats']['frontier_size']} boundaries={len(result['target_a_boundaries'])}")
    aggregate = Counter(result["status"] for result in all_results)
    output = {
        "schema": "rr-target-a-exhaustive-results-v1", "grade": "exact search when a root naturally exhausts; otherwise incomplete",
        "scope": "22 audited Round-27 incomplete roots only; not Target B/C or NR6",
        "input_ledger_sha256": sha256_file(args.ledger), "input_prefixes_sha256": sha256_file(args.prefixes),
        "state_key_audit": audit, "prune_registry": PRUNE_REGISTRY,
        "results": all_results, "status_histogram": dict(aggregate),
    }
    certificates = {"schema": "rr-target-a-exhaustion-certificates-v1",
                    "certificates": [root_certificate(result) for result in all_results]}
    boundaries = [boundary for result in all_results for boundary in result["target_a_boundaries"]]
    new_boundaries = {"schema": "rr-target-a-new-boundaries-v1", "boundaries": boundaries,
                      "count": len(boundaries), "scope": "Target-A only; Target-B dispatch metadata is non-authoritative"}
    atomic_json(args.output, output)
    atomic_json(args.certificates, certificates)
    atomic_json(args.new_boundaries, new_boundaries)


if __name__ == "__main__":
    main()
