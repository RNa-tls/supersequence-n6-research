# 7-of-8 exhaustion: conditional proof-significance analysis

## 0. Verification status — read first

**No commit or branch was cited this round, and none was found.**
`git fetch origin --prune` and `git fetch --all --prune` show the same
seven remote branches already known — `codex/round-v6-endpoint-v7-plan`
is unchanged, still at `4792891` (the commit independently verified last
round, whose own manifest recorded `"status":
"PLAN_ONLY_NO_SEARCH_STARTED"`). No `v7`-result branch, no new commit
anywhere, and a repository-wide search for any of this round's specific
numbers turns up nothing. **Every figure below (7/8 exhausted,
`short_ell2_r1_37` at 305,000 expansions/frontier 22, 421,221 total
nodes, 204,685 R2 records, "B1-B6 all zero") is asserted in the prompt
only.**

One internal inconsistency worth flagging regardless of verification
status: the prompt states "421,219 B0 states with no B1 event" in task 4
but "421,221 nodes" in the headline figures — a 2-node discrepancy
between two numbers in the same message. This may be an immaterial
rounding/labeling difference (e.g. B0-state count vs. total node count
including non-B0 nodes) but is noted here as a precise, checkable
detail rather than silently reconciled.

Per this session's established practice (most recently vindicated two
rounds ago, when unverified "v6" figures were confirmed accurate once a
real branch landed the following round), this document performs the
requested six tasks **conditionally** — reasoning about what would
follow *if* the figures are accurate — without promoting any of them to
confirmed fact.

## 1. Strongest exact theorem supported by the seven exhausted branches, conditional

*If* the seven branches (`short_ell4_r1_12`, `short_ell1_r1_98`,
`short_ell2_r1_40`, `short_ell3_r1_64`, `short_ell2_r1_107`,
`short_ell3_r1_56`, and now `short_ell2_r1_70`) are genuinely
naturally exhausted (queue empty, no cap), the strongest statement the
data would support is a **conjunction of seven independent, per-child
exact certificates**:

> For each of these seven specific `R1`-provenance children, under the
> literal-`R2`-source-corrected recognizer and the `TARGET_A_SAFE_
> PROFILE` prune set, the *complete* reachable continuation space
> contains no `FOUND_TARGET_A` outcome and no incidence-forest merge
> between the `R1`-target orbit's component and the hub component.

This is exact and strong **for these seven specific children** — but it
is a finite conjunction of seven separately-verified facts, not a
symbolic argument that would extend to an eighth child, let alone to the
remaining 431 children in the 439-child corpus or the 105 capped
children outside the top-8. Nothing here is a generalized theorem over
an infinite or even an unenumerated family; it is exactly seven
completed finite searches.

## 2. Why the one capped branch blocks a family-wide theorem

This is a matter of logical form, not evidence weight. Any family-wide
claim of the shape "no child in the top-8 family admits a bridge or a
Target A hit" is a **universally quantified statement over 8 cases**.
Seven exact certificates verify the statement for seven of the eight
instances — they say **nothing at all** about the eighth, by
construction: an exact certificate for child *A* is silent about child
*B*. `short_ell2_r1_37` is exactly the one instance the universal
quantifier has not yet been discharged for, and no amount of certainty
about the other seven substitutes for checking it, because the seven
certificates and the eighth case are logically independent facts about
disjoint search spaces. This is unaffected by *how close* to closure
`short_ell2_r1_37` reportedly is (frontier size 22, if accurate) — the
gap is binary (checked / not yet checked), not a matter of degree.

## 3. Candidate ranking functions or monotone invariants for 7/8 exhaustion

Grounded in this session's own already-verified formal derivations
(the component-bridge mechanism analysis from three rounds ago),
several candidate quantities are worth naming as **explanatory
candidates**, not yet promoted to a proof of why exhaustion occurs so
broadly:

- **`F`-budget exhaustion** (`F <= TARGET_F = 1`, already proven exact):
  every joint after the root must be "forced" (non-abandoning); this
  sharply restricts which weight&ge;2 targets are ever legal at all,
  and is the most literal explanation for why literal-collision
  saturation dominates prune histograms in every branch checked so far.
- **Total-orbit-count ceiling**: since only `Z3` opens a fresh orbit,
  and the total number of orbits is a fixed global constant
  (`ORBIT_COUNT`), the number of times a branch can ever open a new
  orbit is absolutely bounded; once every reachable orbit is either
  fully visited or already open, only `Z2`/`R` remain, both far more
  constrained (`Z2` bounded to 5 phases per orbit, `R` immediately
  terminal). This gives a hard finite bound on branch length,
  independent of any bridge question, but does not by itself explain
  the *specific* zero-bridge outcome.
- **`hub_touch_count <= 2`**: an already-proven exact resource cap,
  directly limiting how many times the walk can return to the single
  distinguished hub hexagon.
- **`R`-budget (exactly 2 `R` events, the second always terminal)**:
  already proven; bounds the number of "chances" a branch gets at
  `R2` to exactly one per branch.
