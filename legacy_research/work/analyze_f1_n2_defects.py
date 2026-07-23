#!/usr/bin/env python3
"""Read-only structural analysis for the n=6 F=1,H=0,N=2 slice.

This script never resumes, alters, or reads the live N=0 retry checkpoint.
It reads an immutable N=0 terminal checkpoint and the completed bounded
Area-A depth-six checkpoint.  Its only exploration is a capped continuation
from already-recorded N=1 R-escape states.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import mmap
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
SPEC = importlib.util.spec_from_file_location("f1_n2_defect_macro", MACRO_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MACRO_PATH}")
macro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = macro
SPEC.loader.exec_module(macro)
exact = macro.exact

IMMUTABLE_N0_DEFAULT = ROOT / "outputs" / "f1_small_n0.committed_resume.checkpoint.5fc78a33465b861.backup.json"
AREA_A_DEFAULT = ROOT / "outputs" / "f1_macro_checkpoints" / "A_F1_H0_Nle3_macro_depth6.checkpoint.json"
AREA_A_SNAPSHOT_DEFAULT = ROOT / "outputs" / "f1_area_a_explosion_analysis.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _array_bounds(data: mmap.mmap, key: bytes) -> tuple[int, int]:
    marker = b'"' + key + b'": '
    begin = data.find(marker)
    if begin < 0:
        raise KeyError(key.decode("ascii", errors="replace"))
    start = begin + len(marker)
    if data[start:start + 1] != b"[":
        raise ValueError(f"{key!r} is not a JSON array")
    depth = 0
    quoted = escaped = False
    cursor = start
    while cursor < len(data):
        byte = data[cursor]
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        else:
            if byte == 34:
                quoted = True
            elif byte == 91:
                depth += 1
            elif byte == 93:
                depth -= 1
                if depth == 0:
                    return start, cursor + 1
        cursor += 1
    raise ValueError(f"unterminated JSON array {key!r}")


def iter_json_array(path: Path, key: bytes) -> Iterator[dict[str, Any]]:
    """Yield a top-level object array without materialising other fields."""
    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        start, end = _array_bounds(data, key)
        cursor = start + 1
        while cursor < end - 1:
            while cursor < end - 1 and data[cursor] in b" \t\r\n,":
                cursor += 1
            if cursor >= end - 1:
                break
            if data[cursor] != 123:
                raise ValueError(f"array {key!r} contains non-object item")
            item_start = cursor
            depth = 0
            quoted = escaped = False
            while cursor < end:
                byte = data[cursor]
                if quoted:
                    if escaped:
                        escaped = False
                    elif byte == 92:
                        escaped = True
                    elif byte == 34:
                        quoted = False
                else:
                    if byte == 34:
                        quoted = True
                    elif byte == 123:
                        depth += 1
                    elif byte == 125:
                        depth -= 1
                        if depth == 0:
                            cursor += 1
                            yield json.loads(data[item_start:cursor].decode("utf-8"))
                            break
                cursor += 1
            else:
                raise ValueError(f"unterminated object in {key!r}")


def top_level_header(path: Path) -> dict[str, Any]:
    """Read only the small checkpoint prefix that precedes frontier."""
    with path.open("rb") as handle:
        prefix = handle.read(256 * 1024)
    marker = b'"frontier": '
    index = prefix.find(marker)
    if index < 0:
        raise ValueError("frontier marker not in first 256KiB")
    return json.loads((prefix[:index] + b'"frontier": []}').decode("utf-8"))


def state_hash(state: exact.ExactState) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def popcount(mask: int) -> int:
    return mask.bit_count()


def fragment_summary(state: exact.ExactState) -> dict[str, Any]:
    form = exact.f1_normal_form(state)
    if form is None:
        return {"normal_form_valid": False}
    return {
        "normal_form_valid": True,
        "current_hex": form.current_hex,
        "current_components": [list(x) for x in form.current_components],
        "fragment_hex": form.fragment_hex,
        "fragment_components": [list(x) for x in form.fragment_components],
        "fragment_is_current": form.fragment_hex == form.current_hex,
        "orbit_phase_masks": [[q, mask] for q, mask in form.orbit_masks],
    }


def component_map(state: exact.ExactState) -> tuple[dict[tuple[str, int], tuple[str, int]], dict[int, tuple[str, int]]]:
    """Components of the presently occupied partial port-incidence graph."""
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

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = exact.core.ports_of_e_orbit(exact.core.E_REPS[q])[phase]
                union(("q", q), ("h", exact.core.hexagon_id(port)))
    roots = {node: find(node) for node in list(parent)}
    return roots, {node[1]: root for node, root in roots.items() if node[0] == "h"}


def support_delta(before: exact.ExactState, after: exact.ExactState) -> dict[str, list[list[int]]]:
    return {
        "hexagons": [[i, after.hex_masks[i] & ~before.hex_masks[i]] for i in range(len(before.hex_masks)) if after.hex_masks[i] != before.hex_masks[i]],
        "orbits": [[i, after.orbit_masks[i] & ~before.orbit_masks[i]] for i in range(len(before.orbit_masks)) if after.orbit_masks[i] != before.orbit_masks[i]],
    }


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    kinds = {
        (2, False, False): "Z2_blocked_w2_existing",
        (2, True, True): "Z2_abandon_w2_new",
        (2, True, False): "A2_abandon_w2_existing",
        (2, False, True): "forbidden_blocked_w2_new",
        (3, False, True): "Z3_blocked_w3_new",
        (3, False, False): "R_blocked_w3_existing",
        (3, True, True): "A3_abandon_w3_new",
        (3, True, False): "J_abandon_w3_existing_charge2",
    }
    return kinds.get((weight, abandonment, new_orbit), "outside_H0_joint_alphabet")


def joint_record(
    before_boundary: exact.ExactState,
    pre_joint: exact.ExactState,
    transition: exact.Transition,
    after: exact.ExactState,
    rotation_length: int,
) -> dict[str, Any]:
    source_q, source_phase = exact.ORBIT_PHASE[pre_joint.p]
    target_q, target_phase = exact.ORBIT_PHASE[transition.target]
    roots, hex_roots = component_map(pre_joint)
    source_root, target_root = roots.get(("q", source_q)), roots.get(("q", target_q))
    f_before = fragment_summary(pre_joint)
    f_after = fragment_summary(after)
    fhex = f_before.get("fragment_hex")
    target_hex = exact.core.hexagon_id(transition.target)
    return {
        "kind": joint_kind(transition.move.weight, transition.abandonment, transition.new_orbit),
        "weight": transition.move.weight,
        "move": transition.move.label,
        "rotation_length": rotation_length,
        "source_orbit": source_q,
        "source_phase": source_phase,
        "target_orbit": target_q,
        "target_phase": target_phase,
        "target_hexagon": target_hex,
        "target_phase_mask_before": pre_joint.orbit_masks[target_q],
        "target_phase_mask_after": after.orbit_masks[target_q],
        "abandonment": transition.abandonment,
        "new_orbit": transition.new_orbit,
        "delta": {
            "F": transition.delta_F,
            "S": transition.delta_S,
            "O": int(transition.new_orbit),
            "D": after.D - before_boundary.D,
            "N": after.Ndef - before_boundary.Ndef,
        },
        "partial_component_relation": (
            "same" if source_root is not None and source_root == target_root else
            "different" if source_root is not None and target_root is not None else "unresolved"
        ),
        "target_fragment_relation_before": (
            "no_observable_fragment" if fhex is None else
            "target_is_fragment_hex" if target_hex == fhex else
            "target_component_of_fragment" if roots.get(("q", target_q)) == hex_roots.get(fhex) else "different_or_unresolved"
        ),
        "fragment_before": f_before,
        "fragment_after": f_after,
        "support": support_delta(before_boundary, after),
    }


def serialized_step(state: exact.ExactState, item: Mapping[str, Any]) -> tuple[exact.ExactState, dict[str, Any]]:
    """Replay one serialized macro item and retain its literal pre-joint data."""
    before = state
    pre = state
    ell = int(item["rotation_length"])
    for _ in range(ell):
        step = exact.extend(pre, macro.W1)
        if step is None:
            raise AssertionError("serialized macro contains a rotation collision")
        pre = step.state
    label = str(item["joint"])
    move = next(move for move in exact.ALL_MOVES if move.label == label)
    transition = exact.extend(pre, move)
    if transition is None:
        raise AssertionError("serialized macro joint is illegal")
    raw_after = transition.state
    record = joint_record(before, pre, transition, raw_after, ell)
    return exact.canonicalize(raw_after), record


def replay_path(path: Sequence[Mapping[str, Any]]) -> tuple[exact.ExactState, list[dict[str, Any]]]:
    state = exact.canonicalize(exact.initial_state())
    records: list[dict[str, Any]] = []
    for item in path:
        state, record = serialized_step(state, item)
        records.append(record)
    return state, records


def replay_path_raw_equivariant(path: Sequence[Mapping[str, Any]]) -> tuple[exact.ExactState, list[dict[str, Any]]]:
    """Replay without repeated canonicalization.

    Canonicalization is only a left value-relabeling.  Every literal tail is a
    right position action, so left relabeling commutes with every transition.
    Therefore the raw trajectory is a left-relabelled copy of the serialized
    canonical trajectory: legality, collisions, all resource coordinates, and
    all within-path component/orbit relations are preserved.  This avoids six
    full 720-image canonicalizations per saved depth-six path.
    """
    state = exact.initial_state()
    records: list[dict[str, Any]] = []
    for item in path:
        before = state
        pre = state
        ell = int(item["rotation_length"])
        for _ in range(ell):
            step = exact.extend(pre, macro.W1)
            if step is None:
                raise AssertionError("raw equivariant replay hit a rotation collision")
            pre = step.state
        move = next(move for move in exact.ALL_MOVES if move.label == str(item["joint"]))
        transition = exact.extend(pre, move)
        if transition is None:
            raise AssertionError("raw equivariant replay hit a joint collision")
        state = transition.state
        records.append(joint_record(before, pre, transition, state, ell))
    return state, records


def replay_path_raw_defects(path: Sequence[Mapping[str, Any]]) -> tuple[exact.ExactState, list[tuple[int, dict[str, Any]]]]:
    """Raw replay retaining detailed records only for positive-charge joints.

    Zero-charge joints still undergo literal collision and Delta-N checks, but
    avoiding their component-map construction is important for the 65k-state
    historical bounded frontier.  The two-defect questions depend only on the
    positive-charge records.
    """
    state = exact.initial_state()
    positives: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(path):
        before = state
        pre = state
        ell = int(item["rotation_length"])
        for _ in range(ell):
            step = exact.extend(pre, macro.W1)
            if step is None:
                raise AssertionError("raw defect replay hit a rotation collision")
            pre = step.state
        move = next(move for move in exact.ALL_MOVES if move.label == str(item["joint"]))
        transition = exact.extend(pre, move)
        if transition is None:
            raise AssertionError("raw defect replay hit a joint collision")
        state = transition.state
        delta_n = state.Ndef - before.Ndef
        if delta_n < 0:
            raise AssertionError("blocked-w2 lemma violation in exact replay")
        if delta_n > 0:
            positives.append((index, joint_record(before, pre, transition, state, ell)))
    return state, positives


def finite_truth_table() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for weight in (2, 3):
        for abandonment in (False, True):
            for new_orbit in (False, True):
                kind = joint_kind(weight, abandonment, new_orbit)
                delta = int(weight >= 3) + int(abandonment) - int(new_orbit)
                rows.append({
                    "weight": weight,
                    "abandonment": abandonment,
                    "new_E_orbit": new_orbit,
                    "delta_N": delta,
                    "kind": kind,
                    "geometry": (
                        "excluded by proved blocked-w2 lemma" if kind == "forbidden_blocked_w2_new"
                        else "not excluded by current flow bookkeeping"
                    ),
                })
    return {
        "schema": "f1-n2-local-defect-truth-table-v1",
        "identity": "Delta N = 1_{w>=3} + 1_{abandonment} - 1_{new E-orbit}",
        "rows": rows,
        "proved": {
            "negative_row_excluded": "Only blocked w2 -> new orbit has negative charge, and the blocked-w2 lemma excludes it.",
            "unit_charge_words": ["RR", "RA2", "A2R", "RA3", "A3R"],
            "F1_impossible_words": ["A2A2", "A2A3", "A3A2", "A3A3"],
            "reason_for_impossible_words": "Each A2/A3 is an abandonment; F=1 permits exactly one abandonment.",
        },
        "not_proved": {
            "exactly_two_unit_defects": (
                "The J row, abandonment w3 -> existing orbit, has DeltaN=2. "
                "It is not excluded by the current ledger or blocked-w2 lemma."
            ),
            "single_charge_two_alternative": ["J_abandon_w3_existing_charge2"],
        },
    }


def all_safe_edges(state: exact.ExactState, config: macro.AreaAConfig) -> Iterator[tuple[macro.MacroEdge, exact.ExactState, dict[str, Any]]]:
    for edge in macro.macro_edges(state):
        raw = edge.state
        if macro.area_a_prune_reason(raw, config) is not None:
            continue
        record = joint_record(state, edge.run.state, edge.joint, raw, edge.run.ell)
        yield edge, exact.canonicalize(raw), record


def reconstruct_n1_r_roots(terminals: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Recover the 25 already-observed N=1 R-escapes without active inputs."""
    roots: list[dict[str, Any]] = []
    for terminal_index, certificate in enumerate(terminals):
        state = exact.state_from_json(certificate["state"])
        if (state.F, state.H, state.Ndef) != (1, 0, 0):
            continue
        for _edge, child, record in all_safe_edges(state, macro.SMALL_N1):
            if child.Ndef != 1 or record["kind"] != "R_blocked_w3_existing":
                continue
            roots.append({
                "root_id": len(roots),
                "terminal_index": terminal_index,
                "terminal_state_hash": state_hash(state),
                "terminal_coordinate": macro.state_coordinate(state),
                "path_before_first_defect": certificate.get("path", []),
                "first_defect": record,
                "state": child,
            })
    return roots


