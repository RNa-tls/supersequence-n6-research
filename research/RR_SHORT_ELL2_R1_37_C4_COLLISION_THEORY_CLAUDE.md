# The "C4 collision" phenomenon: real grounding found, but not where claimed

## 0. Verification status — read first, this materially changes the analysis

**"Round 59" and "Stage E" do not exist anywhere this session can
reach**, and the specific figures attributed to them are **directly
contradicted**, not merely unverified, by the latest real data:

- Two genuinely new branches were found this round:
  `codex/round-r1-37-dangerous-entry-results` (Round 57: dangerous-entry
  realizability) and `codex/round-r1-37-first-component-z3-stage-d`
  (Round 58: the Stage-D exact search). Both fetched, all files
  present, both already-established engine machinery grounding
  confirmed by reading the verifier scripts.
- **Round 58's own report states explicitly: "Stage E was optional and
  was not run"** — directly contradicting this round's claim that
  "Stage E added 1,000,000 exact expansions."
- **Round 58's real frontier figures do not match this round's claimed
  figures at all**: the real capped seeds are `:6` (frontier **34,712**)
  and `:3` (frontier **34,657**) after Stage D — not the claimed
  "seed_6 frontier = 560" / "seed_3 frontier = 9,483."
- **No "C1"-"C6" classification appears anywhere in the real ledger.**
  Round 58 uses a *different*, real classification (`FZ0`-`FZ6`,
  defined precisely in its own report), and reports **all 800,516
  accepted `Z3` transitions as `FZ0`** — component-unchanged — with
  `FZ1`through `FZ6` all zero. This is the real, verified analogue of
  "zero dangerous outcome across a very large search," but it is not
  the "C4 collision" framing this round's prompt describes.

**This document does not attack a fabricated "C4 collision"
phenomenon.** Instead, it grounds the same underlying mathematical
question — *why does every accepted `Z3` turn out component-unchanged,
despite local possibility?* — in the **real, independently-verified**
Round 57/58 data, which turns out to be more than sufficient for
genuine progress, including finally completing the R4 classification
this analyst's own prior round explicitly could not do for lack of
data. Every real figure below was read from the fetched files, not
restated from this round's prompt.

## 1. A genuinely new theorem-shape finding, grounded in real data

Round 57's own "necessary exact-state condition" (independently read
from its manifest, not restated from any summary) states precisely:

> For a direct `Z3` dangerous entry, its target hexagon lies in the hub
> component. The new incidence can merge the components only if its
> target orbit already lies in the R1 component... None of the 88
> target orbits is 91.

**This is exactly the desired theorem shape, and it is already proved,
not merely observed** — for a subtle but decisive reason this
document did not previously articulate as sharply: `Z3`'s own defining
condition (`om[q]==0`, fresh) is **logically incompatible** with its
target orbit "already lying in the R1 component" (which requires
`om[q]!=0`, registered). **A "direct `Z3`" event — fresh orbit,
target hexagon in hub — can never simultaneously be the event that
connects to `C_R1`, because freshness and prior-registration are
mutually exclusive for the same orbit.** This is why all 88
"direct-`Z3`" mechanisms are structurally dead on arrival for the
bridge role specifically (though each is still a perfectly legal
ordinary `Z3` in its own right) — **the "object" the theorem needs is
exactly this: the target orbit's own prior registration as a member of
`C_R1`**, and a `Z3` can never supply that object for itself by
definition.

This directly explains why the *other* 108 mechanisms
(`NEXT_Z2_HUB_HEX`) exist at all: they are precisely the escape from
this dead end — a **later** `Z2` (not fresh, orbit-preserving) fired
*after* some earlier event has already put the relevant orbit inside
`C_R1`. **This structure is an exact, independent match to the
mechanistic dichotomy derived in the prior round's document** (direct
FZ1 vs. delayed-`Z2`-completion), confirmed here against real data
Codex separately and independently produced — the 88/108 split is not
merely analogous to that framework, it is the same fact, discovered
twice, from two directions.

