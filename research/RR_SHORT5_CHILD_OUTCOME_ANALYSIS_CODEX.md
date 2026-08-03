# Round 51 - v5 child-outcome analysis

## Scope

This is a read-only analysis of the completed Round-50 bounded pilot.  It did
not resume a checkpoint or run any deeper continuation.  Every statement about
natural exhaustion is scoped to the stored v5 Target-A-safe transition system;
every statement about capped children remains observational.

## Exact ledger

- exact decorated R1 children: 439
- naturally exhausted: 326
- capped with nonempty frontier: 113
- aggregate expansions: 596537
- left-S6 canonical child classes: 439
- mixed exhausted/capped canonical classes: 0

The full child ledger is `outputs/rr_short5_child_outcomes.json`.  It records
the literal R1 trace, replayed exact decorated state, left-S6 class, branch
outcome, checkpoint provenance, exact resource coordinate, component
projection, immediate legal successor profile, and branch-level failure
counts.

## Exhausted versus capped comparison

No causal inference is made from the feature buckets.  The comparison covers
R1 orbit/phase, event order, hub/completer timing, incidence components,
resource coordinates, immediate branching, and explored depth.  The precise
buckets are machine-readable in the child ledger.

At the coarser level, neither completion timing nor local branching supplies a
general exclusion:

- event-order buckets: `{"'CH1'": {"CAPPED_INCOMPLETE": 4}, "'PRE_R_COMPLETER_EVENT_ORDER'": {"CAPPED_INCOMPLETE": 100, "NATURALLY_EXHAUSTED": 326}, "'UNDECIDED'": {"CAPPED_INCOMPLETE": 9}}`
- completer-timing buckets: `{"'BY_R1_COMPLETER'": {"CAPPED_INCOMPLETE": 4}, "'NO_COMPLETER_AT_R1'": {"CAPPED_INCOMPLETE": 9}, "'PRE_R_COMPLETER'": {"CAPPED_INCOMPLETE": 100, "NATURALLY_EXHAUSTED": 326}}`
- immediate-successor buckets: `{"0": {"NATURALLY_EXHAUSTED": 107}, "1": {"CAPPED_INCOMPLETE": 35, "NATURALLY_EXHAUSTED": 118}, "2": {"CAPPED_INCOMPLETE": 48, "NATURALLY_EXHAUSTED": 77}, "3": {"CAPPED_INCOMPLETE": 30, "NATURALLY_EXHAUSTED": 24}}`

The first two have mixed pre-R-completer outcomes.  In particular, they cannot
be used as safe prunes.  Zero immediate successors is the only local condition
in this analysis that directly proves immediate exhaustion; it accounts for
107 children.

## Candidate theorem status

- **Proved:** zero accepted immediate successors implies immediate natural
  exhaustion, directly from the exact transition definition.
- **Not established:** R1 orbit/phase alone determines exhaustion.  The
  required occupancy and decoration information is not removable on current
  evidence.
- **Finite-corpus observation only:** outcome purity/mixing by left-S6 class
  is tabulated.  Here the left-S6 action gives no compression: all 439 exact
  decorated child states lie in distinct canonical classes.
- **Refuted candidates:** pre-R completion and hub-popcount 6 each occur in
  both the naturally exhausted and capped populations, so neither may be used
  as a safe shortcut.

## Recommended next batch

The priority list is in `outputs/rr_short5_capped_priority.json`.  It selects
the first eight capped children lexicographically by smallest saved frontier,
greatest reached depth, Target-A-candidate count, class multiplicity, and
checkpoint size.  This is a scheduling heuristic only, not a dominance rule.

| rank | child | saved frontier | maximum depth | Target-A candidates | checkpoint bytes |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `short_ell2_r1_70` | 7 | 104 | 2461 | 73024676 |
| 2 | `short_ell4_r1_12` | 8 | 102 | 2293 | 69067168 |
| 3 | `short_ell1_r1_98` | 8 | 97 | 2152 | 62668235 |
| 4 | `short_ell2_r1_40` | 9 | 101 | 2466 | 70106532 |
| 5 | `short_ell3_r1_64` | 10 | 100 | 2389 | 66431184 |
| 6 | `short_ell2_r1_37` | 13 | 101 | 2459 | 81843109 |
| 7 | `short_ell2_r1_107` | 13 | 101 | 2379 | 66720682 |
| 8 | `short_ell3_r1_56` | 13 | 96 | 2304 | 65394099 |

## Provenance

- source result SHA-256: `858bf5dadf79985a4658158a732c95f1e7349e23882bee073bc03d4b6dcff115`
- analysis script SHA-256: `0619d62192cd8539b6a1a868bc6f259fac9ea12e32a03acb08830a776fdb1aac`
- v5 driver SHA-256: `bc93957c39bd601a712f4bf3ca377f33273325b39e5a03c7bebc9babe1c6bd2a`
- exact engine SHA-256: `5388bf46a0eb1d56223193c35c842cf19a7a6d6bba7b1b1ade11e785d427d649`
