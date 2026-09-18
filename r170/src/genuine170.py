#!/usr/bin/env python3
"""Round 170 -- genuine safe-target builds on top of a VERIFIED ladder.

The two-factor claim has two halves and this module tests both at once.

FACTOR 1, the census-safe target.  `r170/src/safe170.py` derives S(T) by
binary search over the (P1)-closed census: the largest value that leaves
every exposed row strictly closed.  S is a property of the ROW SYSTEM, so it
is known before any search runs.  That lets the build skip discovery -- the
stage that exhausted the 20 million node cap on both targets -- and prove
cap(T) <= S directly.

FACTOR 2, the mid-depth ladder.  (p) is evaluated at d* = dmax - deficit + 4
+ 5*tok, which SHRINKS as the deficit grows, so deep states are dominated by
small-d cells that a root-level dominator search never looks at.  The ladder
supplies exactly those cells.

Unlike `ladder170.py`, nothing here is counterfactual.  Every dependency
comes from a certificate that verifiers A and B have both accepted, loaded
through gen168's own `load_refs`, and the result is a real L6-EXTREE-3
certificate that can itself be verified.  The counterfactual prediction is
carried alongside only so the two can be compared.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r168" / "src"))
import gen168 as G                                                # noqa: E402


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def main():
    import verify168
    verify168.load_trust()

    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--safe", type=int, required=True,
                    help="census-safe bound S; the build proves cap <= S")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--node-cap", type=int, default=200_000_000)
    ap.add_argument("--predicted", type=int, default=0,
                    help="counterfactual proof-node prediction, for comparison")
    a = ap.parse_args()

    T = parse(a.cell)
    refs, dep_map = G.load_refs(a.ref, verify168.verify_any)
    deps = [(cell, c, psha, rel) for cell, (c, psha, rel)
            in sorted(dep_map.items())]
    certified = {cell: c for cell, (c, _p, _r) in dep_map.items()}
    print(f"dependencies loaded: {len(certified)} certified cells "
          f"from {len(refs)} verified certificates", flush=True)

    t0 = time.time()
    g = G.Engine(certified, a.node_cap)
    toks, err = g.build(T, a.safe)
    secs = round(time.time() - t0, 1)
    status = "TREE_BUILT" if toks else (
        "DEFERRED_NODE_CAP" if "node cap" in (err or "") else "BUILD_FAILED")
    proof = len(toks) if toks else 0
    print(f"  {G.cellstr(T):>16} S={a.safe} target={a.safe + 1} "
          f"{status} search={g.nodes:,} proof={proof:,} {secs}s", flush=True)
    if err:
        print(f"  detail: {err}", flush=True)

    trees = [(T, a.safe, " ".join(toks))] if toks else []
    text = G.write_batch(ROOT / a.out, refs, deps, trees) if trees else None

    rep = dict(
        format=G.MAGIC,
        cell=G.cellstr(T),
        census_safe_bound_S=a.safe,
        target=a.safe + 1,
        discovery="SKIPPED -- S comes from the row system, not from search",
        refs=[dict(container_sha256=c, plain_sha256=p, path=r)
              for c, p, r in refs],
        declared_dependencies=len(deps),
        status=status,
        search_nodes=g.nodes,
        proof_nodes=proof,
        seconds_noncanonical=secs,
        detail=err,
    )
    if a.predicted:
        rep["counterfactual_prediction"] = a.predicted
        if proof:
            rep["genuine_over_predicted"] = round(proof / a.predicted, 4)
            rep["percent_error"] = round(
                100.0 * (proof - a.predicted) / a.predicted, 2)
    if text is not None:
        from gzrule167 import plain_sha256
        import hashlib
        p = ROOT / a.out
        rep.update(stored=a.out, stored_bytes=p.stat().st_size,
                   stored_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                   plain_sha256=plain_sha256(p), plain_bytes=len(text))
    rep["ok"] = bool(toks)
    (ROOT / a.report).write_text(json.dumps(rep, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "refs"},
                     ensure_ascii=False, indent=1))
    return 0 if toks else 1


if __name__ == "__main__":
    sys.exit(main())
