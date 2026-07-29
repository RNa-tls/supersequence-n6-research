#!/usr/bin/env python3
"""Round 30, Part A sections 1-3, 8, 11: the residual hexagon / port graph.

MODEL (section 2), stated exactly before the word "Hamiltonian" is used.

At Phi = 0 every future macro-edge has rotation run ell = 5 (Round 29).
Such an edge, entered at permutation p, rotates through p.Sigma, ...,
p.Sigma^5 -- completing p's hexagon -- and then fires a joint from
p.Sigma^5, landing on

        p . Sigma^5 . a_j  =  p . g_j ,        g_j = Sigma^5 o a_j

with the four composite generators computed in Round 26:

        g(w2:10)  = E        g(w3:120) = E^2
        g(w3:201), g(w3:210) not in <E>.

So the natural object is the PORT graph on permutations: p -> p.g_j, out
degree 4, entirely STATIC.  The hexagon-level graph H -> H' is the image
of that, and it is NOT static: which H' are reachable depends on which
port of H the walk entered by.  That is exactly why section 8 asks for
the lift, and why "hexagon-level Hamiltonian path" alone would admit
false positives.

The dynamic part is only the vertex-deletion: a macro-edge is legal only
if the target hexagon is entirely unvisited (its 5 rotations must not
collide).  So the correct model is

    a static digraph on ports, plus vertex deletion at the hexagon level,

and a Target B continuation is a self-avoiding path visiting exactly one
port of each remaining hexagon.  We build a SAFE OVER-APPROXIMATION: an
edge is kept unless it is statically impossible.  Any obstruction found
in an over-approximation is a genuine obstruction.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("brtbhg", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
JOINTS = ["w2:10", "w3:120", "w3:201", "w3:210"]


def generators():
    S5 = core.power(core.SIGMA, 5)
    epow = {core.power(core.E, i): i for i in range(5)}
    out = {}
    for j in JOINTS:
        g = core.compose(S5, mbl[j].action)
        out[j] = {"g": g, "E_power": epow.get(g), "orbit_preserving": g in epow,
                  "weight": mbl[j].weight}
    return out


def replay(w):
    st = exact.initial_state()
    for _ in range(w["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lab in w["literal_full_word"]:
        e, l = lab.split(";")
        for _ in range(int(e.split("^")[1])):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[l]).state
    return st


def build_graph(st, gens):
    """Safe over-approximation of the residual port graph."""
    untouched = [h for h in range(len(core.ROT_REPS)) if st.hex_masks[h] == 0]
    untouched_set = set(untouched)
    open_orbits = {q for q in range(len(core.E_REPS)) if st.orbit_masks[q] != 0}
    # ports = every permutation lying in an untouched hexagon, plus the current
    # endpoint (the entry port of the partial hexagon the walk stands in)
    ports = []
    for h in untouched:
        rep = core.ROT_REPS[h]
        q = rep
        for _ in range(6):
            ports.append(q)
            q = core.word_after(q, core.SIGMA)
    start = st.p
    idx = {p: i for i, p in enumerate(ports)}
    edges = defaultdict(list)
    dropped = Counter()

    def succs(p):
        out = []
        for j in JOINTS:
            t = core.compose(p, gens[j]["g"])
            th = core.hexagon_id(t)
            if th not in untouched_set:
                dropped["target hexagon not untouched"] += 1
                continue
            if gens[j]["weight"] == 3 and gens[j]["orbit_preserving"]:
                # w3:120 is always an R (orbit preserving, weight 3, never new)
                dropped["w3:120 is always an R"] += 1
                continue
            if gens[j]["weight"] == 3 and not gens[j]["orbit_preserving"]:
                tq, _ = exact.ORBIT_PHASE[t]
                if tq in open_orbits:
                    # cannot be a fresh opening now, and orbits only ever open,
                    # so it can never be one: it would be an R
                    dropped["orbit already open at start -> would be an R"] += 1
                    continue
            out.append((j, t, th))
        return out

    for p in ports:
        edges[p] = succs(p)
    start_edges = succs(start)
    outdeg = Counter(len(v) for v in edges.values())
    indeg = Counter()
    for p, vs in edges.items():
        for _, t, _ in vs:
            indeg[t] += 1
    indeg_hist = Counter()
    for p in ports:
        indeg_hist[indeg.get(p, 0)] += 1
    payload = {
        "untouched_hexagons": len(untouched),
        "n_ports": len(ports),
        "n_edges": sum(len(v) for v in edges.values()),
        "start_permutation": list(start),
        "start_hexagon": core.hexagon_id(start),
        "start_out_degree": len(start_edges),
        "start_edges": [{"joint": j, "target_hexagon": th} for j, _, th in start_edges],
        "port_out_degree_histogram": {str(k): v for k, v in sorted(outdeg.items())},
        "port_in_degree_histogram": {str(k): v for k, v in sorted(indeg_hist.items())},
        "dropped_edge_reasons": dict(dropped),
        "open_orbits_at_start": len(open_orbits),
    }
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    payload["graph_sha256"] = h
    return payload, edges, ports, start, start_edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_target_b_hexagon_graphs.json"))
    ap.add_argument("--ports", default=str(ROOT / "outputs" / "rr_target_b_port_graphs.json"))
    a = ap.parse_args()

    gens = generators()
    print("=== composite generators (Round 26, reused) ===")
    for j, g in gens.items():
        print(f"   {j:<8} {g['g']}  E^{g['E_power']}  weight {g['weight']}  "
              f"orbit-preserving {g['orbit_preserving']}")

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    graphs, ports_out = [], []
    for i, w in enumerate(wits):
        st = replay(w)
        payload, edges, ports, start, sedges = build_graph(st, gens)
        payload["witness_index"] = i
        graphs.append(payload)
        ports_out.append({"witness_index": i, "n_ports": payload["n_ports"],
                          "n_edges": payload["n_edges"],
                          "out_degree_histogram": payload["port_out_degree_histogram"],
                          "in_degree_histogram": payload["port_in_degree_histogram"],
                          "graph_sha256": payload["graph_sha256"]})
        print(f"\n w{i}: untouched hexagons {payload['untouched_hexagons']}, "
              f"ports {payload['n_ports']}, edges {payload['n_edges']}")
        print(f"     start hexagon {payload['start_hexagon']}, out-degree "
              f"{payload['start_out_degree']}: "
              f"{[e['joint'] for e in payload['start_edges']]}")
        print(f"     port out-degree histogram {payload['port_out_degree_histogram']}")
        print(f"     dropped: {payload['dropped_edge_reasons']}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-target-b-hexagon-graphs-v1",
        "model": {
            "port_graph": "static digraph p -> p.g_j on permutations",
            "hexagon_graph": ("the image of the port graph; NOT static -- reachable H' "
                              "depends on which port of H was entered, which is why the "
                              "port lift is required before calling anything Hamiltonian"),
            "dynamics": "vertex deletion at hexagon level (a hexagon is used exactly once)",
            "approximation": ("safe OVER-approximation: an edge is dropped only when it is "
                              "statically impossible, so any obstruction found is genuine"),
        },
        "generators": {k: {**v, "g": list(v["g"])} for k, v in gens.items()},
        "graphs": graphs,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.ports).write_text(json.dumps({
        "schema": "rr-target-b-port-graphs-v1",
        "note": ("vertices are (hexagon, entry port) = permutations lying in untouched "
                 "hexagons; a Target B continuation is a self-avoiding path using exactly "
                 "one port per remaining hexagon"),
        "per_witness": ports_out,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("\nwrote", a.output)
    print("wrote", a.ports)


if __name__ == "__main__":
    main()
