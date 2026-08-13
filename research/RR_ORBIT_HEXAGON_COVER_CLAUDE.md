# Quotienting out `E¹`: the orbit–hexagon cover is the obstruction it cannot repair

**Author:** Claude (independent verification track)
**Round:** 77
**Reproducer:** `src/prove_rr_orbit_hexagon_cover.py` (`geometry` / `feasibility` / `monotonicity` / `e1` / `census`)
**JSON:** `outputs/rr_orbit_hexagon_cover_claude.json`
**Baseline in:** 200,408 residual states, 1,570 canonical classes.
**Baseline out:** **78,214 residual states, 1,312 canonical classes.**
**Scope:** Q2 / Area-A. No search, no frontier re-run, no bounded completion search. Corpus
statistics measure payoff only — no congruence or parity claim is derived from them.

---

## Result, up front

> **`E¹` is not an unbounded free escape.** It advances the phase by +1 on `q0`'s 5-cycle, so
> its closure has **at most 5 states** (observed chain lengths 0–4, never more), and each step
> requires a fresh hexagon.
>
> Quotienting it out leaves one quantity it provably cannot touch: the **orbit–hexagon
> incidence**. An Area-A completion forces the 25 open orbits to cover all 120 hexagons with
> total excess exactly 5. That inequality is **invariant under every one of 7,332 `E¹` steps**
> and it closes **122,194 of the 200,408 residual states — 60.97 %**.

---

## 1. `E¹`, quotiented

`E¹` = the macro edge `(ℓ = 5, w2:10)`, joint kind `Z2` — the unique generator free in `Φ`,
`Ndef`, `O` and `F` (Round 76).

**Legality.** `ℓ = 5` needs five legal forward rotations, i.e. the current hexagon must hold
*only* the endpoint `p`. Agreement between `pc(hex(p)) == 1` and `ℓ_max == 5`: **4,000 / 4,000**
residual states, and all 4,000 have `ℓ_max = 5`.

**The closure is small.** `E¹` sends phase `φ ↦ φ+1` inside `q0`, and the sixth step would target
an already-registered — hence visited — port. So **at most 4 consecutive `E¹` moves**, and each
one must land in a fresh hexagon or the chain stops. Measured closure lengths:

| chain length | 0 | 1 | 2 | 3 | 4 | >4 |
|---|---|---|---|---|---|---|
| states | 897 | 916 | 802 | 728 | 657 | **0** |

That already answers the framing question: "free `E¹` motion" is bounded, not arbitrary.

### Every candidate quantity, classified over 7,332 `E¹` steps

| quantity | observed Δ | class |
|---|---|---|
| `O` (open orbits) | `{0}` | **invariant** |
| `Φ`, `Ndef`, `R_cap`, `R_cap+Φ`, `F` | `{0}` | **invariant** |
| **`covered_hexagons`** | `{0}` | **invariant** |
| **`incidence_collisions`** | `{0}` | **invariant** |
| `dead_port_count` | `{0: 5627, 1: 1509, 2: 165, 3: 30, 5: 1}` | monotone ↑ (worsens) |
| `r` | `{0: 7317, 1: 15}` | monotone ↑ |
| `used(q0)` | `{+1}` | monotone ↑ (caps the chain) |
| `touched_hexagons`, `full_hexagons`, `P` | `{+1}` mostly | monotone ↑ |
| `partial_hexagons`, `noncurrent_partial`, `hexagon_deficiency` | `{−1/−6, 0}` | monotone ↓ |
| `D = 5O − P` | `{−1}` | **freely repairable** |
| `orbit_reentry_demand` | `{−2: 3, −1: 7, 0: 6673, 1: 640, 2: 9}` | **freely repairable** |
| `phase_of_p` | `{+1, −4}` | cycles (the 5-cycle) |

`D` and the re-entry demand are exactly the quantities Rounds 74–76 tried to charge — and `E¹`
moves both in the helpful direction for free. **`O`, coverage and collisions are the ones it
cannot touch.** That is where the theorem has to live.

## 2. The geometry (EC, exhaustive)

| | |
|---|---|
| distinct hexagons per orbit | **5**, for all 144 orbits — zero self-collisions |
| orbits meeting each hexagon | **6**, for all 120 hexagons |
| total (orbit, hexagon) incidences | **720** |

The orbit–hexagon incidence is a biregular bipartite graph, degrees 5 and 6. Every permutation
is a port of exactly one orbit, and the 6 windows of a hexagon lie in 6 *different* orbits.

## 3. ORBIT-HEXAGON COVER (HP, from engine semantics)

> **Theorem.** For `c_open(h)` = the number of open orbits meeting hexagon `h`, every state on a
> path to an Area-A NR6 completion satisfies
> ```
> COLLISIONS(s) = Σ_h max(c_open(h) − 1, 0) = 5·O − |covered(s)| ≤ 5
> ```
> equivalently `120 − |covered(s)| ≤ 5·(25 − O)`.

*Proof.*
1. `area_a_final` requires `visited_count == 720`, so **every** hexagon ends full.
2. A rotation never leaves the current hexagon, so a hexagon is entered only by a joint landing
   in it (or by being the initial hexagon).
