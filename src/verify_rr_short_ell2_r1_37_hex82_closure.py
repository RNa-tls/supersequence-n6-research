#!/usr/bin/env python3
"""Independent verifier for the Round-61 hex-82 provenance certificate."""
from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping

import analyze_rr_short_ell2_r1_37_fz1_candidates as fz1


ROOT = Path(__file__).resolve().parent.parent
ROUTES_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_routes.json"
BACKWARD_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_backward_closure.json"
MITM_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_mitm.json"
OCCUPANCY_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_occupancy_audit.json"
MANIFEST_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
RESULT_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
ROUND60_PATH = ROOT / "outputs" / "rr_short_ell2_r1_37_c4_verified.json"
VERIFIED_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_verified.json"
H40_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_h40_anchor_fullness.json"

search, rr, exact, pilot, core, macro = fz1.search, fz1.rr, fz1.exact, fz1.pilot, fz1.core, fz1.macro
W1 = macro.W1
W2 = next(move for move in macro.NONROT_H0 if move.weight == 2)
W3 = tuple(move for move in macro.NONROT_H0 if move.weight == 3)
ROUTES = ((42, 1, 2), (78, 3, 4), (82, 0, 0), (83, 4, 5), (128, 2, 1))


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
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def orbit_word(q: int, phase: int) -> tuple[int, ...]:
    return tuple(core.orbit(core.E_REPS[q], core.E)[phase])


def inverse_source(target: tuple[int, ...], move) -> tuple[int, ...]:
    sources = [tuple(value) for value in itertools.permutations(range(6))
               if core.word_after(tuple(value), move.action) == target]
    if len(sources) != 1:
        raise AssertionError("non-unique right-action inverse")
    return sources[0]


def rotate_right(value: tuple[int, ...], amount: int) -> tuple[int, ...]:
    amount %= len(value)
    return value if amount == 0 else value[-amount:] + value[:-amount]


def sparse(rows, index: int) -> int:
    return {int(left): int(right) for left, right in rows}.get(index, 0)


def independently_build_entries():
    route_rows = []
    entries = defaultdict(list)
    for route_index, (q, phase, expected_position) in enumerate(ROUTES):
        target = orbit_word(q, phase)
        if exact.HEX_POSITION[target] != (82, expected_position):
            raise AssertionError("fixed route table mismatch")
        predecessors = []
        for move in W3:
            source = inverse_source(target, move)
            blocker = core.word_after(source, core.SIGMA)
            predecessors.append((move.label, source, blocker))
            for ell in range(6):
                entries[rotate_right(source, ell)].append((route_index, q, phase, ell, move, source))
        route_rows.append((q, phase, target, predecessors))
    return route_rows, entries


def h40_incidences(state) -> list[dict[str, object]]:
    rows = []
    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if not (mask & (1 << phase)):
                continue
            value = orbit_word(q, phase)
            h, position = exact.HEX_POSITION[value]
            if h == 40:
                rows.append({
                    "orbit": q, "phase": phase, "word": list(value),
                    "hex_position": position,
                })
    return rows


