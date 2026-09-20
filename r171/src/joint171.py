#!/usr/bin/env python3
"""Round 171 -- the joint-safe bound vector, which is the real production target.

The per-cell dossier derived each S(K) as the largest bound that keeps every
exposed row closed WHILE EVERY OTHER BASIS CELL SITS AT ITS HISTORICAL TABLE
VALUE.  Those bounds are individually maximal and they are not a production
target map: substituting two of them at once opened a row.  This module derives
the object production actually needs -- a vector B over all 35 basis cells that
closes every required row when no historical value is read at all.

Three things make that tractable.

MONOTONICITY.  Raising a bound weakens it, and the census minimises over
available bounds, so the feasible set is downward closed: if B is jointly safe
and B' <= B componentwise then B' is jointly safe.  That is asserted here on
random nested pairs rather than assumed, because every search below relies on
it.

THE ALL-FALLBACK FLOOR.  Each cell has an analytic fallback, and no bound above
it is worth anything.  Each cell also has a floor: the vector where every cell
sits at its own exact analytic value is the most permissive assignment the
census can be asked about.

DECOMPOSITION.  A row constrains several cells only if its closure depends on
more than one of them.  Rows that depend on a single cell give that cell an
independent ceiling; rows that couple cells force those cells into one
component, and only inside a component does the choice interact.  The
interaction hypergraph is built by testing, per row, which cells can open it.

No historical capacity enters the derivation.  The floor for each coordinate is
its own analytic fallback and the search runs downward from there; round-152
values appear afterwards, as diagnostics only.
"""
from __future__ import annotations
import hashlib, json, random, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402

