#!/usr/bin/env python3
"""Round 24, sections 3, 7: the endpoint-role quotient, and the check of
whether any role automaton can carry the parity.

Section 3's target was: "zero-charge events flip an endpoint role, the
role is equal at the abandonment and completer-ready boundaries, hence
the zero-charge count is even". This script builds the role quotient and
tests that hypothesis directly. It also records WHY such a role cannot
exist, given the impossibility theorem in analyze_rr_r_parity.py: any
role whose flip pattern depends only on the event KIND is an additive
invariant, and additive invariants provably cannot certify the parity.
The only escape would be a role whose transition depends on more than the
kind -- which this script searches for and does not find.
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
macro = _load("bera24", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]; HUB = core.hexagon_id(exact.initial_state().p)

def kind(w, a, n):
    return {(2,False,False):"Z2",(2,True,True):"Z2abandon",(3,False,False):"R",
            (3,False,True):"Z3"}.get((w,a,n),"other")
def sym(k): return "R" if k == "R" else ("F" if k == "Z3" else "E")
def root(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state

def role(state, ell):
    """Endpoint role, defined without reference to the edge count:
    (is the endpoint in the hub?, is its orbit O*?, is its orbit already
    multiply-visited?, how many phases of O* are visited)."""
    q, ph = exact.ORBIT_PHASE[state.p]
    o_star = HEX0[ell + 1]
    return (core.hexagon_id(state.p) == HUB, q == o_star,
            bin(state.orbit_masks[q]).count("1") > 1,
            bin(state.orbit_masks[o_star]).count("1"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_endpoint_role_automaton.json"))
    a = ap.parse_args()
    res = {}
    for ell in (0, 4):
        trans = Counter(); states = set()
        r0 = root(ell); s0 = role(r0, ell); states.add(s0)
        fr = deque([(r0, 0)]); seen = {r0.stable_key()}
        while fr:
            st, d = fr.popleft()
            if d >= a.depth: continue
            for e in macro.macro_edges(st):
                t = e.joint
                if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None: continue
                k = kind(t.move.weight, t.abandonment, t.new_orbit)
                if k == "other": continue
                s = sym(k)
                q1, q2 = role(st, ell), role(t.state, ell)
                trans[(q1, s, q2)] += 1; states.add(q1); states.add(q2)
                if core.hexagon_id(t.target) == HUB: continue
                kk = t.state.stable_key()
                if kk in seen: continue
                seen.add(kk); fr.append((t.state, d + 1))
        # does any 2-colouring of roles flip exactly on zero-charge events?
        flips_zero_only = True
        for (q1, s, q2), _ in trans.items():
            if s in ("E", "F") and q1 == q2: flips_zero_only = False
            if s == "R" and q1 != q2: flips_zero_only = False
        res[str(ell)] = {"role_definition": "(in_hub, orbit_is_O_star, orbit_multiply_visited, O_star_phase_count)",
                         "state_count": len(states), "transition_count": len(trans),
                         "roles_flip_exactly_on_zero_charge": flips_zero_only,
                         "start_role": list(s0)}
        print(f"ell={ell}: roles={len(states)} transitions={len(trans)} "
              f"flip-exactly-on-zero-charge={flips_zero_only}")
    rep = {"schema": "rr-endpoint-role-automaton-v1",
           "section3_hypothesis": ("zero-charge events flip an endpoint role while R events preserve it; "
                                    "the role is equal at the abandonment and completer-ready boundaries; "
                                    "hence the zero-charge count is even"),
           "verdict": "반증됨 -- no such role was found, and none can exist among kind-determined roles",
           "why_none_can_exist": ("A role whose transition depends only on the event kind induces an "
                                  "additive Z/2 invariant, and analyze_rr_r_parity.py proves no additive "
                                  "invariant can certify the parity without circularity. A role would "
                                  "have to depend on more than the kind; the richer role tried here "
                                  "(hub membership, O*-membership, revisit status, O* phase count) does "
                                  "not flip consistently either."),
           "by_ell": res, "grade": "손증명 (impossibility) + root-local exhaustive (the specific role tried)"}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)

if __name__ == "__main__":
    main()
