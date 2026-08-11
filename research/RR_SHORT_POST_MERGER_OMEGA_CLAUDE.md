# Post-merger Ω-projection: soundness and termination

작성자: Claude
role: independent theory derivation. No search run.

---

## 0. Artifact status

Re-checked this round: `git fetch --all --prune` returns no new branches;
the Codex tip is still `codex/round-r1-37-hex82-t4` @
`1f9efff0809c47e7ca1857ed6c7734c20e78f081` (Round 61). The Round-62
artifacts remain **absent from every ref**, re-confirmed by direct
existence check on `rr_short_113_family_residuals.json`,
`rr_short_113_family_mechanisms.json`, `RR_SHORT_113_FAMILY_G3_CODEX.md`.

Therefore **task 5 (compute the complete post-merger Ω image from the
committed residual anchors) cannot be performed** — there are no residual
anchors in any committed artifact. Everything else in this document is
derived from committed engine source and is unaffected.

Sources read directly this round:

- `legacy_research/work/superperm_partial_f1.py::extend` (lines 213-255)
- `src/search_rr_target_a_exhaustive.py` @ `1f9efff`:
  `joint_kind` (111), `incidence_components` (348),
  `advance_decoration` (~390), `target_a_recognizer` (690),
  `evaluate_edge` (815)

---

## 1. What the exact Target-A recognizer reads

`target_a_recognizer` accepts iff all six conditions hold. Their complete
input set, read line by line:

| condition | inputs |
|---|---|
| `exactly_two_R_events` | `before.r_count`, `after.r_count` |
| `immediately_after_R2` | `joint_kind(weight, abandonment, new_orbit)` |
| `F_def_equals_1` | `transition.state.F` |
| `H_equals_0` | `transition.state.H` |
| `hub_touch_count_le_2` | `after.hub_touch_count` |
| `same_component` | `incidence_components(joint_source_state)`, `joint_source_state.p`, `transition.target` |

and `incidence_components` reads **only** `state.orbit_masks`
(docstring: *"Fresh union-find from ExactState; no history summary is
trusted"*; it unions `("q",orbit)`↔`("h",hexagon_id(port))` for every set
`orbit_masks` phase bit and nothing else).

**The recognizer never reads `hex_masks`.** `[HAND THEOREM]`

## 2. The minimal projection Ω

```
Ω(state, dec) = ( orbit_masks, p, F, r_count, hub_touch_count )
```

`H` is **droppable**, not merely small — see §4.3: every joint that
survives the RR model has weight ≤ 3, so `dH = max(weight-3, 0) = 0` and
`H` is invariant along every live path. Keeping `H` is harmless; dropping
it is justified.

Note `p` is equivalent to `ORBIT_PHASE[p]`, since `perm ↔ (orbit, phase)`
is a bijection on the 720 permutations; either encoding carries the same
information.

What Ω deliberately omits is `hex_masks` — the 720-bit occupancy vector,
i.e. the dominant part of the exact state and the reason the capped
families cap out.

## 3. Soundness: Ω is a one-sided simulation

### 3.1 The Ω transition relation

For an Ω-state and each rotation length `ℓ ∈ {0..5}` and each joint move
`m` of weight 2 or 3 (there are exactly 4 such moves: one weight-2, three
weight-3, from the committed weight distribution `{1:1, 2:1, 3:3, 4:13,
5:71, 6:461}`):

1. `target := word_after(p, rot^ℓ ∘ m)` — a function of `p` alone.
2. `(q, phase) := ORBIT_PHASE[target]`. **Reject if `orbit_masks[q]` bit
   `phase` is already set** (freshness guard — see §3.3 for why retaining
   this is sound).
3. `new_orbit := (orbit_masks[q] == 0)` — computable in Ω.
4. Infer `kind` and the forced `abandonment` (§3.2).
5. Update: `p := target`; set `orbit_masks[q]` bit `phase`;
   `F += 1` iff `kind == Z2abandon`; `r_count += 1` iff `kind == R`;
   `hub_touch_count += 1` iff `hexagon_id(target) == HUB`.
6. If `kind == R` and `r_count` was 1, this is the R2 boundary: evaluate
   the six Target-A conditions — **all of whose inputs are in Ω** (§1) —
   and terminate the path.

### 3.2 Abandonment needs no nondeterminism `[HAND THEOREM]`

This is the step that makes Ω self-contained rather than merely an
approximation with a free variable.

`joint_kind` in `search_rr_target_a_exhaustive.py` (line 111) admits
**exactly four** labels; every other `(weight, abandonment, new_orbit)`
triple maps to `"other"`, and `evaluate_edge` (line 821) returns
`outside_RR_joint_model` with **no child** for those:

| weight | abandonment | new_orbit | label | in RR model? |
|---|---|---|---|---|
| 2 | False | False | `Z2` | yes |
| 2 | True | True | `Z2abandon` | yes |
| 3 | False | False | `R` | yes |
| 3 | False | True | `Z3` | yes |
| *anything else* | | | `"other"` | **no — DEAD** |

