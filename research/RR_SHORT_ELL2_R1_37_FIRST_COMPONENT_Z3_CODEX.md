# Round 58: `short_ell2_r1_37` first component-changing Z3 search

Author: Codex  
Status: **verified bounded exact search; incomplete branch-wide**  
Final search stage: **D**

## Purpose and scope

Round 57 reduced every abstract dangerous bridge entry to a necessary earlier
event: a legal Z3 transition must first change the component containing the R1
target orbit.  This round searched for exactly that event.  It did not broaden
to another short root or to the remaining 439-child corpus.

The frozen starting domain consists of the six surviving all-13 seed families,
with 84 literal frontier records.  There are 84 exact decorated start states,
84 proved left-`S6` classes, and 84 component signatures.  No resource-profile,
component-geometry, or abstract-triple quotient was used.

## Exact event

For a post-R1/pre-R2 accepted macro transition, the search classifies:

- `FZ0`: legal Z3, but the R1-target component is unchanged;
- `FZ1`: its node set strictly enlarges without touching the hub component;
- `FZ2`: it enlarges into a component with a later exact Z2 hub route;
- `FZ3`: it directly merges with the hub component;
- `FZ4`: after FZ1/FZ2, a later Z2 reaches the hub component;
- `FZ5`: literal Target A after the first change;
- `FZ6`: helper-free Target B survivor.

The first accepted `FZ1`, `FZ2`, or `FZ3` on a path is
`FIRST_COMPONENT_CHANGING_Z3`.  Before and after components are recomputed from
the literal exact state.  No earlier change is allowed in a first-event path.

## Search design

The search uses complete exact successor generation under the existing
Target-A-safe profile.  The priority queue favors one-step component-change
candidates, legal Z3s, dangerous abstract triples, and smaller branching, but
priority is ordering only.  It never prunes a state.

No new component-change prune was introduced.  In particular, none of the
unproved separation, registration, or phase heuristics was used as a prune.
Checkpoints are independent per seed, atomic, and stored only under:

```text
outputs/checkpoints/rr_short5/r1_37_first_component_z3_v1/
```

The cumulative per-seed budgets were:

| Stage | Added to each still-live seed | Cumulative target |
|---|---:|---:|
| A | 25,000 | 25,000 |
| B | 50,000 | 75,000 |
| C | 100,000 | 175,000 |
| D | 250,000 | 425,000 |

Natural exhaustion permanently stops a seed.  There was no budget transfer.
Stage E was optional and was not run: after Stage D the two live families each
still had about 34.7k frontier states, while another million expansions plus a
full independent replay would materially exceed this verified round's budget.
This is a reported hard stop, not an impossibility certificate.

## Exact Stage-D ledger

| Seed | Expansions | Unique decorated digests | Final frontier | Max depth | Status | FZ1+ |
|---|---:|---:|---:|---:|---|---:|
| `short_ell2_r1_37:236166` | 3,158 | 3,157 | 0 | 97 | exact exhaustion | 0 |
| `short_ell2_r1_37:12` | 170,773 | 170,235 | 0 | 105 | exact exhaustion | 0 |
| `short_ell2_r1_37:6` | 425,000 | 456,838 | 34,712 | 102 | capped / incomplete | 0 |
| `short_ell2_r1_37:3` | 425,000 | 457,123 | 34,657 | 101 | capped / incomplete | 0 |
| `short_ell2_r1_37:303321` | 5,964 | 5,918 | 0 | 105 | exact exhaustion | 0 |
| `short_ell2_r1_37:13` | 226,128 | 225,602 | 0 | 103 | exact exhaustion | 0 |

Totals and count units:

- start states: **84**;
- expansions: **1,256,023**;
- parent-DAG nodes, retaining provenance multiplicity: **1,325,392**;
- per-seed unique decorated-digest sum: **1,318,873**;
- global unique exact/decorated hashes: **1,318,577**;
- accepted transitions: **1,325,308**;
- accepted Z2: **524,792**;
- accepted Z3: **800,516**;
- R2 candidates: **632,886**;
- remaining frontier: **69,369**.

Every accepted Z3 in this verified region is `FZ0`:

```text
FZ0 = 800,516
FZ1 = FZ2 = FZ3 = FZ4 = FZ5 = FZ6 = 0
Target A = 0
Target B = 0
```

Four families are exact empty-frontier exhaustions.  The two nonempty capped
families remain open.

## Forward/backward meet-in-the-middle

Round 57 provides 196 dangerous transition identities over 176 distinct
preceding triples: 174 class R3 and 22 class R4, with no R5 witness.  In the
Stage-D forward graph:

- M0 abstract triple intersection: **31 distinct triples**, **55,254 forward
  occurrences**;
- M1 certified coarse structural matches: **0**;
- M2 certified exact decorated-state matches: **0**;
- M3 exact predecessor chain to first component-changing Z3: **0**;
- M4 exact bridge witness: **0**.

The M1/M2 zeroes are witness counts, not nonintersection theorems.  The Round-57
backward rows serialize abstract triples and predecessor conditions, not exact
component partitions or decorated-state digests.  Therefore only M0 is actually
decidable from the two frozen artifacts.  No abstract match was promoted to an
exact match.

## Structural observations, not theorems

- The R1-target component is unchanged across all 800,516 accepted Z3
  transitions in the verified Stage-D region.
- The naturally exhausted cohort comprises four seeds, 406,023 expansions and
  232,646 accepted Z3 transitions.
- The capped cohort comprises two seeds, 850,000 expansions, 567,870 accepted
  Z3 transitions, and 69,369 remaining frontier states.
- Frontier size is not monotone: the long narrow seed families show both
  collapse and regrowth before either exhaustion or cap.

These facts are bounded observations.  They do not prove a monotone invariant
or a branch-wide obstruction.

## Independent verification

The independent verifier rebuilt the frozen manifest, replayed every parent-DAG
node, regenerated every raw candidate at every expanded node, checked the
Target-A-safe verdicts, independently recomputed the component-change class,
and compared the complete R2 multiset and frontier.

Verified totals:

```text
nodes replayed                 1,325,392
expanded nodes replayed        1,256,023
frontier replayed                 69,369
accepted transitions checked   1,325,308
Z3 transitions checked           800,516
R2 candidates checked            632,886
first-change witnesses                  0
```

The verifier passed.  No SAT/CSP model was used, because the exact Stage-D
search produced neither a witness nor a complete closure; a bounded UNSAT model
would not improve the exact theorem level without a separate suffix-completeness
argument.

## Exact conclusion

This round establishes a much larger verified bridge-free/component-change-free
region than depth 4, and exactly closes four of the six surviving seed families.
It does **not** close `short_ell2_r1_37`: two exact frontiers remain nonempty.

Final theorem level: **T1+**.

