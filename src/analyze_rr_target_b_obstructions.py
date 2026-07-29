#!/usr/bin/env python3
"""Round 30, Part A sections 4-7, 9-10: static obstructions for Target B.

The decisive one is a COUNTING obstruction, not a graph-search one, and it
is a hand proof.  Setting for a Target B continuation from a Target A
state with B = TARGET_P - P remaining pass starts:

  (1) every future macro-edge has ell = 5                     [Round 29]
  (2) an ell=5 macro-edge is right-multiplication by one of
        g(w2:10) = E,  g(w3:120) = E^2,  g(w3:201), g(w3:210) [Round 26]
  (3) E and E^2 PRESERVE the E-orbit, so w2:10 and w3:120 can never open a
      new orbit.  w2:10 (weight 2) is then a Z2; w3:120 (weight 3) is then
      always an R.
  (4) w3:201 / w3:210 leave the orbit, so each is either a fresh opening
      (Z3, costing O += 1) or an R.
  (5) at most 4 CONSECUTIVE orbit-preserving edges.  A run of them moves
      the entry port p -> p.E^{s_1} -> p.E^{s_2} -> ... with partial sums
      of 1's and 2's; the ports must be distinct, p.E^s = p.E^s' iff
      s == s' (mod 5), so at most 5 distinct residues and hence at most 4
      edges.
  (6) therefore, writing m for the number of orbit-CHANGING edges,
        B = (orbit-preserving) + m <= 4(m+1) + m = 5m + 4.
  (7) m is bounded by the budgets: each orbit-changing edge is a fresh
      opening (costing one of the TARGET_O - O remaining orbit slots) or an
      R (costing one of the n_limit - N remaining R slots).

Combining (6) and (7) gives  B <= 5*(O_capacity + R_capacity) + 4, which
is checked below against the actual B.  This uses NO search.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
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


macro = _load("artbo", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]


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


def consecutive_bound():
    """Step (5), verified as a finite fact about <E>."""
    # partial sums of steps in {1,2} mod 5, starting from 0, all distinct
    best = 0
    from itertools import product
    for n in range(1, 8):
        ok = False
        for combo in product((1, 2), repeat=n):
            s, seen, good = 0, {0}, True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    good = False
                    break
                seen.add(s)
            if good:
                ok = True
                break
        if ok:
            best = n
        else:
            break
    return best


def budget_obstruction(st, max_run):
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(macro.AREA_A.n_limit - st.Ndef, 0)
    m_max = O_cap + R_cap
    B_max = (max_run + 1) * m_max + max_run
    return {
        "B_remaining_pass_starts": B,
        "O_capacity": O_cap, "R_capacity_under_area_a": R_cap,
        "m_max_orbit_changing_edges": m_max,
        "max_consecutive_orbit_preserving": max_run,
        "B_upper_bound": B_max,
        "contradiction": B > B_max,
        "margin": B - B_max,
        "formula": "B <= (max_run+1)*m + max_run with m <= O_capacity + R_capacity",
    }


def degree_and_scc(graph_payload):
    """Sections 4/6, from the stored over-approximated graph summary."""
    out_hist = {int(k): v for k, v in graph_payload["port_out_degree_histogram"].items()}
    in_hist = {int(k): v for k, v in graph_payload["port_in_degree_histogram"].items()}
    return {
        "ports_with_out_degree_0": out_hist.get(0, 0),
        "ports_with_in_degree_0": in_hist.get(0, 0),
        "out_degree_histogram": out_hist,
        "in_degree_histogram": in_hist,
        "note": ("out-degree 0 ports must be the sink; in-degree 0 ports must be the "
                 "source. These counts are over PORTS, not hexagons -- a hexagon with "
                 "some dead ports is still usable through another port, so this is NOT "
                 "by itself an obstruction."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--graphs", default=str(ROOT / "outputs" / "rr_target_b_hexagon_graphs.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_target_b_obstruction_certificates.json"))
    a = ap.parse_args()

    max_run = consecutive_bound()
    print(f"=== step (5): longest run of orbit-preserving edges ===")
    print(f"   partial sums of 1's and 2's mod 5, all distinct: at most {max_run} edges")
    assert max_run == 4

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    graphs = json.loads(Path(a.graphs).read_text(encoding="utf-8"))["graphs"]

    print(f"\n=== the budget obstruction ===")
    print("  #   B    O_cap  R_cap  m_max   B_max   contradiction  margin")
    certs = []
    for i, w in enumerate(wits):
        st = replay(w)
        b = budget_obstruction(st, max_run)
        g = degree_and_scc(graphs[i])
        verdict = "BUDGET_OBSTRUCTION" if b["contradiction"] else "NO_STATIC_OBSTRUCTION"
        certs.append({"witness_index": i, "budget": b, "degrees": g, "verdict": verdict})
        print(f"  {i}  {b['B_remaining_pass_starts']:>3}   {b['O_capacity']:>3}    "
              f"{b['R_capacity_under_area_a']:>2}     {b['m_max_orbit_changing_edges']:>3}"
              f"    {b['B_upper_bound']:>4}      {str(b['contradiction']):<6}      "
              f"{b['margin']:>3}")

    allcon = all(c["budget"]["contradiction"] for c in certs)
    print(f"\n  every Target A state carries the obstruction: {allcon}")

    print(f"\n=== port degree summary (over-approximated graph) ===")
    for i, c in enumerate(certs):
        print(f"  w{i}: out-deg 0 ports {c['degrees']['ports_with_out_degree_0']}, "
              f"in-deg 0 ports {c['degrees']['ports_with_in_degree_0']}")

    print(f"\n=== section 10 verdicts ===")
    for c in certs:
        print(f"  w{c['witness_index']}: {c['verdict']}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-target-b-obstruction-certificates-v1",
        "theorem": {
            "statement": ("from any Target A state, a Target B continuation requires "
                          "B <= 5*(O_capacity + R_capacity) + 4; all six states violate it"),
            "grade": "손증명 (exact counting obstruction)",
            "steps": [
                "at Phi=0 every future macro-edge has ell=5 (Round 29)",
                "an ell=5 macro-edge is right-multiplication by g_j (Round 26)",
                "E and E^2 preserve the E-orbit, so w2:10 and w3:120 never open a new "
                "orbit; w3:120 (weight 3) is therefore always an R",
                "w3:201/w3:210 leave the orbit, so each is a fresh opening (O += 1) or an R",
                "at most 4 consecutive orbit-preserving edges, because the entry ports "
                "p.E^s must be distinct and there are only 5 residues mod 5",
                "hence B <= 4*(m+1) + m = 5m + 4 with m = #orbit-changing edges",
                "m <= (TARGET_O - O) + (n_limit - N)",
            ],
        },
        "max_consecutive_orbit_preserving": max_run,
        "certificates": certs,
        "all_states_obstructed": allcon,
        "consequence": (
            "Target B is IMPOSSIBLE from all six Target A states. No DFS was run and none "
            "is needed: the obstruction is a counting argument, so the depth-107/110 "
            "search is not merely deferred but unnecessary."
            if allcon else
            "no budget obstruction; the graph-theoretic tests remain the route"),
        "not_claimed": (
            "this says nothing about Target C, about NR6, or about whether OTHER "
            "same-component R2 boundaries (short-preparation ones) admit continuations -- "
            "the argument uses only B, O and N at the given state"),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
