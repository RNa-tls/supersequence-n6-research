#!/usr/bin/env python3
"""A2 legality: exact predicate extraction (section 2), the per-ell
candidate table for all 24 RA2 witnesses (section 3), and five-state
prefix divergence tracking (section 1).

Key simplifying fact this discovers first: there is EXACTLY ONE weight-2
move in the entire model (ALL_MOVES has a single weight=2 entry, "w2:10").
So "does some weight-2 move produce a legal A2 at rotation length ell"
reduces to checking THIS ONE move's behavior at the rotated position --
there is no choice among weight-2 candidates, ever. This directly
explains why every earlier round observed "at most one legal weight-2
abandoning move" at any boundary: there is only one weight-2 move to
begin with.

Exact predicate (derived directly from extend()'s code, not just
observed): for a state S sitting at rotation offset ell within a fresh
hex (endpoint p_ell = SIGMA^ell(p_0)),

    A2Legal(S, ell) :=
        NOT visited(p_ell's rotation successor)          [abandonment]
        AND NOT visited(target(ell))                       [target legal]
        AND orbit_masks[orbit(target(ell))] != 0            [existing target]

    where target(ell) = word_after(p_ell, w2_10.action).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
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


macro = _load("aalh_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1
W2_MOVES = [m for m in exact.ALL_MOVES if m.weight == 2]
assert len(W2_MOVES) == 1, "expected exactly one weight-2 move in this model"
W2_ONLY = W2_MOVES[0]

U4_HASHES = [
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
]
OUTLIER_HASH = "e2b44997e7838537176bd6e0e72ea41df259f429863731b696dc76692beeb98c"
FIVE_HASHES = U4_HASHES + [OUTLIER_HASH]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def replay_to_pre_a2(witness: Dict[str, Any]) -> "exact.ExactState":
    """Replay every macro-edge STRICTLY BEFORE A2's own macro-edge in
    full (rotation + joint + canonicalize); returns the state at the
    FRESH LANDING point of A2's own hex (ell=0 relative to A2's own
    macro-edge) -- i.e. right after the critical restart's landing joint
    fired, before any of A2's own rotations.

    BUGS FIXED (two, found in sequence while validating this function):
    (1) an earlier version assumed A2 was always the LAST entry in
    macro_path (path[:-1]) -- false in general, e.g. 15186b558afe has a
    trailing Z3 event after A2. Fixed by locating A2's actual index via
    its joint kind.
    (2) the first fix then returned the state right before A2's OWN
    joint fires (i.e. already offset by that witness's own ell_A2
    rotations), rather than the fresh landing point ell=0 -- making the
    subsequent ell-sweep start from the wrong origin. Fixed by stopping
    the replay before A2's macro-edge begins at all, not partway through
    it."""
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        # peek: would this macro-edge's joint be A2? check by replaying
        # its rotation+joint on a COPY of cur, without committing, first.
        probe = cur
        for _ in range(ell):
            tr = exact.extend(probe, W1)
            probe = tr.state
        tr = exact.extend(probe, move)
        if joint_kind(move.weight, tr.abandonment, tr.new_orbit) == "A2":
            return cur  # fresh landing point of A2's own hex, ell=0
        # not A2 -- commit this macro-edge for real and continue
        for _ in range(ell):
            tr2 = exact.extend(cur, W1)
            cur = tr2.state
        tr2 = exact.extend(cur, move)
        cur = exact.canonicalize(tr2.state)
    raise AssertionError("no A2 event found in witness macro_path")


def candidate_table(pre_a2: "exact.ExactState") -> List[Dict[str, Any]]:
    rows = []
    p = pre_a2
    for ell in range(6):
        succ = exact.extend(p, W1)
        abandonment_possible = succ is None  # NOT state.visited(successor) == (extend returns a valid step) is inverse; see note
        # NOTE: 'abandonment' in extend() = NOT state.visited(successor). succ is None means the
        # successor IS already visited (rotation blocked) -- i.e. abandonment=False there.
        # So abandonment_possible (True) means succ is NOT None (successor unvisited).
        abandonment_possible = succ is not None
        tr = exact.extend(p, W2_ONLY)
        row: Dict[str, Any] = {"ell": ell, "endpoint": list(p.p), "abandonment_possible": abandonment_possible}
        if tr is None:
            row["target_visited"] = True
            row["a2_legal"] = False
            row["fail_reason"] = "target_already_visited"
        else:
            target_q, target_phase = exact.ORBIT_PHASE[tr.target]
            existing = p.orbit_masks[target_q] != 0
            row.update({
                "target": list(tr.target), "target_orbit_q": target_q, "target_phase": target_phase,
                "target_existing": existing, "target_visited": False,
                "abandonment_flag": tr.abandonment, "new_orbit_flag": tr.new_orbit,
            })
            if not tr.abandonment:
                row["a2_legal"] = False
                row["fail_reason"] = "abandonment_false_hex_already_full_or_blocked"
            elif tr.new_orbit:
                row["a2_legal"] = False
                row["fail_reason"] = "target_orbit_fresh_not_existing"
            else:
                row["a2_legal"] = True
                row["fail_reason"] = None
        rows.append(row)
        if succ is None:
            break
        p = succ.state
    return rows


def prefix_divergence(witnesses: Dict[str, Any]) -> Dict[str, Any]:
    """Section 1: align the 5 witnesses step-by-step (by macro-edge
    index) and find the last common canonical state and the first
    divergent field."""
    replays = {}
    for h, w in witnesses.items():
        path = w["macro_path"]
        cur = exact.canonicalize(exact.initial_state())
        canon_states = [macro.stable_hash(cur)]
        for step in path:
            rot_part, joint_part = step["edge_label"].split(";")
            ell = int(rot_part[len("rot^"):])
            for _ in range(ell):
                tr = exact.extend(cur, W1)
                cur = tr.state
            move = move_by_label[joint_part]
            tr = exact.extend(cur, move)
            cur = exact.canonicalize(tr.state)
            canon_states.append(macro.stable_hash(cur))
        replays[h] = canon_states

    max_len = min(len(v) for v in replays.values())
    last_common = -1
    for i in range(max_len):
        vals = set(replays[h][i] for h in replays)
        if len(vals) == 1:
            last_common = i
        else:
            break
    return {"last_common_step_index": last_common, "step_lengths": {h: len(v) for h, v in replays.items()}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output-tables", default=str(ROOT / "outputs" / "a2_rotation_candidate_tables.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra2 = {w["target_hash"]: w for w in ledger["words"]["RA2"]["witnesses"]}

    five = {h: ra2[h] for h in FIVE_HASHES}
    divergence = prefix_divergence(five)
    print("prefix divergence:", divergence)

    tables = {}
    for h, w in ra2.items():
        pre_a2 = replay_to_pre_a2(w)
        table = candidate_table(pre_a2)
        legal_ells = [r["ell"] for r in table if r.get("a2_legal")]
        tables[h] = {
            "group": "U4" if h in U4_HASHES else ("C20_outlier" if h == OUTLIER_HASH else "C20"),
            "candidate_table": table,
            "legal_ells": legal_ells,
        }
        print(h[:12], tables[h]["group"], "legal_ells:", legal_ells,
              "fail_reasons:", [r["fail_reason"] for r in table if not r.get("a2_legal", True)][:6])

    report = {
        "schema": "a2-rotation-candidate-tables-v1",
        "key_simplifying_fact": "there is exactly one weight-2 move in the entire model (w2:10) -- A2 legality reduces to this single move's behavior at each rotation offset",
        "prefix_divergence_five_state": divergence,
        "tables_by_witness": tables,
    }
    Path(args.output_tables).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output_tables}, indent=2))


if __name__ == "__main__":
    main()
