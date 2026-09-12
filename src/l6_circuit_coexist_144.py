#!/usr/bin/env python3
"""L6 endgame — the pure-E-circuit coexistence test for the last 871 rows.

WHAT IS LEFT.  With the three upper-bound models combined soundly, length 871
reduces to coordinate rows whose bound EQUALS the required port count.  Each is
a single hex-simple chain of `P` ports together with `c` pure clean-E circuits
(full tau-orbits).  For those rows the Round-142 incidence bound is TIGHT:

    K + R_int = G + 1,      K = c + 1,  R_int = 0,  G = c.

THE CONSEQUENCE.  In the proof of the incidence bound (src/l6_incidence_144.py)
the slack is exactly the number of independent cycles of the bipartite graph
joining the 121 alpha-cycles (120 hexagons + the dummy) to the K beta-components.
So tightness says that graph is a TREE.  Since R_int = 0 every (hexagon,
component) pair meets in at most one port, so its edges are the 120 + G + 1
port/dummy incidences, and the tree condition becomes

  * every one of the 120 hexagons is used (otherwise the repeat excess exceeds G);
  * the c circuits' 5c hexagons must COVER the 120 - P hexagons the chain does
    not use, and 120 - P = 4c, so exactly c of the 5c incidences fall outside
    that set -- on a chain hexagon or on a hexagon another circuit already used;
  * the circuit/chain hypergraph is acyclic.

So the question is finite and small: given the chain, do `c` tau-orbits exist
that are disjoint from the chain's orbits and cover its complement with total
waste c?  This module answers it by exhaustive search over the equality
witnesses produced by `l6chain_144.exe` in witness mode.

A NEGATIVE answer closes the row.  A POSITIVE answer does NOT build a cover:
the models are relaxations, so it only means this test does not decide.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from verify_f2_structure_126 import setup                          # noqa: E402

G6 = setup(6)
HEX, ORB = G6["hexid"], G6["orbid"]
NP, NH, NQ = 720, 120, 144
ORBPORTS = [[] for _ in range(NQ)]
for v in range(NP):
    ORBPORTS[ORB[v]].append(v)
ORBHEX = [sorted({HEX[v] for v in ORBPORTS[q]}) for q in range(NQ)]
assert all(len(h) == 5 for h in ORBHEX), "a tau-orbit must meet five hexagons"


class _Found(Exception):
    """Raised to stop at the first solution when first_only is set.

    Opt-in only: with first_only False (the default, and what every Q1/Q2
    verdict uses) the search is byte-for-byte the exhaustive one.
    """


def coexist(chain, c, node_cap=20_000_000, first_only=False):
    """Can c tau-orbits, disjoint from the chain's orbits, cover its complement?"""
    Hc = {HEX[v] for v in chain}
    Oc = {ORB[v] for v in chain}
    if len(Hc) != len(chain):
        return dict(ok=False, reason="chain not hex-simple")
    F = sorted(set(range(NH)) - Hc)
    if len(F) != 4 * c:
        return dict(ok=False, reason=f"|F|={len(F)} != 4c={4 * c}")
    cand = [q for q in range(NQ) if q not in Oc]
    byhex = {h: [q for q in cand if h in ORBHEX[q]] for h in F}
    Fset = set(F)
    nodes = [0]
    sols = []

    def rec(covered, used, waste):
        nodes[0] += 1
        if nodes[0] > node_cap:
            raise RuntimeError("coexistence search capped")
        if len(used) == c:
            if covered == Fset:
                sols.append(sorted(used))
                if first_only:
                    raise _Found()
            return
        rem = [h for h in F if h not in covered]
        if not rem:
            return
        need = len(rem)
        if need > 5 * (c - len(used)):          # an orbit meets five hexagons
            return
        h0 = rem[0]
        for q in byhex[h0]:
            if q in used:
                continue
            new = Fset & set(ORBHEX[q]) - covered
            w = 5 - len(new)
            if waste + w > c:
                continue
            rec(covered | new, used | {q}, waste + w)

    try:
        rec(frozenset(), frozenset(), 0)
    except _Found:
        pass
    return dict(ok=bool(sols), solutions=len(sols), nodes=nodes[0],
                examples=[s for s in sols[:3]], free_hexes=len(F),
                chain_orbits=len(Oc), c=c)


def main(path, c, deficit):
    res = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        chain = json.loads(line)["ports"]
        Oc = {ORB[v] for v in chain}
        assert 5 * len(Oc) - len(chain) == deficit, (len(Oc), len(chain))
        r = coexist(chain, c)
        r["ports"] = len(chain)
        res.append(r)
        print(json.dumps({k: r[k] for k in
                          ("ports", "chain_orbits", "free_hexes", "c", "ok",
                           "solutions", "nodes") if k in r}), flush=True)
    return res


if __name__ == "__main__":
    path, c, dfc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    out = main(path, c, dfc)
    tag = Path(path).stem
    (ROOT / "outputs" / f"rr_l6_coexist_{tag}_144.json").write_text(
        json.dumps(dict(witnesses=len(out), any_ok=any(x["ok"] for x in out),
                        detail=out), ensure_ascii=False, indent=1))
    print("witnesses:", len(out), " any admits the circuits:",
          any(x["ok"] for x in out))
