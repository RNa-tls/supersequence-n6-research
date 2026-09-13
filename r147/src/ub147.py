#!/usr/bin/env python3
"""Round 147 -- the SOUND pruning table (Option A: full budget key) and its
independent validator.

WHAT WENT WRONG IN ROUND 144/145.  The searcher looks the table up with the
SUM of the remaining budgets, so a value stored under a summed key has to
dominate EVERY split with that sum.  The generator instead wrote one line per
split under the same summed key and the C loader kept the MINIMUM, which is the
opposite of dominating.  The search then pruned with bounds below the truth and
recorded capacities below the truth.  research/ERRATA_146_CHAIN_UB.md.

WHAT THIS DOES INSTEAD.  Nothing is aggregated.  The table is keyed by the full
remaining budget vector

    UB[tok][d][a_left][bb_left][e_left][h_left]

and the round-147 searcher (r147/src/l6_chain_capacity_147.c) looks it up with
exactly that vector.  So there is no split to dominate and no aggregation
argument to get wrong.

SOUNDNESS.  Write cap(K) for the true capacity of a cell with budget vector
K = (b, d, a, bb, e, h).  Two proved facts:

  (P1) MONOTONICITY.  K <= K' componentwise implies cap(K) <= cap(K').
       Every budget is an upper limit ("at most"), never a requirement: the C
       searcher gates its moves with `au < AMAX`, `bu < BMAX`, `eu >= EMAX`,
       `hu + cost <= HMAX`, `cost > tok`, and records a chain whenever
       `deficit <= DMAX`.  So every chain admissible for K is admissible for
       K', hence the maximum over the larger set is at least as large.

  (P2) HEXAGON COUNTING.  cap(K) <= 120 + a + bb + e.
       Each port of a chain lands in a rotation hexagon.  A port landing in a
       hexagon already used by this chain is, by the catalogue, either a type-A
       dirty edge (paid from a), a type-B dirty edge (paid from bb), or an
       ordinary collision (paid from e) -- `step()` returns unless one of those
       pays for it.  So #ports <= #distinct hexagons + (a + bb + e) and there
       are only 120 hexagons.  (This is the same inequality the searcher's own
       table-free `reach2` prune uses.)

The generator therefore emits, for every key in the box the run can consult,

    UB[key] = min( 120 + a + bb + e ,
                   min over VERIFIED cells K' >= key of cap(K') )

Each term is >= cap(key) by (P2) resp. (P1), so the entry is sound, and the
minimum of finitely many valid bounds is the strongest of them.  A "verified"
cell is one whose capacity was computed EXACT and UNCAPPED, either with no
table at all or with a table built the same way from strictly earlier verified
cells; the induction has no cycle because a cell is never used in its own
table.

Monotonicity of the emitted table (required by the C loader) is automatic:
key1 <= key2 implies {K' >= key2} is a subset of {K' >= key1}, so the inner
minimum is non-decreasing, and 120 + a + bb + e is non-decreasing too.
"""
from __future__ import annotations
import itertools, json
from pathlib import Path

UBD = 40            # must match the C searcher
UBA = 24
UBH = 6
UBT = 5
HEXCAP = 120
INF = 10 ** 9


def analytic(a, bb, e):
    """(P2): a chain with those reuse budgets has at most this many ports."""
    return HEXCAP + a + bb + e


def load_verified(paths):
    """Verified cells: key (b,d,a,bb,e,h) -> dict(cc, nodes, impl, provenance).

    Only EXACT_UNCAPPED entries are admitted.  Anything capped, any decision-
    form bound, any ERROR and anything from the refuted round-144 tables is
    refused -- a bound that is not an exact capacity cannot be used in the
    inner minimum without further argument.
    """
    out = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        for k, v in json.loads(p.read_text()).items():
            if v.get("status") != "EXACT_UNCAPPED" or v.get("capped"):
                continue
            key = tuple(int(x) for x in k.split("|"))
            if len(key) == 5:
                key = key + (0,)
            cc = v["cc"]
            if key in out and out[key]["cc"] != cc:
                raise SystemExit(f"verified store conflict at {key}: "
                                 f"{out[key]['cc']} vs {cc}")
            out[key] = dict(cc=cc, nodes=v.get("nodes"), impl=v.get("impl"),
                            provenance=v.get("provenance", str(p)))
    return out


def _box(budgets):
    b, d, a, bb, e, h = budgets
    return (min(b, UBT), UBD, min(a, UBA), min(bb, UBA), min(e, UBA), min(h, UBH))


