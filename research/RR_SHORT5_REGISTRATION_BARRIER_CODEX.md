# Round 52 — component-bridge and registration-barrier audit

## Exact bridge template

For a post-R1 repair edge `e`, the analyser checks this literal predicate at
the predecessor and exact post-edge state:

1. `e` has kind `Z2` or `Z3_fresh`.
2. `e` is after R1 and before an R2 is taken.
3. Its target hexagon lies in the hub component before the edge, but is not
   the hub hexagon itself.
4. The R1-target orbit component and hub component are distinct before the
   edge and equal after it.

Both component partitions are recomputed from the exact state. Stored
metadata is not used as a substitute for this replay.

## Completed-corpus result

Across all 207,842 legal repair events in the eight v6 branches:

| quantity | count |
| --- | ---: |
| invalid repair kinds | 0 |
| Z2 repairs | 85,451 |
| fresh-Z3 repairs | 122,391 |
| any incidence component merge | 0 |
| target hex in hub component | 0 |
| R1-target/hub merge | 0 |
| full bridge-template matches | 0 |

There are no bridge witnesses to export. The registration-event output holds a
complete replay count plus the empty list of every event meeting any
bridge/registration precondition; the full raw event corpus remains in the
immutable branch checkpoints rather than being cloned into a second
multi-gigabyte artifact.

The R2 hierarchy nevertheless reaches level `R2` 9,608 times: a literal
future R2 source orbit can be present in the incidence forest without being in
the R1-target/hub component. Thus source registration is weaker than the
component-bridge requirement.

## Scope boundary

This is a **finite complete verification of the recorded v6 corpus**. It is
not a proof that no future continuation can bridge the components, because two
branch frontiers stopped at their 50,000-additional-expansion cap. It also does
not prove a universal symbolic family across roots.

`future_R2_source_before` is intentionally undefined until an R2 edge is
chosen. Filling it with macro-entry or a pre-repair candidate would recreate
the literal-source error corrected in the prior round.
