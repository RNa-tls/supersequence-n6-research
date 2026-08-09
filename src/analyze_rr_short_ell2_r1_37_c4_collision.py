#!/usr/bin/env python3
"""Round 60: exact C4-collision provenance audit.

This is a read-only replay of the six immutable Stage-D parent DAGs.  C4 is
not inferred from a profile: a row is counted only when the exact weight-3
target has the required candidate orbit/phase/component/freshness properties
and ``exact.extend`` rejects the literal joint target.

The output deliberately distinguishes the closure of the *observed parent
DAG* from a complete closure of every mathematically possible C4 prerequisite
state.  The former is finite and exact; the latter is not assumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping

import analyze_rr_short_ell2_r1_37_fz1_candidates as fz1


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
CANDIDATES = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_orbits.json"
ROUND59_LEDGER = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_condition_ledger.json"

LEDGER_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_c4_collision_ledger.json"
CLASSES_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_c4_collision_classes.json"
TOUCH_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_c4_first_touch_audit.json"
CLOSURE_OUT = ROOT / "outputs" / "rr_short_ell2_r1_37_c4_predecessor_closure.json"

search, rr, exact, pilot, core, macro = fz1.search, fz1.rr, fz1.exact, fz1.pilot, fz1.core, fz1.macro
R1_ORBIT = fz1.R1_ORBIT
FULL_HEX = exact.FULL_HEX
HUB_CANDIDATES = frozenset({96, 120, 126, 128, 129})
TAXONOMY = ("K0", "K1", "K2", "K3", "K4", "K5", "K6")
TOUCH_CLASSES = ("T0", "T1", "T2", "T3", "T4")


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
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def word_key(word) -> str:
    return "".join(str(int(x)) for x in word)


def word_for(q: int, phase: int):
    return tuple(core.orbit(core.E_REPS[q], core.E)[phase])


def relabel_to_source_identity(source, word) -> list[int]:
    alpha = [0] * exact.N
    for position, symbol in enumerate(source):
        alpha[int(symbol)] = position
    return list(core.left_relabel(tuple(word), tuple(alpha)))


def candidate_table() -> dict[int, dict[str, object]]:
    raw = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    rows = {int(row["orbit_id"]): dict(row) for row in raw["candidate_orbits"]}
    if len(rows) != 20 or sorted(q for q, row in rows.items() if row["touches_hub"]) != sorted(HUB_CANDIDATES):
        raise AssertionError("Round-59 candidate table changed")
    return rows


def target_words(candidates: Mapping[int, Mapping[str, object]]) -> dict[str, tuple[int, int, tuple[int, ...]]]:
    result = {}
    for q, row in candidates.items():
        for phase in row["orbit_91_contact_phases"]:
            word = word_for(q, int(phase))
            result[word_key(word)] = (q, int(phase), word)
    return result


def replay_introductions(parent_state, edge, node_id: str, depth: int) -> list[dict[str, object]]:
    """Return every newly visited literal window in one stored macro edge."""
    rows = []
    cursor = parent_state
    for index in range(edge.run.ell):
        step = exact.extend(cursor, macro.W1)
        if step is None:
            raise AssertionError("stored rotation prefix stopped early")
        rows.append({
            "word": tuple(step.target), "position": f"rotation:{index + 1}",
            "node_id": node_id, "depth": depth, "macro_edge": rr.edge_json(edge),
            "macro_source_word": list(parent_state.p), "introduced_word": list(step.target),
        })
        cursor = step.state
    if cursor != edge.run.state:
        raise AssertionError("stored rotation endpoint mismatch")
    rows.append({
        "word": tuple(edge.joint.target), "position": "joint",
        "node_id": node_id, "depth": depth, "macro_edge": rr.edge_json(edge),
        "macro_source_word": list(parent_state.p), "introduced_word": list(edge.joint.target),
    })
    return rows


def current_run_collision_introduction(state, run, target) -> dict[str, object] | None:
    if state.visited(target):
        return None
    cursor = state
    for index in range(run.ell):
        step = exact.extend(cursor, macro.W1)
        if step is None:
            raise AssertionError("candidate rotation prefix stopped early")
        if tuple(step.target) == tuple(target):
            return {
                "origin": "CURRENT_ATTEMPT_ROTATION",
                "position": f"rotation:{index + 1}",
                "introduced_word": list(target),
                "introduction_depth": None,
            }
        cursor = step.state
    raise AssertionError("collision target absent from macro-entry state and attempted rotation prefix")


def local_signature(row: Mapping[str, object]) -> dict[str, object]:
    intro = row["first_introduction"]
    edge = intro.get("macro_edge") if isinstance(intro, Mapping) else None
    return {
        "mechanism_family": row["mechanism_family"],
        "candidate_orbit": row["candidate_orbit"],
        "candidate_phase": row["candidate_phase"],
        "source_orbit": row["source_orbit"],
        "source_phase": row["source_phase"],
        "rotation_length": row["rotation_length"],
        "attempted_joint": row["attempted_joint"],
        "target_hexagon": row["target_hexagon"],
        "target_hex_position": row["target_hex_position"],
        "collided_permutation": row["collided_permutation"],
        "introduction_origin": intro["origin"],
        "introduction_position": intro.get("position"),
        "introducing_edge": None if edge is None else {
            "rotation_length": edge["rotation_length"], "joint": edge["joint"],
            "kind": edge["kind"], "source": edge["source"], "target": edge["target"],
        },
    }


def canonical_local_signature(row: Mapping[str, object]) -> dict[str, object]:
    intro = row["first_introduction"]
    source = tuple(row["literal_joint_source"])
    result = {
        "mechanism_family": row["mechanism_family"],
        "literal_joint_source_normalized": relabel_to_source_identity(source, source),
        "collided_permutation_normalized": relabel_to_source_identity(source, row["collided_permutation"]),
        "rotation_length": row["rotation_length"],
        "attempted_joint": row["attempted_joint"],
        "introduction_origin": intro["origin"],
        "introduction_position": intro.get("position"),
    }
    if intro.get("introduced_word") is not None:
        result["introduced_word_normalized"] = relabel_to_source_identity(source, intro["introduced_word"])
    if intro.get("macro_source_word") is not None:
        result["introducing_macro_source_normalized"] = relabel_to_source_identity(source, intro["macro_source_word"])
    edge = intro.get("macro_edge")
    if edge is not None:
        result["introducing_edge_action"] = {
            "rotation_length": edge["rotation_length"], "joint": edge["joint"], "kind": edge["kind"]
        }
    return result


def iter_c4(state, dec, candidates, intro_by_word, node_id: str, node_depth: int, state_hash: str):
    summary = rr.component_summary(state)
    component_partition_digest = rr.component_digest(state)
    r1 = search.component(summary, ("q", R1_ORBIT))
    if r1 is None:
        raise AssertionError("R1 component absent")
    r1_hexagons = set(int(x) for x in r1["hexagons"])
    for run in macro.rotation_runs(state):
        for move in macro.NONROT_H0:
            if move.weight != 3:
                continue
            target = core.word_after(run.state.p, move.action)
            q, phase = exact.ORBIT_PHASE[target]
            if q not in candidates:
                continue
            candidate = candidates[int(q)]
            if int(phase) not in set(int(x) for x in candidate["orbit_91_contact_phases"]):
                continue
            h, hpos = exact.HEX_POSITION[target]
            if int(h) not in r1_hexagons or run.state.orbit_masks[int(q)] != 0:
                continue
            transition = exact.extend(run.state, move)
            if transition is not None:
                # This is C5/C6, not C4.
                continue
            key = word_key(target)
            intro = intro_by_word.get(key)
            if intro is None:
                intro = current_run_collision_introduction(state, run, target)
                if intro is None:
                    raise AssertionError("visited C4 target lacks an introducer")
            else:
                intro = dict(intro)
            preexisting_at_macro_entry = state.visited(target)
            mechanism = "K0" if preexisting_at_macro_entry else "K5"
            touch = "T2" if preexisting_at_macro_entry else "T1"
            dec_json = dec.to_json()
            row = {
                "candidate_orbit": int(q), "candidate_phase": int(phase),
                "hub_touching_candidate": int(q) in HUB_CANDIDATES,
                "source_state_node_id": node_id, "source_state_hash": state_hash,
                "source_depth": node_depth,
                "source_orbit": int(exact.ORBIT_PHASE[run.state.p][0]),
                "source_phase": int(exact.ORBIT_PHASE[run.state.p][1]),
                "literal_joint_source": list(run.state.p),
                "rotation_length": int(run.ell), "attempted_joint": move.label,
                "attempted_weight": int(move.weight), "target_hexagon": int(h),
                "target_hex_position": int(hpos), "target_hex_mask_at_macro_entry": int(state.hex_masks[int(h)]),
                "target_hex_mask_at_joint_source": int(run.state.hex_masks[int(h)]),
                "collided_object_type": "permutation_window",
                "collided_permutation": list(target), "engine_rejection": "exact_permutation_collision",
                "mechanism_family": mechanism, "first_introduction": intro,
                "first_touch_class": touch,
                "candidate_registration_mask_before": int(run.state.orbit_masks[int(q)]),
                "candidate_previously_registered": False,
                "continuous_residency_since_registration": False,
                "delayed_Z2_route_remains": False,
                "r1_provenance": dec_json["r_events"][0] if dec_json["r_events"] else None,
                "component_partition_digest": component_partition_digest,
                "r1_component": {"id": r1["id"], "e_orbits": r1["e_orbits"], "hexagons": r1["hexagons"]},
                "resources": {name: int(getattr(state, name)) for name in ("P", "O", "F", "H", "Ndef", "D")},
            }
            row["exact_local_signature"] = local_signature(row)
            row["exact_local_signature_sha256"] = sha256_json(row["exact_local_signature"])
            row["left_s6_canonical_signature"] = canonical_local_signature(row)
            row["left_s6_canonical_signature_sha256"] = sha256_json(row["left_s6_canonical_signature"])
            yield row


def update_class(classes, key: str, row: Mapping[str, object], signature_field: str) -> None:
    current = classes.get(key)
    if current is None:
        classes[key] = {
            "signature_sha256": key, "signature": row[signature_field], "count": 1,
            "candidate_orbits": Counter({str(row["candidate_orbit"]): 1}),
            "mechanism_families": Counter({str(row["mechanism_family"]): 1}),
            "representative": dict(row),
        }
        return
    current["count"] += 1
    current["candidate_orbits"][str(row["candidate_orbit"])] += 1
    current["mechanism_families"][str(row["mechanism_family"])] += 1
    if (int(row["source_depth"]), str(row["source_state_node_id"])) < (
        int(current["representative"]["source_depth"]), str(current["representative"]["source_state_node_id"])
    ):
        current["representative"] = dict(row)


def normalize_classes(classes: Mapping[str, Mapping[str, object]]) -> list[dict[str, object]]:
    rows = []
    for key, value in sorted(classes.items()):
        rows.append({
            "signature_sha256": key, "signature": value["signature"], "count": int(value["count"]),
            "candidate_orbits": dict(sorted(value["candidate_orbits"].items(), key=lambda item: int(item[0]))),
            "mechanism_families": dict(sorted(value["mechanism_families"].items())),
            "representative": value["representative"],
        })
    return rows


def audit_branch(path: Path, manifest, seed_id: str, candidates, target_map):
    frontier_ids = {str(row["node_id"]) for row in fz1.iter_top_array(path, "frontier")}
    child_counts: Counter[str] = Counter()
    parents: dict[str, str | None] = {}
    depths: dict[str, int] = {}
    for row in fz1.iter_top_array(path, "nodes"):
        node_id = str(row["node_id"])
        parent = None if row["parent_id"] is None else str(row["parent_id"])
        parents[node_id] = parent
        depths[node_id] = int(row["depth"])
        if parent is not None:
            child_counts[parent] += 1
    roots = fz1.source_lookup(manifest, seed_id)
    active = {}
    exact_classes, canonical_classes = {}, {}
    mechanism = Counter({key: 0 for key in TAXONOMY})
    touch = Counter({key: 0 for key in TOUCH_CLASSES})
    per_candidate = defaultdict(Counter)
    target_hex_masks = Counter()
    c4_nodes: set[str] = set()
    attempts = 0
    for stored in fz1.iter_top_array(path, "nodes"):
        node_id = str(stored["node_id"])
        parent_id = None if stored["parent_id"] is None else str(stored["parent_id"])
        depth = int(stored["depth"])
        if parent_id is None:
            source = roots[str(stored["start_record_id"])]
            state = exact.state_from_json(source["state"])
            dec = rr.Decoration.from_json(source["decoration"])
            introductions = {}
            for key, (_q, _phase, word) in target_map.items():
                if state.visited(word):
                    introductions[key] = {
                        "origin": "PRE_STAGE_D_ANCHOR", "position": None,
                        "introduced_word": list(word), "introduction_depth": None,
                        "anchor_node_id": str(source["source_node_id"]),
                        "anchor_path_hash": str(source["source_path_hash"]),
                    }
        else:
            if parent_id not in active:
                raise AssertionError(f"active parent missing: {node_id}")
            parent_state, parent_dec, parent_intro = active[parent_id]
            edge = pilot.edge_from_json(parent_state, stored["incoming_macro_edge"])
            verdict, dec, recognition = rr.evaluate_edge(parent_state, parent_dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
            if verdict != "child" or dec is None or recognition is not None:
                raise AssertionError(f"stored edge replay failed: {node_id}")
            state = edge.state
            introductions = dict(parent_intro)
            for item in replay_introductions(parent_state, edge, node_id, depth):
                key = word_key(item.pop("word"))
                if key in target_map and key not in introductions:
                    introductions[key] = {"origin": "STAGE_D_ANCESTOR", "introduction_depth": depth, **item}
            child_counts[parent_id] -= 1
            if child_counts[parent_id] == 0:
                del active[parent_id]
        if rr.state_hash(state) != stored["exact_state_hash"] or dec.to_json() != stored["decoration"]:
            raise AssertionError(f"literal state mismatch: {node_id}")
        if node_id not in frontier_ids:
            for row in iter_c4(state, dec, candidates, introductions, node_id, depth, str(stored["exact_state_hash"])):
                attempts += 1
                c4_nodes.add(node_id)
                mechanism[row["mechanism_family"]] += 1
                touch[row["first_touch_class"]] += 1
                q = str(row["candidate_orbit"])
                per_candidate[q]["attempts"] += 1
                per_candidate[q][f"mechanism:{row['mechanism_family']}"] += 1
                per_candidate[q][f"phase:{row['candidate_phase']}"] += 1
                per_candidate[q][f"hex:{row['target_hexagon']}"] += 1
                target_hex_masks[f"h{row['target_hexagon']}:m{row['target_hex_mask_at_joint_source']}"] += 1
                update_class(exact_classes, str(row["exact_local_signature_sha256"]), row, "exact_local_signature")
                update_class(canonical_classes, str(row["left_s6_canonical_signature_sha256"]), row, "left_s6_canonical_signature")
        if child_counts[node_id] > 0:
            active[node_id] = (state, dec, introductions)
    if active:
        raise AssertionError(f"unconsumed replay parents: {seed_id}: {len(active)}")
    closure = set()
    for node_id in c4_nodes:
        cursor = node_id
        while cursor is not None and cursor not in closure:
            closure.add(cursor)
            cursor = parents[cursor]
    return {
        "seed_id": seed_id, "checkpoint_sha256": sha256_file(path), "c4_attempts": attempts,
        "c4_source_nodes": len(c4_nodes), "observed_predecessor_closure_nodes": len(closure),
        "mechanism_histogram": dict(mechanism), "first_touch_histogram": dict(touch),
        "target_hex_mask_histogram": dict(sorted(target_hex_masks.items())),
        "per_candidate": {q: dict(counter) for q, counter in sorted(per_candidate.items(), key=lambda item: int(item[0]))},
        "exact_classes": normalize_classes(exact_classes),
        "canonical_classes": normalize_classes(canonical_classes),
    }


def merge_class_rows(branches, key: str) -> list[dict[str, object]]:
    merged = {}
    for branch in branches:
        for row in branch[key]:
            signature = str(row["signature_sha256"])
            current = merged.get(signature)
            if current is None:
                current = {
                    "signature_sha256": signature, "signature": row["signature"], "count": 0,
                    "candidate_orbits": Counter(), "mechanism_families": Counter(),
                    "representative": row["representative"], "seeds": Counter(),
                }
                merged[signature] = current
            current["count"] += int(row["count"])
            current["candidate_orbits"].update({str(q): int(n) for q, n in row["candidate_orbits"].items()})
            current["mechanism_families"].update({str(q): int(n) for q, n in row["mechanism_families"].items()})
            current["seeds"][str(branch["seed_id"])] += int(row["count"])
            rep = row["representative"]
            if (int(rep["source_depth"]), str(rep["source_state_node_id"])) < (
                int(current["representative"]["source_depth"]), str(current["representative"]["source_state_node_id"])
            ):
                current["representative"] = rep
    return [{
        "signature_sha256": signature, "signature": value["signature"], "count": int(value["count"]),
        "candidate_orbits": dict(sorted(value["candidate_orbits"].items(), key=lambda item: int(item[0]))),
        "mechanism_families": dict(sorted(value["mechanism_families"].items())),
        "seeds": dict(sorted(value["seeds"].items())), "representative": value["representative"],
    } for signature, value in sorted(merged.items())]


def seed_from_node_id(node_id: str) -> str:
    pieces = node_id.split(":")
    if len(pieces) < 2:
        raise AssertionError(f"cannot recover seed from node id: {node_id}")
    return ":".join(pieces[:2])


def enrich_class_histories(classes: dict[str, object], result: Mapping[str, object]) -> None:
    """Attach the complete stored macro suffix to every representative.

    This is a parent-DAG read only operation.  The final attempted C4 joint is
    rejected and therefore is appended as an explicit terminal item rather
    than being confused with an accepted stored edge.
    """
    groups = (classes["exact_signatures"], classes["left_s6_canonical_signatures"])
    by_seed: dict[str, list[dict[str, object]]] = defaultdict(list)
    for group in groups:
        for signature in group:
            rep = signature["representative"]
            by_seed[seed_from_node_id(str(rep["source_state_node_id"]))].append(rep)
    result_by_seed = {str(row["seed_id"]): row for row in result["branches"]}
    for seed_id, representatives in by_seed.items():
        path = ROOT / result_by_seed[seed_id]["checkpoint"]["path"]
        parents: dict[str, str | None] = {}
        for row in fz1.iter_top_array(path, "nodes"):
            parents[str(row["node_id"])] = None if row["parent_id"] is None else str(row["parent_id"])
        wanted = set()
        paths = {}
        for rep in representatives:
            source = str(rep["source_state_node_id"])
            ancestry = []
            cursor = source
            while cursor is not None:
                ancestry.append(cursor)
                cursor = parents[cursor]
            ancestry.reverse()
            intro = rep["first_introduction"]
            if intro["origin"] == "STAGE_D_ANCESTOR":
                start = str(intro["node_id"])
                if start not in ancestry:
                    raise AssertionError("introduction node is not an ancestor")
                ancestry = ancestry[ancestry.index(start):]
            paths[id(rep)] = ancestry
            wanted.update(ancestry)
        edge_rows = {}
        for row in fz1.iter_top_array(path, "nodes"):
            node_id = str(row["node_id"])
            if node_id in wanted:
                edge_rows[node_id] = row["incoming_macro_edge"]
        for rep in representatives:
            ancestry = paths[id(rep)]
            accepted = [edge_rows[node_id] for node_id in ancestry if edge_rows[node_id] is not None]
            rep["macro_history_suffix"] = {
                "origin": rep["first_introduction"]["origin"],
                "accepted_edge_count": len(accepted),
                "accepted_macro_edges": accepted,
                "rejected_terminal_attempt": {
                    "rotation_length": rep["rotation_length"], "joint": rep["attempted_joint"],
                    "literal_joint_source": rep["literal_joint_source"],
                    "collided_permutation": rep["collided_permutation"],
                },
                "full_stored_suffix": True,
            }


def unresolved_hex82_routes(candidates: Mapping[int, Mapping[str, object]]) -> list[dict[str, int]]:
    rows = []
    for q, candidate in sorted(candidates.items()):
        contact = set(int(x) for x in candidate["orbit_91_contact_phases"])
        for phase_row in candidate["all_phase_rows"]:
            if int(phase_row["phase"]) in contact and int(phase_row["hexagon"]) == 82:
                rows.append({
                    "candidate_orbit": q, "candidate_phase": int(phase_row["phase"]),
                    "target_hexagon": 82, "target_hex_position": int(phase_row["hex_rotation_position"]),
                })
    return rows


def finalize_existing_outputs() -> None:
    ledger = json.loads(LEDGER_OUT.read_text(encoding="utf-8"))
    classes = json.loads(CLASSES_OUT.read_text(encoding="utf-8"))
    touch = json.loads(TOUCH_OUT.read_text(encoding="utf-8"))
    closure = json.loads(CLOSURE_OUT.read_text(encoding="utf-8"))
    candidates = candidate_table()
    origins = Counter()
    for row in classes["exact_signatures"]:
        origins[str(row["signature"]["introduction_origin"])] += int(row["count"])
    routes = unresolved_hex82_routes(candidates)
    if routes != [
        {"candidate_orbit": 42, "candidate_phase": 1, "target_hexagon": 82, "target_hex_position": 2},
        {"candidate_orbit": 78, "candidate_phase": 3, "target_hexagon": 82, "target_hex_position": 4},
        {"candidate_orbit": 82, "candidate_phase": 0, "target_hexagon": 82, "target_hex_position": 0},
        {"candidate_orbit": 83, "candidate_phase": 4, "target_hexagon": 82, "target_hex_position": 5},
        {"candidate_orbit": 128, "candidate_phase": 2, "target_hexagon": 82, "target_hex_position": 1},
    ]:
        raise AssertionError(f"hex-82 route table changed: {routes}")
    ledger["first_introduction_origin_histogram"] = dict(sorted(origins.items()))
    touch["first_introduction_origin_histogram"] = dict(sorted(origins.items()))
    closure["remaining_hex82_case"]["unresolved_local_phase_routes"] = routes
    closure["remaining_hex82_case"]["exact_global_class_count"] = None
    closure["remaining_hex82_case"]["SAT_CSP_status"] = (
        "NOT_ENCODED: five local routes are not five exact global states; no proved finite provenance quotient exists"
    )
    closure["four_full_hex_route_proof"] = {
        "hexagons": [40, 90, 91, 92],
        "covered_candidate_phase_routes": [
            {"candidate_orbit": q, "candidate_phase": int(phase_row["phase"]), "target_hexagon": int(phase_row["hexagon"])}
            for q, candidate in sorted(candidates.items()) for phase_row in candidate["all_phase_rows"]
            if int(phase_row["phase"]) in set(int(x) for x in candidate["orbit_91_contact_phases"])
            and int(phase_row["hexagon"]) in {40, 90, 91, 92}
        ],
        "claim": "every descendant C4 prerequisite using one of these phase routes collides before the Z3 can execute",
    }
    write_json(LEDGER_OUT, ledger)
    write_json(TOUCH_OUT, touch)
    write_json(CLOSURE_OUT, closure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--enrich-existing", action="store_true")
    parser.add_argument("--finalize-existing", action="store_true")
    args = parser.parse_args()
    if args.finalize_existing:
        finalize_existing_outputs()
        print(json.dumps({"finalized": True, "unresolved_hex82_routes": 5}, sort_keys=True))
        return 0
    if args.enrich_existing:
        classes = json.loads(CLASSES_OUT.read_text(encoding="utf-8"))
        result = json.loads(RESULT.read_text(encoding="utf-8"))
        enrich_class_histories(classes, result)
        write_json(CLASSES_OUT, classes)
        print(json.dumps({
            "exact": len(classes["exact_signatures"]),
            "canonical": len(classes["left_s6_canonical_signatures"]),
            "histories_enriched": True,
        }, sort_keys=True))
        return 0
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    round59 = json.loads(ROUND59_LEDGER.read_text(encoding="utf-8"))
    candidates = candidate_table()
    targets = target_words(candidates)
    result_by_seed = {str(row["seed_id"]): row for row in result["branches"]}
    branches = []
    for seed_id in search.SOURCE_IDS:
        path = ROOT / result_by_seed[seed_id]["checkpoint"]["path"]
        if sha256_file(path) != result_by_seed[seed_id]["checkpoint"]["sha256"]:
            raise AssertionError(f"immutable checkpoint changed: {seed_id}")
        branch = audit_branch(path, manifest, seed_id, candidates, targets)
        branches.append(branch)
        print(json.dumps({"seed_id": seed_id, "C4": branch["c4_attempts"]}, sort_keys=True), flush=True)
    total = sum(int(row["c4_attempts"]) for row in branches)
    expected = sum(int(row["level_counts"]["C4"]) for row in round59["per_candidate"])
    if total != 253537 or total != expected:
        raise AssertionError(f"C4 conservation failed: {total}, {expected}")
    exact_rows = merge_class_rows(branches, "exact_classes")
    canonical_rows = merge_class_rows(branches, "canonical_classes")
    mechanisms = Counter({key: 0 for key in TAXONOMY})
    touches = Counter({key: 0 for key in TOUCH_CLASSES})
    per_candidate = {str(q): Counter() for q in candidates}
    closure_nodes = 0
    source_nodes = 0
    masks = Counter()
    for branch in branches:
        mechanisms.update(branch["mechanism_histogram"])
        touches.update(branch["first_touch_histogram"])
        closure_nodes += int(branch["observed_predecessor_closure_nodes"])
        source_nodes += int(branch["c4_source_nodes"])
        masks.update(branch["target_hex_mask_histogram"])
        for q, values in branch["per_candidate"].items():
            per_candidate[q].update(values)
    candidate_rows = []
    for q in sorted(candidates):
        values = per_candidate[str(q)]
        candidate_rows.append({
            "candidate_orbit": q, "hub_touching": q in HUB_CANDIDATES,
            "C4_attempt_count": int(values["attempts"]),
            "collision_family_distribution": {key: int(values[f"mechanism:{key}"]) for key in TAXONOMY},
            "phase_distribution": {key.split(":", 1)[1]: int(value) for key, value in values.items() if key.startswith("phase:")},
            "target_hexagon_distribution": {key.split(":", 1)[1]: int(value) for key, value in values.items() if key.startswith("hex:")},
            "minimum_macro_depth": min(
                int(row["representative"]["source_depth"])
                for row in exact_rows if str(q) in row["candidate_orbits"]
            ) if values["attempts"] else None,
            "unique_obstruction": False,
        })
    fixed_full = {}
    for h in (40, 82, 90, 91, 92):
        histogram = Counter()
        for record in manifest["start_domain"]["records"]:
            sparse = {int(index): int(mask) for index, mask in record["state"]["hex_masks"]}
            histogram[str(sparse.get(h, 0))] += 1
        fixed_full[str(h)] = dict(sorted(histogram.items(), key=lambda item: int(item[0])))
    ledger = {
        "schema": "rr-short-ell2-r1-37-c4-collision-ledger-v1",
        "scope": "six immutable Stage-D parent DAGs; exact observed corpus only",
        "C4_attempts": total, "exact_collision_signatures": len(exact_rows),
        "left_s6_canonical_collision_signatures": len(canonical_rows),
        "mechanism_family_count": sum(bool(mechanisms[key]) for key in TAXONOMY),
        "mechanism_histogram": dict(mechanisms), "candidate_rows": candidate_rows,
        "branches": [{key: value for key, value in row.items() if key not in {"exact_classes", "canonical_classes"}} for row in branches],
        "engine_semantics": {
            "joint_rejection": "exact.extend returns None iff the literal target permutation window is already visited",
            "K0": "target was visited before the attempted macro began",
            "K5": "target was first visited in the tentative rotation prefix of this same macro",
            "K1_K4_K6": "zero: the exact engine has no separate rejection at these layers",
        },
        "input_sha256": {"manifest": sha256_file(MANIFEST), "result": sha256_file(RESULT), "round59_ledger": sha256_file(ROUND59_LEDGER)},
        "analyzer_sha256": sha256_file(Path(__file__)),
    }
    classes = {
        "schema": "rr-short-ell2-r1-37-c4-collision-classes-v1",
        "exact_local_signature_definition": "literal orbit/phase, source, action, target word/hex, and exact first-introduction event; no quotient",
        "left_s6_signature_definition": "the same local words normalized by the unique proved alphabet relabelling sending the literal joint source to identity",
        "heuristic_profiles_not_quotiented": True,
        "exact_signature_count": len(exact_rows), "left_s6_canonical_signature_count": len(canonical_rows),
        "exact_signatures": exact_rows, "left_s6_canonical_signatures": canonical_rows,
    }
    enrich_class_histories(classes, result)
    touch_payload = {
        "schema": "rr-short-ell2-r1-37-c4-first-touch-audit-v1",
        "C4_attempts": total, "classification": dict(touches),
        "definitions": {
            "T0": "wrong qualifying phase (zero by the C4 prerequisite)",
            "T1": "correct phase, but its literal window was first touched in this same tentative rotation prefix",
            "T2": "the literal target window was touched before this macro; direct fresh registration therefore collides",
            "T3": "previous registration with continuous residence permits a delayed Z2 route",
            "T4": "realizable FZ1 witness",
        },
        "candidate_orbit_registration_before": {"registered": 0, "fresh": total},
        "continuous_residency_delayed_Z2_candidates": int(touches["T3"]),
        "interpretation": "C4 freshness is about pass-start registration; the collided permutation window may already have been visited by a rotation in another pass.",
    }
    closure = {
        "schema": "rr-short-ell2-r1-37-c4-predecessor-closure-v1",
        "closure_domain": "exact ancestors of observed C4 source nodes inside the six frozen Stage-D parent DAGs",
        "C4_source_nodes": source_nodes, "observed_predecessor_closure_nodes": closure_nodes,
        "closure_stabilized_inside_observed_DAG": True,
        "new_states_outside_observed_DAG_enumerated": False,
        "complete_finite_C4_prerequisite_closure": False,
        "unresolved_reason": "backward ancestry closure cannot manufacture legal predecessor states absent from the bounded Stage-D corpus",
        "root_hex_mask_histograms": fixed_full,
        "observed_C4_target_hex_mask_histogram": dict(sorted(masks.items())),
        "proved_monotone_subcase": {
            "hexagons_full_in_all_84_roots": [40, 90, 91, 92],
            "claim": "all descendants keep these four hexagons full, so every C4 prerequisite targeting one of them collides",
            "proof": "hex masks only gain bits under exact.extend",
        },
        "remaining_hex82_case": {
            "root_histogram": fixed_full["82"],
            "status": "OBSERVED_COLLISION_ONLY_UNLESS_A_SEPARATE_PRECEDENCE_LEMMA_IS_PROVED",
        },
        "theorem_level": "T2: all observed C4 states collide; T2+ is not established",
    }
    origin_histogram = Counter()
    for row in exact_rows:
        origin_histogram[str(row["signature"]["introduction_origin"])] += int(row["count"])
    ledger["first_introduction_origin_histogram"] = dict(sorted(origin_histogram.items()))
    touch_payload["first_introduction_origin_histogram"] = ledger["first_introduction_origin_histogram"]
    routes = unresolved_hex82_routes(candidates)
    closure["remaining_hex82_case"]["unresolved_local_phase_routes"] = routes
    closure["remaining_hex82_case"]["exact_global_class_count"] = None
    closure["remaining_hex82_case"]["SAT_CSP_status"] = (
        "NOT_ENCODED: five local routes are not five exact global states; no proved finite provenance quotient exists"
    )
    if args.write:
        write_json(LEDGER_OUT, ledger)
        write_json(CLASSES_OUT, classes)
        write_json(TOUCH_OUT, touch_payload)
        write_json(CLOSURE_OUT, closure)
    print(json.dumps({
        "C4": total, "exact_signatures": len(exact_rows), "canonical_signatures": len(canonical_rows),
        "mechanisms": dict(mechanisms), "touch": dict(touches), "closure": closure_nodes,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
