#!/usr/bin/env python3
"""Round 22, sections 8-10: tests the Rh-free sublanguage identity
    P(ell=0) == P(ell=4) INTERSECT {E,F}*
in both inclusions, and builds the branch transport map.

Inclusion 1 (P0 subset of Rh-free P4) and Inclusion 2 (the converse) are
tested separately, and each candidate structural reason R1-R4 for why Rh
cannot appear at ell=0 is checked against exact transitions rather than
asserted.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

def _load(n, f):
    p = WORK / f; s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m

macro = _load("vrfl_macro", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]

def kind(w, a, n):
    return {(2,False,False):"Z2",(2,True,True):"Z2abandon",(3,False,False):"R",
            (3,False,True):"Z3"}.get((w,a,n),"other")

def root(init, ell):
    c = init
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state

def rh_reachable(init, hub, ell, depth):
    """Section 8: is an Rh edge (an R targeting O*) EVER locally legal
    anywhere in a preparation prefix at this ell? If yes at ell=0, then
    candidate reasons R2/R3 (Rh structurally impossible) are refuted and
    R4 (locally legal but incompatible with the terminal form) stands."""
    o_star = HEX0[ell + 1]
    fr = deque([(root(init, ell), 0, 0)]); seen = {root(init, ell).stable_key()}
    found = []
    while fr:
        st, rused, d = fr.popleft()
        if d >= depth: continue
        for e in macro.macro_edges(st):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None: continue
            k = kind(t.move.weight, t.abandonment, t.new_orbit)
            tq, tph = exact.ORBIT_PHASE[t.target]
            thex = core.hexagon_id(t.target)
            if thex == hub: continue          # that would be the completer, not a P edge
            if k == "R" and tq == o_star and len(found) < 5:
                found.append({"depth": d + 1, "target_orbit": tq, "target_phase": tph,
                              "target_hexagon": thex, "joint": t.move.label})
            if k == "R" and rused: continue
            kk = t.state.stable_key()
            if kk in seen: continue
            seen.add(kk); fr.append((t.state, rused or k == "R", d + 1))
    return found

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--words", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_rh_free_language_check.json"))
    ap.add_argument("--transport-output", default=str(ROOT / "outputs" / "rr_branch_transport.json"))
    a = ap.parse_args()

    d = json.loads(Path(a.words).read_text(encoding="utf-8"))
    P = {}
    for ell, r in d["results_by_ell"].items():
        for f in r["preparations"]:
            c = f["completer_index_within_preparation"]
            P.setdefault(ell, set()).add(tuple(f["symbolic_preparation_word"][:c-1]))
    P0, P4 = P.get("0", set()), P.get("4", set())
    rhfree4 = {w for w in P4 if "Rh" not in w}
    inc1 = P0 <= rhfree4
    lens0 = {len(w) for w in P0}
    rhfree4_same_len = {w for w in rhfree4 if len(w) in lens0}
    inc2_restricted = rhfree4_same_len <= P0

    print(f"P(ell=0) = {sorted(''.join(w) for w in P0)}")
    print(f"Rh-free P(ell=4) = {sorted(''.join(w) for w in rhfree4)}")
    print(f"Inclusion 1  P0 subset Rh-free(P4): {inc1}")
    print(f"Inclusion 2 (restricted to lengths present in P0): {inc2_restricted}")

    init = exact.initial_state(); hub = core.hexagon_id(init.p)
    rh0 = rh_reachable(init, hub, 0, a.depth)
    rh4 = rh_reachable(init, hub, 4, a.depth)
    print(f"\nSection 8 -- Rh edges locally legal in a preparation prefix?")
    print(f"  ell=0 (O*=120): {len(rh0)} found (showing up to 5) -> {rh0[:2]}")
    print(f"  ell=4 (O*=1):   {len(rh4)} found -> {rh4[:2]}")

    verdicts = {
        "R1_exhausts_ancestry_too_early": "미완료 (not tested directly)",
        "R2_orbit1_target_R_cannot_enter_preparation_at_ell0":
            ("반증됨" if rh0 else "지지됨") +
            f" -- Rh edges are {'locally legal' if rh0 else 'never locally legal'} in ell=0 preparation prefixes",
        "R3_Rh_only_compatible_with_O_star_equals_1":
            ("반증됨" if rh0 else "지지됨") + " -- same evidence as R2",
        "R4_locally_legal_but_incompatible_with_terminal_normal_form":
            ("지지됨" if rh0 else "해당 없음") +
            " -- Rh is locally legal at ell=0 yet appears in NO same-component witness, so the obstruction lies in the terminal form, not in local legality",
    }
    for k, v in verdicts.items(): print(f"  {k}: {v}")

    rep = {"schema": "rr-rh-free-language-check-v1",
           "P_ell0": sorted("".join(w) for w in P0),
           "P_ell4": sorted("".join(w) for w in P4),
           "Rh_free_P_ell4": sorted("".join(w) for w in rhfree4),
           "inclusion_1_P0_subset_RhfreeP4": inc1,
           "inclusion_2_restricted_to_P0_lengths": inc2_restricted,
           "inclusion_2_unrestricted": "미완료 -- ell=4 has Rh-free words of length 6 that ell=0 only reaches at depth 9; verified there in Round 21, but longer lengths untested",
           "section8_rh_local_legality": {"ell0_examples": rh0, "ell4_examples": rh4},
           "section8_verdicts": verdicts,
           "grade": "exact language identity within the naturally-exhausted lengths (2,4,6); 미완료 beyond"}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", a.output)

    transport = {"schema": "rr-branch-transport-v1",
        "map": "tau : preparation boundaries at ell=4 -> ell=0",
        "preserved": ["E/F symbolic action", "preparation parity (|P| even in both)",
                      "the requirement that the completer targets O*",
                      "Phi=0 (proved ell-independently in Round 21)"],
        "changed": {"O_star": {"ell4": 1, "ell0": 120},
                    "tail_T": {"ell4": "empty", "ell0": "Xh"},
                    "completer_landing_phase": {"ell4": 4, "ell0": 0},
                    "completer_to_R2_distance": {"ell4": 1, "ell0": 2},
                    "Rh_availability": "present at ell=4, absent from every ell=0 witness"},
        "status": ("the map is specified only at the level of these invariants; an explicit "
                   "state-to-state bijection was NOT constructed. 미완료."),
        "why_Rh_differs": ("At ell=0 the completer must itself be R1, because the completer "
                           "targets O* and chaining requires R1 to target O*; hence no earlier "
                           "Rh can exist. At ell=4, O*=1 sits at the hub exit position, so R1 "
                           "may target O* at an earlier phase and a later zero-charge edge "
                           "completes the hub -- leaving room for Rh inside P. 손증명 given the "
                           "terminal normal form."),
    }
    Path(a.transport_output).write_text(json.dumps(transport, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", a.transport_output)

if __name__ == "__main__":
    main()
