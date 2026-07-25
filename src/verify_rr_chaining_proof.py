#!/usr/bin/env python3
"""Round 14, section 11: builds the RR relation implication lattice --
tests every requested implication exhaustively over the full 4,470-
witness corpus, recording exact counterexample counts (0 = holds,
>0 = falsified with a minimal witness).
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


macro = _load("vrcp_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--corpus", default=str(ROOT / "legacy_research" / "outputs" / "f1_n2_defect_words.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_relation_lattice.json"))
    args = parser.parse_args()

    wdata = json.loads(Path(args.witnesses).read_text(encoding="utf-8"))
    table = json.loads(Path(args.relation_table).read_text(encoding="utf-8"))
    rows = {r["hash"]: r for r in table["rows"] if "error" not in r}

    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    rr_records = {r["state_hash"]: r for r in corpus["area_a_depth6"]["state_records"] if r["word"] == "RR"}

    # per-witness: does the hub exist, and what's its completer orbit (if any)
    hub_info: Dict[str, Any] = {}
    for h, w in wdata["witnesses"].items():
        cur = exact.initial_state()
        touches = {core.hexagon_id(cur.p): [-1]}
        for idx, step in enumerate(w["macro_path"]):
            rot_part, joint_part = step["edge_label"].split(";")
            ell = int(rot_part[len("rot^"):])
            move = move_by_label[joint_part]
            for _ in range(ell):
                tr = exact.extend(cur, W1)
                cur = tr.state
            tr = exact.extend(cur, move)
            tq, _ = exact.ORBIT_PHASE[tr.target]
            th = core.hexagon_id(tr.target)
            touches.setdefault(th, []).append((idx, tq))
            cur = tr.state
        multi = {hx: seq for hx, seq in touches.items() if len(seq) >= 2}
        if multi:
            (hub_hex, seq), = multi.items()
            hub_info[h] = {"hub_exists": True, "completer_orbit": seq[1][1]}
        else:
            hub_info[h] = {"hub_exists": False, "completer_orbit": None}

    implications = {}

    def check(name: str, antecedent, consequent):
        total = 0
        holds_count = 0
        counterexamples = []
        for h, row in rows.items():
            if not antecedent(h, row):
                continue
            total += 1
            if consequent(h, row):
                holds_count += 1
            else:
                if len(counterexamples) < 3:
                    counterexamples.append(h)
        implications[name] = {
            "antecedent_count": total,
            "holds_count": holds_count,
            "counterexample_count": total - holds_count,
            "holds_exactly": total == holds_count,
            "example_counterexamples": counterexamples,
        }

    check("same_component_implies_chaining",
          lambda h, r: r["r2_own_component_relation"] == "same",
          lambda h, r: r["chaining"])

    check("chaining_implies_same_component",
          lambda h, r: r["chaining"],
          lambda h, r: r["r2_own_component_relation"] == "same")

    check("chaining_implies_not_unresolved",
          lambda h, r: r["chaining"],
          lambda h, r: r["r2_own_component_relation"] != "unresolved")

    check("hub_touched_implies_chaining",
          lambda h, r: hub_info[h]["hub_exists"],
          lambda h, r: r["chaining"])

    check("same_target_orbit_implies_chaining",
          lambda h, r: rr_records.get(h, {}).get("orbit_relation", {}).get("same_target", False),
          lambda h, r: r["chaining"])

    check("hub_exists_and_chaining_implies_completer_matches_r1_target",
          lambda h, r: hub_info[h]["hub_exists"] and r["chaining"],
          lambda h, r: hub_info[h]["completer_orbit"] == r["r1_target"])

    check("hub_exists_and_completer_matches_r1_target_implies_same",
          lambda h, r: hub_info[h]["hub_exists"] and hub_info[h]["completer_orbit"] == r["r1_target"],
          lambda h, r: r["r2_own_component_relation"] == "same")

    for name, v in implications.items():
        print(name, "->", "HOLDS" if v["holds_exactly"] else f"FALSIFIED ({v['counterexample_count']} counterexamples)",
              f"[{v['holds_count']}/{v['antecedent_count']}]")

    report = {
        "schema": "rr-relation-lattice-v1",
        "total_rr_witnesses": len(rows),
        "implications": implications,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
