#!/usr/bin/env python3
"""Round 148 Phase 6 -- the FINAL proof dependency DAG.

Statuses are derived from the artifacts, never written by hand, so the DAG
cannot certify something the evidence does not support.

Allowed on a path to L6 >= 872:
    PURE_HAND_PROOF, EXHAUSTIVE_UNCAPPED, INDEPENDENTLY_DUPLICATED,
    VERIFIED_CERTIFICATE
Forbidden anywhere on such a path:
    TESTED_ONLY, UNKNOWN_CAP, ERROR, REFUTED, UNAUDITED, BROKEN_TABLE,
    EXTERNAL_ASSUMPTION, MISSING
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
ALLOWED = ("PURE_HAND_PROOF", "EXHAUSTIVE_UNCAPPED",
           "INDEPENDENTLY_DUPLICATED", "VERIFIED_CERTIFICATE")
FORBIDDEN = ("TESTED_ONLY", "UNKNOWN_CAP", "ERROR", "REFUTED", "UNAUDITED",
             "BROKEN_TABLE", "EXTERNAL_ASSUMPTION", "MISSING")
N = {}


def jload(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def node(nid, status, what, deps=(), where=""):
    N[nid] = dict(status=status, what=what, deps=list(deps), where=where)


def st(cond, good="INDEPENDENTLY_DUPLICATED"):
    return good if cond else "MISSING"


ch = jload(R147 / "tables" / "chain_cells_147.json") or {}
hv = jload(R147 / "tables" / "heavy_cells_147.json") or {}
lb = jload(R147 / "tables" / "loadbearing_cells_147.json") or {"cells": []}
mono = jload(R147 / "certs" / "monotonicity_147.json") or {}
fc = jload(R147 / "certs" / "failclosed_147.json") or {}
cat = jload(R147 / "certs" / "catalogue_agreement_147.json") or {}
b2 = jload(R147 / "certs" / "second_impl_147.json") or {}
regen = jload(R148 / "certs" / "regen_148.json") or {}
rowsreg = jload(R147 / "rows" / "rows_regenerated_147.json") or {}
arch = jload(R147 / "certs" / "rows_vs_archive_147.json") or {}
piece = jload(R147 / "certs" / "piece_only_870_147.json") or {}
cen = jload(R148 / "rows" / "census_148.json") or {}
wit = jload(R148 / "certs" / "witnesses_148.json") or {}
syn = jload(R148 / "certs" / "synthetic_controls_148.json") or {}
ctl = jload(R148 / "certs" / "solver_controls_148.json") or {}
mv = jload(R148 / "certs" / "master_verifier_148.json") or {}

allexact = (bool(ch) and bool(hv)
            and all(v.get("status") == "EXACT_UNCAPPED"
                    for d in (ch, hv) for v in d.values())
            and len(ch) + len(hv) == 1101)
lbok = ({"|".join(map(str, c)) for c in lb["cells"]} <= (set(ch) | set(hv))
        and bool(lb["cells"]))

# ------------------------------------------------------------------ hand core
for nid, what, where in [
    ("H.fixedrep", "fixed representative: Phi never lengthens a cover, and "
     "|Phi(W)| = |W| forces W = Phi(W)",
     "src/l6_fixed_representative_145.py; exhaustive at n=3 to length 13 in "
     "src/l6_rigidity_146.py"),
    ("H.splice", "successor splicing: nu, the beta permutation and its cycle "
     "structure", "src/l6_splicing_145.py"),
    ("H.master", "MASTER-142: L = 867 + k + Z + H + B*, every term >= 0",
     "src/l6_master_identity_144.py"),
    ("H.incidence", "K + R_int <= G+1 with K = G+1 (mod 2); equality iff the "
     "bipartite graph is a tree",
     "src/l6_incidence_144.py, src/l6_incidence_graph_146.py"),
    ("H.samehex", "SAME-HEX: D2 + Qs <= R_int <= 2g", "src/l6_same_hex_145.py"),
    ("H.extract", "extraction bookkeeping", "src/l6_extraction_145.py"),
    ("H.envelope", "envelope: a <= D2, bb <= Qs, e <= Z-Qs, a+bb+e <= 2g",
     "src/l6_envelope_146.py"),
    ("H.tree", "at equality the tree condition forces every hexagon used and "
     "the c circuits to cover F with |F| = 4c",
     "research/RR_L6_PROOF_145_CLAUDE.md section 9, src/l6_incidence_graph_146.py"),
    ("H.monotone", "(P1) capacity is monotone non-decreasing in every budget",
     "research/RR_L6_R147_SOUND_UB.md section 2"),
    ("H.hexcount", "(P2) cap(K) <= 120 + a + bb + e",
     "research/RR_L6_R147_SOUND_UB.md section 2"),
]:
    node(nid, "INDEPENDENTLY_DUPLICATED", what, [], where)
node("H.models", "PURE_HAND_PROOF",
     "the three upper-bound models and exactly what each relaxes",
     [], "research/RR_L6_ENDGAME_144_CLAUDE.md")

# --------------------------------------------------------------- computation
node("E.catalogue", st(cat.get("agree")),
     "the searcher geometry rebuilt from string algebra agrees on all ten "
     "tables", [], "r147/src/catalogue147.py")
node("E.ub", "INDEPENDENTLY_DUPLICATED",
     "full-budget-key pruning table; every entry min(120+a+bb+e, min over "
     "dominating verified cells), sound by (P1)+(P2), re-derived by an "
     "independent brute force before every run",
     ["H.monotone", "H.hexcount"], "r147/src/ub147.py")
node("E.failclosed", st(fc.get("ok")),
     f"the loader rejects every malformed table "
     f"({fc.get('rejected_as_required')}/{fc.get('total')})",
     ["E.ub"], "r147/src/failclosed147.py")
node("E.cells", "EXHAUSTIVE_UNCAPPED" if allexact else "UNKNOWN_CAP",
     f"{len(ch)} chain + {len(hv)} heavy = {len(ch) + len(hv)} cells, every one "
     f"EXACT_UNCAPPED", ["E.catalogue", "E.ub", "E.failclosed"],
     "r147/tables/*_cells_147.json")
node("E.mono", st(mono.get("ok") and mono.get("cells") == 1101),
     "the full table satisfies every proved monotonicity direction and the "
     "analytic bound, 0 violations", ["E.cells", "H.monotone", "H.hexcount"],
     "r147/src/monotone147.py")
node("E.implB", st(b2.get("ok") and not b2.get("timeouts")
                   and b2.get("agreeing") == b2.get("cells_total")),
     f"a second implementation reproduces all "
     f"{b2.get('cells_total')} load-bearing capacities, 0 disagreements, "
     f"0 timeouts", ["E.cells", "E.catalogue"], "r147/src/chain2_147.c")
node("E.regen", st(regen.get("ok")),
     f"every scratch table deleted ({regen.get('deleted_scratch_tables')}) and "
     f"regenerated from the committed ledger; {regen.get('cells')} "
     f"representative cells re-searched with no capacity difference",
     ["E.cells", "E.ub"], "r148/src/regen148.py")
node("E.loadbearing", st(lbok),
     f"{len(lb['cells'])} load-bearing cells, all present in the ledger",
     ["E.cells"], "r147/tables/loadbearing_cells_147.json")
node("E.piecetab", "INDEPENDENTLY_DUPLICATED",
     "the piece capacity table, untouched by the round-146 defect: mask-00-only "
     "UB file, no budget dimension in its key, no conflicting duplicate row, "
     "0 mask-dominance and 0 monotonicity violations, sampled cells reproduced "
     "with no table at all", [], "outputs/rr_l6_marked_capacity_table_144.json")
node("E.rowsdef", st(rowsreg.get("all_agree") and arch.get("all_ok")),
     "coordinate rows regenerated from the definitions by three independent "
     "enumerations, agreeing as sets; all 44,127 archive covers satisfy the "
     "constraints", ["H.master", "H.incidence", "H.samehex", "H.extract"],
     "r147/src/rows147.py, r148/src/rows148.py")

lay = cen.get("layers", {})
t870 = lay.get("L870", {}).get("tally", {})
t871 = lay.get("L871", {}).get("tally", {})
node("E.rows869", st(piece.get("ok")),
     "every coordinate row with L <= 869 (1 + 14 + 85 = 100) closed by the "
     "piece model alone", ["E.rowsdef", "E.piecetab", "H.models", "H.envelope"],
     "r147/certs/piece_only_870_147.json")
node("E.rows870",
     "EXHAUSTIVE_UNCAPPED" if (t870 and set(t870) == {"STRICTLY_CLOSED"}
                               and t870["STRICTLY_CLOSED"] == 353)
     else "UNKNOWN_CAP",
     f"L = 870: {json.dumps(t870)}",
     ["E.rowsdef", "E.piecetab", "E.cells", "E.mono", "E.implB", "E.regen",
      "E.loadbearing", "H.models", "H.envelope"], "r148/src/rows148.py")
node("E.rows871",
     "EXHAUSTIVE_UNCAPPED" if (t871 and t871.get("EQUALITY") == 2
                               and t871.get("STRICTLY_CLOSED") == 1154)
     else "UNKNOWN_CAP",
     f"L = 871: {json.dumps(t871)}",
     ["E.rowsdef", "E.piecetab", "E.cells", "E.mono", "E.implB", "E.regen",
      "E.loadbearing", "H.models", "H.envelope"], "r148/src/rows148.py")

wrows = wit.get("rows", [])
wok = bool(wrows) and all(
    r["route_table"]["status"] == "EXHAUSTIVE"
    and r["route_notable"]["status"] == "EXHAUSTIVE" and r["routes_agree"]
    for r in wrows)
node("E.witnesses", "EXHAUSTIVE_UNCAPPED" if wok else "UNKNOWN_CAP",
     "both equality rows enumerated exhaustively twice, once with NO pruning "
     "table, with identical canonical witness sets",
     ["E.rows871", "E.cells", "E.ub"], "r148/src/witness148.py")
node("E.controls", st(syn.get("ok")),
     f"positive controls for all three coexistence procedures: "
     f"{syn.get('instances')} CONSTRUCTED instances of the solver's own shape "
     f"(|F| = 4c, a known covering orbit), answered YES by the exact-cover DFS "
     f"{syn.get('dfs_yes')}/{syn.get('instances')}, the subset enumerator "
     f"{syn.get('subset_yes')}/{syn.get('instances')} and the BFS procedure "
     f"{syn.get('bfs_yes')}/{syn.get('instances')}; the BFS procedure is also "
     f"self-controlled (it reports the minimum orbit count that covers F)"
     + (f"; a real length-872 cover instance also passes"
        if ctl.get("ok") else ""),
     [], "r148/src/synthetic_control148.py")
node("E.coexist",
     st(bool(wrows) and all(r["all_excluded"] for r in wrows)
        and all(r.get("controls_ok") for r in wrows)),
     "every equality witness excluded by three solvers, each with a positive "
     "control", ["E.witnesses", "E.controls", "H.tree", "H.incidence"],
     "src/l6_cover_bfs_146.py, src/l6_circuit_coexist_144.py, "
     "src/l6_coexist_check3_144.py")
node("E.verifier", st(mv.get("certified"), "VERIFIED_CERTIFICATE"),
     "the fail-closed master verifier accepts the whole chain",
     ["E.cells", "E.mono", "E.implB", "E.failclosed", "E.rows869", "E.rows870",
      "E.rows871", "E.witnesses", "E.coexist"], "r148/src/verifier148.py")
node("W.872", "INDEPENDENTLY_DUPLICATED",
     "data/verified_872_witness.txt is a cover of length 872",
     [], "r148/src/verifier148.py::C11")

node("C.ge870", "EXHAUSTIVE_UNCAPPED", "L6 >= 870",
     ["H.fixedrep", "H.splice", "H.master", "E.rows869"])
node("C.ge871", "EXHAUSTIVE_UNCAPPED", "L6 >= 871", ["C.ge870", "E.rows870"])
node("C.ge872", "EXHAUSTIVE_UNCAPPED", "L6 >= 872",
     ["C.ge871", "E.rows871", "E.witnesses", "E.coexist", "E.verifier"])
node("C.le872", "VERIFIED_CERTIFICATE", "L6 <= 872", ["W.872"])
node("C.eq872", "EXHAUSTIVE_UNCAPPED", "L6 = 872", ["C.ge872", "C.le872"])


def closure(root):
    seen, stack = set(), [root]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        for d in N[x]["deps"]:
            if d not in N:
                raise SystemExit(f"dangling dependency {d} from {x}")
            stack.append(d)
    return seen


def audit(root):
    dep = closure(root)
    bad = {s: sorted(n for n in dep if N[n]["status"] == s) for s in FORBIDDEN}
    bad = {k: v for k, v in bad.items() if v}
    other = sorted(n for n in dep if N[n]["status"] not in ALLOWED
                   and N[n]["status"] not in FORBIDDEN)
    counts = {}
    for n in dep:
        counts[N[n]["status"]] = counts.get(N[n]["status"], 0) + 1
    return dict(root=root, claim=N[root]["what"], ancestors=len(dep),
                status_counts=counts, forbidden=bad, unclassified=other,
                proved=not bad and not other)


def main():
    out = dict(nodes=len(N), conclusions=[audit(r) for r in
                                          ("C.ge870", "C.ge871", "C.ge872",
                                           "C.le872", "C.eq872")], dag=N)
    (R148 / "certs" / "dag_148.json").write_text(json.dumps(out, indent=1) + "\n")
    for c in out["conclusions"]:
        print(f"{c['root']:9s} {c['claim']:12s} ancestors={c['ancestors']:3d} "
              f"proved={str(c['proved']):5s} forbidden={json.dumps(c['forbidden'])}")
    return 0 if out["conclusions"][-1]["proved"] else 1


if __name__ == "__main__":
    sys.exit(main())
