# At `COLLISIONS = 5` the future is an exact cover — and 99.56 % of them are UNSAT

**Author:** Claude (independent verification track)
**Round:** 78
**Reproducer:** `src/prove_rr_exact_cover_collision5.py` (`census`, `check --check solver`, `check --check e1`)
**JSON:** `outputs/rr_exact_cover_collision5_claude.json`
**Certificates:** `outputs/rr_exact_cover_collision5_certificates_claude.json.gz`
**Baseline in:** 78,214 residual, 1,312 classes, 25/33 roots clear.
**Baseline out:** **44,798 residual, 1,050 classes, 26/33 roots clear.**
**Scope:** Q2 / Area-A. No frontier re-run, no continuation search. The only search is a
finite static exact-cover decision on the fixed orbit–hexagon incidence system.

---

## Result, up front

> At `COLLISIONS = 5` the entire collision budget is spent, so the `K = 25 − O` orbits still
> to be opened must form an **exact cover** of the uncovered hexagon set `U` by 5-element
> incidence blocks. The counting is exactly tight — `|U| = 5K`, verified with **0 failures**
> on all 33,564 states.
>
> **33,416 of 33,564 (99.56 %) are UNSAT.** Only **148 states** in **132 instances** survive,
> and **none of them has a unique cover** — the sparsest has 6.

---

## 1. The instance

Let `C` be the hexagons already met by an open orbit and `U = 120 ∖ C`. From Round 77,
`COLLISIONS(s) = 5·O − |C| ≤ 5`, and this round's population sits at exactly 5.

* A newly opened orbit with a port in `C` raises a `c(h)` that is already ≥ 1, adding a
  collision — forbidden. So **every future orbit's 5 hexagons lie in `U`**.
* Two future orbits sharing a hexagon likewise add a collision. So the chosen blocks are
  **pairwise disjoint**.
* Every hexagon must end covered, so their **union is `U`**.

```
|U| = 120 − (5·O − 5) = 5·(25 − O) = 5K
```

so `K` disjoint 5-blocks inside a `5K`-element set that cover it — an **exact cover**, with no
slack anywhere. The identity is not assumed: it was checked on every one of the 33,564 states,
**0 failures**.

