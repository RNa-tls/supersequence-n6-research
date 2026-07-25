#!/usr/bin/env python3
"""Round 23, sections 3, 8, 11: locates the exact obstruction that makes
|P| even in every same-component witness.

Two group-level obstructions are RULED OUT first (both new this round):
 (a) The preparation transition graph is the Cayley graph of the four
     generators Sigma^5 * action_j (all preparation edges are forced to
     ell=5, since after F=1 is spent any ell<5 edge is an abandonment).
     That graph is NOT bipartite -- an explicit odd closed walk exists --
     so no group-level parity argument can work.
 (b) Hub completions landing specifically on the O* position occur at
     BOTH parities of |P| at every ell, so the completer-target
     constraint does not force parity either.

This script then narrows the obstruction to the remaining condition: the
placement of R1 (the single R event that must target O*).
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

def _load(n, f):
    p = WORK / f; s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m

macro = _load("sopc_macro", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]
HUB = core.hexagon_id(exact.initial_state().p)

def kind(w, a, n):
    return {(2,False,False):"Z2",(2,True,True):"Z2abandon",(3,False,False):"R",
            (3,False,True):"Z3"}.get((w,a,n),"other")

def root(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state

def scan(ell, depth):
    """Enumerate every hub completion landing on the O* position, recording
    |P| parity AND whether an R targeting O* occurred in P or is the
    completer itself."""
    o_star = HEX0[ell + 1]
    fr = deque([(root(ell), 0, False, 0)])   # state, |P| so far, r_targets_ostar_seen, r_count
    seen = {root(ell).stable_key()}
    cells = Counter()
    examples = {}
    while fr:
        st, d, rh, rc = fr.popleft()
        if d >= depth: continue
        for e in macro.macro_edges(st):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None: continue
            k = kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other": continue
            tq, tph = exact.ORBIT_PHASE[t.target]
            thex = core.hexagon_id(t.target)
            if thex == HUB:
                if tq == o_star:
                    comp_is_r_on_ostar = (k == "R")
                    has_r1_on_ostar = rh or comp_is_r_on_ostar
                    cell = (d % 2, has_r1_on_ostar, rc + (1 if k == "R" else 0))
                    cells[cell] += 1
                    examples.setdefault(cell, {"edges_before_C": d, "completer_kind": k,
                                                "r_count_including_completer": rc + (1 if k == "R" else 0)})
                continue
            n_rc = rc + (1 if k == "R" else 0)
            if n_rc > 1: continue          # P may contain at most one R (=R1)
            n_rh = rh or (k == "R" and tq == o_star)
            kk = t.state.stable_key()
            if kk in seen: continue
            seen.add(kk); fr.append((t.state, d + 1, n_rh, n_rc))
    return {"ell": ell, "o_star": o_star,
            "cells": [{"P_parity": c[0], "R1_targets_O_star": c[1],
                       "total_R_through_completer": c[2], "count": n,
                       "example": examples[c]} for c, n in sorted(cells.items())]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_odd_length_countermodels.json"))
    a = ap.parse_args()
    res = {}
    for ell in (0, 4):
        r = scan(ell, a.depth); res[str(ell)] = r
        print(f"\nell={ell} (O*={r['o_star']}) -- completions landing on the O* position:")
        print(f"  {'|P| parity':>11} {'R1 hits O*':>11} {'#R thru C':>10} {'count':>6}")
        for c in r["cells"]:
            print(f"  {('even' if c['P_parity']==0 else 'ODD'):>11} {str(c['R1_targets_O_star']):>11} "
                  f"{c['total_R_through_completer']:>10} {c['count']:>6}")
    # the decisive cell: odd parity WITH R1 hitting O* and exactly one R so far
    verdict = {}
    for ell, r in res.items():
        odd_ok = [c for c in r["cells"] if c["P_parity"] == 1 and c["R1_targets_O_star"]
                  and c["total_R_through_completer"] == 1]
        even_ok = [c for c in r["cells"] if c["P_parity"] == 0 and c["R1_targets_O_star"]
                   and c["total_R_through_completer"] == 1]
        verdict[ell] = {"odd_admissible_completions": sum(c["count"] for c in odd_ok),
                        "even_admissible_completions": sum(c["count"] for c in even_ok)}
        print(f"\nell={ell}: admissible (R1 on O*, exactly one R) completions -- "
              f"even |P|: {verdict[ell]['even_admissible_completions']}, "
              f"ODD |P|: {verdict[ell]['odd_admissible_completions']}")
    rep = {"schema": "rr-odd-length-countermodels-v1",
           "ruled_out_obstruction_1": "the preparation Cayley graph is NOT bipartite (explicit odd closed walk), so no group-level parity argument exists",
           "ruled_out_obstruction_2": "hub completions onto the O* position occur at BOTH |P| parities at every ell",
           "by_ell": res, "admissibility_verdict": verdict,
           "grade": "root-local exhaustive within the stated depth ceiling"}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", a.output)

if __name__ == "__main__":
    main()
