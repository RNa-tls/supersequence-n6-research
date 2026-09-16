#!/usr/bin/env python3
"""Round 156 Phase 14 -- what does H.extract actually depend on?

r153/certs/dag_153.json records  H.extract  with  deps: []  -- i.e. as a node
that needs nothing.  This file lists the statements the reconstructed proof
really uses, says where each of them is proved, and cites the ablation in
r156/certs/abstract_156.json that shows the dependency is not decorative.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

NEEDED = [
    dict(node="H.fixedrep",
         statement="W is a fixed representative: every selected gap equals "
                   "omega, so every joint is a SHORTEST connector and the "
                   "catalogue applies",
         used_for="the whole pass/joint construction",
         where="src/l6_fixed_representative_145.py",
         evidence="r156/certs/inputs_156.json: `fixed` verified on every word"),
    dict(node="H.splice / Lemma A",
         statement="the arcs of a hexagon partition it; sum_h (m_h - 1) = G",
         used_for="P = n!/n + G, hence `required` = n!/n + G - (n-1)c",
         where="src/l6_splicing_145.py lines 16-19",
         evidence="r156/certs/inputs_156.json: Lemma A re-verified"),
    dict(node="H.splice / Lemma B-D",
         statement="nu is a permutation whose cycles are the hexagons; "
                   "beta = T alpha^{-1} is a permutation with beta(nu(i))=i+1",
         used_for="the beta components the chains are cut out of",
         where="src/l6_splicing_145.py lines 21-47",
         evidence="r156/certs/inputs_156.json: Lemmas B-D re-verified"),
    dict(node="H.splice / Lemma E",
         statement="a pure clean-E beta component has exactly n-1 passes, they "
                   "are all n-1 elements of ONE tau-orbit, and no other pass "
                   "lies in that orbit",
         used_for="Claim 1 (the deleted ports number exactly (n-1)c) and "
                  "Claim 4 (sigma >= 0)",
         where="src/l6_splicing_145.py lines 49-57",
         evidence="abstract_156.json ablation drop_LemmaE_size breaks C1/C2 "
                  "in 508 cases; drop_LemmaE_orbit_and_cap breaks C4one in "
                  "825 cases"),
    dict(node="H.splice / Lemma F",
         statement="blocks = P - cleanE = S + 1 + D2, unchanged by deleting a "
                   "pure circuit",
         used_for="the closed form B* = S + 1 + D2 - O + c that MASTER-142 "
                  "substitutes; Claim 3's identity itself needs only "
                  "blocks = P - cleanE",
         where="src/l6_splicing_145.py lines 59-63",
         evidence="r156/src/extract156.py checks LemmaF on every word"),
    dict(node="H.catalogue",
         statement="a clean-E joint sends the pass entry v to tau(v) (same "
                   "tau-orbit); a type-A joint to sigma(v) and a type-B joint "
                   "to sigma^2(v) (same hexagon)",
         used_for="Claim 3 (only clean E keeps the orbit) and Claim 5 "
                  "(a retained A/B edge occupies a hexagon repeat)",
         where="r149/PROOF.md section 2",
         evidence="abstract_156.json ablation drop_E_preserves_orbit breaks "
                  "C3/C3sum in 3,660 cases; adversarial_156.json corrupts an "
                  "A label and is caught in 454/454 attempts"),
    dict(node="H.incidence",
         statement="R_int <= 2g",
         used_for="only to turn Claim 5's bound R_int into the row budget 2g; "
                  "Claim 5 itself is proved against R_int",
         where="src/l6_incidence_144.py + research/RR_L6_PROOF_145_CLAUDE.md "
               "section 5",
         evidence="r156/src/extract156.py checks K + R_int <= G+1 on every "
                  "word"),
]

NOT_NEEDED = [
    dict(node="H.samehex",
         statement="D2 + Qs <= R_int",
         why="Claims 1-5 never use it; it is a separate statement about the "
             "whole word, consumed by the ROW ENUMERATION (Qs <= 2g - D2), "
             "not by the extraction"),
    dict(node="the five-type beta-component classification",
         statement="every beta component is E-clean / R2 / S / P / M",
         why="no such theorem exists in this repository "
             "(research/RR_BETA_COMPONENT_FIVE_TYPE_AUDIT.md) and the "
             "extraction never branches on more than pure / non-pure -- "
             "verified mechanically in r156/certs/"
             "hidden_classification_156.json"),
]


def main():
    dag = json.loads((ROOT / "r153" / "certs" / "dag_153.json").read_text())
    node = dag["nodes"]["H.extract"]
    missing = [d["node"] for d in NEEDED
               if d["node"].split(" /")[0] not in node["deps"]]
    # mitigation: is every real dependency nevertheless ON the theorem path?
    nodes = dag["nodes"]
    reach, stack = set(), [dag["top"]]
    while stack:
        x = stack.pop()
        if x in reach:
            continue
        reach.add(x)
        stack += nodes[x]["deps"]
    real = sorted({d["node"].split(" /")[0] for d in NEEDED})
    off_path = [x for x in real if x not in reach]
    hand = [k for k, v in nodes.items()
            if v["status"] == "AUDITED_HAND_PROOF"]
    out = dict(dag_node=node,
               declared_deps=node["deps"],
               required_deps=NEEDED,
               not_required=NOT_NEEDED,
               declared_but_missing=sorted(set(missing)),
               dag_metadata_defect=bool(missing),
               convention_note="every AUDITED_HAND_PROOF node in dag153.py is "
                               "written with deps=[]; the empty list is a "
                               "convention, not a claim of independence",
               hand_proof_nodes_with_empty_deps=sorted(
                   k for k in hand if not nodes[k]["deps"]),
               all_real_deps_on_the_theorem_path=not off_path,
               real_deps_off_path=off_path,
               nodes_on_path=len(reach),
               where_exists=(ROOT / node["where"]).exists())
    (ROOT / "r156" / "certs" / "deps_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(declared=node["deps"],
                          missing=out["declared_but_missing"],
                          where=node["where"],
                          where_exists=out["where_exists"]),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
