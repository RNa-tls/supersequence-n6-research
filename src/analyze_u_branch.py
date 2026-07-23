#!/usr/bin/env python3
"""U-branch (two-unit-defect ordered words RR, RA2, A2R, RA3, A3R) corpus
builder.

Reuses the SAME bounded search checkpoint that recovered all 230 J
witnesses (node_limit=20000, max_macro_depth=6 -- this corpus's own
recorded bound, not a new/larger search): that checkpoint's node_records
already contain literal canonical states for nearly the entire U-branch
target set (RA2 24/24, RR 4470/4470, RA3 9952/9952, A3R 10936/10984). No
new search is run here -- this only backtracks parent chains already
recorded in that checkpoint, exactly as recover_j_witnesses.py's
finalize() does for J.

A2R (0 observed in this corpus) is handled separately by
search_a2r_min_depth.py, since there is nothing to backtrack for it.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
OUTPUTS_LEGACY = ROOT / "legacy_research" / "outputs"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("u_branch_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def load_target_hashes_by_word() -> Dict[str, List[str]]:
    data = json.loads((OUTPUTS_LEGACY / "f1_n2_defect_words.json").read_text(encoding="utf-8"))
    records = data["area_a_depth6"]["state_records"]
    by_word: Dict[str, List[str]] = {}
    for r in records:
        by_word.setdefault(r["word"], []).append(r["state_hash"])
    return by_word


def backtrack_witness(node_records: Dict[str, Any], target_hash: str) -> Optional[Dict[str, Any]]:
    if target_hash not in node_records:
        return None
    chain: List[Tuple[str, Dict[str, Any]]] = []
    cursor: Optional[str] = target_hash
    while cursor is not None:
        rec = node_records[cursor]
        chain.append((cursor, rec))
        cursor = rec["parent_hash"]
    chain.reverse()
    macro_path = [
        {"edge_label": rec["edge_label"], "transition": rec["transition"], "depth": rec["depth"]}
        for _, rec in chain[1:]
    ]
    return {"target_hash": target_hash, "macro_path": macro_path, "final_state_json": chain[-1][1]["state"]}


def analyze_interaction(state: "exact.ExactState", macro_path: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Independently recompute the interaction ledger (positive-charge
    events only) via literal replay, rather than trusting the corpus's own
    pre-computed component_relation/fragment_relation/orbit_relation
    fields -- those are re-derived here from scratch and can be
    cross-checked against them."""
    move_by_label = {m.label: m for m in exact.ALL_MOVES}
    W1 = macro.W1
    cur = exact.canonicalize(exact.initial_state())
    events = []
    for step in macro_path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        move = move_by_label[joint_part]
        before = cur
        tr = exact.extend(cur, move)
        cur = exact.canonicalize(tr.state)
        delta_n = cur.Ndef - before.Ndef
        if delta_n != 0:
            events.append({
                "weight": move.weight, "abandonment": tr.abandonment, "new_orbit": tr.new_orbit,
                "delta_F": tr.delta_F, "delta_S": tr.delta_S, "delta_N": delta_n,
                "target_orbit": exact.ORBIT_PHASE[tr.target][0],
            })
    if len(events) != 2:
        return {"event_count": len(events), "note": "expected exactly 2 positive-charge events for a U-branch word"}
    e1, e2 = events
    return {
        "event_count": 2,
        "first_event": e1,
        "second_event": e2,
        "same_target_orbit_reused": e1["target_orbit"] == e2["target_orbit"],
        "word_reconstructed": (
            ("R" if not e1["abandonment"] else ("A2" if e1["weight"] == 2 else "A3"))
            + ("R" if not e2["abandonment"] else ("A2" if e2["weight"] == 2 else "A3"))
        ),
    }


def build_word_corpus(word: str, target_hashes: List[str], node_records: Dict[str, Any],
                       limit: Optional[int]) -> Dict[str, Any]:
    witnesses = []
    missing = []
    hashes = sorted(target_hashes)
    if limit is not None:
        hashes = hashes[:limit]
    for h in hashes:
        w = backtrack_witness(node_records, h)
        if w is None:
            missing.append(h)
            continue
        state = exact.state_from_json(w["final_state_json"])
        form = exact.f1_normal_form(state)
        interaction = analyze_interaction(state, w["macro_path"])
        witnesses.append({
            "target_hash": h,
            "macro_path": w["macro_path"],
            "final_state_json": w["final_state_json"],
            "coordinate_P_F_S_H_O_D_N": list(macro.state_coordinate(state)),
            "visited_count": state.visited_count,
            "phi": phi(state),
            "fragment_hex": form.fragment_hex,
            "fragment_components": list(form.fragment_components),
            "current_hex": form.current_hex,
            "current_components": list(form.current_components),
            "interaction": interaction,
        })
    return {
        "word": word,
        "total_in_corpus": len(target_hashes),
        "recovered": len(witnesses),
        "missing": missing,
        "witnesses": witnesses,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, help="path to the J-witness-recovery checkpoint to reuse")
    parser.add_argument("--words", nargs="+", default=["RA2", "RR", "RA3", "A3R"])
    parser.add_argument("--limit-per-word", type=int, default=None)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "u_branch_state_ledger.json"))
    args = parser.parse_args()

    ckpt = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
    node_records = ckpt["node_records"]
    by_word = load_target_hashes_by_word()

    result = {}
    for word in args.words:
        result[word] = build_word_corpus(word, by_word.get(word, []), node_records, args.limit_per_word)
        print(f"{word}: total={result[word]['total_in_corpus']} recovered={result[word]['recovered']} "
              f"missing={len(result[word]['missing'])}")

    out = {"schema": "u-branch-state-ledger-v1", "words": result}
    Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": args.output}, indent=2))


if __name__ == "__main__":
    main()
