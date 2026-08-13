#!/usr/bin/env python3
"""Round 77 — E^1 QUOTIENT and the ORBIT-HEXAGON COVER inequality.

Rounds 74-76 each died the same way: the event a candidate wanted to forbid or charge
could be realised for free by ``E^1`` = the macro edge ``(ell = 5, w2:10)``, the unique
generator that is free in ``Phi``, ``Ndef``, ``O`` and ``F``.  This module first quotients
``E^1`` out -- treating arbitrary legal ``E^1`` motion as free from the start -- and then
states the obstruction that survives it.

THE THEOREM (ORBIT-HEXAGON COVER)
---------------------------------
Geometry (verified, not assumed): each of the 144 E-orbits has 5 ports lying in 5
*distinct* hexagons, and each of the 120 hexagons meets exactly 6 orbits -- 720
incidences, biregular.

At an Area-A NR6 completion ``area_a_final`` demands ``visited_count == 720``, so every
hexagon is full.  A hexagon is only ever entered by a joint landing in it (a rotation
never leaves the current hexagon), every joint has weight >= 2 and therefore registers its
target's (orbit, phase), and the initial window is registered too.  Hence:

    every hexagon contains at least one registered port, so at least one of the 6 orbits
    meeting it is open.

Writing ``c(h)`` for the number of open orbits meeting hexagon ``h``, the completion has
``O = 25`` open orbits contributing exactly ``5 * 25 = 125`` incidences over 120 hexagons
with ``c(h) >= 1`` throughout, so

    sum_h ( c(h) - 1 )  =  125 - 120  =  5 .

Orbit masks are only ever set, never cleared, so the open set grows monotonically and
``c_open(h) <= c_final(h)`` pointwise.  Therefore at every state on a path to an Area-A
completion:

    COLLISIONS(s) = sum_h max( c_open(h) - 1, 0 )  =  5*O - |covered(s)|  <=  5 .

Equivalently ``120 - |covered(s)| <= 5 * (25 - O)``: the orbits still to be opened must
cover every hexagon no open orbit reaches yet.  Sharpening the right-hand side by the
actual per-orbit contribution gives ``cover_capacity`` below.

This is demand-side: it never estimates how far a walk can travel, only which orbits must
end up open.  It is untouched by q0 return, by repeated re-entry, and -- the point of this
round -- by ``E^1``, which opens no orbit and so leaves ``COLLISIONS`` literally fixed.

Subcommands: ``geometry`` / ``e1`` / ``census`` / ``feasibility``.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import pickle
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "superperm_partial_f1_macro",
    ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py",
)
macro = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = macro
_SPEC.loader.exec_module(macro)

exact = macro.exact
core = macro.core
AREA_A = macro.AREA_A
NORB = len(core.E_REPS)
NHEX = len(core.ROT_REPS)
TP, TO, TD = exact.TARGET_P, exact.TARGET_O, exact.TARGET_D
NLIM = AREA_A.n_limit
pc = int.bit_count
FULL_HEX = 63

PORT_HEXBIT = [[exact.HEX_POSITION[w] for w in core.ports_of_e_orbit(core.E_REPS[q])]
               for q in range(NORB)]
PORT_HEX = [[h for h, _ in PORT_HEXBIT[q]] for q in range(NORB)]
E1_JOINT = next(m for m in macro.NONROT_H0 if m.label == "w2:10")


# ------------------------------------------------------------------ the quantity


def cover_state(orbit_masks) -> dict:
    """COLLISIONS, coverage and both cover capacities, from the orbit masks alone."""
    covered = set()
    open_count = 0
    for q in range(NORB):
        if orbit_masks[q]:
            open_count += 1
            covered.update(PORT_HEX[q])
    uncovered = NHEX - len(covered)
    remaining = TO - open_count
    collisions = 5 * open_count - len(covered)
    # sharpened capacity: only the uncovered hexagons a closed orbit actually reaches
    contributions = sorted(
        (sum(1 for h in PORT_HEX[q] if h not in covered)
         for q in range(NORB) if not orbit_masks[q]),
        reverse=True,
    )[:max(remaining, 0)]
    return dict(open_orbits=open_count, covered=len(covered), uncovered=uncovered,
                collisions=collisions, plain_capacity=5 * max(remaining, 0),
                cover_capacity=sum(contributions))


def cover_violation(orbit_masks) -> str | None:
    c = cover_state(orbit_masks)
    if c["collisions"] > 5:
        return "orbit_hexagon_cover_plain"
    if c["uncovered"] > c["cover_capacity"]:
        return "orbit_hexagon_cover_sharp"
    return None


# ---------------------------------------------------------------------- geometry


def geometry() -> dict:
    per_orbit = Counter(len(set(PORT_HEX[q])) for q in range(NORB))
    per_hex = Counter()
    for q in range(NORB):
        for h in PORT_HEX[q]:
            per_hex[h] += 1
    return dict(
        orbits=NORB, hexagons=NHEX,
        distinct_hexagons_per_orbit=dict(sorted(per_orbit.items())),
        orbits_per_hexagon=dict(sorted(Counter(per_hex.values()).items())),
        total_incidences=sum(per_hex.values()),
        biregular=(set(per_orbit) == {5} and set(per_hex.values()) == {6}),
    )


def feasibility(trials: int = 4000, seed: int = 0) -> dict:
    """A 25-orbit set covering all 120 hexagons must exist, or the bound is vacuous."""
    random.seed(seed)
    best = None
    for _ in range(trials):
        covered: set[int] = set()
        chosen: list[int] = []
        while len(chosen) < TO:
            q = max((q for q in range(NORB) if q not in chosen),
                    key=lambda q: len(set(PORT_HEX[q]) - covered))
            chosen.append(q)
            covered |= set(PORT_HEX[q])
        excess = 5 * TO - len(covered)
        if best is None or excess < best[0]:
            best = (excess, len(covered), sorted(chosen))
        if excess <= 5:
            break
    return dict(best_excess=best[0], hexagons_covered=best[1],
                full_cover_exists=best[1] == NHEX, witness_orbits=best[2])


# -------------------------------------------------------------------- E^1 audit


def e1_step(state):
    """The unique universally-free generator: a full rotation run then ``w2:10``."""
    runs = macro.rotation_runs(state)
    if runs[-1].ell != 5:
        return None
    tr = exact.extend(runs[-1].state, E1_JOINT)
    return tr.state if tr is not None else None


def quantities(state) -> dict:
    hm, om = state.hex_masks, state.orbit_masks
    P = sum(pc(m) for m in om)
    visited = sum(pc(m) for m in hm)
    O = sum(1 for m in om if m)
    T = sum(1 for m in hm if m)
    q0 = exact.ORBIT_PHASE[state.p][0]
    current = exact.HEX_POSITION[state.p][0]
    dead = 0
    live_elsewhere = []
    for q in range(NORB):
        mask = om[q]
        if not mask:
            continue
        dq = lq = 0
        for ph in range(5):
            if mask & (1 << ph):
                continue
            h, b = PORT_HEXBIT[q][ph]
            if hm[h] & (1 << b):
                dq += 1
            else:
                lq += 1
        dead += dq
        if q != q0 and lq:
            live_elsewhere.append(lq)
    Ndef = state.S + state.F - O
    Rcap = max(NLIM - Ndef, 0)
    Phi = 5 + 6 * (TP - P) - (720 - visited)
    budget = TD - dead
    live_elsewhere.sort()
    acc = kept = 0
    for x in live_elsewhere:
        if acc + x <= budget:
            acc += x
            kept += 1
        else:
            break
    partial = [h for h in range(NHEX) if hm[h] not in (0, FULL_HEX)]
    cov = cover_state(om)
    return dict(
        D=5 * O - P, dead_port_count=dead,
        orbit_reentry_demand=len(live_elsewhere) - kept, r=P - T,
        touched_hexagons=T, full_hexagons=sum(1 for m in hm if m == FULL_HEX),
        partial_hexagons=len(partial),
        noncurrent_partial=len([h for h in partial if h != current]),
        hexagon_deficiency=sum(6 - pc(hm[h]) for h in partial),
        incidence_collisions=cov["collisions"], covered_hexagons=cov["covered"],
        open_orbits=O, used_q0=pc(om[q0]), phase_of_p=exact.ORBIT_PHASE[state.p][1],
        Ndef=Ndef, Phi=Phi, Rcap=Rcap, shared_budget=Rcap + Phi, P=P, F=state.F,
    )


def e1_audit(states) -> dict:
    """Classify every candidate quantity over the full E^1-closure of each state."""
    deltas = defaultdict(Counter)
    chain = Counter()
    steps = 0
    for state in states:
        cur = state
        qs = quantities(cur)
        n = 0
        while n < 10:
            nxt = e1_step(cur)
            if nxt is None or macro.area_a_prune_reason(nxt, AREA_A) is not None:
                break
            qn = quantities(nxt)
            for k in qs:
                deltas[k][qn[k] - qs[k]] += 1
            cur, qs = nxt, qn
            n += 1
            steps += 1
        chain[n] += 1
    out = {}
    for k, d in deltas.items():
        obs = dict(sorted(d.items()))
        if set(obs) == {0}:
            cls = "invariant"
        elif all(x >= 0 for x in obs):
            cls = "monotone_non_decreasing"
        elif all(x <= 0 for x in obs):
            cls = "monotone_non_increasing"
        else:
            cls = "freely_repairable"
        out[k] = dict(observed_deltas=obs, classification=cls)
    return dict(states=len(states), e1_steps=steps,
                closure_chain_length=dict(sorted(chain.items())), quantities=out)


# ----------------------------------------------------------------------- census


def census(checkpoint_dir: Path) -> dict:
    """Payoff of the cover bound on the Round-71 residual, replayed from checkpoints."""
    agg = Counter()
    closed_by_root = Counter()
    surv_by_root = Counter()
    surv_coord = defaultdict(Counter)
    surv_classes = Counter()
    collision_dist = Counter()

    for path in sorted(glob.glob(str(checkpoint_dir / "*.json"))):
        key = os.path.basename(path)[:-5]
        data = json.load(open(path))
        for entry in data["frontier"]:
            st = entry["state"]
            hm, om = st["hex_masks"], st["orbit_masks"]
            F, S, H = st["F"], st["S"], st["H"]
            P = sum(pc(m) for m in om)
            visited = sum(pc(m) for m in hm)
            O = sum(1 for m in om if m)
            T = sum(1 for m in hm if m)
            D = 5 * O - P
            Ndef = S + F - O
            Phi = 5 + 6 * (TP - P) - (720 - visited)
            if F > 1 or H > 0 or P > TP or O > TO or Ndef > NLIM:
                continue
            rem = TP - P
            num = TD - D + rem
            if not (rem >= 0 and num % 5 == 0 and 0 <= num // 5 <= rem):
                continue
            if 720 - visited < rem or Phi < 0:
                continue
            if (TO - O) > rem + (1 - F):
                continue
            q0 = exact.ORBIT_PHASE[tuple(st["p"])][0]
            used = pc(om[q0])
            Rcap = max(NLIM - Ndef, 0)
            if (5 - used) + 5 * (TO - O) + 4 * (Rcap + Phi) - rem < 0:
                continue
            dead = 0
            live_elsewhere = []
            for q in range(NORB):
                mask = om[q]
                if not mask:
                    continue
                dq = lq = 0
                for ph in range(5):
                    if mask & (1 << ph):
                        continue
                    h, b = PORT_HEXBIT[q][ph]
                    if hm[h] & (1 << b):
                        dq += 1
                    else:
                        lq += 1
                dead += dq
                if q != q0 and lq:
                    live_elsewhere.append(lq)
            if dead > TD:
                continue
            budget = TD - dead
            live_elsewhere.sort()
            acc = kept = 0
            for x in live_elsewhere:
                if acc + x <= budget:
                    acc += x
                    kept += 1
                else:
                    break
            need = len(live_elsewhere) - kept
            if need > Rcap + Phi:
                continue
            agg["residual_round71"] += 1
            cov = cover_state(om)
            collision_dist[min(cov["collisions"], 20)] += 1
            if cov["collisions"] > 5:
                agg["closed_cover_plain"] += 1
                closed_by_root[key] += 1
                continue
            if cov["uncovered"] > cov["cover_capacity"]:
                agg["closed_cover_sharp"] += 1
                closed_by_root[key] += 1
                continue
            agg["residual_new"] += 1
            surv_by_root[key] += 1
            surv_classes[(Ndef, Phi, Rcap, O, P, D, dead, need, used)] += 1
            for nm, v in (("P", P), ("O", O), ("Phi", Phi), ("Ndef", Ndef),
                          ("Ddead", dead), ("r", P - T), ("used", used)):
                surv_coord[nm][v] += 1
        print(f"{key:16s} closed={closed_by_root[key]:7d} surviving={surv_by_root[key]:7d}",
              flush=True)
        del data

    return dict(aggregate=dict(agg),
                collision_distribution=dict(sorted(collision_dist.items())),
                closed_by_root=dict(closed_by_root),
                surviving_by_root=dict(surv_by_root),
                surviving_by_coordinate={k: dict(sorted(v.items()))
                                         for k, v in surv_coord.items()},
                surviving_classes=len(surv_classes),
                top_surviving_classes={str(k): v for k, v in surv_classes.most_common(15)})


def monotonicity_check(walks: int = 400, depth: int = 200, seed: int = 7) -> dict:
    """COLLISIONS must never decrease along a legal walk, and must equal 5*O - covered."""
    random.seed(seed)
    bad_identity = bad_monotone = steps = 0
    for _ in range(walks):
        state = exact.initial_state()
        prev = cover_state(state.orbit_masks)["collisions"]
        for _ in range(depth):
            kids = [e.state for e in macro.macro_edges(state)
                    if macro.area_a_prune_reason(e.state, AREA_A) is None]
            if not kids:
                break
            state = random.choice(kids)
            steps += 1
            c = cover_state(state.orbit_masks)
            if 5 * c["open_orbits"] - c["covered"] != c["collisions"]:
                bad_identity += 1
            if c["collisions"] < prev:
                bad_monotone += 1
            prev = c["collisions"]
    return dict(walks=walks, macro_steps=steps,
                identity_violations=bad_identity, monotonicity_violations=bad_monotone)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("geometry", "feasibility", "e1", "census",
                                        "monotonicity", "all"))
    ap.add_argument("--checkpoints", default=str(ROOT / "outputs" / "rr_target_a_checkpoints"))
    ap.add_argument("--states", help="pickle of residual states for the E^1 audit")
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {}
    if args.command in ("geometry", "all"):
        result["geometry"] = geometry()
        print("geometry:", json.dumps(result["geometry"]))
    if args.command in ("feasibility", "all"):
        result["feasibility"] = feasibility()
        print("full 25-orbit cover exists:", result["feasibility"]["full_cover_exists"],
              "excess", result["feasibility"]["best_excess"])
    if args.command in ("monotonicity", "all"):
        result["monotonicity"] = monotonicity_check()
        print("monotonicity:", result["monotonicity"])
    if args.command in ("e1", "all") and args.states:
        recs = pickle.load(open(args.states, "rb"))
        states = [exact.ExactState(tuple(r["p"]), tuple(r["hex_masks"]),
                                   tuple(r["orbit_masks"]), F=r["F"], S=r["S"], H=r["H"])
                  for r in recs]
        result["e1_audit"] = e1_audit(states)
        for k, v in sorted(result["e1_audit"]["quantities"].items()):
            print(f"{k:24s} {v['classification']}")
    if args.command in ("census", "all"):
        result["census"] = census(Path(args.checkpoints))
        print("census:", result["census"]["aggregate"])
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
