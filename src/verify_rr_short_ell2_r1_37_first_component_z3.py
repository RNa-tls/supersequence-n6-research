#!/usr/bin/env python3
"""Independent replay verifier for the first-component-changing-Z3 search."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "src" / "search_rr_short_ell2_r1_37_first_component_z3.py"
MANIFEST = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
WITNESSES = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_witnesses.json"
VERIFIED = ROOT / "outputs" / "rr_short_ell2_r1_37_component_change_verified.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


search = load_module("rr_first_component_search_for_verify", DRIVER)
rr, exact, pilot, core = search.rr, search.exact, search.pilot, search.core


def sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def component(summary: Mapping[str, object], node: tuple[str, int]):
    return summary["node_component"].get(node)  # type: ignore[index,union-attr]


def nodes(item) -> frozenset[tuple[str, int]]:
    if item is None:
        return frozenset()
    return frozenset(
        [("q", int(value)) for value in item["e_orbits"]]
        + [("h", int(value)) for value in item["hexagons"]]
    )


def independent_z2_route(state, dec) -> bool:
    summary = rr.component_summary(state)
    r1 = component(summary, ("q", int(dec.r1.target_orbit)))
    hub = component(summary, ("h", int(dec.hub_id)))
    if r1 is None or hub is None:
        return False
    hub_hexes = set(int(value) for value in hub["hexagons"])
    return any(
        core.hexagon_id(port) in hub_hexes
        for orbit in r1["e_orbits"]
        for port in core.ports_of_e_orbit(core.E_REPS[int(orbit)])
    )


def independent_class(parent_state, parent_dec, edge, child_state, child_dec) -> tuple[str, bool]:
    if pilot.edge_kind(edge) != "Z3":
        return "FZ0", False
    pre, post = rr.component_summary(parent_state), rr.component_summary(child_state)
    r1_node = ("q", int(parent_dec.r1.target_orbit))
    hub_node = ("h", int(parent_dec.hub_id))
    pre_r1, pre_hub = nodes(component(pre, r1_node)), nodes(component(pre, hub_node))
    post_r1, post_hub = nodes(component(post, r1_node)), nodes(component(post, hub_node))
    if not pre_r1 or not pre_hub or pre_r1 == pre_hub:
        raise AssertionError("verifier encountered invalid pre-event component relation")
    changed = post_r1 > pre_r1
    if not changed:
        return "FZ0", False
    if post_r1 == post_hub:
        return "FZ3", True
    return ("FZ2" if independent_z2_route(child_state, child_dec) else "FZ1"), True


def start_lookup(manifest: Mapping[str, object], seed_id: str):
    return {
        str(row["source_node_id"]): row
        for row in manifest["start_domain"]["records"] if row["seed_id"] == seed_id
    }


def verify_branch(manifest: Mapping[str, object], result_row: Mapping[str, object]) -> dict[str, object]:
    seed_id = str(result_row["seed_id"])
    path = ROOT / result_row["checkpoint"]["path"]
    if sha256_file(path) != result_row["checkpoint"]["sha256"]:
        raise AssertionError(f"checkpoint SHA mismatch: {seed_id}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != search.CHECKPOINT_SCHEMA or not raw.get("complete_frontier_snapshot"):
        raise AssertionError(f"checkpoint schema mismatch: {seed_id}")
    if raw.get("provenance") != search.checkpoint_provenance(manifest, seed_id):
        raise AssertionError(f"checkpoint provenance mismatch: {seed_id}")
    roots = start_lookup(manifest, seed_id)
    states = {}
    first_change_by_node: dict[str, str | None] = {}
    max_level_by_node: dict[str, int] = {}
    recomputed_witnesses = []
    for row in raw["nodes"]:
        node_id = str(row["node_id"])
        parent_id = row["parent_id"]
        if parent_id is None:
            source = roots[str(row["start_record_id"])]
            state = exact.state_from_json(source["state"])
            dec = rr.Decoration.from_json(source["decoration"])
            first_change, max_level = None, 0
        else:
            if str(parent_id) not in states:
                raise AssertionError(f"parent-after-child: {node_id}")
            parent_state, parent_dec = states[str(parent_id)]
            edge = pilot.edge_from_json(parent_state, row["incoming_macro_edge"])
            verdict, dec, recognition = rr.evaluate_edge(
                parent_state, parent_dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            if verdict != "child" or dec is None or recognition is not None:
                raise AssertionError(f"stored child is not independently accepted: {node_id}")
            state = edge.state
            parent_first = first_change_by_node[str(parent_id)]
            parent_level = max_level_by_node[str(parent_id)]
            first_change, max_level = parent_first, parent_level
            if parent_first is None:
                label, changed = independent_class(parent_state, parent_dec, edge, state, dec)
                if changed:
                    first_change = node_id
                    max_level = int(label[2:])
                    recomputed_witnesses.append((node_id, label, rr.edge_json(edge)))
            elif search.audit.exact_bridge(parent_state, parent_dec, state, dec):
                kind = pilot.edge_kind(edge)
                max_level = max(max_level, 4 if kind == "Z2" else 3)
        if rr.state_hash(state) != row["exact_state_hash"] or dec.to_json() != row["decoration"]:
            raise AssertionError(f"literal node replay mismatch: {node_id}")
        if search.decorated_digest(state, dec) != row["decorated_state_sha256"]:
            raise AssertionError(f"decorated digest mismatch: {node_id}")
        if row.get("first_component_change_id") != first_change or int(row.get("max_fz_level", 0)) != max_level:
            raise AssertionError(f"component-change lineage mismatch: {node_id}")
        states[node_id] = (state, dec)
        first_change_by_node[node_id] = first_change
        max_level_by_node[node_id] = max_level

    frontier_ids = {str(row["node_id"]) for row in raw["frontier"]}
    if len(frontier_ids) != len(raw["frontier"]):
        raise AssertionError("duplicate frontier node id")
    for row in raw["frontier"]:
        state, dec = states[str(row["node_id"])]
        if exact.state_to_json(state) != row["state"] or dec.to_json() != row["decoration"]:
            raise AssertionError("frontier differs from replayed parent DAG")
    expanded_ids = [node_id for node_id in states if node_id not in frontier_ids]
    if len(expanded_ids) != int(raw["stats"]["expanded"]):
        raise AssertionError(f"expanded/frontier conservation failed: {seed_id}")

    stats = Counter(expanded=len(expanded_ids))
    replayed_r2 = []
    for node_id in expanded_ids:
        state, dec = states[node_id]
        first_change = first_change_by_node[node_id]
        for edge, collision in rr.iter_raw_macro_candidates(state):
            stats["generated_edges"] += 1
            if collision is not None or edge is None:
                stats[f"prune:{collision or 'missing_edge'}"] += 1
                continue
            verdict, after, recognition = rr.evaluate_edge(state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
            kind = pilot.edge_kind(edge)
            if kind == "R":
                stats["R2_candidates"] += 1
                if after is None or recognition is None:
                    raise AssertionError("R2 replay lost recognizer")
                stats[f"R2:{recognition['r2_outcome']}"] += 1
                replayed_r2.append((node_id, rr.edge_json(edge), recognition, first_change))
                if recognition["is_target_a"]:
                    stats["FZ5"] += 1
                continue
            if verdict != "child" or after is None:
                stats[f"prune:{verdict}"] += 1
                continue
            stats[f"accepted:{kind}"] += 1
            if kind == "Z3":
                stats["Z3_transitions"] += 1
                if first_change is None:
                    label, _changed = independent_class(state, dec, edge, edge.state, after)
                    stats[label] += 1
            if first_change is not None and search.audit.exact_bridge(state, dec, edge.state, after):
                stats["FZ4" if kind == "Z2" else "FZ3"] += 1

    ignored = {"checkpoint_count", "max_depth"}
    stored_stats = Counter({key: int(value) for key, value in raw["stats"].items() if key not in ignored})
    compared = Counter({key: int(value) for key, value in stats.items() if key not in ignored and value})
    # Explicit zeros need not be serialized by Counter.
    if {k: v for k, v in stored_stats.items() if v} != {k: v for k, v in compared.items() if v}:
        raise AssertionError(f"candidate ledger mismatch: {seed_id}")
    if len(replayed_r2) != len(raw["r2_records"]):
        raise AssertionError(f"R2 record count mismatch: {seed_id}")
    replayed_r2_multiset = Counter(
        sha256_json({"node": node_id, "edge": edge_json, "recognizer": recognition, "first": first_change})
        for node_id, edge_json, recognition, first_change in replayed_r2
    )
    stored_r2_multiset = Counter(
        sha256_json({
            "node": actual["predecessor_node_id"], "edge": actual["edge"],
            "recognizer": actual["recognizer"], "first": actual.get("first_component_change_id"),
        })
        for actual in raw["r2_records"]
    )
    if replayed_r2_multiset != stored_r2_multiset:
        raise AssertionError(f"R2 replay multiset mismatch: {seed_id}")
    stored_witnesses = [(row["child_node_id"], row["component_change"]["classification"], row["edge"])
                        for row in raw["witnesses"]]
    if stored_witnesses != recomputed_witnesses:
        raise AssertionError(f"first-event witness mismatch: {seed_id}")
    return {
        "seed_id": seed_id, "checkpoint_sha256": result_row["checkpoint"]["sha256"],
        "nodes_replayed": len(states), "expanded_nodes_replayed": len(expanded_ids),
        "frontier_replayed": len(frontier_ids), "accepted_transitions_rechecked": int(stats["accepted:Z2"] + stats["accepted:Z3"]),
        "R2_candidates_rechecked": len(replayed_r2), "Z3_transitions_rechecked": int(stats["Z3_transitions"]),
        "first_component_change_witnesses": len(recomputed_witnesses),
        "naturally_exhausted": len(frontier_ids) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    stored_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rebuilt_manifest = search.build_manifest()
    if stored_manifest != rebuilt_manifest:
        raise AssertionError("frozen manifest reconstruction mismatch")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if result.get("manifest_sha256") != sha256_json(stored_manifest):
        raise AssertionError("result manifest identity mismatch")
    rows = [verify_branch(stored_manifest, row) for row in result["branches"]]
    aggregate = {
        "nodes_replayed": sum(row["nodes_replayed"] for row in rows),
        "expanded_nodes_replayed": sum(row["expanded_nodes_replayed"] for row in rows),
        "frontier_replayed": sum(row["frontier_replayed"] for row in rows),
        "accepted_transitions_rechecked": sum(row["accepted_transitions_rechecked"] for row in rows),
        "R2_candidates_rechecked": sum(row["R2_candidates_rechecked"] for row in rows),
        "Z3_transitions_rechecked": sum(row["Z3_transitions_rechecked"] for row in rows),
        "first_component_change_witnesses": sum(row["first_component_change_witnesses"] for row in rows),
    }
    witness_payload = json.loads(WITNESSES.read_text(encoding="utf-8"))
    if witness_payload["witness_count"] != aggregate["first_component_change_witnesses"]:
        raise AssertionError("aggregate witness count mismatch")
    payload = {
        "schema": "rr-short-ell2-r1-37-first-component-z3-independent-verification-v1",
        "verified": True, "stage": result["stage"], "manifest_sha256": sha256_json(stored_manifest),
        "result_sha256": sha256_file(RESULT), "witness_sha256": sha256_file(WITNESSES),
        "driver_sha256": sha256_file(DRIVER), "verifier_sha256": sha256_file(Path(__file__)),
        "verification_scope": "literal parent-DAG replay and complete candidate regeneration for every expanded node",
        "branches": rows, "aggregate": aggregate,
        "theorem_scope": "bounded exact region only unless every branch has an empty frontier",
        "overall_status": result["overall_status"],
    }
    if args.write:
        atomic_json(VERIFIED, payload)
    if not VERIFIED.exists() or json.loads(VERIFIED.read_text(encoding="utf-8")) != payload:
        raise AssertionError("verified output differs; run with --write")
    print(json.dumps({"verified": True, "stage": result["stage"], **aggregate}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
