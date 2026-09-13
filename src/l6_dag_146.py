#!/usr/bin/env python3
"""Round 146 — the explicit proof dependency DAG for  L6 = 872.

Every node carries a kind (definition / hand lemma / exhaustive computation /
certificate / witness) and an audit status:

  PURE_HAND_PROOF          proved on paper here, single implementation checking it
  EXHAUSTIVE_COMPUTATION   finite and uncapped
  INDEPENDENTLY_DUPLICATED proved AND checked by >= 2 implementations that do not
                           share a representation
  TEST_ONLY                supported by sampling only
  EXTERNAL_DEPENDENCY      relies on something outside this repository
  UNAUDITED                nobody has checked it

The script computes the transitive closure of dependencies of the final node and
reports any TEST_ONLY / EXTERNAL_DEPENDENCY / UNAUDITED node on a path to it.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

N = {}


def node(nid, kind, status, what, deps=(), where=""):
    N[nid] = dict(kind=kind, status=status, what=what, deps=list(deps), where=where)


# ------------------------------------------------------------------ definitions
node("D.words", "definition", "PURE_HAND_PROOF",
     "cover, window, first occurrence, trimming",
     where="src/l6_cleanroom_146.py::invariants")
node("D.geom", "definition", "INDEPENDENTLY_DUPLICATED",
     "sigma, tau, hexagon, orbit, omega; built algebraically (python), by string "
     "overlap scanning (C) and by canonical rotation strings (clean room)",
     where="src/verify_f2_structure_126.py::setup, src/l6_chain_capacity_144.c::geometry, "
           "src/l6_cleanroom_146.py")
node("D.pass", "definition", "INDEPENDENTLY_DUPLICATED",
     "pass/port/joint/weight; P,G,O,k,S,H", ["D.words", "D.geom"],
     "src/l6_splicing_145.py, src/l6_cleanroom_146.py")
node("D.beta", "definition", "INDEPENDENTLY_DUPLICATED",
     "nu, alpha, T, beta, K, R_int, c, d, g, z, Z, D2, Qs, B*, sigma-sharing",
     ["D.pass"], "src/l6_splicing_145.py, src/l6_incidence_graph_146.py")
node("D.models", "definition", "PURE_HAND_PROOF",
     "piece / split-chain / merged-chain models and their budgets", ["D.beta"],
     "research/RR_L6_PROOF_145_CLAUDE.md 5-7")

# ------------------------------------------------------------------ hand lemmas
node("L.fixedrep", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "every cover has a fixed representative, no longer, with all selected "
     "connectors shortest and all repeats hidden connector windows; rigidity of "
     "the equality case",
     ["D.words"], "src/l6_fixed_representative_145.py, src/l6_rigidity_146.py")
node("L.FO", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "L = 844 + G + S + H", ["D.pass", "L.fixedrep"],
     "src/l6_master_identity_144.py, src/l6_cleanroom_146.py")
node("L.arcs", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "the arcs of a hexagon partition it; sum (m_h - 1) = G", ["D.pass"],
     "src/l6_splicing_145.py Lemma A, src/l6_cleanroom_146.py")
node("L.nu", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "nu is a permutation whose cycles are the hexagons", ["L.arcs"],
     "src/l6_splicing_145.py Lemma B")
node("L.splice", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "the joint source equals end(v_nu(i)); reassignment changes no source "
     "window, target, gap, spelling or hidden window", ["L.nu", "L.fixedrep"],
     "src/l6_splicing_145.py Lemma C, src/l6_envelope_146.py::splice_string_audit")
node("L.betaperm", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "beta = T o alpha^{-1} is a permutation and beta(nu(i)) = i+1", ["D.beta"],
     "src/l6_splicing_145.py Lemma D, src/l6_incidence_graph_146.py")
node("L.incidence", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "K + R_int <= G+1 and K = G+1 mod 2", ["L.betaperm", "L.arcs"],
     "src/l6_incidence_144.py, src/l6_incidence_graph_146.py")
node("L.tree", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "the inequality is tight iff the bipartite incidence graph is a tree",
     ["L.incidence"], "src/l6_incidence_graph_146.py::graph_audit")
node("L.allhex", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "every hexagon carries a pass (so all 120 are used), unconditionally",
     ["D.pass"], "src/l6_incidence_graph_146.py, src/l6_cleanroom_146.py")
node("L.pure", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "a pure clean-E circuit is a whole orbit of length n-1 and that orbit "
     "occurs nowhere else", ["D.beta"], "src/l6_splicing_145.py Lemma E")
node("L.blocks", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "blocks = S + 1 + D2", ["D.beta"], "src/l6_splicing_145.py Lemma F")
node("L.master", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "B* = S+1+D2-O+c and hence MASTER  L = 867 + k + Z + H + B*, all terms >= 0",
     ["L.FO", "L.blocks", "L.samehex"],
     "src/l6_bookkeeping_144.py, src/l6_cleanroom_146.py")
node("L.samehex", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "D2 + Qs <= R_int, hence D2+Qs <= 2g and Z >= Qs >= 0",
     ["L.betaperm", "L.fixedrep"],
     "src/l6_same_hex_145.py, src/l6_envelope_146.py")
node("L.extract", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "chain budgets: sum P_i, sum D_i, sum tok_i = B* - sigma, sigma >= 0 "
     "(= 0 for one chain), hex repeats <= R_int, chains <= d+1+h",
     ["L.pure", "L.blocks"], "src/l6_extraction_145.py, src/l6_envelope_146.py")
node("L.envelope", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "a <= D2, bb <= Qs, e <= Z-Qs, a+bb+e <= R_int <= 2g",
     ["L.samehex", "L.extract"], "src/l6_envelope_146.py::envelope_audit")
node("L.catalogue", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "the shortest connectors out of end(v) are exactly E, E^2, 201, 210, "
     "E-sigma, sigma-E, sigma, sigma^2 and the heavy ones", ["D.geom"],
     "src/l6_marked_capacity_144.py::catalogue_check, src/l6_cleanroom_146.py")
node("L.S6", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "the left S6 action commutes with every connector map and is transitive on "
     "ports, so fixing the start port is a proved reduction", ["D.geom"],
     "src/l6_marked_capacity_144.py::s6_symmetry")
node("L.companion", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "orb(v) and orb(sigma v) share exactly the hexagons h(v), h(Ev)",
     ["D.geom"], "src/l6_marked_capacity_144.py::companion_lemma")
node("L.degree", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "at R_int = 0 with c = G the tree forces P_1 = 120 - 4c",
     ["L.tree", "L.pure", "L.allhex"], "src/l6_incidence_graph_146.py")
node("L.cover", "hand lemma", "INDEPENDENTLY_DUPLICATED",
     "the c pure circuits must cover the 4c hexagons the chain does not use "
     "(acyclicity NOT used, so the test is a weaker necessary condition)",
     ["L.degree", "L.allhex", "L.pure"],
     "src/l6_incidence_graph_146.py, src/l6_circuit_coexist_144.py")

# ------------------------------------------------- exhaustive computations
node("E.piecetab", "exhaustive computation", "EXHAUSTIVE_COMPUTATION",
     "piece capacity table: 55 cells, 0 capped, 3.29e10 nodes, two "
     "implementations agreeing to the node count",
     ["L.catalogue", "L.S6", "L.companion"],
     "outputs/rr_l6_marked_capacity_table_144.json")
node("E.chaintab", "exhaustive computation", "REFUTED",
     "chain capacity table: 1501 cells, 0 capped, 6.49e10 nodes -- REFUTED in "
     "round 146: the pruning table it was computed with was not a valid upper "
     "bound (per-split lines under a combined-budget key, loader takes the "
     "minimum), so recorded capacities are BELOW the truth (0|0|0|0|9: 45 < 50; "
     "0|0|0|0|10: 40 < 55; 87 of the 377 cells with b=0, d<=1). "
     "See research/ERRATA_146_CHAIN_UB.md",
     ["L.catalogue", "L.S6"], "outputs/rr_l6_chain_capacity_144.json")
node("E.heavytab", "exhaustive computation", "REFUTED",
     "heavy-merged chain table: 42 cells, 0 capped -- same defect as "
     "E.chaintab (computed with the same invalid pruning table)",
     ["L.catalogue", "L.S6"], "outputs/rr_l6_heavychain_capacity_144.json")
node("E.rows", "exhaustive computation", "REFUTED",
     "every coordinate row with t <= 4 is strict except two at t = 4 -- "
     "REFUTED as stated: 61 of the 353 rows at t=3 and 552 of the 1156 at t=4 "
     "are closed ONLY by a bound read off the refuted chain tables. "
     "The t=2 layer survives: all 85 rows are closed by the piece model alone",
     ["L.master", "L.envelope", "L.extract", "D.models",
      "E.piecetab", "E.chaintab", "E.heavytab"],
     "src/l6_rows_final_144.py, outputs/rr_l6_rows_final_144.json")
node("E.q1", "exhaustive computation", "EXHAUSTIVE_COMPUTATION",
     "Q1 equality witnesses: exactly 2 up to left S6 (four routes, one with no "
     "bound table, 900,166,560 nodes uncapped, identical SHA-256)",
     ["E.rows", "L.S6"], "outputs/witness_144/wit_Q1*.jsonl")
node("E.q2", "exhaustive computation", "EXHAUSTIVE_COMPUTATION",
     "Q2 equality witnesses: exactly 1 up to left S6 (three routes)",
     ["E.rows", "L.S6"], "outputs/witness_144/wit_Q2*.jsonl")
node("E.coexist", "exhaustive computation", "EXHAUSTIVE_COMPUTATION",
     "no witness admits the forced pure circuits: three independent procedures "
     "(recursive DFS over frozensets, subset enumeration, and round 146's "
     "layered BFS over bitmasks with no waste bookkeeping).  The third carries "
     "its own positive control -- the minimum number of tau-orbits that DOES "
     "cover F is 8 on all three witnesses, margin 2/2/1 -- so it said NO from "
     "a state in which it can say YES.  NOTE: this node survives round 146 but "
     "hangs off E.q1/E.q2, which hang off the refuted E.rows, so it closes "
     "nothing on its own",
     ["E.q1", "E.q2", "L.cover"],
     "src/l6_circuit_coexist_144.py, src/l6_coexist_check3_144.py, "
     "src/l6_cover_bfs_146.py")
node("E.n3rigid", "exhaustive computation", "EXHAUSTIVE_COMPUTATION",
     "rigidity of |Phi(W)|=|W| exhaustively over all words on 3 letters up to "
     "length 13: 2,391,471 words, 9,732 covers, 54 equal-length, 0 counterexamples",
     ["L.fixedrep"], "src/l6_rigidity_146.py")

# --------------------------------------------------------------- witness
node("W.872", "witness", "EXHAUSTIVE_COMPUTATION",
     "data/verified_872_witness.txt is a cover of length 872 (checked in repo)",
     [], "src/l6_proof_145.py::step1")

# --------------------------------------------------------------- conclusions
node("C.lower", "conclusion", "REFUTED",
     "L6 >= 872 -- RETRACTED in round 146; it rests on E.rows, which rests on "
     "the refuted chain tables",
     ["L.fixedrep", "L.master", "E.rows", "E.coexist", "E.n3rigid", "L.splice"])
node("E.rows870", "exhaustive computation", "EXHAUSTIVE_COMPUTATION",
     "every coordinate row with t <= 2 is strict, by the PIECE model alone "
     "(85 of 85 rows; the piece UB file emits only mask-00 cells, has no "
     "budget dimension in its key and no conflicting duplicate line, and five "
     "sampled cells recomputed with no table at all agree exactly)",
     ["L.master", "L.envelope", "L.extract", "D.models", "E.piecetab"],
     "src/l6_rows_final_144.py, outputs/rr_l6_chain_dependency_146.json")
node("C.lower870", "conclusion", "EXHAUSTIVE_COMPUTATION",
     "L6 >= 870 -- what survives the round-146 retraction",
     ["L.fixedrep", "L.master", "E.rows870", "E.n3rigid", "L.splice"])
node("C.final", "conclusion", "REFUTED",
     "L6 = 872 -- RETRACTED in round 146 (see C.lower)", ["C.lower", "W.872"])
node("C.interval", "conclusion", "EXHAUSTIVE_COMPUTATION",
     "L6 in {870, 871, 872}", ["C.lower870", "W.872"])

# -------- validation only: NOT a dependency of the proof
node("V.archive", "certificate", "EXHAUSTIVE_COMPUTATION",
     "44,121 length-872 and 6 length-873 archive covers audited: 0 failures, "
     "every 872 word gives MASTER = 872 with t = 5 via (k,H) = (5,0), (4,1), (3,2). "
     "VALIDATION ONLY -- the lower bound does not depend on it",
     [], "outputs/rr_l6_cleanroom_146.json (full-archive run)")


def closure(root):
    seen, stack = set(), [root]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack += N[x]["deps"]
    return seen


if __name__ == "__main__":
    dep = closure("C.final")
    OFFEND = ("TEST_ONLY", "EXTERNAL_DEPENDENCY", "UNAUDITED", "REFUTED")
    bad = {s: [n for n in sorted(dep) if N[n]["status"] == s] for s in OFFEND}
    counts = {}
    for n in sorted(dep):
        counts[N[n]["status"]] = counts.get(N[n]["status"], 0) + 1
    # the conclusion that SURVIVES round 146, audited the same way
    dep2 = closure("C.interval")
    bad2 = {s: [n for n in sorted(dep2) if N[n]["status"] == s] for s in OFFEND}
    counts2 = {}
    for n in sorted(dep2):
        counts2[N[n]["status"]] = counts2.get(N[n]["status"], 0) + 1
    # every node must be reachable-checked for dangling deps
    dangling = [(n, d) for n in N for d in N[n]["deps"] if d not in N]
    out = dict(nodes=len(N), on_path_to_final=len(dep),
               status_counts=counts, offending=bad, dangling=dangling,
               pure_hand_proof_on_path=[n for n in sorted(dep)
                                        if N[n]["status"] == "PURE_HAND_PROOF"],
               validation_only=[n for n in N if n not in dep],
               ok=(not any(bad.values()) and not dangling),
               surviving_conclusion=dict(
                   root="C.interval", on_path=len(dep2), status_counts=counts2,
                   offending=bad2, ok=(not any(bad2.values()) and not dangling)),
               dag={k: v for k, v in N.items()})
    (ROOT / "outputs" / "rr_l6_dag_146.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "dag"},
                     ensure_ascii=False, indent=1))
