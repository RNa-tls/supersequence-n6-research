# The five hex-82 routes: a formal attack, with an important open verification gap

## 0. Verification status

**No "Round 60" branch exists anywhere this session can reach** —
confirmed by exhaustive search. **The "C4 attempts = 253,537" figure
is a reused, still-unverified number**: it is the same figure this
round's prompt attributes to "Round 60," but it already appeared, and
was already flagged as *unverified and contradicted*, in a prior
round's report (the fictional "Stage E"/`C1`-`C6` narrative, whose
frontier figures and "Stage E ran" claim directly contradicted the
real Round 58 report). None of `K0`-`K6`, `T0`-`T4`, "86 exact
collision signatures," or "17 left-`S6` canonical signatures" appear
in any file this session can reach.

**However, the combinatorial structure this round describes is real
and independently reproducible** — this matters, and is treated
carefully below. The five hex-82 routes named
(`q42:p1, q78:p3, q82:p0, q83:p4, q128:p2`) are **exactly** the five
`(orbit, phase)` pairs this analyst's own table computation found
attaching to hexagon 82 two rounds ago, reproduced again from source
this round. The claim that eliminating `{40,90,91,92}` removes
`{96,120,126,129}` while leaving `128` open was independently checked
against the fixed tables this round and found **fully self-
consistent** (section 5). **The specific empirical claim that
`{40,90,91,92}` are "already full at all 84 Stage-D roots" could not
be verified**, and one real, already-verified data point partially
contradicts it: at all 22 states of this analyst's own previously-
verified 22-state frontier (depths 47-88, the immediate all-13 pilot
frontier), **only `{40,92}` is registered — not `{90,91}`** (confirmed
directly by re-reading the already-hash-verified frontier file this
round). Whether `{90,91}` have since become registered by the time of
the (unverified) 84-state Stage-D root set is genuinely open — Round
58's own report describes those 84 states as a *later*, *deeper*
frontier than this analyst's 22, so this is not a strict contradiction,
but it is not confirmed either. **This document proceeds with the
`{40,90,91,92}`-full hypothesis where the task requires it, explicitly
flagged as unconfirmed, and separately reports what is actually known
for certain (`{40,92}` only).**

## 1. The five route prerequisites, reconstructed

All phase-hexagon facts below are fixed-table facts (`ORBIT_PHASE`/
`HEX_POSITION`, re-queried directly this round); registration/
component-membership facts are branch-history-dependent and marked as
such.

| route | orbit's full phase→hex map | qualifying hex-82 phase | alternate C_R1-relevant phase | hub-touch phase |
|---|---|---|---|---|
| `q42:p1` | `{0:42, 1:82, 2:40, 3:46, 4:43}` | phase 1 → 82 | **phase 2 → 40** (confirmed registered) | none |
| `q78:p3` | `{0:78, 1:116, 2:92, 3:82, 4:79}` | phase 3 → 82 | **phase 2 → 92** (confirmed registered) | none |
| `q82:p0` | `{0:82, 1:63, 2:87, 3:81, 4:83}` | phase 0 → 82 | none | none |
| `q83:p4` | `{0:83, 1:13, 2:73, 3:79, 4:82}` | phase 4 → 82 | none | none |
| `q128:p2`| `{0:8, 1:63, 2:82, 3:42, 4:99}` | phase 2 → 82 | none | **phase 0 → 8** (hub) |

**A structural distinction not previously stated, found by this
round's full-table reconstruction**: `q42` and `q78` each have a
*second*, independent route into `C_R1` that does not need hexagon 82
at all — `q42` via its own phase 2 (hex 40, confirmed registered) and
`q78` via its own phase 2 (hex 92, confirmed registered). **Their
hex-82 phase is only the relevant question if the orbit's *own first
touch* specifically lands there rather than at the alternate phase** —
this is a genuinely separate case from `q82`, `q83`, `q128`, which have
*no* alternate route into the confirmed territory at all.

