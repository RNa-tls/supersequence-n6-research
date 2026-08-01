#!/usr/bin/env python3
"""Read-only independent verifier for Round-43 taxonomy exports.

It does not resume a search or consume a checkpoint as mutable input.  Every
opaque geometry record is independently reclassified from its serialized
endpoint-membership witnesses; every frontier state is reconstructed and its
next-edge ledger is recalculated from the exact engine.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GEOMETRY = ROOT / "outputs" / "rr_short_ell0_v3_geometry_failures.json"
FRONTIER = ROOT / "outputs" / "rr_short_ell0_v3_frontier_export.json"
COMPONENTS = ROOT / "outputs" / "rr_short_ell0_v3_component_failures.json"
OUTPUT = ROOT / "outputs" / "rr_short_ell0_v3_taxonomy_verified.json"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", type=Path, default=GEOMETRY)
    parser.add_argument("--frontier", type=Path, default=FRONTIER)
    parser.add_argument("--components", type=Path, default=COMPONENTS)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    rr = load("rr_taxonomy_verifier_engine", ROOT / "src" / "search_rr_target_a_exhaustive.py")
    geo = json.loads(args.geometry.read_text(encoding="utf-8"))
    front = json.loads(args.frontier.read_text(encoding="utf-8"))
    comps = json.loads(args.components.read_text(encoding="utf-8"))
    failures: list[str] = []
    checkpoint_info = front.get("checkpoint_read_only", {})
    checkpoint_path = ROOT / checkpoint_info.get("path", "")
    checkpoint_rows: dict[tuple[str, str], Mapping[str, object]] = {}
    if not checkpoint_path.exists():
        failures.append("frontier source checkpoint unavailable")
    else:
        raw_checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        for item in raw_checkpoint.get("frontier", []):
            state = rr.exact.state_from_json(item["state"])
            dec = rr.Decoration.from_json(item["decoration"])
            checkpoint_rows[(rr.state_hash(state), repr(rr.decorated_key(state, dec)))] = item

    if tuple(geo.get("taxonomy_order", ())) != rr.GEOMETRY_FAILURE_VOCABULARY:
        failures.append("taxonomy vocabulary/order")
    recounted: Counter[str] = Counter()
    ids = set()
    for record in geo.get("records", []):
        source_present = bool(record["source_orbit_present_in_pre_r2_forest"])
        target_present = bool(record["target_orbit_present_in_pre_r2_forest"])
        try:
            expected = rr.geometry_failure_reason(source_present=source_present,
                                                  target_present=target_present)
        except AssertionError:
            failures.append("geometry record without opaque endpoint failure")
            continue
        if expected != record.get("primary_reason"):
            failures.append("geometry primary reason mismatch")
        flags = record.get("secondary_missing_endpoint_flags", {})
        if flags != {"source_missing": not source_present, "target_missing": not target_present}:
            failures.append("geometry secondary flags")
        if record["candidate_id"] in ids:
            failures.append("duplicate geometry candidate id")
        ids.add(record["candidate_id"])
        recounted[expected] += 1
    expected_counts = {name: int(recounted[name]) for name in rr.GEOMETRY_FAILURE_VOCABULARY}
    if geo.get("geometry_failure_counts") != expected_counts:
        failures.append("geometry category counts")
    if sum(recounted.values()) != int(geo.get("legacy_opaque_geometry_failure_count", -1)):
        failures.append("geometry partition total")
    if len(geo.get("records", [])) != int(geo.get("record_count", -1)):
        failures.append("geometry record count")

    component_ids = set()
    for row in comps.get("records", []):
        if row["candidate_id"] in component_ids:
            failures.append("duplicate component candidate id")
        component_ids.add(row["candidate_id"])
        source = row.get("r2_source_component")
        target = row.get("r2_target_component")
        if source is None or target is None or source.get("id") == target.get("id"):
            failures.append("not-same component witness")
        if row.get("exact_relation_checked") != (
                "pre-R2 incidence forest: component(q,R2.source) == component(q,R2.target)"):
            failures.append("component exact relation label")
    if len(component_ids) != int(comps.get("record_count", -1)):
        failures.append("component record count")
    if int(comps.get("expected_record_count", -1)) != int(comps.get("record_count", -2)):
        failures.append("component expected count")

    state_ids = set()
    for row in front.get("records", []):
        if row["stable_state_id"] in state_ids:
            failures.append("duplicate frontier state id")
        state_ids.add(row["stable_state_id"])
        item = checkpoint_rows.get((row.get("exact_state_hash"), row.get("decorated_key")))
        if item is None:
            failures.append("frontier state absent from source checkpoint")
            continue
        state = rr.exact.state_from_json(item["state"])
        dec = rr.Decoration.from_json(item["decoration"])
        if rr.state_hash(state) != row.get("exact_state_hash"):
            failures.append("frontier exact-state hash")
        if repr(rr.decorated_key(state, dec)) != row.get("decorated_key"):
            failures.append("frontier decorated key")
        canonical_key = rr.exact.canonicalize(state).stable_key()
        if repr(canonical_key) != row.get("canonical_key"):
            failures.append("frontier canonical key")
        if rr.sha256_bytes(repr(canonical_key).encode("utf-8")) != row.get("canonical_state_hash"):
            failures.append("frontier canonical state hash")
        recomputed = []
        for edge, collision in rr.iter_raw_macro_candidates(state):
            if collision is not None:
                recomputed.append({"label": None, "verdict": collision})
                continue
            assert edge is not None
            verdict, _child, recognition = rr.evaluate_edge(state, dec, edge,
                                                             prune_profile=rr.TARGET_A_SAFE_PROFILE)
            item = {"label": edge.label, "verdict": verdict}
            if recognition is not None:
                item["r2_outcome"] = recognition["r2_outcome"]
                item["geometry_failure_reason"] = recognition["geometry_failure_reason"]
            recomputed.append(item)
        if recomputed != row.get("next_edge_labels"):
            failures.append("frontier next-edge replay")
        labels = row.get("next_edge_labels", [])
        legal = sum(1 for edge in labels if edge.get("verdict") == "child")
        if legal != int(row.get("legal_successor_count", -1)):
            failures.append("frontier legal successor count")
        if int(row.get("r_count", -1)) not in (0, 1):
            failures.append("frontier invalid r count")
    if len(state_ids) != int(front.get("record_count", -1)) or len(state_ids) != 85:
        failures.append("frontier cardinality")

    # These two ledgers partition the exact historical R2 total.  They are
    # deliberately independent of the old generic parent name.
    if len(ids) + len(component_ids) != 49_440:
        failures.append("R2 total from detailed ledgers")
    result = {
        "schema": "rr-short-ell0-v3-taxonomy-independent-verifier-v1",
        "geometry_record_count": len(ids),
        "geometry_category_counts": expected_counts,
        "component_record_count": len(component_ids),
        "frontier_record_count": len(state_ids),
        "failures": sorted(set(failures)),
        "verified": not failures,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"verified={result['verified']} failures={len(result['failures'])}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
