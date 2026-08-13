#!/usr/bin/env python3
"""Round 76 — MANDATORY-FINAL-BRIDGE / BRIDGE-CHARGE payoff test.

Background
----------
Let ``T`` be the set of *touched* hexagons (``hex_masks[h] != 0``) and ``P`` the number of
registered pass-starts.  The **incidence excess** is ``r = P - |T|``.  At an Area-A NR6
completion ``P = 121`` and every hexagon is touched, so ``r_final = 1`` exactly, while
``r`` is non-decreasing along every legal walk.  Hence every state with ``r = 0`` must
still create its first bridge.

This module tests the weakest lemma that could turn that observation into a bound:

    "Creating the first bridge from ``r = 0`` necessarily incurs at least one unit of a
     globally charged resource."

Three subcommands, none of which runs a search or re-runs the 33-root frontier:

``types``    exhaustive static classification of every transition type that can raise
             ``r`` from 0 to 1, with the literal engine resource deltas;
``census``   re-reads the stored checkpoint frontiers, replays the Round-71 classification
             (capacity_slack -> dead-port -> orbit-reentry) and reports the ``r``
             distribution of the 200,408 proof-valid residual plus the payoff each
             charge hypothesis would produce;
``witness``  constructs, with the exact engine and from ``initial_state``, a legal
             ``r: 0 -> 1`` event whose cost in ``Phi``, ``Ndef``, ``O`` and ``F`` is zero.

The ``witness`` subcommand is an EXISTENCE argument.  No bounded continuation is used
anywhere as impossibility evidence.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict, deque
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
TP, TO, TD = exact.TARGET_P, exact.TARGET_O, exact.TARGET_D
NLIM = AREA_A.n_limit
pc = int.bit_count

PORT_HEXBIT = [
    [exact.HEX_POSITION[w] for w in core.ports_of_e_orbit(core.E_REPS[q])]
    for q in range(NORB)
]

# joint_kind -> (dS, dF, dO); the four labels the macro layer admits.
JOINT_KIND = {
    (2, False, False): ("Z2", 0, 0, 0),
    (2, True, True): ("Z2abandon", 0, 1, 1),
    (3, False, False): ("R", 1, 0, 0),
    (3, False, True): ("Z3", 1, 0, 1),
}


def coordinates(state) -> dict:
    """Every quantity the bound stack uses, recomputed from the literal masks."""
    P = sum(pc(m) for m in state.orbit_masks)
    visited = sum(pc(m) for m in state.hex_masks)
    O = sum(1 for m in state.orbit_masks if m)
    T = sum(1 for m in state.hex_masks if m)
    return dict(
        P=P, visited=visited, O=O, T=T, D=5 * O - P, Ndef=state.S + state.F - O,
        Phi=5 + 6 * (TP - P) - (720 - visited), r=P - T, F=state.F, S=state.S, H=state.H,
    )


# --------------------------------------------------------------------------- types


def transition_types() -> dict:
    """Every (rotation-run length, joint) type, with its literal resource deltas.

    ``r`` rises by one exactly when the joint's target hexagon was already touched, so
    the classification below is complete: a rotation step never registers and never
    touches a fresh hexagon, and every macro edge carries exactly one joint.
    """
    sigma = core.SIGMA
    hex_of = {w: exact.HEX_POSITION[w][0] for w in core.ALL_WORDS}
    orbit_of = {w: exact.ORBIT_PHASE[w][0] for w in core.ALL_WORDS}

    geometry = defaultdict(Counter)
    lands_in_current_hexagon = Counter()
    for p in core.ALL_WORDS:
        pp = p
        for ell in range(6):
            if ell:
                pp = core.word_after(pp, sigma)
            for move in macro.NONROT_H0:
                t = core.word_after(pp, move.action)
                same_hex = hex_of[t] == hex_of[p]
                geometry[(ell, move.label)][
                    ("same_hex" if same_hex else "other_hex",
                     "same_orbit" if orbit_of[t] == orbit_of[p] else "other_orbit")
                ] += 1
                if same_hex:
                    lands_in_current_hexagon[(ell, move.label)] += 1

    rows = []
    for ell in range(6):
        d_phi = ell - 5                       # 6*(-dP) + (ell + 1) visited windows
        for move in macro.NONROT_H0:
            for (w, ab, no), (kind, dS, dF, dO) in JOINT_KIND.items():
                if w != move.weight:
                    continue
                if ell == 5 and ab:
                    continue  # sigma(p') = p is visited, so abandonment cannot occur
                rows.append(dict(
                    ell=ell, joint=move.label, weight=move.weight, kind=kind,
                    abandonment=ab, new_orbit=no,
                    dPhi=d_phi, dNdef=dS + dF - dO, dO=dO, dF=dF, dP=1,
                    shared_cost=(-d_phi) + (dS + dF - dO),
                ))
    rows.sort(key=lambda r: (r["shared_cost"], r["dO"], r["dF"], r["ell"]))
    zero = [r for r in rows
            if r["shared_cost"] == 0 and r["dO"] == 0 and r["dF"] == 0]
    return dict(
        geometry={f"ell={k[0]},{k[1]}": {f"{a}/{b}": n for (a, b), n in v.items()}
                  for k, v in sorted(geometry.items())},
        joints_landing_in_current_hexagon={str(k): v for k, v in lands_in_current_hexagon.items()},
        cost_rows=rows,
        zero_cost_types=zero,
    )


# -------------------------------------------------------------------------- census


def residual_census(checkpoint_dir: Path) -> dict:
    """Replay the Round-71 classification and census ``r`` on the surviving residual."""
    agg = Counter()
    r_by_root = defaultdict(Counter)
    r_by_coord = {k: defaultdict(Counter) for k in ("P", "O", "Phi", "Rcap", "Ddead", "used")}
    classes_r0 = Counter()
    classes_all = Counter()
    slack_r0 = Counter()
    margin_r0 = Counter()
    payoff = Counter()

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
            # ---- Q2 / Area-A admissibility ----
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
            agg["q2_admissible"] += 1
            q0 = exact.ORBIT_PHASE[tuple(st["p"])][0]
            used = pc(om[q0])
            Rcap = max(NLIM - Ndef, 0)
            slack = (5 - used) + 5 * (TO - O) + 4 * (Rcap + Phi) - rem
            if slack < 0:
                agg["closed_capacity_slack"] += 1
                continue
            agg["survives_capacity_slack"] += 1
            # ---- dead-port census over open orbits ----
            Ddead = 0
            live_elsewhere = []
            for q in range(NORB):
                mask = om[q]
                if not mask:
                    continue
                dead = live = 0
                for ph in range(5):
                    if mask & (1 << ph):
                        continue
                    h, b = PORT_HEXBIT[q][ph]
                    if hm[h] & (1 << b):
                        dead += 1
                    else:
                        live += 1
                Ddead += dead
                if q != q0 and live:
                    live_elsewhere.append(live)
            if Ddead > TD:
                agg["closed_dead_port"] += 1
                continue
            # ---- orbit re-entry (demand-side) ----
            budget = TD - Ddead
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
                agg["closed_orbit_reentry"] += 1
                continue
            # ---- residual ----
            agg["RESIDUAL"] += 1
            r = P - T
            agg[f"r={r}"] += 1
            r_by_root[key][r] += 1
            cls = (Ndef, Phi, Rcap, O, P, D, Ddead, need, used)
            classes_all[cls] += 1
            for name, value in (("P", P), ("O", O), ("Phi", Phi), ("Rcap", Rcap),
                                ("Ddead", Ddead), ("used", used)):
                r_by_coord[name][value][r] += 1
            if r == 0:
                classes_r0[cls] += 1
                slack_r0[slack] += 1
                margin_r0[(Rcap + Phi) - need] += 1
                if (5 - used) + 5 * (TO - O) + 4 * (Rcap + Phi - 1) - rem < 0:
                    payoff["capacity_slack_shared_minus_1"] += 1
                if need > Rcap + Phi - 1:
                    payoff["orbit_reentry_shared_minus_1"] += 1
                if Ddead + 1 > TD:
                    payoff["dead_port_plus_1"] += 1
        print(f"{key:16s} residual={sum(r_by_root[key].values()):7d} "
              f"r={dict(sorted(r_by_root[key].items()))}", flush=True)
        del data

    return dict(
        aggregate=dict(agg),
        r_by_root={k: dict(sorted(v.items())) for k, v in r_by_root.items() if v},
        r_by_coordinate={n: {str(v): dict(sorted(c.items()))
                             for v, c in sorted(d.items())} for n, d in r_by_coord.items()},
        residual_classes_total=len(classes_all),
        residual_classes_r0=len(classes_r0),
        capacity_slack_distribution_r0=dict(sorted(slack_r0.items())),
        orbit_reentry_margin_r0=dict(sorted(margin_r0.items())),
        payoff_if_lemma_held=dict(payoff),
    )


# ------------------------------------------------------------------------- witness


def zero_cost_witness(max_nodes: int = 60000, max_depth: int = 6) -> dict:
    """Find a legal ``r: 0 -> 1`` macro edge costing nothing in Phi, Ndef, O or F.

    Positive existence only.  Failure to find one within the bound proves nothing and is
    reported as ``None``.
    """
    start = exact.initial_state()
    seen = {start.stable_key()}
    queue = deque([(start, [])])
    expanded = 0
    while queue and expanded < max_nodes:
        state, path = queue.popleft()
        expanded += 1
        before = coordinates(state)
        for edge in macro.macro_edges(state):
            child = edge.state
            if macro.area_a_prune_reason(child, AREA_A) is not None:
                continue
            after = coordinates(child)
            if (before["r"] == 0 and after["r"] == 1
                    and after["Phi"] == before["Phi"] and after["Ndef"] == before["Ndef"]
                    and after["O"] == before["O"] and after["F"] == before["F"]):
                q_before = exact.ORBIT_PHASE[state.p][0]
                q_after = exact.ORBIT_PHASE[child.p][0]
                target_hex = exact.HEX_POSITION[edge.joint.target][0]
                return dict(
                    macro_path=path + [edge.label],
                    parent=before, child=after,
                    ell=edge.run.ell, joint=edge.joint.move.label,
                    joint_weight=edge.joint.move.weight,
                    abandonment=edge.joint.abandonment, new_orbit=edge.joint.new_orbit,
                    joint_kind=JOINT_KIND[(edge.joint.move.weight, edge.joint.abandonment,
                                           edge.joint.new_orbit)][0],
                    orbit_preserved=q_before == q_after,
                    target_hex=target_hex,
                    target_hex_popcount_before=pc(edge.run.state.hex_masks[target_hex]),
                    target_hex_popcount_after=pc(child.hex_masks[target_hex]),
                    used_q0_before=pc(state.orbit_masks[q_before]),
                    used_q0_after=pc(child.orbit_masks[q_after]),
                    nodes_expanded=expanded,
                )
            key = child.stable_key()
            if key not in seen and len(path) < max_depth:
                seen.add(key)
                queue.append((child, path + [edge.label]))
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("types", "census", "witness", "all"))
    ap.add_argument("--checkpoints", default=str(ROOT / "outputs" / "rr_target_a_checkpoints"))
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {}
    if args.command in ("types", "all"):
        result["transition_types"] = transition_types()
        zero = result["transition_types"]["zero_cost_types"]
        print("zero-cost r:0->1 transition types:",
              [(r["ell"], r["joint"], r["kind"]) for r in zero])
    if args.command in ("witness", "all"):
        result["zero_cost_witness"] = zero_cost_witness()
        print("witness:", json.dumps(result["zero_cost_witness"], indent=1))
    if args.command in ("census", "all"):
        result["census"] = residual_census(Path(args.checkpoints))
        print("census aggregate:", result["census"]["aggregate"])
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
