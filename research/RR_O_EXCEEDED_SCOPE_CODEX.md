# `O_exceeded` is not a Target-A prune

## Exact code meaning

In `legacy_research/work/superperm_partial_f1_macro.py`, the test is exactly

```python
if state.O > TARGET_O:  # TARGET_O == 25
    return "O_exceeded"
```

Here `O` is the number of opened E-orbits.  The exact transition engine does
not regard `O>25` as illegal: it is an upper-budget condition only for the
Area-A terminal target, where `O=25` is demanded.

## Scope proof

The Target-A predicate is: R2, child `F_def=1`, child `H=0`, and same
incidence component for the R2 source and target E-orbits.  Its definition
contains no assertion `O<=25`.  Hence no proof can infer a Target-A prefix
contradiction merely from `O>25` unless an additional theorem proves every
Target-A witness completion-compatible.  No such theorem is present; the
documented hierarchy is only `Q2 => Q1`, not its converse.

Therefore `O_exceeded` is:

* not a global exact-legality violation;
* a monotone obstruction to an Area-A/Target-B completion with final `O=25`;
* forbidden in a semantic Target-A traversal;
* permitted in the legacy Area-A/Q2 comparison profile.

## Exact differential witness

`outputs/rr_short_ell0_prune_differential.json` contains a literal replay
from `short_ell0` to the first O-only divergence.  The resulting exact child
has `O=26` and passes the Target-A registry.  The same literal edge is legal
under `ExactState.extend`; only the legacy completion bundle drops it.

This is labeled `EXACT_COUNTEREXAMPLE` to the claimed **prune safety**.  It is
not a Target-A witness and it does not establish a full nonrepeat completion.

## Consequence

The earlier v2 100,250-expansion result must be reported as
`PREMATURELY_PRUNED_INVALID_FOR_TARGET_A_COVERAGE`.  Its checkpoint is
historical and is blocked by the v3 checkpoint schema.  Any future Target-A
search starts fresh from a v3 semantic checkpoint; Area-A/Q2 predicates may
only enter after an R2 boundary is recognized and labelled for downstream
Target-B analysis.
