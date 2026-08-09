#!/usr/bin/env python3
"""Post-process the verified Round-58 first-component-Z3 search.

This script deliberately does not expand the search.  It consumes the frozen
parent-DAG checkpoints, the independent replay certificate, and the Round-57
backward ledgers.  In particular, it does not manufacture an exact MITM match
when the backward artifact contains only an abstract transition triple.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
RESULT = OUT / "rr_short_ell2_r1_37_first_component_z3_results.json"
VERIFIED = OUT / "rr_short_ell2_r1_37_component_change_verified.json"
MANIFEST = OUT / "rr_short_ell2_r1_37_first_component_z3_manifest.json"
DANGEROUS = OUT / "rr_short_ell2_r1_37_dangerous_entries.json"
BACKWARD = OUT / "rr_short_ell2_r1_37_backward_realizability.json"
MITM_OUT = OUT / "rr_short_ell2_r1_37_component_change_mitm.json"
STATS_OUT = OUT / "rr_short_ell2_r1_37_component_change_stats.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


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


def triple_id(edge: Mapping[str, object]) -> str:
    source = edge["source"]
    return f"{edge['joint']}|q{int(source[0]):03d}|p{int(source[1])}"


def top(counter: Counter, limit: int = 25) -> list[dict[str, object]]:
    return [{"key": str(key), "count": int(count)} for key, count in counter.most_common(limit)]


def merge_counter(target: Counter, rows: Iterable[Mapping[str, object]]) -> None:
    for row in rows:
        target.update({str(key): int(value) for key, value in row.items()})


def main() -> int:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    verified = json.loads(VERIFIED.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dangerous = json.loads(DANGEROUS.read_text(encoding="utf-8"))
    backward = json.loads(BACKWARD.read_text(encoding="utf-8"))
    if not verified.get("verified") or verified.get("stage") != "D":
        raise AssertionError("Stage-D independent replay certificate is required")
    if verified["aggregate"]["first_component_change_witnesses"] != 0:
        raise AssertionError("zero-event post-processor received a witness-bearing run")

    dangerous_by_triple: dict[str, list[dict[str, object]]] = {}
    for row in dangerous["direct_z3_entries"]:
        dangerous_by_triple.setdefault(str(row["triple_id"]), []).append(row)
    for row in dangerous["next_z2_entries"]:
        dangerous_by_triple.setdefault(str(row["preceding_z3_triple_id"]), []).append(row)
    r4_triples = {
        str(row["triple_id"]) for row in backward["entries"] if row["global_class"] == "R4"
    }

    global_counters: dict[str, Counter] = {
        name: Counter() for name in (
            "incoming_kind", "z3_joint", "z3_rotation_length", "z3_source_orbit",
            "z3_source_phase", "z3_target_orbit", "z3_target_phase", "z3_target_hexagon",
            "relative_depth", "absolute_depth", "dangerous_triple", "r4_triple",
        )
    }
    global_exact_state_hashes: set[str] = set()
    global_decorated_digests: set[str] = set()
    forward_dangerous_matches: dict[str, dict[str, object]] = {}
    branch_rows = []
    for branch in result["branches"]:
        checkpoint = ROOT / branch["checkpoint"]["path"]
        if sha256_file(checkpoint) != branch["checkpoint"]["sha256"]:
            raise AssertionError(f"checkpoint changed: {branch['seed_id']}")
        raw = json.loads(checkpoint.read_text(encoding="utf-8"))
        local = {name: Counter() for name in global_counters}
        incoming_z3 = 0
        for node in raw["nodes"]:
            global_exact_state_hashes.add(str(node["exact_state_hash"]))
            global_decorated_digests.add(str(node["decorated_state_sha256"]))
            local["relative_depth"][int(node["relative_depth"])] += 1
            local["absolute_depth"][int(node["depth"])] += 1
            edge = node.get("incoming_macro_edge")
            if not edge:
                continue
            kind = str(edge["kind"])
            local["incoming_kind"][kind] += 1
            if kind != "Z3":
                continue
            incoming_z3 += 1
            source, target = edge["source"], edge["target"]
            local["z3_joint"][str(edge["joint"])] += 1
            local["z3_rotation_length"][int(edge["rotation_length"])] += 1
            local["z3_source_orbit"][int(source[0])] += 1
            local["z3_source_phase"][int(source[1])] += 1
            local["z3_target_orbit"][int(target[0])] += 1
            local["z3_target_phase"][int(target[1])] += 1
            local["z3_target_hexagon"][int(edge["target_hexagon"])] += 1
            triple = triple_id(edge)
            if triple in dangerous_by_triple:
                local["dangerous_triple"][triple] += 1
                item = forward_dangerous_matches.setdefault(triple, {
                    "triple_id": triple,
                    "accepted_forward_occurrences": 0,
                    "forward_seed_ids": set(),
                    "round57_mechanisms": sorted({str(x["mechanism"]) for x in dangerous_by_triple[triple]}),
                    "round57_global_classes": sorted({
                        str(x["global_class"]) for x in backward["entries"] if x["triple_id"] == triple
                    }),
                })
                item["accepted_forward_occurrences"] += 1
                item["forward_seed_ids"].add(str(branch["seed_id"]))
            if triple in r4_triples:
                local["r4_triple"][triple] += 1
        for name, counter in local.items():
            global_counters[name].update(counter)
        branch_rows.append({
            "seed_id": branch["seed_id"],
            "status": branch["status"],
            "naturally_exhausted": branch["naturally_exhausted"],
            "expansions": branch["expansions"],
            "nodes": len(raw["nodes"]),
            "frontier": len(raw["frontier"]),
            "accepted_incoming_Z3_nodes": incoming_z3,
            "candidate_Z3_transitions_replayed": branch["Z3_transitions"],
            "R2_candidates": branch["R2_candidates"],
            "unique_exact_state_digests": branch["unique_exact_state_digests"],
            "max_depth": branch["max_depth"],
            "prune_histogram": branch["prune_histogram"],
            "top_Z3_target_orbits": top(local["z3_target_orbit"], 15),
            "top_Z3_target_hexagons": top(local["z3_target_hexagon"], 15),
            "dangerous_triple_occurrences": int(sum(local["dangerous_triple"].values())),
            "R4_triple_occurrences": int(sum(local["r4_triple"].values())),
            "checkpoint_sha256": branch["checkpoint"]["sha256"],
        })
        del raw

    for item in forward_dangerous_matches.values():
        item["forward_seed_ids"] = sorted(item["forward_seed_ids"])

    exhausted = [row for row in branch_rows if row["naturally_exhausted"]]
    capped = [row for row in branch_rows if not row["naturally_exhausted"]]
    def cohort(rows: list[dict[str, object]]) -> dict[str, object]:
        expansions = sum(int(row["expansions"]) for row in rows)
        return {
            "branch_count": len(rows),
            "seed_ids": [row["seed_id"] for row in rows],
            "expansions": expansions,
            "nodes": sum(int(row["nodes"]) for row in rows),
            "frontier": sum(int(row["frontier"]) for row in rows),
            "candidate_Z3_transitions": sum(int(row["candidate_Z3_transitions_replayed"]) for row in rows),
            "R2_candidates": sum(int(row["R2_candidates"]) for row in rows),
            "Z3_per_expansion": None if not expansions else round(
                sum(int(row["candidate_Z3_transitions_replayed"]) for row in rows) / expansions, 9
            ),
        }

    result_sha = sha256_file(RESULT)
    verification_sha = sha256_file(VERIFIED)
    common = {
        "stage": "D",
        "result_sha256": result_sha,
        "independent_verification_sha256": verification_sha,
        "manifest_sha256": sha256_file(MANIFEST),
        "dangerous_entries_sha256": sha256_file(DANGEROUS),
        "backward_realizability_sha256": sha256_file(BACKWARD),
        "analysis_script_sha256": sha256_file(Path(__file__)),
    }
    mitm = {
        "schema": "rr-short-ell2-r1-37-component-change-mitm-v1",
        **common,
        "forward_domain": {
            "start_states": result["start_state_count"],
            "replayed_nodes": verified["aggregate"]["nodes_replayed"],
            "expanded_nodes": verified["aggregate"]["expanded_nodes_replayed"],
            "frontier": verified["aggregate"]["frontier_replayed"],
        },
        "backward_domain": {
            "dangerous_transition_identities": dangerous["counts"]["total_mechanism_labelled_transition_identities"],
            "distinct_preceding_triples": dangerous["counts"]["unique_preceding_z3_triples"],
            "R3": backward["global_maximum_class_counts"]["R3"],
            "R4": backward["global_maximum_class_counts"]["R4"],
            "R5": backward["global_maximum_class_counts"]["R5"],
        },
        "intersection_ledger": {
            "M0_abstract_triple_matches": {
                "distinct_triples": len(forward_dangerous_matches),
                "forward_occurrences": sum(int(x["accepted_forward_occurrences"]) for x in forward_dangerous_matches.values()),
            },
            "M1_coarse_structural_matches": {
                "certified": 0,
                "not_decidable_from_round57_backward_artifact": len(forward_dangerous_matches),
                "reason": "Round-57 backward rows serialize abstract triples and predecessor conditions, not exact component partitions or decorations.",
            },
            "M2_exact_decorated_state_matches": {
                "certified": 0,
                "reason": "No Round-57 backward entry contains an exact decorated-state digest; zero is a certified-witness count, not a nonintersection theorem.",
            },
            "M3_exact_predecessor_chain_to_first_component_Z3": 0,
            "M4_exact_bridge_witness": 0,
        },
        "matched_abstract_triples": sorted(forward_dangerous_matches.values(), key=lambda row: row["triple_id"]),
        "key_sufficiency": {
            "exact_forward_decorated_digest": "collision-free identity within the serialized forward DAG; continuation-equivalence theorem not claimed",
            "round57_backward_exact_key_available": False,
            "conclusion": "The available backward artifact supports M0 only. M1/M2 need exact backward decorations and were not inferred.",
        },
        "status": "MITM_ABSTRACT_INTERSECTION_ONLY",
    }
    stats = {
        "schema": "rr-short-ell2-r1-37-component-change-stats-v2",
        **common,
        "scope": "verified Stage-D bounded exact region; two nonempty capped seed families remain",
        "theorem_level": "T1+",
        "aggregate": result["aggregate"],
        "reachable_state_count_units": {
            "serialized_parent_DAG_nodes": int(verified["aggregate"]["nodes_replayed"]),
            "per_seed_unique_decorated_digest_sum": int(result["aggregate"]["unique_exact_state_digest_sum"]),
            "global_unique_exact_state_hashes": len(global_exact_state_hashes),
            "global_unique_decorated_state_digests": len(global_decorated_digests),
            "note": "The first count retains provenance multiplicity; the global sets deduplicate identical hashes across all six seed families.",
        },
        "independent_replay": verified["aggregate"],
        "branches": branch_rows,
        "cohort_comparison": {"naturally_exhausted": cohort(exhausted), "capped": cohort(capped)},
        "accepted_transition_metadata": {
            "incoming_kind": dict(sorted(global_counters["incoming_kind"].items())),
            "Z3_joint": dict(sorted(global_counters["z3_joint"].items())),
            "Z3_rotation_length": {str(k): int(v) for k, v in sorted(global_counters["z3_rotation_length"].items())},
            "Z3_source_phase": {str(k): int(v) for k, v in sorted(global_counters["z3_source_phase"].items())},
            "Z3_target_phase": {str(k): int(v) for k, v in sorted(global_counters["z3_target_phase"].items())},
            "top_Z3_source_orbits": top(global_counters["z3_source_orbit"], 30),
            "top_Z3_target_orbits": top(global_counters["z3_target_orbit"], 30),
            "top_Z3_target_hexagons": top(global_counters["z3_target_hexagon"], 30),
            "dangerous_triple_forward_occurrences": int(sum(global_counters["dangerous_triple"].values())),
            "R4_triple_forward_occurrences": int(sum(global_counters["r4_triple"].values())),
        },
        "component_change": {
            "candidate_Z3_transitions_replayed": result["aggregate"]["Z3_transitions"],
            "FZ0": result["aggregate"]["FZ_counts"]["FZ0"],
            "FZ1": result["aggregate"]["FZ_counts"]["FZ1"],
            "FZ2": result["aggregate"]["FZ_counts"]["FZ2"],
            "FZ3": result["aggregate"]["FZ_counts"]["FZ3"],
            "FZ4": result["aggregate"]["FZ_counts"]["FZ4"],
            "FZ5": result["aggregate"]["FZ_counts"]["FZ5"],
            "FZ6": result["aggregate"]["FZ_counts"]["FZ6"],
        },
        "candidate_monotone_quantities": [
            {
                "name": "R1-target component node set",
                "observation": "unchanged across all 800,516 accepted Z3 transitions in the verified Stage-D region",
                "status": "bounded observation only; not a branch-wide invariant",
            },
            {
                "name": "frontier size",
                "observation": "not monotone (seed_12 and seed_13 exhibit collapse and regrowth before exhaustion)",
                "status": "counterexample to monotonicity in the measured run",
            },
        ],
        "hard_stop": {
            "stage": "D",
            "reason": "Stage E was optional. Two remaining families each retain about 34.7k frontier states; another 1,000,000 expansions plus full independent replay would materially exceed the verified Stage-D round budget.",
            "caps_are_not_certificates": True,
        },
        "status": "FIRST_COMPONENT_Z3_SEARCH_INCOMPLETE",
    }
    atomic_json(MITM_OUT, mitm)
    atomic_json(STATS_OUT, stats)
    print(json.dumps({
        "mitm_M0_distinct": mitm["intersection_ledger"]["M0_abstract_triple_matches"]["distinct_triples"],
        "mitm_M0_occurrences": mitm["intersection_ledger"]["M0_abstract_triple_matches"]["forward_occurrences"],
        "FZ1_plus": sum(int(result["aggregate"]["FZ_counts"][f"FZ{i}"]) for i in range(1, 7)),
        "exhausted_branches": len(exhausted),
        "capped_branches": len(capped),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
