# The 1,398 Round-35–37 Target-A boundaries, fully reclassified

**Author:** Claude (independent verification track)
**Round:** 70
**Reproducer:** `src/reclassify_rr_target_a_1398.py`
**Deliverables:** `outputs/rr_target_a_1398_status_claude.json`,
`outputs/rr_target_a_1398_mechanisms_claude.json`,
`outputs/rr_target_a_1398_residuals_claude.json`
**No search of any kind was run.** Every boundary is replayed literally through the exact engine
from its own root and the recognizer is re-applied from scratch. No node-capped or bounded
continuation appears anywhere, as a proof step or otherwise.

**Helpers deliberately not used:** the retracted `true_phase_walk_capacity` phase-capacity helper,
any phase-derived pruning, the old parity conjecture, the v1/v2 completeness claims, and the
invalidated hierarchy macro-entry source semantics. The only capacity input is the coarse segment
bound, which `src/audit_rr_capacity_helpers.py` grades *"SOUND_FOR_SINGLE_LANDING, exact theorem,
occupancy-independent, precondition: none beyond the RR alphabet"*.

---

## 0. Headline

| | |
|---|---|
| **1,398 total** | replayed and hash-verified **1,398 / 1,398** (raw and canonical) |
| **Closed** | **1,398** (Target B) |
| **Remaining** | **0** |
| **Distinct canonical classes** | 1,398 boundary states, collapsing to **7** mechanism classes (**3** if `root_ell` is dropped) |
| **Distinct bridge mechanisms** | **1** — hexagon 0 (the hub), for all 1,398 |
| **known-18** | **6** |
| **New Target-A classes** | **0 at Q2 / Area-A scope**; 1,392 remain genuine **Q1** boundaries |
| **Target-B survivors** | **0** |
| **Exact remaining premise** | the Area-A completion target `(P, O, D) = (121, 25, 4)` with `Ndef ≤ 3`; nothing else |

The single most important structural fact:

> **Only 6 of the 1,398 are admissible in the Q2 / Area-A slab at all.** The other 1,392 fail
> `area_a_prune_reason` with `remaining_cover_capacity_impossible` — i.e. `Phi < 0` — and that is
> the *only* recognizer condition any of them fails. And those 6 are **exactly** the 6 already in
> the known 18.

---

## 1. Method

Roots are rebuilt exactly as `run_rr_target_a_coverage.py` does: `short_ellN` = `initial_state`,
`N` rotations, `w2:10`; `long_found_i` / `long_q1_i` = the same prefix followed by the recorded
`literal_joint_word` of `outputs/rr_long_excursion_prefixes.json`, each joint preceded by five
rotations. Each boundary path is then replayed **edge by edge**, and at every edge I record the
forced rotation length, the incidence excess `r`, the maximum hexagon degree, `Phi`, whether the
joint target landed in a virgin hexagon, and the running R-event count.

The Target-A verdict is then re-derived from scratch, restating
`build_rr_target_a_roots.is_target_a`: `joint_kind == R`, `F == 1`, `H == 0`,
`area_a_prune_reason(child) is None`, exactly two R events, and `same_component` computed by a
fresh union-find on the **pre-joint** (rotation-run end) state. Nothing from the original search's
bookkeeping is trusted, so none of the Round-40–48 bugs can survive into the verdict.

Agreement with the recorded artifact: **raw hash 1,398 / 1,398, canonical hash 1,398 / 1,398.**

---

## 2. A. Canonicalization of all 1,398

Per boundary the status file records `source_root_key`, `root_ell`, `root_r_count`, `path`,
`extension_depth`, both hashes, the full coordinate vector `{P, O, D, Ndef, F, H, Phi, S,
visited}`, `r` at the R2 source and at the boundary, the bridge, the same-component mechanism, the
recognizer re-check, the per-path theorem audit, the known-18 match and the Target-B status.

Corpus-wide coordinates:

