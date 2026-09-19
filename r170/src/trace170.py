#!/usr/bin/env python3
"""Round 170 -- the structural account of the mid-depth ladder effect.

Counting how often a rung supplies the (p) minimum explained nothing: all
twelve H rungs won at least once, yet leave-one-out showed six of them idle.
The gap is that winning the argmin is not the same as causing a prune.  The
build prunes when

    ports + ub(state) - 1  <  target

and `ub` is the minimum over certified dominators, falling back to
UBFALL + a + bb + e.  If the FALLBACK alone already satisfies that
inequality, the node dies whether or not a rung was the argmin, and the rung
bought nothing there.  So a rung's real contribution is the count of nodes
where it won AND the prune fired AND the fallback would not have pruned.

This module records exactly that, per rung, together with the geometry the
effect is supposed to come from: the recursion depth, the state coordinates,
and the value

    d* = dmax - deficit + 4 + 5*tok

at which (p) is evaluated -- the quantity that SHRINKS as the deficit grows
and therefore sends deep states to small-d cells that a root-level dominator
search never examines.

The engine's `build` is reimplemented here rather than hooked, because the
prune test needs `ports`, which the `ub` call does not see.  Duplicated logic
can drift from production, so the instrumented run asserts it reproduces the
genuine certificate's proof-node count exactly; a mismatch invalidates the
trace and is reported as such instead of being explained away.
"""
from __future__ import annotations
import json, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import gen168 as G                                                # noqa: E402
import routeb164 as R                                            # noqa: E402


def parse(s):
    return tuple(int(x) for x in s.split("|"))


