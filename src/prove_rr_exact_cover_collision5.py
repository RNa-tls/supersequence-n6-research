#!/usr/bin/env python3
"""Round 78 — the exact-cover obstruction at ``COLLISIONS = 5``.

Round 77 proved ``COLLISIONS(s) = 5*O - |covered(s)| <= 5`` is necessary for an Area-A NR6
completion.  A state at ``COLLISIONS = 5`` has spent the entire collision budget, so every
orbit it still opens must add **zero** further collision.  That pins the future exactly:

    THE INSTANCE.  Let ``C`` be the hexagons already met by an open orbit, ``U`` its
    complement, and ``K = 25 - O`` the orbits still to open.  Each of those K orbits must
    have all five of its port-hexagons inside ``U`` (a port in ``C`` would raise a
    ``c(h)`` that is already >= 1), and the K chosen blocks must be pairwise disjoint (a
    shared hexagon is likewise a new collision).  Every hexagon must end covered, so their
    union is ``U``.  With ``|U| = 120 - (5*O - 5) = 5*(25 - O) = 5K`` the counting is
    exactly tight:

        the K orbits still to be opened must form an EXACT COVER of U
        by 5-element blocks of the fixed orbit-hexagon incidence system.

A block lies inside ``U`` only if its orbit is still closed, so the instance is a function
of ``U`` alone -- ``frozenset(U)`` is a complete canonical key.  It is also invariant under
free ``E^1`` motion, which opens no orbit (verified by ``--check e1``).

Necessary tests are applied before any search, cheapest first:

  A COVERABILITY   every ``h in U`` lies in at least one block contained in ``U``
  B SUPPLY         at least K such blocks exist
  C FORCED         a hexagon with a unique supplier forces that block; forced blocks must
                   be pairwise disjoint
  D COMPONENTS     a block lies inside one connected component, so each component's size
                   must be a multiple of 5 and hold at least size/5 blocks

Then Algorithm X, run to completion per component.  Exceeding the node cap is reported as
UNKNOWN and never as UNSAT.  ``--check solver`` runs a positive control (an exact cover of
all 120 hexagons must be found), a negative control, and re-decides every UNSAT with a
different variable-selection order.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
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

PORT_HEXBIT = [[exact.HEX_POSITION[w] for w in core.ports_of_e_orbit(core.E_REPS[q])]
               for q in range(NORB)]
PORT_HEX = [[h for h, _ in PORT_HEXBIT[q]] for q in range(NORB)]
BLOCK = [frozenset(PORT_HEX[q]) for q in range(NORB)]
NODE_CAP = 20_000_000


# --------------------------------------------------------------------- exact cover


def algorithm_x(universe, blocks, want=1, mrv=True, cap=NODE_CAP):
    """Complete exact-cover search.  Returns (solutions, witness, nodes, completed).

    ``completed`` False means the node cap was hit; the caller must report UNKNOWN, never
    UNSAT.  Selecting one element and branching over every block containing it is
    exhaustive, because any exact cover contains exactly one such block.
    """
    by_element = defaultdict(list)
    for i, b in enumerate(blocks):
        for h in b:
            by_element[h].append(i)
    state = {"n": 0, "nodes": 0, "done": True, "witness": None}

    def rec(remaining, chosen):
        if not remaining:
            state["n"] += 1
            if state["witness"] is None:
                state["witness"] = list(chosen)
            return state["n"] >= want
        state["nodes"] += 1
        if state["nodes"] > cap:
            state["done"] = False
            return True
        if mrv:
            h = min(remaining,
                    key=lambda x: sum(1 for i in by_element[x] if blocks[i] <= remaining))
        else:
            h = min(remaining)
        for i in by_element[h]:
            if blocks[i] <= remaining:
                chosen.append(i)
                if rec(remaining - blocks[i], chosen):
                    return True
                chosen.pop()
        return False

    rec(frozenset(universe), [])
    return state["n"], state["witness"], state["nodes"], state["done"]


def connected_components(universe, blocks):
    adjacent = defaultdict(set)
    for b in blocks:
        members = list(b)
        for x in members:
            adjacent[x].update(members)
    seen, out = set(), []
    for h in universe:
        if h in seen:
            continue
        stack, comp = [h], set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            stack.extend(adjacent[x] - comp)
        seen |= comp
        out.append(comp)
    return out


def decide(U, K, want_count=1):
    """Decide one instance.  Cheap necessary tests first, then a complete search."""
    U = frozenset(U)
    candidates = [q for q in range(NORB) if BLOCK[q] <= U]
    blocks = [BLOCK[q] for q in candidates]
    rec = dict(size_U=len(U), K=K, candidates=len(candidates))
    if len(U) != 5 * K:
        rec["verdict"] = "MALFORMED_identity"
        return rec

    supplier = defaultdict(list)
    for q in candidates:
        for h in BLOCK[q]:
            supplier[h].append(q)

    uncoverable = sorted(h for h in U if not supplier[h])
    if uncoverable:
        rec.update(verdict="UNSAT_coverability", witness_uncoverable_hexagons=uncoverable)
        return rec
    if len(candidates) < K:
        rec.update(verdict="UNSAT_supply")
        return rec

    forced = sorted({supplier[h][0] for h in U if len(supplier[h]) == 1})
    rec["forced_blocks"] = len(forced)
    for i, a in enumerate(forced):
        for b in forced[i + 1:]:
            if BLOCK[a] & BLOCK[b]:
                rec.update(verdict="UNSAT_forced_conflict", witness_forced_orbits=forced,
                           witness_conflicting_pair=[a, b],
                           witness_shared_hexagons=sorted(BLOCK[a] & BLOCK[b]))
                return rec

    comps = connected_components(U, blocks)
    rec["components"] = sorted(len(c) for c in comps)
    for c in comps:
        inside = [b for b in blocks if b <= c]
        if len(c) % 5 or len(inside) < len(c) // 5:
            rec.update(verdict="UNSAT_component", witness_component=sorted(c),
                       witness_blocks_inside=len(inside))
            return rec

    nodes = 0
    total = 1
    witness = []
    for c in comps:
        idx = [i for i, b in enumerate(blocks) if b <= c]
        n, w, nd, done = algorithm_x(c, [blocks[i] for i in idx], want=want_count)
        nodes += nd
        if not done and n == 0:
            rec.update(verdict="UNKNOWN_node_cap", search_nodes=nodes)
            return rec
        if n == 0:
            rec.update(verdict="UNSAT_exact_cover", search_nodes=nodes,
                       certificate="complete Algorithm X enumeration, 0 solutions")
            return rec
        total *= n
        witness.extend(candidates[idx[i]] for i in w)
    rec.update(verdict=("SAT_unique" if total == 1 else "SAT_multiple"),
               search_nodes=nodes, exact_covers=total, witness_orbits=sorted(witness))
    return rec


# ------------------------------------------------------------------------- checks


def check_solver(instances=None) -> dict:
    n, w, nodes, _ = algorithm_x(frozenset(range(NHEX)), BLOCK, want=1)
    positive = bool(n) and len(w) == 24 and len(set().union(*(BLOCK[i] for i in w))) == NHEX
    U_bad = frozenset(range(NHEX)) - {0}
    n2, _, _, done2 = algorithm_x(U_bad, [b for b in BLOCK if b <= U_bad], want=1)
    out = dict(positive_control_finds_full_cover=positive, positive_control_nodes=nodes,
               negative_control_solutions=n2, negative_control_complete=done2)
    if instances:
        disagreements = 0
        for U in instances:
            U = frozenset(U)
            n3, _, _, done3 = algorithm_x(U, [b for b in BLOCK if b <= U], want=1, mrv=False)
            if n3 or not done3:
                disagreements += 1
        out["unsat_recheck_instances"] = len(instances)
        out["unsat_recheck_disagreements"] = disagreements
    return out


def check_e1(states) -> dict:
    """The instance must be untouched by free E^1 motion (Round 77)."""
    w2 = next(m for m in macro.NONROT_H0 if m.label == "w2:10")

    def step(st):
        runs = macro.rotation_runs(st)
        if runs[-1].ell != 5:
            return None
        tr = exact.extend(runs[-1].state, w2)
        return tr.state if tr is not None else None

    def uncovered(om):
        cov = set()
        for q in range(NORB):
            if om[q]:
                cov |= BLOCK[q]
        return frozenset(range(NHEX)) - cov

    tested = steps = changed_U = changed_family = 0
    for st in states:
        O = sum(1 for m in st.orbit_masks if m)
        U0 = uncovered(st.orbit_masks)
        if 5 * O - (NHEX - len(U0)) != 5:
            continue
        tested += 1
        fam0 = frozenset(q for q in range(NORB) if BLOCK[q] <= U0)
        cur = st
        for _ in range(10):
            nxt = step(cur)
            if nxt is None or macro.area_a_prune_reason(nxt, AREA_A) is not None:
                break
            steps += 1
            U1 = uncovered(nxt.orbit_masks)
            if U1 != U0:
                changed_U += 1
            if frozenset(q for q in range(NORB) if BLOCK[q] <= U1) != fam0:
                changed_family += 1
            cur = nxt
    return dict(states_tested=tested, e1_steps=steps,
                uncovered_set_changed=changed_U, candidate_family_changed=changed_family)


# ------------------------------------------------------------------------- census


def census(checkpoint_dir: Path) -> dict:
    """Decide every COLLISIONS = 5 residual state, canonicalising instances by U."""
    agg = Counter()
    cache = {}
    identity_failures = 0
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
            D = 5 * O - P
            Ndef = S + F - O
            Phi = 5 + 6 * (TP - P) - (720 - visited)
            if F > 1 or H > 0 or P > TP or O > TO or Ndef > NLIM:
                continue
            rem = TP - P
            num = TD - D + rem
            if not (rem >= 0 and num % 5 == 0 and 0 <= num // 5 <= rem):
                continue
            if 720 - visited < rem or Phi < 0 or (TO - O) > rem + (1 - F):
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
            if len(live_elsewhere) - kept > Rcap + Phi:
                continue
            covered = set()
            for q in range(NORB):
                if om[q]:
                    covered |= BLOCK[q]
            collisions = 5 * O - len(covered)
            if collisions > 5:
                continue
            agg["residual_round77"] += 1
            if collisions != 5:
                agg["collisions_below_5"] += 1
                agg["RESIDUAL_new"] += 1
                continue
            agg["collisions_eq_5"] += 1
            U = frozenset(range(NHEX)) - covered
            K = TO - O
            if len(U) != 5 * K:
                identity_failures += 1
            if U not in cache:
                cache[U] = decide(U, K)
            verdict = cache[U]["verdict"]
            agg[verdict] += 1
            if not verdict.startswith("UNSAT"):
                agg["RESIDUAL_new"] += 1
        print(f"{key:16s} instances={len(cache):6d}", flush=True)
        del data
    return dict(aggregate=dict(agg), identity_failures=identity_failures,
                distinct_instances=len(cache),
                instances_by_verdict=dict(Counter(v["verdict"] for v in cache.values())))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("census", "check"))
    ap.add_argument("--check", choices=("solver", "e1"), default="solver")
    ap.add_argument("--checkpoints", default=str(ROOT / "outputs" / "rr_target_a_checkpoints"))
    ap.add_argument("--states", help="pickle of residual states, for --check e1")
    ap.add_argument("--out")
    args = ap.parse_args()

    result = {}
    if args.command == "check" and args.check == "solver":
        result["solver"] = check_solver()
        print(json.dumps(result["solver"], indent=1))
    elif args.command == "check":
        import pickle
        recs = pickle.load(open(args.states, "rb"))
        states = [exact.ExactState(tuple(r["p"]), tuple(r["hex_masks"]),
                                   tuple(r["orbit_masks"]), F=r["F"], S=r["S"], H=r["H"])
                  for r in recs]
        result["e1"] = check_e1(states)
        print(json.dumps(result["e1"], indent=1))
    else:
        result["census"] = census(Path(args.checkpoints))
        print(json.dumps(result["census"]["aggregate"], indent=1))
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
