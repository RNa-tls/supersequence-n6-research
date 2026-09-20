# Round 171 — J is the frozen production target

This supersedes the **stop condition**, not the finite findings, in
JOINT_ENDPOINT_AUDIT_CODEX.md. The user explicitly corrected the requirement
that the historical d5/d7 pair appear in the active endpoint hypergraph.
Global Pareto optimality is an optional cost problem, not a soundness gate.

- PRODUCTION_VECTOR_J = SOUND (conditional sufficiency of proposed bounds).
- GLOBAL_PARETO_OPTIMUM = UNRESOLVED, not required for production.
- OPT=35 remains frozen in its established universe/rule system.
- All 8,192 endpoint evaluations and 62 rowwise hyperedges are immutable.
- The production dossier explicitly separates five GENUINELY_BACKED_VALUE
  cells from thirty PRODUCTION_TARGET_VALUE cells.
- The old individual dossier is SUPERSEDED_FOR_PRODUCTION_TARGETS, not false.

The audit commit feb1fa095fdf4d3e10a9af69241bb4fe9422e951 was pushed to
origin/codex/round171-joint-audit and ls-remote returned that exact SHA.

## Fresh pilot checkpoint

All 30 remaining cells were run serially at target J+1, cap 100,000, against
the same 129 genuine predecessor cells. All thirty exceeded the cap. There
were 3,000,030 attempted node visits (the engine tests its cap after increment,
so each aborted run reports 100,001). No bound is refuted; no helper is thereby
proved necessary. No historical capacity was used as a generation target.

This pilot budget is deliberately only initial triage. `first_useful_P1_prune_depth`
is actual ports-1 at the first visited state pruned using a strict dominator;
it is **not** the deficit-query coordinate that the historical pilot called
depth. Fallback fractions count actual ub calls, including cache hits, not
only distinct query keys. They are not directly comparable to old fractions.

The two d=0 special cells received the same small pilot only; no massive run
is scheduled for them.

## First family selection

Select b=1, B-budget=1, E=H=0, A+d=9:
`1|4|5|1|0|0`, `1|6|3|1|0|0`, `1|8|1|1|0|0`.

Rationale: a shallow d=2 helper at the componentwise A=5 shape can assist all
three; no higher-b re-entry budget is needed; the first target J=121 is not
an exact-capacity demand. This is the best next *measurable low-risk trial*,
not a proved globally optimal family ranking from capped data.

Measure each direct target at 2M visits, then attempt only one shared helper
`1|2|5|1|0|0`, with 1M discovery and 1M proof caps. Do not pre-build a ladder.
Only if it builds and passes both validators may it be used for investment
measurements. A small finished target batch will be dual replayed before any
progress count is increased. Timings are stored separately from proof content.

## Trust and boundaries

The frozen environment records artifact/container/plain hashes and verifier,
driver and generator source versions. Existing accepted objects are reused;
this is not a fresh full replay of all historical predecessors. Added r171
trust entries require A/B accepted per-batch reports, equal proof/histogram
counts and matching validator hashes. New target proofs get fresh A/B replay.
No generated but unverified object is made a predecessor.

## Measured outcome of the first investment

The three direct 2,000,000-node trials all reached their caps. Exact discovery
of `1|2|5|1|0|0` also reached its 1,000,000-node cap; no exact value was inferred.
A bounded upper-bound trial at d=2, bound 80, reached 200,000 nodes. A shallower
helper `1|1|5|1|0|0 <= 64` then completed with 122,892 proof nodes. Both independent
validators accepted it, with 122,892 histogram checks and no mismatch. This is
an upper bound, not a discovered exact maximum, and is not one of the 35 targets.

Using that accepted helper, all three selected targets again reached a smaller
200,000-node measurement cap (200,001 attempted visits each). The helper was
actually used 2,448 times on the first target, and zero times in the measured
prefixes of the other two. No family-wide speedup or amortization is established;
the unequal direct/invested caps cannot establish a total-cost comparison.
The investment files are completed measurements, not completed target proofs.

The regenerated progress ledger therefore remains **5/35 jointly usable**, with
30 targets remaining, one new auxiliary helper, and zero new load-bearing
certificates. Direct evaluation of J still closes 180 exposed rows, with 1,607
strict rows and two equality rows in the full census, without historical basis
fallback. This conditional sufficiency does not certify the missing bounds.

All seven production regression tests passed, including a synthetic genuinely
three-way forbidden interaction which cannot be certified by a pair graph.
No search remains active in this checkpoint. The next bounded investment, if
continued, should test whether the accepted shallow helper makes the d=2 upper
bound affordable before building any further helper ladder; none is launched
here. Node caps do not establish impossibility or helper necessity.

Checkpoint verdict: **ROUND171_J_PRODUCTION_BLOCKED** (production incomplete
at the measured budgets, not a mathematical obstruction).

Regression checks reject both singleton-only and pair-only projections of the
real endpoint evidence. A valid production vector still needs all thirty new
upper bounds proved: feasibility of J alone is not theorem completion.
