#!/usr/bin/env python3
"""Round 167 phases 15 and 20 -- margins per certificate and the round-168 plan.

Two things a generation plan needs that the optimum alone does not give.

MARGIN.  Eight of the 190 cells are absent from the round-152 chain table;
their capacity is PREDICTED by (BRIDGE-EQ) from the tabulated piece value.  A
prediction is a planning input, so the plan has to say how much slack there
is: by how much could the generated certificate exceed the planned value
before a census row re-opens?  Raising one cell's value from v towards its
analytic fallback is monotone, so only the rows that open when the cell is
withdrawn entirely can be affected -- those rows are recorded by the solver,
and the margin is a binary search over them alone.

ORDER.  Certificates are generated cheapest first, so that a wrong assumption
surfaces in minutes rather than after a week of CPU.  Checkpoints are placed
at 25/50/75/100 per cent of the estimated node budget, and at each one the
plan states, in advance, exactly how many exposed rows must be closed.  A
checkpoint that misses its number is a refutation, not a delay.
"""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import hidden163 as H                                             # noqa: E402
import extree_basis_verify as V                                   # noqa: E402
sys.path.insert(0, str(ROOT / "r167" / "src"))
from optcert167 import (Rules, groups_by_layer, closed, done_cells,   # noqa: E402
                        parse, cellstr, sha, BATCHES)

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def calibration():
    """EXTREE node count against the round-152 search node count."""
    cn = {parse(r["cell"]): r.get("nodes", 0)
          for r in json.loads((CERTS / "verify_all_c152.json").read_text())
          ["rows"] if r["status"] in GOOD}
    pairs = []
    for rel in BATCHES:
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for cell, _capv, toks in V.parse_batch(text)[1]:
            if cn.get(tuple(cell)):
                pairs.append((cellstr(tuple(cell)), len(toks), cn[tuple(cell)]))
    rat = sorted(a / b for _, a, b in pairs)
    return dict(cells=len(pairs),
                extree_nodes=sum(a for _, a, _ in pairs),
                search_nodes=sum(b for _, _, b in pairs),
                ratio_min=round(rat[0], 4),
                ratio_median=round(rat[len(rat) // 2], 4),
                ratio_max=round(rat[-1], 4),
                ratio_aggregate=round(sum(a for _, a, _ in pairs)
                                      / sum(b for _, _, b in pairs), 4),
                rule="planned EXTREE nodes = round-152 search nodes x the "
                     "aggregate ratio; the maximum observed ratio is used for "
                     "the pessimistic column")


def main():
    t0 = time.time()
    src = json.loads((ROOT / "r167" / "certs"
                      / "row_optimum_167.json").read_text())
    assert src["ok"]
    R = Rules()
    G = groups_by_layer()
    U = {parse(c) for c in src["universe"]["cells"]}
    OPT = {parse(c) for c in src["optimum"]["cells"]}
    guard = {parse(c): [(t, tuple(k)) for t, k in v]
             for c, v in src["optimum"]["guarded_rows"].items()}
    DONE = done_cells()
    REM = sorted(OPT - DONE)
    cn = {parse(r["cell"]): r.get("nodes", 0)
          for r in json.loads((CERTS / "verify_all_c152.json").read_text())
          ["rows"] if r["status"] in GOOD}
    pn = {(r["b"], r["d"], r["fp"], r["lp"]): r.get("nodes", 0)
          for r in json.loads((CERTS / "verify_piece_c152.json").read_text())
          ["rows"] if r["status"] in GOOD}

    def search_nodes(K):
        if cn.get(K):
            return cn[K], "measured chain search"
        if K[2:] == (0, 0, 0, 0) and pn.get((K[0], K[1], 0, 0)):
            return pn[(K[0], K[1], 0, 0)], "measured piece search, same walks"
        best = None
        for k, v in cn.items():
            if v and all(a <= b for a, b in zip(K, k)):
                best = v if best is None else min(best, v)
        return best, "estimated from the cheapest measured dominating cell"

    # ---------- phase 15: margin of every selected certificate
    plan_val = {}
    for K in sorted(OPT):
        v = R.value_of(K)
        plan_val[K] = v
    margins = {}
    for K in sorted(OPT):
        rows = guard[K]
        v = plan_val[K]
        cap = 120 + K[2] + K[3] + K[4]          # the analytic fallback

        def ok(x):
            R.apply(OPT, override={K: x})
            return all(closed(G[t][k])[0] for t, k in rows)

        lo, hi = v, cap                          # ok(lo) true, ok(cap) false
        assert ok(lo), cellstr(K)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ok(mid):
                lo = mid
            else:
                hi = mid
        margins[cellstr(K)] = dict(
            planned_value=v, largest_still_safe=lo, margin=lo - v,
            analytic_fallback=cap, guarded_rows=len(rows),
            from_the_chain_table=K in R.chain_tab)

    # ---------- phase 20: order and checkpoints
    order = sorted(REM, key=lambda K: (search_nodes(K)[0] or 0, K))
    cal = calibration()
    rows_ex = None
    R.full()
    base = {(t, k): closed(v)[0] for t, g in G.items() for k, v in g.items()}
    R.apply(set())
    now = {(t, k): closed(v)[0] for t, g in G.items() for k, v in g.items()}
    EX = sorted(k for k in base if base[k] and not now[k])
    total = sum(search_nodes(K)[0] or 0 for K in order)
    cum, marks, batches = 0, [0.25, 0.5, 0.75, 1.0], []
    nxt = 0
    for i, K in enumerate(order, 1):
        cum += search_nodes(K)[0] or 0
        while nxt < len(marks) and cum >= marks[nxt] * total:
            R.apply(DONE | set(order[:i]))
            shut = sum(1 for k in EX if closed(G[k[0]][k[1]])[0])
            batches.append(dict(
                checkpoint=f"{int(marks[nxt] * 100)}%",
                certificates_generated=i, last_cell=cellstr(K),
                cumulative_search_nodes=cum,
                planned_extree_nodes=int(cum * cal["ratio_aggregate"]),
                pessimistic_extree_nodes=int(cum * cal["ratio_max"]),
                exposed_rows_that_must_be_closed=shut,
                exposed_rows_still_open=len(EX) - shut))
            nxt += 1

    out = dict(
        inputs={p: sha(p) for p in
                ("r167/certs/row_optimum_167.json",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json") + BATCHES},
        calibration=cal,
        margins=dict(
            cells=len(margins),
            zero_margin=sorted(c for c, v in margins.items()
                               if v["margin"] == 0),
            zero_margin_count=sum(1 for v in margins.values()
                                  if v["margin"] == 0),
            predicted_cells=dict(
                (c, margins[c]) for c in sorted(margins)
                if not margins[c]["from_the_chain_table"]),
            detail=margins,
            meaning="largest_still_safe is the biggest capacity value this "
                    "cell could turn out to have with every exposed row still "
                    "strictly closed.  A generated certificate reporting more "
                    "than that refutes the plan for this cell and the row "
                    "optimisation has to be redone with the true value."),
        generation_plan=dict(
            remaining=len(REM),
            already_certified=len(OPT & DONE),
            order=[dict(cell=cellstr(K), search_nodes=search_nodes(K)[0],
                        basis=search_nodes(K)[1]) for K in order],
            total_search_nodes=total,
            total_planned_extree_nodes=int(total * cal["ratio_aggregate"]),
            total_pessimistic_extree_nodes=int(total * cal["ratio_max"]),
            checkpoints=batches,
            rule="cheapest first, so that a wrong planned value shows up "
                 "early; each checkpoint states in advance how many of the "
                 f"{len(EX)} exposed rows must be closed by then"),
    )
    out["ok"] = (len(batches) == 4
                 and batches[-1]["exposed_rows_still_open"] == 0
                 and len(margins) == len(OPT))
    (ROOT / "r167" / "certs" / "round168_plan_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = json.loads(json.dumps(out))
    show.pop("inputs")
    show["margins"].pop("detail")
    show["generation_plan"].pop("order")
    print(json.dumps(show, ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
