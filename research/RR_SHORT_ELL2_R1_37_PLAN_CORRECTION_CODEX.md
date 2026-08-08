# Round 55: `short_ell2_r1_37` plan correction and Round-53 ledger reconciliation

Author: Codex

Status: **plan corrected; all 13 unresolved states covered; no continuation executed**

## 1. Correction to Round 54 Strategy D

The Round-54 eight-state list was described too strongly.  Independent
reproduction shows:

* the 13 unresolved states have 13 distinct compound
  `(successor signature, component geometry)` profiles;
* the eight-state loop therefore performs no profile deduplication;
* the eight states are merely the first eight under the deterministic ordering
  `(fewest legal successors, greater depth, stable state id)`;
* five unresolved states are omitted;
* the eight states cover only 7 of the 18 resource profiles and 7 of the 19
  component geometries in the full 22-state frontier.

Accordingly, those eight states are now called **priority-selected states**.
They are not profile, quotient, or equivalence-class representatives.  No
continuation equivalence is proved.  The Round-54 report remains historical;
this document and `rr_short_ell2_r1_37_all13_pilot_plan.json` supersede only
its proposed continuation plan.

Within the 13 unresolved states there are 11 resource profiles and 11
component-geometry profiles, but all 13 exact successor/geometry compound
profiles are distinct.  These weaker profile coincidences still do not permit
state merging or pruning.

## 2. Round-53 node-count reconciliation

The two original v7 checkpoint `nodes` arrays were streamed directly.  Node
IDs were checked for sequentiality and `parent_id=null` was counted from the
raw records.  The original bridge ledger was then checked against every
parent-nonnull record.

| Branch | Parent-DAG nodes | Parent-null roots | Parent-nonnull paths | B0 paths | Frontier |
|---|---:|---:|---:|---:|---:|
| `short_ell2_r1_70` | 116,199 | 1 | 116,198 | 116,198 | 0 |
| `short_ell2_r1_37` | 305,022 | 1 | 305,021 | 305,021 | 22 |
| **Total** | **421,221** | **2** | **421,219** | **421,219** | **22** |

The discrepancy is therefore exact and benign:

```text
421,221 parent-DAG state vertices
-     2 parent-null branch roots
=421,219 accepted incoming paths classified B0--B6
```

All 421,219 classified paths are B0; B1--B6 are zero.  B0--B6 classifies an
accepted incoming parent-DAG edge/path, not the root state vertex.  The two
root records have no incoming edge and are the only node records outside that
classification.

The 22 frontier vertices are nonroot vertices.  Their incoming edges are
already included in the 305,021 B0 paths for `r1_37`; they are not excluded
records.  Separately,

```text
421,199 expanded records + 22 frontier records = 421,221 node records.
```

The 421,219 repair-event rows and 204,685 R2-attempt rows are auxiliary event
and candidate ledgers.  They are not additional parent-DAG state vertices and
do not add rows to the B0--B6 denominator.

The raw artifacts are local, untracked large-computation outputs.  Their exact
paths and SHA-256 values are recorded in
`outputs/rr_round53_node_count_reconciliation.json`, including both checkpoint
hashes, the raw result, bridge ledger, final continuation ledger, and
independent verifier output.

## 3. Complete all-13 pilot

The corrected baseline gives every unresolved exact state its own independent
10,000-additional-expansion cap.  There is no budget transfer.  Natural
exhaustion stops a branch early; a nonempty frontier at the cap is
`INCOMPLETE`.

All states have (F=1), (H=0), (N_{def}=1), and (Phi=0).  `C` below is
the incidence-component count.  The JSON ledger contains full resource-class
and component-geometry hashes, marked hub/R1 components, exact macro endpoint
coordinates, state hashes, and parent-replay hashes.

| Priority | State | Succ. | Depth | (P,O,D,C) | Immediate legal moves | Cap |
|---:|---|---:|---:|---|---|---:|
| 1 | `:304973` | 1 | 77 | 79,32,81,31 | `rot^5;w2:10` | 10,000 |
| 2 | `:304860` | 1 | 67 | 69,28,71,27 | `rot^5;w2:10` | 10,000 |
| 3 | `:304858` | 1 | 66 | 68,28,72,27 | `rot^5;w3:201` | 10,000 |
| 4 | `:303323` | 1 | 59 | 61,23,54,22 | `rot^5;w2:10` | 10,000 |
| 5 | `:236166` | 1 | 56 | 58,22,52,21 | `rot^5;w2:10` | 10,000 |
| 6 | `:304872` | 2 | 74 | 76,30,74,29 | `w2:10`, `w3:201` | 10,000 |
| 7 | `:303324` | 2 | 59 | 61,23,54,22 | `w3:201`, `w3:210` | 10,000 |
| 8 | `:12` | 2 | 52 | 54,19,41,18 | `w2:10`, `w3:210` | 10,000 |
| 9 | `:6` | 2 | 48 | 50,17,35,16 | `w3:201`, `w3:210` | 10,000 |
| 10 | `:3` | 2 | 47 | 49,17,36,16 | `w2:10`, `w3:210` | 10,000 |
| 11 | `:305018` | 3 | 88 | 90,36,90,35 | `w2:10`, `w3:201`, `w3:210` | 10,000 |
| 12 | `:303321` | 3 | 58 | 60,23,55,22 | `w2:10`, `w3:201`, `w3:210` | 10,000 |
| 13 | `:13` | 3 | 52 | 54,19,41,18 | `w2:10`, `w3:201`, `w3:210` | 10,000 |

The `short_ell2_r1_37:` prefix is omitted in the State column only for
readability.  Priority affects scheduling order only.  It conveys no
dominance or equivalence.

## 4. Runtime and disk estimate

The estimate uses actual v7 invocation data:

| Empirical branch | Additional expansions | Seconds | Expansions/s | Checkpoint bytes/node |
|---|---:|---:|---:|---:|
| `r1_70` | 61,199 | 1,320.907 | 46.33 | 14,271.5 |
| `r1_37` | 250,000 | 8,806.375 | 28.39 | 16,013.8 |

For at most 130,000 additional expansions:

* sequential runtime range: approximately **46.8--76.4 minutes**;
* combined-rate point estimate: **70.5 minutes**;
* checkpoint growth: approximately **142.7--160.2 MB per state**, or
  **1.86--2.09 GB total**.

These disk estimates require fresh single-root subcheckpoints.  The immutable
4.88-GB v7 parent DAG must be referenced by checkpoint SHA, exact state hash,
and parent replay hash, not copied thirteen times.  Round-53 memory telemetry
recorded zero due the known instrumentation defect, so no unsupported peak
memory estimate is asserted.

## 5. Checkpoint and verification plan

Proposed namespace:

```text
outputs/checkpoints/rr_short5/r1_37_all13_v8/<state_id>/checkpoint.json
```

Each subcheckpoint starts from one literally replayed frontier state and
stores:

* immutable v7 checkpoint SHA;
* exact state and decorated-key hashes;
* parent replay hash;
* engine, driver, schema, and configuration hashes;
* exact bridge and B0--B6 instrumentation; and
* literal R2-source semantics.

Use atomic writes every 1,000 expansions and at natural exhaustion/cap.  Each
branch is independently verified.  Empty frontier is required for exhaustion;
otherwise the result is `INCOMPLETE`.  No continuation was started in this
round.

## Deliverables

* `outputs/rr_short_ell2_r1_37_all13_pilot_plan.json`
* `outputs/rr_round53_node_count_reconciliation.json`

The corrected plan covers all thirteen unresolved exact states without
claiming any unproved quotient.
