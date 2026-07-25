#!/usr/bin/env python3
"""Round 22, sections 1, 2, 5, 6, 7: the symbolic preparation automaton.

Boundary state (invariant, no implementation orbit ids):
    Q = (hub_side, o_star_touched, r_used, fresh_mode, phase_class)
  hub_side       : is the current endpoint inside the hub hexagon?
  o_star_touched : has O* (the nearest residual orbit) been targeted yet?
  r_used         : has the single preparation R (=R1) already fired?
  fresh_mode     : has any fresh Z3 opening occurred yet?
  phase_class    : the current endpoint's phase within its E-orbit (0..4)

Alphabet, derived from EXACT transition kinds rather than fitted to data:
    E  = zero-charge, existing orbit  (necessarily the unique weight-2 move)
    F  = zero-charge, fresh orbit     (weight-3, new_orbit=True)
    Rh = R event targeting O*
    Rx = R event targeting another orbit
Note E is forced to be w2:10 by UNIQUE_WEIGHT2_MOVE_THEOREM: a weight-3
zero-charge non-fresh joint is by definition an R, so every non-R
non-fresh preparation edge is the unique weight-2 move. 손증명.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

def _load(name, filename):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod); return mod

macro = _load("bpa_macro", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W2_10 = move_by_label["w2:10"]
HEX0_POSITION_ORBIT = [0, 120, 33, 9, 3, 1]

def kind(w, a, n):
    return {(2,False,False):"Z2",(2,True,True):"Z2abandon",(3,False,False):"R",
            (3,False,True):"Z3"}.get((w,a,n),"other")

def symbol(k, tgt_orbit, o_star):
    if k == "R":  return "Rh" if tgt_orbit == o_star else "Rx"
    if k == "Z3": return "F"
    if k == "Z2": return "E"
    return "?"

def boundary(state, hub, o_star, r_used, fresh, o_star_touched):
    q, ph = exact.ORBIT_PHASE[state.p]
    return (core.hexagon_id(state.p) == hub, o_star_touched, r_used, fresh > 0, ph)

def abandonment_root(init, ell):
    cur = init
    for _ in range(ell): cur = exact.extend(cur, W1).state
    return exact.extend(cur, W2_10).state

def build(ell, depth_ceiling, init, hub):
    """Enumerate every legal preparation prefix (before the hub completer)
    and record the induced symbolic automaton transitions."""
    o_star = HEX0_POSITION_ORBIT[ell + 1]
    root = abandonment_root(init, ell)
    start_Q = boundary(root, hub, o_star, False, 0, False)
    trans = Counter()          # (Q, symbol, Q') -> count
    states = {start_Q}
    completer_ready = Counter() # Q from which a hub-completing joint exists
    frontier = deque([(root, start_Q, False, 0, False, 0)])
    seen = {(root.stable_key(), start_Q)}
    while frontier:
        st, Q, r_used, fresh, ost, depth = frontier.popleft()
        if depth >= depth_ceiling: continue
        for edge in macro.macro_edges(st):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None: continue
            k = kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other": continue
            tq, _ = exact.ORBIT_PHASE[tr.target]
            thex = core.hexagon_id(tr.target)
            if thex == hub:
                completer_ready[Q] += 1     # this Q can complete the hub
                continue                    # preparation stops before the completer
            sym = symbol(k, tq, o_star)
            if sym == "?": continue
            n_r = r_used or k == "R"
            if r_used and k == "R": continue   # RR words allow only one R in P
            n_fresh = fresh + (1 if tr.new_orbit else 0)
            n_ost = ost or tq == o_star
            Q2 = boundary(tr.state, hub, o_star, n_r, n_fresh, n_ost)
            trans[(Q, sym, Q2)] += 1
            states.add(Q2)
            key = (tr.state.stable_key(), Q2)
            if key in seen: continue
            seen.add(key)
            frontier.append((tr.state, Q2, n_r, n_fresh, n_ost, depth + 1))
    return {"abandonment_ell": ell, "o_star": o_star, "depth_ceiling": depth_ceiling,
            "start_state": start_Q, "state_count": len(states),
            "states": sorted(states),
            "transition_count": len(trans),
            "transitions": [{"from": list(a), "symbol": s, "to": list(b), "exact_witness_count": c}
                            for (a, s, b), c in sorted(trans.items(), key=lambda kv: -kv[1])],
            "completer_ready_states": [{"state": list(q), "hub_joint_count": c}
                                        for q, c in sorted(completer_ready.items())],
            "symbols_used": sorted({s for (_, s, _) in trans})}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_preparation_automaton.json"))
    a = ap.parse_args()
    init = exact.initial_state(); hub = core.hexagon_id(init.p)
    res = {}
    for ell in (0, 4):
        r = build(ell, a.depth, init, hub)
        res[str(ell)] = r
        print(f"ell={ell} O*={r['o_star']}: states={r['state_count']} transitions={r['transition_count']} "
              f"symbols={r['symbols_used']} completer_ready_states={len(r['completer_ready_states'])}")
    rep = {"schema": "rr-preparation-automaton-v1",
           "boundary_definition": "(hub_side, o_star_touched, r_used, fresh_mode, phase_class)",
           "alphabet": {"E": "zero-charge existing orbit (forced to be w2:10)",
                        "F": "zero-charge fresh Z3 opening",
                        "Rh": "R targeting O*", "Rx": "R targeting another orbit"},
           "grade": ("necessary-condition automaton: every exact preparation edge induces "
                     "one of these symbolic transitions, but a symbolic transition does NOT "
                     "guarantee an exact realization (literal collisions and orbit novelty "
                     "are not encoded in Q). sound over-approximation."),
           "by_ell": res}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", a.output)

if __name__ == "__main__":
    main()
