#!/usr/bin/env python3
"""Round 15, sections 5-8: full extraction of the ell=0 branch (and, for
comparison, ell=1,2,3) of "hub-completed" RR witnesses -- builds the
completer-choice x relation truth table and traces the exact mechanism
of the single ell=0 same-component witness.

No new search: replays outputs/rr_literal_witnesses.json entries already
identified in outputs/rr_abandonment_ell_table.json (Round 15, this
round).
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


macro = _load("aeb_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
HEX0_POSITION_ORBIT = [0, 120, 33, 9, 3, 1]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def full_trace(word: dict):
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
        src_hex = core.hexagon_id(cur.p)
        sq, sph = exact.ORBIT_PHASE[cur.p]
        tr = exact.extend(cur, move)
        tgt_hex = core.hexagon_id(tr.target)
        tq, tph = exact.ORBIT_PHASE[tr.target]
        steps.append({
            "idx": idx, "ell": ell, "move": joint_part,
            "kind": joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit),
            "src_hex": src_hex, "src_orbit": sq, "src_phase": sph,
            "tgt_hex": tgt_hex, "tgt_orbit": tq, "tgt_phase": tph,
        })
        cur = tr.state
    return hex0, steps


def hex0_closure_positions(word):
    cur = exact.initial_state()
    hex0 = core.hexagon_id(cur.p)
    visited = {0}
    for step in word["macro_path"]:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
            if core.hexagon_id(cur.p) == hex0:
                q, ph = exact.ORBIT_PHASE[cur.p]
                if q in HEX0_POSITION_ORBIT:
                    visited.add(HEX0_POSITION_ORBIT.index(q))
        tr = exact.extend(cur, move)
        if core.hexagon_id(tr.target) == hex0:
            q, ph = exact.ORBIT_PHASE[tr.target]
            if q in HEX0_POSITION_ORBIT:
                visited.add(HEX0_POSITION_ORBIT.index(q))
        cur = tr.state
    return visited


def main() -> None:
    wdata = json.loads((ROOT / "outputs" / "rr_literal_witnesses.json").read_text(encoding="utf-8"))
    elltab = json.loads((ROOT / "outputs" / "rr_abandonment_ell_table.json").read_text(encoding="utf-8"))
    recs = elltab["records"]

    truth_table = {}
    for ell in range(5):
        sub = [x for x in recs if x["abandon_ell"] == ell and x["hub_completer_found"]]
        cross = Counter()
        for x in sub:
            closure = hex0_closure_positions(wdata["witnesses"][x["hash"]])
            fully_closed = len(closure) == 6
            cross[(x["completer_orbit"], x["r2_relation"], x["chaining"], fully_closed)] += 1
        truth_table[str(ell)] = {
            "hub_completed_total": len(sub),
            "cross_tab": [
                {"completer_orbit": k[0], "r2_relation": k[1], "chaining": k[2], "hex0_fully_closed": k[3], "count": v}
                for k, v in sorted(cross.items(), key=lambda kv: -kv[1])
            ],
        }
        print(f"ell={ell}", truth_table[str(ell)]["cross_tab"])

    # exact trace of the single ell=0 same-component witness
    same0 = next(x for x in recs if x["abandon_ell"] == 0 and x["r2_relation"] == "same")
    hex0, steps = full_trace(wdata["witnesses"][same0["hash"]])

    # which orbit ids get touched (as source or target) more than once -- the
    # "reused" orbit driving the same-component connection
    orbit_touches = Counter()
    for s in steps:
        orbit_touches[s["src_orbit"]] += 1
        orbit_touches[s["tgt_orbit"]] += 1
    reused_orbits = {o: c for o, c in orbit_touches.items() if c >= 2}

    ell0_exception = {
        "hash": same0["hash"],
        "hex0": hex0,
        "steps": steps,
        "reused_orbits": reused_orbits,
        "mechanism": (
            "R1 (idx3, kind R) is itself the hub completer, landing on hex0's "
            "position 1 (orbit 120, phase 0) -- reusing orbit 120, which was "
            "already touched three times before (idx0 abandonment target "
            "phase1, idx1 Z2 target phase2, idx2 Z2 target phase3, all in "
            "different hexagons). This registers hex0 into the same "
            "union-find component as those earlier hexagons. Because "
            "union-find nodes are keyed by orbit id only (phase-independent, "
            "RR_PHASE_FREEDOM.md), hex0 is now transitively connected to "
            "that whole chain. Hex0 then fully closes via forced pure "
            "rotation (Hub Touch Count<=2), and the very next joint (idx4, "
            "Z2) leaves hex0 from position 5 (orbit 1) per the Hub Exit "
            "Source Lemma, landing in hex96. R2 (idx5, kind R) then sources "
            "from hex96's own orbit-120 phase (phase 4) -- the fifth and "
            "last unvisited phase of orbit 120 -- which is the SAME "
            "phase-independent union-find node touched by R1's completion "
            "and by the idx0-2 chain. All 5 phases of orbit 120 end up "
            "visited across the word, and R2's source is the last one, so "
            "R2 is 'same' via orbit 120, not via orbit 1 directly -- a "
            "second, indirect mechanism distinct from the ell=4 branch's "
            "direct hex0-position5-exit mechanism."
        ),
    }

    report = {
        "schema": "rr-ell0-branch-truth-table-v1",
        "truth_table_by_ell": truth_table,
        "ell0_exception_full_trace": ell0_exception,
    }
    out = ROOT / "outputs" / "rr_ell0_completer_truth_table.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
