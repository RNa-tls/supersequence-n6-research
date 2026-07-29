#!/usr/bin/env python3
"""Round 31, Parts B and C: phase/port-aware capacity, and the
capacity-saturating block classification.

The Round 30 bound treats every orbit segment as worth 5 ports.  The
refinement asks how many ports of each orbit are ACTUALLY usable: a port
is usable only if its hexagon is still unvisited, since each hexagon is
consumed by exactly one macro-edge.

    c(q) = #{ ports of orbit q whose hexagon is unvisited at the boundary }

Refined bound (safe -- it can only lower the ceiling):

    B + 1  <=  c(q_0)  +  sum of the O_cap largest c(q) over UNOPENED
               orbits  +  5 * R_cap

using c(q_0) for the segment the walk is already in.  Choosing the
largest c(q) is what makes it an upper bound: the continuation may use
any O_cap unopened orbits, so we grant it the best ones.

Part C (sections 12-15) enumerates the capacity-saturating blocks: a
maximal preserving run of length 4 is an E/E^2 word whose partial sums are
distinct mod 5, i.e. it uses all five phases of its orbit.  Those blocks
are what an equality case would have to be built from.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, defaultdict
from itertools import product
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


macro = _load("brrcb", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]


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


def port_capacities(st):
    """c(q) for every orbit, plus which orbits are still unopened."""
    unvisited_hex = [h for h in range(len(core.ROT_REPS)) if st.hex_masks[h] == 0]
    uh = set(unvisited_hex)
    c = {}
    unopened = []
    for q in range(len(core.E_REPS)):
        ports = core.ports_of_e_orbit(core.E_REPS[q])
        c[q] = sum(1 for p in ports if core.hexagon_id(p) in uh)
        if st.orbit_masks[q] == 0:
            unopened.append(q)
    return c, unopened, len(unvisited_hex)


def refined_bound(st):
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(macro.AREA_A.n_limit - st.Ndef, 0)
    c, unopened, n_unvis_hex = port_capacities(st)
    q0, _ = exact.ORBIT_PHASE[st.p]
    # the segment already in progress: its remaining usable ports, plus the
    # port the walk currently stands on
    c0 = min(c[q0] + 1, 5)
    top = sorted((c[q] for q in unopened), reverse=True)[:O_cap]
    refined = c0 + sum(top) + 5 * R_cap
    uniform = 5 * (O_cap + R_cap) + 5      # = (5m+4)+1, in port units
    return {
        "B": B, "B_plus_1": B + 1, "O_cap": O_cap, "R_cap": R_cap,
        "current_orbit": q0, "c_current_orbit": c0,
        "n_unopened_orbits": len(unopened),
        "n_unvisited_hexagons": n_unvis_hex,
        "c_histogram_over_unopened": {str(k): v for k, v in
                                      sorted(Counter(c[q] for q in unopened).items())},
        "sum_top_O_cap_c": sum(top),
        "refined_port_bound": refined,
        "uniform_port_bound": uniform,
        "improvement": uniform - refined,
        "refined_contradiction": (B + 1) > refined,
        "refined_margin": refined - (B + 1),
    }


def saturating_blocks():
    """Section 13: maximal preserving runs of length 4 over {E, E^2}."""
    blocks = []
    for combo in product((1, 2), repeat=4):
        s, seen, ok = 0, [0], True
        for d in combo:
            s = (s + d) % 5
            if s in seen:
                ok = False
                break
            seen.append(s)
        if ok:
            blocks.append({"steps": list(combo),
                           "symbols": ["E" if d == 1 else "E2" for d in combo],
                           "phase_signature": seen,
                           "uses_all_five_phases": len(set(seen)) == 5,
                           "total_displacement_mod5": s})
    return blocks


def block_lengths():
    """How long can a preserving run be, by length?  (Section 13 support.)"""
    out = {}
    for n in range(1, 6):
        cnt = 0
        for combo in product((1, 2), repeat=n):
            s, seen, ok = 0, {0}, True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    ok = False
                    break
                seen.add(s)
            if ok:
                cnt += 1
        out[n] = cnt
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--out-cap", default=str(ROOT / "outputs" / "rr_refined_phase_capacities.json"))
    ap.add_argument("--out-blocks", default=str(ROOT / "outputs" / "rr_saturating_blocks.json"))
    a = ap.parse_args()

    print("=== Part C section 13: preserving-run blocks over {E, E^2} ===")
    bl = block_lengths()
    for n, c in bl.items():
        print(f"   runs of length {n}: {c} legal words")
    blocks = saturating_blocks()
    print(f"   capacity-SATURATING blocks (length 4): {len(blocks)}")
    for b in blocks:
        print(f"      {''.join(b['symbols']):<10} phases {b['phase_signature']} "
              f"all-five {b['uses_all_five_phases']}")

    surv = json.loads(Path(a.survivors).read_text(encoding="utf-8"))
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    rows = []
    print(f"\n=== Part B: refined port capacity at each CAPACITY_SURVIVOR ===")
    print("  ell P_core  B+1  c(q0)  sum_top  R_cap*5  refined  uniform  impr  contra")
    for r in surv["rows"]:
        if r["verdict"] != "CAPACITY_SURVIVOR":
            continue
        ell = r["root_ell"]
        rec = None
        for p in preps["results_by_ell"][str(ell)]["preparations"]:
            if p["raw_state_hash"][:12] == r.get("raw_state_hash"):
                rec = p
                break
        if rec is None:
            continue
        st = replay_historical(ell, rec)
        if st is None:
            continue
        rb = refined_bound(st)
        rb.update({"root_ell": ell, "P_core": r["P_core"],
                   "raw_state_hash": r["raw_state_hash"],
                   "uniform_margin": r["margin"]})
        rows.append(rb)
        print(f"  {ell:>2}  {r['P_core']:>4}  {rb['B_plus_1']:>4}  {rb['c_current_orbit']:>4}   "
              f"{rb['sum_top_O_cap_c']:>5}    {5*rb['R_cap']:>5}   {rb['refined_port_bound']:>5}"
              f"   {rb['uniform_port_bound']:>5}  {rb['improvement']:>4}   "
              f"{rb['refined_contradiction']}")

    n_new = sum(1 for r in rows if r["refined_contradiction"])
    print(f"\n  survivors newly removed by the refined bound: {n_new} / {len(rows)}")
    print(f"  improvement (uniform - refined) histogram: "
          f"{dict(sorted(Counter(r['improvement'] for r in rows).items()))}")

    Path(a.out_cap).write_text(json.dumps({
        "schema": "rr-refined-phase-capacities-v1",
        "definition": ("c(q) = number of ports of orbit q whose hexagon is still unvisited; "
                       "refined port bound = c(q0) + (sum of the O_cap largest c over "
                       "unopened orbits) + 5*R_cap"),
        "safety": ("granting the continuation the O_cap orbits with the LARGEST c makes "
                   "this an upper bound, hence a safe capacity bound"),
        "rows": rows,
        "survivors_removed_by_refinement": n_new,
        "verdict": ("REFINED_IMPOSSIBLE for some survivors" if n_new else
                    "no survivor is removed: every unopened orbit still has essentially "
                    "all five ports available, so the refinement does not bite"),
        "grade": "safe capacity bound",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out_blocks).write_text(json.dumps({
        "schema": "rr-saturating-blocks-v1",
        "definition": ("a capacity-saturating block is a maximal preserving run of length "
                       "4 over the orbit-preserving generators E (w2:10) and E^2 (w3:120); "
                       "its partial sums must be distinct mod 5"),
        "run_length_counts": {str(k): v for k, v in bl.items()},
        "saturating_blocks": blocks,
        "n_saturating_blocks": len(blocks),
        "note": ("every saturating block uses all five phases of its orbit, so it consumes "
                 "all five of that orbit's port hexagons. E^2 blocks additionally cost an R "
                 "slot, since w3:120 is always an R."),
        "grade": "exact symbolic reduction",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_cap)
    print("wrote", a.out_blocks)


if __name__ == "__main__":
    main()
