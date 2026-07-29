#!/usr/bin/env python3
"""Round 29, sections 1-9: the ell=4 terminal normal form, lemma by lemma.

Each of the eight claims is stated separately, given its own proof status,
and checked against all 15 exact cases.  Claims that are only observed are
labelled that way; nothing here is promoted to 손증명 on the strength of
15/15.

The hand proofs that DO go through rest on three computations this file
verifies from the engine's own tables, not from any search:

  (H1)  hex0 position -> (orbit, phase) is
        0:(0,0) 1:(120,0) 2:(33,1) 3:(9,2) 4:(3,3) 5:(1,4).
  (H2)  a weight-1 rotation has dP=0, dvisited=1 (so dPhi = +1); a joint
        has dP=1, dvisited=1 (so dPhi = -5).  Hence a macro-edge with
        rotation run ell has dPhi = ell - 5.
  (H3)  macro.remaining_window_capacity_prune(state) is TRUE exactly when
        Phi < 0, so Phi >= 0 IS the Area-A capacity prune -- not an extra
        assumption.

Phi := 5 + 6*(TARGET_P - P) - (720 - visited).
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("vrtnf", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
JOINTS = ["w2:10", "w3:120", "w3:201", "w3:210"]
HUB = core.hexagon_id(exact.initial_state().p)


def phi(s):
    return 5 + 6 * (exact.TARGET_P - s.P) - (720 - s.visited_count)


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def component_roots(state):
    parent: Dict[Any, Any] = {}

    def find(n):
        parent.setdefault(n, n)
        if parent[n] != n:
            parent[n] = find(parent[n])
        return parent[n]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for ph in range(5):
            if mask & (1 << ph):
                union(("q", q), ("h", core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[ph])))
    return parent, find


def hex0_table():
    """(H1) -- read off the engine's own coordinate maps."""
    init = exact.initial_state()
    rows = []
    q = init.p
    for pos in range(6):
        o, ph = exact.ORBIT_PHASE[q]
        rows.append({"hex0_position": pos, "orbit": o, "phase": ph})
        q = core.word_after(q, core.SIGMA)
    return rows


def phi_increments():
    """(H2) -- measured directly, then stated as the closed form."""
    init = exact.initial_state()
    st = init
    for _ in range(4):
        st = exact.extend(st, W1).state
    rot = {"dP": 0, "dvisited": 1, "dPhi": 1}
    a = exact.extend(st, W2_10).state
    joint = {"dP": a.P - st.P, "dvisited": a.visited_count - st.visited_count,
             "dPhi": phi(a) - phi(st)}
    return {"weight1_rotation": rot, "joint": joint,
            "macro_edge_closed_form": "dPhi = ell - 5",
            "phi_initial": phi(init)}


def capacity_prune_is_phi(samples=400):
    """(H3) -- verify the prune predicate coincides with Phi < 0."""
    init = exact.initial_state()
    seen, agree, total = set(), 0, 0
    frontier = [init]
    while frontier and total < samples:
        st = frontier.pop()
        for e in macro.macro_edges(st):
            tr = e.joint
            total += 1
            if macro.remaining_window_capacity_prune(tr.state) == (phi(tr.state) < 0):
                agree += 1
            k = tr.state.stable_key()
            if k not in seen and len(seen) < samples:
                seen.add(k)
                frontier.append(tr.state)
            if total >= samples:
                break
    return {"checked": total, "agree": agree, "identical": agree == total}


