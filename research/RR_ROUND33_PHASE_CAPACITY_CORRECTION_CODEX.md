# Round 39 correction — Round 33 phase-walk capacity

## Correction

The function called `true_phase_walk_capacity` returned 2 at the recorded
`long_found_142` boundary, but the literal exact engine accepts these three
macro edges after that boundary:

```text
rot^0;w3:120
rot^3;w2:10
rot^4;w2:10
```

The third edge lands in a hexagon with mask `0b101111`; five positions are
occupied and the sixth is legal. Therefore that function is **not a sound
upper bound on arbitrary future legal macro-edge capacity**. The original
generic theorem wording and all proof uses that require that interpretation
are retracted.

The exact replay is machine-recorded in
`outputs/rr_round38_claim_provenance.json` and regression-tested.

## What survives

The following statements do not use the rejected helper and remain valid:

1. Round 30 coarse capacity: `B+1 <= 5(O_cap+R_cap)+4`.
2. Round 31 port-count refinement, based on `c(q)` as a count of unvisited
   port hexagons.
3. Round 32 B+R orbit-reuse penalty, whose re-entry contribution is at most
   four and whose budget is the exact `Ndef` arithmetic.
4. The full-block theorem under its stated full-segment/fresh-hexagon
   hypotheses.

The historical `18 -> 9 -> 8 -> 7` reduction is retained as
`coarse -> port count -> B+R`. It must not be described as depending on a
generic ordered phase-walk capacity of two.

## Correct status of the old table

The old seven-row table's numerical value `2` can still be an observation
about a **restricted full-segment initial option set**, but it is not a
generic capacity theorem. This audit does not reuse that observation to
prune any boundary. Its serialized output and successor-profile metadata
are historical/descriptive only pending a separately stated restricted
theorem.

Classification: **RETRACTION_REQUIRED** for the generic Round-33 theorem;
**RETAINED_BY_INDEPENDENT_ARGUMENT** for the coarse, port-count, B+R, and
full-block results above.
