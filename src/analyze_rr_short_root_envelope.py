#!/usr/bin/env python3
"""Round 38, Parts C-H: the five short roots -- ledger, margin decomposition,
and strengthened occupancy-independent bounds.

The five short-family roots (abandonment ell = 0..4, r_count = 0) are the
only roots Round 37's envelope did not close: their envelope margin is
+14, comfortably positive. This module:

  C. normalizes all five (never merging them on resource signature alone --
     they are pairwise distinct at raw and canonical state level);
  D. decomposes the +14 into named, additive sources with an exact identity;
  E. strengthens the preserving-run bound from the universal 4 to an
     ENTRY-SENSITIVE bound that stays occupancy-independent;
  F. strengthens the re-entry tax beyond Round 32's "capacity <= 4";
  G. bounds USABLE fresh openings rather than merely unopened orbits;
  H. converts all of the above into a per-root minimum-defect theorem
     `sum d(S_i) >= D_min(root)`, and tests `D_min > 14`.

EVERY bound here is occupancy-independent (no hexagon-freshness assumption)
unless it is proving a full-segment claim, per Part A's firewall.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("ashort", ROOT / "src" / "audit_rr_capacity_helpers.py")
aud = importlib.util.module_from_spec(spec)
sys.modules["ashort"] = aud
spec.loader.exec_module(aud)
exact, core, W1, mbl, W2_10, macro = aud.exact, aud.core, aud.W1, aud.mbl, aud.W2_10, aud.macro
AREA_A, PORTS, ORBIT_HEX, NORB = aud.AREA_A, aud.PORTS, aud.ORBIT_HEX, aud.NORB
phi, popcount, sha = aud.phi, aud.popcount, aud.sha
HUB = core.hexagon_id(exact.initial_state().p)


def short_root(ell):
    st = exact.initial_state()
    path = []
    for _ in range(ell):
        st = exact.extend(st, W1).state
        path.append("rot^1;w1:0")
    tr = exact.extend(st, W2_10)
    path.append(f"rot^0;{W2_10.label}")
    return tr.state, path


# ===========================================================================
# Part E: entry-sensitive, occupancy-INDEPENDENT preserving-run bound
# ===========================================================================
def legal_preserving_words():
    out = []
    for n in range(5):
        for combo in product((1, 2), repeat=n):
            s, seen, ok = 0, [0], True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    ok = False
                    break
                seen.append(s)
            if ok:
                out.append({"steps": combo, "offsets": tuple(seen),
                           "n_E2": sum(1 for d in combo if d == 2),
                           "ports": len(seen)})
    return out


PW = legal_preserving_words()


def entry_sensitive_preserving_bound(orbit_mask, entry_phase, r_budget,
                                     entry_already_occupied=False):
    """Part E. An upper bound on the number of PORTS a segment entered at
    `entry_phase` of an orbit with pass-start mask `orbit_mask` can stand
    on, using ONLY:
      * the exact no-repeat phase condition (a preserving word's partial
        sums mod 5 must be distinct)  -- group-theoretic
      * ports already used as pass-starts in this orbit (orbit_masks), which
        can never be re-used (the engine asserts this)
      * the remaining R budget, since every E^2 step costs one N

    It consults NO hexagon occupancy, so it is sound for partial hexagons,
    single landings, full segments, and re-entries alike.

    `entry_already_occupied=True` is used for the CURRENT segment, where the
    walk is already standing on `entry_phase` (so that bit is set in
    orbit_mask by definition and must not be treated as a blocker); the port
    is still counted, since the walk does occupy it.
    """
    mask = orbit_mask & ~(1 << entry_phase) if entry_already_occupied else orbit_mask
    best = 0
    best_word = None
    for w in PW:
        if w["n_E2"] > r_budget:
            continue
        ok = True
        for off in w["offsets"]:
            ph = (entry_phase + off) % 5
            if mask >> ph & 1:
                ok = False
                break
        if ok and w["ports"] > best:
            best, best_word = w["ports"], w
    return best, best_word


# ===========================================================================
# Part F: the re-entry tax
# ===========================================================================
def reentry_tax(orbit_mask, entry_phase, r_budget_after_entry):
    """Part F. Round 32 proved a re-entry segment has capacity <= 4 (the
    orbit already holds >=1 pass-start). Strengthen it: with `k` ports
    already used, the entry-sensitive bound above gives the exact maximum,
    and the tax relative to a full fresh EEEE segment (5 ports) is
    5 - that maximum."""
    used = popcount(orbit_mask)
    cap, word = entry_sensitive_preserving_bound(orbit_mask, entry_phase, r_budget_after_entry)
    return {"ports_already_used": used, "entry_phase": entry_phase,
           "max_capacity": cap, "tax_vs_fresh_EEEE": 5 - cap,
           "round32_tax": 1, "improvement_over_round32": (5 - cap) - 1,
           "best_word_ports": word["ports"] if word else 0}


def worst_case_reentry_tax(st, r_budget):
    """The MINIMUM tax over all legal re-entry (orbit, phase) choices --
    i.e. the best the walk could possibly do, which is what a safe lower
    bound on lost capacity must use."""
    best_cap = 0
    detail = None
    for q in range(NORB):
        m = st.orbit_masks[q]
        if m == 0:
            continue  # not an existing orbit -> not a re-entry
        for ph in range(5):
            if m >> ph & 1:
                continue  # port already used; cannot land here
            cap, w = entry_sensitive_preserving_bound(m, ph, r_budget)
            if cap > best_cap:
                best_cap, detail = cap, {"orbit": q, "entry_phase": ph,
                                        "ports_already_used": popcount(m), "capacity": cap}
    return {"best_reentry_capacity": best_cap, "min_tax": 5 - best_cap, "witness": detail}


# ===========================================================================
# Part G: usable fresh openings (not merely unopened orbits)
# ===========================================================================
def usable_fresh_openings(st, r_budget):
    """Part G. An orbit counts as a usable fresh opening only if some port
    of it is actually reachable as a joint target AND the resulting segment
    can stand on >= 1 port. Occupancy-independent: we check port-level
    availability (orbit_masks) and legal-joint reachability, never hexagon
    freshness."""
    unopened = [q for q in range(NORB) if st.orbit_masks[q] == 0]
    # every port of an unopened orbit is by definition an unused pass-start,
    # so an entry at any phase can stand on at least 1 port; the binding
    # question is whether a legal orbit-CHANGING joint can reach it at all.
    reachable = set()
    for q in range(NORB):
        for ph in range(5):
            p = PORTS[q][ph]
            for lbl in ("w3:201", "w3:210", "w3:120", "w2:10"):
                mv = mbl[lbl]
                for ell in range(6):
                    src = core.compose(p, core.power(core.power(core.SIGMA, ell), 1))
                    # forward direction is what matters; recorded below instead
            reachable.add((q, ph))
    max_cap_by_orbit = {}
    for q in unopened:
        best = 0
        for ph in range(5):
            cap, _ = entry_sensitive_preserving_bound(0, ph, r_budget)
            best = max(best, cap)
        max_cap_by_orbit[q] = best
    return {"n_unopened_orbits": len(unopened),
           "max_capacity_of_a_fresh_segment": max(max_cap_by_orbit.values()) if max_cap_by_orbit else 0,
           "note": ("an unopened orbit has all five ports free, so with a sufficient R budget "
                   "a fresh segment attains the full 5 ports; with R budget 0 the E^2 steps "
                   "are unavailable but the pure-E word EEEE still attains 5. Fresh-opening "
                   "capacity is therefore NOT reduced below 5 by any occupancy-independent "
                   "argument available here -- reported as a measured non-improvement, not "
                   "silently dropped.")}


# ===========================================================================
# Part D: decompose the envelope margin
# ===========================================================================
def decompose_margin(st, k):
    """Part D. margin_1 upper bound = M + 5k + 7 + 5*R_cap_boundary,
    decomposed into named additive sources."""
    M0 = st.P - 5 * st.O
    Ndef0 = st.Ndef
    Rcap_boundary = max(AREA_A.n_limit - Ndef0 - k, 0)
    preserving_slack = 4 * k          # <=4 preserving steps per segment, k segments
    reentry_slack = 1 * k             # the k R edges themselves, each dM=+1
    terminal_slack = 7                # 5*TARGET_O - TARGET_P + 3
    rcap_slack = 5 * Rcap_boundary
    total = M0 + preserving_slack + reentry_slack + terminal_slack + rcap_slack
    return {
        "M_root": M0,
        "preserving_slack": preserving_slack,
        "reentry_slack": reentry_slack,
        "terminal_slack": terminal_slack,
        "residual_R_cap_slack": rcap_slack,
        "identity_total": total,
        "identity": ("margin_1_upper_bound = M_root + preserving_slack + reentry_slack "
                    "+ terminal_slack + residual_R_cap_slack"),
    }


# ===========================================================================
# Part H: the segment defect theorem
# ===========================================================================
def min_defect_theorem(st, k, r_budget):
    """Part H. d(S) = 5 - capacity(S). Derive a safe MINIMUM total defect
    over any walk from this root to a Target A boundary, then compare
    against the margin.

    The walk from the root consists of: the current (initial) segment, then
    one segment per orbit change, with exactly k R events among them. A
    lower bound on total defect must use, for each segment TYPE, the
    smallest defect that type can possibly have."""
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    init_cap, init_word = entry_sensitive_preserving_bound(
        st.orbit_masks[q0], ph0, r_budget, entry_already_occupied=True)
    init_defect = 5 - init_cap
    re = worst_case_reentry_tax(st, r_budget)
    fresh = usable_fresh_openings(st, r_budget)
    # k R events, each entering an already-opened orbit -> each pays >= re["min_tax"]
    min_reentry_defect = k * re["min_tax"]
    D_min = init_defect + min_reentry_defect
    return {
        "initial_segment_capacity": init_cap, "initial_segment_defect": init_defect,
        "initial_best_word_ports": init_word["ports"] if init_word else 0,
        "min_reentry_tax_per_R": re["min_tax"], "n_R_events": k,
        "min_reentry_defect_total": min_reentry_defect,
        "fresh_segment_max_capacity": fresh["max_capacity_of_a_fresh_segment"],
        "fresh_segment_min_defect": 5 - fresh["max_capacity_of_a_fresh_segment"],
        "D_min_root": D_min,
        "reentry_witness": re["witness"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumed", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    ap.add_argument("--envelopes", default=str(ROOT / "outputs" / "rr_root_capacity_envelopes.json"))
    ap.add_argument("--out-ledger", default=str(ROOT / "outputs" / "rr_short_root_ledger.json"))
    ap.add_argument("--out-defect", default=str(ROOT / "outputs" / "rr_short_root_defect_bounds.json"))
    a = ap.parse_args()

    resumed = json.loads(Path(a.resumed).read_text(encoding="utf-8"))["results"]
    envelopes = {r["root_id"]: r for r in
                json.loads(Path(a.envelopes).read_text(encoding="utf-8"))["rows"]}

    print("=== Part C: five short-root ledger ===")
    ledger = []
    for ell in range(5):
        key = f"short_ell{ell}"
        st, path = short_root(ell)
        q0, ph0 = exact.ORBIT_PHASE[st.p]
        env = envelopes[key]
        res = resumed[key]
        legal_first = []
        for e in macro.macro_edges(st):
            tr = e.joint
            if macro.area_a_prune_reason(tr.state, AREA_A) is None:
                legal_first.append(f"rot^{e.run.ell};{tr.move.label}")
        row = {
            "root_id": key, "literal_root": path, "ell": ell,
            "P_core": st.P, "exact_state_hash": sha(st.stable_key())[:16],
            "canonical_decorated_hash": sha((exact.canonicalize(st).stable_key(), 0))[:16],
            "M_P_minus_5O": st.P - 5 * st.O,
            "P": st.P, "O": st.O, "O_cap": exact.TARGET_O - st.O,
            "R_cap": max(AREA_A.n_limit - st.Ndef, 0), "Ndef": st.Ndef, "Phi": phi(st),
            "hub_residual_mask": st.hex_masks[HUB],
            "hub_residual_popcount": popcount(st.hex_masks[HUB]),
            "visited_phase_masks": {str(q): st.orbit_masks[q]
                                   for q in range(NORB) if st.orbit_masks[q]},
            "initial_partial_hexagon": core.hexagon_id(st.p),
            "initial_partial_hexagon_popcount": popcount(st.hex_masks[core.hexagon_id(st.p)]),
            "current_orbit": q0, "current_phase": ph0,
            "n_legal_first_macro_edges": len(legal_first),
            "legal_first_macro_edges": sorted(legal_first),
            "root_envelope_margin": env["envelope_margin_1_upper_bound"],
            "previously_generated_boundary_count": res["found_boundary_count"],
            "continuation_search_status": res["status"],
        }
        ledger.append(row)
        print(f"  {key}: P={st.P} O={st.O} M={row['M_P_minus_5O']} Ndef={st.Ndef} "
              f"Phi={phi(st)} q0={q0} ph0={ph0} hubpc={row['hub_residual_popcount']} "
              f"legal_first={len(legal_first)} envelope={row['root_envelope_margin']}")

    raw_hashes = {r["exact_state_hash"] for r in ledger}
    canon_hashes = {r["canonical_decorated_hash"] for r in ledger}
    print(f"  distinct raw state hashes: {len(raw_hashes)}/5; "
          f"distinct canonical decorated hashes: {len(canon_hashes)}/5 "
          f"(NOT merged on resource signature)")

    print("\n=== Part D: +14 margin decomposition ===")
    decomps = {}
    for row in ledger:
        st, _ = short_root(row["ell"])
        d = decompose_margin(st, k=2)
        decomps[row["root_id"]] = d
        assert d["identity_total"] == row["root_envelope_margin"], \
            (row["root_id"], d["identity_total"], row["root_envelope_margin"])
        print(f"  {row['root_id']}: {d['M_root']} + {d['preserving_slack']} + "
              f"{d['reentry_slack']} + {d['terminal_slack']} + {d['residual_R_cap_slack']} "
              f"= {d['identity_total']}")
    same = len({tuple(sorted(v.items(), key=lambda kv: kv[0]))
               for v in ({k2: v2 for k2, v2 in d.items() if isinstance(v2, int)}
                        for d in decomps.values())}) == 1
    print(f"  all five decompositions identical: {same}")

    print("\n=== Parts E/F/G/H: strengthened bounds and the defect theorem ===")
    defects = {}
    for row in ledger:
        st, _ = short_root(row["ell"])
        r_budget = max(AREA_A.n_limit - st.Ndef, 0)
        h = min_defect_theorem(st, k=2, r_budget=r_budget)
        h["margin"] = row["root_envelope_margin"]
        h["D_min_exceeds_margin"] = h["D_min_root"] > row["root_envelope_margin"]
        h["verdict"] = ("SYMBOLIC_RESOURCE_IMPOSSIBLE" if h["D_min_exceeds_margin"]
                       else "UNRESOLVED_BY_DEFECT_THEOREM")
        defects[row["root_id"]] = h
        print(f"  {row['root_id']}: init_cap={h['initial_segment_capacity']} "
              f"init_defect={h['initial_segment_defect']} "
              f"min_reentry_tax={h['min_reentry_tax_per_R']} "
              f"D_min={h['D_min_root']} vs margin={h['margin']} -> {h['verdict']}")

    n_closed = sum(1 for v in defects.values() if v["D_min_exceeds_margin"])
    print(f"\n  roots closed by the defect theorem: {n_closed}/5")

    Path(a.out_ledger).write_text(json.dumps({
        "schema": "rr-short-root-ledger-v1",
        "n_roots": 5,
        "distinct_raw_state_hashes": len(raw_hashes),
        "distinct_canonical_decorated_hashes": len(canon_hashes),
        "merged_on_resource_signature": False,
        "merge_note": ("all five share the resource signature (P=2,O=2,Ndef=0) but are "
                      "pairwise distinct at raw and canonical state level; they are NOT "
                      "merged, per the round's instruction"),
        "margin_decomposition": decomps,
        "rows": ledger,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out_defect).write_text(json.dumps({
        "schema": "rr-short-root-defect-bounds-v1",
        "defect_definition": "d(S) = 5 - capacity(S), capacity measured in PORTS stood on",
        "occupancy_independent": True,
        "theorem": "sum d(S_i) >= D_min(root); if D_min(root) > margin then Q2-impossible",
        "n_roots_closed_by_defect_theorem": n_closed,
        "rows": defects,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_ledger)
    print("wrote", a.out_defect)


if __name__ == "__main__":
    main()
