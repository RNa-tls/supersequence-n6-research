# The Q2 / Area-A proof frontier, rebuilt

**Author:** Claude (independent verification track)
**Round:** 71
**Reproducer:** `src/rebuild_q2_area_a_frontier.py`
**JSON:** `outputs/rr_q2_area_a_frontier_claude.json`
**Scope:** everything below is **Q2 / Area-A**. Nothing is claimed for Q1 — the frontier states
discussed here remain perfectly good Q1 objects and none of them is deleted.
**No search was run.** Every state processed was already stored by an earlier round; applying a
prune to a stored frontier is a filter, not a continuation. No node-capped expansion is used as a
proof step anywhere.
**Helpers deliberately not used:** the retracted `true_phase_walk_capacity` and any phase-derived
port-count bound, the old parity conjecture, the v1/v2 completeness claims, the invalidated
hierarchy macro-entry source semantics.

---

## 0. Headline

| | |
|---|---|
| **Total current Q2 residual** | **200,408** stored frontier states |
| **Distinct mechanism classes** | **1,570** |
| **Largest unresolved class** | `Ndef=0, Φ=5, R_cap=3, O=10, P=13, D=37, D_dead=1, re-entry need=8, used=1` — **3,969** states (2.0%) |
| **Exact logical gap** | Target-B closure only covers boundaries that were *found*; **no coverage search has ever been exhausted** |
| **Best next theorem** | the **SKIP-COST** inequality (§6) |
| **New D-descent inequality plausible?** | **Yes** — the residual sits exactly on the tight band, and one resource is provably uncharged |

---

## 1. What the closures so far actually establish

Not re-analysed here, taken as given from the committed record:

| item | round | status |
|---|---|---|
| corrected-v5 residual 24 families / 1,818 anchors | 69, 69b | closed at Q2 |
| Rounds 35–37, the 1,398 Target-A boundaries | 70 | Target B closed, 0 survivors |
| the known 18 | 34, 39 (helper-free) | closed; certificate reused verbatim |

**What they do not cover.** Every one of those results is a statement about a boundary that has
already been *found*. And the coverage searches that find boundaries have never been exhausted:
`outputs/rr_target_a_resumed_frontiers.json` records, for **all 33 roots**,
`stop_reason: INCOMPLETE_TIMEOUT` and `frontier_emptied_naturally: false`, with **3,321,753**
queued states left unexpanded.

**⟹ The Q2 frontier is the Q2-admissible part of that stored frontier**, not a residue among the
known boundaries.

That those searches ran in Q1 mode is deliberate and correct: they used
`search_rr_target_a_unified.q1_safe_prune_reason`, which omits every completion-assuming test
(`q1_forbidden_prune_check` raises if one is ever cited). For the **Q2** question those tests are
available again, and applying them to a stored frontier is exactly what this round does.

---

## 2. The frontier, filtered

| stage | states | note |
|---|---|---|
| stored frontier | **3,321,753** | 33 roots, none exhausted |
| Q2-admissible | **3,248,890** | −72,863 by the Q2-only prunes (dominated by `Phi < 0`) |
| closed by `capacity_slack` | **2,956,692** | 91.0% of the admissible frontier |
| survives `capacity_slack` | **292,198** | |
| closed by the dead-port bound (new, §5) | **19,073** | |
| closed by the orbit re-entry inequality (new, §5) | **72,717** | |
| **RESIDUAL** | **200,408** | in **1,570** classes |

The two new inequalities of §5 close **91,790 of the 292,198** survivors — **31.4%** of what the
committed capacity bound leaves open.

**22 of the 33 roots are now fully closed at Q2.** The 11 with residual:

| root | Q2-admissible | survives slack | dead-port | re-entry | residual |
|---|---|---|---|---|---|
| `short_ell4` | 133,668 | 103,874 | 10,146 | 12,995 | **80,733** |
| `short_ell3` | 130,248 | 79,897 | 3,286 | 14,629 | **61,982** |
| `short_ell2` | 129,486 | 60,874 | 2,262 | 23,156 | **35,456** |
| `short_ell1` | 128,434 | 31,014 | 1,042 | 13,991 | **15,981** |
| `short_ell0` | 112,961 | 11,924 | 470 | 5,367 | **6,087** |
| `long_found_4` | 101,342 | 1,915 | 780 | 1,069 | 66 |
| `long_found_9` | 100,533 | 1,969 | 894 | 1,021 | 54 |
| `long_q1_3` | 98,868 | 277 | 29 | 220 | 28 |
| `long_q1_8` | 93,765 | 284 | 46 | 219 | 19 |
| `long_q1_2`, `long_q1_7` | | 10, 10 | 0, 2 | 9, 7 | 1, 1 |

**99.92 % of the residual (200,239 of 200,408) sits in the five short roots**, and it is remarkably
uniform: `Ndef = 0` for all of it, and `P ∈ {13, 14}` — a shallow, wide band. The long-root
residual is 169 states.

