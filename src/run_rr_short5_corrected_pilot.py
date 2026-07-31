#!/usr/bin/env python3
"""Run one bounded, checkpointed R1-complete short-root validation pilot.

This is intentionally *not* an exhaustion run.  Its positive node cap gives
the only permitted result class, ``INCOMPLETE``, unless a frontier happens to
empty naturally.  It validates R1 serialization, R2 terminal treatment, and
the v2 checkpoint firewall before any uncapped short-root traversal starts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs" / "rr_short5_corrected_pilot.json"
CHECKPOINT_DIR = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v2"


def load_short5():
    import importlib.util
    import sys

    path = ROOT / "src" / "search_rr_short5_exact.py"
    spec = importlib.util.spec_from_file_location("rr_short5_corrected_pilot_driver", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selection_table(short5) -> list[dict[str, object]]:
    rows = []
    for record in short5.short_root_records():
        state, decoration = short5.rr.initial_decoration(record)
        children = []
        r1_children = []
        for edge, collision in short5.rr.iter_raw_macro_candidates(state):
            if collision is not None or edge is None:
                continue
            verdict, child_decoration, _ = short5.rr.evaluate_edge(state, decoration, edge)
            if verdict == "child":
                assert child_decoration is not None
                children.append(edge.label)
                if child_decoration.r_count == 1:
                    r1_children.append(edge.label)
        rows.append({
            "root_id": record["root_id"],
            "legal_successor_count": len(children),
            "depth_1_frontier_estimate": len(children),
            "resource_margin": int(record["round37_envelope_margin"]),
            "R1_child_labels": r1_children,
        })
    rows.sort(key=lambda row: (int(row["legal_successor_count"]),
                               int(row["depth_1_frontier_estimate"]),
                               int(row["resource_margin"]), str(row["root_id"])))
    return rows


def checkpoint_summary(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    r_counts = [len(item["decoration"]["r_events"]) for item in raw["frontier"]]
    r1_decorations = [item["decoration"] for item in raw["frontier"]
                      if len(item["decoration"]["r_events"]) == 1]
    return {
        "path": str(path.relative_to(ROOT)),
        "schema": raw["schema"],
        "root_universe": raw["config"].get("root_universe"),
        "complete_frontier_snapshot": raw.get("complete_frontier_snapshot"),
        "frontier_size": len(raw["frontier"]),
        "r_count_histogram": {str(value): r_counts.count(value) for value in sorted(set(r_counts))},
        "r1_decorations": r1_decorations,
        "stats": raw["stats"],
        "checkpoint_lineage": raw["checkpoint_lineage"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-limit", type=int, default=250)
    parser.add_argument("--checkpoint-every", type=int, default=25)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.node_limit < 2:
        raise ValueError("the corrected pilot needs at least two expansions")
    if args.checkpoint_every < 1:
        raise ValueError("checkpoint interval must be positive")

    short5 = load_short5()
    records = short5.short_root_records()
    by_id = {str(record["root_id"]): record for record in records}
    table = selection_table(short5)
    selected_id = str(table[0]["root_id"])
    selected = by_id[selected_id]
    manifest = short5.short_root_manifest(records)
    extra = short5.config_extra(manifest)
    state_key_audit = short5.audit_short_state_key(records)
    if not state_key_audit["passed"] or state_key_audit["r1_states_examined"] < 1:
        raise RuntimeError("STATE_KEY_UNSOUND")

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    r1_seed = CHECKPOINT_DIR / f"{selected_id}_r1_seed.json"
    pilot_checkpoint = CHECKPOINT_DIR / f"{selected_id}_pilot.json"
    # One expansion creates the R1 child and then intentionally interrupts.
    seed = short5.rr.search_root(selected, node_limit=1, max_depth=None,
                                 checkpoint=r1_seed, checkpoint_every=1,
                                 checkpoint_config_extra=extra)
    seed_summary = checkpoint_summary(r1_seed)
    if seed["status"] != "INCOMPLETE" or not seed_summary["r1_decorations"]:
        raise AssertionError("R1 seed failed to serialize an R1 child")
    # This matching-config resume does not advance beyond the cap; it confirms
    # lossless load/write preservation of the stored R1 frontier.
    resumed_seed = short5.rr.search_root(selected, node_limit=1, max_depth=None,
                                         checkpoint=r1_seed, checkpoint_every=1,
                                         resume=r1_seed,
                                         checkpoint_config_extra=extra)
    resumed_seed_summary = checkpoint_summary(r1_seed)
    if resumed_seed_summary["r1_decorations"] != seed_summary["r1_decorations"]:
        raise AssertionError("R1 decoration changed across matching-config resume")

    result = short5.rr.search_root(selected, node_limit=args.node_limit, max_depth=None,
                                   checkpoint=pilot_checkpoint,
                                   checkpoint_every=args.checkpoint_every,
                                   checkpoint_config_extra=extra)
    pilot_summary = checkpoint_summary(pilot_checkpoint)
    if result["status"] != "INCOMPLETE":
        raise AssertionError("a cap-bounded pilot must be reported INCOMPLETE")
    if int(result["stats"]["R1_transitions"]) < 1:
        raise AssertionError("pilot did not enqueue an R1 transition")
    if int(result["stats"]["post_R1_nodes"]) < 1:
        raise AssertionError("pilot did not expand a post-R1 state")

    payload = {
        "schema": "rr-short5-corrected-pilot-v1",
        "classification": "INCOMPLETE",
        "scope": "bounded validation only; no short-root exhaustion claim",
        "selected_root": selected_id,
        "selection_rule": ["smallest legal successor count", "smallest depth-1 frontier estimate",
                           "lowest resource margin", "stable root id"],
        "selection_table": table,
        "short5_manifest": manifest,
        "state_key_audit": state_key_audit,
        "r1_seed": {"result": seed, "resume_result": resumed_seed, "checkpoint": resumed_seed_summary},
        "pilot": {"result": result, "checkpoint": pilot_summary},
    }
    short5.atomic_json(args.output, payload)
    print(json.dumps({"selected_root": selected_id, "status": result["status"],
                      "pre_R_nodes": result["stats"]["pre_R_nodes"],
                      "post_R1_nodes": result["stats"]["post_R1_nodes"],
                      "R1_transitions": result["stats"]["R1_transitions"],
                      "R2_candidate_edges": result["stats"]["R2_candidate_edges"],
                      "Target_A_hits": result["stats"]["Target_A_hits"]}, sort_keys=True))


if __name__ == "__main__":
    main()
