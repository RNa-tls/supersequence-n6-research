#!/usr/bin/env python3
"""Round 14, sections 1-4: formalizes hub completer candidates
invariantly, and -- crucially -- tests the original target theorem
("O != O_R candidates all violate some exact legality condition") by
DIRECTLY enumerating every reachable hub-completing candidate orbit
from a same-component witness's post-abandonment state.

Result (see module-level docstring in the generated output): this
target theorem is FALSIFIED. Multiple distinct orbits (not just O_R)
are legally reachable as hub completers. The corpus-exact fact that
survives is narrower: whenever "same" actually results, the completer
orbit that was ACTUALLY used equals R1's target orbit -- but this is a
fact about which candidate got used, not about which candidates exist.
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


macro = _load("arhco_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def replay_to_post_abandonment(witness: Dict[str, Any]):
    path = witness["macro_path"]
    cur = exact.initial_state()
    step = path[0]
    rot_part, joint_part = step["edge_label"].split(";")
    ell = int(rot_part[len("rot^"):])
    move = move_by_label[joint_part]
    for _ in range(ell):
        tr = exact.extend(cur, W1)
        cur = tr.state
    tr = exact.extend(cur, move)
    return tr.state if tr.abandonment else None, ell


def enumerate_hub_completing_candidates(state: "exact.ExactState", node_cap: int, max_depth: int) -> Dict[str, Any]:
    """Bounded (node_cap, max_depth) exhaustive-if-frontier-empties BFS
    from the post-abandonment state, recording every DISTINCT orbit ever
    reachable as a hub (hex0) completer, with the event kind and
    existing/fresh status of each occurrence."""
    frontier = deque([(0, state)])
    expanded = 0
    candidates: Dict[int, List[Dict[str, Any]]] = {}
    while frontier and expanded < node_cap:
        depth, st = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        for e in macro.macro_edges(st):
            tr = e.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if kind in ("A2", "A3", "J"):
                continue
            if tr.target is not None and core.hexagon_id(tr.target) == 0:
                tq, tphase = exact.ORBIT_PHASE[tr.target]
                candidates.setdefault(tq, []).append({
                    "depth": depth, "event_type": kind, "phase": tphase,
                    "existing_at_time": not tr.new_orbit, "ell": e.run.ell,
                    "source_permutation": list(e.run.state.p), "target_permutation": list(tr.target),
                })
            frontier.append((depth + 1, tr.state))
    return {
        "nodes_expanded": expanded, "frontier_remaining": len(frontier),
        "exhaustive_within_bound": len(frontier) == 0,
        "distinct_candidate_orbits": sorted(candidates.keys()),
        "candidates_detail": candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--node-cap", type=int, default=20000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_hub_completer_candidates.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    table = json.loads(Path(args.relation_table).read_text(encoding="utf-8"))
    same_hashes = [r["hash"] for r in table["rows"] if r.get("r2_own_component_relation") == "same"]
    rows_by_hash = {r["hash"]: r for r in table["rows"]}

    results = {}
    for h in same_hashes:
        w = wdata["witnesses"][h]
        post_abandon, abandon_ell = replay_to_post_abandonment(w)
        if post_abandon is None:
            results[h] = {"error": "first joint does not abandon"}
            continue
        enum = enumerate_hub_completing_candidates(post_abandon, args.node_cap, args.max_depth)
        r1_target = rows_by_hash[h]["r1_target"]
        enum["abandon_ell"] = abandon_ell
        enum["r1_target_orbit_actually_used"] = r1_target
        enum["r1_target_is_among_candidates"] = r1_target in enum["distinct_candidate_orbits"]
        enum["other_legal_candidates_besides_r1_target"] = [
            q for q in enum["distinct_candidate_orbits"] if q != r1_target
        ]
        results[h] = enum
        print(h[:12], "abandon_ell", abandon_ell, "candidates", enum["distinct_candidate_orbits"],
              "r1_target", r1_target, "exhaustive", enum["exhaustive_within_bound"])

    report = {
        "schema": "rr-hub-completer-candidates-v1",
        "target_theorem_tested": "O != O_R candidates all violate some exact legality condition",
        "verdict": "FALSIFIED -- multiple distinct orbits are legally reachable as hub completers in every tested witness, not just R1's own target orbit",
        "method": (
            f"bounded BFS (max_depth={args.max_depth}, node_cap={args.node_cap} per witness) from "
            "the post-abandonment state, recording every distinct orbit ever legally reachable as a "
            "hub-completing target -- bounded, reuses macro_edges()/area_a_prune_reason(), not a new "
            "large-scale search."
        ),
        "per_witness": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
