# Applying the Ω theory to the real Round-68 113-family corpus

작성자: Claude
role: independent analysis of supplied Codex artifacts. No search run.

---

## 0. Provenance, and what is actually in hand

The Round-68 artifacts were supplied **inline in conversation**, not via git.
Re-checked this round: `git fetch --all --prune` still shows the Codex tip at
`codex/round-r1-37-hex82-t4` @ `1f9efff` (Round 61); none of these files exist
in any ref. Treating the pasted text as source of truth as instructed, and
recording that they are **not yet independently fetchable or hash-checkable**.

**Two round numbers are in conflict.** The request calls this "Round 62", but
the report's own title is *"Round 68 — full 113-family reclassification and G3
audit"*, and the analyzer separately references a distinct Round-62 artifact
(`outputs/rr_short_t4_child_classification.json`, bound to `ROUND62`/
`ROUND62_VERIFIED`). This document uses **Round 68** throughout, matching the
artifacts' own self-identification. Worth fixing before it reaches a
certificate, for the same reason as the G2/G3 collision flagged last round.

### Supplied vs. missing

| # | described as | actual schema / identity | usable? |
|---|---|---|---|
| 1 | research report | `RR_SHORT_113_FAMILY_G3_CODEX.md` | yes |
| 2 | 439-family master ledger | `rr-short-113-family-status-v1` | yes |
| 3 | residual ledger | `rr-short-113-family-residuals-v1` | yes |
| 4 | **mechanism ledger** | **`rr-short-113-family-residuals-v1` — a duplicate of #3** | **no** |
| 5 | independent verification | `rr-short-113-family-g3-verified-v1` | yes |
| 6 | analyzer | `analyze_rr_short_113_family_g3.py` | yes |
| 7 | independent verifier | `verify_rr_short_113_family_g3.py` | yes |

**`rr_short_113_family_mechanisms.json` was not supplied** — item 4 is byte-wise
the residuals ledger again. Its contents (`theorem_stack`,
`already_merged_audit`, `legal_Z2_merger_audit`,
`universal_R2_source_obstruction`, `observed_R2_corpus_by_current_class`) are
therefore known only indirectly, from the analyzer source that writes it and
the verifier that reads one field of it.

**Also missing, and load-bearing:** `outputs/rr_short_t4_direct_z2_families.json`.
This is the *only* source of the per-anchor records
(`first_R1_hub_merge_provenance`, `R1_hub_same_component`,
`direct_Z2_candidates`) from which the four anchor mechanisms are derived. It
is not supplied, and neither are the 439 checkpoints (10,939,666,873 bytes per
`checkpoint_aggregate`). Consequences are given per-task in §2-§5.

---

## 1. Independent arithmetic verification of the supplied ledgers

Recomputed from the 24 residual family rows, not from the summary blocks.
**Everything checks.** `[EC]`

| check | result |
|---|---|
| partition `F0..F8` sums to 439 | ✓ |
| nonempty = 113; T4-closed `F1+F2+F4+F5` = 89; residual `F7+F8` = 24 | ✓ |
| `A4 = F5+F7+F8 = 21+16+8 = 45`; historical `9+47+12+45 = 113` | ✓ |
| 24 residual families: 16 `F7` + 8 `F8` | ✓ |
| residual anchor total from the 24 rows = **1818** | ✓ |
| mechanism counts sum `1183+612+16+7` = 1818 | ✓ |
| Target-A hits across residuals = 3, all `EXACT_KNOWN18_MATCH` | ✓ |

