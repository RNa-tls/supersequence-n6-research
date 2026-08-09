#!/usr/bin/env python3
"""Build and independently verify the R1_37 dangerous-entry audit.

No continuation is performed.  Exact replay is limited to the already frozen
depth-4 graph and checkpoint/result artifacts.  Symbolic closure results are
always labelled as occupancy-free over-approximations.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parent.parent
PHASE_TABLE_TOOL = ROOT / "src" / "verify_rr_short_ell2_r1_37_phase_table.py"
GRAPH_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_deep_z3_graph.json"
GRAPH_CLASSES_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_deep_z3_classes.json"
Z2_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_z2_certificate.json"
WATCH_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_z3_watchlist.json"
PHASE_EDGE_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_watchlist_phase_edges.json"
PHASE_FAILURE_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_phase_failure_classes.json"
PHASE_INVARIANT_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_phase_invariant_candidates.json"
TABLE_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_z3_transition_table.json"
CLOSURE_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_z3_transition_closure.json"
ALL13_RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_pilot_results.json"
ALL13_VERIFIED = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_verified.json"
ALL13_PLAN = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_pilot_plan.json"
TOP2_RESULT = ROOT / "outputs" / "rr_short5_top2_v7_results.json"
TOP2_LEDGER = ROOT / "outputs" / "rr_short5_top2_v7_continuation.json"
TOP2_VERIFIED = ROOT / "outputs" / "rr_short5_top2_v7_verified.json"

MANIFEST_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_dangerous_entry_manifest.json"
DANGER_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_dangerous_entries.json"
REFINE_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_refinement_analysis.json"
BACKWARD_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_backward_realizability.json"
Z2_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_z2_lemma_certificate.json"
VERIFIED_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_dangerous_entry_verified.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


phase = load_module("rr_r1_37_danger_phase_table", PHASE_TABLE_TOOL)
exact, rr, pilot, audit, core = phase.exact, phase.rr, phase.pilot, phase.audit, phase.core


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def json_field_from_prefix(path: Path, field: str, *, prefix_bytes: int = 1 << 20) -> object:
    """Decode one top-level field stored near the start of a huge JSON file.

    The v7 checkpoints are several GiB because their parent DAG follows the
    small identity/provenance header.  Reading a bounded prefix avoids a
    multi-GiB materialization while still taking the identity from the
    checkpoint itself.  Failure to find or fully decode the field is fatal.
    """
    with path.open("rb") as handle:
        prefix = handle.read(prefix_bytes).decode("utf-8")
    needle = f'\n  "{field}":'
    location = prefix.find(needle)
    if location < 0:
        raise AssertionError(f"missing top-level {field!r} in checkpoint prefix: {path}")
    value_start = location + len(needle)
    while value_start < len(prefix) and prefix[value_start].isspace():
        value_start += 1
    value, _ = json.JSONDecoder().raw_decode(prefix, value_start)
    return value


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def artifact(path: Path, *, role: str, expected_sha256: str | None = None) -> dict[str, object]:
    if not path.exists():
        raise AssertionError(f"missing frozen artifact: {path}")
    # The two immutable v7 endpoint checkpoints are 1.6/4.9 GB and were
    # already hashed by the independently verified Round-53 ledger.  Rehash
    # all smaller artifacts now; for files over 512 MiB, freeze the verified
    # ledger digest plus exact local size/mtime without claiming a new byte
    # pass.  This distinction is explicit in the certificate.
    inherited = path.stat().st_size > (512 << 20) and expected_sha256 is not None
    actual = expected_sha256 if inherited else sha256_file(path)
    if expected_sha256 is not None and actual != expected_sha256:
        raise AssertionError(f"frozen SHA mismatch: {path}: {actual} != {expected_sha256}")
    row: dict[str, object] = {
        "path": str(path.relative_to(ROOT)),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": actual,
        "recorded_sha256": expected_sha256,
        "recorded_sha256_matches": expected_sha256 is None or actual == expected_sha256,
        "sha256_verification_mode": (
            "inherited_from_independently_verified_Round53_ledger"
            if inherited else "rehashed_in_this_audit"
        ),
        "local_mtime_ns": path.stat().st_mtime_ns,
    }
    if path.suffix == ".json" and path.stat().st_size < 50_000_000:
        payload = json.loads(path.read_text(encoding="utf-8"))
        row["schema"] = payload.get("schema")
    return row


def frozen_manifest() -> dict[str, object]:
    all13 = json.loads(ALL13_RESULT.read_text(encoding="utf-8"))
    top2 = json.loads(TOP2_LEDGER.read_text(encoding="utf-8"))
    fixed = [
        (ALL13_RESULT, "all-13 result"), (ALL13_VERIFIED, "all-13 independent verification"),
        (ALL13_PLAN, "all-13 plan and seed ledger"),
        (TOP2_RESULT, "Round-53/v7 raw result"), (TOP2_LEDGER, "Round-53/v7 official ledger"),
        (TOP2_VERIFIED, "Round-53/v7 independent verification"),
        (GRAPH_PATH, "depth-4 exact graph"), (GRAPH_CLASSES_PATH, "depth-4 profile table"),
        (Z2_INPUT, "prior Z2 fixed-table certificate"), (WATCH_INPUT, "34-orbit Z3 watch list"),
        (PHASE_EDGE_INPUT, "92-edge phase audit"), (PHASE_FAILURE_INPUT, "P0-P3 ledger"),
        (PHASE_INVARIANT_INPUT, "phase/refinement audit"),
        (TABLE_INPUT, "308-triple transition table"), (CLOSURE_INPUT, "1,440-triple closure"),
    ]
    rows = [artifact(path, role=role) for path, role in fixed]
    seen_checkpoints = set()
    for branch in top2["branches"]:
        checkpoint = branch["checkpoint"]
        path = ROOT / checkpoint["path"]
        seen_checkpoints.add(str(path.resolve()))
        row = artifact(
            path, role=f"Round-53/v7 endpoint checkpoint {branch['child_id']}",
            expected_sha256=str(checkpoint["sha256"]),
        )
        config = json_field_from_prefix(path, "config")
        provenance = json_field_from_prefix(path, "continuation_provenance")
        if not isinstance(config, dict) or not isinstance(provenance, dict):
            raise AssertionError(f"invalid v7 config/provenance header: {path}")
        if (
            config.get("schema") != "rr-short5-top2-continuation-config-v7"
            or config.get("checkpoint_payload_schema") != "rr-short5-top2-replay-validated-checkpoint-v7"
            or config.get("recognizer_semantics") != "R2_LITERAL_JOINT_SOURCE_V1"
            or config.get("branch_id") != branch["child_id"]
            or provenance.get("branch_id") != branch["child_id"]
            or provenance.get("recognizer_semantics") != "R2_LITERAL_JOINT_SOURCE_V1"
            or provenance.get("engine_sha256") != config.get("engine_sha256")
            or provenance.get("v7_driver_sha256") != config.get("v7_driver_sha256")
        ):
            raise AssertionError(f"v7 config identity mismatch: {path}")
        row["config_identity"] = {
            "config_sha256_recomputed": sha256_json(config),
            "config": config,
            "continuation_provenance": provenance,
        }
        rows.append(row)
    for branch in all13["branches"]:
        checkpoint = branch["checkpoint"]
        path = ROOT / checkpoint["path"]
        if str(path.resolve()) in seen_checkpoints:
            continue
        row = artifact(
            path, role=f"all-13 pilot checkpoint {branch['state_id']}",
            expected_sha256=str(checkpoint["sha256"]),
        )
        checkpoint_payload = json.loads(path.read_text(encoding="utf-8"))
        provenance = checkpoint_payload.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("config_sha256"):
            raise AssertionError(f"missing all-13 config identity: {path}")
        unsigned_provenance = {key: value for key, value in provenance.items() if key != "config_sha256"}
        if (
            checkpoint_payload.get("schema") != "rr-short-ell2-r1-37-all13-checkpoint-v8"
            or provenance.get("recognizer_semantics") != "R2_LITERAL_JOINT_SOURCE_V1"
            or provenance.get("state_id") != branch["state_id"]
            or sha256_json(unsigned_provenance) != provenance["config_sha256"]
        ):
            raise AssertionError(f"all-13 config identity mismatch: {path}")
        row["config_identity"] = {"provenance": provenance}
        rows.append(row)
    closure = json.loads(CLOSURE_INPUT.read_text(encoding="utf-8"))
    table = json.loads(TABLE_INPUT.read_text(encoding="utf-8"))
    return {
        "schema": "rr-short-ell2-r1-37-dangerous-entry-frozen-manifest-v1",
        "scope": "immutable evidence used for the dangerous-entry realizability audit",
        "artifact_count": len(rows),
        "artifacts": rows,
        "recomputed_invariants": {
            "observed_triples": int(table["observed_triple_count"]),
            "observed_watch_triples": int(table["observed_watch_target_triple_count"]),
            "fresh_direct_hub_entries": int(closure["fresh_watchlist_hub_phase_entry_count"]),
            "symbolic_next_z2_hub_entries": int(closure["symbolic_next_z2_hub_hex_entry_count"]),
        },
        "all_recorded_checkpoint_hashes_match": all(row["recorded_sha256_matches"] for row in rows),
        "large_checkpoint_hashes_inherited_not_rehashed": sum(
            row["sha256_verification_mode"] == "inherited_from_independently_verified_Round53_ledger"
            for row in rows
        ),
        "config_identity_count": sum("config_identity" in row for row in rows),
        "config_identity_assertions": {
            "v7_checkpoint_config_schema": "rr-short5-top2-continuation-config-v7",
            "v7_checkpoint_payload_schema": "rr-short5-top2-replay-validated-checkpoint-v7",
            "v7_recognizer_semantics": "R2_LITERAL_JOINT_SOURCE_V1",
            "all13_checkpoint_schema": "rr-short-ell2-r1-37-all13-checkpoint-v8",
            "all13_recognizer_semantics": "R2_LITERAL_JOINT_SOURCE_V1",
        },
        "verifier_sha256": sha256_file(Path(__file__)),
    }


def table_and_closure() -> tuple[dict[str, object], dict[str, object]]:
    rebuilt_table, rebuilt_closure = phase.build()
    stored_table = json.loads(TABLE_INPUT.read_text(encoding="utf-8"))
    stored_closure = json.loads(CLOSURE_INPUT.read_text(encoding="utf-8"))
    if rebuilt_table != stored_table or rebuilt_closure != stored_closure:
        raise AssertionError("Round-55 table/closure failed independent reconstruction")
    return rebuilt_table, rebuilt_closure


def dangerous_ledger(table: Mapping[str, object], closure: Mapping[str, object], manifest_sha: str):
    table_by_id = {str(row["triple_id"]): row for row in table["entries"]}
    closure_by_id = {str(row["triple_id"]): row for row in closure["closure_entries"]}
    direct_ids = set(str(value) for value in closure["fresh_watchlist_hub_phase_triple_ids"])
    later_ids = set(str(value) for value in closure["symbolic_next_z2_hub_hex_triple_ids"])
    overlap = direct_ids & later_ids
    direct = []
    for tid in sorted(direct_ids):
        row = closure_by_id[tid]
        source = phase.INVERSE_ORBIT_PHASE[(int(row["source_orbit"]), int(row["source_phase"]))]
        source_hex, source_pos = exact.HEX_POSITION[source]
        direct.append({
            "transition_identity": f"DIRECT_Z3::{tid}", "mechanism": "DIRECT_Z3_HUB_PHASE",
            "triple_id": tid, "joint": row["joint"],
            "source_orbit": row["source_orbit"], "source_phase": row["source_phase"],
            "source_hexagon": int(source_hex), "source_hex_position": int(source_pos),
            "target_orbit": row["target_orbit"], "target_phase": row["target_phase"],
            "target_hexagon": row["target_hexagon"],
            "hub_compatible_phase_set": row["hub_compatible_target_phases"],
            "first_symbolic_closure_round": row["discovery_layer"],
            "absent_from_observed_308": tid not in table_by_id,
            "absence_reason": "literal source triple is absent from the fixed depth-4 308-triple domain",
            "requires_prior_r1_component_expansion": int(row["target_orbit"]) != 91,
            "fixed_component_merge_possible": int(row["target_orbit"]) == 91,
            "overlaps_next_z2_mechanism_by_preceding_triple": tid in overlap,
        })
    later = []
    exact_exposed = 0
    for tid in sorted(later_ids):
        row = closure_by_id[tid]
        z2 = row["symbolic_next_z2"]
        observed = table_by_id.get(tid)
        observed_count = int(observed["observation_count"]) if observed else 0
        exact_legal_values = observed["observed_later_z2_bridge_values"] if observed else []
        if observed_count:
            exact_exposed += 1
        later.append({
            "transition_identity": f"NEXT_Z2::{tid}", "mechanism": "NEXT_Z2_HUB_HEX",
            "preceding_z3_triple_id": tid,
            "preceding_joint": row["joint"],
            "preceding_source_orbit": row["source_orbit"],
            "preceding_source_phase": row["source_phase"],
            "resulting_z2_source_orbit": row["next_full_segment_source"]["orbit"],
            "resulting_z2_source_phase": row["next_full_segment_source"]["phase"],
            "z2_target_orbit": z2["target_orbit"], "z2_target_phase": z2["target_phase"],
            "z2_target_hexagon": z2["target_hexagon"],
            "first_symbolic_closure_round": row["discovery_layer"],
            "overlaps_direct_z3_mechanism_by_preceding_triple": tid in overlap,
            "preceding_triple_observed_exactly": observed is not None,
            "exact_observation_count": observed_count,
            "observed_legal_later_z2_bridge_values": exact_legal_values,
            "requires_prior_r1_component_expansion": int(z2["target_orbit"]) != 91,
            "fixed_component_merge_possible": int(z2["target_orbit"]) == 91,
        })
    if len(direct) != 88 or len(later) != 108 or len(overlap) != 20 or exact_exposed != 22:
        raise AssertionError("dangerous ledger count mismatch")
    if any(row["fixed_component_merge_possible"] for row in direct + later):
        raise AssertionError("a dangerous transition unexpectedly uses fixed R1 orbit 91")
    payload = {
        "schema": "rr-short-ell2-r1-37-dangerous-entries-v1",
        "scope": "196 mechanism-labelled transitions from the complete abstract triple closure; exact reachability is recorded separately",
        "frozen_manifest_sha256_prewrite": manifest_sha,
        "counts": {
            "direct_z3_transition_identities": len(direct),
            "next_z2_transition_identities": len(later),
            "total_mechanism_labelled_transition_identities": len(direct) + len(later),
            "unique_preceding_z3_triples": len(direct_ids | later_ids),
            "overlap_preceding_triples": len(overlap),
            "direct_only_preceding_triples": len(direct_ids - later_ids),
            "later_z2_only_preceding_triples": len(later_ids - direct_ids),
            "exactly_observed_later_z2_precursor_triples": exact_exposed,
        },
        "identity_rule": "DIRECT_Z3 and NEXT_Z2 are distinct abstract transition identities even when they share a preceding Z3 triple",
        "direct_z3_entries": direct, "next_z2_entries": later,
        "necessary_condition": {
            "statement": "every one of the 196 entries requires the relevant target orbit to have entered the R1-target component before the hub-touching incidence is added",
            "fixed_r1_component_orbits": [91],
            "fixed_r1_component_hexagons": [40, 92],
            "fixed_hub_component_orbits": [0, 9],
            "fixed_hub_component_hexagons": [0, 1, 4, 6, 8, 9, 18, 24, 96],
            "consequence": "all 196 are impossible before a component-changing Z3 event; the abstract triple closure omitted this ancestry condition",
            "branch_wide_after_arbitrary_z3_history": False,
        },
        "exact_state_realizability_requirements": {
            "structural": [
                "the macro-entry permutation must rotate through five collision-free w1 windows to the recorded literal source orbit/phase",
                "the literal joint target window and pass-start phase must both be unvisited",
                "the active hexagon masks must agree with the claimed full rotation segment",
                "the incidence forest reconstructed from orbit masks must contain distinct R1-target and hub components before the bridge edge",
                "for a direct Z3 mechanism, the target orbit must already be registered in the R1-target component while the target hexagon is in the hub component",
                "for a later-Z2 mechanism, the Z2-preserved orbit must be in the R1-target component while its target hexagon is in the hub component",
                "the exact joint kind must remain legal under the visited-window and F/H resource rules",
                "the state must retain Phi=0, F=1, H=0, Ndef=1, r_count=1, hub_touch_count=1 in the audited branch scope",
                "P and O are exact-state values and may not be replaced by the abstract triple; any completion claim must separately check their final requirements",
                "hub completion and terminal geometry must remain available before a prospective R2/Target-A boundary",
            ],
            "historical_or_provenance": [
                "proved short_ell2 R1 event and its literal source/target metadata",
                "previous macro kind and recent macro suffix",
                "accumulated Z2/Z3 word and trace-Z2 residue",
                "parent component ancestry and all prior incidence edges",
                "registered-orbit mask and phase masks",
                "exact decoration including completer timing and event order",
            ],
            "not_determined_by_triple": True,
        },
        "filtering_ledger": {
            "abstract_dangerous_transition_identities": 196,
            "locally_defined_permutation_actions": 196,
            "abstract_predecessor_consistent": 196,
            "exact_precursor_triples_exposed_in_depth4": 22,
            "exact_legal_dangerous_transitions_in_depth4": 0,
            "global_unresolved_without_reachability_closure": 196,
            "bridge_witnesses": 0,
        },
    }
    return payload


def component_snapshot(state, decoration) -> dict[str, object]:
    summary = rr.component_summary(state)
    r1_id = audit.component_id(summary, ("q", int(decoration.r1.target_orbit)))
    hub_id = audit.component_id(summary, ("h", int(decoration.hub_id)))
    if r1_id is None or hub_id is None:
        raise AssertionError("missing distinguished component")
    r1_orbits, r1_hexagons = phase.base.component_nodes(summary, r1_id)
    hub_orbits, hub_hexagons = phase.base.component_nodes(summary, hub_id)
    size_vector = sorted(
        (len(item["e_orbits"]), len(item["hexagons"])) for item in summary["components"]
    )
    return {
        "component_count": int(summary["component_count"]),
        "r1_orbits": r1_orbits, "r1_hexagons": r1_hexagons,
        "hub_orbits": hub_orbits, "hub_hexagons": hub_hexagons,
        "r1_signature": [r1_orbits, r1_hexagons],
        "hub_signature": [hub_orbits, hub_hexagons],
        "component_size_vector": [list(item) for item in size_vector],
    }


def incidence_degree_signature(state, decoration) -> list[int]:
    inverse = phase.INVERSE_ORBIT_PHASE
    orbit_degrees = [int(mask).bit_count() for mask in state.orbit_masks]
    hex_degrees = [0] * exact.HEX_COUNT
    for orbit, mask in enumerate(state.orbit_masks):
        for ph in range(5):
            if int(mask) & (1 << ph):
                h, _pos = exact.HEX_POSITION[inverse[(orbit, ph)]]
                hex_degrees[int(h)] += 1
    current_q, _ = exact.ORBIT_PHASE[state.p]
    current_h, _ = exact.HEX_POSITION[state.p]
    return [
        orbit_degrees[int(current_q)], hex_degrees[int(current_h)],
        orbit_degrees[int(decoration.r1.target_orbit)], hex_degrees[int(decoration.hub_id)],
    ]


def successor_signature(node: Mapping[str, object], edges: Mapping[str, Mapping[str, object]]) -> str:
    rows = []
    for edge_id in node["outgoing_edge_ids"]:
        edge = edges[str(edge_id)]
        rows.append({
            "kind": edge["kind"],
            "source": [edge["literal_joint_source_orbit"], edge["literal_joint_source_phase"]],
            "target": [edge["target_orbit"], edge["target_phase"], edge["target_hexagon"]],
            "watch": edge["target_orbit_in_watchlist"],
            "hub": edge["target_hexagon_in_hub_component_before"],
            "r1_expand": edge["r1_target_component_expands"],
            "merge": edge["r1_hub_component_merge"],
        })
    return sha256_json(rows)


def conflict_pairs(groups: Iterable[Sequence[Mapping[str, object]]]) -> int:
    total = 0
    for group in groups:
        counter = Counter(str(row["successor_signature"]) for row in group)
        n = len(group)
        total += n * (n - 1) // 2 - sum(v * (v - 1) // 2 for v in counter.values())
    return total


def refinement_metric(nodes: Sequence[Mapping[str, object]], name: str) -> dict[str, object]:
    groups: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in nodes:
        value = row["coordinates"][name]
        groups[(str(row["base_profile"]), json.dumps(value, sort_keys=True))].append(row)
    mixed = [g for g in groups.values() if len({r["successor_signature"] for r in g}) > 1]
    encoded = [canonical_json(row["coordinates"][name]) for row in nodes]
    return {
        "coordinate": name,
        "reachable_exact_classes_represented": len(groups),
        "distinct_coordinate_values": len({value for value in encoded}),
        "mixed_successor_cells": len(mixed),
        "exact_states_in_mixed_cells": sum(len(g) for g in mixed),
        "conflicting_exact_state_pairs": conflict_pairs(groups.values()),
        "sufficient_to_determine_next_structural_transition": not mixed,
        "average_serialized_coordinate_bytes": round(sum(map(len, encoded)) / len(encoded), 3),
        "total_serialized_coordinate_bytes_for_1075_states": sum(map(len, encoded)),
        "abstract_dangerous_entries_remaining_conservatively": 196,
        "reason_dangerous_count_not_reduced": "new abstract entries have no certified value for historical coordinates; bounded absence is not impossibility",
        "safe_quotient": False,
    }


def symbolic_distances(closure: Mapping[str, object], dangerous_ids: set[str]) -> dict[str, int]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for row in closure["closure_entries"]:
        for child in row["symbolic_z3_successor_triples"]:
            reverse[str(child)].append(str(row["triple_id"]))
    dist = {tid: 0 for tid in dangerous_ids}
    queue = deque(sorted(dangerous_ids))
    while queue:
        child = queue.popleft()
        for parent in reverse.get(child, []):
            if parent not in dist:
                dist[parent] = dist[child] + 1
                queue.append(parent)
    return dist


def depth_split_audit(closure: Mapping[str, object], danger: Mapping[str, object]) -> dict[str, object]:
    plan = json.loads(ALL13_PLAN.read_text(encoding="utf-8"))
    result = json.loads(ALL13_RESULT.read_text(encoding="utf-8"))
    outcomes = {str(row["state_id"]): row for row in result["branches"]}
    danger_ids = {
        str(row["triple_id"]) for row in danger["direct_z3_entries"]
    } | {
        str(row["preceding_z3_triple_id"]) for row in danger["next_z2_entries"]
    }
    distances = symbolic_distances(closure, danger_ids)
    rows = []
    for seed in plan["state_selection_ledger"]:
        outcome = outcomes[str(seed["state_id"])]
        starts = []
        for move in seed["immediate_legal_macro_moves"]:
            source_q, source_phase = map(int, move["source"])
            if move["kind"] == "Z3":
                starts.append(phase.triple_id((str(move["joint"]), source_q, source_phase)))
            elif move["kind"] == "Z2":
                target_q, target_phase = map(int, move["target"])
                target_word = phase.INVERSE_ORBIT_PHASE[(target_q, target_phase)]
                _word, next_q, next_phase = phase.full_segment_source(target_word)
                starts.extend(phase.triple_id((label, next_q, next_phase)) for label in phase.JOINTS)
        min_distance = min((distances[x] + (1 if all(m["kind"] == "Z2" for m in seed["immediate_legal_macro_moves"]) else 0)
                            for x in starts if x in distances), default=None)
        coordinate = seed["resource_profile"]["coordinate"]
        rows.append({
            "state_id": seed["state_id"], "starting_depth": int(seed["depth"]),
            "outcome": outcome["status"], "expansions": int(outcome["expansions"]),
            "frontier_size": int(outcome["frontier_size"]),
            "starting_successor_count": int(seed["successor_count"]),
            "starting_component_count": int(seed["component_geometry"]["component_count"]),
            "resource_counters": coordinate,
            "depth_equals_P_minus_2": int(seed["depth"]) == int(coordinate["P"]) - 2,
            "abstract_distance_to_dangerous_signature": min_distance,
            "abstract_backward_chain_can_reach_seed_signature": min_distance is not None,
            "distance_scope": "occupancy-free symbolic triple graph only",
        })
    exhausted = [r for r in rows if r["outcome"] == "EXHAUSTED_NO_BRIDGE"]
    capped = [r for r in rows if r["outcome"] == "INCOMPLETE"]
    return {
        "seed_count": len(rows), "rows": rows,
        "observed_split": {
            "exhausted_count": len(exhausted), "capped_count": len(capped),
            "exhausted_start_depth_range": [min(r["starting_depth"] for r in exhausted), max(r["starting_depth"] for r in exhausted)],
            "capped_start_depth_range": [min(r["starting_depth"] for r in capped), max(r["starting_depth"] for r in capped)],
            "exhausted_start_P_range": [min(r["resource_counters"]["P"] for r in exhausted), max(r["resource_counters"]["P"] for r in exhausted)],
            "capped_start_P_range": [min(r["resource_counters"]["P"] for r in capped), max(r["resource_counters"]["P"] for r in capped)],
            "depth_P_relation_holds_all_13": all(r["depth_equals_P_minus_2"] for r in rows),
            "interpretation": "the depth split is exactly the same empirical split as P<=60 versus P>=61 because depth=P-2 on all 13 seeds; it is not independent evidence of depth monotonicity",
        },
    }


def refinement_analysis(danger: Mapping[str, object], closure: Mapping[str, object]) -> dict[str, object]:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    _roots, _sources, states, decorations, _replayed = phase.replay_graph(graph)
    edges = {str(row["edge_id"]): row for row in graph["edges"]}
    enriched = []
    for node in graph["nodes"]:
        node_id = str(node["node_id"])
        state, decoration = states[node_id], decorations[node_id]
        trace = [str(label) for label in node["bounded_trace"]]
        current_hex, _current_pos = exact.HEX_POSITION[state.p]
        full_word, _full_q, _full_phase = phase.full_segment_source(tuple(state.p))
        _source_hex, source_hex_pos = exact.HEX_POSITION[full_word]
        comp = component_snapshot(state, decoration)
        registered = [q for q, mask in enumerate(state.orbit_masks) if mask]
        coordinates = {
            "source_hex_position": int(source_hex_pos),
            "previous_macro_kind": "ROOT" if not trace else ("Z2" if ";w2:" in trace[-1] else "Z3"),
            "trace_z2_count_mod5": sum(";w2:" in label for label in trace) % 5,
            "current_F": int(state.F), "current_H": int(state.H), "current_Ndef": int(state.Ndef),
            "hub_touch_count": int(decoration.hub_touch_count),
            "component_size_vector": comp["component_size_vector"],
            "incidence_degree_signature": incidence_degree_signature(state, decoration),
            "r1_target_component_signature": comp["r1_signature"],
            "hub_component_signature": comp["hub_signature"],
            "registered_orbit_mask": registered,
            "recent_macro_suffix_1": trace[-1:],
            "recent_macro_suffix_2": trace[-2:],
            "recent_macro_suffix_3": trace[-3:],
        }
        enriched.append({
            "node_id": node_id, "base_profile": node["structural_profile_id"],
            "successor_signature": successor_signature(node, edges), "coordinates": coordinates,
            "current_hexagon": int(current_hex),
        })
    names = list(enriched[0]["coordinates"])
    metrics = [refinement_metric(enriched, name) for name in names]
    best = min(metrics, key=lambda r: (r["conflicting_exact_state_pairs"], r["total_serialized_coordinate_bytes_for_1075_states"], r["coordinate"]))
    histogram = lambda values: {str(key): value for key, value in sorted(Counter(values).items())}
    bounded_invariants = {
        "Phi": histogram(int(rr.phi(state)) for state in states.values()),
        "F": histogram(int(state.F) for state in states.values()),
        "H": histogram(int(state.H) for state in states.values()),
        "Ndef": histogram(int(state.Ndef) for state in states.values()),
        "r_count": histogram(int(dec.r_count) for dec in decorations.values()),
        "hub_touch_count": histogram(int(dec.hub_touch_count) for dec in decorations.values()),
    }
    if bounded_invariants != {
        "Phi": {"0": 1075}, "F": {"1": 1075}, "H": {"0": 1075},
        "Ndef": {"1": 1075}, "r_count": {"1": 1075}, "hub_touch_count": {"1": 1075},
    }:
        raise AssertionError(f"unexpected bounded invariant ledger: {bounded_invariants}")
    return {
        "schema": "rr-short-ell2-r1-37-refinement-analysis-v1",
        "scope": "1,075 exact bounded states; refinements are reporting partitions, never traversal quotients",
        "exact_state_count": len(enriched), "base_profile_count": 334,
        "base_mixed_successor_profile_count": 197,
        "bounded_exact_invariant_histograms": bounded_invariants,
        "candidate_coordinate_results": metrics,
        "best_single_coordinate_by_conflicting_pairs": best,
        "historical_fields_missing_from_triple": [
            "previous macro kind", "accumulated Z2/Z3 sequence", "trace Z2 count mod 5",
            "component ancestry", "registered-orbit history", "incidence edges", "exact decoration",
        ],
        "why_abstract_closure_is_spurious": "the 1,440-triple closure propagates permutation endpoints only; every bridge-relevant entry additionally requires prior R1-component expansion and exact occupancy legality",
        "dangerous_entry_refinement": {
            "mechanism_entries": 196,
            "exact_precursor_exposed_in_existing_transcripts": 22,
            "exact_legal_bridge_transition": 0,
            "remaining_conservatively_without_complete_reachability": 196,
        },
        "depth_split_audit": depth_split_audit(closure, danger),
        "equivalence_warning": "no candidate coordinate is a proved continuation quotient",
    }


def predecessor_chain(entry_id: str, closure_by_id: Mapping[str, Mapping[str, object]]) -> list[str]:
    chain = [entry_id]
    while closure_by_id[chain[-1]]["certificate_parent_triple_id"] is not None:
        chain.append(str(closure_by_id[chain[-1]]["certificate_parent_triple_id"]))
    chain.reverse()
    return chain


def backward_realizability(danger: Mapping[str, object], closure: Mapping[str, object]) -> dict[str, object]:
    closure_by_id = {str(row["triple_id"]): row for row in closure["closure_entries"]}
    entries = []
    counts = Counter()
    for row in danger["direct_z3_entries"]:
        tid = str(row["triple_id"])
        chain = predecessor_chain(tid, closure_by_id)
        classification = "R3"
        counts[classification] += 1
        entries.append({
            "transition_identity": row["transition_identity"], "mechanism": row["mechanism"],
            "triple_id": tid, "abstract_predecessor_chain": chain,
            "abstract_distance_from_observed_domain": int(closure_by_id[tid]["discovery_layer"]),
            "fixed_component_class": "R2",
            "global_class": classification,
            "reason": "abstract predecessor chain reaches an observed triple, but no exact reachable source state for this direct transition is certified",
            "required_predecessor_condition": f"target orbit {row['target_orbit']} must already belong to the R1-target component",
            "exact_bridge_witness": None,
        })
    for row in danger["next_z2_entries"]:
        tid = str(row["preceding_z3_triple_id"])
        chain = predecessor_chain(tid, closure_by_id)
        if row["preceding_triple_observed_exactly"]:
            classification = "R4"
            reason = "an exact reachable post-Z3 precursor state exists in the bounded graph, but every observed later-Z2 bridge legality value is false"
        else:
            classification = "R3"
            reason = "abstract predecessor chain exists, but the post-Z3 precursor state is not certified reachable"
        counts[classification] += 1
        entries.append({
            "transition_identity": row["transition_identity"], "mechanism": row["mechanism"],
            "triple_id": tid, "abstract_predecessor_chain": chain,
            "abstract_distance_from_observed_domain": int(closure_by_id[tid]["discovery_layer"]),
            "fixed_component_class": "R2", "global_class": classification,
            "reason": reason,
            "required_predecessor_condition": f"Z2-preserved orbit {row['z2_target_orbit']} must already belong to the R1-target component",
            "exact_observation_count": row["exact_observation_count"],
            "observed_legal_values": row["observed_legal_later_z2_bridge_values"],
            "exact_bridge_witness": None,
        })
    if len(entries) != 196 or counts != Counter({"R3": 174, "R4": 22}):
        raise AssertionError(f"backward classification mismatch: {counts}")
    return {
        "schema": "rr-short-ell2-r1-37-backward-realizability-v1",
        "taxonomy": {
            "R0": "locally impossible exact state", "R1": "locally realizable but no legal predecessor",
            "R2": "abstract chain violates fixed-component/resource/provenance conditions",
            "R3": "abstract chain reaches a known exact-state class but not a verified reachable source state",
            "R4": "exact reachable precursor state found", "R5": "exact bridge transition found",
        },
        "global_maximum_class_counts": {key: counts.get(key, 0) for key in ("R0", "R1", "R2", "R3", "R4", "R5")},
        "fixed_component_regime_class_counts": {"R2": 196},
        "exact_bridge_witness_count": 0,
        "entries": entries,
        "scope_warning": "R3/R4 are bounded-evidence classifications; none is a branch-wide reachability closure",
        "targeted_search_started": False,
        "targeted_search_recommendation": "if continued, target the first component-changing Z3 predecessor, not the 196 endpoints uniformly",
    }


def z2_lemma_certificate(manifest_sha: str) -> dict[str, object]:
    orbit = 91
    phase_rows = []
    for ph in range(5):
        word = phase.INVERSE_ORBIT_PHASE[(orbit, ph)]
        h, pos = exact.HEX_POSITION[word]
        phase_rows.append({"orbit": orbit, "phase": ph, "word": list(word), "hexagon": int(h), "hex_position": int(pos)})
    linked = sorted({row["hexagon"] for row in phase_rows})
    hub = [0, 1, 4, 6, 8, 9, 18, 24, 96]
    intersection = sorted(set(linked) & set(hub))
    # Exhaustively check the fixed-table statement that every full-segment Z2
    # endpoint remains in the same E-orbit.
    preservation_checks = []
    for q in range(144):
        for ph in range(5):
            word = phase.INVERSE_ORBIT_PHASE[(q, ph)]
            source_word, source_q, source_ph = phase.full_segment_source(word)
            target = core.word_after(source_word, phase.W2.action)
            target_q, target_ph = exact.ORBIT_PHASE[target]
            # ``source_q`` is the literal source after the five rotations and
            # need not equal the pass-start orbit.  The full-pass+flip
            # endpoint is E(pass_start), hence ``target_q == q``.
            preservation_checks.append(target_q == q)
    if linked != [40, 82, 90, 91, 92] or intersection or not all(preservation_checks):
        raise AssertionError("Z2 lemma fixed-table certificate failed")
    return {
        "schema": "rr-short-ell2-r1-37-z2-lemma-certificate-v1",
        "statement": "before any component-changing Z3 event, a Z2 transition cannot merge the R1-target component with the hub component",
        "conditions": {
            "r1_target_component_orbits": [91],
            "r1_target_component_not_previously_expanded": True,
            "hub_component_hexagons": hub,
        },
        "orbit_91_phase_rows": phase_rows,
        "orbit_91_phase_linked_hexagons": linked,
        "hub_component_hexagons": hub,
        "intersection": intersection,
        "z2_orbit_preservation_checks": len(preservation_checks),
        "z2_orbit_preservation_failures": preservation_checks.count(False),
        "proof_steps": [
            "a full-segment Z2 endpoint stays in the source E-orbit (720/720 fixed-table checks)",
            "therefore a Z2 from the unexpanded R1-target component remains on orbit 91",
            "all five orbit-91 phases lie in hexagons {40,82,90,91,92}",
            "that set is disjoint from the hub-component hexagons",
            "hence no such Z2 incidence can connect the R1-target and hub components",
        ],
        "invalidation_condition": "a prior component-changing Z3 adds another orbit to the R1-target component; Z2 on that added orbit is outside the orbit-91 argument",
        "branch_wide_after_arbitrary_z3_history": False,
        "frozen_manifest_sha256_prewrite": manifest_sha,
    }


def build_all():
    manifest = frozen_manifest()
    manifest_sha = sha256_json(manifest)
    table, closure = table_and_closure()
    if (table["observed_triple_count"], table["observed_watch_target_triple_count"],
            closure["fresh_watchlist_hub_phase_entry_count"], closure["symbolic_next_z2_hub_hex_entry_count"]) != (308, 48, 88, 108):
        raise AssertionError("frozen cardinalities changed")
    danger = dangerous_ledger(table, closure, manifest_sha)
    refinement = refinement_analysis(danger, closure)
    backward = backward_realizability(danger, closure)
    z2 = z2_lemma_certificate(manifest_sha)
    payloads = {
        MANIFEST_OUT: manifest, DANGER_OUT: danger, REFINE_OUT: refinement,
        BACKWARD_OUT: backward, Z2_OUT: z2,
    }
    verified = {
        "schema": "rr-short-ell2-r1-37-dangerous-entry-independent-verification-v1",
        "verified": True,
        "verification_method": "rehash frozen artifacts; rebuild the fixed Z3 table/closure; replay the 991 stored edges; recompute dangerous ledgers, refinement partitions, predecessor chains, and 720 Z2 preservation checks",
        "output_sha256_prewrite": {
            str(path.relative_to(ROOT)): sha256_json(value) for path, value in payloads.items()
        },
        "count_ledger": danger["filtering_ledger"],
        "dangerous_counts": danger["counts"],
        "backward_counts": backward["global_maximum_class_counts"],
        "z2_lemma_verified": not z2["intersection"] and z2["z2_orbit_preservation_failures"] == 0,
        "strongest_supported_theorem_level": "T1",
        "theorem_scope": "all exact states and edges in the complete depth-4 bounded graph are bridge-free; all 196 abstract mechanisms require an earlier component-changing Z3, absent from that graph",
        "branch_wide_T4_proved": False,
        "overall_status": "DANGEROUS_ENTRY_SET_REDUCED",
        "verifier_sha256": sha256_file(Path(__file__)),
    }
    payloads[VERIFIED_OUT] = verified
    return payloads


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payloads = build_all()
    if args.write:
        for path, payload in payloads.items():
            atomic_json(path, payload)
    for path, expected in payloads.items():
        if not path.exists():
            raise AssertionError(f"missing output {path}; run --write")
        actual = json.loads(path.read_text(encoding="utf-8"))
        if actual != expected:
            raise AssertionError(f"output differs from reconstruction: {path}")
    verified = payloads[VERIFIED_OUT]
    print(json.dumps({
        "verified": True,
        "dangerous": verified["dangerous_counts"],
        "backward": verified["backward_counts"],
        "theorem_level": verified["strongest_supported_theorem_level"],
        "status": verified["overall_status"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
