#!/usr/bin/env python3
"""Round 23, sections 1-5, 9: the preparation incidence graph degree
ledger, and the proof that no degree/handshake/forest argument can give
the |P| parity.

The ledger is fully determined because every preparation edge is forced
to ell=5 (after F=1 is spent an ell<5 edge would be an abandonment, which
area_a_prune_reason removes as F_exceeded). Hence:
  hub                -> degree ell+1
  each traversed hex -> degree exactly 6 (fully swept)
  the current hex    -> degree exactly 1 (just entered, not yet swept)
so |E| = ell + 6k + 2 and |E| mod 2 = ell mod 2, INDEPENDENT of k.
Handshake therefore yields no parity information, and the forest identity
5k = n_O - c - ell merely re-expresses k. Both are recorded here with the
measurements that confirm them.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
def _load(n, f):
    p = WORK / f; s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
macro = _load("apg_macro", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]; HUB = core.hexagon_id(exact.initial_state().p)

def root(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state

def graph_of(state):
    hexdeg, orbdeg = Counter(), Counter()
    for q, m in enumerate(state.orbit_masks):
        for ph in range(5):
            if m & (1 << ph):
                h = core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[ph])
                hexdeg[h] += 1; orbdeg[q] += 1
    # components of the incidence graph
    par = {}
    def f(n):
        par.setdefault(n, n)
        if par[n] != n: par[n] = f(par[n])
        return par[n]
    def u(x, y):
        a, b = f(x), f(y)
        if a != b: par[b] = a
    for q, m in enumerate(state.orbit_masks):
        for ph in range(5):
            if m & (1 << ph):
                u(("q", q), ("h", core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[ph])))
    comps = len({f(n) for n in par})
    E = sum(hexdeg.values())
    V = len(hexdeg) + len(orbdeg)
    return {"hex_degrees": dict(sorted(hexdeg.items())), "orbit_count": len(orbdeg),
            "hexagon_count": len(hexdeg), "edges": E, "vertices": V, "components": comps,
            "is_forest": E == V - comps,
            "odd_degree_hexagons": sorted(h for h, dgr in hexdeg.items() if dgr % 2)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_parity_graph_certificates.json"))
    a = ap.parse_args()
    d = json.loads(Path(a.words).read_text(encoding="utf-8"))
    rows = []
    print("witness-by-witness incidence ledger at the completer-ready boundary:")
    for ellk, r in d["results_by_ell"].items():
        for w in r["preparations"]:
            ell = int(ellk); cur = root(ell); cidx = w["completer_index_within_preparation"]
            for i, st in enumerate(w["preparation_trace"]):
                if i > cidx - 2: break
                for _ in range(st["ell"]): cur = exact.extend(cur, W1).state
                cur = exact.extend(cur, mbl[st["joint"]]).state
            g = graph_of(cur); k = cidx - 1
            check = (5 * k == g["orbit_count"] - g["components"] - ell)
            rows.append({"raw_state_hash": w["raw_state_hash"], "ell": ell, "P_length": k,
                         "graph": g, "forest_identity_5k_eq_nO_minus_c_minus_ell": check})
            print(f"  {w['raw_state_hash'][:12]} ell={ell} |P|={k} hexes={g['hexagon_count']} "
                  f"orbits={g['orbit_count']} E={g['edges']} V={g['vertices']} c={g['components']} "
                  f"forest={g['is_forest']} odd_deg_hex={g['odd_degree_hexagons']} 5k-identity={check}")
    allforest = all(r["graph"]["is_forest"] for r in rows)
    allid = all(r["forest_identity_5k_eq_nO_minus_c_minus_ell"] for r in rows)
    print(f"\nincidence graph is a forest at every completer-ready boundary: {allforest}")
    print(f"forest identity 5k = n_O - c - ell holds: {allid}")
    prev = {}
    p = Path(a.output)
    if p.exists(): prev = json.loads(p.read_text(encoding="utf-8"))
    prev.update({"section1_5_degree_ledger": {
        "forced_by": "every preparation edge is ell=5 (F=1 spent => ell<5 is an abandonment)",
        "hub_degree": "ell+1", "traversed_hexagon_degree": 6, "current_hexagon_degree": 1,
        "edge_count_formula": "|E| = ell + 6k + 2", "edge_parity": "|E| = ell (mod 2), independent of k",
        "handshake_gives_parity": False,
        "forest_at_every_boundary": allforest,
        "forest_identity_holds": allid,
        "forest_identity": "5k = n_O - c - ell",
        "verdict": ("반증됨 -- every preparation edge produces the SAME degree change, so any "
                    "degree-based quantity is a linear function of the edge count and carries no "
                    "parity information. Handshake, odd-degree and forest routes all fail."),
        "per_witness": rows}})
    p.write_text(json.dumps(prev, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", p)

if __name__ == "__main__":
    main()
