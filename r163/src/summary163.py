#!/usr/bin/env python3
"""Round 163 phase 15 -- the consolidated hand-proof inventory certificate.

Every ownership row names a primary owner node and a pattern that must be
present in THAT node's current DAG text.  A row whose pattern is missing is
reported, not quietly dropped.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
C = ROOT / "r163" / "certs"

# assertion -> (primary owner, pattern that must appear in that node's text,
#               imported-from list, note)
OWNERSHIP = [
    ("H.tight: equality row => mu(B) = R_int = 0 => B is a tree",
     "H.incidence", r"2g = mu\(B\) \+ R_int", ["H.tight"],
     "the identity is H.incidence's; H.tight only substitutes g = 0"),
    ("H.tight: all 120 hexagons carry a pass",
     "H.splice", r"every hexagon carries a pass", ["H.tight"],
     "round 155 showed section 9's parenthetical ground is not a derivation; "
     "Lemma A is"),
    ("H.tight: the chain is hexagon-simple",
     "H.tight", r"hexagon-simple", [],
     "immediate from R_int = 0"),
    ("H.tight: |F| = 4c",
     "H.tight", r"\|F\| = 4c", ["H.extract", "H.incidence"],
     "needs G = 2g + c + d with g = d = 0, hence c = G"),
    ("H.tight: the c pure circuits (complete tau-orbits) cover F",
     "H.tight", r"tau-orbits", ["H.splice", "A.orbitfive"],
     "'pure circuit = complete tau-orbit' is splice Lemma E; 'an orbit meets "
     "five distinct hexagons' is A.orbitfive"),
    ("H.samehex: LOWER bound D2 + Qs <= R_int",
     "H.samehex", r"D2 \+ Qs <= R_int", [],
     "proved at the where and re-proved in round 159; NOT a corollary of the "
     "extraction theorem"),
    ("H.samehex: UPPER bound R_int <= 2g",
     "H.incidence", r"R_int <= 2g", ["H.samehex", "H.envelope"],
     "imported, not proved in H.samehex (round 159 correction)"),
    ("H.master: the identity L = 867 + k + Z + H + B*",
     "H.master", r"867 \+ k \+ Z \+ H \+ B", [],
     "an exact rearrangement of (FO); re-derived from the raw word in 160"),
    ("H.master: k >= 0",
     "H.splice", r"sum_h \(m_h - 1\) = G", ["H.models", "H.master"],
     "needs G >= 0 (splice Lemma A) and (n-1)O >= P (= G <= 5k, H.models "
     "Lemma 1.1)"),
    ("H.master: Z >= 0",
     "H.samehex", r"D2 \+ Qs <= R_int", ["H.incidence", "H.master"],
     "needs D2 + Qs <= R_int and R_int <= 2g"),
    ("H.master: B* >= 0",
     "H.extract", r"Claim 3", ["H.master"],
     "B* = sum tok_i + sigma_bar with both >= 0 (Claims 3 and 4)"),
    ("H.master: H >= 0",
     "H.master", r"heavy COST", [],
     "true by definition: H = sum (w-3)_+"),
    ("H.envelope: the four upper bounds a <= D2, bb <= Qs, e <= Z - Qs, "
     "a + bb + e = rep <= R_int <= 2g",
     "H.envelope", r"a <= D2, bb <= Qs, e <= Z - Qs", ["H.extract"],
     "corollaries of r156/THEOREM.md (5) and (7), re-proved independently in "
     "round 158"),
    ("H.envelope: the piece-model LOWER bounds a >= D2 - d and "
     "a + bb >= D2 + Qs - d",
     "H.envelope", r"a >= D2 - d", [],
     "found by round 158; they are what the piece model consumes and they "
     "were in no node's what before that"),
    ("H.splice: Lemmas A-F",
     "H.splice", r"Lemmas A-F", [],
     "split into 23 clauses and re-proved in round 161"),
    ("H.splice: G1, a tau-orbit meets n-1 DISTINCT hexagons",
     "A.orbitfive", r"every tau-orbit meets exactly five hexagons",
     ["H.splice"],
     "a separate CERTIFIED_MACHINE node; round 161 supplies a one-line proof"),
    ("H.fixedrep: existence of a fixed representative of no greater length",
     "H.fixedrep", r"FIXED REPRESENTATIVE W\* = Phi\^m\(W\)", [],
     "L1-L4 and the WLOG corollary; uniqueness is FALSE and is not needed"),
    ("H.fixedrep: the exact bridge to splice C3, L5(b) every selected gap "
     "equals omega",
     "H.fixedrep", r"EVERY SELECTED GAP EQUALS omega", ["H.splice"],
     "C3 is the only splice clause needing it, and it enters as a CHECKABLE "
     "hypothesis, so the dependence is one-way and not circular"),
    ("census row space: G <= 5k",
     "H.models", r"G <= 5k", [],
     "r149 Lemma 1.1; round 163 found it owned by nobody and measured it "
     "load-bearing (332 rows re-open)"),
    ("census row space: G = 2g + c + d with g, c, d >= 0",
     "H.incidence", r"2g := \(G\+1\) - K", ["H.extract", "H.tight"],
     "2g := (G+1) - K >= 0 and even is H.incidence; d := K - c - 1 >= 0 (the "
     "dummy's beta-cycle is never pure) is H.extract; round 163 found the "
     "decomposition in no node's text and measured it the strongest single "
     "assumption (7,848 rows re-open)"),
    ("census row space: required = 120 + G - 5c",
     "H.extract", r"120 \+ G - 5c", [],
     "Claim 1; round 163 found it in no node's text (8 rows re-open if it is "
     "weakened by one pure circuit)"),
    ("census row space: t = k + Z + H + B*",
     "H.master", r"867 \+ k \+ Z \+ H \+ B", [],
     "the master identity in row coordinates (504 rows re-open without it)"),
    ("census row space: 1 <= h <= H when H > 0",
     "H.master", r"heavy COST", [],
     "each heavy joint costs at least one, so the count never exceeds the "
     "cost (664 rows re-open without it)"),
]

CATEGORY = {
    "H.wlog": ("INDEPENDENTLY_REPROVED",
               "paper proof in r149 section 2.4 plus 518,400-pair check; "
               "round 163 re-derived it from the definitions -- transitivity "
               "with trivial stabiliser, and equivariance on all 518,400 "
               "(v,t) pairs for each of five generators of S6 (2,592,000 "
               "pairs, 0 violations), which settles the whole group by "
               "closure.  No dedicated audit ROUND, but the statement is "
               "elementary and now independently reproved"),
    "H.catalogue": ("INDEPENDENTLY_REPROVED",
                    "round 149 enumerated all 518,400 ordered pairs; round "
                    "163 recomputed the catalogue from the definitions and "
                    "matched every number (gap distribution, per-source "
                    "profile 1/1/1/5/710, C1-C4, 0 unclassified).  No "
                    "dedicated audit ROUND"),
    "H.feas": ("MACHINE_ASSISTED_FULLY_AUDITED",
               "round 150 proved the Token-Touched-Orbit theorem and its dual "
               "certificate and checked implementation conformance on 179,850 "
               "cases across five C bodies (0 disagreements) plus 104,448 "
               "arbitrary states with 0 false rejections; round 163 closed the "
               "algorithm identity EXHAUSTIVELY over the operational domain "
               "(220,255 states: production greedy = dual = subset optimum).  "
               "Residual is NOT a hand proof: state-maintenance fidelity in "
               "the search, and the absence of historical per-prune traces"),
    "H.models": ("PREVIOUSLY_FULLY_AUDITED",
                 "dedicated round 149; its verdict OPUS_H_MODELS_PARTIAL had "
                 "exactly one cause, the feas cross-validation gap, which "
                 "round 150 removed.  Round 163 re-derived Lemma 1.1 and "
                 "measured all three models load-bearing (split 439, piece 53, "
                 "merged 3 rows re-open)"),
    "H.tight": ("INDEPENDENTLY_REPROVED", "dedicated round 155"),
    "H.extract": ("INDEPENDENTLY_REPROVED",
                  "dedicated round 156.  Its verdict H_EXTRACT_PARTIAL was "
                  "about PROVENANCE: the mathematics (the corrected theorem "
                  "(0)-(7)) was proved and checked, while the document the "
                  "node cited stated a different, unimplementable cut.  Round "
                  "163 applied the repair round 156 named -- `where` now "
                  "points at r156/THEOREM.md -- so the cause of the PARTIAL is "
                  "gone.  The round-156 artefact is NOT edited and still reads "
                  "H_EXTRACT_PARTIAL"),
    "H.incidence": ("INDEPENDENTLY_REPROVED", "dedicated round 157"),
    "H.envelope": ("INDEPENDENTLY_REPROVED",
                   "dedicated round 158; also a DERIVED_COROLLARY_OF_"
                   "CERTIFIED_NODE (r156/THEOREM.md (5) and (7)) for its four "
                   "upper bounds, but the two piece-model lower bounds are "
                   "its own"),
    "H.samehex": ("INDEPENDENTLY_REPROVED",
                  "dedicated round 159; explicitly NOT a corollary of the "
                  "extraction theorem"),
    "H.master": ("INDEPENDENTLY_REPROVED", "dedicated round 160"),
    "H.splice": ("INDEPENDENTLY_REPROVED", "dedicated round 161"),
    "H.fixedrep": ("INDEPENDENTLY_REPROVED", "dedicated round 162"),
}


def main():
    inv = json.loads((C / "inventory_163.json").read_text())
    ev = json.loads((C / "evidence_163.json").read_text())
    hid = json.loads((C / "hidden_163.json").read_text())
    rec = json.loads((C / "recheck_163.json").read_text())
    dagf = json.loads((C / "dag_163.json").read_text())
    hashes = json.loads((C / "hash_invariance_163.json").read_text())
    cov = json.loads((C / "coverage_163.json").read_text())
    nodes = dagf["dag"]["nodes"]

    own = []
    for claim, owner, rx, imported, note in OWNERSHIP:
        v = nodes.get(owner, {})
        txt = f"{v.get('what')} {v.get('derived_from')} {v.get('where')}"
        own.append(dict(assertion=claim, primary_owner=owner,
                        owner_exists=owner in nodes,
                        pattern=rx,
                        pattern_found_in_owner=bool(re.search(rx, txt)),
                        imported_by_or_from=imported, note=note))
    bad_own = [o["assertion"] for o in own if not o["pattern_found_in_owner"]]

    cats = {}
    for n in inv["hand_proof_nodes"]:
        c, why = CATEGORY[n]
        cats[n] = dict(category=c, reason=why,
                       status=inv["nodes"][n]["status"],
                       direct_dependents=inv["nodes"][n]["direct_dependents"],
                       transitive_dependents=inv["nodes"][n]
                       ["transitive_dependents"],
                       audits=ev["audits"].get(n, []))

    obligations = []          # phase 9: hand-proof obligations only

    out = dict(
        round=163,
        branch=inv["branch"], head=inv["head"],
        dag_path="r163/certs/dag_163.json",
        dag_supersedes=dagf["supersedes"],
        dag_source_sha256=dagf["source_sha256"],
        theorem_status=dict(
            top=inv["walk"]["top"],
            node_count=inv["node_count"],
            theorem_path_node_count=inv["theorem_path_node_count"],
            status_counts=inv["status_counts"],
            forbidden_or_unresolved=inv["walk"]
            ["forbidden_or_unresolved_nodes"],
            sources_with_a_bad_label=inv["walk"]["sources_with_a_bad_label"],
            final_verifier="r153/src/theorem153.py",
            final_verifier_result="L6 >= 872 and L6 <= 872 and L6 = 872"),
        hand_proof_nodes=cats,
        category_counts={c: sum(1 for v in cats.values()
                                if v["category"] == c)
                         for c in sorted({v["category"]
                                          for v in cats.values()})},
        ownership=own,
        ownership_rows_whose_owner_does_not_state_them=bad_own,
        hidden_claims=dict(
            measured_against="r162/certs/dag_162.json (pre-repair)",
            load_bearing=[k for k, v in hid["claims"].items()
                          if v.get("load_bearing")],
            unrepresented_before_repair=(
                hid["load_bearing_but_unrepresented"]
                + hid["load_bearing_only_in_an_equivalent_form"]),
            after_repair=inv["hidden_claim_recheck"],
            still_unrepresented=inv["hidden_claims_still_unrepresented"]),
        provenance=dict(
            defects_now=inv.get("provenance_defects", []),
            historical_defects_resolved={
                "H.incidence wrong where (n=5 era document)":
                    "repaired in round 157; current where exists and states "
                    "the claim",
                "H.feas prose-only where":
                    "repaired in round 163; now r150/PROOF.md and the round-150 "
                    "certificates",
                "H.extract historical prose bug":
                    "recorded in round 156; the DAG citation moved to "
                    "r156/THEOREM.md in round 163, the defective prose is "
                    "hash-pinned and left untouched",
                "incomplete H.envelope what":
                    "repaired in round 158 (the two piece-model lower bounds)",
                "incomplete H.splice what":
                    "repaired in round 161 (Lemmas A-F spelled out)",
                "H.tight where predates its own audit":
                    "repaired in round 163",
                "H.extract placeholder what":
                    "repaired in round 163",
                "H.incidence empty derived_from":
                    "repaired in round 163"},
            unrecorded_corrections=ev["unrecorded_corrections"],
            immutable_files=hashes["files"],
            immutable_all_unchanged=hashes["all_unchanged"]),
        deps_convention=dict(
            all_hand_leaves_have_empty_deps=inv["deps_semantics"]
            ["all_hand_leaves_are_empty"],
            convention="deps is the MACHINE pipeline edge set: which "
                       "certificate consumes which.  Mathematical dependence "
                       "between hand proofs lives in derived_from prose.  The "
                       "12 hand proofs are leaves of the machine pipeline by "
                       "construction, so deps: [] is correct there and "
                       "populating it would confuse the two relations.",
            mathematical_dependencies_recorded_in_prose=inv["deps_semantics"]
            ["prose_dependencies"]),
        independent_rederivations_this_round=dict(
            catalogue=rec["catalogue"]["ordered_pairs"],
            wlog_generator_pairs=rec["wlog"]["generator_equivariance_pairs"],
            feas_multisets=rec["feas_dual"]["multisets_checked"],
            feas_operational_states=rec["feas_operational"]["states_checked"],
            census_baseline=hid["baseline"]),
        remaining_hand_proof_obligations=obligations,
        remaining_non_hand_proof_residual=[
            dict(item="single-implementation capacity cells",
                 node="C.chaincaps / C.piececaps (machine)",
                 why="every capacity the census reads is certified and 0 are "
                     "unread, but the Python checker runs under a 20M-node "
                     "cap, so 247 of the 1,101 chain cells and 109 of the 220 "
                     "piece cells carry ONE implementation's certification -- "
                     "exactly the expensive ones.  The 854 + 111 "
                     "double-implemented cells show 0 cap disagreements",
                 measured=cov["single_implementation_cells_the_census_reads"],
                 source="r163/certs/coverage_163.json"),
            dict(item="feas state-maintenance fidelity",
                 node="C.chaincaps / C.piececaps (machine), via H.feas",
                 why="the lemma and the algorithm identity are now closed "
                     "(220,255 operational states: production greedy = dual = "
                     "subset optimum), and round 150 checked conformance of "
                     "five C bodies on 179,850 cases, but that a checker's "
                     "masks, counts and tokens ARE the (u_q, k) the lemma is "
                     "about is argued, not exhaustively verified, and no "
                     "historical per-prune trace exists.  Mitigated, not "
                     "removed, by checker152 being independent of the "
                     "production solver",
                 source="r150/certs/final150.json cheapest_remaining_risk")],
        capacity_certificate_coverage=cov
    )
    out["ok"] = (not bad_own and not out["hidden_claims"]
                 ["still_unrepresented"]
                 and not ev["unrecorded_corrections"]
                 and hashes["all_unchanged"]
                 and not inv["walk"]["forbidden_or_unresolved_nodes"])
    (C / "hand_proof_inventory_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(
        node_count=out["theorem_status"]["node_count"],
        theorem_path_node_count=out["theorem_status"]
        ["theorem_path_node_count"],
        hand_proof_nodes=len(cats),
        category_counts=out["category_counts"],
        ownership_rows=len(own),
        ownership_rows_failing=bad_own,
        still_unrepresented=out["hidden_claims"]["still_unrepresented"],
        provenance_defects=out["provenance"]["defects_now"],
        remaining_hand_proof_obligations=obligations,
        ok=out["ok"]), ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