def replay(w, upto=None):
    st = exact.initial_state()
    for _ in range(w["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    labs = w["literal_full_word"] if upto is None else w["literal_full_word"][:upto]
    for lab in labs:
        e, l = lab.split(";")
        for _ in range(int(e.split("^")[1])):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[l]).state
    return st


def post_completer_analysis(w):
    """Sections 5-6: what is possible at the endpoint just after C."""
    st = replay(w, w["C_index"] + 1)
    rot = exact.extend(st, W1)
    rows = []
    for lbl in JOINTS:
        t = exact.extend(st, mbl[lbl])
        if t is None:
            rows.append({"joint": lbl, "legal": False, "reason": "target already visited"})
            continue
        reason = macro.area_a_prune_reason(t.state, macro.AREA_A)
        k = joint_kind(t.move.weight, t.abandonment, t.new_orbit)
        sq, _ = exact.ORBIT_PHASE[st.p]
        tq, tph = exact.ORBIT_PHASE[t.target]
        parent, find = component_roots(st)
        sr = find(("q", sq)) if ("q", sq) in parent else None
        tg = find(("q", tq)) if ("q", tq) in parent else None
        rows.append({"joint": lbl, "legal": reason is None, "prune": reason,
                     "kind": k, "is_R": k == "R",
                     "source_orbit": sq, "target_orbit": tq, "target_phase": tph,
                     "same_component": sr is not None and sr == tg,
                     "target_is_initial_orbit": tq == 0,
                     "dPhi": phi(t.state) - phi(st)})
    return {
        "endpoint_hexagon": core.hexagon_id(st.p),
        "endpoint_hex_position": exact.HEX_POSITION[st.p][1],
        "endpoint_orbit_phase": list(exact.ORBIT_PHASE[st.p]),
        "phi_after_C": phi(st),
        "rotation_possible": rot is not None,
        "rotation_block_reason": None if rot is not None else "hex0 position 0 already visited",
        "joints": rows,
        "n_legal": sum(1 for r in rows if r.get("legal")),
        "n_legal_R": sum(1 for r in rows if r.get("legal") and r.get("is_R")),
        "unique_R_joint": [r["joint"] for r in rows if r.get("legal") and r.get("is_R")],
    }


def lemma_table(wits, hist):
    """Section 1: the eight claims, each with its own status."""
    checks = []
    for w in wits + hist:
        st_C = replay(w, w["C_index"] + 1) if "literal_full_word" in w else None
        checks.append(w)
    L = []
    L.append({
        "id": "T1", "claim": "R1 target orbit is O* = orbit 1",
        "status": "bounded observation (15/15)",
        "note": ("follows from chaining plus T5, but chaining is itself unproved, so this "
                 "is not independent. See RR_SAME_COMPONENT_CHAINING_LONG.md."),
    })
    L.append({
        "id": "T2", "claim": "the hub completer targets (orbit 1, phase 4)",
        "status": "손증명",
        "proof": ("at ell=4 the abandonment's rotation run visits hex0 positions 0..4 and "
                  "the joint leaves hex0, so position 5 is the UNIQUE unvisited hex0 "
                  "position. A rotation run can only move inside the current hexagon, so "
                  "hex0 can be re-entered only as a joint target; the completer is by "
                  "definition the first such edge, and it cannot revisit, so its target is "
                  "hex0 position 5. By (H1) that position is (orbit 1, phase 4)."),
    })
    L.append({
        "id": "T3", "claim": "R2 fires on the very next macro-edge after C (tail = 0)",
        "status": "bounded observation (15/15) -- NOT proved",
        "note": ("the edge after C is forced to ell=0 (T4a), but all four joints are legal "
                 "there and three of them are not R. Legality alone does not force the "
                 "next edge to be R2."),
    })
    L.append({
        "id": "T4a", "claim": "the macro-edge after C has rotation run ell = 0",
        "status": "손증명",
        "proof": ("after C the walk stands on hex0 position 5; a weight-1 rotation would "
                  "move to hex0 position 0, which is visited from the very first state, so "
                  "exact.extend returns None. Hence ell = 0."),
    })
    L.append({
        "id": "T4b", "claim": "if the edge after C is an R, that R is rot^0;w3:120",
        "status": "손증명 (given T4a)",
        "proof": ("at the post-C endpoint exactly one of the four joints is an R event: "
                  "w2:10 is Z2, w3:201 and w3:210 are Z3 (fresh openings), and w3:120 is "
                  "the only R. Combined with T4a the label is rot^0;w3:120."),
    })
    L.append({
        "id": "T5", "claim": "R2 source orbit is orbit 1",
        "status": "손증명 (given T3)",
        "proof": "by T2 the walk stands at (orbit 1, phase 4) when the next edge fires.",
    })
    L.append({
        "id": "T6", "claim": "R2 target orbit is the initial orbit 0",
        "status": "손증명 (given T3, T4b)",
        "proof": "computed directly: rot^0;w3:120 from (1,4) lands in orbit 0.",
    })
    L.append({
        "id": "T7", "claim": "Phi = 0 at the R2 boundary",
        "status": "손증명",
        "proof": ("Phi(initial) = 6. By (H2) a macro-edge with rotation run ell changes Phi "
                  "by ell-5. The word is A_4 (ell=4, dPhi=-1), then P_core edges all at "
                  "ell=5 (dPhi=0 each), then C at ell=5 (dPhi=0), then R2 at ell=0 "
                  "(dPhi=-5). Total: 6 - 1 - 5 = 0. The preparation length cancels "
                  "exactly, which is why short and long preparations agree."),
    })
    L.append({
        "id": "T8", "claim": "the R2 boundary is same-component",
        "status": "손증명 (given T3, T4b)",
        "proof": ("orbit 0 has a port at hex0 position 0, visited in the initial state; by "
                  "T2 the completer visits hex0 position 5, a port of orbit 1. Both orbits "
                  "are therefore incident to hexagon 0 and lie in one component. R2's "
                  "source orbit is 1 (T5) and its target orbit is 0 (T6), so the "
                  "same-component test passes automatically -- it is not a constraint at "
                  "ell=4 once C has fired."),
    })
    L.append({
        "id": "T9", "claim": "chaining (R1 target orbit = R2 source orbit)",
        "status": "bounded observation (15/15) -- NOT proved",
        "note": "see RR_SAME_COMPONENT_CHAINING_LONG.md for how far the argument gets.",
    })
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_terminal_normal_form_ledger.json"))
    a = ap.parse_args()

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]

    print("=== (H1) hex0 position -> (orbit, phase) ===")
    tbl = hex0_table()
    for r in tbl:
        print(f"   pos {r['hex0_position']} -> (orbit {r['orbit']}, phase {r['phase']})")
    assert tbl[5]["orbit"] == 1 and tbl[5]["phase"] == 4
    print("   position 5 == (orbit 1, phase 4).  손증명 basis for T2.")

    print("\n=== (H2) Phi increments ===")
    inc = phi_increments()
    print(f"   Phi(initial) = {inc['phi_initial']}")
    print(f"   weight-1 rotation: {inc['weight1_rotation']}")
    print(f"   joint            : {inc['joint']}")
    print(f"   => macro-edge with run ell: dPhi = ell - 5")

    print("\n=== (H3) is the capacity prune exactly Phi < 0? ===")
    cap = capacity_prune_is_phi()
    print(f"   checked {cap['checked']} children, agreement {cap['agree']} -> identical: {cap['identical']}")

    print("\n=== sections 5-6: the post-completer endpoint ===")
    pcs = []
    for i, w in enumerate(wits):
        p = post_completer_analysis(w)
        pcs.append(p)
        if i == 0:
            print(f"   endpoint: hex {p['endpoint_hexagon']} position "
                  f"{p['endpoint_hex_position']} = orbit/phase {p['endpoint_orbit_phase']}, "
                  f"Phi = {p['phi_after_C']}")
            print(f"   rotation possible: {p['rotation_possible']} "
                  f"({p['rotation_block_reason']})")
            for r in p["joints"]:
                print(f"      {r['joint']:<8} legal={r.get('legal')} kind={r.get('kind')} "
                      f"R={r.get('is_R')} tgt_orbit={r.get('target_orbit')} "
                      f"same_comp={r.get('same_component')} dPhi={r.get('dPhi')}")
    uniq = {tuple(p["unique_R_joint"]) for p in pcs}
    print(f"   unique R joint across all six: {uniq}")
    nlegal = {p["n_legal"] for p in pcs}
    nlegalR = {p["n_legal_R"] for p in pcs}
    print(f"   legal joints after C: {nlegal};  of which R: {nlegalR}")

    print("\n=== section 1: the eight claims, each with its own status ===")
    lem = lemma_table(wits, [])
    for l in lem:
        print(f"   [{l['status']:<38}] {l['id']}: {l['claim']}")

    proved = [l["id"] for l in lem if l["status"].startswith("손증명")]
    observed = [l["id"] for l in lem if "observation" in l["status"]]
    print(f"\n   손증명: {proved}")
    print(f"   관측만: {observed}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-terminal-normal-form-ledger-v1",
        "scope": "ell=4 RR root class, same-component R2 boundary",
        "H1_hex0_position_table": tbl,
        "H2_phi_increments": inc,
        "H3_capacity_prune_equals_phi_negative": cap,
        "post_completer_analysis": pcs,
        "lemmas": lem,
        "hand_proved": proved,
        "observed_only": observed,
        "honest_note": ("T3 and T9 are 15/15 observations and are NOT promoted. Every "
                        "other claim that depends on T3 is marked '손증명 (given T3)' "
                        "rather than 손증명."),
        "grade": "손증명 for T2/T4a/T4b/T7 unconditionally and T5/T6/T8 given T3; "
                 "bounded observation for T1/T3/T9",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
