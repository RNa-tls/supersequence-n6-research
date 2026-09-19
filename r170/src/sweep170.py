#!/usr/bin/env python3
"""Round 170 -- subset sweep over a genuinely certified ladder.

Round 170's first ablation pass tested remove-one and two hand-picked
subsets.  That is not enough to claim a minimal useful ladder, because the
per-rung deltas are measured with every OTHER rung present and are not
additive: dropping the six individually-idle H rungs together cost 557,525
nodes even though each cost nothing alone.

So the subsets have to be built.  This module sweeps a family of them --
prefixes, suffixes, remove-one, and sparse strides -- and scores each on what
actually matters:

    total cost = (cost of certifying the kept rungs) + (cost of the target)

not on rung count.  A rung that is technically removable stays if removing it
raises the target by more than the rung costs to build; a rung that is
technically useful goes if it costs more than it returns.  `0|14|0|0|0|1` is
the extreme case in Family H -- 22,770,490 nodes to certify, 1,202,144 saved.

Every capacity used is one both verifiers accepted, so a build restricted to a
subset is a genuine certificate depending only on that subset.
"""
from __future__ import annotations
import json, sys, time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r168" / "src"))
import gen168 as G                                                # noqa: E402

CERT: dict = {}
TARGET: tuple = ()
SAFE: int = 0
LADDER: list = []


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def _init(cert, target, safe, ladder):
    global CERT, TARGET, SAFE, LADDER
    CERT, TARGET, SAFE, LADDER = cert, target, safe, ladder


def _one(spec):
    name, keep, cap = spec
    keep = set(keep)
    allr = set(LADDER)
    sub = {K: c for K, c in CERT.items() if K not in allr or K in keep}
    t0 = time.time()
    g = G.Engine(sub, cap)
    toks, err = g.build(TARGET, SAFE)
    n = len(toks) if toks else 0
    del toks
    return dict(variant=name, rungs_kept=sorted(G.cellstr(k) for k in keep),
                rungs_kept_n=len(keep), node_cap=cap, search_nodes=g.nodes,
                proof_nodes=n, completed=bool(n),
                detail=None if n else str(err)[:70],
                seconds=round(time.time() - t0, 1))


def main():
    import argparse
    import verify168
    verify168.load_trust()

    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--safe", type=int, required=True)
    ap.add_argument("--rungs", required=True)
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--rung-costs", required=True,
                    help="verifier A report naming the ladder batch")
    ap.add_argument("--ladder-batch", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--baseline", type=int, required=True)
    ap.add_argument("--node-cap", type=int, default=60_000_000)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--skip-drop-one", action="store_true",
                    help="remove-one already measured elsewhere (loo170)")
    a = ap.parse_args()

    T = parse(a.cell)
    ladder = [parse(x) for x in
              Path(a.rungs[1:]).read_text().split() if x.strip()]
    _refs, dep_map = G.load_refs(a.ref, verify168.verify_any)
    cert = {cell: c for cell, (c, _p, _r) in dep_map.items()}
    va = json.loads((ROOT / a.rung_costs).read_text())
    rung_cost = {parse(r["cell"]): r["nodes"]
                 for r in va["per_cell"][a.ladder_batch]}
    full_inv = sum(rung_cost.values())

    # the subset families
    jobs, seen = [], set()

    def add(name, keep):
        key = tuple(sorted(keep))
        if key in seen:
            return
        seen.add(key)
        jobs.append((name, list(keep), a.node_cap))

    n = len(ladder)
    for k in range(n + 1):
        add(f"prefix_{k}", ladder[:k])
    for k in range(n + 1):
        add(f"suffix_{k}", ladder[n - k:] if k else [])
    if not a.skip_drop_one:
        for i, K in enumerate(ladder):
            add(f"drop_{G.cellstr(K)}", [x for x in ladder if x != K])
    for step in (2, 3, 4):
        for off in range(step):
            add(f"stride{step}_off{off}", ladder[off::step])
    # The cap here is a SCREENING cap.  A subset whose target alone already
    # exceeds the full ladder's entire total cannot be the cheapest subset
    # whatever its exact cost, so running it to completion teaches nothing; it
    # is recorded as "> cap" and excluded from the minimum rather than being
    # given a fabricated number.
    print(f"{len(cert)} certified cells, {n} rungs, {len(jobs)} distinct "
          f"subsets, screening cap {a.node_cap:,} "
          f"(full-ladder total {full_inv + a.baseline:,}), {a.jobs} jobs",
          flush=True)

    t0 = time.time()
    rows = []

    def flush():
        done = [r for r in rows if r["completed"]]
        best = min(done, key=lambda r: r["total_nodes"], default=None)
        (ROOT / a.report).write_text(json.dumps(dict(
            cell=G.cellstr(T), census_safe_bound_S=a.safe,
            baseline_target_proof_nodes=a.baseline,
            full_ladder_rungs=n, full_ladder_investment=full_inv,
            full_ladder_total=full_inv + a.baseline,
            subsets_tested=len(rows), subsets_planned=len(jobs),
            complete=len(rows) == len(jobs),
            rung_costs={G.cellstr(K): v for K, v in rung_cost.items()},
            variants=sorted(rows, key=lambda r: (r["total_nodes"] is None,
                                                 r["total_nodes"] or 0)),
            cheapest=dict(
                variant=best["variant"], rungs=best["rungs_kept_n"],
                investment=best["ladder_investment"],
                target=best["proof_nodes"], total=best["total_nodes"],
                saving_vs_full_ladder=full_inv + a.baseline
                - best["total_nodes"]) if best else None,
            optimised="total proof nodes (ladder certification + target), "
                      "not rung count",
            seconds_noncanonical=round(time.time() - t0, 1),
            ok=True), ensure_ascii=False, indent=1) + "\n")

    with Pool(a.jobs, initializer=_init,
              initargs=(cert, T, a.safe, ladder)) as pool:
        for r in pool.imap_unordered(_one, jobs):
            keep = {parse(c) for c in r["rungs_kept"]}
            r["ladder_investment"] = sum(rung_cost[K] for K in keep)
            r["total_nodes"] = (r["ladder_investment"] + r["proof_nodes"]
                                if r["completed"] else None)
            r["delta_vs_baseline"] = (r["proof_nodes"] - a.baseline
                                      if r["completed"] else None)
            rows.append(r)
            print(f"  {r['variant']:<22} rungs={r['rungs_kept_n']:<3} "
                  f"invest={r['ladder_investment']:>11,} "
                  f"target={r['proof_nodes']:>12,} "
                  f"total={(r['total_nodes'] or 0):>12,} {r['seconds']}s"
                  + ("" if r["completed"] else "  DEFERRED"), flush=True)
            flush()
    flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
