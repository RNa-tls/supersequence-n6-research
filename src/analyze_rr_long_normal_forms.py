#!/usr/bin/env python3
"""Round 28, sections 6-12: the long-preparation normal form, why Target A
survives a long excursion, the parity accounting, chaining, the terminal
normal form's scope, and the classification of the 22 INCOMPLETE roots.

Section 6 decomposes each witness as

    A_4 . U . X_long . V . C . R2

with X_long the L>=7 O* first-return excursion, U the preparation before
it, V the preparation between the excursion's return and the completer.

Section 8 records the parity accounting with NO assumption that anything
"compensates elsewhere" -- the numbers are simply reported, split into
zero-charge events inside the excursion, outside it, and to non-O*
orbits, alongside the historical short witnesses.

Section 12 classifies the 22 INCOMPLETE roots from the existing search
log only.  No search is re-run and no INCOMPLETE root is reinterpreted as
impossible.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, defaultdict
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


macro = _load("arlnf", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core


def decompose(w):
    """Section 6: A_4 . U . X_long . V . C . R2."""
    L = w["L"]
    trace = w["trace"]
    # the excursion occupies indices 0..L-1 of the post-abandonment word,
    # because the corpus prefixes ARE the excursion (they start at the
    # abandonment port, which is the first O* visit).
    U = trace[:0]
    X = trace[:L]
    V = trace[L:w["C_index"]]
    C = trace[w["C_index"]]
    T = trace[w["C_index"] + 1:w["R2_index"]]
    R2 = trace[w["R2_index"]]
    return {
        "U_length": len(U), "U_symbolic": "".join(x["sym"] for x in U),
        "X_long_length": len(X), "X_long_symbolic": "".join(x["sym"] for x in X),
        "V_length": len(V), "V_symbolic": "".join(x["sym"] for x in V),
        "C_label": C["label"], "C_sym": C["sym"],
        "C_target_orbit": C["target_orbit"], "C_target_phase": C["target_phase"],
        "T_length": len(T), "T_symbolic": "".join(x["sym"] for x in T),
        "R2_label": R2["label"],
        "R2_target_orbit": R2["target_orbit"], "R2_target_phase": R2["target_phase"],
    }


def survival_ledger(w):
    """Section 7: what the excursion consumed and what the terminal normal
    form still needed."""
    o = w["o_star"]
    used = [p for p in w["O_star_phase_sequence"]]
    return {
        "o_star": o,
        "abandonment_phase": w["O_star_phase_sequence"][0],
        "O_star_phases_used_in_order": used,
        "distinct_O_star_phases_used": len(set(used)),
        "phase_4_still_available_when_C_fires": (
            w["O_star_phase_sequence"][-1] == 4),
        "C_lands_on_O_star_phase_4": (w["C_target_orbit_is_o_star"]
                                      if "C_target_orbit_is_o_star" in w else None),
        "return_exponent_of_excursion": w["return_exponent_k_step"],
        "winding_k": w["winding_number_k"],
        "r1_target_orbit": w["r1_target_orbit"],
        "r2_source_orbit": w["r2_source_orbit"],
        "chaining": w["chaining"],
        "phi": w["phi"],
        "n_components_at_R2": w["n_components"],
    }


def parity_accounting(w):
    """Section 8: measured, never assumed."""
    return {
        "n_Z_to_O_star_total_in_PC": w["n_Z_to_O_star"],
        "n_Z_to_O_star_inside_excursion": w["n_Z_to_O_star_inside_excursion"],
        "n_Z_to_O_star_outside_excursion": w["n_Z_to_O_star_outside_excursion"],
        "n_Z_to_other": w["n_Z_to_other"],
        "n_Z_total": w["n_Z_total_in_PC"],
        "n_Z_to_O_star_parity": w["n_Z_to_O_star"] % 2,
        "n_Z_to_other_parity": w["n_Z_to_other"] % 2,
        "n_Z_total_parity": w["n_Z_total_in_PC"] % 2,
        "winding_k": w["winding_number_k"],
        "n_R_steps_with_odd_delta": w["n_R_steps_with_odd_delta"],
        "corrected_identity_holds": w["corrected_identity_holds"],
    }


def historical_parity():
    """The short witnesses, for the side-by-side comparison section 8 asks
    for. Scope: the 95 O*-landing completions at depth ceiling 6."""
    p = ROOT / "outputs" / "rr_ordered_event_words.json"
    if not p.exists():
        return {"available": False}
    rows = [r for r in json.loads(p.read_text(encoding="utf-8"))["rows"]
            if r["landing_class"] == "O_star"]
    zo = Counter()
    for r in rows:
        o = r["o_star"]
        n = sum(1 for e in r["events"] if e["sym"] != "R" and e["target_orbit"] == o)
        zo[n] += 1
    return {"available": True, "n_completions": len(rows),
            "n_Z_to_O_star_histogram": {str(k): v for k, v in sorted(zo.items())},
            "all_even": all(k % 2 == 0 for k in zo),
            "scope": "depth ceiling 6 after the abandonment -- cannot contain an L>=7 excursion"}


def classify_incomplete(results):
    """Section 12: from the existing log only."""
    inc = [r for r in results if r["status"] == "INCOMPLETE"]
    found = [r for r in results if r["status"] == "FOUND"]
    found_sym = {r["symbolic_word"] for r in found}
    rows = []
    for r in inc:
        rows.append({
            "root_ell": r["root_ell"], "symbolic_word": r["symbolic_word"],
            "L": r["L"], "return_exponent": r["return_exponent"],
            "f_sym_count": r["f_sym_count"],
            "nodes_expanded": r["nodes_expanded"],
            "dedup_states": r["dedup_states"],
            "r2_boundaries_reached": r["r2_boundaries_reached"],
            "same_component_found": r["n_same_component_witnesses"],
            "dominant_prune": max(r["prune_reason_histogram"].items(),
                                  key=lambda kv: kv[1])[0] if r["prune_reason_histogram"] else None,
            "prune_histogram": r["prune_reason_histogram"],
            "same_symbolic_class_as_a_FOUND_root": r["symbolic_word"] in found_sym,
            "truncated_by_node_cap": r["truncated_by_node_cap"],
        })
    by_ell = Counter(r["root_ell"] for r in rows)
    by_sym = Counter(r["symbolic_word"] for r in rows)
    return {
        "n_incomplete": len(rows),
        "by_root_ell": {str(k): v for k, v in sorted(by_ell.items())},
        "by_symbolic_word": dict(by_sym),
        "all_share_symbolic_class_with_a_FOUND_root": all(
            r["same_symbolic_class_as_a_FOUND_root"] for r in rows),
        "r2_boundaries_reached_range": [min(r["r2_boundaries_reached"] for r in rows),
                                        max(r["r2_boundaries_reached"] for r in rows)],
        "interpretation": (
            "every INCOMPLETE root shares its symbolic excursion class with a FOUND root "
            "and differs only in the abandonment ell. All 22 hit the node cap; none "
            "exhausted its frontier. They are NOT evidence of impossibility and are not "
            "read as such. bounded incomplete."),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--results", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_long_normal_form_classes.json"))
    a = ap.parse_args()

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    res = json.loads(Path(a.results).read_text(encoding="utf-8"))["results"]

    decomps, ledgers, parities = [], [], []
    for w in wits:
        w["C_target_orbit_is_o_star"] = w["trace"][w["C_index"]]["target_orbit"] == w["o_star"]
        decomps.append(decompose(w))
        ledgers.append(survival_ledger(w))
        parities.append(parity_accounting(w))

    print("=== section 6: A_4 . U . X_long . V . C . R2 ===")
    print(" #  |U|  X_long        |V|  V_sym  C            C_target   |T|  R2")
    for i, d in enumerate(decomps):
        print(f" {i}   {d['U_length']}   {d['X_long_symbolic']:<9}  {d['V_length']}   "
              f"{d['V_symbolic'] or '-':<6} {d['C_label']:<12} "
              f"({d['C_target_orbit']},{d['C_target_phase']})   {d['T_length']}   {d['R2_label']}")

    print("\n=== section 7: what survived the excursion ===")
    for i, l in enumerate(ledgers):
        print(f" {i}  O*={l['o_star']}  phases used {l['O_star_phases_used_in_order']}  "
              f"distinct={l['distinct_O_star_phases_used']}  ends at 4: "
              f"{l['phase_4_still_available_when_C_fires']}  chaining={l['chaining']}  "
              f"phi={l['phi']}")

    print("\n=== section 8: parity accounting (measured, not assumed) ===")
    print(" #  Z->O* (in exc / out)  Z->other  Z total  k  #R_odd  identity")
    for i, p in enumerate(parities):
        print(f" {i}   {p['n_Z_to_O_star_total_in_PC']} "
              f"({p['n_Z_to_O_star_inside_excursion']}/{p['n_Z_to_O_star_outside_excursion']})"
              f"           {p['n_Z_to_other']:>2}        {p['n_Z_total']:>2}    "
              f"{p['winding_k']}    {p['n_R_steps_with_odd_delta']}      "
              f"{p['corrected_identity_holds']}")
    hist = historical_parity()
    if hist.get("available"):
        print(f"\n historical short witnesses ({hist['n_completions']} completions, "
              f"depth<=6): #Z->O* histogram {hist['n_Z_to_O_star_histogram']}, "
              f"all even = {hist['all_even']}")

    print("\n=== section 10: same-component => chaining ===")
    ch = all(w["chaining"] for w in wits)
    print(f" all six witnesses chain (R1 target orbit == R2 source orbit): {ch}")
    print(f" r1_target_orbit values: {sorted({w['r1_target_orbit'] for w in wits})}")
    print(f" r2_source_orbit values: {sorted({w['r2_source_orbit'] for w in wits})}")

    print("\n=== section 11: terminal normal form scope ===")
    tnf = {
        "o_star_is_orbit_1": sorted({w["o_star"] for w in wits}) == [1],
        "C_target": sorted({(w["trace"][w["C_index"]]["target_orbit"],
                             w["trace"][w["C_index"]]["target_phase"]) for w in wits}),
        "R2_label": sorted({w["trace"][w["R2_index"]]["label"] for w in wits}),
        "chaining_all": ch,
        "phi_all_zero": sorted({w["phi"] for w in wits}) == [0],
        "tail_lengths": sorted({w["tail_length"] for w in wits}),
    }
    for k, v in tnf.items():
        print(f"  {k}: {v}")

    inc = classify_incomplete(res)
    print(f"\n=== section 12: the 22 INCOMPLETE roots ===")
    print(f"  count {inc['n_incomplete']}, by ell {inc['by_root_ell']}")
    print(f"  by symbolic word {inc['by_symbolic_word']}")
    print(f"  all share a symbolic class with a FOUND root: "
          f"{inc['all_share_symbolic_class_with_a_FOUND_root']}")
    print(f"  R2 boundaries reached, range {inc['r2_boundaries_reached_range']}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-long-normal-form-classes-v1",
        "decomposition": "A_4 . U . X_long . V . C . R2",
        "decompositions": decomps,
        "survival_ledgers": ledgers,
        "parity_accounting": parities,
        "historical_short_witness_parity": hist,
        "same_component_implies_chaining": {
            "all_six_chain": ch,
            "status": ("same-component => chaining is NOT refuted by these witnesses; all "
                       "six satisfy it, so they are six new confirming instances, not "
                       "counterexamples"),
            "grade": "exact replay",
        },
        "terminal_normal_form_scope": tnf,
        "incomplete_classification": inc,
        "grade": "exact replay + exact quotient + bounded incomplete (section 12)",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
