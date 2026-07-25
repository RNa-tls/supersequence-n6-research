#!/usr/bin/env python3
"""Round 17, section 1: evidence audit of the RR research line's core
claims (Rounds 11-16). This script does not run new computation -- it
encodes, as structured data, the audit performed by reading the cited
research documents and cross-checking each claim's actual evidential
basis against outputs/*.json this session already produced (Round 16's
corpus-completeness discovery and Round 17's fresh uncapped-local
universe).

Proof-status vocabulary used throughout this project's history vs the
vocabulary this audit standardizes on:
  historical label -> audited/corrected label
  "유한 완전 검증" (claims resting on f1_n2_defect_words.json) -> "capped-corpus exact"
  "유한 완전 검증" (claims resting on this round's frontier-empty local BFS) -> "uncapped local exhaustive"
  claims never re-derived independent of the corpus -> unchanged, flagged
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLAIMS = [
    {
        "claim": "same-component RR ⟹ chaining",
        "first_appeared": "RR_SAME_COMPONENT_CHAINING_THEOREM.md (Round 11), reconfirmed RR_RELATION_LATTICE.md (Round 14)",
        "original_label": "유한 완전 검증 (10/10, over the 4,470-witness corpus)",
        "data_scope": "legacy_research/outputs/f1_n2_defect_words.json 'area_a_depth6' (25,660 records) filtered to word=='RR' (4,470)",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "capped-corpus exact (10/10 within the capped corpus); NOT independently reverified this round over the full uncapped local universe for ALL ell -- only the narrower same_component_count vs chaining_count equality was spot-checked in the fresh universe (Round 16/17: at every ell, chaining_count == same_component_count exactly in the fresh sample, consistent with but not a full proof of the implication)",
        "counterexample_found": False,
        "corrected_statement": "same-component RR ⟹ chaining holds without exception in the 4,470-witness capped corpus (capped-corpus exact); consistent with (not yet independently proven over) the fresh uncapped-local universe.",
    },
    {
        "claim": "chaining ⟹ relation != unresolved",
        "first_appeared": "Round 9 (pre-RR-specific work), reconfirmed RR_RELATION_LATTICE.md (Round 14, 75/75)",
        "original_label": "유한 완전 검증",
        "data_scope": "capped corpus, 75 chaining witnesses out of 4,470",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "capped-corpus exact; not reverified this round",
        "counterexample_found": False,
        "corrected_statement": "chaining ⟹ not unresolved holds in the capped corpus (75/75); general status unknown.",
    },
    {
        "claim": "hub completer orbit = R1's target orbit (general)",
        "first_appeared": "implicitly assumed through Round 13, explicitly tested and FALSIFIED in RR_HUB_COMPLETER_ORBIT_THEOREM.md (Round 14)",
        "original_label": "반증됨 (already, by Round 14 itself)",
        "data_scope": "one manually-constructed synthetic state (ell=0), local bounded BFS depth<=6, node_cap=20000",
        "cap_present": True,
        "corpus_dependent": False,
        "current_status": "반증됨 (unchanged) -- this was already correctly falsified before this audit; no correction needed",
        "counterexample_found": True,
        "corrected_statement": "Falsified in Round 14 already; this audit found no reason to revisit the falsification.",
    },
    {
        "claim": "abandon_ell=4 ⟹ hub completer orbit uniquely forced (=orbit 1)",
        "first_appeared": "RR_HUB_COMPLETER_ORBIT_THEOREM.md (Round 14)",
        "original_label": "손증명 (combinatorial, from the position-orbit bijection on hex 0)",
        "data_scope": "pure combinatorics (hex 0 has 6 positions total; ell=4 leaves exactly 1 residual) -- NOT corpus-dependent",
        "cap_present": False,
        "corpus_dependent": False,
        "current_status": "손증명 (unchanged, reconfirmed this round -- see RR_COMPLETION_COST_THEOREM.md's cost table, ell=4 always has exactly 1 residual orbit regardless of corpus)",
        "counterexample_found": False,
        "corrected_statement": "Unchanged: a genuinely corpus-independent combinatorial fact.",
    },
    {
        "claim": "nearest-residual completer is the ONLY one realized (all ell)",
        "first_appeared": "RR_ABANDONMENT_ELL_DICHOTOMY.md, RR_ELL0_EXCEPTIONAL_BRANCH.md (Round 15)",
        "original_label": "유한 완전 검증 (212/212 hub-completions, 'corpus is an exhaustive census of depth<=6 RR words')",
        "data_scope": "capped corpus (4,470 witnesses, 212 with hub_completer_found=True)",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "반증됨 (this round, via fresh uncapped-local exhaustive search: legal non-nearest completers occur at every ell<4, e.g. ell=0 distribution {120:19,1:10,33:12,9:9,3:3})",
        "counterexample_found": True,
        "corrected_statement": "FALSE as originally stated. Corrected: within the capped corpus specifically, 43/43 ell=0 completions happened to use the nearest orbit (capped-corpus exact, not a general fact). The TRUE general fact is narrower: cost=2 (the minimum possible) completions always land on the nearest residual position (uncapped local exhaustive, RR_COMPLETION_COST_THEOREM.md) -- but higher-cost non-nearest completions are also legal and do occur.",
    },
    {
        "claim": "hub-completed ⟹ Phi(final) = 0 (all ell)",
        "first_appeared": "RR_ELL_BRANCH_PHI / STATUS.md Round 15 section",
        "original_label": "유한 완전 검증 (212/212 hub-completed witnesses)",
        "data_scope": "capped corpus, 212 hub-completed witnesses",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "반증됨 (fresh exhaustive local search found 7 counterexamples out of 300 hub-touched RR-final states, ~98% not 100%)",
        "counterexample_found": True,
        "corrected_statement": "hub-touched RR-final states reach Phi=0 in ~98% of cases in the fresh local universe (293/300), not universally. The reverse direction (no hub touch ⟹ Phi != 0) held 300/300 in the same sample and is a stronger candidate for a general fact, though still only bounded-observation grade.",
    },
    {
        "claim": "same-component RR ⟹ abandonment ell ∈ {0,4}",
        "first_appeared": "RR_ABANDONMENT_ELL_DICHOTOMY.md (Round 15)",
        "original_label": "유한 완전 검증 ('코퍼스가 depth≤6 RR word의 완전한 전수조사이므로')",
        "data_scope": "capped corpus (4,470 witnesses) originally; reverified Round 16/17 via fresh uncapped-local search from 5 independent abandonment roots",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "uncapped local exhaustive (reconfirmed independent of the capped corpus: same-component count is 0 at ell=1,2,3 in the fresh, frontier-empty local universe at depth ceiling 6, cross-checked by an independent DFS traversal, verify_rr_exhaustive_certificate.py -- ALL MATCH)",
        "counterexample_found": False,
        "corrected_statement": "Holds within the root-local exhaustive universe (root class 1, abandonment-instant state, depth ceiling 6, frontier empty, independently cross-checked). Still bounded by the depth-6 ceiling and by max_r_events=2 scope -- not a proof for arbitrary word length.",
    },
    {
        "claim": "ell=0 same-component witness is unique",
        "first_appeared": "RR_ELL0_EXCEPTIONAL_BRANCH.md (Round 15), RR_ELL0_SATURATED_PHASE_NORMAL_FORM.md (Round 16)",
        "original_label": "유한 완전 검증 (Round 15, capped corpus); then 'genuinely exhaustive, corpus-independent' (Round 16)",
        "data_scope": "Round 16/17: fresh BFS from the ell=0 abandonment root, depth ceiling 5 AND 6, frontier fully empties both times, node cap never hit",
        "cap_present": False,
        "corpus_dependent": False,
        "current_status": "uncapped local exhaustive (within depth ceiling 6, root class 1) -- reconfirmed and cross-checked this round by an independent DFS traversal (exact match)",
        "counterexample_found": False,
        "corrected_statement": "Exactly 1 same-component witness exists in the root-local exhaustive universe at depth ceiling 6 from the ell=0 abandonment root. Scope is explicitly bounded (depth<=6 past abandonment, max_r_events=2, root class 1 only) -- not proven for unbounded depth.",
    },
    {
        "claim": "the incidence graph is a forest (0 redundant unions) across the RR corpus",
        "first_appeared": "RR_INCIDENCE_FOREST_LEMMA.md",
        "original_label": "유한 완전 검증 (0/53,054 pre/post-joint states across 4,470 RR witnesses; 0/85,238 broader depth<=6 sample)",
        "data_scope": "capped corpus (4,470 RR + 85,238 broader depth<=6 sample, all from the same capped 65,340-state frontier)",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "capped-corpus exact (unchanged this round -- NOT reverified against the fresh uncapped-local universe; see RR_EVIDENCE_AUDIT.md section 13 for the honest gap)",
        "counterexample_found": False,
        "corrected_statement": "The forest property is capped-corpus exact only. The document itself already correctly noted this is not implied by pure graph axioms alone (an abstract countermodel with the same degree constraints was constructed). This audit found no independent, corpus-free re-derivation was attempted -- left open.",
    },
    {
        "claim": "6 non-R1-completer same-component witnesses form one 'delayed same-orbit completer' family",
        "first_appeared": "STATUS.md Round 14 section, RR_DELAYED_COMPLETER_NORMAL_FORM.md (Round 15)",
        "original_label": "corpus-exact classification (implicitly, not explicitly labeled)",
        "data_scope": "capped corpus, 6 of the 10 same-component witnesses",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "capped-corpus exact -- since the base same-component COUNT itself is now known to be corpus-completeness-uncertain at ell=4 (9 in the capped corpus vs 5 in this round's fresh local universe, an unresolved discrepancy -- outputs/rr_old_new_corpus_diff.json), this classification's completeness is also uncertain",
        "counterexample_found": False,
        "corrected_statement": "capped-corpus exact classification of the capped corpus's 6 witnesses; NOT reverified against the fresh universe's own (smaller, 5-witness) same-component set this round.",
    },
    {
        "claim": "relation implication lattice (7 implications tested, only 2 hold)",
        "first_appeared": "RR_RELATION_LATTICE.md (Round 14)",
        "original_label": "유한 완전 검증 (exhaustive over all 4,470 witnesses)",
        "data_scope": "capped corpus, all 7 implications",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "capped-corpus exact (not reverified this round); the falsified implications remain falsified regardless of corpus completeness (a single concrete counterexample inside the capped corpus is still a valid counterexample against the corpus-independent universal claims)",
        "counterexample_found": True,
        "corrected_statement": "The 5 FALSIFIED implications remain correctly falsified (a capped-corpus counterexample still disproves a universal claim). The 2 implications reported as HOLDING (same_component=>chaining, chaining=>not-unresolved) should be relabeled capped-corpus exact, not 유한 완전 검증.",
    },
    {
        "claim": "abandonment event always uses move w2:10 (4,470/4,470)",
        "first_appeared": "Round 16 (RR_NEAREST_RESIDUAL_THEOREM.md)",
        "original_label": "유한 완전 검증",
        "data_scope": "capped corpus, all 4,470 witnesses",
        "cap_present": True,
        "corpus_dependent": True,
        "current_status": "capped-corpus exact; NOT reverified against the fresh universe this round (though the fresh universe's root construction assumes it, matching the historical convention)",
        "counterexample_found": False,
        "corrected_statement": "capped-corpus exact (4,470/4,470); not independently reverified as a general necessity this round.",
    },
    {
        "claim": "Unique Hub Hexagon (F<=1 budget ⟹ at most one hexagon touched 2+ times)",
        "first_appeared": "RR_HEX0_NECESSITY_THEOREM.md (Round 12)",
        "original_label": "손증명 (from f1_normal_form's F+1 partial-hexagon invariant, a code-level deductive fact)",
        "data_scope": "not corpus-dependent -- pure deduction from f1_normal_form's definition",
        "cap_present": False,
        "corpus_dependent": False,
        "current_status": "손증명 (unchanged, corpus-independent)",
        "counterexample_found": False,
        "corrected_statement": "Unchanged.",
    },
    {
        "claim": "Hub Touch Count <= 2",
        "first_appeared": "RR_HUB_TOUCH_COUNT.md (Round 13)",
        "original_label": "손증명 (deductive, from current_hex's code definition + F<=1 budget)",
        "data_scope": "not corpus-dependent",
        "cap_present": False,
        "corpus_dependent": False,
        "current_status": "손증명 (unchanged, corpus-independent)",
        "counterexample_found": False,
        "corrected_statement": "Unchanged.",
    },
    {
        "claim": "Hub Exit Source Lemma (post-F1, any joint leaving hex0 sources orbit 1)",
        "first_appeared": "Round 15 (conversation), formalized in RR_ELL0_EXCEPTIONAL_BRANCH.md",
        "original_label": "손증명 + 212/212 유한 완전 검증 (capped corpus)",
        "data_scope": "deductive argument (hex0's fixed position order + F<=1) PLUS capped-corpus verification",
        "cap_present": True,
        "corpus_dependent": "partially -- the deductive core is corpus-independent; the 212/212 count is capped-corpus",
        "current_status": "손증명 (the deductive argument itself is corpus-independent and unaffected by the capped-corpus discovery); the '212/212' verification count should be relabeled capped-corpus exact",
        "counterexample_found": False,
        "corrected_statement": "The lemma's PROOF is corpus-independent (deductive from hex 0's structure). Its historical '212/212' verification count is capped-corpus exact, not a general enumeration -- though this does not weaken the deductive proof itself.",
    },
]


def main() -> None:
    print(f"{len(CLAIMS)} claims audited")
    counts = {}
    for c in CLAIMS:
        counts[c["current_status"].split(" (")[0].split(",")[0]] = counts.get(c["current_status"].split(" (")[0].split(",")[0], 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:2d}  {k}")

    report = {
        "schema": "rr-claim-audit-v1",
        "proof_status_vocabulary": {
            "손증명": "deductive proof from code-level definitions, corpus-independent",
            "유한 완전 검증": "RESERVED going forward for claims verified over a provably complete, corpus-independent state space (e.g. this round's frontier-empty local universes)",
            "capped-corpus exact": "true within legacy_research/outputs/f1_n2_defect_words.json's capped 65,340-state frontier replay; NOT proven complete beyond it",
            "uncapped local exhaustive": "verified via a genuinely uncapped (frontier-empty) BFS from a well-defined local root, independent of the historical corpus, but scoped to a declared depth ceiling and root class",
            "bounded observation": "verified only over a capped/sampled search, no completeness claim intended",
            "exact counterexample": "a single, concretely constructed, verified-legal state disproving a universal claim",
            "반증됨": "falsified by a concrete counterexample",
            "미완료": "open, not resolved",
        },
        "claims": CLAIMS,
    }
    out = ROOT / "outputs" / "rr_claim_audit.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
