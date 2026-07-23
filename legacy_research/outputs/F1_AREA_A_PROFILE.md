# F=1 Area A macro-depth profile

## Scope and status

This is a **bounded macro-depth experiment**, not an enumeration of Area A.
The exact target is

\[
F=1,\qquad H=0,\qquad N\le3,\qquad(P,O,D)=(121,25,4).
\]

The macro keeps the full exact state and compresses only a consecutive literal
rotation run before a `w2`/`w3` joint.  Every run length is retained, so this
does not impose a full-pass normal form.

| macro depth | completed | canonical states seen | remaining frontier | generated macro edges |
|---:|:---:|---:|---:|---:|
| 1 | yes | 25 | 0 | 24 |
| 2 | yes | 197 | 0 | 600 |
| 3 | yes | 1,184 | 0 | 4,728 |
| 4 | yes | 6,109 | 0 | 28,236 |
| 5 | yes | 28,618 | 0 | 145,372 |
| 6 | **no** — 20,000-node cap | 85,340 | 65,340 | 476,248 |

The depth-6 checkpoint is intact and the search stopped by its deliberately
configured node cap; it did **not** advance to depth 7.  Its state growth is
therefore evidence that unrestricted Area A should not be started yet, not a
claim of nonexistence.

## Pruning interpretation

Only the rules catalogued in
[`PARTIAL_F1_AREA_A_PRUNES.md`](../PARTIAL_F1_AREA_A_PRUNES.md) were applied:
literal window collision, monotone resource bounds, exact final-`D`
arithmetic, and necessary cover/opening capacities.  No `C_4/C_3` clean
cassette rule, empirical repair-saturation rule, or fragment-type statistic
was used for pruning.

## Memory instrumentation note

The current macro profile JSON records zero for its internal Windows
working-set field.  That is an instrumentation defect, **not** a zero-memory
claim.  Independent read-only process snapshots during depth 6 observed a
checkpoint-serialization peak of 801,996,800 bytes and normal working sets
in the 0.35–0.46 GiB range.  This profile remains useful for state/transition
growth, but a later macro revision must repair the internal peak-memory field
before it is used for capacity planning.

## Next calculation

The smaller monotone subcase

\[
F=1,\quad H=0,\quad N=0
\]

was chosen from the previous bounded comparison and has been started only
after this profile process exited.  It is checkpointable with no node limit.
Until its result file says `completed: true` and the read-only literal replay
verifier passes, it is an in-progress finite computation rather than a
closed subcase.

Machine-readable details, including checkpoint hashes and prune counts, are
in [`f1_area_a_profile.json`](f1_area_a_profile.json).
