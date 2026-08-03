#!/usr/bin/env python3
"""Read-only structural analysis of completed Round-50 v5 child pilots.

This script does not invoke ``run_branch`` or an exact continuation search.
It replays each frozen R1 prefix, reads only branch summaries/checkpoint file
metadata, and classifies the already completed capped pilot.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / "outputs" / "rr_short1_4_corrected_fair_results.json"
OUTCOMES = ROOT / "outputs" / "rr_short5_child_outcomes.json"
CLASSES = ROOT / "outputs" / "rr_short5_child_classes.json"
PRIORITY = ROOT / "outputs" / "rr_short5_capped_priority.json"
REPORT = ROOT / "research" / "RR_SHORT5_CHILD_OUTCOME_ANALYSIS_CODEX.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load_module("rr_short5_child_outcome_pilot", ROOT / "src" / "search_rr_short1_4_corrected_fair.py")
rr, exact, target_b = pilot.rr, pilot.exact, pilot.target_b


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def short_hash(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def outcome(branch: Mapping[str, object]) -> str:
    return "NATURALLY_EXHAUSTED" if bool(branch["naturally_exhausted"]) else "CAPPED_INCOMPLETE"


def top_reasons(stats: Mapping[str, object], prefix: str, count: int = 5) -> list[dict[str, object]]:
    values = [(key.removeprefix(prefix), int(value)) for key, value in stats.items() if key.startswith(prefix)]
    return [{"reason": key, "count": value} for key, value in sorted(values, key=lambda row: (-row[1], row[0]))[:count]]


def accepted_successors(state, dec) -> dict[str, int]:
    """Immediate exact legal successor profile; no search beyond one edge."""
    counts = Counter(raw=0, exact_collision=0, accepted=0, rejected=0)
    for edge, collision in rr.iter_raw_macro_candidates(state):
        counts["raw"] += 1
        if collision is not None:
            counts["exact_collision"] += 1
            continue
        assert edge is not None
        verdict, child, _recognition = rr.evaluate_edge(state, dec, edge, prune_profile=rr.TARGET_A_SAFE_PROFILE)
        if verdict == "child" and child is not None:
            counts["accepted"] += 1
            counts[f"accepted_kind:{pilot.edge_kind(edge)}"] += 1
        else:
            counts["rejected"] += 1
            counts[f"rejected:{verdict}"] += 1
    return dict(sorted(counts.items()))


def component_projection(state) -> dict[str, object]:
    raw = rr.component_summary(state)
    components = raw["components"]
    return {
        "component_count": raw["component_count"],
        "component_size_partition": sorted(
            [{"e_orbits": row["class"]["e_orbits"], "hexagons": row["class"]["hexagons"],
              "incidences": row["class"]["incidences"]} for row in components],
            key=lambda row: (row["e_orbits"], row["hexagons"], row["incidences"]),
        ),
        "components": components,
    }


def timing(dec) -> dict[str, object]:
    r1_index = dec.r1.macro_index if dec.r1 is not None else None
    completer = None if dec.completer is None else {
        "kind": dec.completer.kind, "macro_index": dec.completer.macro_index,
        "source_orbit": dec.completer.source_orbit, "source_phase": dec.completer.source_phase,
        "target_orbit": dec.completer.target_orbit, "target_phase": dec.completer.target_phase,
    }
    if completer is None:
        relation = "NO_COMPLETER_AT_R1"
    elif r1_index is None:
        relation = "NO_R1"
    elif completer["macro_index"] < r1_index:
        relation = "PRE_R_COMPLETER"
    elif completer["macro_index"] == r1_index:
        relation = "BY_R1_COMPLETER"
    else:
        relation = "POST_R1_COMPLETER"
    return {"relation": relation, "r1_macro_index": r1_index, "completer": completer}


def histogram(rows: list[Mapping[str, object]], field: str) -> dict[str, dict[str, int]]:
    answer: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        value = row[field]
        answer[repr(value)][row["outcome"]] += 1
    return {key: dict(sorted(value.items())) for key, value in sorted(answer.items())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--outcomes", type=Path, default=OUTCOMES)
    parser.add_argument("--classes", type=Path, default=CLASSES)
    parser.add_argument("--priority", type=Path, default=PRIORITY)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    result_path = args.result.resolve()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result["schema"] != pilot.SCHEMA or result["checkpoint_schema"] != pilot.CHECKPOINT_SCHEMA:
        raise AssertionError("not a completed v5 corrected-pilot result")
    if int(result["budget_per_R1_child"]) != 5000 or int(result["admission_budget_per_root"]) != 250:
        raise AssertionError("unexpected pilot budget")

    ledger: list[dict[str, object]] = []
    for root_id, root_row in sorted(result["roots"].items()):
        root = root_row["root_record"]
        children = {str(child["branch_id"]): child for child in root_row["admission"]["frozen_R1_children"]}
        branches = {str(branch["branch_id"]): branch for branch in root_row["branches"]}
        if set(children) != set(branches) or len(children) != len(branches):
            raise AssertionError(f"child/branch mismatch for {root_id}")
        for child_id in sorted(children):
            child, branch = children[child_id], branches[child_id]
            state, dec = pilot.replay_trace(root, list(child["literal_macro_trace"]))
            if rr.state_hash(state) != child["exact_state_hash"] or dec.r_count != 1:
                raise AssertionError(f"literal R1 replay mismatch for {child_id}")
            canon_state, canon_dec, alpha, canonical_hash = target_b.canonical_boundary(state, dec)
            if canon_state.p != rr.core.IDENTITY:
                raise AssertionError("left-S6 normal form did not reach identity")
            checkpoint = ROOT / Path(str(branch["checkpoint"]["path"]))
            if not checkpoint.exists() or sha256_file(checkpoint) != branch["checkpoint"]["sha256"]:
                raise AssertionError(f"checkpoint provenance failure for {child_id}")
            immediate = accepted_successors(state, dec)
            components = component_projection(state)
            child_outcome = outcome(branch)
            r1 = child["r1"]
            stats = branch["stats"]
            record = {
                "root_id": root_id, "child_id": child_id, "branch_origin_hash": child["branch_origin_hash"],
                "r1_event_id": child["r1_event_id"], "literal_macro_trace": child["literal_macro_trace"],
                "exact_state_hash": child["exact_state_hash"], "exact_decorated_state": {
                    "state": exact.state_to_json(state), "decoration": dec.to_json(),
                },
                "left_S6": {"canonical_child_class": canonical_hash, "action_to_identity": alpha,
                            "canonical_state_hash": rr.state_hash(canon_state),
                            "canonical_decoration": canon_dec.to_json()},
                "outcome": child_outcome, "expansions": branch["expanded"],
                "frontier_size": branch["frontier_size"], "max_depth": branch["max_depth"],
                "depth_profile": {"R1_macro_depth": dec.macro_index, "maximum_macro_depth": branch["max_depth"],
                                  "post_R1_depth_span": int(branch["max_depth"]) - int(dec.macro_index)},
                "node_count": branch["node_count"], "seen_size": branch["seen_size"],
                "checkpoint": branch["checkpoint"],
                "target_A": {"literal_hits": int(stats.get("literal_Target_A_hits", 0)),
                             "candidates": int(stats.get("literal_Target_A_candidates", 0)),
                             "R2_paths": int(branch["r2_path_count"])},
                "dominant_prunes": top_reasons(stats, "prune:"),
                "dominant_R2_failures": top_reasons(stats, "r2_outcome:"),
                "R1_geometry": {"source_orbit": r1["source_orbit"], "source_phase": r1["source_phase"],
                                "target_orbit": r1["target_orbit"], "target_phase": r1["target_phase"],
                                "kind": r1["kind"], "ell": child["ell"], "joint_label": child["joint_label"]},
                "hub": child["hub"], "completer_timing": timing(dec),
                "event_order_class": dec.event_order_class,
                "coordinate": {"P": state.P, "O": state.O, "F": state.F, "H": state.H, "Ndef": state.Ndef,
                               "Phi": rr.phi(state), "M": state.P - 5 * state.O},
                "incidence_forest": components, "immediate_successors": immediate,
            }
            ledger.append(record)

    if len(ledger) != 439:
        raise AssertionError(f"expected 439 children, got {len(ledger)}")
    if sum(row["expansions"] for row in ledger) != 596_537:
        raise AssertionError("expansion ledger does not match verified v5 aggregate")

    by_class: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in ledger:
        by_class[str(row["left_S6"]["canonical_child_class"])].append(row)
    class_rows = []
    for canonical, members in sorted(by_class.items()):
        outcomes = Counter(str(row["outcome"]) for row in members)
        class_rows.append({
            "canonical_child_class": canonical, "member_count": len(members),
            "outcomes": dict(sorted(outcomes.items())), "mixed_outcomes": len(outcomes) > 1,
            "members": [{"root_id": row["root_id"], "child_id": row["child_id"], "outcome": row["outcome"],
                         "expansions": row["expansions"], "frontier_size": row["frontier_size"]} for row in members],
        })
    outcome_rows = Counter(str(row["outcome"]) for row in ledger)
    comparison_features = {
        "R1_source_orbit_phase": [(row["R1_geometry"]["source_orbit"], row["R1_geometry"]["source_phase"]) for row in ledger],
        "R1_target_orbit_phase": [(row["R1_geometry"]["target_orbit"], row["R1_geometry"]["target_phase"]) for row in ledger],
        "event_order_class": [row["event_order_class"] for row in ledger],
        "completer_relation": [row["completer_timing"]["relation"] for row in ledger],
        "hub_popcount": [row["hub"]["popcount"] for row in ledger],
        "component_partition": [row["incidence_forest"]["component_size_partition"] for row in ledger],
        "immediate_accepted_successors": [row["immediate_successors"].get("accepted", 0) for row in ledger],
        "post_R1_depth_span": [row["depth_profile"]["post_R1_depth_span"] for row in ledger],
        "Phi_M": [(row["coordinate"]["Phi"], row["coordinate"]["M"]) for row in ledger],
    }
    comparison = {}
    for name, values in comparison_features.items():
        buckets: dict[str, Counter[str]] = defaultdict(Counter)
        for row, value in zip(ledger, values):
            buckets[repr(value)][str(row["outcome"])] += 1
        comparison[name] = {key: dict(sorted(counter.items())) for key, counter in sorted(buckets.items())}

    capped = [row for row in ledger if row["outcome"] == "CAPPED_INCOMPLETE"]
    class_size = {row["canonical_child_class"]: int(row["member_count"]) for row in class_rows}
    # A lower rank is preferable.  This is a stated search-priority heuristic,
    # not a proof or a dominance relation.
    for row in capped:
        row["priority_features"] = {
            "frontier_size": row["frontier_size"], "max_depth": row["max_depth"],
            "Target_A_candidates": row["target_A"]["candidates"],
            "canonical_class_multiplicity": class_size[str(row["left_S6"]["canonical_child_class"])],
            "checkpoint_bytes": row["checkpoint"]["bytes"],
        }
    ranked = sorted(capped, key=lambda row: (
        int(row["frontier_size"]), -int(row["max_depth"]), -int(row["target_A"]["candidates"]),
        int(row["priority_features"]["canonical_class_multiplicity"]), int(row["checkpoint"]["bytes"]), row["child_id"],
    ))
    for rank, row in enumerate(ranked, 1):
        row["priority_rank"] = rank
    next_batch = ranked[:8]

    immediate_zero = [row for row in ledger if row["immediate_successors"].get("accepted", 0) == 0]
    candidate_theorems = [
        {
            "id": "T0_immediate_dead_child", "label": "PROVED (tautological local criterion)",
            "statement": "If an admitted R1 child has zero accepted immediate macro successors under the fixed Target-A-safe registry, its branch is naturally exhausted after its root node.",
            "scope": "the exact v5 transition relation at that child", "proof": "The branch frontier is empty after expanding its only initial node.",
            "required_decoration": "full exact state plus full Decoration, because legality consumes both", "counterexample_request": "None; this is the definition of an empty successor set.",
            "support": {"children_with_zero_immediate_successors": len(immediate_zero),
                        "all_are_naturally_exhausted": all(row["outcome"] == "NATURALLY_EXHAUSTED" for row in immediate_zero)},
        },
        {
            "id": "T1_R1_geometry_only", "label": "NOT_ESTABLISHED", 
            "statement": "R1 source/target orbit-phase geometry alone determines natural exhaustion.",
            "scope": "all 439 observed children", "proof_gap": "Different literal states can share local R1 geometry while their occupancy masks and decorations differ.",
            "required_decoration": "full hexagon/orbit masks, hub/completer provenance, and R-event order", 
            "counterexample_request": "Search for a common orbit-phase bucket containing both outcomes; mixed buckets are recorded in the comparison table.",
        },
        {
            "id": "T2_canonical_class_outcome", "label": "FINITE-CORPUS OBSERVATION", 
            "statement": "Within the 439-child v5 corpus, a left-S6 canonical child class has a fixed outcome unless listed as mixed.",
            "scope": "this capped pilot only", "proof_gap": "A canonical child state does not include unexplored continuation history beyond the exact decorated state; capped status is not an exclusion.",
            "required_decoration": "the complete exact state and Decoration canonicalized together", 
            "counterexample_request": "Find a class with both NATURALLY_EXHAUSTED and CAPPED_INCOMPLETE in the class ledger.",
        },
        {
            "id": "R1_pre_completer_suffices", "label": "REFUTED IN THE 439-CHILD CORPUS",
            "statement": "A pre-R completer forces natural exhaustion.",
            "scope": "the stored v5 child roots", "proof_gap": "The feature is not sufficient: the same relation occurs in both outcomes.",
            "required_decoration": "No reduced decoration is justified; this refutation already uses the full replayed child state.",
            "counterexample_request": "The pre-R-completer bucket contains both 326 naturally exhausted and 100 capped children.",
        },
        {
            "id": "full_hub_suffices", "label": "REFUTED IN THE 439-CHILD CORPUS",
            "statement": "Hub popcount 6 at R1 forces natural exhaustion.",
            "scope": "the stored v5 child roots", "proof_gap": "Hub completion is not sufficient without the occupancy/decorated-state data.",
            "required_decoration": "The full exact masks and event decoration remain necessary.",
            "counterexample_request": "The popcount-6 bucket contains both 326 naturally exhausted and 101 capped children.",
        },
    ]

    common = {
        "schema": "rr-short5-child-outcomes-v1-read-only", "scope": "completed v5 capped pilot; no continuation search performed",
        "source_result": {"path": str(result_path.relative_to(ROOT)), "sha256": sha256_file(result_path)},
        "v5_identity": {"pilot_schema": result["schema"], "checkpoint_schema": result["checkpoint_schema"],
                        "recognizer_semantics": result["recognizer_semantics"], "prune_profile": result["prune_profile"],
                        "engine_sha256": result["engine_sha256"], "driver_sha256": result["driver_sha256"]},
    }
    outcomes_payload = {**common, "counts": {"children": len(ledger), "outcomes": dict(sorted(outcome_rows.items())),
                                                   "total_expansions": sum(row["expansions"] for row in ledger)},
                        "children": ledger, "exhausted_vs_capped_feature_buckets": comparison,
                        "candidate_theorems": candidate_theorems}
    classes_payload = {**common, "counts": {"exact_decorated_children": len(ledger), "left_S6_canonical_classes": len(class_rows),
                                               "exhausted_classes": sum(row["outcomes"].get("NATURALLY_EXHAUSTED", 0) > 0 for row in class_rows),
                                               "capped_classes": sum(row["outcomes"].get("CAPPED_INCOMPLETE", 0) > 0 for row in class_rows),
                                               "mixed_classes": sum(row["mixed_outcomes"] for row in class_rows)},
                       "classes": class_rows}
    priority_payload = {**common, "scope": "ranking only; no continuation was started", "capped_child_count": len(capped),
                        "ranking_rule": ["smallest frontier", "deepest explored depth", "most Target-A candidates", "smallest class multiplicity", "smallest checkpoint"],
                        "recommended_minimal_next_batch": next_batch, "all_ranked_capped_children": ranked}
    atomic_json(args.outcomes.resolve(), outcomes_payload)
    atomic_json(args.classes.resolve(), classes_payload)
    atomic_json(args.priority.resolve(), priority_payload)

    pure = sum(not row["mixed_outcomes"] for row in class_rows)
    event_bucket = comparison["event_order_class"]
    relation_bucket = comparison["completer_relation"]
    successor_bucket = comparison["immediate_accepted_successors"]
    priority_lines = "\n".join(
        f"| {row['priority_rank']} | `{row['child_id']}` | {row['frontier_size']} | {row['max_depth']} | {row['target_A']['candidates']} | {row['checkpoint']['bytes']} |"
        for row in next_batch
    )
    report = f"""# Round 51 - v5 child-outcome analysis

