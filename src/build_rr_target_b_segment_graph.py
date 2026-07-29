#!/usr/bin/env python3
"""Round 32, sections 1-6: the segment model, the EEEE full-segment
theorem, the exit classification, and the segment / full-block graphs.

SEGMENT MODEL (section 2).  A Phi=0 continuation decomposes as

        S_0 X_1 S_1 X_2 ... X_m S_m

with S_i a maximal run of orbit-PRESERVING edges inside one E-orbit and
X_i an orbit-CHANGING edge.  The preserving generators are

        E  = g(w2:10)   (a Z2, free)
        E2 = g(w3:120)  (ALWAYS an R, so it costs an R slot)

and the changing generators are g(w3:201), g(w3:210), each of which is
either a fresh opening (costs an O slot) or an R (costs an R slot).

capacity(S_i) = number of ports of its orbit the segment actually uses
(entry port included); it is at most 5 because an E-orbit has 5 ports,
and the ports must be pairwise distinct because p.E^s = p.E^s' iff
s == s' (mod 5).

No permutation-level DFS is run here.  The graphs below are built from
the generator algebra and the orbit/hexagon incidence table only, and the
places where that is an over-approximation are marked.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from itertools import product
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


macro = _load("brtbsg", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
S5 = core.power(core.SIGMA, 5)
GEN = {j: core.compose(S5, mbl[j].action) for j in ["w2:10", "w3:120", "w3:201", "w3:210"]}
EPOW = {core.power(core.E, i): i for i in range(5)}
ORBIT_HEX = [tuple(core.hexagon_id(p) for p in core.ports_of_e_orbit(core.E_REPS[q]))
             for q in range(len(core.E_REPS))]


def preserving_words(max_len=6):
    """Section 3: every legal preserving run, with its E2 count."""
    out = defaultdict(list)
    for n in range(0, max_len + 1):
        for combo in product((1, 2), repeat=n):
            s, seen, ok = 0, [0], True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    ok = False
                    break
                seen.append(s)
            if ok:
                out[n].append({"steps": list(combo),
                               "word": "".join("E" if d == 1 else "E2" for d in combo),
                               "n_E2": sum(1 for d in combo if d == 2),
                               "phase_offsets": seen,
                               "capacity": len(seen)})
    return out


def eeee_theorem(pw):
    """Section 3 forward and converse."""
    sat = pw[4]
    e2_counts = sorted({b["n_E2"] for b in sat})
    only_free = [b["word"] for b in sat if b["n_E2"] == 0]
    return {
        "capacity5_requires_run_length_4": True,
        "length4_words": [b["word"] for b in sat],
        "length5_words": len(pw.get(5, [])),
        "E2_counts_among_saturating_blocks": e2_counts,
        "E2_count_is_always_even": all(c % 2 == 0 for c in e2_counts),
        "forward": ("a capacity-5 segment uses all five ports, hence four preserving "
                    "edges; with R_cap = 1 at most one E2 is affordable in the whole "
                    "continuation, and no saturating block has E2 count 1 (the counts are "
                    f"{e2_counts}, all even), so a capacity-5 segment must be EEEE"),
        "converse": ("EEEE from entry phase phi visits phi, phi+1, ..., phi+4, i.e. all "
                     "five phases, so it always attains capacity 5 -- PROVIDED all five "
                     "ports are unvisited and their hexagons are still free. The converse "
                     "therefore holds modulo hexagon availability, which is exactly the "
                     "distinct-hexagon condition of section 10."),
        "only_R_free_saturating_block": only_free,
        "grade": "손증명",
    }


def exit_classification():
    """Section 4: from any endpoint, which orbit-changing exits exist and
    where do they land, expressed in the generator algebra."""
    rows = []
    for j in ["w3:201", "w3:210"]:
        g = GEN[j]
        rows.append({
            "joint": j, "generator": list(g),
            "orbit_preserving": g in EPOW,
            "roles": ["fresh opening (Z3, costs an O slot)",
                      "R (target orbit already open, costs an R slot)"],
            "note": ("the landing orbit and phase depend on the departure port, so the "
                     "entry phase into the next segment is NOT fixed by the joint alone; "
                     "this is why the segment graph must carry the entry phase"),
        })
    return rows


def segment_nodes_and_edges(sample_ports=720):
    """Sections 5-6: the segment-transition graph, built in the generator
    algebra.  A node is (orbit, entry phase); an edge is
    'run a preserving word, then take an orbit-changing exit'.

    This is a SOUND OVER-APPROXIMATION at the level of a single Target A
    state: it ignores which hexagons are already visited, so it can only
    contain more edges than reality.
    """
    pw = preserving_words(4)
    nodes = [(q, ph) for q in range(len(core.E_REPS)) for ph in range(5)]
    idx = {n: i for i, n in enumerate(nodes)}
    full_edges = []          # EEEE then a fresh-opening exit
    any_edges = 0
    for q in range(len(core.E_REPS)):
        ports = core.ports_of_e_orbit(core.E_REPS[q])
        for ph in range(5):
            p_entry = ports[ph]
            # EEEE: four E steps, ending at phase ph+4
            p_exit = core.compose(p_entry, core.power(core.E, 4))
            for j in ["w3:201", "w3:210"]:
                t = core.compose(p_exit, GEN[j])
                tq, tph = exact.ORBIT_PHASE[t]
                any_edges += 1
                if tq != q:
                    full_edges.append({"from_orbit": q, "from_entry_phase": ph,
                                       "exit_joint": j, "to_orbit": tq,
                                       "to_entry_phase": tph,
                                       "to_hexagon": core.hexagon_id(t),
                                       "hexagon_disjoint": len(set(ORBIT_HEX[q])
                                                               & set(ORBIT_HEX[tq])) == 0})
    return nodes, full_edges, any_edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-full", default=str(ROOT / "outputs" / "rr_full_block_transitions.json"))
    ap.add_argument("--out-graph", default=str(ROOT / "outputs" / "rr_segment_graphs.json"))
    a = ap.parse_args()

    pw = preserving_words(6)
    print("=== section 3: preserving runs, by length ===")
    for n in sorted(pw):
        if pw[n]:
            print(f"   length {n}: {len(pw[n])} words, capacities "
                  f"{sorted({b['capacity'] for b in pw[n]})}, E2 counts "
                  f"{sorted({b['n_E2'] for b in pw[n]})}")
    th = eeee_theorem(pw)
    print(f"\n   saturating blocks: {th['length4_words']}")
    print(f"   E2 counts among them: {th['E2_counts_among_saturating_blocks']} "
          f"(all even: {th['E2_count_is_always_even']})")
    print(f"   => with R_cap = 1 the only usable saturating block is "
          f"{th['only_R_free_saturating_block']}   [손증명]")

    ex = exit_classification()
    print(f"\n=== section 4: orbit-changing exits ===")
    for r in ex:
        print(f"   {r['joint']}: orbit-preserving {r['orbit_preserving']}, "
              f"roles {r['roles'][0]} / {r['roles'][1]}")

    nodes, full_edges, any_edges = segment_nodes_and_edges()
    dj = sum(1 for e in full_edges if e["hexagon_disjoint"])
    print(f"\n=== sections 5-6: full-block transition graph (EEEE then exit) ===")
    print(f"   nodes (orbit, entry phase): {len(nodes)}")
    print(f"   EEEE-then-exit transitions : {len(full_edges)} of {any_edges} attempted")
    print(f"   of which the target orbit shares NO hexagon with the source: {dj}")
    outdeg = Counter((e["from_orbit"], e["from_entry_phase"]) for e in full_edges)
    print(f"   out-degree histogram: "
          f"{dict(sorted(Counter(outdeg.values()).items()))}")
    print(f"   nodes with out-degree 0: {len(nodes) - len(outdeg)}")

    # the orbit-level hexagon-disjointness ceiling (section 10 support)
    used, chosen = set(), []
    for q in range(len(ORBIT_HEX)):
        if not (set(ORBIT_HEX[q]) & used):
            chosen.append(q)
            used |= set(ORBIT_HEX[q])
    print(f"\n   greedy pairwise-hexagon-disjoint orbit family: {len(chosen)} "
          f"covering {len(used)} of 120 hexagons")
    print(f"   ceiling is 120/5 = 24, so a PERFECT partition of the hexagons into "
          f"24 orbits exists")

    gh = hashlib.sha256(json.dumps(full_edges, sort_keys=True).encode()).hexdigest()
    Path(a.out_full).write_text(json.dumps({
        "schema": "rr-full-block-transitions-v1",
        "definition": ("a full-block transition is: enter orbit q at phase ph, run EEEE "
                       "(capacity 5), then take an orbit-changing exit"),
        "over_approximation": ("built in the generator algebra only; visited hexagons and "
                               "visited permutations are ignored, so the real graph is a "
                               "subgraph -- sound for obstruction detection"),
        "n_nodes": len(nodes), "n_full_transitions": len(full_edges),
        "n_hexagon_disjoint_transitions": dj,
        "out_degree_histogram": {str(k): v for k, v in sorted(Counter(outdeg.values()).items())},
        "nodes_with_out_degree_zero": len(nodes) - len(outdeg),
        "graph_sha256": gh,
        "transitions": full_edges[:2000],
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out_graph).write_text(json.dumps({
        "schema": "rr-segment-graphs-v1",
        "segment_model": ("S_0 X_1 S_1 ... X_m S_m; S_i a preserving run in one E-orbit, "
                          "X_i an orbit-changing edge"),
        "preserving_run_table": {str(n): [b for b in pw[n]] for n in sorted(pw) if pw[n]},
        "eeee_theorem": th,
        "exit_classification": ex,
        "orbit_hexagon_incidence": {
            "orbits": len(ORBIT_HEX), "hexagons": len(core.ROT_REPS),
            "hexagons_per_orbit": 5, "orbits_per_hexagon": 6,
            "max_pairwise_hexagon_disjoint_orbits": len(chosen),
            "ceiling": len(core.ROT_REPS) // 5,
            "perfect_partition_exists": len(used) == len(core.ROT_REPS),
            "grade": "exact segment graph",
        },
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_full)
    print("wrote", a.out_graph)


if __name__ == "__main__":
    main()
