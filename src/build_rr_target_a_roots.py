#!/usr/bin/env python3
"""Round 35, sections 1-7 and 10-12: fixing the 22 incomplete Target A roots.

Round 34 closed Target B for all 18 KNOWN Target A boundary states.  The
bottleneck therefore moved from "can a known boundary continue?" to "is the
list of boundaries complete?".  The concrete gap named in the brief is the
Round 27 long-prefix extension search: 6 FOUND, 22 INCOMPLETE, 0 exhausted,
node cap 8,000.

This module fixes those 22 roots exactly and computes every safe filter the
brief asks for.  It also draws a distinction that turns out to decide the
whole round, so it is stated up front:

  Q1  IS THERE A TARGET A BOUNDARY beyond this root?
      Target A is a LOCAL predicate on one macro edge (second R event,
      F_def=1, H=0, same-component).  It does NOT require the word to
      complete to an NR6 walk.  Round 30 already proved six Target A
      boundaries have no continuation at all and are still Target A.

  Q2  IS THERE A TARGET A BOUNDARY THAT COULD STILL COMPLETE?
      i.e. one from which an Area-A NR6 completion is not already
      arithmetically excluded.

Q2 admits a strong safe prune (the capacity bound below).  Q1 does NOT --
and the difference is not hypothetical: on one of the ell=0 P_core=4 known
boundaries the bound is already negative at the state the R2 edge departs
from, so using it for Q1 would delete that real Target A boundary.  One
counterexample is enough.  That is checked mechanically in
verify_rr_target_a_coverage.py and is why the two questions are answered
separately everywhere in this round.
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


macro = _load("brtar", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
AREA_A = macro.AREA_A
HUB = core.hexagon_id(exact.initial_state().p)
NORB = len(core.E_REPS)
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]
PORT_INDEX = {}
for _q in range(NORB):
    for _ph in range(5):
        PORT_INDEX[PORTS[_q][_ph]] = (_q, _ph)
# section 6: the hand-proved ell=4 terminal geometry names orbit 1 phase 4
COMPLETER_TARGET = (1, 4)

popcount = lambda x: bin(x).count("1")
phi = lambda st: 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count)


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


# --------------------------------------------------------------------------
# section 3: the Target A recognizer, fixed and hashed
# --------------------------------------------------------------------------
TARGET_A_SPEC = {
    "name": "same-component second-R boundary (Area A)",
    "conditions": [
        "the macro edge's joint is an R event (weight 3, no abandonment, no new orbit)",
        "it is the SECOND R event of the word (the root carries exactly one)",
        "the child state has F_def == 1",
        "the child state has H == 0",
        "the R2 source orbit and R2 target orbit lie in the same component of the "
        "orbit/hexagon incidence forest built from the PRE-joint state's orbit_masks",
        "the child state passes area_a_prune_reason(., AREA_A)",
    ],
    "recorded_but_not_required": [
        "chaining (R1 target orbit == R2 source orbit)",
        "abandonment ell (the ell=4 vs ell=0 branch)",
        "hub completer geometry: first edge landing in hexagon 0, target (1,4)",
        "Ndef of the child, which is 2 because an R event costs one N",
        "Phi of the child",
    ],
    "deliberately_NOT_part_of_the_recognizer": [
        "any Target B condition (admissible terminal continuation)",
        "any Target C / NR6 completion condition",
        "the capacity bound of section 5 -- see the Q1/Q2 split",
    ],
}
TARGET_A_SPEC_SHA = sha(TARGET_A_SPEC)


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
                uni(("q", q), ("h", core.hexagon_id(PORTS[q][ph])))
    return par, find


def is_target_a(edge):
    """Section 3 / section 12: the recognizer, plus the MINIMAL ancestry
    decoration it needs.

    The ancestry needed is exactly one boolean -- do the two orbits share a
    component of the forest determined by the pre-joint orbit_masks -- so no
    union-find history is stored.  The forest is a function of the state, so
    the predicate is state-local given that the root carries exactly one R.
    """
    tr = edge.joint
    if joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit) != "R":
        return None
    if not (tr.state.F == 1 and tr.state.H == 0):
        return None
    if macro.area_a_prune_reason(tr.state, AREA_A) is not None:
        return None
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
            "child_phi": phi(tr.state), "child_Ndef": tr.state.Ndef,
            "child_O": tr.state.O, "child_P": tr.state.P,
            "joint": tr.move.label}


# --------------------------------------------------------------------------
# section 5: the capacity bound -- SAFE FOR Q2 ONLY
# --------------------------------------------------------------------------
def capacity_slack(st):
    """Round 32's (B+R) bound re-imported to Phi > 0 states, in the
    pass-start currency (손증명).

    Every macro edge creates exactly one pass-start, so P must climb to
    TARGET_P = 121.  Pass-starts group into SEGMENTS = maximal runs inside
    one E-orbit, and a segment uses at most 5 ports of its orbit (at most 4
    if the orbit was already opened, since it already holds a port).  A new
    segment begins only at an orbit-changing joint, and each of those is:

      * ell=5, weight 3, fresh orbit   -> costs one O   (<= TARGET_O - O)
      * ell=5, weight 3, opened orbit  -> costs one N   (<= n_limit - Ndef)
      * ell<5                          -> costs >= 1 Phi (<= Phi)
      * ell=5, weight 2                -> impossible: g_{w2:10} = E preserves
                                          the orbit
      * weight 2 opening a fresh orbit -> needs an abandonment, so F would
                                          exceed TARGET_F = 1

    Hence future segments <= O_rem + N_rem + Phi, of which at most O_rem are
    fresh, and

        TARGET_P - P  <=  (5 - used ports of the current orbit)
                          + 5*O_rem + 4*(N_rem + Phi).

    Slack = right side minus left side; it is NON-INCREASING along any legal
    walk, dropping by (5 - used) whenever an orbit is left unsaturated.

    SCOPE.  This is a necessary condition for an Area-A NR6 COMPLETION.  It
    is NOT a necessary condition for a Target A boundary, which is a local
    predicate.  Using it to prune Q1 would be unsound.
    """
    q, _ = exact.ORBIT_PHASE[st.p]
    used = popcount(st.orbit_masks[q])
    o_rem = max(exact.TARGET_O - st.O, 0)
    n_rem = max(AREA_A.n_limit - st.Ndef, 0)
    bound = (5 - used) + 5 * o_rem + 4 * (n_rem + phi(st))
    return bound - (exact.TARGET_P - st.P), bound, exact.TARGET_P - st.P


# --------------------------------------------------------------------------
# section 11: orbit/phase reachability, ignoring visited collisions
# --------------------------------------------------------------------------
def build_port_reachability():
    """Over-approximation: from every port, the ports reachable by one macro
    edge rot^ell;joint for any ell in 0..5 and any of the four joints, with
    all visited-collision constraints DROPPED.  Unreachability here is a
    safe prune; reachability proves nothing."""
    succ = {}
    for q in range(NORB):
        for ph in range(5):
            p = PORTS[q][ph]
            out = set()
            for ell in range(6):
                pe = core.compose(p, core.power(core.SIGMA, ell))
                for lbl, mv in mbl.items():
                    if mv.weight < 2:
                        continue
                    out.add(PORT_INDEX[core.word_after(pe, mv.action)])
            succ[(q, ph)] = sorted(out)
    return succ


def bfs_distance(succ, start, target):
    if start == target:
        return 0
    seen, layer, d = {start}, [start], 0
    while layer:
        d += 1
        nxt = []
        for u in layer:
            for v in succ[u]:
                if v == target:
                    return d
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        layer = nxt
    return None


def replay_root(rec):
    st = exact.initial_state()
    for _ in range(rec["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lbl in rec["literal_joint_word"]:
        for _ in range(5):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st


def explosion_profile(st, node_cap):
    """Section 4: why the Round 27 frontier grew, measured per root."""
    fr = deque([(st, 0)])
    seen = {st.stable_key()}
    canon = set()
    exp = 0
    branch, kinds, prunes, r2reason = Counter(), Counter(), Counter(), Counter()
    maxdepth = 0
    fresh_by_depth, dedup_hits = Counter(), 0
    while fr and exp < node_cap:
        cur, d = fr.popleft()
        exp += 1
        maxdepth = max(maxdepth, d)
        n_child = 0
        for e in macro.macro_edges(cur):
            tr = e.joint
            r = macro.area_a_prune_reason(tr.state, AREA_A)
            if r is not None:
                prunes[r] += 1
                continue
            k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other":
                prunes["outside_RR_alphabet"] += 1
                continue
            kinds[k] += 1
            if k == "R":
                v = is_target_a(e)
                r2reason["target_A" if (v and v["same_component"]) else
                          (v["reason"] if v else "failed_FH_or_area_a")] += 1
                continue
            kk = tr.state.stable_key()
            if kk in seen:
                dedup_hits += 1
                continue
            seen.add(kk)
            if tr.new_orbit:
                fresh_by_depth[d + 1] += 1
            n_child += 1
            fr.append((tr.state, d + 1))
        branch[n_child] += 1
    for s in list(seen)[:4000]:
        canon.add(s[0])
    return {
        "expanded": exp, "distinct_raw_states": len(seen),
        "max_r_free_depth_reached": maxdepth,
        "branching_histogram": {str(k): v for k, v in sorted(branch.items())},
        "mean_branching": round(sum(k * v for k, v in branch.items()) / max(sum(branch.values()), 1), 3),
        "event_kind_histogram": dict(kinds),
        "area_a_prune_histogram": dict(prunes),
        "r2_edge_outcome_histogram": dict(r2reason),
        "raw_dedup_hits": dedup_hits,
        "fresh_openings_by_depth": {str(k): v for k, v in sorted(fresh_by_depth.items())},
        "truncated": exp >= node_cap,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--old", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--profile-cap", type=int, default=4000)
    ap.add_argument("--out-roots", default=str(ROOT / "outputs" / "rr_22_incomplete_roots.json"))
    ap.add_argument("--out-pred", default=str(ROOT / "outputs" / "rr_target_a_predecessor_universe.json"))
    a = ap.parse_args()

    pref = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    old = json.loads(Path(a.old).read_text(encoding="utf-8"))
    inc = [r for r in old["results"] if r["status"] == "INCOMPLETE"]
    found = [r for r in old["results"] if r["status"] == "FOUND"]
    print(f"Round 27 recorded {len(found)} FOUND and {len(inc)} INCOMPLETE roots "
          f"(node cap {old['node_cap']}, depth ceiling {old['extension_depth_ceiling']}, "
          f"stop_on_first={old.get('stop_on_first')})")

    succ = build_port_reachability()
    deg = Counter(len(v) for v in succ.values())
    print(f"section 11: over-approximated port successor graph, 720 nodes, "
          f"out-degree histogram {dict(deg)}")

    rows = []
    for r in inc + found:
        rec = pref["prefixes"][r["prefix_index"]]
        st = replay_root(rec)
        slack, bound, need = capacity_slack(st)
        q0, ph0 = exact.ORBIT_PHASE[st.p]
        dist = bfs_distance(succ, (q0, ph0), COMPLETER_TARGET)
        rows.append({
            # ---- section 1 ----
            "prefix_index": r["prefix_index"], "old_status": r["status"],
            "root_ell": rec["root_ell"], "literal_joint_word": rec["literal_joint_word"],
            "symbolic_word": rec["symbolic_word"],
            "first_return_length_L": rec["L"], "return_exponent": rec["return_exponent"],
            "gap_G": rec.get("G"), "r_count": rec["r_count"],
            "f_sym_count": rec["f_sym_count"], "F_def": st.F,
            "phi": phi(st), "O": st.O, "Ndef": st.Ndef, "S": st.S, "D": st.D,
            "P": st.P, "visited_permutations": st.visited_count,
            "current_orbit": q0, "current_phase": ph0,
            "hub_popcount": popcount(st.hex_masks[HUB]),
            "hub_complete": st.hex_masks[HUB] == 63,
            "remaining_R_budget": 2 - rec["r_count"],
            "old_nodes_expanded": r["nodes_expanded"],
            "old_dedup_states": r["dedup_states"],
            "old_r2_boundaries_reached": r["r2_boundaries_reached"],
            "old_truncated_by_node_cap": r["truncated_by_node_cap"],
            "old_truncated_by_ceiling": r["truncated_by_ceiling"],
            # ---- section 2: quotients ----
            "raw_state_hash": sha(st.stable_key())[:16],
            "left_s6_canonical_hash": sha(exact.canonicalize(st).stable_key())[:16],
            "resource_signature": [st.P, st.F, st.S, st.H, st.O, st.D, st.Ndef, phi(st)],
            "decorated_continuation_hash": sha((st.stable_key(), rec["r_count"],
                                                rec["symbolic_word"]))[:16],
            "symbolic_excursion_class": f"L{rec['L']}_exp{rec['return_exponent']}_{rec['symbolic_word']}",
            # ---- sections 5, 7, 10, 11 ----
            "capacity_need": need, "capacity_bound": bound, "capacity_slack": slack,
            "capacity_dead_at_root": slack < 0,
            "min_future_R_events": 1,
            "min_additional_macro_edges_to_target_A": 1,
            "phi_budget_for_short_rotations": phi(st),
            "max_R2_edge_ell_affordable": 5 - phi(st) if phi(st) <= 5 else 0,
            "over_approx_distance_to_orbit1_phase4": dist,
            "orbit1_opened": st.orbit_masks[1] != 0,
        })

    # ---- section 2: quotient collapse ----
    for level, key in (("exact_state", "raw_state_hash"),
                       ("left_s6_canonical", "left_s6_canonical_hash"),
                       ("decorated_continuation", "decorated_continuation_hash"),
                       ("resource_signature", "resource_signature"),
                       ("symbolic_excursion_class", "symbolic_excursion_class")):
        vals = [repr(x[key]) for x in rows if x["old_status"] == "INCOMPLETE"]
        print(f"section 2 quotient of the 22 at level {level:<24}: {len(set(vals))} classes")

    dead = [x for x in rows if x["old_status"] == "INCOMPLETE" and x["capacity_dead_at_root"]]
    alive = [x for x in rows if x["old_status"] == "INCOMPLETE" and not x["capacity_dead_at_root"]]
    print(f"\nsection 5 (Q2 only): {len(dead)} of the 22 roots are capacity-dead AT THE ROOT; "
          f"{len(alive)} survive")
    print("  surviving roots and their slack: "
          + ", ".join(f"{x['prefix_index']}(ell={x['root_ell']},s={x['capacity_slack']})"
                      for x in alive))
    assert all(not x["capacity_dead_at_root"] for x in rows if x["old_status"] == "FOUND"), \
        "the bound must not kill a root that demonstrably reaches Target A"
    print("  sanity: none of the 6 FOUND roots is killed by the bound")

    # ---- section 4 ----
    print(f"\nsection 4: explosion profile (cap {a.profile_cap} nodes per root)")
    for x in rows:
        if x["old_status"] != "INCOMPLETE":
            continue
        rec = pref["prefixes"][x["prefix_index"]]
        x["explosion_profile"] = explosion_profile(replay_root(rec), a.profile_cap)
        p = x["explosion_profile"]
        print(f"  idx={x['prefix_index']:>3} ell={x['root_ell']} mean branching "
              f"{p['mean_branching']:.2f} kinds={p['event_kind_histogram']} "
              f"R2 outcomes={p['r2_edge_outcome_histogram']}")

    causes = Counter(tuple(sorted(x["explosion_profile"]["r2_edge_outcome_histogram"]))
                     for x in rows if x["old_status"] == "INCOMPLETE")
    print(f"  distinct R2-outcome cause signatures among the 22: {len(causes)} -> {dict(causes)}")

    Path(a.out_roots).write_text(json.dumps({
        "schema": "rr-22-incomplete-roots-v1",
        "target_A_recognizer": TARGET_A_SPEC,
        "target_A_recognizer_sha256": TARGET_A_SPEC_SHA,
        "two_questions": {
            "Q1": ("is there a Target A boundary beyond this root? Target A is a LOCAL "
                   "predicate and does not require completability, so the capacity bound "
                   "may NOT be used"),
            "Q2": ("is there a Target A boundary that could still complete to an Area-A "
                   "NR6 walk? the capacity bound is a sound prune here"),
            "why_it_matters": ("Round 30 proved six Target A boundaries have no continuation "
                               "at all and are still Target A; and on one ell=0 P_core=4 "
                               "boundary the bound is already negative at the state its R2 "
                               "edge departs from, so using it for Q1 would delete that "
                               "genuine Target A boundary"),
        },
        "capacity_bound": {
            "statement": capacity_slack.__doc__,
            "grade": "safe capacity bound for Q2 (손증명); 반증됨 as a Q1 prune",
            "monotone": "slack is non-increasing along any legal walk",
        },
        "n_incomplete_roots": len(inc), "n_found_roots": len(found),
        "roots": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")

    Path(a.out_pred).write_text(json.dumps({
        "schema": "rr-target-a-predecessor-universe-v1",
        "sections": "6, 9, 11",
        "hand_proved_terminal_geometry": {
            "completer_target": list(COMPLETER_TARGET),
            "ell4_branch_R2_edge_ell": 0,
            "ell0_branch_R2_edge_ell": 5,
            "second_R_joint_observed": "w3:120 at every one of the 12 known short boundaries",
            "terminal_phi": 0,
            "scope": ("this geometry is the observed normal form of the 18 KNOWN boundaries, "
                      "not a proof that every Target A boundary has it; see the backward "
                      "filter verdict below"),
        },
        "backward_filter_verdict": {
            "usable_as_a_forward_prune": False,
            "grade": "scope correction",
            "why": ("the R2 edge's ell is not fixed across the branches -- it is 0 at all "
                    "nine ell=4 known boundaries and 5 at all three ell=0 ones -- so no "
                    "single predecessor class exists to filter against. The Phi budget "
                    "already encodes the only sound consequence: an R2 edge of length ell "
                    "costs 5-ell of Phi, so a root with Phi = ell_root + 1 can only afford "
                    "R2 edges with ell >= 4 - ell_root."),
            "phi_budget_per_root_class": {str(e): {"root_phi": e + 1,
                                                    "min_affordable_R2_edge_ell": max(4 - e, 0)}
                                          for e in range(5)},
        },
        "port_successor_over_approximation": {
            "nodes": 720,
            "out_degree_histogram": {str(k): v for k, v in sorted(deg.items())},
            "target": list(COMPLETER_TARGET),
            "note": ("collisions dropped, so unreachability would be a safe prune; "
                     "measured distances are small and prune nothing"),
        },
        "distances_to_completer_target": sorted(
            {x["over_approx_distance_to_orbit1_phase4"] for x in rows}),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("\nwrote", a.out_roots)
    print("wrote", a.out_pred)


if __name__ == "__main__":
    main()