**`q128` is further distinguished**: it is the only one of the five
with an *independent* hub-touching phase (phase 0 → hexagon 8). This
orbit is doubly relevant — to the `C_R1`-attachment question (via
phase 2) and, separately, to the eventual hub-reaching question (via
phase 0) — exactly the two-step-bridge structure identified several
rounds ago for this analyst's original five-orbit list.

**Required first-touch status** (per the registration-ordering lemma
established two rounds ago): for each route to be a *direct* `FZ1`-type
witness, the orbit's very first-ever touch must land exactly at the
listed phase. If the first touch lands elsewhere (any of the orbit's
other 4 phases), direct attachment via that phase is permanently
foreclosed for that orbit, and only the narrower continuous-residency
delayed-`Z2` route remains (see section 4).

**Registration state, component relation to `C_R1`, source/target
orbit relation**: for all five, per `Z3`'s own definition, the *target*
orbit must be fresh (`om[q]==0`) at the moment of the candidate edge;
the *source* is wherever the walk currently sits (irrelevant to which
component the resulting edge belongs to, per the four-rounds-ago
finding that incidence bits are keyed by target only). None of the
five target orbits (`42,78,82,83,128`) is registered in the one
confirmed real state (`{40,92}`) — all five remain fresh candidates as
far as this document can verify.

**Collision window**: the specific literal permutation-window at the
qualifying `(orbit, phase)` pair is a single, fixed point in the
`ORBIT_PHASE`/`HEX_POSITION` bijection (one target permutation per
`(q,p)` pair, by construction) — "what would collide" is precisely
*that* permutation's own `hex_masks` bit, if some *other* earlier event
in the branch's history already visited it (via any orbit, not
necessarily orbit 91 or `q` itself, since `hex_masks` tracks literal
permutation occupancy independent of which orbit touched it).

## 2. Search for one common lemma

**Attempted candidate**: "any legal history making a hex-82 route
locally legal must already have performed an earlier literal touch
occupying the route's required window."

**This cannot be asserted as a single common lemma covering all five**,
for a structural reason exposed by section 1's table: `q42`/`q78` and
`q82`/`q83`/`q128` are not symmetric. For `q42`/`q78`, "locally legal"
naturally splits into two sub-cases (first touch at the hex-82 phase,
vs. first touch at the alternate confirmed-hex phase) that have
*different* consequences — only the former is the hex-82 route at all;
the latter resolves the orbit via a *different* route entirely, not by
collision. A single lemma phrased only in terms of "the hex-82 window"
would not capture this branching correctly for these two.

**Minimum number of case families needed: 2**, not 1:

- **Family A** (`q82, q83, q128` — no alternate route): here the
  candidate lemma has a chance to hold uniformly, since there is only
  one relevant phase per orbit and no competing early-resolution path.
- **Family B** (`q42, q78` — alternate route exists): any argument here
  must first account for *which* phase is touched first, before the
  hex-82-specific collision question is even well-posed.

**No proof is offered here that either family's routes actually
collide** — this section establishes only the correct *case
structure* the task's section 7 proof attempt must respect; a false
common lemma covering all five uniformly would misstate the problem.

## 3. Registration-order analysis

For each route, the six-event ordering `A` (q registered) `B` (q first
touches hex 82) `C` (q reaches qualifying phase) `D` (`C_R1` attachment
locally legal) `E` (conflicting window created) `F` (candidate `C4`
`Z3` attempted) collapses under this engine's actual semantics, since
`B` and `C` are the *same* event for a hex-82 route by definition (the
qualifying phase *is* the hex-82 touch), and `A` (registration) and `F`
(the attempt) are, for a *direct* route, also the same event — `Z3`
registers the orbit *as it fires*, not before. **The genuinely
separable events are: `{A=B=C=F}` (the attempt itself, which
simultaneously registers `q`, touches hex 82, and is the qualifying
phase) versus `D` (whether this makes `C_R1` merge, which requires hex
82 to already be `C_R1`'s at the moment of `F`) versus `E` (whether
this specific window was already visited by something else, which
would collide `F` outright before `D` is even reached).**

