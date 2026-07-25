#!/usr/bin/env python3
"""Round 14, section 7: extracts the exact normal form of the 6
non-R1-completer same-component witnesses, classifying each by
(R1 index, completer index, intervening word, target orbit) --
producing outputs/rr_delayed_completer_normal_forms.json.

Also re-verifies (section 3 groundwork): for each same-component
witness, the role trajectory of O_R (R1's target orbit) -- when it
first becomes existing, its incidence with the hub, and its component
root relationship.
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


macro = _load("vroi_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def full_event_ledger(witness: Dict[str, Any]) -> List[Dict[str, Any]]:
    path = witness["macro_path"]
    cur = exact.initial_state()
    events = []
    for idx, step in enumerate(path):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        tgt_q, tgt_phase = exact.ORBIT_PHASE[tr.target]
        events.append({
            "index": idx, "kind": kind, "ell": ell,
            "target_orbit": tgt_q, "target_phase": tgt_phase,
            "target_hexagon": core.hexagon_id(tr.target),
        })
        cur = tr.state
    return events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_delayed_completer_normal_forms.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    table = json.loads(Path(args.relation_table).read_text(encoding="utf-8"))
    same_hashes = [r["hash"] for r in table["rows"] if r.get("r2_own_component_relation") == "same"]

    normal_forms = {}
    for h in same_hashes:
        w = wdata["witnesses"][h]
        events = full_event_ledger(w)
        r_events = [e for e in events if e["kind"] == "R"]
        r1_idx = r_events[0]["index"]
        r1_target = r_events[0]["target_orbit"]
        # hub (hex0) touches (including the implicit initial registration at index -1)
        hub_touches = [-1] + [e["index"] for e in events if e["target_hexagon"] == 0]
        completer_idx = hub_touches[1] if len(hub_touches) > 1 else None
        completer_orbit = events[completer_idx]["target_orbit"] if completer_idx is not None else None
        is_r1_completer = completer_idx == r1_idx
        intervening = [events[i]["kind"] for i in range(r1_idx + 1, completer_idx)] if (completer_idx is not None and completer_idx > r1_idx) else []
        normal_forms[h] = {
            "r1_index": r1_idx, "r1_target_orbit": r1_target,
            "completer_index": completer_idx, "completer_target_orbit": completer_orbit,
            "completer_is_r1_itself": is_r1_completer,
            "intervening_events_between_r1_and_completer": intervening,
            "orbit_match": completer_orbit == r1_target,
            "full_event_sequence": [e["kind"] for e in events],
        }
        print(h[:12], "r1_idx", r1_idx, "completer_idx", completer_idx,
              "same_event", is_r1_completer, "orbit_match", normal_forms[h]["orbit_match"])

    # group into families
    families: Dict[str, List[str]] = {}
    for h, nf in normal_forms.items():
        key = f"r1_completer_gap={nf['completer_index'] - nf['r1_index']}_intervening={tuple(nf['intervening_events_between_r1_and_completer'])}"
        families.setdefault(key, []).append(h)

    report = {
        "schema": "rr-delayed-completer-normal-forms-v1",
        "note": (
            "6/10 same-component witnesses have a hub completer event that is NOT R1 itself "
            "(round-13/14 correction of round 12's false claim). All 6 share one general "
            "'same-orbit delayed completer' family: R1 and the completer are distinct events "
            "that both target the SAME orbit via different phases."
        ),
        "per_witness": normal_forms,
        "families_by_r1_completer_gap": {k: v for k, v in families.items()},
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "distinct_families": len(families)}, indent=2))


if __name__ == "__main__":
    main()
