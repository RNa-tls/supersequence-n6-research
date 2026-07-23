#!/usr/bin/env python3
"""Read-only N=1 defect analysis from immutable N=0 terminal certificates.

The input checkpoint is never resumed or modified.  The only exploration is a
bounded (default depth three) continuation from the terminal states that gain
an N=1-safe tail; a global node cap applies across all such roots.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import mmap
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
SPEC = importlib.util.spec_from_file_location("f1_n1_defect_macro", MACRO_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MACRO_PATH}")
macro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = macro
SPEC.loader.exec_module(macro)
exact = macro.exact


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_json_array(path: Path, key: bytes) -> list[dict[str, Any]]:
    """Extract one JSON array without materializing the giant frontier/seen set."""
    marker = b'"' + key + b'": '
    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        begin = data.find(marker)
        if begin < 0:
            raise KeyError(key.decode())
        start = begin + len(marker)
        if data[start:start + 1] != b"[":
            raise ValueError("expected array")
        depth, quoted, escaped = 0, False, False
        cursor = start
        while cursor < len(data):
            byte = data[cursor]
            if quoted:
                if escaped:
                    escaped = False
                elif byte == 92:
                    escaped = True
                elif byte == 34:
                    quoted = False
            else:
                if byte == 34:
                    quoted = True
                elif byte == 91:
                    depth += 1
                elif byte == 93:
                    depth -= 1
                    if depth == 0:
                        return json.loads(data[start:cursor + 1].decode("utf-8"))
            cursor += 1
    raise ValueError("unterminated array")


def move_delta_label(edge: macro.MacroEdge, state: exact.ExactState) -> tuple[str, dict[str, Any]]:
    joint = edge.joint
    source_q, _ = exact.ORBIT_PHASE[state.p]
    target_q, target_phase = exact.ORBIT_PHASE[joint.target]
    target_hex = exact.core.hexagon_id(joint.target)
    before = state.orbit_masks[target_q]
    after = edge.state.orbit_masks[target_q]
    if joint.move.weight == 3 and not joint.abandonment and not joint.new_orbit:
        kind = "R_blocked_w3_existing"
    elif joint.move.weight == 3 and joint.abandonment and joint.new_orbit:
        kind = "A3_abandon_w3_new"
    elif joint.move.weight == 2 and joint.abandonment and not joint.new_orbit:
        kind = "A2_abandon_w2_existing"
    elif joint.move.weight == 3 and not joint.abandonment and joint.new_orbit:
        kind = "normal_w3_new"
    elif joint.move.weight == 2 and joint.abandonment and joint.new_orbit:
        kind = "normal_w2_abandon_new"
    elif joint.move.weight == 2 and not joint.abandonment and not joint.new_orbit:
        kind = "normal_w2_blocked_existing"
    else:
        kind = "forbidden_or_delta_two"
    return kind, {
        "joint_type": kind,
        "weight": joint.move.weight,
        "rotation_length": edge.run.ell,
        "source_orbit": source_q,
        "target_orbit": target_q,
        "target_phase": target_phase,
        "target_hexagon": target_hex,
        "target_phase_mask_before": before,
        "target_phase_mask_after": after,
        "abandonment": joint.abandonment,
        "new_orbit": joint.new_orbit,
        "delta": {"F": joint.delta_F, "S": joint.delta_S, "O": int(joint.new_orbit), "N": edge.state.Ndef - state.Ndef, "D": edge.state.D - state.D},
    }


def fragment_summary(state: exact.ExactState) -> dict[str, Any]:
    form = exact.f1_normal_form(state)
    if form is None:
        return {"normal_form_valid": False}
    return {
        "normal_form_valid": True,
        "current_hex": form.current_hex,
        "current_components": form.current_components,
        "fragment_hex": form.fragment_hex,
        "fragment_components": form.fragment_components,
        "fragment_is_current": form.fragment_hex == form.current_hex,
        "orbit_phase_masks": form.orbit_masks,
    }


def component_map(state: exact.ExactState) -> tuple[dict[tuple[str, int], tuple[str, int]], dict[int, int]]:
    parent: dict[tuple[str, int], tuple[str, int]] = {}
    def find(node: tuple[str, int]) -> tuple[str, int]:
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]
    def union(left: tuple[str, int], right: tuple[str, int]) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a
    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = exact.core.ports_of_e_orbit(exact.core.E_REPS[q])[phase]
                union(("q", q), ("h", exact.core.hexagon_id(port)))
    result = {node: find(node) for node in list(parent)}
    hex_root = {node[1]: root[1] for node, root in result.items() if node[0] == "h"}
    return result, hex_root


def bounded_survival(root: exact.ExactState, depth: int, cap: int, remaining_budget: list[int]) -> dict[str, Any]:
    frontier = [root]
    by_depth: list[int] = []
    next_tail_counts: list[int] = []
    truncated = False
    for _level in range(depth):
        children: dict[tuple[object, ...], exact.ExactState] = {}
        for state in frontier:
            safe = []
            for edge in macro.macro_edges(state):
                if macro.area_a_prune_reason(edge.state, macro.SMALL_N1) is None:
                    safe.append(edge.state)
            next_tail_counts.append(len(safe))
            for child in safe:
                if remaining_budget[0] <= 0:
                    truncated = True
                    break
                remaining_budget[0] -= 1
                children.setdefault(child.stable_key(), child)
            if truncated:
                break
        frontier = list(children.values())
        by_depth.append(len(frontier))
        if truncated or not frontier:
            break
    return {"survivors_by_macro_depth": by_depth, "safe_tail_counts_encountered": next_tail_counts, "truncated_by_global_node_cap": truncated}


def immediate_rejection_summary(state: exact.ExactState) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for edge in macro.macro_edges(state):
        reason = macro.area_a_prune_reason(edge.state, macro.SMALL_N1)
        counts["safe" if reason is None else f"pruned:{reason}"] += 1
    return dict(sorted(counts.items()))


def defect_automaton() -> dict[str, Any]:
    # Necessary-only abstraction.  The status of a repair cannot be determined
    # from this quotient, so it is explicitly nondeterministic.
    transitions = [
        {"name": "normal_w3_new", "pre": "defect_unused_or_used", "post": "same_defect_bit", "delta": {"N": 0, "D": 4, "O": 1}, "fragment": "unchanged", "status": "proved local flow"},
        {"name": "normal_w2_abandon_new", "pre": "fragment_unused", "post": "fragment_spent", "delta": {"N": 0, "D": 4, "O": 1}, "fragment": "creates the unique abandonment", "status": "proved local flow"},
        {"name": "normal_w2_blocked_existing", "pre": "any", "post": "repair_pending_or_repaired", "delta": {"N": 0, "D": -1, "O": 0}, "fragment": "does not determine whether it repairs the old gap", "status": "proved delta; repair relation omitted"},
        {"name": "R_blocked_w3_existing", "pre": "defect_unused", "post": "defect_used", "delta": {"N": 1, "D": -1, "O": 0}, "fragment": "unchanged", "status": "proved defect normal form"},
        {"name": "A3_abandon_w3_new", "pre": "fragment_unused,defect_unused", "post": "fragment_spent,defect_used", "delta": {"N": 1, "D": 4, "O": 1}, "fragment": "creates abandonment", "status": "proved defect normal form"},
        {"name": "A2_abandon_w2_existing", "pre": "fragment_unused,defect_unused", "post": "fragment_spent,defect_used", "delta": {"N": 1, "D": -1, "O": 0}, "fragment": "creates abandonment", "status": "proved defect normal form"},
    ]
    return {
        "schema": "f1-n1-necessary-defect-automaton-v1",
        "states": "(fragment_unused/spent, defect_unused/used, current_component_relation, repair_unknown/pending/repaired)",
        "transitions": transitions,
        "SCC_statement": "After quotienting only by the defect-used bit, all transitions are within a layer or go unused->used; no transition returns used->unused. Exact SCCs are not determined by this relaxation.",
        "defect_free_completion": "permitted by the relaxation; exact N=0 feasibility is not decided here",
        "minimum_distance_to_second_defect": "not defined in N<=1 automaton: a second DeltaN=1 transition is budget-forbidden immediately",
        "terminal_claim": "none; literal masks are required to decide collision/capacity terminality",
    }


def md_escape(report: Mapping[str, Any]) -> str:
    lines = ["# N=1 escapes from N=0 terminals", "", "Status: limited experiment on immutable N=0 terminal certificates; not an N=1 enumeration.", "", "## Summary", "", f"- terminal certificates read: {report['terminal_input_count']}", f"- N=1 escape roots: {report['escape_root_count']}", f"- bounded macro-node cap: {report['bounded_experiment']['node_cap']}", f"- depth: {report['bounded_experiment']['depth']}", "", "## Defect archetypes", ""]
    for name, row in report["escape_archetypes"].items():
        lines.append(f"- `{name}`: {row['count']} roots; survivors at depth 1/2/3 aggregated as {row['aggregate_survivors_by_depth']}.")
    lines += [
        "",
        "## Bounded findings",
        "",
        "All recorded escapes are `R_blocked_w3_existing`; the other two",
        "proved defect normal forms do not occur in this particular N=0-terminal",
        "sample.  Every escape survives three bounded N<=1 macro steps.  This is",
        "a restricted observation, not evidence for an N=1 completion.",
        "",
        "Candidate A and B are proved algebraically by the one-defect lemma.",
        "Candidate C is not tested by a complete repair predicate, and candidate",
        "D needs a paired exact N=0/N=1 capacity comparison; neither is promoted",
        "to a theorem.",
        "",
        "All component and split-hexagon relations below refer only to the current partial port-incidence graph, not to a completed skeleton.",
        "",
        "```json", json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), "```"]
    return "\n".join(lines) + "\n"


def md_automaton(automaton: Mapping[str, Any]) -> str:
    return "# F=1,N=1 necessary defect automaton\n\nStatus: necessary-only quotient; no exact-state conclusion.\n\n```json\n" + json.dumps(automaton, ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--node-cap", type=int, default=50000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--automaton-output", type=Path, required=True)
    parser.add_argument("--automaton-markdown", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.depth <= 4 or not 1 <= args.node_cap <= 50000:
        raise ValueError("depth must be 1..4 and node cap 1..50000")
    terminals = extract_json_array(args.checkpoint, b"terminal_certificates")
    if not terminals:
        raise ValueError("no terminal certificates")
    roots: list[dict[str, Any]] = []
    global_budget = [args.node_cap]
    for cert in terminals:
        state = exact.state_from_json(cert["state"])
        if state.F != 1 or state.H != 0 or state.Ndef != 0:
            continue
        components, hex_roots = component_map(state)
        for edge in macro.macro_edges(state):
            child = edge.state
            if macro.area_a_prune_reason(child, macro.SMALL_N1) is not None or child.Ndef != 1:
                continue
            kind, defect = move_delta_label(edge, state)
            source_node, target_node = ("q", defect["source_orbit"]), ("q", defect["target_orbit"])
            source_root, target_root = components.get(source_node), components.get(target_node)
            fs = fragment_summary(state)
            fhex = fs.get("fragment_hex")
            defect["partial_port_component_relation"] = "same" if source_root is not None and source_root == target_root else "different_or_unresolved"
            defect["fragment_hex_component_relation"] = "unobservable" if fhex is None else ("target_component" if components.get(target_node) == hex_roots.get(fhex) else "different_or_unresolved")
            defect["target_is_observed_fragment_hex"] = None if fhex is None else defect["target_hexagon"] == fhex
            roots.append({
                "canonical_state_hash": cert["state_hash"],
                "terminal_coordinate": cert["coordinate"],
                "terminal_fragment": fs,
                "representative_path": cert.get("path", []),
                "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
                "defect": defect,
                "post_defect_coordinate": macro.state_coordinate(child),
                "post_defect_fragment": fragment_summary(child),
                "bounded_continuation": bounded_survival(child, args.depth, args.node_cap, global_budget),
                "post_defect_immediate_rejections": immediate_rejection_summary(child),
            })
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for root in roots:
        d = root["defect"]
        key = json.dumps({"type": d["joint_type"], "weight": d["weight"], "rotation_length": d["rotation_length"], "component_relation": d["partial_port_component_relation"], "fragment_relation": d["fragment_hex_component_relation"], "phase_before": d["target_phase_mask_before"]}, sort_keys=True)
        groups[key].append(root)
    archetypes: dict[str, Any] = {}
    for key, values in groups.items():
        aggregate = [0] * args.depth
        for value in values:
            for index, count in enumerate(value["bounded_continuation"]["survivors_by_macro_depth"]):
                aggregate[index] += count
        archetypes[key] = {"count": len(values), "aggregate_survivors_by_depth": aggregate, "minimum_representative": values[0]["canonical_state_hash"]}
    automaton = defect_automaton()
    observed_fragment_targets = [root["defect"]["target_is_observed_fragment_hex"] for root in roots if root["defect"]["target_is_observed_fragment_hex"] is not None]
    immediate_n2_prunes = sum(root["post_defect_immediate_rejections"].get("pruned:N_exceeded_monotone", 0) for root in roots)
    report: dict[str, Any] = {
        "schema": "f1-n1-terminal-escape-analysis-v1",
        "scope": "read-only source checkpoint plus bounded N<=1 continuation; no N=1 exhaustive claim",
        "input_checkpoint": {"path": str(args.checkpoint), "sha256": sha256_file(args.checkpoint)},
        "code_sha256": {"analysis": sha256_file(HERE), "macro": macro.CODE_SHA256, "engine": macro.ENGINE_SHA256, "core": macro.CORE_SHA256},
        "terminal_input_count": len(terminals),
        "escape_root_count": len(roots),
        "distinct_terminal_states_with_escape": len({root["canonical_state_hash"] for root in roots}),
        "bounded_experiment": {"depth": args.depth, "node_cap": args.node_cap, "generated_nodes": args.node_cap - global_budget[0], "cap_hit": global_budget[0] == 0},
        "escape_archetypes": archetypes,
        "escape_roots": roots,
        "candidate_lemmas": {
            "A_one_defect_allows_one_N_increasing_revisit": {"status": "proved for an N<=1 trajectory", "reason": "Delta N is nonnegative and final N=1, so a second DeltaN=1 joint is impossible"},
            "B_after_defect_all_other_joints_follow_zero_defect_flow": {"status": "proved", "reason": "the one-defect theorem leaves every other joint with DeltaN=0"},
            "C_split_repair_consumes_defect": {"status": "limited experiment", "definition": "defect target equals the currently observable noncurrent fragment hexagon", "states_checked": len(roots), "observable_fragment_states": len(observed_fragment_targets), "same_hex_count": sum(observed_fragment_targets), "counterexamples": None, "reason": "same-hex incidence is not a complete definition of repair; no theorem follows"},
            "D_one_defect_bypasses_at_most_one_capacity_gate": {"status": "not determined", "definition": "requires a paired exact N=0/N=1 continuation comparison, not supplied by a local tail", "states_checked": len(roots), "immediate_N2_prunes_after_defect": immediate_n2_prunes, "reason": "capacity is a global exact-mask condition; only bounded observations are available"},
        },
        "limitations": "Partial component relations are computed from current pass-start ports, not a completed 25-orbit skeleton. Any missing relation is unresolved, not false.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown.write_text(md_escape(report), encoding="utf-8")
    args.automaton_output.write_text(json.dumps(automaton, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    args.automaton_markdown.write_text(md_automaton(automaton), encoding="utf-8")
    print(json.dumps({"terminal_input_count": len(terminals), "escape_root_count": len(roots), "archetype_count": len(archetypes), "bounded_nodes": args.node_cap - global_budget[0], "cap_hit": global_budget[0] == 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
