#!/usr/bin/env python3
"""Round 165 phases 8, 9, 16 -- cost of the basis, shared prerequisite
structure, and failure sensitivity.

PHASE 9 matters most.  An exhaustion tree's (p) leaves cite cells certified
EARLIER IN THE SAME FILE, so the cost of certifying a set is not the sum of
its cells' search node counts: a cell may need prerequisites, and
prerequisites are shared.  This module measures the real citation structure by
re-validating the round-164 tree while recording WHICH earlier cell supplies
the monotone bound at each (p) leaf.
"""
from __future__ import annotations
import gzip, hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
import hidden163 as H                                             # noqa: E402
import routeb164 as R                                             # noqa: E402
import closure165 as CL                                           # noqa: E402

CERTS = ROOT / "r152" / "certs"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


class CitingVerifier(R.TreeVerifier):
    """Same validator, but it records which cell each (p) leaf leans on."""

    def __init__(self, certified):
        super().__init__(certified, check_feas_forms=False)
        self.citations = Counter()

    def ub_with_source(self, tok, d, a, bb, e, h):
        best, src = R.UBFALL + a + bb + e, None
        for (kb, kd, ka, kbb, ke, kh), c in self.cert.items():
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best, src = c, (kb, kd, ka, kbb, ke, kh)
        return best, src

    def ub(self, tok, d, a, bb, e, h):
        best, src = self.ub_with_source(tok, d, a, bb, e, h)
        if src is not None:
            self.citations[src] += 1
        return best


def prerequisite_structure():
    """Which earlier cells does each tree actually cite?"""
    gz = ROOT / "r164" / "certs" / "extree_prefix_164.txt.gz"
    text = gzip.open(gz, "rt").read()
    tmp = ROOT / "r165" / "certs" / ".tree.tmp"
    tmp.write_text(text)
    trees = R.parse_extree(tmp)
    tmp.unlink()
    certified, rows = {}, []
    for cell, capv, toks in trees:
        v = CitingVerifier(dict(certified))
        ok, info = v.validate(cell, capv, toks)
        cites = sorted(("|".join(map(str, k)), n)
                       for k, n in v.citations.items())
        rows.append(dict(cell="|".join(map(str, cell)), cap=capv,
                         valid=bool(ok), nodes=v.nodes,
                         distinct_cells_cited=len(cites),
                         citations=cites[:12],
                         total_citations=sum(n for _, n in cites)))
        if ok:
            certified[cell] = capv
    # transitive prerequisite closure inside this file
    idx = {r["cell"]: i for i, r in enumerate(rows)}
    direct = {r["cell"]: {c for c, _ in r["citations"]} for r in rows}
    closure = {}
    for r in rows:
        seen, stack = set(), list(direct[r["cell"]])
        while stack:
            x = stack.pop()
            if x in seen or x not in direct:
                continue
            seen.add(x)
            stack.extend(direct[x])
        closure[r["cell"]] = sorted(seen)
    return rows, closure, idx


