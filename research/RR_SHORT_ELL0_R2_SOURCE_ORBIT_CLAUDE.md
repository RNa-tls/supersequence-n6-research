# `short_ell0` v3: why the R2 source orbit fails, and whether that's a theorem

Analyst pass over Codex's `codex/round43-short-ell0-taxonomy` branch. All
data below is read directly from committed files; no search was run, and
none of Codex's checkpoints or certificates were touched.

## 0. Remote commit verification

```
git fetch origin codex/round43-short-ell0-taxonomy
git log origin/codex/round43-short-ell0-taxonomy --oneline
  24002fd  Round 43 Codex: classify v3 R2 geometry failures
  785ddab  Round 42: run Target-A-safe short ell0 medium search
  d90b69a  Round 41: separate Target A prunes from Area A completion
  abfcdca  Round 40 Codex: run corrected ell0 medium continuation
  ...
```

**All three cited commits (`d90b69a`, `785ddab`, `24002fd`) are reachable.**
This supersedes, rather than contradicts, the last two rounds' "not
found" conclusions — those SHAs genuinely did not exist on any reachable
branch at the time; they exist now that the branch has actually been
pushed. Ten files were read from this branch: the six named in the first
message of this round plus `research/RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md`,
`research/RR_O_EXCEEDED_SCOPE_CODEX.md`,
`outputs/rr_short_ell0_medium_v3_verified.json`, and
`outputs/rr_short_ell0_v2_v3_differential.json` (the last one only for
the explicitly-labeled differential, per instruction).

**Independent verification passed on both checks already present in the
branch**, not just self-reported: `rr_short_ell0_medium_v3_verified.json`
(`verified: true`, `r1_event_failures: []`, `failures: []`) and
`rr_short_ell0_v3_taxonomy_verified.json` (`verified: true`,
`geometry_category_counts.r2_wrong_source_orbit: 44021`, all other
categories `0`). The replay-equivalence block inside the geometry-failure
ledger itself additionally confirms `same_expansion_sequence`,
`same_frontier`, `same_seen_key_set`, and `same_semantic_stats` are all
`true` between the frozen `785ddab` run and the `24002fd` instrumented
replay. **The stated "Main Codex result" is confirmed exactly**: 44,021
`r2_wrong_source_orbit` + 5,419 `not_same_component` + 0 everything else
= 49,440 R2 candidates, matching `R2 candidates: 49440` in both the
medium-run telemetry and the differential file.

## 1. The incidence-forest predicate, exactly

**`CLAUDE_OBSERVATION`**, read directly from `incidence_components`
(`src/search_rr_target_a_exhaustive.py` lines 324-344, unchanged from the
version audited two rounds ago):

```python
for orbit, mask in enumerate(state.orbit_masks):
    for phase in range(5):
        if mask & (1 << phase):
            port = core.ports_of_e_orbit(core.E_REPS[orbit])[phase]
            union(("q", orbit), ("h", core.hexagon_id(port)))
```

- **Vertices.** Two disjoint kinds: `("q", orbit_id)` for each E-orbit that
  has at least one set bit in `state.orbit_masks[orbit_id]`, and
  `("h", hexagon_id)` for each hexagon that is the target of at least one
  such registered port. An orbit with `orbit_masks[q] == 0` has **no**
  `q`-vertex at all — it is not "in a singleton component," it is simply
  absent from the graph.
- **Edges.** One union per **set bit** of `orbit_masks`: bit `phase` of
  orbit `q` being set creates the edge `("q", q) -- ("h", hexagon_id(port
  at that phase))`. A single orbit with `k` set bits contributes `k`
  edges (possibly to `k` different hexagons), all incident to the same
  `q`-vertex.
- **Distinguished hub/root.** The hub is `dec.hub_id` — the hexagon ID of
  the walk's own starting position, fixed per root (`hub_id=0` for
  `short_ell0`, confirmed in every exported record). It has no special
  status *inside* `incidence_components` itself (it is just another
  `h`-vertex); its distinguished role is entirely in `Decoration` (hub
  popcount, `hub_touch_count`, `completer`), a separate bookkeeping
  structure layered on top of the same `orbit_masks`.
