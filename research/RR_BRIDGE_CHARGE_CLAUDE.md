# BRIDGE-CHARGE — payoff test: `r = 0` is nearly universal, and the first bridge is free

**Author:** Claude (independent verification track)
**Round:** 76
**Reproducer:** `src/probe_rr_bridge_charge.py` (`types` / `census` / `witness`)
**JSON:** `outputs/rr_bridge_charge_claude.json`
**Baseline:** 200,408 proof-valid Q2 residual states, 1,570 canonical classes.
**Scope:** Q2 / Area-A. No search, no frontier re-run, no bounded continuation used as
impossibility evidence.

---

## Result, up front

> **The lemma is refuted, and the payoff is 0.** `r = 0` is not rare — it is **196,056 of
> 200,408 (97.83 %)** of the residual, so the candidate had real leverage: had the lemma
> held it would have closed **83,914 states (41.9 %)**. But there is exactly **one**
> transition type that raises `r` from 0 to 1 at zero cost in every globally charged
> resource — `ℓ = 5, w2:10`, i.e. `E¹` — and it is **realised**: 10 stratified residual
> states have a Q2-admissible zero-cost bridge child, and an independent 3-edge walk from
> `initial_state` reproduces the event from scratch.
>
> Creating the first bridge costs **nothing** in `Φ`, `Ndef`, `O` or `F`. The one thing it
> does consume — a single within-orbit registration out of `5 − used(q0)` — is *exactly*
> what `capacity_slack` already charges every joint, so the event is **capacity_slack-neutral**.

---

## 1. The premise, re-derived from engine semantics (HP)

`T` = touched hexagons (`hex_masks[h] ≠ 0`), `P` = registered pass-starts, `r = P − |T|`.

`extend()` sets `hm[h] |= 1<<bit` on **every** transition and `om[q] |= 1<<phase` **only**
when `move.weight ≥ 2`. Hence `dr = dP − dT` and:

| transition | `dP` | `dT` | `dr` |
|---|---|---|---|
| weight-1 rotation (target `σ(p)`, same hexagon, already touched) | 0 | 0 | **0** |
| weight ≥ 2 joint into a **fresh** hexagon | 1 | 1 | **0** |
| weight ≥ 2 joint into an **already-touched** hexagon | 1 | 0 | **+1** |

So `r` is non-decreasing, it rises **only** on a joint landing in a touched hexagon, and at
an Area-A NR6 completion `P = 121` with all 120 hexagons touched gives
**`r_final = 1` exactly**. Every `r = 0` state must therefore still create exactly one bridge.
The premise is sound. (It also reproduces Round 69's `6r ≤ 11 − Φ` directly: `visited ≤ 6|T|`
with `visited = 6P + Φ − 11`.)

## 2. Census of the 200,408 residual (no frontier re-run)

Read back from the stored checkpoint frontiers, replaying the Round-71 chain verbatim
(`capacity_slack` 2,956,692 → dead-port 19,073 → orbit-reentry 72,717 → **residual 200,408**,
reproduced exactly).

| | `r = 0` | `r = 1` |
|---|---|---|
| **states** | **196,056 (97.83 %)** | 4,352 (2.17 %) |
| canonical classes | 1,475 | — (1,570 total) |

**`r = 0` is not rare.** The first stop-rule branch does not fire.

| coordinate | `r = 0` | `r = 1` |
|---|---|---|
| `P = 13` | 93,172 | 86 |
| `P = 14` | 102,715 | 4,266 |
| `P ∈ {20,21}` | 169 | 0 |
| `Φ = 0` | **0** | **4,169** |
| `Φ = 1 … 4` | 116,209 | 183 |
| `Φ = 5` | **79,847** | **0** |
| `O = 7…10` | 182,995 | 147 |
| `R_cap = 3` | 195,887 | 4,352 |
| `D_dead = 0…4` | 40,655 / 63,462 / 50,251 / 29,174 / 12,514 | 1,429 / 1,573 / 878 / 388 / 84 |

