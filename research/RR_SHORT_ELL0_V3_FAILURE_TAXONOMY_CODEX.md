# Round 43: `short_ell0` v3 R2 geometry-failure taxonomy

Status: **bounded deterministic replay only**.  This did not resume or modify the medium search checkpoint.

## Replay equivalence

- Frozen `785ddab` and instrumented engines expanded the same 100250 states.
- Expansion transcript hash equal: `True`.
- Serialized 85-state frontier equal: `True`.
- Seen decorated-key set equal: `True`.
- R1/R2/Target-A counters: `4` / `49440` / `0`.

## Opaque geometry exit refined

The historical parent count is 44021.  Its exact child partition follows.

| deterministic geometry child | count |
|---|---:|
| `no_completer` | 0 |
| `completer_wrong_target_orbit` | 0 |
| `completer_wrong_target_phase` | 0 |
| `r2_wrong_source_orbit` | 44021 |
| `r2_wrong_target_orbit` | 0 |
| `r2_wrong_ell` | 0 |
| `r2_wrong_joint` | 0 |
| `wrong_hub_residual_position` | 0 |
| `wrong_event_order` | 0 |
| `chaining_failure` | 0 |
| `terminal_boundary_mismatch` | 0 |
| `other_asserted_reason` | 0 |

The primary label is deterministic: a missing R2 source orbit takes priority if both endpoints are absent; the serialized secondary flags retain that overlap.  No catch-all geometry category is emitted: an unclassifiable old opaque exit raises an assertion.

The active Target-A geometry predicate is exactly the pre-R2 incidence-component relation.  The retained zero labels (`no_completer`, completer/event-order/chaining/hub/terminal labels, and `other_asserted_reason`) are explicit audit slots, not newly introduced Target-A rejection predicates.  The literal R2 records retain completer and event-order fields so a later separately specified normal form can be tested without re-running the prefix.

## Same-component rejection evidence

There are 5419 `not_same_component` rows.  Each exports the pre-R2 relation `component(q,R2.source) == component(q,R2.target)`, both component IDs/classes, and the counterfactual post-edge merge result.

## Frontier

The frontier export contains 85 states, not the 374 MiB checkpoint.  It has exact state/decorated keys, R1/completer history, coordinates, component summary, and independently recomputed next-edge labels.

## Scope

These are diagnostics for the fixed 100,250-expansion Target-A-safe prefix.  They neither exhaust `short_ell0` nor assert a Target-B or NR6 conclusion.