**What "object" means precisely, in engine semantics**: the incidence-
forest edge `(target_orbit, target_hexagon)` that a prior event must
have already registered, such that `target_orbit` is a member of
`C_R1`'s vertex set *before* the dangerous `Z3`/`Z2` is attempted.

## 2. The first-touch mechanism, applied to the real R4 data

**This round's own claim — "253,537/253,537 observed C4 attempts
collide" — cannot be checked (no such data exists), but the real R4
data supports an exactly analogous, and now *fully* checkable, claim.**

All 22 real R4 entries (independently pulled and inspected, not
sampled) share the identical structural shape: **every one is a
`NEXT_Z2_HUB_HEX` mechanism** (zero are `DIRECT_Z3`), each with
`observed_legal_values: [false]` and `exact_observation_count` ranging
1-7 — i.e., every time the specific preceding triple was actually
observed in the bounded (depth-4) graph, the resulting `Z2`'s bridge
legality evaluated to `false`, every single time, no exceptions. This
is the real, exact analogue of "100% observed failure" the prompt's
"C4" framing gestures at.

**Forced chronology, stated precisely from the real
`required_predecessor_condition` field of each of the 22**: each entry
requires a *specific* named orbit to "already belong to the R1-target
component" before its `Z2` can bridge — 17 distinct orbits across the
22 entries: `{1,3,7,10,11,13,16,25,27,35,57,63,65,97,121,126,138}`.
**No cyclic contradiction was found** — each is a plain, unfulfilled
precondition (the named orbit is simply not yet in `C_R1` at the
observed point), not a logical impossibility. The registration
→ prior-occupation → local-legality → attempted-bridge chronology the
task asks about is real and confirmed by the data's own field
structure, but it terminates in an *unfulfilled precondition*, not a
*contradiction* — consistent with this analyst's own negative result
last round (no cycle found there either, on independent grounds).

**A direct, hand-verified cross-check between this analyst's own prior
computation and the real 22 R4 entries**: of the 17 required orbits,
**exactly one — orbit 126 — appears in this analyst's own previously-
computed candidate-orbit lists** (both the 5-hexagon and 2-hexagon
versions, and among the "hub-touching" subsets from two prior rounds).
The other 16 required orbits do not appear in either list, meaning
they are **second-or-later-generation** members `C_R1` would need to
reach — i.e., most of the 22 real R4 cases require a *multi-hop* chain
into `C_R1`, not the single-hop chain this analyst's own prior
"5-orbit two-step" lemma addressed. **This is a genuine limitation of
the prior lemma, now precisely quantified**: it covered at most 1 of
22 real observed near-miss cases; the other 21 require orbits this
analyst has not yet characterized at all.

One record (`orbit 126`'s own R4 entry,
`NEXT_Z2::w3:210|q082|p0`) was inspected in full field detail; its
`resulting_z2_source_orbit: 98` field does not obviously match its own
`z2_target_orbit: 126` in the way "orbit-preserving `Z2`" would
suggest at first reading. **This is flagged honestly as an unresolved
field-semantics question, not resolved by guessing** — it may reflect
a naming convention (e.g. "source" denoting a step before the one
being recorded) this document does not have enough context to
determine confidently; it is not asserted as either confirming or
contradicting this analyst's own model.

## 3. The five hub-touching candidate orbits, revisited against real data

Cross-referencing this analyst's own five candidates
(`{96,120,126,128,129}`, from the 5-hexagon framing) against the real
22 R4 entries: **only orbit 126 appears**, confirming section 2's
finding. Orbits `96, 120, 128, 129` do not appear among the 22 real
R4 cases at all — meaning either (a) they have not yet been tested in
the bounded region Round 57's depth-4 graph covers, or (b) they were
tested and resolved to a *different* class (`R3`, not `R4`) — this
document cannot distinguish these without the full 174-entry `R3` list,
which was not pulled in full this round given the scope already
covered.

**No finite case proof is offered for the 5 orbits as a family** — the
real data shows this family is not uniform: one member (126) has a
real, observed (if still-unfulfilled) `R4` precursor; the other four
have no confirmed status in what was checked this round. Asserting a
uniform "finite case proof" across all five would overreach what the
real data supports.

