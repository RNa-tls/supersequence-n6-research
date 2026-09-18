#!/usr/bin/env python3
"""Round 170 -- an independent audit of the exact minimum 35.

`basis170.py` collapses the 33..36 bracket to 35 and the claim rests on three
things that are each checkable on their own, so this module rebuilds all three
from scratch rather than reusing that module's intermediate state.

  1. MONOTONICITY, the load-bearing lemma.  The whole reduction "every
     feasible set contains every necessary cell" depends on row closure never
     reopening a row when a cell is ADDED.  It is tested directly on random
     nested pairs of selections instead of being assumed.

  2. NECESSITY of each of the 33.  For each K, the full universe minus K must
     leave some exposed row open.  This is what puts K in every feasible set.

  3. SUFFICIENCY and MINIMALITY of the 35.  The set must close all 180 rows,
     and dropping any one of its members must reopen one.

If all three hold, 35 is the exact minimum over this universe: no 34-cell set
can be feasible, because a feasible 34 would be the 33 plus a single cell, and
the size-1 scan is exhaustive.
"""
from __future__ import annotations
import hashlib, json, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402
from recheck168 import parse, cellstr                             # noqa: E402


def main():
    rep = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    U167 = {parse(c) for c in st["universe_cells"]}

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)
    single = {K for K in S.chain_tab if K not in S.dual_chain}
    univ = sorted(U167 | single)
    E = {parse(c) for c in src["minimum"]["cells"]}
    X = {parse(c) for c in rep["minimum"]["witness_completion"]}
    BASIS = E | X

    def closed(sel, rows=None):
        rows = EXS if rows is None else rows
        S.apply(sel)
        v = S.verdicts(rows)
        return {k for k in rows if v[k] == "STRICTLY_CLOSED"}

    t0 = time.time()

    # ---- 1. monotonicity
    rng = random.Random(170)
    mono_bad = []
    for _ in range(40):
        a = set(rng.sample(univ, rng.randint(20, 120)))
        extra = set(rng.sample([c for c in univ if c not in a],
                               rng.randint(1, 30)))
        ca, cb = closed(a), closed(a | extra)
        if not ca <= cb:
            mono_bad.append(dict(lost=[str(k) for k in sorted(ca - cb)][:4],
                                 added=len(extra)))
    print(f"monotonicity: 40 nested pairs, {len(mono_bad)} violations",
          flush=True)

    # ---- 2. necessity of each of the 33
    not_necessary = []
    for K in sorted(E, key=cellstr):
        if len(closed(set(univ) - {K})) == len(EX):
            not_necessary.append(cellstr(K))
    print(f"necessity: {len(E)} cells checked, "
          f"{len(not_necessary)} were NOT necessary", flush=True)

    # ---- 3. the 35 closes everything, and is minimal
    got = closed(BASIS)
    sufficient = got == EXS
    droppable = []
    for K in sorted(BASIS, key=cellstr):
        if len(closed(BASIS - {K})) == len(EX):
            droppable.append(cellstr(K))
    print(f"the {len(BASIS)}-cell basis closes {len(got)}/{len(EX)}; "
          f"{len(droppable)} members droppable", flush=True)

    # ---- 4. the size-1 scan again, independently
    best1, one_ok = 0, False
    R = EXS - closed(E)
    for K in sorted(set(univ) - E, key=cellstr):
        n = len(closed(E | {K}, R))
        best1 = max(best1, n)
        if n == len(R):
            one_ok = True
    print(f"size-1 rescan: best covers {best1}/{len(R)} "
          f"-> 34 is {'POSSIBLE' if one_ok else 'IMPOSSIBLE'}", flush=True)

    out = dict(
        audited="r170/certs/basis_170.json",
        audited_sha256=hashlib.sha256(
            (ROOT / "r170" / "certs" / "basis_170.json").read_bytes()
        ).hexdigest(),
        monotonicity=dict(nested_pairs_tested=40, violations=mono_bad,
                          holds=not mono_bad,
                          means="adding a cell never reopens a closed row, "
                                "so a feasible set can never omit a "
                                "necessary cell"),
        necessity=dict(checked=len(E), not_necessary=not_necessary,
                       all_necessary=not not_necessary),
        basis=dict(size=len(BASIS), rows_closed=len(got),
                   sufficient=sufficient,
                   droppable_members=droppable,
                   minimal=not droppable),
        size_1_rescan=dict(residual_rows=len(R),
                           best_covered=best1,
                           thirty_four_possible=one_ok),
        verdict=None,
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    exact = (not mono_bad and not not_necessary and sufficient
             and not droppable and not one_ok)
    out["verdict"] = ("EXACT_MINIMUM_35_CONFIRMED" if exact
                      else "AUDIT_FAILED")
    out["ok"] = exact
    (ROOT / "r170" / "certs" / "basis_audit_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if exact else 1


if __name__ == "__main__":
    sys.exit(main())