**Not re-derivable from what was supplied:** the 5,332 total nonempty anchor
count (needs all 113 rows' anchor counts — the 89 closed families' counts are
in ledger #2 but were not re-summed here), and every SHA-256 in
`input_sha256` / `checkpoint_aggregate` (no files to hash).

### 1.1 A structural fact the ledgers do not state `[EC]`

Summing anchors by family class gives an exact correspondence that is
**nowhere stated in the supplied documents**, which present the four mechanisms
as a flat decomposition of 1818:

```
F7 (16 families)  ->  1183 anchors  ==  MERGED_BY_R      (exactly, 100%)
F8 ( 8 families)  ->   635 anchors  ==  MERGED_BY_Z2 612
                                     +  SEPARATE_MONOTONE_BLOCKED 16
                                     +  SEPARATE_CLEAR             7
```

So the mechanisms are **not** distributed across the residual; they are sharply
localized:

- **Every F7 anchor is already R1-merged.** The family label
  `R1_HUB_ALREADY_MERGED` holds anchor-for-anchor.
- **F8 is mixed.** Its label is `LITERAL_DIRECT_Z2_BRIDGE_IN_ANCESTRY` —
  "in ancestry" — and indeed **23 of its 635 anchors (16 SM + 7 SC) are not
  merged at all.** The family is flagged because *some* ancestry contains the
  bridge, not because every frozen anchor sits past it.

This materially changes the closure strategy (§5) and localizes the 7
`SEPARATE_CLEAR` anchors to F8 families — a fact needed for §4 and not
recorded anywhere in the supplied data.

---

## 2. Task 1 — Ω-projection of the 1,818 residual anchors: **BLOCKED**

Ω = `(orbit_masks, p, F, r_count, hub_touch_count)`
(`RR_SHORT_POST_MERGER_OMEGA_CLAUDE.md` §2).

**None of these five fields appear in any supplied artifact.** The residual
ledger carries `anchor_count`, `anchor_class_counts` (the A1-A4 label only),
`checkpoint_sha256`, and aggregate `observed_R2_outcomes` — no exact state.
The anchor states live in the 439 checkpoints and in
`rr_short_t4_direct_z2_families.json`, neither supplied.

I will not synthesize 1,818 state vectors. What is needed is exactly: for each
residual anchor, `state.orbit_masks`, `state.p`, `state.F`, `dec.r_count`,
`dec.hub_touch_count`. `state.hex_masks` is **not** needed — by M4 the
Target-A predicate never reads it, and by OMEGA-SOUND dropping it is the
sound direction.

---

## 3. Task 2 — Ω-closure of MERGED_BY_R (1,183) and MERGED_BY_Z2 (612): **BLOCKED, but now fully specified**

Blocked for the same reason. What the new data *does* buy is that the
computation is now completely specified and provably terminating:

**Theorem (residual Ω-closure is a terminating, sound decision procedure).**
`[HAND THEOREM, from OMEGA-SOUND + OMEGA-TERM + M2′ + M3 + M4]`

For each of the 1,795 merged anchors (1183 `MERGED_BY_R` + 612
`MERGED_BY_Z2`):

1. By **M2′**, co-component is permanent, so the Target-A `same_component`
   condition is discharged for every source/target orbit pair inside the
   merged component, at every descendant — and cannot be re-blocked.
2. By **M3**, the only remaining obstructions are the five non-component
   recognizer conditions (`r_count 1→2`, `kind==R`, `F==1`, `H==0`,
   `hub_touch_count<=2`).
3. By **M4**, all five plus the component relation are Ω-computable; the
   predicate never reads `hex_masks`.
4. By **OMEGA-TERM**, the Ω-closure from each anchor is acyclic with depth
   ≤ `720 − popcount(orbit_masks)` and branching ≤ 24, so a memoized DFS
   terminates.
5. By **OMEGA-SOUND**, a negative result transfers to exact: *no Ω-reachable
   Target-A exit ⟹ no exact-reachable Target-A exit.*

So family-level closure of F7 and the merged part of F8 reduces to **1,795
terminating Ω-closures**, each sound one-sided. This is the concrete form of
the "finite-image theorem" requested — the mathematics is done, only the input
states are missing.

**Honest caveat, unchanged:** termination is proved; *tractability* is not.
Ω retains a 720-bit `orbit_masks`, and nothing here bounds the reachable image
by a small number. The 8-post-Z2-state collapse reported for `MERGED_BY_Z2` is
encouraging but is an observation over witnessed mergers, not a proved bound
on the Ω-image.

---

## 4. Task 3 — Target-A exits: **COMPLETE for the observed corpus** `[EC]` / `[BO]`

All three residual-corpus Target-A exits, fully enumerated from ledger #2:

| # | family | class | mechanism | witness | canonical state hash | known-18 | Target-B |
|---|---|---|---|---|---|---|---|
| 1 | `short_ell4_r1_18` | F8 | Z2 merger | `short_ell4_target_a_00000` | `79f21d2f…e1c4` | `EXACT_KNOWN18_MATCH` | helper-free cert reused |
| 2 | `short_ell4_r1_62` | F7 | R1 merged | `short_ell4_target_a_00001` | `20585475…5616` | `EXACT_KNOWN18_MATCH` | helper-free cert reused |
| 3 | `short_ell4_r1_71` | F8 | Z2 merger | `short_ell4_target_a_00002` | `f1a92555…9aa9` | `EXACT_KNOWN18_MATCH` | helper-free cert reused |

Observations that matter:

- **All three are in `short_ell4`.** Every residual family under
  `short_ell1/2/3` has zero Target-A hits. Whether that is structural or an
  artifact of the bounded prefix is **not determinable** from this data.
- **The split is 1 F7 / 2 F8**, i.e. Target-A exits occur under *both* merger
  mechanisms — R1-created and Z2-created alike.
- 3 hits against 1,818 anchors and ~53,000 serialized R2 path records across
  the residual families. Frequency is `[BO]` only.

**These exits are exact-reachable, not Ω-artifacts.** They are literal
`TARGET_A_HIT` outcomes in the recognizer telemetry. That direction matters:
Ω can only *close*, never witness (OMEGA-SOUND's direction warning), so a
real exit found by exact replay is strictly stronger evidence than anything Ω
could produce.

### 4.1 This confirms the falsification I recorded last round

`RR_SHORT_MERGED_BY_R_THEORY_CLAUDE.md` §5/§10 argued structurally that
merger **relaxes** the Target-A predicate — it enlarges the qualifying
`(sq,tq)` set monotonically — so "no new boundary post-merger" fights the
direction of the structure, and I declined to assert the MR-Theorem.

The data bears that out: a merged family *did* produce a Target-A exit
(entry 2 above, an F7/R1-merged family). Codex's own report reaches the same
place from the other side — *"The proposed universal wrong-R2-source
obstruction is false because literal Target-A counterexamples exist."*

What remains genuinely open is the weaker, still-unproved half: whether every
such exit is known-18. Three-for-three is consistent with it and **is not
evidence for it** — that is exactly the evidential shape that produced this
project's parity retraction (master status §5.1). I continue to decline the
MR-Theorem.

---

## 5. Task 4 — the 7 `SEPARATE_CLEAR` transition graph: **PARTIALLY UNBLOCKED**

Newly established from §1.1: the 7 SC anchors (and the 16 SM anchors) live
**inside F8 families**, not F7. That was not previously known and is not
stated in the supplied ledgers.

Still missing: *which* F8 families, and the anchors' exact states. Both live in
`rr_short_t4_direct_z2_families.json`. The residual ledger cannot localize
them — every residual family's `anchor_class_counts` is uniformly `{"A4": n}`,
which is the historical class, not the mechanism.

So the per-state enumeration remains blocked. But the theory now composes
usefully:

**SC anchors flow into the mechanism that already dominates their own family.**
By M7, every SC successor lies in `{SC, MZ, R2, DEAD}` (and `SC → MR` is
provably impossible, since R1 is in the past). Their families are already
`LEGAL_Z2_MERGER` families. So the SC anchors' descendants enter exactly the
`MERGED_BY_Z2` analysis of §3 — **closing MZ closes most of SC as a
by-product.** By SC-3, the residual `SC → SC` recurrence is finite and acyclic
with depth ≤ 720, so no separate termination argument is needed.

### 5.1 A classification edge case worth fixing

The analyzer assigns `SEPARATE_MONOTONE_BLOCKED` via

```python
elif all(candidate["current_exact_legality"][
         "permanently_blocked_by_monotone_no_repeat_at_this_fixed_incidence"]
         for candidate in anchor["direct_Z2_candidates"]):
```

`all()` over an **empty** list is `True`. An anchor with *no* direct-Z2
candidates is therefore labelled `SEPARATE_MONOTONE_BLOCKED`, not
`SEPARATE_CLEAR`. Semantically both mean "no direct Z2 bridge available", so
the aggregate counts are not wrong — but the label conflates *"candidates
exist and every one is monotone-blocked"* with *"no candidate exists at all"*.

That distinction is load-bearing for the SM closure route I proposed last
round (`RR_SHORT_G3_RESIDUAL_THEORY_CLAUDE.md` §7), which turns on the
blocking quantity being monotone and the blocked predicate upward-closed. A
vacuous anchor has no blocking quantity to be monotone about and needs a
different (easier, but different) argument. **Recommend splitting the label**
into `SEPARATE_NO_CANDIDATE` and `SEPARATE_ALL_BLOCKED` before proving
anything over the 16.

---

## 6. Task 5 — the family-level closure theorem, as far as it goes

**Theorem (residual reduction).** `[HAND THEOREM]` Given §1.1's localization,
family-level closure of the 24 residual families decomposes exactly as:

```
F7  (16 families, 1183 anchors)  needs:  merged-anchor Ω-closure only
F8  ( 8 families,  635 anchors)  needs:  merged-anchor Ω-closure (612)
                                       + SM argument              ( 16)
                                       + SC transition closure    (  7)
```

with no cross-terms: no F7 anchor requires the SM or SC arguments, because
every F7 anchor is merged (§1.1). Combined with §3, closure of all 24 families
follows from:

1. **1,795 terminating, sound Ω-closures** yielding only known-18 Target-A
   exits or none (§3), **plus**
2. an SM argument over 16 anchors — after the label split of §5.1, **plus**
3. an SC transition closure over 7 anchors, largely subsumed by (1) via §5.

This is a complete and finite proof plan. **It is not a proof**, and I do not
claim G3. The single irreducible unknown is whether step (1) returns only
known-18 exits — and §4.1 records why I expect that to be the hard part rather
than a formality.

---

## 7. Audit of the supplied analyzer and verifier

Read in full. The discipline is good — genuinely independent re-derivation of
the A1-A4 family classification by streaming every frontier from the immutable
checkpoints, SHA-checking each, and refusing to proceed on a mismatch. Four
issues worth recording:

1. **The `true_phase_walk_capacity` firewall covers 2 of 5 proof-path files.**
   The verifier greps only `analyze_rr_short_113_family_g3.py` and its own
   source. The three imported modules that do the actual replay —
   `verify_rr_short_t4_template.py`, `verify_rr_short_t4_direct_z2.py`,
   `verify_rr_short_t4_a3_open_w2.py` — are not grepped, yet the emitted
   certificate asserts `"true_phase_walk_capacity_called": false` unqualified.
   Given master status §5.5 (that helper is retracted outside full-segment
   scope), the check should cover every imported module in the proof path.
2. **The residual-mechanism logic is duplicated, not independently derived.**
   The verifier recomputes the four mechanism counts with byte-identical logic
   to the analyzer, over the same `rr_short_t4_direct_z2_families.json`. A
   wrong `first_R1_hub_merge_provenance` in that file would be reproduced
   identically by both. The A1-A4 classification *is* independently
   re-derived; the mechanism split is not.
3. **An unchecked negative telemetry delta.** `short_ell4_r1_18` has
   `serialized_R2_path_records = 2321` but `telemetry_R2_outcome_events = 2320`
   (`delta = -1`). Every other residual family has delta ≥ 0. A negative delta
   means a serialized R2 path record with no telemetry counterpart — the
   opposite of the benign "telemetry ahead of capped serialization" pattern.
   Neither the analyzer nor the verifier asserts anything about this field's
   sign. This is the same family as Target-A witness `…_00000`, so it is worth
   resolving rather than leaving as a curiosity.
4. **A fifth mechanism branch exists and is silently empty.**
   `SAME_COMPONENT_NO_REPLAY_PROVENANCE` is a live branch in both files but
   appears in no output. It came out 0; that is good news, but the "0 other
   residual" claim would read more honestly if the empty class were reported
   explicitly rather than omitted.

None of these invalidate the ledger. (1)-(3) are checkable in minutes and
would materially strengthen it.

---

## 8. Proof-status summary

| item | status |
|---|---|
| ledger arithmetic, 24 families, 1818 anchors, 3 Target-A hits | **EC** (recomputed from rows) |
| F7 ⟺ MERGED_BY_R; F8 = 612 + 16 + 7 (§1.1) | **EC** (new; not in supplied docs) |
| residual Ω-closure is terminating and sound (§3) | **HAND THEOREM** |
| F7/F8 closure decomposition with no cross-terms (§6) | **HAND THEOREM** |
| SC ⊂ F8, and SC feeds the MZ analysis (§5) | **HAND THEOREM** |
| the 3 Target-A exits are all known-18 | **EC for the observed corpus; BO as a general claim** |
| MR-Theorem (all merged exits known-18) | **CONJECTURE — still declined (§4.1)** |
| G3 | **NOT ACHIEVED** — agrees with `G3_FINITE_MECHANISMS_REMAIN` |
| Ω-projection of 1818 anchors; MZ/MR Ω-closure; per-state SC graph | **BLOCKED** — needs `rr_short_t4_direct_z2_families.json` |
| every SHA-256 and the 5,332 anchor total | **NOT VERIFIED** — no files to hash |

## 9. What to send next, in priority order

1. **`outputs/rr_short_t4_direct_z2_families.json`** — single highest-value
   item. Unblocks §2, §3 and §5 at once: it carries the per-anchor records and
   is the only source of the mechanism split.
2. `outputs/rr_short_113_family_mechanisms.json` — the actual one (item 4 was
   a duplicate).
3. Push Round 68 to a branch so the SHA-256 chain and `checkpoint_aggregate`
   become checkable. Everything in §1 is currently arithmetic-only.

## End token

`CLAUDE_G3_ROUND68_OMEGA_PARTIAL`
