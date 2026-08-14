# Cover-compatible orbit ordering gives nothing — and the measurement says why

**Author:** Claude (independent verification track)
**Round:** 81
**Reproducer:** `src/probe_rr_cover_order.py` (`relation`, `census`)
**JSON:** `outputs/rr_cover_order_claude.json`
**Baseline:** 6,657 residual states, 761 classes — **unchanged**.
**Scope:** Q2 / Area-A. The residual is read entirely from the Round-80 archive: no frontier
access, no continuation search, no revisiting of static slack-cover feasibility.

---

## Result, up front

> **Closure: 0 of 6,657.** Every residual state admits a cover-compatible final orbit set that
> is **entirely reachable** under a maximally conservative opening relation — in fact the
> reachable fixpoint contains **every** candidate orbit in **every** state, so the restricted
> cover instance is literally identical to Round 79's and stage D is provably pointless.
>
> This is the negative structural result the brief anticipated: **static incidence plus
> orbit-level ordering is exhausted.**
>
> The measurement identifies the obstacle precisely. The phase-refined relation has out-degree
> **17**, not 55, and a walk pinned to one `(orbit, phase)` could open as few as **0**
> candidates. That factor of ~3.2 is real unused restriction — and it is unusable because
> **`E¹` moves the phase for free**.

---

## 1. The conservative opening relation

For orbits `q ≠ r`:

> `q → r` **iff** there exist a phase `f ∈ {0…4}`, a rotation-run length `ℓ ∈ {0…5}` and a
> non-rotation joint `a ∈ {w2:10, w3:120, w3:201, w3:210}` such that
> `word_after(σ^ℓ(port(q, f)), a)` is a port of `r`.

**It is an over-approximation.** A genuine opening of `r` from `q` is, in the engine, a macro
edge taken from the walk's endpoint `p ∈ q`: `ℓ` rotations then one joint whose target lies in
`r`. The engine imposes strictly *more* conditions than the relation above — every rotation
target must be unvisited, the joint target must be unvisited, the child must survive
`area_a_prune_reason`, and the endpoint occupies **one specific phase**. All of these are
dropped here, and the phase is existentially quantified over all five, which in particular
allows arbitrary legal `E¹` closure beforehand. Dropping conditions can only *add* edges, so no
genuinely possible opening is omitted. ∎

**Excluded edges are excluded by exhaustion, not by absence from a search.** From orbit `q` the
5 phases × 6 rotation lengths × 4 joints give a fixed multiset of exactly **120 target
permutations**, computed in full. An orbit not represented in it cannot be entered from `q` by
any single macro edge whatsoever — a statement about the fixed group action, involving no
visitation, no resources and no history. 12,672 of the 20,592 ordered pairs are excluded on
exactly that ground.

**No weight-2 exclusion is made**, deliberately. It is tempting to argue that with `F = 1`
already spent only weight-3 joints can open an orbit. That argument is **wrong**: `extend()`
computes `abandonment` and `new_orbit` independently and gates neither, so a weight-2 joint into
a fresh orbit is a legal engine transition. `w2:10` therefore stays in the joint set — this is
the Round-75 lesson (omitting a legal free transition manufactures a false bound) applied before
the fact rather than after.

**Cross-check.** The relation reproduces Round 75's transition digraph exactly: **7,920** ordered
pairs, uniform out-degree **55**, uniform in-degree **55**.

## 2. What was tested, and why it is the right restriction

Only orbits in the slack-cover candidate family can ever be opened — opening any other would
exceed the collision budget — and the walk only ever occupies open orbits. So with `R`
initialised to the currently-open set (itself an over-approximation: not every open orbit need
be reachable from the endpoint), `R` grows by candidates having an in-edge from `R`, and a
completion needs a `K`-orbit slack cover entirely inside the fixpoint.

`Ndef = 0` was **verified from the preserved ledger** before use: `{0: 6657}`, all 6,657 states.

## 3. Stages A–C

| stage | input | closed | survivors | UNKNOWN |
|---|---|---|---|---|
| **A** relation | — | — | 144 nodes, out-degree 55 | — |
| **B** first-open feasibility | 6,657 | **0** | 6,657 | 0 |
| **C** iterated reachable cover | 6,657 | **0** | 6,657 | 0 |
| **D** joint cover + reachability | *not attempted* | — | — | — |

**Stage B.** Every residual state has at least **41** cover-compatible candidates openable in a
single step from its currently-open set. The worst state reaches **71 %** of its candidates in
one step; the median reaches 96–98 %; 161 states reach 100 %.

**Stage C.** The reachable fixpoint contains **every** candidate orbit in **all 6,657** states —
the unreachable-candidate histogram is `{0: 6657}`. So the restricted slack-cover instance is
identical to the unrestricted one and never needed re-deciding.

**Stage D was not attempted**, per the brief's payoff gate. With zero unreachable candidates the
joint cover+reachability formulation is not merely unpromising, it is *provably* the same
problem Round 79 already solved.

## 4. Why it is so permissive — two measured reasons

**(1) SLACK-COVER barely restricts individual orbit membership.** The candidate family is nearly
the whole orbit set: the median state has **128 of 144** orbits cover-compatible, and the
distribution peaks at 128–138. This is the crucial distinction the brief's framing did not
anticipate — the cover condition is decisive about *which K-subsets* work, and almost vacuous
about *which single orbits* are usable. As a vertex filter on a reachability graph it does
essentially nothing.

**(2) The orbit-level relation is dense.** Out-degree 55 of 143 is 38.5 %, and the union over
the 7–10 currently-open orbits swamps the candidate set.

## 5. The decisive obstacle: phase, and why it cannot be used

| relation | nodes | out-degree |
|---|---|---|
| orbit-level (what is sound here) | 144 | **55** |
| `(orbit, phase)`-refined | 720 | **17** |

A walk pinned to a single `(orbit, phase)` could open at most **17** candidates, and measured
across the residual the *best* open phase reaches 5–17 candidates while the **worst reaches as
few as 0**. That is a factor of roughly 3.2 of restriction sitting unused.

It is unusable because **`E¹` moves the phase for free** — it advances the phase by `+1` on the
orbit's 5-cycle at zero cost in `Φ`, `Ndef`, `O` and `F` (Rounds 76–77), so a sound relation must
quantify over all five phases. This is the same wall as Rounds 74–76, now located precisely: the
restriction exists, and `E¹` is what makes it inaccessible.

## 6. What finer information is required

Ranked by what the measurement actually supports:

1. **Port-level occupancy / the no-repeat rule.** This is the single lever that would let phase
   be pinned, because it is exactly what gates `E¹`: `E¹` needs the current hexagon to hold only
   the endpoint (so `ℓ = 5` is legal) and its target port to be unvisited. **Charging `E¹` *is*
   charging port occupancy** — there is no other handle on it.
2. **Which specific port of `r`** an opening joint lands on, and whether that port is still
   unvisited. The orbit-level relation discards this entirely.
3. **Fragment repair** — the unique doubly-passed hexagon must be re-entered at one specific
   window.
4. **Resource timing** — deliberately not charged this round, per the brief.

No stronger exclusion was invented to manufacture payoff. Every edge the relation omits is
omitted by exhaustion over the fixed group action.

## 7. Ledger

| | |
|---|---|
| Q2 residual | **6,657** — unchanged |
| canonical classes | **761** — unchanged |
| closed by cover-compatible ordering | **0** |
| UNKNOWN | **0** |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