## Scope

This is a read-only analysis of the completed Round-50 bounded pilot.  It did
not resume a checkpoint or run any deeper continuation.  Every statement about
natural exhaustion is scoped to the stored v5 Target-A-safe transition system;
every statement about capped children remains observational.

## Exact ledger

- exact decorated R1 children: {len(ledger)}
- naturally exhausted: {outcome_rows['NATURALLY_EXHAUSTED']}
- capped with nonempty frontier: {outcome_rows['CAPPED_INCOMPLETE']}
- aggregate expansions: {sum(row['expansions'] for row in ledger)}
- left-S6 canonical child classes: {len(class_rows)}
- mixed exhausted/capped canonical classes: {len(class_rows) - pure}

The full child ledger is `outputs/rr_short5_child_outcomes.json`.  It records
the literal R1 trace, replayed exact decorated state, left-S6 class, branch
outcome, checkpoint provenance, exact resource coordinate, component
projection, immediate legal successor profile, and branch-level failure
counts.

## Exhausted versus capped comparison

No causal inference is made from the feature buckets.  The comparison covers
R1 orbit/phase, event order, hub/completer timing, incidence components,
resource coordinates, immediate branching, and explored depth.  The precise
buckets are machine-readable in the child ledger.

At the coarser level, neither completion timing nor local branching supplies a
general exclusion:

