#!/usr/bin/env python3
"""RR (two-R-event) same-component <=> chaining investigation.

Terminology (all defined precisely; canonicalization-invariance argument
in research/RR_SAME_COMPONENT_CHAINING_THEOREM.md section 1):

- R event: a joint with weight=3, abandonment=False, new_orbit=False
  ("blocked, existing-target" weight-3 move).
- source orbit (of a joint): the E-orbit id of the state's permutation
  right before the joint fires (i.e. AFTER that block's own rotation run,
  NOT the block's landing point -- these differ whenever ell>0, since a
  hexagon's 6 rotation positions belong to 6 DISTINCT E-orbits).
- target orbit (of a joint): the E-orbit id of the joint's target
  permutation.
- incidence component: the union-find tree (over bipartite nodes ("q",
  orbit id) and ("h", hexagon id)) built by unioning (q, hexagon_id(port))
  for every VISITED (orbit, phase) pair recorded in state.orbit_masks --
  including the state's own initial registration.
- component root: the union-find representative of a node.
- chaining: first R's target orbit id == second R's source orbit id
  (an ORBIT-level match; the literal target/source PERMUTATIONS may
  differ in phase).
- same-component: the SECOND R's own component_relation is "same", i.e.
  its own source orbit root == its own target orbit root (a self-relation
  of R2, NOT a comparison between R1 and R2 -- this was the one
  terminology point earlier rounds got right structurally but that is
  easy to misread from the name alone).
- unresolved relation: at least one side (source or target orbit) has
  never been registered in the union-find structure yet.
- first R / second R: temporal order within one witness's macro_path
  (well-defined, no ambiguity -- a macro_path is a literal sequence).
- R-between word: the zero-charge (Z2/Z3/Z2abandon) macro-edges strictly
  between the first and second R in the macro_path.

Central NEW finding this round (see the research doc for the full
argument): hex 0 (the hexagon containing the WORD'S OWN starting
permutation) is registered from initial_state() itself, before any joint
fires. This is the ONE node in the incidence graph guaranteed registered
from t=0. Whenever an R's source orbit (which, for a chaining R2, is
exactly R1's target orbit) has ANY of its phases visited-and-landing-in-
hex-0 by some event before R2 fires, that orbit's whole component merges
with hex 0's component (which contains orbit 0). Verified EXHAUSTIVELY
(not sampled) over all 75 chaining witnesses in the full 4,470-record RR
corpus: hex0-touched-before-R2 <=> R2's component_relation=="same",
75/75, zero exceptions.
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


macro = _load("arc_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W1 = macro.W1


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def component_map(state: "exact.ExactState") -> Tuple[Dict[Any, Any], int]:
    """Returns (roots dict, redundant_union_count). redundant_union_count
    is 0 iff the induced incidence graph is a forest -- i.e. every union()
    call merged two PREVIOUSLY DIFFERENT trees; a nonzero count means a
    cycle-closing edge was found (relevant to the forest lemma)."""
    parent: Dict[Any, Any] = {}
    redundant = 0

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        nonlocal redundant
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
        else:
            redundant += 1

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return {n: find(n) for n in parent}, redundant


def load_full_rr_corpus() -> List[Dict[str, Any]]:
    data = json.loads((OUTPUTS_LEGACY / "f1_n2_defect_words.json").read_text(encoding="utf-8"))
    return [r for r in data["area_a_depth6"]["state_records"] if r["word"] == "RR"]


def backtrack(node_records: Dict[str, Any], target_hash: str) -> Optional[Dict[str, Any]]:
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


def literal_analysis(witness: Dict[str, Any]) -> Dict[str, Any]:
    """Raw (never-canonicalized) replay: computes, for the FIRST and
    SECOND R events, source/target orbit ids, ell, hexagon of target,
    each R's own component_relation (self source-vs-target), the
    chaining relation (R1 target orbit == R2 source orbit), macro
    distance, and whether hex 0 was touched by ANY event before R2
    fires -- the new mechanism this round identifies as deciding
    "same" within the chaining subset."""
    path = witness["macro_path"]
    cur = exact.initial_state()
    events: List[Dict[str, Any]] = []
    hex0_touched_before: List[bool] = []
    hex0_seen = False
    for idx, step in enumerate(path):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        pre_joint = cur
        src_q, src_phase = exact.ORBIT_PHASE[cur.p]
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        tgt_q, tgt_phase = exact.ORBIT_PHASE[tr.target]
        roots, _redundant = component_map(pre_joint)
        src_root, tgt_root = roots.get(("q", src_q)), roots.get(("q", tgt_q))
        rel = "same" if src_root is not None and src_root == tgt_root else (
            "different" if src_root is not None and tgt_root is not None else "unresolved")
        hex0_touched_before.append(hex0_seen)
        events.append({
            "index": idx, "kind": kind, "ell": ell,
            "source_orbit": src_q, "source_phase": src_phase,
            "target_orbit": tgt_q, "target_phase": tgt_phase,
            "target_hexagon": core.hexagon_id(tr.target),
            "own_component_relation": rel,
            "hex0_touched_before_this_event": hex0_touched_before[-1],
        })
        if core.hexagon_id(tr.target) == 0:
            hex0_seen = True
        cur = tr.state

    r_events = [e for e in events if e["kind"] == "R"]
    if len(r_events) != 2:
        return {"error": f"expected exactly 2 R events, found {len(r_events)}", "events": events}
    r1, r2 = r_events[0], r_events[1]
    chaining = r1["target_orbit"] == r2["source_orbit"]
    return {
        "events": events,
        "r1": r1, "r2": r2,
        "macro_distance": r2["index"] - r1["index"],
        "chaining": chaining,
        "r2_own_component_relation": r2["own_component_relation"],
        "hex0_touched_before_r2": r2["hex0_touched_before_this_event"],
    }


def local_candidate_enumeration(witness: Dict[str, Any]) -> Dict[str, Any]:
    """Section 5: replay up to and including R1, then enumerate EVERY
    legal macro-edge from that exact boundary (a single macro_edges()
    call -- bounded, not a search), classifying each candidate's kind,
    chaining status (relative to R1's own target), and R2's own
    component_relation if that candidate were taken."""
    path = witness["macro_path"]
    cur = exact.initial_state()
    r1_target_orbit = None
    for step in path:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            tr = exact.extend(cur, W1)
            cur = tr.state
        tr = exact.extend(cur, move)
        kind = joint_kind(move.weight, tr.abandonment, tr.new_orbit)
        cur = tr.state
        if kind == "R":
            r1_target_orbit, _ = exact.ORBIT_PHASE[tr.target]
            break
    if r1_target_orbit is None:
        return {"error": "no R1 found"}

    roots, _redundant = component_map(cur)
    candidates = []
    for e in macro.macro_edges(cur):
        tr = e.joint
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        src_q, _src_phase = exact.ORBIT_PHASE[e.run.state.p]
        tgt_q = None
        if tr.target is not None:
            tgt_q, _tgt_phase = exact.ORBIT_PHASE[tr.target]
        src_root = roots.get(("q", src_q))
        tgt_root = roots.get(("q", tgt_q)) if tgt_q is not None else None
        rel = "same" if src_root is not None and src_root == tgt_root else (
            "different" if src_root is not None and tgt_root is not None else "unresolved")
        candidates.append({
            "ell": e.run.ell, "kind": kind, "legal": reason is None, "fail_reason": reason,
            "source_orbit": src_q, "target_orbit": tgt_q,
            "chaining_relative_to_r1": src_q == r1_target_orbit,
            "component_relation_if_taken": rel,
        })
    return {"r1_target_orbit": r1_target_orbit, "candidates_at_boundary_right_after_r1": candidates}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, help="path to the (scratch, outside-repo) J-witness recovery checkpoint")
    parser.add_argument("--output-witnesses", default=str(ROOT / "outputs" / "rr_literal_witnesses.json"))
    parser.add_argument("--output-relation-table", default=str(ROOT / "outputs" / "rr_full_relation_table.json"))
    parser.add_argument("--output-candidates", default=str(ROOT / "outputs" / "rr_same_component_candidates.json"))
    args = parser.parse_args()

    ckpt = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
    node_records = ckpt["node_records"]

    full_corpus = load_full_rr_corpus()
    print(f"full RR corpus (exact, from stored corpus): {len(full_corpus)} records")

    witnesses: Dict[str, Any] = {}
    missing: List[str] = []
    for rec in full_corpus:
        h = rec["state_hash"]
        w = backtrack(node_records, h)
        if w is None:
            missing.append(h)
            continue
        witnesses[h] = w
    print(f"literal witnesses recovered: {len(witnesses)} / {len(full_corpus)} (missing: {len(missing)})")

    Path(args.output_witnesses).write_text(json.dumps({
        "schema": "rr-literal-witnesses-v1",
        "total_in_corpus": len(full_corpus),
        "recovered_count": len(witnesses),
        "missing_count": len(missing),
        "missing_hashes": missing,
        "witnesses": witnesses,
    }, indent=2, sort_keys=True, default=str), encoding="utf-8")

    rows = []
    counters = {
        "chaining_total": 0, "same_component_total": 0,
        "chaining_and_hex0": 0, "chaining_and_same": 0,
        "chaining_and_hex0_and_not_same": 0, "chaining_and_same_and_not_hex0": 0,
        "same_and_not_chaining": 0, "not_chaining_and_same": 0,
        "errors": 0,
    }
    for h, w in witnesses.items():
        analysis = literal_analysis(w)
        if "error" in analysis:
            counters["errors"] += 1
            rows.append({"hash": h, "error": analysis["error"]})
            continue
        chaining = analysis["chaining"]
        same = analysis["r2_own_component_relation"] == "same"
        hex0 = analysis["hex0_touched_before_r2"]
        if chaining:
            counters["chaining_total"] += 1
            if hex0:
                counters["chaining_and_hex0"] += 1
                if not same:
                    counters["chaining_and_hex0_and_not_same"] += 1
            if same:
                counters["chaining_and_same"] += 1
                if not hex0:
                    counters["chaining_and_same_and_not_hex0"] += 1
        if same:
            counters["same_component_total"] += 1
            if not chaining:
                counters["same_and_not_chaining"] += 1
        rows.append({
            "hash": h, "macro_distance": analysis["macro_distance"], "chaining": chaining,
            "r2_own_component_relation": analysis["r2_own_component_relation"],
            "hex0_touched_before_r2": hex0,
            "r1_source": analysis["r1"]["source_orbit"], "r1_target": analysis["r1"]["target_orbit"],
            "r2_source": analysis["r2"]["source_orbit"], "r2_target": analysis["r2"]["target_orbit"],
            "r1_ell": analysis["r1"]["ell"], "r2_ell": analysis["r2"]["ell"],
        })

    print(json.dumps(counters, indent=2))
    print("hidden-axiom check (hex0 <=> same, WITHIN chaining subset):",
          "PERFECT MATCH" if counters["chaining_and_hex0_and_not_same"] == 0 and counters["chaining_and_same_and_not_hex0"] == 0 else "MISMATCH FOUND")
    print("same-component ==> chaining check:", "HOLDS" if counters["same_and_not_chaining"] == 0 else "COUNTEREXAMPLE FOUND")

    report = {
        "schema": "rr-full-relation-table-v1",
        "total_rr_records_in_corpus": len(full_corpus),
        "literal_witnesses_recovered": len(witnesses),
        "literal_witnesses_missing": len(missing),
        "counters": counters,
        "same_implies_chaining_holds_over_recovered_set": counters["same_and_not_chaining"] == 0,
        "hex0_bridge_iff_same_within_chaining_holds_over_recovered_set": (
            counters["chaining_and_hex0_and_not_same"] == 0 and counters["chaining_and_same_and_not_hex0"] == 0
        ),
        "rows": rows,
    }
    Path(args.output_relation_table).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")

    same_hashes = [r["hash"] for r in rows if r.get("r2_own_component_relation") == "same"]
    candidate_report = {}
    for h in same_hashes:
        candidate_report[h] = local_candidate_enumeration(witnesses[h])
    Path(args.output_candidates).write_text(json.dumps({
        "schema": "rr-same-component-candidates-v1",
        "method": "single macro_edges() enumeration at the boundary right after R1 fires, for each of the 10 same-component witnesses -- bounded, not a search",
        "per_witness": candidate_report,
    }, indent=2, sort_keys=True, default=str), encoding="utf-8")

    print(json.dumps({"wrote": [args.output_witnesses, args.output_relation_table, args.output_candidates]}, indent=2))


if __name__ == "__main__":
    main()
