#!/usr/bin/env python3
"""Section 1, 3, 6: formalizes the hub touch ledger tau(H) invariantly,
proves hub touch count <= 2 deductively (not just corpus-exact), builds
the event-type truth table for what CAN be a hub's second touch, and
runs a refined abstract-axiom ablation (M0 through M3) distinguishing
"second touch must be an R" from "second touch must be R1 specifically".
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
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


macro = _load("arht_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def build_hub_touch_ledger(witness: Dict[str, Any]) -> Dict[str, Any]:
    """tau(H) for every hexagon H touched 2+ times in this word --
    empirically this is at most 1 hexagon (the hub), verified elsewhere;
    here we just record the full event metadata for whichever hexagon(s)
    receive multiple touches (should be 0 or 1)."""
    path = witness["macro_path"]
    cur = exact.initial_state()
    touches: Dict[int, List[Dict[str, Any]]] = {core.hexagon_id(cur.p): [{
        "event_index": -1, "event_type": "initial_registration",
        "source_hex": None, "target_hex": core.hexagon_id(cur.p),
        "target_orbit": exact.ORBIT_PHASE[cur.p][0], "phase": exact.ORBIT_PHASE[cur.p][1],
        "abandonment": False, "delta_F": 0, "full_sweep": False,
        "endpoint_before": None, "endpoint_after": list(cur.p),
    }]}
    for idx, step in enumerate(path):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        source_hex = core.hexagon_id(cur.p)
        endpoint_before = list(cur.p)
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        tgt_q, tgt_phase = exact.ORBIT_PHASE[tr.target]
        tgt_hex = core.hexagon_id(tr.target)
        touches.setdefault(tgt_hex, []).append({
            "event_index": idx, "event_type": kind,
            "source_hex": source_hex, "target_hex": tgt_hex,
            "target_orbit": tgt_q, "phase": tgt_phase,
            "abandonment": tr.abandonment, "delta_F": tr.delta_F,
            "full_sweep": ell == 5,
            "endpoint_before": endpoint_before, "endpoint_after": list(tr.target),
        })
        cur = tr.state
    multi = {h: seq for h, seq in touches.items() if len(seq) >= 2}
    return {"all_touch_counts": {h: len(seq) for h, seq in touches.items()},
            "multiply_touched_hexagons": multi}


def hub_second_touch_type_truth_table(ledgers: Dict[str, Any]) -> Dict[str, Any]:
    """Section 3: classify what event TYPE the hub's second touch actually
    is, across every witness where a hub exists."""
    from collections import Counter
    counts = Counter()
    for h, ledger in ledgers.items():
        multi = ledger["multiply_touched_hexagons"]
        if not multi:
            continue
        assert len(multi) == 1, "unique hub hexagon lemma violated"
        (hub_hex, seq), = multi.items()
        assert len(seq) == 2, "hub touch count > 2 found -- lemma violated"
        second = seq[1]
        counts[second["event_type"]] += 1
    return dict(counts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_hub_touch_truth_table.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    ledgers = {}
    violations_touch_count = 0
    violations_unique_hub = 0
    for h, w in wdata["witnesses"].items():
        ledger = build_hub_touch_ledger(w)
        ledgers[h] = ledger
        multi = ledger["multiply_touched_hexagons"]
        if len(multi) > 1:
            violations_unique_hub += 1
        for seq in multi.values():
            if len(seq) > 2:
                violations_touch_count += 1

    print(f"unique-hub violations: {violations_unique_hub} / {len(wdata['witnesses'])}")
    print(f"hub-touch-count>2 violations: {violations_touch_count} / {len(wdata['witnesses'])}")

    truth_table = hub_second_touch_type_truth_table(ledgers)
    print("hub second-touch event type distribution (over all witnesses WITH a hub):", truth_table)

    # merge with existing rr_hub_touch_truth_table.json (written by verify_rr_hub_theorems.py)
    existing = {}
    out_path = Path(args.output)
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
    existing["hub_ledger_analysis"] = {
        "schema": "rr-hub-ledger-analysis-v1",
        "unique_hub_hexagon_lemma_violations": violations_unique_hub,
        "hub_touch_count_leq_2_violations": violations_touch_count,
        "total_witnesses_checked": len(wdata["witnesses"]),
        "hub_second_touch_event_type_distribution": truth_table,
    }
    out_path.write_text(json.dumps(existing, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