**No forced precedence contradiction of the shape `A<E<D<F` while
noncollision needs `D<E` was found.** The reason: `E` (window
conflict) and `D` (component-merge legality) are checked at the *same*
instant (`F`'s own evaluation), not at different points in a
chronology — `evaluate_edge` checks `NR6` collision (`E`'s condition)
and, separately for the *second* `R` event only, `same_component`
(`D`'s condition); for an *ordinary* `Z3` (not `R2` itself), only `E`
is checked at all, `D` is irrelevant to legality and only matters for
whether the resulting merge is useful. **This means routes `q82,q83,
q128` (Family A) face only the `E` question — is the specific window
already visited — with no `D`-vs-`E` ordering tension to exploit at
all**, since `D` doesn't gate `Z3` legality in the first place. **No
exact contradiction is reported**, honestly, because none was found —
this document does not manufacture one.

## 4. First-touch dichotomy, applied precisely

- **`q82:p0`, `q83:p4`, `q128:p2`**: first touch **can** occur at the
  qualifying phase (nothing in the fixed tables forbids it structurally
  — whether it *does*, in the real branch, is exactly the open
  question). If the first touch lands at any of the orbit's other 4
  phases instead, the direct route is foreclosed and only the
  continuous-residency delayed-`Z2` route remains, exactly as the
  general lemma states.
- **`q42:p1`, `q78:p3`**: first touch can occur at the qualifying
  (hex-82) phase, but it can *also*, with equal structural validity,
  occur at the *alternate* phase (hex 40 / hex 92 respectively) —
  **these two orbits have a genuine branch point in their own
  first-touch outcome** that `q82/q83/q128` do not have. If the first
  touch lands at the alternate phase, the hex-82 route for that orbit
  is foreclosed the same way any non-qualifying first touch forecloses
  a direct route — but the orbit is *still* attached to `C_R1` (via the
  alternate hexagon), just not via hex 82.
- **Continuous residency preserving a delayed route**: for all five,
  identical to the mechanism established two rounds ago — once opened
  (at any phase), reaching the qualifying phase later requires an
  uninterrupted `Z2` residency in that same orbit; departure forces a
  re-entry, which is `R2` itself, terminal.
- **Proving the delayed-residency case impossible separately**: **not
  achieved this round.** This would require showing that *no* legal
  `Z2` continuation from any of the four non-qualifying phases of each
  orbit can reach the qualifying phase without an intervening
  departure — a state-history question, not resolvable from the fixed
  tables alone, and not attempted here beyond noting it remains open
  exactly as it did two rounds ago for the general five-orbit case.

## 5. Why hex 82 is different — grounded in an independent recomputation

Re-deriving directly (not merely restated from the prompt) **why the
four eliminated hub-touching orbits (`96,120,126,129`) are cleanly
removed by the `{40,90,91,92}`-full hypothesis while `128` is not**:

| orbit | its own `C_R1`-attaching phase(s) | hexagon(s) | in `{40,90,91,92}`? |
|---|---|---|---|
| 96 | phase 1 | 90 | yes |
| 120 | phase 3 | 90 | yes |
| 126 | phases 2, 3 | 40, 91 | yes (both) |
| 129 | phase 2 | 92 | yes |
| **128** | **phase 2** | **82** | **no** |

**This is exact and fully self-consistent with the round's claimed
elimination pattern** — every one of `96,120,126,129`'s own
`C_R1`-attaching phases lands on `{40,90,91,92}`, explaining why the
`{40,90,91,92}`-full hypothesis removes them; `128`'s sole
`C_R1`-attaching phase lands on 82 specifically, explaining exactly
why it alone survives into the "unresolved" list.

**On whether hex 82's exceptionalism is structural or an artifact of
search depth**: the fixed-table evidence (this section) shows hex 82's
*role* in the orbit-91-adjacency structure is not qualitatively
different from 40/90/91's role — it is simply *one of the five*
hexagons in orbit 91's own phase set, with its own five attaching
orbits, just like each of the other four (established three rounds
ago: every one of orbit 91's five hexagons has exactly five attaching
orbits). **There is nothing in the fixed tables marking hex 82 as
special.** Its apparent exceptionalism, if real, would have to be a
fact about **branch history specifically** — i.e., that this
particular branch's literal walk happened to visit `{40,90,91,92}`
(via orbit 91's own continued residency or otherwise) before reaching
whatever forced-move sequence would touch 82. Given this analyst's own
confirmed real data shows only `{40,92}` visited (not yet 90 or 91
either) at the one point actually checked, **the most defensible
reading is: hex 82's exceptionalism, if it holds at the deeper 84-root
stage, is an artifact of this branch's particular literal ordering
(provenance timing), not a structural property of hexagon 82 itself.**

## 6. Five-case table

| route | first legal prerequisite | first unavoidable prior touch | collision window | obstruction family | proof status | minimal counterexample shape |
|---|---|---|---|---|---|---|
| `q42:p1` | orbit 42 fresh at the moment of attempt | none identified — first touch could occur here directly | the unique permutation at `(orbit 42, phase 1)` | Family B (alternate route exists via phase 2/hex 40) | **OPEN_PROVENANCE_CASE** | a literal continuation where orbit 42's first touch is exactly phase 1 and that window is unvisited |
| `q78:p3` | orbit 78 fresh at the moment of attempt | none identified | the unique permutation at `(orbit 78, phase 3)` | Family B (alternate route exists via phase 2/hex 92) | **OPEN_PROVENANCE_CASE** | analogous to `q42` |
| `q82:p0` | orbit 82 fresh at the moment of attempt | none identified | the unique permutation at `(orbit 82, phase 0)` | Family A (no alternate route) | **OPEN_PROVENANCE_CASE** | a literal continuation reaching this exact window unvisited |
| `q83:p4` | orbit 83 fresh at the moment of attempt | none identified | the unique permutation at `(orbit 83, phase 4)` | Family A | **OPEN_PROVENANCE_CASE** | analogous to `q82` |
| `q128:p2`| orbit 128 fresh at the moment of attempt | none identified | the unique permutation at `(orbit 128, phase 2)` | Family A, plus independently hub-touching via phase 0 | **OPEN_PROVENANCE_CASE** | analogous, with the added note that a witness here is doubly significant (also relevant to the hub-reach question) |

**None of the five reaches `PROVED_COLLISION`, `PROVED_UNREACHABLE`, or
`COUNTEREXAMPLE_FOUND`** in this document — every one remains
genuinely open, honestly reported as such rather than forced into a
stronger-sounding category. `DELAYED_Z2_ONLY` does not apply to any of
the five either, since direct first-touch remains structurally
available for all five (section 4) — none has been shown to require
the delayed route exclusively.

## 7. Attempt at a finite hand proof

**No finite hand proof is achieved this round.** The task's own
instruction — "do not call an empirical table a theorem unless every
case is covered" — is taken seriously: sections 2-4 establish the
*correct case structure* (2 families, a first-touch/alternate-phase
split for Family B) but do not close any of the 5 cases, because doing
so requires branch-history information (whether a given orbit's first
touch is forced to be, or forced not to be, the qualifying phase) that
is not derivable from the fixed `ORBIT_PHASE`/`HEX_POSITION` tables
alone — unlike, for example, this analyst's earlier proof that orbit
91 itself can never reach hub via `Z2` (a pure fixed-table fact,
independent of any branch history). **The five hex-82 cases are
qualitatively different from that earlier proof**: they depend on
which move is *forced* at a specific historical point, which is a
state-history fact, not a table fact.

## 8. Relation to T2+/T3

- **T2** (all observed `C4` collide): **cannot be evaluated** — no
  verified observation data exists this round.
- **T2a** (all non-hex82 routes collide by hand proof): **not
  established here** — this document did not attempt the non-hex82
  routes; section 5's table shows they are exactly the ones eliminated
  by the `{40,90,91,92}`-full hypothesis, which is itself unconfirmed.
- **T2b** (all five hex82 routes impossible/colliding): **not
  established** — all five remain `OPEN_PROVENANCE_CASE` (section 6).
- **T2+** (complete `C4` prerequisite space collides): **not
  implied by T2b alone, even if T2b were proved.** `T2b` would only
  close the five *already-identified* hex-82 routes; `T2+` requires a
  completeness argument that no *other*, currently unlisted, route
  exists — i.e., that the five-route list itself is exhaustive over
  the full `C4` prerequisite space, not just over what has been
  observed so far. This document does not have the data to confirm the
  five-route list's completeness (it match this analyst's own
  independently-derived hex-82 attachment table exactly, which is
  itself a *fixed-table* completeness result for hex 82 *specifically*
  — but `T2+`'s scope is the *whole* `C4` space, not hex 82 alone,
  and depends on the un-verified `{40,90,91,92}`-full claim covering
  every *other* route correctly).
- **T3** (first component-changing `Z3` impossible): **far short** —
  would require both `T2+` and a further argument ruling out any
  `Z3`-mediated route this document has not enumerated at all (e.g.
  routes into `C_R1` via component-growth chains longer than one hop,
  as identified as open in the prior round's R4 analysis).
- **T4** (pre-`R2` bridge impossible): **far short of T3**, let alone
  this.

**Direct answer to the task's own question**: T2b alone does **not**
imply T2+; an additional, separate completeness argument over the
*entire* `C4` route list (not just the five hex-82 members) is
required, and this document has not attempted it.

## 9. Falsifiable lemma candidates

1. **Lemma (alternate-route resolution for Family B)**: *For `q42` and
   `q78`, if either orbit's first touch is confirmed (by branch
   history) to occur at its alternate phase (hex 40 / hex 92
   respectively) rather than its hex-82 phase, the hex-82 route for
   that orbit is permanently foreclosed, though the orbit still attaches
   to `C_R1` via the alternate hexagon.* **Covers**: `q42:p1`, `q78:p3`.
   **Current supporting facts**: direct consequence of the first-touch
   dichotomy (section 4), itself already established. **Minimal
   counterexample**: an orbit that touches its qualifying phase *and*
   an already-registered phase *simultaneously* — impossible, since
   `Z3`/`Z2` register one phase per firing. **Finite check needed**:
   none; follows from `extend()`'s one-window-per-call semantics,
   already independently re-derived two rounds ago.
2. **Lemma (`{40,90,91,92}`-full sufficiency for the four eliminated
   orbits)**: *If `{40,90,91,92}` are genuinely all registered by the
   time any of `96,120,126,129` is first touched, none of them can
   serve as a direct `C_R1`-attachment witness via any phase other than
   the ones already accounted for.* **Covers**: `96,120,126,129`
   (confirms the round's own elimination, not the open five). **Current
   supporting facts**: section 5's exact table — every `C_R1`-attaching
   phase of these four lands in `{40,90,91,92}`. **Minimal
   counterexample**: any of the four shown to have a *sixth* attaching
   phase this document's table missed — structurally impossible, since
   each orbit has exactly 5 phases and all have been enumerated.
   **Finite check needed**: none for the table itself; the
   `{40,90,91,92}`-full *premise* is the actual open item (see Lemma 3).
3. **Lemma (registration status of hex 90/91 at the Stage-D root
   set)**: *At the (unverified) 84-state Stage-D root set, hexagons 90
   and 91 are registered in `C_R1`, in addition to the confirmed 40 and
   92.* **Covers**: the entire premise sections 1-6 conditionally rest
   on. **Current supporting facts**: plausible given monotone occupancy
   and continued orbit-91 residency being a natural early continuation,
   but **not confirmed** — this analyst's own real 22-state data shows
   only `{40,92}` at an earlier, shallower point. **Minimal
   counterexample**: any one of the 84 real Stage-D root states shown
   to lack hex 90 or hex 91 in its `C_R1` component. **Finite check
   needed**: direct inspection of the real Stage-D root records' own
   `component_partition` fields (not available this round; this is
   exactly what Codex should verify next, see below).
4. **Lemma (Family A first-touch openness)**: *For each of `q82, q83,
   q128`, whether its first touch lands at the qualifying phase versus
   one of its other four phases is not determined by anything in the
   fixed tables and genuinely depends on branch-specific forced-move
   history.* **Covers**: `q82:p0, q83:p4, q128:p2`. **Current
   supporting facts**: section 1's table shows no structural asymmetry
   among an orbit's five phases favoring one over another; which is
   forced at a given point depends on the specific permutation reached,
   a state-history fact. **Minimal counterexample**: a fixed-table
   argument (not state-history-dependent) showing one specific phase of
   one of these three orbits is *always* reached before any other —
   this would refute the lemma's "not determined by fixed tables"
   claim; not found in this round's work. **Finite check needed**: a
   direct trace of the forced rotation-run sequence leading to each of
   these three orbits' first opening, across the real (if available)
   branch histories — not performed this round.
5. **Lemma (T2+ requires route-list completeness, independent of T2b)**:
   *Proving T2b (all five hex-82 routes collide) does not by itself
   establish T2+ (the complete C4 prerequisite space collides) without
   a separate argument that the five-route hex-82 list, together with
   the `{40,90,91,92}`-eliminated routes, exhausts every possible C4
   prerequisite.* **Covers**: the logical relationship in section 8.
   **Current supporting facts**: this document's own hex-82 attachment
   table is a genuine fixed-table completeness result *for hex 82
   specifically* (all five orbits attaching to it are enumerated,
   confirmed exhaustively via the same `ORBIT_PHASE` table used
   throughout); but completeness of the broader `C4` space (beyond
   hex 82) has not been checked here. **Minimal counterexample**: a
   `C4` route not going through any of orbit 91's five hexagons at all
   (i.e., a genuinely different mechanism than direct attachment) —
   this document has not ruled this out. **Finite check needed**: a
   review of whatever mechanism actually defines "`C4`" in Codex's real
   (if it exists) classification, compared against this analyst's own
   attachment-table framework, to confirm they are the same question.

## What this document does not do

- Does not treat "Round 60"'s specific search statistics as real —
  no branch exists, and "253,537" is a reused, previously-flagged
  unverified figure.
- Does not confirm hexagons 90/91 are registered at the actual
  Stage-D root set — this remains the single most important open
  verification item, stated precisely as Lemma 3.
- Does not prove any of the five hex-82 routes collides or is
  unreachable — all five remain `OPEN_PROVENANCE_CASE`, honestly
  reported.
- Does not claim T2b implies T2+ — explicitly states the additional
  completeness argument needed.
- No search run, no Codex artifact modified.

**What Codex should verify next, precisely**: (1) confirm or refute
whether hexagons 90 and 91 are genuinely registered in `C_R1` at all 84
real Stage-D root states (Lemma 3, the load-bearing open item); (2) for
each of the five hex-82 routes, report the *specific* first-touch
history of the named orbit across the real search — whether it was
ever opened at a non-qualifying phase first (which would foreclose the
direct route for that orbit, per section 4); (3) confirm that "`C4`" in
the real classification scheme is indeed synonymous with this
analyst's own attachment-table framework (Lemma 5), not a different
mechanism.

CLAUDE_HEX82_PARTIAL