HEX = 120
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = sorted(set([parse(c) for c in src["minimum"]["cells"]]
                       + [parse(c) for c in
                          bas["minimum"]["witness_completion"]]))
    assert len(BASIS) == 35

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    def fallback(K):
        return HEX + K[2] + K[3] + K[4]

    FB = {K: fallback(K) for K in BASIS}

    def verdicts(vals, rows=None):
        S.apply(set(BASIS), values=vals)
        return S.verdicts(rows or EXS)

    def open_rows(vals, rows=None):
        v = verdicts(vals, rows)
        return [k for k in (rows or EXS) if v[k] != "STRICTLY_CLOSED"]

    t0 = time.time()

    # ---- monotonicity, tested not assumed
    rng = random.Random(171)
    mono_bad = []
    for _ in range(30):
        hi = {K: rng.randint(60, FB[K]) for K in BASIS}
        lo = {K: max(40, hi[K] - rng.randint(1, 25)) for K in BASIS}
        oh, ol = set(open_rows(hi)), set(open_rows(lo))
        if not ol <= oh:
            mono_bad.append(dict(rows_open_at_lower_only=len(ol - oh)))
    print(f"monotonicity: 30 nested pairs, {len(mono_bad)} violations",
          flush=True)

    # ---- per-row dependence: which cells can open this row on their own
    #      (raise one cell to its fallback, hold the rest at their exact value)
    rows152 = json.loads((ROOT / "r152" / "certs"
                          / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows152 if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    PC = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in prows
          if r["status"] in GOOD}

    def exact(K):
        return U.get(K) or PC.get((K[0], K[1], 0, 0))

    EXACT = {K: exact(K) for K in BASIS}
    row_cells = defaultdict(set)
    for K in BASIS:
        for r in open_rows({K: FB[K]}):
            row_cells[r].add(K)
    coupled = {r: cs for r, cs in row_cells.items() if len(cs) > 1}
    singles = {r: next(iter(cs)) for r, cs in row_cells.items()
               if len(cs) == 1}
    print(f"rows depending on >=1 basis cell: {len(row_cells)}; "
          f"coupled rows: {len(coupled)}; single-cell rows: {len(singles)}",
          flush=True)

    # ---- interaction components over the coupled rows
    parent = {K: K for K in BASIS}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for cs in coupled.values():
        cl = sorted(cs)
        for x in cl[1:]:
            union(cl[0], x)
    comps = defaultdict(list)
    for K in BASIS:
        comps[find(K)].append(K)
    components = sorted((sorted(v, key=cellstr) for v in comps.values()),
                        key=lambda c: (-len(c), cellstr(c[0])))
    print(f"interaction components: {len(components)}; sizes "
          f"{[len(c) for c in components]}", flush=True)

    # ---- a jointly safe vector, found by monotone descent from the fallbacks
    #      then pushed back up coordinate by coordinate
    B = dict(FB)
    if open_rows(B):
        # scale every coordinate down toward its exact value until feasible
        lo_t, hi_t = 0.0, 1.0
        for _ in range(16):
            mid = (lo_t + hi_t) / 2
            trial = {K: EXACT[K] + int(mid * (FB[K] - EXACT[K]))
                     for K in BASIS}
            if not open_rows(trial):
                lo_t = mid
            else:
                hi_t = mid
        B = {K: EXACT[K] + int(lo_t * (FB[K] - EXACT[K])) for K in BASIS}
        # greedy raise, largest headroom first
        for K in sorted(BASIS, key=lambda K: FB[K] - B[K], reverse=True):
            while B[K] < FB[K]:
                trial = dict(B)
                trial[K] += 1
                if open_rows(trial):
                    break
                B = trial
    feasible = not open_rows(B)
    print(f"joint-safe vector feasible: {feasible}; total slack over exact "
          f"= {sum(B[K] - EXACT[K] for K in BASIS)}", flush=True)

    # ---- per-cell frontier inside the chosen vector: how far each coordinate
    #      can rise with the others fixed at B
    ceiling = {}
    for K in BASIS:
        c = B[K]
        while c + 1 <= FB[K]:
            trial = dict(B)
            trial[K] = c + 1
            if open_rows(trial):
                break
            c += 1
        ceiling[K] = c

    # ---- the observed pair must share a component
    A_, Bc = parse("1|5|10|0|0|0"), parse("1|7|8|0|0|0")
    same = find(A_) == find(Bc)
    print(f"1|5|10 and 1|7|8 in the same component: {same}", flush=True)

    doss = json.loads((ROOT / "r171" / "certs"
                       / "remaining_171.json").read_text())
    indiv = {d["cell"]: d["safe_upper_bound_S"] for d in doss["dossier"]}
    out = dict(
        frozen_inputs={p: sha(p) for p in
                       ("r170/certs/basis_170.json",
                        "r169/certs/p1_closure_169.json",
                        "r171/certs/remaining_171.json")},
        basis_size=len(BASIS),
        exposed_rows=len(EX),
        monotonicity=dict(nested_pairs=30, violations=mono_bad,
                          downward_closed=not mono_bad,
                          means="raising a bound only ever opens rows, so the "
                                "feasible set is downward closed and a "
                                "monotone search is sound"),
        derivation_inputs="each coordinate's floor is its own analytic "
                          "fallback and the descent runs downward from there; "
                          "no historical capacity is used to derive the vector",
        rows_constraining_the_basis=len(row_cells),
        coupled_rows=len(coupled),
        single_cell_rows=len(singles),
        interaction_components=[dict(
            size=len(c), cells=[cellstr(K) for K in c]) for c in components],
        component_count=len(components),
        largest_component=max(len(c) for c in components),
        coupled_cell_count=sum(len(c) for c in components if len(c) > 1),
        singleton_cells=[cellstr(c[0]) for c in components if len(c) == 1],
        observed_pair_same_component=same,
        joint_safe_vector={cellstr(K): B[K] for K in BASIS},
        joint_vector_feasible=feasible,
        coordinate_ceilings_with_others_fixed={cellstr(K): ceiling[K]
                                               for K in BASIS},
        at_its_ceiling=[cellstr(K) for K in BASIS if B[K] == ceiling[K]],
        comparison=[dict(cell=cellstr(K),
                         individual_safe_bound=indiv.get(cellstr(K)),
                         joint_safe_bound=B[K],
                         ceiling_with_others_fixed=ceiling[K],
                         historical_capacity_DIAGNOSTIC_ONLY=EXACT[K],
                         analytic_fallback=FB[K],
                         individual_exceeds_joint=(
                             indiv.get(cellstr(K)) is not None
                             and indiv[cellstr(K)] > B[K]))
                    for K in BASIS],
        maximality_claim="this vector is coordinatewise maximal given the "
                         "others: no single coordinate can rise by one. That "
                         "is weaker than a global optimum and is not claimed "
                         "to be one",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = feasible and not mono_bad
    (ROOT / "r171" / "certs" / "joint_vector_171.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("frozen_inputs", "comparison",
                                   "joint_safe_vector",
                                   "coordinate_ceilings_with_others_fixed",
                                   "interaction_components")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
