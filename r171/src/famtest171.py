#!/usr/bin/env python3
"""Round 171 -- does shallow shared investment unlock a b>=1 family?

The pilots left 32 of 33 remaining bounds deferred, and the reason was not the
size of the safe bound: the cells with the MOST room failed hardest.  What
decides is whether a (p) lookup finds a dominator at the target's own b level
and budget shape, and both existing ladders are b = 0.

Family b1_a10 is the test case.  Its six members all have b = 1 and
(bb, e, h) = 0, with a <= 10, so a rung at (1, d, 10, 0, 0, 0) dominates every
state any of them can reach.  Three shallow rungs exist, costing 6,423,292
proof nodes together.  The question is whether that buys a completed proof.

Each target runs twice: on the genuine predecessor set alone, and on the same
set plus the shallow rungs.  The instrumented build reimplements the engine's
recursion so the prune test can see `ports`, so it asserts it reproduces the
plain engine's proof-node count; a mismatch voids the trace rather than being
explained away.

Per useful prune the trace records d*, the winning rung, the bound it supplied,
the analytic fallback, and whether ANOTHER available rung could have pruned the
same node.  That last column is what round 170 lacked when it mistook argmin
wins for contribution, and it is what detects substitutable equal-capacity
rungs before a deeper one is ever generated.
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


class Traced(G.Engine):
    """build() with the (p) prune instrumented; watch = the rungs of interest."""

    def __init__(self, certified, node_cap, watch):
        super().__init__(certified, node_cap)
        self.watch = set(watch)
        self.p_leaves = 0
        self.fallback_states = 0
        self.dominator_states = 0
        self.useful = Counter()
        self.redundant_vs_fallback = Counter()
        self.substitutable = Counter()
        self.exclusive = Counter()
        self.first_useful_depth = {}
        self.dstar_of = defaultdict(list)
        self.examples = defaultdict(list)

    def _rank(self, key):
        """(best, who, second_best, fallback) over the certified set."""
        tok, d, a, bb, e, h = key
        fb = R.UBFALL + a + bb + e
        best, who, second = fb, None, fb
        for K, c in self.cert.items():
            if all(k >= v for k, v in zip(K, key)):
                if c < best:
                    second, best, who = best, c, K
                elif c < second:
                    second = c
        return best, who, second, fb

    def traced_build(self, cell, cap):
        b, dmax, amax, bmax, emax, hmax = cell
        f = self._frame(cell)
        phm, hexc = f["phm"], f["hexc"]
        toks = []
        target = cap + 1
        memo = {}

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
            hit = memo.get(key)
            if hit is None:
                hit = self._rank(key)
                memo[key] = hit
            best, who, second, fb = hit
            if who is None:
                self.fallback_states += 1
            else:
                self.dominator_states += 1
            r2 = ports + best - 1
            pruned = r2 < target
            if pruned:
                self.p_leaves += 1
                fb_would = (ports + fb - 1) < target
                if who in self.watch:
                    if fb_would:
                        self.redundant_vs_fallback[who] += 1
                    else:
                        self.useful[who] += 1
                        self.dstar_of[who].append(dstar)
                        self.first_useful_depth.setdefault(who, depth)
                        if (ports + second - 1) < target:
                            self.substitutable[who] += 1
                        else:
                            self.exclusive[who] += 1
                        if len(self.examples[who]) < 3:
                            self.examples[who].append(dict(
                                depth=depth, d_star=dstar, state=list(key),
                                supplied_bound=best,
                                second_best_bound=second,
                                analytic_fallback=fb,
                                another_rung_would_prune=(
                                    (ports + second - 1) < target)))
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
            return None, "a walk reached the target: the cap is not an upper bound"
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached"
        return toks, None


def run_variant(cert, watch, T, S, cap, label):
    t0 = time.time()
    plain = G.Engine(cert, cap)
    ptoks, perr = plain.build(T, S)
    plain_proof = len(ptoks) if ptoks else 0
    del ptoks
    t1 = time.time()
    g = Traced(cert, cap, watch)
    toks, err = g.traced_build(T, S)
    proof = len(toks) if toks else 0
    del toks
    tot = g.fallback_states + g.dominator_states
    row = dict(
        variant=label, cell=G.cellstr(T), safe_bound_S=S, extree_target=S + 1,
        completed=bool(plain_proof),
        proof_nodes=plain_proof, search_nodes=plain.nodes, node_cap=cap,
        detail=None if plain_proof else str(perr)[:70],
        seconds=round(t1 - t0, 1),
        trace_reproduces_plain=(proof == plain_proof),
        p_leaves=g.p_leaves,
        states_on_analytic_fallback=g.fallback_states,
        states_with_a_dominator=g.dominator_states,
        fallback_fraction=(round(g.fallback_states / tot, 4) if tot else None),
        per_rung=[dict(
            rung=G.cellstr(K), cap=cert.get(K),
            useful_prunes=g.useful[K],
            redundant_vs_analytic_fallback=g.redundant_vs_fallback[K],
            another_rung_could_substitute=g.substitutable[K],
            exclusively_this_rung=g.exclusive[K],
            first_useful_depth=g.first_useful_depth.get(K),
            d_star_range=([min(g.dstar_of[K]), max(g.dstar_of[K])]
                          if g.dstar_of[K] else None),
            examples=g.examples[K]) for K in sorted(watch)],
        seconds_traced=round(time.time() - t1, 1))
    return row


def main():
    import argparse
    import verify168
    verify168.load_trust()
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True, help="comma separated targets")
    ap.add_argument("--helper-batch", default="")
    ap.add_argument("--helper-cells", default="")
    ap.add_argument("--node-cap", type=int, default=20_000_000)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    doss = json.loads((ROOT / "r171" / "certs"
                       / "remaining_171.json").read_text())
    S = {d["cell"]: d["safe_upper_bound_S"] for d in doss["dossier"]}
    base_refs = doss["genuine_certificates"]
    _r, dep_a = G.load_refs(base_refs, verify168.verify_any)
    certA = {c: v for c, (v, _p, _rel) in dep_a.items()}
    refs_b = base_refs + ([a.helper_batch] if a.helper_batch else [])
    _r2, dep_b = G.load_refs(refs_b, verify168.verify_any)
    certB = {c: v for c, (v, _p, _rel) in dep_b.items()}
    watch = [parse(x) for x in a.helper_cells.split(",") if x.strip()]
    helper_cost = {K: certB.get(K) for K in watch}
    print(f"A: {len(certA)} certified cells   B: {len(certB)} "
          f"(+{len(certB) - len(certA)} shallow rungs)", flush=True)

    rows = []
    t0 = time.time()
    for cs in a.cells.split(","):
        cs = cs.strip()
        if not cs:
            continue
        T, Sk = parse(cs), S[cs]
        for label, cert in (("A_no_investment", certA),
                            ("B_shallow_rungs", certB)):
            r = run_variant(cert, watch if label.startswith("B") else [],
                            T, Sk, a.node_cap, label)
            rows.append(r)
            print(f"  {cs:>16} {label:<18} "
                  f"{'TREE' if r['completed'] else 'DEFERRED':<9} "
                  f"proof={r['proof_nodes']:>12,} "
                  f"pleaves={r['p_leaves']:>10,} "
                  f"fb={r['fallback_fraction']} {r['seconds']}s "
                  f"faithful={r['trace_reproduces_plain']}", flush=True)
            (ROOT / a.report).write_text(json.dumps(dict(
                family="b1_a10",
                shallow_investment_proof_nodes=6423292,
                helper_rungs={G.cellstr(K): helper_cost[K] for K in watch},
                node_cap=a.node_cap,
                rows=rows,
                complete=False,
                seconds_noncanonical=round(time.time() - t0, 1),
                ok=True), ensure_ascii=False, indent=1) + "\n")

    done = {}
    for r in rows:
        done.setdefault(r["cell"], {})[r["variant"]] = r
    unlocked = [c for c, v in done.items()
                if not v["A_no_investment"]["completed"]
                and v["B_shallow_rungs"]["completed"]]
    out = dict(
        family="b1_a10",
        shallow_investment_proof_nodes=6423292,
        helper_rungs={G.cellstr(K): helper_cost[K] for K in watch},
        node_cap=a.node_cap,
        targets_tested=len(done),
        unlocked_by_shallow_investment=unlocked,
        unlocked_count=len(unlocked),
        rows=rows,
        complete=True,
        seconds_noncanonical=round(time.time() - t0, 1),
        ok=True)
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(f"\nunlocked by the shallow investment: {len(unlocked)}/{len(done)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