- **Source-orbit membership computation.** For an R2 candidate edge,
  `sq, sph = exact.ORBIT_PHASE[pre_state.p]` — `pre_state` is the state
  *after* that candidate's own rotation run (0-5 literal rotations) but
  *before* its joint commits. `source_present = ("q", sq) in parent`,
  i.e., whether `orbit_masks[sq]` has ever had any bit set, checked fresh
  against `pre_state`'s own `orbit_masks` (not a cached history summary —
  `incidence_components` rebuilds the union-find from scratch every call).
- **Where Target A uses it.** The formal definition, restated exactly
  from `RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md`: *"Target A is an R2
  macro edge whose child has `F_def=1`, `H=0`, and whose R2 source and
  target E-orbits lie in the same component of the current orbit-hexagon
  incidence forest."* Membership of the source orbit is a **precondition**
  for even asking the same-component question — if the source orbit has
  no vertex, "same component as the target" is undefined, not merely
  false, and `geometry_failure_reason` reports it as its own category
  (`r2_wrong_source_orbit`) rather than folding it into
  `not_same_component`.

## 2. Transition laws, per legal macro-edge type

**`CLAUDE_OBSERVATION`**, derived from `extend()`
(`legacy_research/work/superperm_partial_f1.py`, confirmed byte-identical
across `abfcdca`→`24002fd` via `git diff`, so no re-verification of this
specific file was skipped) and `advance_decoration`
(`search_rr_target_a_exhaustive.py` lines 360-386):

