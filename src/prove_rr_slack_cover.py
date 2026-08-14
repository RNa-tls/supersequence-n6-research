#!/usr/bin/env python3
"""Round 79 — the SLACK-COVER generalisation of the Round-78 exact-cover obstruction.

Round 77: ``COLLISIONS(s) = 5*O - |covered(s)| <= 5`` is necessary for an Area-A NR6
completion.  Round 78 solved the ceiling case ``c = 5``.  This module handles ``c < 5``,
where the walk still holds ``b = 5 - c`` units of collision slack.

THE ALGEBRA (all four identities machine-checked, see ``check --check algebra``)

    |U| = 5K - b            with C the covered hexagons, U its complement,
                            K = 25 - O and b = 5 - c.

    For any choice of K blocks, writing m(h) for how many chosen blocks contain h,

        5K - |union \\ C|  =  sum_{h in C} m(h)  +  sum_{h in U} max(m(h) - 1, 0)  =: EXCESS

    and -- the point -- if the chosen blocks COVER U then ``union \\ C`` is exactly U, so

        EXCESS = 5K - |U| = b,  forced.

So "total excess at most b" is **not** an independent constraint: it is the counting slack
in the cover, and it is attained automatically.  What survives as a real restriction is its
per-block consequence -- a chosen block can waste at most b, i.e. ``|block & C| <= b`` --
together with the plain requirement that exactly K closed orbits cover U.

    SLACK-COVER.  There must exist exactly K currently-closed orbits whose 5-hexagon
    blocks cover U.

At ``b = 0`` every block must lie inside U and the blocks must be disjoint, so this reduces
exactly to Round 78's exact cover.  Any orbit meeting U is automatically closed (an open
orbit's five hexagons all lie in C), so the instance is a function of ``(U, b)`` alone.

Necessary tests, applied before any search:

  A COVERABILITY     every ``h in U`` has a candidate supplier
  B WASTE FLOOR      let Z be the hexagons of U reachable only by positive-waste blocks;
                     at most b positive-waste blocks may be chosen, so the b largest
                     ``|block & Z|`` must sum to at least ``|Z|``
  C FORCED EXCESS    uniquely-supplied hexagons force blocks, and the forced set's own
                     excess ``5*|forced| - |union(forced) & U|`` must not exceed b
  D COMPONENT/HALL   a candidate's U-part lies inside one component of U, so
                     ``sum_i ceil(m_i / w_i) <= K`` and ``sum_i (5*ceil(m_i/5) - m_i) <= b``

Then a memoised bitset DFS with MRV, run to completion.  A node cap yields UNKNOWN, never
UNSAT.  ``check --check solver`` runs the decisive positive control: instances synthesised
from a known 25-orbit covering family, which are guaranteed satisfiable.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.setrecursionlimit(10000)
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
ALLHEX = (1 << NHEX) - 1

PORT_HEXBIT = [[exact.HEX_POSITION[w] for w in core.ports_of_e_orbit(core.E_REPS[q])]
               for q in range(NORB)]
PORT_HEX = [[h for h, _ in PORT_HEXBIT[q]] for q in range(NORB)]
BLOCKBITS = [sum(1 << h for h in set(PORT_HEX[q])) for q in range(NORB)]
BLOCK = [frozenset(PORT_HEX[q]) for q in range(NORB)]
NODE_CAP = 300_000


def bits(mask):
    out = []
    while mask:
        low = mask & -mask
        out.append(low.bit_length() - 1)
        mask ^= low
    return out


# ------------------------------------------------------------------------ decide


def decide(U, K, b, node_cap=NODE_CAP, mrv=True):
    """Decide one slack-cover instance.  Cheap necessary tests, then a complete DFS."""
    cand = [q for q in range(NORB) if pc(BLOCKBITS[q] & U) >= 5 - b]
    rec = dict(size_U=pc(U), K=K, b=b, candidates=len(cand))
    supplier = defaultdict(list)
    for q in cand:
        for h in bits(BLOCKBITS[q] & U):
            supplier[h].append(q)

    uncoverable = [h for h in bits(U) if not supplier[h]]
    if uncoverable:
        rec.update(verdict="UNSAT_coverability", witness_uncoverable=uncoverable[:8])
        return rec

    if b:
        Z = [h for h in bits(U) if all(pc(BLOCKBITS[q] & U) < 5 for q in supplier[h])]
        rec["Z_size"] = len(Z)
        if Z:
            zmask = sum(1 << h for h in Z)
            gains = sorted((pc(BLOCKBITS[q] & zmask)
                            for q in cand if pc(BLOCKBITS[q] & U) < 5), reverse=True)[:b]
            if sum(gains) < len(Z):
                rec.update(verdict="UNSAT_waste_floor",
                           witness=dict(Z=len(Z), best_b_gains=gains))
                return rec

    forced = sorted({supplier[h][0] for h in bits(U) if len(supplier[h]) == 1})
    rec["forced_blocks"] = len(forced)
    if forced:
        union = 0
        for q in forced:
            union |= BLOCKBITS[q]
        excess = 5 * len(forced) - pc(union & U)
        rec["forced_excess"] = excess
        if excess > b:
            rec.update(verdict="UNSAT_forced_excess",
                       witness=dict(forced_orbits=forced, excess=excess))
            return rec

    parent = {h: h for h in bits(U)}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for q in cand:
        part = bits(BLOCKBITS[q] & U)
        for x in part[1:]:
            a, c = find(part[0]), find(x)
            if a != c:
                parent[c] = a
    comps = defaultdict(list)
    for h in bits(U):
        comps[find(h)].append(h)
    width = {}
    for q in cand:
        part = bits(BLOCKBITS[q] & U)
        r = find(part[0])
        width[r] = max(width.get(r, 0), len(part))
    need_blocks = sum(-(-len(hs) // width.get(r, 1)) for r, hs in comps.items())
    need_waste = sum(5 * (-(-len(hs) // 5)) - len(hs) for hs in comps.values())
    rec["components"] = sorted(len(v) for v in comps.values())
    if need_blocks > K or need_waste > b:
        rec.update(verdict="UNSAT_component_hall",
                   witness=dict(need_blocks=need_blocks, K=K, need_waste=need_waste, b=b))
        return rec

    memo = set()
    stats = {"nodes": 0, "done": True, "witness": None}

    def dfs(remaining, k, chosen):
        if remaining == 0:
            stats["witness"] = list(chosen)
            return True
        stats["nodes"] += 1
        if stats["nodes"] > node_cap:
            stats["done"] = False
            return False
        key = (remaining, k)
        if key in memo:
            return False
        slack = 5 * k - pc(remaining)
        if slack < 0:
            memo.add(key)
            return False
        if mrv:
            best, best_n = None, 99
            for h in bits(remaining):
                ok = [q for q in supplier[h] if pc(BLOCKBITS[q] & remaining) >= 5 - slack]
                if len(ok) < best_n:
                    best, best_n = ok, len(ok)
                    if not best_n:
                        break
            options = best or []
        else:
            h = bits(remaining)[0]
            options = [q for q in supplier[h] if pc(BLOCKBITS[q] & remaining) >= 5 - slack]
        if not options:
            memo.add(key)
            return False
        for q in options:
            chosen.append(q)
            if dfs(remaining & ~BLOCKBITS[q], k - 1, chosen):
                return True
            chosen.pop()
        memo.add(key)
        return False

    sat = dfs(U, K, [])
    rec["search_nodes"] = stats["nodes"]
    if sat:
        rec.update(verdict="SAT", witness_orbits=sorted(stats["witness"]))
    elif not stats["done"]:
        rec.update(verdict="UNKNOWN_node_cap")
    else:
        rec.update(verdict="UNSAT_slack_cover",
                   certificate="complete memoised bitset DFS, 0 solutions")
    return rec


# ------------------------------------------------------------------------ checks


def check_algebra(trials=20000, seed=1) -> dict:
    """|U| = 5K - b, the EXCESS identity, EXCESS == b under coverage, and closedness."""
    random.seed(seed)
    bad_u = bad_excess = bad_forced = bad_closed = n_excess = 0
    for _ in range(trials):
        O = random.randint(1, 24)
        openq = random.sample(range(NORB), O)
        cbits = 0
        for q in openq:
            cbits |= BLOCKBITS[q]
        U = ALLHEX ^ cbits
        c = 5 * O - pc(cbits)
        K, b = TO - O, 5 - c
        if pc(U) != 5 * K - b:
            bad_u += 1
        if any(BLOCKBITS[q] & U for q in openq):
            bad_closed += 1
        if 0 <= b <= 4 and K > 0:
            pick = random.sample([q for q in range(NORB) if q not in openq], K)
            m = Counter()
            union = 0
            for q in pick:
                union |= BLOCKBITS[q]
                for h in bits(BLOCKBITS[q]):
                    m[h] += 1
            lhs = 5 * K - pc(union & ~cbits & ALLHEX)
            rhs = sum(m[h] for h in bits(cbits)) + sum(max(m[h] - 1, 0) for h in bits(U))
            n_excess += 1
            if lhs != rhs:
                bad_excess += 1
            if (U & ~union) == 0 and lhs != b:
                bad_forced += 1
    return dict(trials=trials, u_identity_failures=bad_u,
                excess_identity_trials=n_excess, excess_identity_failures=bad_excess,
                excess_equals_b_failures=bad_forced,
                open_orbit_meets_U_failures=bad_closed)


def check_solver(trials=3000, seed=11) -> dict:
    """Positive control: instances built from a known 25-orbit covering family are SAT."""
    random.seed(seed)
    covered, family = set(), []
    while len(family) < TO:
        q = max((q for q in range(NORB) if q not in family),
                key=lambda q: len(BLOCK[q] - covered))
        family.append(q)
        covered |= BLOCK[q]
    if len(covered) != NHEX:
        return dict(error="no full covering family found")
    failures = n = 0
    by_slack = Counter()
    for _ in range(trials):
        j = random.randint(3, 11)
        openq = random.sample(family, j)
        cbits = 0
        for q in openq:
            cbits |= BLOCKBITS[q]
        b = 5 - (5 * j - pc(cbits))
        if not 0 <= b <= 4:
            continue
        rec = decide(ALLHEX ^ cbits, TO - j, b)
        n += 1
        by_slack[b] += 1
        if rec["verdict"] != "SAT":
            failures += 1
    return dict(instances=n, failures=failures, by_slack=dict(sorted(by_slack.items())),
                family_covers_all_hexagons=True)


def check_e1(states) -> dict:
    """E^1 must leave O, C, U, c and the candidate family untouched."""
    w2 = next(m for m in macro.NONROT_H0 if m.label == "w2:10")

    def step(st):
        runs = macro.rotation_runs(st)
        if runs[-1].ell != 5:
            return None
        tr = exact.extend(runs[-1].state, w2)
        return tr.state if tr is not None else None

    def snapshot(st):
        O = sum(1 for m in st.orbit_masks if m)
        cbits = 0
        for q in range(NORB):
            if st.orbit_masks[q]:
                cbits |= BLOCKBITS[q]
        c = 5 * O - pc(cbits)
        U = ALLHEX ^ cbits
        b = 5 - c
        fam = frozenset(q for q in range(NORB) if pc(BLOCKBITS[q] & U) >= 5 - b)
        return O, cbits, U, c, fam

    tested = steps = 0
    violations = Counter()
    for st in states:
        base = snapshot(st)
        tested += 1
        cur = st
        for _ in range(10):
            nxt = step(cur)
            if nxt is None or macro.area_a_prune_reason(nxt, AREA_A) is not None:
                break
            steps += 1
            now = snapshot(nxt)
            for i, name in enumerate(("O", "C", "U", "c", "candidate_blocks")):
                if now[i] != base[i]:
                    violations[name] += 1
            cur = nxt
    return dict(states_tested=tested, e1_steps=steps, violations=dict(violations))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("check",))
    ap.add_argument("--check", choices=("algebra", "solver"), default="algebra")
    ap.add_argument("--out")
    args = ap.parse_args()
    result = {args.check: check_algebra() if args.check == "algebra" else check_solver()}
    print(json.dumps(result, indent=1))
    if args.out:
        json.dump(result, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
