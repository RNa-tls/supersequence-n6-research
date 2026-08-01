# Necessary conditions for a legal `Z2`/`Z3` component repair between R1 and R2

Continues directly from `RR_SHORT_ELL0_PRODUCTIVE_R1_CLAUDE.md` (commit
`3d0e68d`) over the same already-fetched Codex commit `24002fd` data. No
new fetch, no search. Every claim below is either read from already-
exported data or proved/refuted from already-read source code
(`legacy_research/work/superperm_partial_f1.py`'s `extend()`,
`src/search_rr_target_a_exhaustive.py`'s `incidence_components` and
`advance_decoration`) — no new engine behavior is assumed.

## 1. The preparation spine, formalized

**`CLAUDE_OBSERVATION`**, restating the prior round's finding in the
symbolic form this round asks for:

- **Orbit 120 phase sequence**, in the order the shared `Z2` spine visits
  them: `phase(2) → phase(3) → phase(4) → phase(0)`, i.e. `+1 mod 5` per
  step, starting at phase 2 (the root's own `w2:10` abandonment already
  occupies phase 1, the implicit "phase −1" of this sequence — `O=2` at
  the root already includes orbit 120 with one phase set). Phase 1 of
  orbit 120 is never re-visited by this spine (it is already occupied by
  the root's own landing).
- **Each R1 option** is "fire `w3:120` instead of `w2:10` at spine depth
  `k`," for `k∈{0,1,2,3}`, landing at whichever phase the `w3:120` *move
  formula* computes from that depth's source position (not the same
  phase the `w2:10` alternative would have used — the two moves are
  different fixed transformations of the same source permutation):

  | `k` | R1 lands at (orbit, phase) | this round's label |
  |---|---|---|
  | 0 | (120, 3) | event 1 |
  | 1 | (120, 4) | event 2 |
  | 2 | (120, 0) | event 3 |
  | 4 (after the spine's own hub-touching step at `k=3`) | (0, 2) | event 4 |

  (`k=3`'s own R1 alternative was not observed as a distinct exported
  event — only its `Z2` continuation, which becomes event 4's completer,
  appears in the data. This is recorded as an observed gap, not inferred
  either way.)
- **Hub position coincidence**: orbit 120's phase 0 slot *is* hexagon 0
  (the hub) — a fixed fact about the permutation structure (`hexagon_id`
  of that specific target permutation), confirmed identically by two
  independent edges landing there (event 3's `R` and event 4's spine
  `Z2`), not a property of which move type is used.
- **`CH1` vs. `PRE_R_COMPLETER_EVENT_ORDER`**, exactly, from
  `Decoration.branch`/`event_order_class` (`search_rr_target_a_exhaustive.py`
  lines 144-174): `CH1` requires the completer's `macro_index` to equal
  R1's own `macro_index` — i.e., the *R1 edge itself* is what lands on
  the hub (`k=2`, event 3). `PRE_R_COMPLETER_EVENT_ORDER` requires
  `completer.macro_index < r1.macro_index` — some *earlier* edge already
  landed on the hub before R1 fired (`k=4`, event 4, whose completer is
  the `k=3` spine step). These are mutually exclusive by construction
  (`event_order_class`'s own `if/elif` chain), and no third case applies
  to either event 3 or event 4.

## 2. Repair-type effects, formalized

**`CLAUDE_OBSERVATION` for `Z2`, `CLAUDE_HAND_PROOF` for the vacuity of
"`Z3` re-entry":**

First, a definitional point the task's own vocabulary needs resolving
before the table makes sense. `joint_kind` (`{(2,False,False):"Z2",
(3,False,False):"R", (3,False,True):"Z3"}`) and `extend()`'s own
`new_orbit = om[q] == 0` computation together mean: **a weight-3 edge
landing on an orbit that is already open is *always* classified `R`,
never `Z3`, regardless of the move label used.** "`Z3` re-entry" is
therefore not a distinct legal move category — any edge matching that
description is, by the engine's own definition, an `R`, which §3 of the
prior round already proved unavailable (the R-budget is exhausted at
`R1`+`R2`). **This resolves that item of the task exactly: there is no
third repair type to analyze; only `Z2` and `Z3`-fresh-opening are real
candidates.**

| effect on | `Z2` (existing orbit, new phase) | `Z3` (brand-new orbit) |
|---|---|---|
| incidence-forest vertices | unchanged (orbit already has a vertex) | `+1` (the new orbit's first vertex) |
| incidence-forest edges | `+1` (new `(orbit,phase)`→hexagon edge) | `+1` (identical mechanism, first edge for the new vertex) |
| component partition | may merge the orbit's current component with the target hexagon's current component, **if that hexagon already has a vertex in a different component**; otherwise simply extends the orbit's own component by one hexagon | may attach the new orbit's singleton to whatever component the target hexagon already belongs to, or start a fresh singleton component if the hexagon has none yet |
| hub touch count | `+1` **iff** the target hexagon is the hub, **identical rule for both kinds** (the check is `hexagon_id(target)==hub_id`, independent of `joint_kind`) | same rule |
| `F_def` | `+1` **iff** `not state.visited(word_after(state.p, SIGMA))` — i.e., iff the *old* pass's natural next rotation was still unvisited and got cut short. This is a check on the position *before* this edge fires, using only that position's own visited-set; it does not reference this edge's target, kind, or the incidence forest at all | identical rule (the `dF` computation in `extend()` does not branch on `joint_kind`) |
| R1-target ancestry | unaffected unless this edge's target hexagon happens to already lie in R1-target's component (in which case it extends that same component, it does not create a new one) | same |
| R2-source admissibility | this is what makes the *later* candidate source orbit itself registered, **only if** this specific `Z2`/`Z3` orbit becomes the orbit a later R2 candidate happens to stand in | same |
| terminal geometry (`F≤1`, `H=0`) | at risk only via the abandonment mechanism above; `H` is never at risk (`dH=max(weight-3,0)=0` for weight `≤3`, true of every edge in this alphabet) | identical risk profile |

**`CLAUDE_HAND_PROOF`: `F_def`'s update rule is causally independent of
the incidence-forest/component-merge mechanism.** `dF` is computed from
`state.visited(word_after(state.p, SIGMA))` alone — a predicate over the
*old* orbit's own rotation-continuation and the global visited-set,
containing no reference to `orbit_masks`, `incidence_components`, or
which hexagon the *new* edge targets. Consequently, **whether an edge
merges two components has no causal bearing on whether it triggers
`F_exceeded`.** This is the load-bearing fact for refuting Lemma E below.

## 3. Minimum conditions for a repair to merge the two components

**`CLAUDE_OBSERVATION`**, synthesizing §2 with the exhaustive
`r2_source_component_class`/`r1_target_component` data already read
(`RR_SHORT_ELL0_PRODUCTIVE_R1_CLAUDE.md` §3, re-cited not re-derived): a
`Z2` or `Z3` edge merges R1-target's component with the eventual
R2-source's component **if and only if**:

1. its own orbit already belongs to (or, for `Z3`, becomes) one side of
   the pair — the R2-source's eventual small component; **and**
2. its target hexagon already has a vertex in the *other* side — R1-
   target's component (which, per the one fully-detailed exported
   sample, spans 8 distinct hexagons, not only the hub — see §4); **and**
3. that target *permutation* (not merely the hexagon) has not already
   been visited, or `exact_permutation_collision` rejects the edge before
   the forest is even consulted.

Condition 3 is not automatically satisfied by condition 2: the union-
find operates at **hexagon granularity**
(`("h", hexagon_id(port))`), while collision is checked at **permutation
granularity**. A hexagon with `popcount<6` (i.e., not all 6 of its
slots visited) has a free slot a repair could target without colliding,
even though that hexagon already has a forest vertex from some *other*,
already-visited slot. Only a hexagon at `popcount=6` (the hub is the one
directly observed example, `hub.status: COMPLETE`, all 85 frontier
states) is collision-saturated for every possible target.

## 4. The five candidate lemmas

### Lemma A — "A `Z2` repair cannot merge two distinct components."

**`CLAUDE_HAND_PROOF`: FALSE.** By §2's table, `Z2`'s effect on the
forest is mechanically identical to `Z3`'s (one new edge, orbit-vertex to
hexagon-vertex) except that `Z2` reuses an existing orbit-vertex instead
of creating a new one. Nothing in `Z2`'s definition (`orbit-preserving`,
`new_orbit=False`) constrains *which* hexagon its fixed move-formula
target lands in relative to any existing component — the move label
(e.g. `w2:10`) is a fixed transformation of the current permutation,
computed independently of the incidence-forest state. **Abstract
counterpattern:** any `Z2` edge whose orbit `q` currently sits in
component `C_q`, landing at a fresh phase whose target hexagon `h`
already has a vertex in a *different* component `C_h`, merges `C_q` and
`C_h` — this is not a special or contrived case, it is the generic case
whenever such a `(q, h)` pair with differing components exists and is
reachable by `q`'s fixed move table.

