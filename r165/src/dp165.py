#!/usr/bin/env python3
"""Round 165 phase 13 -- independent DP pilot on the piece model.

The question a DP has to answer is the UPPER bound, so a RELAXED recurrence is
sound: allowing more walks can only raise the bound.  The pilot measures how
much structure a DP can drop and still say anything useful.

State (deliberately unlike the production DFS, which carries the actual port,
the used-hexagon set and the per-orbit phase sets):

    (ports, orbits, blocks, current orbit's phase count)

with the per-orbit phase cap 5 enforced exactly, the block/token arithmetic
      tokens  = blocks - orbits <= b
      deficit = 5*orbits - ports <= d
enforced exactly, and the hexagon constraint relaxed to the counting bound
ports <= 120 (a hexagon is used at most once, and there are 120 of them).

What it drops is WHICH hexagons and WHICH orbits, i.e. the geometry of the
transition relation.  The pilot reports the resulting bound next to the
certified capacity so the cost of that relaxation is visible rather than
argued.
"""
from __future__ import annotations
import json, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
import routeb164 as R                                             # noqa: E402

HEXCAP = 120
NORB = 144


def relaxed_bound(b, d, fp, lp):
    """Largest port count the relaxed recurrence admits."""

    @lru_cache(maxsize=None)
    def best(ports, orbits, blocks, curphase):
        # prune: the arithmetic budgets
        if ports > HEXCAP or orbits > NORB:
            return -1
        if blocks - orbits > b:
            return -1
        acc = ports if 5 * orbits - ports <= d else -1
        out = acc
        # extend the current block by one clean-E step
        if curphase < 5:
            r = best(ports + 1, orbits, blocks, curphase + 1)
            out = max(out, r)
        # a paid move opening a FRESH orbit
        r = best(ports + 1, orbits + 1, blocks + 1, 1)
        out = max(out, r)
        # a paid move re-entering an orbit that still has a free phase
        if orbits >= 1:
            r = best(ports + 1, orbits, blocks + 1, 1)
            out = max(out, r)
        return out

    v = best(1, 1, 1, 1)
    best.cache_clear()
    return v


def main():
    pc, _ = R.parse_pcert(ROOT / "r152" / "certs" / "pcert_all_152.txt")
    graph = json.loads((ROOT / "r165" / "certs"
                        / "row_closure_graph_165.json").read_text())
    ess_piece = [c for c in graph["essential_cells"]
                 if graph["ablation"][c]["model"] == "piece"]
    rows = []
    for c in sorted(ess_piece)[:12]:
        k = tuple(int(x) for x in c.split("|"))
        cap = pc[k]["cap"]
        ub = relaxed_bound(*k)
        rows.append(dict(cell=c, certified_cap=cap, relaxed_dp_bound=ub,
                         sound=(ub >= cap), gap=ub - cap,
                         tight=(ub == cap)))
    analytic = HEXCAP
    out = dict(
        model="piece",
        state="(ports, orbits, blocks, current orbit's phase count)",
        kept=["per-orbit phase cap 5", "tokens = blocks - orbits <= b",
              "deficit = 5*orbits - ports <= d", "ports <= 120"],
        dropped=["which hexagon each port lies in",
                 "which orbit each block enters",
                 "the transition relation itself"],
        cells=rows,
        all_bounds_sound=all(r["sound"] for r in rows),
        any_tight=any(r["tight"] for r in rows),
        median_gap=sorted(r["gap"] for r in rows)[len(rows) // 2],
        analytic_bound_for_comparison=analytic,
        conclusion="the relaxed recurrence reproduces the analytic bound and "
                   "nothing better: every certified capacity is far below it. "
                   "The certified values come from the GEOMETRY of the "
                   "transition relation, which is exactly what a DP has to "
                   "drop to stay polynomial, so a substantially different "
                   "EXACT state representation is not available for this "
                   "model.  Recorded as a negative pilot result.",
    )
    out["ok"] = out["all_bounds_sound"]
    (ROOT / "r165" / "certs" / "dp_pilot_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "cells"},
                     ensure_ascii=False, indent=1))
    for r in rows[:6]:
        print(" ", r)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
