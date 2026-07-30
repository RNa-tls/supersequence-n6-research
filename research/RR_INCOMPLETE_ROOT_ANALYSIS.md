# Why the Round 27 frontier exploded, and whether the 22 share a cause

Round 35, sections 4, 5, 7, 10, 12. Source `src/build_rr_target_a_roots.py`
→ `outputs/rr_22_incomplete_roots.json`.

## 1. The measurement (§4)

Per root, 4,000 nodes expanded with sound `stable_key` dedup (Round 27 used
`(stable_key, depth)`, which stratifies by depth and inflates the state
count without gaining anything — Target A recognition is state-local once
the root carries exactly one R).

| quantity | range across the 22 |
|---|---|
| mean branching | **2.49 – 2.57** |
| `Z3` fresh-opening edges | 6,453 – 6,733 (dominant event) |
| `Z2` edges | 3,484 – 3,570 |
| `R` edges evaluated as R2 candidates | 3,855 – 3,935 |
| R2 outcome `source_or_target_orbit_not_in_forest` | 3,673 – 3,736 (**~95%**) |
| R2 outcome `different_components` | 153 – 216 (**~5%**) |
| R2 outcome `TARGET_A` | **0 at all 22** |

**All 22 roots have exactly one R2-outcome cause signature.** The explosion
is not root-specific: it is the same mechanism everywhere — branching ≈ 2.5
with fresh orbit openings the majority event, and essentially every R edge
failing for the same reason.

That reason is worth naming precisely. The component forest is built from
`orbit_masks`, which records **pass-starts only**. At an R2 edge the source
orbit is `orbit(pre.p)` where `pre.p = p₀·Σ^ℓ`. For ℓ > 0 that permutation
is a port of some orbit but is *not itself* a pass-start, so its orbit is in
the forest only if some **other** port of it was opened earlier. That
coincidence is what fails 95% of the time.

Two consequences, both visible in the known corpus:
* ℓ = 0 makes the source orbit automatically present, since `pre.p = p₀` is a
  pass-start. All **9** ell=4 known boundaries use `ℓ = 0`.
* ℓ = 5 requires the coincidence. All **3** ell=0 known boundaries use
  `ℓ = 5` and get it.

## 2. Φ is exactly `ell + 1` at every root (§10)

Measured, not assumed: Φ = 1, 2, 3, 4, 5 for abandonment ell = 0, 1, 2, 3, 4,
at both the abandonment roots and the long-excursion roots (ℓ=5 edges
preserve Φ, and the excursions are all ℓ=5).

Since `ΔΦ = ℓ − 5` per macro edge and `area_a` enforces Φ ≥ 0, the total
spend over the whole extension is at most Φ. In particular the R2 edge
itself costs `5 − ℓ`, so:

| root ell | root Φ | minimum affordable R2-edge ℓ |
|---|---|---|
| 0 | 1 | **4** |
| 1 | 2 | 3 |
| 2 | 3 | 2 |
| 3 | 4 | 1 |
| 4 | 5 | **0** |

This is the exact reason the ell=4 branch can use the cheap `ℓ = 0` R2 edge
and the others cannot. It is already implied by `area_a`'s own Φ prune, so it
removes nothing new — but it explains the ell dichotomy in one line, which
previous rounds recorded only as an observation.

## 3. The capacity bound, re-imported to Φ > 0 (§5)

Round 32's (B+R) bound applied only at Φ = 0 boundaries. Re-derived here in
the pass-start currency so it applies at Φ > 0 (손증명, full statement in
`capacity_slack`):

    TARGET_P − P  ≤  (5 − used ports of the current orbit)
                     + 5·(TARGET_O − O) + 4·((n_limit − Ndef) + Φ)

The `+Φ` term is the new part and it is needed: a weight-2 joint at ℓ < 5 can
change orbit at **zero** N cost, so a re-entry is not always N-charged — but
it is always Φ-charged. (A weight-2 joint at ℓ = 5 cannot change orbit,
because `g_{w2:10} = E`; and a weight-2 joint opening a *fresh* orbit needs an
abandonment, which would push F past `TARGET_F = 1`.)

**Slack is non-increasing**, dropping by `5 − used` whenever an orbit is left
unsaturated. That monotonicity is what makes the Q2 searches finite.

Root slack: **14 of 22 are already negative** (−2, −3, −7, −11), so those
roots cannot reach `P = 121` at all. The 8 survivors have slack 1, 1, 2, 2,
6, 6, 10, 10.

**Scope, and a refutation.** The bound is a necessary condition for an Area-A
NR6 *completion*, not for a Target A boundary. Replaying it along the known
boundaries' own paths shows it reaching **−2 before the R2 edge** on one
ell=0 `P_core=4` boundary. So it is **반증됨** as a Target A prune and used
only for Q2. Reassuringly, every boundary at which it fires was already
removed as capacity-impossible in Rounds 30–32, so it agrees with the
established ledger wherever it applies.

## 4. R budget (§7)

Every one of the 22 roots has `r_count = 1`, so exactly one R remains and
that R **is** the R2 event by construction — which is why the search never
expands past an R edge (definitional for RR, 손증명). Minimum future R
events: 1. Minimum additional macro edges to Target A: 1.

**No root is removed by R counting alone.** The R-budget obstruction that
cut 186 prefixes down to 28 in an earlier round is already fully applied;
there is nothing left for it to do here. Recorded as such rather than
re-run.

## 5. Minimal ancestry decoration (§12)

The same-component test needs exactly **one boolean** per candidate edge:
do the R2 source and target orbits share a component of the forest
determined by the pre-joint `orbit_masks`? The forest is a function of the
state, so no union-find history is carried, no ancestry log is stored, and
the recognizer stays state-local. That is the whole decoration; §12 asked
for the minimum and this is it.

## 6. Reachability over-approximation (§11) — vacuous

The over-approximated port successor graph (all ℓ ∈ 0..5, all four joints,
visited-collision constraints dropped) has **out-degree 720 at all 720
nodes** — it is complete. The distance from every root's endpoint to the
completer target (1,4) is **1**. So the filter excludes nothing, and no
prune is available from it. Grade: **scope correction**. Reported because a
filter that cannot fire should be recorded as measured-and-vacuous, not
quietly dropped.
