# R2 source semantics: audit finding — the described error does not match the code

## 0. What was checked, and the result up front

**`CLAUDE_OBSERVATION`.** No commit was cited this round. Checked anyway:
`git ls-remote origin` shows `codex/round43-short-ell0-taxonomy`
unchanged at `24002fd` — the same commit already fully analyzed across
the last three rounds. No new branch or commit exists anywhere this
session can reach.

Because this round asks me to retract my *own* prior work, "no new
commit" is not the end of the check this time — reading the
already-fetched source code again *is* something this session can do
without running a search, and it directly adjudicates the specific
technical claim. I did that. **Result: I cannot confirm the described
error.** Re-reading `search_rr_target_a_exhaustive.py` (the exact file
already fetched and cited three rounds running) shows the live search
path uses `edge.run.state` as the R2 recognizer's source state —
**exactly what I already used and cited throughout every one of my
prior three documents**, and exactly what this round's own message
identifies as *"the literal R2 joint source"* (the one it calls
correct). I could not locate any code path, in this codebase, that uses
a different "macro-entry `pre_state`" for this purpose. The audit below
is performed honestly against what the code actually shows, not against
the premise as stated.

**Direct evidence, `evaluate_edge`** (lines 769-797, `search_rr_target_a_exhaustive.py`):

```python
def evaluate_edge(state, dec: Decoration, edge, *, prune_profile=...):
    ...
    child_dec = advance_decoration(edge.run.state, transition, dec)
    ...
    if dec.r_count == 1:
        ...
        recognizer = target_a_recognizer(edge.run.state, transition, dec, child_dec)
```

`evaluate_edge`'s first parameter, `state` — the macro-entry state, the
expanded parent node's position *before* this candidate edge's own
rotation run — is **never referenced anywhere in the function body**.
Only `edge.run.state` is passed to `target_a_recognizer`, and the same
is true at every other call site read this round:
`geometry_failure_record`/`same_component_failure_record`
(lines 1229-1233, both called with `edge.run.state`), and the older
engine's `is_target_a_edge` (`search_rr_target_a_unified.py`, read and
quoted two rounds ago: `pre = edge.run.state`). **Every recognizer call
site in every engine version read across this whole analysis thread uses
`edge.run.state`, consistently.** No inconsistency between "old
hierarchy" and "corrected" semantics was found — there appears to be
only one convention in use throughout.

## 1. Why macro-entry state and literal joint source are not interchangeable, in general

**`CLAUDE_HAND_PROOF`**, stated as general theory — this section answers
task 3 as a formal question, independent of whether the described defect
exists in this specific codebase (§0 shows it does not, but the abstract
question is still worth answering precisely, since a future engine
change could introduce exactly this bug):

1. A macro edge is a rotation-run of length `0≤ℓ≤5` followed by a joint.
   `ORBIT_PHASE` maps a literal permutation to an `(orbit, phase)` pair.
   Pure rotation (the `SIGMA` generator) does **not** preserve `E`-orbit
   membership in general — this is the entire reason a rotation-run can
   walk the position through several different orbits' worth of phases,
   already established and load-bearing in every one of this thread's
   prior rounds (it is the exact mechanism behind `r2_wrong_source_orbit`
   existing at all: a full `ℓ=5` run generically lands in an orbit
   unrelated to the one the walk started the run in).
2. Consequently, `ORBIT_PHASE[macro_entry_state.p]` and
   `ORBIT_PHASE[edge.run.state.p]` are, in general, **different orbits**
   whenever `ℓ>0`. They coincide only in the degenerate case `ℓ=0`.
3. The engine's own `extend()` classifies a weight-`≥2` joint as `R`
   (re-entry) versus `Z3` (fresh) using `new_orbit = (orbit_masks[q]==0)`,
   evaluated **at the state the joint actually fires from** — which is
   `edge.run.state`, by construction of `macro_edges`/`extend`'s own
   calling convention (the joint is applied *to* the post-rotation
   state). **This is the state whose orbit-openness decided `R` vs.
   `Z3` in the first place.** If the recognizer's same-component test
   used a *different* state's orbit for "the R2 source," it would be
   asking a question about an orbit that has no established relationship
   to *why this specific edge was even classified as an `R`* — the
   recognizer and the classifier would be silently talking about two
   different orbits for the same edge, an internal inconsistency, not
   merely an imprecision.