class Tracer(G.Engine):
    def __init__(self, certified, node_cap, watch):
        super().__init__(certified, node_cap)
        self.watch = set(watch)
        self.win = Counter()             # rung was the argmin
        self.useful = Counter()          # ... and only it caused the prune
        self.redundant = Counter()       # ... but fallback would prune anyway
        self.nonprune = Counter()        # ... and no prune happened
        self.depths = defaultdict(list)
        self.dstars = defaultdict(list)
        self.examples = defaultdict(list)
        self.p_prunes = 0
        self.fallback_prunes = 0

    def _argmin(self, key):
        tok, d, a, bb, e, h = key
        fb = R.UBFALL + a + bb + e
        best, who = fb, None
        for K, c in self.cert.items():
            if c < best and all(k >= v for k, v in zip(K, key)):
                best, who = c, K
        return best, who, fb

    def traced_build(self, cell, cap):
        b, dmax, amax, bmax, emax, hmax = cell
        f = self._frame(cell)
        phm, hexc = f["phm"], f["hexc"]
        toks = []
        target = cap + 1
        ubc = {}

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit, depth):
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                raise TimeoutError
            if ports >= target and deficit <= dmax:
                raise StopIteration
            r1 = ports + (R.NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                + (emax - eu)
            if r1 < target:
                toks.append("L")
                return
            if not R.feas_greedy(phm, corb, tok, dmax):
                toks.append("L")
                return
            dstar = dmax - deficit + 4 + 5 * tok
            key = (tok, dstar, amax - au, bmax - bu, emax - eu, hmax - hu)
            hit = ubc.get(key)
            if hit is None:
                hit = self._argmin(key)
                ubc[key] = hit
            val, who, fb = hit
            r2 = ports + val - 1
            pruned = r2 < target
            fb_would = (ports + fb - 1) < target
            if pruned:
                self.p_prunes += 1
                if fb_would:
                    self.fallback_prunes += 1
            if who is not None and who in self.watch:
                self.win[who] += 1
                if not pruned:
                    self.nonprune[who] += 1
                elif fb_would:
                    self.redundant[who] += 1
                else:
                    self.useful[who] += 1
                    self.depths[who].append(depth)
                    self.dstars[who].append(dstar)
                    if len(self.examples[who]) < 3:
                        self.examples[who].append(dict(
                            depth=depth, state=list(key), d_star=dstar,
                            ports=ports, deficit=deficit,
                            supplied_bound=val, analytic_fallback=fb,
                            margin_to_target=target - r2))
            if pruned:
                toks.append("L")
                return
            ms = self._legal(phm, hexc, cell, v, corb, tok, au, bu, eu, hu)
            toks.append(f"N{len(ms)}")
            for t, kind, cost, fresh, se, c in ms:
                q = R.ORB[t]
                if fresh:
                    phm[q] = {R.PHASE[t]}
                else:
                    phm[q].add(R.PHASE[t])
                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1
                rec(t, q, ports + 1, tok - c, au + (kind == "A"),
                    bu + (kind == "B"), eu + se,
                    hu + (cost if kind == "H" else 0),
                    deficit + (4 if fresh else -1), depth + 1)
                hexc[R.HEX[t]] -= 1
                if hexc[R.HEX[t]] == 0:
                    del hexc[R.HEX[t]]
                if fresh:
                    del phm[q]
                else:
                    phm[q].discard(R.PHASE[t])
        try:
            rec(0, R.ORB[0], 1, b, 0, 0, 0, 0, 4, 0)
        except StopIteration:
            return None, "a walk reached the target: cap is not an upper bound"
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached"
        return toks, None


def main():
    import argparse
    import verify168
    verify168.load_trust()

    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--safe", type=int, required=True)
    ap.add_argument("--rungs", required=True)
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--expect-proof", type=int, required=True,
                    help="the genuine certificate's proof-node count")
    ap.add_argument("--report", required=True)
    ap.add_argument("--node-cap", type=int, default=200_000_000)
    a = ap.parse_args()

    T = parse(a.cell)
    ladder = [parse(x) for x in
              Path(a.rungs[1:]).read_text().split() if x.strip()]
    _refs, dep_map = G.load_refs(a.ref, verify168.verify_any)
    cert = {cell: c for cell, (c, _p, _r) in dep_map.items()}
    print(f"{len(cert)} certified cells; tracing {G.cellstr(T)} at S={a.safe}",
          flush=True)

    t0 = time.time()
    g = Tracer(cert, a.node_cap, ladder)
    toks, err = g.traced_build(T, a.safe)
    proof = len(toks) if toks else 0
    del toks
    faithful = proof == a.expect_proof
    print(f"instrumented build: proof={proof:,} "
          f"expected={a.expect_proof:,} faithful={faithful} "
          f"{round(time.time() - t0, 1)}s", flush=True)
    if err:
        print(f"  {err}", flush=True)

    per = []
    for K in ladder:
        per.append(dict(
            rung=G.cellstr(K), cap=cert.get(K),
            p_argmin_wins=g.win[K],
            useful_prunes=g.useful[K],
            redundant_prunes=g.redundant[K],
            wins_without_prune=g.nonprune[K],
            depth_range=([min(g.depths[K]), max(g.depths[K])]
                         if g.depths[K] else None),
            d_star_range=([min(g.dstars[K]), max(g.dstars[K])]
                          if g.dstars[K] else None),
            examples=g.examples[K]))
    for r in per:
        print(f"  {r['rung']:>16} wins={r['p_argmin_wins']:>6} "
              f"useful={r['useful_prunes']:>6} "
              f"redundant={r['redundant_prunes']:>6} "
              f"d*={r['d_star_range']}", flush=True)

    out = dict(
        cell=G.cellstr(T), census_safe_bound_S=a.safe,
        instrumented_proof_nodes=proof,
        genuine_proof_nodes=a.expect_proof,
        trace_is_faithful=faithful,
        faithfulness_note="the instrumented build reimplements the engine's "
                          "recursion so the prune test can see `ports`; if it "
                          "does not reproduce the genuine proof-node count "
                          "exactly the trace describes a different search and "
                          "is void",
        total_p_prunes=g.p_prunes,
        prunes_the_fallback_would_also_make=g.fallback_prunes,
        per_rung=per,
        rung_to_useful_prunes={r["rung"]: r["useful_prunes"] for r in per},
        rungs_with_zero_useful_prunes=[r["rung"] for r in per
                                       if not r["useful_prunes"]],
        reading="a rung matters only where it won the (p) argmin AND the "
                "prune fired AND the analytic fallback would not have pruned; "
                "argmin wins alone overcount, which is why six H rungs won "
                "yet proved removable",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = faithful
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("per_rung",)},
                     ensure_ascii=False, indent=1))
    return 0 if faithful else 1


if __name__ == "__main__":
    sys.exit(main())
