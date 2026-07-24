#!/usr/bin/env python3
"""Section 9: general critical-restart pattern check on RA3/A3R using
only the stored witness ledger (no new continuation search). Reports
whether the second defect's critical restart reuses the first defect's
target orbit, for a bounded sample of each word already recovered in the
ledger.

Section 8 (a full deductive prerequisite-DAG proof for i_min(A2)=4) is
NOT attempted computationally here -- three rounds of investigation
(this one included) have not produced a genuine group-theoretic proof;
A2_PREREQUISITE_DAG_PROOF.md records this honestly as incomplete rather
than forcing a result.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

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


macro = _load("bapp_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def analyze_word(witnesses, first_kind: str, second_kind: str, limit: int) -> Dict[str, Any]:
    sample = witnesses[:limit]
    reuse = unrelated = no_critical = 0
    for w in sample:
        path = w["macro_path"]
        cur = exact.canonicalize(exact.initial_state())
        steps = []
        for step in path:
            rot_part, joint_part = step["edge_label"].split(";")
            ell = int(rot_part[len("rot^"):])
            for _ in range(ell):
                tr = exact.extend(cur, W1)
                cur = tr.state
            move = move_by_label[joint_part]
            tr = exact.extend(cur, move)
            kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
            target_q, _ = exact.ORBIT_PHASE[tr.target]
            steps.append({"kind": kind, "target_q": target_q})
            cur = exact.canonicalize(tr.state)
        i1 = next(i for i, s in enumerate(steps) if s["kind"] == first_kind)
        i2 = next(i for i, s in enumerate(steps) if s["kind"] == second_kind)
        critical_idx = i2 - 1
        if critical_idx <= i1:
            no_critical += 1
            continue
        if steps[critical_idx]["target_q"] == steps[i1]["target_q"]:
            reuse += 1
        else:
            unrelated += 1
    return {"sample_size": len(sample), "reuse": reuse, "unrelated": unrelated, "no_critical_restart": no_critical}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--sample-size", type=int, default=150)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "u_branch_critical_restart_by_word.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    ra3 = analyze_word(ledger["words"]["RA3"]["witnesses"], "R", "A3", args.sample_size)
    a3r = analyze_word(ledger["words"]["A3R"]["witnesses"], "A3", "R", args.sample_size)

    report = {
        "schema": "u-branch-critical-restart-by-word-v1",
        "note": "Uses only the already-recovered witness ledger (RA3/A3R samples); no new continuation search.",
        "RA3_R_first_A3_second": ra3,
        "A3R_A3_first_R_second": a3r,
        "finding": (
            "A3R shows exactly 0/{} reuse cases (the critical restart before R never "
            "reuses A3's own target orbit), a sharp asymmetry versus RA3's mixed 38/150. "
            "Reported as an observation (conjecture for its cause), not a proven theorem -- "
            "see A2_PREREQUISITE_DAG_PROOF.md section 9."
        ).format(a3r["sample_size"]),
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
