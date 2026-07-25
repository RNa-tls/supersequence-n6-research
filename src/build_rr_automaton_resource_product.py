#!/usr/bin/env python3
"""Round 23, sections 17, 18, 20: the automaton x resource product, and
the trailing-count-4 question.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
def _load(n, f):
    p = WORK / f; s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
macro = _load("arp_macro", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
RR_JOINTS = ["w2:10", "w3:120", "w3:201", "w3:210"]
HEX0 = [0, 120, 33, 9, 3, 1]; HUB = core.hexagon_id(exact.initial_state().p)

def kind(w, a, n):
    return {(2,False,False):"Z2",(2,True,True):"Z2abandon",(3,False,False):"R",
            (3,False,True):"Z3"}.get((w,a,n),"other")

def root(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state

def product_states(ell, depth, resources):
    """Q_symbolic x R_minimal. resources is a list of coordinate names."""
    o_star = HEX0[ell + 1]
    def Q(st, rused, fresh, ost):
        q, ph = exact.ORBIT_PHASE[st.p]
        base = (core.hexagon_id(st.p) == HUB, ost, rused, fresh > 0, ph)
        extra = []
        if "r_count" in resources: extra.append(rused)
        if "fresh_count" in resources: extra.append(min(fresh, 3))
        if "o_star_phase_mask" in resources:
            extra.append(bin(st.orbit_masks[o_star]).count("1"))
        if "hub_residual" in resources:
            extra.append(bin(st.hex_masks[HUB]).count("1"))
        return base + tuple(extra)
    r0 = root(ell); s0 = Q(r0, False, 0, False)
    seen_pairs = {(r0.stable_key(), s0)}
    states = {s0}; trans = set(); frontier = deque([(r0, s0, False, 0, False, 0)])
    # false positives: symbolic transitions with no exact witness at some state
    while frontier:
        st, q, rused, fresh, ost, d = frontier.popleft()
        if d >= depth: continue
        for e in macro.macro_edges(st):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None: continue
            k = kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other": continue
            tq, _ = exact.ORBIT_PHASE[t.target]
            if core.hexagon_id(t.target) == HUB: continue
            sym = "Rh" if (k == "R" and tq == o_star) else ("Rx" if k == "R" else ("F" if t.new_orbit else "E"))
            if rused and k == "R": continue
            nr, nf, no = rused or k == "R", fresh + (1 if t.new_orbit else 0), ost or tq == o_star
            q2 = Q(t.state, nr, nf, no)
            trans.add((q, sym, q2)); states.add(q2)
            key = (t.state.stable_key(), q2)
            if key in seen_pairs: continue
            seen_pairs.add(key); frontier.append((t.state, q2, nr, nf, no, d + 1))
    return {"resources": resources, "state_count": len(states), "transition_count": len(trans)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_automaton_resource_states.json"))
    ap.add_argument("--four-output", default=str(ROOT / "outputs" / "rr_trailing_count_four_check.json"))
    a = ap.parse_args()

    combos = [[], ["r_count"], ["fresh_count"], ["o_star_phase_mask"], ["hub_residual"],
              ["r_count", "o_star_phase_mask"], ["r_count", "fresh_count", "o_star_phase_mask", "hub_residual"]]
    res = {}
    print("=== automaton x resource product (section 17-18 ablation) ===")
    for ell in (0, 4):
        res[str(ell)] = []
        for c in combos:
            r = product_states(ell, a.depth, c)
            res[str(ell)].append(r)
            print(f"  ell={ell} resources={str(c):<52} states={r['state_count']:5d} transitions={r['transition_count']:5d}")
    rep = {"schema": "rr-automaton-resource-states-v1",
           "note": ("Adding resource coordinates refines the quotient monotonically. None of "
                    "these coordinates encodes the full visited mask, so the product remains a "
                    "sound over-approximation -- refining it does NOT make it exact, it only "
                    "shrinks the false-positive set. No coordinate combination tested here "
                    "achieved exactness, and exactness was not claimed."),
           "grade": "sound over-approximation (all combinations)",
           "by_ell": res}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", a.output)

    # ---- section 20: can m(S) = 4? ----
    d = json.loads((ROOT / "outputs" / "rr_trailing_edge_exact_counts.json").read_text(encoding="utf-8"))
    blocked_always = Counter()
    for row in d["rows"]:
        if "candidates" not in row: continue
        for c in row["candidates"]:
            if not c["legal"]: blocked_always[c["joint"]] += 1
    n = sum(1 for r in d["rows"] if "candidates" in r)
    print(f"\n=== trailing count 4 check ===\nblocked-candidate frequency over {n} terminal states: {dict(blocked_always)}")
    always = [j for j, c in blocked_always.items() if c == n]
    four = {"schema": "rr-trailing-count-four-check-v1",
            "terminal_states_examined": n,
            "blocked_frequency": dict(blocked_always),
            "always_blocked_joints": always,
            "m_equals_4_observed": any(r.get("legal_count") == 4 for r in d["rows"] if "legal_count" in r),
            "verdict": (
                f"w3:120 is blocked in all {n} terminal states, so m(S)<=3 holds throughout the "
                "root-local exhaustive range. But the blocking is a VISITED-TARGET COLLISION, "
                "not an area_a_prune_reason, so it is a state-dependent fact rather than a "
                "structural one. m(S)=4 is therefore NOT ruled out: no proof that w3:120's "
                "ell=5 target must already be visited was found. The hand-proved bound stays "
                "at 4; m(S)<=3 is root-local exhaustive only. 미완료."),
            }
    Path(a.four_output).write_text(json.dumps(four, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"always-blocked joints: {always}; m=4 observed: {four['m_equals_4_observed']}")
    print("wrote", a.four_output)

if __name__ == "__main__":
    main()