def legal_tail_count(state: exact.ExactState, config: macro.AreaAConfig) -> tuple[int, Counter[str]]:
    count = 0
    rejects: Counter[str] = Counter()
    for edge in macro.macro_edges(state):
        reason = macro.area_a_prune_reason(edge.state, config)
        if reason is None:
            count += 1
        else:
            rejects[reason] += 1
    return count, rejects


def relation_between(first: Mapping[str, Any], second: Mapping[str, Any]) -> dict[str, Any]:
    fsrc, ftgt = int(first["source_orbit"]), int(first["target_orbit"])
    ssrc, stgt = int(second["source_orbit"]), int(second["target_orbit"])
    f_orbits, s_orbits = {fsrc, ftgt}, {ssrc, stgt}
    f_hex = {int(row[0]) for row in first["support"]["hexagons"]}
    s_hex = {int(row[0]) for row in second["support"]["hexagons"]}
    disjoint = not (f_orbits & s_orbits or f_hex & s_hex)
    return {
        "same_source_orbit": fsrc == ssrc,
        "same_target_orbit": ftgt == stgt,
        "first_target_equals_second_source": ftgt == ssrc,
        "first_source_equals_second_target": fsrc == stgt,
        "orbit_support_relation": "disjoint" if not (f_orbits & s_orbits) else "overlap",
        "hex_support_relation": "disjoint" if not (f_hex & s_hex) else "overlap",
        "component_relation_pair": [first["partial_component_relation"], second["partial_component_relation"]],
        "fragment_relation_pair": [first["target_fragment_relation_before"], second["target_fragment_relation_before"]],
        "independence_status": (
            "necessary_support_conditions_hold_but_swap_unverified" if disjoint
            else "not_independent_by_support_definition"
        ),
        "swap_status": "undetermined: exact literal replay is required even when supports are disjoint",
    }