4. Therefore: **using the macro-entry state's orbit for the R2-source
   test would compute forest membership and same-component status for
   an orbit unrelated to the one the `R`-classification itself is about**
   — a different question, not a stricter or looser version of the same
   one. The two are not interchangeable for any `ℓ>0`, and `ℓ>0` is not a
   rare case in the data already read: **all 49,440 R2 candidates in the
   analyzed run have `ℓ=5` exactly** (established two rounds ago,
   re-cited not re-derived).

## 2. Corrected — in this case, *unchanged* — proof-safe definitions

**`CLAUDE_OBSERVATION`.** Since §0 found the already-used convention
already matches the one this round identifies as correct, the following
are **restated, not corrected** — no definition below differs from what
was written in the prior three documents:

- **R2 source**: `sq, sph = exact.ORBIT_PHASE[edge.run.state.p]` — the
  orbit/phase of the position immediately after the R2 candidate's own
  rotation run, immediately before its joint commits.
- **Pre-R2 incidence forest**: `incidence_components(edge.run.state)` —
  rebuilt fresh from `edge.run.state.orbit_masks` (never from a cached
  history summary, confirmed by direct code reading two rounds ago).
- **Same-component predicate**: `find(("q",sq)) == find(("q",tq))` under
  that same freshly-rebuilt union-find, `tq` from
  `ORBIT_PHASE[transition.target]` (the joint's own literal target,
  unambiguous — a joint has exactly one target, so there is no
  macro-entry-vs-run-state ambiguity on the target side at all, only on
  the source side, which is why the task only names "R2 source" and not
  "R2 target" as needing this clarification).
- **Target A boundary state**: an `R`-kind macro edge with `before.r_count
  == 1` (this is the second `R` of the word), whose child has `F_def≤1`,
  `H=0`, and whose R2 source/target (as defined above) share a component.
  Unchanged from `research/RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md`'s own
  formal statement, quoted, not re-derived, in the prior round.

## 3. Audit of prior claims

**`CLAUDE_OBSERVATION`**, task 1/2 combined. Every claim from the three
prior documents (`RR_SHORT_ELL0_R2_SOURCE_ORBIT_CLAUDE.md`,
`RR_SHORT_ELL0_PRODUCTIVE_R1_CLAUDE.md`,
`RR_SHORT_ELL0_REPAIR_THEORY_CLAUDE.md`) is classified below. The
overwhelming majority are classified **unaffected**, for two independent
reasons depending on the claim: either (a) the claim never used
`target_a_recognizer`/R2-source semantics at all, or (b) it did, and §0
shows that usage already matches `edge.run.state`.