Residual distributions: `Φ ∈ {0:4169, 1:5720, 2:15243, 3:34403, 4:61026, 5:79847}`;
`O ∈ 3…10`; `D ∈ {11 … 37}`; `D_dead ∈ {0:42084, 1:65035, 2:51129, 3:29562, 4:12598}`.

---

## 3. Why the residual is not closed by the existing theorems

| theorem | why it does not close these |
|---|---|
| `D ≤ 12` (Round 70) | that is the `Φ = 0, Ndef = 2, used = 1` specialisation. The residual has `Ndef = 0` (so `R_cap = 3`, the largest possible re-entry budget) and `Φ` up to 5, which raises the true threshold `D ≤ 9 − used + 4(R_cap + Φ)` to as much as 40. |
| `r ≤ 1` (unique bridge) | it constrains *which orbit pair* can be co-component; it says nothing about completability. It does hold here — see §4 — but it is not a Target-B obstruction. |
| VNTS / T4 | branch-local certificates about a specific short child's direct-Z2 bridge; they do not apply to arbitrary frontier states. |
| ℓ4 unique-bridge normal form | proved for `root_ell = 4` **residual anchors**, whose `Φ ∈ {0,5}` and `r ∈ {0,1}` are pinned by the R1 history. Frontier states are pre-R2 nodes at other depths with `Ndef = 0`. |
| known-18 closure | applies to 18 specific boundary states; the residual are not boundaries at all. |
| `capacity_slack` | applied — it closes 91.0%. The remainder is exactly where it goes tight. |

---

## 4. D-descent: how `D` must come down, and what it costs

**The descent itself is free.** `D = 5·O − P`, and `ΔD = +4` at a fresh-orbit joint, `−1` at every
other joint. With `O_final = 25` and `P_final = 121` the identity forces `D_final = 4` — so
reaching the target defect imposes **no** constraint. The whole obstruction lives in the segment
structure.

**The segment model, corrected.** Exhaustively over all 24 macro generators × 720 words, exactly
**two** preserve the endpoint's E-orbit, and they do so for every word:

| macro edge | acts as | `joint_kind` | cost |
|---|---|---|---|
| `ell = 5, w2:10` | **E¹** | `Z2` | free |
| `ell = 5, w3:120` | **E²** | **`R` always** — its target is the endpoint's own, already-open orbit, so `new_orbit` is false | **one unit of `Ndef`** |

So a segment walks its orbit's 5-cycle by `+1` (free) or `+2` (costing an R), and **two consecutive
visited ports end the segment**. I had initially assumed only `(5, w2:10)` preserves the orbit; that
was wrong, and the correction matters for §6.

**The committed sharpest bound, in D-form.** `build_rr_target_a_roots.capacity_slack` reads
`TARGET_P − P ≤ (5 − used(q0)) + 5·O_rem + 4·(N_rem + Phi)`. Substituting `D = 5O − P` gives,
verified symbolically with **0 mismatches over 259,360 grid points**:

```
capacity_slack  ==  ( 9 − used(q0) + 4·(R_cap + Phi) ) − D
```

> **Minimum extra cost.** Bringing `D` down to 4 requires at least
> `g ≥ ⌈(D + used(q0) − 9) / 4⌉` orbit re-entries, each costing **one unit of `Ndef`** (an R) or
> **at least one unit of `Φ`** (an `ell < 5` edge).

**The tradeoffs, explicitly.**

| resource | how the descent consumes it |
|---|---|
| `Ndef` | +1 per R; capped at `n_limit = 3`. This is the residual's whole budget (`Ndef = 0 ⟹ R_cap = 3`). |
| `Φ` | non-increasing, must stay ≥ 0; every `ell < 5` edge spends `5 − ell`. |
| `F` | a weight-2 joint opening a fresh orbit needs an abandonment → `F = 2` → dead. Fresh openings must be weight 3. |
| `H` | any weight ≥ 4 joint → `H > 0` → dead. Joints are weight 2 or 3 only. |
| `r` | `6r ≤ 11 − Phi`, so **inside Q2 (`Phi ≥ 0`) `r ≤ 1` unconditionally**: at most one co-component E-orbit pair anywhere in the entire Q2 region. Spending `Φ` cannot buy a second bridge, because `Φ` may not go negative. |

---

## 5. The two new inequalities used this round

**DEAD-PORT.** `D_dead ≤ 4`, where `D_dead` counts visited-but-unregistered ports of open orbits.
It is monotone (dead is permanent — Round 69 LIVE/DEAD), and at the target every unregistered port
is dead while `D_final = 4`. Uses only the no-repeat rule and the target arithmetic — no `Φ`, no
capacity theory. **Closes 19,073.**

**ORBIT-REENTRY.** Let `Q = {open orbits q ≠ q0 holding a live unregistered port}`. Each `q ∈ Q`
either receives a later registration — which needs an orbit-changing joint into `q`, costing one
unit of `R_cap + Phi` — or is abandoned entirely, in which case its live ports die and are charged
against the remaining dead budget `4 − D_dead`. Hence

