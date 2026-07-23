#!/usr/bin/env python3
"""Seed-level exact closure search for the 9 J states unresolved by the
bounded budget search in outputs/j_budget_search.json.

Design note (deviating from a literal per-charge-word subproblem split):
a state's remaining shortfall budget Phi is already a deterministic
function of its canonical (P, visited_count) -- two different historical
charge-word paths that reach the SAME canonical state have identical Phi
and an identical future. Partitioning the search into independent
per-charge-word subproblems (as originally suggested) would therefore
duplicate work across word-subproblems that converge on the same
canonical states, actively hurting the canonical memoization this search
depends on for tractability. Instead this runs ONE canonical-memoized
exhaustive search per seed (which automatically respects every valid
charge-word simultaneously, since Phi>=0 is checked via
area_a_prune_reason regardless of which word produced it), and reports,
as metadata, which charge shapes were actually traversed.

Termination per seed is exactly one of:
  - CLOSED: frontier exhausted (empty), zero success certificates found
    among all reachable canonical states -- every legal branch failed.
  - SUCCESS: a full completion (area_a_final, or a legal trailing
    pure-rotation-only suffix) was found.
  - INCOMPLETE: node cap / time budget hit with frontier still non-empty.
    Never reported as failure.

Checkpointing matches the pattern already used for J-witness recovery
(src/recover_j_witnesses.py): JSON, atomic writes, resumable, stored
outside the repository by the caller.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


macro = _load("j9_exact_macro", "superperm_partial_f1_macro.py")
exact = macro.exact

sys.path.insert(0, str(ROOT / "src"))
import verify_pure_rotation_suffix as prs  # noqa: E402


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


CODE_SHA256 = __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()


def save_checkpoint(path: Path, seed_hash: str, node_records: Dict[str, Any],
                     frontier: List[Tuple[int, str]], expanded: int,
                     prune_counts: Dict[str, int], success_hashes: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = {
        "schema": "j9-exact-search-checkpoint-v1",
        "code_sha256": CODE_SHA256,
        "engine_sha256": exact.CODE_SHA256,
        "macro_sha256": macro.CODE_SHA256,
        "seed_hash": seed_hash,
        "expanded": expanded,
        "frontier": frontier,
        "node_records": node_records,
        "prune_counts": prune_counts,
        "success_hashes": success_hashes,
    }
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(path)


def load_checkpoint(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("code_sha256") != CODE_SHA256 or data.get("engine_sha256") != exact.CODE_SHA256:
        raise ValueError("refusing resume across code SHA change")
    return data


def exhaust_seed(
    seed_state: "exact.ExactState",
    seed_hash: str,
    node_cap: int,
    time_budget_seconds: float,
    checkpoint_path: Optional[Path],
    checkpoint_every: int,
) -> Dict[str, Any]:
    ckpt = load_checkpoint(checkpoint_path) if checkpoint_path is not None else None
    if ckpt is not None:
        node_records = ckpt["node_records"]
        frontier: deque = deque((d, h) for d, h in ckpt["frontier"])
        expanded = ckpt["expanded"]
        prune_counts: Counter = Counter(ckpt["prune_counts"])
        success_hashes = list(ckpt["success_hashes"])
    else:
        root = exact.canonicalize(seed_state)
        root_hash = macro.stable_hash(root)
        node_records = {root_hash: exact.state_to_json(root)}
        frontier = deque([(0, root_hash)])
        expanded = 0
        prune_counts = Counter()
        success_hashes = []

    t0 = time.time()
    hit_time_budget = False
    hit_node_cap = False
    charge_shapes_seen: Counter = Counter()

    while frontier:
        if expanded >= node_cap:
            hit_node_cap = True
            break
        if time.time() - t0 > time_budget_seconds:
            hit_time_budget = True
            break
        depth, state_hash = frontier.popleft()
        state = exact.state_from_json(node_records[state_hash])
        expanded += 1

        # Check trailing pure-rotation-only completion before expanding
        # further (matches the legacy engine's own rotation_only_success
        # handling, cross-checked with the independent verifier).
        for run in macro.rotation_runs(state):
            if macro.area_a_final(run.state, macro.AREA_A) or prs.can_complete_via_pure_rotation(run.state).can_complete:
                if state_hash not in success_hashes:
                    success_hashes.append(state_hash)

        for edge in macro.macro_edges(state):
            tr = edge.joint
            if tr.abandonment:
                prune_counts["would_require_new_abandonment_impossible"] += 1
                continue
            child = tr.state
            child_phi = phi(child)
            if child_phi < 0:
                prune_counts["remaining_cover_capacity_impossible"] += 1
                charge_shapes_seen[5 - edge.run.ell] += 1
                continue
            reason = macro.area_a_prune_reason(child, macro.AREA_A)
            if reason is not None:
                prune_counts[reason] += 1
                continue
            canon = exact.canonicalize(child)
            canon_hash = macro.stable_hash(canon)
            if canon_hash in node_records:
                prune_counts["canonical_memo_duplicate"] += 1
                continue
            node_records[canon_hash] = exact.state_to_json(canon)
            frontier.append((depth + 1, canon_hash))
            if macro.area_a_final(canon, macro.AREA_A):
                success_hashes.append(canon_hash)

        if checkpoint_path is not None and expanded % checkpoint_every == 0:
            save_checkpoint(checkpoint_path, seed_hash, node_records, list(frontier),
                             expanded, dict(prune_counts), success_hashes)

    if checkpoint_path is not None:
        save_checkpoint(checkpoint_path, seed_hash, node_records, list(frontier),
                         expanded, dict(prune_counts), success_hashes)

    status = (
        "SUCCESS" if success_hashes else
        "CLOSED" if not frontier else
        "INCOMPLETE"
    )
    return {
        "seed_hash": seed_hash,
        "status": status,
        "expanded": expanded,
        "canonical_states_recorded": len(node_records),
        "frontier_remaining": len(frontier),
        "hit_node_cap": hit_node_cap,
        "hit_time_budget": hit_time_budget,
        "elapsed_seconds": round(time.time() - t0, 1),
        "prune_counts": dict(sorted(prune_counts.items())),
        "success_hashes": success_hashes,
        "charge_shapes_at_capacity_failure": dict(sorted(charge_shapes_seen.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-hash", required=True)
    parser.add_argument("--node-cap", type=int, default=100_000)
    parser.add_argument("--minutes", type=float, default=9.0)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    witnesses = {
        w["target_hash"]: exact.state_from_json(w["final_state_json"])
        for w in json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    }
    seed_state = witnesses[args.seed_hash]
    result = exhaust_seed(
        seed_state, args.seed_hash, args.node_cap, args.minutes * 60,
        Path(args.checkpoint), checkpoint_every=2000,
    )
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "success_hashes"}, indent=2))


if __name__ == "__main__":
    main()