| claim | classification | reason |
|---|---|---|
| Incidence-forest definition (vertices/edges/hub) | **unaffected semantic/code theorem** | definitional, independent of which state `incidence_components` is later called on |
| Per-edge-type transition laws (`Z2`/`Z3`/`R`/rotation effects) | **unaffected semantic/code theorem** | pure `extend()`/`advance_decoration` facts, no dependency on recognizer pre-state choice |
| "44,021 failures all descend from one R1 event, `ℓ=5`, `r2_wrong_source_orbit`" | **unaffected observation** | computed via `edge.run.state`-based fields already exported by the engine; matches §0's confirmed convention |
| "5,419 `not_same_component` failures, component-class distribution" | **unaffected observation** | same source, `edge.run.state`-based |
| "Candidate theorem false as stated (11% clear source-orbit test)" | **unaffected observation** | direct arithmetic on the two figures above |
| Frontier structural profiles (85 states, 8 profiles) | **unaffected observation** | does not touch R2-source semantics at all — frontier states are pre-R2 positions, not R2 candidates |
| Ranking-function search (no theorem found) | **unaffected — still valid observation** | negative result, independent of R2-source convention |
| Preparation-spine formalization (four R1 events, one shared spine) | **unaffected semantic/code theorem** | R1 is never passed through `target_a_recognizer` at all — only `R2` (the *second* `R`) is recognizer-tested; R1's own classification uses only `joint_kind`/`extend`, untouched by this question |
| Hub-position coincidence (orbit 120 phase 0 = hex 0) | **unaffected semantic/code theorem** | a fact about `hexagon_id`/`ORBIT_PHASE` applied to specific literal targets, not about recognizer pre-state choice |
| `CH1` vs. `PRE_R_COMPLETER_EVENT_ORDER` | **unaffected semantic/code theorem** | built from `Decoration.completer`/`Decoration.r1`, entirely separate machinery from `target_a_recognizer` |
| "Productive branch = scheduling artifact of LIFO traversal" | **unaffected observation** | grounded in the run's own `config.traversal` field, unrelated to R2-source semantics |
| "`Z3` re-entry is not a real move category" | **unaffected semantic/code theorem** | derived from `joint_kind`'s definition (`weight`, `abandonment`, `new_orbit`) alone — no `ORBIT_PHASE`/pre-state term anywhere in that derivation |
| "`Z2` can merge two distinct components" (Lemma A refutation) | **unaffected semantic/code theorem** | a fact about `incidence_components`'s union-find mechanics applied generically, independent of which specific state triggered its construction |
| "Any legal repair changes the future R2 source orbit" (Lemma C) | **unaffected semantic/code theorem** | proof is about position-shift under an inserted edge — a walk-mechanics fact, not a recognizer-pre-state fact |
| "Merging `Z3` need not touch the hub" (Lemma B refutation) | **unaffected observation** | uses `r1_target_component`/`r2_source_component` fields, both `edge.run.state`-derived per §0 |
| "Geometry preservation independent of completer timing" (Lemma D refutation) | **unaffected semantic/code theorem** | `F_def`'s update rule is a fact about `state.visited(word_after(state.p, SIGMA))`, no recognizer term at all |
| "Post-completer repair does not necessarily cause `F_exceeded`" (Lemma E refutation) | **unaffected — empirical part re-confirmed** | the exhaustive `F={1}` evidence over 85 frontier states does not depend on R2-source semantics (frontier states are not R2 candidates) |
| Repair template (§6 of the repair-theory document) | **unaffected proposal** | built from the above, none of which is affected |

**No claim in any of the three prior documents is classified "dependent
on invalid R2 classification" or "retraction required."** One item is
classified **undecided pending corrected replay**, not because a defect
was found in it, but because it was never claimed with certainty in the
first place: the open hypothesis (prior round, §3) that `ℓ=5`-only R2
candidates arise from `exact_permutation_collision` eliminating shorter
rotations first — this was already flagged as *unconfirmed* when
written, and remains exactly that; nothing this round changes its status
either direction.

## 4. On not claiming exhaustiveness

**`CLAUDE_OBSERVATION`, restated, not newly added.** No prior document in
this thread claimed the 100,250-node prefix, the 49,440 R2 candidates, or
any subset of them constitute an exhaustive search of `short_ell0`. Every
document explicitly carried `INCOMPLETE`/bounded-pilot framing forward.
This round's instruction not to claim exhaustiveness is honored by
continuing that same posture, not by a new correction.

## 5. On "preserving the surviving exact statement"

**`CLAUDE_OBSERVATION` — this cannot be preserved as a verified fact,
because the data it describes does not exist in anything this session
can reach.** The instructed statement — *"within the corrected replayed
prefix, the sole literal Target A boundary is left-`S6` equivalent to
known-18 and is Target-B closed"* — describes a specific boundary, a
specific canonicalization result, and a specific Target-B closure
certificate, none of which appear in any file this session has read. No
commit contains a `1`-hit result, a `3,214`-node helper-free closure, or
a left-`S6` equivalence check against the known-18 corpus. **This is not
a claim that the statement is false — it is a report that there is
nothing to check it against**, exactly the same posture taken toward the
`38,406`-hit figure two rounds ago. If and when such a checkpoint and
certificate are pushed to a reachable branch, `research/
RR_SHORT_ELL0_TARGET_B_FRAMEWORK_CLAUDE.md`'s own checklist (§6 of that
document) is already the prepared procedure for verifying exactly this
kind of claim — canonical-hash comparison against the known-18 corpus,
then per-boundary precondition checks before any capacity theorem is
applied to certify closure.

