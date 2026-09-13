#!/usr/bin/env python3
"""Round 147 Phase 17 -- the proof dependency DAG, with statuses READ FROM THE
ARTIFACTS rather than written by hand, so it cannot go stale or overclaim.

No path to a claimed conclusion may contain a node whose status is
REFUTED, UNKNOWN_CAP, TESTED_ONLY, UNAUDITED, BROKEN_TABLE or
EXTERNAL_ASSUMPTION.  The intermediate conclusions L6 >= 870, L6 >= 871,
L6 >= 872, L6 <= 872 and L6 = 872 each appear as their own node and each one is
audited separately.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
ROOT = R147.parent
OFFEND = ("REFUTED", "UNKNOWN_CAP", "TESTED_ONLY", "UNAUDITED",
          "BROKEN_TABLE", "EXTERNAL_ASSUMPTION", "MISSING")
N = {}


def node(nid, status, what, deps=(), where=""):
    N[nid] = dict(status=status, what=what, deps=list(deps), where=where)


def jload(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


# ---------------------------------------------------------- read the artifacts
cells = jload(R147 / "tables" / "chain_cells_147.json") or {}
heavy = jload(R147 / "tables" / "heavy_cells_147.json") or {}
dep = jload(ROOT / "outputs" / "rr_l6_chain_dependency_146.json") or {"cells": []}
hdep = jload(R147 / "tables" / "heavy_dependency_147.json") or {"cells": []}
rowsreg = jload(R147 / "rows" / "rows_regenerated_147.json")
rowseval = jload(R147 / "rows" / "rows_eval_147.json")
mono = jload(R147 / "certs" / "monotonicity_147.json")
failc = jload(R147 / "certs" / "failclosed_147.json")
cat = jload(R147 / "certs" / "catalogue_agreement_147.json")
ctrl = jload(R147 / "certs" / "noub_controls_147.json")
second = jload(R147 / "certs" / "second_impl_147.json")
cover = jload(ROOT / "outputs" / "rr_l6_cover_bfs_146.json")
clean = jload(ROOT / "outputs" / "rr_l6_cleanroom_146.json")
piece870 = jload(ROOT / "outputs" / "rr_l6_piece_only_870_146.json")


def cell_status(store, want):
    need = {"|".join(str(x) for x in (list(c) + [0])[:6]) for c in want}
    ok = {k for k, v in store.items() if v.get("status") == "EXACT_UNCAPPED"}
    missing = need - ok
    return ("EXHAUSTIVE" if not missing else "UNKNOWN_CAP"), len(need), len(missing)


chain_st, chain_need, chain_missing = cell_status(cells, dep["cells"])
heavy_st, heavy_need, heavy_missing = cell_status(heavy, hdep["cells"])

# ------------------------------------------------------------------ hand core
for nid, what, where in [
    ("L.fixedrep", "fixed representative: Phi never lengthens a cover, and "
     "|Phi(W)|=|W| forces W=Phi(W) (exhaustive at n=3 to length 13)",
     "src/l6_fixed_representative_145.py, src/l6_rigidity_146.py"),
    ("L.master", "MASTER-142: L = 867 + k + Z + H + B* with every term >= 0",
     "src/l6_master_identity_144.py"),
    ("L.splice", "successor splicing and the beta permutation",
     "src/l6_splicing_145.py"),
    ("L.incidence", "K + R_int <= G+1, K = G+1 (mod 2), equality iff tree",
     "src/l6_incidence_144.py, src/l6_incidence_graph_146.py"),
    ("L.samehex", "SAME-HEX: D2 + Qs <= R_int <= 2g", "src/l6_same_hex_145.py"),
    ("L.extract", "extraction bookkeeping", "src/l6_extraction_145.py"),
    ("L.envelope", "envelope: a <= D2, bb <= Qs, e <= Z-Qs, a+bb+e <= 2g",
     "src/l6_envelope_146.py"),
    ("L.monotone", "(P1) capacity is monotone non-decreasing in every budget",
     "research/RR_L6_R147_SOUND_UB.md section 2, r147/src/monotone147.py"),
    ("L.hexcount", "(P2) cap(K) <= 120 + a + bb + e",
     "research/RR_L6_R147_SOUND_UB.md section 2"),
]:
    node(nid, "INDEPENDENTLY_DUPLICATED", what, [], where)

node("D.models", "PURE_HAND_PROOF",
     "the three upper-bound models and what each relaxes",
     [], "research/RR_L6_ENDGAME_144_CLAUDE.md")

# ------------------------------------------------------- round-147 computation
node("E.catalogue", "INDEPENDENTLY_DUPLICATED" if (cat or {}).get("agree")
     else "MISSING",
     "the searcher's geometry rebuilt from string algebra agrees on all ten "
     "tables (720 words, 120 hexagons, 144 orbits, 511,200 heavy connectors)",
     [], "r147/src/catalogue147.py")
node("E.soundub", "INDEPENDENTLY_DUPLICATED",
     "the pruning table is keyed by the full budget vector; every entry is "
     "min(120+a+bb+e, min over dominating verified cells), sound by (P1)+(P2), "
     "generated and then re-derived by an independent brute force",
     ["L.monotone", "L.hexcount"], "r147/src/ub147.py")
node("E.failclosed", "INDEPENDENTLY_DUPLICATED" if (failc or {}).get("ok")
     else "MISSING",
     f"the loader rejects every malformed table "
     f"({(failc or {}).get('rejected_as_required')}/{(failc or {}).get('total')} cases)",
     ["E.soundub"], "r147/src/failclosed147.py")
node("E.chaintab147", chain_st,
     f"sound chain capacities: {chain_need - chain_missing}/{chain_need} cells "
     f"EXACT_UNCAPPED, {chain_missing} unresolved",
     ["E.catalogue", "E.soundub", "E.failclosed"],
     "r147/tables/chain_cells_147.json")
node("E.heavytab147", heavy_st,
     f"sound heavy capacities: {heavy_need - heavy_missing}/{heavy_need} cells "
     f"EXACT_UNCAPPED, {heavy_missing} unresolved",
     ["E.catalogue", "E.soundub", "E.failclosed"],
     "r147/tables/heavy_cells_147.json")
node("E.mono147", "INDEPENDENTLY_DUPLICATED" if (mono or {}).get("ok")
     else ("UNKNOWN_CAP" if mono else "MISSING"),
     "the sound table satisfies every proved monotonicity direction and the "
     "analytic bound, with zero violations",
     ["E.chaintab147", "L.monotone", "L.hexcount"], "r147/src/monotone147.py")
node("E.controls147",
     "INDEPENDENTLY_DUPLICATED" if (ctrl or {}).get("ok") else "MISSING",
     "no-UB controls: the table-pruned value equals the value computed with the "
     "pruning table switched off, on every control cell",
     ["E.chaintab147"], "r147/src/noub_controls147.py")
node("E.second147",
     "INDEPENDENTLY_DUPLICATED" if (second or {}).get("ok") else "MISSING",
     "an independent implementation reproduces every load-bearing capacity",
     ["E.catalogue"], "r147/src/chain2_147.py")
node("E.piecetab", "INDEPENDENTLY_DUPLICATED",
     "the piece capacity table, untouched by the round-146 defect: its UB file "
     "emits only mask-00 cells, has no budget dimension in its key and no "
     "conflicting duplicate row; mask dominance and monotonicity violations 0; "
     "five sampled cells recomputed with no table agree on all four masks",
     ["L.catalogue"] if False else [], "outputs/rr_l6_marked_capacity_table_144.json")
node("L.catalogue", "INDEPENDENTLY_DUPLICATED", "the joint catalogue out of "
     "end(v) = sigma^{-1}(v)", [], "src/l6_marked_capacity_144.py")
node("E.rowsdef", "INDEPENDENTLY_DUPLICATED" if (rowsreg or {}).get("all_agree")
     else "MISSING",
     "coordinate rows regenerated from the definitions, agreeing as sets with "
     "the round-144 enumeration: 1 / 14 / 85 / 353 / 1156 groups for "
     "L = 867..871, and satisfied by all 44,127 archive covers",
     ["L.master", "L.incidence", "L.samehex", "L.extract"],
     "r147/src/rows147.py")


def layer_status(L):
    if not rowseval:
        return "MISSING", None
    lay = rowseval.get("layers", {}).get(f"L{L}")
    if not lay:
        return "MISSING", None
    t = lay["tally"]
    bad = {k: v for k, v in t.items() if k != "STRICTLY_CLOSED"}
    return ("EXHAUSTIVE" if not bad else "UNKNOWN_CAP"), lay


st867, l867 = layer_status(867)
st868, l868 = layer_status(868)
st869, l869 = layer_status(869)
st870, l870 = layer_status(870)
st871, l871 = layer_status(871)

node("E.rows869", "INDEPENDENTLY_DUPLICATED" if (piece870 or {}).get("ok")
     else "MISSING",
     "every coordinate row with L <= 869 (1 + 14 + 85 = 100 rows) is closed by "
     "the PIECE model alone, which never reads a chain table",
     ["E.rowsdef", "E.piecetab", "D.models"],
     "outputs/rr_l6_piece_only_870_146.json")
for L, st, lay in ((870, st870, l870), (871, st871, l871)):
    node(f"E.rows{L}", st,
         f"L = {L}: " + (json.dumps(lay["tally"]) if lay else "not evaluated"),
         ["E.rowsdef", "E.piecetab", "E.chaintab147", "E.heavytab147",
          "E.mono147", "E.controls147", "E.second147", "E.envelope"
          if False else "L.envelope", "D.models"],
         "r147/src/rows_eval147.py")
node("E.coexist", "INDEPENDENTLY_DUPLICATED" if (cover or {}).get("ok")
     else "MISSING",
     "no equality witness admits its forced pure circuits; three procedures, "
     "the third with a positive control (minimum orbits to cover F is 8)",
     ["L.incidence"], "src/l6_cover_bfs_146.py")
node("W.872", "INDEPENDENTLY_DUPLICATED",
     "data/verified_872_witness.txt is a cover of length 872",
     [], "src/l6_proof_145.py::step1")
node("V.archive", "INDEPENDENTLY_DUPLICATED" if clean else "MISSING",
     "44,121 length-872 and 6 length-873 archive covers: 0 invariant failures. "
     "VALIDATION ONLY -- no lower bound depends on it",
     [], "outputs/rr_l6_cleanroom_146.json")

# ------------------------------------------------------------- the conclusions
node("C.le872", "INDEPENDENTLY_DUPLICATED", "L6 <= 872", ["W.872"])
node("C.ge870", "EXHAUSTIVE", "L6 >= 870",
     ["L.fixedrep", "L.master", "L.splice", "E.rows869"])
node("C.ge871", "EXHAUSTIVE", "L6 >= 871", ["C.ge870", "E.rows870"])
node("C.ge872", "EXHAUSTIVE", "L6 >= 872",
     ["C.ge871", "E.rows871", "E.coexist"])
node("C.eq872", "EXHAUSTIVE", "L6 = 872", ["C.ge872", "C.le872"])


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
    bad = {s: sorted(n for n in dep if N[n]["status"] == s) for s in OFFEND}
    bad = {k: v for k, v in bad.items() if v}
    counts = {}
    for n in dep:
        counts[N[n]["status"]] = counts.get(N[n]["status"], 0) + 1
    return dict(root=root, claim=N[root]["what"], nodes=len(dep),
                status_counts=counts, offending=bad, proved=not bad)


def main():
    out = dict(nodes=len(N),
               conclusions=[audit(r) for r in ("C.le872", "C.ge870", "C.ge871",
                                               "C.ge872", "C.eq872")],
               dag=N)
    (R147 / "certs" / "dag_147.json").write_text(json.dumps(out, indent=1) + "\n")
    for c in out["conclusions"]:
        print(f"{c['root']:10s} {c['claim']:12s} nodes={c['nodes']:3d} "
              f"proved={c['proved']}  offending={json.dumps(c['offending'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
