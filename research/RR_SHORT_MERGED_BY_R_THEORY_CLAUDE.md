# MERGED_BY_R: theory for R1-created mergers

작성자: Claude
role: independent theory derivation. No search run.

Artifact status: the Round-62 residual corpus remains **absent from every
ref** (re-checked this round; Codex tip still `1f9efff`, Round 61). All
counts from the task request — including `MERGED_BY_R = 1,183` — are
**unverified premises** `[UP]` and are used nowhere as proof inputs.
Everything proved below comes from committed engine source:
`legacy_research/work/superperm_partial_f1.py::extend` and
`src/search_rr_target_a_exhaustive.py` (`joint_kind`,
`incidence_components`, `advance_decoration`, `target_a_recognizer`,
`evaluate_edge`).

---

## 1. What remains relevant once component equality is "already guaranteed"

**It is not guaranteed — and this is the round's main correction.**

`target_a_recognizer` computes

```python
sq, sph = exact.ORBIT_PHASE[joint_source_state.p]
tq, tph = exact.ORBIT_PHASE[transition.target]
same_component = find(("q", sq)) == find(("q", tq))
```

`same_component` relates the **R2 source orbit** `sq` to the **R2 target
orbit** `tq`. It is *not*, by definition, a statement that "C_R1 and C_H
are merged". A merger of C_R1 with C_H makes `same_component` automatic
**only for source/target pairs both lying inside that merged component**.

So the residual information after an R1-created merger is exactly:

1. **Whether the walk is *positioned* in a qualifying orbit when it fires
   R2.** `sq = ORBIT_PHASE[p]`, so this is a constraint on the literal
   position `p` at the R2 joint source (after the rotation run — the
   Round-48 literal-source semantics).
2. **Whether `tq` is co-component with that `sq`.**
3. The resource coordinates: `r_count` must go exactly 1→2, `F == 1`,
   `H == 0`, `hub_touch_count <= 2`.

This sharpens — and partially corrects — my own prior statement in
`RR_SHORT_G3_RESIDUAL_THEORY_CLAUDE.md` §3 (M2). M2 was stated with the
qualifier "for every pair of orbits both lying in that merged component",
which is correct, but the surrounding prose invited the reading that
merger discharges condition 6 outright. It does not. The corrected claim
is M2′ below.

It also explains the reported `[UP]` Z2 datum — *"6 of 8 fail Target A by
wrong source orbit"* — structurally rather than coincidentally: the
component condition is the only one merger touches, and it leaves a live
source-orbit obligation behind.

## 2. Is R2 same-component automatic? — No `[HAND THEOREM]`

> **Theorem M2′.** Let `S` be a state in which orbits `a` and `b` lie in a
> common incidence component. Then in every legal descendant of `S`, `a`
> and `b` remain co-component. Consequently, if an R2 fires from source
> orbit `sq` to target orbit `tq` and **both** lie in a component that was
> already merged at `S`, condition `same_component` holds automatically.
> If either lies outside it, `same_component` is **not** implied.

*Proof.* `incidence_components` rebuilds the partition from scratch,
unioning `("q",orbit)`↔`("h",hexagon_id(port))` for every set
`orbit_masks` phase bit and nothing else. `orbit_masks` is add-only
(`extend` line 245 performs `om[q] |= 1 << phase`; no clearing operation
exists in the module). A union-find whose edge set only grows can only
coarsen its partition, so co-component is permanent. The second sentence
is immediate; the third is the observation that the theorem says nothing
about orbits outside the merged component. ∎

**Corollary (T4 is structurally dead here).** Any argument that closes a
family by proving `same_component` unreachable cannot apply once the
relevant pair is already merged — for those pairs the condition is
permanently true and there is no hypothesis left to contradict. This
proves rather than assumes the premise that ordinary T4 is inapplicable to
`MERGED_BY_R`. In the vocabulary of
`RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` §5a, `MERGED_BY_R` is exactly the
class where hypothesis **D3** (`Phi(q_R1) ∩ H_hub = ∅`) fails at R1 — the
template's own §6 dropped-hypothesis counterexample, realized.

## 3. The exact remaining source-orbit/phase conditions `[HAND THEOREM]`

Collecting §1 and the recognizer's six conditions, a post-merger Target-A
exit requires precisely:

