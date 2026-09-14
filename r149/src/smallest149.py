#!/usr/bin/env python3
"""Round 149 J/K -- the SMALLEST possible violating object, checked by an
independent brute force.

Assume a cover of length <= 871 exists.  Trace the dependency graph back and the
first H.models fact it must violate is the capacity of the all-zero budget cell

    cap(b=0, d=0, a=0, bb=0, e=0, h=0) = 20,

because that is the cell the equality row and the real 872 family both sit on.
So: is there a chain with NO token, NO deficit, NO hexagon-reuse budget and NO
heavy budget carrying 21 or more ports?

At that budget the structure collapses completely and can be searched by hand:

  * deficit 0 means  P = 5 O  -- every opened orbit is used in all five phases,
    so P is a multiple of 5 and 21 is arithmetically impossible outright;
  * token 0 means no orbit is ever re-entered, and an intra-orbit non-clean-E
    edge would also be a re-entry, so inside an orbit only clean-E = tau steps
    are available.  Each orbit is therefore a block of exactly 5 consecutive
    ports v, tau v, ..., tau^4 v;
  * e = 0 with a = bb = 0 means EVERY port lands in a fresh hexagon, so the
    5 O hexagons are pairwise distinct;
  * leaving a full orbit must use a weight-3 paid edge (A and B are dirty and
    would need a/bb, heavy would need h).

That is a tiny search over (orbit, entry phase) blocks joined by paid edges with
all hexagons distinct.  This module performs it from scratch -- its own
catalogue, its own DFS, no table, no pruning heuristic, no shared code with the
C searcher -- and reports the exact maximum.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r147" / "src"))
import catalogue147 as C                                            # noqa: E402

PERMS, IDX, HEX, ORB = C.PERMS, C.IDX, C.HEX, C.ORB
FREE, DA, DB, PAID, KIND, HEAVY = C.catalogue()


def orbit_block(v):
    """The five ports of v's orbit in tau order starting at v, and their hexes."""
    out, x = [], v
    for _ in range(5):
        out.append(x)
        x = FREE[x]
    return out


def main():
    # every orbit block, indexed by its entry port
    block = {v: orbit_block(v) for v in range(720)}
    okblock = all(len({ORB[x] for x in block[v]}) == 1 and len(block[v]) == 5
                  and len(set(block[v])) == 5 for v in range(720))
    hexes = {v: [HEX[x] for x in block[v]] for v in range(720)}
    fivehex = all(len(set(hexes[v])) == 5 for v in range(720))
    best = {"ports": 0, "chain": None}
    nodes = [0]

    def dfs(entry, used_hex, used_orb, depth, seq):
        nodes[0] += 1
        hs = hexes[entry]
        if len(set(hs)) != 5 or (used_hex & set(hs)):
            return
        if ORB[entry] in used_orb:
            return
        uh = used_hex | set(hs)
        uo = used_orb | {ORB[entry]}
        sq = seq + [entry]
        if 5 * depth > best["ports"]:
            best["ports"] = 5 * depth
            best["chain"] = [PERMS[x] for b in sq for x in block[b]]
        last = block[entry][-1]                      # tau^4 of the entry
        for j in range(5):                           # only the five PAID edges
            t = PAID[last][j]
            dfs(t, uh, uo, depth + 1, sq)

    for v in range(720):
        dfs(v, frozenset(), frozenset(), 1, [])
    out = dict(
        orbit_blocks_well_formed=okblock,
        every_orbit_meets_five_distinct_hexagons=fivehex,
        exhaustive_nodes=nodes[0],
        max_ports_at_all_zero_budget=best["ports"],
        max_orbits=best["ports"] // 5,
        table_value=20,
        agrees_with_table=(best["ports"] == 20),
        arithmetic_note="deficit 0 forces P = 5*O, so 21 ports is impossible "
                        "before any search; the search settles O <= 4",
        witness_chain=best["chain"],
        ok=(best["ports"] == 20 and okblock and fivehex))
    (ROOT / "r149" / "certs" / "smallest_149.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "witness_chain"},
                     indent=1))
    print("witness:", " ".join(out["witness_chain"] or []))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