```
|Q| − k  ≤  R_cap + Phi ,   k = max #{members of Q whose live-port counts sum to ≤ 4 − D_dead}
```

**Closes 72,717.** It counts *segments needed*, never ports per segment, so it does not repeat the
failure mode for which `true_phase_walk_capacity` was retracted (that helper bounded how many
hexagons a segment can complete and needed full-hexagon freshness).

---

## 6. Best next theorem target — SKIP-COST

> **Claim to prove.** A within-orbit segment advances by `E¹` (free) or `E²` (one unit of `Ndef`).
> Therefore every dead port that a segment steps *over* costs one unit of `Ndef`, and two
> consecutive visited ports terminate the segment. Summing over the whole future:
>
> ```
> (orbit-changing R steps)  +  (dead ports skipped over)   ≤   R_cap + Phi
> ```

**Why this is the right target.** `capacity_slack` charges an `R` only when it *changes* the orbit.
It does not charge the within-segment `E²` steps — which consume exactly the same `Ndef`. That is a
resource the current bound provably does not count, and §4 shows it is real.

**Why it is sound where the retracted helper was not.** It charges resource consumption per skip
rather than bounding how many ports a segment can register, so it never invokes hexagon freshness —
the precondition whose failure retracted `true_phase_walk_capacity`.

**Estimated payoff.** The re-entry margin distribution over the residual is
`{−7:4, −6:100, −5:874, −4:4051, −3:14422, −2:34366, −1:59937, 0:86654}`. **86,654 residual states
(43.2%) sit at margin exactly 0** — they survive only because the current demand equals the current
budget precisely. Any inequality that adds **≥ 1** to the demand side closes all of them. And
158,324 of the 200,408 residual states have `D_dead ≥ 1`, i.e. they already contain dead ports
inside open orbits — precisely the configurations that force skips.

### Payoff-ranked targets

| rank | target | closes | % of residual |
|---|---|---|---|
| 1 | SKIP-COST inequality | ≥ 86,654 | 43.2 % |
| 2 | `short_ell4` alone | 80,733 | 40.3 % |
| 3 | the `Ndef = 0` band (all five short roots) | 200,239 | 99.9 % |
| 4 | the `P ∈ {13,14}` shallow band | 200,239 | 99.9 % |
| 5 | the 169 long-root residual states | 169 | 0.08 % |

Ranks 3 and 4 are the same set seen two ways: **one theorem about shallow, `Ndef = 0`, five-short-root
frontier states would close essentially the entire Q2 frontier.** That, and not any surviving
mechanism among the known boundaries, is where the Q2 proof is actually blocked.

---

## 7. Exact logical gap

> Target-B closure applies only to Target-A boundaries that have been **found**, and no coverage
> search has ever been exhausted — all 33 stopped on a time cap with a non-empty frontier. The Q2
> proof is therefore blocked not by a hard mechanism among the known boundaries (those are all
> closed) but by **200,408 stored, unexpanded, Area-A-admissible frontier states** from which an
> as-yet-unfound Target-A boundary could still arise.

Two things follow. First, "the 1,818 and the 1,398 are closed" is true and remains true, but it is
a statement about a *list*, not about the search. Second, closing the frontier does **not** require
resuming the search: 91.0 % of it fell to a bound already in the repository, another 31.4 % of the
remainder to two inequalities written this round, and the rest is concentrated in one uniform band
where a single further inequality would apply.

## 8. Corrections issued this round

* **Round 70 §4** claimed the defect threshold `D ≤ 12` is "`Phi`-free". **It is not.** The segment
  count `m ≤ O_cap + R_cap` omits a term: an orbit-changing edge with `ell < 5` costs neither `O`
  nor `N`, only `Φ`. The sound forms carry `+Φ`, exactly as `capacity_slack` already states. The
  Round-70 totals are unchanged (re-verified: the sound form closes 1,398/1,398 on its own). The
  correction is recorded in place in `RR_TARGET_A_1398_RECLASSIFICATION_CLAUDE.md`.
* **This round, §4**: my initial segment model assumed only `(ell=5, w2:10)` preserves the E-orbit.
  `(ell=5, w3:120)` does too, acting as `E²` and always as an `R`. Caught before it was used; it is
  now the basis of §6 rather than an error in it.

## 9. Evidence grading

| label | statement |
|---|---|
| **HP** | the D-form of `capacity_slack`; the minimum-cost formula; the `Φ ≥ 0 ⟹ r ≤ 1` corollary; the soundness of both new inequalities |
| **EC** | the two orbit-preserving generators (24 × 720); the D-form verification (259,360 grid points); the filter over all 3,321,753 stored states |
| **IV** | the per-root exhaustion status read directly from the committed frontier artifact |
| **BO** | none |

**This project has still not proved `L₆ ≥ 872` unconditionally**, and nothing here changes that.
