#!/usr/bin/env python3
"""Round 170 -- the genuine dependency DAG and what it costs in wall time.

The schedule is built from DECLARED dependencies, not from family labels.  A
certificate can only start once every cell it cites is certified, and EXTREE
declares those citations explicitly, so the graph is read out of the artifacts
rather than guessed from cell coordinates.

Two honest limits shape what this can say.

First, only two of the thirty-five basis cells have a measured table-free cost
at a safe bound; the other thirty-three are unmeasured.  A schedule over
unmeasured work would be a schedule over invented numbers, so the critical
path is reported for the MEASURED subgraph, and the unmeasured remainder is
reported as a separate count with no time attached.

Second, node counts are converted to wall time with one measured rate rather
than a nominal one.  The rate comes from this round's own generation runs, and
it is quoted with the spread across them; the two happened to agree within
about 2 percent, which is worth stating rather than leaving implied.

The worker schedules are IDEALISED: perfect packing, no contention, no
reference-loading overhead.  Reference loading is real and was measured at
roughly twelve minutes for the H ladder before the trust table was extended,
so it is reported separately instead of being folded in.
"""
from __future__ import annotations
import gzip, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

BATCHES = [
    "r164/certs/extree_prefix_164.txt.gz",
    "r166/certs/extree_batch2_166.txt.gz",
    "r166/certs/extree_batch3_166.txt.gz",
    "r168/certs/extree_batch1_168.txt.gz",
    "r170/certs/extree_ladder_h_170.txt.gz",
    "r170/certs/extree_ladder_a2_170.txt.gz",
    "r170/certs/extree_target_h_170.txt.gz",
    "r170/certs/extree_target_a2_170.txt.gz",
]


def cellstr(K):
    return "|".join(map(str, K))


def scan(rel):
    text = gzip.decompress((ROOT / rel).read_bytes()).decode()
    own, deps, refs = {}, set(), []
    for line in text.splitlines():
        s = line.split("#")[0].split()
        if not s:
            continue
        if s[0] == "tree":
            own[tuple(int(x) for x in s[1:7])] = int(s[7])
        elif s[0] == "dep":
            deps.add(tuple(int(x) for x in s[1:7]))
        elif s[0] == "ref":
            # L6-EXTREE-2 writes `ref <sha> <path>`, version 3 writes
            # `ref <container_sha> <plain_sha> <path>`; the path is last in
            # both, which is how verifyA168 reads it too.
            refs.append(s[-1])
    return own, deps, refs