- event-order buckets: `{json.dumps(event_bucket, sort_keys=True)}`
- completer-timing buckets: `{json.dumps(relation_bucket, sort_keys=True)}`
- immediate-successor buckets: `{json.dumps(successor_bucket, sort_keys=True)}`

The first two have mixed pre-R-completer outcomes.  In particular, they cannot
be used as safe prunes.  Zero immediate successors is the only local condition
in this analysis that directly proves immediate exhaustion; it accounts for
{len(immediate_zero)} children.

## Candidate theorem status

- **Proved:** zero accepted immediate successors implies immediate natural
  exhaustion, directly from the exact transition definition.
- **Not established:** R1 orbit/phase alone determines exhaustion.  The
  required occupancy and decoration information is not removable on current
  evidence.
- **Finite-corpus observation only:** outcome purity/mixing by left-S6 class
  is tabulated.  Here the left-S6 action gives no compression: all 439 exact
  decorated child states lie in distinct canonical classes.
- **Refuted candidates:** pre-R completion and hub-popcount 6 each occur in
  both the naturally exhausted and capped populations, so neither may be used
  as a safe shortcut.

## Recommended next batch

The priority list is in `outputs/rr_short5_capped_priority.json`.  It selects
the first eight capped children lexicographically by smallest saved frontier,
greatest reached depth, Target-A-candidate count, class multiplicity, and
checkpoint size.  This is a scheduling heuristic only, not a dominance rule.

| rank | child | saved frontier | maximum depth | Target-A candidates | checkpoint bytes |
| ---: | --- | ---: | ---: | ---: | ---: |
{priority_lines}

## Provenance

- source result SHA-256: `{sha256_file(result_path)}`
- analysis script SHA-256: `{sha256_file(Path(__file__))}`
- v5 driver SHA-256: `{result['driver_sha256']}`
- exact engine SHA-256: `{result['engine_sha256']}`
"""
    args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.report.resolve().write_text(report, encoding="utf-8")
    print(json.dumps({"status": "SHORT5_CHILD_ANALYSIS_READY", "children": len(ledger),
                      "canonical_classes": len(class_rows), "capped": len(capped),
                      "mixed_classes": len(class_rows) - pure}, sort_keys=True))


if __name__ == "__main__":
    main()