| edge type | forest vertices | forest edges | component structure | R1-target ancestry | candidate R2 source orbit | hub attachment |
|---|---|---|---|---|---|---|
| pure rotation (`w=1`, any of the 0-5 literal steps inside a rotation run) | **unchanged** — `orbit_masks` is never touched by a `w=1` step | **unchanged** | **unchanged** | **unchanged** | **changes** — moves the walk's current position, hence `ORBIT_PHASE[pre.p]`, to a possibly different orbit, with no corresponding forest update | **unchanged** |
| `Z2` (orbit-preserving, weight 2) | unchanged (lands in the orbit the walk is already in, which by definition already has a vertex) | `+1` edge (the new phase's hexagon) unless that exact `(orbit, phase)` pair was already set (`om[q]&(1<<phase)` would raise `AssertionError` if reused — never happens by legality construction) | may merge two previously-separate components, if the new edge's hexagon was already in a different component | unaffected unless this Z2 lands in R1-target's own orbit | if this Z2 *is* the R2 candidate's joint (not applicable — Z2 cannot itself be tested as R2, only `R`-kind joints are) | `+1` to hub `touch_count` if the landing hexagon is the hub, and sets `completer` if not already set |
| `Z3` (fresh orbit, weight 3) | `+1` vertex (the new orbit) | `+1` edge (that orbit's first phase to its landing hexagon) | may attach a new solo component, or merge into an existing one if the landing hexagon is already registered elsewhere | unaffected unless this Z3 opens R1-target's orbit (impossible — R1-target is by definition already open) | not directly (Z3 is not R-kind) | same rule as `Z2` |
| `R` (re-entry into an existing orbit, weight 3) | unchanged (target orbit already has a vertex, by `R`'s own definition — `new_orbit=False`) | `+1` edge (the new phase) | may merge two components | this is exactly the R2 (or R1) event itself | **this is the event under test** | same rule as `Z2`/`Z3` |
| `Z2abandon` (root-only, weight 2, abandonment) | `+1` vertex (only ever fires once, at the literal root, opening the second orbit) | `+1` edge | trivial (first non-hub component created) | n/a (fires before R1 exists) | n/a | n/a (fires before hub can be touched by anything else) |

**Monotone quantities**: the vertex set, the edge set, and therefore (by
a standard union-find argument) the partition into components can only
**coarsen** — established already in a prior round from the `om[q] |=
1<<phase` OR-only assignment (re-confirmed here: this file is byte-
identical to the version that assignment was verified in). Consequently:
`P`, `O`, `Ndef`, hub popcount, and "orbit `q` has a forest vertex" are
all monotone non-decreasing/one-directional (once true, always true).

**Not monotone**: `M = P-5O` (rises `+1` per `Z2`/`R`, falls `-4` per
`Z3`); `Phi` (sawtooth — rises during literal rotation, drops by
`(ell-5)` at each joint; already established in a prior round); and, most
importantly for this analysis, **"is the R2 candidate's source orbit
registered" is not a property of a fixed orbit at all — it is a property
of an ephemeral, attempt-specific landing point** determined by however
many pure-rotation steps (0-5) happened to precede that specific R2 test.
The same walk position, if tested with a different rotation-run length,
would generally test a *different* candidate source orbit. This is the
single most important fact for §3.

## 3. Why 44,021 of 49,440 R2 candidates fail on the source orbit

**`CLAUDE_OBSERVATION`**, from `outputs/rr_short_ell0_v3_geometry_failures.json`'s
44,021 records (aggregated, no per-record content reproduced beyond
summary counts):

| fact | value |
|---|---|
| distinct `ell` (rotation-run length) values observed | **{5}** — all 44,021 have `ell=5` exactly |
| distinct `r1.source_orbit` values | **{1}** — all 44,021 descend from exactly one R1 event |
| distinct `event_order_class` values | **{`PRE_R_COMPLETER_EVENT_ORDER`}** — all 44,021 |
| distinct `completer` records | **1** — all share the identical `{kind: Z2, macro_index: 4, source_orbit: 96, target_orbit: 120}` |
| distinct source orbits (the orbit that failed to register) | **113** distinct values |
| depth range | 6 to 104 |
| `target_orbit_present_in_pre_r2_forest` | **always `True`** (`secondary_missing_endpoint_flags.target_missing: false` in all 44,021) |

**All 44,021 failures come from a single R1 event's subtree** — the one
whose R1 fired at `macro_index=5`, targeting orbit `0` (the hub), with a
hub completer that fired *earlier*, at `macro_index=4` (the
`PRE_R_COMPLETER_EVENT_ORDER` / provisional-`CH0` pattern already
identified two rounds ago). Cross-checking `outputs/rr_short_ell0_v3_component_failures.json`'s
5,419 records shows the identical signature: `event_order_class` is
`PRE_R_COMPLETER_EVENT_ORDER` for all 5,419 too, `r1_target_orbit` is `0`
for all 5,419, and `ell` is `5` for all 5,419. **All 49,440 R2 candidates
in this run — both failure classes, with no exception — descend from
this one event.** The other three R1 events (two `UNDECIDED`, one `CH1`)
contributed zero R2 candidates within this 100,250-expansion budget; this
matches the frontier data (§5) showing their subtrees are far shallower.

**Mechanism, from §2's transition law table.** Every one of these 44,021
R2 candidates is preceded by a *full* 5-step rotation run
(`rot^5;...`). A frontier-state check (§5) confirms that **every one of
the 85 frontier states' own current orbit is already registered** (100%
— because a frontier state is, by construction, always standing exactly
where its own most recent weight-`≥2` joint landed, and that landing
*always* sets a bit for its own orbit). It is specifically the
*additional* rotation — the up-to-5 further pure-rotation steps an R2
**candidate**'s own rotation run performs *before* its joint is tested —
that can walk the position into a *different* E-orbit than the one it
started in, and pure rotation (§2) never registers anything. **The
source-orbit failure is not evidence the reachable state space avoids
registered orbits in general; it is a direct, mechanical consequence of
testing `ell=5` R2 candidates specifically**, since a full rotation run
is the one case where the candidate's final position is farthest (in
rotation-steps) from the position that was actually registered.

**Why is `ell` always exactly 5 in this data, never 0-4?** This is
recorded as an **open question, not resolved by the exported ledgers**
(honoring instruction 10 — not inferring an unexported count). The
`enabled_prune_counts` in the medium run show `exact_permutation_collision:
1,541,360` as the single dominant prune reason overall — a plausible
mechanism is that shorter rotation-run candidates (`ell<5`) collide with
an already-visited permutation before ever reaching the R2 test point
(increasingly likely this deep — depths up to 104 out of a 720-state
universe), leaving only `ell=5` candidates to survive to
`evaluate_edge`'s R2 branch. This is **stated as a hypothesis, not a
proven fact**: the exported ledgers give the `ell` of R2 candidates that
*did* reach the recognizer, not a rotation-length histogram of every
generated (including collision-pruned) edge, so this cannot be confirmed
from what is exported. See the counterexample/export request at the end
of this document.

## 4. The 5,419 `not_same_component` failures

**`CLAUDE_OBSERVATION`**, from `rr_short_ell0_v3_component_failures.json`'s
`histograms` block (5,419 of 5,419 records, exhaustive, not sampled):

| quantity | value |
|---|---|
| `r1_target_component_id` | a single fixed ID, identical across all 5,419 |
| `r1_target_vs_r2_source` | `DIFFERENT`, all 5,419 |
| `component_count_pre_r2` | ranges 21-46, a real distribution (not a single value), peak at 31-33 |
| `r2_source_component_class` | exactly 4 distinct shapes, **all with `e_orbits: 1`** — `{1 e_orbit, 1 hexagon, 2 incidences}` (3,438), `{1,2,3}` (1,744), `{1,3,4}` (206), `{1,4,5}` (31) |
| `candidate_edge_would_merge_components` | **`False`, all 5,419** |

**In every one of the 5,419 cases, the R2 candidate's source orbit
belongs to a small, solo component — exactly one E-orbit, together with
1-4 hexagons it has itself touched — never a component that has already
merged with anything else.** This is a real, exhaustive fact, not a
sampled tendency.

**Whether component coarsening could later repair the relation:**
`CLAUDE_OBSERVATION` — nothing in this data proves it cannot, and nothing
proves it must. §2 established that once two nodes share a component they
share it forever, but the converse — that two *currently different*
components will *eventually* merge — is not implied by monotonicity in
either direction. Per instruction, **this document does not infer
permanent impossibility merely because the components are currently
different.** The `candidate_edge_would_merge_components: False` field
answers a narrower question honestly: *this specific* (already-failing)
candidate edge, if it were hypothetically forced through, would not
itself be the merging event — but that says nothing about whether some
*other*, later `Z2`/`Z3`/`R` edge (one that touches a hexagon shared by
both R1-target's component and this source orbit's component) could
still merge them. The exported data does not contain enough of the
walk's *future* trajectory (this is a frontier snapshot, not a
continuation) to check that directly.

