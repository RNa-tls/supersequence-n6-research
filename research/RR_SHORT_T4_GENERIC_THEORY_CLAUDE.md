# A generic lemma schema for the T4 pre-R2-bridge obstruction

작성자: Claude
role: theory synthesis, no new search run

Base case fully verified this session: `short_ell2_r1_37`, Round 61,
`research/RR_SHORT_ELL2_R1_37_T4_FINAL_VERIFICATION_CLAUDE.md`,
end token `CLAUDE_T4_VERIFIED`. This document abstracts that proof into a
branch-independent schema. It proves nothing new about the state space; it
only reorganizes already-verified facts (engine source semantics, and the
specific finite certificates checked for `short_ell2_r1_37`) into reusable
general lemmas, and states precisely what a *different* branch would still
have to supply to inherit T4 "for free."

---

## 1. Abstracting the proof into branch-independent hypotheses

The `short_ell2_r1_37` T4 proof rests on exactly three logical layers, and
each layer separates cleanly into an engine-universal mechanism plus a
branch-specific (anchor-family-specific) finite certificate:

| layer | engine-universal mechanism | branch-specific certificate needed |
|---|---|---|
| (A) predecessor blocking | `extend()` add-only occupancy + no-repeat gate; weight-2 action is a bijection on the 720-permutation space, hence every target has a unique weight-2 predecessor | which literal window is the predecessor, and whether it is visited-everywhere/terminal-nowhere across the frozen anchor family |
| (B) direct bridge blocking | a non-abandoning weight-2 (`Z2`) transition's target orbit must already be open (`new_orbit=False`); while a component is single-orbit, "already open" can only mean "is that one orbit itself" | the phase-hexagon set of the R1-target orbit is disjoint from the fixed hub hexagon set |
| (C) first-component-change blocking | incidence edges union components only through a shared `(h, hexagon)` vertex, and such an edge is created only by the *target* orbit/phase of a legal transition | a *complete* enumeration of every orbit-phase incidence that could land in one of the R1-target orbit's hexagons, each shown obstructed by (A) or by an equally rigorous alternative |

None of the three layers needs to be re-derived from scratch for a new
branch: (A) and (B)'s mechanisms are fixed engine facts (Section 2). Only
the *instantiation data* -- which windows, which hexagons, which anchors --
changes per branch.

## 2. Engine-universal vs. anchor-specific classification

**Engine-universal (true for the whole engine / move table, independent of
which orbit is chosen as R1-target or which anchors are frozen):**

- `extend()` copies `hex_masks` and only ever performs `hm[h] |= 1 << bit`
  for the transition's target window; no code path clears a bit. (Read
  directly from `legacy_research/work/superperm_partial_f1.py`, confirmed
  again this session.)
- `extend()` rejects (`returns None`) any transition whose target window
  bit is already set. No-repeat is a precondition on every single legal
  transition, not a post-hoc check.
- Exactly one weight-2 move exists among the 550 total `ALL_MOVES`
  (`{1:1, 2:1, 3:3, 4:13, 5:71, 6:461}`), and `core.word_after` under any
  fixed move is a bijection on the 720-permutation space. Consequently
  every permutation has exactly one weight-2 predecessor -- a trivial,
  universal fact of this specific engine, unrelated to any branch's
  content.
- `joint_kind` (confirmed this round directly from
  `legacy_research/work/analyze_f1_n2_defects.py::joint_kind`): a
  weight-2, non-abandoning transition is classified `Z2_blocked_w2_existing`
  if and only if `new_orbit=False`, i.e. the target's orbit is *already
  open* (`om[q] != 0`). A weight-3, non-abandoning transition is `Z3`
  (`new_orbit=True`, target orbit must be *fresh*, `om[q]==0`) or `R`
  (`new_orbit=False`, re-entry into an *already-open* orbit, and if fired
  after `R1` this is immediately evaluated as the terminal `R2` event, not
  an intermediate registration step).
- Incidence-component structure: vertices are `(q, orbit)` and
  `(h, hexagon)`; an edge is created per registered `orbit_masks` bit,
  keyed by the transition's *target* orbit/phase and that phase's fixed
  hexagon (from `HEX_POSITION`), never by the source. Two components merge
  if and only if some transition's target vertex pair shares a
  `(h, hexagon)` vertex already reachable from both.
