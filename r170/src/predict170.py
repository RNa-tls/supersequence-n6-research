#!/usr/bin/env python3
"""Round 170 -- subsets predicted by the capacity-group structure.

The trace and the leave-one-out disagreed until the rung CAPACITIES were laid
beside them:

    cap  53: d=3                cap  92: d=8, d=9, d=10
    cap  66: d=4, d=5           cap  99: d=11
    cap  79: d=6, d=7           cap 103: d=12, d=13
                                cap 106: d=14

A rung (0,d,0,0,0,1) bounds every state with d* <= d, so within a group of
EQUAL capacity the largest d subsumes the smaller ones exactly -- same bound,
strictly more states.  That predicts precisely the observed leave-one-out
pattern: d=4 idle under d=5, d=6 idle under d=7, d=8 and d=9 idle under d=10,
and d=12, d=13 each idle under the other while neither is droppable once both
are gone.  It also explains the non-additivity, since dropping all six idle
rungs together removes cap 103 entirely.

The sweep's prefix/suffix/stride families do not contain the set this
structure points at -- one rung per distinct capacity, preferring the cheaper
member of a tied group and weighing each rung's own certification cost against
what it returns.  Those candidates are built here explicitly.
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


def _init(cert, target, safe, ladder):
    global CERT, TARGET, SAFE, LADDER
    CERT, TARGET, SAFE, LADDER = cert, target, safe, ladder


def _one(spec):
    name, keep, cap = spec
    keep = set(keep)
    sub = {K: c for K, c in CERT.items()
           if K not in set(LADDER) or K in keep}
    t0 = time.time()
    g = G.Engine(sub, cap)
    toks, err = g.build(TARGET, SAFE)
    n = len(toks) if toks else 0
    del toks
    return dict(variant=name, rungs=sorted(G.cellstr(k) for k in keep),
                rungs_n=len(keep), search_nodes=g.nodes, proof_nodes=n,
                completed=bool(n), detail=None if n else str(err)[:60],
                seconds=round(time.time() - t0, 1))


def main():
    import argparse
    import verify168
    verify168.load_trust()
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--baseline", type=int, required=True)
    ap.add_argument("--node-cap", type=int, default=30_000_000)
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()

    T = (0, 15, 0, 0, 0, 1)
    SAFE_ = 115
    ladder = [(0, d, 0, 0, 0, 1) for d in range(3, 15)]
    refs = ["r164/certs/extree_prefix_164.txt.gz",
            "r166/certs/extree_batch2_166.txt.gz",
            "r166/certs/extree_batch3_166.txt.gz",
            "r168/certs/extree_batch1_168.txt.gz",
            "r170/certs/extree_ladder_h_170.txt.gz"]
    _r, dep_map = G.load_refs(refs, verify168.verify_any)
    cert = {c: v for c, (v, _p, _rel) in dep_map.items()}
    va = json.loads((ROOT / "r170" / "certs"
                     / "verification_a_h_170.json").read_text())
    rung_cost = {tuple(int(x) for x in r["cell"].split("|")): r["nodes"]
                 for r in va["per_cell"]["r170/certs/extree_ladder_h_170.txt.gz"]}

    spec = json.loads(Path(a.spec).read_text())["subsets"]
    jobs = [(name, [(0, d, 0, 0, 0, 1) for d in ds], a.node_cap)
            for name, ds in spec.items()]
    print(f"{len(cert)} certified cells; {len(jobs)} predicted subsets; "
          f"cap {a.node_cap:,}", flush=True)

    t0 = time.time()
    rows = []

    def flush():
        done = [r for r in rows if r["completed"]]
        best = min(done, key=lambda r: r["total_nodes"], default=None)
        (ROOT / a.report).write_text(json.dumps(dict(
            cell=G.cellstr(T), census_safe_bound_S=SAFE_,
            baseline_target_proof_nodes=a.baseline,
            full_ladder_investment=sum(rung_cost.values()),
            full_ladder_total=sum(rung_cost.values()) + a.baseline,
            capacity_groups={str(c): sorted(K[1] for K in rung_cost
                                            if rung_cost[K] is not None
                                            and cert.get(K) == c)
                             for c in sorted(set(cert[K] for K in ladder
                                                 if K in cert))},
            structural_rule="a rung bounds every state with d* <= d, so "
                            "within an equal-capacity group the largest d "
                            "subsumes the smaller ones: same bound, strictly "
                            "more states",
            variants=sorted(rows, key=lambda r: (r["total_nodes"] is None,
                                                 r["total_nodes"] or 0)),
            cheapest=best, complete=len(rows) == len(jobs),
            seconds_noncanonical=round(time.time() - t0, 1), ok=True),
            ensure_ascii=False, indent=1) + "\n")

    with Pool(a.jobs, initializer=_init,
              initargs=(cert, T, SAFE_, ladder)) as pool:
        for r in pool.imap_unordered(_one, jobs):
            keep = {tuple(int(x) for x in c.split("|")) for c in r["rungs"]}
            r["ladder_investment"] = sum(rung_cost[K] for K in keep)
            r["total_nodes"] = (r["ladder_investment"] + r["proof_nodes"]
                                if r["completed"] else None)
            r["delta_vs_baseline"] = (r["proof_nodes"] - a.baseline
                                      if r["completed"] else None)
            rows.append(r)
            print(f"  {r['variant']:<26} n={r['rungs_n']:<3} "
                  f"invest={r['ladder_investment']:>11,} "
                  f"target={r['proof_nodes']:>12,} "
                  f"total={(r['total_nodes'] or 0):>12,} {r['seconds']}s"
                  + ("" if r["completed"] else "  DEFERRED"), flush=True)
            flush()
    flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