### Lemma B — "Any `Z3` repair that merges the needed components consumes the only remaining allowed hub touch."

**`CLAUDE_HAND_PROOF`: FALSE.** This would only hold if the *only*
hexagon already in R1-target's component were the hub itself. It is
not: the one fully-detailed exported sample
(`rr_short_ell0_v3_component_failures.json` records[0]) gives
R1-target's component as `{e_orbits: 2, hexagons: 8, incidences: 10}` —
**8 distinct hexagons**, of which the hub is only one. **Exact
counterpattern, grounded in already-exported data, not invented:** a
`Z3` edge opening a fresh orbit whose move-formula target lands in any
of the **other 7** already-in-component hexagons (any with
`popcount<6`, per §3 condition 3) merges the needed components without
touching the hub hexagon at all, and so does not consume any hub-touch
budget.

### Lemma C — "Any legal repair changes the future R2 source orbit."

**`CLAUDE_HAND_PROOF`: TRUE**, generalizing the prior round's proof
(there stated only for "the repair event" generically; here confirmed to
hold for both concrete repair types). Inserting *any* additional macro
edge — `Z2` or `Z3`, it does not matter which — lengthens the walk's
history by one edge, so every subsequent rotation-run's landing position
shifts relative to the un-repaired walk (a rotation-run's landing is a
deterministic function of the *exact* preceding position, which has now
changed). **There is no repair type or placement that leaves later R2
candidates' source orbit unchanged**, because the mechanism (position
shift under an inserted edge) is agnostic to which edge kind was
inserted. ∎

