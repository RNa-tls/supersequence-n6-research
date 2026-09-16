#!/usr/bin/env python3
"""Round 157 Phase 14 -- provenance repair for H.incidence, non-destructively.

r153/certs/dag_153.json records

    "H.incidence": {"what":  "K + R_int <= G + 1, with equality iff the
                              incidence graph is a tree",
                    "where": "research/RR_INCIDENCE_FOREST_LEMMA.md"}

Two things are wrong with that record, and both are ROUND-153 REGRESSIONS:
r148/src/dag148.py and r150/certs/dag150.json both carried the correct version.

  W1  `where` points at an n = 5-era document about union-find redundant
      unions in an RR corpus.  It does not state K + R_int <= G + 1 at all.
      The canonical sources are src/l6_incidence_144.py (statement, parity,
      abstract random check) and src/l6_incidence_graph_146.py (the explicit
      bipartite graph, connectivity and the tree equivalence).

  W2  the PARITY clause `K = G + 1 (mod 2)` was dropped from `what`.  It is
      load-bearing: the row enumeration writes K = G + 1 - 2g and enumerates
      integer g >= 0, so a real cover with G + 1 - K odd would match no
      enumerated row and would escape the census.

This file does NOT edit dag153.py or dag_153.json.  It reads the published
DAG, applies the repair, RE-DERIVES every computed field from the node table,
checks that the diff against the original is exactly the two repaired strings,
and writes r157/certs/dag_157.json as the superseding metadata record.  It
then verifies that every mathematical certificate in the repository still has
the sha256 it had before.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r153" / "certs" / "dag_153.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.incidence": dict(
        what="K + R_int <= G + 1 with K = G + 1 (mod 2); equality iff the "
             "SIMPLE bipartite incidence graph B is a tree",
        where="research/RR_L6_H_INCIDENCE_AUDIT.md (round 157); "
              "src/l6_incidence_144.py lines 1-35; "
              "src/l6_incidence_graph_146.py lines 9-56"),
}

# defects recorded but deliberately NOT repaired here: they belong to other
# nodes and this round audits H.incidence only.
CARRIED_DEFECTS = [
    dict(node="H.feas",
         field="where",
         recorded='"round 150 feasibility audit"',
         correct="r150/PROOF.md",
         found_in="research/RR_L6_HAND_PROOF_NODE_INVENTORY.md"),
    dict(node="H.extract",
         field="where / statement",
         recorded="src/l6_extraction_145.py",
         correct="the written cut recipe there is defective; the repaired "
                 "statement is r156/THEOREM.md",
         found_in="research/RR_L6_H_EXTRACT_AUDIT.md (round 156, PARTIAL)"),
    dict(node="all AUDITED_HAND_PROOF nodes",
         field="deps",
         recorded="[]",
         correct="a convention, not a claim of independence; every real "
                 "dependency is nevertheless on the theorem path",
         found_in="r156/certs/deps_156.json"),
]

# every artefact whose hash must be unchanged by a metadata repair
IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/eqcompare_153.json",
    "r153/certs/covertree_153.json", "r153/certs/coexist_153.json",
    "r153/certs/adversarial_153.json", "r153/certs/theorem_153.json",
    "r153/certs/mutations_153.json", "r153/certs/witness872_153.json",
    "r155/certs/audit_155.json", "r156/certs/provenance_156.json",
    "src/l6_incidence_144.py", "src/l6_incidence_graph_146.py",
    "src/l6_splicing_145.py", "src/l6_extraction_145.py",
    "data/verified_872_witness.txt",
]


def sha(p):
    q = ROOT / p
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


def derive(nodes, top):
    def anc(nid, seen):
        for d in nodes[nid]["deps"]:
            if d not in seen:
                seen.add(d)
                anc(d, seen)
        return seen
    path = anc(top, set()) | {top}
    bad = sorted(n for n in path if nodes[n]["status"] in BAD)
    return dict(nodes=nodes, top=top, ancestors_on_path=len(path),
                by_status={s: sorted(n for n in path
                                     if nodes[n]["status"] == s)
                           for s in sorted({nodes[n]["status"]
                                            for n in path})},
                forbidden_on_path=[n for n in bad
                                   if nodes[n]["status"] == "FORBIDDEN"],
                retracted_on_path=[n for n in bad
                                   if nodes[n]["status"] == "RETRACTED"],
                unresolved_on_path=[n for n in bad
                                    if nodes[n]["status"] == "UNRESOLVED"],
                theorem_path_clean=not bad)


def main():
    before = {p: sha(p) for p in IMMUTABLE}
    orig = json.loads(SRC.read_text())
    nodes = json.loads(json.dumps(orig["nodes"]))        # deep copy
    changes = []
    for nid, fields in REPAIR.items():
        if nid not in nodes:
            print(f"node {nid} absent", file=sys.stderr)
            return 1
        for f, v in fields.items():
            changes.append(dict(node=nid, field=f,
                                old=nodes[nid][f], new=v))
            nodes[nid][f] = v
    new = derive(nodes, orig["top"])

    # ---- the diff must be EXACTLY the repaired strings
    diff = []
    for nid in sorted(set(orig["nodes"]) | set(nodes)):
        a, b = orig["nodes"].get(nid), nodes.get(nid)
        if a is None or b is None:
            diff.append(("node added/removed", nid))
            continue
        for f in sorted(set(a) | set(b)):
            if a.get(f) != b.get(f):
                diff.append((nid, f))
    expected = sorted((c["node"], c["field"]) for c in changes)
    derived_same = all(new[k] == orig[k] for k in
                       ("top", "ancestors_on_path", "by_status",
                        "forbidden_on_path", "retracted_on_path",
                        "unresolved_on_path", "theorem_path_clean"))
    out = dict(
        supersedes="r153/certs/dag_153.json",
        source_sha256=sha("r153/certs/dag_153.json"),
        repairs=changes,
        diff_against_source=sorted(diff),
        diff_is_exactly_the_repairs=(sorted(diff) == expected),
        every_derived_field_unchanged=derived_same,
        statuses_unchanged=all(orig["nodes"][k]["status"] == nodes[k]["status"]
                               for k in nodes),
        deps_unchanged=all(orig["nodes"][k]["deps"] == nodes[k]["deps"]
                           for k in nodes),
        carried_defects_not_repaired_here=CARRIED_DEFECTS,
        dag=new)
    (ROOT / "r157" / "certs" / "dag_157.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")

    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE),
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"]
    (ROOT / "r157" / "certs" / "hash_invariance_157.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=1) + "\n")

    ok = (out["diff_is_exactly_the_repairs"] and derived_same
          and out["statuses_unchanged"] and out["deps_unchanged"]
          and inv["all_unchanged"] and new["theorem_path_clean"])
    print(json.dumps(dict(repairs=[(c["node"], c["field"]) for c in changes],
                          diff=sorted(diff),
                          diff_is_exactly_the_repairs=
                          out["diff_is_exactly_the_repairs"],
                          derived_unchanged=derived_same,
                          theorem_path_clean=new["theorem_path_clean"],
                          immutable_files_unchanged=inv["all_unchanged"],
                          ok=ok), ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
