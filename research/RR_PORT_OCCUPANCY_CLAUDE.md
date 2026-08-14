# Port occupancy really does pin the phase — and it closes nothing, with a measured ceiling of 13

**Author:** Claude (independent verification track)
**Round:** 82
**Reproducer:** `src/probe_rr_port_occupancy.py census`
**JSON:** `outputs/rr_port_occupancy_claude.json`
**Baseline:** 6,657 residual states — **unchanged**.
**Scope:** Q2 / Area-A. States fetched by their Round-80 `(root, idx)` provenance straight out
of the stored checkpoint frontiers — a lookup of preserved data, not a frontier replay; nothing
is expanded, searched or re-generated. No continuation solver was built.

---

## Result, up front

> **Closure: 0 of 6,657.** But the interesting part is *why*, and it is not the reason the last
> three rounds failed.
>
> **Port occupancy genuinely pins the phase.** 448 states cannot move phase at all; the maximal
> `E¹` chain is 4, exactly as Round 77 saw; and from a pinned phase closure only **4–54** of a
> ~130-orbit candidate family are openable.
>
> **It still closes nothing, and the ceiling is measured, not conjectured.** Under a
> deliberately *unsound* strengthening that forbids **all** phase repair — assuming `E¹` and
> `E²` away entirely — the first-open test closes **13 of 6,657 (0.20 %)**. Allowing the true
> phase closure drops that to **1**.
>
> So `E¹` costs this direction 12 states. The direction was worth at most 13 to begin with.

---

## 1. Literal `E¹` availability

`E¹ = (ℓ=5, w2:10)` and `E²= (ℓ=5, w3:120)` are the orbit-preserving macro edges, advancing the
phase by `+1` and `+2`. Both require a full five-step rotation run — legal exactly when the
current hexagon holds only the endpoint — and both require their joint target unvisited. These
are taken from the engine itself (`macro.rotation_runs` + `exact.extend`), never inferred from
orbit identity. `E²` is included because every residual state has `Ndef = 0`, **verified from
the preserved ledger** before use.

`PhaseClosure(s)` is the set of `q0` positions reachable by any sequence of orbit-preserving
macro edges. Until the walk leaves `q0` these are its only moves, so **the first orbit-changing
edge of any continuation departs from this set** — that is what makes it the right object.

## 2. The closure census

| `|PhaseClosure|` | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| states | **448** | 737 | 1,160 | 1,787 | 2,525 |

| maximal consecutive `E¹` chain | 0 | 1 | 2 | 3 | 4 | >4 |
|---|---|---|---|---|---|---|
| states | 493 | 748 | 1,142 | 1,749 | 2,525 | **0** |

**Round-77 cross-check: the chain never exceeds 4**, exactly as observed there. The histogram is
**identical** with and without the Area-A prune applied — the prune never blocks an `E¹` step in
this residual, so the closure is decided purely by the no-repeat rule.

`E²` earns its place: 448 states have `PhaseClosure` size 1 while 493 have `E¹`-chain 0, so **45
states have `E¹` blocked but `E²` available**. Omitting `E²` would have manufactured 45 false
pins.

## 3. Phase-pinned first-open test

Two versions, which must not be confused:

* **`NEXT_pinned`** — openable from `PhaseClosure(s)` only. Range **4–54**. This is a
  **diagnostic**: closing on it would be unsound, because the walk may re-enter another
  already-open orbit first and open from there.
* **`NEXT_sound`** — the above plus everything openable from any open orbit reachable through
  open orbits, with the arrival phase over-approximated to all five. Range **15–80**. Only this
  may close a state.

| classification | states |
|---|---|
| no legal phase | 0 |
| `E¹` repair exists but no fresh orbit openable | 0 |
| fresh orbit openable but none in any valid slack cover | 0 |
| **cover-compatible next opening** | **6,657** |

Cover compatibility is decided exactly — force `q` into the cover and re-decide the Round-79
instance on `U ∖ block(q)` with `K−1` blocks and slack `b − waste(q)`.

**Closure: 0. UNKNOWN: 0.** Per the payoff gate, stages C (`E¹` depletion) and D (phase-level
continuation solver) were **not attempted**.

## 4. Diagnostics, including the ones that decide the direction

| question | answer |
|---|---|
| states where the current phase alone is dead | **0** |
| states where all `E¹`-reachable phases are dead | **0** |
| `NEXT` from the *current phase only* | 1–17, median ≈ 15 |
| correlation with `c` / slack | **none** — every state in every band `c = 1…5` lands in the same class |

### The ceiling measurement

The question the whole round exists to answer: how much could this direction *ever* be worth?
Measured by deliberately unsound strengthenings:

| strengthening | states it would close |
|---|---|
| pinned to `q0`'s true phase closure (ignores re-entry) | **1** |
| **no phase repair at all** — current phase only, `E¹`/`E²` assumed away | **13** |

**13 of 6,657 is the hard ceiling on everything in this family.**

## 5. Why it fails — and it is not `E¹` this time

The last three rounds died because `E¹` repaired the thing being charged. That is *not* what
happened here: the pin is real, and giving it up costs only 12 states.

The actual cause is the one Round 81 measured and this round confirms from the other side:

> A first-open test can close a state only when **every** orbit it can open is cover-incompatible.
> The median state has **128 of 144** orbits individually cover-compatible, because SLACK-COVER
> constrains which `K`-subsets work, not which single orbits are usable. With ~90 % of orbits
> individually usable, and 1–17 openable even from a completely pinned single phase, at least one
> is cover-compatible in **6,644 of 6,657** states.

So: **first-open tests are exhausted at every refinement level** — orbit (Round 81) and
`(orbit, phase)` + occupancy (this round). Refining the *position* cannot help, because the
weakness is in the *predicate*, not the resolution.

## 6. What would actually be needed

1. **A condition on a sequence or a set, not on the next single step.** The cover is a set
   constraint; only a set or sequence constraint can interact with it. Every first-open variant
   is now measured to be worth ≤ 13 states.
2. The concrete leak in `NEXT_sound` is re-entry into another open orbit with the arrival phase
   over-approximated to all five. The arrival phase is in fact *determined* by the entering
   joint, so a phase-exact multi-step relation is constructible — but that is the phase-level
   continuation solver the brief defers, and it would still face the set-versus-step problem
   above.
3. **Fragment repair** — deliberately deferred by the brief until the occupancy test was
   exhausted. It now is.

No exclusion was invented to manufacture payoff; the pinned and no-repair numbers are reported
precisely because they are *unsound*, to bound the direction rather than to close states.

## 7. Ledger

| | |
|---|---|
| Q2 residual | **6,657** — unchanged |
| closed this round | **0** |
| UNKNOWN | **0** |
| canonical classes | 761 — Claude-computed, **not** independently audited |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
