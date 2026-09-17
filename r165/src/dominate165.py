#!/usr/bin/env python3
"""Round 165 phases 4, 5, 7 -- analytic domination, then the minimum basis.

PHASE 5.  (P1) monotonicity is a PROVEN_ANALYTIC node: if every budget of K is
at most the corresponding budget of K', every walk legal in K is legal in K',
so cap(K) <= cap(K').  Therefore a DUAL-CERTIFIED K' that dominates a
single-route K supplies a sound upper bound for K without certifying K at all.
The direction is verified on every dual-certified pair before it is used.

For the piece model the mask flags are RESTRICTIONS -- fp = 1 demands a partial
first block -- so the order is b <= b', d <= d', fp >= fp', lp >= lp'.  That
direction is verified too.

PHASE 4.  A row is only exposed if, with the single-route cells replaced by the
best bound available WITHOUT them, no model closes it.  Since the census takes
the minimum over split / piece / merged and each already falls back to a proved
analytic bound, this test covers every closure route the project currently has.

PHASE 7.  A cell that is INDIVIDUALLY ESSENTIAL must belong to every sufficient
basis (monotonicity again).  So if the set of individually essential cells is
itself sufficient, it is the unique minimum basis and optimality is PROVED, not
argued.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
import hidden163 as H                                             # noqa: E402
import closure165 as CL                                           # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def dual_sets():
    """Cells a SECOND implementation has certified (the python checkers)."""
    v = json.loads((ROOT / "r152" / "certs"
                    / "verify_subset_152.json").read_text())
    p = json.loads((ROOT / "r152" / "certs"
                    / "verify_piece_152.json").read_text())
    chain = {tuple(int(x) for x in r["cell"].split("|")): r["cap"]
             for r in v["rows"] if r["status"] in GOOD}
    piece = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"]
             for r in p["rows"] if r["status"] in GOOD}
    return chain, piece


def chain_dominates(K, Kp):
    return all(a <= b for a, b in zip(K, Kp))


def piece_dominates(K, Kp):
    b, d, fp, lp = K
    b2, d2, fp2, lp2 = Kp
    return b <= b2 and d <= d2 and fp >= fp2 and lp >= lp2


def verify_order(cells, dom):
    """Sanity: the claimed order must never contradict the certified values."""
    bad = []
    items = list(cells.items())
    for K, c in items:
        for Kp, cp in items:
            if K != Kp and dom(K, Kp) and c > cp:
                bad.append(dict(K=str(K), capK=c, Kp=str(Kp), capKp=cp))
                if len(bad) > 8:
                    return bad
    return bad


def main():
    H.load()
    CERT0, PCERT0 = dict(H.CERT), dict(H.PCERT)
    dual_chain, dual_piece = dual_sets()

    # the order must be consistent with every certified value we have
    allchain = dict(CERT0)
    allpiece = {k: v for k, v in PCERT0.items()}
    bad_c = verify_order(allchain, chain_dominates)
    bad_p = verify_order({k: v for k, v in allpiece.items() if v >= 0},
                         piece_dominates)

    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    vg = json.loads((ROOT / "r164" / "certs"
                     / "verifygen_164.json").read_text())
    done = {tuple(int(x) for x in s.split("|"))
            for s in vg["targets_upper_certified_by_two_validators"]}
    chain = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"] if tuple(c) not in done]
    piece = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"] if tuple(c) not in done]

    # ---------- phase 5: what does domination actually give us?
    dom_chain, dom_piece = {}, {}
    for K in chain:
        cands = [(cp, Kp) for Kp, cp in dual_chain.items()
                 if chain_dominates(K, Kp)]
        if cands:
            cp, Kp = min(cands)
            dom_chain[K] = (cp, Kp)
    for K in piece:
        cands = [(cp, Kp) for Kp, cp in dual_piece.items()
                 if piece_dominates(K, Kp) and cp >= 0]
        if cands:
            cp, Kp = min(cands)
            dom_piece[K] = (cp, Kp)

    # how many are as good as the certified value?
    tight_c = sum(1 for K, (cp, _) in dom_chain.items() if cp <= CERT0[K])
    tight_p = sum(1 for K, (cp, _) in dom_piece.items()
                  if PCERT0.get(K, -1) >= 0 and cp <= PCERT0[K])

    groups = CL.grouped()
    base = CL.evaluate(groups)

    def withdraw_with_domination(chain_out, piece_out):
        """Withdraw, but substitute the best dominating dual-certified bound."""
        for c in chain_out:
            if c in dom_chain:
                H.CERT[c] = dom_chain[c][0]
            else:
                H.CERT.pop(c, None)
        for c in piece_out:
            if c in dom_piece:
                H.PCERT[c] = dom_piece[c][0]
            else:
                H.PCERT.pop(c, None)
        H.best.cache_clear()

    withdraw_with_domination(chain, piece)
    dom_res = CL.evaluate(groups)
    CL.restore(CERT0, PCERT0)
    exposed_dom = sorted(k for k in base
                         if base[k]["verdict"] == "STRICTLY_CLOSED"
                         and dom_res[k]["verdict"] != "STRICTLY_CLOSED")

    # ---------- phase 7: is the essential set sufficient?
    graph = json.loads((ROOT / "r165" / "certs"
                        / "row_closure_graph_165.json").read_text())
    ess = set(graph["essential_cells"])
    red_chain = [c for c in chain if "|".join(map(str, c)) not in ess]
    red_piece = [c for c in piece if "|".join(map(str, c)) not in ess]
    CL.withdraw(red_chain, red_piece)
    ess_res = CL.evaluate(groups)
    CL.restore(CERT0, PCERT0)
    still_open = sorted(k for k in base
                        if base[k]["verdict"] == "STRICTLY_CLOSED"
                        and ess_res[k]["verdict"] != "STRICTLY_CLOSED")
    ess_tally = Counter(v["verdict"] for v in ess_res.values())

    # ---------- the same question, with domination also allowed
    withdraw_with_domination(red_chain, red_piece)
    ess_dom_res = CL.evaluate(groups)
    CL.restore(CERT0, PCERT0)
    ess_dom_open = sorted(k for k in base
                          if base[k]["verdict"] == "STRICTLY_CLOSED"
                          and ess_dom_res[k]["verdict"] != "STRICTLY_CLOSED")

    out = dict(
        inputs={p: sha(p) for p in
                ("r152/certs/verify_subset_152.json",
                 "r152/certs/verify_piece_152.json",
                 "r165/certs/row_closure_graph_165.json")},
        dual_certified=dict(chain=len(dual_chain), piece=len(dual_piece)),
        order_consistency=dict(
            chain_violations=bad_c, piece_violations=bad_p,
            chain_ok=not bad_c, piece_ok=not bad_p,
            note="a dominating cell must never carry a SMALLER certified "
                 "capacity than the cell it dominates; checked over every "
                 "certified pair"),
        domination=dict(
            chain_cells_with_a_dominating_dual_cell=len(dom_chain),
            chain_of_those_at_least_as_tight=tight_c,
            piece_cells_with_a_dominating_dual_cell=len(dom_piece),
            piece_of_those_at_least_as_tight=tight_p,
            reading="'at least as tight' means the dominating bound is <= the "
                    "single-route cell's own claimed capacity, i.e. the "
                    "single-route value buys nothing"),
        exposure=dict(
            without_domination=graph["exposed_rows"],
            with_domination=len(exposed_dom),
            rows_rescued_by_domination=graph["exposed_rows"] - len(exposed_dom)),
        essential_basis=dict(
            size=len(ess),
            withdrawing_only_the_redundant_opens=len(still_open),
            sufficient=not still_open,
            census_tally=dict(ess_tally),
            with_domination_also_allowed_opens=len(ess_dom_open)),
        minimum_basis=dict(
            lower_bound=len(ess),
            lower_bound_reason="every individually essential cell lies in "
                               "every sufficient basis: withdrawing it while "
                               "keeping all others already opens a row, and "
                               "bounds are monotone, so no smaller set can "
                               "do better",
            upper_bound=len(ess) if not still_open else None,
            proved_optimal=not still_open,
            size=len(ess) if not still_open else None),
        exposed_rows_after_domination=[list(k[1]) for k in exposed_dom],
    )
    out["ok"] = (out["order_consistency"]["chain_ok"]
                 and out["order_consistency"]["piece_ok"])
    (ROOT / "r165" / "certs" / "minimum_basis_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "exposed_rows_after_domination")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
