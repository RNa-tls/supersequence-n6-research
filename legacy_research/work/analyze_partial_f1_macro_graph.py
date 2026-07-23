#!/usr/bin/env python3
"""Bounded quotient graph of F=1 fragment fingerprints under macro edges.

This is a diagnostic quotient.  Its SCCs never assert cycles of exact walks:
the full exact masks and visited-window count are intentionally forgotten.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, Mapping, Tuple

HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
SPEC = importlib.util.spec_from_file_location("partial_f1_macro_graph_engine", MACRO_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MACRO_PATH}")
macro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = macro
SPEC.loader.exec_module(macro)
exact = macro.exact
PROFILE_PATH = HERE.with_name("analyze_partial_f1_profiles.py")
PROFILE_SPEC = importlib.util.spec_from_file_location("partial_f1_profile_fingerprint", PROFILE_PATH)
if PROFILE_SPEC is None or PROFILE_SPEC.loader is None:
    raise RuntimeError(f"cannot load {PROFILE_PATH}")
profile = importlib.util.module_from_spec(PROFILE_SPEC)
sys.modules[PROFILE_SPEC.name] = profile
PROFILE_SPEC.loader.exec_module(profile)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tid(fp: object) -> str:
    if fp is None:
        return "pre_fragment"
    return "T_" + hashlib.sha256(repr(fp).encode("utf-8")).hexdigest()[:16]


def coarse_existing_fingerprint(state: exact.ExactState) -> object:
    """The lossless state is still retained; this is only the old 20-type
    observational fingerprint with creation weight intentionally forgotten.

    A macro edge alone cannot recover historical creation weight from an exact
    state after canonical merging.  Keeping it out here prevents a false
    claim that this quotient is a Markov state.
    """
    value = profile.fragment_fingerprint(state, None)
    if isinstance(value, dict):
        value = dict(value)
        value.pop("creation_weight", None)
    return value


def missing_rotation_u(state: exact.ExactState) -> int | None:
    form = exact.f1_normal_form(state)
    if form is None or form.fragment_hex is None:
        return None
    return 6 - state.hex_masks[form.fragment_hex].bit_count()


def tarjan(vertices: Iterable[str], adjacency: Mapping[str, Iterable[str]]) -> list[list[str]]:
    index = 0
    indices: Dict[str, int] = {}
    low: Dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    answer: list[list[str]] = []

    def visit(v: str) -> None:
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v); active.add(v)
        for w in adjacency.get(v, ()):
            if w not in indices:
                visit(w); low[v] = min(low[v], low[w])
            elif w in active:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            component: list[str] = []
            while True:
                w = stack.pop(); active.remove(w); component.append(w)
                if w == v: break
            answer.append(sorted(component))

    for v in sorted(vertices):
        if v not in indices:
            visit(v)
    return answer


def analyze(max_depth: int, node_limit: int) -> dict[str, object]:
    config = macro.AREA_A
    start = exact.canonicalize(exact.initial_state())
    queue = deque([(0, start)])
    seen = {start.stable_key()}
    type_data: Dict[str, dict[str, object]] = {}
    edge_data: Counter[Tuple[str, str, int, int, bool, str]] = Counter()
    adjacency: Dict[str, set[str]] = defaultdict(set)
    expanded = 0
    bounded_terminal: Counter[str] = Counter()

    while queue and expanded < node_limit:
        depth, state = queue.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        source_fp = coarse_existing_fingerprint(state)
        source = tid(source_fp)
        type_data.setdefault(source, {"fingerprint": repr(source_fp), "max_depth": depth, "states": 0, "u_values": Counter()})
        type_data[source]["max_depth"] = max(int(type_data[source]["max_depth"]), depth)
        type_data[source]["states"] = int(type_data[source]["states"]) + 1
        if (u := missing_rotation_u(state)) is not None:
            type_data[source]["u_values"][str(u)] += 1
        surviving = 0
        for edge in macro.macro_edges(state):
            reason = macro.area_a_prune_reason(edge.state, config)
            if reason is not None:
                continue
            child = exact.canonicalize(edge.state)
            target_fp = coarse_existing_fingerprint(child)
            target = tid(target_fp)
            event = (
                "fragment_create" if source_fp is None and target_fp is not None else
                "fragment_repair_or_complete" if source_fp is not None and target_fp is None else
                "fragment_persist"
            )
            dN = child.Ndef - state.Ndef
            dD = child.D - state.D
            edge_data[(source, target, dN, dD, edge.joint.new_orbit, event)] += 1
            adjacency[source].add(target)
            surviving += 1
            key = child.stable_key()
            if key not in seen:
                seen.add(key); queue.append((depth + 1, child))
        if surviving == 0:
            bounded_terminal[source] += 1

    vertices = set(type_data) | {x[1] for x in edge_data}
    components = tarjan(vertices, adjacency)
    payload_types = {
        key: {**data, "u_values": dict(sorted(data["u_values"].items()))}
        for key, data in sorted(type_data.items())
    }
    payload_edges = [
        {"source": s, "target": t, "delta_N": dn, "delta_D": dd, "new_orbit": no,
         "fragment_event": ev, "observed_multiplicity": count}
        for (s, t, dn, dd, no, ev), count in sorted(edge_data.items())
    ]
    return {
        "schema": "partial-f1-fragment-type-graph-v1",
        "analysis_sha256": sha256_file(HERE),
        "macro_sha256": macro.CODE_SHA256,
        "engine_sha256": macro.ENGINE_SHA256,
        "core_sha256": macro.CORE_SHA256,
        "config": {"max_macro_depth": max_depth, "node_limit": node_limit, "subcase": config.name},
        "completed_bounded_search": not queue,
        "expanded_exact_states": expanded,
        "canonical_exact_states_seen": len(seen),
        "types": payload_types,
        "edges": payload_edges,
        "bounded_terminal_type_counts": dict(sorted(bounded_terminal.items())),
        "strongly_connected_components": components,
        "warning": "Type-graph SCCs are quotient artifacts, not exact-walk cycles; exact visited masks strictly grow.",
    }


def markdown(report: Mapping[str, object]) -> str:
    return "# F=1 fragment-type quotient graph\n\n" + \
        "This is a bounded diagnostic quotient, not a state-space proof.  SCCs do not lift to exact walk cycles because the full visited-mask component was forgotten.\n\n```json\n" + \
        json.dumps(report, ensure_ascii=False, indent=2) + "\n```\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--max-depth", type=int, default=3)
    p.add_argument("--node-limit", type=int, default=5000)
    p.add_argument("--output", default=str(ROOT / "outputs" / "f1_fragment_type_graph.json"))
    p.add_argument("--markdown", default=str(ROOT / "outputs" / "F1_FRAGMENT_TYPE_GRAPH.md"))
    args = p.parse_args()
    report = analyze(args.max_depth, args.node_limit)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.markdown).write_text(markdown(report), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ('completed_bounded_search','expanded_exact_states','canonical_exact_states_seen')}, ensure_ascii=False))


if __name__ == "__main__":
    main()
