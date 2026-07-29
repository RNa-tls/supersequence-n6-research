#!/usr/bin/env python3
"""Round 28, sections 1-5: the six counterexamples, their certificates,
their minimality, and their quotient.

SECTION 1 -- LENGTH SYMBOLS, SEPARATED ONCE AND FOR ALL.  The word is

    A_ell . P_core . C . T_ell . R2

  P_core        macro-edges after the abandonment and STRICTLY BEFORE the
                hub completer.  Equals `edges_before_completer` in
                outputs/rr_preparation_words.json.
  C             the hub completer edge (exactly 1).
  T_ell         edges after C and before R2 (Lemma P1: 0 at ell=4, 1
                otherwise).
  P_reported    `preparation_length` in the JSON = P_core + 1 + |T_ell|.
  L, G          first-return length / gap of an O* excursion, G = L-1.

These are FIVE different numbers and past documents have used the bare
symbol |P| for at least two of them.  The audit below settles which one
Conjecture A was stated in: over the 12 historical records,

    P_core     + #R_{<=C}  ==  1 (mod 2)  in 12/12  -- UNIFORM
    P_reported + #R_{<=C}  ==  1 at ell=0, 0 at ell=4  -- NOT uniform

so Conjecture A is a statement about P_core.  Round 27's write-up used
P_reported; it identified the same two witnesses as violating, but quoted
the historical baseline under the non-uniform convention.  This file is
the correction, and every table below reports BOTH.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
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


macro = _load("vrcc", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)
HEX0 = [0, 120, 33, 9, 3, 1]


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def sym(k):
    return "R" if k == "R" else ("F" if k == "Z3" else "E")


def state_hash(state):
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


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


def canonical_pair(state, o_star, r1t):
    best_key, alphas = None, []
    for a in range(len(core.ALL_WORDS)):
        key = exact.relabel_sparse_key(state, a)
        if best_key is None or key < best_key:
            best_key, alphas = key, [a]
        elif key == best_key:
            alphas.append(a)
    variants = [(exact.LEFT_ORBIT_ACTION[a][o_star][0],
                 None if r1t is None else exact.LEFT_ORBIT_ACTION[a][r1t][0])
                for a in alphas]
    return (repr(best_key), min(variants)), len(alphas)


def historical_audit():
    p = ROOT / "outputs" / "rr_preparation_words.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    rep, cor, rows = Counter(), Counter(), []
    for ell, r in d["results_by_ell"].items():
        for w in r["preparations"]:
            ks = w["kind_signature"]
            Prep, ci = w["preparation_length"], w["edges_before_completer"]
            nR = sum(1 for k in ks[:ci + 1] if k == "R")
            rep[(Prep + nR) % 2] += 1
            cor[(ci + nR) % 2] += 1
            rows.append({"ell": int(ell), "P_reported": Prep, "P_core": ci,
                         "tail": Prep - ci - 1, "nR_le_C": nR,
                         "P_reported_plus_R_mod2": (Prep + nR) % 2,
                         "P_core_plus_R_mod2": (ci + nR) % 2})
    return {"records": len(rows),
            "P_reported_histogram": {str(k): v for k, v in sorted(rep.items())},
            "P_core_histogram": {str(k): v for k, v in sorted(cor.items())},
            "conjecture_A_convention": ("P_core -- the only convention under which the "
                                        "historical corpus is uniform (12/12 give 1)"),
            "rows": rows}


def build_witness(res):
    """Replay the full word and extract every field section 2 asks for."""
    ell = res["root_ell"]
    o = HEX0[ell + 1]
    st = exact.initial_state()
    for _ in range(ell):
        st = exact.extend(st, W1).state
    tr = exact.extend(st, W2_10)
    st = tr.state
    abandon_phase = exact.ORBIT_PHASE[tr.target][1]
    w = res["same_component_witnesses"][0]
    seq = [(5, l) for l in res["literal_joint_word"]]
    for s in w["extension_trace"]:
        a, b = s["label"].split(";")
        seq.append((int(a.split("^")[1]), b))
    rows, C_index, r_idx = [], None, []
    o_star_visits, phase_seq = [], [abandon_phase]
    for i, (el, lbl) in enumerate(seq):
        for _ in range(el):
            st = exact.extend(st, W1).state
        pre = st
        t = exact.extend(st, mbl[lbl])
        k = joint_kind(t.move.weight, t.abandonment, t.new_orbit)
        s = sym(k)
        tq, tph = exact.ORBIT_PHASE[t.target]
        hx = core.hexagon_id(t.target)
        if hx == HUB and C_index is None:
            C_index = i
        if s == "R":
            r_idx.append(i)
        if tq == o:
            o_star_visits.append(i)
            phase_seq.append(tph)
        rows.append({"index": i, "label": f"rot^{el};{lbl}", "sym": s, "kind": k,
                     "target_orbit": tq, "target_phase": tph, "target_hexagon": hx,
                     "is_hub": hx == HUB, "targets_O_star": tq == o})
        st = t.state
    total = len(rows)
    R2_index = r_idx[-1]
    P_core = C_index
    tail = R2_index - C_index - 1
    P_reported = R2_index
    nR_le_C = sum(1 for x in rows[:C_index + 1] if x["sym"] == "R")
    Z_ostar = [x for x in rows[:C_index + 1] if x["sym"] != "R" and x["targets_O_star"]]
    Z_all = [x for x in rows[:C_index + 1] if x["sym"] != "R"]
    Z_other = [x for x in Z_all if not x["targets_O_star"]]
    Lx = res["L"]
    exc = rows[:Lx]
    parent, find = component_roots(st)
    deltas = [(phase_seq[i + 1] - phase_seq[i]) % 5 for i in range(len(phase_seq) - 1)]
    k_wind = (sum(deltas) - ((phase_seq[-1] - phase_seq[0]) % 5)) // 5
    step_syms = [rows[j]["sym"] for j in o_star_visits]
    n_R_odd = sum(1 for s2, dl in zip(step_syms, deltas) if s2 == "R" and dl % 2 == 1)
    n_E_steps = sum(1 for s2 in step_syms if s2 != "R")
    return {
        "root_ell": ell, "o_star": o,
        "literal_full_word": [f"rot^{e};{l}" for e, l in seq],
        "long_excursion_subword": res["literal_joint_word"],
        "excursion_symbolic": res["symbolic_word"],
        "L": Lx, "G": Lx - 1, "return_exponent_k_step": res["return_exponent"],
        "P_core": P_core, "C_index": C_index, "tail_length": tail,
        "P_reported": P_reported, "R2_index": R2_index,
        "total_macro_edges_after_abandonment": total,
        "total_macro_depth": total + 1,
        "R_indices": r_idx, "R1_index": r_idx[0],
        "nR_le_C": nR_le_C,
        "n_F_sym": sum(1 for x in rows if x["sym"] == "F"),
        "n_Z_total_in_PC": len(Z_all),
        "n_Z_to_O_star": len(Z_ostar),
        "n_Z_to_other": len(Z_other),
        "n_Z_to_O_star_inside_excursion": sum(
            1 for x in exc if x["sym"] != "R" and x["targets_O_star"]),
        "n_Z_to_O_star_outside_excursion": sum(
            1 for x in rows[Lx:C_index + 1] if x["sym"] != "R" and x["targets_O_star"]),
        "F_def": st.F, "H": st.H, "N_def": st.Ndef, "O": st.O, "P": st.P,
        "visited_count": st.visited_count,
        "phi": 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count),
        "O_star_visit_indices": o_star_visits,
        "O_star_phase_sequence": phase_seq,
        "O_star_phase_deltas": deltas,
        "winding_number_k": k_wind,
        "O_star_step_symbols": step_syms,
        "n_R_steps_with_odd_delta": n_R_odd,
        "n_E_steps_to_O_star": n_E_steps,
        "corrected_identity_holds": (n_E_steps % 2) == ((k_wind + n_R_odd) % 2),
        "r1_target_orbit": w["r1_target_orbit"],
        "r2_source_orbit": w["r2_source_orbit"], "r2_source_phase": w["r2_source_phase"],
        "r2_target_orbit": w["r2_target_orbit"], "r2_target_phase": w["r2_target_phase"],
        "chaining": w["chaining"],
        "component_root_of_O_star": str(find(("q", o)) if ("q", o) in parent else None),
        "n_components": len({find(x) for x in list(parent)}),
        "post_r2_state_hash": state_hash(st),
        "post_r2_stable_key": repr(st.stable_key()),
        "extension_length": w["extension_length"],
        "conjecture_A_P_core": (P_core + nR_le_C) % 2,
        "conjecture_A_P_reported": (P_reported + nR_le_C) % 2,
        "conjecture_B_Z_O_star_parity": len(Z_ostar) % 2,
        "conjecture_C_k": k_wind,
        "trace": rows,
        "_final_state": st,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--certificates", default=str(ROOT / "outputs" / "rr_counterexample_certificates.json"))
    a = ap.parse_args()

    aud = historical_audit()
    print("=== section 1: length convention audit ===")
    print(f"historical records: {aud['records']}")
    print(f"  P_reported + #R<=C mod 2 : {aud['P_reported_histogram']}   NOT uniform")
    print(f"  P_core     + #R<=C mod 2 : {aud['P_core_histogram']}   UNIFORM")
    print(f"  => Conjecture A is about P_core.")

    data = json.loads(Path(a.results).read_text(encoding="utf-8"))
    found = [r for r in data["results"] if r["status"] == "FOUND"]
    wits = [build_witness(r) for r in found]
    # deterministic order
    wits.sort(key=lambda w: (w["L"], w["P_core"], w["literal_full_word"]))

    print(f"\n=== section 2/4: the six witnesses (deterministic order) ===")
    print(" # ell  L  P_core  C  tail  P_rep  #R<=C | A(P_core) A(P_rep) | #Z->O*  k")
    for i, w in enumerate(wits):
        print(f" {i}  {w['root_ell']}   {w['L']}   {w['P_core']:>2}   {w['C_index']:>2}   "
              f"{w['tail_length']}    {w['P_reported']:>2}     {w['nR_le_C']}   |    "
              f"{w['conjecture_A_P_core']}        {w['conjecture_A_P_reported']}    |    "
              f"{w['n_Z_to_O_star']}    {w['winding_number_k']}")

    # ---- section 4: certificates ----
    cert = {
        "A": {"statement": "|P_core| + #R_{<=C} == 1 (mod 2)",
              "convention": "P_core = macro-edges strictly before the hub completer",
              "historical_baseline": "1 in 12/12 records (both ell branches)",
              "violating_witnesses": [i for i, w in enumerate(wits)
                                      if w["conjecture_A_P_core"] != 1],
              "satisfying_witnesses": [i for i, w in enumerate(wits)
                                       if w["conjecture_A_P_core"] == 1],
              "verdict": None},
        "B": {"statement": "#Z_{->O*} == 0 (mod 2)",
              "historical_baseline": "even in all 95 O*-landing completions (depth<=6 scope)",
              "violating_witnesses": [i for i, w in enumerate(wits)
                                      if w["conjecture_B_Z_O_star_parity"] != 0],
              "satisfying_witnesses": [i for i, w in enumerate(wits)
                                       if w["conjecture_B_Z_O_star_parity"] == 0],
              "verdict": None},
        "REDUCTION": {
            "statement": "#Z_{->O*} == k (mod 2)",
            "status_claimed_in_round_27": "still valid",
            "historical_baseline": "holds in all 95 completions (depth<=6 scope)",
            "violating_witnesses": [i for i, w in enumerate(wits)
                                    if (w["n_Z_to_O_star"] % 2) != (w["winding_number_k"] % 2)],
            "satisfying_witnesses": [i for i, w in enumerate(wits)
                                     if (w["n_Z_to_O_star"] % 2) == (w["winding_number_k"] % 2)],
            "verdict": None,
            "why": ("the reduction was never unconditional -- it needed every R step into O* "
                    "to have EVEN phase displacement, which is exactly the alphabet premise "
                    "refuted in Round 26. Round 27 recorded the reduction as surviving and "
                    "inferred k >= 1 from it; that inference is WRONG and is corrected here."),
            "corrected_identity": ("#Z_{->O*} == k + #R_{odd delta}  (mod 2), where "
                                   "#R_{odd delta} counts R steps into O* whose phase "
                                   "displacement is odd. Unconditional 손증명: F never targets "
                                   "O* so #Z = #E; every E step has delta 1; sum of deltas = "
                                   "4 + 5k; reduce mod 2."),
            "corrected_identity_holds_on_all_witnesses": None,
        },
        "C": {"statement": "winding number k == 0",
              "historical_baseline": "k = 0 in all 95 completions (depth<=6 scope)",
              "violating_witnesses": [i for i, w in enumerate(wits)
                                      if w["conjecture_C_k"] != 0],
              "satisfying_witnesses": [i for i, w in enumerate(wits)
                                       if w["conjecture_C_k"] == 0],
              "verdict": None},
    }
    for key, c in cert.items():
        c["verdict"] = ("반증됨" if c["violating_witnesses"] else "not refuted by these witnesses")
        c["n_violating"] = len(c["violating_witnesses"])
    cert["REDUCTION"]["corrected_identity_holds_on_all_witnesses"] = all(
        w["corrected_identity_holds"] for w in wits)
    print(f"\n=== section 4: refutation certificates ===")
    for key, c in cert.items():
        print(f"  Conjecture {key}: {c['statement']}")
        print(f"     baseline {c['historical_baseline']}")
        print(f"     violated by witnesses {c['violating_witnesses']}  -> {c['verdict']}")

    # ---- section 3: minimality ----
    crit = {
        "shortest_long_excursion_L": min(w["L"] for w in wits),
        "shortest_total_extension": min(w["extension_length"] for w in wits),
        "fewest_R_before_C": min(w["nR_le_C"] for w in wits),
        "fewest_F_sym": min(w["n_F_sym"] for w in wits),
        "smallest_k": min(w["winding_number_k"] for w in wits),
        "smallest_total_macro_depth": min(w["total_macro_depth"] for w in wits),
    }
    mins = {}
    for name, val in crit.items():
        field = {"shortest_long_excursion_L": "L",
                 "shortest_total_extension": "extension_length",
                 "fewest_R_before_C": "nR_le_C", "fewest_F_sym": "n_F_sym",
                 "smallest_k": "winding_number_k",
                 "smallest_total_macro_depth": "total_macro_depth"}[name]
        mins[name] = {"value": val,
                      "witnesses": [i for i, w in enumerate(wits) if w[field] == val]}
    lex = min(range(len(wits)), key=lambda i: wits[i]["literal_full_word"])
    mins["lexicographically_minimal_literal_word"] = {"value": None, "witnesses": [lex]}
    simultaneous = set(range(len(wits)))
    for m in mins.values():
        simultaneous &= set(m["witnesses"])
    print(f"\n  corrected identity  #Z == k + #R_odd  holds on all six: "
          f"{all(w['corrected_identity_holds'] for w in wits)}")
    for i, w in enumerate(wits):
        print(f"     w{i}: #Z={w['n_Z_to_O_star']} k={w['winding_number_k']} "
              f"#R_odd={w['n_R_steps_with_odd_delta']} deltas={w['O_star_phase_deltas']} "
              f"syms={w['O_star_step_symbols']}")

    print(f"\n=== section 3: minimality ===")
    for name, m in mins.items():
        print(f"  {name:<38} value={m['value']}  witnesses={m['witnesses']}")
    print(f"  witnesses minimal in EVERY criterion simultaneously: {sorted(simultaneous)}")

    # ---- section 5: quotient ----
    q_exact = defaultdict(list)
    q_canon = defaultdict(list)
    q_sym = defaultdict(list)
    q_phase = defaultdict(list)
    q_res = defaultdict(list)
    q_bnd = defaultdict(list)
    ties = Counter()
    for i, w in enumerate(wits):
        q_exact[w["post_r2_stable_key"]].append(i)
        key, nt = canonical_pair(w["_final_state"], w["o_star"], w["r1_target_orbit"])
        ties[nt] += 1
        q_canon[repr(key)].append(i)
        q_sym[w["excursion_symbolic"]].append(i)
        q_phase[repr(w["O_star_phase_sequence"])].append(i)
        q_res[repr((w["P_core"], w["nR_le_C"], w["n_F_sym"], w["O"], w["P"],
                    w["visited_count"], w["phi"]))].append(i)
        q_bnd[repr((w["r1_target_orbit"], w["r2_source_orbit"], w["r2_source_phase"],
                    w["r2_target_orbit"], w["r2_target_phase"], w["chaining"],
                    w["phi"]))].append(i)
    print(f"\n=== section 5: quotient of the six ===")
    print(f"  exact post-R2 state       : {len(q_exact)} classes")
    print(f"  left-S6 canonical pair    : {len(q_canon)} classes  (stabilizer ties {dict(ties)})")
    print(f"  decorated R2 boundary     : {len(q_bnd)} classes -> {list(q_bnd.values())}")
    print(f"  symbolic excursion        : {len(q_sym)} classes -> {dict(q_sym)}")
    print(f"  O* phase word             : {len(q_phase)} classes -> {list(q_phase.values())}")
    print(f"  resource ledger           : {len(q_res)} classes -> {list(q_res.values())}")

    for w in wits:
        w.pop("_final_state", None)
    Path(a.output).write_text(json.dumps({
        "schema": "rr-six-counterexamples-v1",
        "length_convention_audit": aud,
        "deterministic_order": "sorted by (L, P_core, literal_full_word)",
        "witnesses": wits,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)

    Path(a.certificates).write_text(json.dumps({
        "schema": "rr-counterexample-certificates-v1",
        "conjectures": cert,
        "minimality": mins,
        "simultaneously_minimal_witnesses": sorted(simultaneous),
        "quotient": {
            "exact_post_r2_state_classes": len(q_exact),
            "left_s6_canonical_classes": len(q_canon),
            "decorated_boundary_classes": {k: v for k, v in q_bnd.items()},
            "symbolic_excursion_classes": {k: v for k, v in q_sym.items()},
            "phase_word_classes": {k: v for k, v in q_phase.items()},
            "resource_ledger_classes": {k: v for k, v in q_res.items()},
            "stabilizer_tie_histogram": {str(k): v for k, v in ties.items()},
        },
        "grade": "exact counterexample + exact replay + exact quotient",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.certificates)


if __name__ == "__main__":
    main()