`new_orbit` is computable in Ω (step 3). Given `weight` and `new_orbit`,
the table admits **at most one** value of `abandonment`:

- `w2, new_orbit=False` → must be `abandonment=False` (`Z2`); `True` gives
  `(2,True,False)` = A2 = `"other"` = DEAD.
- `w2, new_orbit=True` → must be `abandonment=True` (`Z2abandon`).
- `w3, new_orbit=False` → must be `abandonment=False` (`R`); `True` gives
  `(3,True,False)` = J = `"other"` = DEAD.
- `w3, new_orbit=True` → must be `abandonment=False` (`Z3`); `True` gives
  `(3,True,True)` = A3 = `"other"` = DEAD.

So Ω assumes the unique RR-legal `abandonment`. This is sound as an
over-approximation: if the true (hex_masks-determined) abandonment differs,
the exact edge is DEAD, and a DEAD edge can never reach Target A, so
admitting it in Ω only adds behaviour that cannot produce a false negative.

### 3.3 Soundness theorem `[HAND THEOREM]`

> **Theorem Ω-SOUND.** Every exact RR-legal macro transition's Ω-image is
> an Ω-transition. Hence for any anchor `A`,
> `{Target-A boundaries exact-reachable from A}` ⊆
> `{Target-A boundaries Ω-reachable from Ω(A)}`.
> **If no Ω-path from Ω(A) reaches Target A, then no exact path from A
> reaches Target A.**

*Proof.* Exact legality is a conjunction: the `extend` no-repeat guard on
`hex_masks` (line 221), the orbit-phase freshness implied by it, the
RR-model kind restriction, and the resource guards. Ω retains every
conjunct except the `hex_masks` guard, and replaces the hex-dependent
`abandonment` by the unique RR-legal value (§3.2). Removing a conjunct and
relaxing a determined value to its legal candidate can only enlarge the
transition relation. The rotation-run length is likewise relaxed: exact
runs are limited by `hex_masks`, Ω allows all `ℓ ∈ {0..5}`. So every exact
transition survives into Ω. The Target-A predicate is computed identically
in both, since by §1 it reads only Ω-visible fields. ∎

The freshness guard (step 2) is sound to **retain** because exact
semantics already guarantees it: `extend` returns `None` when
`state.visited(target)` (line 221), and since `perm ↔ (orbit, phase)` is a
bijection, an already-set `orbit_masks[q]` bit `phase` implies `target`
was already visited. The engine makes this explicit with an assertion
(lines 240-243: *"reused pass-start phase without repeated window"*).
Retaining a guard that never fires in exact semantics preserves soundness
while buying termination (§4).

**Direction warning.** The converse fails and must never be used. An
Ω-reachable Target-A boundary is **not** evidence of an exact one: the
dropped `hex_masks` guard may be exactly what forbids it. Ω closes
families; it never witnesses them.

## 4. Finiteness and termination

### 4.1 Every macro edge strictly increases `popcount(orbit_masks)` `[HAND THEOREM]`

From `extend` (lines 232-245), the `orbit_masks` update is guarded by
`if move.weight >= 2:` — so weight-1 rotation moves leave `orbit_masks`
untouched, and every joint sets `om[q] |= 1 << phase`. By the assertion at
lines 240-243 that bit was previously clear. A macro edge is a rotation
run plus exactly one joint. Therefore:

> **Theorem Ω-MONO.** Every macro edge — exact or Ω — increases
> `popcount(orbit_masks)` by exactly 1.

(Note this also shows `hex_masks` and `orbit_masks` are *not* redundant:
`hex_masks` records every visited permutation, `orbit_masks` records only
the pass-start subset, i.e. joint targets.)

### 4.2 Termination `[HAND THEOREM]`

> **Theorem Ω-TERM.** The Ω transition relation is acyclic, and every
> Ω-path from `Ω(A)` has length at most `720 − popcount(orbit_masks(A))`.
> Branching is at most `6 × 4 = 24`. Hence the Ω-closure is computable by
> a terminating DFS with memoization.

*Proof.* `orbit_masks` has `144 × 5 = 720` bits and is add-only. By Ω-MONO
each edge consumes exactly one, giving the length bound; a strictly
increasing integer forbids revisiting a state, giving acyclicity. Branching
is at most 6 rotation lengths × 4 admissible joint moves. ∎

This answers task 4 affirmatively: **yes, all legal exact transitions
induce a finite — indeed acyclic and depth-bounded — transition relation
on Ω.**

### 4.3 `H` is invariant on live paths `[HAND THEOREM]`

Every RR-admissible joint has weight ≤ 3 (§3.2 table), and
`dH = max(weight − 3, 0)`, so `dH = 0` on every live edge. `H` therefore
never changes along a path that stays in the RR model. Since `H` is
add-only and Target A requires `H == 0`, any exact edge of weight ≥ 4 is
both outside the RR model *and* permanently Target-A-fatal.

