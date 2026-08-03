# Can the R1-target component merge with the hub component before R2? A formal, code-grounded audit

No search run this round, in either the exhaustive or the deterministic-replay
sense used in prior rounds — Codex's continuation worker is doing the actual
state-space work. Everything below is derived directly from three already-
verified source files (`legacy_research/work/superperm_partial_f1.py`'s
`extend`, `ExactState`; `src/search_rr_target_a_exhaustive.py`'s
`advance_decoration`, `evaluate_edge`, `target_a_recognizer`,
`incidence_components`) plus the already-verified per-child JSON data from
the prior two rounds (`incidence_forest` records for the top-8). Where the
analysis depends on a fact about a *specific* child's state that isn't
already recorded in the cached JSON (e.g. whether a particular hexagon
coincidence actually exists), it is left explicitly open, framed as the
precise question for Codex's own running continuation traces to answer —
not computed here.

## 0. The exact mechanism, read from source

Three facts, each pinned to a specific line, that the whole analysis rests
on:

**(i) Only weight&ge;2 moves touch `orbit_masks`; rotation (weight1) never
does.** `extend()` (`superperm_partial_f1.py:213-255`): the `if
move.weight >= 2:` block is the only place `om[q] |= 1 << phase` occurs.
`RotationRun.delta_orbit_bits` is therefore always empty in practice — pure
rotation only ever mutates `hex_masks`, never `orbit_masks`. Consequence:
**only joints (`Z2`, `Z2abandon`, `Z3`, `R`) can add an edge to the
incidence forest; rotation cannot.**

**(ii) Each joint sets exactly one incidence bit, keyed by its *target*
orbit and *target* hexagon — never its source.** `q, phase =
ORBIT_PHASE[target]; om[q] |= 1 << phase` (`superperm_partial_f1.py:239,
245`). Combined with `incidence_components`'s own definition ("edges = one
per set `orbit_masks` bit", vertices `(q,orbit)` and `(h,hexagon)`), one
joint = one edge `(target_orbit, target_hexagon)`. **The source orbit of a
joint never itself receives a new edge from that joint** — it only remains
connected to whatever it was already connected to before.

**(iii) `F` only increases on an *abandonment*, and abandonment is a
property of the state, not of which joint is chosen.**
`abandonment = not state.visited(core.word_after(state.p, core.SIGMA))`
(`superperm_partial_f1.py:235`) depends only on `state.p` — the position the
walk is *at*, not which weight&ge;2 target is picked from there. Since
these roots already have `F = TARGET_F = 1` (`target_a_recognizer`'s own
comment, and `TARGET_F = 1` at `superperm_partial_f1.py:51`), **any further
abandoning joint pushes `F` to 2 and is pruned (`F_exceeded`)**. At a given
state, abandonment is all-or-nothing across every weight&ge;2 candidate
from it: either continuing rotation is still legal (every joint fired now
is `Z2abandon`/an abandoning `Z3`/`R`, all pruned) or it collided (every
joint fired now is `Z2`/`Z3`/`R` proper, all `F`-preserving). This is the
exact reason the observed literal traces always fire joints at one specific
"forced" rotation length per step (hand-confirmed by direct replay two
rounds ago: at the D1 divergence point, the only surviving `rot^5` options
were `Z2`/`Z3`, while `rot^0`-`rot^4` alternatives were all `Z2abandon` or
`other`).

**(iv) `H` never changes for any RR-alphabet joint.**
`dH = max(move.weight - 3, 0)` — zero for every weight-2 or weight-3 move.
`H_positive` can only ever be triggered by a weight&ge;4 move, which
`evaluate_edge` already excludes as `kind == "other"` before `H` is even
considered. **`H` is a non-issue for any `Z2`/`Z3`/`R` bridge candidate.**

**(v) `hub_touch_count` increments only when the target's hexagon equals
one *specific* hexagon (`dec.hub_id`), not "any hexagon in the hub's
incidence component".** `advance_decoration`
(`search_rr_target_a_exhaustive.py:401`): `if
core.hexagon_id(transition.target) == dec.hub_id: touch_count += 1`. For
all 8 top-8 children, `hub_id = 0` and the completer (the *first* touch)
is exactly what sets `touch_count` from 0 to 1. The hub's *incidence
component*, by contrast, is much larger — e.g. for `short_ell2_r1_70`,
`{0,1,4,6,8,9,18,24,96}`, nine distinct hexagons. **These are not the same
thing: landing on hexagons 1, 4, 6, 8, 9, 18, 24, or 96 merges into the
hub's component without touching `hub_touch_count` at all; only landing on
hexagon 0 specifically does.**

