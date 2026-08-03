#!/usr/bin/env python3
"""Independent ledger verifier for the completed Round-52 top-eight corpus.

It is intentionally read-only with respect to the v6 checkpoints.  The full
literal replay is performed by ``analyze_rr_short5_top8_completed.py``; this
separate verifier independently rebuilds all count ledgers from the eight
atomic payloads and rejects an analysis whose asserted replay coverage or
bridge accounting is incomplete.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
V6 = ROOT / "outputs" / "rr_short5_top8_continuation.json"
ANALYSIS = ROOT / "outputs" / "rr_short5_top8_continuation_analysis.json"
REGISTRATION = ROOT / "outputs" / "rr_short5_top8_registration_events.json"
HIERARCHY = ROOT / "outputs" / "rr_short5_top8_success_hierarchy.json"
OUT = ROOT / "outputs" / "rr_short5_top8_continuation_verified.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    v6 = json.loads(V6.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    hierarchy = json.loads(HIERARCHY.read_text(encoding="utf-8"))
    if analysis["input"]["v6_result_sha256"] != sha256_file(V6):
        raise AssertionError("analysis was not derived from this v6 index")
    by_id = {str(row["child_id"]): row for row in v6["children"]}
    if len(by_id) != 8 or len(analysis["branches"]) != 8:
        raise AssertionError("top8 branch cardinality mismatch")
    endpoints, repair_types, hierarchy_levels, failures, r2_outcomes = (Counter(), Counter(), Counter(), Counter(), Counter())
    repairs = r2_paths = target_a = component_merges = 0
    per_branch = []
    for row in analysis["branches"]:
        branch_id = str(row["child_id"])
        result = by_id[branch_id]["continuation_result"]
        checkpoint = ROOT / result["checkpoint"]["path"]
        raw = json.loads(checkpoint.read_text(encoding="utf-8"))
        if row["checkpoint"]["sha256"] != sha256_file(checkpoint):
            raise AssertionError(f"checkpoint SHA mismatch: {branch_id}")
        expected_endpoint = "NATURALLY_EXHAUSTED" if not raw["frontier"] else "CAP_REACHED_NONEMPTY_FRONTIER"
        if row["endpoint"] != expected_endpoint or row["expanded"] != raw["stats"]["expanded"]:
            raise AssertionError(f"endpoint ledger mismatch: {branch_id}")
        raw_repairs, raw_r2 = raw["repair_events"], raw["r2_paths"]
        if row["repair_events"]["total"] != len(raw_repairs) or row["r2"]["total"] != len(raw_r2):
            raise AssertionError(f"event-count mismatch: {branch_id}")
        if row["repair_events"]["literal_replayed"] != len(raw_repairs) or row["r2"]["literal_replayed"] != len(raw_r2):
            raise AssertionError(f"literal replay coverage mismatch: {branch_id}")
        local_types = Counter(str(event["repair_type"]) for event in raw_repairs)
        if set(local_types) - {"Z2", "Z3_fresh"}:
            raise AssertionError(f"invalid repair alphabet: {branch_id}")
        if local_types != Counter(row["repair_events"]["types"]):
            raise AssertionError(f"repair-type ledger mismatch: {branch_id}")
        local_merges = sum(bool(event["component_merge"]) for event in raw_repairs)
        if local_merges != row["repair_events"]["component_merges"]:
            raise AssertionError(f"component-merge ledger mismatch: {branch_id}")
        if row["repair_events"]["bridge_template_matches"] > local_merges:
            raise AssertionError(f"bridge cannot exceed component merges: {branch_id}")
        # Stored path metadata is only an auxiliary hierarchy ledger. Its
        # source-sensitive semantic truth is separately guaranteed by the
        # analyser's literal replay coverage assertion above.
        local_levels = Counter(str(path.get("maximum_level")) for path in raw_r2 if "maximum_level" in path)
        local_failures = Counter(str(path.get("failure_reason")) for path in raw_r2 if "failure_reason" in path)
        if local_levels != Counter(row["r2"]["hierarchy_maximum_levels"]):
            raise AssertionError(f"hierarchy-level ledger mismatch: {branch_id}")
        if local_failures != Counter(row["r2"]["hierarchy_failures"]):
            raise AssertionError(f"hierarchy-failure ledger mismatch: {branch_id}")
        local_hits = sum(bool(path.get("literal_Target_A")) for path in raw_r2)
        if local_hits != len(row["r2"]["target_a_hits"]):
            raise AssertionError(f"Target-A ledger mismatch: {branch_id}")
        endpoints[expected_endpoint] += 1; repair_types.update(local_types); hierarchy_levels.update(local_levels)
        failures.update(local_failures); repairs += len(raw_repairs); r2_paths += len(raw_r2); target_a += local_hits; component_merges += local_merges
        per_branch.append({"child_id": branch_id, "checkpoint_sha256": sha256_file(checkpoint), "endpoint": expected_endpoint,
                           "repair_events": len(raw_repairs), "r2_paths": len(raw_r2), "component_merges": local_merges})
    aggregate = analysis["aggregate"]
    if dict(sorted(endpoints.items())) != aggregate["branch_endpoints"]:
        raise AssertionError("endpoint aggregate mismatch")
    if repairs != aggregate["repair_events"] or r2_paths != aggregate["r2_paths"] or target_a != aggregate["literal_target_a_hits"]:
        raise AssertionError("aggregate count mismatch")
    if dict(sorted(hierarchy_levels.items())) != aggregate["success_hierarchy"] or dict(sorted(failures.items())) != aggregate["repair_failure_taxonomy"]:
        raise AssertionError("aggregate hierarchy mismatch")
    if aggregate["bridge_template_matches"] != len(registration["bridge_records"]):
        raise AssertionError("bridge export count mismatch")
    if registration["all_legal_repairs_replayed"] != repairs or hierarchy["r2_paths_replayed"] != r2_paths:
        raise AssertionError("replay coverage aggregate mismatch")
    if hierarchy["literal_target_a_hits"] != target_a or hierarchy["target_b_survivors"]:
        raise AssertionError("Target-A/B ledger mismatch")
    if component_merges != 0 or registration["records"] or registration["bridge_records"]:
        raise AssertionError("unexpected registration/bridge evidence requires fresh review")
    payload = {"schema": "rr-short5-top8-continuation-verifier-v1", "passed": True,
               "scope": "completed v6 corpus; two capped frontiers remain INCOMPLETE", "input_sha256": sha256_file(V6),
               "aggregate": {"endpoints": dict(sorted(endpoints.items())), "repair_events": repairs, "r2_paths": r2_paths,
                             "component_merges": component_merges, "literal_target_a_hits": target_a,
                             "bridge_template_matches": len(registration["bridge_records"])}, "branches": per_branch}
    atomic_json(OUT, payload)
    print(json.dumps({"passed": True, **payload["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
