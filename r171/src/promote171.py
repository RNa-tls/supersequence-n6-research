#!/usr/bin/env python3
"""Round 171 -- the dual-acceptance gate, compared at the right granularity.

A first version of this check compared verifier A's total against verifier B's
total and declared two sound certificates FAILED.  The mistake was the
granularity: verifier A is run on one batch and reports that batch, while
verifier B walks the whole dependency DAG and reports the sum over every batch
it REPLAYED.  When a dependency is not in the trust table B replays it too, so
B's total legitimately exceeds the batch under test.

The comparison that means something is per batch:

    verifier A's node count for the batch
      == verifier B's node count for that same batch
      == the generator's proof-node count
      == verifier B's histogram-check count for that batch

with zero histogram mismatches and both verifiers reporting all_ok.  That is
what this module enforces, and it prints B's extra replay separately so the
dual-verification cost stays visible instead of looking like a discrepancy.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True,
                    help="tag:batch:report_a:report_b:generator comma list")
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    rows, all_ok = [], True
    for case in a.cases.split(","):
        tag, batch, ra, rb, rg = case.split(":")
        A = json.loads((ROOT / ra).read_text())
        B = json.loads((ROOT / rb).read_text())
        G = json.loads((ROOT / rg).read_text())
        a_nodes = A["total_nodes"]
        b_batch = B["batches"].get(batch, {})
        b_nodes = b_batch.get("nodes")
        hist = b_batch.get("hist_checks")
        gen = G.get("proof_nodes") or G.get("total_proof_nodes")
        cells = A["per_cell"][batch]
        statuses = {c["status"] for c in cells}
        agree = (a_nodes == b_nodes == gen == hist)
        ok = (A["all_ok"] and B["all_ok"]
              and B["histogram_mismatches"] == 0
              and agree and statuses == {"UPPER_CERTIFIED"})
        all_ok &= ok
        extra = B["total_proof_nodes"] - (b_nodes or 0)
        rows.append(dict(
            tag=tag, batch=batch,
            cells=[dict(cell=c["cell"], cap=c["cap"], status=c["status"],
                        nodes=c["nodes"]) for c in cells],
            verifier_a_nodes=a_nodes, verifier_b_nodes_for_this_batch=b_nodes,
            generator_proof_nodes=gen,
            verifier_b_histogram_checks=hist,
            four_way_identical=agree,
            verifier_a_all_ok=A["all_ok"], verifier_b_all_ok=B["all_ok"],
            histogram_mismatches=B["histogram_mismatches"],
            verifier_b_extra_replay_nodes=extra,
            verifier_b_also_replayed=[r for r in B["replayed_here"]
                                      if r != batch],
            status="GENUINELY_CERTIFIED" if ok else "NOT_ACCEPTED"))
        print(f"  {tag:<6} {statuses} A={a_nodes:,} B={b_nodes:,} "
              f"gen={gen:,} hist={hist:,} -> {rows[-1]['status']}"
              + (f"   (B also replayed {extra:,} nodes of untrusted deps)"
                 if extra else ""), flush=True)

    out = dict(
        gate="per-batch four-way identity, not aggregate totals",
        why="verifier B walks the whole DAG and sums every batch it replays, "
            "so its total exceeds the batch under test whenever a dependency "
            "is outside the trust table; comparing that total against one "
            "batch's count wrongly reports a failure",
        cases=rows,
        all_genuinely_certified=all_ok,
        ok=all_ok)
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
