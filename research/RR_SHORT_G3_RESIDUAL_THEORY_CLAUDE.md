# G3 residual theory — the 24 residual families and the already-merged mechanisms

작성자: Claude
role: independent verification analyst / theory derivation. No search run.

---

## 0. Artifact status — read this before using any number in this document

**Every Round-62 artifact cited in the task request is confirmed
nonexistent in this repository.** Checked with `git fetch --all --prune`
(no new branches; Codex tip is still
`codex/round-r1-37-hex82-t4` @ `1f9efff0809c47e7ca1857ed6c7734c20e78f081`,
Round 61), then by direct existence check against the worktree and the
Codex tip, and then by searching **every ref and all reachable history**:

| cited artifact | worktree | codex tip | any ref, any commit |
|---|---|---|---|
| `research/RR_SHORT_113_FAMILY_G3_CODEX.md` | absent | absent | absent |
| `outputs/rr_short_113_family_status.json` | absent | absent | absent |
| `outputs/rr_short_113_family_residuals.json` | absent | absent | absent |
| `outputs/rr_short_113_family_mechanisms.json` | absent | absent | absent |
| `outputs/rr_short_113_family_g3_verified.json` | absent | absent | absent |
| `research/RR_SHORT_Z2_MERGER_USEFULNESS_CODEX.md` | absent | absent | absent |
| `research/RR_SHORT_T4_A3_EXCEPTIONAL_ROUTES_CODEX.md` | absent | absent | absent |
| `research/RR_SHORT_T4_A3_OPEN_W2_REACHABILITY_CODEX.md` | absent | absent | absent |
| `research/RR_SHORT_TOP8_G2_FINALIZATION_CODEX.md` | absent | absent | absent |
| `research/RR_SHORT_T4_TEMPLATE_GENERALIZATION_CODEX.md` | absent | absent | absent |

The mechanism vocabulary itself (`MERGED_BY_R`, `MERGED_BY_Z2`,
`SEPARATE_MONOTONE_BLOCKED`, `SEPARATE_CLEAR`) returns **zero** matches
across all refs.

Consequence for this document:

- Every **count** in the task request (439 / 326 / 113 / 89 / 16 / 8 / 24 /
  1,818 / 1,183 / 612 / 16 / 7 / "exactly 3 Target-A, all known-18") is
  treated as an **UNVERIFIED PREMISE**, labeled `[UP]`, and is never used
  as a proof input. The counts are internally arithmetically consistent
  (326+89=415; 439−415=24; 89+16+8+0=113; 1183+612+16+7=1818), which is
  mildly reassuring but is not evidence that the underlying corpus exists.
- Everything this document states as **proved** is derived instead from
  **committed engine source** that does exist and that I read directly
  this round — principally
  `src/search_rr_target_a_exhaustive.py` on the Codex tip
  (`target_a_recognizer`, `incidence_components`, `advance_decoration`,
  `evaluate_edge`) plus this project's own already-verified T4/VNTS
  results. Those derivations are unaffected by the missing Round-62 data,
  because they are statements about the **recognizer and the transition
  semantics**, not about any particular corpus.

This is the same pattern seen in Rounds 59, 60 and 61, where cited
commits were confirmed nonexistent at check time and became real later.
When Round 62 lands, sections 6, 7 and 8 below are the ones that need the
data re-run against them; sections 2, 3, 4, 5, 9, 10 and 11 should survive
unchanged.

### A naming collision that must be fixed before it propagates

