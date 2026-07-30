# Round 39 retention audit — Round 34 Target-B flow

## Exact flow result retained

Round 34's `FlowSearch` constructs initial candidates directly from the
exact boundary state. Its `true_phase_walk_capacity` table is read only to
sort the seven models; the `FlowSearch` transition relation does not call it.
The seven model roots were selected by the retained coarse, port-count, and
B+R filters.

Round 39 independently replayed all 18 boundaries and reran the engine-level
macro DFS from every coarse survivor using only:

```text
macro.macro_edges
macro.area_a_prune_reason(..., AREA_A)
Round-32 B+R capacity bound recomputed from ExactState
```

No phase-walk helper or serialized capacity field is used. The result is:

```text
9  COARSE_CAPACITY_IMPOSSIBLE
9  EXHAUSTED_NO_PATH
```

All seven historical flow roots are among the latter nine and re-exhaust.
The same independent run also closes the two P-core=4 states that historical
metadata discussed through phase capacity; each is already closed by B+R.

## What is corrected

`build_rr_segment_successors.py` stores helper-derived
`initial_capacity_max` and profile metadata. Those profile statistics are
not used by the replacement proof and must not be cited as a capacity
certificate until reconstructed with a full-segment-only theorem.

The old Area-A-only bounded runs stay `INCOMPLETE`; they remain diagnostics,
not proof. The exact B+R engine DFS results are retained exactly.
