#!/usr/bin/env python3
"""Round 158 Phase 13/15 -- metadata repair for H.envelope, non-destructively.

The current superseding metadata record is r157/certs/dag_157.json, whose
H.envelope node reads

    "what":  "a <= D2, bb <= Qs, e <= Z - Qs, a + bb + e <= 2g"
    "where": "src/l6_envelope_146.py"

Findings of round 158:

  N1  the `where` is CORRECT and not stale.  src/l6_envelope_146.py lines 6-33
      state all four inequalities AND already carry the corrected derivation
      of e <= Z - Qs, including the step `x + y <= d` that r149/PROOF.md's
      restatement omits.  Nothing to repair there; the pointer is extended,
      not replaced.

  N2  the `what` is INCOMPLETE relative to what C.census actually consumes.
      The piece model (r152/src/rows152.py::piece_bound, inherited from
      src/l6_coupled_144.py::evaluate_row) reads

          nA   = max(0, D2 - d)             a LOWER bound on a
          m_lo = max(1, D2 + Qs - d + 1)    a LOWER bound on a + bb, plus 1

      Raising either of them lowers the piece bound, so both must be genuine
      LOWER bounds or the census can close a row a real cover realises.
      Neither appears in the node's `what`.

  N3  round 156 proves the exact form  a + bb + e = rep <= R_int <= 2g,
      of which the recorded `a + bb + e <= 2g` is the weaker consequence.

  N4  the node is a COROLLARY of r156/THEOREM.md clauses (5) and (7); round
      158 re-proves it independently, so it does not rest on the H_EXTRACT
      PARTIAL verdict, which concerns the cut recipe as WRITTEN in
      src/l6_extraction_145.py rather than those clauses.

The `deps` list is left untouched: every AUDITED_HAND_PROOF node in the
published DAG carries deps=[] as a convention, and the real dependencies
(H.extract's Claim 5, H.incidence, H.samehex) are already on the theorem
path.  The derivation is recorded in a new additive `derived_from` field.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r157" / "certs" / "dag_157.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.envelope": dict(
        what="a <= D2, bb <= Qs, e <= Z - Qs, and a + bb + e = rep <= R_int "
             "<= 2g; plus the two LOWER bounds the piece model consumes, "
             "a >= D2 - d and a + bb >= D2 + Qs - d",
        where="research/RR_L6_H_ENVELOPE_AUDIT.md (round 158); "
              "src/l6_envelope_146.py lines 6-33; "
              "r156/THEOREM.md clauses (5) and (7)",
        derived_from="a corollary of r156/THEOREM.md (5) and (7); "
                     "re-proved independently in round 158 from "
                     "a = D2 - x, bb = Qs - y, x + y <= d together with "
                     "rep <= R_int (r156 Claim 5), R_int <= 2g (H.incidence), "
                     "D2 + Qs <= R_int (H.samehex) and z = 2g + d, Z = z - D2"),
}

IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/theorem_153.json",
    "r153/certs/witness872_153.json",
    "r155/certs/audit_155.json",
    "r156/THEOREM.md", "r156/certs/provenance_156.json",
    "r157/certs/dag_157.json", "r157/certs/hash_invariance_157.json",
    "r157/certs/provenance_157.json",
    "src/l6_envelope_146.py", "src/l6_coupled_144.py",
    "src/l6_extraction_145.py", "src/l6_incidence_144.py",
    "src/l6_same_hex_145.py", "r152/src/rows152.py",
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
    prev = json.loads(SRC.read_text())
    orig = prev["dag"]
    nodes = json.loads(json.dumps(orig["nodes"]))
    changes = []
    for nid, fields in REPAIR.items():
        for f, v in fields.items():
            changes.append(dict(node=nid, field=f,
                                old=nodes[nid].get(f), new=v))
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
    out = dict(
        supersedes="r157/certs/dag_157.json",
        source_sha256=sha("r157/certs/dag_157.json"),
        earlier_repairs=prev.get("repairs"),
        repairs=changes,
        diff_against_source=sorted(diff),
        diff_is_exactly_the_repairs=(sorted(diff) == expected),
        every_derived_field_unchanged=derived_same,
        statuses_unchanged=all(orig["nodes"][k]["status"] == nodes[k]["status"]
                               for k in nodes),
        deps_unchanged=all(orig["nodes"][k]["deps"] == nodes[k]["deps"]
                           for k in nodes),
        carried_defects_not_repaired_here=
        prev.get("carried_defects_not_repaired_here"),
        dag=new)
    (ROOT / "r158" / "certs" / "dag_158.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE),
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"]
    (ROOT / "r158" / "certs" / "hash_invariance_158.json").write_text(
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
