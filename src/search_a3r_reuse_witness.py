#!/usr/bin/env python3
"""Section 10: express the A3R "no pre-R reuse of A3's target orbit"
observation (298/298 stored corpus, from research/RA3_A3R_ORBIT_HISTORY_ASYMMETRY.md,
an EARLIER round -- not re-derived here) in orbit-history language, and --
since no deductive proof of impossibility exists -- run a SMALL BOUNDED
local search (not a new large-scale search) from a handful of A3R witnesses'
post-A3 states, looking for the minimum-depth witness where R reuses A3's
own just-opened orbit.

Scope discipline: sample_size witnesses (default 298, i.e. the FULL stored
A3R corpus -- not a new large-scale continuation search, since each
witness's post-A3 state is only explored ONE macro-edge deep, default
max_depth=1, node_cap=1000 -- a single macro_edges() call per witness).

RESULT (this round): a legal, unpruned R-kind macro-edge that reuses A3's
own just-opened target orbit exists at depth 1 for ALL 298/298 stored
A3R witnesses. This means the "0/298 no pre-R reuse" observation from the
earlier round's research/RA3_A3R_ORBIT_HISTORY_ASYMMETRY.md is a fact
about which SPECIFIC path each stored witness's own recorded macro_path
happens to take (it doesn't route through the reuse), NOT a structural
impossibility -- an immediate reuse continuation is trivially reachable
from every sampled post-A3 state. See research/A3R_TARGET_REUSE_STATUS.md.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

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


macro = _load("sarw_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def replay_to_post_a3(witness: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Raw (never-canonicalized) replay, locating the word's A3 event and
    returning the state immediately after it fires, plus the orbit id it
    opened (in this same raw frame -- consistent since never relabeled)."""
    path = witness["macro_path"]
    cur = exact.initial_state()
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
        if kind == "A3":
            q, _phase = exact.ORBIT_PHASE[tr.target]
            return {"post_a3_state": cur, "a3_target_orbit_q": q}
    return None


def bounded_search_for_reuse(post_a3_state: "exact.ExactState", a3_orbit_q: int, max_depth: int, node_cap: int) -> Dict[str, Any]:
    """Small bounded BFS from post_a3_state, looking for the shallowest R
    event whose target orbit equals a3_orbit_q (i.e. R reusing A3's own
    just-opened orbit before any other abandonment could reset F)."""
    frontier = deque([(0, post_a3_state)])
    expanded = 0
    min_depth_found = None
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
            if kind == "R" and tr.target is not None:
                q, _phase = exact.ORBIT_PHASE[tr.target]
                if q == a3_orbit_q and min_depth_found is None:
                    min_depth_found = depth + 1
            if kind in ("A2", "A3", "J"):
                continue  # word already has its one abandonment (A3); further abandoning events are out of scope for this specific question
            frontier.append((depth + 1, tr.state))
    return {
        "min_depth_reuse_witness_found": min_depth_found,
        "nodes_expanded": expanded,
        "frontier_remaining": len(frontier),
        "exhaustive_within_bound": len(frontier) == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--sample-size", type=int, default=298)
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--node-cap", type=int, default=1000)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "a3r_reuse_search.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    a3r_witnesses = ledger["words"]["A3R"]["witnesses"][: args.sample_size]

    results = {}
    any_reuse_found = 0
    for w in a3r_witnesses:
        h = w["target_hash"]
        info = replay_to_post_a3(w)
        if info is None:
            results[h] = {"error": "no A3 event found in macro_path"}
            continue
        search = bounded_search_for_reuse(info["post_a3_state"], info["a3_target_orbit_q"], args.max_depth, args.node_cap)
        results[h] = {"a3_target_orbit_q_raw": info["a3_target_orbit_q"], **search}
        if search["min_depth_reuse_witness_found"] is not None:
            any_reuse_found += 1
        print(h[:12], "a3_orbit", info["a3_target_orbit_q"], "min_depth_reuse", search["min_depth_reuse_witness_found"],
              "exhaustive", search["exhaustive_within_bound"])

    report = {
        "schema": "a3r-reuse-search-v1",
        "method": (
            f"bounded local search (max_depth={args.max_depth}, "
            f"node_cap={args.node_cap}) from the state immediately after A3 "
            f"fires, over a SAMPLE of {len(a3r_witnesses)} (of 298 stored) "
            "A3R witnesses -- looking for the shallowest R event that "
            "targets the SAME orbit A3 just opened. This is a small, bounded "
            "search, not a repeat of any prior large-scale continuation "
            "search."
        ),
        "sample_size": len(a3r_witnesses),
        "witnesses_with_reuse_found_within_bound": any_reuse_found,
        "per_witness": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "witnesses_with_reuse_found_within_bound": any_reuse_found, "sample_size": len(a3r_witnesses)}, indent=2))


if __name__ == "__main__":
    main()
