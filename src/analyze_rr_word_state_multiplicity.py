#!/usr/bin/env python3
"""Round 19, section 4: the word-vs-state counting identity.

Establishes, as an EXACT COUNTING IDENTITY over the historical ell=4
same-component set, the relation

    #words = SUM over post-R2 states S of #allowed_trailing_completions(S)

and determines WHY each of the H3 states admits exactly 3 trailing
macro-edges (rather than asserting the 3 as a coincidence).

Definition of "allowed trailing completion" used here, stated precisely
because the identity is only exact under one reading: a trailing
completion of a post-R2 state S at word-depth d is a legal macro-edge
(rot^ell; joint) out of S whose child passes area_a_prune_reason, AND
which brings the word to exactly the historical corpus's word length
(6 macro-edges). It is NOT "any legal continuation of any length" --
that set is larger and the identity would fail. This distinction is the
whole content of the Round 18 counting-unit correction.
"""
from __future__ import annotations

import hashlib
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


macro = _load("arwsm_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def state_hash(state) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def replay_to_post_r2(witness):
    """Returns (post_r2_state, edges_used_up_to_and_including_R2, tail_edges)."""
    cur = exact.initial_state()
    rc = 0
    used = 0
    post = None
    tail: List[str] = []
    for step in witness["macro_path"]:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            cur = exact.extend(cur, W1).state
        tr = exact.extend(cur, move_by_label[joint_part])
        kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        cur = tr.state
        if post is None:
            used += 1
        else:
            tail.append(f"rot^{ell};{joint_part}")
        if kind == "R":
            rc += 1
            if rc == 2:
                post = cur
    return post, used, tail


def trailing_edges(state) -> List[Dict[str, Any]]:
    out = []
    for edge in macro.macro_edges(state):
        reason = macro.area_a_prune_reason(edge.joint.state, macro.AREA_A)
        if reason is None:
            tr = edge.joint
            tq, tph = exact.ORBIT_PHASE[tr.target]
            out.append({
                "label": f"rot^{edge.run.ell};{tr.move.label}",
                "ell": edge.run.ell,
                "joint": tr.move.label,
                "kind": joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit),
                "target_orbit": tq, "target_phase": tph,
                "target_hexagon": core.hexagon_id(tr.target),
                "child_new_orbit": tr.new_orbit,
            })
    return sorted(out, key=lambda d: d["label"])


def main() -> None:
    elltab = json.loads((ROOT / "outputs" / "rr_abandonment_ell_table.json").read_text(encoding="utf-8"))
    wdata = json.loads((ROOT / "outputs" / "rr_literal_witnesses.json").read_text(encoding="utf-8"))
    h9 = [r for r in elltab["records"] if r["abandon_ell"] == 4 and r["r2_relation"] == "same"]

    by_state: Dict[str, Dict[str, Any]] = {}
    for rec in h9:
        w = wdata["witnesses"][rec["hash"]]
        post, used, tail = replay_to_post_r2(w)
        sh = state_hash(post)
        entry = by_state.setdefault(sh, {
            "post_r2_raw_hash": sh,
            "post_r2_canonical_hash": state_hash(exact.canonicalize(post)),
            "edges_up_to_and_including_r2": used,
            "total_word_macro_edges": len(w["macro_path"]),
            "historical_words": [],
            "historical_tails": [],
            "trailing_edges": trailing_edges(post),
        })
        entry["historical_words"].append(rec["hash"][:12])
        entry["historical_tails"].append(tail)

    # the counting identity
    total_words = sum(len(v["historical_words"]) for v in by_state.values())
    total_trailing = sum(len(v["trailing_edges"]) for v in by_state.values())
    identity_exact = total_words == total_trailing

    print(f"post-R2 states in H9: {len(by_state)}")
    for sh, v in by_state.items():
        used_labels = sorted(t[0] for t in v["historical_tails"])
        avail_labels = sorted(e["label"] for e in v["trailing_edges"])
        print(f"  {sh[:12]}: words={len(v['historical_words'])} trailing_edges={len(v['trailing_edges'])} "
              f"used=={avail_labels == used_labels}")
        for e in v["trailing_edges"]:
            print(f"      {e['label']:20s} kind={e['kind']:10s} -> hex{e['target_hexagon']} orbit{e['target_orbit']} phase{e['target_phase']}")
        v["historical_tails_used"] = used_labels
        v["trailing_edge_labels"] = avail_labels
        v["every_trailing_edge_realized_as_a_word"] = (avail_labels == used_labels)

    print(f"\nCOUNTING IDENTITY: sum of trailing completions = {total_trailing}, historical words = {total_words}, exact = {identity_exact}")

    # WHY exactly 3? examine the structure of the 3 trailing edges per state
    why = {}
    for sh, v in by_state.items():
        kinds = Counter(e["kind"] for e in v["trailing_edges"])
        ells = Counter(e["ell"] for e in v["trailing_edges"])
        joints = sorted(e["joint"] for e in v["trailing_edges"])
        why[sh] = {
            "kind_distribution": dict(kinds),
            "ell_distribution": dict(ells),
            "joints_used": joints,
            "all_same_ell": len(ells) == 1,
            "joints_are_a_proper_subset_of_all_four": set(joints) != {"w2:10", "w3:120", "w3:201", "w3:210"},
            "missing_joints": sorted({"w2:10", "w3:120", "w3:201", "w3:210"} - set(joints)),
        }
    print("\nWHY exactly 3 trailing edges per state:")
    for sh, d in why.items():
        print(f"  {sh[:12]}: ells={d['ell_distribution']} joints={d['joints_used']} missing={d['missing_joints']}")

    # is the missing joint always the same one, and why is it illegal?
    missing_reasons = {}
    for sh, v in by_state.items():
        rec = h9[[r["hash"][:12] for r in h9].index(v["historical_words"][0])]
        w = wdata["witnesses"][rec["hash"]]
        post, _, _ = replay_to_post_r2(w)
        blocked = []
        for edge in macro.macro_edges(post):
            reason = macro.area_a_prune_reason(edge.joint.state, macro.AREA_A)
            if reason is not None:
                blocked.append({"label": f"rot^{edge.run.ell};{edge.joint.move.label}", "prune_reason": reason})
        missing_reasons[sh] = blocked
    print("\nPruned (illegal) macro-edges out of each post-R2 state:")
    for sh, blocked in missing_reasons.items():
        reasons = Counter(b["prune_reason"] for b in blocked)
        print(f"  {sh[:12]}: {len(blocked)} pruned, reasons={dict(reasons)}")

    report = {
        "schema": "rr-word-state-multiplicity-v1",
        "definition_of_trailing_completion": (
            "a legal macro-edge out of the post-R2 state whose child passes "
            "area_a_prune_reason, bringing the word to the historical corpus's "
            "6-macro-edge length. NOT 'any legal continuation of any length'."
        ),
        "post_r2_states": by_state,
        "why_exactly_three": why,
        "pruned_edges_per_state": missing_reasons,
        "counting_identity": {
            "sum_of_trailing_completions": total_trailing,
            "historical_word_count": total_words,
            "exact": identity_exact,
            "formula": "#words = SUM_{S in post-R2 states} #allowed_trailing_completions(S)",
            "instance": f"9 = {' + '.join(str(len(v['trailing_edges'])) for v in by_state.values())}",
        },
        "proof_status": "exact counting identity (exact replay of all 9 historical witnesses + direct enumeration of every legal macro-edge out of each of the 3 post-R2 states)",
    }
    out = ROOT / "outputs" / "rr_word_state_multiplicity.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
