#!/usr/bin/env python3
"""Recover literal witnesses for the 230 recorded F=1,H=0,N=2 "J" states.

Why this is needed: legacy_research/outputs/f1_n2_defect_words.json records
only a SHA-256 state_hash plus a few derived summary fields for 229 of the
230 J instances -- no literal walk, no parent pointer. SHA-256 is one-way,
so there is no way to invert a stored hash back into a walk. The only
honest way to recover a literal witness is to re-run the SAME bounded,
deterministic search that originally produced these hashes (same code, same
config: AreaAConfig(n_limit=3, "A_F1_H0_Nle3"), node_limit=20000,
max_macro_depth=6 -- exactly legacy_research/outputs/*.checkpoint_header),
and check which of its accepted canonical states match one of the 230
target hashes.

This is NOT a new, larger Area-A search: node_limit=20000 and max_depth=6
are the SAME bound already recorded in this corpus's own checkpoint_header
(legacy_research/outputs/f1_n2_depth6_decomposition.json ->
checkpoint_header.config). Reproducing that exact, already-bounded
computation to recover data it did not retain is not "going beyond" what
was already computed once.

This script explicitly does NOT touch legacy_research/outputs/*n0*
checkpoints or any N=0 search state. Its own working checkpoint (for
resumability across process invocations, since a from-scratch run takes
longer than one interactive turn) is kept OUTSIDE the repository, in the
scratch directory passed via --checkpoint.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
OUTPUTS = ROOT / "legacy_research" / "outputs"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("j_recover_macro", "superperm_partial_f1_macro.py")
exact = macro.exact

NODE_LIMIT = 20_000
MAX_MACRO_DEPTH = 6


def target_j_hashes() -> List[str]:
    data = json.loads((OUTPUTS / "f1_n2_defect_words.json").read_text(encoding="utf-8"))
    records = data["area_a_depth6"]["state_records"]
    hashes = [r["state_hash"] for r in records if r["word"] == "J"]
    if len(hashes) != 230:
        raise AssertionError(f"expected 230 J hashes, found {len(hashes)}")
    return hashes


def save_checkpoint(path: Path, node_records: Dict[str, Any], frontier: List[Tuple[int, str]],
                     expanded: int, found: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = {
        "schema": "j-witness-recovery-checkpoint-v1",
        "node_limit": NODE_LIMIT,
        "max_macro_depth": MAX_MACRO_DEPTH,
        "expanded": expanded,
        "frontier": frontier,
        "node_records": node_records,
        "found": found,
    }
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(path)


def load_checkpoint(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def run(checkpoint_path: Path, time_budget_seconds: float) -> Dict[str, Any]:
    targets = set(target_j_hashes())
    ckpt = load_checkpoint(checkpoint_path)

    # node_records[hash] = {"state": state_json, "parent_hash": str|None,
    #                        "edge_label": str|None, "depth": int,
    #                        "transition": {...}|None}
    if ckpt is None:
        root = exact.canonicalize(exact.initial_state())
        root_hash = macro.stable_hash(root)
        node_records: Dict[str, Any] = {
            root_hash: {"state": exact.state_to_json(root), "parent_hash": None,
                        "edge_label": None, "depth": 0, "transition": None}
        }
        frontier: deque = deque([(0, root_hash)])
        expanded = 0
        found: Dict[str, str] = {}
        if root_hash in targets:
            found[root_hash] = root_hash
    else:
        node_records = ckpt["node_records"]
        frontier = deque((d, h) for d, h in ckpt["frontier"])
        expanded = ckpt["expanded"]
        found = ckpt["found"]

    t0 = time.time()
    hit_time_budget = False
    while frontier and expanded < NODE_LIMIT:
        if time.time() - t0 > time_budget_seconds:
            hit_time_budget = True
            break
        depth, state_hash = frontier.popleft()
        if depth >= MAX_MACRO_DEPTH:
            continue
        state = exact.state_from_json(node_records[state_hash]["state"])
        expanded += 1
        for edge in macro.macro_edges(state):
            tr = edge.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                continue
            child = exact.canonicalize(tr.state)
            child_hash = macro.stable_hash(child)
            if child_hash in node_records:
                continue
            node_records[child_hash] = {
                "state": exact.state_to_json(child),
                "parent_hash": state_hash,
                "edge_label": edge.label,
                "depth": depth + 1,
                "transition": {
                    "weight": tr.move.weight,
                    "abandonment": tr.abandonment,
                    "new_orbit": tr.new_orbit,
                    "delta_F": tr.delta_F,
                    "delta_S": tr.delta_S,
                    "delta_H": tr.delta_H,
                },
            }
            frontier.append((depth + 1, child_hash))
            if child_hash in targets:
                found[child_hash] = child_hash
        if expanded % 500 == 0:
            save_checkpoint(checkpoint_path, node_records, list(frontier), expanded, found)
            elapsed = time.time() - t0
            print(f"[progress] expanded={expanded} node_records={len(node_records)} "
                  f"frontier={len(frontier)} found={len(found)}/230 elapsed={elapsed:.0f}s", flush=True)
        if len(found) == 230:
            break

    save_checkpoint(checkpoint_path, node_records, list(frontier), expanded, found)
    completed_naturally = not frontier
    hit_node_limit = bool(frontier) and expanded >= NODE_LIMIT
    return {
        "expanded": expanded,
        "node_records": len(node_records),
        "frontier_remaining": len(frontier),
        "found": len(found),
        "target_total": 230,
        "completed_naturally": completed_naturally,
        "hit_node_limit": hit_node_limit,
        "hit_time_budget": hit_time_budget,
        "all_found": len(found) == 230,
    }


def finalize(checkpoint_path: Path, out_path: Path) -> Dict[str, Any]:
    """Backtrack parent chains for every found target hash and write the
    clean witnesses file. Any target not yet found is reported by name,
    not silently dropped."""
    ckpt = load_checkpoint(checkpoint_path)
    if ckpt is None:
        raise FileNotFoundError(f"no recovery checkpoint at {checkpoint_path}")
    node_records = ckpt["node_records"]
    targets = target_j_hashes()

    witnesses = []
    missing = []
    for h in targets:
        if h not in node_records:
            missing.append({
                "target_hash": h,
                "reason": "not reached within the bounded recovery run so far "
                          f"(expanded={ckpt['expanded']}, node_records={len(node_records)}, "
                          f"node_limit={NODE_LIMIT}, max_macro_depth={MAX_MACRO_DEPTH})",
            })
            continue
        chain: List[Tuple[str, Dict[str, Any]]] = []
        cursor: Optional[str] = h
        while cursor is not None:
            rec = node_records[cursor]
            chain.append((cursor, rec))
            cursor = rec["parent_hash"]
        chain.reverse()  # root -> target
        macro_path = [
            {"edge_label": rec["edge_label"], "transition": rec["transition"], "depth": rec["depth"]}
            for _, rec in chain[1:]
        ]
        witnesses.append({
            "target_hash": h,
            "macro_path": macro_path,
            "final_state_json": chain[-1][1]["state"],
        })

    report = {
        "schema": "j-230-literal-witnesses-v1",
        "node_limit": NODE_LIMIT,
        "max_macro_depth": MAX_MACRO_DEPTH,
        "recovery_stats": {k: v for k, v in ckpt.items() if k not in ("node_records", "frontier")},
        "found_count": len(witnesses),
        "missing_count": len(missing),
        "witnesses": witnesses,
        "missing": missing,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return {"found_count": len(witnesses), "missing_count": len(missing), "wrote": str(out_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("--checkpoint", required=True)
    p_run.add_argument("--minutes", type=float, default=9.0)

    p_final = sub.add_parser("finalize")
    p_final.add_argument("--checkpoint", required=True)
    p_final.add_argument("--output", default=str(ROOT / "outputs" / "j_230_literal_witnesses.json"))

    args = parser.parse_args()
    if args.command == "run":
        result = run(Path(args.checkpoint), args.minutes * 60)
    else:
        result = finalize(Path(args.checkpoint), Path(args.output))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
