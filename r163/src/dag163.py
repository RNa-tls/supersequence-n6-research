#!/usr/bin/env python3
"""Round 163 phase 17 -- non-destructive metadata repair of the current DAG.

Superseding record: r162/certs/dag_162.json.  Statuses, deps and every derived
field are left exactly as they are; only `what`, `where` and `derived_from`
strings are edited, and only where round 163 found the current text wrong,
prose-only, a placeholder, or silent about a load-bearing assumption.

What round 163 found (each repair below cites the finding):

  F1  H.extract carries the placeholder what "the extraction bookkeeping" and
      a `where` pointing ONLY at src/l6_extraction_145.py, whose written cut
      recipe round 156 proved defective (the implementation is correct).  The
      corrected statement is r156/THEOREM.md (0)-(7); round 156 explicitly
      named moving `where` there as the repair that closes the node.
      Claim 1 (sum P_i = 120 + G - 5c) is the census's `required` and is
      load-bearing: lowering it by 5 re-opens 8 rows (r163 ablation).

  F2  G = 2g + c + d with g, c, d >= 0 appears in NO node's text, and it is
      the strongest load-bearing assumption measured: relaxing it takes the
      row space from 1,609 to 50,335 and leaves 7,848 rows SURVIVING.  It is
      not one claim but three: 2g := (G+1) - K >= 0 and even [H.incidence],
      c = the number of pure circuits [definition], and d := K - c - 1 >= 0,
      i.e. at least one beta-cycle is not pure because the dummy's cycle never
      is [H.extract].

  F3  G <= 5k appears only inside H.master's derived_from, spelled
      "(n-1)O >= P", as a prerequisite of k >= 0 and owned by nobody.  As a
      row-space constraint it is load-bearing: dropping it leaves 332 rows
      SURVIVING.  Its proof is r149 Lemma 1.1 and its owner is H.models.

  F4  H.feas `where` is prose, not a path ("round 150 feasibility audit") --
      a defect carried since round 153 and recorded unrepaired by rounds 155
      and 156.

  F5  H.tight `where` is correct but predates its dedicated audit
      (research/RR_L6_H_TIGHT_AUDIT.md, round 155), and the section it cites
      justifies "all 120 hexagons are used" by a parenthesis that round 155
      showed is not a valid derivation; the correct ground is splice Lemma A.

  F6  H.incidence has no derived_from, so the identity that is the node's real
      content, 2g = mu(B) + R_int, and the coordinate substitution
      2g := (G+1) - K that the census enumerates in, are unrecorded.

  F7  H.models and H.catalogue and H.wlog cite r149/PROOF.md without the
      section that states them, and none records that round 163 re-derived
      them independently.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r162" / "certs" / "dag_162.json"
BAD = ("FORBIDDEN", "RETRACTED", "UNRESOLVED")

REPAIR = {
    "H.extract": dict(
        what="the extraction bookkeeping, in the CORRECTED form of "
             "r156/THEOREM.md (0)-(7): (0) cutting the beta-components yields "
             "well-defined chains, no clean-E edge is ever cut, and each chain "
             "lies in one beta-component; (1) Claim 1 sum_i P_i = P - 5c = "
             "120 + G - 5c, which is the census's `required`; (2) Claim 2 "
             "sum_i D_i = 5k - G + 5*sigma_bar; (3) Claim 3 sum_i tok_i = "
             "B* - sigma_bar; (4) Claim 4 0 <= sigma_bar <= B*, and "
             "sigma_bar = 0 for a single chain; (5) Claim 5 sum_i rep_i <= "
             "R_int, so a + bb + e <= R_int <= 2g; (6) #chains = d + 1 + h - s "
             "<= d + 1 + h, and d + 1 in the merged model; (7) the budget "
             "envelope a <= D2, bb <= Qs, e <= Z - Qs.  Also d := K - c - 1 "
             ">= 0: the beta-cycle carrying the dummy is never pure, which is "
             "what makes the census coordinate decomposition G = 2g + c + d "
             "legal",
        where="r156/THEOREM.md (round 156, the corrected statement and its "
              "proof); research/RR_L6_H_EXTRACT_AUDIT.md (round 156); "
              "src/l6_extraction_145.py (the IMPLEMENTATION, which is correct "
              "-- but its docstring lines 18-22 and r149/PROOF.md section 3 "
              "steps 3-5 state a cut recipe that is NOT what it implements)",
        derived_from="round 156 verdict H_EXTRACT_PARTIAL was about the "
                     "PROVENANCE, not the mathematics: the theorem (0)-(7) was "
                     "proved and checked on 20,327,589 exhaustive cases plus "
                     "8,822,032 targeted searches with 0 counterexamples, "
                     "while the document the node pointed at described a "
                     "different, unimplementable cut (40/794 cases cannot "
                     "execute it; taken literally it gives d+2+h chains in "
                     "523/754 cases and P+1-5c ports in 754/754).  Moving "
                     "`where` to r156/THEOREM.md is the repair round 156 "
                     "named.  The defective prose in src/l6_extraction_145.py "
                     "and r149/PROOF.md is hash-pinned and is NOT edited.  "
                     "Claim 5 imports H.samehex; R_int <= 2g imports "
                     "H.incidence.  Round 163 measured Claim 1 to be "
                     "load-bearing (lowering `required` by 5 re-opens 8 rows)"),
    "H.incidence": dict(
        derived_from="the inequality is one line of Euler characteristic; the "
                     "node's real content is the DECOMPOSITION IDENTITY "
                     "2g = mu(B) + R_int with mu(B) = |E(B)| - |V(B)| + "
                     "comp(B) >= 0 the first Betti number of the SIMPLE "
                     "bipartite incidence graph B (round 157, re-proved there "
                     "from scratch and checked on 409,113 abstract cases).  "
                     "The census enumerates in the coordinate 2g := (G+1) - K, "
                     "so this node is what makes 2g >= 0, 2g even and "
                     "R_int <= 2g true; H.samehex and H.envelope import "
                     "R_int <= 2g from here.  Connectivity of B is the only "
                     "non-trivial hypothesis and comes from T being a single "
                     "(P+1)-cycle: dropping it produces 105,077 "
                     "counterexamples (round 157)"),
    "H.models": dict(
        what="the three upper-bound models (split / merged / piece) and what "
             "each relaxes, i.e. obligations (O1)-(O6) of r149/PROOF.md "
             "section 0, together with the two counting lemmas the row space "
             "itself rests on: Lemma 1.1 G <= 5k, because the P passes live in "
             "O = 24 + k tau-orbits of five phases each, so P <= 5O = 120 + 5k; "
             "and Lemma 1.2 a pure circuit is a whole tau-orbit of five "
             "passes.  All three models are load-bearing for the census: "
             "removing split / piece / merged leaves 439 / 53 / 3 rows "
             "SURVIVING (round 163)",
        where="r149/PROOF.md sections 0-5 and 9-10 (round 149, the dedicated "
              "audit); Lemma 1.1 and Lemma 1.2 at r149/PROOF.md lines 59-73; "
              "r150/PROOF.md (round 150, the feasibility obligation)",
        derived_from="round 149 closed (O2)(O3)(O6) by exhaustive enumeration "
                     "and (O5) by machine, and ended at "
                     "OPUS_H_MODELS_PARTIAL for exactly ONE reason: the feas() "
                     "prune could not be cross-validated by switching it off.  "
                     "Round 150 removed that reason with a universal proof and "
                     "a dual certificate (node H.feas).  What remains hand "
                     "work is Claims 1-5 [H.extract] and Lemmas 1.1-1.2 here; "
                     "Claim 5 cites H.samehex.  Round 163 re-derived Lemma 1.1 "
                     "as a row-space constraint and measured it load-bearing: "
                     "dropping G <= 5k leaves 332 rows SURVIVING"),
    "H.feas": dict(
        what="the feasibility prune removes no realisable continuation: with "
             "u_q the unused phases of each already-opened non-current orbit "
             "and k the remaining tokens, every completion has final deficit "
             "at least L = min over |T| <= k of sum_{q not in T} u_q, because "
             "each such orbit's FIRST re-entry is not clean-E and therefore "
             "spends a token.  The prune rejects exactly when L > DMAX",
        where="r150/PROOF.md (round 150, the universal proof, the dual "
              "certificate and the implementation conformance); r149/PROOF.md "
              "section 9.5 (round 149, the first written proof); "
              "r150/src/audit_feas150.py; r150/certs/clauses_and_monotonicity"
              ".json; r150/certs/source_conformance.json; "
              "r149/certs/feaslemma_149.json",
        derived_from="the dual form -- for every lambda >= 0, "
                     "sum_q min(u_q, lambda) - k*lambda is a lower bound, and "
                     "its maximum over lambda EQUALS the subset optimum -- was "
                     "re-derived and checked exhaustively over all 7,722 "
                     "multisets with at most 8 non-current orbits, deficits "
                     "0..4 and tokens 0..5 in round 163 (0 mismatches, 0 "
                     "violations of the per-T bound).  Round 163 also closed "
                     "the ALGORITHM IDENTITY over the whole operational "
                     "domain: the prune's value depends only on the histogram "
                     "(n1,n2,n3,n4) of non-current unused-phase counts and the "
                     "token budget, and for t <= 4 the chain opens "
                     "O = 24 + k <= 28 orbits, so at most 27 are non-current; "
                     "over all 220,255 such states the PRODUCTION histogram "
                     "greedy, the dual bound and the subset optimum are equal "
                     "(0 mismatches).  KNOWN LIMITS, stated by "
                     "the audits themselves: re-running the search with the "
                     "prune OFF is UNAVAILABLE (round 149), the two "
                     "implementations share the idea so A/B agreement does not "
                     "test it, and the per-prune certificates are PROSPECTIVE "
                     "-- historical runs did not emit them, so the route is "
                     "'universal proof + implementation conformance', never a "
                     "replay of the historical prunes.  What is therefore NOT "
                     "closed is state-maintenance fidelity -- that the search's "
                     "masks, counts and tokens really are the (u_q, k) the "
                     "lemma is about -- which round 150 names as the cheapest "
                     "remaining risk and which is a MACHINE obligation on "
                     "C.chaincaps / C.piececaps, not a hand proof"),
    "H.tight": dict(
        where="research/RR_L6_H_TIGHT_AUDIT.md (round 155, the dedicated "
              "audit and the repaired derivation); "
              "research/RR_L6_PROOF_145_CLAUDE.md section 9 lines 292-300 "
              "(the original statement, which is correct)",
        derived_from="all four conclusions follow from the stated hypotheses "
                     "g = 0 and d = 0.  Equality propagates through the "
                     "identity 2g = mu(B) + R_int [H.incidence]: g = 0 forces "
                     "mu(B) = R_int = 0, so B is a tree and the chain is "
                     "hexagon-simple.  |F| = 4c follows from G = 2g + c + d "
                     "with g = d = 0, hence c = G.  The claim that ALL 120 "
                     "hexagons carry a pass is NOT justified by the "
                     "parenthesis in section 9, which round 155 showed is not "
                     "a valid derivation; the correct ground is splice Lemma A "
                     "(the arcs of a hexagon partition it, so m_h >= 1) "
                     "[H.splice].  That a pure circuit is a complete tau-orbit "
                     "is splice Lemma E, and that such an orbit meets five "
                     "distinct hexagons is A.orbitfive"),
    "H.wlog": dict(
        what="fixing the start word is WLOG: left S6 acts letterwise, sigma, "
             "tau, end, the overlap distance and 'is this window a "
             "permutation' are defined by positions and letter equality alone, "
             "so the whole joint catalogue is equivariant; left S6 is "
             "transitive on the 720 permutations with trivial stabiliser, so "
             "any chain maps to one starting at 123456 with identical "
             "resources",
        where="r149/PROOF.md section 2.4 lines 145-157 (the structural proof "
              "and the 518,400-pair check); r149/certs/catalogue_complete_149"
              ".json field left_S6_equivariance; r163/certs/recheck_163.json "
              "field wlog (round 163, independent re-derivation)",
        derived_from="round 163 re-derived this from the definitions, "
                     "importing nothing from src/ or r149/: left S6 is "
                     "transitive on the ports with stabiliser of size 1, and "
                     "the type map is equivariant on ALL 518,400 ordered (v,t) "
                     "pairs for each of the five adjacent transpositions "
                     "(2,592,000 pairs, 0 violations).  Equivariance is closed "
                     "under composition and those five generate S6, so the "
                     "check is exhaustive for the whole group, not a sample.  "
                     "This node is INDEPENDENT of H.fixedrep: H.wlog relabels "
                     "letters and acts on the start port of the capacity "
                     "search, H.fixedrep re-spells a word and may shorten it, "
                     "and the two commute -- Phi(pi.W) = pi.Phi(W), verified "
                     "on 2,952 pairs in round 162"),
    "H.catalogue": dict(
        what="the joint catalogue is complete and the charging rules are "
             "exhaustive: over all 720x720 ordered pairs the gap is 1..6 "
             "(720 / 1,440 / 4,320 / 17,280 / 86,400 / 408,240), every pair "
             "with gap >= 2 falls in exactly one of clean E, dirty A, dirty B, "
             "the five paid kinds and heavy, each source has exactly one clean "
             "E, one A, one B, five paid and 710 heavy targets, and the only "
             "two omitted targets per source are t = v and t = end(v), both "
             "impossible because t is a FIRST occurrence while v and end(v) "
             "are already written.  Charging: clean E = tau, A = sigma, "
             "B = sigma^2, A and B stay in the source hexagon, and a PAID edge "
             "never lands in the source hexagon",
        where="r149/PROOF.md sections 2.1-2.3 lines 89-144 (round 149); "
              "r149/certs/catalogue_complete_149.json; "
              "r163/certs/recheck_163.json field catalogue (round 163, "
              "independent re-derivation)",
        derived_from="round 163 recomputed the whole catalogue from the "
                     "definitions of sigma, tau, end and maximum overlap, "
                     "importing nothing from src/ or r149/: the gap "
                     "distribution, the per-source profile (1,1,1,5,710 for "
                     "all 720 sources), C1 720/720, C2 720/720 for A and for "
                     "B, C3 720/720 for A and for B, C4 = 0 paid edges landing "
                     "in the source hexagon, 1,440 heavy edges that do, 0 "
                     "unclassified pairs and 0 failures -- every number equal "
                     "to the round-149 certificate.  Gap >= 7 is impossible "
                     "because two 6-windows overlap in 0..5 letters"),
}

IMMUTABLE = [
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r153/certs/dag_153.json", "r153/certs/theorem_153.json",
    "r153/certs/witness872_153.json", "r155/certs/audit_155.json",
    "r156/THEOREM.md", "r156/certs/provenance_156.json",
    "r157/certs/dag_157.json", "r157/certs/provenance_157.json",
    "r161/certs/dag_161.json", "r162/certs/dag_162.json",
    "r162/certs/provenance_162.json", "r159/certs/hash_invariance_159.json",
    "r159/certs/provenance_159.json", "r149/PROOF.md", "r149/AUDIT.md",
    "r150/PROOF.md", "r149/certs/catalogue_complete_149.json",
    "src/l6_fixed_representative_145.py", "src/l6_splicing_145.py",
    "src/l6_master_identity_144.py", "src/l6_cleanroom_146.py",
    "src/l6_same_hex_145.py", "src/l6_incidence_144.py",
    "src/l6_extraction_145.py", "src/l6_envelope_146.py",
    "r152/src/rows152.py", "data/verified_872_witness.txt",
    "research/RR_L6_PROOF_145_CLAUDE.md",
    "research/RR_L6_H_TIGHT_AUDIT.md", "research/RR_L6_H_EXTRACT_AUDIT.md",
]

CARRIED = [
    "src/l6_extraction_145.py docstring lines 18-22 and r149/PROOF.md "
    "section 3 steps 3-5 still state the defective cut recipe.  They are "
    "hash-pinned in several rounds' provenance and are NOT edited; the DAG "
    "no longer cites them as the canonical statement (round 163 repair).",
    "r152/src/rows152.py lines 16-19 still say 'the piece model is not used "
    "at all'.  It is: bounds() records res['piece'] unconditionally and the "
    "piece model is the sole closer of rows the other two leave open "
    "(removing it leaves 53 rows SURVIVING).  Self-description only; the "
    "piece capacities are certified and the file is hash-pinned.",
    "deps is [] on all 12 hand-proof nodes by convention: deps is the "
    "MACHINE pipeline edge set (which certificate consumes which), while "
    "mathematical dependence between hand proofs is recorded in prose in "
    "derived_from.  Round 163 checked the prose dependence graph is acyclic.",
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
    missing = [p for p, v in before.items() if v is None]
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
    out = dict(supersedes="r162/certs/dag_162.json",
               source_sha256=sha("r162/certs/dag_162.json"),
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
               nodes_unchanged=sorted(k for k in nodes if k not in REPAIR),
               carried_defects_not_repaired_here=CARRIED,
               dag=new)
    (ROOT / "r163" / "certs" / "dag_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    after = {p: sha(p) for p in IMMUTABLE}
    inv = dict(files=len(IMMUTABLE), missing=missing,
               unchanged=[p for p in IMMUTABLE if before[p] == after[p]],
               changed=[p for p in IMMUTABLE if before[p] != after[p]],
               sha256=after)
    inv["all_unchanged"] = not inv["changed"] and not missing
    (ROOT / "r163" / "certs" / "hash_invariance_163.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=1) + "\n")
    ok = (out["diff_is_exactly_the_repairs"] and derived_same
          and out["statuses_unchanged"] and out["deps_unchanged"]
          and inv["all_unchanged"] and new["theorem_path_clean"])
    print(json.dumps(dict(repairs=[(c["node"], c["field"]) for c in changes],
                          diff=sorted(diff),
                          diff_is_exactly_the_repairs=
                          out["diff_is_exactly_the_repairs"],
                          derived_unchanged=derived_same,
                          statuses_unchanged=out["statuses_unchanged"],
                          deps_unchanged=out["deps_unchanged"],
                          theorem_path_clean=new["theorem_path_clean"],
                          immutable_files=len(IMMUTABLE),
                          immutable_missing=missing,
                          immutable_files_unchanged=inv["all_unchanged"],
                          ok=ok), ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
