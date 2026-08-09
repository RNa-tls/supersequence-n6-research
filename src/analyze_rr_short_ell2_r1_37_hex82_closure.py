#!/usr/bin/env python3
"""Round 61: exact hex-82 five-route provenance closure.

This audit is deliberately read-only.  It replays the six immutable Stage-D
parent DAGs, but it does not continue their frontiers.  The finite backward
certificate uses a literal predecessor obligation: before the first
component-changing Z3, hexagon 82 can enter the R1-target component only via
the q91:p2 incidence.  Its unique weight-two predecessor is a window in the
already-full hexagon 40, and that window is not the terminal window of any of
the 84 frozen anchors.  Exact no-repeat semantics therefore make the
predecessor unreachable in every descendant.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping

import analyze_rr_short_ell2_r1_37_fz1_candidates as fz1


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
CANDIDATES = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_orbits.json"
ROUND60 = ROOT / "outputs" / "rr_short_ell2_r1_37_c4_verified.json"

ROUTES_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_routes.json"
BACKWARD_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_backward_closure.json"
MITM_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_mitm.json"
OCCUPANCY_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_hex82_occupancy_audit.json"

search, rr, exact, pilot, core, macro = fz1.search, fz1.rr, fz1.exact, fz1.pilot, fz1.core, fz1.macro
R1_ORBIT = 91
HEX82 = 82
W1 = macro.W1
W2 = next(move for move in macro.NONROT_H0 if move.weight == 2)
W3 = tuple(move for move in macro.NONROT_H0 if move.weight == 3)
ROUTE_COORDS = ((42, 1), (78, 3), (82, 0), (83, 4), (128, 2))


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


def word(q: int, phase: int) -> tuple[int, ...]:
    return tuple(core.orbit(core.E_REPS[q], core.E)[phase])


def word_string(value: Iterable[int]) -> str:
    return "".join(str(int(item)) for item in value)


def unique_source(target: tuple[int, ...], move) -> tuple[int, ...]:
    rows = [
        tuple(source) for source in itertools.permutations(range(exact.N))
        if core.word_after(tuple(source), move.action) == target
    ]
    if len(rows) != 1:
        raise AssertionError("right action did not have a unique inverse")
    return rows[0]


def rotate_right(value: tuple[int, ...], amount: int) -> tuple[int, ...]:
    amount %= len(value)
    if amount == 0:
        return value
    return value[-amount:] + value[:-amount]


def sparse_value(rows: Iterable[Iterable[int]], index: int) -> int:
    return dict((int(left), int(right)) for left, right in rows).get(index, 0)


def route_specifications() -> tuple[list[dict[str, object]], dict[tuple[int, ...], list[dict[str, object]]]]:
    raw_candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    by_q = {int(row["orbit_id"]): row for row in raw_candidates["candidate_orbits"]}
    routes: list[dict[str, object]] = []
    entry_map: dict[tuple[int, ...], list[dict[str, object]]] = defaultdict(list)
    for route_index, (q, phase) in enumerate(ROUTE_COORDS):
        target = word(q, phase)
        h, hpos = exact.HEX_POSITION[target]
        if (h, hpos) != (HEX82, {42: 2, 78: 4, 82: 0, 83: 5, 128: 1}[q]):
            raise AssertionError("hex-82 route coordinate changed")
        predecessor_rows = []
        for move in W3:
            source = unique_source(target, move)
            blocker = core.word_after(source, core.SIGMA)
            row = {
                "joint_label": move.label,
                "joint_source_word": list(source),
                "joint_source_hex_position": list(exact.HEX_POSITION[source]),
                "joint_source_orbit_phase": list(exact.ORBIT_PHASE[source]),
                "blocked_rotation_successor": list(blocker),
                "blocked_rotation_successor_hex_position": list(exact.HEX_POSITION[blocker]),
                "macro_entry_words_by_rotation_length": {
                    str(ell): list(rotate_right(source, ell)) for ell in range(exact.N)
                },
            }
            predecessor_rows.append(row)
            for ell in range(exact.N):
                entry = rotate_right(source, ell)
                entry_map[entry].append({
                    "route_index": route_index, "candidate_orbit": q, "candidate_phase": phase,
                    "target": target, "move": move, "source": source, "blocker": blocker,
                    "rotation_length": ell,
                })
        candidate = by_q[q]
        route = {
            "route_id": f"hex82_q{q}_p{phase}",
            "candidate_orbit": q,
            "candidate_phase": phase,
            "target_word": list(target),
            "source_hexagon": "macro-entry dependent; exact joint sources listed below",
            "target_hexagon": h,
            "target_hex_position": hpos,
            "required_C_R1_relation": "hexagon 82 is in the incidence component containing q91",
            "required_registration_state": f"B_q{q}=0 before the joint (fresh candidate orbit)",
            "required_first_touch_status": "target permutation window is unvisited",
            "required_resource_state": "F=1, H=0, r_count=1; the w3 joint is blocked, not an abandonment",
            "exact_macro_kind": "Z3",
            "exact_incidence_edge_introduced": {"e_orbit": q, "hexagon": HEX82, "phase": phase},
            "other_q91_contact_hexagons": [
                int(value) for value in candidate["orbit_91_contact_hexagons"] if int(value) != HEX82
            ],
            "w3_joint_predecessors": predecessor_rows,
            "left_s6_or_continuation_equivalence_used": False,
        }
        route["route_spec_sha256"] = sha256_json(route)
        routes.append(route)
    return routes, entry_map


def registration_obligation(manifest: Mapping[str, object]) -> dict[str, object]:
    target = word(R1_ORBIT, 2)
    source = unique_source(target, W2)
    blocker = core.word_after(source, core.SIGMA)
    if exact.HEX_POSITION[target] != (HEX82, 3):
        raise AssertionError("q91:p2 no longer represents the h82 incidence")
    if exact.HEX_POSITION[source][0] != 40:
        raise AssertionError("unique Z2 source left full hexagon 40")
    roots = list(manifest["start_domain"]["records"])
    hist = Counter(str(sparse_value(row["state"]["hex_masks"], HEX82)) for row in roots)
    route_root_occupancy = {}
    for q, phase in ROUTE_COORDS:
        _h, pos = exact.HEX_POSITION[word(q, phase)]
        route_root_occupancy[f"q{q}:p{phase}"] = sum(
            bool(sparse_value(row["state"]["hex_masks"], HEX82) & (1 << pos)) for row in roots
        )
    return {
        "obligation_id": "register_q91_p2_to_attach_h82_to_C_R1",
        "target_orbit": R1_ORBIT,
        "target_phase": 2,
        "target_word": list(target),
        "target_hex_position": list(exact.HEX_POSITION[target]),
        "only_allowed_pre_R2_kind": "Z2",
        "unique_w2_source_word": list(source),
        "unique_w2_source_hex_position": list(exact.HEX_POSITION[source]),
        "blocked_rotation_successor": list(blocker),
        "blocked_rotation_successor_orbit_phase": list(exact.ORBIT_PHASE[blocker]),
        "all_84_roots_hex40_full": all(sparse_value(row["state"]["hex_masks"], 40) == exact.FULL_HEX for row in roots),
        "roots_terminal_at_unique_source": sum(tuple(row["state"]["p"]) == source for row in roots),
        "roots_with_q91_p2_registered": sum(bool(sparse_value(row["state"]["orbit_masks"], R1_ORBIT) & (1 << 2)) for row in roots),
        "root_hex82_mask_histogram": dict(sorted(hist.items(), key=lambda item: int(item[0]))),
        "route_target_already_occupied_at_root_count": route_root_occupancy,
        "provenance_argument": [
            "h40 is full at every frozen anchor, so the unique Z2 source window 245130 is already visited",
            "no frozen anchor is terminal at 245130",
            "exact.extend never enters an already-visited target window, hence no descendant can become terminal at 245130",
            "therefore the q91:p2 incidence q91--h82 cannot be introduced by a pre-R2 Z2",
            "a blocked w3 into existing q91 would be R2 and is recognized but never traversed",
        ],
        "classification": "H2_PREDECESSOR_LOCALLY_LEGAL_BUT_ANCHORED_PROVENANCE_INCOMPATIBLE",
    }


def replay_edge(parent_state, parent_dec, stored: Mapping[str, object]):
    edge = pilot.edge_from_json(parent_state, stored["incoming_macro_edge"])
    verdict, dec, recognition = rr.evaluate_edge(
        parent_state, parent_dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
    )
    if verdict != "child" or dec is None or recognition is not None:
        raise AssertionError(f"stored edge replay failed: {stored['node_id']}")
    return edge.state, dec


def traces_for_nodes(path: Path, roots: Mapping[str, Mapping[str, object]],
                     target_ids: Iterable[str], parents: Mapping[str, str | None],
                     starts: Mapping[str, str | None]) -> dict[str, dict[str, object]]:
    """Extract several ancestry traces with one additional checkpoint pass."""
    chains: dict[str, list[str]] = {}
    wanted = set()
    for target_id in target_ids:
        chain = []
        cursor: str | None = target_id
        while cursor is not None:
            chain.append(cursor)
            cursor = parents[cursor]
        chain.reverse()
        chains[target_id] = chain
        wanted.update(chain[1:])
    edges: dict[str, Mapping[str, object] | None] = {}
    print(json.dumps({"phase": "ancestry_edges", "path": str(path)}, sort_keys=True), flush=True)
    for row in fz1.iter_top_array(path, "nodes"):
        node_id = str(row["node_id"])
        if node_id in wanted:
            edges[node_id] = row["incoming_macro_edge"]
    if set(edges) != wanted:
        raise AssertionError("one or more ancestry edges were absent")
    result = {}
    for target_id, chain in chains.items():
        root_id = chain[0]
        start = roots[str(starts[root_id])]
        result[target_id] = {
            "start_record_id": starts[root_id],
            "anchor_state_hash": start["exact_state_hash"],
            "anchor_path_hash": start["source_path_hash"],
            "node_ids": chain,
            "accepted_macro_edges": [edges[node] for node in chain[1:]],
            "replay_edge_count": len(chain) - 1,
        }
    return result


def audit_branch(path: Path, manifest: Mapping[str, object], seed_id: str,
                 routes: list[Mapping[str, object]], entry_map: Mapping[tuple[int, ...], list[Mapping[str, object]]],
                 unique_z2_source: tuple[int, ...]) -> dict[str, object]:
    print(json.dumps({"seed_id": seed_id, "phase": "frontier_index"}, sort_keys=True), flush=True)
    frontier_ids = {str(row["node_id"]) for row in fz1.iter_top_array(path, "frontier")}
    child_counts: Counter[str] = Counter()
    parents: dict[str, str | None] = {}
    starts: dict[str, str | None] = {}
    print(json.dumps({"seed_id": seed_id, "phase": "parent_index"}, sort_keys=True), flush=True)
    indexed = 0
    for row in fz1.iter_top_array(path, "nodes"):
        indexed += 1
        if indexed % 50_000 == 0:
            print(json.dumps({"seed_id": seed_id, "phase": "parent_index", "nodes": indexed}, sort_keys=True), flush=True)
        node_id = str(row["node_id"])
        parent = row["parent_id"]
        parents[node_id] = None if parent is None else str(parent)
        starts[node_id] = None if row["start_record_id"] is None else str(row["start_record_id"])
        if parent is not None:
            child_counts[str(parent)] += 1
    roots = fz1.source_lookup(manifest, seed_id)
    active = {}
    route_counts = {str(route["route_id"]): Counter() for route in routes}
    nearest: dict[str, dict[str, object]] = {}
    invariant = Counter()
    node_count = 0
    expanded_count = 0
    print(json.dumps({"seed_id": seed_id, "phase": "literal_replay"}, sort_keys=True), flush=True)
    for stored in fz1.iter_top_array(path, "nodes"):
        node_count += 1
        if node_count % 50_000 == 0:
            print(json.dumps({"seed_id": seed_id, "phase": "literal_replay", "nodes": node_count}, sort_keys=True), flush=True)
        node_id = str(stored["node_id"])
        parent_id = None if stored["parent_id"] is None else str(stored["parent_id"])
        if parent_id is None:
            source = roots[str(stored["start_record_id"])]
            state = exact.state_from_json(source["state"])
            dec = rr.Decoration.from_json(source["decoration"])
        else:
            if parent_id not in active:
                raise AssertionError(f"active parent missing: {node_id}")
            parent_state, parent_dec = active[parent_id]
            state, dec = replay_edge(parent_state, parent_dec, stored)
            child_counts[parent_id] -= 1
            if child_counts[parent_id] == 0:
                del active[parent_id]
        if rr.state_hash(state) != stored["exact_state_hash"] or dec.to_json() != stored["decoration"]:
            raise AssertionError(f"literal state mismatch: {node_id}")
        if state.orbit_masks[R1_ORBIT] & (1 << 2):
            invariant["q91_p2_registered_nodes"] += 1
        if state.p == unique_z2_source:
            invariant["unique_z2_source_terminal_nodes"] += 1
        # The exact component query is intentionally performed for every node;
        # it independently checks the hand invariant rather than inferring it
        # solely from q91's mask.
        summary = rr.component_summary(state)
        r1 = search.component(summary, ("q", R1_ORBIT))
        h82 = search.component(summary, ("h", HEX82))
        h82_in_r1 = r1 is not None and h82 is not None and r1["id"] == h82["id"]
        if h82_in_r1:
            invariant["hex82_in_r1_component_nodes"] += 1
        if node_id not in frontier_ids:
            expanded_count += 1
        for template in entry_map.get(tuple(state.p), ()):
            route = routes[int(template["route_index"])]
            route_id = str(route["route_id"])
            cursor = state
            available = True
            for _ in range(int(template["rotation_length"])):
                step = exact.extend(cursor, W1)
                if step is None:
                    available = False
                    break
                cursor = step.state
            if not available or cursor.p != tuple(template["source"]):
                continue
            counts = route_counts[route_id]
            counts["M1_orbit_phase_macro_match"] += 1
            q = int(template["candidate_orbit"])
            target = tuple(template["target"])
            q_fresh = cursor.orbit_masks[q] == 0
            blocked = cursor.visited(tuple(template["blocker"]))
            target_fresh = not cursor.visited(target)
            resource_ok = state.F == 1 and state.H == 0 and dec.r_count == 1
            conditions = {
                "hex82_in_R1_component": h82_in_r1,
                "candidate_orbit_fresh": q_fresh,
                "w3_is_blocked": blocked,
                "target_window_fresh": target_fresh,
                "resource_scope": resource_ok,
            }
            score = sum(bool(value) for value in conditions.values())
            if h82_in_r1 and q_fresh and blocked and resource_ok:
                counts["M2_structural_state_match"] += 1
            transition = exact.extend(cursor, template["move"])
            if h82_in_r1 and q_fresh and blocked and resource_ok and transition is not None:
                edge = macro.MacroEdge(
                    next(run for run in macro.rotation_runs(state) if run.ell == int(template["rotation_length"])),
                    transition,
                )
                if pilot.edge_kind(edge) == "Z3":
                    verdict, after, recognition = rr.evaluate_edge(
                        state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
                    )
                    if verdict == "child" and after is not None and recognition is None:
                        counts["M4_exact_legal_noncolliding_C4"] += 1
                        classification = search.classify_component_change(state, dec, edge, edge.state, after)
                        if classification["is_first_component_change_candidate"]:
                            counts["M5_FZ1_witness"] += 1
            failed = next((name for name, value in conditions.items() if not value), "none")
            counts[f"first_failed:{failed}"] += 1
            rank = (-score, int(stored["depth"]), node_id, str(template["move"].label))
            current = nearest.get(route_id)
            if current is None or tuple(rank) < tuple(current["rank"]):
                nearest[route_id] = {
                    "rank": list(rank), "satisfied_condition_count": score,
                    "conditions": conditions, "first_failed_condition": failed,
                    "seed_id": seed_id, "node_id": node_id, "depth": int(stored["depth"]),
                    "state_hash": str(stored["exact_state_hash"]),
                    "decorated_state_sha256": str(stored["decorated_state_sha256"]),
                    "macro_label": f"rot^{template['rotation_length']};{template['move'].label}",
                    "literal_joint_source": list(cursor.p), "literal_target": list(target),
                    "target_already_visited": not target_fresh,
                }
        if child_counts[node_id] > 0:
            active[node_id] = (state, dec)
    if active:
        raise AssertionError(f"unconsumed active parents: {seed_id}: {len(active)}")
    traces = traces_for_nodes(
        path, roots, (str(row["node_id"]) for row in nearest.values()), parents, starts
    ) if nearest else {}
    for route_id, row in nearest.items():
        row["representative_path"] = traces[str(row["node_id"])]
        row.pop("rank", None)
    return {
        "seed_id": seed_id,
        "checkpoint_path": str(path.relative_to(ROOT)),
        "checkpoint_sha256": sha256_file(path),
        "nodes_replayed": node_count,
        "expanded_nodes": expanded_count,
        "frontier_nodes": len(frontier_ids),
        "invariant_counts": dict(invariant),
        "route_counts": {key: dict(value) for key, value in route_counts.items()},
        "nearest_route_states": nearest,
    }


def merge_nearest(branches: list[Mapping[str, object]], route_ids: Iterable[str]) -> dict[str, object]:
    result = {}
    for route_id in route_ids:
        rows = [branch["nearest_route_states"].get(route_id) for branch in branches]
        rows = [row for row in rows if row is not None]
        if rows:
            result[route_id] = min(rows, key=lambda row: (
                -int(row["satisfied_condition_count"]), int(row["depth"]), str(row["node_id"])
            ))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if not json.loads(ROUND60.read_text(encoding="utf-8"))["verified"]:
        raise AssertionError("Round-60 prerequisite is not independently verified")
    routes, entry_map = route_specifications()
    obligation = registration_obligation(manifest)
    if not obligation["all_84_roots_hex40_full"] or obligation["roots_terminal_at_unique_source"] != 0:
        raise AssertionError("finite provenance obstruction failed at the anchor family")
    result_by_seed = {str(row["seed_id"]): row for row in result["branches"]}
    branches = []
    for seed_id in search.SOURCE_IDS:
        path = ROOT / result_by_seed[seed_id]["checkpoint"]["path"]
        if sha256_file(path) != result_by_seed[seed_id]["checkpoint"]["sha256"]:
            raise AssertionError(f"immutable Stage-D checkpoint changed: {seed_id}")
        branch = audit_branch(
            path, manifest, seed_id, routes, entry_map,
            tuple(int(value) for value in obligation["unique_w2_source_word"]),
        )
        branches.append(branch)
        print(json.dumps({
            "seed_id": seed_id, "nodes": branch["nodes_replayed"],
            "route_matches": sum(sum(v.values()) for v in branch["route_counts"].values()),
        }, sort_keys=True), flush=True)
    invariant_total = Counter()
    totals = {str(route["route_id"]): Counter() for route in routes}
    for branch in branches:
        invariant_total.update(branch["invariant_counts"])
        for route_id, counts in branch["route_counts"].items():
            totals[route_id].update(counts)
    if any(invariant_total[key] for key in (
        "q91_p2_registered_nodes", "unique_z2_source_terminal_nodes", "hex82_in_r1_component_nodes"
    )):
        raise AssertionError(f"hand invariant contradicted by exact corpus: {invariant_total}")
    route_payload = {
        "schema": "rr-short-ell2-r1-37-hex82-routes-v1",
        "scope": "five exact hex-82 route specifications; no quotient",
        "route_count": len(routes), "routes": routes,
        "common_registration_obligation": obligation,
        "inputs": {"candidate_table_sha256": sha256_file(CANDIDATES), "manifest_sha256": sha256_file(MANIFEST)},
        "analyzer_sha256": sha256_file(Path(__file__)),
    }
    backward = {
        "schema": "rr-short-ell2-r1-37-hex82-backward-closure-v1",
        "closure_kind": "finite literal predecessor-obligation closure",
        "strong_key": [
            "literal target orbit/phase/window", "required incidence component relation",
            "candidate registration mask", "target occupancy", "joint kind and source",
            "R-count and F/H scope", "anchor visited-set provenance",
        ],
        "route_classes": 5,
        "deduplicated_predecessor_classes": 1,
        "predecessor_classes": [obligation],
        "provenance_consistent_classes": 0,
        "exact_reachable_classes": 0,
        "exact_noncolliding_C4_witnesses": 0,
        "stabilized": True,
        "classification_by_route": [{
            "route_id": route["route_id"], "highest_backward_level": "H3",
            "terminal_predecessor_level": "H2",
            "first_failed_condition": "unique q91:p2 Z2 source was visited before every anchor and is not an anchor terminal",
            "H4_exact_reachable": False, "H5_exact_noncolliding_C4": False,
        } for route in routes],
        "levels": {
            "H0": "locally impossible", "H1": "locally realizable but predecessor illegal",
            "H2": "predecessor locally legal but anchored provenance incompatible",
            "H3": "route prerequisites are abstractly compatible", "H4": "exact reachable state",
            "H5": "exact noncolliding C4 witness",
        },
        "SAT_CSP": "NOT_NEEDED: the one literal predecessor obligation is eliminated by exact no-repeat provenance",
    }
    nearest = merge_nearest(branches, (str(route["route_id"]) for route in routes))
    match_totals = Counter()
    for counts in totals.values():
        match_totals.update(counts)
    mitm = {
        "schema": "rr-short-ell2-r1-37-hex82-mitm-v1",
        "scope": "read-only replay of all stored Stage-D exact/decorated nodes plus one-step route tests",
        "root_route_coarse_pairs_M0": 84 * 5,
        "match_units": "route-specific one-step w3 macro candidates from exact stored nodes",
        "M1_orbit_phase_matches": int(match_totals["M1_orbit_phase_macro_match"]),
        "M2_structural_state_matches": int(match_totals["M2_structural_state_match"]),
        "M3_exact_decorated_state_matches": 0,
        "M4_exact_legal_noncolliding_C4": int(match_totals["M4_exact_legal_noncolliding_C4"]),
        "M5_FZ1_witnesses": int(match_totals["M5_FZ1_witness"]),
        "invariant_counts": dict(invariant_total),
        "per_route": [{"route_id": route_id, "counts": dict(counts)} for route_id, counts in totals.items()],
        "shortest_exact_reachable_near_miss": nearest,
        "branches": branches,
        "interpretation": "M1 is nonempty only as a local macro-target match; every such route fails before M2 because h82 never enters C_R1",
    }
    occupancy = {
        "schema": "rr-short-ell2-r1-37-hex82-occupancy-audit-v1",
        "anchor_count": 84,
        "root_hex82_mask_histogram": obligation["root_hex82_mask_histogram"],
        "hex82_rotation_table": [{
            "hex_position": position, "word": list(value),
            "orbit": int(exact.ORBIT_PHASE[value][0]), "phase": int(exact.ORBIT_PHASE[value][1]),
        } for position, value in enumerate(core.orbit(core.ROT_REPS[HEX82], core.SIGMA))],
        "q91_h82_incidence": {
            "orbit": 91, "phase": 2, "hex_position": 3, "word": list(word(91, 2)),
        },
        "hidden_forced_occupation_lemma": {
            "status": "PROVED_FOR_THE_84_ANCHOR_DESCENDANT_FAMILY",
            "statement": "before R2, no legal descendant can introduce q91:p2, hence h82 never joins C_R1; every one of the five C4 route prerequisites is unreachable",
            "proof_steps": obligation["provenance_argument"],
            "monotonicity": "visited permutation windows never become unvisited",
        },
        "five_case_analysis": [{
            "route_id": route["route_id"],
            "shortest_abstract_prerequisite_chain": [
                "introduce q91:p2 by blocked w2 so h82 joins C_R1",
                f"keep q{route['candidate_orbit']} fresh and its target window unvisited",
                "execute the listed blocked w3 joint as Z3",
            ],
            "shortest_exact_reachable_near_miss": nearest.get(str(route["route_id"])),
            "first_forced_failure": "q91:p2 registration predecessor is provenance-incompatible",
            "failure_forced": True,
            "SAT_CSP_needed": False,
        } for route in routes],
        "theorem_ladder": {
            "T2": "PROVED: all 253,537 observed C4 attempts collide (Round 60)",
            "T2a": "PROVED: every route through full h40/h90/h91/h92 collides by monotonicity",
            "T2b": "PROVED: all five h82 routes are exact-unreachable before R2",
            "T2+": "PROVED for the frozen 84-anchor descendant family: the complete first-component-Z3 C4 prerequisite space is obstructed",
            "T3": "PROVED for the same family: a first R1-component-changing Z3 cannot occur",
            "T4": "PROVED for the same family, using the prior direct-Z2 obstruction plus T3: a pre-R2 bridge cannot occur",
        },
        "scope_warning": "This is branch-family closure below the 84 frozen Stage-D anchors, not a theorem for arbitrary short_ell2 or arbitrary RR states.",
    }
    if args.write:
        write_json(ROUTES_OUT, route_payload)
        write_json(BACKWARD_OUT, backward)
        write_json(MITM_OUT, mitm)
        write_json(OCCUPANCY_OUT, occupancy)
    print(json.dumps({
        "routes": 5, "predecessor_classes": 1,
        "M1": mitm["M1_orbit_phase_matches"], "M2": mitm["M2_structural_state_matches"],
        "M4": mitm["M4_exact_legal_noncolliding_C4"], "M5": mitm["M5_FZ1_witnesses"],
        "theorem": "T4_FROZEN_84_ANCHOR_FAMILY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
