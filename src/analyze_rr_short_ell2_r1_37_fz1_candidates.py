#!/usr/bin/env python3
"""Round 59: read-only FZ1 local-candidate reachability audit.

The six immutable Round-58 Stage-D checkpoints are replayed literally.  The
audit separates the fixed 20-orbit incidence-table possibility from exact
reachability.  It never changes a search checkpoint and it never prunes a
continuation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
R4_INPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_backward_realizability.json"

CANDIDATES_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_orbits.json"
LEDGER_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_condition_ledger.json"
SEEDS_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_seed3_seed6_candidate_census.json"
R4_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_r4_candidate_crosscheck.json"
BOUND_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_144z3_bound_audit.json"

SCHEMA = "rr-short-ell2-r1-37-fz1-candidate-reachability-v1"
R1_ORBIT = 91
HUB_HEXAGONS = frozenset({0, 1, 4, 6, 8, 9, 18, 24, 96})
LEVELS = tuple(f"C{i}" for i in range(7))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


search = load_module(
    "rr_fz1_stage_d_search",
    ROOT / "src" / "search_rr_short_ell2_r1_37_first_component_z3.py",
)
rr, exact, pilot, core = search.rr, search.exact, search.pilot, search.core
macro = rr.macro


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def iter_top_array(path: Path, key: str) -> Iterable[dict[str, object]]:
    """Stream objects from a compact top-level JSON array without mutation."""
    marker = (json.dumps(key) + ":[").encode("ascii")
    decoder = json.JSONDecoder()
    with path.open("rb") as handle:
        data = b""
        while marker not in data:
            block = handle.read(1 << 20)
            if not block:
                raise AssertionError(f"array {key!r} absent in {path}")
            data = (data + block)[-max(len(marker) - 1, 1) - len(block):]
        position = data.index(marker) + len(marker)
        buffer = data[position:].decode("utf-8")
        while True:
            buffer = buffer.lstrip(" \r\n\t,")
            if buffer.startswith("]"):
                return
            try:
                item, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                block = handle.read(1 << 20)
                if not block:
                    raise
                buffer += block.decode("utf-8")
                continue
            if not isinstance(item, dict):
                raise AssertionError(f"non-object in {key} array")
            yield item
            buffer = buffer[end:]


def orbit_rows(orbit_id: int) -> list[dict[str, object]]:
    rows = []
    for phase, word in enumerate(core.orbit(core.E_REPS[orbit_id], core.E)):
        q, recovered_phase = exact.ORBIT_PHASE[word]
        h, hpos = exact.HEX_POSITION[word]
        if q != orbit_id or recovered_phase != phase:
            raise AssertionError("fixed ORBIT_PHASE inverse mismatch")
        rows.append({
            "orbit": orbit_id,
            "phase": phase,
            "word": list(word),
            "hexagon": int(h),
            "hex_rotation_position": int(hpos),
        })
    return rows


def build_candidate_table() -> tuple[dict[str, object], dict[int, dict[str, object]]]:
    phase_rows = {q: orbit_rows(q) for q in range(exact.ORBIT_COUNT)}
    phase_hex = {q: {int(row["hexagon"]) for row in rows} for q, rows in phase_rows.items()}
    r1_hex = phase_hex[R1_ORBIT]
    candidates: dict[int, dict[str, object]] = {}
    degrees = Counter()
    for q in range(exact.ORBIT_COUNT):
        degrees[sum(bool(phase_hex[q] & phase_hex[r]) for r in range(exact.ORBIT_COUNT) if r != q)] += 1
        if q == R1_ORBIT or not (phase_hex[q] & r1_hex):
            continue
        r1_hits = [row for row in phase_rows[q] if int(row["hexagon"]) in r1_hex]
        hub_hits = [row for row in phase_rows[q] if int(row["hexagon"]) in HUB_HEXAGONS]
        templates = []
        for attach in r1_hits:
            for hub in hub_hits:
                templates.append({
                    "r1_attachment_phase": int(attach["phase"]),
                    "r1_attachment_hexagon": int(attach["hexagon"]),
                    "hub_attachment_phase": int(hub["phase"]),
                    "hub_attachment_hexagon": int(hub["hexagon"]),
                    "E_phase_displacement": (int(hub["phase"]) - int(attach["phase"])) % 5,
                })
        candidates[q] = {
            "orbit_id": q,
            "all_phase_rows": phase_rows[q],
            "orbit_91_contact_hexagons": sorted(phase_hex[q] & r1_hex),
            "orbit_91_contact_phases": sorted(int(row["phase"]) for row in r1_hits),
            "hub_contact_hexagons": sorted(phase_hex[q] & HUB_HEXAGONS),
            "hub_contact_phases": sorted(int(row["phase"]) for row in hub_hits),
            "touches_hub": bool(hub_hits),
            "direct_local_two_edge_bridge_potential": bool(hub_hits),
            "two_edge_templates": templates,
            "exact_local_legality_conditions": [
                "the R1-attachment target phase must be unvisited and its hexagon must already be in C_R1",
                "the candidate orbit must be fresh so the blocked weight-3 event is Z3, not R",
                "F=1 and H=0 and the F1 fragment normal form must survive the event",
                "a later incidence at a listed hub phase must be collision-free in the same literal history",
                "the later incidence must preserve the future R2 source and terminal geometry",
            ],
        }
    if sorted(r1_hex) != [40, 82, 90, 91, 92]:
        raise AssertionError("orbit-91 phase-linked hexagon set changed")
    if len(candidates) != 20 or set(degrees) != {20} or degrees[20] != 144:
        raise AssertionError(f"candidate/degree reproduction failed: {len(candidates)}, {degrees}")
    hub_candidates = sorted(q for q, row in candidates.items() if row["touches_hub"])
    if hub_candidates != [96, 120, 126, 128, 129]:
        raise AssertionError(f"five hub-touch candidates changed: {hub_candidates}")
    payload = {
        "schema": "rr-short-ell2-r1-37-fz1-candidate-orbits-v1",
        "claim_status": "PROVED_BY_FIXED_144_ORBIT_TABLE_EXHAUSTION",
        "definition": "all E-orbits other than 91 sharing at least one rotation hexagon with one of orbit 91's five phases",
        "r1_target_orbit": R1_ORBIT,
        "r1_phase_linked_hexagons": sorted(r1_hex),
        "hub_component_hexagons": sorted(HUB_HEXAGONS),
        "candidate_count": len(candidates),
        "candidate_orbits": [candidates[q] for q in sorted(candidates)],
        "hub_touching_candidate_count": len(hub_candidates),
        "hub_touching_candidate_orbits": hub_candidates,
        "all_orbit_adjacency_degree_histogram": dict(sorted(degrees.items())),
        "claude_comparison": {
            "reported_candidate_count": 20,
            "reported_hub_touching_count": 5,
            "candidate_count_matches": len(candidates) == 20,
            "hub_touching_count_matches": len(hub_candidates) == 5,
            "explicit_reported_orbit_ids_available": False,
        },
        "inputs": {
            "core_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_port_lift.py"),
            "exact_engine_sha256": sha256_file(ROOT / "legacy_research" / "work" / "superperm_partial_f1.py"),
            "analyzer_sha256": sha256_file(Path(__file__)),
        },
    }
    return payload, candidates


def component_nodes(item: Mapping[str, object] | None) -> frozenset[tuple[str, int]]:
    return search.component_nodes(item)


def classify_candidate_attempts(state, dec, candidates: Mapping[int, Mapping[str, object]], *,
                                count_all_legal: bool = False) -> tuple[list[dict[str, object]], int]:
    """Classify every weight-3 attempt targeting one of the 20 candidates."""
    summary = rr.component_summary(state)
    r1 = search.component(summary, ("q", R1_ORBIT))
    if r1 is None:
        raise AssertionError("R1 target orbit absent from reachable state")
    r1_hexagons = set(int(x) for x in r1["hexagons"])
    r1_orbits = set(int(x) for x in r1["e_orbits"])
    attempts: list[dict[str, object]] = []
    legal_successors = 0
    for run in macro.rotation_runs(state):
        if run.state.orbit_masks != state.orbit_masks:
            raise AssertionError("rotation run unexpectedly changed the incidence forest")
        for move in macro.NONROT_H0:
            target = core.word_after(run.state.p, move.action)
            q, phase = exact.ORBIT_PHASE[target]
            h, hpos = exact.HEX_POSITION[target]
            relevant = move.weight == 3 and q in candidates
            if not relevant and not count_all_legal:
                continue
            transition = exact.extend(run.state, move)
            edge = None if transition is None else macro.MacroEdge(run, transition)
            verdict = None
            after = None
            recognition = None
            kind = None
            if edge is not None:
                kind = pilot.edge_kind(edge)
                verdict, after, recognition = rr.evaluate_edge(
                    state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
                )
                if verdict == "child":
                    legal_successors += 1
            if not relevant:
                continue
            row = candidates[int(q)]
            contact_phases = set(int(x) for x in row["orbit_91_contact_phases"])
            level = "C0"
            reason = "candidate_orbit_reached"
            if int(phase) not in contact_phases:
                level, reason = "C1", "orbit_matches_but_phase_misses_orbit91_contact"
            elif int(h) not in r1_hexagons:
                level, reason = "C2", "orbit_phase_matches_but_target_hex_not_in_current_C_R1"
            elif run.state.orbit_masks[int(q)] != 0:
                level, reason = "C3", "attachment_hex_present_but_candidate_orbit_already_registered"
            elif transition is None:
                level, reason = "C4", "fresh_local_attachment_blocked_by_exact_collision"
            elif kind != "Z3":
                level, reason = "C4", f"fresh_local_attachment_not_Z3:{kind}"
            elif verdict != "child" or after is None:
                level, reason = "C4", f"fresh_local_attachment_rejected:{verdict}"
            else:
                classification = search.classify_component_change(state, dec, edge, edge.state, after)
                if classification["is_first_component_change_candidate"]:
                    level, reason = "C6", "exact_FZ1_or_higher_witness"
                else:
                    level, reason = "C5", "all_local_conditions_hold_but_no_exact_component_change"
            attempts.append({
                "candidate_orbit": int(q),
                "source_orbit": int(exact.ORBIT_PHASE[run.state.p][0]),
                "source_phase": int(exact.ORBIT_PHASE[run.state.p][1]),
                "rotation_length": int(run.ell),
                "joint": move.label,
                "target_phase": int(phase),
                "target_hexagon": int(h),
                "target_hex_rotation_position": int(hpos),
                "level": level,
                "first_failed_condition": reason,
                "collision": transition is None,
                "joint_kind": kind,
                "verdict": verdict,
                "candidate_orbit_fresh": run.state.orbit_masks[int(q)] == 0,
                "candidate_orbit_in_C_R1": int(q) in r1_orbits,
                "target_hex_in_C_R1": int(h) in r1_hexagons,
                "legal_Z3_target": bool(kind == "Z3" and verdict == "child"),
                "hub_touching_candidate": bool(row["touches_hub"]),
            })
    return attempts, legal_successors


def update_attempt_counters(container: dict[str, object], attempts: list[Mapping[str, object]], candidates) -> int:
    best = 0
    for attempt in attempts:
        q = str(attempt["candidate_orbit"])
        level = str(attempt["level"])
        best = max(best, int(level[1:]))
        container["level_counts"][q][level] += 1
        container["failure_reasons"][q][str(attempt["first_failed_condition"])] += 1
        container["candidate_orbit_exposure"][q] += 1
        if attempt["legal_Z3_target"]:
            container["legal_Z3_target_exposure"][q] += 1
        if attempt["hub_touching_candidate"]:
            container["hub_touching_attempts"] += 1
        container["attempts_total"] += 1
    container["state_best_level"][f"C{best}"] += 1
    return best


def empty_counters(candidates) -> dict[str, object]:
    return {
        "states": 0,
        "attempts_total": 0,
        "hub_touching_attempts": 0,
        "candidate_orbit_exposure": Counter(),
        "legal_Z3_target_exposure": Counter(),
        "state_best_level": Counter(),
        "level_counts": {str(q): Counter() for q in candidates},
        "failure_reasons": {str(q): Counter() for q in candidates},
    }


def normalize_counters(value: Mapping[str, object], candidates) -> dict[str, object]:
    return {
        "states": int(value["states"]),
        "attempts_total": int(value["attempts_total"]),
        "hub_touching_attempts": int(value["hub_touching_attempts"]),
        "candidate_orbit_exposure": {str(q): int(value["candidate_orbit_exposure"][str(q)]) for q in candidates},
        "legal_Z3_target_exposure": {str(q): int(value["legal_Z3_target_exposure"][str(q)]) for q in candidates},
        "state_best_level": {level: int(value["state_best_level"][level]) for level in LEVELS},
        "level_counts": {
            str(q): {level: int(value["level_counts"][str(q)][level]) for level in LEVELS}
            for q in candidates
        },
        "failure_reasons": {
            str(q): dict(sorted(value["failure_reasons"][str(q)].items())) for q in candidates
        },
    }


def source_lookup(manifest: Mapping[str, object], seed_id: str) -> dict[str, Mapping[str, object]]:
    return {
        str(row["source_node_id"]): row
        for row in manifest["start_domain"]["records"]
        if row["seed_id"] == seed_id
    }


def ancestry_trace(target_id: str, parents: Mapping[str, str | None], records: Mapping[str, Mapping[str, object]]) -> list[dict[str, object]]:
    ids = []
    cursor: str | None = target_id
    while cursor is not None:
        ids.append(cursor)
        cursor = parents[cursor]
    ids.reverse()
    return [
        {
            "node_id": node_id,
            "parent_id": records[node_id]["parent_id"],
            "incoming_macro_edge": records[node_id]["incoming_macro_edge"],
            "exact_state_hash": records[node_id]["exact_state_hash"],
            "decorated_state_sha256": records[node_id]["decorated_state_sha256"],
            "path_hash": records[node_id]["path_hash"],
            "depth": records[node_id]["depth"],
        }
        for node_id in ids
    ]


def audit_branch(path: Path, manifest: Mapping[str, object], seed_id: str,
                 candidates: Mapping[int, Mapping[str, object]], global_seen_all: set[str],
                 global_seen_expanded: set[str]) -> dict[str, object]:
    frontier_rows = list(iter_top_array(path, "frontier"))
    frontier_ids = {str(row["node_id"]) for row in frontier_rows}
    parents: dict[str, str | None] = {}
    child_counts: Counter[str] = Counter()
    node_count = 0
    for row in iter_top_array(path, "nodes"):
        node_id = str(row["node_id"])
        parent = None if row["parent_id"] is None else str(row["parent_id"])
        parents[node_id] = parent
        if parent is not None:
            child_counts[parent] += 1
        node_count += 1

    roots = source_lookup(manifest, seed_id)
    active: dict[str, tuple[object, object, int, int]] = {}
    literal = empty_counters(candidates)
    unique = empty_counters(candidates)
    max_z3_on_path = 0
    repeated_orbit_example = None
    best_frontier: list[dict[str, object]] = []
    selected_records: dict[str, Mapping[str, object]] = {}
    unique_frontier_first_occurrences = 0

    for row in iter_top_array(path, "nodes"):
        node_id = str(row["node_id"])
        parent_id = None if row["parent_id"] is None else str(row["parent_id"])
        if parent_id is None:
            source = roots[str(row["start_record_id"])]
            state = exact.state_from_json(source["state"])
            dec = rr.Decoration.from_json(source["decoration"])
            seen_orbits = 0
            z3_count = 0
        else:
            if parent_id not in active:
                raise AssertionError(f"active parent missing for {node_id}")
            parent_state, parent_dec, parent_seen, parent_z3 = active[parent_id]
            edge = pilot.edge_from_json(parent_state, row["incoming_macro_edge"])
            verdict, dec, recognition = rr.evaluate_edge(
                parent_state, parent_dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            if verdict != "child" or dec is None or recognition is not None:
                raise AssertionError(f"stored child no longer accepted: {node_id}")
            state = edge.state
            z3_count = parent_z3 + int(pilot.edge_kind(edge) == "Z3")
            seen_orbits = parent_seen
            child_counts[parent_id] -= 1
            if child_counts[parent_id] == 0:
                del active[parent_id]
        current_orbit, current_phase = exact.ORBIT_PHASE[state.p]
        if seen_orbits & (1 << int(current_orbit)) and repeated_orbit_example is None:
            repeated_orbit_example = {
                "later_node_id": node_id,
                "repeated_orbit": int(current_orbit),
                "later_phase": int(current_phase),
                "exact_state_hash": row["exact_state_hash"],
                "component_digest": rr.component_digest(state),
                "note": "same orbit recurs on one exact ancestry; orbit identity alone is not a continuation key",
            }
        seen_orbits |= 1 << int(current_orbit)
        max_z3_on_path = max(max_z3_on_path, z3_count)
        if rr.state_hash(state) != row["exact_state_hash"] or dec.to_json() != row["decoration"]:
            raise AssertionError(f"literal replay mismatch: {node_id}")
        digest = str(row["decorated_state_sha256"])
        if node_id not in frontier_ids:
            attempts, _legal = classify_candidate_attempts(state, dec, candidates)
            literal["states"] += 1
            update_attempt_counters(literal, attempts, candidates)
            global_seen_all.add(digest)
            if digest not in global_seen_expanded:
                global_seen_expanded.add(digest)
                unique["states"] += 1
                update_attempt_counters(unique, attempts, candidates)
        if child_counts[node_id] > 0:
            active[node_id] = (state, dec, seen_orbits, z3_count)

    if active:
        raise AssertionError(f"unconsumed parent states remain for {seed_id}: {len(active)}")

    for stored in frontier_rows:
        state = exact.state_from_json(stored["state"])
        dec = rr.Decoration.from_json(stored["decoration"])
        frontier_digest = search.decorated_digest(state, dec)
        if frontier_digest not in global_seen_all:
            global_seen_all.add(frontier_digest)
            unique_frontier_first_occurrences += 1
        attempts, legal_successors = classify_candidate_attempts(
            state, dec, candidates, count_all_legal=True
        )
        best = max((int(str(row["level"])[1:]) for row in attempts), default=0)
        summary = rr.component_summary(state)
        r1 = search.component(summary, ("q", R1_ORBIT))
        ranked = sorted(
            attempts,
            key=lambda row: (-int(str(row["level"])[1:]), int(row["candidate_orbit"]), int(row["target_phase"])),
        )
        best_frontier.append({
            "node_id": str(stored["node_id"]),
            "exact_state_hash": rr.state_hash(state),
            "decorated_state_sha256": search.decorated_digest(state, dec),
            "path_hash": stored["path_hash"],
            "depth": int(stored["depth"]),
            "relative_depth": int(stored["relative_depth"]),
            "best_level": f"C{best}",
            "legal_successor_count": legal_successors,
            "current_orbit": int(exact.ORBIT_PHASE[state.p][0]),
            "current_phase": int(exact.ORBIT_PHASE[state.p][1]),
            "r1_component": None if r1 is None else {
                "id": r1["id"], "e_orbits": r1["e_orbits"], "hexagons": r1["hexagons"]
            },
            "resources": {name: int(getattr(state, name)) for name in ("P", "O", "F", "H", "Ndef", "D")},
            "nearest_attempts": ranked[:5],
        })
    best_frontier.sort(key=lambda row: (-int(str(row["best_level"])[1:]), row["legal_successor_count"], -row["depth"], row["node_id"]))
    selected_ids = set()
    for row in best_frontier[:3]:
        cursor: str | None = str(row["node_id"])
        while cursor is not None and cursor not in selected_ids:
            selected_ids.add(cursor)
            cursor = parents[cursor]
    if selected_ids:
        for row in iter_top_array(path, "nodes"):
            if str(row["node_id"]) in selected_ids:
                selected_records[str(row["node_id"])] = row
    for row in best_frontier[:3]:
        row["exact_replay_path"] = ancestry_trace(str(row["node_id"]), parents, selected_records)

    return {
        "seed_id": seed_id,
        "checkpoint": {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "bytes": path.stat().st_size},
        "node_count": node_count,
        "expanded_states": node_count - len(frontier_ids),
        "frontier_count": len(frontier_ids),
        "globally_unique_frontier_first_occurrences": unique_frontier_first_occurrences,
        "literal_census": normalize_counters(literal, candidates),
        "globally_unique_first_occurrence_census": normalize_counters(unique, candidates),
        "max_Z3_events_on_one_stage_D_ancestry": max_z3_on_path,
        "same_orbit_revisit_example": repeated_orbit_example,
        "closest_frontier_states": best_frontier[:10],
    }


def aggregate_ledgers(branches: list[Mapping[str, object]], candidates, manifest, result) -> dict[str, object]:
    total = empty_counters(candidates)
    unique = empty_counters(candidates)
    for branch in branches:
        for source_name, target in (("literal_census", total), ("globally_unique_first_occurrence_census", unique)):
            source = branch[source_name]
            target["states"] += int(source["states"])
            target["attempts_total"] += int(source["attempts_total"])
            target["hub_touching_attempts"] += int(source["hub_touching_attempts"])
            for q in candidates:
                qs = str(q)
                target["candidate_orbit_exposure"][qs] += int(source["candidate_orbit_exposure"][qs])
                target["legal_Z3_target_exposure"][qs] += int(source["legal_Z3_target_exposure"][qs])
                for level in LEVELS:
                    target["level_counts"][qs][level] += int(source["level_counts"][qs][level])
                target["failure_reasons"][qs].update(source["failure_reasons"][qs])
            for level in LEVELS:
                target["state_best_level"][level] += int(source["state_best_level"][level])
    rows = []
    normalized = normalize_counters(total, candidates)
    for q in candidates:
        qs = str(q)
        levels = normalized["level_counts"][qs]
        highest = max((int(level[1:]) for level, count in levels.items() if count), default=0)
        rows.append({
            "candidate_orbit": q,
            "attempt_count": normalized["candidate_orbit_exposure"][qs],
            "legal_Z3_target_count": normalized["legal_Z3_target_exposure"][qs],
            "level_counts": levels,
            "highest_reached_level": f"C{highest}",
            "first_failed_condition_histogram": normalized["failure_reasons"][qs],
            "C0_orbit_never_appeared": normalized["candidate_orbit_exposure"][qs] == 0,
        })
    return {
        "schema": SCHEMA,
        "scope": "all six immutable Stage-D parent DAGs; capped seed_3 and seed_6 remain bounded",
        "condition_semantics": {
            "C0": "candidate orbit never occurs as a reachable raw weight-3 target (reported per orbit, not per attempt)",
            "C1": "target orbit is a candidate but the target phase is not an orbit-91-contact phase",
            "C2": "orbit and phase match, but the contact hexagon is not in the current C_R1 component",
            "C3": "the contact hexagon is in C_R1, but the candidate orbit is already registered and cannot be a fresh Z3 opening",
            "C4": "fresh local attachment is blocked by literal collision, non-Z3 flow type, or a Target-A-safe resource predicate",
            "C5": "all local tests pass and the edge is accepted, but exact component provenance does not enlarge C_R1",
            "C6": "an exact accepted first component-changing Z3 witness",
        },
        "literal_parent_DAG_census": normalized,
        "globally_unique_decorated_state_census": normalize_counters(unique, candidates),
        "per_candidate": rows,
        "branches": branches,
        "input_identity": {
            "manifest_sha256": sha256_file(MANIFEST),
            "result_sha256": sha256_file(RESULT),
            "stage": result["stage"],
            "stage_D_expansions": result["aggregate"]["expansions"],
            "stage_D_unique_exact_state_count": 1318577,
            "analyzer_sha256": sha256_file(Path(__file__)),
        },
    }


def r4_crosscheck(candidates: Mapping[int, Mapping[str, object]]) -> dict[str, object]:
    raw = json.loads(R4_INPUT.read_text(encoding="utf-8"))
    rows = []
    for entry in raw["entries"]:
        if entry["global_class"] != "R4":
            continue
        orbit_fields = {}
        for key, value in entry.items():
            if "orbit" in key and isinstance(value, int):
                orbit_fields[key] = value
        matches = sorted({value for value in orbit_fields.values() if value in candidates})
        phase_matches = []
        for q in matches:
            phases = set(int(x) for x in candidates[q]["orbit_91_contact_phases"])
            for key, value in entry.items():
                if "phase" in key and isinstance(value, int) and value in phases:
                    phase_matches.append({"candidate_orbit": q, "field": key, "phase": value})
        rows.append({
            "transition_identity": entry["transition_identity"],
            "mechanism": entry["mechanism"],
            "fixed_component_class": entry["fixed_component_class"],
            "global_class": entry["global_class"],
            "abstract_distance_from_observed_domain": entry["abstract_distance_from_observed_domain"],
            "orbit_fields": orbit_fields,
            "candidate_orbit_matches": matches,
            "candidate_phase_matches": phase_matches,
            "component_condition": entry["required_predecessor_condition"],
            "registration_condition": "not certified in the R4 abstraction",
            "provenance_condition": entry["reason"],
            "interpretation": "R4 is an abstract backward-reachability entry, not an exact Stage-D FZ1 attempt",
        })
    if len(rows) != 22:
        raise AssertionError(f"Round-57 R4 count changed: {len(rows)}")
    return {
        "schema": "rr-short-ell2-r1-37-r4-candidate-crosscheck-v1",
        "r4_entry_count": len(rows),
        "entries_matching_any_of_20_candidates": sum(bool(row["candidate_orbit_matches"]) for row in rows),
        "entries_matching_candidate_phase": sum(bool(row["candidate_phase_matches"]) for row in rows),
        "entries": rows,
        "conclusion": "Round-57 R4 rows live in an abstract backward table; overlap is recorded fieldwise and is not exact reachability evidence.",
        "input_sha256": sha256_file(R4_INPUT),
    }


def bound_audit(branches: list[Mapping[str, object]]) -> dict[str, object]:
    repeats = [row["same_orbit_revisit_example"] for row in branches if row["same_orbit_revisit_example"]]
    maximum = max(int(row["max_Z3_events_on_one_stage_D_ancestry"]) for row in branches)
    return {
        "schema": "rr-short-ell2-r1-37-144z3-bound-audit-v1",
        "claim": "If FZ1 exists, it occurs within 144 Z3 events.",
        "verdict": "NOT_PROVED_BY_ORBIT_PIGEONHOLE",
        "audited_distinctions": {
            "same_orbit_revisit_possible": bool(repeats),
            "same_orbit_different_phase_possible": True,
            "same_orbit_different_component_or_provenance_possible": True,
            "orbit_pigeonhole_implies_exact_continuation_equivalence": False,
        },
        "exact_revisit_examples": repeats[:6],
        "maximum_Z3_events_on_any_replayed_Stage_D_ancestry": maximum,
        "counterexample_scope": "the examples refute the continuation-equivalence premise, not the numerical implication itself",
        "proof_gap": "an orbit repetition does not repeat hex masks, orbit phase masks, component partition, resource coordinates, or R1 provenance; no pumping/deletion lemma identifies the two continuations",
        "conclusion": "The proposed 144-event bound remains an unsupported conjecture and cannot justify exhaustion or pruning.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    candidate_payload, candidates = build_candidate_table()
    global_seen_all: set[str] = set()
    global_seen_expanded: set[str] = set()
    branches = []
    result_by_seed = {str(row["seed_id"]): row for row in result["branches"]}
    for seed_id in search.SOURCE_IDS:
        result_row = result_by_seed[seed_id]
        path = ROOT / result_row["checkpoint"]["path"]
        if sha256_file(path) != result_row["checkpoint"]["sha256"]:
            raise AssertionError(f"immutable checkpoint SHA mismatch: {seed_id}")
        branch = audit_branch(
            path, manifest, seed_id, candidates, global_seen_all, global_seen_expanded
        )
        branches.append(branch)
        print(json.dumps({
            "seed_id": seed_id,
            "expanded": branch["expanded_states"],
            "frontier": branch["frontier_count"],
            "candidate_attempts": branch["literal_census"]["attempts_total"],
        }, sort_keys=True), flush=True)
    ledger = aggregate_ledgers(branches, candidates, manifest, result)
    if len(global_seen_all) != 1318577:
        raise AssertionError(f"global unique exact/decorated corpus mismatch: {len(global_seen_all)} != 1318577")
    seed_rows = [row for row in branches if row["seed_id"] in {"short_ell2_r1_37:3", "short_ell2_r1_37:6"}]
    seed_payload = {
        "schema": "rr-short-ell2-r1-37-seed3-seed6-candidate-census-v1",
        "scope": "read-only Stage-D endpoints and parent DAGs",
        "branches": seed_rows,
        "same_bottleneck": None,
    }
    if len(seed_rows) != 2:
        raise AssertionError("seed_3/seed_6 split absent")
    seed_payload["same_bottleneck"] = (
        seed_rows[0]["literal_census"]["state_best_level"] == seed_rows[1]["literal_census"]["state_best_level"]
        and seed_rows[0]["literal_census"]["legal_Z3_target_exposure"] == seed_rows[1]["literal_census"]["legal_Z3_target_exposure"]
    )
    cross = r4_crosscheck(candidates)
    bound = bound_audit(branches)
    if args.write:
        write_json(CANDIDATES_OUT, candidate_payload)
        write_json(LEDGER_OUT, ledger)
        write_json(SEEDS_OUT, seed_payload)
        write_json(R4_OUT, cross)
        write_json(BOUND_OUT, bound)
    else:
        print(json.dumps({
            "candidate_count": candidate_payload["candidate_count"],
            "hub_candidates": candidate_payload["hub_touching_candidate_orbits"],
            "attempts": ledger["literal_parent_DAG_census"]["attempts_total"],
            "r4": cross["r4_entry_count"],
            "bound": bound["verdict"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
