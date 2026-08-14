# Z3-only generation: the restriction turns out to be no restriction at all

**Author:** Claude (independent verification track)
**Round:** 84
**Reproducer:** `src/probe_rr_cover_order.py` (archive loading + slack-cover decider)
**JSON:** `outputs/rr_z3_generation_claude.json`
**Baseline:** 6,657 residual states — **unchanged**.
**Scope:** Q2 / Area-A. Residual read from the Round-80 archive; no frontier replay, no
continuation search, no first-open tests.

**Scoping note.** The blocked-w2 lemma is used here only as a *reachable-legal-history*
invariant, which is exactly what its Round-83 proof establishes — the proof argues from the
walk's no-repeat history (`p'` visited exactly once, now). It is never applied to arbitrary
hand-built `ExactState` masks.

---

## Result, up front

> **Closure: 0 of 6,657, with 0 UNKNOWN.** Two findings, and the first is the surprise:
>
> **The Z3-only relation is *identical* to Round 81's generic relation** — same 7,920 edges,
> out-degree 55, verified as **set equality per orbit**, not merely equal counts. Every orbit
> change the weight-2 joint can make is also makeable by some weight-3 joint from the same
> source orbit, so the w2 edges are a strict subset. Restricting to Z3 removes **nothing**.
>
> **The induced-set condition — the genuinely new constraint — rejected zero cover solutions.**
> In all 476 states where it could bite, the *first* cover found was already induced-reachable.
>
> **Static cover + orbit-level Z3 generation is exhausted.**

---

## 1. The exact Z3 relation

> `q → r` **iff** there exist a phase `f`, a rotation-run length `ℓ ∈ 0…5` and a weight-3 joint
> `a` such that `word_after(σ^ℓ(port(q,f)), a)` is a port of `r`.

**Over-approximation.** A genuine Z3 opening of `r` from `q` is a macro edge departing the
walk's endpoint in `q`: `ℓ` rotations then a weight-3 joint landing in `r`, with
`abandonment = False` and `new_orbit = True`. The engine imposes strictly more — every rotation
target unvisited, the joint target unvisited, `σ(p')` visited, `r` closed, and one specific
endpoint phase. All are dropped and the phase is quantified over all five, so no genuinely
possible Z3 edge is omitted. ∎

| relation | edges | out-degree | in-degree | SCCs |
|---|---|---|---|---|
| **Z3-only** (w3, all ℓ) | **7,920** | 55 | 55 | **1** |
| Round-81 generic (all 4 joints) | 7,920 | 55 | 55 | 1 |
| w2-only | 2,880 | 20 | — | — |
| Z3 at `ℓ = 5` only | 1,440 | 10 | 10 | — |

**`Z3 == generic` as edge sets** (checked per orbit), and **`w2-edges ⊆ Z3-edges`**. This is
why the round could not have paid off through the relation: the constraint "only Z3 openings are
legal", though true and newly proved in Round 83, is *invisible* at orbit level.

## 2. The generation necessity, proved

Every orbit of `S` must be opened fresh, and with `F = 1` every fresh opening is a Z3
(Round 83). A Z3 opening of `r` is a macro edge departing the walk's current orbit, which at
that moment lies in `A ∪ (already-opened members of S)`. So the openings admit an order
`s_1 … s_K` in which each `s_i` has a Z3 predecessor in `A ∪ {s_1 … s_{i-1}}`.

Conversely, such an order is exactly a witness that every element of `S` is reachable from `A`
**inside the induced graph `G[A ∪ S]`**: the greedy closure of `A` within `A ∪ S` reaches all of
`S` iff such an order exists. ∎

Reachability in the **full** graph is strictly weaker — a path there may pass through an orbit
not selected into `S`. That gap is the new content of this round, and Round 81 never tested it.

## 3–4. Payoff

| stage | input | closed | note |
|---|---|---|---|
| **B** full-graph Z3 reachable-cover filter | 6,657 | **0** | the Z3 closure from `A` reaches **every** candidate in **every** state (`{0: 6657}` unreachable) |
| **C** one-step cut | 6,657 | — | **6,181** admit a cover lying entirely in the one-step Z3 image of `A`, so the induced condition holds trivially |
| **D** exact joint cover + generation | **476** | **0** | **476 SAT, 0 UNSAT, 0 UNKNOWN**, 170,250 search nodes |

**The decisive number in stage D: 476 cover solutions examined for 476 instances.** The first
cover found was induced-reachable every single time — the induced condition never rejected one.

By band, the states needing the multi-step test: `c=1` 30, `c=2` 219, `c=3` 163, `c=4` 49,
`c=5` 15. Tight-cover bands are *not* more constrained by Z3 generation; the split tracks band
size, not slack.

Each SAT carries an explicit witness: the selected `S`, its cover of `U`, and the generation
order from `A`.

## 5. A sound derived lemma that still did not pay

Worth recording, because it follows from already-proved results and looked like the natural
sharpening:

> **At most two future macro edges can have `ℓ < 5`.** `F = 1` on every residual state, so no
> future abandonment is legal (Round 83). A pass entering a **fresh** hexagon must therefore
> leave by natural rotation collision — it fills the hexagon, and its departing edge has
> `ℓ = 5`. By the Round-76/78 pass count exactly one hexagon receives two passes, and with
> `F = 1` that must be the already-existing fragment. So only the current pass (if its hexagon
> is partial) and the fragment-repair pass can depart with `ℓ < 5`.

The `ℓ = 5` Z3 relation has out-degree **10** rather than 55 — a factor of 5.5 sparser, which
looked decisive. It is not. Under the deliberately unsound projection that *all* Z3 edges must
have `ℓ = 5`, only 10–50 % of candidates sit one edge from `A` — but **the full `ℓ=5` closure
still reaches every candidate in all 6,657 states**. Even that sharpening closes 0 by
reachability.

Recorded as a sound fact; used to close nothing.

## 6. Negative structural result

> **Static cover + orbit-level Z3 generation is exhausted.** All 6,657 states admit a
> Z3-generated slack-cover final orbit set, the induced-set condition rejects nothing, and the
> sharpest available `ℓ`-restriction leaves the closure complete.

What could still constrain a genuinely multi-step sequence — none of it established here:

1. **Landing phase of each Z3 opening.** The entering joint determines the arrival phase
   exactly; the orbit-level relation discards it. This is the coordinate every orbit-level
   result has thrown away.
2. **Port occupancy across several selected orbits simultaneously**, rather than one at a time —
   Round 82 measured occupancy per-orbit and found the ceiling was in the predicate, not the
   resolution.
3. **Source-orbit reuse**: how many openings one pass through a single orbit can supply.
4. **Resource timing**: when `R_cap + Φ` is spent relative to the openings.

## 7. Ledger

| | |
|---|---|
| Q2 residual | **6,657** — unchanged |
| closed this round | **0** |
| UNSAT / UNKNOWN in the joint solve | 0 / 0 |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
