# Length-871 one-path exclusion

Every length-871 necessary arithmetic row with **d=0** is now excluded in
the unconditional fixed-first-occurrence framework. This includes positive
Z and heavy cost, not merely the earlier `Z=H=0` domain. The complete
length-871 exclusion remains open: 61 necessary arithmetic rows with d>0
survive these bounds. Thus the unconditional interval is still 871..872.

## Necessary model and certified pruning

The hand proof is `RR_ROUND143_ONE_PATH_SUFFIX_AUDIT_CODEX.md`. After the
c pure E circuits are removed, d=0 gives exactly one beta path. Its ports
are distinct; its resources obey exact A, exact Qs, repeated-hex arrivals
at most A+Z, heavy cost at most H, b=B*, D=5k-G, and P=120+G-5c.
Every shortest full-pass connector of weight 2 through min(6,H+3) is
retained. Hidden chronological obligations are relaxed, never strengthened.

At a chosen non-E boundary, the suffix bound uses aggregate D+5b, not the
nonmonotone current D. It consumes boundary A/B/heavy/repeat and old-orbit
charges exactly once, clears prefix exclusions for its upper relaxation,
then maximizes over every allowed retained-A allocation. Two independent
resource-allocation algorithms agree on 488 cells producing 2,837 bounds.
Missing cells are infinity. No finite maximum is inferred from a cap.

One C implementation advances whole E-runs and constructs literal tails;
the other advances individual ports and derives geometry from all 518,400
literal overlap comparisons. Both preserve full port and hex occupancy.
The independent Python short-path oracle agrees with both in 10 complete
small controls, including A/B, repeated hexes, heavy weights 4/5/6, a
zero-resource case, cap handling, and overwrite refusal. Bound-on and
bound-off exported path sets agree in the controls. These tests supplement,
not replace, the hand inclusion proof.

## Complete exact-P decisions

The 121 previously unresolved d=0 arithmetic rows map to 90 distinct
(A,Qs,R,H,b,D,P) necessary queries. Four initial pilot queries had a
5,000,000-node cap but all naturally exhausted far below it. The other
86 used node_cap=0. Every query is complete in both implementations.

- 89 queries have no exact-P path.
- One query `(0,0,0,1,0,8,92)` has exactly one rooted path.
- The two complete export sets agree in every query.

The surviving path has P=92, O=20, D=8, b=0, one heavy-cost unit, and no
A/B or repeated-hex arrival. It occurs in the k=3,G=c=7 row. Seven removed
pure E circuits would have to cover all 28 remaining hexagons using closed
orbits. The independent static exact-cover recurrence completely exhausts
this instance in 151 nodes and returns UNSAT. It rechecks its known-SAT
and small brute-force controls before accepting the exclusion.

## Current necessary arithmetic ledger

| Length-871 classification | Rows |
|---|---:|
| Strict scalar/endpoint capacity exclusion | 874 |
| Sigma-deficit obstruction | 339 |
| Earlier exact-P empty model | 152 |
| Earlier all-prefix static exclusion | 1 |
| New generic one-path empty model | 120 |
| New all-prefix static exclusion | 1 |
| Equality, unresolved | 12 |
| Capacity above requirement, unresolved | 49 |
| Total | 1548 |

These rows are arithmetic possibilities, not literal isomorphism classes.
The remaining d>0 cases must retain their nonpure-cycle closing geometry;
the one-path theorem is not applied to them.

## Replayable sources

- `rr_round143_general_prefix_pilot_codex.json` and its JSONL directory.
- `rr_round143_general_prefix_complete_codex.json` and its JSONL directory.
- `rr_round143_general_suffix_v1.json/.txt`: hashed bound inputs.
- `rr_round143_general_paired_small_codex.json`: independent short oracle.
- `rr_round143_generic_query_ledger_codex.json`: all decisions and static check.
- `verify_round143_general_query_ledger_codex.py`: replays both export sets,
  checks hashes and exact domains, and reruns the finite static completion.

All actual query runs use frozen source commit
`12a8e0473ccaaadf1d7528f6466c366f906e290e`, previously pushed and checked
against the remote HEAD. Canonical LF source, runtime source, executable,
compiler, argv, cap/completion status, node count, time, transcript and
export hashes are recorded in their query artifacts. No chronological
full-cover DFS or old frontier reconstruction was run.
