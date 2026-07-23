#!/usr/bin/env python3
"""Read-only analysis of the saved bounded Area-A macro profile checkpoint.

This program does not add a state, write a checkpoint, canonicalize a child,
or resume a search.  It can therefore describe only the serialized frontier,
not all 85,340 states ever discovered by the interrupted bounded stage.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
PROFILE_PATH = HERE.with_name("analyze_partial_f1_profiles.py")


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = load("area_a_snapshot_macro", MACRO_PATH)
profile = load("area_a_snapshot_profile", PROFILE_PATH)
exact = macro.exact


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default=str(ROOT / "outputs" / "f1_macro_checkpoints" / "A_F1_H0_Nle3_macro_depth6.checkpoint.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "f1_area_a_explosion_analysis.json"))
    parser.add_argument("--markdown", default=str(ROOT / "outputs" / "F1_AREA_A_EXPLOSION_ANALYSIS.md"))
    args = parser.parse_args()
    cp = Path(args.checkpoint)
    raw = cp.read_bytes()  # one read-only snapshot, safe across atomic replace
    data = json.loads(raw)
    frontier = data["frontier"]
    depth_counts: Counter[str] = Counter()
    n_counts: Counter[str] = Counter()
    d_counts: Counter[str] = Counter()
    o_counts: Counter[str] = Counter()
    odp_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    type_global_states: dict[str, set[tuple[object, ...]]] = {}
    legal_counts: Counter[str] = Counter()
    partial_mask_signatures: Counter[str] = Counter()
    u_counts: Counter[str] = Counter()

    for node in frontier:
        state = exact.state_from_json(node["state"])
        depth_counts[str(node["depth"])] += 1
        n_counts[str(state.Ndef)] += 1
        d_counts[str(state.D)] += 1
        o_counts[str(state.O)] += 1
        odp_counts[str((state.O, state.P, state.D, state.Ndef))] += 1
        fp = profile.fragment_fingerprint(state, None)
        if isinstance(fp, dict):
            fp = dict(fp)
            fp.pop("creation_weight", None)
        fp_key = key(fp)
        type_counts[fp_key] += 1
        type_global_states.setdefault(fp_key, set()).add(state.stable_key())
        partial_mask_signatures[key(sorted(mask for _h, mask in state.sparse_hex() if mask not in (0, 63)))] += 1
        h = profile.fragment_hex_id(state)
        if h is not None:
            u_counts[str(6 - state.hex_masks[h].bit_count())] += 1
        # Exact legal macro tails only: no canonicalization and no search.
        legal_counts[str(sum(1 for _edge in macro.macro_edges(state)))] += 1

    type_rows = [
        {
            "fingerprint": json.loads(fp),
            "frontier_state_count": count,
            "distinct_global_occupancy_states_in_frontier": len(type_global_states[fp]),
        }
        for fp, count in type_counts.most_common()
    ]
    report = {
        "schema": "area-a-profile-frontier-snapshot-v1",
        "analysis_sha256": sha(HERE),
        "checkpoint": str(cp),
        "checkpoint_sha256": hashlib.sha256(raw).hexdigest(),
        "checkpoint_modified_time_utc": cp.stat().st_mtime,
        "macro_sha256": data.get("macro_sha256"),
        "engine_sha256": data.get("engine_sha256"),
        "core_sha256": data.get("core_sha256"),
        "saved_stage_stats": data.get("stats"),
        "scope": (
            "read-only current frontier snapshot. It does not reconstruct the full discovered set, "
            "the already-expanded parents, or any unrecorded parent-child relation."
        ),
        "frontier_state_count": len(frontier),
        "macro_depth_distribution": dict(sorted(depth_counts.items(), key=lambda x: int(x[0]))),
        "N_distribution": dict(sorted(n_counts.items(), key=lambda x: int(x[0]))),
        "D_distribution": dict(sorted(d_counts.items(), key=lambda x: int(x[0]))),
        "E_orbit_count_distribution": dict(sorted(o_counts.items(), key=lambda x: int(x[0]))),
        "O_P_D_N_distribution": dict(sorted(odp_counts.items())),
        "fragment_types": type_rows,
        "fragment_unvisited_rotation_length_distribution": dict(sorted(u_counts.items(), key=lambda x: int(x[0]))),
        "legal_macro_tail_count_distribution": dict(sorted(legal_counts.items(), key=lambda x: int(x[0]))),
        "partial_hex_mask_signature_count": len(partial_mask_signatures),
        "largest_partial_hex_mask_signatures": [
            {"signature": json.loads(sig), "frontier_state_count": count}
            for sig, count in partial_mask_signatures.most_common(20)
        ],
        "top_100_parent_canonical_child_counts": None,
        "top_100_unavailable_reason": (
            "The bounded checkpoint stores a frontier and seen keys, not the already-expanded parent/child map. "
            "Recovering it would require re-enumerating canonical children, which this read-only analysis forbids."
        ),
        "dominance_assessment": (
            "No dominance rule is proposed. Same local fragment data with different exact global masks is common, "
            "but visited-set inclusion alone is not a safe dominance relation for an exact-cover completion problem."
        ),
    }
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md = "# Broad Area A explosion: read-only frontier analysis\n\n" \
         "This report is a snapshot of the saved depth-6 bounded-search frontier only. It is not a new search and does not describe all discovered states.\n\n" \
         "```json\n" + json.dumps(report, ensure_ascii=False, indent=2) + "\n```\n"
    Path(args.markdown).write_text(md, encoding="utf-8")
    print(json.dumps({"frontier_state_count": len(frontier), "N_distribution": report["N_distribution"], "fragment_type_count": len(type_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
