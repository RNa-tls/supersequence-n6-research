#!/usr/bin/env python3
"""Round 171 -- the interaction hypergraph, built by a test that can see pairs.

A first attempt decided which cells a row depends on by raising ONE cell to its
analytic fallback while holding every other cell at its historical value, and
reported 31 components with a largest size of 3.  That construction is unsound
and the evidence was already in hand: the row that broke production,

    (4, (3, 0, 0, 1, 10, 4, 2, 0, 8, 0, 0))

opens when 1|5|10|0|0|0 sits at 129 AND 1|7|8|0|0|0 sits at 123, and opens for
NEITHER of them alone -- not even with either raised all the way to its
fallback.  A one-cell-at-a-time probe cannot see a constraint that needs two
cells weakened together, so that row contributed no edge and the pair came out
in different components.  The decomposition was therefore under-detecting
couplings, which is the dangerous direction: it would license optimising two
interacting cells independently.

This module rebuilds the graph around the FEASIBLE VECTOR B instead, where the
production question actually lives, and tests pairs:

  singles   raising K alone above B[K] (to its fallback) opens row R
  pairs     raising K1 and K2 together opens R while neither alone does

Rows found only by the pair test are recorded separately, because they are the
ones the first construction missed.

The limitation is stated rather than hidden: this detects couplings of order one
and two.  A row requiring three or more cells weakened simultaneously, with no
pair sufficient, would still be invisible here, so the component structure is
reported as PAIRWISE-COMPLETE and not as proven-complete.
"""
from __future__ import annotations
import hashlib, itertools, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402

HEX = 120


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    jv = json.loads((ROOT / "r171" / "certs"
                     / "joint_vector_171.json").read_text())
    B = {parse(k): v for k, v in jv["joint_safe_vector"].items()}
    BASIS = sorted(B)
    FB = {K: HEX + K[2] + K[3] + K[4] for K in BASIS}

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    def opened(vals):
        S.apply(set(BASIS), values=vals)
        v = S.verdicts(EXS)
        return {k for k in EX if v[k] != "STRICTLY_CLOSED"}

    t0 = time.time()
    assert not opened(B), "the joint vector must close every exposed row"

    # ---- singles: raise one coordinate from B to its fallback
    single_open = {}
    for K in BASIS:
        vals = dict(B)
        vals[K] = FB[K]
        single_open[K] = opened(vals)
    print(f"singles probed: {len(BASIS)}", flush=True)

    row_single = defaultdict(set)
    for K, rows in single_open.items():
        for r in rows:
            row_single[r].add(K)

    # ---- pairs: raise two together; keep only rows neither opens alone
    pair_only = defaultdict(set)
    tested = 0
    for K1, K2 in itertools.combinations(BASIS, 2):
        tested += 1
        vals = dict(B)
        vals[K1], vals[K2] = FB[K1], FB[K2]
        both = opened(vals)
        new = both - single_open[K1] - single_open[K2]
        for r in new:
            pair_only[r].add((K1, K2))
    print(f"pairs probed: {tested}; rows opened only by a pair: "
          f"{len(pair_only)}", flush=True)

    # ---- hypergraph
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
    edges = []
    for r, cs in row_single.items():
        if len(cs) > 1:
            cl = sorted(cs)
            edges.append(dict(row=list(r[1]), kind="single-probe",
                              cells=[cellstr(K) for K in cl]))
            for x in cl[1:]:
                union(cl[0], x)
    for r, pairs in pair_only.items():
        for (K1, K2) in pairs:
            edges.append(dict(row=list(r[1]), kind="pair-only",
                              cells=[cellstr(K1), cellstr(K2)]))
            union(K1, K2)
    comps = defaultdict(list)
    for K in BASIS:
        comps[find(K)].append(K)
    components = sorted((sorted(v, key=cellstr) for v in comps.values()),
                        key=lambda c: (-len(c), cellstr(c[0])))
    print(f"components: {len(components)}; sizes {[len(c) for c in components]}",
          flush=True)

    A_, Bc = parse("1|5|10|0|0|0"), parse("1|7|8|0|0|0")
    same = find(A_) == find(Bc)
    print(f"1|5|10 and 1|7|8 now in the same component: {same}", flush=True)

    out = dict(
        inputs={p: sha(p) for p in ("r171/certs/joint_vector_171.json",
                                    "r170/certs/basis_170.json")},
        supersedes="the interaction_components field of "
                   "r171/certs/joint_vector_171.json, which used a "
                   "one-cell-at-a-time probe and under-detected couplings",
        defect_found=dict(
            row=[3, 0, 0, 1, 10, 4, 2, 0, 8, 0, 0],
            opens_with=["1|5|10|0|0|0 at 129", "1|7|8|0|0|0 at 123"],
            opens_with_either_alone=False,
            opens_with_either_at_its_fallback_alone=False,
            consequence="a one-cell probe cannot see a row that needs two "
                        "cells weakened together, so the row contributed no "
                        "edge and the interacting pair was split across "
                        "components"),
        probe=dict(singles=len(BASIS), pairs=tested,
                   rows_opened_only_by_a_pair=len(pair_only),
                   evaluated_at="the feasible joint vector B, which is where "
                                "the production question lives"),
        rows_coupling_multiple_cells=len([e for e in edges]),
        coupling_edges=edges,
        component_count=len(components),
        components=[dict(size=len(c), cells=[cellstr(K) for K in c])
                    for c in components],
        largest_component=max(len(c) for c in components),
        coupled_cell_count=sum(len(c) for c in components if len(c) > 1),
        singleton_cells=[cellstr(c[0]) for c in components if len(c) == 1],
        observed_pair_same_component=same,
        completeness="PAIRWISE_COMPLETE: couplings of order one and two are "
                     "detected.  A row needing three or more cells weakened "
                     "simultaneously, with no pair sufficient, would not be "
                     "seen; the structure is not claimed to be complete",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = same
    (ROOT / "r171" / "certs" / "interaction_171.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "coupling_edges", "components")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
