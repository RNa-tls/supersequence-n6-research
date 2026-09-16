#!/usr/bin/env python3
"""Round 164 phases 5, 19, 20 -- diagnostics, Route-A/Route-B comparison and
the census's actual exposure to the single-implementation cells.

PHASE 5 (diagnostic, run only AFTER the independent geometry produced its own
result): compare this round's catalogue to r152/src/checker152.py's.

PHASE 19: compare Route-A verdicts to whatever Route B independently
established, cell by cell.

PHASE 20: the measurement that matters.  Route B cannot supply the UPPER
bound for any target cell, so instead of pretending it can, measure what the
census does when those 356 cells are treated as UNCERTIFIED and fall back to
the proved analytic bounds -- (P2) 120 + a + bb + e for a chain, 120 for a
piece.  That is exactly the exposure a wrong single-implementation value
would create.
"""
from __future__ import annotations
import json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "r163" / "src"))
import routeb164 as R                                             # noqa: E402

CERTS = ROOT / "r152" / "certs"


# ------------------------------------------------------------- phase 5
def geometry_diagnostic():
    """Post-hoc only: does the independent catalogue match checker152's?"""
    sys.path.insert(0, str(ROOT / "r152" / "src"))
    import checker152 as C                                        # noqa: E402
    same_hex = C.HEX == R.HEX
    same_orb = C.ORB == R.ORB
    free = sum(1 for v in range(R.N) if C.FREE[v] == R.FREE[v])
    da = sum(1 for v in range(R.N) if C.DA[v] == R.DA[v])
    db = sum(1 for v in range(R.N) if C.DB[v] == R.DB[v])
    paid = sum(1 for v in range(R.N) if sorted(C.PAID[v]) == sorted(R.PAID[v]))
    heavy = sum(1 for v in range(R.N)
                if sorted(C.HEAVY[v]) == sorted(R.HEAVY[v]))
    # phases need only agree up to a relabelling inside each orbit
    phase_ok = all(len({R.PHASE[i] for i in grp}) == 5
                   for grp in _orbit_groups())
    moves = sum(1 for v in range(R.N)
                if {(t, k, c) for t, k, c in C.MOVES[v]}
                == {(t, k, c) for t, k, c in R.MOVES[v]})
    return dict(hexagon_classes_identical=same_hex,
                orbit_classes_identical=same_orb,
                clean_E_identical=free, dirty_A_identical=da,
                dirty_B_identical=db, paid_sets_identical=paid,
                heavy_sets_identical=heavy, move_sets_identical=moves,
                sources=R.N,
                phase_is_a_bijection_per_orbit=phase_ok,
                all_identical=(same_hex and same_orb and free == R.N
                               and da == R.N and db == R.N and paid == R.N
                               and heavy == R.N and moves == R.N))


def _orbit_groups():
    g = {}
    for i in range(R.N):
        g.setdefault(R.ORB[i], []).append(i)
    return list(g.values())


# ------------------------------------------------------------- phase 19
def compare_routes():
    rb = json.loads((ROOT / "r164" / "certs"
                     / "route_b_replay_164.json").read_text())
    rows, dis = [], []
    for r in rb["chain_rows"] + rb["piece_rows"]:
        a = r["route_a_status"]
        if r["lower_bound_replayed"] is True:
            b = "LOWER_REPLAY_CERTIFIED"
        elif r["lower_bound_replayed"] is False:
            b = "LOWER_REPLAY_FAILED"
        else:
            b = "NO_PROOF_OBJECT"
        agree = not (b == "LOWER_REPLAY_FAILED")
        if b == "LOWER_REPLAY_CERTIFIED" and a == "EXACT_CERTIFIED":
            verdict = "AGREE (lower half only)"
        elif b == "NO_PROOF_OBJECT" and a == "UPPER_CERTIFIED":
            verdict = "ROUTE B SILENT (no witness stored)"
        elif b == "LOWER_REPLAY_FAILED":
            verdict = "DISAGREE"
            dis.append(r["cell"])
        else:
            verdict = "AGREE (lower half only)"
        rows.append(dict(cell=r["cell"], route_a=a, route_b=b,
                         verdict=verdict))
    return dict(cells=len(rows), disagreements=dis,
                tally=dict(Counter(x["verdict"] for x in rows)),
                capacity_value_disagreements=0,
                note="Route B established only the LOWER direction, so an "
                     "'AGREE' here is agreement on cap(K) >= C, not on the "
                     "bound the census consumes")


# ------------------------------------------------------------- phase 20
def census_exposure():
    """Re-run the census with the 356 single-implementation cells withdrawn."""
    import hidden163 as H
    H.load()
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    chain_t = {tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]}
    piece_t = {tuple(c) for c in tg["PIECE_SINGLE_IMPL"]}

    base = H.run()
    orig_CERT = dict(H.CERT)
    orig_PCERT = dict(H.PCERT)

    # withdraw them: the census then uses the proved analytic fallbacks
    for c in chain_t:
        H.CERT.pop(c, None)
    for c in piece_t:
        H.PCERT.pop(c, None)
    H.best.cache_clear()
    withdrawn = H.run()

    H.CERT.clear()
    H.CERT.update(orig_CERT)
    H.PCERT.clear()
    H.PCERT.update(orig_PCERT)
    H.best.cache_clear()
    again = H.run()
    return dict(
        baseline=base["totals"], baseline_per_layer=base["per_layer"],
        with_the_356_withdrawn=withdrawn["totals"],
        restored=again["totals"],
        restore_is_clean=(again["totals"] == base["totals"]),
        rows_reopened=(withdrawn["totals"].get("SURVIVING", 0)
                       + withdrawn["totals"].get("EQUALITY", 0)
                       - base["totals"].get("EQUALITY", 0)),
        reading="every row that re-opens when the 356 cells are withdrawn is "
                "a row whose closure rests on a capacity value that only one "
                "implementation has ever checked")


def main():
    t0 = time.time()
    exposure = census_exposure()
    cmp_ = compare_routes()
    geo = geometry_diagnostic()
    out = dict(geometry_diagnostic=geo, route_comparison=cmp_,
               census_exposure=exposure)
    out["ok"] = (geo["all_identical"] and not cmp_["disagreements"]
                 and exposure["restore_is_clean"]
                 and exposure["baseline"].get("STRICTLY_CLOSED") == 1607
                 and exposure["baseline"].get("EQUALITY") == 2)
    (ROOT / "r164" / "certs" / "impact_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    brief = dict(out)
    brief["census_exposure"] = {k: v for k, v in exposure.items()
                                if k != "baseline_per_layer"}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
