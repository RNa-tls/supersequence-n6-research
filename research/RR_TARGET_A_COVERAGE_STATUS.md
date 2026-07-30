# Target A coverage status: the honest picture after Round 36

> **Status of this document at commit time: the group-3 (22-root) coverage
> execution is still running in the background** (long-running, one root at
> a time, its own independent budget per §18). This document, and
> `outputs/rr_target_a_resumed_frontiers.json` /
> `outputs/rr_new_target_a_boundaries.json`, are committed as an honest
> **partial snapshot** and will be updated with final tallies once the
> execution completes. Every number below is labeled with how many of the
> 33 roots it reflects at snapshot time. Nothing here is a final coverage
> claim.

Round 36, Part F + final status. Sources: `outputs/rr_target_a_root_universe.json`,
`outputs/rr_target_a_search_status_audit.json`,
`outputs/rr_target_a_known18_regression.json`,
`outputs/rr_target_a_resumed_frontiers.json`.

## 1. What changed from Round 35

Round 35 built the Q1/Q2 distinction but its "Q1" search still used the
bundled `area_a_prune_reason` as a traversal prune, which silently carried
six completion-assuming sub-conditions into every intermediate-state check
(`RR_TARGET_A_Q1_Q2_SEPARATION.md`). Round 35's `EXHAUSTED_NO_TARGET_A`
claims were for **Q2** (completability) and were correctly labeled so; its
Q1 runs were reported `INCOMPLETE`, which remains accurate, but the *reason*
they were incomplete (branching ≈2.5 with no strong prune available) was
not yet distinguished from "genuinely searched with the right prune set and
ran out of budget" versus "used a smuggled-in completion assumption that
happened not to fire." This round removes that ambiguity by re-implementing
the prune set from scratch (`q1_safe_prune_reason`) and asserting, in code,
that no Q2-only reason can ever appear in a Q1 run's histogram.

## 2. Root universe (Part A) — now audited, not assumed

33 exact-state roots across 3 source groups (5 short-family, 6 long-FOUND,
22 long-INCOMPLETE), confirmed pairwise disjoint at the exact-state and
canonical levels (`RR_TARGET_A_SOURCE_UNIVERSE.md`). The abandonment ℓ
range {0,1,2,3,4} is now an exhaustively checked fact, not an inherited
assumption.

## 3. The known-18 regression (Part D §14) — 18/18 pass

Every one of the **18 currently known Target A boundaries** replays
literally against this round's independently re-implemented recognizer.
Two bugs were caught and fixed while building this regression, both worth
recording because they illustrate exactly the kind of unit confusion this
round exists to prevent:

1. A first replay attempt called `macro.macro_edges()` on a state that had
   already been advanced by the literal rotation count, double-applying the
   final rotation. Fixed by mirroring the pattern already established (and
   already verified 7/7 against the engine) in
   `build_rr_target_b_exact_cover.py::replay_state`: a direct `extend()`
   call for the R2 joint, not a fresh macro-edge rotation run.
2. `P_core = preparation_length − 2` — asserted as "the established
   convention" in earlier drafts of this round's own documents — turned out
   to hold **only for the ℓ=0 branch**. For ℓ=4 the correct offset is
   `preparation_length − 1`, because the ℓ=4 branch's R2 edge is a bare
   `ℓ=0` joint while the ℓ=0 branch's is a full `ℓ=5` rotation run. The
   regression script does not use either offset formula: it looks up each
   replayed boundary's authoritative `P_core` directly in
   `rr_target_b_survivors.json` by `(root_ell, raw_hash)`.

With both fixed: **18/18 literal replays succeed**, and cross-referencing
against `rr_target_b_survivors.json` and `rr_flow_certificates.json`
reproduces exactly the expected split — the 7 boundaries that survived to
Round 34 all show Target B status `EXHAUSTED_NO_PATH` (independently
verified UNSAT), and the other 11 are correctly identified as removed
earlier by the capacity theorem (Rounds 30-32).

## 4. Coverage execution (Part E) — results

Budgets: node cap 100,000, wall-clock 90s per root (a generous, but
necessarily finite, allowance — see §6 below on why no larger budget would
have changed the qualitative picture).

