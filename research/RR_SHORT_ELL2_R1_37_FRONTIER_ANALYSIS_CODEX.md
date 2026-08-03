# Round 54: `short_ell2_r1_37` v7 frontier analysis

Author: Codex
Status: **read-only structural audit complete; the global branch remains INCOMPLETE**

## Scope and provenance

This audit reads the immutable v7 endpoint checkpoint and does not resume or
modify it.  The source checkpoint is
`outputs/checkpoints/rr_short5/top2_continuation_v7/short_ell2/short_ell2_r1_37/checkpoint.json`
(4,884,573,885 bytes; independently verified SHA-256
`2847a6bd5861476428ec7cd9bd9d1d855229b33378662ebeef4ae4db832b1551`).

The checkpoint was not loaded as a five-GiB JSON object.  The analyzer:

1. extracted the 22-record frontier prefix;
2. streamed all 305,022 parent-DAG records to recover parent indices;
3. streamed the DAG a second time to retain only the 65 nodes in the union of
   the 22 ancestry paths; and
4. literally replayed those paths from the immutable v5 R1 anchor.

Every replayed exact-state hash, decoration, and stored frontier state matched.
Each exported frontier record contains the exact state hash, conservative
decorated key, parent replay hashes, complete incidence forest, component
partition, legal edge ledger, and future R2 candidates.

## Exact frontier ledger

| Quantity | Count |
|---|---:|
| Stored frontier records | 22 |
| Exact decorated states | 22 |
| Proved left-(S_6) canonical classes | 22 |
| Resource-profile classes | 18 |
| Successor-signature classes | 22 |
| Component-geometry profile classes | 19 |

Thus there is no exact-state or proved-symmetry compression of this frontier.
Three pairs share a component-geometry profile and four pairs share a resource
profile, but none share the full successor signature.  These weaker profiles
are **not** continuation equivalences and must not be used for pruning.

Depths range from 47 to 88.  Legal traversable/terminal successor counts are:

| Successors | States |
|---:|---:|
| 0 | 5 |
| 1 | 9 |
| 2 | 5 |
| 3 | 3 |

The five zero-successor records are pending DFS frontier records, not prior
exhaustion claims.  The read-only local replay establishes their dead-end
status.

## Common geometry

The following are finite observations on all 22 exact states:

* (F=1), (H=0), (N_{def}=1), and (Phi=0);
* the hub mask is `63` in every state, so the hub is complete;
* the R1-target component is distinct from the hub component in every state;
* the incidence-component count equals (O-1) in every state;
* nine immediate R2 candidates exist, and all nine fail exactly the
  `same_component` predicate; and
* no immediate Target A boundary occurs.

This identifies the present barrier precisely: the missing event is not hub
completion or R2 geometry in general, but a legal pre-R2 merge of the
R1-target and hub components.

## Exact local bridge audit

For each frontier state, an exact, unquotiented breadth-first replay was run to
depth three using only Target-A-safe legal children.  R2 is recognized as a
terminal event and is not traversed.

* Nine frontier roots have a completely exhausted reachable subgraph within
  this audit, with no component bridge.
* The other thirteen have no bridge in their exact first three macro steps.
  Their bridge distance is therefore at least four, but it is not declared
  infinite.
* Across all 22 local audits, 144 distinct exact decorated states were
  examined and no bridge was found.

The nine locally closed roots are:

```text
short_ell2_r1_37:304862  short_ell2_r1_37:304864
short_ell2_r1_37:304869  short_ell2_r1_37:304871
short_ell2_r1_37:304971  short_ell2_r1_37:305011
short_ell2_r1_37:305012  short_ell2_r1_37:305014
short_ell2_r1_37:305016
```

This is a finite complete result for those nine local subgraphs.  It is not an
exhaustion certificate for `short_ell2_r1_37` as a whole.

## Recurrence and ranking audit