**(vi) The R-budget structurally forbids using `R` as an intermediate
bridge.** `evaluate_edge` (`search_rr_target_a_exhaustive.py:823-846`): once
`dec.r_count == 1` (post-`R1`), *any* `R`-kind edge taken is immediately
routed to `target_a_recognizer` and returned as `FOUND_TARGET_A` or
`r2_not_target` — terminal either way, never re-classified as an ordinary
`child`. **There is no way to "spend" the one remaining `R` slot as a
practice merge and then fire a second, real `R2` later — whichever `R`
edge is taken second is unconditionally *the* `R2` attempt.** Bridging must
therefore use only `Z2` and `Z3`.

## 1. Which legal edge kinds can merge the two components

| kind | can merge? | mechanism | side-effect on the walk's current orbit |
|---|---|---|---|
| `Z2` (forced, non-abandoning) | **yes, conditionally** | preserves orbit (target orbit = walk's current orbit, already has a vertex); merges component iff the target *hexagon* happens to already be registered in hub's component via some other orbit | none — walk stays in the same orbit, only phase advances |
| `Z3` (forced, non-abandoning, opens a genuinely fresh orbit) | **yes, conditionally** | the fresh orbit's *only* edge is `(fresh_orbit, target_hexagon)`; merges the fresh orbit into hub's component iff that target hexagon is already hub-registered — but this does **not** retroactively pull the *source* orbit of the `Z3` into hub's component, only the walk's position *after* the move (which is now inside the fresh, now-hub-connected orbit) | walk moves into the fresh orbit |
| `R` | **structurally excluded as a bridge** | any `R` taken post-`R1` is consumed as `R2` itself (section 0.vi) | n/a — terminal |
| `Z2abandon` / abandoning `Z3`/`R` | **no** | pruned by `F_exceeded` before any component question is even reached, since these roots already sit at `F = TARGET_F = 1` | n/a |

**Both live bridge mechanisms (`Z2`, `Z3`) are conditional on the same
underlying event: a target hexagon that is already registered in hub's
component being reachable, without collision, from wherever the walk
currently sits at its next forced rotation length.** This event's
existence for any of the 8 specific children's post-`R1` states is not
verified in this document (see section 6).

## 2. Effects of each edge kind, systematically

| | `Z2` (forced) | `Z3` (forced) | `R` (any) |
|---|---|---|---|
| **R budget** | untouched (`r_count` unaffected — `joint_kind` is not `"R"`) | untouched | consumes the sole remaining slot; `r_count` 1&rarr;2, terminal |
| **Incidence forest** | adds edge `(current_orbit, target_hex)`; merges iff `target_hex` already registered elsewhere | adds edge `(fresh_orbit, target_hex)`; merges the *fresh* orbit (not the source) iff `target_hex` already registered elsewhere | adds edge `(reentered_orbit, target_hex)` to an *already*-registered orbit; this is precisely what `target_a_recognizer`'s `same_component` check evaluates |
| **hub_touch_count** | +1 iff `target_hex == hub_id` exactly (0 in these 8); +0 for any other hub-component hexagon | same rule, independent of kind | same rule; this is the very edge being judged, so its own touch is what's checked against the `<=2` cap |
| **F / H** | `F` unchanged (forced, non-abandoning by construction, section 0.iii); `H` unchanged (section 0.iv) | same | same, plus `F_def == 1` and `H == 0` are the recognizer's own explicit gates on the resulting state |
| **Future R2 source orbit** | **unchanged** — the walk remains in the same orbit; an `R2` fired immediately after would still source from this orbit, just a later phase | **changed** — the walk is now positioned in the fresh orbit; an `R2` fired immediately after sources from there instead | n/a (this edge *is* R2 or R1) |
| **Terminal geometry** | none of `F_exceeded`/`H_positive`/`F1_fragment_normal_form_impossible` triggered when forced (by construction) | same | evaluated by `target_a_recognizer`'s own `F_def_equals_1`/`H_equals_0` conditions on the resulting state |

The single sharpest asymmetry: **`Z2` can grow the merged territory while
leaving the future `R2` source orbit unchanged; `Z3` cannot** — firing a
`Z3` necessarily relocates the walk to the fresh orbit, so whatever
merge it achieves comes bundled with a changed `R2`-source-orbit
candidate.

## 3. Does a merge require touching the hub directly, an intermediate, before/after the completer, or altering the future R2 source?

- **Direct touch vs. intermediate component**: not required to be direct.
  A merge could in principle happen via a genuinely *third* component (an
  orbit unconnected to either R1's territory or hub's, that happens, across
  two separate incidences, to touch a hexagon in each) — but per section
  0.ii, **a single joint sets only one edge**, so a true two-hop bridge
  (orbit X touches R1-target's territory via one joint, then a *different*
  later joint from elsewhere touches hub's territory while landing back in
  orbit X) requires **two separate joints through the same orbit vertex**,
  not one. This is geometrically possible (nothing in the mechanics forbids
  revisiting an orbit's *unused* phases across non-consecutive steps) but
  is a strictly more expensive template than the one-step version in
  section 1, and is not needed if a one-step coincidence already exists.
- **Before or after the completer**: irrelevant to the *mechanism* — the
  completer only matters because it is the event that first sets
  `hub_touch_count` from 0 to 1 and fixes `hub_id`'s identity; the
  incidence-forest merge machinery (section 0.i-ii) applies identically to
  every joint regardless of its position relative to the completer. The
  completer is already, definitionally, one of hub's own registered
  incidences (it is how hub's component came to include hexagon 0 as its
  first member).
- **Alter the future R2 source orbit**: **only if the merge is achieved via
  `Z3`** (section 2) — a `Z2`-mediated merge leaves the source orbit fixed.

## 4. The four candidate lemmas

### Lemma A — "`Z2` cannot connect the isolated `R1`-target component to the hub without changing the future R2 source."

**Refuted, exact symbolic counterpattern.** By definition `Z2` is
orbit-preserving (section 0, section 2): firing it does not move the walk
out of `R1`'s target orbit, only to a new phase within it. If (and only
if) that new phase's target hexagon happens to already be registered in
hub's component via some *other* orbit, this single `Z2` edge merges
`R1`-target's component with hub's — while the walk's current orbit
(hence the source orbit any immediately-following `R2` attempt would use)
is **unchanged**, exactly the case Lemma A claims cannot exist. **Whether
such a coincidental hexagon actually exists within any of the 8 children's
`R1`-target orbit's *unvisited* phase set is not verified in this
document** — the lemma is refuted at the mechanism level (the claimed
impossibility does not follow from the rules), not shown to be realized in
any concrete instance. This existence question is handed to Codex in
section 6.

### Lemma B — "Any `Z3`-fresh merge into the hub component causes an F or hub-touch violation."

**Refuted, exact symbolic counterpattern.** Section 0.v is the precise
mechanism: `hub_touch_count` increments only for the one specific hexagon
`hub_id` (hex 0 in all 8 cases), never for any other hexagon in hub's
(much larger) incidence component. A forced `Z3` targeting, say, hexagon 96
or hexagon 18 — both already members of `short_ell2_r1_70`'s own hub
component per its `incidence_forest` record — would merge into hub's
component while leaving `hub_touch_count` completely untouched. And by
section 0.iii, a *forced* (non-abandoning) `Z3` never increments `F`
regardless of which hexagon it targets — abandonment is a state property,
not a target-hexagon property. **Neither half of Lemma B's disjunction is
forced to trigger** by a `Z3` merge that avoids the single hexagon
`hub_id`. As with Lemma A, whether the *specific* geometric coincidence
needed (a forced `Z3` from the relevant post-`R1` state landing on a
non-`hub_id` hub-component hexagon) actually occurs for any of the 8
children is left open for Codex's continuation traces.

### Lemma C — "Any legal two-step component bridge consumes geometry needed for R2."

**Partially refuted; true only in an avoidable special case.** Read
literally ("any... bridge"), false: an `R`-budget check is moot (`Z2`/`Z3`
never touch `r_count`, section 0.vi), `F`/`H` are moot for forced joints
(section 0.iii-iv), and `hub_touch_count` is moot *provided the bridge
avoids the single hexagon `hub_id`* (section 0.v, Lemma B). A well-chosen
one-step bridge (section 1) consumes none of the four resources
`target_a_recognizer` actually gates on. **The refuted claim is the
universal "any"; the genuine risk it points at is real but conditional**:
a bridge that happens to re-touch hexagon `hub_id` specifically *would*
consume the one remaining hub-touch slot (the completer already spent the
first of the two allowed), potentially leaving none for whatever `R2`
itself lands on if `R2`'s own target also happens to be hexagon 0 — a
real, avoidable cost, not a necessary one. The two-hop version of a bridge
(section 3) genuinely does cost one extra macro step's worth of `F`/`H`
exposure compared to the one-step version, but neither is intrinsically
forced to consume resources "needed for R2" in the sense of exhausting a
hard budget.

### Lemma D — "The isolated component can only merge through an orbit already absent from the required incidence forest."

Two readings, both addressed:

- **Reading 1 (the bridging orbit must be fresh/never-before-registered,
  i.e. only `Z3` can bridge)**: **Refuted**, same counterpattern as Lemma
  A — `Z2`, which reuses the *already-registered* `R1`-target orbit rather
  than a fresh one, is an equally valid bridge mechanism under the exact
  rules (section 1-2). The merge does not require an absent/fresh orbit at
  all.
- **Reading 2 (the bridging orbit must be one not otherwise needed by the
  eventual R2 attempt, i.e. a "sacrificial" orbit distinct from R2's own
  target)**: **left open** — nothing in `evaluate_edge` or
  `target_a_recognizer` distinguishes a "sacrificial" bridging orbit from
  the orbit `R2` itself eventually targets; whether a *specific* successful
  path would reuse the same orbit for both purposes or need two distinct
  orbits is a question about which literal continuations are legal from a
  given post-`R1` state — exactly the kind of fact only a continuation
  trace (Codex's, not a fresh search here) can settle.

## 5. Summary verdict table

| lemma | verdict | basis |
|---|---|---|
| A | refuted (mechanism-level); existence of the specific coincidence unverified | `Z2` orbit-preservation (section 0.ii, section 2) |
| B | refuted (mechanism-level); existence of the specific coincidence unverified | `hub_touch_count`'s single-hexagon scope (section 0.v) |
| C | refuted as a universal claim; true only in the avoidable hub_id-touching special case | resource accounting across all four gated quantities (section 0.iii-vi) |
| D | refuted under reading 1; left open under reading 2 | `Z2` bridge counterpattern; no engine-level "sacrificial orbit" concept found |

## 6. The smallest unresolved component-bridge template, for Codex's continuation traces

Everything above reduces the open existential to one concrete, checkable
pattern. For each of the 8 children's continuation trace (or, more
generally, any `R1`-provenance child in the 439-child corpus), Codex's
worker can check, for every macro edge fired strictly between `R1` and
whichever edge is eventually judged as `R2` (or the branch's cap point):

> **Is there a legal (`exact.extend`-succeeding), forced (non-`Z2abandon`,
> non-abandoning) `Z2` or `Z3` edge, sourced from the walk's then-current
> orbit, whose `target_hexagon` is already a member of the pre-move
> incidence forest's hub-containing component, and is *not* equal to
> `hub_id` itself?**

If such an edge exists and is taken, this document's analysis predicts
(from the rules alone, not from having observed it): `F`, `H`,
`hub_touch_count`, and the `R`-budget all remain exactly as they were
one step earlier, the merge is achieved, and — if the edge was `Z2`
specifically — the future `R2`'s candidate source orbit is unchanged from
what it would have been without the bridge. This is the exact,
minimal, mechanically-necessary-and-sufficient condition; nothing weaker
suffices (per section 0.i-ii, no other edge kind or hexagon choice can add
a merging incidence bit) and nothing stronger is required (per section
0.iii-vi, no resource is spent by construction when this specific
condition holds).

## What this document does not do

- Does not check whether the above template's condition is actually
  satisfied for any of the 8 children, or for any child in the 439-child
  corpus — that requires either the literal orbit/hexagon geometry tables
  or a continuation trace, and is explicitly left to Codex's already-running
  worker per the task's instruction not to duplicate it.
- Does not claim a component merge, even if achieved, is *sufficient* for
  `FOUND_TARGET_A` — `target_a_recognizer` also requires the resulting
  `R2` edge itself to satisfy `F_def_equals_1`, `H_equals_0`, and
  `hub_touch_count_le_2` at the moment it fires, which is a separate,
  unaddressed question from whether the *forest* permits it.
- Does not resolve Lemma D's second reading (a possible "sacrificial
  orbit" distinction) — flagged as genuinely open, not engine-visible from
  the code read this round.
- Runs no search and no replay of any kind — this is a pure, source-grounded
  derivation from already-read code and already-verified prior-round JSON
  data.

CLAUDE_COMPONENT_BRIDGE_ANALYSIS_COMPLETE
