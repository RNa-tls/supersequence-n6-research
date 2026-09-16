#!/usr/bin/env python3
"""Round 160 Phase 16 -- metadata repair for H.master, non-destructively.

The current superseding record is r159/certs/dag_159.json, whose H.master node
reads

    "what":  "MASTER-142: L = 867 + k + Z + H + B*, every term >= 0"
    "where": "src/l6_master_identity_144.py"

Findings of round 160:

  P1  the `where` is CORRECT and not stale: src/l6_master_identity_144.py
      states the identity, derives it from (FO), and verifies the algebra.

  P2  the `what` OVERSTATES what the `where` proves.  That file establishes the
      IDENTITY and says so explicitly ("this module proves that identity is an
      exact rearrangement of (FO), so it carries no extra hypothesis beyond the
      definitions of B* and Z").  It does NOT prove "every term >= 0":

        k  >= 0   needs  G >= 0            [H.splice Lemma A]
                  and    (n-1)O >= P       [a tau-orbit holds at most n-1
                                            distinct pass entries]
        Z  >= 0   needs  D2 + Qs <= R_int  [H.samehex]  and  R_int <= 2g
                  [H.incidence]  and  G = 2g + c + d
        H  >= 0   by definition
        B* >= 0   needs  B* = sum_i tok_i + sigma with both >= 0
                  [H.extract Claims 3 and 4]

      With deps = [] none of these imports is recorded, so the node appears to
      prove four nonnegativity theorems it does not prove.  They are all
      certified elsewhere and already on the theorem path, so this is an
      attribution defect, not a gap.

  P3  the constant is n-specific and its general form is worth recording:
      CONST(n) = n + n! + (n-1)! + n!/(n(n-1)) - 3 = n! + (n-1)! + (n-2)! + n - 3,
      giving 9, 33, 152, 867 for n = 3, 4, 5, 6.

`deps` is left untouched (every AUDITED_HAND_PROOF node carries deps = [] by
convention); the imports are recorded in an additive `derived_from`.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r159" / "certs" / "dag_159.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.master": dict(
        what="MASTER-142 (this node): the IDENTITY L = 867 + k + Z + H + B*, "
             "an exact rearrangement of (FO) L = 844 + G + S + H via "
             "G = Z + D2 + c, O = 24 + k and B* = S + 1 + D2 - O + c.  "
             "General n: CONST(n) = n! + (n-1)! + (n-2)! + n - 3 "
             "(9, 33, 152, 867 for n = 3, 4, 5, 6).  The NONNEGATIVITY of the "
             "four terms is imported, not proved here",
        where="research/RR_L6_H_MASTER_AUDIT.md (round 160); "
              "src/l6_master_identity_144.py; "
              "src/l6_cleanroom_146.py lines 255-270 (independent general-n "
              "derivation of the constant)",
        derived_from="the identity is proved at the `where` and re-derived "
                     "from the raw word in round 160.  k >= 0 needs G >= 0 "
                     "[H.splice Lemma A] and (n-1)O >= P; Z >= 0 needs "
                     "D2 + Qs <= R_int [H.samehex] and R_int <= 2g "
                     "[H.incidence]; B* >= 0 needs B* = sum tok_i + sigma "
                     "with both >= 0 [H.extract Claims 3, 4]; H >= 0 holds by "
                     "definition.  H is the heavy COST sum (w-3)_+, never the "
                     "heavy COUNT h"),
}

IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/theorem_153.json",
    "r153/certs/witness872_153.json", "r155/certs/audit_155.json",
    "r156/THEOREM.md", "r156/certs/provenance_156.json",
    "r157/certs/dag_157.json", "r157/certs/provenance_157.json",
    "r159/certs/dag_159.json", "r159/certs/hash_invariance_159.json",
    "r159/certs/provenance_159.json",
    "src/l6_master_identity_144.py", "src/l6_bookkeeping_144.py",
    "src/l6_cleanroom_146.py", "src/l6_splicing_145.py",
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
    out = dict(supersedes="r159/certs/dag_159.json",
               source_sha256=sha("r159/certs/dag_159.json"),
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
    (ROOT / "r160" / "certs" / "dag_160.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE),
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"]
    (ROOT / "r160" / "certs" / "hash_invariance_160.json").write_text(
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
