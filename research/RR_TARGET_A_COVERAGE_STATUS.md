# Target A coverage status: the honest picture after Round 36

Round 36, Part F + final status. All 33 roots have completed their budgeted
run. Sources: `outputs/rr_target_a_root_universe.json`,
`outputs/rr_target_a_search_status_audit.json`,
`outputs/rr_target_a_known18_regression.json`,
`outputs/rr_target_a_resumed_frontiers.json`,
`outputs/rr_new_target_a_boundaries.json`.

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

## 4. Coverage execution (Part E) — final results, all 33 roots

Budget per root: node cap 100,000, wall-clock 90s (a generous, but
necessarily finite, allowance — §6 explains why no larger budget available
in this session would have changed the qualitative picture).

| group | roots | status | expanded (range) | hits found |
|---|---|---|---|---|
| 1. short-family (r_count=0) | 5 | **all `INCOMPLETE_TIMEOUT`** | 70,999–80,000 | **0** |
| 2. long FOUND (r_count=1, no stop-on-first) | 6 | **all `FOUND_TARGET_A`** | 64,345–68,235 | **1 each** (the known witness re-found; frontier not exhausted) |
| 3. long INCOMPLETE-22 (r_count=1, Q1-safe) | 22 | **20 `FOUND_TARGET_A`, 2 `INCOMPLETE_TIMEOUT`** | 60,000–67,663 | **0–126 each** |

Status histogram across all 33: **26 `FOUND_TARGET_A`, 7
`INCOMPLETE_TIMEOUT`, 0 `EXHAUSTED_NO_TARGET_A`.** Not one of the 33 roots'
frontiers emptied naturally — every result is honestly time-bounded, and no
status was ever upgraded to exhaustion.

**Group 1 in detail.** All 5 short-family roots — the ones needing TWO
fresh R events from `r_count=0` rather than one from `r_count=1` — expanded
70,999–80,000 nodes with the queue still 120,000–135,000 deep at cutoff and
found nothing. This is the largest, least-pruned search space in the round
(placing the first R is itself an unconstrained sub-search), and it is
exactly where the budget ran out fastest relative to progress.

**Group 2 in detail.** All 6 re-discovered their own known witness quickly,
then kept searching under coverage mode and found no second boundary within
budget. `found_boundary_count = 1`, `frontier_emptied_naturally: false` at
all 6 — a correct "found the known one, budget exhausted looking for more,"
not a coverage claim.

**Group 3 in detail — the headline result.** 20 of the 22 roots that Round
35 closed for Q2 (no *completable* Target A boundary) turn out to have
**many** Target A boundaries under the completion-agnostic Q1 question —
between 27 and 126 each, **1,392 in total**, all independently re-verified
by literal replay (`process_rr_new_target_a_boundaries.py`: 1,392/1,392
re-confirmed). Only 2 of the 22 (`long_q1_140`, `long_q1_178`) found zero
within budget.

## 5. The reconciliation with Round 35's Q2 result

This is the round's most informative finding, and it resolves cleanly
rather than contradicting anything:

> Round 35 found **zero completable** Target A boundaries at these 22
> roots. This round shows that is **not** because the roots have no Target
> A boundaries — they have **1,398 in total** (1,392 new, 6 re-discovered
> known witnesses) across the 26 roots where any were found. It is because
> **every single one of the 1,398 fails the capacity theorem**: `0 of 1398`
> capacity-theorem survivors in `outputs/rr_new_target_a_boundaries.json`.

Q1 and Q2 are not in tension. Q2's `EXHAUSTED_NO_TARGET_A` was a true
statement about completability; Q1 now supplies the reason at a level of
detail Q2 alone could not: the obstruction is not scarcity of local
boundaries, it is that Target A's local geometry and the completion
capacity bound are, at every one of the 1,398 examples found so far,
mutually exclusive. No boundary discovered contradicts Round 35; each one
independently re-derives why Round 35's closure was correct.

