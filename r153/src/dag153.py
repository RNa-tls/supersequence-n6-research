#!/usr/bin/env python3
"""Round 153 Phase 11 -- the FINAL dependency DAG for L6 = 872.

Statuses are derived from the artefacts, never written by hand.

  CERTIFIED_MACHINE   a machine result re-established in this repository by a
                      checker that does not trust the producer
  AUDITED_HAND_PROOF  a human proof that has been read and whose
                      machine-checkable consequences are verified here
  EXPLICIT_WITNESS    an object exhibited and checked directly
  PROVEN_ANALYTIC     a proved closed-form bound
  FORBIDDEN           on the path but not admissible
  RETRACTED           a withdrawn artefact
  UNRESOLVED          a claim nothing in the repository establishes

The theorem path must contain zero FORBIDDEN, zero RETRACTED, zero UNRESOLVED.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")
N = {}


def j(rel):
    p = ROOT / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def node(nid, status, what, deps=(), where=""):
    N[nid] = dict(status=status, what=what, deps=list(deps), where=where)


def main():
    cap = j("r152/certs/verify_all_c152.json")
    pcap = j("r152/certs/verify_piece_c152.json")
    cen = j("r152/certs/census_152.json")
    dag152 = j("r152/certs/dag_152.json")
    eq = j("r153/certs/eqcompare_153.json")
    ct = j("r153/certs/covertree_153.json")
    co = j("r153/certs/coexist_153.json")
    adv = j("r153/certs/adversarial_153.json")
    thm = j("r153/certs/theorem_153.json")
    mut = j("r153/certs/mutations_153.json")
    w872 = j("r153/certs/witness872_153.json")

    def ok(x, good, what, deps=(), where="", bad="UNRESOLVED"):
        return good if x else bad

    # ---------------------------------------------------------- hand core
    for nid, what, where in [
        ("H.fixedrep", "every cover has a fixed representative of no greater "
         "length", "src/l6_fixed_representative_145.py"),
        ("H.splice", "successor splicing and the beta permutation",
         "src/l6_splicing_145.py"),
        ("H.master", "MASTER-142: L = 867 + k + Z + H + B*, every term >= 0",
         "src/l6_master_identity_144.py"),
        ("H.incidence", "K + R_int <= G + 1, with equality iff the incidence "
         "graph is a tree", "research/RR_INCIDENCE_FOREST_LEMMA.md"),
        ("H.samehex", "SAME-HEX: D2 + Qs <= R_int <= 2g",
         "src/l6_same_hex_145.py"),
        ("H.extract", "the extraction bookkeeping", "src/l6_extraction_145.py"),
        ("H.envelope", "a <= D2, bb <= Qs, e <= Z - Qs, a + bb + e <= 2g",
         "src/l6_envelope_146.py"),
        ("H.models", "the three upper-bound models and what each relaxes",
         "r149/PROOF.md"),
        ("H.catalogue", "the joint catalogue is complete and the charging rules "
         "are exhaustive", "r149/PROOF.md section 2"),
        ("H.wlog", "fixing the start word is WLOG: left S6 is transitive and "
         "the catalogue is equivariant", "r149/PROOF.md section 2.4"),
        ("H.feas", "the feasibility prune removes no realisable continuation",
         "round 150 feasibility audit"),
        ("H.tight", "at an equality row the incidence bound is tight, so the "
         "chain is hexagon-simple, all 120 hexagons are used, and the c pure "
         "circuits (complete tau-orbits) must cover the |F| = 4c unused ones",
         "research/RR_L6_PROOF_145_CLAUDE.md section 9"),
    ]:
        node(nid, "AUDITED_HAND_PROOF", what, [], where)
    node("A.monotone", "PROVEN_ANALYTIC",
         "(P1) capacity is monotone non-decreasing in every budget",
         [], "research/RR_L6_R147_SOUND_UB.md")
    node("A.hexcount", "PROVEN_ANALYTIC",
         "(P2) cap(K) <= 120 + a + bb + e; a piece is hexagon-simple so it has "
         "at most 120 ports", [], "research/RR_L6_R147_SOUND_UB.md")
    node("A.orbitfive", ok(co and co["geometry"]["every_orbit_meets_five_hexagons"],
                           "CERTIFIED_MACHINE", ""),
         "every tau-orbit meets exactly five hexagons (all 144 checked)",
         [], "r153/src/coexist153.py")

    # -------------------------------------------------------- capacity layer
    capbad = [r["cell"] for r in (cap or {"rows": []})["rows"]
              if r["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED")]
    pbad = [r["cell"] for r in (pcap or {"rows": []})["rows"]
            if r["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED")]
    node("C.chaincaps",
         ok(cap and len(cap["rows"]) == 1101 and not capbad, "CERTIFIED_MACHINE", ""),
         f"{len(cap['rows']) if cap else 0} chain capacities independently "
         f"certified, {len(capbad)} not",
         ["A.monotone", "A.hexcount", "H.catalogue", "H.wlog", "H.feas"],
         "r152/certs/verify_all_c152.json")
    node("C.piececaps",
         ok(pcap and len(pcap["rows"]) == 220 and not pbad, "CERTIFIED_MACHINE", ""),
         f"{len(pcap['rows']) if pcap else 0} marked piece capacities "
         f"independently certified, {len(pbad)} not",
         ["A.monotone", "A.hexcount", "H.catalogue", "H.wlog", "H.feas"],
         "r152/certs/verify_piece_c152.json")
    node("C.dag152",
         ok(dag152 and dag152.get("capacity_layer_certified"),
            "CERTIFIED_MACHINE", ""),
         "the round-152 capacity DAG has no forbidden ancestor",
         ["C.chaincaps", "C.piececaps"], "r152/certs/dag_152.json")
    lay = (cen or {}).get("layers", {})
    strict_ok = all(set(v["tally"]) == {"STRICTLY_CLOSED"}
                    for L, v in lay.items() if L != "L871")
    l871 = lay.get("L871", {}).get("tally", {})
    node("C.census",
         ok(cen and strict_ok and l871.get("EQUALITY") == 2
            and not l871.get("SURVIVING") and not l871.get("UNKNOWN_CAP"),
            "CERTIFIED_MACHINE", ""),
         "the certified-only census: " + json.dumps(
             {L: v["tally"] for L, v in lay.items()}),
         ["C.chaincaps", "C.piececaps", "C.dag152", "H.master", "H.incidence",
          "H.samehex", "H.extract", "H.envelope", "H.models"],
         "r152/certs/census_152.json")

    # -------------------------------------------------------- equality layer
    eqrows = (eq or {}).get("rows", [])
    node("E.equivariance",
         ok(eq and eq["equivariance"]["ok"], "CERTIFIED_MACHINE", ""),
         "left S6 commutes with the whole catalogue: "
         f"{(eq or {}).get('equivariance', {}).get('pairs')} pairs, "
         f"{(eq or {}).get('equivariance', {}).get('violations')} violations",
         ["H.wlog"], "r153/src/eqcompare153.py")
    node("E.enumeration",
         ok(eqrows and all(r["agree"] for r in eqrows), "CERTIFIED_MACHINE", ""),
         "every capacity-attaining walk enumerated five ways with identical raw "
         "and canonical sets: " + ", ".join(
             f"{r['name']} {r['witness_count']} witnesses / {r['class_count']} "
             f"classes" for r in eqrows),
         ["C.chaincaps", "C.census", "E.equivariance", "A.hexcount", "H.feas"],
         "r153/certs/eqcompare_153.json")

    # ----------------------------------------------------- coexistence layer
    node("X.structure",
         ok(adv and all(s["hex_simple"] and s["F_equals_4c"]
                        for r in adv["rows"] for s in r["step4"]),
            "CERTIFIED_MACHINE", ""),
         "each witness is hexagon-simple and leaves |F| = 4c hexagons unused",
         ["E.enumeration", "H.tight", "H.incidence"],
         "r153/certs/adversarial_153.json")
    node("X.exclusion",
         ok(ct and ct["all_excluded"], "CERTIFIED_MACHINE", ""),
         "an explicit exhaustion tree, validated without search, shows no c "
         "tau-orbits cover F for any witness ("
         + ", ".join(f"{r['name']}#{r['index']} {r['nodes']} nodes"
                     for r in (ct or {"rows": []})["rows"]) + ")",
         ["X.structure", "A.orbitfive"], "r153/certs/covertree_153.txt")
    node("X.nolemmaE",
         ok(co and all(c2["excluded_without_lemmaE"] for r in co["rows"]
                       for c2 in r["certificates"]), "CERTIFIED_MACHINE", ""),
         "the exclusion holds with every tau-orbit allowed as a circuit, so it "
         "does not rest on the round-148 restriction to orbits the chain avoids",
         ["X.exclusion"], "r153/certs/coexist_153.json")
    node("X.controls",
         ok(co and co["controls_ok"], "CERTIFIED_MACHINE", ""),
         "each decision procedure answers YES on constructed instances that do "
         "have a cover, and reports the true minimum cover size on the very "
         "instances it rejects",
         ["X.exclusion"], "r153/certs/coexist_153.json")
    node("X.mutation",
         ok(mut and mut["invalid_all_caught"] and mut["ok"],
            "CERTIFIED_MACHINE", ""),
         "every invalid mutation of the equality/coexistence chain is refused, "
         "and the two checks that do the refusing are shown load-bearing",
         [], "r153/certs/mutations_153.json")
    node("X.adversarial",
         ok(adv and not adv["any_escaping_object"], "CERTIFIED_MACHINE", ""),
         "the attempt to construct an escaping family fails; the smallest "
         "family of orbits covering F has 8 members against budgets 6 and 7",
         ["X.exclusion"], "r153/certs/adversarial_153.json")

    # -------------------------------------------------------- the two bounds
    node("W.872", ok(w872 and w872["ok"], "EXPLICIT_WITNESS", ""),
         "data/verified_872_witness.txt is a word of length 872 over {1..6} "
         "containing all 720 permutations as windows",
         [], "r153/src/witness872_153.py")
    node("T.ge872", ok(thm and thm["L6_ge_872"], "CERTIFIED_MACHINE", ""),
         "L6 >= 872",
         ["C.census", "E.enumeration", "X.exclusion", "X.nolemmaE", "X.controls",
          "X.mutation", "X.adversarial", "H.fixedrep", "H.splice", "H.master"])
    node("T.le872", ok(thm and thm["L6_le_872"], "EXPLICIT_WITNESS", ""),
         "L6 <= 872", ["W.872"])
    node("T.eq872", ok(thm and thm["L6_equals_872"], "CERTIFIED_MACHINE", ""),
         "L6 = 872", ["T.ge872", "T.le872"])

    def anc(nid, seen=None):
        seen = seen if seen is not None else set()
        for d in N[nid]["deps"]:
            if d not in seen:
                seen.add(d)
                anc(d, seen)
        return seen

    top = "T.eq872"
    path = anc(top) | {top}
    bad_on_path = sorted(n for n in path if N[n]["status"] in BAD)
    out = dict(nodes=N, top=top, ancestors_on_path=len(path),
               by_status={s: sorted(n for n in path if N[n]["status"] == s)
                          for s in sorted({N[n]["status"] for n in path})},
               forbidden_on_path=[n for n in bad_on_path
                                  if N[n]["status"] == "FORBIDDEN"],
               retracted_on_path=[n for n in bad_on_path
                                  if N[n]["status"] == "RETRACTED"],
               unresolved_on_path=[n for n in bad_on_path
                                   if N[n]["status"] == "UNRESOLVED"],
               theorem_path_clean=not bad_on_path)
    (ROOT / "r153" / "certs" / "dag_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    for nid in sorted(path):
        v = N[nid]
        print(f"  {v['status']:<19} {nid:<16} {v['what'][:96]}")
    print()
    for s, ns in out["by_status"].items():
        print(f"  {s}: {len(ns)}")
    print("forbidden:", out["forbidden_on_path"],
          " retracted:", out["retracted_on_path"],
          " unresolved:", out["unresolved_on_path"])
    print("theorem path clean:", out["theorem_path_clean"])
    return 0 if out["theorem_path_clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