@dataclass
class ContinuationNode:
    state: exact.ExactState
    root_id: int
    first: dict[str, Any]
    macro_since_first: int
    literal_since_first: int


def bounded_second_defects(roots: Sequence[Mapping[str, Any]], depth: int, edge_cap: int) -> dict[str, Any]:
    """A deliberately small N<=2 experiment from N=1 R-escape states."""
    config = macro.AreaAConfig(2, "analysis_F1_H0_Nle2")
    frontier = [
        ContinuationNode(root["state"], int(root["root_id"]), dict(root["first_defect"]), 0, 0)
        for root in roots
    ]
    seen: set[tuple[object, ...]] = {(node.root_id, node.state.stable_key()) for node in frontier}
    events: list[dict[str, Any]] = []
    layer_counts = [len(frontier)]
    rejects: Counter[str] = Counter()
    generated = 0
    cap_hit = False
    short = {
        "R_blocked_w3_existing": "R",
        "A2_abandon_w2_existing": "A2",
        "A3_abandon_w3_new": "A3",
        "J_abandon_w3_existing_charge2": "J",
    }
    for _ in range(depth):
        next_frontier: list[ContinuationNode] = []
        for node in frontier:
            for edge in macro.macro_edges(node.state):
                generated += 1
                if generated > edge_cap:
                    cap_hit = True
                    break
                raw = edge.state
                reason = macro.area_a_prune_reason(raw, config)
                if reason is not None:
                    rejects[reason] += 1
                    continue
                child = exact.canonicalize(raw)
                record = joint_record(node.state, edge.run.state, edge.joint, raw, edge.run.ell)
                if child.Ndef == 2 and int(record["delta"]["N"]) > 0:
                    legal_after, immediate_rejects = legal_tail_count(child, config)
                    events.append({
                        "root_id": node.root_id,
                        "first_defect": node.first,
                        "second_defect": record,
                        "ordered_word": "R" + short.get(record["kind"], "?"),
                        "macro_distance_between_defects": node.macro_since_first + 1,
                        "literal_tail_distance_between_defects": node.literal_since_first + edge.run.ell + 1,
                        "post_second_coordinate": macro.state_coordinate(child),
                        "post_second_fragment": fragment_summary(child),
                        "interaction": relation_between(node.first, record),
                        "legal_macro_tail_count_after_second": legal_after,
                        "immediate_prune_counts_after_second": dict(sorted(immediate_rejects.items())),
                        "capacity_prune_distance": 1 if immediate_rejects.get("remaining_cover_capacity_impossible", 0) else None,
                        "state_hash_after_second": state_hash(child),
                    })
                key = (node.root_id, child.stable_key())
                if key not in seen:
                    seen.add(key)
                    next_frontier.append(ContinuationNode(
                        child, node.root_id, node.first,
                        node.macro_since_first + 1,
                        node.literal_since_first + edge.run.ell + 1,
                    ))
            if cap_hit:
                break
        frontier = next_frontier
        layer_counts.append(len(frontier))
        if cap_hit or not frontier:
            break
    word_counts = Counter(event["ordered_word"] for event in events)
    interaction_counts = Counter(
        (event["ordered_word"], event["interaction"]["orbit_support_relation"], event["interaction"]["hex_support_relation"])
        for event in events
    )
    return {
        "scope": "limited bounded experiment from existing N=1 R-escapes; not N=2 enumeration",
        "config": {"macro_depth": depth, "generated_macro_edge_cap": edge_cap, "N_limit": 2},
        "root_count": len(roots),
        "generated_macro_edges": generated,
        "cap_hit": cap_hit,
        "layer_state_counts": layer_counts,
        "safe_prune_counts": dict(sorted(rejects.items())),
        "second_defect_event_count": len(events),
        "ordered_word_counts": dict(sorted(word_counts.items())),
        "interaction_counts": [
            {"word": key[0], "orbit_support": key[1], "hex_support": key[2], "count": count}
            for key, count in sorted(interaction_counts.items())
        ],
        "events": events,
        "warning": "Deduplication retains root_id but not every chronological history; an event is a witnessed local path only.",
    }