```
r_count: 1 → 2                          (the firing joint is the R2)
kind == R                               (weight 3, non-abandoning, existing orbit)
F == 1                                  (after the transition)
H == 0                                  (automatic on live paths — see below)
hub_touch_count <= 2                    (monotone budget)
sq := ORBIT_PHASE[p_joint_source]  and  tq := ORBIT_PHASE[target]
        must be co-component at the joint source state
```

Two of these collapse:

- **`H == 0` is automatic.** Every RR-admissible joint has weight ≤ 3
  (`joint_kind` admits only `Z2`, `Z2abandon`, `R`, `Z3`; everything else
  is `"other"` → `outside_RR_joint_model`, no child), and
  `dH = max(weight−3, 0) = 0`. So `H` never changes on a live path.
- **`kind == R` forces `new_orbit == False`**, i.e. `tq` is an
  already-open orbit. So `tq` is drawn from the finite set of orbits with
  `orbit_masks[tq] != 0`.

What genuinely remains is a **joint condition on `(p, tq)`**: the walk's
literal position at the R2 joint source must lie in an orbit co-component
with the R2 target orbit.

## 4. Can those conditions be reduced to a finite table? — Partly `[HAND THEOREM]` / partly open

The conditions are *evaluable* on a finite state description: all of
`orbit_masks, p, F, r_count, hub_touch_count` are Ω-fields (see the
companion `RR_SHORT_POST_MERGER_OMEGA_CLAUDE.md`), and the recognizer
reads nothing else. So the **predicate** is a finite-table function of Ω.

What is **not** reducible to a small table is the set of Ω-states actually
reachable. Ω is finite but astronomically large (`≤ 2^720 × 720 × 2 × 3 ×
3`); the companion document proves the Ω transition relation is acyclic
with depth ≤ 720 and branching ≤ 24, so the reachable image is computable
in principle, but no bound better than "finite" is established.

**Answer:** the *conditions* reduce to a finite table; the *reachable
instances* of those conditions do not, on present evidence.

## 5. Can a genuinely new Target-A boundary arise from an R1-created merger?

**Not excluded — and the structural pressure runs toward "yes".**
`[CONJECTURE, leaning negative on the closure claim]`

By M2′ the merger *enlarges* the set of `(sq, tq)` pairs satisfying
`same_component`, and by monotonicity that set only grows further along
any descent. Every other Target-A condition is unchanged by merger. So an
R1-created merger strictly **relaxes** the Target-A predicate relative to
an unmerged branch: it can only add candidate exits, never remove them.

There is therefore no structural argument in the direction of "no new
boundary." Any such result must come from showing the *reachable*
`(sq, tq, resources)` combinations happen to be exhausted by known
classes — an enumeration fact, not a structural one.

## 6. Are all Target-A-producing states necessarily known-18? — Not proved, and I am sceptical

`[CONJECTURE — explicitly not asserted]`

The strongest candidate theorem, as posed:

> *Every legal R1-merged descendant reaching Target A is left-`S6`-equivalent
> to a known-18 boundary.*

I decline to state this. §10 records a serious falsification attempt that
I could not dismiss.

## 7. The weakest exact finite alternative

What *is* defensible, given the artifacts, is a conditional finite
statement:

> **Conditional exit-set theorem (schema).** Let `A` be a post-merger
> anchor and let `E(A)` be the set of Ω-states at which an `R`-kind joint
> fires with `r_count: 1→2`. If the terminating Ω-closure of §4 (companion
> doc §4.2) enumerates `E(A)` and every element either fails one of the
> five non-component conditions or yields a boundary in a known-18 left-`S6`
> class, then no exact descendant of `A` yields a Target-A boundary outside
> known-18.

This is sound by Ω-SOUND (one-sided): a negative or known-18-only Ω result
transfers to exact. It is **schema, not theorem** — it has no content
until `E(A)` is actually computed, which requires the artifacts.

## 8. Monotone invariants surviving after merger `[HAND THEOREM]`

Merger destroys the component-separation invariant, but **six monotone
quantities survive**, all add-only with no decrement path anywhere in the
engine:

| invariant | why monotone | Target-A use |
|---|---|---|
| `popcount(orbit_masks)` | `om[q] \|= 1<<phase`, +1 per macro edge (`extend` 232-245, assertion 240-243) | bounds path length ≤ 720; gives acyclicity |
| incidence partition (coarsening) | union-find over an add-only edge set | co-component is permanent (M2′) |
| `hex_masks` occupancy | `hm[h] \|= 1<<bit`, never cleared | underlies VNTS / no-repeat |
| `hub_touch_count` | `advance_decoration` only `+= 1` | `> 2` ⟹ hereditarily Target-A-dead |
| `F` | `dF = int(abandonment) >= 0` | `F` must be exactly 1 at R2 |
| `H` | `dH = max(w−3,0) >= 0`, and `= 0` on live paths | invariant at 0 |
| `r_count` | `+1` per `R` | budget 2, R2 terminal |

So the answer to task 8 is emphatically **yes** — merger costs the project
exactly one invariant (component separation) and leaves the rest intact.
The `hub_touch_count` one is the sharpest: it is a genuine hereditary
death certificate, since `evaluate_edge` refuses to emit a child when the
count would exceed 2 (lines 831-832, 849-850) and Target A requires ≤ 2.

## 9. The exact missing premise for descendant completeness

> **Missing premise (MR).** A complete characterisation of
> `E = { (sq, sph, tq, tph, F, hub_touch_count) : reachable as an R2 joint
> from some R1-merged descendant }`, together with the claim that every
> element of `E` either fails a non-component condition or lies in a
> known-18 left-`S6` class.

Everything else needed for descendant completeness is already proved:
soundness of the abstraction (Ω-SOUND), termination of its closure
(Ω-TERM), invariance of `H`, and the monotone budgets of §8. `E` is the
one genuinely missing object, and by §5 it cannot be obtained by a
structural shortcut — it has to be enumerated (soundly, via Ω).

## 10. Falsification attempt against my own strongest candidate

Task 10 asks me to try hard to falsify the candidate of §6. I did, and
**the attempt succeeded well enough that I will not assert the theorem.**

Three independent pressures against it:

1. **Merger relaxes, never restricts (§5).** The Target-A predicate
   post-merger is strictly weaker than pre-merger, since condition 6 is
   satisfied on a *larger* set of `(sq,tq)` pairs and monotonically grows.
   A theorem claiming "no new boundaries" therefore fights the direction
   of the structure, and would need the enumeration to accidentally come
   out empty.
2. **The evidence base is three data points `[UP]`.** "3/3 known-18" is
   the same evidential shape that produced this project's most expensive
   retraction: the preparation-parity family (master status §5.1) held
   over vastly larger observed samples and was still false, with an
   identical failure mode — a bounded corpus that structurally could not
   contain the counterexample. Here the corpus is not merely bounded, it
   is *absent from every ref*.
3. **The natural coarsening that would prove it is unsound.** The obvious
   route — quotient by the component partition and argue there are only a
   few post-merger classes — fails: `new_orbit = (om[q] == 0)`
   distinguishes "orbit `q` unopened" from "opened", while a partition in
   which `q` is a singleton does not. Two states with identical partitions
   can admit different joint kinds (`Z3` vs `R`), changing `r_count` and
   hence Target A. So the tempting proof route is closed by a genuine
   counterexample argument, not merely by lack of effort.

I could not construct an explicit exact counterexample state — that would
require the residual anchors — so this is **not** a refutation. It is a
justified refusal to assert.

## Proof-status summary

| result | status |
|---|---|
| M2′ (co-component permanent; same-component **not** automatic in general) | **HAND THEOREM** |
| T4 structurally inapplicable to MERGED_BY_R | **HAND THEOREM** |
| `H == 0` automatic on live paths; `kind==R` ⟹ `tq` already open | **HAND THEOREM** |
| conditions reduce to a finite table of Ω-fields | **HAND THEOREM** |
| six monotone invariants survive merger (§8) | **HAND THEOREM** |
| reachable instance set is small / canonical | **NOT PROVED** |
| MR-Theorem (all Target-A exits known-18) | **CONJECTURE — declined, see §10** |
| every Round-62 count | **UNVERIFIED PREMISE** |
| observed "3/3 known-18" | **BOUNDED OBSERVATION** (and unverifiable) |

## End token

`CLAUDE_MR_PARTIAL`