3. Every joint in the macro layer has weight 2 or 3, and `extend` sets `om[q] |= 1<<phase` for
   the target whenever `weight ≥ 2`; `initial_state` registers `p`. So **every hexagon contains
   at least one registered port**, hence `c(h) ≥ 1` for all 120 hexagons at the completion.
4. The completion has `O = 25`, and each orbit's 5 ports lie in 5 distinct hexagons (§2), so
   `Σ_h c(h) = 125`.
5. With every term ≥ 1, `Σ_h (c(h) − 1) = 125 − 120 = 5`.
6. Orbit masks are only ever set, never cleared, so the open set grows monotonically and
   `c_open(h) ≤ c_final(h)` pointwise; `max(·−1, 0)` is monotone, so the sum is bounded by 5 at
   every earlier state. ∎

It is **demand-side**: it constrains which orbits must end up open, never how far a walk can
travel. `q0` return, repeated re-entry and entry multiplicity are all irrelevant to it — the
Round-73 failure mode cannot recur here.

**In words:** an Area-A completion must pick 25 orbits that almost exactly cover the 120
hexagons — 125 incidences for 120 hexagons, so at most 5 hexagons may be reached twice. It is a
near-exact-cover condition, and nothing in the committed stack (`capacity_slack`, dead-port,
orbit-re-entry, `Φ`) looks at incidence at all.

### Adversarial checks, all run before the payoff was measured

| check | result |
|---|---|
| `E¹`-closure invariance (the one this round demanded) | **0 changes in 7,332 steps** |
| identity `COLLISIONS = 5·O − covered` | **0 violations** / 13,336 macro steps, 400 random legal walks |
| monotone non-decreasing along legal walks | **0 violations** / same 13,336 steps |
| **feasibility** — could the bound be vacuously unsatisfiable? | **no**: a 25-orbit set covering all 120 hexagons with excess exactly 5 exists (greedy witness); 24 orbits give a perfect cover |

The feasibility check matters: if no legal 25-orbit cover existed, a 61 % closure would be a
symptom of an error rather than a theorem. One does exist.

**Prior art, stated honestly.** "A fresh segment covers at most 5 hexagons, one per port of its
orbit" is already in `src/verify_rr_target_b_flow.py` (Round-32 capacity) — but in the *supply*
direction, per segment. What is new is the **global** consequence for the final open set, and
that is what bites.

## 4. Payoff on the 200,408 residual

| stage | states |
|---|---|
| Round-71 proof-valid residual | **200,408** |
| closed by **ORBIT-HEXAGON COVER** | **122,194 (60.97 %)** |
| closed by the sharpened cover capacity | **0 further** |
| **residual** | **78,214** in **1,312 classes** |

Collision count on the residual: `{1: 1001, 2: 5369, 3: 13446, 4: 24834, 5: 33564, 6: 36525,
7: 32906, 8: 24452, 9: 15323, 10: 7915, 11: 3463, 12: 1180, 13: 348, 14: 69, 15: 10, 16: 2,
17: 1}` — everything from 6 upward is closed.

Per root — `long_found_4` (66/66), `long_found_9` (54/54) and `long_q1_7` (1/1) are now fully
closed, so **25 of 33 roots have empty Q2 residual**:

| root | `short_ell0` | `ell1` | `ell2` | `ell3` | `ell4` | long roots |
|---|---|---|---|---|---|---|
| closed | 2,329 | 5,074 | 17,326 | 36,055 | 61,268 | 142 |
| surviving | 3,758 | 10,907 | 18,130 | 25,927 | 19,465 | 27 |

The survivors shift down in `O` (peak moves from 8–9 to 7–8) and stay `Ndef = 0` (78,187 of
78,214), `P ∈ {13,14}`, `r = 0` (74,528). Largest class 1,214 (1.55 %).

**Why the sharpened form added nothing.** Replacing `5·(25−O)` by the sum of the `(25−O)`
largest per-orbit contributions is strictly tighter in principle, but on every survivor the top
closed orbits still each reach 5 uncovered hexagons, so the two forms coincide. Reported as 0
rather than folded into the headline.

**Margin.** `33,564 survivors sit at COLLISIONS = 5 exactly` — margin 0. Any sound argument
worth one more unit of incidence closes them, and that is the sharpest lead this round leaves.

## 5. What this changes about method

Three rounds died to `E¹`; quotienting it out first turned a 0 % round into a 61 % one. The
usable rule:

> **Classify a candidate quantity under free `E¹` motion before proposing any inequality on it.**
> `E¹` freely repairs `D`, `P` and the orbit-re-entry demand, so no bound built on those alone
> can bite. It cannot move `O`, coverage or incidence collisions — and the one bound built on
> those closed 61 % of the residual on first measurement.

The general shape: every bound that has ever worked here counts a **resource**; `E¹` is free in
every resource the stack tracks *except* the orbit-set it never touches. Incidence was the one
uncounted resource.

## 6. Ledger

| | before | after |
|---|---|---|
| Q2 residual | 200,408 | **78,214** |
| canonical classes | 1,570 | **1,312** |
| roots with empty Q2 residual | 22 / 33 | **25 / 33** |
| survivors at margin 0 | — | 33,564 |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.** The residual states
remain perfectly good Q1 objects; nothing is deleted, and the bound is a necessary condition for
an Area-A NR6 completion `(P, O, D) = (121, 25, 4)` with `Ndef ≤ 3`, which is its only premise.