def area_a_depth6_decomposition(path: Path, snapshot_path: Path) -> dict[str, Any]:
    """Replay saved paths only; do not expand the 65k-state bounded frontier."""
    header = top_level_header(path)
    expected = (macro.CODE_SHA256, macro.ENGINE_SHA256, macro.CORE_SHA256)
    actual = (header.get("macro_sha256"), header.get("engine_sha256"), header.get("core_sha256"))
    checkpoint_sha = sha256_file(path)
    if actual[0] is None and snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        reconstructed = (
            snapshot.get("macro_sha256"),
            snapshot.get("engine_sha256"),
            snapshot.get("core_sha256"),
        )
        if snapshot.get("checkpoint_sha256") != checkpoint_sha or reconstructed != expected:
            raise ValueError("historical macro SHA provenance does not match current code or checkpoint")
        provenance = {
            "status": "historical checkpoint omitted macro_sha256; reconstructed from matching read-only snapshot",
            "snapshot": str(snapshot_path),
            "snapshot_sha256": sha256_file(snapshot_path),
            "snapshot_checkpoint_sha256": snapshot.get("checkpoint_sha256"),
            "reconstructed_code_sha": reconstructed,
        }
    elif actual == expected:
        provenance = {"status": "checkpoint carries complete matching code SHA triple"}
    else:
        raise ValueError(f"Area-A code SHA mismatch: {actual!r} != {expected!r}")
    selected = malformed = delta_two_paths = canonical_spot_checks = 0
    word_counts: Counter[str] = Counter()
    distance_counts: Counter[int] = Counter()
    relation_counts: Counter[tuple[str, str, str]] = Counter()
    component_counts: Counter[tuple[str, ...]] = Counter()
    fragment_counts: Counter[tuple[str, ...]] = Counter()
    phase_counts: Counter[tuple[int, ...]] = Counter()
    tail_counts: Counter[int] = Counter()
    local_tail_sets: dict[tuple[object, ...], set[tuple[str, ...]]] = defaultdict(set)
    local_examples: dict[tuple[object, ...], dict[str, Any]] = {}
    counterexample: Optional[dict[str, Any]] = None
    representatives: dict[str, dict[str, Any]] = {}
    state_records: list[dict[str, Any]] = []
    config = macro.AreaAConfig(3, "read_only_original_AreaA")
    for item in iter_json_array(path, b"frontier"):
        final = exact.state_from_json(item["state"])
        if (final.F, final.H, final.Ndef) != (1, 0, 2):
            continue
        selected += 1
        replayed, positives = replay_path_raw_defects(item.get("path", []))
        if (
            macro.state_coordinate(replayed) != macro.state_coordinate(final)
            or replayed.visited_count != final.visited_count
        ):
            raise AssertionError("raw equivariant replay changes an invariant coordinate")
        # Deterministic diagnostic samples also take the slower fully
        # canonical path.  The general justification is the proved left-S6
        # equivariance; these samples guard against implementation mistakes.
        if selected <= 5 or selected % 1000 == 0:
            canonical, _canonical_records = replay_path(item.get("path", []))
            if canonical.stable_key() != final.stable_key():
                raise AssertionError("canonical spot replay fails exact equality")
            canonical_spot_checks += 1
        charge = sum(int(row["delta"]["N"]) for _, row in positives)
        if charge != 2:
            malformed += 1
            continue
        if len(positives) == 1 and int(positives[0][1]["delta"]["N"]) == 2:
            word, interaction, distance = "J", None, None
            delta_two_paths += 1
        elif len(positives) == 2 and all(int(row["delta"]["N"]) == 1 for _, row in positives):
            abbreviate = {
                "R_blocked_w3_existing": "R",
                "A2_abandon_w2_existing": "A2",
                "A3_abandon_w3_new": "A3",
            }
            word = abbreviate.get(positives[0][1]["kind"], "?") + abbreviate.get(positives[1][1]["kind"], "?")
            interaction = relation_between(positives[0][1], positives[1][1])
            distance = positives[1][0] - positives[0][0]
            distance_counts[distance] += 1
            relation_counts[(word, interaction["orbit_support_relation"], interaction["hex_support_relation"])] += 1
        else:
            word, interaction, distance = "unexpected_charge_decomposition", None, None
        word_counts[word] += 1
        deficits = tuple(sorted(5 - popcount(mask) for mask in final.orbit_masks if mask and popcount(mask) < 5))
        phase_counts[deficits] += 1
        legal, _rejects = legal_tail_count(final, config)
        tail_counts[legal] += 1
        local = (
            word,
            deficits,
            tuple(sorted((row["kind"], int(row["target_phase_mask_before"])) for _, row in positives)),
        )
        tail_set = tuple(sorted(
            edge.label for edge in macro.macro_edges(final)
            if macro.area_a_prune_reason(edge.state, config) is None
        ))
        local_tail_sets[local].add(tail_set)
        example = {"state_hash": state_hash(final), "path": item.get("path", []), "safe_tails": tail_set}
        if local not in local_examples:
            local_examples[local] = example
        elif counterexample is None and len(local_tail_sets[local]) > 1:
            counterexample = {
                "claim_refuted": "ordered defect word plus deficit-phase tuple determines legal macro-tail set",
                "local_fingerprint": local,
                "first_example": local_examples[local],
                "second_example": example,
            }
        representatives.setdefault(word, {
            "state_hash": state_hash(final),
            "coordinate": macro.state_coordinate(final),
            "defects": [row for _, row in positives],
            "macro_distance": distance,
            "interaction": interaction,
            "deficit_phase_type": deficits,
            "legal_macro_tail_count": legal,
            "path": item.get("path", []),
        })
        if interaction is None:
            component_key = (word, "single_charge_two")
            fragment_key = (word, "single_charge_two")
            component_relation = None
            fragment_relation = None
            orbit_relation = None
        else:
            component_relation = interaction["component_relation_pair"]
            fragment_relation = interaction["fragment_relation_pair"]
            orbit_relation = {
                "same_source": interaction["same_source_orbit"],
                "same_target": interaction["same_target_orbit"],
                "first_target_second_source": interaction["first_target_equals_second_source"],
                "first_source_second_target": interaction["first_source_equals_second_target"],
                "support": interaction["orbit_support_relation"],
            }
            component_key = (word, *component_relation)
            fragment_key = (word, *fragment_relation)
        component_counts[component_key] += 1
        fragment_counts[fragment_key] += 1
        global_mask_fingerprint = hashlib.sha256(
            repr((final.p, final.sparse_hex(), final.sparse_orbits())).encode("utf-8")
        ).hexdigest()
        state_records.append({
            "state_hash": state_hash(final),
            "global_visited_mask_fingerprint": global_mask_fingerprint,
            "word": word,
            "defect_macro_distance": distance,
            "deficit_phase_type": deficits,
            "legal_macro_tail_count": legal,
            "orbit_relation": orbit_relation,
            "component_relation": component_relation,
            "fragment_relation": fragment_relation,
            "charge_two_single_event": word == "J",
        })
    return {
        "schema": "f1-n2-area-a-depth6-path-decomposition-v1",
        "scope": "finite complete replay of an existing bounded Area-A frontier; not an N=2 enumeration",
        "checkpoint": str(path),
        "checkpoint_sha256": checkpoint_sha,
        "provenance": provenance,
        "checkpoint_header": {
            "config": header.get("config"),
            "macro_sha256": header.get("macro_sha256"),
            "engine_sha256": header.get("engine_sha256"),
            "core_sha256": header.get("core_sha256"),
        },
        "selected_F1_H0_N2_frontier_states": selected,
        "replay_method": {
            "full": "raw literal replay justified by proved left-S6 equivariance",
            "canonical_spot_checks": canonical_spot_checks,
            "canonical_spot_check_rule": "first five selected paths and every 1000th selected path",
        },
        "malformed_charge_decompositions": malformed,
        "charge_two_single_event_paths": delta_two_paths,
        "ordered_word_counts": dict(sorted(word_counts.items())),
        "defect_macro_distance_counts": dict(sorted(distance_counts.items())),
        "interaction_counts": [
            {"word": key[0], "orbit_support": key[1], "hex_support": key[2], "count": count}
            for key, count in sorted(relation_counts.items())
        ],
        "component_relation_counts": [
            {"word": key[0], "relations": list(key[1:]), "count": count}
            for key, count in sorted(component_counts.items())
        ],
        "fragment_relation_counts": [
            {"word": key[0], "relations": list(key[1:]), "count": count}
            for key, count in sorted(fragment_counts.items())
        ],
        "deficit_phase_counts": {str(key): value for key, value in sorted(phase_counts.items())},
        "legal_macro_tail_count_distribution": dict(sorted(tail_counts.items())),
        "local_fingerprint_count": len(local_tail_sets),
        "local_fingerprints_with_multiple_tail_sets": sum(len(value) > 1 for value in local_tail_sets.values()),
        "minimum_counterexample_word_phase_to_tail_determinacy": counterexample,
        "representatives_by_word": representatives,
        "state_records": state_records,
    }


