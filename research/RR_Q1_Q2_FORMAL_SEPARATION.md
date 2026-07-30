# Q1 and Q2, formally separated: Target A abundance is not completion viability

Round 37, section 1. Source `src/verify_rr_q1_enumerator.py` →
`outputs/rr_q1_q2_prune_ledger.json`.

## 1. The predicates

```
Reach(r)   := ExactStates reachable from root r by legal RR-alphabet macro
              edges {Z2, Z3, R}, respecting the "at most 2 R events total"
              budget (손증명, Round 33/35: an RR word has exactly two R
              events).

TargetA(b) := b's generating edge is an R event, the SECOND R of the word,
              and the child state has F_def==1, H==0, and the R2
              source/target orbits share a component of the orbit/hexagon
              incidence forest built from the pre-joint state's
              orbit_masks.

Q1(r) := exists b in Reach(r): TargetA(b)
Q2(r) := exists b in Reach(r): TargetA(b) AND CompletionCompatible(b)
```

where `CompletionCompatible(b)` means `b`'s own capacity theorem
(`5*(O_cap+R_cap)+4 >= B+1`, or a refinement) does not already exclude it
from ever reaching a full Area-A completion.

## 2. Theorem: Q2(r) ⇒ Q1(r)

**Proof (손증명).** `Q2(r)` asserts the existence of a `b` satisfying a
conjunction, `TargetA(b) ∧ CompletionCompatible(b)`. Any witness for a
conjunction is a witness for each conjunct separately; in particular it
witnesses `TargetA(b)`, which is exactly `Q1(r)`'s existential claim. This
holds by the pure logical form of the two definitions — no engine
computation, no capacity arithmetic, no search is needed for this
direction.

## 3. The converse is false — an exact counterexample family, not one instance

**Claim.** There exist roots `r` with `Q1(r)` true and `Q2(r)` false.

**Witnesses.** All 28 of the 28 long-excursion Target A roots (the 6
Round-27 long-FOUND roots plus the 22 previously-incomplete ones):

* `Q1(r)` is **true**, demonstrated by direct exhibition: 1,398 literally
  replayed, independently re-confirmed Target A boundaries across 26 of
  the 28 roots (Round 36), plus — for the remaining 2 that found none
  within the search budget — a root-level proof of `Q1`-irrelevant but
  `Q2`-certifying fact (see below) that does not depend on finding a
  witness at all.
* `Q2(r)` is **false** for every one of the 28, established two
  independent ways: (a) empirically, 0 of the 1,398 exhibited boundaries
  pass even the coarsest capacity theorem
  (`outputs/rr_1398_boundary_capacity_ledger.json`); (b) structurally, the
  root-level envelope theorem
  (`RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md`) proves `Q2(r)` false for all 28
  directly from each root's own `(P, O, Ndef)`, without enumerating any
  boundary at all.

Grade: **exact counterexample family**, cross-verified by exhibition and by
an independent non-enumerative theorem — the strongest form available,
stronger than a single counterexample.

## 4. What this corrects

Round 35 named the Q1/Q2 distinction; Round 36 built infrastructure that
respects it (never using a Q2-only prune inside a Q1 search) but did not
yet have language for *why* the two questions diverge so sharply on this
corpus. This document supplies that: Q1 and Q2 diverge here specifically
because reaching *any* Target A boundary costs very little (the R-budget
argument alone bounds the minimum extension at exactly the number of
remaining R events, 1 or 2), while reaching a *completion-compatible* one
requires a resource margin that Round 37's conservation law shows can never
be assembled at these roots — a structural deficit, not a scarcity of raw
boundaries.

## 5. Scope note

This document does not claim Q1/Q2 diverge at *every* root in the universe
— only that a genuine, exactly-verified counterexample family exists. The
5 short-family roots (needing 2 R events) are NOT part of this
counterexample family: their `Q1` status is `INCOMPLETE_TIMEOUT` (unknown)
and their `Q2` status is likewise undetermined by the envelope theorem
(envelope = +14 > 0, inconclusive — see `RR_INCOMPLETE_ROOT_AUDIT.md`).
Nothing here claims `Q1`/`Q2` for those 5.
