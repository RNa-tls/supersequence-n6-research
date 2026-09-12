#!/usr/bin/env python3
"""Round 146 — POSITIVE CONTROLS for the pure-circuit coexistence solvers.

Mutation testing showed that a "no admissible circuits" verdict survives a
CORRUPTED orbit->hexagon table (mutation M7).  A negative verdict is therefore
not by itself evidence that the solver and its geometry are right.  This module
supplies positive controls: every real length-872 cover IS a solved instance of
exactly the coexistence problem the Q1/Q2 rows pose.

For a length-872 cover with c pure circuits and a chain of P_1 ports,
    |F| = 120 - P_1 = 4c
holds (round 146 §Target1 (ii)), and the cover's OWN c circuit orbits are a
cover of F by c orbits disjoint from the chain's orbits.  So both solvers MUST
return ok = True on those instances, and the witness's own orbit set must be
among the solutions found.  If a solver says "no" here, its Q1/Q2 negatives are
worthless.
"""
from __future__ import annotations
import gzip, itertools, json, sys
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from l6_cleanroom_146 import sig, tau, hexkey, orbkey                  # noqa
import l6_circuit_coexist_144 as CO                                    # noqa
import l6_coexist_check3_144 as CO3                                    # noqa

PERMS = ["".join(p) for p in itertools.permutations("123456")]
RANK = {p: i for i, p in enumerate(PERMS)}


def lexrank(s):
    """Map a 6-char permutation string to the round-144 integer index."""
    t = s
    if set(s) == set("012345"):
        t = "".join(chr(ord(ch) + 1) for ch in s)
    return RANK[t]


def decompose(W):
    n, N = 6, 720
    seen, sel, pos = set(), [], []
    for i in range(len(W) - n + 1):
        w = W[i:i + n]
        if len(set(w)) == n and w not in seen:
            seen.add(w); sel.append(w); pos.append(i)
    gaps = [pos[j + 1] - pos[j] for j in range(N - 1)]
    passes, run = [], [0]
    for j, g in enumerate(gaps):
        if g == 1:
            run.append(j + 1)
        else:
            passes.append(run); run = [j + 1]
    passes.append(run)
    ent = [sel[r[0]] for r in passes]
    lens = [len(r) for r in passes]
    P = len(passes)
    idx = {e: i for i, e in enumerate(ent)}
    nu = []
    for i in range(P):
        x = ent[i]
        for _ in range(lens[i]):
            x = sig(x)
        nu.append(idx[x])
    DUM = "*"
    T = {i: i + 1 for i in range(P - 1)}; T[P - 1] = DUM; T[DUM] = 0
    alpha = {i: nu[i] for i in range(P)}; alpha[DUM] = DUM
    ainv = {v: k for k, v in alpha.items()}
    beta = {x: T[ainv[x]] for x in list(range(P)) + [DUM]}
    ty = {}
    for j, g in enumerate(gaps):
        if g == 1:
            continue
        src = sel[j]
        i = next(i for i in range(P) if _adv(ent[i], lens[i] - 1) == src)
        p = nu[i]
        ty[p] = "E" if (g == 2 and sel[j + 1] == tau(ent[p])) else "other"
    comps, seen2 = [], set()
    for st in list(range(P)) + [DUM]:
        if st in seen2:
            continue
        cy, x = [], st
        while x not in seen2:
            seen2.add(x); cy.append(x); x = beta[x]
        comps.append(cy)
    pure = [cy for cy in comps if DUM not in cy and all(ty.get(x) == "E" for x in cy)]
    chain = [cy for cy in comps if DUM in cy][0]
    chain_ports = [x for x in chain if x != DUM]
    return ent, chain_ports, pure, P


def _adv(s, j):
    for _ in range(j):
        s = sig(s)
    return s


def control(W):
    ent, chain_ports, pure, P = decompose(W)
    c = len(pure)
    chain_idx = [lexrank(ent[x]) for x in chain_ports]
    chain_hex = {hexkey(ent[x]) for x in chain_ports}
    F = set(hexkey(p) for p in PERMS) - chain_hex
    own_orbs = {orbkey(ent[cy[0]]) for cy in pure}
    # the witness's own circuits must cover F
    covered = set()
    for o in own_orbs:
        x = next(p for p in PERMS if orbkey(p) == o)
        for _ in range(5):
            covered.add(hexkey(x)); x = tau(x)
    # existence-only: these instances have astronomically many solutions
    r1 = (CO.coexist(chain_idx, c, node_cap=60_000_000, first_only=True)
          if len(F) == 4 * c else dict(ok=None, reason="|F| != 4c"))
    r3 = (CO3.solve(chain_idx, c, first_only=True)
          if len(F) == 4 * c else dict(ok=None))
    return dict(L=len(W), P=P, c=c, chain_ports=len(chain_ports),
                predicted_chain_ports=120 - 4 * c, F=len(F),
                own_circuits_cover_F=(covered >= F),
                dfs_ok=r1.get("ok"), dfs_solutions=r1.get("solutions"),
                subset_ok=r3.get("ok"), subset_solutions=r3.get("solutions"),
                control_passes=(r1.get("ok") is True and r3.get("ok") is True
                                and covered >= F
                                and len(chain_ports) == 120 - 4 * c))


if __name__ == "__main__":
    rows = []
    for path in sys.argv[1:]:
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "rt") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#") or len(set(s)) != 6 or len(s) < 800:
                    continue
                r = control(s)
                r["file"] = path.split("/")[-1]
                rows.append(r)
                print(json.dumps({k: r[k] for k in
                                  ("file", "L", "c", "chain_ports",
                                   "predicted_chain_ports", "F",
                                   "own_circuits_cover_F", "dfs_ok",
                                   "dfs_solutions", "subset_ok",
                                   "subset_solutions", "control_passes")},
                                 ensure_ascii=False), flush=True)
                break                    # one representative per file
    (ROOT / "outputs" / "rr_l6_coexist_control_146.json").write_text(
        json.dumps(dict(controls=rows,
                        all_pass=all(r["control_passes"] for r in rows)),
                   ensure_ascii=False, indent=1))
    print("\nall controls pass:", all(r["control_passes"] for r in rows))
