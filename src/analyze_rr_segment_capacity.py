#!/usr/bin/env python3
"""Round 32, sections 7-11, 13: segment defect budgets and the
R-reentry penalty.

Three successively stronger safe bounds, each stated with its own
assumptions (section 20):

  (A) coarse                B+1 <= 5(m+1)
  (B) initial-phase refined B+1 <= c(q_0) + 5*m
  (C) segment-defect        B+1 <= 5(m+1) - sum_i d_i,  d_i = 5 - cap(S_i)

and the new ingredient of this round, which turns (B) into a strictly
stronger bound:

  ORBIT-REUSE PENALTY (손증명).  A segment entered by an orbit-changing R
  edge lies in an orbit that is ALREADY OPEN -- that is exactly what makes
  the edge an R rather than a fresh opening (new_orbit is False).  An open
  orbit has at least one visited port, so such a segment has capacity at
  most 4.  Hence the R slots contribute 4 each, not 5:

      B+1 <= c(q_0) + sum over the O_cap largest c(q) + 4*R_cap.

Nothing here runs a permutation-level DFS.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
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


macro = _load("arsc", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
ORBIT_HEX = [tuple(core.hexagon_id(p) for p in core.ports_of_e_orbit(core.E_REPS[q]))
             for q in range(len(core.E_REPS))]


def replay_historical(ell, prep):
    st = exact.initial_state()
    for _ in range(ell):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for s in prep["preparation_trace"]:
        for _ in range(s["ell"]):
            tr = exact.extend(st, W1)
            if tr is None:
                return None
            st = tr.state
        tr = exact.extend(st, mbl[s["joint"]])
        if tr is None:
            return None
        st = tr.state
    for _ in range(prep["ell_profile"][-1]):
        tr = exact.extend(st, W1)
        if tr is None:
            return None
        st = tr.state
    for lbl, mv in mbl.items():
        if mv.weight != 3:
            continue
        tr = exact.extend(st, mv)
        if tr is None:
            continue
        q, ph = exact.ORBIT_PHASE[tr.target]
        if q == prep["r2_target_orbit"] and ph == prep["r2_target_phase"]:
            return tr.state
    return None


def analyse(st):
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(macro.AREA_A.n_limit - st.Ndef, 0)
    uh = {h for h in range(len(core.ROT_REPS)) if st.hex_masks[h] == 0}
    c = {q: sum(1 for h in ORBIT_HEX[q] if h in uh) for q in range(len(core.E_REPS))}
    unopened = [q for q in range(len(core.E_REPS)) if st.orbit_masks[q] == 0]
    q0, _ = exact.ORBIT_PHASE[st.p]
    c0 = min(c[q0] + 1, 5)
    top = sorted((c[q] for q in unopened), reverse=True)[:O_cap]
    coarse = 5 * (O_cap + R_cap + 1)
    refined_r5 = c0 + sum(top) + 5 * R_cap
    refined_r4 = c0 + sum(top) + 4 * R_cap
    m1 = O_cap + R_cap + 1
    f_min = max((B + 1) - 4 * m1, 0)          # section 7: required full segments
    # section 13: hexagon-disjoint ceiling among orbits usable for full segments
    avail_full = [q for q in unopened if c[q] == 5]
    used, chosen = set(), []
    for q in sorted(avail_full):
        if not (set(ORBIT_HEX[q]) & used):
            chosen.append(q)
            used |= set(ORBIT_HEX[q])
    return {
        "B": B, "B_plus_1": B + 1, "O_cap": O_cap, "R_cap": R_cap,
        "m_plus_1_max_segments": m1,
        "current_orbit": q0, "c_current_orbit": c0,
        "sum_top_O_cap": sum(top),
        "bound_A_coarse": coarse,
        "bound_B_initial_refined": refined_r5,
        "bound_B_with_R_penalty": refined_r4,
        "margin_A": coarse - (B + 1),
        "margin_B": refined_r5 - (B + 1),
        "margin_B_R": refined_r4 - (B + 1),
        "contradiction_A": (B + 1) > coarse,
        "contradiction_B": (B + 1) > refined_r5,
        "contradiction_B_R": (B + 1) > refined_r4,
        "required_full_segments_f_min": f_min,
        "n_unopened_orbits": len(unopened),
        "n_orbits_with_full_5_ports": len(avail_full),
        "greedy_hexagon_disjoint_full_orbits": len(chosen),
        "greedy_is_a_LOWER_bound_on_max_disjoint": True,
        "safe_ceiling_on_disjoint_full_orbits": len(uh) // 5,
        "hexagon_disjointness_blocks_f_min": (len(uh) // 5) < f_min,
        "note_disjointness": ("the greedy family is a LOWER bound on the maximum "
                              "hexagon-disjoint set, so it can never certify an "
                              "obstruction; the safe ceiling floor(#unvisited hexagons / 5) "
                              "is used for the verdict instead"),
        "defect_budget": max(refined_r4 - (B + 1), 0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--out-ledger", default=str(ROOT / "outputs" / "rr_short_survivor_ledger.json"))
    ap.add_argument("--out-defects", default=str(ROOT / "outputs" / "rr_segment_defect_budgets.json"))
    a = ap.parse_args()

    surv = json.loads(Path(a.survivors).read_text(encoding="utf-8"))
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    rows = []
    for r in surv["rows"]:
        if r["verdict"] != "CAPACITY_SURVIVOR":
            continue
        ell = r["root_ell"]
        rec = next((p for p in preps["results_by_ell"][str(ell)]["preparations"]
                    if p["raw_state_hash"][:12] == r.get("raw_state_hash")), None)
        if rec is None:
            continue
        st = replay_historical(ell, rec)
        if st is None:
            continue
        an = analyse(st)
        an.update({"root_ell": ell, "P_core": r["P_core"],
                   "raw_state_hash": r["raw_state_hash"],
                   "canonical_state_hash": r["canonical_state_hash"],
                   "legal_outgoing_signature": r["legal_outgoing_signature"]})
        rows.append(an)

    rows.sort(key=lambda x: (x["root_ell"], x["P_core"], x["raw_state_hash"]))

    print("=== the 9 CAPACITY_SURVIVORs, three bounds side by side ===")
    print(" ell P_core  B+1   A   mA    B    mB   B+Rpen  mB_R  contra_B  contra_B_R")
    for x in rows:
        print(f"  {x['root_ell']:>2} {x['P_core']:>5}  {x['B_plus_1']:>4} {x['bound_A_coarse']:>4} "
              f"{x['margin_A']:>4} {x['bound_B_initial_refined']:>4} {x['margin_B']:>5} "
              f"{x['bound_B_with_R_penalty']:>6} {x['margin_B_R']:>5}   "
              f"{str(x['contradiction_B']):<8} {x['contradiction_B_R']}")

    n_b = sum(1 for x in rows if x["contradiction_B"])
    n_br = sum(1 for x in rows if x["contradiction_B_R"])
    print(f"\n removed by bound B (initial-phase refinement) : {n_b} / {len(rows)}")
    print(f" removed by bound B + R-reentry penalty        : {n_br} / {len(rows)}")
    print(f" NEWLY removed by the R-reentry penalty        : {n_br - n_b}")

    print(f"\n=== section 7/13: required full segments vs hexagon-disjoint supply ===")
    print(" ell P_core  f_min  full-cap orbits  greedy(LOWER)  safe ceiling  blocks?")
    for x in rows:
        print(f"  {x['root_ell']:>2} {x['P_core']:>5}  {x['required_full_segments_f_min']:>5}  "
              f"{x['n_orbits_with_full_5_ports']:>14}  "
              f"{x['greedy_hexagon_disjoint_full_orbits']:>12}  "
              f"{x['safe_ceiling_on_disjoint_full_orbits']:>11}  "
              f"{x['hexagon_disjointness_blocks_f_min']}")
    print("   (greedy is a LOWER bound and cannot certify an obstruction; the verdict")
    print("    uses the safe ceiling floor(#unvisited hexagons / 5))")

    print(f"\n=== defect budgets (bound B + R penalty) ===")
    for x in rows:
        print(f"  ell={x['root_ell']} P_core={x['P_core']}: defect budget "
              f"{x['defect_budget']}  (segments {x['m_plus_1_max_segments']}, "
              f"f_min {x['required_full_segments_f_min']})")

    Path(a.out_ledger).write_text(json.dumps({
        "schema": "rr-short-survivor-ledger-v1",
        "n_rows": len(rows), "rows": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out_defects).write_text(json.dumps({
        "schema": "rr-segment-defect-budgets-v1",
        "bounds": {
            "A_coarse": {"formula": "B+1 <= 5(m+1)", "assumptions": ["Phi=0", "generator algebra"],
                         "grade": "손증명"},
            "B_initial_refined": {"formula": "B+1 <= c(q0) + sum of O_cap largest c(q) + 5*R_cap",
                                  "assumptions": ["A", "a port is usable only if its hexagon is free"],
                                  "grade": "safe segment bound"},
            "B_with_R_penalty": {
                "formula": "B+1 <= c(q0) + sum of O_cap largest c(q) + 4*R_cap",
                "assumptions": ["B", "orbit-reuse penalty"],
                "orbit_reuse_penalty": ("a segment entered by an orbit-changing R lies in an "
                                        "ALREADY OPEN orbit (that is what makes the edge an R "
                                        "rather than a fresh opening), so it has at least one "
                                        "visited port and capacity at most 4"),
                "grade": "손증명"},
            "C_segment_defect": {"formula": "B+1 <= 5(m+1) - sum_i d_i, d_i = 5 - cap(S_i)",
                                 "assumptions": ["A", "per-segment capacity accounting"],
                                 "grade": "손증명 (definitional restatement of A)"},
        },
        "removed_by_B": n_b, "removed_by_B_with_R_penalty": n_br,
        "newly_removed_by_R_penalty": n_br - n_b,
        "rows": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_ledger)
    print("wrote", a.out_defects)


if __name__ == "__main__":
    main()
