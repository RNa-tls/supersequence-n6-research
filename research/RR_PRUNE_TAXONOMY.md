# Prune taxonomy: predicate, monotonicity, Q1/Q2 safety, minimal counterexample

Round 37, section 2. Source `src/verify_rr_q1_enumerator.py::section2_prune_ledger`
→ `outputs/rr_q1_q2_prune_ledger.json`.

This restates Round 36's `PRUNE_CLASSIFICATION` as a single ledger, adding
what Round 36 established but did not tabulate in one place: for every
Q2-only reason, the exact minimal counterexample that proves it unsafe for
Q1.

## The ten sub-conditions of `area_a_prune_reason`

| condition | monotone | Q1-safe | Q2-only | completion assumption needed |
|---|---|---|---|---|
| `F_exceeded` | yes | **✓** | | none — Target A's own definition requires child `F_def==1` |
| `H_positive` | yes | **✓** | | none — Target A's own definition requires child `H==0` |
| `N_exceeded_monotone` | yes | **✓** (Area-A scope) | | none intrinsically; `n_limit=3` is a disclosed scope choice |
| `F1_fragment_normal_form_impossible` | n/a (structural) | **✓** | | none — pure state-consistency check, no `TARGET_*` reference |
| `P_exceeded` | yes | | **✓** | `P <= TARGET_P=121` (full completion pass-start count) |
| `O_exceeded` | yes | | **✓** | `O <= TARGET_O=25` (full completion orbit count) |
| `final_D_impossible` | trajectory-invariant | | **✓** | reachability of `(TARGET_P, TARGET_D)` exactly |
| `remaining_pass_starts_exceed_remaining_windows` | yes | | **✓** | `TARGET_P` reachability given remaining windows |
| `remaining_cover_capacity_impossible` (Φ<0) | yes | | **✓** | the full Round 32/34/35 capacity bound |
| `insufficient_future_orbit_opening_credit` | yes | | **✓** | `TARGET_O`, `TARGET_P`, `TARGET_F` jointly |

## Minimal counterexample for the Q2-only family

**`remaining_cover_capacity_impossible`** (the Φ<0 test, i.e. the capacity
bound): replayed along a known short Target A boundary's own path, it goes
**negative strictly before the R2 edge** on the ell=0, `P_core=4` boundary
(one of the two such boundaries in the currently-known corpus). Using it as
a Q1 prune would delete a boundary that is independently confirmed to exist
(literal replay succeeds; the recognizer accepts it). This is the exact
finding from `outputs/rr_target_a_coverage_certificate.json` (Round 35,
check 1), re-cited here rather than re-derived.

**The other five Q2-only conditions** are all gated on the same three
completion targets (`TARGET_P`, `TARGET_O`, `TARGET_D`) that the capacity
bound uses. None of them appears anywhere in Target A's own definition
(`F_def==1`, `H==0`, same-component), so the same argument — a genuine
Target A boundary can exist at a state these conditions would reject —
applies to the whole family by the identical reasoning, not merely by
association. `outputs/rr_q1_q2_prune_ledger.json` records this explicitly
per-condition rather than asserting it once and hoping it generalizes.

## Why the four Q1-safe conditions are safe, restated with proof

* **`F_exceeded`, `H_positive`.** Both track quantities (`F`, `H`) that are
  *exactly* the quantities Target A's recognizer requires to equal a
  specific value (`1` and `0` respectively) at the boundary. Since both are
  monotone non-decreasing (`dF = int(abandonment) ∈ {0,1}`,
  `dH = max(weight-3,0) ≥ 0`), once either exceeds its target value it can
  never return — so pruning on that condition never discards a state that
  could still become a Target A boundary. This is not an approximation; it
  follows deductively from Target A's own definition.
* **`N_exceeded_monotone`.** `Ndef` is monotone (`dNdef = dS+dF-dO ∈
  {0,+1}` for every RR joint — the conservation law re-derived in
  `RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md` §7). `n_limit=3` is not part of
  Target A's definition; it is Area A's own scope boundary, inherited from
  every round since 27. Pruning on it restricts the search to a disclosed
  domain, not a false completeness claim.
* **`F1_fragment_normal_form_impossible`.** References no completion
  target at all; it is a structural sanity check on the *current* state's
  fragment geometry (its own docstring: "a necessary prefix invariant, not
  an unproved pruning heuristic").

## Static and dynamic enforcement

`q1_safe_prune_reason` is a **separate re-implementation** of these four
checks (not a filter applied to `area_a_prune_reason`'s output), so a
future edit to the bundled function cannot silently widen what Q1 uses.
Three independent checks confirm this (§17 of the brief, documented in
`RR_ENUMERATOR_CORRECTNESS.md`):

1. a static source-level allowlist scan (no Q2-only reason name or
   forbidden `TARGET_*` token appears in `q1_safe_prune_reason`'s source);
2. an exhaustive runtime assertion test (all 6 Q2-only reasons raise, all
   4 Q1-safe reasons pass);
3. an adversarial leakage test (a deliberately corrupted variant that
   re-introduces the capacity bound is caught immediately by the static
   assertion, and is shown to actually invoke the forbidden prune 55 times
   in a live run — proving the corruption engages, not merely that a check
   exists to catch it in principle).