Two clean **bounded observations** (BO, corpus-only — not theorems): every `Φ = 5` residual
state has `r = 0`, and every `Φ = 0` residual state has `r = 1`. The first direction is forced
by `6r ≤ 11 − Φ` only at `Φ ≥ 6`; at `Φ = 5` it is tight but permissive, so both are
observations, not consequences.

`r = 0` states by root: `short_ell4` 79,727 · `short_ell3` 60,934 · `short_ell2` 34,349 ·
`short_ell1` 15,192 · `short_ell0` 5,685 · long roots 169.

**Resource slack at `r = 0`.** `capacity_slack` margin: 2,209 states at 0, 5,193 at 1,
7,555 at 2, 15,815 at 3, 22,569 at 4. Orbit-re-entry margin `(R_cap + Φ) − need`:
**83,914 at exactly 0**, 58,839 at 1, 33,949 at 2.

**Payoff had the lemma held** (charging one unit of the shared `R_cap + Φ` currency to every
`r = 0` state): **83,914** by orbit-re-entry alone, 30,772 by `capacity_slack`, 12,514 by the
dead-port budget. A genuinely large target — which is why it was worth auditing rather than
assuming.

## 3. Exhaustive classification of every `r: 0 → 1` transition type

A macro edge is `ℓ` rotations plus one joint from `{w2:10, w3:120, w3:201, w3:210}`. Rotations
never change `r`, so the classification is complete over `(ℓ, joint, joint_kind)`.
`ΔΦ = ℓ − 5` (six windows' worth of `Φ` per registration, `ℓ + 1` windows gained);
`ΔNdef = [w≥3] + [abandon] − [new_orbit]`. At `ℓ = 5`, `σ(p′) = p` is visited, so abandonment
is impossible.

**Geometry check first:** across all 720 words × 6 rotation lengths × 4 joints, **no joint ever
lands in the current hexagon**. So "target hexagon already touched" is a genuine state
predicate, never automatic — and never impossible.

| `ℓ` | joint | kind | `ΔΦ` | `ΔNdef` | `ΔO` | `ΔF` | cost in `R_cap + Φ` |
|---|---|---|---|---|---|---|---|
| **5** | **`w2:10`** | **`Z2` = `E¹`** | **0** | **0** | **0** | **0** | **0** |
| 5 | `w3:120/201/210` | `Z3` | 0 | 0 | **1** | 0 | 0 |
| 5 | `w3:120/201/210` | `R` | 0 | **1** | 0 | 0 | 1 |
| 4 | `w2:10` | `Z2` | −1 | 0 | 0 | 0 | 1 |
| 4 | `w2:10` | `Z2abandon` | −1 | 0 | 1 | **1** | 1 |
| ≤ 4 | any | any | `ℓ−5` | 0 or 1 | 0 or 1 | 0 or 1 | 1 … 6 |

**Exactly one type is free in every budgeted resource: `(ℓ = 5, w2:10) = E¹`.** The `ℓ = 5`
`Z3` row is free in the shared currency and costs one orbit **opening** — which an Area-A
completion must perform 25 times regardless, so it is not a surplus charge either.

## 4. The refutation — literal witnesses

**On corpus.** Over a 4,000-state stratified sample of `r = 0` residual states (≤ 3 per
canonical class, covering the `r = 0` class space), one-step macro enumeration with the exact
engine finds **10 states with a Q2-admissible zero-cost `r: 0 → 1` child**, every one of them
`rot^5;w2:10`, kind `Z2`, orbit-preserving, target-hexagon popcount 1–3 before the joint:

| root | edge | `Φ` | `Ndef` | `O` | `F` | `P` | `T` | `r` | `used(q0)` |
|---|---|---|---|---|---|---|---|---|---|
| `short_ell0` | `rot^5;w2:10` | 1 → **1** | 0 → **0** | 5 → **5** | 0 → **0** | 13 → 14 | 13 → 13 | 0 → **1** | 1 → 2 |
| `short_ell0` | `rot^5;w2:10` | 1 → **1** | 0 → **0** | 7 → **7** | 0 → **0** | 13 → 14 | 13 → 13 | 0 → **1** | 3 → 4 |

A further 14 sampled states reach `r = 1` at zero shared cost via an `ℓ = 5` `Z3`, paying only
a mandatory orbit opening.

**Independent, from scratch.** Not trusting the corpus decoding, a second witness was built
from `exact.initial_state()` with the exact engine, found after 31 node expansions:

```
rot^0;w3:120  →  rot^5;w3:120  →  rot^5;w2:10
```

| | `P` | `visited` | `O` | `T` | `Ndef` | `Φ` | `F` | `r` |
|---|---|---|---|---|---|---|---|---|
| before the last edge | 3 | 8 | 2 | 3 | 2 | 1 | 1 | **0** |
| after | 4 | 14 | 2 | 3 | 2 | **1** | 1 | **1** |

`joint_kind = Z2`, `abandonment = false`, `new_orbit = false`, orbit preserved, target hexagon
popcount 1 → 2, `used(q0)` 2 → 3. **`ΔΦ = ΔNdef = ΔO = ΔF = 0`.**

> **The first bridge can be created for free. The lemma is false.**

*(The 3,750 sampled states with no one-step `r: 0 → 1` child are **not** evidence of anything:
a bridge may be created at any later depth, and bounded continuation is not impossibility.
Only the positive witnesses are used.)*

## 5. Why the fallback reading also gives nothing

The natural retreat is "the bridge event must consume *something*". It does: one pass-start,
registered in `q0`, drawn from the `5 − used(q0)` term. But `capacity_slack` is

```
TARGET_P − P  ≤  (5 − used(q0)) + 5·O_rem + 4·(R_cap + Φ)
```

and an `E¹` bridge decrements the left side by 1 and the `(5 − used(q0))` term by 1
simultaneously — verified in every witness (`P` 13 → 14 while `used(q0)` 1 → 2). **The event is
exactly slack-neutral.** It is neither undercharged nor overcharged; the bound already prices
it correctly. `ORBIT-REENTRY` charges orbit-*changing* joints, and `E¹` changes no orbit, so it
correctly charges nothing.

This is the brief's second stop condition — *the cost is already fully charged by existing
inequalities* — reached from the other side. Either way: **no payoff, 0 states closed.**

## 6. What survives, and what this rules out

**Survives as a proved fact (HP + engine-verified):** `r` is monotone with `dr ∈ {0,1}`; `r`
rises exactly on a joint into a touched hexagon; `r_final = 1` exactly at Area-A completion;
no joint ever lands in the current hexagon at any rotation-run length; exactly one macro
transition type is free in all of `Φ, Ndef, O, F`, namely `E¹`.

**Ruled out:** any bound of the form "reaching `r = 1` costs an extra unit of `Φ`, `Ndef`,
`R_cap + Φ`, `O` or `F`". A single legal witness kills the universal claim, and there are 11.

**The pattern, now three rounds deep.** Round 74 (per-orbit segment capacity), Round 75
(inter-orbit sequencing) and now Round 76 (bridge charge) all fail the same way: the quantity
being counted is either already priced by `capacity_slack` or freely obtainable via the two
free generators `E¹` and `ℓ=5` `Z3`. **`E¹` is the recurring culprit** — an orbit-preserving,
`Φ`-free, `Ndef`-free, `O`-free registration. Any future candidate should be tested against
`E¹` *first*: if `E¹` can realise the event the candidate forbids or charges, the candidate is
dead before the residual is consulted. That is a one-line pre-filter and it would have settled
this round in minutes.

## 7. Ledger

| | |
|---|---|
| Q2 residual (unchanged) | **200,408** |
| canonical classes (unchanged) | **1,570** |
| `r = 0` share of the residual | **196,056 (97.83 %)** |
| payoff had the lemma held | 83,914 (41.9 %) |
| **states actually closed** | **0** |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
