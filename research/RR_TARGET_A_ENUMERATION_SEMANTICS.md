# Target A enumeration semantics: status vocabulary and frontier accounting

Round 36, Parts B (sections 4-7). Source `src/search_rr_target_a_unified.py`.

## 0. Why this document exists

Round 35's `frontier_empty` flag is computed as `not cap_hit and
len(frontier) == 0` — **after** states at a depth ceiling are dropped
unexpanded. A search that drops 30,408 of 43,459 expanded states at the
ceiling and then finds an empty queue reports `frontier_empty: true`
identically to a search that genuinely exhausted every reachable state. The
flag cannot distinguish the two. That bug produced the largest coverage gap
identified last round (§17(b) of `RR_BRANCH_CLOSURE_SCOPE.md`), and it is
fixed here by replacing the single boolean with a status vocabulary that
makes every way a search can stop mutually exclusive and individually
named.

## 1. The status vocabulary (§4)

Exactly seven statuses, mutually exclusive:

| status | means |
|---|---|
| `FOUND_TARGET_A` | at least one Target A boundary was found (queue may or may not be empty — see §3) |
| `EXHAUSTED_NO_TARGET_A` | the queue emptied naturally, zero boundaries found |
| `INCOMPLETE_NODE_CAP` | the node budget ran out first |
| `INCOMPLETE_DEPTH_CEILING` | a depth ceiling dropped at least one state unexpanded |
| `INCOMPLETE_TIMEOUT` | the wall-clock budget ran out first |
| `STOPPED_AFTER_FIRST` | witness mode (`coverage=False`): search stopped at the first hit, by design, never used for a coverage claim |
| `INVALID_ROOT` | the supplied root failed to replay or reconstruct |

No other value is emitted. `EXHAUSTED_NO_TARGET_A` requires the queue to be
empty **and** zero states dropped at a depth ceiling **and** no cap hit
**and** no timeout **and** not a stop-on-first run — all five conditions,
not one flag standing in for all of them.

## 2. Frontier accounting (§5)

Every run records, regardless of outcome:

```
expanded_nodes            generated_nodes           queued_frontier_at_stop
pruned_by_reason (dict)   depth_ceiling_dropped_nodes   duplicate_state_merges
found_boundary_count      stop_reason               frontier_emptied_naturally
```

`pruned_by_reason` is a full histogram, not a total — every distinct prune
cause (including each Q1-safe reason from `PRUNE_CLASSIFICATION`, plus
`outside_RR_alphabet`, `r_count_exceeded`, `R_event_not_eligible_r_count`,
`different_components`, `source_or_target_orbit_not_in_forest`) is counted
separately, so a reader can see exactly what stopped a given branch without
re-running anything.

## 3. `FOUND_TARGET_A` does not imply exhaustion

A run can report `FOUND_TARGET_A` with `frontier_emptied_naturally: false`:
coverage mode keeps searching after a hit (it is not witness mode), but if
the node cap or timeout is reached with hits already recorded, the honest
status is still "found at least one" — downgrading it to an INCOMPLETE_*
status would hide a real result, and upgrading it to a coverage claim would
overstate one. Both `found_boundary_count` and `frontier_emptied_naturally`
are always present so a reader gets the true picture rather than a single
collapsed verdict.

## 4. Depth ceilings (§6) and stop-on-first (§7)

The Q1 (coverage) driver runs are launched with **no depth ceiling** —
`depth_cap=None`. If a depth ceiling is ever supplied for a run, its result
is unconditionally `INCOMPLETE_DEPTH_CEILING`, never folded into
`EXHAUSTED_NO_TARGET_A`; the enumerator enforces this in code (see
`enumerate_target_a`'s status derivation), not only in documentation.

`--stop-on-first` (the `coverage=False` path) exists for witness-finding —
producing one example quickly — and is architecturally incapable of
returning `EXHAUSTED_NO_TARGET_A`: the only statuses reachable from that
branch are `STOPPED_AFTER_FIRST` or an `INCOMPLETE_*`/`INVALID_ROOT` status.
No coverage-mode driver in this round ever sets `coverage=False`.

## 5. Determinism (§12)

`sorted_macro_edges` orders every macro edge by `(rotation length, joint
label)` before expansion, so two runs over the same root visit nodes in an
identical order regardless of process, platform, or dict-iteration order
elsewhere in the engine. Combined with the raw-dedup `seen` set (keyed on
the decorated key, §11), this makes `expanded_nodes`, `pruned_by_reason`,
and `found_boundary_count` exactly reproducible from one run to the next —
verified by re-running the same root twice and diffing the JSON output
(see `tests/test_rr_target_a_unified.py::test_determinism`).

## 6. Checkpoint / resume

Every `checkpoint_every` expansions (and once at the end of a run), the
current frontier, the seen-set hashes, the hit list, and the running stats
are written to a JSON file. `--resume` reconstructs `ExactState` objects
directly from their serialized `(p, hex_masks, orbit_masks, F, S, H)`
fields — not by replaying the literal path from the root — so resumption is
exact and does not re-derive anything. A resumed run's `expanded_nodes` and
`pruned_by_reason` continue accumulating from the checkpoint, not from
zero, so multi-invocation totals are truthful.
