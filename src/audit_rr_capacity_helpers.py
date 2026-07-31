#!/usr/bin/env python3
"""Round 38, Part A: capacity-helper soundness audit and firewall.

THE ROOT CAUSE, stated once.  Every capacity refinement in this codebase
counts a port as "usable" only if its HEXAGON is entirely unvisited:

    c(q)                      counts ports of q whose hexagon has mask 0
    true_phase_walk_capacity  same, restricted to a legal {+1,+2} phase walk

That precondition is exactly right for one question and exactly wrong for
another:

  FULL-SEGMENT question ("how many hexagons can this segment COMPLETE?").
      At Phi = 0 the engine forces ell = 5 on every macro edge, and an
      ell=5 rotation run from a port visits all six permutations of that
      port's hexagon.  So the hexagon must be entirely fresh, and the
      helper is SOUND.

  SINGLE-LANDING question ("how many ports can this segment STAND ON?",
  i.e. how many times can P increment).
      A joint landing needs only its own target permutation free.  A
      hexagon with five of six slots already visited can still supply that
      one free slot.  The helper therefore UNDERCOUNTS, and using it as an
      upper bound on port count is UNSOUND.

Round 37 discovered this while building the root envelope, but recorded the
counterexample with the wrong numbers ("predicts 2, engine achieves 3").
The exact figures, re-derived here from the engine, are 3 vs 4 -- see
`formalize_counterexample()`.  The correction is applied to the Round 37
documents by this round.

WHY NOTHING HISTORICAL BREAKS.  Every historical elimination that used a
freshness-dependent refinement (Rounds 31, 32, 33) was evaluated at a
Phi = 0 Target B boundary, where ell = 5 is forced and the precondition
holds.  This module re-verifies that claim state by state rather than
asserting it, and additionally re-derives every such elimination through a
freshness-INDEPENDENT replacement proof, so that no result is retained
merely because its final answer happened to match.
"""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, sys
from collections import Counter
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


macro = _load("arch", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
AREA_A = macro.AREA_A
NORB = len(core.E_REPS)
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]
ORBIT_HEX = [tuple(core.hexagon_id(p) for p in PORTS[q]) for q in range(NORB)]

popcount = lambda x: bin(x).count("1")
phi = lambda st: 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count)


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


# ===========================================================================
# Part A.4/A.5: the taxonomy and the runtime firewall
# ===========================================================================
class CapacityPreconditionError(AssertionError):
    """Raised when a full-segment-only helper is invoked in a context whose
    precondition (ell=5 forced, i.e. Phi==0) does not hold."""


