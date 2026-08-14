# SLACK-COVER: the excess is forced, not budgeted — and it closes 38,141 of 44,650

**Author:** Claude (independent verification track)
**Round:** 79
**Reproducer:** `src/prove_rr_slack_cover.py` (`check --check algebra`, `check --check solver`)
**JSON:** `outputs/rr_slack_cover_claude.json`
**Baseline in:** 44,798 residual, 1,050 classes, 26/33 roots clear.
**Baseline out:** **6,657 residual, 761 classes, 28/33 roots clear.**
**Scope:** Q2 / Area-A. No frontier re-run, no continuation search, no revisiting of the
Round-78 `c = 5` UNSAT instances. The only search is a finite static feasibility decision on
the fixed orbit–hexagon incidence system.

---

## Result, up front

> **38,141 of 44,650 closed (85.42 %).** Residual falls to **6,657** in **761** classes, and
> every long root is now clear — **28 of 33**.
>
> The derivation corrects the framing: the future excess is **not** "at most `b`", it is
> **exactly `b`, forced**. What actually restricts the walk is the plain cover requirement
> plus its per-block consequence.
>
> The method's power decays monotonically with slack — **97.4 % → 87.7 % → 40.1 % → 0 %** —
> and at `b = 4` it has none at all.

---

## 1. The algebra, derived rather than guessed

With `C` the covered hexagons, `U` its complement, `K = 25 − O`, `c = COLLISIONS(s)`, `b = 5 − c`:

```
|U| = 120 − |C| = 120 − (5·O − c) = 5(25 − O) − (5 − c) = 5K − b        ✔ 0 failures / 44,650 states
```

For **any** choice of `K` blocks, writing `m(h)` for how many chosen blocks contain `h`:

```
5K − |⋃B_i ∖ C| = Σ_{h∈C} m(h) + Σ_{h∈U} max(m(h) − 1, 0)  =:  EXCESS
```

— each incidence with an already-covered hexagon costs 1, and each duplicate covering of an
uncovered hexagon costs 1. Verified on random configurations, 0 failures.

**Now the part that changes the shape of the problem.** Every hexagon outside `C` is in `U` by
definition, so `⋃B_i ∖ C ⊆ U` always. If the chosen blocks *cover* `U` then `U ⊆ ⋃B_i`, hence
`⋃B_i ∖ C = U` exactly, and therefore

```
EXCESS = 5K − |U| = b        exactly, always
```

> **So "total excess ≤ b" is not an independent constraint.** It is the counting slack in the
> cover, and it is attained automatically the moment `U` is covered. Imposing it separately
> would have added nothing.

What survives is the requirement itself, plus its per-block consequence:

> **SLACK-COVER.** There must exist exactly `K` currently-closed orbits whose 5-hexagon blocks
> **cover** `U`. Since the whole excess is only `b`, every chosen block satisfies
> `|block ∩ C| ≤ b`.

**Reduction check.** At `b = 0` each block must waste nothing, so `block ⊆ U` and the blocks are
disjoint with `|U| = 5K` — precisely Round 78's exact cover. ✔

**Canonicalisation.** An open orbit's five hexagons all lie in `C`, so **any orbit meeting `U` is
automatically closed** (0 failures in 20,000 random configurations). Hence the candidate family
— and the whole instance — is a function of `(U, b)` alone. 44,650 states give **43,643 distinct
instances**.

## 2. Necessary tests, applied before any search

| | test | necessary because |
|---|---|---|
| **A** | coverability | every `h ∈ U` needs a candidate supplier |
| **B** | waste floor | `Z` = hexagons of `U` reachable only by positive-waste blocks; at most `b` positive-waste blocks may be chosen, so the `b` largest `\|block ∩ Z\|` must sum to ≥ `\|Z\|` |
| **C** | forced excess | uniquely-supplied hexagons force blocks; the forced set's own excess `5·\|forced\| − \|⋃forced ∩ U\|` must not exceed `b` |
| **D** | component / Hall | a candidate's `U`-part lies in one component, so `Σᵢ ⌈mᵢ/wᵢ⌉ ≤ K` and `Σᵢ (5⌈mᵢ/5⌉ − mᵢ) ≤ b` |

Then a memoised bitset DFS with MRV, run to completion. The invariant `5k′ − |U′| = b′` holds at
every node, so slack never has to be tracked separately.

