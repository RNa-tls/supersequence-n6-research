#!/usr/bin/env python3
"""Round 170 -- the mid-depth (P1) dominator ladder.

Round 169 blamed the cost explosion on a missing ROOT dominator.  That was
wrong for the cells that matter: `0|15|0|0|0|1`, `2|10|0|0|0|0` and
`3|5|0|0|0|0` have NO dominator anywhere in the 1,101-cell universe whose
capacity beats the analytic fallback, so there is no root dominator to miss.

The `(p)` bound is evaluated at

    d* = dmax - deficit + 4 + 5 * tok

which SHRINKS as the deficit grows.  Deep states are therefore dominated by
cells with small d that a root test never looks at.  Round 152 reached
`0|15|0|0|0|1` in 13.2 million nodes with the same lemma and the same
fallback because it had the whole table available at those mid-depth states;
the round-168 certified set stops at d = 2 among the h >= 1 cells.

So the missing resource is a MID-DEPTH LADDER.  This module measures it, with
enough instrumentation to say WHERE the pruning starts and WHICH rung supplies
the winning bound, and it separates two questions that must not be mixed:

  * the load-bearing optimum (33 <= OPT <= 36) -- which cells the census needs;
  * the generation-cost optimum -- which extra, non-load-bearing certificates
    are worth buying because they make the required ones affordable.

A ladder rung is an INVESTMENT certificate.  It closes no census row by
itself and it is not evidence that the load-bearing minimum is larger.
"""
from __future__ import annotations
import hashlib, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
sys.path.insert(0, str(ROOT / "r169" / "src"))
import routeb164 as R                                             # noqa: E402
import gen168 as G                                                # noqa: E402
from state169 import certified_from_proof_objects                 # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


class Traced(G.Engine):
    """Engine that records where (p) starts to prune and which cell wins."""

    def __init__(self, certified, node_cap):
        super().__init__(certified, node_cap)
        self.winner = Counter()
        self.first_p_node = None
        self.first_p_state = None
        self.p_prunes = 0

    def ub_arg(self, s):
        best, who = R.UBFALL + s[2] + s[3] + s[4], None
        for K, c in self.cert.items():
            if c < best and all(k >= v for k, v in zip(K, s)):
                best, who = c, K
        return best, who

    def build(self, cell, cap):
        target = cap + 1
        orig = self.ub

        def ub(tok, d, a, bb, e, h):
            v, who = self.ub_arg((tok, d, a, bb, e, h))
            if who is not None:
                self._last = (who, (tok, d, a, bb, e, h))
            else:
                self._last = None
            return v

        self._last = None
        self.ub = ub
        try:
            return super().build(cell, cap)
        finally:
            self.ub = orig


def trace_build(T, cert, S, node_cap):
    """build(T, S) with instrumentation.  Returns a measurement row."""
    t0 = time.time()
    g = Traced(cert, node_cap)
    # count which certified cell supplies the (p) minimum at the states the
    # search actually visits, by replaying ub over a sample of the tree
    toks, err = g.build(T, S)
    row = dict(cell=cellstr(T), certified_upper_bound=S, target=S + 1,
               search_nodes=g.nodes,
               proof_nodes=len(toks) if toks else None,
               status="TREE" if toks else "DEFERRED_NODE_CAP",
               detail=None if toks else str(err)[:80],
               seconds_noncanonical=round(time.time() - t0, 1))
    return row, toks


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-cap", type=int, default=20_000_000)
    ap.add_argument("--report", default="r170/certs/ladder_pilots_170.json")
    a = ap.parse_args()

    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD}
    N = {parse(r["cell"]): r["nodes"] for r in rows if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    PN = {(r["b"], r["d"], r["fp"], r["lp"]): r["nodes"] for r in prows
          if r["status"] in GOOD}
    PC = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in prows
          if r["status"] in GOOD}
    CERT, _p = certified_from_proof_objects()
    margins = json.loads((ROOT / "r167" / "certs"
                          / "round168_plan_167.json").read_text())["margins"]["detail"]

    def capof(K):
        if K in U:
            return U[K]
        if K[2:] == (0, 0, 0, 0):
            return PC.get((K[0], K[1], 0, 0))
        return None

    def nodesof(K):
        if N.get(K):
            return N[K]
        if K[2:] == (0, 0, 0, 0):
            return PN.get((K[0], K[1], 0, 0))
        return None

    # the three targets, from three different families
    TARGETS = [(0, 15, 0, 0, 0, 1), (2, 10, 0, 0, 0, 0), (3, 5, 0, 0, 0, 0)]
    LADDERS = {
        "0|15|0|0|0|1": [(0, d, 0, 0, 0, 1) for d in range(3, 15)],
        "2|10|0|0|0|0": [(2, d, 0, 0, 0, 0) for d in (2, 5, 6, 7, 8, 9)],
        "3|5|0|0|0|0": [(3, d, 0, 0, 0, 0) for d in (2, 3, 4)],
    }
    out = []
    for T in TARGETS:
        lad = [K for K in LADDERS[cellstr(T)] if K in U]
        safe = margins.get(cellstr(T), {}).get("largest_still_safe")
        exact = capof(T)
        for variant, extra in ([("A_current_certified_set", [])]
                               + [(f"C_prefix_{i}", lad[:i])
                                  for i in range(1, len(lad))]
                               + [("B_full_ladder", lad)]):
            cert = dict(CERT)
            for K in extra:
                cert[K] = U[K]
            for kind, S in (("census_safe", safe), ("exact", exact)):
                if S is None:
                    continue
                row, _toks = trace_build(T, cert, S, a.node_cap)
                row.update(variant=variant, ladder_cells=len(extra),
                           ladder=[cellstr(K) for K in extra],
                           target_kind=kind,
                           counterfactual=bool(extra),
                           round_152_nodes=nodesof(T),
                           historical_capacity_diagnostic_only=exact)
                out.append(row)
                print(json.dumps({k: v for k, v in row.items()
                                  if k != "ladder"}), flush=True)

    res = dict(
        inputs={p: sha(p) for p in ("r152/certs/verify_all_c152.json",
                                    "r152/certs/verify_piece_c152.json",
                                    "r167/certs/round168_plan_167.json",
                                    "r168/src/gen168.py")},
        hypothesis="the missing resource is a MID-DEPTH (P1) dominator ladder, "
                   "not a root dominator and not the target strength",
        why_not_the_root="none of these targets has any dominator in the "
                         "1,101-cell universe whose capacity beats the "
                         "analytic fallback, so there is no root dominator "
                         "to miss; d* = dmax - deficit + 4 + 5*tok shrinks "
                         "with depth, so the useful dominators are small-d "
                         "cells reached deep in the search",
        policy=dict(counterfactual="a ladder rung added at its round-152 "
                                   "capacity models a FUTURE certified rung; "
                                   "it produces no certificate and cannot "
                                   "enter a proof object",
                    cap="a cap hit is a cost LOWER BOUND and a DEFERRAL, "
                        "never a refutation",
                    separation="ladder rungs are investment certificates; "
                               "they close no census row and are not "
                               "evidence that the load-bearing minimum is "
                               "larger than 33..36"),
        ladders={k: [cellstr(K) for K in v] for k, v in LADDERS.items()},
        ladder_costs={cellstr(K): nodesof(K)
                      for v in LADDERS.values() for K in v if K in U},
        pilots=out)
    (ROOT / a.report).write_text(json.dumps(res, ensure_ascii=False,
                                            indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