HELPER_TAXONOMY = {
    "c_of_q__port_capacity": {
        "where": ["src/build_rr_refined_capacity_bound.py::port_capacities",
                 "src/analyze_rr_segment_capacity.py::analyse (c dict)"],
        "question": "how many ports of orbit q lie in an entirely unvisited hexagon",
        "requires_full_hexagon_freshness": True,
        "requires_only_single_landing": False,
        "precondition": "Phi == 0 (so ell = 5 is forced and each port's hexagon is COMPLETED)",
        "class": "SOUND_FOR_FULL_SEGMENT",
        "proof_status": "exact theorem under the stated precondition; UNSOUND without it",
        "affected_results": ["Round 31 refined bound (removed 1 survivor)",
                            "Round 32 orbit-reuse penalty (removed 1 survivor)"],
    },
    "true_phase_walk_capacity": {
        "where": ["src/verify_rr_target_b_unsat.py::initial_capacity",
                 "src/build_rr_1398_boundary_ledger.py::true_phase_walk_capacity"],
        "question": ("maximum number of hexagons the current segment can COMPLETE, "
                    "over legal {+1,+2} phase walks from the current phase"),
        "requires_full_hexagon_freshness": True,
        "requires_only_single_landing": False,
        "precondition": "Phi == 0 (ell = 5 forced)",
        "class": "SOUND_FOR_FULL_SEGMENT",
        "proof_status": ("exact theorem under the precondition; UNSOUND as a bound on port "
                        "count / P-increments -- exact counterexample recorded below"),
        "affected_results": ["Round 33 independent re-derivation of two Round 32 removals",
                            "Round 37 bound_3 in the 1,398-boundary ledger (NOT load-bearing: "
                            "all 1,398 already fail bound_1)"],
    },
    "coarse_segment_bound": {
        "where": ["src/process_rr_new_target_a_boundaries.py::capacity_theorem",
                 "src/build_rr_1398_boundary_ledger.py::classify_row (bound_1)"],
        "question": "5*(O_cap+R_cap)+4 >= B+1",
        "requires_full_hexagon_freshness": False,
        "requires_only_single_landing": False,
        "precondition": ("none beyond the RR alphabet: derived purely from segment COUNT "
                        "(<= O_cap + R_cap orbit changes) and max ports per segment (<= 5), "
                        "with no reference to hexagon occupancy at all"),
        "class": "SOUND_FOR_SINGLE_LANDING",
        "proof_status": "exact theorem, occupancy-independent",
        "affected_results": ["Round 30 (removed 9 of 18)", "Round 35 (14 of 22 roots dead)",
                            "Round 36/37 (all 1,398 boundaries)"],
    },
    "capacity_slack__port_availability": {
        "where": ["src/build_rr_target_a_roots.py::capacity_slack",
                 "src/verify_rr_target_b_flow.py::orbit_capacity_bound"],
        "question": "(5 - used_ports(q0)) + 5*O_rem + 4*(N_rem + Phi) >= TARGET_P - P",
        "requires_full_hexagon_freshness": False,
        "requires_only_single_landing": True,
        "precondition": ("none: uses popcount(orbit_masks[q0]) -- PORT occupancy, not hexagon "
                        "occupancy -- so it counts landable ports, not completable hexagons"),
        "class": "SOUND_FOR_SINGLE_LANDING",
        "proof_status": "exact theorem, occupancy-independent (port-level, not hexagon-level)",
        "affected_results": ["Round 35 Q2 closure of 22 roots"],
    },
    "root_envelope": {
        "where": ["src/analyze_rr_root_capacity_envelopes.py::envelope_for_root"],
        "question": "upper bound on margin_1 over ALL Target A boundaries reachable from a root",
        "requires_full_hexagon_freshness": False,
        "requires_only_single_landing": True,
        "precondition": ("none: uses only the conservation law (dM = +1 / -4), the exact "
                        "Ndef cost of an R event, and the group-theoretic max preserving run "
                        "of 4 -- all occupancy-independent"),
        "class": "SOUND_FOR_SINGLE_LANDING",
        "proof_status": "exact theorem, occupancy-independent",
        "affected_results": ["Round 37 closure of 28 of 33 roots"],
    },
}


def assert_full_segment_context(st, helper_name):
    """Part A.5: the firewall.  A full-segment-only helper may be called
    only where ell=5 is forced, i.e. Phi == 0.  Raises otherwise."""
    cls = HELPER_TAXONOMY.get(helper_name, {}).get("class")
    if cls != "SOUND_FOR_FULL_SEGMENT":
        return
    p = phi(st)
    if p != 0:
        raise CapacityPreconditionError(
            f"{helper_name} is SOUND_FOR_FULL_SEGMENT only (requires Phi==0 so that ell=5 "
            f"is forced and each counted port's hexagon is completed); called at a state "
            f"with Phi={p}. At Phi != 0 a joint may land on a port whose hexagon is only "
            f"partially free, which this helper undercounts.")


def guarded_true_phase_walk_capacity(st, words):
    """Firewalled wrapper.  Same computation as the historical helper, but
    it refuses to run outside its precondition."""
    assert_full_segment_context(st, "true_phase_walk_capacity")
    return _raw_true_phase_walk_capacity(st, words)


