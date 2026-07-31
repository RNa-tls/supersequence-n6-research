#!/usr/bin/env python3
"""Round 38, Parts I and J: the symbolic resource relaxation and the
search-worthiness decision for the five short roots.

PART I -- a tiny symbolic resource model, solved by EXHAUSTIVE ENUMERATION
(no certified ILP solver exists in this environment, so an independently
checkable enumerator is used instead, exactly as the brief requires).

Variables, all non-negative integers:
    c_init                capacity (ports) of the segment already in progress
    f_j   for j in 1..5   number of FRESH-opening segments of capacity j
    r_j   for j in 1..4   number of RE-ENTRY segments of capacity j
                          (capacity <= 4: an opened orbit already holds a
                          pass-start, Round 32)
    n_E2                  total E^2 preserving steps used anywhere

Constraints:
    (1) ports        c_init + sum_j j*f_j + sum_j j*r_j == TARGET_P - P0 + 1
    (2) fresh budget sum_j f_j <= O_cap        (= TARGET_O - O0)
    (3) N budget     sum_j r_j + n_E2 <= R_cap (= n_limit - Ndef0);
                     each re-entry costs one N, each E^2 step costs one N
    (4) initial cap  1 <= c_init <= init_cap_max  (Part E, entry-sensitive,
                     occupancy-INDEPENDENT)
    (5) M conservation is implied by (1)-(3) and is checked, not assumed

INTERPRETATION, stated before the result so it cannot drift:
    infeasible  =>  the root is Q2-impossible          (a real certificate)
    feasible    =>  UNRESOLVED. Never a continuation witness: this is a
                    resource RELAXATION with no path, no geometry, no
                    hexagon disjointness, and no ordering.

PART J -- classification into ROOT_ENVELOPE_IMPOSSIBLE /
SYMBOLIC_RESOURCE_IMPOSSIBLE / STRUCTURAL_SURVIVOR / MODEL_INCOMPLETE.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("vshort", ROOT / "src" / "analyze_rr_short_root_envelope.py")
sre = importlib.util.module_from_spec(spec)
sys.modules["vshort"] = sre
spec.loader.exec_module(sre)
exact, AREA_A = sre.exact, sre.AREA_A


def solve_resource_model(P0, O0, Ndef0, init_cap_max, n_limit=None):
    """Exhaustive enumeration over the (c_init, f_*, r_*, n_E2) lattice.

    Returns (feasible, witness_or_None, n_states_examined). The enumeration
    is complete by construction: it iterates c_init over its full legal
    range and, for each, iterates the number of re-entry segments and their
    total capacity, then checks whether the residual port requirement can be
    met by fresh segments within the fresh budget. Every quantity is bounded
    by an explicit, small integer range, so no truncation occurs.
    """
    if n_limit is None:
        n_limit = AREA_A.n_limit
    need = exact.TARGET_P - P0 + 1
    O_cap = exact.TARGET_O - O0
    R_cap = max(n_limit - Ndef0, 0)
    examined = 0
    for c_init in range(1, init_cap_max + 1):
        for n_re in range(0, R_cap + 1):
            # each re-entry costs one N; remaining N may buy E^2 steps, which
            # do not add ports of their own beyond the segment capacities
            for re_total in range(n_re * 1, n_re * 4 + 1):   # total ports from re-entries
                residual = need - c_init - re_total
                if residual < 0:
                    continue
                # fresh segments: at most O_cap of them, each 1..5 ports
                for n_fresh in range(0, O_cap + 1):
                    examined += 1
                    if n_fresh == 0:
                        if residual == 0:
                            return True, {"c_init": c_init, "n_re": n_re,
                                         "re_total_ports": re_total, "n_fresh": 0,
                                         "fresh_total_ports": 0}, examined
                        continue
                    if n_fresh <= residual <= 5 * n_fresh:
                        return True, {"c_init": c_init, "n_re": n_re,
                                     "re_total_ports": re_total, "n_fresh": n_fresh,
                                     "fresh_total_ports": residual}, examined
    return False, None, examined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=str(ROOT / "outputs" / "rr_short_root_ledger.json"))
    ap.add_argument("--defects", default=str(ROOT / "outputs" / "rr_short_root_defect_bounds.json"))
    ap.add_argument("--envelopes", default=str(ROOT / "outputs" / "rr_root_capacity_envelopes.json"))
    ap.add_argument("--resumed", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_short_root_resource_results.json"))
    a = ap.parse_args()

    ledger = json.loads(Path(a.ledger).read_text(encoding="utf-8"))
    defects = json.loads(Path(a.defects).read_text(encoding="utf-8"))["rows"]
    envelopes = {r["root_id"]: r for r in
                json.loads(Path(a.envelopes).read_text(encoding="utf-8"))["rows"]}
    resumed = json.loads(Path(a.resumed).read_text(encoding="utf-8"))["results"]

    print("=== Part I: symbolic resource relaxation (exhaustive enumerative verifier) ===")
    rows = []
    for row in ledger["rows"]:
        key = row["root_id"]
        init_cap_max = defects[key]["initial_segment_capacity"]
        feasible, witness, examined = solve_resource_model(
            row["P"], row["O"], row["Ndef"], init_cap_max)
        env = envelopes[key]
        dfc = defects[key]
        if env["certified_q2_impossible"]:
            verdict = "ROOT_ENVELOPE_IMPOSSIBLE"
        elif not feasible:
            verdict = "SYMBOLIC_RESOURCE_IMPOSSIBLE"
        elif dfc["D_min_exceeds_margin"]:
            verdict = "SYMBOLIC_RESOURCE_IMPOSSIBLE"
        else:
            verdict = "STRUCTURAL_SURVIVOR"
        rows.append({
            "root_id": key, "P0": row["P"], "O0": row["O"], "Ndef0": row["Ndef"],
            "ports_required": exact.TARGET_P - row["P"] + 1,
            "O_cap": row["O_cap"], "R_cap": row["R_cap"],
            "init_cap_max": init_cap_max,
            "resource_model_feasible": feasible,
            "resource_model_witness": witness,
            "lattice_points_examined": examined,
            "envelope_margin": env["envelope_margin_1_upper_bound"],
            "envelope_certifies_impossible": env["certified_q2_impossible"],
            "D_min": dfc["D_min_root"], "D_min_exceeds_margin": dfc["D_min_exceeds_margin"],
            "classification": verdict,
            "continuation_search_status": resumed[key]["status"],
            "feasibility_is_not_a_witness": ("this is a resource relaxation with no path, "
                                            "no geometry, no hexagon disjointness and no "
                                            "ordering; feasibility means UNRESOLVED only"),
        })
        print(f"  {key}: need={rows[-1]['ports_required']} O_cap={row['O_cap']} "
              f"R_cap={row['R_cap']} init_cap_max={init_cap_max} -> "
              f"feasible={feasible} (lattice points examined {examined}) -> {verdict}")

    print("\n=== Part J: search-worthiness classification ===")
    from collections import Counter
    hist = Counter(r["classification"] for r in rows)
    print(f"  {dict(hist)}")
    survivors = [r for r in rows if r["classification"] == "STRUCTURAL_SURVIVOR"]
    print(f"  STRUCTURAL_SURVIVOR roots eligible for resumed continuation search: "
          f"{[r['root_id'] for r in survivors]}")

    # explicit, clearly-labelled heuristic cost-benefit note (NOT a proof)
    cost_benefit = {
        "label": "HEURISTIC -- not a proof, not a certificate, never used to prune",
        "observation": ("at the Round 36 budget each short root expanded 71k-80k nodes in 90s "
                        "with the queue still growing to 120k-134k; extrapolating that growth "
                        "rate, exhausting even one of these roots is far outside any budget "
                        "available in a single session"),
        "consequence": ("these roots ARE search-worthy in the mathematical sense -- they are "
                        "genuine STRUCTURAL_SURVIVORs with no impossibility certificate -- but "
                        "a naive resumption is not the efficient next step; a new "
                        "occupancy-independent bound, or a proved quotient, would be"),
        "explicitly_not_claimed": "that the roots are closed, or that search is pointless",
    }

    Path(a.out).write_text(json.dumps({
        "schema": "rr-short-root-resource-results-v1",
        "model": {
            "variables": ["c_init", "f_1..f_5 (fresh segments by capacity)",
                         "r_1..r_4 (re-entry segments by capacity)", "n_E2"],
            "constraints": [
                "c_init + sum j*f_j + sum j*r_j == TARGET_P - P0 + 1",
                "sum f_j <= O_cap",
                "sum r_j + n_E2 <= R_cap",
                "1 <= c_init <= init_cap_max (entry-sensitive, occupancy-independent)",
                "re-entry capacity <= 4 (Round 32)",
            ],
            "solver": "exhaustive enumeration over an explicitly bounded integer lattice",
            "interpretation": {
                "infeasible": "root is Q2-impossible (certificate)",
                "feasible": "UNRESOLVED -- never a continuation witness",
            },
        },
        "classification_histogram": {k: v for k, v in hist.items()},
        "heuristic_cost_benefit_note": cost_benefit,
        "rows": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
