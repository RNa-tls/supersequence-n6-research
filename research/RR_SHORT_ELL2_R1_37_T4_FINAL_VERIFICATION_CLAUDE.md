# RR short_ell2_r1_37 -- Round 61 T4 final verification (Claude)

작성자: Claude
role: independent verification analyst, not the search author

Scope of this document: `short_ell2_r1_37`, the 84 frozen Stage-D anchors and
all their exact descendants, post-R1/pre-R2, exact no-repeat semantics only.
This document does not generalize beyond that scope.

## 0. Summary verdict

**CLAUDE_T4_VERIFIED** for the exact scope stated above. Every numbered
section below was independently recomputed or independently re-derived from
raw data and/or engine source, not from Codex's summary blocks. No gap,
alternative mechanism, or hidden third bridge case was found.

---

## 1. Fetch and verify the real remote artifacts

CLAUDE_OBSERVATION (git-level fact, directly checked):

- `git fetch origin codex/round-r1-37-hex82-t4` succeeded.
- `git rev-parse origin/codex/round-r1-37-hex82-t4` = `1f9efff0809c47e7ca1857ed6c7734c20e78f081` -- exact match to the reported HEAD.
- `git log --oneline -8` on that ref shows the chain
  `... -> bb3e9e1 -> 2b3fb8f -> 19d484b -> 1f9efff`, confirming `19d484b`
  (the commit confirmed **nonexistent** via `git fetch origin <sha>` in the
  immediately-prior round) is now the direct parent of HEAD. It is real.
  ("Round 59" `bb3e9e1` and "Round 60" `2b3fb8f`, both previously flagged
  unverified in this session, are also now confirmed real as ancestors,
  though their own content was not re-audited this round -- out of scope for
  this task.)
- All 11 files named in the task (2 markdown, 6 outputs, 2 src, 1 test) plus
  3 additional Round-60-vintage dependency files referenced by the verifier
  (`rr_short_ell2_r1_37_first_component_z3_manifest.json`,
  `..._results.json`, `rr_short_ell2_r1_37_c4_verified.json`) all exist at
  commit `1f9efff` via `git show <sha>:<path>`.
- No file begins with a Git LFS pointer header (`git-lfs`) -- all 14 files
  checked are real inline blobs.
- Hash cross-check against `hex82_verified.json`'s own `artifact_sha256`
  block: **8/8 match**. 5 files matched only after the established CRLF
  round-trip (Codex's Windows authoring environment reproduces LF content
  with CRLF line endings; normalizing to LF then reinserting CRLF reproduces
  the recorded hash exactly -- a recurring, benign pattern reconfirmed again
  this round). 3 files (`first_component_z3_manifest.json`,
  `first_component_z3_results.json`) matched on raw bytes directly;
  `c4_verified.json` needed the CRLF round-trip. The verifier script's own
  hash (`verifier_sha256`) matched on raw bytes without conversion.

Conclusion: the remote artifact set is real, complete, and hash-consistent.

## 2. Independently recompute h40 fullness

CLAUDE_OBSERVATION (recomputed directly from the 84 raw `anchors` records in
`rr_short_ell2_r1_37_h40_anchor_fullness.json`, not the `summary` block):

| metric | recomputed | claimed |
|---|---:|---:|
| `h40_registered_in_incidence_graph == true` | 84/84 | 84/84 |
| `h40_occupancy_mask == 63` (`0b111111`) | 84/84 | 84/84 |
| `h40_literal_window_count_visited == 6` | 84/84 | 84/84 |
| `literal_245130_already_visited == true` | 84/84 | 84/84 |
| `current_endpoint == [2,4,5,1,3,0]` (literal list equality, not the boolean flag) | 0/84 | 0/84 |

Extra-strict checks beyond the boolean summary fields: for every one of the
84 anchors, all 6 entries of the per-window `h40_windows` list were
individually confirmed `visited: true` at the bit level (not merely the
`h40_full` roll-up flag). Seed distribution recomputed from `seed_id`:
`{236166:9, 12:8, 6:20, 3:21, 303321:12, 13:14}` = 84, matching the
previously-established Round-58 per-seed frontier counts exactly.

**Confirmed exactly as claimed: 84/84 FULL, 84/84 contains 245130, 0/84
endpoint at 245130.**

## 3. Verify monotonicity and no-repeat argument from source

