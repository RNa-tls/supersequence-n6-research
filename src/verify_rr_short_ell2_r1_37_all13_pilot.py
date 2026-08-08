#!/usr/bin/env python3
"""Independent replay verifier for the Round-56 all-13 pilot.

This verifier does not trust the runner's aggregate counters.  For every
checkpoint it reconstructs every stored child from its parent, re-enumerates
all legal outgoing macro edges of every expanded node, and compares the exact
child and R2 transcripts with the stored records.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
RUNNER_PATH = ROOT / "src" / "search_rr_short_ell2_r1_37_all13_pilot.py"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_pilot_results.json"
BRIDGE = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_bridge_ledger.json"
OUTPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_all13_verified.json"


def load_module(name: str, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


run = load_module("rr_all13_runner_for_verification", RUNNER_PATH)
rr, exact, pilot, v7 = run.rr, run.exact, run.pilot, run.v7


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def edge_signature(data: Mapping[str, object]) -> str:
    return sha256_json(data)


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def replay_checkpoint(summary: Mapping[str, object]) -> dict[str, object]:
    state_id = str(summary["state_id"])
    path = ROOT / str(summary["checkpoint"]["path"])
    assert_equal(sha256_file(path), summary["checkpoint"]["sha256"], f"{state_id} checkpoint SHA")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert_equal(raw.get("schema"), run.CHECKPOINT_SCHEMA, f"{state_id} schema")
    assert raw.get("complete_frontier_snapshot") is True
    assert_equal(raw["state_plan"]["state_id"], state_id, f"{state_id} plan identity")
    assert_equal(raw["provenance"]["recognizer_semantics"], run.R2_SEMANTICS, "R2 semantics")
    assert_equal(raw["provenance"]["prune_profile"], rr.TARGET_A_SAFE_PROFILE, "prune profile")
    assert raw["provenance"]["budget_transfer"] is False
    assert_equal(int(raw["provenance"]["additional_cap"]), 10_000, "independent cap")

    root_state = exact.state_from_json(raw["starting_state"])
    root_dec = rr.Decoration.from_json(raw["starting_decoration"])
    assert_equal(rr.state_hash(root_state), raw["state_plan"]["exact_state_hash"], "root state hash")
    assert root_state.F == 1 and root_state.H == 0 and root_state.Ndef == 1 and root_dec.r_count == 1

    node_rows = list(raw["nodes"])
    nodes_by_id = {str(row["node_id"]): row for row in node_rows}
    assert_equal(len(nodes_by_id), len(node_rows), f"{state_id} unique node ids")
    state_by_id: dict[str, Any] = {}
    dec_by_id: dict[str, Any] = {}
    path_by_id: dict[str, str] = {}
    child_edges: dict[str, list[str]] = defaultdict(list)
    roots = []

    for row in node_rows:
        node_id = str(row["node_id"])
        parent_id = row["parent_id"]
        if parent_id is None:
            roots.append(node_id)
            state, dec = root_state, root_dec
            expected_path = sha256_json({
                "parent_replay_hash": raw["state_plan"]["parent_replay_hash"],
                "starting_state_hash": raw["state_plan"]["exact_state_hash"],
            })
            assert row["incoming_macro_edge"] is None
        else:
            parent_id = str(parent_id)
            if parent_id not in state_by_id:
                raise AssertionError(f"{state_id}: parent appears after child: {node_id}")
            edge = run.edge_from_json(state_by_id[parent_id], row["incoming_macro_edge"])
            verdict, after_dec, recognition = rr.evaluate_edge(
                state_by_id[parent_id], dec_by_id[parent_id], edge,
                prune_profile=rr.TARGET_A_SAFE_PROFILE,
            )
            assert_equal(verdict, "child", f"{node_id} incoming verdict")
            assert after_dec is not None and recognition is None and pilot.edge_kind(edge) != "R"
            state, dec = edge.state, after_dec
            expected_path = sha256_json({
                "parent_path_hash": path_by_id[parent_id],
                "edge": row["incoming_macro_edge"],
            })
            child_edges[parent_id].append(edge_signature(row["incoming_macro_edge"]))
        assert_equal(rr.state_hash(state), row["exact_state_hash"], f"{node_id} state hash")
        assert_equal(dec.to_json(), row["decoration"], f"{node_id} decoration")
        assert_equal(expected_path, row["path_hash"], f"{node_id} replay hash")
        state_by_id[node_id], dec_by_id[node_id], path_by_id[node_id] = state, dec, expected_path
    assert_equal(len(roots), 1, f"{state_id} root count")

    frontier_ids = {str(row["node_id"]) for row in raw["frontier"]}
    assert frontier_ids <= nodes_by_id.keys()
    for row in raw["frontier"]:
        node_id = str(row["node_id"])
        assert_equal(rr.state_hash(exact.state_from_json(row["state"])), nodes_by_id[node_id]["exact_state_hash"], "frontier state")
        assert_equal(row["decoration"], nodes_by_id[node_id]["decoration"], "frontier decoration")
        assert_equal(row["path_hash"], nodes_by_id[node_id]["path_hash"], "frontier path hash")
    expanded_ids = [node_id for node_id in nodes_by_id if node_id not in frontier_ids]
    assert_equal(len(expanded_ids), int(raw["stats"]["expanded"]), f"{state_id} expanded-node identity")

    stored_r2: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for record in raw["r2_records"]:
        stored_r2[str(record["predecessor_node_id"])].append(record)

    recomputed = Counter(expanded=0, generated_edges=0)
    recomputed.update({level: 0 for level in run.B_LEVELS})
    recomputed_bridges: list[Mapping[str, object]] = []
    target_a_records = 0
    target_b_records = 0

    for node_id in expanded_ids:
        state, dec = state_by_id[node_id], dec_by_id[node_id]
        expected_children: list[str] = []
        expected_r2: list[tuple[str, Mapping[str, object], Any, Any]] = []
        recomputed["expanded"] += 1
        for edge, collision in rr.iter_raw_macro_candidates(state):
            recomputed["generated_edges"] += 1
            if collision is not None or edge is None:
                recomputed[f"prune:{collision or 'missing_edge'}"] += 1
                continue
            verdict, after_dec, recognition = rr.evaluate_edge(
                state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE
            )
            kind = pilot.edge_kind(edge)
            if kind == "R":
                assert after_dec is not None and recognition is not None and after_dec.r_count == 2
                expected_r2.append((edge_signature(rr.edge_json(edge)), recognition, edge, after_dec))
                timing = "immediate" if int(nodes_by_id[node_id]["relative_depth"]) == 0 else "later"
                recomputed[f"R2:{timing}:total"] += 1
                recomputed[f"R2:{timing}:outcome:{recognition['r2_outcome']}"] += 1
                if recognition["is_target_a"]:
                    target_a_records += 1
                continue
            if verdict != "child":
                recomputed[f"prune:{verdict}"] += 1
                continue
            assert after_dec is not None and after_dec.r_count == 1
            signature = edge_signature(rr.edge_json(edge))
            expected_children.append(signature)
            recomputed[f"accepted:{kind}"] += 1
            merge = run.component_merge(state, dec, edge.state, after_dec)
            if merge:
                witness = v7.bridge_record(state, dec, edge, edge.state, after_dec,
                                           child_id="verify", parent_id=node_id)
                assert witness is not None
                level = "B2"
                if witness["future_R2_source_admissible"]:
                    level = "B3"
                if level == "B3" and witness["terminal_geometry_available"]:
                    level = "B4"
                recomputed[level] += 1
                recomputed["component_merge"] += 1
                recomputed["bridge_template"] += int(bool(witness["template_match"]))
                recomputed_bridges.append(witness)
            else:
                recomputed["B0"] += 1
        assert_equal(sorted(expected_children), sorted(child_edges.get(node_id, [])), f"{node_id} exact children")

        actual_r2 = stored_r2.get(node_id, [])
        assert_equal(len(actual_r2), len(expected_r2), f"{node_id} R2 count")
        expected_by_sig = {item[0]: item for item in expected_r2}
        assert_equal(len(expected_by_sig), len(expected_r2), f"{node_id} unique R2 labels")
        for record in actual_r2:
            signature = edge_signature(record["edge"])
            if signature not in expected_by_sig:
                raise AssertionError(f"{node_id}: unrecognized stored R2 edge")
            _, recognition, edge, after_dec = expected_by_sig[signature]
            assert_equal(record["recognizer"], recognition, f"{node_id} R2 recognition")
            assert_equal(record["literal_joint_source_state_hash"], rr.state_hash(edge.run.state), "literal joint source")
            assert_equal(record["post_R2_state_hash"], rr.state_hash(edge.state), "R2 target")
            assert_equal(record["decoration_after"], after_dec.to_json(), "R2 decoration")
            assert_equal(bool(record["literal_Target_A"]), bool(recognition["is_target_a"]), "Target A bit")
            if recognition["is_target_a"]:
                independent_tb = run.target_b_analysis(edge.state)
                assert_equal(record["target_b"], independent_tb, "helper-free Target B replay")
                target_b_records += int(bool(independent_tb["target_b_survivor"]))
                recomputed["literal_Target_A"] += 1
                level = "B6" if independent_tb["target_b_survivor"] else "B5"
                recomputed[level] += 1
                recomputed["Target_B_survivor"] += int(level == "B6")

    # The runner's statistics contain timing and checkpoint metadata in addition
    # to proof counters.  Compare every proof counter reconstructed above.
    stored_stats = Counter(raw["stats"])
    for key, value in recomputed.items():
        assert_equal(int(stored_stats[key]), int(value), f"{state_id} counter {key}")
    assert_equal(len(raw["r2_records"]), sum(int(recomputed[k]) for k in recomputed if k.endswith(":total")), "R2 ledger total")
    assert_equal(len(raw["bridge_records"]), int(recomputed["component_merge"]), "bridge ledger total")
    assert_equal(target_a_records, int(stored_stats["literal_Target_A"]), "Target A count")
    assert_equal(target_b_records, int(stored_stats["Target_B_survivor"]), "Target B count")
    assert_equal(len(nodes_by_id), int(summary["node_count"]), "summary node count")
    assert_equal(len(frontier_ids), int(summary["frontier_size"]), "summary frontier")
    assert_equal(not frontier_ids, bool(summary["naturally_exhausted"]), "exhaustion status")
    if frontier_ids:
        assert int(summary["expansions"]) == 10_000
        assert_equal(summary["status"], "INCOMPLETE", "capped status")

    result = {
        "state_id": state_id,
        "checkpoint_sha256": sha256_file(path),
        "nodes": len(nodes_by_id),
        "expanded": len(expanded_ids),
        "frontier": len(frontier_ids),
        "r2_records": len(raw["r2_records"]),
        "component_merges": int(recomputed["component_merge"]),
        "literal_Target_A": target_a_records,
        "Target_B_survivors": target_b_records,
        "status": summary["status"],
        "exact_successor_replay": "PASS",
    }
    del raw, state_by_id, dec_by_id, path_by_id, nodes_by_id
    gc.collect()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--bridge", type=Path, default=BRIDGE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    bridge = json.loads(args.bridge.read_text(encoding="utf-8"))
    assert_equal(result["schema"], run.RESULT_SCHEMA, "result schema")
    assert_equal(bridge["schema"], run.BRIDGE_SCHEMA, "bridge schema")
    assert_equal(result["planned_state_count"], 13, "planned state count")
    assert_equal(result["completed_state_records"], 13, "completed state count")
    assert result["budget_transfer"] is False
    assert_equal(result["total_maximum_expansions"], 130_000, "total cap")

    verified = [replay_checkpoint(row) for row in result["branches"]]
    assert_equal(len({row["state_id"] for row in verified}), 13, "unique verified states")
    aggregates = {
        "expansions": sum(row["expanded"] for row in verified),
        "frontier_size": sum(row["frontier"] for row in verified),
        "component_merges": sum(row["component_merges"] for row in verified),
        "literal_Target_A": sum(row["literal_Target_A"] for row in verified),
        "Target_B_survivors": sum(row["Target_B_survivors"] for row in verified),
    }
    for key, value in aggregates.items():
        assert_equal(int(result["aggregate"][key]), value, f"aggregate {key}")
    assert_equal(bridge["aggregate"], result["aggregate"], "bridge/result aggregate")

    payload = {
        "schema": "rr-short-ell2-r1-37-all13-independent-verification-v1",
        "verified": True,
        "verification_scope": "all stored incoming edges plus exact outgoing-edge replay of every expanded node",
        "result_sha256": sha256_file(args.result),
        "bridge_ledger_sha256": sha256_file(args.bridge),
        "verifier_sha256": sha256_file(Path(__file__)),
        "runner_sha256": sha256_file(RUNNER_PATH),
        "branches": verified,
        "aggregate": aggregates,
        "overall_status": result["overall_status"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verified": True, "overall_status": result["overall_status"], **aggregates}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
