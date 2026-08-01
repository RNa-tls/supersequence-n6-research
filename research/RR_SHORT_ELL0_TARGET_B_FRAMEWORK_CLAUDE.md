# Proof-safe canonicalization and Target B framework for new `short_ell0` boundaries

Planning document — **prepared ahead of, not in response to, verified
data.** No new search was run.

## 0. Verification check on the cited result

**`CLAUDE_OBSERVATION`.** This round cites "Codex found 38,406 exact
Target A hits in the fair repair search" with no commit reference. I
checked anyway, consistent with every prior round: `git ls-remote origin`
shows `codex/round43-short-ell0-taxonomy` unchanged at `24002fd` — the
same commit already fully analyzed (`Target_A_hits: 0` in that run) — and
no new branch exists. **The 38,406 figure is not verified from anything
reachable by this session.** This document does not depend on it being
accurate: it is a methodology framework, built entirely from this
repository's own already-proven facts, written to be ready *if and when*
such a result lands, exactly as the "prepare the analysis schema ahead of
the v3 run" framework was two rounds before the v3 run actually existed.
Nothing below cites 38,406 as a fact about the world.

## 1. Proved symmetries that may identify Target A boundaries

**`CLAUDE_OBSERVATION`**, all read from already-existing, already-tested
code and docs — no new symmetry is derived here:

| symmetry | status | source |
|---|---|---|
| **Left-`S6` relabeling** (`exact.canonicalize`) | **proven**, exercised at scale | `legacy_research/work/superperm_partial_f1.py` lines 421-435: the lexicographically-least translate under left multiplication by the 720-element symbol-relabeling group. Docstring's own caveat, load-bearing: *"This is a child quotient only. It never assumes a strict canonical-parent property, so it cannot remove a complete orbit merely because a prefix was reached in another order."* |
| **Decorated-pair canonicalization** (`(S, D)` jointly) | **proven, with a measured (not assumed) triviality result** | `research/RR_DECORATED_BOUNDARY_STATE.md` §3: since `canonicalize()` returns only the minimal key, not the achieving `α`, the *pair* `(state, decoration)` must be canonicalized by transporting decoration through every `α` achieving the minimal state-key and taking the lex-least result. Measured on the existing 2,234-boundary corpus: `stabilizer_size=1` and `tie_variant_count=1` for **all** 2,234 — i.e., no boundary in that corpus has a nontrivial symmetry to break a tie with. This is recorded explicitly as a **root-local exhaustive observation**, not a proof that ties never occur — *"tie가 relation 판정을 바꾸지 않음은 이 universe에서 공허하게 참이다... 일반 상황에서 tie가 생기면... 그 절차의 relation-불변성은 이번 라운드에서 증명하지 않았다 — 미완료"* (translated: vacuously true for this universe only; the tie-resolution procedure's relation-invariance was not proven in general). **For a new corpus (short_ell0-derived), this vacuity cannot be assumed — nontrivial stabilizers are not ruled out and must be re-measured.** |
| Rotation/hexagon structure (right action, `SIGMA`) | **not itself a boundary-identification symmetry** | rotation defines the hexagon partition (used throughout this project's own `hex_masks`/`hexagon_id` machinery) but is not applied as an equivalence *between distinct boundaries* anywhere in the read documents — it is baked into the state representation itself, not a separate quotient step. |
| Any reversal / time-reversal symmetry | **no proof found in any document read** | not mentioned in `RR_TARGET_A_DEFINITION.md`, `RR_DECORATED_BOUNDARY_STATE.md`, or `RR_TARGET_A_SOURCE_UNIVERSE.md`. Absence of a proof is reported as absence, not as a claim that no such symmetry exists. |

**Consequence for the new corpus:** exactly one symmetry (left-`S6`) is
proven at the state level, and the decorated-pair canonicalization
procedure built on it is proven *mechanically* (well-defined) but its
observed triviality (`stabilizer_size=1` everywhere) is an **empirical
fact about the old 2,234-boundary corpus specifically**, not a theorem
about all possible boundaries. The new corpus must run the same
measurement, not inherit the old result.

## 2. Features that must remain in the boundary key

**`CLAUDE_OBSERVATION`**, mapping this round's requested feature list
onto `RR_DECORATED_BOUNDARY_STATE.md`'s already-proven 27-field
decoration schema (5 orbit-transported + 4 hexagon-transported + 18
left-`S6`-invariant fields) plus one gap that schema does not cover:

| requested feature | status in the existing schema | verdict for the new corpus |
|---|---|---|
| **decorated state** (the raw `ExactState`) | Round 19 showed each of the old corpus's 2,234 post-R2 `ExactState`s maps to *exactly one* boundary — meaning `ExactState` alone would trivially separate everything, which is *why* the Round 20 ablation deliberately excluded it to test decoration's own sufficiency. That 1-boundary-per-state fact is itself a **corpus-specific empirical finding**, not a theorem. | **must remain** — "one state, one boundary" is not proven to transfer to the new (repair-produced) corpus, where the same `ExactState` could conceivably be reached by more than one distinct repair history |
| **incidence forest** | not stored directly; represented through the derived hub-ancestry fields below | **must remain reconstructible** — every downstream relation (`same_component`, `chaining`) is computed fresh from `orbit_masks` at query time in this codebase (`incidence_components` rebuilds from scratch every call, confirmed two rounds ago) rather than cached, so the *state* (from which the forest is rebuilt) is the actual requirement, not a separate cached forest object |
| **component partition** | represented via `r1_target_hub_distance`, `r2_source_hub_distance`, `r2_target_hub_distance` (BFS distances to the `("h",hub)` node) and `r2_meet_is_hub` (an LCA-type coordinate) | **must remain** — these are the fields Round 20 cites as *structurally* (not merely separatingly) necessary for `same_component`, per its own explicit correction of the greedy-minimal-subset trap (§ "결과 3", below) |
| **R1/R2 relation** | `r1_source_orbit, r1_target_orbit, r2_source_orbit, r2_target_orbit` (orbit-transported) plus `r1_macro_index, r2_macro_index` (left-`S6`-invariant) | **must remain** — `chaining` is *defined* as `r1_target_orbit == r2_source_orbit`; this is not an empirical correlation to potentially drop, it is the literal definition |
| **completer timing** | `hub_completer_orbit`, `hub_completer_hexagon`, `hub_completer_macro_index`, `hub_completer_kind`, `hub_completer_is_r1` | **must remain** — this is exactly the machinery `event_order_class`/`Decoration.branch` (CH1/CH2/`PRE_R_COMPLETER_EVENT_ORDER`) are built from in the newer engine; the new corpus's completer-timing values are precisely what this round's own prior analyses (R2-source-orbit, productive-R1) already show varies structurally across events |
| **hub state** | `hub_id` (hexagon-transported) plus the BFS-distance fields above | **must remain** |
| **provenance** (which repair path produced this boundary) | **not part of the existing 27-field schema at all** | **gap, addressed in §3** — this is the one feature this round's list names that the existing, proven schema does not cover |

**The Round 20 document's own warning applies with full force here,
restated because it is the single most important caution for building
any new key:** *greedy separating-minimality is not structural
minimality.* A field subset that happens to separate every boundary in a
*specific, finite* corpus (the old greedy 7-field result) does not
thereby become "the" minimal decorated state — `chaining`'s own
definition requires `r1_target_orbit`/`r2_source_orbit`, which the old
greedy subset omitted entirely. **Any field-dropping decision for the new
corpus must be justified by the field's role in a *definition* or a
*proven* relation, never merely by "removing it didn't create a
collision in this sample."**

## 3. Can repair history affect Target B continuation after identical boundary geometry?

**`CLAUDE_OBSERVATION` — open, not resolved this round, and not
assumed either way.**

The existing sufficiency argument for dropping provenance
(`decorated_key`'s own docstring, `search_rr_target_a_unified.py`: *"Two
histories reaching the identical (stable_key, r_count) pair therefore
have IDENTICAL future Target-A reachability, because every subsequent
macro edge is a pure function of the ExactState and r_count"*) is a
**deductive** claim about the *engine's* transition function — if the
post-boundary `ExactState` (plus whatever decoration is retained per §2)
is identical, the set of legal *future* macro edges is a pure function of
that state, independent of history, by construction of `extend()` (which
takes only `state` and a `move`, never a history object). **This part is
not corpus-specific — it follows from the transition function's own
signature, which has not changed.**

**What is *not* covered by that argument:** whether two different repair
histories, having produced *bit-for-bit identical* `(state, decoration)`
pairs, could still differ in some property Target B's own continuation
search additionally consults *outside* the state-transition function —
for example, if a future Target B search were to use the R-budget
already consumed, or a hub-touch count computed differently depending on
*how many* hub-hexagon-landing edges occurred along the repair path
versus the original walk (the repair theory round already established
`hub_touch_count` is tracked as accumulated history, not re-derived
purely from the final state — a genuinely path-dependent field, by
`advance_decoration`'s own accumulation logic, `touch_count = dec.
hub_touch_count; ...; touch_count += 1`). **If `hub_touch_count` (or any
other accumulated-not-recomputed decoration field) is retained in the
key at all (§2 says it must be), then by construction it already
captures the one concrete way provenance *could* matter — a repair path
that touches the hub one extra time versus one that does not, even while
landing at an identical final state, carries a different accumulated
`hub_touch_count` and is therefore already a *different* decorated key,
not a silent collision.** So: **provenance beyond what is already folded
into the retained decoration fields is not shown to matter, and is not
assumed not to matter** — the honest position is that the *known*
path-dependent fields (`hub_touch_count`, the ordered `r_events` tuple,
`completer`) are already required to be part of the key by §2, which
is exactly what prevents two provenance-different, geometry-identical
walks from silently colliding under an under-specified key.

## 4. Exact hypotheses needed for each named theorem

**`CLAUDE_OBSERVATION`**, stating preconditions precisely rather than
assuming carryover to the new corpus:

- **`Phi=0` continuation forces `ell=5`.** Hypothesis: this is the
  sawtooth identity (`Phi` rises by 1 per literal rotation, drops by
  `(ell-5)` at each joint) applied at a state where `Phi` is *already*
  exactly 0. It requires nothing about `O`, `Ndef`, or root family — it
  is a pure arithmetic consequence of the `Phi` definition and is
  root-independent. **No re-verification against the new corpus should
  be needed for this specific identity**, but *whether any new-corpus
  boundary state actually has `Phi=0`* is itself an empirical question
  that must be checked per state, not assumed.
- **Full-segment capacity theorem** (`research/RR_TARGET_B_FULL_BLOCK_THEOREM.md`
  §1, Round 32): *"`EEEE` full-segment theorem — when `R_cap=1`, the only
  preserving word of a capacity-5 segment is `EEEE`."* **Explicit
  precondition: `R_cap = 1` exactly**, plus (for the converse direction)
  an unquoted "distinct-hexagon condition" (§10 of that document, not
  re-read this round) requiring the relevant five ports/hexagons to be
  mutually unvisited. **For the new short_ell0-derived corpus, `R_cap`
  at a boundary is `n_limit - Ndef(boundary)`** — but `research/
  RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md` (Round 41) already established
  `Ndef_cap`/`n_limit` is itself a **disabled**, Q2-only/Area-A-scope
  restriction in the Target-A-safe profile that found these new
  boundaries. **If `n_limit` is not enforced, `R_cap=1` is not
  guaranteed, or even well-defined in the old sense, for a new-corpus
  boundary — this precondition must be checked explicitly per boundary,
  not assumed from the old corpus's scope.**
- **Existing-orbit entry capacity `≤4`** (Round 32, restated in
  `research/RR_SHORT_ROOT_DEFECT_THEOREM.md` §2): an `R`-entry into an
  orbit that already holds one used port has capacity at most 4 (a tax
  of 1 relative to a fresh `EEEE`). **Precondition: the target orbit must
  already have exactly the "one used port" configuration the proof
  assumes** — the proof's own witness (§2 of that document) is "orbit 0,
  entry phase 1, 1 port already used." A new-corpus boundary reached via
  a repair edge could enter an orbit with a *different* occupancy profile
  (per this round's own repair-theory document, R1-target's exported
  component already spans 8 hexagons with only 10 total incidences —
  i.e. mostly single-occupancy, but not proven uniformly so for every
  orbit a new boundary might involve). **Must be re-checked per orbit
  occupancy, not assumed `≤4` universally.**
- **Helper-free exact macro DFS.** Hypothesis set, stated because no
  single "the theorem" exists here — this names an *engineering*
  approach (a plain exhaustive traversal consulting none of the audited
  capacity helpers), not a mathematical claim: (a) its own prune set must
  be Target-A/B-safe in the same sense Round 41 established for
  `search_rr_target_a_exhaustive.py` (no Q2-only reason applied as a
  traversal-level prune when the goal is boundary/coverage-style
  reachability); (b) it must be deterministic and checkpointable, exactly
  as the existing state-key audit pattern requires, so its results can be
  independently re-verified rather than trusted from a single run; (c) it
  terminates within an affordable node budget — a claim about resources,
  not provable in the abstract, and not assumed here.

## 5. Why the old known-18 closure may not transfer

**`CLAUDE_OBSERVATION`**, the most load-bearing finding of this
document:

The old known-18/2,234-boundary corpus (`RR_TARGET_A_SOURCE_UNIVERSE.md`,
`RR_DECORATED_BOUNDARY_STATE.md`) and its capacity-theorem-based
Target-B closure were built and verified **entirely within the old
Area-A scope**: `O ≤ 25`, `Ndef ≤ n_limit(=3)`, and the coarse capacity
theorem's own arithmetic (`bound_1 = 5·(O_cap+R_cap)+4`, `O_cap =
TARGET_O - O`, `R_cap = n_limit - Ndef`) implicitly assumes `O_cap` and
`R_cap` are **non-negative** — a fact that was always true under the old,
enforced `O≤25`/`Ndef≤3` scope, and is *not* automatically true once
those caps are lifted.

Two independent findings from this session's own prior rounds establish
that the new short_ell0-derived boundaries were found **precisely by
disabling those caps**: `research/RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md`
(Round 41) retires `O_exceeded` and `Ndef_cap`/`N_exceeded_monotone` from
the Target-A-safe traversal profile as Q2-only/Area-A-scope artifacts,
and `outputs/rr_short_ell0_v3_frontier_export.json`'s own 85-state
frontier (already read, two rounds ago) shows `O` reaching **34** —
already 9 past the old cap — well before any R2 event, with `Ndef`
staying at the small values `{0,1}` only because these particular states
happen not to have exercised a third R (not because anything enforces
it). **A boundary found via this profile could, in principle, have
`O>25` (`O_cap<0`) at exactly the moment the coarse capacity theorem is
applied to it — an input regime the theorem's proof, as read, was never
checked against.** This is not a claim the theorem is *false* outside
that regime — only that its proof, as available in this repository, does
not cover it, and applying it anyway without re-derivation would be
exactly the kind of unstated-precondition violation Round 38's capacity-
helper firewall was built to catch in a different, related context.

**Concretely, the closure basis may fail to transfer for any of these
independent reasons, and each should be checked, not assumed, for every
new boundary:**

1. `O_cap` or `R_cap` negative at the boundary (possible now that the
   caps producing these boundaries are themselves disabled).
2. The full-segment theorem's `R_cap=1` precondition (§4) not holding —
   short roots require `k=2` R events, not `k=1`, so the *root-level*
   `R_cap` accounting this repository's own Round 37 envelope theorem
   uses (`k=1` for long-excursion roots, `k=2` for short roots) already
   differs structurally between the two corpora.
3. The re-entry-capacity-`≤4` witness orbit's specific occupancy profile
   (§4) not matching whatever orbit a new boundary's continuation would
   need to enter.
4. The decorated-key tie-triviality (§1) being corpus-specific, not
   general — a new boundary could have a nontrivial stabilizer the old
   corpus never exhibited.

## 6. Checklist: duplicate, symmetry-equivalent, resource-collision, or genuinely new

**`CLAUDE_PROPOSAL`** — a decision procedure, not itself a proof, built
directly from §§1-2's proven machinery:

```
for each newly reported Target A boundary B:
  1. Compute raw_state_hash(B) and canonical_state_hash(B) via
     exact.canonicalize (the one proven symmetry, section 1).
     -> if canonical_state_hash(B) matches an EXISTING known boundary's
        canonical_state_hash EXACTLY:
          compute canonical_decorated_hash(B) (the decorated-pair
          canonicalization, section 1) and compare against the existing
          entry's stored value too.
          -> both match:            classify EXACT_DUPLICATE
          -> state matches, decoration differs:
                                     classify PROVED_SYMMETRY_EQUIVALENT
                                     only if the specific transporting
                                     alpha and the resulting decoration
                                     mapping are exhibited and checked
                                     against section 2's required-field
                                     list -- an unexplained decoration
                                     mismatch must NOT be silently
                                     resolved as equivalence
  2. If canonical_state_hash(B) is new: compute the coarse resource
     profile (P, O, F, H, Ndef, D) and section 2's required decoration
     fields.
     -> if this EXACT (P,O,F,H,Ndef,D,decoration) tuple already exists
        among known boundaries but the raw/canonical state hash differs:
                                     classify RESOURCE_PROFILE_COLLISION_ONLY
                                     -- explicitly NOT evidence of
                                     equivalence; record it and move on,
                                     do not merge
     -> otherwise:                  classify GENUINELY_NEW_CLASS
  3. For any GENUINELY_NEW_CLASS boundary, before applying ANY existing
     capacity theorem from section 4:
       - verify O_cap >= 0 and R_cap >= 0 explicitly (section 5.1)
       - verify which k (1 or 2) applies and confirms against the
         boundary's own root-family record (section 5.2)
       - verify the specific orbit-occupancy precondition each theorem
         needs, per-orbit, not assumed (section 5.3)
     A theorem applied without these three checks passing is not a
     closure -- it is an unverified extrapolation, and must be labeled
     as such if used at all.
```

## What this document does not do

- Does not confirm, use, or analyze the cited 38,406-hit figure — it is
  unverified from this session (§0).
- Does not claim any new short_ell0-derived boundary is closed, open,
  duplicate, or novel — no boundary data exists in this session to apply
  the checklist to.
- Does not re-derive any theorem from scratch — every theorem cited in
  §4 is quoted from an already-existing, already-graded document, with
  its precondition stated, not re-proven.
- Runs no search, edits no Codex file.

CLAUDE_TARGET_B_FRAMEWORK_READY