- `ORBIT_PHASE` / `HEX_POSITION` are fixed, global, branch-independent
  lookup tables: given any orbit `q`, its phase-to-hexagon incidence set
  `Φ(q)` is computable in O(1), with no search.

**Anchor-specific / branch-specific (must be certified fresh per branch):**

- Which orbit is `q_R1` (fixes `Φ(q_R1)`, a specific finite hexagon set --
  for `short_ell2_r1_37`, `Φ(91) = {40,82,90,91,92}`).
- The frozen anchor family `A` itself (which states are "frozen Stage-D
  anchors," how many there are -- 84 in this branch -- and their exact
  literal permutation/mask content).
- For each hexagon `h` in the relevant candidate set, whether `h` (or the
  specific predecessor window that matters) is visited-at-every-anchor and
  terminal-at-no-anchor. This is a finite fact about `A`, not a fact about
  the engine.
- The claim that the candidate-incidence enumeration into `Φ(q_R1)` is
  *complete* (no sixth route, no omitted orbit). This is a from-scratch
  recomputation against the fixed rotation table for this specific `q_R1`,
  but is otherwise a branch-specific bookkeeping fact, not an engine law.

**Uncertain / flagged, not resolved this round:** whether the hub's touched
hexagon set (`{0,1,4,6,8,9,18,24,96}` for this branch) is itself
engine-universal (i.e. the same fixed set regardless of which orbit is
chosen as R1-target) or is a branch-specific derived quantity that happens
to coincide across the branches examined so far. This document does not
resolve that question; Section 7 lists it as a certificate a new branch
must supply, precisely because it is not yet known to be free.

## 3. The generic "visited non-terminal source" (VNTS) / predecessor-blocking lemma

This is the reusable core of the whole proof.

> **Lemma (VNTS).** Let `τ` be any literal permutation window that is the
> target of a (unique) weight-2 move, and let `σ` be its unique weight-2
> predecessor. Let `A` be a finite family of frozen `ExactState` anchors.
> Suppose:
>
> - **(H1)** `σ` is visited (its occupancy bit is set) at every anchor in `A`.
> - **(H2)** No anchor in `A` has current endpoint (`state.p`) equal to `σ`.
>
> Then no exact descendant of any anchor in `A` can ever have `σ` as its
> current endpoint, and therefore the weight-2 move into `τ` can never fire
> in any exact descendant of `A`. Consequently `τ` can never be newly
> introduced as an incidence in any descendant's incidence graph via this
> route.

**Proof.** By the engine-universal add-only occupancy fact, `σ`'s bit,
once set, remains set in every descendant (H1 propagates). For `σ` to
become some descendant's current endpoint, some legal transition in that
descendant's history must have `σ` as its *target* (a state's current
endpoint is always the target of the most recent transition, or the
anchor's own endpoint for zero-step descendants, excluded by H2). But
`extend()` rejects any transition whose target window is already visited,
and `σ` is visited at the anchor and remains visited at every intermediate
ancestor by monotonicity -- so no transition in the descendant's history
could have legally targeted `σ`. By H2 the anchor itself is not already at
`σ` either. Hence no descendant is ever at `σ`, so the weight-2 move
sourced at `σ` never has an available "current position" from which to
fire. $\blacksquare$

**Why this needs no search.** The conclusion quantifies over the entire
(finite but potentially enormous) set of exact descendants of `A`, yet the
proof only inspects the finite anchor family itself (H1, H2) plus the
engine's fixed transition rules. This is the entire value of the lemma: it
converts an unbounded reachability claim into two anchor-level bit checks,
by induction on the monotonicity of occupancy rather than by enumeration of
descendants.

### 3.1 The "full-hex" batched corollary

> **Corollary (Full-Hex Provenance Obstruction).** Let `h` be any hexagon
> with windows `w_0,...,w_5`. If `hex_masks[h] = 0b111111` (FULL) at every
> anchor in `A`, and no anchor's current endpoint lies in `h` (i.e. is any
> `w_k`), then VNTS applies simultaneously to all six windows of `h` as
> sources: for every `k`, the unique weight-2 move sourced at `w_k` can
> never fire in any descendant of `A`.

