#!/usr/bin/env python3
"""Round 170 -- closing the 33..36 gap exactly.

Round 169 bracketed the load-bearing minimum and stopped: 33 cells are
individually necessary, a constructed set of 36 is feasible and minimAL, and
the exact minimum was left somewhere in between.  The bracket can be closed
by exhaustion, and cheaply, because of two facts the bracket already proves.

FACT 1, the residual is tiny.  The 33 necessary cells close 176 of the 180
exposed rows.  Only four rows remain.

FACT 2, every feasible set contains all 33.  A cell is individually necessary
when withdrawing it while keeping every other candidate already opens a row.
Row closure is MONOTONE in the selected set -- more certified cells means the
census minimises over more dominators, so bounds only fall and rows only
close -- hence if the full universe minus K fails, every subset missing K
fails too.  So every feasible selection has the form E u X, and

    OPT = 33 + min { |X| : E u X closes all 180 rows }.

That turns an unbounded search over 2^254 subsets into a search for the
smallest completion X.  |X| = 3 is already known to work, so only |X| = 1 and
|X| = 2 have to be ruled out, which is 254 + 32,131 closure evaluations.

Monotonicity is also what makes it sound to score a candidate on the four
residual rows alone: E already closes the other 176, and adding cells never
reopens a row.  The winning set is re-checked against all 180 regardless.
"""
from __future__ import annotations
import hashlib, itertools, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402
from recheck168 import parse, cellstr                             # noqa: E402


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    assert src["p1"]["holds"], "(P1) must hold before this argument is used"
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

    def closes(sel, rows):
        S.apply(sel)
        v = S.verdicts(rows)
        return {k for k in rows if v[k] == "STRICTLY_CLOSED"}

    t0 = time.time()
    got = closes(set(E), EXS)
    R = EXS - got
    print(f"exposed rows {len(EX)}   universe {len(univ)}   "
          f"necessary {len(E)}", flush=True)
    print(f"the {len(E)} necessary cells close {len(got)}; "
          f"{len(R)} rows remain", flush=True)

    cand = [K for K in univ if K not in E]

    # ---- |X| = 1
    singles = []
    for K in cand:
        c = closes(E | {K}, R)
        if c:
            singles.append((cellstr(K), len(c)))
        if len(c) == len(R):
            print(f"  ONE cell completes the basis: {cellstr(K)}", flush=True)
    best_single = max((n for _c, n in singles), default=0)
    one_works = best_single == len(R)
    print(f"|X|=1 scanned {len(cand)}: best covers {best_single}/{len(R)} "
          f"-> {'FEASIBLE' if one_works else 'IMPOSSIBLE'}", flush=True)

    # ---- |X| = 2
    pairs_tested, two_works, witness2 = 0, False, None
    if not one_works:
        # only cells that close at least one residual row can appear in a
        # minimal completion together with another such cell, but a cell that
        # closes nothing alone may still help a partner, so the scan is over
        # every pair.  Cells are ordered so the productive ones come first.
        helpful = {c for c, _n in singles}
        order = sorted(cand, key=lambda K: cellstr(K) not in helpful)
        for A, B in itertools.combinations(order, 2):
            pairs_tested += 1
            if len(closes(E | {A, B}, R)) == len(R):
                two_works, witness2 = True, (cellstr(A), cellstr(B))
                print(f"  TWO cells complete the basis: {witness2}",
                      flush=True)
                break
        print(f"|X|=2 tested {pairs_tested} pairs -> "
              f"{'FEASIBLE' if two_works else 'IMPOSSIBLE'}", flush=True)

    # ---- the answer
    if one_works:
        opt, wit = len(E) + 1, None
    elif two_works:
        opt, wit = len(E) + 2, list(witness2)
    else:
        # |X| = 3 is known feasible from round 169's constructed set; recover
        # an explicit witness and CHECK it on all 180 rows, not just the four.
        cov = {}
        for K in cand:
            c = closes(E | {K}, R)
            if c:
                cov[K] = frozenset(c)
        wit, opt = None, None
        for trio in itertools.combinations(sorted(cov, key=cellstr), 3):
            if set().union(*(cov[k] for k in trio)) == R:
                if closes(E | set(trio), EXS) == EXS:
                    wit, opt = [cellstr(k) for k in trio], len(E) + 3
                    break
    full_ok = None
    if wit:
        full_ok = closes(E | {parse(c) for c in wit}, EXS) == EXS

    out = dict(
        inputs={p: sha(p) for p in ("r169/certs/p1_closure_169.json",
                                    "r168/certs/state_168.json",
                                    "r169/certs/cover_169.json")},
        universe=len(univ),
        exposed_rows=len(EX),
        necessary_cells=len(E),
        rows_closed_by_necessary=len(got),
        residual_rows=len(R),
        argument="every feasible selection contains all individually "
                 "necessary cells, because row closure is monotone in the "
                 "selection; hence OPT = |E| + min|X| over completions X, "
                 "and ruling out |X| in {1,2} leaves |X| = 3 exactly",
        completion_size_1=dict(scanned=len(cand),
                               best_residual_rows_covered=best_single,
                               feasible=one_works),
        completion_size_2=dict(pairs_tested=pairs_tested,
                               feasible=two_works,
                               witness=list(witness2) if witness2 else None),
        minimum=dict(
            cells=opt,
            witness_completion=wit,
            verified_on_all_exposed_rows=full_ok,
            proved_exact=opt is not None and full_ok is True),
        round_169_bracket=dict(lower=33, upper=36,
                               note="this module replaces the bracket with an "
                                    "exact value over the same universe"),
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = bool(out["minimum"]["proved_exact"])
    (ROOT / "r170" / "certs" / "basis_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "inputs"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
