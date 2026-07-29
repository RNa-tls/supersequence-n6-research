#!/usr/bin/env python3
"""Round 28, sections 13-15: Target B's definition and its STATIC ledger.

No Target B search is run here.  This file computes, for each of the six
post-R2 states, what a Target B continuation would have to accomplish and
whether any of it is already statically contradictory.

TARGET B (fixed here, and deliberately narrower than "a completion"):

    starting from a same-component R2 boundary state S, an admissible
    terminal continuation is a sequence of legal macro-edges that
      (i)   never revisits a permutation,
      (ii)  never abandons again (F_def stays 1) and never adds a hub
            defect (H stays 0),
      (iii) adds no further R event (N_def stays 2 -- the RR word is
            already closed at R2),
      (iv)  passes area_a_prune_reason at every state, and
      (v)   ends at a state admitting a pure-rotation suffix, i.e. a
            legal terminal boundary in the sense the project already uses
            for Area A.

Target C (a full NR6 completion covering all 720 permutations) is a
STRICTLY stronger requirement and is not what Target B asks for.  The two
must not be blurred: Target B is about admissibility of the slab
continuation, Target C is about the global lower bound.

The static ledger below reports remaining demand and looks for an
immediate contradiction.  If none exists, that is reported as "none" --
it is NOT dressed up as a search failure, and it is NOT evidence that a
continuation exists.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("brtbl", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]


def replay_full(w):
    st = exact.initial_state()
    for _ in range(w["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lab in w["literal_full_word"]:
        e, l = lab.split(";")
        for _ in range(int(e.split("^")[1])):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[l]).state
    return st


def static_ledger(st):
    visited = st.visited_count
    remaining_perms = 720 - visited
    orbit_phase_remaining = 0
    orbits_untouched = 0
    orbits_partial = 0
    for q, mask in enumerate(st.orbit_masks):
        c = bin(mask).count("1")
        orbit_phase_remaining += 5 - c
        if c == 0:
            orbits_untouched += 1
        elif c < 5:
            orbits_partial += 1
    edges = list(macro.macro_edges(st))
    legal = []
    for e in edges:
        tr = e.joint
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        legal.append({"label": f"rot^{e.run.ell};{tr.move.label}",
                      "prune": reason,
                      "legal": reason is None,
                      "abandonment": bool(tr.abandonment),
                      "new_orbit": bool(tr.new_orbit),
                      "weight": tr.move.weight})
    n_legal = sum(1 for x in legal if x["legal"])
    phi = 5 + 6 * (exact.TARGET_P - st.P) - (720 - visited)
    return {
        "visited_count": visited,
        "remaining_unvisited_permutations": remaining_perms,
        "P": st.P, "O": st.O, "D": st.D, "S": st.S,
        "F_def": st.F, "H": st.H, "N_def": st.Ndef,
        "TARGET_P": exact.TARGET_P, "TARGET_O": exact.TARGET_O,
        "TARGET_D": exact.TARGET_D, "TARGET_F": exact.TARGET_F,
        "remaining_P_demand": exact.TARGET_P - st.P,
        "remaining_O_capacity": exact.TARGET_O - st.O,
        "orbit_phases_remaining": orbit_phase_remaining,
        "orbits_untouched": orbits_untouched,
        "orbits_partially_visited": orbits_partial,
        "phi": phi,
        "n_outgoing_macro_edges": len(edges),
        "n_legal_outgoing": n_legal,
        "outgoing_prune_histogram": dict(Counter(
            x["prune"] or "LEGAL" for x in legal)),
        "outgoing_edges": legal,
    }


SAFE_PRUNES = [
    {"prune": "repeated permutation",
     "statement": "exact.extend returns None when the target permutation is already visited",
     "proof": ("a walk visits each permutation at most once by definition of the model; "
               "such a successor state does not exist"),
     "state_local": True, "grade": "손증명"},
    {"prune": "F_def budget",
     "statement": "a second abandonment makes F_def = 2 > TARGET_F = 1",
     "proof": "area_a_prune_reason returns F_exceeded; monotone, never repaid",
     "state_local": True, "grade": "손증명"},
    {"prune": "N/H budget",
     "statement": "the RR word is closed at R2 with N_def = 2, H = 0; TARGET_BUDGET = N + H = 3",
     "proof": "N_def and H are monotone non-decreasing, so an excess can never be repaid",
     "state_local": True, "grade": "손증명"},
    {"prune": "Phi < 0",
     "statement": "Phi = 5 + 6*(TARGET_P - P) - (720 - visited) must stay >= 0",
     "proof": ("Phi is the slab shortfall functional already used by Area A; a negative "
               "value means the remaining permutations cannot be covered within the cost slab"),
     "state_local": True, "grade": "손증명"},
    {"prune": "unavailable required phase",
     "statement": "a required (orbit, phase) port is already visited",
     "proof": "orbit_masks records visited ports; a visited port cannot be entered again",
     "state_local": True, "grade": "손증명"},
    {"prune": "component merge deficit",
     "statement": ("the number of remaining merges needed to join all touched components "
                   "exceeds the number of remaining joint events available"),
     "proof": "each macro-edge merges at most one pair of components",
     "state_local": False, "grade": "손증명 후보 -- 미완료 (the available-event count is not bounded yet)"},
    {"prune": "no legal terminal endpoint",
     "statement": "no reachable state admits a pure-rotation suffix",
     "proof": "not established; would require the terminal characterization",
     "state_local": False, "grade": "미완료"},
    {"prune": "impossible remaining cost",
     "statement": "a lower bound on the remaining macro-edge cost exceeds the slab budget",
     "proof": "not established; no nontrivial lower bound on remaining cost exists yet",
     "state_local": False, "grade": "미완료"},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_target_b_static_ledgers.json"))
    a = ap.parse_args()

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    rows = []
    print("=== Target B static ledger at the six post-R2 states ===")
    print(" #  visited  remaining  P   O   phi  legal_out  prune histogram")
    for i, w in enumerate(wits):
        st = replay_full(w)
        assert w["post_r2_state_hash"], "witness must carry its post-R2 hash"
        led = static_ledger(st)
        led["witness_index"] = i
        led["root_ell"] = w["root_ell"]
        led["excursion_symbolic"] = w["excursion_symbolic"]
        rows.append(led)
        print(f" {i}   {led['visited_count']:>3}     {led['remaining_unvisited_permutations']:>3}    "
              f"{led['P']:>2}  {led['O']:>2}   {led['phi']:>2}      "
              f"{led['n_legal_outgoing']}       {led['outgoing_prune_histogram']}")

    contradictions = []
    for led in rows:
        why = []
        if led["phi"] < 0:
            why.append("phi < 0")
        if led["F_def"] > exact.TARGET_F:
            why.append("F_def over budget")
        if led["O"] > exact.TARGET_O:
            why.append("O over budget")
        if led["n_legal_outgoing"] == 0 and led["remaining_unvisited_permutations"] > 0:
            why.append("no legal outgoing macro-edge while permutations remain")
        if why:
            contradictions.append({"witness_index": led["witness_index"], "reasons": why})

    print(f"\nimmediate static contradictions: {len(contradictions)}")
    for c in contradictions:
        print(f"   witness {c['witness_index']}: {c['reasons']}")
    if not contradictions:
        print("   none. This is reported as 'none' -- it is NOT evidence that a Target B")
        print("   continuation exists, and it is NOT a search failure.")

    print(f"\n=== safe prunes prepared for a future Target B search ===")
    for p in SAFE_PRUNES:
        print(f"   [{p['grade']:<38}] {p['prune']}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-target-b-static-ledgers-v1",
        "target_B_definition": {
            "statement": ("from a same-component R2 boundary state S, a sequence of legal "
                          "macro-edges that never revisits a permutation, keeps F_def = 1 "
                          "and H = 0, adds no further R event (N_def stays 2), passes "
                          "area_a_prune_reason throughout, and ends at a state admitting a "
                          "pure-rotation suffix"),
            "not_target_C": ("Target C is a full NR6 completion covering all 720 "
                             "permutations and is strictly stronger; the two are not "
                             "blurred here"),
            "constraints": {"F_def": 1, "H": 0, "N_def": 2,
                            "TARGET_P": exact.TARGET_P, "TARGET_O": exact.TARGET_O,
                            "TARGET_D": exact.TARGET_D},
        },
        "no_search_was_run": True,
        "ledgers": rows,
        "immediate_static_contradictions": contradictions,
        "contradiction_verdict": ("none" if not contradictions else "present"),
        "honest_note": ("no immediate contradiction is NOT evidence of feasibility; Target B "
                        "remains 미완료 and a targeted search is deferred"),
        "safe_prunes_for_future_target_b_search": SAFE_PRUNES,
        "grade": "exact replay (ledgers) + 손증명 (the prune proofs marked as such) + 미완료 (Target B itself)",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
