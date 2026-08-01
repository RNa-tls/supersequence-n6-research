#!/usr/bin/env python3
"""Round 43: deterministic, non-resuming taxonomy replay of `short_ell0`.

The prior medium checkpoint is read only.  This script runs both the frozen
Round-42 engine and the instrumented engine from the literal short root through
the same 100,250-node prefix, then compares an expansion-order transcript,
the complete serialized frontier, and the memo set.  It never writes or
resumes the 374 MiB checkpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
ROUND42 = "785ddab"
CHECKPOINT = ROOT / "outputs" / "checkpoints" / "rr_short5" / "r1_complete_v3" / "short_ell0_medium.json"
ROUND42_OUTPUT = ROOT / "outputs" / "rr_short_ell0_medium_v3.json"
GEOMETRY = ROOT / "outputs" / "rr_short_ell0_v3_geometry_failures.json"
FRONTIER = ROOT / "outputs" / "rr_short_ell0_v3_frontier_export.json"
COMPONENTS = ROOT / "outputs" / "rr_short_ell0_v3_component_failures.json"
REPORT = ROOT / "research" / "RR_SHORT_ELL0_V3_FAILURE_TAXONOMY_CODEX.md"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_frozen_round42():
    completed = subprocess.run(
        ["git", "show", f"{ROUND42}:src/search_rr_target_a_exhaustive.py"],
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    module = type(sys)("rr_short_ell0_round42_frozen")
    module.__file__ = str(ROOT / "src" / "search_rr_target_a_exhaustive.py")
    sys.modules[module.__name__] = module
    exec(compile(completed.stdout, module.__file__, "exec"), module.__dict__)
    return module


def projection(stats: Mapping[str, object]) -> dict[str, object]:
    """Traversal counters unaffected by additive diagnostic capture."""
    fields = (
        "expanded", "generated_edges", "memo_hits", "prunes", "CH1_nodes", "CH2_nodes",
        "undecided_nodes", "other_nodes", "branch_transitions", "max_macro_depth",
        "pre_R_nodes", "post_R1_nodes", "R1_transitions", "R2_candidate_edges",
        "Target_A_hits", "pre_R_prunes", "post_R1_prunes", "max_post_R1_depth",
        "unique_r1_decorated_keys", "R2_outcomes",
    )
    return {field: stats.get(field) for field in fields}


def observed_run(engine, record: Mapping[str, object], extra: Mapping[str, object], *, capture: bool) -> dict[str, object]:
    """Run an engine once while committing the exact expansion-state sequence."""
    original = engine.iter_raw_macro_candidates
    digest = hashlib.sha256()
    count = 0

    def observed(state):
        nonlocal count
        digest.update(f"{count}:{engine.state_hash(state)}\n".encode("ascii"))
        count += 1
        yield from original(state)

    engine.iter_raw_macro_candidates = observed
    try:
        result = engine.search_root(
            record, node_limit=100_250, checkpoint=None,
            checkpoint_config_extra=extra,
            prune_profile=engine.TARGET_A_SAFE_PROFILE,
            **({"capture_r2_diagnostics": True, "capture_frontier_snapshot": True} if capture else {}),
        )
    finally:
        engine.iter_raw_macro_candidates = original
    if count != int(result["stats"]["expanded"]):
        raise AssertionError("expansion transcript callback did not see every expanded state")
    return {"result": result, "expansion_trace_hash": digest.hexdigest(), "expansion_count": count}


def hist(rows: list[Mapping[str, object]]) -> dict[str, dict[str, int]]:
    """Machine-readable deterministic histograms for the 5,419 rows."""
    def tally(key):
        out: Counter[str] = Counter()
        for row in rows:
            out[key(row)] += 1
        return dict(sorted(out.items()))

    return {
        "r1_target_component_id": tally(lambda row: "ABSENT" if row["r1_target_component"] is None
                                          else str(row["r1_target_component"]["id"])),
        "r2_source_component_id": tally(lambda row: str(row["r2_source_component"]["id"])),
        "r2_target_component_id": tally(lambda row: str(row["r2_target_component"]["id"])),
        "component_count_pre_r2": tally(lambda row: str(row["component_count_pre_r2"])),
        "candidate_edge_would_merge_components": tally(lambda row: str(bool(row["candidate_edge_would_merge_components"]))),
        "r1_target_vs_r2_source": tally(
            lambda row: "R1_TARGET_ABSENT" if row["r1_target_component"] is None
            else ("SAME" if row["r1_target_component"]["id"] == row["r2_source_component"]["id"]
                  else "DIFFERENT")),
        "r2_source_component_class": tally(
            lambda row: json.dumps(row["r2_source_component"]["class"], sort_keys=True)),
        "r2_target_component_class": tally(
            lambda row: json.dumps(row["r2_target_component"]["class"], sort_keys=True)),
    }


def frontier_records(rr, checkpoint: Mapping[str, object], snapshot: list[Mapping[str, object]]) -> list[dict[str, object]]:
    if checkpoint["frontier"] != snapshot:
        raise AssertionError("enhanced replay frontier differs from saved Round-42 checkpoint")
    parent_hash = checkpoint["checkpoint_lineage"][-1] if checkpoint["checkpoint_lineage"] else None
    rows = []
    for item in snapshot:
        state = rr.exact.state_from_json(item["state"])
        dec = rr.Decoration.from_json(item["decoration"])
        next_edges = []
        legal = 0
        for edge, collision in rr.iter_raw_macro_candidates(state):
            if collision is not None:
                next_edges.append({"label": None, "verdict": collision})
                continue
            assert edge is not None
            verdict, _child, recognition = rr.evaluate_edge(state, dec, edge,
                                                             prune_profile=rr.TARGET_A_SAFE_PROFILE)
            if verdict == "child":
                legal += 1
            entry: dict[str, object] = {"label": edge.label, "verdict": verdict}
            if recognition is not None:
                entry["r2_outcome"] = recognition["r2_outcome"]
                entry["geometry_failure_reason"] = recognition["geometry_failure_reason"]
            next_edges.append(entry)
        mask = rr.hub_mask(state, dec)
        canonical_key = rr.exact.canonicalize(state).stable_key()
        raw_key = rr.decorated_key(state, dec)
        state_id = sha256_bytes(repr((rr.state_hash(state), raw_key)).encode("utf-8"))
        summary = rr.component_summary(state)
        rows.append({
            "stable_state_id": state_id,
            # 85 literal states are exported for independent replay.  This is
            # intentionally a small diagnostic frontier, not the 374 MiB
            # checkpoint or its complete memo set.
            "exact_state": rr.exact.state_to_json(state),
            "exact_state_hash": rr.state_hash(state),
            "canonical_state_hash": rr.sha256_bytes(repr(canonical_key).encode("utf-8")),
            "canonical_key": repr(canonical_key),
            "decorated_key": repr(raw_key),
            "decoration": dec.to_json(),
            "depth": item["depth"], "r_count": dec.r_count,
            "r1_metadata": None if dec.r1 is None else asdict(dec.r1),
            "P": state.P, "O": state.O, "F": state.F, "H": state.H,
            "Ndef": state.Ndef, "Phi": rr.phi(state), "M": state.P - 5 * state.O,
            "hub": {"id": dec.hub_id, "mask": mask, "popcount": mask.bit_count(),
                    "status": "COMPLETE" if mask == 0b111111 else ("UNTOUCHED" if mask == 0 else "PARTIAL")},
            "completer_metadata": None if dec.completer is None else asdict(dec.completer),
            "component_summary": {"component_count": summary["component_count"],
                                  "components": summary["components"]},
            "legal_successor_count": legal,
            "next_edge_labels": next_edges,
            "checkpoint_parent_hash": parent_hash,
        })
    return rows


def write_report(geometry: Mapping[str, object], frontier: Mapping[str, object], components: Mapping[str, object]) -> None:
    counts = geometry["geometry_failure_counts"]
    compare = geometry["replay_equivalence"]
    lines = [
        "# Round 43: `short_ell0` v3 R2 geometry-failure taxonomy",
        "",
        "Status: **bounded deterministic replay only**.  This did not resume or modify the medium search checkpoint.",
        "",
        "## Replay equivalence",
        "",
        f"- Frozen `785ddab` and instrumented engines expanded the same {compare['expanded']} states.",
        f"- Expansion transcript hash equal: `{compare['same_expansion_sequence']}`.",
        f"- Serialized 85-state frontier equal: `{compare['same_frontier']}`.",
        f"- Seen decorated-key set equal: `{compare['same_seen_key_set']}`.",
        f"- R1/R2/Target-A counters: `{compare['r1_transitions']}` / `{compare['r2_candidates']}` / `{compare['target_a_hits']}`.",
        "",
        "## Opaque geometry exit refined",
        "",
        f"The historical parent count is {geometry['legacy_opaque_geometry_failure_count']}.  Its exact child partition follows.",
        "",
        "| deterministic geometry child | count |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {counts[name]} |" for name in geometry["taxonomy_order"])
    lines += [
        "",
        "The primary label is deterministic: a missing R2 source orbit takes priority if both endpoints are absent; the serialized secondary flags retain that overlap.  No catch-all geometry category is emitted: an unclassifiable old opaque exit raises an assertion.",
        "",
        "The active Target-A geometry predicate is exactly the pre-R2 incidence-component relation.  The retained zero labels (`no_completer`, completer/event-order/chaining/hub/terminal labels, and `other_asserted_reason`) are explicit audit slots, not newly introduced Target-A rejection predicates.  The literal R2 records retain completer and event-order fields so a later separately specified normal form can be tested without re-running the prefix.",
        "",
        "## Same-component rejection evidence",
        "",
        f"There are {components['record_count']} `not_same_component` rows.  Each exports the pre-R2 relation `component(q,R2.source) == component(q,R2.target)`, both component IDs/classes, and the counterfactual post-edge merge result.",
        "",
        "## Frontier",
        "",
        f"The frontier export contains {frontier['record_count']} states, not the 374 MiB checkpoint.  It has exact state/decorated keys, R1/completer history, coordinates, component summary, and independently recomputed next-edge labels.",
        "",
        "## Scope",
        "",
        "These are diagnostics for the fixed 100,250-expansion Target-A-safe prefix.  They neither exhaust `short_ell0` nor assert a Target-B or NR6 conclusion.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def child(mode: str, output: Path) -> None:
    short5 = load_path(f"rr_taxonomy_short5_{mode}", ROOT / "src" / "search_rr_short5_exact.py")
    rr = load_frozen_round42() if mode == "baseline" else short5.rr
    records = short5.short_root_records()
    record = next(row for row in records if row["root_id"] == "short_ell0")
    extra = short5.config_extra(short5.short_root_manifest(records))
    observed = observed_run(rr, record, extra, capture=(mode == "instrumented"))
    atomic_json(output, observed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=("baseline", "instrumented"))
    parser.add_argument("--child-output", type=Path)
    args = parser.parse_args()
    if args.child:
        if args.child_output is None:
            raise ValueError("--child-output required for child mode")
        child(args.child, args.child_output)
        return
    if not CHECKPOINT.exists() or not ROUND42_OUTPUT.exists():
        raise FileNotFoundError("saved Round-42 checkpoint/output required for taxonomy replay")

    with tempfile.TemporaryDirectory(prefix="rr-taxonomy-") as directory:
        folder = Path(directory)
        baseline_path = folder / "baseline.json"
        enhanced_path = folder / "enhanced.json"
        for mode, destination in (("baseline", baseline_path), ("instrumented", enhanced_path)):
            completed = subprocess.run(
                [PYTHON, str(Path(__file__).resolve()), "--child", mode, "--child-output", str(destination)],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            if completed.returncode:
                raise RuntimeError(f"{mode} replay failed:\nSTDOUT\n{completed.stdout}\nSTDERR\n{completed.stderr}")
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        enhanced = json.loads(enhanced_path.read_text(encoding="utf-8"))

    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    historical = json.loads(ROUND42_OUTPUT.read_text(encoding="utf-8"))
    result = enhanced["result"]
    stats = result["stats"]
    snap = result.pop("diagnostic_frontier_snapshot")
    replay_equivalence = {
        "frozen_commit": ROUND42,
        "expanded": int(stats["expanded"]),
        "baseline_expansion_trace_hash": baseline["expansion_trace_hash"],
        "instrumented_expansion_trace_hash": enhanced["expansion_trace_hash"],
        "same_expansion_sequence": baseline["expansion_trace_hash"] == enhanced["expansion_trace_hash"],
        "same_semantic_stats": projection(baseline["result"]["stats"]) == projection(stats),
        "same_historical_stats": projection(historical["result"]["stats"]) == projection(stats),
        "same_frontier": checkpoint["frontier"] == snap,
        "same_seen_key_set": (
            result["diagnostic_seen_key_hash"] == sha256_bytes(
                "\n".join(sorted(checkpoint["seen_keys"])).encode("utf-8"))),
        "saved_frontier_hash": sha256_bytes(json.dumps(checkpoint["frontier"], sort_keys=True).encode("utf-8")),
        "replayed_frontier_hash": result["diagnostic_frontier_hash"],
        "r1_transitions": int(stats["R1_transitions"]),
        "r2_candidates": int(stats["R2_candidate_edges"]),
        "target_a_hits": int(stats["Target_A_hits"]),
    }
    if not all(replay_equivalence[key] for key in (
            "same_expansion_sequence", "same_semantic_stats", "same_historical_stats",
            "same_frontier", "same_seen_key_set")):
        raise AssertionError(f"v3 replay mismatch: {replay_equivalence}")

    rr = load_path("rr_taxonomy_export_engine", ROOT / "src" / "search_rr_target_a_exhaustive.py")
    geo_records = stats["geometry_failure_records"]
    component_rows = stats["same_component_failure_records"]
    geometry_payload = {
        "schema": "rr-short-ell0-v3-geometry-failure-taxonomy-v1",
        "scope": "deterministic 100250-expansion short_ell0 Target-A-safe replay; diagnostic only",
        "engine_sha256": sha256_file(ROOT / "src" / "search_rr_target_a_exhaustive.py"),
        "checkpoint_read_only": {"path": str(CHECKPOINT.relative_to(ROOT)), "sha256": sha256_file(CHECKPOINT)},
        "replay_equivalence": replay_equivalence,
        "taxonomy_order": list(rr.GEOMETRY_FAILURE_VOCABULARY),
        "taxonomy_definitions": {
            "r2_wrong_source_orbit": "pre-R2 incidence forest has no q-node for the R2 source E-orbit",
            "r2_wrong_target_orbit": "source q-node is present but pre-R2 forest has no q-node for the R2 target E-orbit",
            "other_asserted_reason": "forbidden: unclassified opaque geometry exit raises AssertionError",
        },
        "legacy_opaque_geometry_failure_count": int(stats["R2_outcomes"]["recognizer_geometry_failure"]),
        "geometry_failure_counts": stats["geometry_failure_counts"],
        "record_count": len(geo_records),
        "records": geo_records,
    }
    component_payload = {
        "schema": "rr-short-ell0-v3-not-same-component-detail-v1",
        "scope": "all R2 candidates classified not_same_component in the deterministic replay",
        "record_count": len(component_rows),
        "expected_record_count": int(stats["R2_outcomes"]["not_same_component"]),
        "histograms": hist(component_rows),
        "records": component_rows,
    }
    frontier_rows = frontier_records(rr, checkpoint, snap)
    frontier_payload = {
        "schema": "rr-short-ell0-v3-frontier-export-v1",
        "checkpoint_read_only": {"path": str(CHECKPOINT.relative_to(ROOT)), "sha256": sha256_file(CHECKPOINT)},
        "record_count": len(frontier_rows),
        "frontier_hash": replay_equivalence["saved_frontier_hash"],
        "records": frontier_rows,
    }
    atomic_json(GEOMETRY, geometry_payload)
    atomic_json(COMPONENTS, component_payload)
    atomic_json(FRONTIER, frontier_payload)
    write_report(geometry_payload, frontier_payload, component_payload)
    print(json.dumps({"geometry": len(geo_records), "component": len(component_rows),
                      "frontier": len(frontier_rows), "verified_replay": True}, sort_keys=True))


if __name__ == "__main__":
    main()
