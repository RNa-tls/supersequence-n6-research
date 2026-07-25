#!/usr/bin/env python3
"""Round 23, sections 12-16: the branch transport map, and the obstruction
that rules out an exact state-level one.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
def _load(n, f):
    p = WORK / f; s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
macro = _load("brt_macro", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]

def root(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_branch_transport_map.json"))
    a = ap.parse_args()
    rows = {}
    for ell in range(5):
        r = root(ell)
        rows[str(ell)] = {"O_star": HEX0[ell + 1], "visited_count": r.visited_count,
                          "touched_hexagons": sum(1 for m in r.hex_masks if m),
                          "O": r.O, "S": r.S, "F": r.F, "P": r.P,
                          "endpoint_orbit_phase": list(exact.ORBIT_PHASE[r.p]),
                          "endpoint_hexagon": core.hexagon_id(r.p)}
        print(f"  ell={ell}: O*={HEX0[ell+1]:3d} visited={r.visited_count} hexes={rows[str(ell)]['touched_hexagons']} "
              f"O={r.O} endpoint={exact.ORBIT_PHASE[r.p]}")
    vc = {k: v["visited_count"] for k, v in rows.items()}
    obstruction = len(set(vc.values())) > 1
    print(f"\nabandonment roots have DIFFERENT visited counts: {vc}")
    print(f"exact state-level transport map possible: {not obstruction}")
    rep = {
        "schema": "rr-branch-transport-map-v1",
        "abandonment_roots": rows,
        "exact_state_level_transport": {
            "possible": not obstruction,
            "verdict": "반증됨" if obstruction else "미완료",
            "proof": (
                "The abandonment root for offset ell has visited_count = ell + 2 "
                "(the hub's positions 0..ell, plus the abandonment target). So "
                "root(0) has 2 visited permutations and root(4) has 6. Any map "
                "that preserves exact legality must preserve the visited set's "
                "cardinality, since legality of every subsequent joint is decided "
                "by whether its target permutation is already visited. Hence NO "
                "bijection tau : Q_4 -> Q_0 preserving exact legality can exist "
                "at the state level. 손증명."),
        },
        "what_survives": (
            "Transport is possible only at the SYMBOLIC/quotient level: the two "
            "branches share the E/F alphabet, the |P|-even constraint, the "
            "requirement that the completer targets O*, and Phi=0 (proved "
            "ell-independently in Round 21). The Rh-free language equality is a "
            "statement about those symbolic words, not about states, and this "
            "round's obstruction shows it CANNOT be proved by exhibiting a state "
            "bijection -- a different argument is required. 미완료."),
        "consequence_for_reverse_inclusion": (
            "Round 22 left P4 INTERSECT {E,F}* SUBSET P0 open pending a transport "
            "map. This round shows the intended route is closed: no exact "
            "state-level transport exists. The inclusion remains root-local "
            "exhaustive (verified for lengths 2, 4, 6) with no general proof. 미완료."),
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", a.output)

if __name__ == "__main__":
    main()
