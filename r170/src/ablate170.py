#!/usr/bin/env python3
"""Round 170 -- which rungs of a VERIFIED ladder actually carry weight.

The full H ladder cost 34,937,114 proof nodes, four times what the target it
unlocks costs.  If only part of it is load-bearing the investment shrinks, so
the useful subset has to be identified -- but twelve leave-one-out builds at
roughly eight million nodes each is an hour of search to answer a question the
first build already contains the answer to.

A rung earns its place by supplying the (p) minimum at a state the search
actually visits.  So one INSTRUMENTED build counts, per rung, how often that
rung is the argmin of the upper-bound lookup, and any rung whose count is zero
cannot have affected the tree.  That candidate subset is then CONFIRMED by a
real build restricted to it: if the confirmation reproduces the same proof-node
count, the dropped rungs provably bought nothing.

Nothing here is counterfactual.  Every capacity used is one that verifiers A
and B both accepted, so a build restricted to a subset is a genuine
certificate that depends only on that subset.
"""
from __future__ import annotations
import json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import gen168 as G                                                # noqa: E402
import routeb164 as R                                            # noqa: E402


def parse(s):
    return tuple(int(x) for x in s.split("|"))


class Counted(G.Engine):
    """Engine that records which certified cell wins the (p) lookup."""

    def __init__(self, certified, node_cap, watch):
        super().__init__(certified, node_cap)
        self.watch = set(watch)
        self.winner = Counter()
        self.first_win = {}

    def ub(self, tok, d, a, bb, e, h):
        # the base engine memoises this lookup and the build's cost depends on
        # that, so the instrumentation counts DISTINCT states -- one tally per
        # cache miss -- rather than re-deriving the argmin on every hit.
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        best, who = R.UBFALL + a + bb + e, None
        for K, c in self.cert.items():
            if c < best and all(k >= v2 for k, v2 in zip(K, key)):
                best, who = c, K
        if who is not None and who in self.watch:
            self.winner[who] += 1
            self.first_win.setdefault(who, self.nodes)
        self._ubc[key] = best
        return best


def main():
    import argparse
    import verify168
    verify168.load_trust()

    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--safe", type=int, required=True)
    ap.add_argument("--rungs", required=True,
                    help="@<file> of the ladder cells to treat as ablatable")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--report", required=True)
    ap.add_argument("--node-cap", type=int, default=200_000_000)
    a = ap.parse_args()

    T = parse(a.cell)
    rungs = [parse(x) for x in
             Path(a.rungs[1:]).read_text().split() if x.strip()]
    _refs, dep_map = G.load_refs(a.ref, verify168.verify_any)
    certified = {cell: c for cell, (c, _p, _r) in dep_map.items()}
    present = [K for K in rungs if K in certified]
    print(f"{len(certified)} certified cells; {len(present)}/{len(rungs)} "
          f"ladder rungs present", flush=True)

    # ---- pass 1: instrumented build, full ladder
    t0 = time.time()
    g = Counted(certified, a.node_cap, present)
    toks, err = g.build(T, a.safe)
    full_proof = len(toks) if toks else 0
    print(f"full ladder: search={g.nodes:,} proof={full_proof:,} "
          f"{round(time.time() - t0, 1)}s", flush=True)
    if not toks:
        print(f"  build failed: {err}", flush=True)
        return 1
    del toks

    used = [K for K in present if g.winner[K]]
    idle = [K for K in present if not g.winner[K]]
    per_rung = [dict(rung=G.cellstr(K), cap=certified[K],
                     times_supplied_p_minimum=g.winner[K],
                     first_at_search_node=g.first_win.get(K))
                for K in present]
    for r in per_rung:
        print(f"  {r['rung']:>16} cap={r['cap']:<4} "
              f"wins={r['times_supplied_p_minimum']:>10,}", flush=True)

    # ---- pass 2: confirm on the used subset only
    conf = None
    if idle:
        sub = {K: c for K, c in certified.items()
               if K not in set(idle)}
        t1 = time.time()
        g2 = G.Engine(sub, a.node_cap)
        toks2, err2 = g2.build(T, a.safe)
        conf = dict(rungs_kept=len(used), rungs_dropped=len(idle),
                    search_nodes=g2.nodes,
                    proof_nodes=len(toks2) if toks2 else 0,
                    status="TREE_BUILT" if toks2 else "FAILED",
                    detail=err2,
                    reproduces_full_ladder_proof=(
                        bool(toks2) and len(toks2) == full_proof),
                    seconds_noncanonical=round(time.time() - t1, 1))
        print(f"confirmation without {len(idle)} idle rungs: "
              f"proof={conf['proof_nodes']:,} "
              f"same={conf['reproduces_full_ladder_proof']}", flush=True)
        del toks2

    invested = sum(1 for _ in present)
    out = dict(
        cell=G.cellstr(T), census_safe_bound_S=a.safe,
        ladder_rungs_offered=invested,
        full_ladder=dict(search_nodes=g.nodes, proof_nodes=full_proof),
        per_rung=per_rung,
        load_bearing_rungs=[G.cellstr(K) for K in used],
        idle_rungs=[G.cellstr(K) for K in idle],
        confirmation=conf,
        reading="a rung with zero (p) wins cannot have shaped the tree; the "
                "confirmation build restricted to the load-bearing rungs "
                "settles it by reproducing the proof-node count exactly",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = conf is None or bool(conf["reproduces_full_ladder_proof"])
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "per_rung"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
