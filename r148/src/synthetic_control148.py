#!/usr/bin/env python3
"""Round 148 Phase 11 -- a CONSTRUCTED positive control for the exact-cover
coexistence solver.

src/l6_circuit_coexist_144.py structurally requires |F| = 4c, so it cannot be
controlled by raising c on the same instance the way the BFS and subset
procedures can.  Here an instance of exactly its shape is BUILT with a known
solution, so a NO from it on that instance would be a proved bug:

    pick a tau-orbit q, whose five hexagons are h1..h5;
    let the chain occupy every hexagon except h1..h4, taking its port in h5
    (and everywhere else) from an orbit other than q;
    then F = {h1,h2,h3,h4}, |F| = 4 = 4c with c = 1, and q alone covers F with
    waste 1 = c.

So the answer is YES and the solver must find it.  The same instance is put to
the other two procedures, and the construction is repeated over many orbits so
the control is not a single lucky case.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R148 = ROOT / "r148"
sys.path.insert(0, str(ROOT / "src"))
import l6_circuit_coexist_144 as CO                                 # noqa: E402
import l6_coexist_check3_144 as CO3                                 # noqa: E402
import l6_cover_bfs_146 as CB                                       # noqa: E402

HEX, ORB, ORBHEX = CO.HEX, CO.ORB, CO.ORBHEX


def build(q):
    """A chain whose free hexagons are exactly four of orbit q's five."""
    hs = list(ORBHEX[q])
    F = set(hs[:4])
    chain = []
    for h in range(120):
        if h in F:
            continue
        cand = [v for v in range(720) if HEX[v] == h and ORB[v] != q]
        if not cand:
            return None
        chain.append(cand[0])
    if len({HEX[v] for v in chain}) != len(chain):
        return None
    if q in {ORB[v] for v in chain}:
        return None
    return chain, sorted(F)


def main(argv):
    n = int(argv[0]) if argv else 40
    rows, built = [], 0
    for q in range(144):
        b = build(q)
        if b is None:
            continue
        chain, F = b
        built += 1
        r1 = CO.coexist(chain, 1, first_only=True)
        r3 = CO3.solve(chain, 1, first_only=True)
        rb = CB.decide(chain, 1)
        rows.append(dict(orbit=q, chain_ports=len(chain), F=F,
                         dfs_ok=r1.get("ok"), dfs_nodes=r1.get("nodes"),
                         subset_ok=r3.get("ok"), subset_nodes=r3.get("nodes"),
                         bfs_coverable=rb["coverable_by_c_orbits"],
                         bfs_min_orbits=rb["min_orbits_to_cover_F"]))
        if built >= n:
            break
    out = dict(instances=len(rows),
               dfs_yes=sum(1 for r in rows if r["dfs_ok"] is True),
               subset_yes=sum(1 for r in rows if r["subset_ok"] is True),
               bfs_yes=sum(1 for r in rows if r["bfs_coverable"] is True),
               detail=rows[:10],
               ok=(bool(rows)
                   and all(r["dfs_ok"] is True for r in rows)
                   and all(r["subset_ok"] is True for r in rows)
                   and all(r["bfs_coverable"] is True for r in rows)))
    (R148 / "certs" / "synthetic_controls_148.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