This is a strictly *stronger and coarser* certificate than checking one
window at a time: "hexagon full" is a single 6-bit equality check, and it
discharges up to six VNTS instances at once (one per window), whether or
not the proof at hand actually needs all six.

Round 61's h40 audit is exactly one instantiation of this corollary, with
`h = 40`, discharging `σ = 245130` (window index 1 of hexagon 40) as a
byproduct of certifying all six windows of hexagon 40 full-and-non-terminal
across the 84 anchors -- the other five windows' discharges were not needed
by this round's argument but are free consequences of the same finite
certificate.

## 4. Is the h82 case a broader-principle instance?

**Yes -- and recognizing this required correcting a natural but wrong
framing.** `rr_short_ell2_r1_37_hex82_occupancy_audit.json`'s own text
explicitly rejects the naive reading: hexagon 82's own occupancy mask is
`0` at 81 of the 84 anchors (histogram `{0:81, 2:1, 4:1, 63:1}`), so "h82 is
full" is false and cannot be the basis of any obstruction. The actual
mechanism is a **cross-hexagon** instance of VNTS: the blocked target
`τ = 513042` (`q91:p2`) sits in hexagon **82**, but its unique weight-2
predecessor `σ = 245130` sits in a *different* hexagon, **40**. The Full-Hex
corollary is applied to `h = 40` (not `h = 82`), and the conclusion
("`q91:p2` can never register") is a statement about a target window that
lives in a hexagon whose own occupancy is never inspected at all.

This generalizes cleanly: **VNTS/Full-Hex obstruction never requires the
target's own hexagon to be full.** It only requires *some* hexagon --
wherever the target's unique weight-2 predecessor happens to live -- to be
full-and-non-terminal. Framing the h82 case as "exceptional" was an
artifact of implicitly expecting source and target hexagon to coincide (as
they trivially do when a route is discharged by its own hexagon being
full, e.g. the four `{40,90,91,92}`... case where the *predecessor of a
window in `h`* can itself also lie in `h`, since orbits can have multiple
phases in the same q_R1 phase-hexagon set). Under the general lemma, h82 is
not an exception at all; it is simply the one route in this branch whose
discharging hexagon differs from its own target hexagon. A future branch
should expect cross-hexagon instances to be the *typical* case, not a
special one, since nothing in VNTS's statement ties `σ`'s hexagon to `τ`'s.

## 5. Minimal hypotheses for each theorem

### 5a. No direct Z2 bridge

- **(D1)** [engine-universal] a non-abandoning weight-2 transition's target
  orbit must already be open (`new_orbit=False`).
- **(D2)** [branch-specific, currently established only for `q_R1=91`] while
  the R1-target component `C_{q_R1}` consists of `q_R1` alone (no other
  orbit yet registered into it), the *only* already-open orbit reachable
  from `C_{q_R1}`'s own transitions is `q_R1` itself, so every legal `Z2`
  move fired from within `C_{q_R1}` can only touch hexagons in `Φ(q_R1)`.
- **(D3)** [branch-specific, finite table check] `Φ(q_R1) ∩ H_hub = ∅`,
  where `H_hub` is the hub component's touched-hexagon set.

Given (D1)-(D3): no single `Z2` transition can union `C_{q_R1}` with the
hub component, because doing so would require a shared `(h, hexagon)`
vertex, and by (D2) `Z2`'s reach is confined to `Φ(q_R1)`, which by (D3) is
disjoint from `H_hub`.

### 5b. No first component-changing Z3

- **(C1)** [engine-universal] an incidence edge unions two components only
  through a shared `(h, hexagon)` vertex, created only by a transition's
  *target* orbit/phase.
- **(C2)** [branch-specific, finite, computable] `Φ(q_R1)` is fixed and
  finite (e.g. 5 hexagons for orbit 91).