**Group 1 — short-family roots (5, r_count=0).** All 5 timed out:
`INCOMPLETE_TIMEOUT`, 70,999–80,000 nodes expanded each, **zero new hits**,
frontier still growing at the cutoff (120,000–135,000 queued against
70,000–80,000 expanded).

**Group 2 — long FOUND roots (6, r_count=1), re-run without
`--stop-on-first`.** All 6 re-discovered their known witness quickly (as
expected — that witness is genuinely close to the root) and then continued
searching under the coverage-mode budget: all 6 report `FOUND_TARGET_A`
with `found_boundary_count = 1` and `frontier_emptied_naturally: false` —
found the one known boundary, ran out of budget looking for more, and
correctly did **not** claim exhaustion. No 2nd boundary was found at any of
the 6 within budget; whether one exists beyond the searched frontier is
open.

**Group 3 — the 22 long INCOMPLETE roots, Q1-safe enumerator.** In
progress at snapshot time (3 of 22 done: `long_q1_0`, `long_q1_1`,
`long_q1_2`). All 3 completed so far report `FOUND_TARGET_A` with
`frontier_emptied_naturally: false` (budget-limited, not exhausted) —
**78, 67, and 46 new Target A boundaries respectively**, all independently
re-verified by literal replay (`process_rr_new_target_a_boundaries.py`).

**A finding worth stating even from this partial data, because it
reconciles cleanly with Round 35's Q2 result.** These 22 roots were the
ones Round 35 found `EXHAUSTED_NO_TARGET_A` for the completability question
Q2 — zero *completable* boundaries. This round's Q1 search shows that is
**not** because these roots have no Target A boundaries at all: they have
many (191 new ones found in the first 3 roots alone, against the 18
previously known). It is because **every single one found so far fails the
capacity theorem** (0 of 197 total hits collected at snapshot time survive
it — see `outputs/rr_new_target_a_boundaries.json`). Q1 and Q2 are not in
tension; Q1 is explaining *why* Q2 closed the way it did, at a level of
detail Q2 alone could not provide.

## 5. Discipline audit

`outputs/rr_target_a_search_status_audit.json` checks every resumed-root
result for two classes of violation: (a) `EXHAUSTED_NO_TARGET_A` claimed
without `frontier_emptied_naturally: true`, and (b) any Q2-only prune
reason appearing in a Q1 run's `pruned_by_reason` histogram.
**Violations found: 0.**

## 6. Why the honest answer to Q1 is still "open," and why that is the
correct outcome for this round

Dropping the six completion-assuming sub-conditions of `area_a_prune_reason`
removes most of the pruning power every prior round relied on. A
calibration run showed the frontier growing *faster* than nodes could be
expanded even at a strong 850 nodes/second — this is not a performance
problem to be optimized away, it is the direct, unavoidable cost of asking
a genuinely completion-agnostic question. No node cap this round would
change that; the search needs either dramatically more compute, a new
Q1-safe insight not yet found, or an argument that the search does not need
to be exhaustive in this form at all (e.g. a structural reason many roots
are equivalent — see the `open` items in `RR_TARGET_A_SOURCE_UNIVERSE.md`
§5). None of those was manufactured to force a closure this round did not
earn.

## 7. Net honest statement

**Closed this round:** the semantics bug (Q1 searches no longer smuggle
completion assumptions), the short-family ceiling-truncation bug (superseded
by uncapped-depth Q1-safe runs, even though those runs are themselves
time-truncated for a different, disclosed reason), the stop-on-first
coverage bug (the 6 long-FOUND roots are now searched in coverage mode), and
the root universe (audited, disjoint, count units fixed).

**Still open:** Q1 coverage at every one of the 33 roots (all either timed
out or found their one known hit and then timed out); whether any 7th root
source exists beyond the ones catalogued; L>8 excursions; abandonment roots
and short prefixes outside this corpus; Target A boundaries outside Area A
entirely (never explored by any round, including this one).

**Unchanged, restated per §18/§20 of the brief:** `L_6 ≤ 872` verified in
this repository, `L_6 ≥ 867` proved, `L_6 ≥ 872` open. The corpus of
currently identified Target A boundaries is referred to throughout this
round's documents as "18 currently known Target A boundaries" — never as an
exhaustive count. Target B was not re-searched for the known 18 this round.
The N=0 checkpoint, CH2, T3, Target C, and the U/J branches were not
touched.