def main():
    H.load()
    CERT0, PCERT0 = dict(H.CERT), dict(H.PCERT)
    graph = json.loads((ROOT / "r165" / "certs"
                        / "row_closure_graph_165.json").read_text())
    ess = sorted(graph["essential_cells"])
    ess_chain = [c for c in ess if graph["ablation"][c]["model"] == "chain"]
    ess_piece = [c for c in ess if graph["ablation"][c]["model"] == "piece"]

    # ---------- phase 8: cost from the round-152 search node counts
    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    pC = json.loads((CERTS / "verify_piece_c152.json").read_text())
    cnodes = {r["cell"]: r.get("nodes", 0) for r in vC["rows"]}
    pnodes = {f"{r['b']}|{r['d']}|{r['fp']}|{r['lp']}": r.get("nodes", 0)
              for r in pC["rows"]}
    cost = {}
    for c in ess_chain:
        cost[c] = cnodes.get(c, 0)
    for c in ess_piece:
        cost[c] = pnodes.get(c, 0)
    total_cost = sum(cost.values())
    # for comparison: the cost of all 355
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    vg = json.loads((ROOT / "r164" / "certs"
                     / "verifygen_164.json").read_text())
    done = {"|".join(map(str, c)) for c in
            [tuple(int(x) for x in s.split("|"))
             for s in vg["targets_upper_certified_by_two_validators"]]}
    all355 = ([("|".join(map(str, c))) for c in tg["CHAIN_SINGLE_IMPL"]]
              + ["|".join(map(str, c)) for c in tg["PIECE_SINGLE_IMPL"]])
    all355 = [c for c in all355 if c not in done]
    cost355 = sum(cnodes.get(c, pnodes.get(c, 0)) for c in all355)

    # a minimum-COST basis: essentials are forced, so the only freedom is
    # whether any redundant cell could replace an essential one -- it cannot,
    # because essentials lie in EVERY sufficient basis.  The minimum-cost
    # basis is therefore the same set.
    order = sorted(cost.items(), key=lambda kv: -kv[1])

    # ---------- phase 9: prerequisite structure
    pre_rows, closure, idx = prerequisite_structure()
    cited = Counter()
    for r in pre_rows:
        for c, n in r["citations"]:
            cited[c] += 1
    shared = sorted(cited.items(), key=lambda kv: -kv[1])[:10]

    # ---------- phase 16: failure sensitivity.
    # "+1" turns out to open nothing anywhere, so the informative quantity is
    # the SMALLEST error that does damage.  Removal replaces the value by the
    # analytic fallback, so the margin is searched in [1, fallback - cap];
    # bounds are monotone in the value, so binary search is exact.
    groups = CL.grouped()
    base = CL.evaluate(groups)
    ex = {k for k in base if base[k]["verdict"] == "STRICTLY_CLOSED"}
    exposed = {tuple([lay] + [tuple(r)]) for lay, r in []}
    # only rows that the FULL withdrawal opens can be opened by a smaller
    # error, so restrict to those (monotonicity, checked in phase 2)
    CL.withdraw([tuple(int(x) for x in c.split("|")) for c in ess_chain],
                [tuple(int(x) for x in c.split("|")) for c in ess_piece])
    wres = CL.evaluate(groups, ex)
    CL.restore(CERT0, PCERT0)
    ex = {k for k in ex if wres[k]["verdict"] != "STRICTLY_CLOSED"}

    def opens(model, k, val):
        tbl = H.CERT if model == "chain" else H.PCERT
        old = tbl[k]
        tbl[k] = val
        H.best.cache_clear()
        r = CL.evaluate(groups, ex)
        tbl[k] = old
        H.best.cache_clear()
        return sum(1 for kk in ex if r[kk]["verdict"] != "STRICTLY_CLOSED")

    sens = {}
    for c in ess:
        model = graph["ablation"][c]["model"]
        k = tuple(int(x) for x in c.split("|"))
        cap0 = (H.CERT if model == "chain" else H.PCERT)[k]
        top = (R.UBFALL + k[2] + k[3] + k[4]) if model == "chain" else R.UBFALL
        hi = max(top - cap0, 1)
        if opens(model, k, cap0 + hi) == 0:
            sens[c] = dict(model=model, cap=cap0, plus_one_opens=0,
                           smallest_damaging_error=None,
                           note="even the analytic fallback opens nothing "
                                "through this cell alone")
            continue
        lo, best = 1, hi
        while lo <= hi:
            mid = (lo + hi) // 2
            if opens(model, k, cap0 + mid):
                best, hi = mid, mid - 1
            else:
                lo = mid + 1
        sens[c] = dict(model=model, cap=cap0,
                       plus_one_opens=1 if best == 1 else 0,
                       smallest_damaging_error=best,
                       relative_margin=round(best / cap0, 3),
                       rows_opened_at_that_error=opens(model, k, cap0 + best))
    srt = sorted((v for v in sens.values()
                  if v["smallest_damaging_error"] is not None),
                 key=lambda v: v["smallest_damaging_error"])
    worst = [dict(cell=c, **v) for c, v in sorted(
        sens.items(),
        key=lambda kv: (kv[1]["smallest_damaging_error"] is None,
                        kv[1]["smallest_damaging_error"] or 10 ** 9))][:8]

    out = dict(
        inputs={p: sha(p) for p in
                ("r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json",
                 "r164/certs/extree_prefix_164.txt.gz",
                 "r165/certs/row_closure_graph_165.json")},
        basis=dict(size=len(ess), chain=len(ess_chain), piece=len(ess_piece)),
        minimum_cardinality_basis=len(ess),
        minimum_cost_basis=dict(
            size=len(ess), same_set_as_minimum_cardinality=True,
            reason="every individually essential cell is in EVERY sufficient "
                   "basis, so there is no cheaper alternative set to choose"),
        cost=dict(
            route_a_nodes_for_the_basis=total_cost,
            route_a_nodes_for_all_355=cost355,
            saving=cost355 - total_cost,
            most_expensive_basis_cells=[dict(cell=c, nodes=n)
                                        for c, n in order[:8]],
            cheapest_basis_cells=[dict(cell=c, nodes=n)
                                  for c, n in order[-5:]],
            median_nodes=sorted(cost.values())[len(cost) // 2]),
        prerequisite_structure=dict(
            file="r164/certs/extree_prefix_164.txt.gz",
            trees=len(pre_rows),
            all_valid=all(r["valid"] for r in pre_rows),
            trees_citing_nothing=sum(1 for r in pre_rows
                                     if r["distinct_cells_cited"] == 0),
            max_distinct_cells_cited=max(r["distinct_cells_cited"]
                                         for r in pre_rows),
            most_cited_cells=[dict(cell=c, cited_by_trees=n)
                              for c, n in shared],
            transitive_closure_sizes={r["cell"]: len(closure[r["cell"]])
                                      for r in pre_rows},
            reading="a tree's (p) leaves may only cite cells proved earlier "
                    "in the same file, so certifying a set costs its "
                    "prerequisite closure, not just the set"),
        failure_sensitivity=dict(
            tested="smallest upward error in the claimed upper bound that "
                   "reopens at least one census row, found by binary search "
                   "(bounds are monotone in the value)",
            cells=len(sens),
            cells_where_plus_one_opens_a_row=sum(
                1 for v in sens.values() if v["plus_one_opens"]),
            cells_no_error_up_to_the_analytic_bound_can_break=sum(
                1 for v in sens.values()
                if v["smallest_damaging_error"] is None),
            smallest_damaging_error_min=(srt[0]["smallest_damaging_error"]
                                         if srt else None),
            smallest_damaging_error_median=(
                srt[len(srt) // 2]["smallest_damaging_error"] if srt else None),
            most_fragile_cells=worst,
            reading="a single-route capacity value would have to be wrong by "
                    "this much BEFORE any census row reopens; +1 opens "
                    "nothing anywhere"),
        per_cell_cost=cost,
        per_cell_sensitivity=sens,
    )
    out["ok"] = (out["prerequisite_structure"]["all_valid"]
                 and out["basis"]["size"] == 288)
    (ROOT / "r165" / "certs" / "weighted_basis_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "per_cell_cost",
                                   "per_cell_sensitivity",
                                   "prerequisite_structure")},
                     ensure_ascii=False, indent=1))
    ps = out["prerequisite_structure"]
    print(json.dumps({k: v for k, v in ps.items()
                      if k != "transitive_closure_sizes"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