def main():
    owner, batch_own, batch_refs = {}, {}, {}
    for rel in BATCHES:
        own, deps, refs = scan(rel)
        batch_own[rel] = own
        batch_refs[rel] = refs
        for K in own:
            owner[K] = rel

    # per-cell measured cost: proof nodes, from the verifier A reports
    cost = {}
    for rep, key in (("r170/certs/verification_a_h_170.json",
                      "r170/certs/extree_ladder_h_170.txt.gz"),
                     ("r170/certs/verification_a_a2_170.json",
                      "r170/certs/extree_ladder_a2_170.txt.gz"),
                     ("r170/certs/verification_a_targeth_170.json",
                      "r170/certs/extree_target_h_170.txt.gz"),
                     ("r170/certs/verification_a_targeta2_170.json",
                      "r170/certs/extree_target_a2_170.txt.gz")):
        p = ROOT / rep
        if not p.exists():
            continue
        for r in json.loads(p.read_text())["per_cell"][key]:
            cost[tuple(int(x) for x in r["cell"].split("|"))] = r["nodes"]

    # measured throughput, from this round's generation reports
    rates = []
    for rel, secs in (("r170/certs/generation_ladder_h_170.json", 2777.1),
                      ("r170/certs/generation_ladder_a2_170.json", 1769.3)):
        g = json.loads((ROOT / rel).read_text())
        rates.append(dict(batch=rel, search_nodes=g["total_search_nodes"],
                          seconds=secs,
                          search_nodes_per_second=round(
                              g["total_search_nodes"] / secs)))
    rate_lo = min(r["search_nodes_per_second"] for r in rates)
    rate_hi = max(r["search_nodes_per_second"] for r in rates)

    # the measured subgraph: cells r170 actually produced
    produced = sorted(set(batch_own["r170/certs/extree_ladder_h_170.txt.gz"])
                      | set(batch_own["r170/certs/extree_ladder_a2_170.txt.gz"])
                      | set(batch_own["r170/certs/extree_target_h_170.txt.gz"])
                      | set(batch_own["r170/certs/extree_target_a2_170.txt.gz"]),
                      key=cellstr)
    pre_r170 = set()
    for rel in BATCHES[:4]:
        pre_r170 |= set(batch_own[rel])

    # edges inside the measured subgraph only; anything in a pre-r170 batch is
    # already available at time zero
    preds = {}
    for K in produced:
        rel = owner[K]
        _o, deps, _r = scan(rel)
        # a rung depends on nothing r170 made; a target depends on its rungs
        preds[K] = sorted((d for d in deps if d in set(produced)), key=cellstr)

    # list scheduling with w workers, longest job first among the ready set
    def schedule(w):
        remaining = {K: cost.get(K, 0) for K in produced}
        done, t, busy = set(), 0.0, []      # busy: (finish_time, cell)
        order = []
        free = w
        while len(done) < len(produced):
            ready = [K for K in produced
                     if K not in done and all(p in done for p in preds[K])
                     and not any(K == c for _f, c in busy)]
            ready.sort(key=lambda K: -remaining[K])
            while free > 0 and ready:
                K = ready.pop(0)
                dur = remaining[K] / rate_lo
                busy.append((t + dur, K))
                order.append(dict(cell=cellstr(K), start=round(t, 1),
                                  finish=round(t + dur, 1)))
                free -= 1
            if not busy:
                break
            busy.sort()
            t, K = busy.pop(0)
            done.add(K)
            free += 1
        return round(t, 1), order

    times = {}
    for w in (1, 2, 4, 8):
        secs, _order = schedule(w)
        times[w] = dict(seconds=secs, hours=round(secs / 3600, 2))
        print(f"  {w} worker(s): {secs:,.0f}s  ({secs / 3600:.2f} h)",
              flush=True)

    # critical path: longest chain by cost
    memo = {}

    def cp(K):
        if K in memo:
            return memo[K]
        best = max((cp(p) for p in preds[K]), default=(0, []))
        memo[K] = (best[0] + cost.get(K, 0), best[1] + [cellstr(K)])
        return memo[K]

    cpath = max((cp(K) for K in produced), default=(0, []))
    width = max(len([K for K in produced if not preds[K]]), 1)
    layers = defaultdict(list)

    def depth(K):
        return 0 if not preds[K] else 1 + max(depth(p) for p in preds[K])
    for K in produced:
        layers[depth(K)].append(cellstr(K))

    basis = json.loads((ROOT / "r170" / "certs"
                        / "reclass_170.json").read_text())
    out = dict(
        dag=dict(
            certificates=len(BATCHES),
            cells_total=len(owner),
            cells_produced_by_round_170=len(produced),
            cells_available_before_round_170=len(pre_r170),
            reference_edges={rel: batch_refs[rel] for rel in BATCHES},
            note="edges are read from declared EXTREE dependencies, not "
                 "inferred from cell coordinates"),
        measured_throughput=dict(
            runs=rates, search_nodes_per_second_range=[rate_lo, rate_hi],
            used_for_schedule=rate_lo,
            why_the_slower_rate="the two runs came out within about 2 "
                                "percent of each other, so the choice barely "
                                "matters here; the slower one is used so the "
                                "estimate is not the optimistic end of even "
                                "that narrow spread"),
        critical_path=dict(
            proof_nodes=cpath[0], cells=cpath[1],
            seconds_at_measured_rate=round(cpath[0] / rate_lo, 1),
            hours=round(cpath[0] / rate_lo / 3600, 2)),
        parallel_width=dict(
            independent_roots=width,
            layers={str(k): v for k, v in sorted(layers.items())}),
        idealised_schedule=times,
        idealisation_caveats=[
            "perfect packing, no CPU contention, no memory pressure",
            "reference loading excluded: it was about 12 minutes for the H "
            "ladder before the trust table was extended, and is real cost",
            "verification excluded: verifier A and B each replay every proof "
            "node, so dual verification roughly triples the node budget",
        ],
        unmeasured_remainder=dict(
            basis_cells_still_to_certify=len(
                basis["basis_cells_still_to_certify"]),
            cells=basis["basis_cells_still_to_certify"],
            time_attached=None,
            why="no table-free cost at a safe bound has been measured for "
                "these, and the two that were measured differ by four orders "
                "of magnitude, so any schedule over them would be fiction"),
        ok=True,
    )
    (ROOT / "r170" / "certs" / "schedule_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("dag", "parallel_width")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
