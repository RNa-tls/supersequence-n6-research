#!/usr/bin/env python3
"""Round 159 Phase 16 -- metadata repair for H.samehex, non-destructively.

The current superseding record is r158/certs/dag_158.json, whose H.samehex node
reads

    "what":  "SAME-HEX: D2 + Qs <= R_int <= 2g"
    "where": "src/l6_same_hex_145.py"

Findings of round 159:

  M1  the `where` is CORRECT and not stale: src/l6_same_hex_145.py lines 7-47
      state and prove exactly D2 + Qs <= R_int.

  M2  the `what` is INACCURATE about authorship.  The chain it records bundles
      TWO theorems from TWO nodes: `D2 + Qs <= R_int` is proved at the `where`,
      but `R_int <= 2g` is H.incidence's (round 157: 2g = mu(B) + R_int with
      mu(B) >= 0) and is only CITED there as a corollary.  With deps = [] the
      import is nowhere recorded, so the node appears to prove more than its
      source does.

  M3  what the row enumeration actually consumes is the COROLLARY
      D2 + Qs <= 2g (r152/src/rows152.py lines 54 and 59: `D2 > 2*g` is
      rejected and `Qs` runs to `min(Z, 2*g - D2)`), which needs both halves.

The `what` is rewritten to attribute each half correctly and to name the
corollary the census consumes; `where` is extended with this round's audit
document.  `deps` is left untouched (the published DAG gives every
AUDITED_HAND_PROOF node deps = [] by convention, and H.incidence is already on
the theorem path), and the import is recorded in an additive `derived_from`.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r158" / "certs" / "dag_158.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.samehex": dict(
        what="SAME-HEX (this node): D2 + Qs <= R_int.  Combined with "
             "H.incidence's R_int <= 2g this gives the corollary the row "
             "enumeration consumes, D2 + Qs <= 2g, hence D2 <= 2g, "
             "Qs <= min(Z, 2g - D2) and Z >= Qs >= 0",
        where="research/RR_L6_H_SAMEHEX_AUDIT.md (round 159); "
              "src/l6_same_hex_145.py lines 7-47",
        derived_from="the lower half D2 + Qs <= R_int is proved at the `where` "
                     "and re-proved independently in round 159; the upper half "
                     "R_int <= 2g is H.incidence (round 157) and is imported, "
                     "not proved here.  It is NOT a corollary of the corrected "
                     "Extraction Theorem: that theorem bounds the POST-CUT "
                     "repeat count rep, and D2 + Qs > rep occurs on real "
                     "covers"),
}

IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/theorem_153.json",
    "r153/certs/witness872_153.json", "r155/certs/audit_155.json",
    "r156/THEOREM.md", "r156/certs/provenance_156.json",
    "r157/certs/dag_157.json", "r157/certs/provenance_157.json",
    "r158/certs/dag_158.json", "r158/certs/hash_invariance_158.json",
    "r158/certs/provenance_158.json",
    "src/l6_same_hex_145.py", "src/l6_splicing_145.py",
    "src/l6_incidence_144.py", "src/l6_envelope_146.py",
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
    out = dict(supersedes="r158/certs/dag_158.json",
               source_sha256=sha("r158/certs/dag_158.json"),
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
    (ROOT / "r159" / "certs" / "dag_159.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE),
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"]
    (ROOT / "r159" / "certs" / "hash_invariance_159.json").write_text(
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