| quantity | values |
|---|---|
| `Ndef` | **2** for all 1,398 (the R2 raises it from 1) |
| `F, H` | `1, 0` for all 1,398 |
| `Phi` | `{-8: 9, -4: 449, -3: 592, -2: 164, -1: 178, 0: 6}` — **never positive** |
| `P` | 11 … 23 |
| `O` | 6 … 18 |
| `D` | 19 … 68 |
| `r` at the R2 source | `{1: 1389, 2: 9}` |
| `root_ell` | `{0: 449, 1: 601, 2: 164, 3: 178, 4: 6}` |
| root family | `long_q1_*`: 1,392; `long_found_*`: 6 |

### Q1 versus Q2 — the decisive split

The **only** recognizer failure across the whole corpus is
`area_a_prune=remaining_cover_capacity_impossible`, i.e. `Phi < 0`, and it hits exactly 1,392.
Every other condition — joint kind, `F`, `H`, the two-R-event count, and `same_component` — holds
for all 1,398.

This is precisely the Q1/Q2 distinction that `src/build_rr_target_a_roots.py`'s own docstring
warns about. So:

* **as Q1 objects** (a local predicate on one macro edge) all 1,398 are genuine Target-A
  boundaries, independently re-confirmed by literal replay;
* **as Q2 / Area-A objects** only the 6 `long_found_*` boundaries are admissible, and they are the
  6 already in the known 18 — set equality verified on raw hashes.

**⟹ new Target-A classes at Q2 scope: 0.**

---

## 3. B. Bridge and R2 finite classification

The 1,398 distinct boundary states collapse to **7** mechanism classes keyed by
`(root_ell, bridge hexagon, bridge orbits, source orbit, target orbit, joint, ell)`, and to **3**
when `root_ell` is dropped:

| bridge hexagon | bridge orbits | R2 | joint | ℓ | count | ℓ4 normal form |
|---|---|---|---|---|---|---|
| **0** | `{0, 1}` | orbit 1 → orbit 0 | `w3:120` | 0 | **1,389** | **R2-A** |
| **0** | `{0, 1, 3}` | orbit 3 → orbit 1 | `w3:120` | 0 | 7 | neither |
| **0** | `{0, 1, 3}` | orbit 0 → orbit 1 | `w3:120` | 5 | 2 | **R2-B** |

Uniform facts across all 1,398:

* **the bridge hexagon is the hub, hexagon 0, in every single case** — one bridge mechanism, not 1,398;
* **the joint is `w3:120` in every single case**;
* `ell ∈ {0, 5}` only (1,396 and 2);
* `pair_equals_bridge` is true for the 1,389 two-orbit cases; the 9 three-orbit cases are the
  `r = 2` ones, where the hub carries **three** registered ports (degree 3) and the R2 uses one of
  the induced pairs.

So the Round-69b ℓ4 normal form is not ℓ4-specific: **1,391 of the 1,398 realise exactly R2-A or
R2-B**, and the residual 7 are the single extra shape that only a degree-3 hub can produce.

### The Round-69 theorem stack, audited on 1,398 real paths

| theorem | result |
|---|---|
| forced rotation length | **0 violations** over every edge of every one of the 1,398 replays |
| `6r ≤ 11 − Phi` (UNIQUE BRIDGE) | **0 violations.** `(r, Phi)` pairs are exactly `{(1, −4…0), (2, −8)}` — `r = 2` occurs only at `Phi = −8`, precisely where the bound permits it. The theorem is confirmed on 1,398 states lying **outside** the `Phi ≥ 0` region it was derived for. |
| non-hub hexagon entered twice | **none**, consistent with re-entry cost ≥ 6 |
| σ-adjacency admissibility | every two-orbit bridge is at rotation distance 1 and is weight-3 admissible; the three-orbit hubs contain the same `{0,1}` pair plus orbit 3 |
| LIVE/DEAD incidence | used to define the new invariant of §4 |

---

## 4. D. Target-B closure, and the counting theorem that does it in one line

The user's brief asked for an inequality that closes hundreds of boundaries at once rather than a
certificate per boundary. There is one, and it is exact.

### THEOREM (MARGIN IDENTITY / DEFECT THRESHOLD)

At a Target-A boundary `Ndef = 2`, hence `R_cap = 3 − 2 = 1` and `O_cap = 25 − O`, so the coarse
segment bound reads `bound = 5(O_cap + R_cap) + 4 = 134 − 5·O` while `B + 1 = 122 − P`. Therefore