**Canonicalisation.** A block lies inside `U` only if its orbit is still closed (an open
orbit's hexagons are all in `C`), so the candidate family — and hence the whole instance — is a
function of **`U` alone**. `frozenset(U)` is a complete key. In practice the residual is very
finely stratified: 33,564 states give **33,255 distinct instances** (largest multiplicity 4),
so canonicalisation saved little here, but it makes the certificate archive one row per
instance.

`K` ranges over 15–21: `{15: 1234, 16: 7254, 17: 12135, 18: 9104, 19: 3411, 20: 419, 21: 7}`.

## 2. Necessary tests, cheapest first

| test | what it requires | instances | **states closed** |
|---|---|---|---|
| **A · coverability** | every `h ∈ U` lies in some block ⊆ `U` | 24,309 | **24,419** |
| **B · supply** | at least `K` candidate blocks exist | 0 | 0 |
| **C · forced conflict** | a hexagon with a unique supplier forces that block; forced blocks must be pairwise disjoint | 5,244 | **5,315** |
| **D · component / Hall** | every component size is a multiple of 5 and holds ≥ size/5 blocks | 0 | 0 |
| **E · exact cover UNSAT** | complete Algorithm X finds no cover | 3,570 | **3,682** |
| **SAT survivors** | | 132 | **148** |
| **UNKNOWN (node cap)** | | **0** | **0** |

**Test A alone closes 72.8 %.** The reason is structural: with `|U| ≈ 85` of 120 hexagons, an
orbit's five hexagons all landing inside `U` is already unlikely, so many hexagons in `U` have
no surviving supplier at all. Uncoverable-hexagon counts run 1–16 per instance.

Test C is the second-largest: forced blocks number 2–21 per instance, and once several
hexagons each have a single supplier, two of those suppliers overlap.

Tests B and D never fired. Reporting them as 0 rather than dropping them: supply is never the
binding constraint at these sizes, and the component structure is almost always a single
component (3,549 of 3,570 UNSAT-by-search instances are connected).

## 3. Why the searches are trustworthy

Max search: **28 nodes** under MRV, 16,732 nodes in total across all instances. That is small
enough to demand proof that the solver is not vacuously failing, so four checks were run:

| check | result |
|---|---|
| **positive control** — must find an exact cover of all 120 hexagons | **found**, 24 blocks, verified to partition all 120, 24 nodes |
| **negative control** — a 119-point instance | 0 solutions, search completed |
| **UNSAT re-decision with a different variable order** (plain `min`, no MRV) on **all 3,570** UNSAT-by-search instances | **0 disagreements**, max 7,768 nodes |
| **SAT witnesses verified literally** — 132 instances | every witness is `K` pairwise-disjoint blocks whose union is exactly `U`; **0 invalid** |

The node counts are small because propagation is violent: after two or three blocks are placed,
MRV finds a hexagon with zero remaining suppliers. **No instance hit the node cap**, so no
UNSAT verdict rests on a timeout.

## 4. `E¹` safety

Round 77 established that `E¹` preserves `O`, coverage and collisions. The instance must
therefore be `E¹`-invariant, and this was checked directly rather than inferred: over **763
`COLLISIONS = 5` states and 1,402 `E¹` steps**, the uncovered set `U` changed **0 times** and
the candidate block family changed **0 times**. The formulation needs no repair.

This is the point of the whole construction: the obstruction lives entirely in *which orbits are
open*, which is exactly the coordinate `E¹` cannot move.

## 5. Why the 148 survive

| | |
|---|---|
| states / instances / classes | 148 / 132 / **98** |
| **unique-cover survivors** | **0** |
| exact covers per instance | min **6**, max **404**, all counted to completion |
| connected components | 123 instances single-component, 9 split into two |
| forced blocks | 87 instances have **none** |

The survivors are not near-misses. Every one has at least six exact covers, and 22 instances
have 116 covers each. They survive because their `U` happens to be *cover-rich*, not because
some delicate structure barely holds. Their coordinates are unremarkable relative to the band —
`P ∈ {13,14}` split 74/74, `O` peaking at 7–8, `r = 0` for 145 of 148, spread across all five
short roots — so no single coordinate predicts survival.

**The honest reading:** the exact-cover test is close to saturated. Squeezing the last 148 will
not come from a better cover argument; it needs a constraint the static incidence system does not
see — the *order* in which those `K` orbits can legally be opened, or their interaction with the
fragment-repair obligation. That is a genuinely different mechanism.

## 6. Payoff report

| | |
|---|---|
| `COLLISIONS = 5` input | **33,564** |
| distinct exact-cover instances | **33,255** |
| closed by coverability | **24,419** |
| closed by forced-orbit conflict | **5,315** |
| closed by Hall-type / component conditions | 0 |
| closed by exact-cover UNSAT | **3,682** |
| **total closed** | **33,416 (99.56 %)** |
| SAT survivors | **148** |
| unique-cover survivors | **0** |
| **total Q2 residual after this round** | **44,798** in **1,050 classes** |

Roots: `long_q1_2` clears, so **26 of 33 roots have empty Q2 residual**. The remaining residual
is `short_ell3` 15,244 · `short_ell2` 10,914 · `short_ell4` 9,220 · `short_ell1` 7,278 ·
`short_ell0` 2,131 · long roots 11.

**Strongest structural pattern among survivors.** The surviving residual is now defined by
`COLLISIONS ≤ 4`: `{1: 1001, 2: 5369, 3: 13446, 4: 24834, 5: 148}`. The `COLLISIONS = 5` layer
has essentially been removed as a population, and what remains is states that still hold
collision slack — precisely the states for which the exact-cover argument degenerates into a
*bounded-excess* cover.

**Next target, stated but not claimed.** Generalise to `COLLISIONS = c < 5`: the future orbits
may add up to `5 − c` further collisions, so the requirement becomes "cover `U` with `K` blocks
of total excess ≤ `5 − c`". That is the same machinery with slack, and it applies to 44,650
states — the entire remaining residual. Nothing here establishes it.

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