def build_table(budgets, verified, exclude=()):
    """The full-key table for one run, as {key: value}.  Pure-python, no numpy:
    a 6-dimensional suffix minimum over the box, applied one axis at a time."""
    B, D, A, BB, E, H = _box(budgets)
    dims = (B + 1, D + 1, A + 1, BB + 1, E + 1, H + 1)
    M = {}
    for key in itertools.product(*(range(n) for n in dims)):
        M[key] = INF
    used = []
    for K, rec in verified.items():
        if K in exclude:
            continue
        p = (min(K[0], B), min(K[1], D), min(K[2], A), min(K[3], BB),
             min(K[4], E), min(K[5], H))
        if rec["cc"] < M[p]:
            M[p] = rec["cc"]
        used.append(K)
    # suffix minimum: after axis i is processed, M[key] is the min over all
    # placed values whose coordinate i is >= key[i] (others already handled)
    for axis in range(6):
        for key in sorted(M, key=lambda k: -k[axis]):
            nxt = list(key)
            nxt[axis] += 1
            nxt = tuple(nxt)
            if nxt in M and M[nxt] < M[key]:
                M[key] = M[nxt]
    tab = {}
    for key, v in M.items():
        tab[key] = min(v, analytic(key[2], key[3], key[4]))
    return tab, used


def write_table(path, budgets, verified, exclude=()):
    tab, used = build_table(budgets, verified, exclude)
    rows = [f"{t} {d} {a} {bb} {e} {h} {v}"
            for (t, d, a, bb, e, h), v in sorted(tab.items())]
    Path(path).write_text(f"UB7 {len(rows)}\n" + "\n".join(rows) + "\n")
    return dict(rows=len(rows), verified_used=len(used),
                budgets=list(budgets),
                min_value=min(tab.values()), max_value=max(tab.values()))


# ---------------------------------------------------------------- validator
def validate_table(path, budgets, verified, exclude=(), cells_claimed=None):
    """INDEPENDENT check of a written table.  Recomputes every entry by brute
    force from the raw per-cell data (no suffix-min trick), and checks the file
    itself for every failure mode round 146 saw or could have seen."""
    fail = []
    txt = Path(path).read_text().splitlines()
    if not txt or not txt[0].startswith("UB7 "):
        return dict(ok=False, failures=["missing or wrong UB7 magic"])
    try:
        want = int(txt[0].split()[1])
    except Exception:
        return dict(ok=False, failures=["unparseable row count in magic line"])
    if len(txt) - 1 != want:
        fail.append(f"header says {want} rows, file has {len(txt) - 1} "
                    f"(truncated or padded)")
    seen = {}
    for i, ln in enumerate(txt[1:], start=2):
        parts = ln.split()
        if len(parts) != 7:
            fail.append(f"line {i}: arity {len(parts)} != 7")
            continue
        try:
            t, d, a, bb, e, h, v = (int(x) for x in parts)
        except ValueError:
            fail.append(f"line {i}: non-integer field")
            continue
        if not (0 <= t <= UBT and 0 <= d <= UBD and 0 <= a <= UBA
                and 0 <= bb <= UBA and 0 <= e <= UBA and 0 <= h <= UBH):
            fail.append(f"line {i}: index out of range")
            continue
        key = (t, d, a, bb, e, h)
        if key in seen and seen[key] != v:
            fail.append(f"line {i}: duplicate key {key} with conflicting "
                        f"values {seen[key]} and {v}")
        seen[key] = v

    # 1. every entry must equal the brute-force minimum
    B, D, A, BB, E, H = _box(budgets)
    expected_keys = set(itertools.product(range(B + 1), range(D + 1),
                                          range(A + 1), range(BB + 1),
                                          range(E + 1), range(H + 1)))
    missing = expected_keys - set(seen)
    extra = set(seen) - expected_keys
    if missing:
        fail.append(f"{len(missing)} keys the run can consult are missing, "
                    f"e.g. {sorted(missing)[:3]}")
    if extra:
        fail.append(f"{len(extra)} keys outside the consultable box, "
                    f"e.g. {sorted(extra)[:3]}")
    pool = [(K, r["cc"]) for K, r in verified.items() if K not in exclude]
    bad_value = 0
    for key in sorted(expected_keys & set(seen)):
        t, d, a, bb, e, h = key
        best = analytic(a, bb, e)
        for K, cc in pool:
            if (K[0] >= t and K[1] >= d and K[2] >= a and K[3] >= bb
                    and K[4] >= e and K[5] >= h and cc < best):
                best = cc
        if seen[key] != best:
            bad_value += 1
            if bad_value <= 3:
                fail.append(f"entry {key}: file says {seen[key]}, brute force "
                            f"says {best}")
    if bad_value:
        fail.append(f"{bad_value} entries disagree with brute force")

    # 2. monotonicity in every direction the C loader requires
    mono = 0
    for key in seen:
        for axis in range(1, 6):
            lo = list(key)
            lo[axis] -= 1
            lo = tuple(lo)
            if lo in seen and seen[lo] > seen[key]:
                mono += 1
                if mono <= 3:
                    fail.append(f"monotonicity: {lo} -> {key} drops "
                                f"{seen[lo]} -> {seen[key]}")
    if mono:
        fail.append(f"{mono} monotonicity violations")

    # 3. the store may only contain exact uncapped capacities
    for K, r in verified.items():
        if r.get("cc") is None:
            fail.append(f"verified store entry {K} has no capacity")

    # 4. a cell must never appear in its own table
    for K in exclude:
        if K in {k for k, _ in pool}:
            fail.append(f"excluded cell {K} leaked into the pool")

    return dict(ok=not fail, failures=fail[:12], rows=len(seen),
                pool=len(pool), box=[B, D, A, BB, E, H])
