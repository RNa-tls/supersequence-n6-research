#!/usr/bin/env python3
"""Abandonment 2-axis classification: (ell_A, nu_A) where nu_A=0 means the
abandoning move's target E-orbit was already visited (existing) and
nu_A=1 means it opens a fresh orbit (new_orbit=True).

Pulls every recovered A2 event (from RA2 and RA3 witnesses -- A2 or A3 is
always the second, abandoning event in those two words) and every
recovered A3 event as the FIRST event (from A3R witnesses), from the
existing U-branch witness ledger. No new large-scale search -- this is a
re-extraction from data already recovered in prior rounds.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
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


macro = _load("atn_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def orbit_slack(state: "exact.ExactState") -> int:
    return exact.TARGET_O - state.O


def d_frag(state: "exact.ExactState") -> int:
    form = exact.f1_normal_form(state)
    if form is None or form.fragment_hex is None:
        return 0
    return 6 - bin(state.hex_masks[form.fragment_hex]).count("1")


def component_map(state: "exact.ExactState") -> Dict[Any, Any]:
    parent: Dict[Any, Any] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return {node: find(node) for node in list(parent)}


def first_child_signature(state: "exact.ExactState") -> List[Any]:
    out = []
    for e in macro.macro_edges(state):
        tr = e.joint
        if tr.abandonment:
            continue
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        if reason is not None:
            continue
        out.append((e.run.ell, tr.move.weight, tr.new_orbit, tr.state.Ndef - state.Ndef))
    return sorted(out)


def extract_abandonment_event(witness: Dict[str, Any], word: str) -> Dict[str, Any]:
    path = witness["macro_path"]
    cur = exact.canonicalize(exact.initial_state())
    a_idx = None
    events = 0
    for i, step in enumerate(path):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        pre_joint = cur
        move = move_by_label[joint_part]
        tr = exact.extend(cur, move)
        if tr.abandonment:
            a_idx = i
            a_ell = ell
            a_pre = pre_joint
            a_tr = tr
        post = tr.state
        cur = exact.canonicalize(post)
        if tr.abandonment or (tr.move.weight == 3 and not tr.abandonment and tr.state.Ndef - pre_joint.Ndef == 1):
            events += 1

    assert a_idx is not None, f"no abandonment found in {word} witness"
    a_post_raw = a_tr.state
    a_post_canon = exact.canonicalize(a_post_raw)
    src_q, src_phase = exact.ORBIT_PHASE[a_pre.p]
    tgt_q, tgt_phase = exact.ORBIT_PHASE[a_tr.target]
    roots = component_map(a_pre)
    src_root = roots.get(("q", src_q))
    tgt_root_pre = roots.get(("q", tgt_q))

    form_post = exact.f1_normal_form(a_post_raw)
    return {
        "target_hash": witness["target_hash"],
        "word": word,
        "abandonment_index_in_path": a_idx,
        "ell_A": a_ell,
        "weight_A": a_tr.move.weight,
        "nu_A": 1 if a_tr.new_orbit else 0,
        "source_orbit_q": src_q, "source_phase": src_phase, "source_hexagon": core.hexagon_id(a_pre.p),
        "target_orbit_q": tgt_q, "target_phase": tgt_phase, "target_hexagon": core.hexagon_id(a_tr.target),
        "component_relation_at_pre": (
            "same" if src_root is not None and src_root == tgt_root_pre else
            "different" if src_root is not None and tgt_root_pre is not None else "unresolved"
        ),
        "fragment_hex_after": form_post.fragment_hex if form_post else None,
        "fragment_debt_after": d_frag(a_post_raw),
        "phi_after": phi(a_post_raw),
        "orbit_slack_after": orbit_slack(a_post_raw),
        "P_after": a_post_raw.P, "O_after": a_post_raw.O, "D_after": a_post_raw.D, "Ndef_after": a_post_raw.Ndef,
        "endpoint_class_canonical": list(a_post_canon.p),
        "first_child_signature": first_child_signature(a_post_raw),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "abandonment_length_novelty_table.json"))
    args = parser.parse_args()

    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))

    all_events = []
    for word in ("RA2", "RA3", "A3R"):
        witnesses = ledger["words"][word]["witnesses"]
        for w in witnesses:
            ev = extract_abandonment_event(w, word)
            all_events.append(ev)
        print(f"{word}: extracted {len(witnesses)} abandonment events")

    table = defaultdict(list)
    for ev in all_events:
        table[(ev["ell_A"], ev["nu_A"])].append(ev)

    summary = {}
    for (ell, nu), evs in sorted(table.items()):
        words = Counter(e["word"] for e in evs)
        weights = Counter(e["weight_A"] for e in evs)
        summary[f"ell={ell},nu={nu}"] = {
            "count": len(evs), "by_word": dict(words), "by_weight": dict(weights),
            "phi_after_values": sorted(set(e["phi_after"] for e in evs)),
            "fragment_debt_after_values": sorted(set(e["fragment_debt_after"] for e in evs)),
        }

    report = {
        "schema": "abandonment-length-novelty-table-v1",
        "total_events": len(all_events),
        "summary_by_ell_nu": summary,
        "events": all_events,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output, "total_events": len(all_events), "cells_populated": list(summary.keys())}, indent=2))


if __name__ == "__main__":
    main()