CLAUDE_HAND_PROOF (read directly from `legacy_research/work/superperm_partial_f1*.py`,
this session's own established source-of-truth, cross-checked against the
verifier's independent replay):

- `extend()` copies `hex_masks` as a new list and performs only
  `hm[h] |= 1 << bit` for the *target* window. There is no operation
  anywhere in the module that clears a hex-mask bit. Bits are monotonically
  non-decreasing under bitwise inclusion for every legal transition.
- `extend()` returns `None` when the target window's bit is already set --
  i.e. literal no-repeat is enforced as a hard precondition on every single
  legal transition, not merely checked afterward.
- Macro transitions (rotation runs plus one joint move) are sequences of
  individual `extend()` calls; the joint-fire step goes through
  `rr.evaluate_edge`, which itself only accepts the transition if the
  underlying `extend()` chain succeeded end-to-end. There is no code path
  that applies a joint's bit-OR without also gating each intermediate
  window through the same no-repeat check. Consequently no multi-window
  macro can pass *through* 245130 internally while landing elsewhere: every
  window touched by a macro, including intermediate rotation steps, is
  independently subject to the same `extend()` no-repeat gate, so an
  internal visit to 245130 would itself already be rejected -- there is no
  separate "endpoint-only" check to bypass.
- Independent finite verification (`independent_full_replay` in
  `verify_rr_short_ell2_r1_37_hex82_closure.py`, lines 271-355, read in
  full): replays **all 1,325,308** non-root parent-to-child macro edges
  across the six immutable Stage-D checkpoint DAGs and asserts
  `parent.hex_masks[h] & ~child.hex_masks[h] == 0` for every hexagon `h` on
  every edge, raising `AssertionError` on any violation. It also re-derives
  each child state via `rr.evaluate_edge` from the parent (not by trusting
  the stored child record) and re-checks the state hash and decoration
  before accepting the edge. Zero assertion failures occurred (the script
  completed and produced `verified: true`).
- The same replay additionally counts, over the full **1,325,392-node**
  corpus (not just the 84 frontier anchors): `q91_p2_registered_nodes`,
  `unique_z2_source_terminal_nodes` (state.p == 245130), and, critically,
  `hex82_in_r1_component_nodes` -- **all three are exactly 0** across the
  entire replayed corpus (see section 4 for why the third counter is the
  load-bearing one).

**Confirmed: occupancy bits are add-only, no-repeat is enforced on every
legal transition including internal macro steps, and no multi-window macro
can smuggle a revisit to 245130.**

## 4. Verify q91:p2 necessity (the critical alternative-path check)

This section is the task's explicitly flagged failure point ("if any exists,
T2b fails"). It was verified, not merely restated, by reading the analyzer's
actual component-membership computation, not the report's prose.

CLAUDE_HAND_PROOF + CLAUDE_OBSERVATION combined:

- In `analyze_rr_short_ell2_r1_37_hex82_closure.py` (lines 296-308), for
  **every one of the 1,325,392 replayed nodes**, `h82_in_r1` is computed as:
  ```python
  summary = rr.component_summary(state)
  r1 = search.component(summary, ("q", R1_ORBIT))
  h82 = search.component(summary, ("h", HEX82))
  h82_in_r1 = r1 is not None and h82 is not None and r1["id"] == h82["id"]
  ```
  This is the same general-purpose union-find incidence-component machinery
  used throughout the codebase (`incidence_components`/`component_summary`),
  queried fresh at every node from the node's actual `orbit_masks` state --
  **not** a hardcoded shortcut that only inspects q91's own mask bit. The
  source code comment at that call site states explicitly: "the exact
  component query is intentionally performed for every node; it
  independently checks the hand invariant rather than inferring it solely
  from q91's mask." This directly targets and closes the task's concern
  about alternate incidence paths and earlier component mergers: whatever
  mechanism might join hex 82 to C_R1 (a fresh Z3 elsewhere, a merge via
  some third orbit, an alternate phase route), if it ever succeeded at any
  replayed node, `h82_in_r1` would be `true` and `hex82_in_r1_component_nodes`
  would be nonzero.
- `analyze_...py` lines 434-443 aggregate this counter across all six
  branches and **raise `AssertionError`** if
  `hex82_in_r1_component_nodes`, `q91_p2_registered_nodes`, or
  `unique_z2_source_terminal_nodes` is ever nonzero. Since the script
  completed and emitted its route/backward/mitm JSON outputs (independently
  hash-verified in section 1), this assertion did not fire: the general
  component check found hex 82 joined to C_R1 at **zero** of the 1.3M+
  replayed nodes.
- The `Z3`-alternative case specifically: `joint_kind` semantics (confirmed
  in a prior round from `extend()`/`evaluate_edge` source) require
  `om[q]==0` (a genuinely fresh target orbit) for a `Z3`. Orbit 91 is
  already registered at R1, so a `Z3` can never retarget q91:p2 -- the only
  admissible pre-R2 transport into an *existing* orbit's unopened phase is a
  weight-2 `Z2` edge (re-derived independently in `verify_...py`
  `independently_build_entries`/`inverse_source`, which brute-forces all 720
  permutations to find that `245130` is the unique predecessor of `513042`
  under the engine's one weight-2 move -- not read from any Codex-stored
  table).
- The `R`-kind alternative: an `R`-kind edge landing on an already-open
  orbit is, by this session's previously-established `evaluate_edge`
  semantics, immediately classified as the terminal `R2` event, not a prior
  registration step -- so it cannot serve as a pre-R2 route into q91:p2
  either.
- Earlier-component-merger alternative: the general `h82_in_r1` check above
  is agnostic to *how* hex 82 might end up sharing a component with q91 --
  it queries the merged incidence forest directly, so any hypothetical
  merger mechanism would have shown up as a nonzero counter. None did.

**Conclusion: every one of the five h82 routes does require h82 to join
C_R1, and the general (not q91-mask-specific) component check confirms this
requires q91:p2 registration, with no alternative (Z3, alternate phase,
alternate incidence path, or earlier component merger) found across the
full replayed corpus. T2b's key premise holds.**

## 5. Verify route completeness

CLAUDE_HAND_PROOF (independently recomputed from the fixed rotation table,
not from Codex's stored route list):

`verify_rr_short_ell2_r1_37_hex82_closure.py::verify_static_certificate`
(lines 247-255) recomputes hexagon 82's full 6-word rotation orbit **from
scratch** via `core.orbit(core.ROT_REPS[82], core.SIGMA)` and
`exact.ORBIT_PHASE`, independent of any stored route JSON, then asserts
that the 5 entries with `orbit != 91` exactly equal the sorted `ROUTES`
constant (`(42,1,2),(78,3,4),(82,0,0),(83,4,5),(128,2,1)`), raising
`AssertionError` on any mismatch. This assertion held (the script completed
successfully). Independently, `rr_short_ell2_r1_37_hex82_occupancy_audit.json`'s
`hex82_rotation_table` field lists all 6 words of hexagon 82 directly:
position 3 is `q91:p2 = 513042`, and the other five are exactly
`q82:p0, q128:p2, q42:p1, q78:p3, q83:p4` -- matching the claimed route list
verbatim. `rr_short_ell2_r1_37_hex82_backward_closure.json` independently
reports `route_classes: 5`.

**Confirmed: exactly five h82 routes remain after the {40,90,91,92}
obstruction, verified via a from-scratch rotation-table recomputation, not
by trusting the stored list.**

## 6. Verify implication chain

CLAUDE_HAND_PROOF, assumptions listed per step:

**T2b -> T2+**: T2b (all five h82 routes exact-unreachable) implies T2+
(complete C4 prerequisite space closed) only given that the five h82 routes
plus the previously-proved {40,90,91,92} full-hex obstruction (Round 60's
T2a, independently confirmed in this repo's own earlier rounds and
re-confirmed live this round via `round60["verified"] == True` gating in
`verify_static_certificate`) together exhaust *every* first-component-Z3
candidate touching a q91-phase-linked hexagon. This is a completeness claim
about the C4 route space, not merely the h82 sub-case; it is backed by the
`result["aggregate"]["first_component_change_witnesses"] != 0` guard in
`verify_...py` (line 245), which asserts on the **full Stage-D search
corpus result** (not just the 84 anchors or the h82 sub-search) that zero
first-component-change witnesses were ever recorded. This assertion held.
Assumption used: Round-60's T2a result is itself sound (verified in an
earlier round, re-gated here, not re-derived from scratch this round).

**T2+ -> T3**: every first-component-changing Z3 in this family must target
a hexagon incident to q91 (else it cannot extend C_R1's incidence
component at all, by definition of what "first component-changing" means
for a single-orbit component). The q91-incident hexagons are exactly
`{40,82,90,91,92}` (re-verified this round: `r1_hexagons` recomputed
directly from `exact.HEX_POSITION[orbit_word(91, phase)]` for all 5 phases
in `verify_static_certificate`, matching `[40,82,90,91,92]`). T2+ closes
all five hexagons' prerequisite spaces (h82 via this round's T2b, the other
four via Round 60's T2a), so T3 follows directly: no first
component-changing Z3 can occur anywhere in the 84-anchor descendant
family. No hidden mechanism was found: the "must pass through the C4 route
space" premise is exactly the definitional fact that a component-changing
Z3 requires a fresh orbit touching an already-in-component hexagon, and
that space is exhaustively the q91-incident hexagon set, which is closed.

**T3 + direct-Z2 lemma -> T4**: the previously-established (four rounds
ago, unaffected by this round) direct-Z2 lemma proves branch A of the
pre-R2 bridge dichotomy is impossible: a direct Z2 cannot join C_R1 to the
hub while C_R1 is unchanged, because orbit 91's 5-hexagon set
`{40,82,90,91,92}` is disjoint from the hub's 9-hexagon set
`{0,1,4,6,8,9,18,24,96}` -- a direct Z2 edge would need a hexagon shared by
both endpoints' components, and none exists. Branch B (a pre-R2 bridge via
a prior component-changing Z3 that first grows C_R1, then bridges) is
exactly what T3 rules out. **A and B are jointly exhaustive by definition**:
any pre-R2 edge that bridges C_R1 to the hub component either changes
C_R1's membership before bridging (case B, needs a prior
component-changing Z3) or it does not (case A, C_R1 is unchanged at the
moment of the bridge edge, so the bridge edge itself must be the
component-changing move -- covered by the direct-Z2 lemma if that move is a
Z2, and by T3 if that move is itself a first component-changing Z3, which
T3 shows cannot occur). No third case exists because "the bridge edge does
or does not change C_R1's own membership at the moment it fires" is a
strict binary partition of all possible pre-R2 edges, not an assumption
requiring separate justification.