- **(C3)** [branch-specific, requires completeness proof -- Section 6/task 5
  of the prior round] the *complete* enumeration of every orbit-phase
  incidence that maps into some hexagon of `Φ(q_R1)`, other than `q_R1`'s
  own phases, is known and finite (in `short_ell2_r1_37`: the four
  already-full hexagons' incidences plus exactly five h82 routes).
- **(C4)** [branch-specific, per-candidate] every candidate enumerated in
  (C3) is individually obstructed, either by the Full-Hex corollary applied
  directly to its own target hexagon, or by a VNTS instance whose source
  hexagon lies elsewhere (the h82 pattern of Section 4).

Given (C1)-(C4): no fresh orbit can ever register an incidence into any
hexagon of `Φ(q_R1)`, so `C_{q_R1}` can never gain a second orbit -- no
first component-changing Z3 exists.

### 5c. No pre-R2 bridge (T4)

- The union of 5a and 5b's hypotheses, plus:
- **(T4-dichotomy)** [purely definitional, no additional hypothesis] any
  pre-R2 transition that would bridge `C_{q_R1}` to the hub component
  either changes `C_{q_R1}`'s orbit membership at the moment it fires
  (requires a prior first component-changing Z3, blocked by 5b) or it does
  not (so it must itself be a direct bridge from the still-single-orbit
  `C_{q_R1}`, blocked by 5a). These two cases are exhaustive and mutually
  exclusive by definition of "changes membership," so no third mechanism
  needs to be separately hypothesized or ruled out.

## 6. Counterexamples: why each dropped hypothesis is necessary

Each counterexample is a direct logical consequence of dropping exactly one
hypothesis, requiring no new search -- only tracing what the engine's rules
permit once the corresponding safeguard is removed.

**Drop H1 (σ visited at every anchor).** Suppose instead some anchor `A0`
has `σ` unvisited. Nothing then prevents a two-step descendant of `A0`:
first a legal transition targeting `σ` (legal precisely because `σ` is not
yet visited), making `σ` both visited *and* the current endpoint
simultaneously; then immediately firing the weight-2 move onward to `τ`.
This directly registers `τ`, contradicting the VNTS conclusion. H1 is load
bearing.

**Drop H2 (no anchor terminal at σ).** Suppose instead some anchor `A1` has
current endpoint exactly `σ` (note: this is consistent with H1, since being
at `σ` implies `σ` is visited). `A1` can then fire the weight-2 move
*immediately*, in one step, registering `τ`. H2 is independent of H1 and
equally load bearing -- this is exactly why Codex's audit reported "245130
visited: 84/84" and "current endpoint = 245130: 0/84" as two *separate*
metrics rather than inferring one from the other.

**Drop D3 (`Φ(q_R1) ∩ H_hub = ∅`).** Suppose instead some hexagon `h*`
belonged to both sets. Registering `q_R1`'s own remaining phase in `h*` is
a fully legal, non-abandoning `Z2` transition under D1-D2 (it targets
`q_R1`, an already-open orbit) -- and firing it immediately unions
`C_{q_R1}` with the hub component through the shared `(h*, hexagon)`
vertex, in a single move. This is a literal one-step direct Z2 bridge,
exactly what 5a claims is impossible. D3 is load bearing.

**Drop C3 (completeness of the candidate enumeration).** Suppose a sixth
route into `Φ(q_R1)` existed but was omitted from the enumerated candidate
list. Every *enumerated* candidate could individually be proved obstructed
(C4 holds vacuously for the incomplete list) while T2+ ("complete C4
prerequisite space closed") is nonetheless false, because the omitted
candidate can still fire, change `C_{q_R1}`'s membership, and invalidate T3
and T4 downstream. This is precisely why the prior round's task insisted on
an independent, from-scratch rotation-table recomputation of the candidate
list (verified in `RR_SHORT_ELL2_R1_37_T4_FINAL_VERIFICATION_CLAUDE.md`
section 5) rather than trusting a stored route file -- a silently omitted
route is a hypothesis, not a proof, and its omission is undetectable from
inside the (incomplete) enumeration itself.

## 7. Finite certificate checklist for automatic T4 inheritance

For a new child branch with R1-target orbit `q'` and its own frozen anchor
family `A'` to inherit T4 via this schema **without a fresh bespoke hand
proof**, Codex must supply the following, all of which are either O(1)
fixed-table lookups or finite, mechanically checkable certificates over
`A'`'s own stored/replayed corpus -- none require a new open-ended search
beyond what already produced `A'` and its descendant corpus:

1. **`Φ(q')`** -- the phase-hexagon incidence set of `q'`, from
   `ORBIT_PHASE`/`HEX_POSITION` directly (free, O(1), no certificate
   needed beyond the table lookup itself).
2. **Hub disjointness certificate**: `Φ(q') ∩ H_hub = ∅`. If `H_hub` is
   confirmed engine-universal (Section 2's open question resolved
   affirmatively), this is a free table check; otherwise `H_hub` must be
   independently recomputed for the branch containing `q'` and the
   disjointness re-verified from scratch.
3. **Full candidate enumeration into `Φ(q')`**: for every hexagon
   `h ∈ Φ(q')`, all orbit-phase incidences (other than `q'`'s own) whose
   target window lies in `h`, recomputed from the fixed rotation table
   independent of any stored route list (the from-scratch check that
   guards against the C3 counterexample of Section 6).
4. **Per-candidate discharge**: for each candidate in (3), either (a) a
   Full-Hex certificate on its own target hexagon, or (b) a VNTS
   certificate whose predecessor chain traces to some hexagon `h_src`
   (possibly different from the candidate's own hexagon, per Section 4)
   that is full-and-non-terminal across `A'`.
5. **Anchor-level ledger**: for each `h_src` used in (4), an explicit
   per-anchor record (not a summary flag) of `hex_masks[h_src] == 63` and
   `current_endpoint ∉ windows(h_src)` for every anchor in `A'` -- the
   `short_ell2_r1_37` analog is `rr_short_ell2_r1_37_h40_anchor_fullness.json`'s
   84 raw `anchors` records.
6. **Full-corpus monotonicity replay**: an assertion-guarded replay of
   every parent-to-child macro edge across `A''s entire stored descendant
   corpus (not merely the frontier/anchor snapshot) confirming
   `parent.hex_masks[h] & ~child.hex_masks[h] == 0` for every hexagon on
   every edge -- the `short_ell2_r1_37` analog is the 1,325,308-edge
   replay.
7. **Full-corpus general component-membership replay**: a replay, over the
   same full corpus, of the *general* union-find `component_summary` query
   (not a shortcut on any single orbit's mask bit) confirming that the
   target hexagon of every candidate in (3) never shares a component with
   `q'` at any replayed node -- the `short_ell2_r1_37` analog is
   `hex82_in_r1_component_nodes == 0` over 1,325,392 nodes. This item alone,
   if satisfied, subsumes most of the discharge burden of (4)-(5): it is
   the single strongest, most general safety net, and is exactly what
   directly answers the "no hidden alternative mechanism" concern for a new
   branch the same way it did for `short_ell2_r1_37`.

Given items 1-7, T4 for the new branch follows by the *same* VNTS +
Full-Hex + union-find argument structure proved generically in Sections 3-5
of this document, with no new bespoke reasoning required -- only the
finite, mechanically-verifiable certificates above, which are the exact
generalization of what Codex already produced for `short_ell2_r1_37`.

---

## Deliverable cross-reference

Machine-readable mirror: `outputs/rr_short_t4_generic_theory_claude.json`

## Explicit non-claims

- This document proves no new fact about any specific branch's state space;
  `short_ell2_r1_37`'s own T4 remains scoped exactly as stated in the prior
  verification round.
- The hub-hexagon-set engine-universality question (Section 2) is
  explicitly left open, not resolved either way.
- Item 3 of Section 7 (candidate enumeration completeness) is stated as a
  *requirement*, not proved here to be achievable in bounded time for an
  arbitrary orbit `q'` -- some orbits may have larger or more entangled
  `Φ(q')` sets than orbit 91's.
- No claim is made that every branch's hub-disjointness (D3) or
  candidate-obstruction (C4) will hold; the schema only says *if* these
  finite certificates are supplied, T4 follows automatically. Whether they
  can be supplied for any given `q'` is a separate, per-branch empirical
  question.

## End token

`CLAUDE_T4_GENERIC_THEORY_READY`