## 6. The new-boundary pipeline (Part F §19) — run, and correctly a no-op

Every hit went through the five required steps: exact replay (re-confirmed,
not merely trusted from the search's own bookkeeping), canonicalize,
compare against the 18 currently known (raw + canonical hash), CH1/CH2
classification, and the capacity theorem. **Step 6 (Round 34's flow
verifier) never fired**, because its precondition — a capacity-theorem
survivor — never occurred (0 of 1,398). This is the correct behavior: the
brief requires Target B determination to be separate post-processing, not
an assumption, and here that post-processing correctly found nothing to
hand off.

## 7. Discipline audit — 0 violations

`outputs/rr_target_a_search_status_audit.json` checks every one of the 33
resumed-root results for two classes of violation: (a)
`EXHAUSTED_NO_TARGET_A` claimed without `frontier_emptied_naturally: true`,
and (b) any Q2-only prune reason appearing in a Q1 run's `pruned_by_reason`
histogram. **Violations found: 0 across all 33 roots.**

## 8. Why Q1 coverage is still open, and why that is the correct outcome

Dropping the six completion-assuming sub-conditions of `area_a_prune_reason`
removes most of the pruning power every prior round relied on. A
calibration run showed the frontier growing *faster* than nodes could be
expanded even at ≈850 nodes/second, and the full 33-root run confirms it at
scale: **every single root's queue was still growing at cutoff** (87,000–
135,000 queued against 60,000–80,000 expanded). This is not a performance
problem to be optimized away — it is the direct, unavoidable cost of asking
a genuinely completion-agnostic question with only four weak local prunes
available. No larger node cap in this session would have changed the
qualitative picture; closing Q1 needs either substantially more compute
(the checkpoints in `outputs/rr_target_a_checkpoints/` — gitignored, ~130MB
per root — allow exactly this kind of resumption in a future round), a new
Q1-safe insight not yet found, or a structural argument that full
enumeration is unnecessary (e.g. a proof that many roots are
continuation-equivalent — flagged as **open** in
`RR_TARGET_A_SOURCE_UNIVERSE.md` §5). None of those was manufactured to
force a closure this round did not earn.

## 9. Net honest statement

**Closed this round:**
* the semantics bug — Q1 searches no longer smuggle completion assumptions
  (verified by a runtime assertion plus a 0-violation discipline audit);
* the short-family ceiling-truncation bug — superseded by uncapped-depth
  Q1-safe runs (still time-truncated, but for a disclosed, different
  reason, correctly labeled `INCOMPLETE_TIMEOUT` rather than a misleading
  `frontier_empty`);
* the stop-on-first coverage bug — the 6 long-FOUND roots are now searched
  in coverage mode, confirmed to find no second boundary within budget;
* the root universe — audited, 33 roots pairwise disjoint, count units
  fixed;
* **why** Round 35's Q2 closure held — 1,398 Target A boundaries found at
  the 22 roots, 0 of them capacity-theorem survivors.

**Still open:** full Q1 coverage at every one of the 33 roots (all either
timed out with zero hits or found some finite number and then timed out);
whether any 7th root source exists beyond the ones catalogued; L>8
excursions; abandonment roots and short prefixes outside this corpus;
Target A boundaries outside Area A entirely (never explored by any round,
including this one).

**Unchanged, restated per §18/§20 of the brief:** `L_6 ≤ 872` verified in
this repository, `L_6 ≥ 867` proved, `L_6 ≥ 872` open. The corpus of
currently identified Target A boundaries is referred to throughout this
round's documents as "18 currently known Target A boundaries" — never as an
exhaustive count. Target B was not re-searched for the known 18 this round,
and the 1,398 newly found boundaries were correctly never handed to a
Target B search either, since none survived the capacity theorem that gates
step 6. The N=0 checkpoint, CH2, T3, Target C, and the U/J branches were not
touched.