def automaton_payload() -> dict[str, Any]:
    return {
        "schema": "f1-n2-necessary-defect-automaton-v1",
        "status": "necessary-only quotient; exact visited masks intentionally omitted",
        "state": "(N_charge in {0,1,2}, event_count, last_defect_type, abandonment_credit unused/spent, fragment_phase_type, component_relation, repair_status)",
        "zero_charge_transitions": [
            {"name": "Z3", "condition": "blocked w3 -> new orbit", "delta": {"N": 0, "F": 0, "S": 1, "O": 1, "D": 4}},
            {"name": "Z2-open", "condition": "abandonment w2 -> new orbit", "delta": {"N": 0, "F": 1, "S": 0, "O": 1, "D": 4}, "credit": "unused -> spent"},
            {"name": "Z2-repair", "condition": "blocked w2 -> existing orbit", "delta": {"N": 0, "F": 0, "S": 0, "O": 0, "D": -1}},
        ],
        "positive_charge_transitions": [
            {"name": "R", "condition": "blocked w3 -> existing orbit", "delta": {"N": 1, "F": 0, "S": 1, "O": 0, "D": -1}, "layer": "q -> q+1"},
            {"name": "A2", "condition": "abandonment w2 -> existing orbit", "delta": {"N": 1, "F": 1, "S": 0, "O": 0, "D": -1}, "layer": "q -> q+1", "credit": "unused -> spent"},
            {"name": "A3", "condition": "abandonment w3 -> new orbit", "delta": {"N": 1, "F": 1, "S": 1, "O": 1, "D": 4}, "layer": "q -> q+1", "credit": "unused -> spent"},
            {"name": "J", "condition": "abandonment w3 -> existing orbit", "delta": {"N": 2, "F": 1, "S": 1, "O": 0, "D": -1}, "layer": "0 -> 2", "credit": "unused -> spent", "status": "not excluded by current bookkeeping lemmas"},
        ],
        "proved_word_filter": {
            "unit_charge_words": ["RR", "RA2", "A2R", "RA3", "A3R"],
            "F1_impossible_words": ["A2A2", "A2A3", "A3A2", "A3A3"],
            "additional_single_charge_two_form": ["J"],
        },
        "SCC_statement": "N charge is monotone: every geometrically admitted H=0 joint has DeltaN >= 0. Thus no SCC crosses charge layers. Zero-charge SCCs in this quotient are not exact SCC statements.",
        "unresolved_exact_information": [
            "whether J is realizable in an F=1,H=0 exact prefix",
            "component, fragment, and repair compatibility of two defects",
            "whether disjoint supports make defects swappable",
            "literal collision and capacity terminality",
        ],
    }