- **The genuinely explanatory candidate, not yet a theorem**: the
  "source-orbit registration barrier" itself — a monotone claim that
  the `R1`-target orbit's incidence-forest component, once isolated at
  admission, tends to stay isolated because every forced (non-
  abandoning) `Z2`/`Z3` continuation lands on a hexagon that has not
  yet been touched by anything in the hub's component. If a precise
  combinatorial argument for *why* this coincidence essentially never
  occurs (rather than merely observing that it has not occurred) could
  be found — e.g., a counting argument on how many of the fixed,
  finite `HEX_POSITION`/`ORBIT_PHASE` tables' hexagons are shared
  between an `R1`-target orbit's reachable phase set and hub's
  component — that would be the actual monotone invariant underlying
  the 7/8 (or, if accurate, 8/8) exhaustion pattern. This has not been
  derived in this document or, so far as verifiable, anywhere else.

## 4. What does a large zero-hit count actually suggest?

*If* 421,219 (or 421,221 — see section 0's flagged discrepancy) `B0`
states with no `B1` event is accurate, the same grading discipline
applied throughout this session's work applies here: a large finite
negative count is evidence, never proof, and the four listed
possibilities are not equally supported.

- **Structural impossibility**: would require a combinatorial argument
  independent of the count itself (see section 3's unfinished
  candidate) — **not established** by the count alone, however large.
- **A missing transition type**: this session has already independently
  verified, from source, that the underlying search's move enumeration
  (`iter_raw_macro_candidates`, `macro.rotation_runs(state) x
  macro.NONROT_H0`) is exhaustive over the complete RR move alphabet —
  so for *that* engine specifically, a missing-transition-type
  explanation is **unlikely**. This document cannot extend that
  confidence to whatever "`B1`" specifically denotes this round, since
  no file defining that term was found — flagged as an open
  terminology gap, not resolved here.
- **A long-tail rare event**: plausible and not excluded — a large but
  still-finite sample cannot distinguish "never happens" from "happens
  at a rate far below 1-in-400,000" no matter how large the sample gets,
  without an independent argument bounding the true rate.
- **Bounded evidence only**: **the correct default grade**, consistent
  with every other zero-occurrence finding graded in this session's
  prior work — strong, but not a certificate, and not yet a theorem.

## 5. Smallest possible counterexample shape for `short_ell2_r1_37`

This restates, precisely, the minimal template already derived three
rounds ago (the component-bridge document), now specifically scoped to
this one branch:

> A single legal, forced (non-abandoning) `Z2` or `Z3` edge, fired from
> some node in `short_ell2_r1_37`'s (reportedly 22-node) frontier, whose
> target hexagon is already a member of the hub component in that
> frontier node's incidence forest and is *not* equal to `hub_id`
> itself — followed by a legal `R`-kind edge (the branch's `R2`
> candidate) whose target orbit is *also* in that now-merged component,
> with `F_def == 1`, `H == 0`, and `hub_touch_count <= 2` all still
> satisfied at that point.

This is the minimal shape because nothing weaker can merge the two
components at all (per the exact mechanism derived three rounds ago:
only `Z2`/`Z3` can add a merging incidence-forest edge, and only if the
specific hexagon coincidence exists), and nothing beyond this single
bridge-plus-`R2` pair is needed once the merge occurs (the recognizer's
other conditions are ordinary, already-satisfied bookkeeping in this
family). **Whether this specific coincidence exists anywhere in
`short_ell2_r1_37`'s remaining frontier is exactly the open question**
this round's report does not resolve for this analyst, since no data
file exists to check it against.

## 6. Recommended next mathematical step

**Conditional on the reported frontier size (22 nodes) being accurate**:
**frontier classification**, not further blind deepening. At this
reported scale, directly enumerating each of the (claimed) 22 remaining
frontier nodes' legal successors and checking each one explicitly
against section 5's minimal template is cheaper, more decisive, and
strictly more informative per unit effort than raising an expansion cap
again — it either finds the template realized somewhere (a constructive
counterexample, resolving the branch outright) or, if none of the 22
nodes satisfies it, converts a large but bounded observation into an
actual **finite, hand-checkable certificate for this one branch
specifically** (22 explicit non-matches, verified by direct inspection
rather than by search volume). This is a genuine escalation toward a
hand-proof attempt for this one branch, conditional on the frontier
really being that small — if the true frontier is much larger than
reported, deeper exact continuation would remain the more tractable
option. Given this session cannot verify the frontier size this round,
the recommendation is stated as conditional rather than unconditional.

## What this document does not do

- Does not confirm any figure in this round's report — no commit or
  file was found to check them against.
- Does not resolve the internal 421,219-vs-421,221 discrepancy — flagged,
  not adjudicated, since no source data exists to determine which (if
  either) is correct.
- Does not claim the top-8 bridge conjecture is proved, disproved, or
  "close" in any quantifiable sense beyond the logical point in section
  2 — seven exact certificates plus one open case is not a fraction of
  a proof, it is seven proofs and one open problem.
- Does not extend any confidence about this project's own verified
  move-alphabet exhaustiveness to whatever "`B1`-`B6`" denotes this
  round — that term is undefined in any file this session can reach.
- No search run, no Codex file touched.

CLAUDE_TOP8_7_OF_8_ANALYSIS_READY
