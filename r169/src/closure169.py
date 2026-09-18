#!/usr/bin/env python3
"""Round 169 phases 5, 6 and 11 -- the census closed under (P1) domination.

FINDING.  The census reads a capacity by exact lookup.  It does not apply
(P1) monotonicity, even though (P1) is a PROVEN_ANALYTIC node of this proof
system -- round 165 established it, every EXTREE certificate already uses it
for `(p)` leaves, and it is what `ub()` computes.  (P1) says

    K dominates T componentwise  =>  cap(T) <= cap(K)

so a certified dominator supplies a sound upper bound for everything below it,
with no certificate for the dominated cell at all.

The direction is checked, not assumed: over the round-152 tables there are
45,289 chain domination pairs and 6,890 piece pairs, with ZERO violations.

CONSEQUENCE.  Of the 164 basis cells round 168 still had to certify, 129 are
dominated by another cell of the same 190-cell basis, and 94 of those by a
dominator with an EQUAL capacity -- so certifying the dominator loses nothing
at all.  The round-167 minimum of 190 was computed under a census that could
not see this, so it is not minimal under the rule system this project actually
has.

This module closes the census under (P1) and recomputes the minimum, with the
same matching-bound method round 167 used: show the universe feasible, test
every member for individual necessity, then show the necessary set sufficient.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
sys.path.insert(0, str(ROOT / "r169" / "src"))
import hidden163 as H                                             # noqa: E402
from recheck168 import System, parse, cellstr                     # noqa: E402
from state169 import certified_from_proof_objects, sha            # noqa: E402

HEX = 120
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def chain_dom(K, T):
    return all(t <= k for t, k in zip(T, K))


def piece_dom(K, T):
    return (T[0] <= K[0] and T[1] <= K[1] and T[2] >= K[2] and T[3] >= K[3])


class ClosedSystem(System):
    """System.apply, then close the capacity maps under (P1).

    The dominator lists are precomputed once from the coordinates alone -- no
    capacity is read to build them -- so a closure pass costs one sweep over
    the domination pairs instead of a quadratic scan.
    """

    def __init__(self):
        super().__init__()
        cells = sorted(self.chain_tab)
        extra = [K for K in self.piece_tab]
        self.chain_cells = cells
        self.cdom = {T: [K for K in cells if K != T and chain_dom(K, T)]
                     for T in cells}
        pc = sorted(self.piece_tab)
        self.pdom = {T: [K for K in pc if K != T and piece_dom(K, T)]
                     for T in pc}
        self.zero_extra = sorted({(b, d, 0, 0, 0, 0)
                                  for (b, d, _f, _l) in pc
                                  if (b, d, 0, 0, 0, 0) not in self.chain_tab})
        for T in self.zero_extra:
            self.cdom[T] = [K for K in cells if chain_dom(K, T)]

    def apply(self, granted, values=None):
        cert, pcert = super().apply(granted, values)
        closed_c, closed_p = dict(cert), dict(pcert)
        for T, ds in self.cdom.items():
            fb = HEX + T[2] + T[3] + T[4]
            best = closed_c.get(T, fb)
            for K in ds:
                v = cert.get(K)
                if v is not None and v < best:
                    best = v
            if best < fb:
                closed_c[T] = best
        for T, ds in self.pdom.items():
            best = closed_p.get(T, HEX)
            for K in ds:
                v = pcert.get(K)
                if v is not None and v < best:
                    best = v
            if best < HEX:
                closed_p[T] = best
        H.CERT.clear(); H.CERT.update(closed_c)
        H.PCERT.clear(); H.PCERT.update(closed_p)
        H.best.cache_clear()
        return closed_c, closed_p


def verify_p1():
    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    P = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in prows
         if r["status"] in GOOD}
    cp = cv = pp = pv = 0
    for T, ct in sorted(U.items()):
        for K, ck in sorted(U.items()):
            if K != T and chain_dom(K, T):
                cp += 1
                cv += ct > ck
    for T, ct in sorted(P.items()):
        for K, ck in sorted(P.items()):
            if K != T and piece_dom(K, T):
                pp += 1
                pv += ct > ck
    return dict(chain_pairs=cp, chain_violations=cv,
                piece_pairs=pp, piece_violations=pv,
                holds=(cv == 0 and pv == 0)), U, P


def main():
    p1, U, P = verify_p1()
    if not p1["holds"]:
        raise SystemExit("(P1) fails on the tables; nothing below is valid")

    S = ClosedSystem()
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    OPT = {parse(c) for c in st["optimum"]}
    U167 = {parse(c) for c in st["universe_cells"]}
    CERT, _prov = certified_from_proof_objects()

    S.full()
    base = S.verdicts()
    tally = Counter(base.values())
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    # the candidate universe: every cell that still needs a certificate --
    # round 167's 222 plus every single-route tabulated chain cell, so a
    # dominator outside the old basis is a candidate too
    single = {K for K in S.chain_tab if K not in S.dual_chain}
    univ = sorted(U167 | single)
    S.apply(set(univ))
    v_all = S.verdicts(EXS)
    open_all = [k for k in EX if v_all[k] != "STRICTLY_CLOSED"]

    # necessity, one cell at a time -- the same matching-bound method
    nec, red = [], []
    for K in univ:
        S.apply(set(univ) - {K})
        vv = S.verdicts(EXS)
        o = [k for k in EX if vv[k] != "STRICTLY_CLOSED"]
        (nec if o else red).append(K)

    E = set(nec)
    S.apply(E)
    vE = S.verdicts(EXS)
    open_E = [k for k in EX if vE[k] != "STRICTLY_CLOSED"]

    S.apply(set(CERT))
    now = S.verdicts(EXS)
    closed_now = [k for k in EX if now[k] == "STRICTLY_CLOSED"]

    out = dict(
        inputs={p: sha(p) for p in
                ("r168/certs/state_168.json", "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json", "r163/src/hidden163.py")},
        p1=p1,
        baseline=dict(rows=len(base), tally=dict(tally),
                      reproduces_round_152=(tally["STRICTLY_CLOSED"] == 1607
                                            and tally["EQUALITY"] == 2)),
        exposed_rows=len(EX),
        round_167_exposed=180,
        universe=dict(size=len(univ), feasible=not open_all,
                      rows_left_open=len(open_all)),
        minimum=dict(necessary=len(nec), redundant=len(red),
                     feasible=not open_E, rows_left_open=len(open_E),
                     cells=sorted(cellstr(K) for K in nec)),
        round_167_minimum=190,
        progress=dict(certified_in_the_new_minimum=len(set(CERT) & E),
                      still_needed=len(E - set(CERT)),
                      rows_closed_now=len(closed_now),
                      exposed_rows=len(EX)),
        domination_structure=dict(
            round_167_basis=len(OPT),
            basis_cells_dominated_by_another_basis_cell=sum(
                1 for T in OPT if any(K != T and chain_dom(K, T) for K in OPT)),
            with_equal_capacity=sum(
                1 for T in OPT
                if any(K != T and chain_dom(K, T) and U.get(K) is not None
                       and U.get(K) == U.get(T) for K in OPT))),
    )
    out["ok"] = (out["baseline"]["reproduces_round_152"]
                 and out["universe"]["feasible"]
                 and out["minimum"]["feasible"])
    (ROOT / "r169" / "certs" / "p1_closure_169.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = json.loads(json.dumps(out))
    show.pop("inputs")
    show["minimum"].pop("cells")
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
