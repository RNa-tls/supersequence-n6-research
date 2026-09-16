#!/usr/bin/env python3
"""Round 161 Phase 23 -- metadata repair for H.splice, non-destructively.

The current superseding record is r160/certs/dag_160.json, whose H.splice node
reads

    "what":  "successor splicing and the beta permutation"
    "where": "src/l6_splicing_145.py"

Findings of round 161:

  S1  the `where` is CORRECT: src/l6_splicing_145.py lines 16-66 state and
      prove Lemmas A-F.

  S2  the `what` UNDER-DESCRIBES the node.  It names an operation, not the six
      lemmas the rest of the proof consumes:
        A  the arcs of a hexagon partition it; every hexagon carries a pass;
           sum_h (m_h - 1) = G                      -> H.master, H.tight
        B  nu is a permutation whose cycles are the hexagons; c(nu) = n!/n
           -> H.incidence (c(alpha) = n!/n + 1)
        C  the joint source is end(v_nu(i)); the reassignment changes source,
           target, gap, spelling and hidden windows NOT AT ALL; the reassigned
           edge is a shortest connector                 -> H.samehex, H.catalogue
        D  beta = T alpha^{-1} is a permutation with beta(nu(i)) = i+1
           -> H.incidence, H.samehex, H.extract
        E  a pure clean-E beta-cycle is exactly a complete tau-orbit of n-1
           passes, and no other pass lies in that orbit  -> H.extract, H.tight
        F  blocks = P - cleanE = S + 1 + D2, unchanged by deleting a pure
           circuit                                        -> H.master, H.extract

  S3  only clause C3 (`the reassigned edge is a SHORTEST connector`) uses the
      fixed-representative hypothesis.  Everything else needs only that W is a
      COVER.  Verified: on 92 covers that are not fixed representatives,
      exactly C3 breaks and no other clause does.

  S4  the CONVERSE of Lemma E (a complete tau-orbit forms a pure circuit) is
      FALSE -- it fails on 324 of 646 real covers -- and is nowhere used.

`deps` is left untouched (convention); the split is recorded in an additive
`derived_from`.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r160" / "certs" / "dag_160.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.splice": dict(
        what="successor splicing and the beta permutation, i.e. Lemmas A-F of "
             "src/l6_splicing_145.py: (A) the arcs of a hexagon partition it, "
             "every hexagon carries a pass, sum_h (m_h - 1) = G; (B) nu is a "
             "permutation whose cycles are the hexagons, c(nu) = n!/n; (C) the "
             "joint source is end(v_nu(i)) and the reassignment changes source, "
             "target, gap, spelling and hidden windows not at all, the "
             "reassigned edge being a shortest connector; (D) beta = T "
             "alpha^{-1} is a permutation with beta(nu(i)) = i+1 and "
             "c(alpha) = n!/n + 1; (E) a pure clean-E beta-cycle is exactly a "
             "complete tau-orbit of n-1 passes and no other pass lies in that "
             "orbit; (F) blocks = P - cleanE = S + 1 + D2, unchanged by "
             "deleting a pure circuit",
        where="research/RR_L6_H_SPLICE_AUDIT.md (round 161); "
              "src/l6_splicing_145.py lines 16-66",
        derived_from="A-F are proved at the `where` and re-proved clause by "
                     "clause in round 161.  Hypotheses: A, B, D, E, F need "
                     "only that W is a COVER; only clause C3 (shortest "
                     "connector) uses the fixed-representative hypothesis "
                     "gap = omega, which is a checkable property of the given "
                     "word and not H.fixedrep's WLOG theorem.  Lemma F's count "
                     "cleanE = P-1-S-D2 rests on the local fact that the only "
                     "gap-2 targets out of end(v) are tau(v) and sigma(v), "
                     "exhausted for n = 3..6.  The CONVERSE of Lemma E is "
                     "false and is not used.  That a tau-orbit meets n-1 "
                     "DISTINCT hexagons is the separate node A.orbitfive; "
                     "round 161 supplies a one-line proof of it"),
}

IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/theorem_153.json",
    "r153/certs/witness872_153.json", "r155/certs/audit_155.json",
    "r156/THEOREM.md", "r156/certs/provenance_156.json",
    "r157/certs/dag_157.json", "r157/certs/provenance_157.json",
    "r160/certs/dag_160.json", "r159/certs/hash_invariance_159.json",
    "r159/certs/provenance_159.json",
    "src/l6_splicing_145.py", "src/l6_fixed_representative_145.py",
    "src/l6_master_identity_144.py", "src/l6_cleanroom_146.py",
    "src/l6_same_hex_145.py", "src/l6_incidence_144.py",
    "r152/src/rows152.py", "data/verified_872_witness.txt",
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
    prev = json.loads(SRC.read_text())
    orig = prev["dag"]
    nodes = json.loads(json.dumps(orig["nodes"]))
    changes = []
    for nid, fields in REPAIR.items():
        for f, v in fields.items():
            changes.append(dict(node=nid, field=f, old=nodes[nid].get(f),
                                new=v))
            nodes[nid][f] = v
    new = derive(nodes, orig["top"])
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
    out = dict(supersedes="r160/certs/dag_160.json",
               source_sha256=sha("r160/certs/dag_160.json"),
               earlier_repairs=prev.get("repairs"),
               repairs=changes,
               diff_against_source=sorted(diff),
               diff_is_exactly_the_repairs=(sorted(diff) == expected),
               every_derived_field_unchanged=derived_same,
               statuses_unchanged=all(
                   orig["nodes"][k]["status"] == nodes[k]["status"]
                   for k in nodes),
               deps_unchanged=all(orig["nodes"][k]["deps"] == nodes[k]["deps"]
                                  for k in nodes),
               carried_defects_not_repaired_here=
               prev.get("carried_defects_not_repaired_here"),
               dag=new)
    (ROOT / "r161" / "certs" / "dag_161.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE),
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"]
    (ROOT / "r161" / "certs" / "hash_invariance_161.json").write_text(
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
