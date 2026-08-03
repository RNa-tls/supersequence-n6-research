# `short_ell2_r1_37` v7 frontier analysis: independent verification

Branch `codex/round-r1-37-frontier-analysis` fetched directly. Every
claim below was checked by loading the raw JSON/Python and recomputing
directly — including reproducing Codex's own batch-selection algorithm
line-by-line to confirm it — not by re-reading Codex's summary text.

## 1. Remote verification

- `git fetch origin codex/round-r1-37-frontier-analysis` succeeded (the
  branch did not appear in an initial `git fetch --all --prune`; it was
  found via `git remote show origin`, which listed it as `new` — the
  push landed between the two fetch attempts).
- `git rev-parse` = `fae8ded9a8fe5e2958e602fafb2ac4e337ef8958` — **exact
  match** to the claimed commit.
- `git log --oneline`: `fae8ded → 4792891 → ...` — **parent relationship
  confirmed**: this commit's parent is exactly
  `479289107591ce887097550d370dd7f3785475d9`, the commit independently
  verified two rounds ago.
- All 5 required files exist (`git show` succeeded for each): the
  markdown, all three JSON outputs, and the analyzer script.
- **No Git LFS pointers**: checked all 5 files for a `git-lfs` marker at
  the start of the blob — none found; all are real content
  (`rr_short_ell2_r1_37_frontier.json` alone is 702,386 bytes of literal
  JSON, not a pointer).