def markdown_lemma(truth: Mapping[str, Any]) -> str:
    return """# F=1, H=0, N=2 defect-charge lemma

Status:

- **Proved:** the local truth table, nonnegativity after the blocked-w2 lemma,
  the F=1 word filter, and zero-charge factorisation between positive-charge
  events.
- **Not proved:** that every N=2 completion has exactly two unit defects.

## Correction to the requested normal form

The local row J = abandonment w3 -> existing E-orbit has Delta N=2.
It is not removed by the blocked-w2 lemma.  Therefore the ledger gives

    N=2 = 1+1  or  N=2,

where the second alternative is one charge-two J event.  A two-unit-defect
theorem requires an additional geometric proof that J is impossible.

## Truth table

~~~json
""" + json.dumps(truth, ensure_ascii=False, indent=2, sort_keys=True) + """
~~~

If the charge is split into two unit events, every other joint has zero
charge, so the path has form Z0; d1; Z1; d2; Z2.  The current bookkeeping
does not force a positive length for Z1; adjacent unit defects are not
algebraically excluded.  Component and fragment relations require exact
mask information and are not promoted from observations to theorems.
"""


def markdown_interactions(report: Mapping[str, Any]) -> str:
    bounded = report["bounded_escape_continuation"]
    area = report["area_a_depth6"]
    slim = {key: value for key, value in bounded.items() if key != "events"}
    area_slim = {key: value for key, value in area.items() if key != "state_records"}
    return """# F=1, H=0, N=2 defect interactions

Status:

- **Limited experiment:** bounded continuation from existing N=1 R-escapes.
- **Finite complete replay:** the saved bounded Area-A depth-six frontier.
- Neither source is an exhaustive N=2 calculation.

## Bounded escape continuation

~~~json
""" + json.dumps(slim, ensure_ascii=False, indent=2, sort_keys=True) + """
~~~

The event list is in outputs/f1_n2_defect_words.json.  A pair with disjoint
recorded support is only a candidate for independence; swapping it still
requires literal exact replay.

## Depth-six replay summary

~~~json
""" + json.dumps(area_slim, ensure_ascii=False, indent=2, sort_keys=True) + """
~~~
"""