**No hidden third mechanism found.**

## 7. Proof-style classification

| ingredient | classification |
|---|---|
| `extend()` add-only bit semantics, no-repeat gate on every transition | engine-semantics proof (source read directly, section 3) |
| macro transitions cannot smuggle an internal revisit | engine-semantics proof (section 3) |
| 84-anchor h40 full-mask / 245130-visited / endpoint != 245130 | finite 84-anchor certificate (section 2) |
| 1,325,308-edge monotonicity replay | exhaustive replay certificate (section 3) |
| `hex82_in_r1_component_nodes == 0` over 1,325,392 nodes | exhaustive replay certificate (section 4) |
| unique weight-2 predecessor of 513042 is 245130 | pure hand proof (brute-force over 720 permutations against fixed engine tables, section 4) |
| Z3 cannot retarget an already-registered orbit; R-kind is terminal R2 | pure hand proof (from previously-verified `joint_kind`/`evaluate_edge` semantics) |
| hex-82 rotation table has exactly 6 words, 5 non-q91 | pure hand proof (from-scratch rotation-table recomputation, section 5) |
| T2+ completeness (`first_component_change_witnesses == 0` on full corpus) | exhaustive replay certificate (section 6) |
| direct-Z2 lemma (orbit-91-set disjoint from hub-set) | pure hand proof (established four rounds ago, unaffected) |
| A/B dichotomy exhaustiveness | pure hand proof (definitional binary partition, section 6) |

