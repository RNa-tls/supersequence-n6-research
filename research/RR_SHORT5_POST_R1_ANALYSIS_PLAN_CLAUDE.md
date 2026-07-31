# Post-R1 analysis framework for the corrected short-root pilot (Claude, planning only)

## 0. Role, scope, and a verification note

This is a **planning document**, not an analysis of results — no post-R1
data exists yet in this repository for the five short roots
(`short_ell0`..`short_ell4`) as of this writing. It specifies the schema,
metrics, and provably-sound prune candidates that a corrected post-R1
traversal (Codex's pilot) should be measured against, so that once real
post-R1 data lands, analysis can start immediately without a design
round-trip. No new search is run here. No file produced by Codex is read,
inferred beyond its stated scope, or modified.

**`CLAUDE_OBSERVATION` — verification note on the cited commit.** The
assigning message names `d8600b9` as the "검증된 Codex 수정 커밋"
(verified Codex fix commit). I checked for it directly: `git log --all`
in this checkout does not contain it, and the GitHub API
(`get_commit`, `search_commits`) returns no match for `d8600b9` on either
branch of `rna-tls/supersequence-n6-research` (`main` or
`claude/n6-supersequence-length-rn17wf`) — a 422 "No commit found for
SHA" on direct lookup, 0 results on search. I cannot independently confirm
`CODEX_VERIFIED` status from anything visible to this session. This is
reported as a scope correction, not a refusal: the framework below is
written to be **source-agnostic** — it specifies what a corrected pilot's
output must contain to be analyzable, not a reaction to any specific
commit's diff, so it remains valid whether or not `d8600b9` resolves to a
real commit. If a different identifier or a different repository is
intended, that would need to be supplied for me to inspect the actual fix.

## 1. What "post-R1" means here, precisely

Per `RR_SHORT5_FRONTIER_ANALYSIS_CLAUDE.md` §5 (prior deliverable, not
revised here): the five short roots start at `r_count=0` and a Target A
boundary requires exactly `k=2` R events. "Post-R1" denotes any reachable
state with `r_count=1`, i.e. a state reached immediately after (or any
number of `Z2`/`Z3` edges past) the *first* R-kind macro edge taken from
one of these roots. "R2" denotes the second R-kind edge, which — by
Target A's own recognizer (`is_target_a_edge`, unchanged, `r_count_before
== 1` required) — is the only edge that can ever be a Target A boundary
from these roots.

## 2. Required decoration schema — `CLAUDE_PROPOSAL`

Two decoration questions are distinguished, because they have different
proof obligations:

### 2a. What is *sufficient for correctness* — **correction applied**

**`CLAUDE_OBSERVATION`, correcting §2a of the version of this document as
first published.** The original text called `decorated_key`'s sufficiency
claim "already proven." That overstates what is actually established.
`decorated_key`'s docstring (`search_rr_target_a_unified.py` lines
303-319) gives a deductive *argument* — every subsequent macro edge and
the recognizer are pure functions of `ExactState` and `r_count` alone —
but this document has not independently re-derived that argument from the
engine's own transition-function signature, and the only thing actually
exercised against it is the **tested universe**: the states this
engine's own test suite and the 33-root coverage run have actually
visited (`tests/test_rr_target_a_unified.py`'s determinism test,
`decorated_key_hash`'s use as the dedup key across the Round 36 coverage
run). **The correct grade is exhaustive tested-universe equivalence, not
a universal proof** — it holds for every state this repository has
actually enumerated and checked, which is a real and useful guarantee,
but is not the same claim as "holds for every reachable state, proven."
**This document does not propose adding anything to `(state, r_count)`
for correctness** — that conclusion is unchanged — but the *reason* given
for it is now stated at its correct strength.

### 2b. What is needed for *this analysis specifically* — `CLAUDE_PROPOSAL`

The state+`r_count` pair does **not** retain R1's own identity (which
literal edge was R1, its source/target orbit and phase, at what depth it
fired) — only its cumulative effect on `orbit_masks`/`Ndef`/`M` survives.
Recovering "which edge was R1" from a bare state is not possible in
general (the same `orbit_masks` bit-pattern can arise from different
edge orders). To answer §3's questions at all, the corrected pilot's
post-R1 output record needs these fields, **in addition to** whatever
`decorated_key` already requires:

| field | type | meaning | feeds |
|---|---|---|---|
| `r1_depth` | int | depth (edge count from root) at which R1 fired | distance metrics |
| `r1_source_orbit`, `r1_source_phase` | int, int | `ORBIT_PHASE[pre.p]` at the moment R1 fired (`pre` = state just before R1's joint) | R1 target orbit/phase distribution |
| `r1_target_orbit`, `r1_target_phase` | int, int | `ORBIT_PHASE[tr.target]` for R1's joint | R1 target orbit/phase distribution |
| `r1_joint_label` | str | e.g. `"w3:xyz"` | R1 target orbit/phase distribution (cross-check) |
| `r1_ell` | int | rotation-run length of R1's macro edge (`edge.run.ell`) | Phi/M-at-R1 (needed to reconstruct the pre-joint Phi, since Phi drops by `ell-5` at the joint — see §3.5) |
| `hub_popcount_at_r1_minus` | int | hub hexagon popcount **immediately before** R1's joint fires | hub-completion timing (§3.4) |
| `hub_popcount_at_r1_plus` | int | hub hexagon popcount **immediately after** R1's joint fires | hub-completion timing (§3.4) — these two together detect "R1 itself completed the hub" |
| `hub_complete_relative_to_r1` | enum: `before_r1`, `at_r1`, `after_r1_pending` | derived from the two fields above (`before_r1` if `hub_popcount_at_r1_minus==6`; `at_r1` if `hub_popcount_at_r1_minus<6` and `hub_popcount_at_r1_plus==6`; else `after_r1_pending`) | §3.3, §3.4 |
| `Phi_at_r1`, `M_at_r1` | int, int | `Phi`/`M` of the state immediately after R1's joint | §3.5 |
| `Ndef_at_r1` | int | should equal `Ndef(root) + 1` exactly for every one of these five roots (§4, Candidate 1) — recorded to *check* that identity empirically, not assumed | §4 Candidate 1's counterexample request |
| every subsequent state along the walk, tagged with `steps_since_r1` | int | edge count since R1 (0 at R1 itself) | §3.6 (distance to completer), §3.7 (R2 predecessor geometry), §3.8 (dead-end motifs) |

None of this is required for the search to be *correct* (§2a already
covers that) — it is required only so that a human or later automated
pass can answer §3's questions without re-deriving R1's identity from
scratch for every record. If Codex's pilot already logs something
equivalent under different field names, this table should be read as "the
information must be present," not as a literal naming mandate.

## 3. Focus-area metric definitions

### 3.1 R1 target orbit distribution — `CLAUDE_OBSERVATION` (method) / no data yet

Histogram of `r1_target_orbit` across all post-R1 states reached (or,
more precisely, across all *distinct R1 edges taken from the root*, since
many post-R1 states can descend from the same R1 edge — the natural unit
here is "one row per distinct R1 edge actually fired," not "one row per
post-R1 frontier state," to avoid double-counting a single R1 choice
by however many `Z2`/`Z3` continuations follow it). Two orbits are
already known to be open at the root (`O=2`): the hub orbit (orbit of the
walk's starting position) and the orbit reached by the root's own `w2:10`
abandonment landing. **An `R`-kind edge requires landing in an
already-open orbit with an unoccupied phase** (`new_orbit=False`,
enforced by the engine's own `AssertionError` guard against reusing an
occupied phase — see `superperm_partial_f1.py` lines 240-245). At the
literal root, only these same 2 orbits are open, so if R1 fires as the
very *first* macro edge (depth 1), its target orbit is necessarily one of
these 2 — but the pre-R checkpoint (§0 of the prior document) cannot
confirm whether R1 ever fires that early, because it never reaches
`r_count=1` at all. This is exactly what "do not infer beyond stated
scope" (§7) forbids extrapolating — the true distribution can only come
from Codex's corrected pilot.

### 3.2 R1 target phase distribution — same method as 3.1

Histogram of `r1_target_phase` (0..4). No prune or theorem constrains this
a priori beyond phase ∈ {0..4} and "not already occupied in that orbit" —
recorded as an open empirical question for the pilot.

### 3.3 CH1 vs. CH2 emergence — `CLAUDE_OBSERVATION` (a candidate third case) — **correction applied: CH0 is provisional**

The existing CH1/CH2 dichotomy (`RR_CH1_CH2_EXTENSION_SEARCH.md` §1) was
defined for the 22 long-excursion roots, where the root already carries
`r_count=1` and the hub hexagon is *always* incomplete at the root
(popcount 1-5, proven, never 6): **CH1** = hub completer edge `C` is
itself the first R event (there, R1 itself); **CH2** = `C` is a `Z2` and
R1 already happened. For the five short roots this taxonomy does not
obviously cover the observed data: the prior document (§7 of
`RR_SHORT5_FRONTIER_ANALYSIS_CLAUDE.md`) already found ~2.1% of the
*pre-R1* frontier sample reaches hub popcount 6 with **zero** R events
fired — a case the CH1/CH2 split as originally worded has no label for,
since it presupposes R1 has already happened.

**Correcting the version of this document as first published:** that
section previously called this a "genuine third case" and asserted three
"exhaustive, mutually exclusive" cases outright. That is not yet
established. **`CH0` is provisional until the exact event-order relation
to CH1/CH2 is settled** — specifically, §3.3's own open task below (task
1 of the current round) is to determine *whether* CH0 is truly a
structurally distinct third class or is instead a **degenerate/limiting
case of CH2**. A plausible alternative reading: CH2's own definition ("C
is a `Z2` and R1 happened earlier") could be read as implicitly requiring
R1 to precede `C`; if instead CH2 is more naturally understood as "the
hub completer `C` is a `Z2` edge, and R1's position relative to `C` is
otherwise unconstrained," then a hub-complete-before-R1 walk is just a
CH2 instance where `C` happens to precede R1 rather than follow it — not
a new class at all. This document does not decide between these two
readings; it only names the observation (`hub_complete_relative_to_r1 ==
before_r1`) precisely enough to let the actual event order in real data
decide. Pending that determination, the table below is a **provisional
partition of the observation space**, not a claim about the true
structural taxonomy:

| provisional case | condition | status |
|---|---|---|
| **CH0** (provisional label) | hub hexagon reaches popcount 6 before R1 fires at all | open: third class, or CH2 subtype? (task 1 below) |
| **CH1** | `hub_complete_relative_to_r1 == at_r1` | unaffected by this correction |
| **CH2** | hub reaches popcount 6 strictly after R1, via a `Z2` edge | unaffected by this correction |

This is offered as a **naming proposal** for the pilot's output
categories, not a claim about which case dominates, and — after this
correction — not a claim that CH0 is structurally distinct at all. That
determination is exactly what
the pilot is for.

### 3.4 Hub completion before/after R1 — method

Directly `hub_complete_relative_to_r1` (§2b) plus, for `after_r1_pending`
records, the `steps_since_r1` value at the point popcount first reaches 6
(if it ever does before the record's own frontier boundary). Aggregate as
a histogram over `{before_r1, at_r1, after_r1_within_N_steps for small N,
never_observed_yet}`.

### 3.5 Phi and M at first R — method, plus one exact identity to check

`Phi_at_r1` and `M_at_r1` (§2b) should satisfy two identities that are
**already proven** in prior rounds and are recorded here only as
*checks* the pilot's output can be validated against, not as new claims:

- `M_at_r1 = M(root) + (contribution of every Z2/Z3 edge before R1,
  each +1 or -4 respectively, per the Round 37 conservation law) + 1`
  (the `+1` is R1's own contribution, since `R` has the same `(dP,dO) =
  (+1,0)` as `Z2` — see `analyze_rr_root_capacity_envelopes.py`'s
  conservation table).
- `Phi` drops by exactly `(r1_ell - 5)` at the R1 joint itself (sawtooth
  identity, `RR_SHORT5_FRONTIER_ANALYSIS_CLAUDE.md` §8, itself citing
  `SHORTFALL_BUDGET_THEOREM.md` §2) and is otherwise flat across `rot^5`
  edges — so `Phi_at_r1` is fully reconstructible from the pre-R1 path's
  rotation-run lengths plus `r1_ell`. A mismatch between the pilot's
  reported `Phi_at_r1` and this reconstruction would indicate either a
  logging bug in the pilot or (more interestingly) a genuine edge case
  these earlier rounds' sawtooth argument did not anticipate — either way
  worth flagging, not silently trusting one side.

### 3.6 Distance from R1 to potential completer — method, no lower bound claimed

Define `distance_to_completer := steps_since_r1` at whichever event is
being called "the completer" — this is ambiguous until §3.3's CH0/CH1/CH2
label is known for the record in question (for CH0 the completer precedes
R1, so this distance is undefined/negative and should be recorded
separately, not coerced to 0). **No provable nonzero lower bound on this
distance is asserted here.** I attempted to derive one (is R2 able to
fire literally immediately after R1, zero `Z2`/`Z3` edges between them?)
and could not complete a confident case analysis over the exact move
table (`ALL_MOVES`, `ORBIT_PHASE`) in this pass without either running
code beyond the existing checkpoints (which would risk exactly the
"duplicate search" this role is told to avoid) or asserting something
unverified. This is recorded as an open question for the pilot's raw
data to answer empirically, not as a proven bound — see §4 for why this
means no prune is proposed on this basis.

### 3.7 R2 predecessor geometry — method, with one proven monotonicity fact

`R2`'s own recognizer test (`is_target_a_edge`) needs the *pre-R2* state's
current orbit and R2's target orbit to lie in the same
`component_forest` component. One fact about that forest is fully general
and worth stating precisely, because it shapes how "R2 predecessor
geometry" should be tracked: — `CLAUDE_OBSERVATION`, verified directly
against the engine's mutation code —

**Component membership is monotone non-decreasing along any walk.**
`component_forest` is built purely from `orbit_masks` bits (one union
per set bit, orbit-node to hexagon-node of that visited port — see
`search_rr_target_a_unified.py` lines 281-300). `orbit_masks` bits are
only ever set, never cleared, by the engine (`om[q] |= 1 << phase`,
`superperm_partial_f1.py` line 245 — an `OR`-assignment, and the
preceding `if om[q] & (1 << phase): raise AssertionError(...)` guard
actively forbids the alternative of re-setting an already-set bit, let
alone clearing one). Consequently the induced partition of
`{orbits} ∪ {hexagons}` into components can only **coarsen** — merge,
never split — as the walk proceeds; any two nodes in the same component
at some point remain so forever after.

This means "the first step at which R2's eventual source and target
orbit become same-component" is a well-defined, monotone event for any
fixed target orbit, and the pilot's raw per-state `orbit_masks` (already
part of the state serialization) is sufficient to compute it in
post-processing — no extra decoration is needed for this specific metric
beyond what §2a already guarantees. Recorded as an observation to guide
*how* to compute R2 predecessor geometry, not as a prune (see §4 for why
the natural-seeming prune direction from this fact does not go through).

### 3.8 Recurring post-R1 dead-end motifs — method, no claims yet

No post-R1 data exists to characterize a "recurring" motif from. The
pre-R1 dead-end motif already identified (`R_event_not_eligible_r_count`,
prior document §4) is, by construction, only observable at `r_count=0`
states and cannot recur post-R1 in the same form (an R-kind edge from an
`r_count=1` state is *always* eligible to be checked by
`is_target_a_edge`, never rejected on `r_count` grounds alone — the
rejection there is `r_count_before != 1`, which is false once `r_count=1`).
Recommended tracking for the pilot: histogram `pruned_by_reason` exactly
as the pre-R1 engine already does (§3 of the prior document), separately
for `r_count=0` and `r_count=1` sub-populations, plus a specific new
bucket for `different_components` / `source_or_target_orbit_not_in_forest`
(the two `is_target_a_edge` near-miss reasons that can only ever fire
post-R1, since they require `r_count_before==1`) — those two are the
actual candidate "post-R1 dead-end motif," and are worth histogramming
by `(r1_target_orbit, steps_since_r1)` once real data exists, to see
whether near-misses cluster around particular R1 choices.

## 4. Safe prune candidates

### Candidate 1 — post-R1 `Ndef` ceiling refinement

**`CLAUDE_PROPOSAL`:** for any post-R1 (`r_count==1`) state reached from
a short root, if `Ndef(state) >= n_limit` (i.e. `Ndef >= 3`, since
`AREA_A.n_limit == 3`), no Target A boundary reachable from that state
lies within the disclosed Area-A scope, and the state (and its entire
subtree) may be pruned exactly as `N_exceeded_monotone` already prunes
`Ndef > n_limit` — this tightens the threshold by exactly 1 at
`r_count==1` states specifically.

**`CLAUDE_HAND_PROOF`:**

1. An `R`-kind edge has `(dS, dF, dO) = (1, 0, 0)` — weight `>=3` gives
   `dS=1`; `R`'s own `joint_kind` definition (`(3, False, False)`) fixes
   `dF=0` (not abandonment) and `dO=0` (not a new orbit, that is what
   "re-entry" means). By the existing, already-proven identity
   `dNdef = dS + dF - dO` (stated and used identically in
   `N_exceeded_monotone`'s `monotone_proof` and in the Round 37 envelope
   theorem's derivation), `dNdef = 1 + 0 - 0 = +1` **exactly** for any
   `R`-kind edge — not a bound, an exact identity, already established.
2. From a post-R1 (`r_count==1`) state, Target A's own recognizer
   requires the boundary edge to be exactly the *second* R
   (`is_target_a_edge`, `r_count_before == 1` required) — so exactly one
   more R event, and no more (`r_count_exceeded` already forbids a
   third), lies between any post-R1 state and any Target A boundary
   reachable from it. No `Z2`/`Z3` edge changes `Ndef` (established:
   `dNdef=0` for both in the Round 37 conservation table).
3. Combining (1) and (2): `Ndef(boundary_child) = Ndef(current_state) + 1`
   **exactly**, for every Target A boundary reachable from a post-R1
   state — the identical "`+k` exactly" argument the Round 37 envelope
   theorem already uses for `Ndef(boundary) = Ndef(root) + k`, here
   specialized to `k=1` from a post-R1 vantage point instead of from the
   root.
4. `N_exceeded_monotone`'s own disclosed scope requires
   `Ndef(boundary_child) <= n_limit`. Substituting (3):
   `Ndef(current_state) + 1 <= n_limit`, i.e.
   `Ndef(current_state) <= n_limit - 1`. Contrapositive:
   `Ndef(current_state) >= n_limit` (i.e. `>= 3`) certifies no
   Area-A-scope Target A boundary is reachable from that state — QED.

**Exact scope:** applies only to states with `r_count == 1` reached from a
root with `root_r_count == 0` (i.e. the five short roots specifically —
for a long-excursion root, which already starts at `r_count=1`, this
candidate does not apply as stated, since there `r_count==1` *is* the
root's own starting condition and the relevant threshold is the
unmodified `Ndef(root) <= n_limit - 1`, already covered by existing
theorems, not a new claim). Requires Area-A scope (`n_limit=3`) to hold,
exactly as `N_exceeded_monotone` already requires.

**Required decoration:** `r_count` and `Ndef`, both already present in
every existing frontier record (`ExactState.Ndef`, `decorated_key`'s
`r_count`) — no new field needed for this specific prune (distinct from
the analysis-only fields in §2b).

**Honesty check before recommending this be wired in:** for these five
specific short roots, `Ndef(root) = 0` (uniformly, §1 of the prior
document) and only `R`-kind edges move `Ndef`. Since post-R1
(`r_count=1`), pre-R2 states have had *exactly one* R event fire
(`Ndef = 0 + 1 = 1`) and cannot have a second until R2 itself (which is
the boundary, not a state to prune), **`Ndef` is expected to be pinned at
exactly `1` throughout the entire post-R1, pre-R2 region reachable from
these five roots** — well below the `>= 3` threshold. **This candidate is
therefore expected to be correct but vacuous for the short-root family as
currently scoped** — it would never actually fire here. It is still
recorded (rather than discarded) for two reasons: it documents a genuine,
generally-applicable Q1-safe refinement other roots could use, and its
predicted vacuity here is itself a checkable claim (see the
counterexample request below) — if it turns out NOT vacuous, that would
mean `Ndef` moves somewhere this argument did not anticipate, which would
be a more important finding than the prune itself.

**Minimal counterexample search request for Codex:** among all
`r_count==1` records the corrected pilot actually generates from the five
short roots, report the distribution of `Ndef`. Expected: `{1: <all of
them>}`. Any record with `Ndef != 1` at `r_count==1` is either evidence
this prune is not vacuous after all (if `Ndef >= 3`, worth flagging
immediately) or evidence of an engine/decoration bug (if `Ndef` is
anything other than 0 or 1, since only 0 R events or exactly 1 R event
should be possible in that population). This is a single aggregate
histogram over data the pilot is already producing — not a new search.

### Candidate 2 — same-component monotonicity: considered, not proposed as a prune

The monotonicity fact in §3.7 (components only coarsen) is tempting to
read as a prune ("if X and Y aren't in the same component yet, prune"),
but that direction is **unsound**: monotonicity means components can
still merge *later* via further `Z2`/`Z3`/`R` edges, so "not yet
same-component" is never a valid impossibility certificate — it is
exactly backwards from what a sound prune needs. I could not find a
sound prune in the other direction either (a lower bound on *how many*
further edges are needed to force a merge) within this pass, without
either running new code against live states (outside this role's scope)
or asserting an unverified claim about the specific hexagon/orbit
adjacency structure. **No prune is proposed here** — per the assigning
instruction ("only propose a new prune if you can provide a hand proof of
soundness"), the correct response to an incomplete proof is to not
propose it, not to propose it anyway with a hedge. The monotonicity fact
itself is retained in §3.7 as a genuine, fully-proven `CLAUDE_OBSERVATION`
because it is still useful for *computing* R2 predecessor geometry
correctly, even though it does not yield a prune.

## 5. What this document does not do

- It does not analyze any actual post-R1 data — none exists in this
  repository's checkpoints as of this writing (the prior document's §5
  established that the pre-R1 checkpoints contain zero `r_count>0`
  states).
- It does not confirm or deny `CODEX_VERIFIED` status for commit
  `d8600b9` — see §0; that commit could not be located by this session.
- It does not infer R1 target-orbit/phase distributions, CH0/CH1/CH2
  proportions, hub-completion timing proportions, or dead-end-motif
  frequencies from the pre-R1 checkpoint — every one of §3's questions is
  left as an open empirical question for the corrected pilot, exactly as
  instructed ("do not infer anything from the old pre-R checkpoint beyond
  its stated scope").
- It does not implement Candidate 1 anywhere in this repository, and does
  not implement (because it does not propose) any prune under
  Candidate 2.
- It does not modify any Codex traversal code or checkpoint file, and
  runs no search of its own.

CLAUDE_POST_R1_PLAN_READY
