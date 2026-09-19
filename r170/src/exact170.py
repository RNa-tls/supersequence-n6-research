#!/usr/bin/env python3
"""Round 170 -- the exact-target row of the two-factor table.

The 2x2 needs four cells per family: exact target or census-safe target,
crossed with no ladder or the genuine ladder.  Three were already measured.
The missing row is the EXACT target, which means running discovery -- the
maximising search that finds cap(T) itself rather than proving cap(T) <= S.

`gen168.py` would do this, but it writes its output through
`Path.relative_to(ROOT)` and so cannot write outside the repository; an
earlier attempt pointed it at the scratchpad and died at serialisation AFTER
completing the search.  The searches themselves are what the table needs, so
this module runs discovery directly and records only that.  Nothing is
generated, nothing is certified, and no certificate file is produced -- a
deferred discovery proves no bound at all, which is exactly the finding.

A deferral is reported as a strict lower bound, never as a cost.  "Did not
finish inside 30,000,001 nodes" is knowledge; turning it into a number would
not be.
"""
from __future__ import annotations
import json, sys, time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r168" / "src"))
import gen168 as G                                                # noqa: E402

BASE = ["r164/certs/extree_prefix_164.txt.gz",
        "r166/certs/extree_batch2_166.txt.gz",
        "r166/certs/extree_batch3_166.txt.gz",
        "r168/certs/extree_batch1_168.txt.gz"]
LADDER = {"H": "r170/certs/extree_ladder_h_170.txt.gz",
          "A2": "r170/certs/extree_ladder_a2_170.txt.gz"}
TARGET = {"H": (0, 15, 0, 0, 0, 1), "A2": (0, 18, 2, 0, 0, 0)}


def _one(spec):
    family, with_ladder, cert, cap = spec
    T = TARGET[family]
    t0 = time.time()
    g = G.Engine(cert, cap)
    capfound, err = g.discover(T)
    return dict(family=family, with_ladder=with_ladder,
                cell=G.cellstr(T), stage="discovery",
                discovered_cap=capfound,
                completed=capfound is not None,
                search_nodes=g.nodes, node_cap=cap,
                detail=None if capfound is not None else str(err)[:80],
                seconds=round(time.time() - t0, 1))


def main():
    import argparse
    import verify168
    verify168.load_trust()
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-cap", type=int, default=30_000_000)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--report", default="r170/certs/exact_targets_170.json")
    a = ap.parse_args()

    jobs = []
    for family in ("H", "A2"):
        for with_ladder in (False, True):
            refs = list(BASE) + ([LADDER[family]] if with_ladder else [])
            _r, dep_map = G.load_refs(refs, verify168.verify_any)
            cert = {c: v for c, (v, _p, _rel) in dep_map.items()}
            jobs.append((family, with_ladder, cert, a.node_cap))
            print(f"  {family} with_ladder={with_ladder}: "
                  f"{len(cert)} certified cells", flush=True)

    t0 = time.time()
    rows = []

    def flush():
        (ROOT / a.report).write_text(json.dumps(dict(
            purpose="the exact-target row of the two-factor 2x2: discovery "
                    "finds cap(T) itself, rather than proving cap(T) <= S",
            node_cap=a.node_cap,
            runs=rows,
            complete=len(rows) == len(jobs),
            reporting_rule="a deferral is a strict lower bound, not a cost; "
                           "it is recorded as 'did not finish inside the cap' "
                           "and never converted into a number",
            seconds_noncanonical=round(time.time() - t0, 1),
            ok=True), ensure_ascii=False, indent=1) + "\n")

    with Pool(a.jobs) as pool:
        for r in pool.imap_unordered(_one, jobs):
            rows.append(r)
            print(f"  {r['family']:<3} ladder={str(r['with_ladder']):<5} "
                  f"{'cap=' + str(r['discovered_cap']) if r['completed'] else 'DEFERRED':<14} "
                  f"nodes={r['search_nodes']:>12,} {r['seconds']}s", flush=True)
            flush()
    flush()
    print(json.dumps(dict(runs=[{k: v for k, v in r.items()
                                 if k != "detail"} for r in rows]),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
