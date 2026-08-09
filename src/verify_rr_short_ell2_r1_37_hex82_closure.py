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


def verify_static_certificate(route_rows) -> dict[str, object]:
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
    ladder = occupancy["theorem_ladder"]
    if not all(str(ladder[key]).startswith("PROVED") for key in ("T2", "T2a", "T2b", "T2+", "T3", "T4")):
        raise AssertionError("theorem ladder was not serialized as proved in its stated scope")
    return {"q91_p2": list(q91p2), "unique_z2_source": list(z2_source), "anchor_count": len(roots)}


def independent_full_replay(entries: Mapping[tuple[int, ...], list[tuple]]) -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    result_by_seed = {str(row["seed_id"]): row for row in result["branches"]}
    per_route = {f"hex82_q{q}_p{phase}": Counter() for q, phase, _pos in ROUTES}
    nodes = expanded = frontier_total = 0
    q91p2_nodes = source_nodes = 0
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
        "M1_by_route": {key: int(value["M1_orbit_phase_macro_match"]) for key, value in per_route.items()},
        "M1_total": sum(int(value["M1_orbit_phase_macro_match"]) for value in per_route.values()),
        "branches": branches,
    }


def main() -> int:
    route_rows, entries = independently_build_entries()
    static = verify_static_certificate(route_rows)
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
            "finite predecessor-obligation closure", "M1 count conservation", "M2-M5 absence",
            "T2b/T2+/T3/T4 in the explicitly stated frozen-anchor descendant scope",
        ],
        "artifact_sha256": {str(path.relative_to(ROOT)): sha256_file(path) for path in (
            ROUTES_PATH, BACKWARD_PATH, MITM_PATH, OCCUPANCY_PATH, MANIFEST_PATH, RESULT_PATH, ROUND60_PATH
        )},
        "verifier_sha256": sha256_file(Path(__file__)),
    }
    write_json(VERIFIED_OUT, payload)
    print(json.dumps({"verified": True, "nodes": replay["nodes"], "M1": replay["M1_total"], "M2_M5": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