The task uses **G2** and **G3** as *RR-short program milestones* ("G2 has
been achieved for the top-8 ledger; G3 has not"). But `G2` already has a
different, committed, canonical meaning in this repository:
`legacy_research/outputs/SUPERPERMUTATION_RESEARCH_RECORD_KO.md` §6 is
titled *"`F=0` full-cassette 가지: G2"* — the F=0 full-cassette theorem
(`F=0 => H>=6 => L>=873`), recorded as such in
`research/SUPERPERMUTATION_N6_MASTER_STATUS.md` §4.7 only one commit ago.
There is no `G1` or `G3` anywhere in the repository.

These are two unrelated things sharing one symbol. This document uses
**G3(milestone)** and **G2(milestone)** explicitly whenever the program
milestone is meant, and reserves bare `G2` for the F=0 theorem. Codex
should pick a distinct milestone prefix (e.g. `M2`/`M3`, or
`LEDGER-G2`/`LEDGER-G3`) before this collision reaches a certificate.

---

## 1. What is actually verifiable, and what this document is built on

Committed and read directly this round (all on the Codex tip
`1f9efff`, file `src/search_rr_target_a_exhaustive.py`):

- `target_a_recognizer` (line 690) — the exact Target-A boundary predicate.
- `incidence_components` (line 348) — the union-find over `orbit_masks`.
- `advance_decoration` (line ~390) — `hub_touch_count` maintenance.
- `evaluate_edge` (line 815) — R1/R2 dispatch and pruning.
- The Target-A prune registry (line ~280) — including the committed
  `hub_touch_count` lemma entry.

Already-verified this session and reused: the T4 theorem for
`short_ell2_r1_37` (`research/RR_SHORT_ELL2_R1_37_T4_FINAL_VERIFICATION_CLAUDE.md`,
`CLAUDE_T4_VERIFIED`) and the generic VNTS template
(`research/RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md`).

**The exact Target-A predicate.** From `target_a_recognizer`, Target A
holds iff **all six** of the following hold (the function computes
`target = all(conditions.values())` over exactly this dict):

| # | condition | source expression |
|---|---|---|
| 1 | `exactly_two_R_events` | `before.r_count == 1 and after.r_count == 2` |
| 2 | `immediately_after_R2` | `joint_kind(w, abandonment, new_orbit) == "R"` |
| 3 | `F_def_equals_1` | `transition.state.F == 1` |
| 4 | `H_equals_0` | `transition.state.H == 0` |
| 5 | `hub_touch_count_le_2` | `after.hub_touch_count <= 2` |
| 6 | `same_component` | `find(("q",sq)) == find(("q",tq))` |

where `sq = ORBIT_PHASE[joint_source_state.p]` (the **literal joint
source** after the rotation run — the Round-48 correction, §11), and
`tq = ORBIT_PHASE[transition.target]`.

Note `same_component` relates the **R2 source orbit** to the **R2 target
orbit**. It is *not*, by definition, a statement about "C_R1 and C_H".
`chaining` (`r1.target_orbit == sq`) is computed separately and is
explicitly **not** an acceptance condition. This distinction matters
throughout §3-§5 and is a place where informal descriptions of the
residual mechanisms could easily drift from what the engine actually
tests.

---

## 2. The exact logical gap to G3(milestone)

The four levels the task asks to separate, stated precisely:

- **(A) observed-anchor classification.** For each frozen anchor in the
  residual corpus, a mechanism label is assigned. Evidence type: `[EC]`
  over the anchor set — a finite, complete classification *of the anchors
  that exist in the frozen set*.
- **(B) observed-descendant closure.** For the descendants actually
  expanded within the search budget, no Target-A boundary outside the
  known-18 classes appears. Evidence type: `[BO]` — bounded. This is what
  a capped F7/F8 family currently supplies.
- **(C) complete descendant-mechanism classification.** For **every** legal
  descendant of every residual anchor — not merely the expanded ones —
  the mechanism label lies in the finite known set
  `{MR, MZ, SM, SC}` (or the descendant is dead/at R2). Evidence type:
  must be `[HP]` or `[EC]`; cannot be reached by more expansion.
- **(D) family-level closure.** For every residual family: no legal
  descendant yields a Target-A boundary that is not left-`S6`-equivalent
  to a known-18 class (and hence already Target-B-closed).

**The minimum missing implication for G3(milestone) is (B) ⇒ (D), and it
does not hold on its own.** Bounded absence of a witness is not absence.
The gap is bridged only by inserting (C) plus a per-mechanism closure
theorem:

```
(A) anchor classification            [EC, have it, per UP]
 +  (C) descendant-mechanism closure  [MISSING — needs a theorem]
 +  per-mechanism Target-A theorem    [MISSING for MR and MZ]
 ------------------------------------------------------------
 => (D) family-level closure = G3(milestone)
```

So G3(milestone) needs exactly two things, and neither is more search:

1. **A closure theorem for the mechanism transition system** — every legal
   descendant of a residual anchor stays inside `{MR, MZ, SM, SC}` until
   it dies or fires R2 (§9 shows most of this is already provable).
2. **A per-mechanism Target-A theorem** for `MR` and `MZ` — that every
   Target-A boundary reachable under that mechanism is known-18
   equivalent (§3, §4: not proved here, and the precise missing step is
   identified).

`SM` and `SC` need (1) only, if §7's hereditary argument is completed.

---

## 3. MERGED_BY_R theory

### 3.1 What "already merged" provably implies

**Lemma M1 (component monotonicity; merger is irreversible).**
`[CLAUDE_HAND_PROOF]`

`incidence_components(state)` rebuilds the partition from scratch, unioning
`("q", orbit)` with `("h", hexagon_id(port))` for **every set phase bit of
`state.orbit_masks`** and nothing else. `orbit_masks` bits are only ever
set, never cleared (same add-only argument as the `hex_masks` monotonicity
verified in the T4 round; `extend` performs `om[q] |= 1 << phase`). A
union-find whose edge set only grows can only coarsen its partition.

Therefore: if two nodes lie in the same incidence component at state `S`,
they lie in the same component at **every** legal descendant of `S`. A
merger can never be undone.

**Theorem M2 (component-separation arguments are structurally dead in
merged families).** `[CLAUDE_HAND_PROOF]`

Let `F` be a family in which the R1-target component and the hub component
are already merged at the anchor. By M1 they remain merged in every
descendant. Condition 6 (`same_component`) of the Target-A predicate is
then satisfied for **every** pair of orbits both lying in that merged
component, at every descendant.

Consequently no T4-style argument can close such a family. T4 works by
proving `same_component` unreachable (via VNTS: the merging incidence can
never be registered). In a merged family that incidence is *already*
registered, so the argument has no hypothesis to apply. This **proves**,
rather than assumes, the task's premise that "ordinary T4 is inapplicable"
— and it also shows the failure is structural, not a matter of finding a
cleverer T4 variant.

Read against the generic template: `MERGED_BY_R` is exactly the class
where hypothesis **D3** of `RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` §5a
(`Phi(q_R1) ∩ H_hub = ∅`) **fails at R1 itself**. The T4 template's own
§6 counterexample for dropping D3 predicted precisely this family: "if
some hexagon `h*` belonged to both sets, registering `q_R1`'s own phase in
`h*` ... unions `C_R1` with the hub component in a single move." The
residual corpus is that counterexample realized, not a surprise.

### 3.2 The residual obstruction set — what is left to constrain

**Theorem M3 (residual obstruction set for merged families).**
`[CLAUDE_HAND_PROOF]`

In a merged family, the only Target-A obstructions that can still bind are
conditions 1-5 of §1's table:

```
exactly_two_R_events  ∧  immediately_after_R2  ∧
F_def == 1  ∧  H == 0  ∧  hub_touch_count <= 2
```

This list is exhaustive because `target_a_recognizer` accepts iff all six
named conditions hold, and condition 6 is discharged by M2.

This is the correct pivot for MR theory: **the question is no longer "can
the components connect" but "can a legal R2 fire at all, with the resource
coordinates intact."** Three of the five are hard budget facts:

- `r_count` must go exactly `1 → 2`. `evaluate_edge` (line 837) shows an
  `R` edge at `r_count == 1` is evaluated as the R2 boundary and is
  **never enqueued** (registry test
  `test_long_root_r2_is_recognized_on_edge_and_never_enqueued`). So R2 is
  terminal: there is exactly one R2 attempt per descent path, at whatever
  state the path happens to be in when an `R` joint fires.
- `F == 1` and `H == 0` are the standing regime constraints
  (`TARGET_F = 1`).
- `hub_touch_count <= 2` is a monotone budget — see M6 (§7).

### 3.3 The MR-Theorem: not proved, and exactly what is missing

The task asks whether an R1-created merger can generate a genuinely **new**
Target-A boundary, ideally proving:

> *MR-Theorem (target).* Every legal R1-merged descendant reaching Target A
> is left-`S6`-equivalent to a known-18 boundary.

**I do not state this as a theorem. It is not proved here, and it cannot
be proved from what is committed.** Marking it: `[CONJECTURE]`.

What blocks it is a genuine mathematical gap, not just the missing data.
By M2 the component condition gives no leverage at all in this regime, so
any MR-Theorem proof must come **entirely** from constraining the R2
source/target orbit pair `(sq, tq)` and the resource coordinates. The
precise missing step is:

> **Missing step (MR).** Characterize the set
> `S_MR = { (sq, sph, tq, tph) : reachable as a literal R2 joint from some
> R1-merged descendant, with F=1, H=0, hub_touch_count<=2 }`
> and show every element of `S_MR` yields a boundary state in a known-18
> left-`S6` class.

Two properties make this plausibly finite and therefore attackable without
a continuation search:

1. `tq` must be an **already-open** orbit (`R` has `new_orbit=False`), and
   `sq` is the orbit of the literal joint source. Both are drawn from the
   finite registered set.
2. By M1 the merged component only grows, so `S_MR` is *monotone* in the
   descent — which means it can be over-approximated safely (§10) rather
   than enumerated exactly.

That over-approximation is the recommended attack, and is why §12 ranks
the MR theorem first.

---

## 4. MERGED_BY_Z2 theory

Structurally, `MERGED_BY_Z2` differs from `MERGED_BY_R` **only in how the
merger arose** — by a later legal `Z2` rather than by R1 itself. M1, M2 and
M3 apply verbatim: the merger is equally irreversible, condition 6 is
equally discharged, and the residual obstruction set is identical.

The reported reduction `[UP]` (612 literal witnesses → 8 exact post-Z2
states → all 8 immediate R2 → 6 fail by wrong source orbit → 2 reach
Target A → both known-18) has a very specific shape worth naming: it says
the *observed* post-merger behaviour collapses to a tiny finite set, and
that the discriminating condition is **the source orbit**, exactly as M3
predicts (component is free; the source orbit is what bites).

**What would make that descendant-complete.** The reduction is currently
(B)-level. It becomes (D)-level given either:

- **(Z2-a) A post-merger normal-form theorem.** Show the map
  `descendant ↦ (component-relation, sq, sph, tq, tph, F, H, r_count,
  hub_touch_count)` has image of size 8 over all legal post-Z2
  descendants, not merely the observed ones. By M4 (§10) this tuple is
  *exactly* what the recognizer reads, so bounding its image bounds every
  Target-A outcome. **This is the strongest available route** and it is
  the one I recommend to Codex.
- **(Z2-b) A second-merger impossibility.** Show any *distinct* second Z2
  merger requires a predecessor that VNTS (or the same-hexagon occupancy
  argument) forbids. This is the natural place to reuse the existing
  cross-hexagon VNTS machinery, since a merger requires registering a
  specific phase whose unique weight-2 predecessor may already be visited
  and non-terminal.

Note (Z2-a) is *not* a coarse quotient of the kind this project has
repeatedly found unsafe (§11): it does not claim continuation equivalence,
only that the recognizer-relevant projection has bounded image — a
strictly weaker and safely checkable claim.

---

## 5. Unification: "already-connected-before-R2"

**Yes — MR and MZ are the same concept**, and M1-M3 prove it: both are
instances of

> **already-connected-before-R2**: the R2 source and target orbits lie in a
> common incidence component at the moment the R2 joint fires,
> irrespective of which earlier event created that connection.

Because M1 makes connection irreversible and M2 makes it inevitable
thereafter, the *provenance* of the merger (R1 vs. a later Z2) has **no
effect whatsoever on the Target-A predicate**. The predicate cannot see
history; it recomputes `incidence_components` fresh from `orbit_masks`
(the docstring is explicit: *"Fresh union-find from ExactState; no history
summary is trusted"*).

**Post-merger Target-A normal form (proposed, partially proved).**

> Once the R2 source and target orbits are co-component before R2, the only
> remaining freedom relevant to Target A is the literal R2 source
> orbit/phase together with the resource coordinates
> `(F, H, r_count, hub_touch_count)`.

The "only remaining freedom" half is **proved** (M3 + M4). The half that
would make it a closure tool — that the admissible source set is *finite
and branch-independent* — is **not proved** and I decline to assert it;
branch-independence in particular looks doubtful, since `sq` ranges over
whatever orbits a given branch has actually opened, which is branch
history. The defensible version is **mechanism-dependent and
family-finite**, which is exactly (Z2-a).

I have deliberately **not** created a separate
`RR_SHORT_POST_MERGER_NORMAL_FORM_CLAUDE.md`: the result is one theorem
plus one open half, it lives naturally here, and this project has just
finished endorsing consolidation over file proliferation. It should be
split out only once the finite-image half is actually proved.

---

## 6. The 3 observed Target-A boundaries — why "3/3 known-18" must not be promoted

`[UP]` — the three boundaries themselves are not inspectable; the residual
corpus does not exist in any ref.

What can be said rigorously: there are at least four candidate
explanations, and the current evidence **cannot distinguish them**:

| candidate explanation | would it generalize? | how to test it |
|---|---|---|
| coincidence of the bounded corpus | no | expand the corpus; a 4th, non-known-18 boundary refutes universality outright |
| consequence of terminal normal form | yes, if the normal-form result is itself proved | check whether each of the 3 is forced by the terminal normal form alone |
| consequence of R2 source geometry | yes — this is the M3 route | compute `S_MR`/`S_MZ` and check known-18 membership as a *set* statement |
| consequence of component ancestry | partially | ancestry is invisible to the recognizer (M1/M5), so this can only act via which orbits got opened |

**Do not promote 3/3 to universality.** Three data points is exactly the
regime in which this project has been burned before: the parity conjecture
family (master status §5.1) held over *far* larger observed samples and was
still false, and the failure mode was identical — a bounded corpus that
structurally could not contain the counterexample. The honest reading of
"3/3 known-18" is: *consistent with* the R2-source-geometry explanation,
and therefore a reason to attempt the M3-route proof — not evidence for
it.

---

## 7. The 16 SEPARATE_MONOTONE_BLOCKED anchors

`[UP]` for the count; the hereditary machinery below is `[CLAUDE_HAND_PROOF]`.

**Theorem M6 (hub-touch hereditary death).** `[CLAUDE_HAND_PROOF]`

`advance_decoration` updates the hub counter only as

```python
if core.hexagon_id(transition.target) == dec.hub_id:
    touch_count += 1
```

— strictly monotone non-decreasing, with no decrement path anywhere in the
module (the project's own prune registry records this as the committed
lemma *"with F <= 1, no hexagon can be a joint target more than twice"*,
scope `universally_safe_under_F_le_1`, regression test
`test_hub_touch_counter_is_monotone`). `evaluate_edge` refuses to produce a
child whenever the count would exceed 2 (lines 831-832 on the R1 path,
849-850 otherwise), and Target-A condition 5 requires `<= 2`.

Therefore `hub_touch_count > 2` is **hereditarily Target-A-dead**: no
descendant of such a state can ever be a Target-A boundary, and the
engine will not even generate the subtree.

This is a genuine hereditary closure device, and it is exactly the shape
needed for `SEPARATE_MONOTONE_BLOCKED`. **What it does not yet give** is
closure of those 16 anchors, because "monotone blocked" as a mechanism
label presumably refers to occupancy-monotone blocking (the T2a-style
full-hexagon collision argument) rather than the hub counter. The
completing step is:

> **Missing step (SM).** Show the blocking quantity for these anchors is
> monotone in the same add-only sense as `hex_masks`/`orbit_masks`/
> `hub_touch_count`, and that the blocked predicate is *upward closed*
> under it. Given that, hereditary closure is immediate by the same
> one-line induction as M1.

If the blocking quantity is occupancy, this is very likely to go through —
occupancy monotonicity is already proved and independently replayed over
1,325,308 macro edges in the T4 round. **16 anchors is small enough that
this should be settled by hand, not by search.**

---

## 8. The 7 SEPARATE_CLEAR anchors

`[UP]`, and **the per-anchor analysis the task requests (exact state, legal
Z2/Z3/R candidates, orbit/phase/hex targets, predecessor structure,
resource coordinates) cannot be performed**: the anchors are not in any
committed artifact. I will not fabricate seven state descriptions.

What is provable now is the *shape* of the transition theorem, which is
worth having in advance:

**Theorem M7 (SC transition dichotomy — partial).** `[CLAUDE_HAND_PROOF]`
for the enumerated cases; `[CONJECTURE]` for exhaustiveness.

Consider a legal macro edge out of a `SEPARATE_CLEAR` state (components not
yet connected). By `evaluate_edge` and `joint_kind`, the edge is exactly
one of:

- **`R` with `r_count == 1`** → evaluated immediately as the R2 boundary,
  terminal, never enqueued → lands in `R2`.
- **`R` with `r_count >= 2`** → `rr_R_budget_exceeded` → `DEAD`.
- **`Z2`** → may register a phase that connects the two components →
  `MZ` if it connects, otherwise still separate.
- **`Z3`** → opens a fresh orbit; connects only if the fresh orbit's
  registered phase-hexagon already lies in the other component (this is
  precisely a *component-changing Z3*) → `MZ`-like if it connects,
  otherwise still separate.
- **any edge exceeding a budget** (`hub_touch_count > 2`, R budget, prune
  profile) → `DEAD`.

So every SC successor is in `{SC, MZ, R2, DEAD}` **plus** whatever the
still-separate successors are classified as (`SC` or `SM`). Note SC can
**never** transition to `MR`: `MR` is defined by R1 having created the
merger, and R1 is already in the past for every post-R1 state. That
asymmetry is provable and worth recording.

The genuinely open half is the task's clause (a): *"remains in the finite
clear set"* — finiteness of the clear set is not established, and is the
whole content of a real closure theorem.

---

## 9. Residual mechanism transition graph

Nodes: `MR`, `MZ`, `SM`, `SC`, `R2` (terminal), `DEAD`.

```
                 (R at r_count=1)
   SC ─────────────────────────────────────────────▶ R2
    │  │                                              ▲
    │  │ (Z2/Z3 that connects components)             │
    │  └──────────────────────▶ MZ ───────────────────┤
    │                           │ ▲                   │
    │ (occupancy-blocked)       │ └──(stays merged)   │
    ▼                           │                     │
   SM ──────────────────────────┼─────────────────────┤
    │                           │                     │
    │                     MR ───┘ (stays merged)      │
    │                      │                          │
    └──────────────┬───────┴──────────────────────────┘
                   ▼
                 DEAD   (budget: R>2, hub_touch>2, prune, collision)
```

Edge-by-edge status:

| edge | status | ground |
|---|---|---|
| `MR → MR`, `MZ → MZ` (merged stays merged) | **PROVED** | M1 (union-find only coarsens) |
| `MR ↛ SC`, `MR ↛ SM`, `MZ ↛ SC`, `MZ ↛ SM` (no un-merging) | **PROVED** | M1 |
| `SC ↛ MR` (cannot become R1-merged post-R1) | **PROVED** | R1 is in the past; `MR` is defined by R1's own registration |
| `SC → R2`, `MR → R2`, `MZ → R2`, `SM → R2` | **PROVED** possible | `evaluate_edge` line 837: any `R` at `r_count==1` is evaluated as R2 |
| `* → DEAD` | **PROVED** possible | budget guards, lines 831/844-850 |
| `SC → MZ` | **PROVED** possible | a connecting `Z2`/component-changing `Z3` is a legal edge shape |
| `SC → SM`, `SC → SC` | **OBSERVED** | depends on the (uncommitted) `SM` definition |
| **no fifth mechanism exists** | **CONJECTURED** | this is the (C)-level gap of §2; "0 other residual families" is an observation on the current corpus, not a closure proof |

**Is the graph closed?** The *merged half* is provably closed and
absorbing (M1). The *separate half* is closed **only up to** the
conjectured non-existence of a fifth mechanism. So:

> G3(milestone) reduces to finitely checking the R2 exits **iff** the
> fifth-mechanism conjecture is discharged.

That reduction is real and is the single most valuable thing in this
document: it converts G3 from "search more" into "prove one closure
statement, then check finitely many R2 exits."

---

## 10. A finite-state quotient — and a *sound* one-sided simulation

This project has repeatedly been burned by unsafe quotients (the lossy
J-branch fingerprint; the retracted 144-Z3 orbit-pigeonhole, §11). So I
give a quotient only with a soundness proof, and I give the *one-sided*
version because it is what impossibility arguments actually need.

**Theorem M4 (the Target-A predicate is `hex_masks`-blind).**
`[CLAUDE_HAND_PROOF]`

Reading `target_a_recognizer` line by line, the predicate's inputs are
exactly: `before.r_count`, `after.r_count`, the firing transition's
`joint_kind`, `transition.state.F`, `transition.state.H`,
`after.hub_touch_count`, `joint_source_state.p`, `transition.target`, and
`incidence_components(joint_source_state)` — which by its own definition
reads **only** `state.orbit_masks`. The recognizer **never reads
`hex_masks`**.

Define the projection

```
Ω(state, dec) = (orbit_masks, p, F, H, r_count, hub_touch_count)
```

**Corollary M5 (sound one-sided simulation for impossibility).**
`[CLAUDE_HAND_PROOF]`

Legality of an exact transition is *conjunctive*: it requires the no-repeat
`hex_masks` guard **and** the orbit/resource conditions. Dropping the
`hex_masks` guard therefore only ever **adds** transitions. Hence the image
of every legal exact descent is a legal Ω-descent, so

```
{ Target-A boundaries exact-reachable from anchor A }
      ⊆  { Target-A boundaries Ω-reachable from Ω(A) }
```

Consequently: **if an Ω-search from a residual anchor finds no Target-A
boundary, then no exact descendant of that anchor has one.** This is a
sound impossibility certificate.

The converse fails and must never be used: an Ω-reachable Target-A
boundary is **not** evidence of an exact one, because the dropped
no-repeat guard may be exactly what forbids it. Ω is usable for closing
families, never for claiming witnesses.

Why this is practically valuable for G3: Ω discards the 720-bit occupancy
vector — the dominant part of the exact state and the reason the F7/F8
families cap out. An Ω-search explores a far smaller space, and by M5 a
negative Ω-result is a *proof*, not an observation. This is the concrete
mechanism by which capped families can be upgraded from (B) to (D)
without a larger exact search.

Residual caution: Ω still carries `orbit_masks` (144×5 bits), so Ω is not
automatically finite-tractable. It is monotone, though (M1), which is
what makes fixed-point/closure computation over it plausible. I have
**not** verified tractability and do not claim it.

---

## 11. Invalidated-machinery audit

Explicit audit of this document against the master status §5 list:

| invalidated item | used here? | note |
|---|---|---|
| old parity / `k>=1` claims | **no** | cited in §6 only as a cautionary precedent about small samples, never as an inference |
| v1 short-root R-child completeness | **no** | §3.2/§8 use the *corrected* asymmetric rule (`r_count==0` enqueues R1; `r_count==1` is terminal R2), read from the current `evaluate_edge` |
| v2 Target-A `O>25` prune | **no** | `area_a_prune_reason` appears in `target_a_recognizer` at line 723 but is explicitly marked *"intentionally diagnostic only"* and is **not** among the six acceptance conditions; this document uses only the six |
| macro-entry R2 source semantics | **no** | §1 uses the literal joint source; the recognizer itself now rejects untagged states (`R2_LITERAL_JOINT_SOURCE_TAG`) |
| `true_phase_walk_capacity` outside full-segment scope | **no** | not used anywhere in this document |
| stale v6 provenance assumptions | **no** | no v6 checkpoint field is relied on |
| 144-Z3 naive pigeonhole | **no** | §10 deliberately proves its quotient's soundness rather than assuming an orbit-count bound; this is the direct lesson of that retraction |

One further self-imposed constraint: §5 declines to assert
branch-independence of the admissible source set, and §6 declines to
promote 3/3 — both are exactly the kind of step that produced the
retracted results above.

---

## 12. The next Codex target, ranked by expected payoff

1. **`MZ` post-merger finite-image theorem (Z2-a) — highest payoff, most
   tractable.** Prove that over *all* legal post-Z2-merger descendants the
   Ω-projection of §10 has image exactly the 8 observed post-Z2 states
   (or any finite set), then check the Target-A predicate on that finite
   set. By M4 this is sufficient — the recognizer reads nothing else.
   Closes 8 families. Concretely: *compute the forward Ω-closure from the
   8 post-merger states under all legal joints and show it is finite and
   contains no new Target-A boundary.*
2. **`MR` source-set theorem (§3.3's missing step).** Characterize `S_MR`
   — the reachable literal R2 `(sq,sph,tq,tph)` tuples under
   `F=1, H=0, hub_touch<=2` — and show each yields a known-18 class.
   Largest mechanism (1,183 anchors `[UP]`) so highest value, but harder
   because M2 removes all component leverage. **Attack it via the Ω
   over-approximation of M5, not by exact continuation.**
3. **`SM` hereditary-monotonicity lemma (§7's missing step).** 16 anchors;
   should be a hand proof, one induction, reusing the already-verified
   occupancy monotonicity. Cheapest item on the list.
4. **`SC` finite-clear-set theorem (§8).** Needs the 7 states published
   first; the transition dichotomy M7 is already laid out, so the only
   open half is finiteness of the clear set.
5. **Fifth-mechanism non-existence (§9).** The formal (C)-level gap.
   Possibly falls out of 1-4 rather than needing separate work.

**Explicitly not recommended:** deeper continuation search on the F7/F8
families. By §2, more expansion moves evidence within level (B) and can
never by itself reach (D).

**And first, before any of the above:** push the Round-62 artifacts. None
of the ten cited files exists in any ref, so items 1-4 currently cannot be
checked by anyone.

---

## 13. Proposed master-status patch note (NOT yet applied)

Prepared but **deliberately not written into**
`research/SUPERPERMUTATION_N6_MASTER_STATUS.md`, because every figure in
it is `[UP]` and the master document's own source-of-truth policy forbids
recording unverifiable counts. Apply verbatim once the Round-62 artifacts
land and the counts are recomputed from them:

```markdown
### Corrected-v5 RR-short child ledger (Round 62) — PENDING VERIFICATION

- 439 children total
- 326 exact exhausted
- 113 nonempty families, of which 89 T4-closed
- 415 / 439 currently handled (326 + 89)
- 24 residual families, containing 1,818 frozen anchors, decomposing into
  exactly four mechanisms:
  MERGED_BY_R = 1,183 · MERGED_BY_Z2 = 612 ·
  SEPARATE_MONOTONE_BLOCKED = 16 · SEPARATE_CLEAR = 7
- 3 Target-A boundaries observed in the residual corpus, all known-18,
  all helper-free Target-B closed  [BO — bounded corpus, not universal]
- G2(milestone) achieved for the designated top-8 corrected-v5 ledger
- G3(milestone) NOT achieved: descendant completeness unproved for the
  capped F7/F8 families (see RR_SHORT_G3_RESIDUAL_THEORY_CLAUDE.md §2)
- NOTE: "G2/G3" here are RR-short program milestones and collide with the
  committed meaning of G2 (the F=0 full-cassette theorem, master status
  §4.7). Rename before this reaches a certificate.
```

No historical certificate was modified by this round.

---

## Summary of proof-status labels used

| label | meaning |
|---|---|
| `[CLAUDE_HAND_PROOF]` | derived here from committed engine source; M1, M2, M3, M4, M5, M6, M7(partial) |
| `[CONJECTURE]` | plausible, explicitly not proved; MR-Theorem, fifth-mechanism non-existence, SC finiteness |
| `[UP]` | unverified premise from the task request; every Round-62 count |
| `[BO]` | bounded observation; the 3/3 known-18 result |

## End token

`CLAUDE_G3_THEORY_PARTIAL`
