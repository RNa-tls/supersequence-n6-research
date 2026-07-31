# Round 40 corrected short-root pilot

**Result:** bounded validation run, `INCOMPLETE`; this is not an exhaustion
claim.

## Retirement and version firewall

The pre-correction worker was retired only after a normal atomic checkpoint.
It was PID `21612`, searched `short_ell0`, began at
`2026-07-31T13:54:47.9542571+09:00`, and its final snapshot had 580,000
expansions, 74 frontier states, and no serialized R event. It is preserved,
readable, and marked through the immutable sidecar
[`outputs/rr_short5_worker_retirement.json`](../outputs/rr_short5_worker_retirement.json)
as `PRE_R_V1_INVALID_FOR_FULL_SEARCH`; it must never be resumed.

The corrected traversal uses only:

```text
outputs/checkpoints/rr_short5/r1_complete_v2/
```

Its config binds the root universe
`round37-short5-bare-abandonment-r1-complete-v2` and its payload binds
`rr-target-a-exhaustive-checkpoint-v2-short-r1`. A v1 payload under the v2
config is a hard schema failure, independently of the changed engine hash.

## Deterministic pilot selection

The five roots tied on all three numerical criteria:

| root | legal successors | depth-1 frontier estimate | resource margin | R1 edge |
|---|---:|---:|---:|---|
| `short_ell0`–`short_ell4` | 4 | 4 | 14 | `rot^5;w3:120` |

Stable root-id order therefore selects `short_ell0`.

## Run

The validation pilot used node limit 250 and checkpoint interval 25. Its
positive cap is deliberate, so `INCOMPLETE` is the required result class.

| telemetry | value |
|---|---:|
| expanded nodes | 250 |
| final frontier | 84 |
| pre-R nodes | 5 |
| R1 transitions enqueued | 4 |
| post-R1 nodes expanded | 245 |
| unique decorated R1 keys | 319 |
| maximum post-R1 depth | 72 |
| R2 candidate edges | 136 |
| Target-A hits | 0 |
| stored R1 states in final frontier | 74 |

The one-node seed checkpoint stored one R1 child. Its R event replayed as

```text
macro_index=1, kind=R,
source=(E-orbit 33, phase 0), target=(E-orbit 120, phase 3).
```

Reloading that v2 checkpoint under exactly the same config preserved the
serialized R1 decoration and frontier byte-for-byte at the semantic level.
No v1 checkpoint was consumed. The independent verifier replayed every
stored frontier trace, checked its R1 source/target, rejected any stored
`r_count > 1`, and passed with zero failures.

The pilot itself did not reach a hub-completion state (`CH1_nodes=CH2_nodes=0`)
within 250 expansions. This is reported as an observation, not as a branch
claim. The decoration update rule is separately controlled by a real stored
CH2 transition from `R27-prefix-6` and a same-index R-completion CH1 fixture.

## State-key stress control

The corrected depth-2 short-root audit generated 99 states, including 34
post-R1 states. Each was deliberately duplicated before successor-signature
comparison: 34 post-R1 duplicate groups, zero key/signature mismatches, and
zero JSON round-trip failures. The key retains ordered R events (including
source, target, and macro index), the first completer, and the remaining
chaining-relevant decoration.

## Scope

The pilot establishes only that the repaired traversal and checkpoint protocol
execute the formerly omitted R1 subspace correctly. It neither closes nor
reopens any short root, and it does not search a long root.