- **SHA-256 internal consistency, checked where reproducible**: every
  hex string matching a SHA-256-shaped pattern across the 3 JSON files
  was checked programmatically for exactly 64 hex characters — no
  anomalies. The `next_plan.json` provenance's `checkpoint.sha256_from_
  verified_v7_ledger` matches the `frontier.json` provenance's field of
  the same name exactly (cross-file consistency, independently
  compared, not merely re-read).
- **One unverifiable upstream link, disclosed rather than glossed
  over**: `provenance.verified_v7_ledger_sha256` and `checkpoint.sha256_
  from_verified_v7_ledger` reference an intermediate "v7 ledger" and a
  4.88 GB checkpoint that this session cannot independently re-hash
  (neither file was provided this round, and no "round 53" branch or
  commit exists anywhere `git branch -ra` / `git remote show origin`
  can reach). This round's own audit is nonetheless self-grounded
  independent of that gap: it replays 65 ancestry nodes literally from
  the already-verified **v5** anchor (established real several rounds
  ago) and its own `assert` checks (`replay hash mismatch` /
  `expected 22 frontier records`) would have raised on any
  inconsistency — confirmed by reading `main()`'s own guard clauses in
  the analyzer script (lines 540-549).

## 2. Exact class-count verification, with equivalence definitions checked

All six counts independently recomputed directly from the 22 raw
per-state records (not read from any summary line):

| quantity | recomputed count | claimed | match |
|---|---:|---:|---|
| frontier states | 22 | 22 | yes |
| exact decorated states (`exact_state_hash`) | 22 | 22 | yes |
| proved left-`S6` classes (`left_s6_canonical_class_sha256`) | 22 | 22 | yes |
| resource profiles (`resource_profile_class_sha256`) | 18 | 18 | yes |
| successor signatures (`successor_signature_class_sha256`) | 22 | 22 | yes |
| component geometries (`component_geometry_class_sha256`) | 19 | 19 | yes |

**Equivalence definitions, read directly from the analyzer source
(lines 566-604, 211-231, 355-358)** — the point the task specifically
asks not to gloss over:

- **`exact_state_hash`**: `rr.state_hash(state)`, literal state
  identity — the finest possible grain, a proved-trivial equivalence
  (identical states only).
- **`left_s6_canonical_class_sha256`**: the hash of
  `canonical_state_decoration(state, dec)`'s output — this is the
  already-established, previously-verified left-`S6` canonicalization
  method used throughout this project. **This is the one class count
  among the five that rests on a proved symmetry**, not a heuristic.
  Result: even under the *proved* symmetry, all 22 states remain
  pairwise distinct — a genuine, non-trivial confirmation that no two
  of the 22 are secretly the same state up to the one relation this
  project has actually proved.
- **`resource_profile_class_sha256`**: `SHA256({P, O, F, H, Ndef, D,
  Phi, M})` — a coarse hash of eight scalar resource coordinates only.
  **This is explicitly a heuristic profile, not a proved continuation
  equivalence** — two states can share every one of these eight numbers
  while having completely different reachable futures (different
  literal permutation, different incidence forest, etc.).
- **`successor_signature_class_sha256`**: a hash of the state's own
  computed legal-successor structure (`successor_analysis`'s
  `signature_payload`). Empirically unique across all 22 states here,
  but this is a per-state descriptive summary, not an equivalence
  proved to predict deeper continuation behavior.
- **`component_geometry_class_sha256`**: a hash of a **deliberately
  coarsened** component-shape list (`geometry_profile`, lines 211-231)
  — it records only each component's `{e_orbits, hexagons, incidences}`
  *counts* plus `is_hub`/`is_r1_target`/`has_current_orbit`/`has_
  current_hexagon` flags, explicitly discarding the specific orbit and
  hexagon *identities*. By construction this is a shape signature, not
  an exact-state or proved-symmetry equivalence.

**Conclusion, directly answering the task's caution**: only two of the
five counts (`exact_state_hash`, `left_s6_canonical_class_sha256`) rest
on proved equivalences; the other three (`resource_profile`,
`successor_signature`, `component_geometry`) are heuristic profiles by
the analyzer's own construction, and Codex's own document is explicit
that they "are **not** continuation equivalences and must not be used
for pruning" — confirmed to be an accurate self-characterization, not
an understatement.

## 3. Structural predicates: literal facts, not derived classifications

All three are **direct, literal properties of the exact state and
decoration**, not post-hoc derived classifications:

- **Hub complete**: `hub_mask == 63` where `hub_mask =
  int(state.hex_masks[dec.hub_id])` — a direct read of the exact
  state's own `hex_masks` array at a fixed index. Confirmed `true` for
  all 22 by direct recomputation.
- **`Phi = 0`**: `rr.phi(state)`, the already-established Φ invariant
  formula (`5 + 6*(TARGET_P-P) - (720-visited_count)`), applied
  directly to each exact state. Confirmed `0` for all 22.
- **`R1`-target component distinct from hub component**: computed via
  `component_id(summary, ("q", r1_orbit)) != component_id(summary,
  ("h", hub_id))`, where `summary = rr.component_summary(state)` is the
  same already-verified `incidence_components` machinery this session
  independently confirmed from source three rounds ago. Confirmed
  `true` (distinct) for all 22.

None of these three are coarsened or heuristic — each is a direct
boolean/numeric fact about the literal exact state, computed via
already-verified project machinery, not a new classification invented
this round.

## 4. Immediate-`R2` subgroup: verdict and exact certificate unit

- **Exactly 9 of the 22 frontier states carry a
  `future_R2_source_candidates` entry** (1 each, 9 total across all 22)
  — independently recomputed by counting, not read from a summary.
- **All 9 fail only `same_component`** — every one of the 9 candidate
  records has `same_component: false` and no other failure reason
  present.
- **Each of the 9 associated reachable subgraphs is exactly exhausted,
  with no bridge** — `bridge_distance.status ==
  "reachable_subgraph_exhausted_no_bridge"` for exactly these same 9
  node IDs. Reading the analyzer's own BFS code
  (`bridge_distance_within`, lines 247-293) confirms this status is
  returned **only when the BFS queue empties before reaching the
  depth-3 cap** — i.e., it is a genuine complete exploration of
  everything reachable from that state under the Target-A-safe legal
  edges, not a depth-capped "nothing found yet."

**Exact certificate unit: subgraph, not state and not branch.** The
certificate is not about the single frontier state alone (it is a
claim about everything *reachable* from it) and it is not about the
`short_ell2_r1_37` branch as a whole (only 9 of the 22 roots have this
property; the branch remains open). It is a **per-root reachable-
subgraph exhaustion certificate**, one for each of the 9 named states
independently.

## 5. Remaining 13 states: scope verdict, no overclaim found

- All 13 non-exhausted states carry `status: "not_found_within_bound"`,
  `lookahead_bound: 3`, `proved_lower_bound: 4` — **uniformly, exactly
  as claimed, no stronger status value present anywhere in the 13**.
  No encoding of exhaustion or impossibility was found for any of them.
- **Recurrence count = 0**: `exact_decorated_recurrences == []` in
  `rr_short_ell2_r1_37_frontier_classes.json` — a true empty list, not
  merely a low count.
- **Collision saturation is non-monotone**: `collision_saturation.
  monotone_saturation_observed == false`, with the recorded means
  (`frontier_mean_exact_collisions: 13.1818...`,
  `frontier_mean_legal_successors: 1.2727...`) matching the document's
  "13.18"/"1.27" to displayed precision — a data-backed, not merely
  asserted, non-monotonicity finding.
- **Other monotone quantities do appear in the exported data,
  independent of the collision-saturation question**: `monotonicity`
  records `P, O, S, Ndef, Phi, hub_popcount, visited` as all exactly
  `nondecreasing_on_replayed_paths: true` with `violation_count: 0`,
  while `D` and `M` are explicitly **not** monotone (242 and 274
  violations respectively, with minimal counterexamples recorded). This
  directly answers "whether any other monotone quantity appears" —
  **yes, seven do**, cleanly separated in the same file from the two
  that don't.

## 6. The 421,219 vs 421,221 discrepancy: cannot be explained from ledger fields

**This cannot be resolved with a matching ledger field, and is reported
as such rather than papered over with a verbal guess.**

- `"421,221"` appears in exactly three places across the fetched files
  — the markdown (§"Separation-invariant candidate"), the JSON
  (`candidate_theorems[0].support`), and the analyzer source itself
  (line 667) — and **in every one of the three it is a fixed literal
  string**, `"All 421,221 previously verified replay nodes were B0..."`.
  It is **not** the output of any computation performed by this round's
  analyzer, and no field named or resembling `"B0"` with a numeric
  count of 421,221 (or any count at all) exists anywhere in the two
  JSON outputs. `provenance.parent_dag_nodes_scanned` for this specific
  branch is `305,022` — a different, locally-computed and internally-
  consistent number, unrelated to 421,221.
- `"421,219"` (the task's other figure) **does not appear anywhere** in
  any of the 5 required files, in any format, comma-separated or not.

**Conclusion**: neither number is a ledger-backed, locally-computed
fact in this round's artifacts. `421,221` is a **carried-forward,
hardcoded reference** to a figure from outside this round's own
analysis — almost certainly the same "421,221 nodes" figure from the
prior round's report, which this session was unable to verify against
any real branch or commit at the time (see this analyst's own prior
document, `RR_TOP8_7_OF_8_SIGNIFICANCE_CLAUDE.md`, which flagged the
identical number as unverified for exactly that reason). `421,219`
cannot be traced to any source in what was fetched this round at all.
**No "two non-B0 units," root-node-exclusion convention, or terminal-
node convention can be confirmed or refuted, because neither of the
two numbers being compared is backed by a computed field in the files
available this round.** This is reported as an open provenance gap in
Codex's own artifacts, not resolved by speculation.

## 7. Strategy D: exact reproduction and assessment

**The exact 8 selected state IDs, selection criterion, and ranking were
independently reproduced from raw data — not merely re-read — and
matched exactly.**

Reproducing the analyzer's own selection code (lines 694-717): sort the
13 non-exhausted states by `(legal_successor_count ascending,
proved_lower_bound ascending, depth descending, node_id)`, then
deduplicate by the compound key `(successor_signature_class_sha256,
component_geometry_class_sha256)`, then take the first 8. **Independent
recomputation of this exact procedure reproduces the claimed 8-state
batch precisely**: `short_ell2_r1_37:{304973, 304860, 304858, 303323,
236166, 304872, 303324, 12}`.

**A precise structural finding, not previously stated by Codex**: among
the 13 unresolved states, **every one already has a distinct compound
`(successor_signature, component_geometry)` profile** — no two of the
13 share a compound profile at all. **The deduplication step is
therefore a no-op on this data**: it removes nothing, because nothing
was duplicated at the compound-key level to begin with. The "8-state
batch" is consequently not really "one representative from each of
several groups" in any meaningful compressive sense — it is precisely
**the top 8 of 13 already-fully-distinct states, ranked by fewest
successors, then tightest proved bridge-distance lower bound, then
greatest depth**. This is a correct and faithful implementation of the
stated rule, but the rule's practical effect here is a priority
truncation, not a coverage-preserving compression.

- **Resource-profile coverage**: the 8 states touch **7 of the 18**
  `resource_profile_class_sha256` classes present across the whole
  22-state frontier.
- **Component-geometry coverage**: the 8 states touch **7 of the 19**
  `component_geometry_class_sha256` classes present across the whole
  frontier.
- **All 13 unresolved states are *not* represented**: the batch
  excludes `:3, :6, :305018, :303321, :13` — precisely the 5 states
  with the *highest* `legal_successor_count` (2, 2, 3, 3, 3
  respectively) among the 13, i.e. the batch systematically favors the
  narrowest, most tractable-looking states first and defers the
  broadest ones.
- **"Representative" is heuristic, not backed by any proved
  continuation equivalence** — confirmed on two independent grounds:
  first, Codex's own document explicitly disclaims the profiles as
  non-equivalences; second, given the compound-key dedup is a no-op
  here (previous paragraph), there is no actual equivalence class being
  represented at all — each "representative" simply *is* the one state
  its own unique profile describes, standing for nothing beyond itself.

### Assessment: is 8 × 25,000 the best next step?

- **A (all 13 independently)**: strictly more complete, and — given the
  dedup-is-a-no-op finding above — not meaningfully more expensive in
  proof-structure terms than the 8-batch, since there was never a real
  compression being exploited. The only savings from doing 8 first is
  raw compute (8 × 25,000 = 200,000 expansions vs. 13 × 25,000 =
  325,000), not any lost information.
- **B (a smaller proof-oriented subset)**: given every state's profile
  is already unique, there is no principled way to pick a smaller
  *provably representative* subset without an actual equivalence
  relation to justify it — any subset smaller than 13 is, on the
  current data, a resource-driven guess, exactly as large as the
  8-batch is.
- **C (hand analysis of the 9 exact-exhaustion subgraphs)**: these are
  already fully closed (§4) — further hand analysis of them could only
  extract a *shared mechanism* (candidate hand-theorem material) from
  data already in hand, at zero further computation cost. This is
  arguably higher-value *per unit effort* than either A or the 8-batch,
  since it requires no new search at all — only structural comparison
  of 9 already-complete certificates, exactly the kind of analysis this
  analyst's own role is suited to perform next, independent of whatever
  Codex does with the 13 open states.
- **D (deeper continuation of the single hardest profile)**: lowest
  proof value per unit effort — a single deep run tells us about one
  state, with no coverage or comparative value, and no reason from the
  current data to expect it converges faster than a breadth-first
  approach across several states.

**Given the "dedup is a no-op" finding, the honest ranking is: C first
(free, uses only existing data), then A over the specific 8-batch (more
complete for comparable effort, since no real compression was being
exploited), with D least justified.** This refines rather than
contradicts Codex's own "D_then_A" framing (Codex's "D" label refers to
the *structural-subfamily strategy*, not to this document's lettering
of the four options in this section) — Codex's own document is correct
that pure equal-effort-on-all-22 (Codex's strategy "A") is wasteful
this early, and correct that some prioritization is better than none;
this analysis adds the more precise finding that the prioritization
achieved is not the coverage-preserving one its own description implies.

## Final response summary

1. **Remote verification**: branch, commit, and parent relationship all
   confirmed exactly; all 5 files present and real (no LFS); one
   upstream provenance link (the round-53-era v7 ledger and 4.88 GB
   checkpoint) is unverifiable this round, disclosed rather than
   assumed.
2. **Exact class-count verification**: all six counts (22/22/22/18/22/19)
   confirmed exactly; only `exact_state_hash` and the left-`S6` class
   rest on proved equivalences, the other three are explicitly
   heuristic by construction, matching Codex's own disclaimer.
3. **Immediate-R2 subgroup verdict**: 9 states, all failing only
   `same_component`, each with an exactly-exhausted reachable subgraph
   (certificate unit: subgraph, not state or branch) — confirmed.
4. **Remaining-13 scope verdict**: only a 3-macro-step no-bridge bound
   is encoded for the 13, confirmed no stronger claim anywhere;
   recurrence is a true zero; collision saturation is non-monotone
   (data-backed); seven other quantities (`P,O,S,Ndef,Phi,hub_popcount,
   visited`) are separately confirmed monotone.
5. **421,219 vs 421,221**: **cannot be explained from any ledger field
   in this round's artifacts** — `421,221` is a hardcoded string
   inherited from an unverified prior-round figure, `421,219` does not
   appear anywhere in the fetched files at all. Reported as an open gap.
6. **Strategy-D verdict**: the exact batch and ranking were reproduced
   precisely, but the claimed "one representative per profile" coverage
   is misleading on this data — deduplication is a no-op (all 13
   profiles already unique), so the batch is a priority truncation
   (favoring low-successor-count states), covering 7/18 resource
   profiles and 7/19 component-geometry profiles, explicitly not all 13
   unresolved states. Recommended sequencing: hand analysis of the 9
   closed subgraphs first (free), then all 13 over the specific 8-batch
   if further search is pursued.

## What this document does not do

- Does not verify the round-53 process behind the 305,022-node v7
  checkpoint — unreachable this session.
- Does not resolve the 421,219/421,221 discrepancy — reported as
  unexplainable from available data, not guessed at.
- Does not claim Codex's methodology is flawed — the batch-selection
  code is a correct, faithful implementation of its stated rule; the
  finding is that the rule's practical effect on this particular data
  (a no-op deduplication) differs from what its description implies.
- No search run, no Codex file touched.

CLAUDE_R1_37_FRONTIER_PARTIAL