## 4. Empirical collision vs. structural collision — the correct escalation route

Restating the task's own upgrade question against the *real* R4 data
(not the unverified "C4" figures): "every observed occurrence of this
triple has `observed_legal_values=[false]`" (real, confirmed for all
22) needs to become "every *possible* occurrence would evaluate
`false`," and the ranked routes are:

1. **Complete predecessor-state closure** (highest plausibility,
   given what already exists): for each of the 22, exhaustively
   enumerate every way `orbit_masks`/`hex_masks` could be consistent
   with "the required orbit is registered but the walk reaches this
   exact triple" — a finite, bounded question per entry, since each
   entry names one specific orbit and one specific triple.
2. **Finite registration-order table** (second): building directly on
   section 2's chronology — for each of the 17 required orbits,
   determine (via the same fixed-table method used in prior rounds)
   whether it is *itself* one of the FZ1-candidate orbits for some
   *other* already-open orbit, recursively — this is exactly the
   "multi-hop chain" question section 2 flagged as unresolved.
3. **Forbidden-order lemma** (third): actively sought in section 2,
   not found — remains available as a target but no positive result
   exists yet.
4. **SAT/UNSAT of noncolliding state** (fourth): Round 58's own report
   explicitly declined this route ("a bounded UNSAT model would not
   improve the exact theorem level without a separate suffix-
   completeness argument") — this document agrees with that
   assessment and does not recommend it as the near-term route.
5. **Exact continuation quotient** (fifth, least plausible near-term):
   Round 57's own incremental-coordinate audit (independently read)
   found the *only* coordinate achieving zero mixed cells
   (`registered-orbit mask`) is explicitly noted as "descriptive
   rather than a useful quotient theorem" by Codex itself — this
   document's own reading agrees; no proved continuation equivalence
   exists in any of the real data inspected this round.

## 5. Arrow 2, revisited

The prior round identified Arrow 2 (exact-state-realizability →
branch-reachability) as the likely locus of the gap. **The real R4
data suggests a sharper, three-way split is warranted, and identifies
which new arrow is failing**:

`local C4-analogue geometry → exact noncolliding precursor state →
branch reachability`

The real data shows: for all 22 R4 entries, **the middle stage
(exact noncolliding precursor state) is *not* the failure point** —
`abstract_distance_from_observed_domain: 0` for every one of the 22,
and each has `exact_observation_count >= 1`, meaning **an exact,
reachable precursor state genuinely exists and was genuinely
observed** in the bounded graph. The failure is squarely at the *last*
stage: the resulting `Z2`'s bridge legality, checked at that exact,
reached state, evaluates `false` — **because the required orbit is
simply not yet registered**, not because the precursor itself is
unreachable. **This means the originally-identified "Arrow 2" was too
coarse**: reachability of *a* relevant precursor state is not, in
these 22 cases, the problem at all — the problem is a *further*,
*specific* registration precondition failing at that precursor, which
this document now separates as its own distinct question (matching
section 2's "required predecessor orbit" framing) rather than folding
it into general "reachability."

## 6. Falsifiable lemma candidates

1. **Lemma (Direct-Z3 exclusion)**: *No `DIRECT_Z3_HUB_PHASE` mechanism
   can ever be an `FZ1`/bridge witness for `C_R1`, for any orbit,
   under this engine's rules.* **Why the data suggests it**: proved in
   section 1 from `Z3`'s own freshness definition, and consistent with
   all 88 real direct-`Z3` entries showing `fixed_component_merge_
   possible: false`. **Minimal counterexample**: a single `Z3` edge
   whose target orbit is simultaneously fresh (`om[q]==0`) and already
   a `C_R1` member (`q` present in `C_R1`'s vertex set) — impossible
   by definition, so this lemma is **already proved**, not merely
   falsifiable. **Finite check needed**: none; it follows from
   `extend()`'s own source.
2. **Lemma (R4-to-R5 single-hop scarcity)**: *At most one of the 22
   real `R4` entries (the orbit-126 case) can be resolved by a
   single-hop `C_R1` expansion; the other 21 require a `C_R1`
   expansion chain of length >= 2.* **Why the data suggests it**:
   direct cross-check in section 2 (only orbit 126 among the 17
   required orbits appears in this analyst's own 1-hop candidate
   lists). **Minimal counterexample**: any one of the other 16
   required orbits (e.g. orbit 35) shown to share a hexagon directly
   with orbit 91's own phase set after all — refutable by a single
   fixed-table lookup, not yet performed for all 16 this round.
   **Finite check needed**: repeat this analyst's own table-lookup
   method for each of the 16 remaining required orbits against orbit
   91's hexagon set — a bounded, cheap, non-search computation.
3. **Lemma (Collision-object identity)**: *In every `R4` case, the
   specific NR6 collision reported by a naive attempt at the resulting
   `Z2` (if attempted) is caused by the target hexagon's specific
   permutation window already being occupied by a state visited during
   the walk's OWN prior traversal of that hexagon* — i.e., the "object"
   is literally a window the branch itself already wrote, not an
   externally-imposed obstruction. **Why the data suggests it**: the
   real `observed_legal_values:[false]` records a *legality* failure,
   but this document does not have direct evidence distinguishing an
   `NR6` collision from a *component-registration* failure (the
   `required_predecessor_condition` language suggests the latter, not
   `NR6`) — **this lemma is flagged as plausible but genuinely
   uncertain**, not suggested strongly by the data as read. **Minimal
   counterexample**: a single R4 entry whose failure is a component-
   registration gate, not an `NR6` collision — likely true for most or
   all 22, which would refute this lemma as stated. **Finite check
   needed**: inspect the specific rejection reason field (not the
   summary `observed_legal_later_z2_bridge_values`) for each of the 22
   — not available in the files pulled this round.
4. **Lemma (Chronology non-cyclicity)**: *No pair of the 196 real
   dangerous mechanisms forces a mutually contradictory registration
   order (A before B and B before A).* **Why the data suggests it**:
   this analyst's own active search (this round and last) found no
   such pair. **Minimal counterexample**: two specific mechanisms whose
   `required_predecessor_condition`s each name the *other's own target
   orbit* as a prerequisite. **Finite check needed**: a direct pairwise
   scan of all 196 `required_predecessor_condition` fields against all
   196 target/resulting orbit fields — a small, bounded, non-search
   computation not performed this round for lack of remaining scope,
   but fully specified and cheap.
5. **Lemma (Multi-hop closure sufficiency)**: *If, for each of the 16
   unresolved `R4` required orbits, a finite chain of already-real
   candidate-orbit lookups (recursively applying this analyst's own
   table method) shows the orbit is reachable from orbit 91 within
   some bounded number of hops via hexagons not yet excluded, then a
   genuine multi-step bridge template exists for that R4 case.*
   **Why the data suggests it**: section 2's chain-length finding
   directly motivates this as the natural next question. **Minimal
   counterexample**: any one of the 16 orbits shown to be *unreachable*
   at any finite hop count from orbit 91 within the fixed hexagon
   tables — a genuine, checkable negative result if found. **Finite
   check needed**: a bounded (not search) breadth-first closure over
   the fixed orbit-hexagon adjacency graph, starting from orbit 91,
   which this document's prior rounds have already shown is a
   deterministic, non-search table computation.

## What this document does not do

- Does not treat "Round 59"/"Stage E"/"C1-C6" as real — they are
  contradicted, not merely unverified, by Round 58's own explicit
  report.
- Does not claim to have resolved all 22 R4 cases — only cross-checked
  one (orbit 126) against prior work and precisely scoped what remains
  for the other 21.
- Does not assert Lemma 3 (collision-object identity) as likely true —
  flagged explicitly as uncertain given available data.
- Does not perform the pairwise scan (Lemma 4) or the multi-hop closure
  (Lemma 5) — both specified precisely as bounded, non-search
  computations for a future round, not executed here given the scope
  already covered.
- No search run, no Codex artifact modified.

CLAUDE_C4_COLLISION_THEORY_READY
