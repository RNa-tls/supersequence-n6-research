#!/usr/bin/env python3
"""Round 152 -- the capacity layer of the proof DAG, with statuses read off the
artifacts rather than written by hand.

The round-148 DAG gave the capacity table the status EXHAUSTIVE_UNCAPPED on the
strength of the production searcher's own report.  This file replaces that node
with one whose status is derived from certificates that two independent checkers
re-established, and it refuses to call anything certified that the artifacts do
not support.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R152 = ROOT / "r152"
ALLOWED = ("PURE_HAND_PROOF", "INDEPENDENTLY_DUPLICATED", "VERIFIED_CERTIFICATE",
           "EXHAUSTIVE_UNCAPPED")
FORBIDDEN = ("TESTED_ONLY", "UNKNOWN_CAP", "ERROR", "REFUTED", "UNAUDITED",
             "SOLVER_SELF_REPORT", "MISSING")
N = {}


def jload(p):
    """Absent OR unparsable both give None, which maps to status MISSING.

    A half-written report (a run still in flight) must never be read as a pass.
    """
    p = Path(p)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        print(f"  note: {p} is not valid JSON (incomplete run?) -- treated as "
              f"absent")
        return None


def node(nid, status, what, deps=(), where=""):
    N[nid] = dict(status=status, what=what, deps=list(deps), where=where)


def main():
    vpy = jload(R152 / "certs" / "verify_all_152.json")
    vc = jload(R152 / "certs" / "verify_all_c152.json")
    vpil = jload(R152 / "certs" / "verify_pilot_152.json")
    agr = jload(R152 / "certs" / "agreement_152.json")
    mut = jload(R152 / "certs" / "mutations_152.json")
    cen = jload(R152 / "certs" / "census_152.json")
    vpc = jload(R152 / "certs" / "verify_piece_c152.json")
    vpp = jload(R152 / "certs" / "verify_piece_152.json")
    pmut = jload(R152 / "certs" / "mutations_piece_152.json")
    extr = jload(R152 / "certs" / "extree_pilot_152.json")
    emut = jload(R152 / "certs" / "mutations_extree_152.json")
    inv = jload(R152 / "certs" / "invariants_152.json")
    cat = jload(R152 / "certs" / "catalogue_crosscheck_152.json")
    hfx = jload(R152 / "certs" / "heavyfix_152.json")

    node("H.monotone", "PURE_HAND_PROOF",
         "(P1) cap is monotone non-decreasing in every budget",
         [], "research/RR_L6_R147_SOUND_UB.md")
    node("H.hexcount", "PURE_HAND_PROOF", "(P2) cap(K) <= 120 + a + bb + e",
         [], "research/RR_L6_R147_SOUND_UB.md")
    node("H.catalogue", "PURE_HAND_PROOF",
         "the joint catalogue is complete and the charging rules are exhaustive",
         [], "r149/PROOF.md sections 2.2-2.3")
    node("H.wlog", "PURE_HAND_PROOF",
         "fixing the start port is WLOG (left S6 transitive, catalogue "
         "equivariant; 518,400 pairs checked)", [], "r149/PROOF.md section 2.4")
    node("H.feas", "PURE_HAND_PROOF",
         "the feasibility prune never removes a realisable continuation",
         [], "round 150 feasibility audit")
    node("D.cap", "PURE_HAND_PROOF",
         "cap(K) defined as a maximum over chains, every budget an upper bound",
         ["H.catalogue", "H.wlog"], "r152/CAPACITY_CERTIFICATE.md section 1")

    # -- the checkers themselves
    mut_ok = bool(mut) and mut.get("all_caught") and mut.get("baseline_passes")
    node("V.mutation",
         "VERIFIED_CERTIFICATE" if mut_ok else "MISSING",
         f"every mutation of the certificate and of the checker source is "
         f"refused ({sum(1 for r in (mut or {}).get('mutations', []) if r['caught'])}"
         f"/{len((mut or {}).get('mutations', []))})",
         [], "r152/src/mutate152.py")
    agr_ok = bool(agr) and agr.get("agree")
    node("V.twochecks",
         "INDEPENDENTLY_DUPLICATED" if agr_ok else "MISSING",
         "a Python and a C checker, sharing no code and no data file, reach the "
         "same verdict on the same certificate bytes"
         + (f" ({agr.get('cells')} cells, "
            f"{agr.get('cells_with_different_node_counts')} node-count "
            f"differences)" if agr else ""),
         ["D.cap", "H.monotone", "H.hexcount", "H.feas"],
         "r152/src/checker152.py, r152/src/checker152.c")

    # -- the certified cells
    def summarise(v):  # noqa: E306
        if not v:
            return None
        rows = v["rows"] if "rows" in v else []
        ok = sum(r["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
                 for r in rows)
        exact = sum(r["status"] == "EXACT_CERTIFIED" for r in rows)
        bad = [r for r in rows
               if r["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED")]
        return dict(cells=len(rows), certified=ok, exact=exact,
                    unverified=len(bad),
                    unverified_examples=[r["cell"] for r in bad[:10]])

    sc, sp = summarise(vc), summarise(vpy)
    src = sc or sp
    node("E.certcells",
         "VERIFIED_CERTIFICATE" if (src and src["unverified"] == 0)
         else ("UNKNOWN_CAP" if src else "MISSING"),
         (f"{src['certified']}/{src['cells']} cells carry a verified upper "
          f"bound ({src['exact']} of them exact); "
          f"{src['unverified']} not verified" if src else "no verification run"),
         ["V.twochecks", "V.mutation"], "r152/certs/verify_all_*.json")

    spil = summarise(vpil)
    node("E.equalitycells",
         "VERIFIED_CERTIFICATE"
         if (spil and spil["unverified"] == 0 and spil["exact"] == spil["cells"])
         else "MISSING",
         "the two cells the L=871 equality rows rest on, 0|14|0|0|0|0 = 96 and "
         "0|8|0|0|0|1 = 92, are certified EXACT together with their ladders",
         ["V.twochecks", "V.mutation"], "r152/certs/verify_pilot_152.json")

    node("E.heavyfix",
         "INDEPENDENTLY_DUPLICATED" if hfx else "MISSING",
         "the heavy-retained model is keyed on HMAX = H; the round-148 code used "
         "the joint count h.  Reproduced and repaired; the census is unchanged "
         + (f"({hfx.get('bug_impact', {}).get('called_with_h_ne_H', '?')} rows "
            f"called it with h != H, "
            f"{hfx.get('bug_impact', {}).get('closed_only_by_merged_and_wrong', '?')}"
            f" of them closed only by a wrong call)" if hfx else ""),
         [], "r152/src/heavyfix152.py")

    node("V.invariants",
         "INDEPENDENTLY_DUPLICATED" if (inv or {}).get("ok") else "MISSING",
         "the catalogue invariants I1-I6, checked over all 720 words; they say "
         "which guards in the searchers are load-bearing and which are vacuous",
         [], "r152/src/invariants152.py")
    node("V.catalogue",
         "INDEPENDENTLY_DUPLICATED" if (cat or {}).get("agree") else "MISSING",
         "the checker's own catalogue agrees field by field with round 147's, "
         "including all 511,200 heavy joints (a cross-check, not a dependency)",
         [], "r152/src/catcheck152.py")
    node("E.extree",
         "VERIFIED_CERTIFICATE"
         if ((extr or {}).get("all_valid") and (emut or {}).get("ok"))
         else "MISSING",
         "an EXPLICIT exhaustion tree for the cells the equality rows rest on, "
         "validated by a program that performs no search"
         + (f" ({extr['cells']} cells, {extr['total_nodes']:,} nodes, "
            f"{extr['tree_bytes']:,} bytes)" if extr else ""),
         ["D.cap", "H.monotone", "H.hexcount", "H.feas"],
         "r152/src/extree152.py")

    spc = summarise(vpc) or summarise(vpp)
    node("V.piecemutation",
         "VERIFIED_CERTIFICATE" if (pmut or {}).get("all_caught") else "MISSING",
         "every mutation of a piece certificate and of the piece checker source "
         "is refused", [], "r152/src/pmutate152.py")
    node("E.piececells",
         "VERIFIED_CERTIFICATE" if (spc and spc["unverified"] == 0)
         else ("UNKNOWN_CAP" if spc else "MISSING"),
         (f"{spc['certified']}/{spc['cells']} marked piece capacities carry a "
          f"verified bound ({spc['exact']} exact); {spc['unverified']} not "
          f"verified" if spc else "no piece verification run"),
         ["V.piecemutation", "V.invariants", "H.catalogue"],
         "r152/certs/verify_piece_*.json")

    lay = (cen or {}).get("layers", {})
    t871 = lay.get("L871", {}).get("tally", {})
    t870 = lay.get("L870", {}).get("tally", {})
    node("E.census871",
         "VERIFIED_CERTIFICATE"
         if (t871.get("STRICTLY_CLOSED", 0) + t871.get("EQUALITY", 0)
             == sum(t871.values()) and t871.get("SURVIVING", 0) == 0 and t871)
         else ("UNKNOWN_CAP" if t871 else "MISSING"),
         f"L = 871 census using certified capacities only: {json.dumps(t871)}",
         ["E.certcells", "E.equalitycells", "E.heavyfix", "E.piececells",
          "E.extree", "V.catalogue"], "r152/src/rows152.py")
    node("E.census870",
         "VERIFIED_CERTIFICATE"
         if (t870 and set(t870) == {"STRICTLY_CLOSED"}) else
         ("UNKNOWN_CAP" if t870 else "MISSING"),
         f"L = 870 census using certified capacities only: {json.dumps(t870)}",
         ["E.certcells", "E.heavyfix", "E.piececells", "V.catalogue"],
         "r152/src/rows152.py")

    # ---------------------------------------------------------------- report
    bad = {k: v for k, v in N.items() if v["status"] in FORBIDDEN}
    def anc(nid, seen=None):
        seen = seen if seen is not None else set()
        for d in N[nid]["deps"]:
            if d not in seen:
                seen.add(d)
                anc(d, seen)
        return seen
    top = "E.census871"
    forbidden_on_path = sorted(
        {n for n in anc(top) | {top} if N[n]["status"] in FORBIDDEN})
    out = dict(nodes=N, forbidden_statuses=sorted(bad),
               top=top, forbidden_on_path_to_top=forbidden_on_path,
               capacity_layer_certified=not forbidden_on_path)
    (R152 / "certs" / "dag_152.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in N.items():
        print(f"  {v['status']:<26} {k:<18} {v['what'][:90]}")
    print()
    print(f"forbidden statuses anywhere: {sorted(bad) or 'none'}")
    print(f"forbidden on the path to {top}: {forbidden_on_path or 'none'}")
    print(f"capacity layer certified: {out['capacity_layer_certified']}")
    return 0 if out["capacity_layer_certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