### 4.4 The honest caveat on tractability

Finite and terminating is **not** the same as tractable. `|Ω| ≤ 2^720 ×
720 × 2 × 3 × 3`. The depth bound is 720 and branching 24. Nothing here
bounds the *reachable* Ω-image by a small number, and I have **not**
computed one. Claiming otherwise would repeat this project's own history
of over-scoped quotients (master status §5).

What is genuinely bought: Ω discards the 720-bit occupancy vector while
keeping the entire Target-A predicate exactly computable, and a negative Ω
result is a **proof**, not an observation. That is the mechanism by which a
capped family can move from bounded observation to closure without a larger
exact search.

## 5. Complete post-merger Ω image — NOT COMPUTED

Blocked: no residual anchors exist in any committed artifact (§0). When
Round 62 lands, the computation is exactly the terminating DFS of §4.2
seeded at the Ω-images of the post-merger anchors, with the Target-A
predicate of §1 evaluated at every `R`-with-`r_count==1` edge.

## 6. Finite normal form for post-merger states — NOT FOUND

I did not find a normal form coarser than Ω that is provably sound. Two
candidates were considered and both rejected:

- **Drop `p`, keep only `ORBIT_PHASE[p]`.** Not a reduction — the map is a
  bijection.
- **Drop `orbit_masks`, keep only the induced component partition.** This
  is *not* sound: `new_orbit = (om[q] == 0)` distinguishes "orbit `q`
  unopened" from "orbit `q` opened", and a partition that has `q` as a
  singleton component does not determine which. Two states with identical
  component partitions can therefore admit different joint kinds (`Z3` vs
  `R`), which changes `r_count` and hence Target A. **This is a genuine
  counterexample to the most tempting coarsening**, and is exactly the
  class of unsafe quotient this project has been burned by before.

`H` is droppable (§4.3), which is a real but minor reduction.

## 7. Every post-merger Target-A exit lies in a finite canonical list — NOT PROVED

Task 7 asks to prove or refute that post-merger Target-A exits belong to a
finite list of canonical source-orbit/phase states.

**Trivially finite, non-trivially unbounded.** The set of
`(source orbit, source phase, target orbit, target phase)` tuples is finite
a priori (`720 × 720` bounded), so "finite" is not the content. The content
would be a *small, computed, branch-independent* list — and that I neither
have nor can obtain without the artifacts.

Worse, there is a structural reason for scepticism, recorded in §3 of the
companion `RR_SHORT_MERGED_BY_R_THEORY_CLAUDE.md`: merger **enlarges** the
set of `(sq, tq)` pairs satisfying `same_component`, and by monotonicity
that set only grows further. The pressure is toward *more* admissible
exits post-merger, not fewer. I therefore decline to conjecture that the
list is small.

## 8. Comparison to known-18 Target-A classes — NOT PERFORMED

Requires §5 and §7 outputs. Not attempted; no left-`S6` equivalence
computation was run.

## 9. `hex_masks` usage audit

`hex_masks` is used in exactly one place in this document: §3.3, to
establish that dropping it *enlarges* the transition relation (soundness
direction). It is not used in the projection, in the predicate, or in the
termination argument. This complies with task 9.

## 10. Proof-status separation

| result | status |
|---|---|
| recognizer is `hex_masks`-blind (§1) | **HAND THEOREM** |
| minimal Ω, `H` droppable (§2, §4.3) | **HAND THEOREM** |
| abandonment needs no nondeterminism (§3.2) | **HAND THEOREM** |
| Ω-SOUND one-sided simulation (§3.3) | **HAND THEOREM** |
| Ω-MONO: +1 orbit bit per macro edge (§4.1) | **HAND THEOREM** |
| Ω-TERM: acyclic, depth ≤ 720, branching ≤ 24 (§4.2) | **HAND THEOREM** |
| component-partition quotient is unsound (§6) | **HAND THEOREM** (counterexample argument) |
| complete post-merger Ω image (§5) | **BLOCKED — no artifacts** |
| small/canonical exit list (§7) | **NOT PROVED**; structural scepticism recorded |
| known-18 comparison (§8) | **NOT PERFORMED** |
| every count from the task request | **UNVERIFIED PREMISE** |

## Verdict

The goal — *"prove or refute that after R1/hub merger, all Target-A-relevant
future behaviour can be soundly projected to a finite quotient containing
only the fields the recognizer reads"* — is **proved in the soundness and
termination directions**: Ω exists, contains only recognizer-read fields,
is a sound one-sided simulation, and its transition relation is acyclic
with depth ≤ 720 and branching ≤ 24.

It is **not** established that the reachable image is *small*, and the
concrete image was not computed (no artifacts). Because
`CLAUDE_OMEGA_FINITE_IMAGE_PROVED` would be read as claiming a computed
finite image, and that would overclaim, the accurate token is the
soundness one — with the explicit note that termination was also proved,
which is strictly more than soundness alone.

## End token

`CLAUDE_OMEGA_SOUND_ONLY`
