# Target A coverage: two different questions, two different answers

Round 35. Sections 1–3, 13, 15, 16. Sources
`src/build_rr_target_a_roots.py`, `src/search_rr_target_a_exhaustive.py`,
`src/verify_rr_target_a_coverage.py`.

## 0. The distinction that decides the round

Round 34 closed Target B for all 18 known Target A boundaries, so the
bottleneck moved to completeness of the boundary list. The brief asked to
decide the 22 INCOMPLETE long-prefix roots exactly. Attempting that forced a
split that had not been made before:

| | question | capacity bound usable? | answer |
|---|---|---|---|
| **Q1** | is there **any** Target A boundary beyond this root? | **no** | 22/22 `INCOMPLETE` |
| **Q2** | is there a Target A boundary from which an Area-A NR6 completion is **still possible**? | **yes** | 22/22 `EXHAUSTED_NO_TARGET_A` |

Target A is a **local** predicate on one macro edge — second R event,
`F_def=1`, `H=0`, same-component. It does not require the word to complete.
Round 30 already proved six Target A boundaries have no continuation at all
and remain Target A. So a completability prune is not a Target A prune, and
`verify_rr_target_a_coverage.py` check 1 confirms this is not hypothetical:
on one of the ell=0 `P_core=4` known boundaries the capacity slack is
already **−2** at the state its R2 edge departs from. Using the bound for
Q1 would have deleted that genuine boundary. Grade for the bound as a Q1
prune: **반증됨**. As a Q2 prune: **safe capacity bound**.

## 1. The frozen recognizer (§3)

`TARGET_A_SPEC`, SHA-256 recorded in every output. Required: R-event joint
(weight 3, no abandonment, no new orbit); the **second** R of the word; child
`F_def = 1`; child `H = 0`; R2 source and target orbits in the same component
of the orbit/hexagon forest built from the **pre-joint** `orbit_masks`; child
passes `area_a_prune_reason(·, AREA_A)`.

Recorded but **not** required: chaining, abandonment ell, hub completer
geometry, child `Ndef` (always 2, since an R costs one N), child Φ.
Deliberately excluded: every Target B and Target C condition, and the
capacity bound.

Validation (§15): all **12/12** known short boundaries replay from their
recorded preparations and are re-recognized by the frozen recognizer.
Counting unit: boundary **states**, `P_core = preparation_length − 2`.

## 2. The 22 roots, fixed (§1) and quotiented (§2)

| quotient level | classes among the 22 |
|---|---|
| exact state | **22** |
| left-S6 canonical state | **22** |
| decorated continuation state | **22** |
| resource signature `(P,F,S,H,O,D,Ndef,Φ)` | **8** |
| symbolic excursion class | **3** (`L7_exp3_FFEFEFR`, `L8_exp1_FFFFEFFR`, `L8_exp1_FFFEFFFR`) |

No two roots are identified by any state-level quotient — the left-S6 action
collapses nothing here — so all 22 had to be decided individually. The
resource signature collapses them to 8 classes, which is exactly the
`(ell, L)` grid: Φ = **ell + 1** at every root, `Ndef = 1`, `F_def = 1`,
one R already spent.

## 3. Result (§13)

**Q2 — completable Target A: 22/22 `EXHAUSTED_NO_TARGET_A`, every frontier
emptied naturally, 0 boundaries found.** No node cap and no depth ceiling
was in force; `frontier_emptied_naturally` is true at all 22.

* 14 roots are decided **without any search**: the capacity bound is already
  negative at the root (slack −2, −3, −7, −11).
* 8 roots are decided **by exhaustive search**: 2, 2, 25, 25, 242, 248,
  10,335, 10,389 nodes expanded. Slack at these roots is 1, 1, 2, 2, 6, 6,
  10, 10, and slack is non-increasing, which is what makes them finite.

Sanity check that the bound is not simply deleting everything: **none of the
6 FOUND roots is killed by it**, asserted in the builder.

**Q1 — Target A coverage without the completability assumption: 22/22
`INCOMPLETE`.** Mean branching is 2.50–2.57 with no useful safe prune
available, so the frontier grows without bound; ~13,600–18,800 nodes were
expanded per root before the budget ran out. Grade: **bounded incomplete**.

Grades: **root-local exhaustive** for Q2 over the stated 22-root class;
**bounded incomplete** for Q1.

## 4. Section 16 outcome: **C**

Not A: A requires every root exhausted for the unconditional question, and
Q1 is incomplete at all 22. Not B: no new Target A boundary was found, so
the §14 pipeline (witness → quotient comparison → capacity theorem →
phase/R-reuse refinement → Round 34 flow solver) never fired; it is
implemented and recorded as untriggered.

`root-local exhaustive` is therefore claimed **only for Q2**.

## 5. What this adds to the RR picture

Combined with Round 34, for the 22 long-prefix roots:

> no Target A boundary reachable from them can extend to Target B or
> Target C, because none of them can even reach `P = TARGET_P`.

That is what the `L_6 ≥ 872` argument needs from these roots. It is **not**
Target A coverage, and this round does not claim it is. Five coverage gaps
remain open — see `RR_BRANCH_CLOSURE_SCOPE.md`, including two that were
identified for the first time this round.

`L_6 ≤ 872` verified here, `L_6 ≥ 867` proved, `L_6 ≥ 872` open. Unchanged.
