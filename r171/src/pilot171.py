#!/usr/bin/env python3
"""Round 171 -- bounded pilots on the 33 remaining load-bearing bounds.

Nothing large is generated until every remaining cell has been priced, because
round 170 showed the spread is enormous: two cells proved at a census-safe
bound came in at 8,099,282 and 218 nodes.  Scheduling against an average of
those would be meaningless.

Each pilot proves the production claim directly -- build(K, S(K)), no
discovery -- against the genuine predecessor set only, under a cap chosen to
triage rather than to finish.  What comes out is one of:

  CHEAP_DIRECT           finished inside the triage cap on what already exists;
  HELPER_ACCELERATED     finished, but only with helper certificates in the
                         predecessor set that a bare run does not have;
  NEEDS_NEW_INVESTMENT   did not finish, and the trace shows the (p) bound
                         falling back to the analytic value at mid depth,
                         which is the signature a ladder addresses;
  EXPENSIVE_UNRESOLVED   did not finish and shows no such signature.

A cap hit is DEFERRED.  It is a strict lower bound on that cell's cost and
never evidence that the bound is false.

The dossier's slack column predicts most of this.  A cell whose safe bound
sits 68 above its historical capacity has enormous room and should fall
quickly; `1|11|4|0|0|0` has zero slack, so its safe bound is exactly its
capacity and no margin exists to prune against.  The pilots test that
prediction rather than assuming it.
"""
from __future__ import annotations
import json, sys, time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import gen168 as G                                                # noqa: E402
import routeb164 as R                                            # noqa: E402

CERT: dict = {}


def parse(s):
    return tuple(int(x) for x in s.split("|"))


class Probe(G.Engine):
    """Engine that records where (p) stops being the analytic fallback."""

    def __init__(self, certified, node_cap):
        super().__init__(certified, node_cap)
        self.first_nonfallback_depth = None
        self.nonfallback_states = 0
        self.fallback_states = 0

    def ub(self, tok, d, a, bb, e, h):
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        fb = R.UBFALL + a + bb + e
        best = fb
        for (kb, kd, ka, kbb, ke, kh), c in self.cert.items():
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best = c
        if best < fb:
            self.nonfallback_states += 1
            if self.first_nonfallback_depth is None:
                self.first_nonfallback_depth = d
        else:
            self.fallback_states += 1
        self._ubc[key] = best
        return best


def _init(cert):
    global CERT
    CERT = cert


def _one(spec):
    cellstr, S, cap = spec
    K = parse(cellstr)
    t0 = time.time()
    g = Probe(CERT, cap)
    toks, err = g.build(K, S)
    n = len(toks) if toks else 0
    del toks
    tot = g.nonfallback_states + g.fallback_states
    return dict(
        cell=cellstr, safe_bound_S=S, extree_target=S + 1,
        completed=bool(n), proof_nodes=n, search_nodes=g.nodes,
        node_cap=cap,
        detail=None if n else str(err)[:70],
        first_nonfallback_p_depth=g.first_nonfallback_depth,
        states_with_a_real_dominator=g.nonfallback_states,
        states_on_analytic_fallback=g.fallback_states,
        fallback_fraction=(round(g.fallback_states / tot, 4) if tot else None),
        seconds=round(time.time() - t0, 1))


def main():
    import argparse
    import verify168
    verify168.load_trust()
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-cap", type=int, default=2_000_000)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--report", default="r171/certs/pilots_171.json")
    ap.add_argument("--only", default="", help="comma separated cells")
    a = ap.parse_args()

    doss = json.loads((ROOT / "r171" / "certs"
                       / "remaining_171.json").read_text())
    refs = doss["genuine_certificates"]
    _r, dep_map = G.load_refs(refs, verify168.verify_any)
    cert = {c: v for c, (v, _p, _rel) in dep_map.items()}
    print(f"genuine predecessor set: {len(cert)} certified cells from "
          f"{len(refs)} certificates", flush=True)

    want = set(a.only.split(",")) if a.only else None
    jobs = [(d["cell"], d["safe_upper_bound_S"], a.node_cap)
            for d in doss["dossier"]
            if want is None or d["cell"] in want]
    slack = {d["cell"]: d["slack_S_minus_historical"]
             for d in doss["dossier"]}
    # cheapest-looking first: the biggest slack should fall fastest
    jobs.sort(key=lambda j: -(slack.get(j[0]) or 0))
    print(f"{len(jobs)} pilots, triage cap {a.node_cap:,}, {a.jobs} jobs",
          flush=True)

    t0 = time.time()
    rows = []

    def classify(r):
        if r["completed"]:
            return "CHEAP_DIRECT"
        frac = r["fallback_fraction"]
        if frac is not None and frac >= 0.5:
            return "NEEDS_NEW_INVESTMENT"
        return "EXPENSIVE_UNRESOLVED"

    def flush():
        done = [r for r in rows if r["completed"]]
        (ROOT / a.report).write_text(json.dumps(dict(
            triage_cap=a.node_cap,
            genuine_predecessor_cells=len(cert),
            pilots=len(rows), planned=len(jobs),
            complete=len(rows) == len(jobs),
            finished_inside_cap=len(done),
            deferred=len(rows) - len(done),
            total_proof_nodes_of_finished=sum(r["proof_nodes"]
                                              for r in done),
            cap_hit_meaning="DEFERRED: a strict lower bound on that cell's "
                            "cost, never evidence the bound is false",
            classification_rule="CHEAP_DIRECT finished on what exists; "
                                "NEEDS_NEW_INVESTMENT deferred with the (p) "
                                "bound mostly on the analytic fallback, the "
                                "signature a ladder addresses; "
                                "EXPENSIVE_UNRESOLVED deferred without it",
            rows=sorted(rows, key=lambda r: (not r["completed"],
                                             r["proof_nodes"] or 1 << 60)),
            seconds_noncanonical=round(time.time() - t0, 1),
            ok=True), ensure_ascii=False, indent=1) + "\n")

    with Pool(a.jobs, initializer=_init, initargs=(cert,)) as pool:
        for r in pool.imap_unordered(_one, jobs):
            r["classification"] = classify(r)
            r["slack_diagnostic"] = slack.get(r["cell"])
            rows.append(r)
            print(f"  {r['cell']:>16} S={r['safe_bound_S']:<4} "
                  f"{r['classification']:<22} "
                  f"proof={r['proof_nodes']:>10,} "
                  f"fb_frac={r['fallback_fraction']} {r['seconds']}s",
                  flush=True)
            flush()
    flush()
    print(f"\nfinished inside cap: "
          f"{sum(1 for r in rows if r['completed'])}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
