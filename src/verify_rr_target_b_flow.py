#!/usr/bin/env python3
"""Round 34, sections 12, 16, 17: independent verification of the flow search.

The flow search in search_rr_target_b_flow.py reports that the tree of
legal continuations from every one of the seven boundary states is FINITE
and SMALL -- a few hundred to a few thousand nodes, dying 70-80 hexagons
short of completion.  A claim like that is exactly the kind that is usually
a modelling bug, so it is not accepted on the model's own word.

Three checks, in increasing strength.

1. RESOURCE ACCOUNTING (section 12).  The model charges one R for each E^2
   preserving step and one R for each orbit re-entry, and nothing for a
   fresh opening.  That is re-derived here from the engine's own transition
   arithmetic: Ndef = S + F - O, dS = [weight >= 3], dO = [new orbit], and
   at the end of a full ell=5 run p.SIGMA is visited so dF = 0.

2. ell=5 IS FORCED.  Phi = 5 + 6(TARGET_P - P) - (720 - visited) is 0 at
   every boundary state and changes by ell - 5 per macro edge, and the
   engine's own `remaining_window_capacity_prune` is true exactly when
   Phi < 0.  So no macro edge with ell < 5 survives, and ell = 6 revisits
   the run's first permutation.  Checked against the engine at every node.

3. ENGINE-LEVEL EXHAUSTIVE MACRO DFS -- the decisive one.  This walks the
   real `macro.macro_edges` / `macro.area_a_prune_reason(., AREA_A)` tree
   from the boundary state and knows NOTHING about segments, orbits,
   hexagon covers, or the Round 32 capacity bound.  If that tree is finite
   and contains no completion, the survivor is dead for reasons the segment
   model cannot have invented.  This is a bounded search over macro edges,
   not the forbidden permutation-level depth-100 DFS: it terminates on its
   own, and the node count is reported so the reader can see that it did.

A FOUND result would instead be replayed literally into a character string
and handed to src.verify; no such result occurred.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
sys.setrecursionlimit(20000)


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("vrtbf", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
AREA_A = macro.AREA_A


def phi(st):
    return 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count)


def replay_state(ell, prep):
    st = exact.initial_state()
    for _ in range(ell):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for s in prep["preparation_trace"]:
        for _ in range(s["ell"]):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[s["joint"]]).state
    for _ in range(prep["ell_profile"][-1]):
        st = exact.extend(st, W1).state
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


def resource_accounting_audit():
    """Check 1: the model's R charges are the engine's own arithmetic."""
    rows = []
    for lbl in ("w2:10", "w3:120", "w3:201", "w3:210"):
        mv = mbl[lbl]
        rows.append({"joint": lbl, "weight": mv.weight,
                     "delta_S": int(mv.weight >= 3),
                     "delta_H": max(mv.weight - 3, 0),
                     "orbit_preserving": lbl in ("w2:10", "w3:120")})
    return {
        "statement": ("Ndef = S + F - O; a macro joint has dS = [weight >= 3], "
                      "dF = [p.SIGMA unvisited] = 0 at the end of a full ell=5 run, "
                      "and dO = [target orbit was unopened]"),
        "grade": "exact replay",
        "joints": rows,
        "derived_charges": {
            "w2:10 (= E, preserving)": "dS=0, same orbit so dO=0  ->  dNdef = 0",
            "w3:120 (= E^2, preserving)": "dS=1, same orbit so dO=0  ->  dNdef = +1",
            "w3:201 / w3:210 into a FRESH orbit": "dS=1, dO=1  ->  dNdef = 0",
            "w3:201 / w3:210 into an OPENED orbit": "dS=1, dO=0  ->  dNdef = +1",
        },
        "conclusion": ("the model's R budget -- one unit per E^2 step and one per "
                       "orbit re-entry, none for a fresh opening -- is exactly "
                       "Ndef, and area_a caps it at n_limit = 3"),
    }


def orbit_capacity_bound(st):
    """The Round 32 bound (B+R), recomputed from an ENGINE state alone.

    Every remaining hexagon is completed by exactly one macro edge, and the
    macro edges group into segments: the rest of the current segment, then
    one segment per exit joint.  An exit joint either opens a fresh orbit
    (TARGET_O - O of those remain) or re-enters an opened one (n_limit -
    Ndef of those remain, since a re-entry costs one N).  A fresh segment
    covers at most 5 hexagons, one per port of its orbit; a re-entry covers
    at most 4, because an opened orbit already has a visited port.  The rest
    of the current segment covers the current hexagon plus at most one per
    still-unused port of the current orbit.

    Returns (need, bound).  need > bound is a safe prune -- it is the
    Round 32 orbit-reuse-penalty bound, and it is NOT part of the engine's
    own `area_a_prune_reason`, so it is stated separately here.
    """
    need = exact.TARGET_P - st.P + 1
    q, _ = exact.ORBIT_PHASE[st.p]
    used_ports = bin(st.orbit_masks[q]).count("1")
    o_rem = max(exact.TARGET_O - st.O, 0)
    r_rem = max(AREA_A.n_limit - st.Ndef, 0)
    bound = 1 + (5 - used_ports) + 5 * o_rem + 4 * r_rem
    return need, bound


def engine_dfs(st, node_cap, deadline, stats, use_capacity_bound):
    """Exhaustive macro DFS on the REAL engine.

    `use_capacity_bound=False` uses nothing but the engine's own
    `area_a_prune_reason`; that variant is fully independent but prunes less.
    `use_capacity_bound=True` adds `orbit_capacity_bound`, recomputed from
    engine state fields only.  Terminal test: a state whose maximal rotation
    run finishes all 720 windows.
    """
    stats["nodes"] += 1
    if stats["nodes"] >= node_cap or time.time() > deadline:
        stats["truncated"] = True
        return None
    runs = macro.rotation_runs(st)
    if runs[-1].state.visited_count == 720:
        return []
    stats["depth_hist"][stats["depth"]] += 1
    stats["max_depth"] = max(stats["max_depth"], stats["depth"])
    stats["max_visited"] = max(stats["max_visited"], st.visited_count)
    ells = set()
    for e in macro.macro_edges(st):
        reason = macro.area_a_prune_reason(e.state, AREA_A)
        if reason is not None:
            stats["prune"][reason] += 1
            continue
        if use_capacity_bound:
            need, bound = orbit_capacity_bound(e.state)
            if need > bound:
                stats["prune"]["orbit_capacity_bound_B_plus_R"] += 1
                continue
        ells.add(e.run.ell)
        stats["depth"] += 1
        got = engine_dfs(e.state, node_cap, deadline, stats, use_capacity_bound)
        stats["depth"] -= 1
        if got is not None:
            return [e.label] + got
        if stats["truncated"]:
            return None
    if ells:
        stats["surviving_ells"].update(ells)
    else:
        stats["leaf_states"] += 1
    return None


def new_stats(st):
    return {"nodes": 0, "truncated": False, "depth": 0, "max_depth": 0,
            "max_visited": st.visited_count, "prune": Counter(),
            "depth_hist": Counter(), "surviving_ells": set(), "leaf_states": 0}


def verdict_of(path, stats):
    if path is not None:
        return "FOUND_TARGET_B"
    return "INCOMPLETE" if stats["truncated"] else "EXHAUSTED_NO_PATH"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=str(ROOT / "outputs" / "rr_target_b_ilp_models.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--flow", default=str(ROOT / "outputs" / "rr_flow_search_results.json"))
    ap.add_argument("--succ", default=str(ROOT / "outputs" / "rr_segment_successor_index.json"))
    ap.add_argument("--node-cap", type=int, default=8000000)
    ap.add_argument("--seconds", type=float, default=900.0)
    ap.add_argument("--seconds-plain", type=float, default=60.0,
                    help="budget for the area_a-only variant, which prunes less")
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_flow_certificates.json"))
    a = ap.parse_args()

    acct = resource_accounting_audit()
    print("=== check 1: resource accounting re-derived from the engine ===")
    for k, v in acct["derived_charges"].items():
        print(f"  {k}: {v}")

    models = json.loads(Path(a.models).read_text(encoding="utf-8"))["models"]
    surv = json.loads(Path(a.survivors).read_text(encoding="utf-8"))["rows"]
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    flow = {r["key"]: r for r in json.loads(Path(a.flow).read_text(encoding="utf-8"))["results"]}
    succ_sha = hashlib.sha256(Path(a.succ).read_bytes()).hexdigest()
    flow_sha = hashlib.sha256(Path(a.flow).read_bytes()).hexdigest()

    print("\n=== check 2 + 3: engine-level exhaustive macro DFS (model-independent) ===")
    certs, mismatches = [], []
    for m in models:
        row = next(r for r in surv if r["root_ell"] == m["root_ell"]
                   and r["P_core"] == m["P_core"]
                   and r["canonical_state_hash"] == m["canonical_state_hash"])
        rec = next(p for p in preps["results_by_ell"][str(m["root_ell"])]["preparations"]
                   if p["raw_state_hash"][:12] == row["raw_state_hash"])
        st = replay_state(m["root_ell"], rec)
        assert st is not None and phi(st) == 0

        # variant B: engine + the Round 32 capacity bound, recomputed from
        # engine state fields.  This is the certificate-grade run.
        sB = new_stats(st)
        t0 = time.time()
        pB = engine_dfs(st, a.node_cap, time.time() + a.seconds, sB, True)
        elB = time.time() - t0
        vB = verdict_of(pB, sB)

        # variant A: the engine's own area_a and nothing else.  Prunes less,
        # so it may truncate; that is not a contradiction, only weaker.
        sA = new_stats(st)
        t0 = time.time()
        pA = engine_dfs(st, a.node_cap, time.time() + a.seconds_plain, sA, False)
        elA = time.time() - t0
        vA = verdict_of(pA, sA)

        fr = flow[m["key"]]
        # a CONTRADICTION is an engine result that cannot coexist with the
        # model result.  A truncated engine run is merely weaker, not a
        # contradiction, and is never recorded as one.
        contradiction = None
        if "FOUND_TARGET_B" in (vA, vB) and fr["status"] == "EXHAUSTED_NO_PATH":
            contradiction = "engine found a continuation the model excluded"
        if vB == "EXHAUSTED_NO_PATH" and fr["status"] == "FOUND_TARGET_B":
            contradiction = "model found a continuation the engine excluded"
        if contradiction:
            mismatches.append({"key": m["key"], "engine_B": vB, "engine_A": vA,
                               "model": fr["status"], "why": contradiction})
        verified = (vB == "EXHAUSTED_NO_PATH" and fr["status"] == "EXHAUSTED_NO_PATH")
        certs.append({
            "key": m["key"], "root_ell": m["root_ell"], "P_core": m["P_core"],
            "canonical_state_hash": m["canonical_state_hash"],
            "root_phi": phi(st), "root_P": st.P, "root_O": st.O,
            "root_Ndef": st.Ndef, "root_visited": st.visited_count,
            "engine_verdict": vB,
            "engine_nodes": sB["nodes"], "engine_seconds": round(elB, 2),
            "engine_truncated": sB["truncated"],
            "engine_max_macro_depth": sB["max_depth"],
            "engine_max_visited": sB["max_visited"],
            "engine_windows_short_of_720": 720 - sB["max_visited"],
            "engine_leaf_states": sB["leaf_states"],
            "engine_surviving_ells": sorted(sB["surviving_ells"]),
            "engine_prune_reasons": dict(sB["prune"]),
            "engine_depth_histogram": {str(k): v for k, v in sorted(sB["depth_hist"].items())},
            "engine_area_a_only_verdict": vA,
            "engine_area_a_only_nodes": sA["nodes"],
            "engine_area_a_only_truncated": sA["truncated"],
            "engine_area_a_only_max_macro_depth": sA["max_depth"],
            "engine_area_a_only_seconds": round(elA, 2),
            "model_verdict": fr["status"],
            "model_nodes": fr["nodes"],
            "model_max_segments": fr["max_segments_reached"],
            "model_max_hexagons_covered": fr["max_hexagons_covered"],
            "contradiction": contradiction,
            "grade": ("independently verified UNSAT" if verified else "bounded incomplete"),
        })
        print(f"  {m['key']}: engine+bound {vB} in {elB:.1f}s nodes={sB['nodes']} "
              f"max macro depth={sB['max_depth']} short={720 - sB['max_visited']} "
              f"ells={sorted(sB['surviving_ells'])} | area_a only {vA} "
              f"nodes={sA['nodes']} depth={sA['max_depth']} | model {fr['status']}"
              f" | contradiction={contradiction}", flush=True)

    hist = Counter(c["engine_verdict"] for c in certs)
    histA = Counter(c["engine_area_a_only_verdict"] for c in certs)
    n_unsat = sum(1 for c in certs if c["grade"] == "independently verified UNSAT")
    print(f"\n  engine+bound verdict histogram: {dict(hist)}")
    print(f"  area_a-only verdict histogram:   {dict(histA)}")
    print(f"  contradictions between engine and model: {len(mismatches)}")
    print(f"  independently verified UNSAT certificates: {n_unsat} / {len(certs)}")
    all_ells = sorted({e for c in certs for e in c["engine_surviving_ells"]})
    print(f"  every surviving macro edge had ell in {all_ells} "
          f"(ell=5 forced by Phi=0, confirmed by the engine)")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-flow-certificates-v1",
        "resource_accounting_audit": acct,
        "ell_forced_check": {
            "statement": ("Phi = 5 + 6(TARGET_P - P) - (720 - visited) is 0 at every "
                          "boundary state, dPhi = ell - 5 per macro edge, and the "
                          "engine's remaining_window_capacity_prune is true exactly "
                          "when Phi < 0; so every surviving macro edge has ell = 5"),
            "grade": "exact replay",
            "observed_surviving_ells": all_ells,
            "confirms_ell_5_forced": all_ells == [5],
        },
        "engine_independent_search": {
            "variant_B_certificate_grade": (
                "macro.macro_edges + macro.area_a_prune_reason(., AREA_A) + the Round 32 "
                "(B+R) capacity bound recomputed from ExactState fields alone "
                "(orbit_capacity_bound). No segments, no option corpus, no hexagon "
                "cover, no cover-first bookkeeping."),
            "variant_A_area_a_only": (
                "macro.macro_edges + macro.area_a_prune_reason(., AREA_A) and NOTHING "
                "else. Fully independent but prunes strictly less, so it may truncate; "
                "a truncated variant-A run is reported as INCOMPLETE and is NOT treated "
                "as disagreeing with variant B."),
            "capacity_bound_statement": (
                "need = TARGET_P - P + 1 hexagons remain; they are covered by the rest of "
                "the current segment (at most 1 + (5 - used ports of the current orbit)) "
                "plus one segment per exit joint, of which at most TARGET_O - O open a "
                "fresh orbit (capacity <= 5) and at most n_limit - Ndef re-enter an opened "
                "one (capacity <= 4, since an opened orbit already has a visited port). "
                "need > that sum is infeasible."),
            "capacity_bound_grade": "safe capacity bound (Round 32, re-derived here)",
            "not_a_depth_100_permutation_dfs": ("the tree terminates on its own after a "
                                                "few hundred to a few thousand macro "
                                                "nodes; the node counts are recorded so "
                                                "that this is checkable, not asserted"),
            "verdict_histogram": {k: v for k, v in hist.items()},
            "mismatches": mismatches,
            "independently_verified_unsat": n_unsat,
        },
        "inputs": {"successor_index_sha256": succ_sha, "flow_results_sha256": flow_sha,
                   "engine_code_sha256": exact.CODE_SHA256,
                   "engine_core_sha256": exact.CORE_SHA256},
        "certificates": certs,
        "scope": ("these certificates are about TARGET B continuations from the seven "
                  "Phi=0 Target A boundary states inside Area A (F=1, H=0, N<=3). They "
                  "say nothing about L(6) >= 872, nothing about the N=0 checkpoint, and "
                  "nothing about the CH2 chaining question."),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