### Lemma D — "A repair preserving terminal geometry must occur before completer."

**`CLAUDE_HAND_PROOF`: FALSE.** §2 already establishes `F_def`'s update
rule references only the pre-edge position's own rotation-continuation
and the global visited-set — it has no term for "has the completer
already fired" or "what `macro_index` is this." `H` is never at risk
from any weight-`≤3` edge regardless of timing. **There is no proven
mechanism linking terminal-geometry preservation to completer timing at
all** — the two are governed by disjoint state (`F`/`H` vs.
`Decoration.completer`). **Counterpattern (abstract, since the concrete
walk this data describes already has its completer fixed *before* R1):**
a `Z3` edge, fired strictly between R1 and the re-attempted R2 (hence
necessarily *after* the historical completer in this specific lineage),
targeting a non-hub, non-full hexagon already in R1-target's component —
nothing established in §2 or §3 forces this to trigger an abandonment or
exceed the hub-touch cap merely because it occurs after the completer.

### Lemma E — "A repair after completer necessarily causes `F_exceeded` or collision."

**`CLAUDE_HAND_PROOF`: FALSE, refuted exhaustively by the exported data
itself, not merely abstractly.** In event 4's lineage, the completer
fires at `macro_index 4`, strictly *before* R1 (`macro_index 5`) — so
**every single one of the 100,245 post-R1 node expansions in this run
is, by definition, "after completer."** `outputs/rr_short_ell0_v3_frontier_export.json`'s
85 frontier states report `F: {1}` **exhaustively, with zero
exceptions**, across every one of them — i.e., not one of the (at least)
tens of thousands of accepted, expanded edges in this post-completer
region ever pushed `F` above 1. Combined with §2's causal-independence
proof (component-merging and `F_exceeded` are governed by disjoint
mechanisms), there is no basis — proven or empirical — for the claim
that firing *after* the completer *necessarily* triggers `F_exceeded` or
collision. **This is the most decisively refuted of the five lemmas.**
One caveat, stated precisely rather than glossed over: this exhausts
*ordinary* post-completer continuations, not a *repair*-classified edge
specifically (no confirmed successful repair exists anywhere in this
data — `Target_A_hits: 0`), so the refutation rests on (a) the proven
causal-independence argument, which applies to any edge regardless of
whether it happens to also merge components, plus (b) the exhaustive
empirical absence of `F_exceeded` among all accepted post-completer
edges — not on a directly observed successful repair, which does not
exist in this data.

