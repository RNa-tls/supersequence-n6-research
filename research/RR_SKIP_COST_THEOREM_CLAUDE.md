# SKIP-COST: the uncharged `E²` resource, proved and evaluated

**Author:** Claude (independent verification track)
**Round:** 72
**Reproducer:** `src/prove_rr_skip_cost.py`
**JSON:** `outputs/rr_skip_cost_claude.json`
**Scope:** Q2 / Area-A. No search was run — this filters states already stored by an earlier
round. No node-capped expansion is used as a proof step.

---

## 1. The adversarial gate, run first

`src/audit_rr_capacity_helpers.py` refuted `true_phase_walk_capacity` on the root
`long_found_142`: the helper **predicted 3** ports where the **engine achieves 4**. The recorded
reason is exact:

> *"the helper rejects offset 3 (phase 4, hexagon 0) because that hexagon has popcount 5, i.e. is
> not entirely unvisited. That rejection is correct for the FULL-SEGMENT question … But it is wrong
> for the PORT-COUNT question: the joint landing needs only its own target permutation free."*

Replaying that exact state through this round's formulation, before using it for anything:

| port of orbit 1 | hexagon | hexagon popcount | **port visited?** | registered? |
|---|---|---|---|---|
| ph0 | 1 | 6 | yes | yes |
| ph1 | 72 | 1 | yes | yes |
| ph2 | 12 | 0 | no | no |
| ph3 | 2 | 0 | no | no |
| **ph4** | **0** | **5** | **no** | no |

`ph4` is exactly the port the old helper threw away for having a non-free hexagon. This round's
reach function asks only whether the *permutation* is unvisited, so it keeps it:

```
retracted helper : 3        this formulation : 4        engine (literal replay) : 4
```

**The gate passes**: the bound is a valid upper bound on the same state that refuted the old one.
Three design rules make this structural rather than lucky — every one of them enlarges the
estimate of what the walk can do, which is the sound direction for an upper bound:

1. only port-level (permutation) visitation is ever tested; hexagon popcount is never consulted;
2. the `ell = 5` rotation-run legality requirement is **dropped**, so segments are credited with
   continuations the engine might refuse;
3. liveness is read at the current state, and visitation only grows, so present reach
   over-estimates all future reach.

## 2. The two engine facts

**FACT 1 — exactly two orbit-preserving generators.** Over all 24 macro generators × 720 words:

| macro edge | acts as | phase shift | `joint_kind` | cost |
|---|---|---|---|---|
| `ell = 5, w2:10` | `E¹` | +1 | `Z2` | free |
| `ell = 5, w3:120` | `E²` | +2 | **`R`, always** | **exactly one unit of `Ndef`** |

and **zero** generators preserve the orbit for some words but not others — there are no partial
cases to reason around.

**FACT 2 — every `E²` edge costs exactly `Ndef` +1.** Structurally: the target lies in the
endpoint's *own* orbit, which already holds the endpoint as a registered port, so `new_orbit` is
false; at `ell = 5` abandonment is false because `σ⁶(p) = p` is visited; hence weight 3 + no
abandonment + no new orbit = `R`. And `R` has `dS = +1, dO = 0, dF = 0`, so
`Ndef = S + F − O` rises by exactly 1. Verified literally on **3,073 / 3,073** `E²` edges taken in a
random legal walk: `joint_kind` `R` every time, `ΔNdef = +1` every time.

**Consequence.** A *segment* — a maximal run of orbit-preserving macro edges — walks its orbit's
5-cycle forward by `+1` (free) or `+2` (one `Ndef`), and every joint target must be an unvisited
permutation. Two consecutive visited ports end the segment.

## 3. Can `E¹` alone cover what a completion needs?

No, not in general, and the reason is the whole point. With `E¹` only, a segment registers a
**consecutive run** of currently-unvisited ports. A segment that must reach a port lying past a
visited one has exactly two options: pay one `Ndef` for an `E²` skip, or end the segment and
re-enter the orbit later — which costs one orbit-changing joint, i.e. one unit of `R_cap + Φ`.

They are substitutes drawn on **the same budget**, and that is the gap in the committed bound:

> `build_rr_target_a_roots.capacity_slack` charges an `R` only when it **changes** the orbit. The
> within-segment `E²` steps consume the identical `Ndef` and are **not charged**.

## 4. The two inequalities

**LIVE-PORT SUPPLY.** Every future joint registers a permutation that is unvisited at the time, and
visitation is monotone, so every future registration is a port unvisited *now*. Registrations in
orbit `q` are therefore capped by `live(q)`, its currently-unvisited port count. The final open set
is the currently-open orbits plus `O_cap = 25 − O` new ones, so

```
B  ≤  Σ_{q open} live(q)  +  (the O_cap largest live(q) over closed orbits)
```

Uses no `Φ`, no capacity theory, no hexagons.

**SKIP-COST.** Let `T = R_cap + Φ`. Every orbit-changing joint into an already-open orbit is either
an `ell = 5` weight-3 edge (an `R`, one `Ndef`) or an `ell < 5` edge (≥ 1 `Φ`) — it cannot be
`ell = 5, w2:10`, which preserves the orbit. Every `E²` skip is an `R`. Hence

```
(orbit-changing joints into open orbits)  +  (E² skips)   ≤   R_cap + Φ
```

and the registrable total is bounded by a per-segment reach table computed on the 5-cycle from
port-level liveness alone, with `f = O_cap` fresh segments. The evaluation gives **every** segment
the full remaining skip budget, which over-counts the budget and so keeps the bound sound.