```
margin  =  bound − (B + 1)  =  12 − (5·O − P)  =  12 − D
```

**verified as an exact identity on all 1,398 rows.** So

> **An Area-A NR6 completion from a Target-A boundary requires `D ≤ 12`.**

The observed defects are `D ∈ [19, 68]`, minimum 19. **One inequality closes 1,398 / 1,398.**

> ### CORRECTION (Round 71)
>
> This section originally added "and it uses no `Phi`". **That was wrong.** The segment count
> `m ≤ O_cap + R_cap` silently omits a term: an orbit-changing macro edge with `ell < 5` consumes
> neither an `O` nor an `N` — only `Phi`. The sound general statement is
> `m ≤ O_cap + R_cap + Phi`, exactly as `build_rr_target_a_roots.capacity_slack` already says
> ("*Hence future segments <= O_rem + N_rem + Phi*"), which is also why
> `outputs/rr_target_b_survivors.json` records the scope as "needs only Phi=0".
>
> The sound general forms are
> **`D ≤ 9 − used(q0) + 4·(R_cap + Phi)`** (the D-form of `capacity_slack`, sharpest) and the
> weaker **`D ≤ 8 + 5·(R_cap + Phi)`** (Round-32 bound A). `D ≤ 12` is their
> `Phi = 0, Ndef = 2, used = 1` specialisation.
>
> **The totals in this document are unchanged.** Re-checked: the sound form
> `D ≤ 8 + 5(R_cap + Phi)` closes **1,398 / 1,398** on its own — at `Ndef = 2` and `Phi ≤ 0` the
> threshold is at most 13 and the observed minimum is `D = 19`. What changes is only the
> attribution: the closure is not "Phi-free".

### The same theorem, in interpretable form

`D = 5·O − P` counts the unregistered ports of open orbits, and `D` moves by `+4` at every
orbit-opening joint and by `−1` at every other joint. `D ≤ 12` therefore says

> a completable Target-A boundary must already be **orbit-saturated**: `P/O ≥ 5 − 12/O`.

| | observed | required |
|---|---|---|
| registered ports per open orbit | **1.22 – 2.10**, mean **1.51** | **3.00 – 4.33** |
| boundaries meeting it | **0 / 1,398** | |

The corpus misses by a factor of roughly 2.5 — this is not a marginal closure. And the reason is
structural: these boundaries all descend from **long-excursion prefixes**, whose defining feature
is a Z3-rich `literal_joint_word` (4 or 6 orbit-openings in the root alone). Hopping between
orbits is exactly what drives `D` up, and a completion needs the opposite.

### Two further counting closures, and an honest comparison

* **Window budget.** `Phi ≥ 0` (`remaining_window_capacity_prune`: `5 + 6·(121 − P) ≥ 720 − visited`)
  is necessary for a completion. It closes **1,392** of the 1,398 on its own.
* **Dead-port bound (new).** A visited-but-unregistered port can never be registered (Round 69
  LIVE/DEAD). An Area-A completion ends at `P = 121, O = 25`, hence `D = 4`, and at `visited = 720`
  every unregistered port is dead. So
  `D_dead := #{ports visited, unregistered, in an open orbit}` is **monotone non-decreasing** and
  must satisfy **`D_dead ≤ 4`**. Opening a further orbit `q` adds `dead(q)`, giving the sharper
  selection form: a completion must find `25 − O` further orbits whose dead counts sum to at most
  `4 − D_dead`. This uses **neither `Phi` nor any capacity theory** — only the no-repeat rule and
  the target arithmetic.
  It closes **750** of the 1,398 (`D_dead` runs from 0 to 18).

  **Honest verdict on my own invariant:** on this corpus the dead-port bound is *strictly
  subsumed* by the defect threshold — it closes **0** boundaries that the coarse bound leaves
  open. It is reported because it is sound, monotone, `Phi`-free, and independent of the capacity
  theory, so it is a second certificate for those 750; it is **not** an improvement here.

Union of the three: **1,398 / 1,398 closed. Target-B survivors: 0.**

---

## 5. C. known-18 collapse and certificate reuse

