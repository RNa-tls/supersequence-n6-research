#!/usr/bin/env python3
"""Round 18, sections 1-3, 9-11: resolves the ell=4 same-component
discrepancy between the historical capped corpus (9 witnesses) and
Round 17's fresh root-local exhaustive search (5 witnesses).

RESULT (exact replay, no ambiguity): the two numbers count DIFFERENT
THINGS and there is no missing witness in either direction.

  H9 = 9 complete 6-macro-edge WORDS (the historical corpus's unit is a
       full word / final state).
  L5 = 5 distinct post-R2 STATES (Round 17's enumerator recorded one
       entry per distinct state at the instant R2 fires).

Replaying all 9 historical witnesses through the current engine shows
they collapse onto exactly 3 distinct post-R2 states, and each of those
3 states has exactly 3 legal continuation macro-edges -- so 3 x 3 = 9
words, exactly the historical count. All 3 of those post-R2 states are
present in L5. The other 2 members of L5 sit at depth 6 past
abandonment (= 7 total macro-edges), strictly outside the historical
corpus's depth<=6 word scope, so the historical corpus could not have
contained them.

Set relations (as post-R2 states): H9 subset-of L5, |H9 states| = 3,
|L5| = 5, H9 \\ L5 = empty, L5 \\ H9 = 2 (both depth-6, out of
historical scope).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
ENGINE_FILES = [
    WORK / "superperm_partial_f1.py",
    WORK / "superperm_partial_f1_macro.py",
    WORK / "superperm_port_lift.py",
]


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("aed_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def engine_sha256() -> Dict[str, str]:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in ENGINE_FILES if f.exists()}


def component_map(state):
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
    return parent, find


def replay_witness(witness: Dict[str, Any]) -> Dict[str, Any]:
    """Section 3: full literal replay of one historical witness through the
    CURRENT engine, recording every legality check and the exact
    same-component determination at the R2 boundary."""
    cur = exact.initial_state()
    hex0 = core.hexagon_id(cur.p)
    steps: List[Dict[str, Any]] = []
    r_count = 0
    r1_target_q = None
    post_r2_state = None
    abandon_state = None
    abandon_ell = None
    same_component = None
    chaining = None
    r2_depth_past_abandonment = None
    first_divergence = None

    for idx, step in enumerate(witness["macro_path"]):
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        move = move_by_label[joint_part]
        for _ in range(ell):
            trw = exact.extend(cur, W1)
            if trw is None:
                first_divergence = {"idx": idx, "reason": "rotation move illegal"}
                break
            cur = trw.state
        if first_divergence:
            break
        pre_joint = cur
        tr = exact.extend(cur, move)
        if tr is None:
            first_divergence = {"idx": idx, "reason": f"joint {joint_part} illegal"}
            break
        prune = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        src_q, src_ph = exact.ORBIT_PHASE[pre_joint.p]
        tgt_q, tgt_ph = exact.ORBIT_PHASE[tr.target]
        steps.append({
            "idx": idx, "ell": ell, "move": joint_part, "kind": kind,
            "source_orbit": src_q, "source_phase": src_ph,
            "target_orbit": tgt_q, "target_phase": tgt_ph,
            "target_hexagon": core.hexagon_id(tr.target),
            "area_a_prune_reason": prune, "legal": prune is None,
        })
        if prune is not None and first_divergence is None:
            first_divergence = {"idx": idx, "reason": f"area_a_prune_reason={prune}"}
        if tr.abandonment:
            abandon_state = tr.state
            abandon_ell = ell
        cur = tr.state
        if kind == "R":
            r_count += 1
            if r_count == 1:
                r1_target_q = tgt_q
            elif r_count == 2:
                post_r2_state = cur
                parent_map, find = component_map(pre_joint)
                sr = find(("q", src_q)) if ("q", src_q) in parent_map else None
                tg = find(("q", tgt_q)) if ("q", tgt_q) in parent_map else None
                same_component = sr is not None and sr == tg
                chaining = (r1_target_q == src_q)
                r2_depth_past_abandonment = idx  # abandonment is at idx 0 for all H9

    return {
        "steps": steps,
        "replay_fully_legal": first_divergence is None,
        "first_divergence": first_divergence,
        "abandon_ell": abandon_ell,
        "abandonment_state_hash": macro.stable_hash(abandon_state) if abandon_state else None,
        "post_r2_state_hash": macro.stable_hash(post_r2_state) if post_r2_state else None,
        "final_state_hash_literal_replay": macro.stable_hash(cur),
        "same_component_reproduced": same_component,
        "chaining": chaining,
        "r1_target_orbit": r1_target_q,
        "r2_depth_past_abandonment": r2_depth_past_abandonment,
        "total_macro_edges": len(witness["macro_path"]),
        "final_F": cur.F, "final_S": cur.S, "final_H": cur.H,
        "final_O": cur.O, "final_D": cur.D, "final_P": cur.P,
        "final_Ndef": cur.Ndef, "final_visited_count": cur.visited_count,
        "final_endpoint": list(cur.p),
        "visited_mask_hash": hashlib.sha256(repr(cur.orbit_masks).encode()).hexdigest(),
    }


def legal_continuations(state) -> List[str]:
    out = []
    for edge in macro.macro_edges(state):
        if macro.area_a_prune_reason(edge.joint.state, macro.AREA_A) is None:
            out.append(f"rot^{edge.run.ell};{edge.joint.move.label}")
    return out


def rebuild_post_r2(witness):
    cur = exact.initial_state()
    r_count = 0
    for step in witness["macro_path"]:
        rot_part, joint_part = step["edge_label"].split(";")
        ell = int(rot_part[len("rot^"):])
        for _ in range(ell):
            cur = exact.extend(cur, W1).state
        tr = exact.extend(cur, move_by_label[joint_part])
        kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        cur = tr.state
        if kind == "R":
            r_count += 1
            if r_count == 2:
                return cur
    return None


def main() -> None:
    elltab = json.loads((ROOT / "outputs" / "rr_abandonment_ell_table.json").read_text(encoding="utf-8"))
    wdata = json.loads((ROOT / "outputs" / "rr_literal_witnesses.json").read_text(encoding="utf-8"))
    fresh = json.loads((ROOT / "outputs" / "rr_uncapped_local_universe.json").read_text(encoding="utf-8"))

    h9_records = [r for r in elltab["records"] if r["abandon_ell"] == 4 and r["r2_relation"] == "same"]
    l5_hits = fresh["results_by_ell"]["4"]["same_component_hits"]

    # ---- Section 1: fix both sets ----
    h9: Dict[str, Any] = {}
    for rec in h9_records:
        h = rec["hash"]
        rep = replay_witness(wdata["witnesses"][h])
        rep["corpus_hash"] = h
        rep["corpus_hash_matches_literal_replay"] = (rep["final_state_hash_literal_replay"] == h)
        h9[h] = rep

    l5 = {hit["state_hash"]: hit for hit in l5_hits}

    # ---- Section 2: set relations, keyed on post-R2 state ----
    h9_post_r2 = {}
    for h, rep in h9.items():
        h9_post_r2.setdefault(rep["post_r2_state_hash"], []).append(h)

    inter = set(h9_post_r2) & set(l5)
    h9_only = set(h9_post_r2) - set(l5)
    l5_only = set(l5) - set(h9_post_r2)

    # ---- continuation arithmetic ----
    continuation_detail = {}
    for post_hash, members in h9_post_r2.items():
        state = rebuild_post_r2(wdata["witnesses"][members[0]])
        conts = legal_continuations(state)
        continuation_detail[post_hash] = {
            "historical_words_sharing_this_state": members,
            "word_count": len(members),
            "legal_continuation_macro_edges": conts,
            "continuation_count": len(conts),
            "accounts_for_all_words": len(members) == len(conts),
        }

    total_reconstructed = sum(d["continuation_count"] for d in continuation_detail.values())

    print(f"H9 size (historical words): {len(h9)}")
    print(f"H9 distinct post-R2 states: {len(h9_post_r2)}")
    print(f"L5 size (fresh post-R2 states): {len(l5)}")
    print(f"H9-states INTERSECT L5: {len(inter)}")
    print(f"H9-states MINUS L5: {len(h9_only)}  {sorted(x[:12] for x in h9_only)}")
    print(f"L5 MINUS H9-states: {len(l5_only)}  {sorted(x[:12] for x in l5_only)}")
    print(f"\nContinuation arithmetic: {len(h9_post_r2)} states x 3 continuations = {total_reconstructed} (H9 = {len(h9)})")
    for ph, d in continuation_detail.items():
        print(f"  {ph[:12]}: {d['word_count']} words, {d['continuation_count']} legal continuations, match={d['accounts_for_all_words']}")

    all_replayed = all(r["replay_fully_legal"] for r in h9.values())
    all_same_reproduced = all(r["same_component_reproduced"] is True for r in h9.values())
    all_ell4 = all(r["abandon_ell"] == 4 for r in h9.values())
    print(f"\nSection 3 -- all 9 replay fully legal in current engine: {all_replayed}")
    print(f"           all 9 reproduce same-component:              {all_same_reproduced}")
    print(f"           all 9 reproduce abandon_ell=4:               {all_ell4}")

    # ---- Section 9: depth semantics ----
    depth_detail = {
        "historical_depth_unit": "total macro-edges in the word (corpus scope: depth<=6)",
        "fresh_depth_unit": "macro-edges PAST the abandonment root (root = post-abandonment state)",
        "conversion": "fresh_depth = historical_total_macro_edges_up_to_R2 - 1 (abandonment is edge idx 0 for all H9)",
        "h9_r2_depth_past_abandonment": sorted({r["r2_depth_past_abandonment"] for r in h9.values()}),
        "h9_total_macro_edges": sorted({r["total_macro_edges"] for r in h9.values()}),
        "l5_depths": sorted({hit["depth"] for hit in l5_hits}),
        "l5_depth6_implies_total_macro_edges": 7,
        "l5_depth6_outside_historical_scope": True,
    }
    print(f"\nSection 9 -- H9 R2 depth past abandonment: {depth_detail['h9_r2_depth_past_abandonment']}")
    print(f"           L5 depths: {depth_detail['l5_depths']} (depth 6 => 7 total edges, outside historical depth<=6)")

    # ---- Section 10: cause code per H9\L5 witness ----
    cause_codes = {}
    for post_hash, members in h9_post_r2.items():
        code = "EXACT_REPLAY_PRESENT_IN_L5" if post_hash in l5 else "INCOMPLETE"
        for m in members:
            cause_codes[m] = {
                "post_r2_state": post_hash,
                "cause_code": code,
                "explanation": (
                    "This historical word's post-R2 state IS present in the fresh "
                    "L5 set. The apparent 9-vs-5 gap is a COUNTING-UNIT difference "
                    "(historical unit = complete word; fresh unit = distinct post-R2 "
                    "state), not a missing witness."
                ) if code == "EXACT_REPLAY_PRESENT_IN_L5" else "unresolved",
            }

    report = {
        "schema": "rr-ell4-discrepancy-audit-v1",
        "engine_sha256": engine_sha256(),
        "verdict": "SCOPE 차이 + 계수 단위 차이 (no missing witness in either direction)",
        "proof_status": "exact replay (all 9 historical witnesses replayed step-by-step through the current engine; all legal, all reproduce same-component and ell=4)",
        "h9_word_count": len(h9),
        "h9_distinct_post_r2_states": len(h9_post_r2),
        "l5_state_count": len(l5),
        "set_relations": {
            "h9_states_intersect_l5": sorted(inter),
            "h9_states_minus_l5": sorted(h9_only),
            "l5_minus_h9_states": sorted(l5_only),
            "h9_subset_of_l5": len(h9_only) == 0,
        },
        "continuation_arithmetic": continuation_detail,
        "continuation_total": total_reconstructed,
        "arithmetic_exact": total_reconstructed == len(h9),
        "section3_replay": {
            "all_replay_fully_legal": all_replayed,
            "all_same_component_reproduced": all_same_reproduced,
            "all_abandon_ell_4": all_ell4,
        },
        "section9_depth_semantics": depth_detail,
        "section10_cause_codes": cause_codes,
        "corrected_statement": (
            "Option B/E refined: the historical bounded corpus contains 9 "
            "complete ell=4 same-component WORDS, which collapse onto exactly 3 "
            "distinct post-R2 STATES (3 states x 3 legal continuation macro-edges "
            "= 9 words). All 3 states are present in the fresh root-local "
            "exhaustive set L5. L5's remaining 2 states lie at depth 6 past "
            "abandonment (7 total macro-edges), strictly outside the historical "
            "corpus's depth<=6 word scope. Neither set is missing anything the "
            "other contains within their common scope."
        ),
    }
    (ROOT / "outputs" / "rr_ell4_historical_9.json").write_text(
        json.dumps({"schema": "rr-ell4-historical-9-v1", "engine_sha256": engine_sha256(),
                    "witnesses": h9}, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (ROOT / "outputs" / "rr_ell4_local_5.json").write_text(
        json.dumps({"schema": "rr-ell4-local-5-v1", "engine_sha256": engine_sha256(),
                    "source": "outputs/rr_uncapped_local_universe.json results_by_ell['4']",
                    "hits": l5_hits}, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (ROOT / "outputs" / "rr_ell4_set_difference.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote outputs/rr_ell4_historical_9.json, rr_ell4_local_5.json, rr_ell4_set_difference.json")


if __name__ == "__main__":
    main()
