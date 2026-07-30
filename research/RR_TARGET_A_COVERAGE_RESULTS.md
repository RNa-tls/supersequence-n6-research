# Round 35 Target-A coverage results

## Audited universe

The Round-35 search universe has exactly 22 **raw** audited long-prefix roots
from `outputs/rr_target_a_22_root_ledger.json`.  The handoff audit established
that all 22 are singleton under the currently safe exact and canonical
comparisons.  They are deliberately not merged by any unproved continuation
equivalence.

The old capped Round-27 reproduction over this same root unit is:

```text
FOUND = 6
INCOMPLETE = 22
EXHAUSTED_IMPOSSIBLE = 0
```

Those old incomplete statuses motivate the new root-local traversal; they are
not proof results.

## Current Round-35 result

Only `R27-prefix-6` has been run with the new implementation, under an
intentional cap of 8,000 expansions.  It ended `INCOMPLETE` with a nonempty
frontier and zero Target-A boundaries.  The independent verifier passed the
bounded manifest.  The other 21 roots have not been searched by this program.

| Root cohort | Root count | Round-35 status | Interpretation |
| --- | ---: | --- | --- |
| `R27-prefix-6` | 1 | `INCOMPLETE` | bounded, independently replayed pilot |
| all remaining audited roots | 21 | not run | open |
| all audited roots together | 22 | open | no aggregate conclusion |

## Explicit gaps outside this traversal

Even a completed all-22 run would cover only its audited long-prefix scope.
The currently uncovered/reported-separately classes include first returns of
length greater than 8, long-prefix paths outside the recorded root generator,
short-prefix roots, other abandonment-root families, capped historical
frontiers, and any root-generation path not present in the Round-27 corpus.
Some `ell=0` entries occur inside the audited long-prefix ledger; that does
not mean all possible `ell=0` root classes are covered.

Thus this file never calls RR, NR6, or the n=6 length lower bound closed.