## 5. Summary of verdicts

| lemma | verdict | grade |
|---|---|---|
| A. `Z2` cannot merge components | **FALSE** | `CLAUDE_HAND_PROOF` |
| B. merging `Z3` always consumes the last hub touch | **FALSE** | `CLAUDE_HAND_PROOF`, exact counterpattern from exported data |
| C. any legal repair changes the future R2 source orbit | **TRUE** | `CLAUDE_HAND_PROOF` |
| D. terminal-geometry-preserving repair must precede completer | **FALSE** | `CLAUDE_HAND_PROOF` |
| E. any post-completer repair causes `F_exceeded`/collision | **FALSE** | `CLAUDE_HAND_PROOF`, exhaustive empirical refutation |

**Net result: four of five candidate lemmas are false, and the one true
lemma (C) does not by itself forbid a repair — it only says a repair
cannot be evaluated against the *original* 5,419 candidates, it produces
new ones.** No proven obstruction to a legal, component-merging,
geometry-preserving repair was found this round — and, per instruction,
none is fabricated. This is a genuinely permissive result relative to
what the candidate lemmas, if true, would have implied.

## 6. The smallest symbolic repair template not ruled out

**`CLAUDE_PROPOSAL`** — synthesizing §§2-5 into the minimal template no
lemma above excludes (not a claim this template is realized anywhere in
the exported data, and not something this document searches for):

```
edge kind:        Z3 (fresh orbit) — chosen over Z2 only because it does
                   not require the repair's own orbit to already be
                   registered; a Z2 template is equally unruled-out if
                   its orbit already sits in the eventual R2-source
                   component (Lemma A)
timing:            strictly after R1, strictly before the re-attempted
                   R2 candidate (necessarily "after completer" in this
                   lineage — Lemma D shows this is not disqualifying)
target hexagon:    any hexagon already possessing a forest vertex in
                   R1-target's component, EXCLUDING the hub hexagon
                   (Lemma B: 7 such non-hub hexagons already known to
                   exist from exported data) AND excluding any hexagon
                   already at popcount=6 (collision risk, Sec.3 cond.3)
target phase/slot: any of that hexagon's not-yet-visited permutations
resulting orbit:   becomes the new orbit the repair's own vertex sits
                   in; a LATER R2 candidate would need its own rotation-
                   run to land back in THIS specific orbit for the
                   repair to matter to it (Lemma C: this is a new,
                   not-yet-characterized candidate, not one of the
                   5,419 already on record)
required check:    F stays <=1 immediately after (not guaranteed by any
                   proof above -- must be checked per concrete edge,
                   since Sec.2's independence proof shows it is POSSIBLE
                   to satisfy, not that it is impossible to fail)
```

This is offered as the target for a future, separate Codex export or
instrumentation request — consistent with the prior round's §6 — not as
a claim that this document has located or verified a working repair.

CLAUDE_REPAIR_THEORY_COMPLETE