**Whether the failure is terminal only at that exact candidate, or
permanently inherited:** it is terminal only at that exact candidate.
`chaining` (recorded per record: `r1.target_orbit == R2.source_orbit`) is
`False` for all 5,419, and each record is a distinct `(pre_state,
candidate)` pair at a distinct depth/position — a later R2 attempt from a
*different* position (a different amount of intervening `Z2`/`Z3`
wandering) could, in principle, test a different, larger, or
differently-connected source component. Nothing here says any later
attempt from this same lineage *would* succeed — only that this data does
not rule it out.

## 5. Frontier structural profiles (all 85 states)

**`CLAUDE_OBSERVATION`**, from `outputs/rr_short_ell0_v3_frontier_export.json`'s
full 85 records (exhaustive):

| quantity | range / distribution |
|---|---|
| `r_count` | `{0: 10, 1: 75}` |
| depth | 51 distinct values, range 1-76 |
| `P` | 3-78 |
| `O` | 2-34 (confirms the run genuinely explores past the old `O=25` boundary, since `O_exceeded` is disabled in this profile) |
| `F`, `H` | `{1}`, `{0}` — fixed at every state (as required to remain a live Target-A candidate) |
| `Ndef` | `{0: 10, 1: 75}` — exactly equal to `r_count` at every state (no exception; `Ndef_cap` is now a *disabled* Area-A-only prune in this profile, so this equality is observed, not enforced) |
| `Phi` | `{0, 1}` only, across all 85 |
| `M` | -95 to -5 |
| hub status | `{COMPLETE: 74, PARTIAL: 11}` (popcount `{6: 74, 1: 10, 2: 1}`) |
| component count | 1 to 33 |
| legal successor count | `{0: 4, 1: 12, 2: 23, 3: 36, 4: 10}` |
| current-position orbit present in incidence forest | **`True`, all 85** (see §3's mechanism note) |

**The 85 states collapse to exactly 8 structural profiles** when grouped
by the 5-tuple `(r_count, R1-target-orbit-if-any, hub status, completer
kind-if-any, legal successor count)` — reported as a **descriptive
grouping for readability, not a claim of continuation equivalence**: states
sharing a profile still differ in depth, exact permutation, and specific
component structure, and nothing here asserts they would behave
identically under further extension.

| profile | count |
|---|---:|
| `r_count=1, R1_target=0, hub=COMPLETE, completer=Z2, successors=3` | 33 |
| `r_count=1, R1_target=0, hub=COMPLETE, completer=Z2, successors=2` | 23 |
| `r_count=1, R1_target=0, hub=COMPLETE, completer=Z2, successors=1` | 12 |
| `r_count=0, R1_target=none, hub=PARTIAL, completer=none, successors=4` | 8 |
| `r_count=1, R1_target=0, hub=COMPLETE, completer=Z2, successors=0` | 4 |
| `r_count=1, R1_target=120, hub=PARTIAL, completer=none, successors=3` | 2 |
| `r_count=0, R1_target=none, hub=COMPLETE, completer=Z2, successors=4` | 2 |
| `r_count=1, R1_target=120, hub=PARTIAL, completer=R, successors=3` | 1 |

**76 of 85 states (89.4%) belong to the single R1-event-4 lineage**
(`R1_target=0` rows), matching §3's finding exactly. **4 states have zero
legal successors** — genuine dead ends within this run's explored region
(every one of their `next_edge_labels` is a prune, confirmed directly:
combinations of `target_a_semantic_v1:F_exceeded`,
`outside_RR_joint_model`, `exact_permutation_collision`, and one lone
`r2_not_target`), not merely unexpanded-for-budget-reasons. The dominant
*non-child* next-edge verdict is `outside_RR_joint_model` for 72 states
and `exact_permutation_collision` for 13 — no state's dominant blocker is
any Target-A-scoped prune, consistent with this being a Target-A-safe
profile by construction.

## 6. Ranking-function search — observation only, no theorem

Per instruction, a candidate is only elevated to `CLAUDE_PROPOSAL` with a
hand proof if a genuine transition law, bound, and forbidden-terminal-
value argument can be completed. None of the candidates below clears
that bar this round:

| candidate | monotone? | bounded? | connects to a Target-A obstruction? |
|---|---|---|---|
| `M = P-5O` | no (sawtooth, `+1`/`-4`) | no (neither `O_exceeded` nor `P_exceeded` are enforced in this profile) | no argument found |
| `Phi` | non-increasing at joint boundaries only (established prior round) | empirically `{0,1}` in this data, but `Phi_window_capacity` is a *disabled* prune here, so no enforced lower bound exists | no argument found |
| remaining hub positions (`6 - popcount`) | **yes, non-increasing, bounded below by 0** | **yes** | **no** — hub completion is not a Target-A condition at all (only `F_def`, `H`, same-component are); reaching 0 says nothing about Target-A reachability |
| component count | **yes, non-increasing, bounded below by 1** | **yes** | no proof connecting a specific bound value to forced Target-A success or failure was found |
| unvisited phase count in a *specific distinguished* orbit | not evaluated — no single orbit is distinguished by Target A's own definition beyond "whichever the walk currently occupies," which is not fixed | — | not pursued further |
| future possible completer landings | not computable as a scalar from the exported fields without assuming a continuation | — | not pursued |
| distance to a terminal predecessor class | no terminal-predecessor classification exists yet to measure distance to | — | not pursued |

**`CLAUDE_OBSERVATION`, not `CLAUDE_PROPOSAL`:** two quantities (remaining
hub positions, component count) are genuinely monotone and bounded, but
neither has a completed proof linking its bound to a forbidden or
required value for Target A itself — Target A's own definition simply
does not mention either quantity. No ranking theorem is proposed this
round.

## 7. The theorem attempt, and why it is false as stated

**Candidate theorem (from the assigning instruction):** *"After the
first R event in the `short_ell0` root, the only possible second-R
source orbits are outside the incidence forest unless a specific
transition pattern occurs."*

**`CLAUDE_OBSERVATION`: this is false as an unconditional statement**,
and the data itself is the counterexample — not a hypothetical one.
10.96% of observed R2 candidates (5,419 of 49,440) *do* have their source
orbit inside the forest; they fail on `not_same_component`, a genuinely
different reason. So the source orbit is not *always* outside the forest
after R1 — it depends on how much intervening `Z2`/`Z3`/`R` traffic has
touched that specific orbit by the time a given R2 candidate's rotation
run happens to land there.

**The exact missing transition pattern (task 8):** the escape from
*both* observed failure modes simultaneously — the pattern any future
Target-A hit from this lineage would require — is precisely:

> an R2 candidate whose rotation run lands in an orbit `q` such that (a)
> `orbit_masks[q]` already has at least one set bit from an *earlier*
> `Z2`/`Z3`/`R` edge in the same walk (so `q` has a forest vertex — this
> rules out `r2_wrong_source_orbit`), **and** (b) that vertex's component
> already contains, or is later joined by an intervening edge to,
> whichever component R1's own target orbit belongs to at that same
> moment (so `same_component` holds — this rules out `not_same_component`).

This is not a new theorem — it is a restatement of Target A's own
definition, specialized to name exactly the two ways the exported data
shows it currently fails. No exported record satisfies both (a) and (b)
simultaneously in this run (`Target_A_hits: 0` confirms it directly). This
is offered as the target for the next instrumentation request (final
section), not as a proof that no such pattern exists.

## 8. Safe-prune candidates

**None proposed this round.** Every candidate considered required either
(a) a claim that a currently-different component can *never* merge — the
counterexample discipline in §4 explicitly forbids inferring that from
current-difference alone, and no additional argument was found to support
it — or (b) treating the observed `ell=5`-only pattern as a *provable*
structural necessity rather than an *observed* correlation whose cause
(§3) is explicitly flagged as unconfirmed. Neither clears the "complete
hand proof" bar this round requires.

## Final response

1. **Remote commit verification:** all three commits (`d90b69a`,
   `785ddab`, `24002fd`) confirmed reachable on
   `codex/round43-short-ell0-taxonomy`; all ten required/referenced files
   read; both independent verifiers in the branch report `verified: true`
   with zero failures; the stated "Main Codex result" figures (44,021 /
   5,419 / 0 / `INCOMPLETE`) are confirmed exactly.
2. **Exact incidence-forest definition:** §1 — vertices are `(q, orbit)`
   for orbits with any registered pass-start phase, plus `(h, hexagon)`
   for hexagons those phases target; edges are one per registered
   `(orbit, phase)` pair; the hub has no special status inside the forest
   itself, only in the separate `Decoration` bookkeeping.
3. **Is source-orbit membership monotone?** Yes, for a *fixed* orbit
   (§2: once `orbit_masks[q] != 0`, it stays nonzero — the vertex, once
   created, is never removed). No, as a property of "the orbit an R2
   candidate happens to test" across different candidates, since that
   orbit is chosen by an ephemeral rotation offset, not fixed.
4. **Can `not_same_component` be later repaired?** Not provably either
   way from this data (§4) — monotonicity guarantees a merge, once it
   happens, is permanent, but does not guarantee any specific pair of
   components ever merges. No permanent-impossibility claim is made.
5. **Frontier structural profiles:** 85 states reduce to 8 descriptive
   profiles (§5), with 89.4% concentrated in one R1-event lineage and 4
   genuine dead-end (zero-successor) states.
6. **Theorem or exact evasion pattern:** the candidate theorem is false
   as stated (§7) — 11% of R2 attempts already clear the source-orbit
   test. The exact pattern that would clear both failure modes
   simultaneously is stated precisely in §7.
7. **Proposed Codex verification task:** see below.

## Proposed Codex export/verification request (not a search request)

To resolve §3's open hypothesis (why every observed R2 candidate has
`ell=5`) without this analyst running any search: export, for a bounded
sample of expanded post-R1 nodes, the **rotation-length histogram of
every generated edge** (not just ones reaching the R2 recognizer),
partitioned by which prune reason each `ell` value received — in
particular, whether `ell∈{0,...,4}` R2-shaped candidates are being
eliminated by `exact_permutation_collision` before ever reaching
`evaluate_edge`'s R2 branch. This would convert §3's hypothesis into
either a confirmed mechanism or a genuine counterexample, without any
new traversal.

CLAUDE_R2_SOURCE_ANALYSIS_COMPLETE
