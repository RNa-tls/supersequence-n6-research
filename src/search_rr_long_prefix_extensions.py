#!/usr/bin/env python3
"""Round 27, sections 3, 5, 9: targeted exact extension search to Target A.

TARGET A, fixed exactly against the project's existing definition (the
same predicate analyze_rr_ell0_family.py uses to collect same-component
R2 boundaries):

    a macro-edge whose joint is the SECOND R event of the word, whose
    resulting state has F_def == 1 and H == 0, and at which the R2 source
    orbit and the R2 target orbit lie in the SAME component of the
    orbit/hexagon incidence forest built from orbit_masks.

Target B (an admissible terminal continuation after that boundary) and
Target C (a full NR6 completion) are NOT attempted here and no claim is
made about them.

The search runs from the 28 long-excursion prefixes that survive the R
budget (a prefix strictly before R2 may contain at most one R -- 손증명,
see build_rr_long_excursion_roots.py).  Each of those has exactly one R
already, so the NEXT R event in any extension is R2 by construction: the
search explores only zero-charge edges (E and F) and evaluates every R
edge as a candidate R2 boundary without expanding past it.  That makes
the frontier finite in a way a general RR search is not, and it is why
this is a targeted analysis rather than a restarted global search.

Only SAFE prunes are used (section 5).  Every prune below is either the
engine's own legality (a state that does not exist) or a monotone budget
that can never be repaid:

  * exact.extend returns None      -- the target permutation is already
                                      visited.  State-local, exact,
                                      completeness-preserving.
  * area_a_prune_reason            -- the project's necessary-condition
                                      prune.  History-independent, applied
                                      to the child state only.
  * a third R                      -- an RR word has exactly two R events.
                                      Definitional, 손증명.

No empirical or heuristic prune is used.  A node cap is NEVER a proof
condition: a root is reported EXHAUSTED_IMPOSSIBLE only when its frontier
empties naturally, and INCOMPLETE otherwise.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, deque
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


macro = _load("srlpe", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


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


def replay_state(rec):
    st = exact.initial_state()
    for _ in range(rec["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lbl in rec["literal_joint_word"]:
        for _ in range(5):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st


def search(rec, ceiling, node_cap, stop_on_first=False):
    """Returns FOUND / EXHAUSTED_IMPOSSIBLE / INCOMPLETE with evidence."""
    start = replay_state(rec)
    r1t = rec["r1_target_orbit"]
    frontier = deque([(start, 0, ())])
    seen = {(start.stable_key(), 0)}
    nodes = 0
    truncated_by_ceiling = False
    truncated_by_cap = False
    r2_boundaries = 0
    same_component_hits = []
    reasons = Counter()
    while frontier:
        if node_cap is not None and nodes >= node_cap:
            truncated_by_cap = True
            break
        st, d, trace = frontier.popleft()
        nodes += 1
        if d >= ceiling:
            truncated_by_ceiling = True
            continue
        for edge in macro.macro_edges(st):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                reasons["area_a"] += 1
                continue
            k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other":
                reasons["outside_model"] += 1
                continue
            pre = edge.run.state
            sq, sph = exact.ORBIT_PHASE[pre.p]
            tq, tph = exact.ORBIT_PHASE[tr.target]
            step = {"label": f"rot^{edge.run.ell};{tr.move.label}", "kind": k,
                    "src": [sq, sph], "tgt": [tq, tph],
                    "tgt_hex": core.hexagon_id(tr.target)}
            if k == "R":
                # this is the SECOND R of the word: a candidate R2 boundary
                if not (tr.state.F == 1 and tr.state.H == 0):
                    reasons["r2_boundary_F_or_H_wrong"] += 1
                    continue
                r2_boundaries += 1
                parent, find = component_roots(pre)
                sr = find(("q", sq)) if ("q", sq) in parent else None
                tg = find(("q", tq)) if ("q", tq) in parent else None
                if sr is not None and sr == tg:
                    same_component_hits.append({
                        "extension_length": d + 1,
                        "extension_trace": list(trace) + [step],
                        "r1_target_orbit": r1t,
                        "r2_source_orbit": sq, "r2_source_phase": sph,
                        "r2_target_orbit": tq, "r2_target_phase": tph,
                        "chaining": r1t == sq,
                        "post_r2_state_hash": state_hash(tr.state),
                        "phi": 5 + 6 * (exact.TARGET_P - tr.state.P)
                               - (720 - tr.state.visited_count),
                    })
                    if stop_on_first:
                        frontier.clear()
                        break
                else:
                    reasons["r2_boundary_not_same_component"] += 1
                continue  # never expand past R2
            key = (tr.state.stable_key(), d + 1)
            if key in seen:
                reasons["dedup"] += 1
                continue
            seen.add(key)
            frontier.append((tr.state, d + 1, trace + (step,)))
    if same_component_hits:
        status = "FOUND"
    elif truncated_by_cap or truncated_by_ceiling:
        status = "INCOMPLETE"
    else:
        status = "EXHAUSTED_IMPOSSIBLE"
    return {
        "status": status,
        "nodes_expanded": nodes,
        "dedup_states": len(seen),
        "frontier_emptied_naturally": not (truncated_by_cap or truncated_by_ceiling),
        "truncated_by_ceiling": truncated_by_ceiling,
        "truncated_by_node_cap": truncated_by_cap,
        "r2_boundaries_reached": r2_boundaries,
        "same_component_witnesses": same_component_hits[:20],
        "n_same_component_witnesses": len(same_component_hits),
        "prune_reason_histogram": dict(reasons),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--ceiling", type=int, default=12)
    ap.add_argument("--node-cap", type=int, default=None)
    ap.add_argument("--stop-on-first", action="store_true",
                    help="return as soon as one Target A witness is found; makes FOUND "
                         "cheap and leaves only the undecided roots for the full run")
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    a = ap.parse_args()

    data = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    idx = data["r_budget_obstruction"]["surviving_indices"]
    recs = [data["prefixes"][i] for i in idx]
    print(f"Target A search over {len(recs)} surviving prefixes "
          f"(extension depth ceiling {a.ceiling}, node cap {a.node_cap})")

    results, status_hist = [], Counter()
    for n, rec in enumerate(recs):
        r = search(rec, a.ceiling, a.node_cap, a.stop_on_first)
        status_hist[r["status"]] += 1
        results.append({
            "prefix_index": idx[n], "root_ell": rec["root_ell"],
            "literal_joint_word": rec["literal_joint_word"],
            "symbolic_word": rec["symbolic_word"], "L": rec["L"],
            "return_exponent": rec["return_exponent"],
            "f_sym_count": rec["f_sym_count"], "r_count": rec["r_count"],
            **r,
        })
        print(f"  [{n+1:>2}/{len(recs)}] ell={rec['root_ell']} L={rec['L']} "
              f"exp={rec['return_exponent']} {rec['symbolic_word']}  -> {r['status']} "
              f"(nodes={r['nodes_expanded']}, R2 boundaries={r['r2_boundaries_reached']}, "
              f"same-comp={r['n_same_component_witnesses']})")

    print(f"\nstatus histogram: {dict(status_hist)}")
    found = [r for r in results if r["status"] == "FOUND"]
    if found:
        best = min(found, key=lambda r: min(w["extension_length"]
                                            for w in r["same_component_witnesses"]))
        m = min(w["extension_length"] for w in best["same_component_witnesses"])
        print(f"\nMINIMAL successful extension: prefix L={best['L']} "
              f"exponent={best['return_exponent']} symbolic={best['symbolic_word']}")
        print(f"   extension length {m} macro-edges after the prefix")

    rep = {
        "schema": "rr-long-prefix-extension-results-v1",
        "target_A_definition": (
            "a macro-edge whose joint is the SECOND R event of the word, whose child "
            "state has F_def == 1 and H == 0, and at which the R2 source orbit and R2 "
            "target orbit share a component of the orbit/hexagon incidence forest built "
            "from orbit_masks -- the same predicate analyze_rr_ell0_family.py uses"),
        "targets_B_and_C": "not attempted; no claim is made about them",
        "safe_prunes": [
            {"prune": "exact.extend returns None", "statement": "target permutation already visited",
             "state_local": True, "history_dependent": False, "completeness_preserving": True,
             "proof": "the engine refuses to revisit a permutation; such a state does not exist"},
            {"prune": "area_a_prune_reason(child, AREA_A)", "statement": "project necessary condition",
             "state_local": True, "history_dependent": False, "completeness_preserving": True,
             "proof": "necessary condition on the child state; used identically in every round"},
            {"prune": "a third R event", "statement": "an RR word has exactly two R events",
             "state_local": False, "history_dependent": True, "completeness_preserving": True,
             "proof": "definitional for RR; 손증명"},
        ],
        "no_empirical_prune_used": True,
        "node_cap_is_not_a_proof_condition": (
            "a root is EXHAUSTED_IMPOSSIBLE only when its frontier empties naturally; "
            "any truncation yields INCOMPLETE"),
        "extension_depth_ceiling": a.ceiling,
        "node_cap": a.node_cap,
        "stop_on_first": a.stop_on_first,
        "status_histogram": dict(status_hist),
        "grade": "exact exhaustive search where frontier_emptied_naturally, else bounded incomplete",
        "results": results,
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False,
                                         default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
