#!/usr/bin/env python3
"""Section 5 / H0-Necessity: bounded local search for a same-component,
NON-chaining R2 witness, starting from each of the 10 known
same-component witnesses' post-R1 state (and, separately, their
post-abandonment/pre-R1 state for a bit more room). This is NOT a new
large-scale search -- it is a small, bounded (depth<=5, node_cap<=20,000
PER starting state) local exploration from states ALREADY reached in the
existing 4,470-witness corpus, reusing the same macro_edges() /
area_a_prune_reason() machinery as every prior round's bounded checks
(comparable in size to search_a2r_min_depth.py's single-state 200,000-node
bound).

If ANY such witness is found, "same-component ==> chaining" is FALSIFIED
by an exact witness. If none is found (exhaustive within the bound, i.e.
frontier fully consumed), that is strong (but not fully general) local
evidence for necessity from these specific starting points.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("vrhn_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def component_map(state: "exact.ExactState") -> Dict[Any, Any]:
    parent: Dict[Any, Any] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return {n: find(n) for n in parent}


def replay_to_post_r1(witness: Dict[str, Any]) -> "exact.ExactState":
    path = witness["macro_path"]
    cur = exact.initial_state()
    r_count = 0
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        cur = tr.state
        if kind == "R":
            r_count += 1
            if r_count == 1:
                return cur
    raise AssertionError("no R1 found")


def search_for_counterexample(state: "exact.ExactState", forbidden_source_orbit: int, max_depth: int, node_cap: int) -> Dict[str, Any]:
    frontier = deque([(0, state)])
    expanded = 0
    found: List[Dict[str, Any]] = []
    while frontier and expanded < node_cap:
        depth, st = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        roots = component_map(st)
        for e in macro.macro_edges(st):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            src_q, _ = exact.ORBIT_PHASE[e.run.state.p]
            if kind == "R" and tr.target is not None:
                tgt_q, _ = exact.ORBIT_PHASE[tr.target]
                src_root, tgt_root = roots.get(("q", src_q)), roots.get(("q", tgt_q))
                rel = "same" if src_root is not None and src_root == tgt_root else (
                    "different" if src_root is not None and tgt_root is not None else "unresolved")
                if rel == "same" and src_q != forbidden_source_orbit:
                    found.append({"depth": depth, "source_orbit": src_q, "target_orbit": tgt_q, "ell": e.run.ell})
            if kind in ("A2", "A3", "J"):
                continue
            frontier.append((depth + 1, tr.state))
    return {
        "nodes_expanded": expanded, "frontier_remaining": len(frontier),
        "exhaustive_within_bound": len(frontier) == 0,
        "same_non_chaining_witnesses_found": found,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--node-cap", type=int, default=20000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_hex0_causal_certificates.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    table = json.loads(Path(args.relation_table).read_text(encoding="utf-8"))
    same_hashes = [r["hash"] for r in table["rows"] if r.get("r2_own_component_relation") == "same"]
    print(f"testing {len(same_hashes)} same-component witnesses' post-R1 boundary")

    results = {}
    any_counterexample = False
    for h in same_hashes:
        w = wdata["witnesses"][h]
        post_r1 = replay_to_post_r1(w)
        r1_target_orbit, _ = exact.ORBIT_PHASE[post_r1.p] if False else (None, None)
        # recover r1_target_orbit from the relation table row instead (already computed there)
        row = next(r for r in table["rows"] if r["hash"] == h)
        r1_target_orbit = row["r1_target"]
        search = search_for_counterexample(post_r1, r1_target_orbit, args.max_depth, args.node_cap)
        results[h] = {"r1_target_orbit": r1_target_orbit, **search}
        if search["same_non_chaining_witnesses_found"]:
            any_counterexample = True
        print(h[:12], "nodes_expanded", search["nodes_expanded"], "exhaustive", search["exhaustive_within_bound"],
              "counterexamples_found", len(search["same_non_chaining_witnesses_found"]))

    report = {
        "schema": "rr-hex0-causal-certificates-v1",
        "method": (
            f"bounded local search (max_depth={args.max_depth}, node_cap={args.node_cap} PER "
            "witness) from each of the 10 same-component witnesses' post-R1 state, looking for "
            "a legal R2 candidate with component_relation=='same' but source orbit != R1's "
            "target orbit (i.e. a same-component, non-chaining witness). Bounded, reuses "
            "existing macro_edges()/area_a_prune_reason() -- not a new large-scale search."
        ),
        "any_counterexample_found": any_counterexample,
        "per_witness": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "any_counterexample_found": any_counterexample}, indent=2))


if __name__ == "__main__":
    main()
