# Fragment repair is not the bottleneck — but the round proved the blocked-w2 lemma

**Author:** Claude (independent verification track)
**Round:** 83
**Reproducer:** `src/probe_rr_port_occupancy.py` (state loading), `tests/test_blocked_w2_lemma.py`
**JSON:** `outputs/rr_fragment_repair_claude.json`
**Baseline:** 6,657 residual states — **unchanged**.
**Scope:** Q2 / Area-A. States fetched by Round-80 provenance from the stored checkpoints; no
frontier replay, no path search.

---

## Result, up front

> **Closure: 0.** Every residual state has `F = 1`, so **no further abandonment is legal** —
> and fragment creation *requires* an abandonment. There is therefore no fragment-creation
> obligation to charge: `M_def = 0` for all 6,657 states, and the payoff gate stops the round.
>
> **The round's actual product is a proof.** The `N_exceeded_monotone` prune — Q1-SAFE and used
> by every search in this repository — rests on the *blocked-w2 lemma*, which the repo cited
> from prior work and explicitly recorded as *"a bounded empirical check, not a proof"*. It now
> has a hand-proof from engine semantics, plus a regression test.

---

## 1. Exact transition taxonomy, from engine semantics

`extend()` registers (`om[q] |= 1<<phase`) on **every** move of weight ≥ 2 and never on a
weight-1 rotation; `initial_state` registers its endpoint. `abandonment` is
`not visited(σ(p'))`, evaluated at the pre-joint endpoint and only for weight ≥ 2. Hence
`ΔNdef = dS + dF − dO` with `dS = [w≥3]`, `dF = [abandon]`, `dO = [new orbit]`.

Two notions must be kept apart, and §1 of the brief is right to ask:

* **Fragment** (hexagon-level) — `f1_normal_form`'s `fragment_hex`, the unique non-current
  partially visited hexagon. **Created only by an abandonment** (`F: 0→1`); repaired when a
  later joint re-enters it and the pass fills it.
* **`Ndef = S + F − O`** (resource-level) — a different quantity entirely, and the one the
  monotone prune tracks.

| `w` | abandon | new orbit | `dF` | `dS` | `dO` | **ΔNdef** | name | fresh? | re-entry? | observed (admissible) |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | F | F | 0 | 0 | 0 | **0** | `Z2` | no | yes | 112,105 |
| 2 | F | **T** | 0 | 0 | 1 | **−1** | **FORBIDDEN** | yes | no | **0** |
| 2 | T | F | 1 | 0 | 0 | +1 | `A2` | no | yes | 217 |
| 2 | T | T | 1 | 0 | 1 | **0** | `Z2abandon` | yes | no | 17,408 |
| 3 | F | F | 0 | 1 | 0 | +1 | `R` | no | yes | 91,564 |
| 3 | F | T | 0 | 1 | 1 | **0** | `Z3` | yes | no | 224,495 |
| 3 | T | F | 1 | 1 | 0 | +2 | `J` | no | yes | 1,013 |
| 3 | T | T | 1 | 1 | 1 | +1 | `A3` | yes | no | 47,506 |

Counts are from 2,647,489 macro edges over 120,000 expanded nodes. **The forbidden row occurs
0 times — including 0 times among *pruned* transitions**, so it is absent structurally rather
than filtered out.

## 2. The blocked-w2 lemma, proved

> **Lemma.** A weight-2 joint cannot open a fresh orbit without an abandonment. Equivalently,
> the row `(w = 2, abandonment = False, new_orbit = True)` is empty.

**Geometric fact** (exhaustive: all 720 words × 6 rotation lengths, 0 exceptions). The w2 target
`t` and the blocking window `σ(p')` — the window whose visitation decides `abandonment` — always
lie in the **same E-orbit**, with `t` exactly one phase past the blocker:

```
t = E( σ(p') )
```

So the blocker is itself a port of the target's orbit. That is what couples the two conditions.

**Proof.** A window becomes visited in exactly three ways: as a joint target (weight ≥ 2, hence
**registered**), as the initial endpoint (registered), or as a rotation target. A rotation
reaches `blocker = σ(p')` only from `p'`. By the no-repeat rule `p'` is visited exactly once,
and that visit is the current one, at the end of the current rotation run — which has not gone
past `p'`. So a visited blocker cannot have been rotation-visited; it is registered. Being a
port of the target's orbit, it makes that orbit open, so `new_orbit` is False. ∎

At `ℓ = 5` the blocker is `p` itself — the pass entry, a joint target — which is also exactly
why `E¹` preserves the orbit.

**Consequences.** `ΔNdef ≥ 0` for every legal macro joint; `Ndef` is monotone non-decreasing;
**`N_exceeded_monotone` is sound**. Pinned by `tests/test_blocked_w2_lemma.py` (5 tests: the
geometric identity, the `ℓ=5` corollary, the sign of every row, and engine agreement over
real macro edges).

This is the one place in the stack that rested on an unproved citation. It no longer does.

## 3. Why fragment repair cannot be the bottleneck

**Every residual state has `F = 1`** — measured on all 6,657, not inferred. So:

* no further abandonment is legal (`F_exceeded`), hence **no new fragment can ever be created**;
* combined with the lemma, the remaining joint alphabet is exactly
  `{rotation, Z2 (w2 → open, ΔNdef 0), Z3 (w3 → fresh, ΔNdef 0), R (w3 → open, ΔNdef +1)}`;
* in particular **every one of the `K` remaining openings must be a `Z3`**, at `ΔNdef = 0`.

The single existing fragment is the unique doubly-passed hexagon already accounted for by the
Round-77 collision identity and the Round-78/79 cover machinery. There is no *new* obligation
to charge.

## 4. Zero-defect test — `M_def = 0` everywhere

Over-approximating availability (any word, any rotation length, any of the three w3 joints):

| | |
|---|---|
| orbits admitting a `Z3` opening | **144 of 144** |
| source orbits per target | **56**, uniform |
| candidates with no zero-defect opening, per state | **0**, for all 6,657 |

So there is a cover solution with **zero unavoidable defect creation** for every state. Per the
payoff gate, stages C (repair supply) and D (matching / flow) were **not attempted** — there is
no creation obligation for them to operate on.

## 5. Adversarial checks

| check | result |
|---|---|
| weight-2 fresh-orbit opening with no abandonment (Round 81's explicit warning) | 0 in 2.6M macro edges — and now **proved impossible**, not merely unobserved |
| any negative `ΔNdef` row | exactly one, `(2, F, T)`, which is the forbidden one |
| `E¹`/`E²` interactions | `E¹` is the `ℓ=5` instance of `Z2` (`ΔNdef = 0`), `E²` of `R` (`+1`); neither abandons, so neither can create or repair a fragment |

Round 81 recorded that "weight-2 fresh-orbit opening is not automatically forbidden by
abandonment semantics" — correct as stated, since `extend()` gates neither flag. The
*structural* exclusion comes from the orbit geometry plus no-repeat, which is what this round
supplies.

## 6. Diagnostics and ledger

| | |
|---|---|
| input states | 6,657 |
| **closed** | **0** |
| UNKNOWN | 0 |
| minimum unavoidable defect count | **0** in every state, in every `c` band |
| opening type responsible | `Z3` throughout — the only legal opening once `F = 1` |
| Q2 residual | **6,657** — unchanged |

Fragment structure has **no headroom**: the obligation does not exist, because the budget that
creates it is already spent. The next bottleneck is not here.

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