## What this document does not do

- Does not retract any claim from the three prior documents — the audit
  found none warranted.
- Does not confirm the `38,406→1` collapse, the `5,419` vs. `38,405`
  figures cited this round, or the `3,214`-node Target-B closure — none
  are checkable from anything reachable.
- Does not claim the described "critical R2-source semantics error" is
  impossible in general — §1 explains precisely when and why such an
  error *would* matter, as a piece of standing theory, independent of
  whether it applies here.
- Runs no search, edits no Codex file.

## Amendment (commit `b09f1d5`, branch `codex/round-r2-literal-source-correction`)

**`CLAUDE_OBSERVATION`, superseding the "not checkable" items above, not
retracting the rest of this document.** The correction branch is now
reachable (`git fetch` + `git log` + independent GitHub `list_branches`
confirmation). Reading the actual diff shows the real defect was **not**
in `evaluate_edge`/`target_a_recognizer` — that call site's diff is a
pure rename (`pre_state`→`joint_source_state`), value unchanged, already
`edge.run.state` both before and after — confirming this document's §0
finding was correct *for the scope it covered*. The real defect was in
`hierarchy_for_r2` (`src/search_rr_short_ell0_repair_fair.py`), a
function that did not exist on any branch reachable when this document
was written, and so was never audited, in either direction, by anything
above.

**Independently reproduced, not merely read:** checked out `b09f1d5`
into an isolated `git worktree` and *ran*
`tests/test_rr_short_ell0_repair_fair.py` directly. All 5 tests pass,
including `test_r2_literal_joint_source_regression_fixture`, which
reproduced the claimed discrepancy myself — `target_a_recognizer` at
macro-entry state returns `same_component=True` for the fixture, at
`edge.run.state` returns `same_component=False`, for the identical
literal trace. The corrected engine's full 89-test suite also passes in
the same worktree.

**Result-file integrity:** the four smaller corrected JSON files'
recorded `input_sha256` values initially appeared not to match the
checked-out files; traced this to CRLF/LF line-ending normalization
between the Windows authoring environment and this Linux checkout
(re-inserting CRLF reproduces the recorded hash exactly, for all four
files — not a data-integrity concern).

**Target-B closure cross-check:** the surviving boundary's ledger row
reports `Phi=0` and `available_R_capacity=1` — exactly the two
preconditions `RR_SHORT_ELL0_TARGET_B_FRAMEWORK_CLAUDE.md` flagged as
required-not-assumable before applying the full-segment capacity
theorem — and explicitly records `phase_helper_used: false`,
`disallowed_helper_name: true_phase_walk_capacity`, honoring the Round
38 capacity-helper firewall. The DFS is explicitly not truncated (3,214
of a 20,000-node cap).

**Known-18 mapping cross-check:** the surviving boundary's
`raw_state_hash` matches known-18 id `short_ell0_33d70b4249b7` — an id
this session independently recognizes from
`outputs/rr_short_survivor_ledger.json`, read at the very start of this
research thread, long before any short_ell0 R1/R2 work began. The
mapping is via literal replay plus the already-proven global left-`S6`
normalization, not a coordinate-only match.

**This document's own zero-retractions conclusion is unchanged**: no
claim audited above depended on `hierarchy_for_r2`, so none required
retraction then or now. The correction itself — figures, mapping, and
closure — is independently verified true here, not merely relayed.

CLAUDE_R2_SEMANTICS_AUDIT_COMPLETE

CLAUDE_CORRECTION_VERIFIED