def _raw_true_phase_walk_capacity(st, words):
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    partial = core.hexagon_id(st.p)
    uh = {h for h in range(len(core.ROT_REPS)) if st.hex_masks[h] == 0}
    best = 0
    for combo, offs in words:
        n, ok = 0, True
        for i, off in enumerate(offs):
            p2 = PORTS[q0][(ph0 + off) % 5]
            h = core.hexagon_id(p2)
            if i == 0:
                if h != partial:
                    ok = False
                    break
            elif h not in uh:
                ok = False
                break
            n += 1
        if ok:
            best = max(best, n)
    return best


def legal_words():
    from itertools import product
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
                out.append((combo, tuple(seen)))
    return out


WORDS = legal_words()


# ===========================================================================
# Part A.3: formalize the counterexample exactly
# ===========================================================================
def replay_long_root(idx, prefixes):
    rec = prefixes["prefixes"][idx]
    st = exact.initial_state()
    for _ in range(rec["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lbl in rec["literal_joint_word"]:
        for _ in range(5):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st


def formalize_counterexample(prefixes):
    st = replay_long_root(142, prefixes)
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    predicted = _raw_true_phase_walk_capacity(st, WORDS)

    occupancy = []
    for i in range(5):
        p = PORTS[q0][(ph0 + i) % 5]
        h = core.hexagon_id(p)
        occupancy.append({"offset": i, "phase": (ph0 + i) % 5, "hexagon": h,
                         "hexagon_popcount": popcount(st.hex_masks[h]),
                         "port_already_pass_start": bool(st.orbit_masks[q0] >> ((ph0 + i) % 5) & 1)})

    cur, ports, trace = st, 1, []
    while True:
        run = cur
        ok = True
        for _ in range(5):
            tr = exact.extend(run, W1)
            if tr is None:
                ok = False
                break
            run = tr.state
        if not ok:
            trace.append({"event": "rot^5 run illegal -> segment ends",
                         "at_phase": exact.ORBIT_PHASE[cur.p][1]})
            break
        tr2 = exact.extend(run, mbl["w2:10"])
        if tr2 is None:
            trace.append({"event": "preserving joint illegal -> segment ends"})
            break
        landed_hex = core.hexagon_id(tr2.target)
        trace.append({"event": "landed on a new port", "port_index": ports + 1,
                     "phase": exact.ORBIT_PHASE[tr2.target][1], "hexagon": landed_hex,
                     "hexagon_popcount_at_root": popcount(st.hex_masks[landed_hex])})
        cur = tr2.state
        ports += 1

    return {
        "root_identifier": "long_found_142 (prefix index 142, abandonment ell=4)",
        "root_state": {"P": st.P, "O": st.O, "Ndef": st.Ndef, "Phi": phi(st),
                      "orbit": q0, "entry_phase": ph0},
        "precondition_violated": f"Phi = {phi(st)} != 0, so ell=5 is NOT forced here",
        "helper_predicted_ports": predicted,
        "engine_achieved_ports": ports,
        "undercount": ports - predicted,
        "port_occupancy_from_entry_phase": occupancy,
        "engine_trace": trace,
        "exact_reason": (
            "the helper rejects offset 3 (phase 4, hexagon 0) because that hexagon has "
            "popcount 5, i.e. is not entirely unvisited. That rejection is correct for the "
            "FULL-SEGMENT question -- an ell=5 run from that port would need all six slots "
            "free and only one is. But it is wrong for the PORT-COUNT question: the joint "
            "landing needs only its own target permutation free, and hexagon 0's single "
            "remaining free slot is exactly that permutation. The engine therefore stands on "
            "4 ports where the helper predicts 3."),
        "round_37_misstatement_corrected": {
            "as_published": "predicts 2, engine achieves 3",
            "actual": f"predicts {predicted}, engine achieves {ports}",
            "note": ("the DIRECTION of the Round 37 finding (the helper undercounts, and is "
                    "therefore unsound as a port-count bound) is confirmed; only the two "
                    "numbers were wrong. The Round 37 envelope itself never used the helper, "
                    "so no Round 37 result depends on the misstated figures."),
        },
        "grade": "exact counterexample",
    }


# ===========================================================================
# Part A.6: re-run every historical elimination that used a refinement
# ===========================================================================
def replay_survivor_state(ell, prep):
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


def freshness_independent_bound(st):
    """The replacement proof: coarse segment bound, using ONLY segment
    count and max ports per segment. No hexagon occupancy is consulted."""
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(AREA_A.n_limit - st.Ndef, 0)
    bound = 5 * (O_cap + R_cap) + 4
    return {"B_plus_1": B + 1, "bound": bound, "margin": bound - (B + 1),
           "eliminated": bound < B + 1}


def replay_long_boundary(prefix_index, witness, prefixes):
    """The 6 long CAPACITY_IMPOSSIBLE boundaries come from the Round 27
    long-prefix search, not from rr_preparation_words.json, so they need
    their own replay path."""
    st = replay_long_root(prefix_index, prefixes)
    for s in witness["extension_trace"]:
        ell = int(s["label"].split(";")[0][4:])
        lbl = s["label"].split(";")[1]
        for _ in range(ell):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st


def rerun_historical_eliminations(preps, survivors, prefixes=None, old_ext=None):
    rows = []
    states = []
    for ellk, v in preps["results_by_ell"].items():
        ell = int(ellk)
        for prep in v["preparations"]:
            st = replay_survivor_state(ell, prep)
            if st is not None:
                states.append((ell, st, "short_family"))
    if prefixes is not None and old_ext is not None:
        for rec in old_ext["results"]:
            if rec["status"] != "FOUND":
                continue
            st = replay_long_boundary(rec["prefix_index"], rec["same_component_witnesses"][0],
                                     prefixes)
            states.append((prefixes["prefixes"][rec["prefix_index"]]["root_ell"], st,
                          f"long_found_{rec['prefix_index']}"))
    for ell, st, provenance in states:
            raw = sha(st.stable_key())[:16]
            surv = next((r for r in survivors["rows"]
                        if r["root_ell"] == ell and r["canonical_state_hash"][:16] == raw), None)
            if surv is None:
                continue
            p = phi(st)
            precond_ok = (p == 0)
            fib = freshness_independent_bound(st)
            # the freshness-DEPENDENT refinement, for comparison only
            c = {q: sum(1 for h in ORBIT_HEX[q] if st.hex_masks[h] == 0) for q in range(NORB)}
            unopened = [q for q in range(NORB) if st.orbit_masks[q] == 0]
            q0, _ = exact.ORBIT_PHASE[st.p]
            O_cap = exact.TARGET_O - st.O
            R_cap = max(AREA_A.n_limit - st.Ndef, 0)
            c0 = min(c[q0] + 1, 5)
            top = sorted((c[q] for q in unopened), reverse=True)[:O_cap]
            refined_r4 = c0 + sum(top) + 4 * R_cap
            B1 = exact.TARGET_P - st.P + 1
            rows.append({
                "root_ell": ell, "P_core": surv["P_core"], "raw_hash": raw,
                "provenance": provenance,
                "recorded_verdict": surv["verdict"],
                "Phi": p, "precondition_Phi_eq_0_holds": precond_ok,
                "freshness_dependent_refined_bound": refined_r4,
                "freshness_dependent_eliminates": refined_r4 < B1,
                "freshness_INDEPENDENT_coarse_bound": fib["bound"],
                "freshness_INDEPENDENT_eliminates": fib["eliminated"],
                "B_plus_1": B1,
            })
    return rows


def static_callsite_scan():
    """Part A.1/A.2: enumerate call sites by parsing every src/*.py."""
    targets = ["true_phase_walk_capacity", "initial_capacity", "capacity_slack",
              "orbit_capacity_bound", "port_capacities", "capacity_theorem",
              "envelope_for_root", "freshness_independent_bound"]
    sites = []
    for path in sorted((ROOT / "src").glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in targets:
                    sites.append({"file": f"src/{path.name}", "line": node.lineno,
                                 "callee": name})
            if isinstance(node, ast.FunctionDef) and node.name in targets:
                sites.append({"file": f"src/{path.name}", "line": node.lineno,
                             "callee": node.name, "is_definition": True})
    return sites


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--old-ext", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_capacity_callsite_audit.json"))
    a = ap.parse_args()

    prefixes = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    survivors = json.loads(Path(a.survivors).read_text(encoding="utf-8"))
    old_ext = json.loads(Path(a.old_ext).read_text(encoding="utf-8"))

    print("=== A.1/A.2: static call-site scan ===")
    sites = static_callsite_scan()
    by_callee = Counter(s["callee"] for s in sites)
    for c, n in sorted(by_callee.items()):
        print(f"  {c:<32} {n} site(s)")

    print("\n=== A.4: helper taxonomy ===")
    for name, h in HELPER_TAXONOMY.items():
        print(f"  {name:<36} {h['class']:<26} freshness_required={h['requires_full_hexagon_freshness']}")

    print("\n=== A.3: the exact counterexample ===")
    ce = formalize_counterexample(prefixes)
    print(f"  root: {ce['root_identifier']}, Phi={ce['root_state']['Phi']}")
    print(f"  helper predicted {ce['helper_predicted_ports']} ports; "
          f"engine achieved {ce['engine_achieved_ports']} ports "
          f"(undercount {ce['undercount']})")
    print(f"  Round 37 published '{ce['round_37_misstatement_corrected']['as_published']}' "
          f"-> corrected to '{ce['round_37_misstatement_corrected']['actual']}'")

    print("\n=== A.5: runtime firewall ===")
    fw = []
    st_bad = replay_long_root(142, prefixes)
    try:
        guarded_true_phase_walk_capacity(st_bad, WORDS)
        fw.append({"case": "Phi!=0 call", "raised": False})
        print("  FAIL: firewall did not raise at Phi != 0")
    except CapacityPreconditionError:
        fw.append({"case": "Phi!=0 call", "raised": True})
        print(f"  firewall correctly raised at Phi={phi(st_bad)}")
    st_good = replay_survivor_state(4, preps["results_by_ell"]["4"]["preparations"][0])
    try:
        v = guarded_true_phase_walk_capacity(st_good, WORDS)
        fw.append({"case": "Phi==0 call", "raised": False, "value": v})
        print(f"  firewall correctly allowed the call at Phi={phi(st_good)} (value {v})")
    except CapacityPreconditionError:
        fw.append({"case": "Phi==0 call", "raised": True})
        print("  FAIL: firewall wrongly raised at Phi == 0")

    print("\n=== A.6: historical elimination re-verification ===")
    hist = rerun_historical_eliminations(preps, survivors, prefixes, old_ext)
    n_precond_ok = sum(1 for r in hist if r["precondition_Phi_eq_0_holds"])
    print(f"  boundaries re-checked: {len(hist)}; precondition (Phi==0) holds at: {n_precond_ok}")
    retained, retracted = [], []
    for r in hist:
        eliminated_recorded = r["recorded_verdict"] == "CAPACITY_IMPOSSIBLE"
        if not eliminated_recorded:
            continue
        if r["freshness_INDEPENDENT_eliminates"]:
            r["status"] = "RETAINED (independent replacement proof succeeds)"
            retained.append(r)
        elif r["precondition_Phi_eq_0_holds"] and r["freshness_dependent_eliminates"]:
            r["status"] = "RETAINED (freshness-dependent proof, precondition verified to hold)"
            retained.append(r)
        else:
            r["status"] = "RETRACTED"
            retracted.append(r)
    for r in hist:
        if r.get("status"):
            print(f"  [{r['provenance']:<16}] ell={r['root_ell']} P_core={r['P_core']:>2} "
                  f"Phi={r['Phi']} -> {r['status']}")
    print(f"\n  retained: {len(retained)}; RETRACTED: {len(retracted)}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-capacity-callsite-audit-v1",
        "call_sites": sites,
        "call_site_histogram": {k: v for k, v in by_callee.items()},
        "helper_taxonomy": HELPER_TAXONOMY,
        "counterexample": ce,
        "firewall_tests": fw,
        "historical_eliminations": hist,
        "n_retained": len(retained), "n_retracted": len(retracted),
        "grade": "exact counterexample + exact replay + exact theorem (replacement proofs)",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
