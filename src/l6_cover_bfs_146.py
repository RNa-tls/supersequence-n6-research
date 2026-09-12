#!/usr/bin/env python3
"""Round 146 (adversarial) -- a THIRD, independent decision procedure for the
pure-circuit coexistence rows that closed length 871, plus the hand-counting
check for Q1 #0.

WHY THIS EXISTS.  Mutation M7 showed that a "no admissible circuits" verdict
from the two round-144 solvers survives a CORRUPTED orbit->hexagon table: a
negative verdict alone is not evidence that the geometry is right.  This module
answers the same question a third way and, crucially, carries its own POSITIVE
CONTROL: it also computes the minimum number of tau-orbits that DO cover F.
If that number came out <= c the procedure would have said YES, so its NO is
informative.

WHAT IS DECIDED.  For an equality row the incidence bound is tight, the
bipartite graph is a tree, the chain is hex-simple on P hexagons and
|F| = 120 - P = 4c.  Then the total waste of c orbits that exactly cover F is
forced: sum(5 - |new_i|) = 5c - 4c = c.  So the waste budget is not an extra
constraint at all, and the question reduces to plain exact set cover:

    do c tau-orbits, none of them an orbit the chain already uses,
    have F-parts whose union is all of F?

DIFFERENCES FROM THE ROUND-144 SOLVERS.
  * state is an int bitmask over F, not a frozenset of hexagon ids;
  * search is iterative layer-by-layer BFS over masks, not recursive DFS
    (l6_circuit_coexist_144) nor subset enumeration (l6_coexist_check3_144);
  * no waste bookkeeping (proved redundant above);
  * the hexagon/orbit partitions are rebuilt from sig()/tau() string algebra
    and only then cross-checked against the production tables.

STATUS of the results: EXHAUSTIVELY_VERIFIED (no cap is used; the BFS closes).
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

PERMS = ["".join(p) for p in itertools.permutations("123456")]


def sig(s):
    return s[1:] + s[0]


def tau(s):
    return s[1:-1] + s[0] + s[-1]


def classes(f):
    """Partition the 720 permutations into the orbits of f."""
    seen, cid = {}, 0
    for p in PERMS:
        if p in seen:
            continue
        q = p
        while q not in seen:
            seen[q] = cid
            q = f(q)
        cid += 1
    return [seen[p] for p in PERMS], cid


HEX, NH = classes(sig)
ORB, NQ = classes(tau)
ORBHEX = [set() for _ in range(NQ)]
for _v in range(720):
    ORBHEX[ORB[_v]].add(HEX[_v])
assert NH == 120 and NQ == 144
assert all(len(h) == 5 for h in ORBHEX), "a tau-orbit must meet five hexagons"


def same_partition(a, b):
    """Do two labellings induce the same partition of 0..719?"""
    fwd, back = {}, {}
    for i in range(720):
        if fwd.setdefault(a[i], b[i]) != b[i]:
            return False
        if back.setdefault(b[i], a[i]) != a[i]:
            return False
    return True


def cross_check():
    """The clean-room partitions must equal the ones the solvers use."""
    from verify_f2_structure_126 import setup
    G6 = setup(6)
    return dict(hex=same_partition(HEX, G6["hexid"]),
                orb=same_partition(ORB, G6["orbid"]))


def min_orbits_to_cover(ports, cmax):
    """Fewest chain-disjoint tau-orbits whose F-parts cover F (None if > cmax).

    Layered BFS with the canonical rule "the lowest still-uncovered hexagon of
    F must be covered by the orbit chosen at this step", which loses no cover
    and kills all orderings of the same set.
    """
    Hc = {HEX[v] for v in ports}
    Oc = {ORB[v] for v in ports}
    F = sorted(set(range(NH)) - Hc)
    bit = {h: 1 << i for i, h in enumerate(F)}
    FULL = (1 << len(F)) - 1
    cands = []
    for q in range(NQ):
        if q in Oc:
            continue
        m = 0
        for h in ORBHEX[q]:
            if h in bit:
                m |= bit[h]
        if m:
            cands.append((q, m))
    by = [[qm for qm in cands if qm[1] >> i & 1] for i in range(len(F))]
    layer, nodes, reached = {0}, 0, {}
    for depth in range(cmax):
        nxt = set()
        for mask in layer:
            low = min(i for i in range(len(F)) if not mask >> i & 1)
            for q, m in by[low]:
                nodes += 1
                nm = mask | m
                if bin(FULL ^ nm).count("1") > 5 * (cmax - depth - 1):
                    continue
                nxt.add(nm)
        layer = nxt
        reached[depth + 1] = len(layer)
        if FULL in layer:
            return dict(min_orbits=depth + 1, nodes=nodes, candidates=len(cands),
                        Fsize=len(F), layers=reached, capped=False)
        if not layer:
            break
    return dict(min_orbits=None, nodes=nodes, candidates=len(cands),
                Fsize=len(F), layers=reached, capped=False)


def decide(ports, c):
    """Exhaustive verdict for one equality row, with its own positive control."""
    Hc = {HEX[v] for v in ports}
    F = set(range(NH)) - Hc
    hex_simple = len(Hc) == len(ports)
    forced = len(F) == 4 * c
    tight = min_orbits_to_cover(ports, c)
    # positive control: the SAME code path must be able to answer YES
    ctrl = min_orbits_to_cover(ports, 12)
    return dict(ports=len(ports), hex_simple=hex_simple, Fsize=len(F), c=c,
                F_equals_4c=forced,
                coverable_by_c_orbits=tight["min_orbits"] is not None,
                nodes_at_c=tight["nodes"],
                min_orbits_to_cover_F=ctrl["min_orbits"],
                nodes_control=ctrl["nodes"], capped=False,
                margin=None if ctrl["min_orbits"] is None else ctrl["min_orbits"] - c)


def hand_count(ports, c):
    """The relaxation used in the write-up: c orbits cover at most the c
    largest values of |hex(orbit) cap F|, so if that sum is < |F| the row dies
    with no search at all.  Reported for every row (it only settles Q1 #0)."""
    Hc = {HEX[v] for v in ports}
    F = set(range(NH)) - Hc
    inter = sorted((len(ORBHEX[q] & F) for q in range(NQ)), reverse=True)
    return dict(Fsize=len(F), top_c=inter[:c], sum_top_c=sum(inter[:c]),
                settles_row=sum(inter[:c]) < len(F))


def main():
    wq1 = [json.loads(l) for l in
           (ROOT / "outputs/witness_144/wit_Q1.jsonl").read_text().splitlines() if l.strip()]
    wq2 = [json.loads(l) for l in
           (ROOT / "outputs/witness_144/wit_Q2.jsonl").read_text().splitlines() if l.strip()]
    rows = [("Q1#0", wq1[0]["ports"], 6), ("Q1#1", wq1[1]["ports"], 6),
            ("Q2#0", wq2[0]["ports"], 7)]
    res = dict(cross_check=cross_check(), rows={})
    for name, ports, c in rows:
        res["rows"][name] = dict(bfs=decide(ports, c), counting=hand_count(ports, c))
    res["ok"] = (all(res["cross_check"].values())
                 and all(not r["bfs"]["coverable_by_c_orbits"] for r in res["rows"].values())
                 and all(r["bfs"]["min_orbits_to_cover_F"] is not None
                         for r in res["rows"].values()))
    out = ROOT / "outputs" / "rr_l6_cover_bfs_146.json"
    out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, sort_keys=True))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
