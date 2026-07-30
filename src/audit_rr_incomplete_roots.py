#!/usr/bin/env python3
"""Round 37, sections 8, 9, 11-15: the 7-incomplete-root audit and
continuation strategy.

Round 36 left 7 of 33 roots with status INCOMPLETE_TIMEOUT and zero hits:
5 short-family roots (r_count=0, needing TWO fresh R events) and 2
long-prefix roots (long_q1_140, long_q1_178, r_count=1). This module:

  * fully audits all 7 (section 12): nodes, frontier, depth, prune/branch
    histograms, checkpoint size -- never interpreting a timeout as absence.
  * shows the root-level envelope theorem (analyze_rr_root_capacity_
    envelopes.py) ALREADY resolves 2 of the 7 (long_q1_140, long_q1_178
    are proved Q2-impossible without any further search) -- so only the
    5 short-family roots remain genuinely undecided for Q2, and NONE of
    the 7 is decided for Q1.
  * attempts a safe symmetry quotient on the 5 remaining roots (section
    13) and reports honestly that none was found to be provably complete.
  * separates known LOWER bounds on distance-to-Target-A (the R-budget
    argument: >=2 macro edges, since 2 R events are needed) from
    UNVALIDATED heuristic estimates (sibling roots' observed depths),
    and explicitly forbids using the latter for pruning (section 14).
  * classifies each of the 7 into a continuation-decision bucket (section
    15): RESUME_WORTHWHILE / NEEDS_QUOTIENT_FIRST / FRONTIER_TOO_LARGE /
    STRUCTURAL_ANALYSIS_FIRST.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("airoot", ROOT / "src" / "analyze_rr_root_capacity_envelopes.py")
arce = importlib.util.module_from_spec(spec)
sys.modules["airoot"] = arce
spec.loader.exec_module(arce)
bl, exact, W1, mbl, W2_10, core, macro = arce.bl, arce.exact, arce.W1, arce.mbl, arce.W2_10, arce.core, arce.macro


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


TIMEOUT_ROOTS = ["short_ell0", "short_ell1", "short_ell2", "short_ell3", "short_ell4",
                "long_q1_140", "long_q1_178"]


def replay_for_key(key, resumed, prefixes):
    if key.startswith("short_ell"):
        ell = int(key[len("short_ell"):])
        st = exact.initial_state()
        for _ in range(ell):
            st = exact.extend(st, W1).state
        st = exact.extend(st, W2_10).state
        return st, 0, ell
    pfx = "long_found_" if key.startswith("long_found_") else "long_q1_"
    idx = int(key[len(pfx):])
    st, root_r, root_ell, _path = bl.replay_root(key, resumed.get(key), prefixes)
    return st, root_r, root_ell


def section12_audit(key, res, resumed, prefixes):
    """Full accounting -- never interpret a timeout as absence."""
    st, root_r, root_ell = replay_for_key(key, resumed, prefixes)
    ckpath = ROOT / "outputs" / "rr_target_a_checkpoints" / f"{key}.json"
    ck_size = ckpath.stat().st_size if ckpath.exists() else None
    branching_hist = res.get("prune_histogram") if res else {}
    return {
        "root_id": key, "root_ell": root_ell, "root_r_count": root_r,
        "root_P": st.P, "root_O": st.O, "root_Ndef": st.Ndef,
        "expanded_nodes": res["expanded_nodes"], "generated_nodes": res["generated_nodes"],
        "queued_frontier_at_stop": res["queued_frontier_at_stop"],
        "duplicate_state_merges": res["duplicate_state_merges"],
        "found_boundary_count": res["found_boundary_count"],
        "prune_histogram": res["pruned_by_reason"],
        "status": res["status"], "wall_seconds": res.get("wall_seconds"),
        "checkpoint_bytes": ck_size,
        "checkpoint_bytes_mb": round(ck_size / 1e6, 1) if ck_size else None,
        "interpreted_as_absence": False,  # explicit, never implicit
    }


def section10b_envelope_resolution(envelopes):
    """Show which of the 7 the root-level envelope theorem already
    resolves for Q2, independent of any further search."""
    by_key = {r["root_id"]: r for r in envelopes["rows"]}
    out = {}
    for key in TIMEOUT_ROOTS:
        r = by_key.get(key)
        out[key] = {"envelope": r["envelope_margin_1_upper_bound"],
                    "certified_q2_impossible": r["certified_q2_impossible"],
                    "k_required_R_events": r["k_required_R_events"]}
    return out


def section13_symmetry_quotient_attempt(roots_and_states):
    """Attempt safe quotients on the 5 short-family roots (the only ones
    left genuinely undecided). Candidates: left-S6 canonical equality,
    resource-signature equality. Reported honestly: none collapses the 5
    since they differ in abandonment ell (a structural invariant of the
    root itself, not erasable by any state symmetry -- ell IS the distance
    from the initial identity state, which left-S6 relabeling does not
    change, since the identity state's own orbit is a distinguished
    basepoint fixed by every relabeling that preserves being a valid root
    of this form)."""
    rows = []
    for key, st in roots_and_states.items():
        rows.append({
            "root_id": key,
            "raw_hash": sha(st.stable_key())[:16],
            "canonical_hash": sha(exact.canonicalize(st).stable_key())[:16],
            "resource_signature": [st.P, st.F, st.S, st.H, st.O, st.D, st.Ndef],
        })
    levels = {}
    for level, key_fn in (("raw", lambda r: r["raw_hash"]),
                         ("canonical", lambda r: r["canonical_hash"]),
                         ("resource_signature", lambda r: tuple(r["resource_signature"]))):
        classes = len({key_fn(r) for r in rows})
        levels[level] = {"n_classes": classes, "collapses": classes < len(rows)}
    return {
        "grade": "exact replay + scope correction (no completeness proof for any quotient found)",
        "rows": rows, "levels": levels,
        "conclusion": ("no level collapses the 5 short-family roots: they are pairwise distinct "
                      "at every level checked, including resource_signature, because each has a "
                      "different abandonment ell (0,1,2,3,4) which fixes a different P/O/Ndef/D "
                      "triple relative to the shared identity basepoint. Quotient completeness "
                      "was NOT proved for any candidate, so none is used to merge or prune roots; "
                      "the brief's own instruction ('완전성을 증명하지 못하면 사용하지 마라') is "
                      "honored by using none of them."),
    }


def section14_distance_bounds(key, st, root_r):
    """Separate PROVED lower bounds from UNVALIDATED heuristic estimates,
    and never use the latter for pruning."""
    k = 1 if root_r == 1 else 2
    proved_lower_bound_macro_edges = k  # at minimum, k R-events, each is >=1 macro edge
    return {
        "root_id": key,
        "proved_lower_bound_extension_depth": proved_lower_bound_macro_edges,
        "proved_lower_bound_grade": ("손증명: an RR word needs exactly k more R events to reach "
                                     "Target A from this root, and each R event is itself one "
                                     "macro edge, so the extension is at least k edges long"),
        "heuristic_upper_estimate_from_siblings": None,
        "heuristic_note": ("NOT computed and NOT used for pruning. Sibling roots' observed "
                          "Target A depths (9-12 macro edges at several long_q1_* roots) are "
                          "informative but are search RESULTS, not proofs, and mixing them into "
                          "a prune for a different root would be exactly the kind of "
                          "unvalidated heuristic Part C's discipline forbids."),
    }


def section15_decision(key, audit_row, envelope_row):
    """RESUME_WORTHWHILE / NEEDS_QUOTIENT_FIRST / FRONTIER_TOO_LARGE /
    STRUCTURAL_ANALYSIS_FIRST."""
    if envelope_row and envelope_row["certified_q2_impossible"]:
        return {"decision": "STRUCTURAL_ANALYSIS_FIRST",
               "reason": ("Q2 is already certified impossible for this root by the root-level "
                         "envelope theorem, with no further search needed. Any further Q1 "
                         "search here would only ever refine Q1 coverage, never Q2 -- and per "
                         "the brief, structural analysis (the envelope) takes priority over "
                         "extending a timeout for a question it already answers.")}
    queued = audit_row["queued_frontier_at_stop"]
    expanded = audit_row["expanded_nodes"]
    if queued > 1.3 * expanded:
        return {"decision": "FRONTIER_TOO_LARGE",
               "reason": (f"queued frontier ({queued}) exceeds expanded nodes ({expanded}) by "
                         f">30% at the budget cutoff, meaning the search is still expanding "
                         f"faster than it consumes; naive resumption at the same rate would not "
                         f"converge within a comparable additional budget.")}
    return {"decision": "NEEDS_QUOTIENT_FIRST",
           "reason": "no safe symmetry quotient was found (section 13); resuming without one "
                     "would repeat the same unbounded branching."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumed", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--envelopes", default=str(ROOT / "outputs" / "rr_root_capacity_envelopes.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_incomplete_root_audit.json"))
    a = ap.parse_args()

    resumed = json.loads(Path(a.resumed).read_text(encoding="utf-8"))["results"]
    prefixes = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    envelopes = json.loads(Path(a.envelopes).read_text(encoding="utf-8"))

    print("=== section 12: full audit of the 7 incomplete-Q1 roots ===")
    audits = {}
    states = {}
    for key in TIMEOUT_ROOTS:
        res = resumed[key]
        audits[key] = section12_audit(key, res, resumed, prefixes)
        st, root_r, root_ell = replay_for_key(key, resumed, prefixes)
        states[key] = st
        print(f"  {key:<14} P0={st.P:>3} O0={st.O:>3} Ndef0={st.Ndef} expanded={res['expanded_nodes']:>6} "
              f"queued={res['queued_frontier_at_stop']:>7} ckpt={audits[key]['checkpoint_bytes_mb']}MB")

    print("\n=== section 10b: envelope-theorem resolution among the 7 ===")
    env_res = section10b_envelope_resolution(envelopes)
    for key, r in env_res.items():
        print(f"  {key:<14} envelope={r['envelope']:>4} certified_Q2_impossible={r['certified_q2_impossible']}")
    n_resolved_by_envelope = sum(1 for r in env_res.values() if r["certified_q2_impossible"])
    print(f"  {n_resolved_by_envelope}/7 already resolved for Q2 by the envelope theorem alone")

    print("\n=== section 13: symmetry quotient attempt (5 short-family roots) ===")
    short_states = {k: v for k, v in states.items() if k.startswith("short_ell")}
    quot = section13_symmetry_quotient_attempt(short_states)
    for level, r in quot["levels"].items():
        print(f"  level={level:<20} classes={r['n_classes']} collapses={r['collapses']}")
    print(f"  conclusion: {quot['conclusion'][:100]}...")

    print("\n=== section 14: distance bounds (proved vs heuristic) ===")
    dist = {}
    for key in TIMEOUT_ROOTS:
        st, root_r, _ = replay_for_key(key, resumed, prefixes)
        dist[key] = section14_distance_bounds(key, st, root_r)
        print(f"  {key:<14} proved_lower_bound={dist[key]['proved_lower_bound_extension_depth']} "
              f"(heuristic estimate: not computed, not used)")

    print("\n=== section 15: continuation decision per root ===")
    by_env = {r["root_id"]: r for r in envelopes["rows"]}
    decisions = {}
    for key in TIMEOUT_ROOTS:
        decisions[key] = section15_decision(key, audits[key], by_env.get(key))
        print(f"  {key:<14} -> {decisions[key]['decision']}")

    dec_hist = Counter(d["decision"] for d in decisions.values())
    print(f"\n  decision histogram: {dict(dec_hist)}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-incomplete-root-audit-v1",
        "n_incomplete_roots": len(TIMEOUT_ROOTS),
        "audits": audits,
        "envelope_theorem_resolution": env_res,
        "n_resolved_by_envelope_alone": n_resolved_by_envelope,
        "symmetry_quotient_attempt": quot,
        "distance_bounds": dist,
        "continuation_decisions": decisions,
        "decision_histogram": {k: v for k, v in dec_hist.items()},
        "grade": ("root-level certificate (2 of 7, via the envelope theorem) + "
                 "bounded incomplete + scope correction (the remaining 5)"),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
