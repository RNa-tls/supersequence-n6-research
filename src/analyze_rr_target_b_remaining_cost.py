#!/usr/bin/env python3
"""Round 29, sections 11-19: the Target B transition universe, the Phi=0
continuation theorem, the remaining-demand vector, and SAFE lower bounds.

The central structural fact, hand-proved here:

  (C1)  dPhi = ell - 5 for a macro-edge with rotation run ell, and
        Phi >= 0 is exactly Area A's capacity prune.  Hence at Phi = 0
        EVERY future macro-edge must have ell = 5.
  (C2)  an ell=5 macro-edge visits exactly 6 new permutations: the 5
        rotations complete the hexagon the walk currently stands in, and
        the joint enters a new hexagon.  So an ell=5 macro-edge covers
        exactly ONE full hexagon and steps to the next.
  (C3)  therefore, from a Phi=0 state with U unvisited permutations and
        B = TARGET_P - P remaining pass starts, Target B requires
             U = 6*B + 5
        with NO slack -- which is precisely Phi = 0 restated.  Every
        remaining macro-edge must cover 6 FRESH permutations and the walk
        must end with a pure-rotation suffix of exactly 5.

No search is run.  Every bound below is a safe lower bound (it can only
under-estimate), and no heuristic estimate is used anywhere.
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


macro = _load("artbrc", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]


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


def replay(w):
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


def hexagon_census(st):
    """Section 13/15: how many hexagons are complete, partial, untouched."""
    full = partial = untouched = 0
    partial_sizes = Counter()
    for h in range(len(core.ROT_REPS)):
        c = bin(st.hex_masks[h]).count("1")
        if c == 6:
            full += 1
        elif c == 0:
            untouched += 1
        else:
            partial += 1
            partial_sizes[c] += 1
    return {"hexagons_total": len(core.ROT_REPS), "full": full,
            "partial": partial, "untouched": untouched,
            "partial_size_histogram": {str(k): v for k, v in sorted(partial_sizes.items())}}


def transition_universe(st):
    """Section 11: every outgoing macro-edge with full detail."""
    rows = []
    for e in macro.macro_edges(st):
        tr = e.joint
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        sq, sph = exact.ORBIT_PHASE[e.run.state.p]
        tq, tph = exact.ORBIT_PHASE[tr.target]
        parent, find = component_roots(st)
        sr = find(("q", sq)) if ("q", sq) in parent else None
        tg = find(("q", tq)) if ("q", tq) in parent else None
        rows.append({
            "label": f"rot^{e.run.ell};{tr.move.label}",
            "ell": e.run.ell, "move": tr.move.label, "weight": tr.move.weight,
            "kind": k, "legal": reason is None, "prune": reason,
            "target_permutation": list(tr.target),
            "target_orbit": tq, "target_phase": tph,
            "target_hexagon": core.hexagon_id(tr.target),
            "dPhi": phi(tr.state) - phi(st),
            "dF_def": tr.state.F - st.F, "dN": tr.state.Ndef - st.Ndef,
            "dH": tr.state.H - st.H, "dO": tr.state.O - st.O,
            "dvisited": tr.state.visited_count - st.visited_count,
            "new_orbit": bool(tr.new_orbit),
            "merges_components": not (sr is not None and sr == tg),
        })
    return rows


def demand_vector(st):
    """Section 13."""
    U_perm = 720 - st.visited_count
    orbit_phase_rem = 0
    orbits_untouched = 0
    for q in range(len(core.E_REPS)):
        c = bin(st.orbit_masks[q]).count("1")
        orbit_phase_rem += 5 - c
        if c == 0:
            orbits_untouched += 1
    parent, find = component_roots(st)
    comps = len({find(x) for x in list(parent)})
    return {
        "U_perm": U_perm,
        "U_orbit_untouched": orbits_untouched,
        "U_phase": orbit_phase_rem,
        "M_component_current": comps,
        "B_remaining_pass_starts": exact.TARGET_P - st.P,
        "O_capacity_remaining": exact.TARGET_O - st.O,
        "E_endpoint": "a state admitting a pure-rotation suffix",
        "R_suffix_required_rotations": 5,
    }


def lower_bounds(st, dem, hexc):
    """Sections 14-18. Every bound is SAFE: it can only under-estimate."""
    U = dem["U_perm"]
    B = dem["B_remaining_pass_starts"]
    # (C2): an ell=5 macro-edge covers exactly 6 fresh permutations; the walk
    # may additionally end with a pure-rotation suffix of at most 5.
    perm_bound = -(-max(U - 5, 0) // 6)          # ceil((U-5)/6)
    # orbit/phase: each macro-edge's joint fills exactly one (orbit, phase)
    # port that was previously unvisited... not true in general, so the SAFE
    # statement is only about the joint target, one per macro-edge.
    phase_bound = 0                              # deliberately not claimed
    # component merges: each macro-edge merges at most one pair
    merge_bound = 0                              # deliberately not claimed
    cmin = max(perm_bound, phase_bound, merge_bound)
    slack = B - cmin
    return {
        "permutation_coverage_bound": {
            "value": perm_bound,
            "derivation": ("at Phi=0 every future macro-edge has ell=5 (C1) and covers "
                           "exactly 6 fresh permutations (C2); a final pure-rotation "
                           "suffix covers at most 5 more. Hence "
                           "#macro-edges >= ceil((U-5)/6)."),
            "grade": "safe lower bound (손증명)",
        },
        "orbit_phase_bound": {"value": phase_bound,
                              "note": ("not claimed: a joint target may land on an "
                                       "already-open orbit, so no nontrivial safe bound "
                                       "follows from phase demand alone"),
                              "grade": "미완료"},
        "component_merge_bound": {"value": merge_bound,
                                  "note": ("not claimed: the required FINAL component "
                                           "structure for Target B is not characterised, "
                                           "so no deficit can be computed"),
                                  "grade": "미완료"},
        "C_min": cmin,
        "B_available": B,
        "slack": slack,
        "exact_packing_identity": {
            "U": U, "B": B, "6B_plus_5": 6 * B + 5,
            "U_equals_6B_plus_5": U == 6 * B + 5,
            "meaning": ("Phi = 0 says exactly U = 6B + 5. So the continuation must be a "
                        "PERFECT packing: all B remaining macro-edges at ell=5, each "
                        "covering 6 previously unvisited permutations, then a "
                        "pure-rotation suffix of exactly 5, leaving nothing over."),
        },
        "hexagon_reading": {
            "note": ("an ell=5 macro-edge completes the hexagon the walk stands in (5 "
                     "rotations) and steps into the next (1 joint target). So Target B is "
                     "a walk that completes every remaining hexagon exactly once."),
            "hexagons_full": hexc["full"], "hexagons_partial": hexc["partial"],
            "hexagons_untouched": hexc["untouched"],
        },
    }


def pure_suffix_check(st):
    """Section 18: can a pure-rotation suffix be appended HERE?  (This is the
    terminal test, applied at the post-R2 state itself -- not a claim about
    reachable terminals.)"""
    cur, steps = st, 0
    for _ in range(5):
        tr = exact.extend(cur, W1)
        if tr is None:
            break
        cur = tr.state
        steps += 1
    return {"rotations_available_now": steps, "needs": 5,
            "suffix_appendable_now": steps == 5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--transitions", default=str(ROOT / "outputs" / "rr_target_b_transition_universe.json"))
    ap.add_argument("--demands", default=str(ROOT / "outputs" / "rr_target_b_demand_vectors.json"))
    ap.add_argument("--bounds", default=str(ROOT / "outputs" / "rr_target_b_lower_bounds.json"))
    a = ap.parse_args()

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    trans, dems, bnds, verdicts = [], [], [], []
    sigs = set()
    print("=== section 11: transition universe at the six post-R2 states ===")
    for i, w in enumerate(wits):
        st = replay(w)
        rows = transition_universe(st)
        legal = [r for r in rows if r["legal"]]
        sig = tuple(sorted((r["label"], r["kind"], r["ell"], r["dPhi"]) for r in legal))
        sigs.add(sig)
        dem = demand_vector(st)
        hexc = hexagon_census(st)
        lb = lower_bounds(st, dem, hexc)
        suf = pure_suffix_check(st)
        trans.append({"witness_index": i, "n_outgoing": len(rows),
                      "n_legal": len(legal), "legal_edges": legal,
                      "signature": [list(x) for x in sig]})
        dems.append({"witness_index": i, **dem, "hexagon_census": hexc,
                     "pure_suffix_now": suf})
        bnds.append({"witness_index": i, **lb, "pure_suffix_now": suf})
        print(f"  w{i}: {len(legal)} legal of {len(rows)}; "
              f"{[r['label'] + '/' + r['kind'] for r in legal]}")

    print(f"\n  distinct legal-transition signatures across the six: {len(sigs)}")

    print("\n=== section 13/15: demand and the exact packing identity ===")
    print("  #  U_perm  B    6B+5   U==6B+5   hex full/partial/untouched   C_min  slack")
    for i, (d, b) in enumerate(zip(dems, bnds)):
        h = d["hexagon_census"]
        print(f"  {i}   {d['U_perm']:>4}  {d['B_remaining_pass_starts']:>3}   "
              f"{b['exact_packing_identity']['6B_plus_5']:>4}    "
              f"{str(b['exact_packing_identity']['U_equals_6B_plus_5']):<7}  "
              f"{h['full']:>3}/{h['partial']:>2}/{h['untouched']:>3}"
              f"              {b['C_min']:>4}   {b['slack']:>3}")

    print("\n=== section 18: pure-rotation suffix at the post-R2 state itself ===")
    for i, d in enumerate(dems):
        print(f"  w{i}: rotations available now = {d['pure_suffix_now']['rotations_available_now']} "
              f"(needs 5) -> appendable now: {d['pure_suffix_now']['suffix_appendable_now']}")

    print("\n=== section 19: static contradiction verdict ===")
    for i, b in enumerate(bnds):
        if b["slack"] < 0:
            v = "immediate contradiction (C_min exceeds available pass starts)"
        elif b["orbit_phase_bound"]["value"] == 0 and b["component_merge_bound"]["value"] == 0:
            v = "lower bound incomplete (only the permutation-coverage bound is available)"
        else:
            v = "no contradiction"
        verdicts.append({"witness_index": i, "verdict": v, "slack": b["slack"]})
        print(f"  w{i}: {v}  (slack {b['slack']})")

    Path(a.transitions).write_text(json.dumps({
        "schema": "rr-target-b-transition-universe-v1",
        "phi0_continuation_theorem": {
            "statement": ("at Phi = 0 every admissible future macro-edge has rotation run "
                          "ell = 5"),
            "proof": ("dPhi = ell - 5 (weight-1 rotation: dP=0, dvisited=1 so dPhi=+1; "
                      "joint: dP=1, dvisited=1 so dPhi=-5), and "
                      "macro.remaining_window_capacity_prune is TRUE exactly when Phi < 0, "
                      "so Phi >= 0 is Area A's own capacity prune. Any ell < 5 would make "
                      "Phi negative and be pruned."),
            "grade": "손증명",
        },
        "identical_signature_across_witnesses": len(sigs) == 1,
        "n_distinct_signatures": len(sigs),
        "per_witness": trans,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.demands).write_text(json.dumps({
        "schema": "rr-target-b-demand-vectors-v1",
        "definition": ("D_rem = (U_perm, U_orbit, U_phase, M_component, E_endpoint, "
                       "R_suffix)"),
        "per_witness": dems,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.bounds).write_text(json.dumps({
        "schema": "rr-target-b-lower-bounds-v1",
        "safety_note": ("every bound here can only under-estimate; no heuristic estimate "
                        "is used, and none of these may be used as a prune beyond what is "
                        "proved"),
        "per_witness": bnds,
        "static_contradiction_verdicts": verdicts,
        "summary": ("Phi = 0 is exactly the identity U = 6B + 5, so Target B from these "
                    "states demands a PERFECT packing with zero slack: every one of the B "
                    "remaining macro-edges must have ell=5 and cover 6 previously "
                    "unvisited permutations -- i.e. complete one whole hexagon -- and the "
                    "walk must finish with a pure-rotation suffix of exactly 5. No "
                    "immediate contradiction follows, and none is manufactured."),
        "grade": "safe lower bound (permutation coverage) + 미완료 (phase and merge bounds)",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.transitions)
    print("wrote", a.demands)
    print("wrote", a.bounds)


if __name__ == "__main__":
    main()
