#!/usr/bin/env python3
"""Round 155 -- independent audit of the hand node H.tight.

H.tight, as the final DAG states it (r153/certs/dag_153.json):

    "at an equality row the incidence bound is tight, so the chain is
     hexagon-simple, all 120 hexagons are used, and the c pure circuits
     (complete tau-orbits) must cover the |F| = 4c unused ones"

source: research/RR_L6_PROOF_145_CLAUDE.md section 9, lines 292-300.

This file recomputes every quantity the theorem mentions, from the definitions,
on every cover the repository contains, and checks the SLACK IDENTITY that the
audit turns on:

        2g  =  mu(B)  +  R_int ,        mu(B) >= 0,  R_int >= 0

where mu(B) is the cyclomatic number (first Betti number) of the bipartite
incidence graph B.  Nothing here is imported from the round-14x modules; the
beta construction comes from r154/src/beta_defs154.py, which was rebuilt from
the definitions in round 154.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r154" / "src"))
from beta_defs154 import build, sigma, tau, classes, splice          # noqa: E402


def analyse(W_word, n, label):
    S = splice(W_word, n)
    Wd, IDX = build(n)
    HEX, nh = classes(Wd, sigma)
    ORB, nq = classes(Wd, tau)
    P, comps, dummy = S["P"], S["comps"], S["dummy"]
    G = P - factorial(n) // n
    K = len(comps)
    n_elt = P + 1
    A = nh + 1                          # alpha-cycles: the hexagons + the dummy

    # alpha-cycle id of every element (the dummy is its own alpha-cycle)
    acyc = {}
    for i, (v, l) in enumerate(S["passes"]):
        acyc[i] = HEX[IDX[v]]
    acyc[dummy] = -1

    # R_int and the bipartite incidence graph
    R_int, edges = 0, set()
    for j, c in enumerate(comps):
        cnt = Counter(acyc[x] for x in c)
        R_int += sum(v - 1 for v in cnt.values())
        for a in cnt:
            edges.add((a, j))
    E = len(edges)
    # connectivity of B
    adj = {}
    for a, j in edges:
        adj.setdefault(("a", a), set()).add(("b", j))
        adj.setdefault(("b", j), set()).add(("a", a))
    seen, stack = set(), [next(iter(adj))]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(adj[x] - seen)
    connected = len(seen) == A + K          # every alpha-cycle and component
    mu = E - (A + K) + 1

    # pure clean-E circuits, chain, c, d, g
    etype = S["edge_type"]
    pure = [c for c in comps if dummy not in c
            and all(etype.get(x, ("?", None))[0] == "E" for x in c)]
    cc = len(pure)
    d = K - 1 - cc
    g2 = G + 1 - K                       # = 2g
    nonpure = [c for c in comps if c not in pure]

    # hexagons met by each part
    hex_of_pass = {i: HEX[IDX[v]] for i, (v, l) in enumerate(S["passes"])}
    m_h = Counter(hex_of_pass.values())
    all_hex_used = len(m_h) == nh and min(m_h.values(), default=0) >= 1

    dummycomp = next(c for c in comps if dummy in c)
    chain = [x for x in dummycomp if x != dummy]
    chain_hexes = {hex_of_pass[x] for x in chain}
    chain_simple = len(chain_hexes) == len(chain)
    F = sorted(set(range(nh)) - chain_hexes)
    circuit_hexes = set()
    circuit_orbits = set()
    for c in pure:
        for x in c:
            circuit_hexes.add(hex_of_pass[x])
            circuit_orbits.add(ORB[IDX[S["passes"][x][0]]])

    return dict(
        label=label, n=n, P=P, G=G, K=K, n_elt=n_elt, A=A,
        alpha_cycles_are_hexagons_plus_dummy=(A == nh + 1),
        R_int=R_int, E=E, mu=mu, B_connected=connected,
        identity_n_elt_eq_E_plus_R_int=(n_elt == E + R_int),
        two_g=g2, g=g2 // 2, g_is_even=(g2 % 2 == 0),
        slack_identity_2g_eq_mu_plus_R_int=(g2 == mu + R_int),
        c_pure_circuits=cc, d=d,
        pure_circuit_lengths=sorted({len(c) for c in pure}),
        pure_circuits_are_whole_orbits=all(
            len({ORB[IDX[S["passes"][x][0]]] for x in c}) == 1 and len(c) == n - 1
            for c in pure),
        circuit_orbits_distinct=(len(circuit_orbits) == cc),
        nonpure_components=len(nonpure),
        nonpure_is_exactly_the_dummy_component=(len(nonpure) == 1
                                                and nonpure[0] is dummycomp),
        every_hexagon_has_a_pass=all_hex_used,
        min_m_h=min(m_h.values()) if m_h else 0,
        chain_ports=len(chain), chain_hexagons=len(chain_hexes),
        chain_hexagon_simple=chain_simple,
        # the general form is |F| = (n-1)c - G; at c = G that is (n-2)c,
        # which is the "4c" of the n = 6 statement
        F_size=len(F), n_minus_2_times_c=(n - 2) * cc,
        n_minus_1_c_minus_G=(n - 1) * cc - G,
        F_equals_n_minus_2_times_c=(len(F) == (n - 2) * cc),
        F_equals_n_minus_1_c_minus_G=(len(F) == (n - 1) * cc - G),
        c_equals_G=(cc == G),
        F_covered_by_circuit_hexagons=set(F) <= circuit_hexes,
        circuit_hexagons=len(circuit_hexes),
        required_120_plus_G_minus_5c=(factorial(n) // n) + G - (n - 1) * cc,
        chain_ports_equals_required=(len(chain) ==
                                     (factorial(n) // n) + G - (n - 1) * cc))


def main():
    covers = []
    covers.append(((ROOT / "data" / "verified_872_witness.txt").read_text().strip(),
                   6, "n6_872_witness"))
    sys.path.insert(0, str(ROOT))
    try:
        from data import known_witnesses as KW
        for nm in dir(KW):
            if nm.startswith("_"):
                continue
            v = getattr(KW, nm)
            if isinstance(v, str) and len(v) > 10 and len(set(v)) in (4, 5, 6):
                al = sorted(set(v))
                m = dict(zip(al, "123456"[:len(al)]))
                covers.append(("".join(m[ch] for ch in v), len(al), f"known:{nm}"))
    except Exception as exc:                                    # noqa: BLE001
        print("known_witnesses:", exc)
    p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
    if p5.exists():
        for i, rec in enumerate(json.loads(p5.read_text())):
            w = rec["word"] if isinstance(rec, dict) else rec
            al = sorted(set(w))
            if len(al) != 5:
                continue
            m = dict(zip(al, "12345"))
            covers.append(("".join(m[ch] for ch in w), 5, f"n5_minimum_{i}"))

    rows, bad = [], []
    for w, n, label in covers:
        try:
            r = analyse(w, n, label)
        except Exception as exc:                                # noqa: BLE001
            bad.append(dict(label=label, error=str(exc)))
            continue
        rows.append(r)
    out = dict(covers=rows, errors=bad)
    universal = ["alpha_cycles_are_hexagons_plus_dummy", "B_connected",
                 "identity_n_elt_eq_E_plus_R_int", "g_is_even",
                 "slack_identity_2g_eq_mu_plus_R_int",
                 "pure_circuits_are_whole_orbits", "circuit_orbits_distinct",
                 "every_hexagon_has_a_pass",
                 "nonpure_is_exactly_the_dummy_component"]
    out["universal_checks"] = {k: all(r[k] for r in rows) for k in universal}
    g0 = [r for r in rows if r["g"] == 0 and r["d"] == 0]
    out["g0_d0_covers"] = len(g0)
    out["g0_d0_conclusions"] = {
        k: all(r[k] for r in g0) for k in
        ("chain_hexagon_simple", "F_equals_n_minus_2_times_c",
         "F_equals_n_minus_1_c_minus_G", "c_equals_G",
         "F_covered_by_circuit_hexagons", "chain_ports_equals_required")}
    out["ok"] = (all(out["universal_checks"].values())
                 and all(out["g0_d0_conclusions"].values()) and not bad)
    (ROOT / "r155" / "certs" / "tight_real_covers_155.json").write_text(
        json.dumps(out, indent=1) + "\n")
    for r in rows:
        print(f"  {r['label']:22s} n={r['n']} P={r['P']:4d} G={r['G']:3d} "
              f"K={r['K']:3d} R_int={r['R_int']:3d} mu={r['mu']:3d} "
              f"2g={r['two_g']:3d} c={r['c_pure_circuits']:3d} d={r['d']:2d} | "
              f"2g=mu+R_int {r['slack_identity_2g_eq_mu_plus_R_int']} | "
              f"chain {r['chain_ports']}p/{r['chain_hexagons']}h simple="
              f"{r['chain_hexagon_simple']} |F|={r['F_size']} "
              f"(n-2)c={r['n_minus_2_times_c']} "
              f"covered={r['F_covered_by_circuit_hexagons']}")
    print()
    print("universal:", json.dumps(out["universal_checks"]))
    print(f"g=0,d=0 covers: {out['g0_d0_covers']}  ->",
          json.dumps(out["g0_d0_conclusions"]))
    print("errors:", bad)
    print("ok:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
