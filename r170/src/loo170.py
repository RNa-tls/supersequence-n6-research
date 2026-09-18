#!/usr/bin/env python3
"""Round 170 -- leave-one-out ablation of a verified ladder.

`ablate170.py` counted how often each rung supplies the (p) minimum and found
every H rung winning at least once, so nothing could be dropped on that
evidence alone.  The counts were also tiny -- seventeen winning states across
an eight million node search -- and that makes the test WEAK in one direction:
a rung can be the argmin at a state that the fallback bound would have pruned
anyway, in which case its win bought nothing.  Winning is necessary for a rung
to matter, not sufficient.

The decisive test is to drop the rung and rebuild.  Three outcomes separate:

  IDLE       the build completes with the SAME proof-node count, so the rung
             contributed nothing and the certificate never needed it;
  HELPFUL    the build completes but costs more, so the rung is a saving and
             not a prerequisite;
  ESSENTIAL  the build no longer completes inside the cap at all.

Builds are independent, so they run in parallel.  The cap is set well above
the full-ladder cost so "more expensive" stays distinguishable from "gone".
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
CAP: int = 0


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def _one(drop):
    sub = {K: c for K, c in CERT.items() if K != drop}
    t0 = time.time()
    g = G.Engine(sub, CAP)
    toks, err = g.build(TARGET, SAFE)
    n = len(toks) if toks else 0
    del toks
    return dict(dropped=G.cellstr(drop), search_nodes=g.nodes, proof_nodes=n,
                completed=bool(n), detail=None if n else str(err)[:70],
                seconds=round(time.time() - t0, 1))


def _init(cert, target, safe, cap):
    global CERT, TARGET, SAFE, CAP
    CERT, TARGET, SAFE, CAP = cert, target, safe, cap


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
    ap.add_argument("--baseline", type=int, required=True,
                    help="full-ladder proof nodes, for classification")
    ap.add_argument("--node-cap", type=int, default=40_000_000)
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()

    T = parse(a.cell)
    rungs = [parse(x) for x in
             Path(a.rungs[1:]).read_text().split() if x.strip()]
    _refs, dep_map = G.load_refs(a.ref, verify168.verify_any)
    cert = {cell: c for cell, (c, _p, _r) in dep_map.items()}
    present = [K for K in rungs if K in cert]
    print(f"{len(cert)} certified cells; dropping each of {len(present)} "
          f"rungs in turn; cap {a.node_cap:,}; {a.jobs} jobs", flush=True)

    t0 = time.time()
    with Pool(a.jobs, initializer=_init,
              initargs=(cert, T, a.safe, a.node_cap)) as pool:
        rows = pool.map(_one, present)

    for r in rows:
        if not r["completed"]:
            r["verdict"] = "ESSENTIAL"
        elif r["proof_nodes"] == a.baseline:
            r["verdict"] = "IDLE"
        else:
            r["verdict"] = "HELPFUL"
        r["delta_vs_baseline"] = (r["proof_nodes"] - a.baseline
                                 if r["completed"] else None)
        print(f"  drop {r['dropped']:>16} {r['verdict']:<10} "
              f"proof={r['proof_nodes']:>12,} "
              f"delta={r['delta_vs_baseline']} {r['seconds']}s", flush=True)

    tally = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    idle = [r["dropped"] for r in rows if r["verdict"] == "IDLE"]

    out = dict(
        cell=G.cellstr(T), census_safe_bound_S=a.safe,
        baseline_proof_nodes=a.baseline,
        node_cap=a.node_cap,
        rungs_tested=len(present),
        rows=rows,
        tally=tally,
        droppable_rungs=idle,
        minimal_useful_subset_size=len(present) - len(idle),
        reading="IDLE means the certificate never needed that rung; HELPFUL "
                "means it is a saving but not a prerequisite; ESSENTIAL means "
                "the build does not finish without it.  Only IDLE rungs can "
                "be removed from the investment without changing the result",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = True
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
