#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- COMPLETE failed-call probe (bounded diagnostic).

Unlike the Round 171 `helper_query_probe.json` (which kept only calls
dominated by one candidate helper), this records EVERY scalar (p) call whose
value exceeds what would prune, with its full query, in the first N nodes of
the unchanged search.  A control run of the unchanged gen168 engine must
visit the same nodes (control equivalence).

For each failed call it also evaluates, offline and exactly, what R1 would
return for that same query (R1 depends only on the query tuple: t and
d0 = d* - 5t), giving a PREDICTED R1 prune count for these calls.  That is a
per-call prediction, not a tree-size prediction.

usage: probe172.py --env-job <job id> --cell b|d|a|bb|e|h --bound J [--nodes N]
"""
from __future__ import annotations
import argparse, collections, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
import env172 as E                                                # noqa: E402
import gen172 as X                                                # noqa: E402

OUT = "r172/certs/probe/"


class Probe(X.G.Engine):
    def __init__(self, cert, limit, bound):
        super().__init__(cert, limit)
        self.bound = bound
        self.calls = 0
        self.failed = collections.Counter()

    def ub(self, *k):
        v = super().ub(*k)
        ports = sys._getframe(1).f_locals["ports"]
        self.calls += 1
        need = self.bound + 1 - ports
        if v > need:
            self.failed[(k, need, v)] += 1
        return v


def r1_value(ub, tok, dstar, a, bb, e, h):
    d0 = dstar - 5 * tok
    vals = [ub(tok - r, d0 + 5 * r, a, bb, e, h)
            for r in range(tok + 1) if d0 + 5 * r >= 0]
    return max(vals) if vals else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-job", required=True)
    ap.add_argument("--cell", required=True)
    ap.add_argument("--bound", type=int, required=True)
    ap.add_argument("--nodes", type=int, default=100000)
    a = ap.parse_args()
    job, refs, dep, cert = E.load_job_env(a.env_job)
    cell = tuple(int(x) for x in a.cell.split("|"))
    assert cell not in cert, "target certified in this environment"
    p = Probe(cert, a.nodes, a.bound)
    pt, pe = p.build(cell, a.bound)
    c = X.G.Engine(cert, a.nodes)
    ct, ce = c.build(cell, a.bound)
    assert (pt, pe, p.nodes) == (ct, ce, c.nodes), "probe changed the search"
    ub = X.G.Engine(cert, 0).ub
    rows, tot, pred = [], 0, 0
    by_d0 = collections.Counter()
    for (k, need, v), n in p.failed.most_common():
        u1 = r1_value(ub, *k)
        prunes = u1 is None or u1 <= need
        tot += n
        pred += n * prunes
        by_d0["d0<0" if k[1] - 5 * k[0] < 0 else "d0>=0"] += n
        rows.append(dict(query="|".join(map(str, k)), required_upper=need,
                         current_upper=v, r1_upper=u1, r1_prunes=prunes,
                         fallback=v == X.G.R.UBFALL + k[2] + k[3] + k[4],
                         count=n))
    fb = sum(r["count"] for r in rows if r["fallback"])
    out = dict(status="BOUNDED_DIAGNOSTIC_NOT_A_CERTIFICATE", cell=a.cell,
               bound=a.bound, probe_nodes=p.nodes, control_nodes=c.nodes,
               control_equivalent=True, completed_within_probe=pt is not None,
               environment_job=a.env_job,
               predecessor_set_sha256=job["predecessor_set_sha256"],
               ub_calls=p.calls, failed_calls=tot,
               failed_calls_fallback_valued=fb,
               failed_calls_by_d0=dict(by_d0),
               r1_would_prune=pred,
               r1_would_prune_fraction=pred / tot if tot else None,
               source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               rows=rows)
    rel = OUT + a.cell.replace("|", "_") + f"_n{a.nodes}_{a.env_job.rsplit('_', 1)[-1]}.json"
    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / rel).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}), flush=True)


if __name__ == "__main__":
    main()
