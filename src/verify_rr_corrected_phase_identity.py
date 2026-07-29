#!/usr/bin/env python3
"""Round 29, section 10: the corrected unconditional phase identity.

    #Z_{->O*}  ==  k + #R_{odd-delta}   (mod 2)

kept as a standalone theorem, deliberately NOT used by the terminal
normal form proof.

DEFINITIONS, stated precisely because the earlier failure was a
definitional one.

  O* phase walk    the sequence of phases of O* visited by the word, in
                   word order, starting from the phase the ABANDONMENT
                   joint lands on and continuing with the target phase of
                   every later event whose target orbit is O*.
  delta_i          (phase_{i+1} - phase_i) mod 5, i.e. the displacement of
                   the i-th STEP of that walk.  A step's delta is relative
                   to the previously visited O* phase, NOT a local property
                   of the event.
  #R_{odd-delta}   the number of steps whose event is an R and whose delta
                   is odd.  Range: steps of the O* walk only -- R events
                   that do not target O* are not counted.
  k                the winding number, defined by  sum_i delta_i = A + 5k
                   where A = (phase_last - phase_first) mod 5.
  #Z_{->O*}        zero-charge events (E or F) whose target orbit is O*,
                   counted over P_core . C.

PROOF (손증명):
  1. F never targets O*: an F event opens a NEW orbit, but O* is already
     open because the abandonment registered it.  So #Z_{->O*} = #E_{->O*}.
  2. Every E step has delta = +1: the ell=5 w2:10 macro-edge is exactly
     right-composition by E (Sigma^5 o tau = E), so from a port q of O* it
     lands on q o E.
  3. sum_i delta_i = A + 5k by the definition of k.
  4. Reducing 3 mod 2 and splitting the left side by event type:
        #E_steps * 1  +  sum over R steps of delta
     == A + 5k, so
        #E_{->O*} + #R_{odd-delta} == A + k (mod 2).
     With A = 4 (the ell-independent total advance) this is
        #Z_{->O*} == k + #R_{odd-delta} (mod 2).                    QED

The historical special case: in the 95 depth<=6 completions every R step
into O* had EVEN delta, so #R_{odd-delta} = 0 and the identity collapsed
to #Z == k -- which is exactly why the collapsed form looked like a
theorem.  It is not one.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
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


macro = _load("vrcpi", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]


def check_generator_identity():
    """Step 2's group fact, verified in S_6."""
    S5 = core.power(core.SIGMA, 5)
    tau = mbl["w2:10"].action
    return {"Sigma5_compose_tau": list(core.compose(S5, tau)),
            "E": list(core.E),
            "equal": core.compose(S5, tau) == core.E}


def walk_from_events(abandon_phase, events, o_star):
    phases = [abandon_phase]
    syms = []
    for e in events:
        if e["target_orbit"] == o_star:
            phases.append(e["target_phase"])
            syms.append(e["sym"])
    deltas = [(phases[i + 1] - phases[i]) % 5 for i in range(len(phases) - 1)]
    A = (phases[-1] - phases[0]) % 5
    total = sum(deltas)
    k = (total - A) // 5 if (total - A) % 5 == 0 else None
    nE = sum(1 for s in syms if s != "R")
    nRodd = sum(1 for s, d in zip(syms, deltas) if s == "R" and d % 2 == 1)
    nReven = sum(1 for s, d in zip(syms, deltas) if s == "R" and d % 2 == 0)
    return {"phases": phases, "deltas": deltas, "step_symbols": syms,
            "A_total_advance": A, "sum_deltas": total, "winding_k": k,
            "n_E_steps": nE, "n_R_odd_delta": nRodd, "n_R_even_delta": nReven,
            "identity_lhs": nE % 2,
            "identity_rhs": None if k is None else (k + nRodd) % 2,
            "identity_holds": None if k is None else (nE % 2) == ((k + nRodd) % 2)}


