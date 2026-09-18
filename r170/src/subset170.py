#!/usr/bin/env python3
"""Round 170 -- what the ladder is actually worth, as an investment.

Leave-one-out settled two things about the H ladder and unsettled a third.
Six rungs are IDLE (dropping one changes nothing), six are HELPFUL (dropping
one costs more but still finishes), and NONE is ESSENTIAL.  So no individual
rung is a prerequisite, yet the twelve together are what separates a finished
build from a deferral -- the value is collective.

That makes the investment question sharp, because the per-rung economics are
lopsided.  `0|14|0|0|0|1` costs 22,770,490 nodes to certify and saves
1,202,144 on the target; `0|13|0|0|0|1` costs 8,676,028 and saves nothing.
Nine of the twelve cost more to build than they ever return.

Leave-one-out cannot answer this on its own: each delta was measured with all
ELEVEN other rungs present, and the deltas are not additive, so a subset has
to be built to be believed.  Two questions decide the verdict.

  1. Is the ladder an ENABLER or a SPEEDUP?  The no-ladder control was only
     ever run to a 20 million node cap and reported as deferred.  Deferred at
     a cap is not the same as impossible, and if a larger cap finishes, the
     ladder is buying time rather than buying the certificate.

  2. What does the CHEAPEST useful ladder cost?  If the three rungs whose
     saving exceeds their own build cost carry most of the benefit, the
     investment falls from 34.9 million to under a hundred thousand.
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


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def _init(cert, target, safe):
    global CERT, TARGET, SAFE
    CERT, TARGET, SAFE = cert, target, safe


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
                rungs_kept_n=len(keep), node_cap=cap,
                search_nodes=g.nodes, proof_nodes=n, completed=bool(n),
                detail=None if n else str(err)[:70],
                seconds=round(time.time() - t0, 1))


LADDER: list = []


def main():
    import argparse
    import verify168
    verify168.load_trust()

    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--safe", type=int, required=True)
    ap.add_argument("--rungs", required=True)
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--report", required=True)
    ap.add_argument("--baseline", type=int, required=True)
    ap.add_argument("--control-cap", type=int, default=150_000_000)
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()

    global LADDER
    T = parse(a.cell)
    LADDER = [parse(x) for x in
              Path(a.rungs[1:]).read_text().split() if x.strip()]
    _refs, dep_map = G.load_refs(a.ref, verify168.verify_any)
    cert = {cell: c for cell, (c, _p, _r) in dep_map.items()}
    rung_cost = {}
    va = json.loads((ROOT / "r170" / "certs"
                     / "verification_a_h_170.json").read_text())
    for r in va["per_cell"]["r170/certs/extree_ladder_h_170.txt.gz"]:
        rung_cost[parse(r["cell"])] = r["nodes"]
    loo = {parse(r["dropped"]): r for r in
           json.loads((ROOT / "r170" / "certs"
                       / "loo_h_170.json").read_text())["rows"]}

    idle = [K for K in LADDER if loo[K]["verdict"] == "IDLE"]
    pays = [K for K in LADDER
            if (loo[K]["delta_vs_baseline"] or 0) > rung_cost[K]]
    notidle = [K for K in LADDER if loo[K]["verdict"] != "IDLE"]

    jobs = [
        ("no_ladder", [], a.control_cap),
        ("drop_all_idle", notidle, 40_000_000),
        ("only_self_paying", pays, 40_000_000),
    ]
    print(f"{len(cert)} certified cells.  variants: "
          + ", ".join(f"{n}({len(k)} rungs)" for n, k, _c in jobs), flush=True)
    print(f"self-paying rungs (saving > own build cost): "
          + ", ".join(G.cellstr(K) for K in pays), flush=True)

    t0 = time.time()
    with Pool(a.jobs, initializer=_init,
              initargs=(cert, T, a.safe)) as pool:
        rows = pool.map(_one, jobs)

    inv = {}
    for r in rows:
        keep = {parse(c) for c in r["rungs_kept"]}
        r["ladder_investment"] = sum(rung_cost[K] for K in keep)
        r["total_nodes"] = (r["ladder_investment"] + r["proof_nodes"]
                            if r["completed"] else None)
        r["delta_vs_baseline"] = (r["proof_nodes"] - a.baseline
                                  if r["completed"] else None)
        inv[r["variant"]] = r
        print(f"  {r['variant']:<18} rungs={r['rungs_kept_n']:<3} "
              f"invest={r['ladder_investment']:>11,} "
              f"target={r['proof_nodes']:>12,} "
              f"total={r['total_nodes'] if r['total_nodes'] else 'n/a':>12} "
              f"{r['seconds']}s" + ("" if r["completed"] else "  DEFERRED"),
              flush=True)

    full_total = sum(rung_cost.values()) + a.baseline
    best = min((r for r in rows if r["completed"]),
               key=lambda r: r["total_nodes"], default=None)
    control = inv["no_ladder"]
    out = dict(
        cell=G.cellstr(T), census_safe_bound_S=a.safe,
        baseline_target_proof_nodes=a.baseline,
        full_ladder_investment=sum(rung_cost.values()),
        full_ladder_total=full_total,
        variants=rows,
        control=dict(
            finished_without_any_ladder=control["completed"],
            cap=control["node_cap"],
            nodes_spent=control["search_nodes"],
            reading=("the ladder is a SPEEDUP, not an enabler: the build "
                     "finishes without it"
                     if control["completed"] else
                     "the build does not finish without a ladder inside a cap "
                     f"of {control['node_cap']:,} nodes, which is "
                     f"{control['node_cap'] // full_total}x the entire "
                     "full-ladder plan; on this evidence the ladder enables "
                     "the certificate rather than merely accelerating it")),
        cheapest_total=dict(
            variant=best["variant"] if best else None,
            total_nodes=best["total_nodes"] if best else None,
            versus_full_ladder=(full_total - best["total_nodes"]
                                if best else None)) if best else None,
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = True
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "variants"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