No exact decorated state recurs on any of the 22 replayed ancestry paths.  A
reduced phase-context signature recurs 124 times on 18 paths, with separations
from 2 to 34 macro edges.  This signature forgets global occupancy, so these
are phase-pattern repetitions rather than state cycles.

The hub mask is repeated trivially (`63` for all states), while component
geometry has 19 profiles and exact successor behavior has 22 profiles.  Hence
the frontier is not a single periodic phase cycle.

There is one rigorous ranking quantity: every one of the 64 distinct replayed
parent edges adds exactly six previously unvisited windows.  Consequently
(720-\text{visited}) decreases strictly by six.  This proves finiteness of a
literal branch but gives no useful short upper bound on its remaining depth.

(P,O,S,N_{def},\Phi), and hub popcount were nondecreasing on the replayed
paths.  (D) and (M=P-5O) were not monotone.  These observations do not yet
yield an obstruction potential.

There is also no monotone collision-saturation pattern.  At the frontier the
mean exact-collision count is 13.18 out of 24 raw candidates and the mean legal
successor count is 1.27, but both quantities fluctuate over the preceding ten
ancestry layers.

## Candidate lemmas and exact gaps

### Separation-invariant candidate — **conjecture**

> In the `short_ell2_r1_37` Target-A-safe reachable universe, the R1-target
> component never merges with the hub component before R2.

Support: all 421,221 nodes in the previously verified v7 replay were B0; all
22 endpoints are separated; and the exact next-three-step neighborhoods have
no bridge.  Gap: legal Z2/Z3 insertions have not been closed for every future
occupancy mask.  A counterexample is one legal post-R1/pre-R2 Z2 or Z3 child
whose two marked components are distinct before and equal afterward.

### Immediate same-component gate — **finite complete check only**

All nine R2 candidates available at the 22 endpoints fail only
`same_component`.  This says nothing about R2 candidates appearing after a
longer continuation.

### Nine local exhaustion certificates — **finite complete check**

The nine roots listed above have fully explored local reachable subgraphs with
no bridge.  This is data-level closure, not yet a shared hand theorem.

## Continuation strategy comparison

| Strategy | Assessment |
|---|---|
| A. Continue all 22 equally | Complete in principle, but spends work on nine already locally closed roots and ignores observed structural diversity. |
| B. Smallest-successor first | Cheap, but can over-sample one geometry and has no proof-preserving dominance justification. |
| C. Prove one common obstruction now | Highest proof value, but the current data do not close all future Z2/Z3 component insertions. |
| D. Split into structural subfamilies | Best immediate choice, provided profiles select experiments but never merge/prune exact states. |

Recommendation: **D, followed by A if needed**.  A first batch should use one
exact representative from each observed `(successor signature, component
geometry)` profile among the thirteen unresolved roots, with equal independent
caps of 25,000 expansions.  The proposed eight-state batch is:

```text
short_ell2_r1_37:304973  short_ell2_r1_37:304860
short_ell2_r1_37:304858  short_ell2_r1_37:303323
short_ell2_r1_37:236166  short_ell2_r1_37:304872
short_ell2_r1_37:303324  short_ell2_r1_37:12
```

Each state must use a fresh branch-local checkpoint keyed by the immutable v7
checkpoint SHA, exact state hash, and parent replay hash.  Caps remain
`INCOMPLETE`; only an empty frontier is exhaustion.  If these representatives
do not exhaust, all thirteen unresolved roots should receive equal work.  No
continuation was started in this round.

## Artifacts

* `outputs/rr_short_ell2_r1_37_frontier.json`: the complete 22-state export.
* `outputs/rr_short_ell2_r1_37_frontier_classes.json`: canonical/profile,
  recurrence, ranking, and candidate-lemma audit.
* `outputs/rr_short_ell2_r1_37_next_plan.json`: nonexecuted continuation plan.
* `src/analyze_rr_short_ell2_r1_37_frontier.py`: reproducible streaming
  analyzer.

No absence result beyond the nine explicitly closed local subgraphs is claimed.
