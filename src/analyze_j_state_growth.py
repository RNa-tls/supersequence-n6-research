#!/usr/bin/env python3
"""Depth-by-depth branching decomposition for the 9 unresolved J seeds.

Answers, per depth, per seed: how many children are generated, how many
survive each prune reason, how many distinct canonical states result, and
what fraction of "new" states differ from already-seen ones only in
endpoint / visited_count / Phi / local orbit-hexagon signature versus
genuinely differing in their full visited mask.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict, deque
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


macro = _load("growth_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def profile_seed(seed_state: "exact.ExactState", max_depth: int, node_cap: int) -> Dict[str, Any]:
    root = exact.canonicalize(seed_state)
    root_hash = macro.stable_hash(root)
    node_records = {root_hash: root}
    frontier: deque = deque([(0, root_hash)])
    expanded = 0

    per_depth: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
        "generated_children": 0, "legal_children": 0, "canonical_unique_children": 0,
        "exact_duplicate_children": 0, "prune_reason_counts": Counter(),
        "endpoint_counts": Counter(), "visited_count_counts": Counter(),
        "phi_counts": Counter(), "branching_factors": [],
    })

    while frontier and expanded < node_cap:
        depth, state_hash = frontier.popleft()
        if depth >= max_depth:
            continue
        state = node_records[state_hash]
        expanded += 1
        bucket = per_depth[depth]
        legal_this_state = 0
        for edge in macro.macro_edges(state):
            bucket["generated_children"] += 1
            tr = edge.joint
            if tr.abandonment:
                bucket["prune_reason_counts"]["would_require_new_abandonment_impossible"] += 1
                continue
            child = tr.state
            if phi(child) < 0:
                bucket["prune_reason_counts"]["remaining_cover_capacity_impossible"] += 1
                continue
            reason = macro.area_a_prune_reason(child, macro.AREA_A)
            if reason is not None:
                bucket["prune_reason_counts"][reason] += 1
                continue
            bucket["legal_children"] += 1
            legal_this_state += 1
            bucket["endpoint_counts"][tuple(child.p)] += 1
            bucket["visited_count_counts"][child.visited_count] += 1
            bucket["phi_counts"][phi(child)] += 1
            canon = exact.canonicalize(child)
            canon_hash = macro.stable_hash(canon)
            if canon_hash in node_records:
                bucket["exact_duplicate_children"] += 1
                continue
            bucket["canonical_unique_children"] += 1
            node_records[canon_hash] = canon
            frontier.append((depth + 1, canon_hash))
        bucket["branching_factors"].append(legal_this_state)

    result = {}
    for depth, bucket in sorted(per_depth.items()):
        bf = bucket["branching_factors"]
        result[str(depth)] = {
            "generated_children": bucket["generated_children"],
            "legal_children": bucket["legal_children"],
            "canonical_unique_children": bucket["canonical_unique_children"],
            "exact_duplicate_children": bucket["exact_duplicate_children"],
            "prune_reason_counts": dict(bucket["prune_reason_counts"]),
            "distinct_endpoints_among_children": len(bucket["endpoint_counts"]),
            "distinct_visited_counts_among_children": len(bucket["visited_count_counts"]),
            "distinct_phi_values_among_children": dict(sorted(bucket["phi_counts"].items())),
            "states_expanded_at_this_depth": len(bf),
            "avg_branching_factor": round(sum(bf) / len(bf), 3) if bf else None,
            "max_branching_factor": max(bf) if bf else None,
        }
    return {
        "expanded_total": expanded,
        "canonical_states_total": len(node_records),
        "per_depth": result,
    }


def main() -> None:
    witnesses = {
        w["target_hash"]: exact.state_from_json(w["final_state_json"])
        for w in json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    }
    nine = sorted([
        "45929408de25b866a834c1fe59a79dba3e3d6427efdca37b22220d469d015459",
        "624257c39b75859d58f62e3c7f1369ecea9ce84434d6df14b4b67950abf6b21a",
        "6b42cfe0deafcfa4344e18928f6c7b173dffa0a11a10fd341bb536417e080117",
        "ad74dbc3a5f5c987c4d8595bd5c40f95ce820aafda92009dabd097b57b83acee",
        "c652843b153b6c7b12f1afcbd7f45ac7f467f74dc17706f410de3ab26d3ed6c3",
        "e0f8ed14b4832a7272cbf641aa7ed449588d195046e359d2f61a74ef76dce184",
        "eaa42caf37c5f6ad1ebaa3268d0969e7acbae46f471d66cbc644d2cbb340af63",
        "f4e71fe28ebaa10b5f525b78e86b174fc323fdc6428421731471201dafcff1a9",
        "f95ab0147fb90de8477d344e8e8fc7fca3283357e8bcdc62c0d093d7e69cfb2e",
    ])

    results = []
    t0 = time.time()
    for h in nine:
        r = profile_seed(witnesses[h], max_depth=4, node_cap=400)
        results.append({"target_hash": h, "profile": r})
        print(f"{h[:12]} expanded={r['expanded_total']} canonical={r['canonical_states_total']} "
              f"elapsed={time.time()-t0:.1f}s", flush=True)

    out = {"schema": "j-branching-profile-v1", "config": {"max_depth": 4, "node_cap": 400}, "seeds": results}
    (ROOT / "outputs" / "j_branching_profile.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(json.dumps({"wrote": "outputs/j_branching_profile.json", "seeds": len(results)}, indent=2))


if __name__ == "__main__":
    main()
