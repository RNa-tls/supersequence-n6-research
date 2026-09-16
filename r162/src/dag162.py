#!/usr/bin/env python3
"""Round 162 Phase 23 -- metadata repair for H.fixedrep, non-destructively.

The current superseding record is r161/certs/dag_161.json, whose H.fixedrep
node reads

    "what":  "every cover has a fixed representative of no greater length"
    "where": "src/l6_fixed_representative_145.py"

Findings of round 162:

  R1  the `where` is CORRECT: src/l6_fixed_representative_145.py lines 10-78
      state and prove Lemmas 1-5 and the corollary.

  R2  the `what` states only the EXISTENCE half.  What the rest of the proof
      consumes is Lemma 5: at a fixed point (a) the word is its own
      maximum-overlap spelling, (b) EVERY SELECTED GAP EQUALS omega, and
      (c) every non-selected permutation window is a repeat lying strictly
      inside a connector interval.  Clause (b) is precisely the hypothesis of
      splice clause C3 -- the only splice clause that needs it -- and (c) is
      what H.samehex's index-increase step uses.  A `what` that mentions only
      "a representative of no greater length" hides the load-bearing content.

  R3  the node is NOT a group-action normalisation.  Phi re-spells the word at
      maximum overlap and trims it; it does not relabel, rotate or conjugate,
      and it can strictly SHORTEN the word.  The left-S_n normalisation is the
      separate node H.wlog, which acts on a different object (the starting
      port inside the capacity search).  The two commute: Phi(pi.W) = pi.Phi(W).

  R4  no structural data is preserved by Phi: beta, nu, the pass decomposition
      and even the SELECTED SEQUENCE can change (169 observed cases).  Nothing
      needs to be preserved, because the only thing transferred to the
      normalised word is its LENGTH.

`deps` is left untouched (convention); the above is recorded in an additive
`derived_from`.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r161" / "certs" / "dag_161.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.fixedrep": dict(
        what="the fixed-representative reduction: Phi(W) re-spells a cover at "
             "maximum overlap over its first-occurrence sequence and trims it; "
             "(L1) Phi(W) is a cover, (L2) |Phi(W)| <= |W_trim| <= |W|, "
             "(L3) equality forces W = Phi(W), (L4) hence every cover has a "
             "FIXED REPRESENTATIVE W* = Phi^m(W) with |W*| <= |W| within "
             "|W| - (n! + n - 1) non-fixed steps, and (L5) at a fixed point "
             "(a) W* is its own maximum-overlap spelling, (b) EVERY SELECTED "
             "GAP EQUALS omega, (c) every non-selected permutation window is a "
             "repeat strictly inside a connector interval, and W* is trimmed.  "
             "Corollary: a lower bound for all fixed representatives is a "
             "lower bound for all covers",
        where="research/RR_L6_H_FIXEDREP_AUDIT.md (round 162); "
              "src/l6_fixed_representative_145.py lines 10-78",
        derived_from="Phi is a REWRITING operator, not a group action: no "
                     "relabelling, no rotation, no conjugation, and it may "
                     "strictly shorten the word.  Nothing structural is "
                     "preserved -- beta, nu, the pass decomposition and even "
                     "the selected sequence may change -- because the only "
                     "thing transferred is the LENGTH.  Clause L5(b) is the "
                     "hypothesis of splice clause C3, the sole splice clause "
                     "that needs it (round 161); L5(c) is used by H.samehex.  "
                     "The proof uses NO splice lemma, so the dependence "
                     "H.fixedrep -> C3 is one-way and not circular.  The "
                     "left-S_n normalisation H.wlog acts on a different object "
                     "and commutes with Phi: Phi(pi.W) = pi.Phi(W)"),
}

IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/theorem_153.json",
    "r153/certs/witness872_153.json", "r155/certs/audit_155.json",
    "r156/THEOREM.md", "r156/certs/provenance_156.json",
    "r157/certs/dag_157.json", "r157/certs/provenance_157.json",
    "r161/certs/dag_161.json", "r159/certs/hash_invariance_159.json",
    "r159/certs/provenance_159.json",
    "src/l6_fixed_representative_145.py", "src/l6_splicing_145.py",
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
    out = dict(supersedes="r161/certs/dag_161.json",
               source_sha256=sha("r161/certs/dag_161.json"),
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
    (ROOT / "r162" / "certs" / "dag_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE),
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"]
    (ROOT / "r162" / "certs" / "hash_invariance_162.json").write_text(
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
