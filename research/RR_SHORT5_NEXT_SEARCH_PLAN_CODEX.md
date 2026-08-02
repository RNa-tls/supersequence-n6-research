# Next corrected short-root search plan

## Decision

**Recommended next action: Strategy B, corrected fair pilots for the four
short roots other than `short_ell0`.**  Do not execute it as part of this
planning document.

The reason is evidential rather than merely computational.  The corrected
`short_ell0` prefix has already produced one literal Target-A class, which is
known-18 equivalent and Target-B closed.  Deeper work on that same root may
still discover new classes, but its marginal value is low until the other four
root universes have been entered under the corrected R1/literal-R2 semantics.

## Preconditions shared by either strategy

1. Never resume a v1, v2, v3, or v4 checkpoint directly.
2. Use the v5 namespace documented in
   `RR_SHORT_ELL0_CORRECTED_STATUS_CODEX.md`.
3. Rebuild or replay-validate every state with the literal-source recognizer
   version and the Target-A-safe prune registry in the config hash.
4. Keep R1 origins branch-local and allocate equal work only after every
   discovered R1 child has passed literal replay/key validation.
5. A positive cap is always `INCOMPLETE`; only a naturally empty frontier
   after an unlimited run may support `EXHAUSTED_NO_TARGET_A`.

## Strategy comparison

| Item | A. deepen four `short_ell0` R1 branches | B. corrected pilots for `short_ell1`–`short_ell4` |
|---|---|---|
| Immediate exact work | 25,000 additional expansions per existing R1 branch: 100,000 if all four receive one equal quantum. | First discover/validate R1 roots under a small fixed pilot (250 expansions per bare root; 1,000 total), then allocate equally per newly discovered R1 child. |
| Expansion estimate | The proposed first fair increment is exactly 100,000, not a forecast of exhaustion. | Discovery is exactly 1,000.  A later fair pass is `25,000 × number_of_valid_R1_children`; that number is measured during the pilot, not assumed. |
| Memory / checkpoint calibration | The historical 100,245-expansion v4 branch checkpoint is 127,829,078 bytes.  The corrected 4×25,000 run had a sampled external working-set high-water mark of about 3.72 GiB; this is calibration, not a guaranteed peak. | No defensible memory forecast exists before R1-child discovery.  The discovery pilot must record memory and checkpoint sizes.  Any post-R1 branch can then use the same conservative monitoring thresholds as A. |
| Output-volume calibration | Corrected hierarchy is 409,111,078 bytes; full witness corpus is 1,680,954,579 bytes.  Future runs should store compact evidence by default and materialize full witness corpora only for hits/R4+ cases. | Pilot output should be compact root/R1 telemetry only.  Full branch witness output is enabled only after a legal R1 child has been verified. |
| Chance of a new Target-A class | Unknown.  The existing observed prefix found one literal class, already known-18 equivalent; this is weak evidence of diminishing immediate return, not an exclusion. | Higher global value: it samples four untouched corrected root universes.  A new class would expand the official Target-B ledger rather than duplicate the same root. |
| Exhaustion prospect | One more 100,000-expansion increment cannot establish exhaustion. | Pilots cannot establish exhaustion.  They decide which root/R1 subroots justify a later exact continuation. |
| Contribution to global RR closure | Local only: improves coverage of one still-open root. | Broader: converts four structural survivors from unentered universes into corrected, audited root-local scopes. |

## Recommended staged protocol (not yet run)

### Stage B0 — corrected root admission

For `short_ell1` through `short_ell4`, run a 250-expansion Target-A-safe
pilot from the bare root.  Export legal R1 events, literal replay hashes,
source/target orbit-phase values, decoration/key audit, and frontier
distribution.  A cap means `INCOMPLETE` even if no R1 occurs.

### Stage B1 — fair post-R1 branches

Freeze every discovered R1 child.  If the state-key audit includes its
post-R1 states without mismatch, allocate the same positive budget to each
child *within a root*.  Preserve branch-local v5 checkpoints and separate
pre-R/post-R1 telemetry.

### Stage B2 — boundary closure

For each literal Target-A hit: exact parent-DAG replay, proven left-`S_6`
canonicalization, comparison against known-18, helper-free coarse Target-B
test, and helper-free exact macro DFS for any class that survives the coarse
test.  Do not use `true_phase_walk_capacity` outside its proven
full-segment scope.

Only after B0/B1 results are available should A be reprioritized.  If B
discovers no valid R1 children in a naturally exhausted run, that specific
root can be closed.  A capped absence has no such interpretation.

## Explicit non-actions

This plan does not run a search, mutate a checkpoint, declare short-root
exhaustion, reuse historical hierarchy labels, or make an NR6/lower-bound
claim.  Cost and calibration data are in
`outputs/rr_short5_next_search_costs.json`.