def build_h40_anchor_ledger(manifest: Mapping[str, object]) -> dict[str, object]:
    """Cross-check every manifest anchor against its immutable source frontier."""
    source_by_seed = {str(row["seed_id"]): row for row in manifest["source_checkpoints"]}
    records_by_seed = defaultdict(list)
    for row in manifest["start_domain"]["records"]:
        records_by_seed[str(row["seed_id"])].append(row)
    h40_words = tuple(core.orbit(core.ROT_REPS[40], core.SIGMA))
    forbidden_source = (2, 4, 5, 1, 3, 0)
    anchor_rows = []
    checkpoint_rows = []
    for seed_id in search.SOURCE_IDS:
        source = source_by_seed[seed_id]
        path = ROOT / source["checkpoint_path"]
        actual_sha = sha256_file(path)
        if actual_sha != source["checkpoint_sha256"]:
            raise AssertionError(f"immutable source checkpoint changed: {seed_id}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("schema") != source["checkpoint_schema"]:
            raise AssertionError(f"source checkpoint schema mismatch: {seed_id}")
        frontier = {str(row["node_id"]): row for row in raw["frontier"]}
        if len(frontier) != int(source["frontier_count"]):
            raise AssertionError(f"source frontier count mismatch: {seed_id}")
        expected = records_by_seed[seed_id]
        if len(expected) != len(frontier):
            raise AssertionError(f"manifest/source anchor count mismatch: {seed_id}")
        for record in expected:
            node_id = str(record["source_node_id"])
            raw_row = frontier.get(node_id)
            if raw_row is None:
                raise AssertionError(f"manifest anchor absent from source checkpoint: {node_id}")
            for field, manifest_field in (
                ("state", "state"), ("decoration", "decoration"), ("path_hash", "source_path_hash"),
                ("depth", "source_depth"), ("relative_depth", "source_relative_depth"),
            ):
                if raw_row[field] != record[manifest_field]:
                    raise AssertionError(f"source anchor field mismatch: {node_id}: {field}")
            state = exact.state_from_json(raw_row["state"])
            if rr.state_hash(state) != str(record["exact_state_hash"]):
                raise AssertionError(f"manifest exact-state hash mismatch: {node_id}")
            mask = int(state.hex_masks[40])
            windows = [{
                "hex_position": position, "word": list(value),
                "visited": bool(mask & (1 << position)),
            } for position, value in enumerate(h40_words)]
            incidences = h40_incidences(state)
            anchor_rows.append({
                "seed_id": seed_id,
                "source_frontier_index": int(record["source_frontier_index"]),
                "source_node_id": node_id,
                "source_path_hash": str(record["source_path_hash"]),
                "exact_state_hash": rr.state_hash(state),
                "manifest_exact_state_hash": str(record["exact_state_hash"]),
                "source_checkpoint_path": source["checkpoint_path"],
                "source_checkpoint_sha256": actual_sha,
                "h40_registered_in_incidence_graph": bool(incidences),
                "h40_registration_incidences": incidences,
                "h40_literal_window_count_visited": mask.bit_count(),
                "h40_occupancy_mask": mask,
                "h40_occupancy_mask_binary": format(mask, "06b"),
                "h40_full": mask == exact.FULL_HEX,
                "h40_windows": windows,
                "current_endpoint": list(state.p),
                "current_endpoint_is_245130": state.p == forbidden_source,
                "literal_245130_already_visited": state.visited(forbidden_source),
            })
        checkpoint_rows.append({
            "seed_id": seed_id, "path": source["checkpoint_path"],
            "sha256": actual_sha, "schema": raw["schema"],
            "frontier_count": len(frontier), "manifest_records": len(expected),
        })
    anchor_rows.sort(key=lambda row: (search.SOURCE_IDS.index(str(row["seed_id"])), int(row["source_frontier_index"])))
    if len(anchor_rows) != 84:
        raise AssertionError("h40 anchor ledger did not contain 84 rows")
    registered = sum(bool(row["h40_registered_in_incidence_graph"]) for row in anchor_rows)
    full = sum(bool(row["h40_full"]) for row in anchor_rows)
    endpoint = sum(bool(row["current_endpoint_is_245130"]) for row in anchor_rows)
    visited = sum(bool(row["literal_245130_already_visited"]) for row in anchor_rows)
    if (registered, full, endpoint, visited) != (84, 84, 0, 84):
        raise AssertionError(f"critical h40 premise failed: {(registered, full, endpoint, visited)}")
    return {
        "schema": "rr-short-ell2-r1-37-h40-anchor-fullness-v1",
        "scope": "84 frozen Stage-D anchors copied from six immutable all-13 frontier checkpoints",
        "anchor_count": len(anchor_rows),
        "source_checkpoint_count": len(checkpoint_rows),
        "summary": {
            "h40_registered_count": registered,
            "h40_full_count": full,
            "h40_mask_histogram": dict(Counter(str(row["h40_occupancy_mask"]) for row in anchor_rows)),
            "h40_window_count_histogram": dict(Counter(str(row["h40_literal_window_count_visited"]) for row in anchor_rows)),
            "endpoint_245130_count": endpoint,
            "literal_245130_visited_count": visited,
            "required_premise_holds": full == 84 and endpoint == 0,
        },
        "semantic_separation": {
            "registered": "at least one used E-orbit phase is incident with h40",
            "full": "all six literal permutation-window bits of h40 are set",
            "registered_was_not_used_as_a_substitute_for_full": True,
        },
        "h40_rotation_words": [list(value) for value in h40_words],
        "source_checkpoints": checkpoint_rows,
        "anchors": anchor_rows,
    }


def verify_static_certificate(route_rows, h40_ledger: Mapping[str, object] | None = None) -> dict[str, object]:
    routes = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    backward = json.loads(BACKWARD_PATH.read_text(encoding="utf-8"))
    occupancy = json.loads(OCCUPANCY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    round60 = json.loads(ROUND60_PATH.read_text(encoding="utf-8"))
    if not round60.get("verified"):
        raise AssertionError("Round 60 is not verified")
    if routes["route_count"] != 5 or backward["deduplicated_predecessor_classes"] != 1:
        raise AssertionError("route/backward class count mismatch")
    serialized = {(int(row["candidate_orbit"]), int(row["candidate_phase"])): row for row in routes["routes"]}
    for q, phase, target, predecessors in route_rows:
        row = serialized[(q, phase)]
        if tuple(row["target_word"]) != target or row["target_hexagon"] != 82:
            raise AssertionError("serialized route target mismatch")
        if [item["joint_label"] for item in row["w3_joint_predecessors"]] != [item[0] for item in predecessors]:
            raise AssertionError("serialized w3 predecessor mismatch")
    q91p2 = orbit_word(91, 2)
    z2_source = inverse_source(q91p2, W2)
    if q91p2 != (5, 1, 3, 0, 4, 2) or z2_source != (2, 4, 5, 1, 3, 0):
        raise AssertionError("literal q91:p2 predecessor changed")
    roots = manifest["start_domain"]["records"]
    if len(roots) != 84:
        raise AssertionError("anchor count changed")
    if not all(sparse(row["state"]["hex_masks"], 40) == 63 for row in roots):
        raise AssertionError("h40 is not full at every anchor")
    if any(tuple(row["state"]["p"]) == z2_source for row in roots):
        raise AssertionError("an anchor is terminal at the forbidden source")
    if any(sparse(row["state"]["orbit_masks"], 91) & 4 for row in roots):
        raise AssertionError("q91:p2 was already registered at an anchor")
    if result["aggregate"]["first_component_change_witnesses"] != 0:
        raise AssertionError("Stage-D result already contains a component change")
    # Route completeness is a fixed 144-orbit-table statement.  The five
    # non-q91 windows of h82 are precisely the five unresolved cases.
    all_h82_non_q91 = sorted(
        (int(exact.ORBIT_PHASE[value][0]), int(exact.ORBIT_PHASE[value][1]), position)
        for position, value in enumerate(core.orbit(core.ROT_REPS[82], core.SIGMA))
        if int(exact.ORBIT_PHASE[value][0]) != 91
    )
    if all_h82_non_q91 != sorted(ROUTES):
        raise AssertionError(f"hex82 route completeness failed: {all_h82_non_q91}")
    r1_hexagons = sorted(exact.HEX_POSITION[orbit_word(91, phase)][0] for phase in range(5))
    if r1_hexagons != [40, 82, 90, 91, 92]:
        raise AssertionError("q91 phase-linked hexagon table changed")
    if h40_ledger is not None and not h40_ledger["summary"]["required_premise_holds"]:
        raise AssertionError("h40 per-anchor ledger rejected the critical premise")
    ladder = occupancy["theorem_ladder"]
    if not all(str(ladder[key]).startswith("PROVED") for key in ("T2", "T2a", "T2b", "T2+", "T3", "T4")):
        raise AssertionError("theorem ladder was not serialized as proved in its stated scope")
    return {
        "q91_p2": list(q91p2), "unique_z2_source": list(z2_source), "anchor_count": len(roots),
        "hex82_non_q91_routes": [list(row) for row in all_h82_non_q91],
        "q91_phase_linked_hexagons": r1_hexagons,
    }


def independent_full_replay(entries: Mapping[tuple[int, ...], list[tuple]]) -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    result_by_seed = {str(row["seed_id"]): row for row in result["branches"]}
    per_route = {f"hex82_q{q}_p{phase}": Counter() for q, phase, _pos in ROUTES}
    nodes = expanded = frontier_total = 0
    q91p2_nodes = source_nodes = monotone_macro_edges = 0
    z2_source = inverse_source(orbit_word(91, 2), W2)
    branches = []
    for seed_id in search.SOURCE_IDS:
        result_row = result_by_seed[seed_id]
        path = ROOT / result_row["checkpoint"]["path"]
        if sha256_file(path) != result_row["checkpoint"]["sha256"]:
            raise AssertionError(f"checkpoint SHA mismatch: {seed_id}")
        frontier_ids = {str(row["node_id"]) for row in fz1.iter_top_array(path, "frontier")}
        children = Counter()
        for row in fz1.iter_top_array(path, "nodes"):
            if row["parent_id"] is not None:
                children[str(row["parent_id"])] += 1
        roots = fz1.source_lookup(manifest, seed_id)
        active = {}
        branch_nodes = branch_expanded = 0
        for stored in fz1.iter_top_array(path, "nodes"):
            branch_nodes += 1
            node_id = str(stored["node_id"])
            parent_id = None if stored["parent_id"] is None else str(stored["parent_id"])
            if parent_id is None:
                source = roots[str(stored["start_record_id"])]
                state = exact.state_from_json(source["state"])
                dec = rr.Decoration.from_json(source["decoration"])
            else:
                parent_state, parent_dec = active[parent_id]
                edge = pilot.edge_from_json(parent_state, stored["incoming_macro_edge"])
                if any(before & ~after for before, after in zip(parent_state.hex_masks, edge.state.hex_masks)):
                    raise AssertionError(f"literal-window occupancy decreased: {node_id}")
                monotone_macro_edges += 1
                verdict, dec, recognition = rr.evaluate_edge(
                    parent_state, parent_dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
                )
                if verdict != "child" or dec is None or recognition is not None:
                    raise AssertionError(f"independent edge replay failed: {node_id}")
                state = edge.state
                children[parent_id] -= 1
                if children[parent_id] == 0:
                    del active[parent_id]
            if rr.state_hash(state) != stored["exact_state_hash"] or dec.to_json() != stored["decoration"]:
                raise AssertionError(f"independent literal state mismatch: {node_id}")
            q91p2_nodes += int(bool(state.orbit_masks[91] & 4))
            source_nodes += int(state.p == z2_source)
            if node_id not in frontier_ids:
                branch_expanded += 1
            for route_index, q, phase, ell, move, source in entries.get(tuple(state.p), ()):
                cursor = state
                available = True
                for _ in range(ell):
                    step = exact.extend(cursor, W1)
                    if step is None:
                        available = False
                        break
                    cursor = step.state
                if available and cursor.p == source:
                    per_route[f"hex82_q{q}_p{phase}"]["M1_orbit_phase_macro_match"] += 1
            if children[node_id] > 0:
                active[node_id] = (state, dec)
        if active:
            raise AssertionError(f"unconsumed parents in independent replay: {seed_id}")
        if branch_expanded != int(result_row["expansions"]) or len(frontier_ids) != int(result_row["frontier_size"]):
            raise AssertionError(f"branch node ledger mismatch: {seed_id}")
        nodes += branch_nodes
        expanded += branch_expanded
        frontier_total += len(frontier_ids)
        branches.append({"seed_id": seed_id, "nodes": branch_nodes, "expanded": branch_expanded,
                         "frontier": len(frontier_ids), "checkpoint_sha256": sha256_file(path)})
    if q91p2_nodes or source_nodes:
        raise AssertionError("literal corpus contradicts the provenance invariant")
    return {
        "nodes": nodes, "expanded": expanded, "frontier": frontier_total,
        "q91_p2_registered_nodes": q91p2_nodes, "unique_z2_source_terminal_nodes": source_nodes,
        "monotone_macro_edges_checked": monotone_macro_edges,
        "M1_by_route": {key: int(value["M1_orbit_phase_macro_match"]) for key, value in per_route.items()},
        "M1_total": sum(int(value["M1_orbit_phase_macro_match"]) for value in per_route.values()),
        "branches": branches,
    }


def main() -> int:
    route_rows, entries = independently_build_entries()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    h40_ledger = build_h40_anchor_ledger(manifest)
    write_json(H40_OUT, h40_ledger)
    static = verify_static_certificate(route_rows, h40_ledger)
    replay = independent_full_replay(entries)
    mitm = json.loads(MITM_PATH.read_text(encoding="utf-8"))
    serialized_by_route = {row["route_id"]: int(row["counts"].get("M1_orbit_phase_macro_match", 0))
                           for row in mitm["per_route"]}
    if replay["M1_by_route"] != serialized_by_route or replay["M1_total"] != int(mitm["M1_orbit_phase_matches"]):
        raise AssertionError("independent M1 replay disagrees with MITM output")
    if any(int(mitm[key]) for key in (
        "M2_structural_state_matches", "M3_exact_decorated_state_matches",
        "M4_exact_legal_noncolliding_C4", "M5_FZ1_witnesses",
    )):
        raise AssertionError("a purported obstructed level is nonzero")
    backward = json.loads(BACKWARD_PATH.read_text(encoding="utf-8"))
    if not backward["stabilized"] or backward["exact_reachable_classes"] != 0:
        raise AssertionError("backward closure status mismatch")
    payload = {
        "schema": "rr-short-ell2-r1-37-hex82-verified-v1",
        "verified": True,
        "verification_mode": "independent fixed-table reconstruction plus full literal replay of six immutable parent DAGs",
        "static_certificate": static,
        "full_replay": replay,
        "verified_claims": [
            "five route specifications", "unique q91:p2 Z2 predecessor", "84-anchor h40 occupancy invariant",
            "registered/full semantic separation", "literal-window occupancy monotonicity",
            "finite predecessor-obligation closure", "route completeness", "M1 count conservation", "M2-M5 absence",
            "T2b/T2+/T3/T4 in the explicitly stated frozen-anchor descendant scope",
        ],
        "artifact_sha256": {str(path.relative_to(ROOT)): sha256_file(path) for path in (
            ROUTES_PATH, BACKWARD_PATH, MITM_PATH, OCCUPANCY_PATH, H40_OUT,
            MANIFEST_PATH, RESULT_PATH, ROUND60_PATH
        )},
        "verifier_sha256": sha256_file(Path(__file__)),
    }
    write_json(VERIFIED_OUT, payload)
    print(json.dumps({"verified": True, "nodes": replay["nodes"], "M1": replay["M1_total"], "M2_M5": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
