# Component-change theorem status after Round 58

## Status ledger

| Level | Statement | Status |
|---|---|---|
| T1 | Existing depth-4 region is bridge-free | retained |
| T1+ | Larger bounded exact region is FZ1+-free | **proved by finite replay for the Stage-D region** |
| T2 | Complete finite closure of all six seeds eliminates first component-changing Z3 | not reached; two frontiers remain |
| T3 | `short_ell2_r1_37` cannot change its R1-target component before R2 | not proved |
| T4 | `short_ell2_r1_37` cannot produce a pre-R2 bridge | not proved |
| T5 | Exact component-changing Z3 witness | not found in verified region |
| T6 | Exact bridge witness | not found in verified region |

## What is proved

1. The exact start domain contains 84 states in six provenance-preserving seed
   families.
2. Four seed families are completely exhausted with empty frontiers and contain
   no FZ1+ event.
3. Across the entire verified Stage-D region, 1,256,023 expanded nodes generate
   800,516 accepted Z3 transitions, all independently classified as FZ0.
4. No literal Target A or Target B occurs in that region.
5. The direct-Z2 lemma remains applicable while the R1-target component is
   unchanged.

## What is not proved

The remaining seed families are:

```text
short_ell2_r1_37:6   frontier 34,712 at 425,000 expansions
short_ell2_r1_37:3   frontier 34,657 at 425,000 expansions
```

Their caps are not exhaustion certificates.  Consequently:

- zero observed FZ1+ does not imply branch-wide impossibility;
- the 31 M0 abstract dangerous-triple intersections do not constitute exact
  forward/backward matches;
- absence of an exact M3/M4 witness does not prove absence beyond the searched
  region;
- no invariant was inferred from frequency or frontier behavior.

## Correct research statement

> In the verified Stage-D exact region reachable from the 84 frozen
> `short_ell2_r1_37` frontier states, 800,516 legal Z3 transitions were replayed
> and none changed the R1-target component.  Four of six seed families are
> exactly exhausted; two retain a combined frontier of 69,369 states.

The only sound final classification is:

```text
FIRST_COMPONENT_Z3_SEARCH_INCOMPLETE
```