def historical():
    p = ROOT / "outputs" / "rr_ordered_event_words.json"
    if not p.exists():
        return {"available": False}
    rows = [r for r in json.loads(p.read_text(encoding="utf-8"))["rows"]
            if r["landing_class"] == "O_star"]
    ok, bad, rodd = 0, 0, Counter()
    zhist = Counter()
    for r in rows:
        # the ordered ledger's O_star_phase_sequence already starts at the
        # abandonment phase
        seq = r["O_star_phase_sequence"]
        syms = [e["sym"] for e in r["events"] if e["target_orbit"] == r["o_star"]]
        deltas = [(seq[i + 1] - seq[i]) % 5 for i in range(len(seq) - 1)]
        A = (seq[-1] - seq[0]) % 5
        k = (sum(deltas) - A) // 5
        nE = sum(1 for s in syms if s != "R")
        nRodd = sum(1 for s, d in zip(syms, deltas) if s == "R" and d % 2 == 1)
        rodd[nRodd] += 1
        zhist[nE] += 1
        if (nE % 2) == ((k + nRodd) % 2):
            ok += 1
        else:
            bad += 1
    return {"available": True, "n": len(rows), "identity_holds": ok,
            "identity_fails": bad,
            "n_R_odd_delta_histogram": {str(k): v for k, v in sorted(rodd.items())},
            "n_Z_to_O_star_histogram": {str(k): v for k, v in sorted(zhist.items())},
            "collapsed_form_valid_here": all(k == 0 for k in rodd)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_corrected_phase_identity.json"))
    a = ap.parse_args()

    gid = check_generator_identity()
    print(f"=== step 2's group fact ===")
    print(f"   Sigma^5 o tau = {gid['Sigma5_compose_tau']}, E = {gid['E']} -> equal: {gid['equal']}")
    assert gid["equal"]

    hist = historical()
    if hist["available"]:
        print(f"\n=== historical special case ({hist['n']} completions, depth<=6) ===")
        print(f"   identity holds {hist['identity_holds']}, fails {hist['identity_fails']}")
        print(f"   #R_odd-delta histogram: {hist['n_R_odd_delta_histogram']}")
        print(f"   #Z_to_O* histogram    : {hist['n_Z_to_O_star_histogram']}")
        print(f"   collapsed form #Z == k valid in this scope: {hist['collapsed_form_valid_here']}")

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    rows = []
    print(f"\n=== six counterexamples ===")
    print("  #  phases            deltas        syms          #Z  k  #R_odd  lhs rhs  ok")
    for i, w in enumerate(wits):
        o = w["o_star"]
        ev = [{"target_orbit": t["target_orbit"], "target_phase": t["target_phase"],
               "sym": t["sym"]} for t in w["trace"][:w["C_index"] + 1]]
        r = walk_from_events(w["O_star_phase_sequence"][0], ev, o)
        r["witness_index"] = i
        rows.append(r)
        print(f"  {i}  {str(r['phases']):<17} {str(r['deltas']):<13} "
              f"{str(r['step_symbols']):<13} {r['n_E_steps']:>2}  {r['winding_k']}  "
              f"{r['n_R_odd_delta']:>5}   {r['identity_lhs']}   {r['identity_rhs']}   "
              f"{r['identity_holds']}")
    allok = all(r["identity_holds"] for r in rows)
    print(f"\n  identity holds on all six: {allok}")
    print(f"  collapsed form #Z == k holds on any of them: "
          f"{any(r['identity_lhs'] == (r['winding_k'] % 2) for r in rows)}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-corrected-phase-identity-v1",
        "theorem": "#Z_{->O*} == k + #R_{odd-delta} (mod 2)",
        "grade": "손증명",
        "definitions": {
            "O_star_phase_walk": ("phases of O* visited in word order, starting from the "
                                  "phase the abandonment joint lands on"),
            "delta": "(phase_{i+1} - phase_i) mod 5 -- relative to the PREVIOUS O* phase",
            "n_R_odd_delta": ("R events that are STEPS OF THE O* WALK and whose delta is "
                              "odd; R events not targeting O* are not counted"),
            "k": "sum(delta) = A + 5k with A = (last - first) mod 5",
            "n_Z_to_O_star": "zero-charge events targeting O*, counted over P_core . C",
        },
        "proof_steps": [
            "F never targets O* (O* is already open), so #Z = #E",
            "every E step has delta +1, because Sigma^5 o tau = E exactly",
            "sum(delta) = A + 5k by definition of k",
            "reduce mod 2 and split by event type",
        ],
        "generator_identity_check": gid,
        "historical_special_case": hist,
        "six_counterexample_application": rows,
        "holds_on_all_six": allok,
        "separation_note": ("this identity is NOT used by the terminal normal form proof "
                            "and is kept as a standalone result, per the round's "
                            "instruction"),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