Six boundaries match the known 18 on **both** the raw and the canonical hash — the same six that
pass the Q2 recognizer:

| raw | root | `P` | `O` | `D` | known-18 key | helper-free status |
|---|---|---|---|---|---|---|
| `f903e663bde5e14f` | `long_found_4` | 11 | 6 | 19 | `ell4_P7_f903e663` | `COARSE_CAPACITY_IMPOSSIBLE` |
| `305ec3a20c421fcd` | `long_found_9` | 11 | 6 | 19 | `ell4_P7_305ec3a2` | `COARSE_CAPACITY_IMPOSSIBLE` |
| `3d0c9ebe3b9b6f95` | `long_found_44` | 14 | 8 | 26 | `ell4_P10_3d0c9ebe` | `COARSE_CAPACITY_IMPOSSIBLE` |
| `6763ba842c37d7ab` | `long_found_74` | 14 | 8 | 26 | `ell4_P10_6763ba84` | `COARSE_CAPACITY_IMPOSSIBLE` |
| `4f85ec5368a065cb` | `long_found_142` | 14 | 8 | 26 | `ell4_P10_4f85ec53` | `COARSE_CAPACITY_IMPOSSIBLE` |
| `fd286587321ec833` | `long_found_180` | 14 | 8 | 26 | `ell4_P10_fd286587` | `COARSE_CAPACITY_IMPOSSIBLE` |

Their rows in `outputs/rr_target_b_18_boundary_corrected_ledger.json` (Round 39, commit `9b345c4`,
verified reachable in this repository's history) carry `phase_helper_used: false` and
`corrected_final_status: COARSE_CAPACITY_IMPOSSIBLE` — the helper-free branch that needs no exact
DFS at all. **The existing helper-free Target-B certificate is reusable verbatim for all six**, and
my independently recomputed margins (`−7`, `−7`, `−14`, `−14`, `−14`, `−14`) reproduce that verdict
from scratch.

---

## 6. E. Residual ledger

`outputs/rr_target_a_1398_residuals_claude.json` is defined as the boundaries that survive the
occupancy-independent coarse bound **and** the dead-port bound **and** the orbit-selection bound
**and** are not a known-18 row with a helper-free closure.

**It is empty: `count: 0`.** There is no residual mechanism left in this corpus.

---

## 7. Scope, and what is *not* claimed

* Every statement that consumes `Phi ≥ 0` is labelled **Q2 / Area-A** and is not extended to Q1.
  In particular the claim "only 6 are admissible" is a Q2 statement; **all 1,398 remain genuine Q1
  Target-A boundaries**, and this document does not delete a single one of them.
* The Target-B closure is inherently Q2: it is a statement about completability to an Area-A NR6
  walk (`P = 121`, `O = 25`, `Ndef ≤ 3`). That target *is* the remaining premise, and it is the
  only one.
* The defect threshold and the dead-port bound do **not** use `Phi`; the window-budget closure
  does.
* No node-capped or bounded continuation was used anywhere. No exhaustion of any search tree is
  claimed — none was run.
* This does not touch `L₆ ≥ 872`, CH2, Target C, `N = 0`, or the U/J branches, and **this project
  has still not proved `L₆ ≥ 872` unconditionally.** What is now established, at Q2 scope, is that
  neither the 24 residual families of the corrected-v5 program (Rounds 69/69b) nor the 1,398
  Rounds-35–37 boundaries contribute a Target-A boundary with an open Target-B question.

---

## 8. Evidence grading

| label | statement |
|---|---|
| **HP** | the margin identity `margin = 12 − D`; the defect threshold; the dead-port bound and its selection form; the Q1/Q2 reading of the single failing recognizer condition |
| **corrected** | §4's claim that the defect threshold is `Phi`-free — see the Round-71 correction box above; totals unchanged |
| **EC** | the literal replay and both hashes for all 1,398; the 7-way and 3-way mechanism collapse; the `6r ≤ 11 − Phi` and forced-rotation-length audits |
| **IV** | agreement with the recorded artifact (1,398/1,398 on both hashes); the six known-18 matches; the helper-free ledger rows |
| **BO** | none — no bounded observation is used in this document |