## 3. Payoff, tightest band first

| `c` | `b` | states | A | B | C | D | complete-UNSAT | **SAT** | **closed** |
|---|---|---|---|---|---|---|---|---|---|
| **4** | 1 | 24,834 | 461 | 8,688 | 6 | 0 | 15,040 | 639 | **24,195 (97.43 %)** |
| **3** | 2 | 13,446 | 0 | 521 | 0 | 0 | 11,274 | 1,651 | **11,795 (87.72 %)** |
| **2** | 3 | 5,369 | 0 | 7 | 0 | 0 | 2,144 | 3,218 | **2,151 (40.06 %)** |
| **1** | 4 | 1,001 | 0 | 0 | 0 | 0 | 0 | 1,001 | **0 (0.00 %)** |
| | | **44,650** | 461 | 9,216 | 6 | 0 | **28,458** | **6,509** | **38,141 (85.42 %)** |

**UNKNOWN: 0 in every band.** Max search 20,178 nodes; no verdict rests on a cap.

Test D never fired — reported as 0 rather than dropped. Test B (the waste floor) is the
distinctive one at `b = 1`, closing 8,688 states on its own; it has no analogue at `b = 0`.

## 4. Why the verdicts are trustworthy

| check | result |
|---|---|
| **positive control** — 620 instances synthesised from a known 25-orbit covering family, so a solution provably exists, spread over slack 0–4 | **0 solver failures** |
| negative control (mismatched `K`) | UNSAT, complete, 1 node |
| **UNSAT re-decided under a non-MRV variable order** — 8,141 instances across bands 1–3 | **0 disagreements, 0 incomplete** |
| **every SAT witness verified** — 6,013 instances | exactly `K` blocks, all closed in the source state, `U` fully covered, excess exactly `b`; **0 invalid** |

The positive control is the decisive one: it is the test that would have exposed an
over-aggressive pruning rule, and a single failure would have voided every UNSAT in this round.

## 5. `E¹` safety, re-confirmed

Over **1,600 `c ≤ 4` states and 4,325 `E¹` steps**, every one of `O`, `C`, `U`, `c` and the
candidate block family was **unchanged — 0 violations**. No quantity charged here is one `E¹`
can repair.

## 6. `COLLISIONS = 5` SAT survivors

The 148 Round-78 SAT states were kept entirely separate: their exact covers were not re-run and
they were not re-decided. They are carried into the new residual unchanged.

## 7. Deliverable

| | |
|---|---|
| input | **44,650** (`c ≤ 4`) |
| distinct slack-cover instances | **43,643** |
| closed by cheap tests | **9,683** |
| closed by complete solver UNSAT | **28,458** |
| **total closed** | **38,141 (85.42 %)** |
| slack-cover SAT | 6,509 |
| `c = 5` SAT carried from Round 78 | 148 |
| **new Q2 residual** | **6,657** in **761 classes** |
| roots fully closed | **28 / 33** — every long root is now clear |

Residual by root: `short_ell3` 1,804 · `short_ell4` 1,624 · `short_ell2` 1,592 ·
`short_ell1` 1,124 · `short_ell0` 513.

**Dominant structure among SAT survivors.** Survival is governed by slack and nothing else. The
`c`-distribution inverts completely: the residual is now `{c=1: 1,001, c=2: 3,218, c=3: 1,651,
c=4: 639, c=5: 148}`, so the *loosest* band — 1,001 states, 2.2 % of the input — contributes the
second-largest block of survivors and was closed at a rate of exactly zero. Every survivor has
`Ndef = 0`; `P` splits 2,960 / 3,697 between 13 and 14; `r = 0` for 5,947 of 6,657. No
coordinate other than `c` predicts survival.

**Is the static final-orbit-set method exhausted?** As stated, yes. Closure runs
97.4 % → 87.7 % → 40.1 % → **0 %** as slack grows, every band was decided completely with no
UNKNOWNs, and at `b = 4` the condition has no power whatsoever: with four units of slack there
are simply too many ways to cover `U` with `K` blocks. A stronger *static* incidence test is not
ruled out, but this one is saturated. Going further needs a mechanism the static system cannot
see — the **order** in which the `K` orbits may legally be opened, or their interaction with the
fragment-repair obligation. Neither is established here.

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
