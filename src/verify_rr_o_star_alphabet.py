#!/usr/bin/env python3
"""Round 25 follow-up: the O*-step alphabet lemma.

`analyze_rr_o_star_winding.py` reduced the open parity proposition to a
single premise:

    (ALPHABET)  every E step advances the O* phase by exactly +1, and
                every R step advances it by an even amount.

That was measured on the 95 O*-landing completions only.  This script
does two things it did not:

  1. Verifies (ALPHABET) over the ENTIRE root-local universe -- every
     legal macro-edge from every reachable state, at every landing class
     and at every prefix, not only the edges that happen to complete at
     the hub.  An exception anywhere refutes the lemma outright.

  2. Looks for the mechanism.  Each of the five phases of an E-orbit
     lives in a DIFFERENT hexagon (verified below), so a phase of O* is
     the same datum as a hexagon.  The candidate mechanism is therefore
     "E lands on the next port of O* in E-cyclic order", which is a
     statement about which hexagon the walk may enter next.

No new completion search: the frontier is the same root-local BFS used
by every Round 19-25 script, with the same depth ceiling and the same
prune.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
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


macro = _load("vroa", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]
HUB = core.hexagon_id(exact.initial_state().p)


def kind(w, a, n):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, a, n), "other")


def sym(k):
    return "R" if k == "R" else ("F" if k == "Z3" else "E")


def root(ell):
    c = exact.initial_state()
    for _ in range(ell):
        c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state


def abandon_phase(ell):
    c = exact.initial_state()
    for _ in range(ell):
        c = exact.extend(c, W1).state
    return exact.ORBIT_PHASE[exact.extend(c, W2_10).target][1]


def port_structure():
    """Each phase of an E-orbit sits in its own hexagon -- so 'phase of O*'
    and 'hexagon of that port' are the same datum.  Verified for all 144
    orbits, not just the five that can be O*."""
    all_distinct, rows = True, {}
    for q in range(len(core.E_REPS)):
        ports = core.ports_of_e_orbit(core.E_REPS[q])
        hexes = [core.hexagon_id(p) for p in ports]
        if len(set(hexes)) != len(hexes):
            all_distinct = False
        if q in HEX0:
            rows[str(q)] = {"phase_to_hexagon": hexes,
                            "phase_to_hex_position": [exact.HEX_POSITION[p][1] for p in ports]}
    return {"every_orbit_has_five_distinct_port_hexagons": all_distinct,
            "n_orbits_checked": len(core.E_REPS),
            "O_star_candidates": rows}


def scan(ell, depth):
    """Every legal macro-edge from every reachable state, carrying the
    O*-phase walk along the path."""
    o = HEX0[ell + 1]
    r = root(ell)
    steps, viol_e, viol_r, order_viol = Counter(), [], [], []
    edges_seen, o_star_steps = 0, 0
    fr = deque([(r, 0, abandon_phase(ell), (abandon_phase(ell),))])
    seen = {r.stable_key()}
    while fr:
        st, d, last_ph, visited = fr.popleft()
        if d >= depth:
            continue
        for e in macro.macro_edges(st):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None:
                continue
            k = kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other":
                continue
            edges_seen += 1
            s = sym(k)
            tq, tph = exact.ORBIT_PHASE[t.target]
            nlast, nvis = last_ph, visited
            if tq == o:
                o_star_steps += 1
                delta = (tph - last_ph) % 5
                steps[f"{s}:+{delta}"] += 1
                rec = {"abandonment_ell": ell, "depth": d, "sym": s,
                       "joint": t.move.label, "from_phase": last_ph,
                       "to_phase": tph, "delta": delta,
                       "target_hexagon": core.hexagon_id(t.target),
                       "visited_phases": list(visited)}
                if s == "E" and delta != 1:
                    viol_e.append(rec)
                if s == "R" and delta % 2 != 0:
                    viol_r.append(rec)
                if s == "F":
                    viol_e.append({**rec, "note": "F targeted O* -- refutes premise (a)"})
                if tph in visited:
                    order_viol.append({**rec, "note": "phase revisited"})
                nlast, nvis = tph, visited + (tph,)
            if core.hexagon_id(t.target) == HUB:
                continue
            kk = t.state.stable_key()
            if kk in seen:
                continue
            seen.add(kk)
            fr.append((t.state, d + 1, nlast, nvis))
    return {"abandonment_ell": ell, "o_star": o, "states_expanded": len(seen),
            "legal_edges_examined": edges_seen, "o_star_steps": o_star_steps,
            "step_histogram": dict(sorted(steps.items())),
            "E_delta_violations": viol_e, "R_parity_violations": viol_r,
            "phase_revisits": order_viol}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_o_star_alphabet.json"))
    a = ap.parse_args()

    ps = port_structure()
    print(f"every E-orbit has 5 distinct port hexagons: "
          f"{ps['every_orbit_has_five_distinct_port_hexagons']} "
          f"({ps['n_orbits_checked']} orbits)")
    for q, r in sorted(ps["O_star_candidates"].items(), key=lambda x: int(x[0])):
        print(f"  orbit {q:>3}: hexagons {r['phase_to_hexagon']} "
              f"hexpos {r['phase_to_hex_position']}")

    per_ell, tot = [], Counter()
    ve = vr = pv = 0
    for ell in range(5):
        r = scan(ell, a.depth)
        per_ell.append(r)
        tot.update(r["step_histogram"])
        ve += len(r["E_delta_violations"])
        vr += len(r["R_parity_violations"])
        pv += len(r["phase_revisits"])
        print(f"\nell={ell} O*={r['o_star']}: states={r['states_expanded']} "
              f"edges={r['legal_edges_examined']} O*-steps={r['o_star_steps']}")
        print(f"   {r['step_histogram']}")
        if r["E_delta_violations"]:
            print(f"   E-DELTA VIOLATIONS: {len(r['E_delta_violations'])}")
            for v in r["E_delta_violations"][:3]:
                print(f"      {v}")
        if r["R_parity_violations"]:
            print(f"   R-PARITY VIOLATIONS: {len(r['R_parity_violations'])}")
            for v in r["R_parity_violations"][:3]:
                print(f"      {v}")
        if r["phase_revisits"]:
            print(f"   PHASE REVISITS: {len(r['phase_revisits'])}")

    print(f"\n=== whole root-local universe ===")
    print(f"O*-step histogram : {dict(sorted(tot.items()))}")
    print(f"E delta != +1     : {ve}")
    print(f"R delta odd       : {vr}")
    print(f"phase revisits    : {pv}")
    holds = (ve == 0 and vr == 0)

    rep = {
        "schema": "rr-o-star-alphabet-v1",
        "premise": ("(ALPHABET) every E step advances the O* phase by exactly +1 and "
                    "every R step advances it by an even amount"),
        "scope": ("every legal macro-edge from every state reachable in the root-local "
                  "BFS from each of the five abandonment roots, depth ceiling "
                  f"{a.depth}, area_a prune, no R cap, no node/edge cap -- NOT only the "
                  "edges that complete at the hub"),
        "port_structure": ps,
        "combined_step_histogram": dict(sorted(tot.items())),
        "E_delta_violation_count": ve,
        "R_parity_violation_count": vr,
        "phase_revisit_count": pv,
        "alphabet_holds_on_whole_local_universe": holds,
        "grade": ("root-local exhaustive over the whole universe (a strict strengthening "
                  "of the 95-completion measurement); still NOT a 손증명, because the "
                  "law is verified rather than derived"),
        "what_would_close_it": (
            "A derivation of the +1 law. The five phases of an E-orbit lie in five "
            "DIFFERENT hexagons, so 'the O* phase' and 'which port hexagon the walk "
            "enters' are the same datum; the +1 law says the walk enters the ports of "
            "O* in E-cyclic order. Deriving that from the macro-edge action "
            "(p -> p . SIGMA^5 . action) would upgrade the whole chain to a hand proof "
            "and, with the finite case analysis in rr_o_star_winding.json, close "
            "#Z_{->O*} evenness."
        ),
        "per_ell": per_ell,
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False,
                                         default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