## 5. Results

### Closure over the whole stored frontier

| stage | states |
|---|---|
| Q2-admissible frontier | **3,248,890** |
| closed by `capacity_slack` (committed) | 2,956,692 |
| survives `capacity_slack` | **292,198** |
| closed by **LIVE-PORT SUPPLY** | **19,073** |
| closed by **SKIP-COST** | **95,225** |
| **residual** | **177,900** in **945** classes |

The two inequalities close **114,298 of the 292,198** states that
`capacity_slack` leaves open — **39.1%** of them.

### Against Round 71

| | Round 71 (dead-port + orbit-reentry) | Round 72 (live-port supply + skip-cost) |
|---|---|---|
| closed of the 292,198 survivors | 91,790 | **114,298** |
| residual | 200,408 | **177,900** |
| distinct classes | 1,570 | **945** |

**Newly closed: 22,508 states (11.2% of the Round-71 residual).** `SKIP-COST` strictly
supersedes the orbit-re-entry inequality on this corpus (95,225 against 72,717) and roughly halves
the number of distinct residual classes.

**Attribution caveat.** The Round-71 "re-entry margin 0" population (86,654) and the Round-72
"skip-cost slack 0" population (45,574) are measured by two different inequalities. The
22,508 newly closed states are reported in aggregate; I did not carry per-state identity across
the two sweeps, so I do **not** claim that the 86,654 are the ones that fell.

### Residual structure

**177,858 of 177,900 (99.98%)** sit in the five short roots; the long roots contribute
**42** states in total. **22 of 33 roots are fully closed at Q2.**

| root | survives slack | live-port supply | skip-cost | residual |
|---|---|---|---|---|
| `long_found_4` | 1,915 | 780 | 1,124 | **11** |
| `long_found_9` | 1,969 | 894 | 1,067 | **8** |
| `long_q1_2` | 10 | 0 | 9 | **1** |
| `long_q1_3` | 277 | 29 | 237 | **11** |
| `long_q1_7` | 10 | 2 | 7 | **1** |
| `long_q1_8` | 284 | 46 | 228 | **10** |
| `short_ell0` | 11,924 | 470 | 6,212 | **5,242** |
| `short_ell1` | 31,014 | 1,042 | 16,229 | **13,743** |
| `short_ell2` | 60,874 | 2,262 | 27,594 | **31,018** |
| `short_ell3` | 79,897 | 3,286 | 21,340 | **55,271** |
| `short_ell4` | 103,874 | 10,146 | 21,144 | **72,584** |

Largest class: `Ndef=0, Φ=5, O=9, P=13, D=32, used=1`, skip-cost slack
`UB − B = 3` — **3,369** states (1.89%).
The band is still uniform: `Ndef = 0` throughout, `P ∈ {13, 14}`.

Skip-cost slack `UB − B` over the residual: `{'0': 45574, '1': 42561, '2': 41247, '3': 32410, '4': 16108}`.
**45,574 states sit at slack exactly 0**, so a further +1 of charged demand would close them.


## 6. Verdict

**The theorem is proved; the closure hypothesis is not.**

*Proved.* Both engine facts hold exactly (24 generators × 720 words, 0 partial cases; 3,073/3,073
`E²` edges are `R` with `ΔNdef = +1`). The inequality
`(orbit-changing joints into open orbits) + (E² skips) ≤ R_cap + Φ` is sound, it is a charge
`capacity_slack` genuinely does not make, and the adversarial gate confirms the reach function is a
valid upper bound on the exact state that refuted `true_phase_walk_capacity`. Combining it with
`capacity_slack` is safe.

*Not achieved.* It does **not** close the `Ndef = 0`, `P ∈ {13,14}` band. The reason is
structural and worth stating plainly: **`E²` is never *locally* forced.** A segment facing a
visited port can always end instead of skipping, and re-enter the orbit later. Skips and re-entries
are **substitutes**, and SKIP-COST's real content is that they are drawn from *the same* budget —
which tightens the count but does not create a forced `+1`. My Round-71 write-up suggested a
forced-skip argument would close the tight band; that expectation was too strong, and this round
refutes it.

What did close: **95,225** states by SKIP-COST and **19,073** by LIVE-PORT SUPPLY, cutting the
residual from **200,408** to **177,900** and the class count from 1,570 to 945.

**Where the next +1 would have to come from.** With 45,574 residual states at slack exactly 0, any
sound argument that charges one more unit closes them. The two candidates the data points at are
(a) an argument that some fresh-orbit segment cannot in fact register all 5 of its ports — this
needs the rotation-run legality that I deliberately dropped, so it would have to be re-introduced
*soundly*, which is precisely where the old helper died; and (b) a bound on how many distinct
orbits can supply full segments simultaneously, given that their ports must come from disjoint
hexagons.


## 7. Scope and honesty notes

* Everything is **Q2 / Area-A**: the residual states remain perfectly good Q1 objects and none is
  deleted.
* Both inequalities are necessary conditions for an **Area-A NR6 completion** `(P, O, D) = (121, 25, 4)`
  with `Ndef ≤ 3` — that target is the only premise.
* No search was run, no bounded continuation is used as a proof step, and no exhaustion is claimed.
* The retracted `true_phase_walk_capacity`, any phase-derived port-count bound, the old parity
  conjecture, the v1/v2 completeness claims and the invalidated hierarchy source semantics are all
  unused.
* **This project has still not proved `L₆ ≥ 872` unconditionally.**
