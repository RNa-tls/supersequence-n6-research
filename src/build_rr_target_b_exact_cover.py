#!/usr/bin/env python3
"""Round 33, sections 1-3, 8-13: the segment-option exact-cover model.

MODEL.  A Target B continuation from a Phi=0 Target A boundary is a
sequence of orbit segments.  Each segment is a choice of

    (orbit q, entry phase ph, preserving word w, exit type e)

and it COVERS a set of hexagons -- one per port it visits -- because an
ell=5 macro-edge completes exactly the hexagon it stands in.  Since every
remaining hexagon must be completed exactly once, the segments must
PARTITION the residual hexagons.  That is an exact-cover problem over
hexagons, with side budgets on O and R slots.

Deliverable-name mapping (the round's brief gave two lists): the files
written here are the section-23 names; `rr_segment_options.json` is the
same corpus the revised list calls `rr_segment_options_r33.json`.

Layer vocabulary used throughout (sections 5 / 17):

    R0 capacity count only          -- decided in Round 32, reused
    R1 hexagon exact cover
    R2 port uniqueness
    R3 segment flow / order (no subtours)
    R4 literal collision (engine replay)
    R5 component compatibility      -- NECESSARY-CONDITION ONLY, never
                                       called exact, because Target B's
                                       final component requirement is
                                       still uncharacterised

No permutation-level DFS.  No solver library is available in this
environment, so every layer is decided by hand-rolled exact reasoning or
reported as bounded incomplete -- never by an unverified solver call.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
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


macro = _load("brtbec", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
S5 = core.power(core.SIGMA, 5)
GEN = {j: core.compose(S5, mbl[j].action) for j in ["w2:10", "w3:120", "w3:201", "w3:210"]}
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(len(core.E_REPS))]
ORBIT_HEX = [tuple(core.hexagon_id(p) for p in PORTS[q]) for q in range(len(PORTS))]


def preserving_words():
    """Legal preserving runs, length 0..4, with their phase offsets."""
    out = []
    for n in range(0, 5):
        for combo in product((1, 2), repeat=n):
            s, seen, ok = 0, [0], True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    ok = False
                    break
                seen.append(s)
            if ok:
                out.append({"word": "".join("E" if d == 1 else "E2" for d in combo),
                            "steps": list(combo), "offsets": seen,
                            "n_E2": sum(1 for d in combo if d == 2),
                            "capacity": len(seen), "defect": 5 - len(seen)})
    return out


def replay_state(ell, prep):
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


def engine_check_initial_edges(st):
    """Section 3's requirement: validate the option-generation rule against
    the real engine rather than against our own bookkeeping."""
    rows = []
    for e in macro.macro_edges(st):
        tr = e.joint
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        if reason is not None:
            continue
        tq, tph = exact.ORBIT_PHASE[tr.target]
        rows.append({"label": f"rot^{e.run.ell};{tr.move.label}", "ell": e.run.ell,
                     "joint": tr.move.label, "target_orbit": tq, "target_phase": tph,
                     "target_hexagon": core.hexagon_id(tr.target),
                     "new_orbit": bool(tr.new_orbit)})
    # the generator prediction: p -> p . g_j
    pred = []
    for j, g in GEN.items():
        t = core.compose(st.p, g)
        tq, tph = exact.ORBIT_PHASE[t]
        pred.append({"joint": j, "target_orbit": tq, "target_phase": tph,
                     "target_hexagon": core.hexagon_id(t)})
    by_joint = {r["joint"]: r for r in rows}
    agree = all(
        by_joint[p["joint"]]["target_orbit"] == p["target_orbit"]
        and by_joint[p["joint"]]["target_phase"] == p["target_phase"]
        for p in pred if p["joint"] in by_joint)
    return {"legal_edges": rows, "generator_prediction": pred,
            "generator_matches_engine": agree,
            "n_legal": len(rows)}


def build_options(st, pw):
    """Sections 2, 9-13: the option corpus for one survivor."""
    uh = {h for h in range(len(core.ROT_REPS)) if st.hex_masks[h] == 0}
    partial_hex = core.hexagon_id(st.p)
    unopened = {q for q in range(len(core.E_REPS)) if st.orbit_masks[q] == 0}
    opened = {q for q in range(len(core.E_REPS)) if st.orbit_masks[q] != 0}
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    opts = []

    def add(kind, q, ph, w, hexes, ports, cap, o_cost, r_cost):
        opts.append({"id": len(opts), "kind": kind, "orbit": q, "entry_phase": ph,
                     "preserving_word": w["word"], "capacity": cap,
                     "defect": 5 - cap, "covered_hexagons": sorted(hexes),
                     "covered_ports": sorted(ports),
                     "O_cost": o_cost, "R_cost": r_cost + w["n_E2"],
                     "exit_phase": (ph + sum(w["steps"])) % 5})

    # --- initial segment: starts at the current port, inside q0 ---
    for w in pw:
        hexes, ports, ok = [], [], True
        for off in w["offsets"]:
            ph = (ph0 + off) % 5
            p = PORTS[q0][ph]
            h = core.hexagon_id(p)
            if off == 0:
                if h != partial_hex:
                    ok = False
                    break
            elif h not in uh:
                ok = False
                break
            hexes.append(h)
            ports.append(ph)
        if ok:
            add("initial", q0, ph0, w, hexes, ports, len(hexes), 0, 0)

    # --- fresh-opening segments: orbit must be unopened ---
    for q in sorted(unopened):
        for ph in range(5):
            for w in pw:
                hexes, ports, ok = [], [], True
                for off in w["offsets"]:
                    p2 = (ph + off) % 5
                    h = core.hexagon_id(PORTS[q][p2])
                    if h not in uh:
                        ok = False
                        break
                    hexes.append(h)
                    ports.append(p2)
                if ok and hexes:
                    add("fresh", q, ph, w, hexes, ports, len(hexes), 1, 0)

    # --- R-entry segments: orbit already open, capacity strictly below 5 ---
    for q in sorted(opened):
        if q == q0:
            continue
        for ph in range(5):
            if st.orbit_masks[q] & (1 << ph):
                continue                      # entry port already visited
            for w in pw:
                hexes, ports, ok = [], [], True
                for off in w["offsets"]:
                    p2 = (ph + off) % 5
                    if st.orbit_masks[q] & (1 << p2):
                        ok = False
                        break
                    h = core.hexagon_id(PORTS[q][p2])
                    if h not in uh:
                        ok = False
                        break
                    hexes.append(h)
                    ports.append(p2)
                if ok and hexes:
                    add("R_entry", q, ph, w, hexes, ports, len(hexes), 0, 1)

    return opts, {"residual_hexagons": sorted(uh | {partial_hex}),
                  "n_residual_hexagons": len(uh) + 1,
                  "partial_hexagon": partial_hex,
                  "n_unopened_orbits": len(unopened),
                  "current_orbit": q0, "current_phase": ph0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdicts", default=str(ROOT / "outputs" / "rr_segment_verdicts.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--out-options", default=str(ROOT / "outputs" / "rr_segment_options.json"))
    ap.add_argument("--out-models", default=str(ROOT / "outputs" / "rr_target_b_ilp_models.json"))
    a = ap.parse_args()

    pw = preserving_words()
    print(f"preserving words (length 0..4): {len(pw)}; capacities "
          f"{sorted({w['capacity'] for w in pw})}")

    verd = json.loads(Path(a.verdicts).read_text(encoding="utf-8"))
    surv_rows = json.loads(Path(a.survivors).read_text(encoding="utf-8"))["rows"]
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    keep = [c for c in verd["certificates"] if c["verdict"] == "SEGMENT_SURVIVOR"]
    print(f"loading the {len(keep)} SEGMENT_SURVIVORs from Round 32 (not re-derived)")

    models, all_opts = [], {}
    for c in keep:
        ell, pc = c["root_ell"], c["P_core"]
        row = next(r for r in surv_rows
                   if r["root_ell"] == ell and r["P_core"] == pc
                   and r["canonical_state_hash"] == c["canonical_state_hash"])
        rec = next(p for p in preps["results_by_ell"][str(ell)]["preparations"]
                   if p["raw_state_hash"][:12] == row["raw_state_hash"])
        st = replay_state(ell, rec)
        assert st is not None
        chk = engine_check_initial_edges(st)
        opts, meta = build_options(st, pw)
        B = exact.TARGET_P - st.P
        O_cap = exact.TARGET_O - st.O
        R_cap = max(macro.AREA_A.n_limit - st.Ndef, 0)
        kinds = Counter(o["kind"] for o in opts)
        caps = Counter(o["capacity"] for o in opts)
        # hexagon coverability: every residual hexagon must appear in some option
        cover_count = Counter()
        for o in opts:
            for h in o["covered_hexagons"]:
                cover_count[h] += 1
        uncovered = [h for h in meta["residual_hexagons"] if cover_count[h] == 0]
        key = f"ell{ell}_P{pc}_{c['canonical_state_hash'][:8]}"
        all_opts[key] = opts
        models.append({
            "key": key, "root_ell": ell, "P_core": pc,
            "canonical_state_hash": c["canonical_state_hash"],
            "B": B, "B_plus_1": B + 1, "O_cap": O_cap, "R_cap": R_cap,
            "max_segments": O_cap + R_cap + 1,
            "defect_budget": c["defect_budget"],
            **meta,
            "n_options": len(opts),
            "options_by_kind": dict(kinds),
            "options_by_capacity": {str(k): v for k, v in sorted(caps.items())},
            "hexagons_with_no_option": uncovered,
            "n_hexagons_with_no_option": len(uncovered),
            "engine_validation": chk,
            "constraints": {
                "hexagon_coverage": "sum_{x: h in C(x)} x = 1 for every residual hexagon",
                "port_uniqueness": "sum_{x: p in P(x)} x <= 1",
                "segment_count": "sum_x x <= O_cap + R_cap + 1",
                "total_capacity": "sum_x cap(x) x = B+1",
                "R_budget": "sum_x R(x) x <= R_cap",
                "fresh_opening_budget": "sum_x O(x) x <= O_cap",
                "initial_segment": "exactly one option of kind 'initial'",
                "defect": "sum_x d(x) x <= defect budget",
            },
        })
        print(f"  {key}: B+1={B+1} O_cap={O_cap} R_cap={R_cap} "
              f"residual hexagons={meta['n_residual_hexagons']} "
              f"options={len(opts)} {dict(kinds)} uncovered_hex={len(uncovered)} "
              f"engine_match={chk['generator_matches_engine']}")

    payload = {"schema": "rr-segment-options-v1",
               "preserving_words": pw,
               "note": ("an option's covered hexagons are the hexagons of the ports its "
                        "phase walk visits; an ell=5 macro-edge completes exactly the "
                        "hexagon it stands in, so the chosen segments must PARTITION the "
                        "residual hexagons"),
               "options_by_survivor": all_opts}
    Path(a.out_options).write_text(json.dumps(payload, indent=2, sort_keys=True,
                                              ensure_ascii=False, default=str),
                                   encoding="utf-8")
    Path(a.out_models).write_text(json.dumps({
        "schema": "rr-target-b-ilp-models-v1",
        "layers": {"R0": "capacity count (Round 32)", "R1": "hexagon exact cover",
                   "R2": "port uniqueness", "R3": "segment flow / order",
                   "R4": "literal collision (engine replay)",
                   "R5": "component compatibility -- NECESSARY-CONDITION ONLY"},
        "no_solver_available": ("this environment has no pulp/ortools/pysat/scipy, so every "
                               "layer is decided by hand-rolled exact reasoning or marked "
                               "bounded incomplete; no unverified solver result is used"),
        "models": models,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_options)
    print("wrote", a.out_models)


if __name__ == "__main__":
    main()