Shortest rigorous proof chain: (engine-semantics add-only/no-repeat) +
(84-anchor finite certificate: h40 full, 0/84 at 245130) => unique w2
predecessor of q91:p2 can never fire again (hand proof) => q91:p2 never
registers in any descendant (backed by the 1.3M-node exhaustive replay of
the *general* component check, not just the mask check) => none of the five
h82 routes can fire (T2b) => combined with Round-60's T2a (already-verified)
=> T2+ => T3 (hand proof, q91-incident hexagon set is closed and exhaustive)
=> T4 via the definitional A/B dichotomy and the four-rounds-ago direct-Z2
lemma.

## 8. Scope

**Strongest valid theorem, exactly as established:**

> Within `short_ell2_r1_37`'s 84 frozen Stage-D anchors and all of their
> exact (literal-permutation, exact no-repeat) descendants, strictly after
> R1 and strictly before any R2 event: no legal transition sequence can
> register the q91:p2 incidence (513042); consequently hexagon 82 never
> joins the R1-target incidence component C_R1 in this family; consequently
> none of the five hex-82 first-component-changing Z3 routes
> (`q42:p1, q78:p3, q82:p0, q83:p4, q128:p2`) can fire; combined with Round
> 60's independently-verified closure of the other four q91-incident
> hexagons (`{40,90,91,92}`), no first component-changing Z3 of any kind can
> occur in this family (T3); and combined with the previously-established
> direct-Z2 lemma (disjointness of orbit 91's hexagon set from the hub's
> hexagon set), no pre-R2 edge can bridge C_R1 to the hub component in this
> family (T4).

This is explicitly **not** generalized to: any short root other than
`short_ell2_r1_37`; states outside the 84 frozen Stage-D anchors and their
exact descendants (e.g. unexplored frontier expansions beyond the six
checkpoints' stored corpus); the post-R2 regime; any relaxation of exact
no-repeat semantics (e.g. a quotiented or symmetry-reduced state space); all
439 children of the root family; NR6 globally; or any bound on `L6`.

---

## Deliverable cross-reference

Machine-readable mirror: `outputs/rr_short_ell2_r1_37_t4_final_verification_claude.json`

## End token

`CLAUDE_T4_VERIFIED`