def markdown_automaton(automaton: Mapping[str, Any]) -> str:
    return "# F=1,H=0,N=2 necessary defect automaton\n\nStatus: **proved local ledger transitions plus a necessary-only quotient**.\n\n~~~json\n" + json.dumps(automaton, ensure_ascii=False, indent=2, sort_keys=True) + "\n~~~\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n0-checkpoint", type=Path, default=IMMUTABLE_N0_DEFAULT)
    parser.add_argument("--area-a-checkpoint", type=Path, default=AREA_A_DEFAULT)
    parser.add_argument("--area-a-snapshot", type=Path, default=AREA_A_SNAPSHOT_DEFAULT)
    parser.add_argument("--bounded-depth", type=int, default=6)
    parser.add_argument("--edge-cap", type=int, default=50000)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    if args.bounded_depth < 0 or args.edge_cap <= 0 or args.edge_cap > 100000:
        raise ValueError("bounded depth must be nonnegative and edge cap must lie in 1..100000")
    if not args.n0_checkpoint.exists() or not args.area_a_checkpoint.exists():
        raise FileNotFoundError("required read-only input is missing")

    truth = finite_truth_table()
    terminals = list(iter_json_array(args.n0_checkpoint, b"terminal_certificates"))
    roots = reconstruct_n1_r_roots(terminals)
    bounded = bounded_second_defects(roots, args.bounded_depth, args.edge_cap)
    area = area_a_depth6_decomposition(args.area_a_checkpoint, args.area_a_snapshot)
    automaton = automaton_payload()
    report = {
        "schema": "f1-n2-defect-analysis-v1",
        "scope": "read-only checkpoints plus a capped continuation from stored N=1 R-escapes; no active N=0 checkpoint is read or modified",
        "code_sha256": {
            "analysis": sha256_file(HERE),
            "macro": macro.CODE_SHA256,
            "engine": macro.ENGINE_SHA256,
            "core": macro.CORE_SHA256,
        },
        "inputs": {
            "immutable_n0_checkpoint": str(args.n0_checkpoint),
            "immutable_n0_checkpoint_sha256": sha256_file(args.n0_checkpoint),
            "area_a_depth6_checkpoint": str(args.area_a_checkpoint),
            "area_a_depth6_checkpoint_sha256": sha256_file(args.area_a_checkpoint),
        },
        "truth_table": truth,
        "terminal_input_count": len(terminals),
        "n1_R_escape_root_count": len(roots),
        "bounded_escape_continuation": bounded,
        "area_a_depth6": area,
        "automaton": automaton,
        "safe_prune_assessment": {
            "proved_safe": [
                "N>2: all geometrically admissible H=0 joints have nonnegative DeltaN",
                "after F=1, any later abandonment is impossible",
                "a unit-defect word containing two A2/A3 letters is impossible",
            ],
            "not_safe_without_additional_proof": [
                "pruning all J states",
                "dominance by defect word, phase type, component, or support relation",
                "treating support-disjoint pairs as swappable",
                "pruning shared split-resource or shared-component pairs",
            ],
        },
    }
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / "PARTIAL_F1_N2_TWO_DEFECT_LEMMA.md").write_text(markdown_lemma(truth), encoding="utf-8")
    (ROOT / "PARTIAL_F1_N2_DEFECT_INTERACTIONS.md").write_text(markdown_interactions(report), encoding="utf-8")
    (out / "f1_n2_defect_words.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (out / "F1_N2_DEFECT_WORDS.md").write_text(markdown_lemma(truth) + "\n" + markdown_interactions(report), encoding="utf-8")
    (out / "f1_n2_depth6_decomposition.json").write_text(json.dumps(area, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (out / "F1_N2_DEPTH6_DECOMPOSITION.md").write_text(
        "# F=1,H=0,N=2 Area-A depth-six decomposition\n\nStatus: **finite complete replay of an existing bounded frontier only**.\n\n~~~json\n"
        + json.dumps({key: value for key, value in area.items() if key != "state_records"}, ensure_ascii=False, indent=2, sort_keys=True) + "\n~~~\n", encoding="utf-8")
    (out / "f1_n2_two_defect_automaton.json").write_text(json.dumps(automaton, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (out / "F1_N2_TWO_DEFECT_AUTOMATON.md").write_text(markdown_automaton(automaton), encoding="utf-8")
    print(json.dumps({
        "terminals": len(terminals),
        "n1_R_roots": len(roots),
        "bounded_second_defect_events": bounded["second_defect_event_count"],
        "bounded_cap_hit": bounded["cap_hit"],
        "area_a_F1_H0_N2": area["selected_F1_H0_N2_frontier_states"],
        "area_a_words": area["ordered_word_counts"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
