#!/usr/bin/env python3
"""Round 169 phases 3, 4 and 13 -- measure cost as a function of the
certified set.

`cost(T | C)` is measured by running the round-168 generator against exactly
the certified set C and counting nodes, with a per-cell node cap.  A cap hit
is reported as a LOWER BOUND on the cost and the cell is DEFERRED; it is never
an UNSAT, never a refutation and never a certification.

COUNTERFACTUAL MODE.  To estimate what a not-yet-certified dominator K would
buy, a pilot may add K to C with the capacity the round-152 table records.
Every such run is flagged `counterfactual: true` and its result is scheduling
information only.  It produces no certificate and nothing it touches may enter
a proof object -- production generation (r168/src/gen168.py) still seeds its
predecessor table exclusively from verified certificates.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r168" / "src"))
sys.path.insert(0, str(ROOT / "r169" / "src"))
import gen168 as G                                                # noqa: E402
from state169 import certified_from_proof_objects, sha            # noqa: E402
from dominate169 import parse, cellstr, s_level, fallback         # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def universe():
    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    return ({parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD},
            {parse(r["cell"]): r["nodes"] for r in rows
             if r["status"] in GOOD})


def pilot(T, cert, node_cap, want_tree=True):
    t0 = time.time()
    g = G.Engine(cert, node_cap)
    cap, err = g.discover(T)
    row = dict(cell=cellstr(T), discovery_nodes=g.nodes)
    if cap is None:
        row.update(status="DEFERRED_NODE_CAP", stage="discover",
                   cost_lower_bound=g.nodes, detail=err,
                   seconds=round(time.time() - t0, 1))
        return row
    row["discovered_cap"] = cap
    if not want_tree:
        row.update(status="DISCOVERED_ONLY",
                   seconds=round(time.time() - t0, 1))
        return row
    g2 = G.Engine(cert, node_cap)
    toks, err = g2.build(T, cap)
    row["tree_nodes"] = g2.nodes
    row["search_nodes"] = g.nodes + g2.nodes
    if toks is None:
        row.update(status="DEFERRED_NODE_CAP", stage="build",
                   cost_lower_bound=g.nodes + g2.nodes, detail=err)
    else:
        row.update(status="MEASURED", proof_nodes=len(toks))
    row["seconds"] = round(time.time() - t0, 1)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", action="append", required=True,
                    help="TARGET[+EXTRA,EXTRA...]  EXTRA cells are added "
                         "counterfactually at their round-152 capacity")
    ap.add_argument("--node-cap", type=int, default=20_000_000)
    ap.add_argument("--discover-only", action="store_true")
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    CERT, _prov = certified_from_proof_objects()
    U, N = universe()
    rows = []
    for spec in a.experiment:
        head, _, tail = spec.partition("+")
        T = parse(head)
        extra = [parse(x) for x in tail.split(",") if x]
        cert = dict(CERT)
        for K in extra:
            if K not in U:
                raise SystemExit(f"{cellstr(K)} is not in the capacity table")
            cert[K] = U[K]
        r = pilot(T, cert, a.node_cap, not a.discover_only)
        r.update(counterfactual=bool(extra),
                 extra_certified=[cellstr(K) for K in extra],
                 extra_capacities={cellstr(K): U[K] for K in extra},
                 certified_set_size=len(cert),
                 round_152_nodes=N.get(T),
                 round_152_cap=U.get(T))
        if r.get("proof_nodes") and N.get(T):
            r["inflation_vs_round_152"] = round(r["proof_nodes"] / N[T], 3)
        rows.append(r)
        print(json.dumps({k: v for k, v in r.items()
                          if k not in ("extra_capacities",)},
                         ensure_ascii=False), flush=True)

    out = dict(
        inputs={p: sha(p) for p in ("r152/certs/verify_all_c152.json",
                                    "r168/src/gen168.py",
                                    "r169/certs/state_169.json")},
        node_cap=a.node_cap,
        policy=dict(
            cap="a cap hit is DEFERRED with a cost LOWER BOUND, never UNSAT, "
                "never a refutation, never a certification",
            counterfactual="runs marked counterfactual add a cell that is NOT "
                           "independently certified, at its round-152 "
                           "capacity, for scheduling estimates only; they "
                           "produce no certificate and touch no proof object"),
        pilots=rows)
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
