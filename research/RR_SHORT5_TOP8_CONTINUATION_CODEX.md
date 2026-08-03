# Round 52 — completed top-8 continuation audit

## Scope and endpoint status

This is a finite audit of the eight preserved v6 branch-local checkpoints, not
an exhaustion of the top-8 problem. The v6 worker wrote its final index and
stdout record `{"additional": 167820, "children": 8, "status": "DONE"}`.
Its process exit code is not recoverable, so the OS termination cause remains
**UNKNOWN**. That does not alter the logical endpoint record in the atomic
payloads.

| endpoint | branches |
| --- | ---: |
| natural exhaustion (empty frontier) | 6 |
| 50,000-additional-expansion cap (nonempty frontier) | 2 |

The capped branches are `short_ell2_r1_70` (frontier 11) and
`short_ell2_r1_37` (frontier 19). Therefore the overall result is
**TOP8_CONTINUATION_INCOMPLETE**. The six empty-frontier results are exact
branch-local exhaustions; zero observations in capped branches are not
impossibility claims.

## Progress reconciliation

The eight v5 subroots contributed 40,000 expansions. Their v6 payloads total
207,820, hence the exact additional work is 167,820. The earlier 206,083
number was not an atomic eight-checkpoint sum and is superseded. The nominal
400,000 is the sum of caps, not a required completion count: natural
exhaustion legitimately stops a branch below cap.

| branch | total | additional | frontier | endpoint |
| --- | ---: | ---: | ---: | --- |
| `short_ell2_r1_70` | 55,000 | 50,000 | 11 | capped |
| `short_ell4_r1_12` | 40,457 | 35,457 | 0 | exhausted |
| `short_ell1_r1_98` | 5,461 | 461 | 0 | exhausted |
| `short_ell2_r1_40` | 5,697 | 697 | 0 | exhausted |
| `short_ell3_r1_64` | 27,737 | 22,737 | 0 | exhausted |
| `short_ell2_r1_37` | 55,000 | 50,000 | 19 | capped |
| `short_ell2_r1_107` | 5,731 | 731 | 0 | exhausted |
| `short_ell3_r1_56` | 12,737 | 7,737 | 0 | exhausted |

Every payload passes the production loader's read-only schema/config/root/R1
child/complete-frontier check. The v6 writer dropped its auxiliary
`top8_continuation` provenance object after its first atomic rewrite; the
original source-checkpoint SHA is instead verified against the immutable
Round-50 aggregate. This is a provenance serializer defect, not state
corruption; no v6 checkpoint was changed.

## Exact completed-corpus replay

`src/analyze_rr_short5_top8_completed.py` replayed every repair edge and R2
path from the literal parent DAG. At an R2 edge, the recognizer is called at
the typed literal joint source `edge.run.state`, never macro entry.

| object | count |
| --- | ---: |
| legal repairs replayed | 207,842 |
| literal R2 paths replayed | 99,438 |
| literal Target A hits | 0 |
| Target B survivors | 0 |

All eight R1 target orbits lie in a component distinct from the hub component
at admission. The R2 ledger contains 89,830 geometry failures and 9,608
not-same-component failures. The success hierarchy is `R0 = 89,830` and
`R2 = 9,608`; every stored path's strongest failure is
`repair_not_component_merging`. These are completed-corpus facts, not
theorems about unvisited continuations.

No literal Target A hit occurred, so no new Target-A boundary invoked
helper-free Target-B DFS in this round.

## Independent verification

`src/verify_rr_short5_top8_continuation.py` independently rereads the eight
atomic payloads and confirms endpoint, repair-type, component-merge,
hierarchy, Target-A, and count-conservation ledgers. It passed with the same
207,842 repair and 99,438 R2 counts.

Artifacts:

- `outputs/rr_short5_top8_interruption_audit.json`
- `outputs/rr_short5_top8_continuation_analysis.json`
- `outputs/rr_short5_top8_registration_events.json`
- `outputs/rr_short5_top8_success_hierarchy.json`
- `outputs/rr_short5_top8_continuation_verified.json`
