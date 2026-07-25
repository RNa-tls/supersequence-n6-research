#!/usr/bin/env python3
"""Round 15, section 1: replays every RR witness and records the exact
abandonment event -- its ell (rotation offset within hex0), the residual
hex0 positions/orbits left unvisited, and whether/how the hub (hex0) is
later completed (second touch), and whether R2 is same-component.

No new search: reuses outputs/rr_literal_witnesses.json and
outputs/rr_full_relation_table.json, which already contain the full
4,470-witness RR corpus recovered in Round 11.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

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


macro = _load("araae_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1

# hex0's fixed position -> orbit table (established Round 12).
HEX0_POSITION_ORBIT = [0, 120, 33, 9, 3, 1]


def replay(word: dict):
    """Replay one witness's macro_path, return per-macro-edge transition info."""
    cur = exact.initial_state()
    hex0 = core.hexagon_id(cur.p)
    steps = []
    for idx, step in enumerate(word["macro_path"]):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        sq, sph = exact.ORBIT_PHASE[cur.p]
        tq, tph = exact.ORBIT_PHASE[tr.target]
        steps.append({
            "idx": idx,
            "ell": ell,
            "abandonment": tr.abandonment,
            "new_orbit": tr.new_orbit,
            "weight": tr.move.weight,
            "source_hex": core.hexagon_id(cur.p),
            "target_hex": core.hexagon_id(tr.target),
            "source_orbit": sq,
            "target_orbit": tq,
        })
        cur = tr.state
    return hex0, steps


def main() -> None:
    wdata = json.loads((ROOT / "outputs" / "rr_literal_witnesses.json").read_text(encoding="utf-8"))
    table = json.loads((ROOT / "outputs" / "rr_full_relation_table.json").read_text(encoding="utf-8"))
    rows = {r["hash"]: r for r in table["rows"] if "error" not in r}

    records = []
    ell_dist = Counter()
    ell_same_dist = Counter()

    for h, w in wdata["witnesses"].items():
        if h not in rows:
            continue
        row = rows[h]
        hex0, steps = replay(w)
        abandon_steps = [s for s in steps if s["abandonment"]]
        assert len(abandon_steps) == 1, f"witness {h} has {len(abandon_steps)} abandonment events"
        ab = abandon_steps[0]
        abandon_ell = ab["ell"]
        residual_positions = list(range(abandon_ell + 1, 6))
        residual_orbits = [HEX0_POSITION_ORBIT[p] for p in residual_positions]

        # hub (hex0) second-touch search: first later step whose target_hex == hex0
        completer = None
        for s in steps:
            if s["idx"] <= ab["idx"]:
                continue
            if s["target_hex"] == hex0:
                completer = s
                break

        rec = {
            "hash": h,
            "abandon_ell": abandon_ell,
            "residual_position_count": len(residual_positions),
            "residual_orbits": residual_orbits,
            "hub_completer_found": completer is not None,
            "completer_orbit": completer["target_orbit"] if completer else None,
            "completer_idx_gap": (completer["idx"] - ab["idx"]) if completer else None,
            "completer_event_weight": completer["weight"] if completer else None,
            "completer_is_new_orbit": completer["new_orbit"] if completer else None,
            "chaining": row["chaining"],
            "r2_relation": row["r2_own_component_relation"],
        }
        records.append(rec)
        ell_dist[abandon_ell] += 1
        if row["r2_own_component_relation"] == "same":
            ell_same_dist[abandon_ell] += 1

    # Section 1 table: per-ell hex0 state right after abandonment.
    ell_table = {}
    for ell in range(6):
        residual_positions = list(range(ell + 1, 6))
        residual_orbits = [HEX0_POSITION_ORBIT[p] for p in residual_positions]
        ell_table[str(ell)] = {
            "residual_position_count": len(residual_positions),
            "residual_positions": residual_positions,
            "residual_orbits": residual_orbits,
            "completer_uniquely_forced": len(residual_positions) == 1,
            "witness_count": ell_dist.get(ell, 0),
            "same_component_count": ell_same_dist.get(ell, 0),
        }

    report = {
        "schema": "rr-abandonment-ell-table-v1",
        "total_rr_witnesses": len(records),
        "ell_table": ell_table,
        "ell_distribution": dict(sorted(ell_dist.items())),
        "same_component_by_ell": dict(sorted(ell_same_dist.items())),
        "records": records,
    }
    out = ROOT / "outputs" / "rr_abandonment_ell_table.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", out)
    print("ell distribution:", dict(sorted(ell_dist.items())))
    print("same-component by ell:", dict(sorted(ell_same_dist.items())))

    # cross-tab: completer_orbit==1 vs ell vs same
    cross = Counter()
    for r in records:
        cross[(r["abandon_ell"], r["hub_completer_found"], r["completer_orbit"] == 1, r["r2_relation"] == "same")] += 1
    for k in sorted(cross):
        print(k, cross[k])


if __name__ == "__main__":
    main()
