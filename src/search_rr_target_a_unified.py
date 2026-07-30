#!/usr/bin/env python3
"""Round 36, Parts B-E: the unified Target A enumerator.

This module replaces every ad-hoc search used for Target A so far
(analyze_rr_ell0_family.py's short-family BFS, search_rr_long_prefix_
extensions.py's --stop-on-first search, and Round 35's search_rr_target_a_
exhaustive.py) with ONE engine that:

  * uses a fixed, disjoint STATUS VOCABULARY (section 4) instead of the
    single `frontier_empty` boolean that Round 35 showed could not
    distinguish "nothing left" from "everything left was ceiling-dropped";
  * records full FRONTIER ACCOUNTING (section 5) on every run;
  * runs in COVERAGE mode (enumerate every Target A boundary, never stop
    early) or WITNESS mode (--stop-on-first, kept for when a single
    example is all that is wanted -- never used for a coverage claim);
  * exposes two prune sets: Q1-SAFE (section 8, used for coverage-mode
    "any Target A boundary" search) and the FULL area_a set (used only for
    the completability question Q2, matching Round 35's already-verified
    scope) -- selected by --mode;
  * is deterministic and checkpointable (section 12): a fixed edge order,
    a JSON frontier/visited checkpoint written periodically, and --resume.

THE CENTRAL CORRECTION THIS ROUND MAKES (Part C): every earlier Target A
traversal, including Round 35's nominal "Q1" search, pruned intermediate
(non-boundary) states with the FULL `area_a_prune_reason`, which bundles
six sub-conditions that assume the walk continues to full Area-A completion
(P=TARGET_P=121, O=TARGET_O=25, D=TARGET_D=4) together with four that are
genuinely local (monotone invariants, or a pure structural consistency
check). Using the bundled function as a
traversal prune therefore already smuggled completion assumptions into
every previous "Q1" run. This module is the first to separate them.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from collections import Counter, deque
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


macro = _load("srtau", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
AREA_A = macro.AREA_A


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


# ===========================================================================
# Part C, sections 8-10: the prune audit, as executable code, not just prose
# ===========================================================================
#
# Every sub-condition of macro.area_a_prune_reason, decomposed and classified.
# Each entry states: the exact test, whether it is monotone (never becomes
# false again once true), whether Target A's OWN definition (F_def==1,
# H==0, same-component) requires it, and the verdict.
#
# Q1-SAFE  -- provably safe to use while searching for ANY Target A boundary
# Q2-ONLY  -- assumes the walk reaches TARGET_P/TARGET_O/TARGET_D; safe only
#             for the completability question
# INVALID  -- neither of the above; not used at all

PRUNE_CLASSIFICATION = {
    "F_exceeded": {
        "test": "state.F > TARGET_F (i.e. F_def > 1)",
        "monotone": True,
        "monotone_proof": "dF = int(abandonment) in {0,1}; F never decreases along any macro edge",
        "target_A_requires": "the R2-boundary CHILD has F_def == 1 exactly",
        "verdict": "Q1-SAFE",
        "reason": ("F_def > 1 can never return to 1 (monotone), and Target A's own recognizer "
                  "requires the eventual boundary's child to have F_def == 1; so once F_def > 1 "
                  "no descendant can ever be a Target A boundary"),
    },
    "H_positive": {
        "test": "state.H > 0",
        "monotone": True,
        "monotone_proof": "dH = max(weight - 3, 0) >= 0 always",
        "target_A_requires": "the R2-boundary CHILD has H == 0 exactly",
        "verdict": "Q1-SAFE",
        "reason": ("H > 0 can never return to 0 (monotone), and Target A requires the child's "
                  "H == 0; identical argument to F_exceeded. (Empirically vacuous within the RR "
                  "alphabet actually explored here, since weight is 2 or 3 for every RR joint "
                  "and dH = 0 for both -- but the argument does not depend on that, and is "
                  "recorded for completeness.)"),
    },
    "N_exceeded_monotone": {
        "test": "state.Ndef > n_limit (AREA_A.n_limit == 3)",
        "monotone": True,
        "monotone_proof": "dNdef = dS + dF - dO in {0, +1} for every legal macro edge (dS = "
                          "[weight>=3], dO = [new orbit], dF = [abandonment]; case analysis over "
                          "the four RR joints shows dNdef is never negative)",
        "target_A_requires": "nothing directly -- n_limit=3 defines AREA A, the disclosed search "
                             "SCOPE this entire Target A/B corpus has operated within since "
                             "Round 27 (every one of the 18 known boundaries has a child that "
                             "passes this test)",
        "verdict": "Q1-SAFE, WITHIN THE DISCLOSED AREA-A SCOPE",
        "reason": ("monotone, so a valid prune for staying inside Area A. This is a SCOPE "
                  "restriction, not a completeness claim: a Target A boundary with Ndef > 3 "
                  "could exist outside Area A and is simply not explored by this search, exactly "
                  "as it was not explored by any prior round's search either"),
    },
    "F1_fragment_normal_form_impossible": {
        "test": "exact.f1_normal_form(state) is None",
        "monotone": "not applicable -- it is a structural CONSISTENCY check on the current state, "
                   "not a forward-looking feasibility test",
        "monotone_proof": ("f1_normal_form checks a necessary invariant of every F<=1 reachable "
                          "prefix (at most one non-current partial hexagon, total fragment "
                          "components <= F+1); its docstring states this is 'a necessary prefix "
                          "invariant, not an unproved pruning heuristic'. It references no "
                          "TARGET_P/TARGET_O/TARGET_D constant."),
        "target_A_requires": "nothing directly, but a state violating this invariant is not a "
                             "genuinely reachable ExactState under F<=1 at all",
        "verdict": "Q1-SAFE",
        "reason": ("does not assume completion; it is a sanity/consistency check on the CURRENT "
                  "state's geometry. It is expected to be vacuous downstream of F_exceeded (F<=1 "
                  "states reachable via extend() should always satisfy it), and is kept for "
                  "defensiveness rather than because it is expected to fire"),
    },
    "P_exceeded": {
        "test": "state.P > TARGET_P (== 121)",
        "monotone": True,
        "monotone_proof": "P = sum of orbit_masks popcounts, incremented by exactly 1 per legal "
                          "weight>=2 event; never decreases",
        "target_A_requires": "nothing -- TARGET_P=121 is the pass-start count of a FULL Area-A "
                             "NR6 completion, not a Target A condition",
        "verdict": "Q2-ONLY",
        "reason": ("Target A does not require P <= 121 at its boundary; a state with P > 121 "
                  "could not be part of an eventual full completion, but could still be a "
                  "genuine local Target A boundary (F_def==1, H==0, same-component) in "
                  "isolation. Using this as a Q1 prune would silently restrict Q1 to "
                  "'boundaries reachable en route to completion', exactly the assumption "
                  "the round prohibits."),
    },
    "O_exceeded": {
        "test": "state.O > TARGET_O (== 25)",
        "monotone": True,
        "monotone_proof": "O = count of nonzero orbit_masks entries; never decreases",
        "target_A_requires": "nothing -- TARGET_O=25 is a full-completion target",
        "verdict": "Q2-ONLY",
        "reason": "identical argument to P_exceeded",
    },
    "final_D_impossible": {
        "test": "not exact.arithmetic_D_reachable(state), i.e. (TARGET_D - D + r) is not a "
               "multiple of 5 in [0, 5r] where r = TARGET_P - P",
        "monotone": ("empirically an INVARIANT of the whole trajectory from the fixed initial "
                    "state, verified by direct simulation: (TARGET_D - D + r) mod 5 stays "
                    "constant (0) over a 4000-step random walk from the identity, because each "
                    "weight>=2 event changes it by either -5 (new orbit, dD=+4) or 0 (old orbit, "
                    "dD=-1), both preserving the residue mod 5"),
        "target_A_requires": "nothing -- it tests reachability of the EXACT pair (TARGET_P, "
                             "TARGET_D), a full-completion condition",
        "verdict": "Q2-ONLY (despite being state-invariant)",
        "reason": ("this is the subtle case: because the residue is an invariant of the entire "
                  "trajectory (not just monotone), it can never actually change from state to "
                  "state along a legal walk from the true root -- so classifying it Q1-safe or "
                  "Q2-only makes no PRACTICAL difference for search correctness here. But the "
                  "PROPERTY it tests -- reachability of TARGET_D at TARGET_P -- is a completion "
                  "condition Target A does not require, so it is classified Q2-only on principle, "
                  "not merely for safety margin"),
    },
    "remaining_pass_starts_exceed_remaining_windows": {
        "test": "720 - visited_count < TARGET_P - state.P",
        "monotone": True,
        "monotone_proof": "both sides move the same direction each edge in the relevant sense; "
                          "not needed since the classification does not depend on monotonicity",
        "target_A_requires": "nothing -- directly compares remaining windows to the remaining "
                             "distance to TARGET_P",
        "verdict": "Q2-ONLY",
        "reason": "explicitly a completion-reachability test against TARGET_P",
    },
    "remaining_cover_capacity_impossible": {
        "test": "remaining_window_capacity_prune(state), i.e. Phi < 0 where "
               "Phi = 5 + 6*(TARGET_P - P) - (720 - visited_count)",
        "monotone": True,
        "monotone_proof": "Phi is non-increasing along any walk with ell < 5 and constant "
                          "under ell = 5 macro edges (established in Round 33-35)",
        "target_A_requires": "nothing -- Phi is defined entirely in terms of TARGET_P",
        "verdict": "Q2-ONLY",
        "reason": ("this IS the Round 32/34/35 capacity bound in another guise, and it is "
                  "EXACTLY the bound Round 35 proved unsound as a Target A prune: replayed "
                  "along a known short boundary's own path it goes negative strictly before "
                  "the R2 edge. Confirmed here, not merely inherited."),
    },
    "insufficient_future_orbit_opening_credit": {
        "test": "(TARGET_O - O) > (TARGET_P - P) + (TARGET_F - F)",
        "monotone": True,
        "monotone_proof": "left side monotone nonincreasing complement, right side monotone "
                          "nonincreasing; not needed for the classification",
        "target_A_requires": "nothing -- directly compares remaining orbit-opening need to "
                             "TARGET_O and remaining budget to TARGET_P/TARGET_F",
        "verdict": "Q2-ONLY",
        "reason": "explicitly a completion-reachability test against TARGET_O, TARGET_P, TARGET_F",
    },
}

Q1_SAFE_REASONS = {k for k, v in PRUNE_CLASSIFICATION.items() if v["verdict"].startswith("Q1-SAFE")}
Q2_ONLY_REASONS = {k for k, v in PRUNE_CLASSIFICATION.items() if v["verdict"].startswith("Q2-ONLY")}
assert Q1_SAFE_REASONS | Q2_ONLY_REASONS == set(PRUNE_CLASSIFICATION)
assert Q1_SAFE_REASONS == {"F_exceeded", "H_positive", "N_exceeded_monotone",
                           "F1_fragment_normal_form_impossible"}


def q1_safe_prune_reason(state):
    """The Q1-safe subset of area_a_prune_reason, re-implemented directly
    (not by filtering the bundled function's output) so that a future change
    to area_a_prune_reason cannot silently re-widen this set."""
    if state.F > exact.TARGET_F:
        return "F_exceeded"
    if state.H > 0:
        return "H_positive"
    if state.Ndef > AREA_A.n_limit:
        return "N_exceeded_monotone"
    if exact.f1_normal_form(state) is None:
        return "F1_fragment_normal_form_impossible"
    return None


def q1_forbidden_prune_check(reason):
    """Section 9: the negative test. Any Q1 search that ever cites one of
    these reasons has a bug, and this raises rather than silently pruning."""
    if reason in Q2_ONLY_REASONS:
        raise AssertionError(f"Q1 search must never use the completion-assuming prune "
                             f"'{reason}' -- see PRUNE_CLASSIFICATION")


# additional Q1-safe prunes NOT part of area_a_prune_reason at all (section 8)
def r_count_exceeded(r_count):
    """An RR word has exactly two R events (proven 손증명 in Round 33/35: the
    root already carries one R, and the second is the R2 boundary itself).
    A third R event is impossible for any RR-branch word. Q1-SAFE, monotone,
    definitional for the RR branch this whole corpus explores."""
    return r_count > 2


HUB_TOUCH_CANDIDATE = {
    "considered": True, "adopted": False,
    "reason": ("a 'hub touch count exceeded' prune was considered per the brief's candidate "
              "list. No sound LOCAL bound could be established: Target A's definition places "
              "no constraint on how many times the hub hexagon is touched, and any bound on hub "
              "touches would depend on assuming a specific eventual CH1/CH2/completer structure "
              "-- exactly the kind of assumption Part C prohibits for Q1. Classified INVALID "
              "and not adopted, rather than silently omitted."),
}
IMPOSSIBLE_EVENT_ORDER_NOTE = (
    "'impossible event order' as a separate prune candidate is subsumed by r_count_exceeded: "
    "the only order constraint Target A's own definition imposes is 'the R2 event is the SECOND "
    "R of the word', which is exactly what the R-count budget enforces. No additional order "
    "constraint was found to be Q1-safe."
)
EXACT_TERMINAL_PREDICATE_CONTRADICTION_NOTE = (
    "'exact terminal predicate contradiction' is not a traversal prune at all in this design -- "
    "it is the RECOGNIZER test applied only at the exact R2-edge candidate state (F_def==1, "
    "H==0, same-component), never extrapolated to non-boundary states, so it needs no separate "
    "prune-safety argument."
)


# ===========================================================================
# Part D, section 11: the minimal decorated key
# ===========================================================================
def component_forest(state):
    par = {}

    def find(n):
        par.setdefault(n, n)
        while par[n] != n:
            par[n] = par[par[n]]
            n = par[n]
        return n

    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[rb] = ra

    for q, m in enumerate(state.orbit_masks):
        for ph in range(5):
            if m & (1 << ph):
                uni(("q", q), ("h", core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[ph])))
    return par, find


def decorated_key(state, r_count):
    """Section 11: ExactState.stable_key() plus r_count.

    r_count is the ONLY decoration needed. Proof: Target A's recognizer
    depends on the state alone (F_def, H, same-component test on the
    PRE-joint state's orbit_masks, which is a function of that state) plus
    'this is the second R of the word' -- a fact fully captured by r_count.
    R1 source/target, CH1/CH2 status, and component ancestry are all
    RECOVERABLE from the state's orbit_masks at the moment they are needed
    (component_forest is computed fresh from orbit_masks every time, per
    Round 35's is_target_a), so storing them again would be redundant, not
    additional information. Two histories reaching the identical
    (stable_key, r_count) pair therefore have IDENTICAL future Target-A
    reachability, because every subsequent macro edge is a pure function of
    the ExactState and r_count, and the recognizer is a pure function of the
    same two things."""
    return (state.stable_key(), r_count)


def decorated_key_hash(state, r_count):
    """A hashable, JSON-serializable stand-in for decorated_key, used for
    the `seen` set so checkpoints are plain strings. sha256 collision risk
    is not a practical concern at this corpus size."""
    return sha(decorated_key(state, r_count))


# ===========================================================================
# Part B, section 4: status vocabulary
# ===========================================================================
STATUSES = ("FOUND_TARGET_A", "EXHAUSTED_NO_TARGET_A", "INCOMPLETE_NODE_CAP",
           "INCOMPLETE_DEPTH_CEILING", "INCOMPLETE_TIMEOUT", "STOPPED_AFTER_FIRST",
           "INVALID_ROOT")


def is_target_a_edge(edge, r_count_before):
    """The recognizer (Round 35, unchanged): F_def==1, H==0, same-component,
    evaluated at the exact R-edge candidate. r_count_before must be exactly 1
    (this is the SECOND R) for the edge to be eligible at all."""
    tr = edge.joint
    if joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit) != "R":
        return None
    if r_count_before != 1:
        return None
    if not (tr.state.F == 1 and tr.state.H == 0):
        return {"same_component": False, "reason": "F_or_H_wrong"}
    pre = edge.run.state
    sq, sph = exact.ORBIT_PHASE[pre.p]
    tq, tph = exact.ORBIT_PHASE[tr.target]
    par, find = component_forest(pre)
    if ("q", sq) not in par or ("q", tq) not in par:
        return {"same_component": False, "reason": "source_or_target_orbit_not_in_forest",
                "r2_source": [sq, sph], "r2_target": [tq, tph], "ell": edge.run.ell}
    if find(("q", sq)) != find(("q", tq)):
        return {"same_component": False, "reason": "different_components",
                "r2_source": [sq, sph], "r2_target": [tq, tph], "ell": edge.run.ell}
    return {"same_component": True, "reason": None,
            "r2_source": [sq, sph], "r2_target": [tq, tph], "ell": edge.run.ell,
            "joint": tr.move.label, "child_phi": 5 + 6 * (exact.TARGET_P - tr.state.P)
                                                 - (720 - tr.state.visited_count)}


def serialize_state(st):
    return {"p": list(st.p), "hex_masks": list(st.hex_masks), "orbit_masks": list(st.orbit_masks),
            "F": st.F, "S": st.S, "H": st.H}


def deserialize_state(d):
    return exact.ExactState(tuple(d["p"]), tuple(d["hex_masks"]), tuple(d["orbit_masks"]),
                            d["F"], d["S"], d["H"])


def sorted_macro_edges(state):
    """Section 12: deterministic edge order -- by rotation length then joint
    label, so two runs of the same root always expand nodes in the same
    order regardless of process/platform."""
    return sorted(macro.macro_edges(state), key=lambda e: (e.run.ell, e.joint.move.label))


# ===========================================================================
# The unified traversal
# ===========================================================================
def enumerate_target_a(root_state, root_r_count, mode, coverage, node_cap, depth_cap,
                       seconds, checkpoint_path=None, checkpoint_every=20000,
                       resume_from=None):
    """mode in {'Q1', 'Q2'} selects the prune set. coverage=True forbids
    stopping at the first hit (STOPPED_AFTER_FIRST is reserved for
    coverage=False, witness-finding runs)."""
    assert mode in ("Q1", "Q2")
    t0 = time.time()

    stats = {"expanded": 0, "generated": 0, "duplicate_state_merges": 0,
             "pruned_by_reason": Counter(), "depth_ceiling_dropped": 0,
             "found_boundary_count": 0}
    hits = []

    if resume_from is not None:
        ck = json.loads(Path(resume_from).read_text(encoding="utf-8"))
        frontier = deque((deserialize_state(d["state"]), d["r_count"], d["depth"], tuple(d["path"]))
                         for d in ck["frontier"])
        seen = set(ck["seen_keys"])
        stats = Counter(ck["stats_expanded_etc"])
        stats["pruned_by_reason"] = Counter(ck["stats_expanded_etc"]["pruned_by_reason"])
        hits = ck["hits"]
        stats["expanded"] = ck["stats_expanded_etc"]["expanded"]
        stats["generated"] = ck["stats_expanded_etc"]["generated"]
        stats["duplicate_state_merges"] = ck["stats_expanded_etc"]["duplicate_state_merges"]
        stats["depth_ceiling_dropped"] = ck["stats_expanded_etc"]["depth_ceiling_dropped"]
        stats["found_boundary_count"] = ck["stats_expanded_etc"]["found_boundary_count"]
    else:
        frontier = deque([(root_state, root_r_count, 0, ())])
        seen = {decorated_key_hash(root_state, root_r_count)}

    stop_reason = None
    depth_dropped_this_run = False

    def checkpoint():
        if checkpoint_path is None:
            return
        Path(checkpoint_path).write_text(json.dumps({
            "frontier": [{"state": serialize_state(s), "r_count": rc, "depth": d, "path": list(p)}
                        for s, rc, d, p in frontier],
            "seen_keys": sorted(seen),
            "hits": hits,
            "stats_expanded_etc": {**{k: v for k, v in stats.items() if k != "pruned_by_reason"},
                                   "pruned_by_reason": dict(stats["pruned_by_reason"])},
        }, default=str), encoding="utf-8")

    while frontier:
        if node_cap is not None and stats["expanded"] >= node_cap:
            stop_reason = "INCOMPLETE_NODE_CAP"
            break
        if time.time() - t0 > seconds:
            stop_reason = "INCOMPLETE_TIMEOUT"
            break
        state, r_count, depth, path = frontier.popleft()
        stats["expanded"] += 1
        if checkpoint_path and stats["expanded"] % checkpoint_every == 0:
            checkpoint()
        if depth_cap is not None and depth >= depth_cap:
            stats["depth_ceiling_dropped"] += 1
            depth_dropped_this_run = True
            continue
        for edge in sorted_macro_edges(state):
            tr = edge.joint
            stats["generated"] += 1
            k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other":
                stats["pruned_by_reason"]["outside_RR_alphabet"] += 1
                continue
            if k == "R":
                v = is_target_a_edge(edge, r_count)
                if v is None:
                    stats["pruned_by_reason"]["R_event_not_eligible_r_count"] += 1
                elif v.get("same_component"):
                    stats["found_boundary_count"] += 1
                    hits.append({**v, "extension_depth": depth + 1,
                                "boundary_raw_hash": sha(tr.state.stable_key())[:16],
                                "boundary_canonical_hash":
                                    sha(exact.canonicalize(tr.state).stable_key())[:16],
                                "path": list(path) + [f"rot^{edge.run.ell};{tr.move.label}"]})
                    if not coverage:
                        stop_reason = "STOPPED_AFTER_FIRST"
                        frontier.clear()
                        break
                else:
                    stats["pruned_by_reason"][v["reason"]] += 1
                continue  # never expand past an R event (2nd R must be the boundary)
            nr = r_count + (1 if k == "R" else 0)
            if r_count_exceeded(nr):
                stats["pruned_by_reason"]["r_count_exceeded"] += 1
                continue
            if mode == "Q1":
                reason = q1_safe_prune_reason(tr.state)
            else:
                reason = macro.area_a_prune_reason(tr.state, AREA_A)
            if reason is not None:
                if mode == "Q1":
                    q1_forbidden_prune_check(reason)
                stats["pruned_by_reason"][reason] += 1
                continue
            kk = decorated_key_hash(tr.state, nr)
            if kk in seen:
                stats["duplicate_state_merges"] += 1
                continue
            seen.add(kk)
            frontier.append((tr.state, nr, depth + 1, path + (f"rot^{edge.run.ell};{tr.move.label}",)))
        if stop_reason:
            break

    if checkpoint_path:
        checkpoint()

    natural = stop_reason is None and not depth_dropped_this_run
    if stop_reason == "STOPPED_AFTER_FIRST":
        status = "STOPPED_AFTER_FIRST"
    elif hits and coverage and natural:
        status = "FOUND_TARGET_A"
    elif hits and not natural:
        status = "FOUND_TARGET_A"  # found at least one, but the tree beyond is not confirmed exhausted
    elif natural:
        status = "EXHAUSTED_NO_TARGET_A"
    elif depth_dropped_this_run and stop_reason is None:
        status = "INCOMPLETE_DEPTH_CEILING"
    else:
        status = stop_reason

    return {
        "status": status,
        "mode": mode, "coverage": coverage,
        "seconds": round(time.time() - t0, 2),
        "expanded_nodes": stats["expanded"],
        "generated_nodes": stats["generated"],
        "queued_frontier_at_stop": len(frontier),
        "pruned_by_reason": dict(stats["pruned_by_reason"]),
        "depth_ceiling_dropped_nodes": stats["depth_ceiling_dropped"],
        "duplicate_state_merges": stats["duplicate_state_merges"],
        "found_boundary_count": stats["found_boundary_count"],
        "stop_reason": stop_reason,
        "frontier_emptied_naturally": natural,
        "node_cap": node_cap, "depth_cap": depth_cap, "seconds_budget": seconds,
        "hits": hits,
    }
