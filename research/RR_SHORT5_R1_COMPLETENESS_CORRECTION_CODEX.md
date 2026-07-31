# Round 40 correction: short-root R1 traversal

**Status:** `CODEX_VERIFIED_COMPLETENESS_GAP`
**Scope:** the five bare Round-37 roots only.  This is not a revision of the
Round-37 long-root envelope or of the known Target-B ledger.

## Finding

The current checkout does not contain Claude analyst commit `0809693`, but the
reported behavior is independently reproduced in the actual Round-35 traversal
file, [`src/search_rr_target_a_exhaustive.py`](../src/search_rr_target_a_exhaustive.py).
Before this correction, its `evaluate_edge` sent **every** `R`-kind macro edge
to the R2 recognizer and returned a terminal classification.  It never enqueued
the child.

That policy is complete for a traversal which starts after `R1`, but not for a
bare short root.  Each of the five short roots has `r_count=0` and has a legal
first R edge (`rot^5;w3:120`).  Reaching a two-R Target-A boundary requires
first inserting the resulting `r_count=1` state into the traversal frontier.
The old code instead labelled that edge `r2_not_target`.

Thus any result, frontier statistic, or prune histogram obtained from the old
short-root driver describes the **pre-R subspace only**.  It is not an
exhaustion result for a short-root Target-A continuation.

## Independent checks

| Check | Result |
|---|---|
| Bare Round-37 roots | `short_ell0` through `short_ell4`, all `r_count=0` |
| Legal first R edge | present and accepted for all 5 roots after the correction |
| Corrected depth-2 key audit | 99 states: 65 at `r_count=0`, 34 at `r_count=1`; 0 key/signature mismatches |
| Long Round-35 root semantics | audited roots start at `r_count=1`; a legal next R is recognized on that edge and never enqueued |
| Regression tests | short R1 enqueue and long R2 terminal rules both pass |

The final pre-correction `short_ell0` checkpoint contains no serialized R
event (`74` frontier decorations with `r_events=[]`, after 580,000 expansions).
No checkpoint for `short_ell1` through `short_ell4` is present in this
checkout.  The worker was retired after its last periodic atomic checkpoint;
it remains an explicitly stale, pre-R-only computation and must not be resumed
as the corrected traversal.

## Correct rule

The R handling is now deliberately asymmetric:

```text
r_count before R = 0  -> create and enqueue its decorated R1 child
r_count before R = 1  -> test the prospective R2 Target-A boundary; do not enqueue it
r_count before R >= 2 -> reject
```

The short-root manifest and checkpoint namespace are versioned as `v2` and
`r1_complete_v2`.  Consequently a corrected search cannot accidentally resume
a pre-correction checkpoint: its checkpoint configuration includes both the
changed engine SHA-256 and a changed root-universe identifier.

## What remains valid

- The 28 long-root Q2 closure and the 18 known Target-B closures did not use
  the bare-short-root `r_count=0` entry condition; this correction does not
  modify them.
- The five short roots remain structural/resource survivors.
- Pre-R observations (for example, a pre-R `Phi` trajectory) may be retained
  only with that explicit scope label.

## What is withdrawn

No old short-root frontier statistic, terminal count, or absence of a found
boundary may be cited as an exact-search result.  A fresh R1-complete run and
independent replay are required before assigning any of the five roots
`FOUND_TARGET_A`, `EXHAUSTED_NO_TARGET_A`, or an informative `INCOMPLETE`.
