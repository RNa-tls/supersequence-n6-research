#!/usr/bin/env python3
"""Round 158 Phase 3/13 -- is H.envelope already implied by Round 156?

For each H.envelope inequality this records the corresponding clause of
r156/THEOREM.md, the classification, and the exact quoted text -- and checks
mechanically that the quoted text is really present in that file, so the
claim "identical" is anchored to the artefact rather than to a summary.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
THM = ROOT / "r156" / "THEOREM.md"

MAP = [
    dict(ineq="(1)  a <= D2",
         r156_clause="(7)",
         quote="`a := sum a_i <= D2`",
         classification="IDENTICAL_TO_R156",
         note="verbatim clause of r156/THEOREM.md (7)"),
    dict(ineq="(2)  bb <= Qs",
         r156_clause="(7)",
         quote="`bb := sum bb_i <= Qs`",
         classification="IDENTICAL_TO_R156",
         note="verbatim clause of r156/THEOREM.md (7)"),
    dict(ineq="(3)  e <= Z - Qs",
         r156_clause="(7)",
         quote="`e := sum e_i <= Z - Qs`",
         classification="IDENTICAL_TO_R156",
         note="verbatim clause of r156/THEOREM.md (7); the corrected "
              "derivation (cut A/B are openings only, openings number d) is "
              "given there and re-proved independently in round 158"),
    dict(ineq="(4)  a + bb + e <= 2g",
         r156_clause="(5)",
         quote="`sum (a+bb+e) <= R_int <= 2g`",
         classification="STRICTLY_WEAKER_THAN_R156",
         note="r156 (5) proves the exact form a+bb+e = rep <= R_int and then "
              "R_int <= 2g, so the node's (4) is the weaker consequence"),
]

EXTRA = [
    dict(ineq="(L1) a >= D2 - d",
         consumer="piece model, nA = max(0, D2 - d) in "
                  "r152/src/rows152.py::piece_bound and "
                  "src/l6_coupled_144.py::evaluate_row",
         classification="DIFFERENT_STATEMENT",
         note="a LOWER bound; not stated in H.envelope's `what` nor in "
              "r156/THEOREM.md (7), but an immediate consequence of the "
              "identity a = D2 - x with x <= d that the proof of (7) "
              "establishes en route"),
    dict(ineq="(L2) a + bb >= D2 + Qs - d",
         consumer="piece model, m_lo = max(1, D2 + Qs - d + 1)",
         classification="DIFFERENT_STATEMENT",
         note="same source: a + bb = D2 + Qs - (x + y) and x + y <= d"),
]


def main():
    txt = THM.read_text()
    for row in MAP:
        row["quote_present_in_r156_THEOREM"] = row["quote"] in txt
    out = dict(
        r156_theorem_sha256=hashlib.sha256(THM.read_bytes()).hexdigest(),
        r156_verdict="H_EXTRACT_PARTIAL",
        r156_verdict_scope="the PARTIAL verdict concerns the cut recipe as "
                           "WRITTEN in src/l6_extraction_145.py and "
                           "r149/PROOF.md, not clauses (5) and (7) of "
                           "r156/THEOREM.md, which are proved and "
                           "exhaustively verified there",
        envelope_inequalities=MAP,
        additional_inequalities_consumed_by_the_census=EXTRA,
        all_four_are_r156_corollaries=all(
            r["classification"] in ("IDENTICAL_TO_R156",
                                    "STRICTLY_WEAKER_THAN_R156")
            for r in MAP),
        all_quotes_found=all(r["quote_present_in_r156_THEOREM"] for r in MAP))
    out["ok"] = out["all_quotes_found"] and out["all_four_are_r156_corollaries"]
    (ROOT / "r158" / "certs" / "implies_158.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("envelope_inequalities",
                                   "additional_inequalities_consumed_by_the_census")},
                     ensure_ascii=False, indent=1))
    for r in MAP:
        print(" ", r["ineq"], r["classification"],
              "quote_found=" + str(r["quote_present_in_r156_THEOREM"]))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
