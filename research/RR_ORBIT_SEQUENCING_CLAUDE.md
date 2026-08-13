# Inter-orbit sequencing: the transition digraph gives no obstruction

**Author:** Claude (independent verification track)
**Round:** 75
**JSON:** `outputs/rr_orbit_sequencing_claude.json`
**Baseline:** 200,408 residual states, 1,570 canonical classes (unchanged).
**Scope:** Q2 / Area-A. No search, no frontier re-run, no bounded continuation. The per-orbit
segment-capacity family is retired and not revisited.

---

## Result, up front

> **Predicted closure: 0 states.** The orbit-only graph is **not** sufficient — *every* transition
> is phase-dependent — but the required `(orbit, phase)` refinement is **strongly connected**, and
> so is the free-movement subgraph. Condensation crossings are **0 for every state**, so every
> sequencing lower bound in the brief's list evaluates to zero before the residual is even
> consulted.

---

## 1. The exact transition digraph

From each of the 5 ports of each of the 144 E-orbits, applying all 24 macro generators
`σ^ℓ · a` and discarding the orbit-preserving ones:

| | |
|---|---|
| ordered orbit pairs carrying a transition | **7,920** of 20,592 (38.5 %) |
| out-degree, all transitions | **55**, uniform over all 144 orbits |

**Costs**, in the shared `R_cap + Φ` currency. Into an **already-open** orbit a transition costs
`(5 − ℓ)` units of `Φ` plus 1 unit of `Ndef` if it is a weight-3 joint (an `R`):

| min cost into an open orbit | 1 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| ordered pairs | **2,160** | 1,440 | 1,440 | 1,440 | 1,440 |

Into a **fresh** orbit the `O` is charged separately and only `Φ` remains, so 1,440 pairs are
**free** (`ℓ=5`, `w3:201/210`); weight-2 into a fresh orbit is impossible (it needs an abandonment,
so `F = 2`).

### Phase dependence — the orbit-only graph is NOT sufficient

| source phases realising a given transition | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| ordered pairs | 5,040 | 1,440 | 1,440 | 0 | **0** |

**Not one of the 7,920 transitions is available from all five source phases.** A 144-node
orbit-only graph would assert movements the engine cannot make from the port the walk actually
occupies. The weakest sound refinement is the full `(orbit, phase)` node set — 720 nodes, i.e. the
permutations themselves. No coarser quotient survives.

## 2. SCC structure — nothing to condense

| graph | nodes | out-degree | SCCs | largest |
|---|---|---|---|---|
| all transitions | 144 | 55 | **1** | 144 |
| cost ≤ 1 into an open orbit | 144 | 15 | **1** | 144 |
| cost ≤ 2 | 144 | 15 | **1** | 144 |
| free (`ℓ=5`, `w3:201/210`) | 144 | 10 | **1** | 144 |
| all transitions, refined | **720** | 22 | **1** | 720 |
| **free movement, refined (`E¹` + `w3:201/210`)** | **720** | 12 | **1** | **720** |

Every graph at every cost level and both granularities is strongly connected, with uniform
out-degree — the generators act too transitively for a condensation to exist. Therefore:

* mandatory SCC crossings: **0**;
* mandatory cut crossings: **0** (there is no condensation to cut);
* articulation / separator structure: **none** — the graph is vertex-transitive;
* minimum directed path-cover cost: **0** extra over the moves already counted.

**Every candidate form listed in the brief evaluates to zero.** No residual sweep is needed: the
condensation is a property of the generators, not of the corpus.

### A near-miss I caught, and it is the important part of this round

My first free-movement graph used only the `ℓ=5, w3:201/210` edges and reported **15 SCCs, largest
48** — which looks exactly like the obstruction being sought. It was wrong: I had **omitted `E¹`**
(`ℓ=5, w2:10`), which is also free. `E¹` makes each orbit's five phases a directed 5-cycle, and
adding it back collapses the graph to a single SCC on all 720 nodes.

Omitting a free move *deletes* legal transitions, which inflates the crossing count and yields an
**unsound** lower bound — precisely the discipline the brief sets out ("when uncertain, ADD edges
rather than remove them"). Had this graph been used, it would have produced a second retraction.
The soundness rule is recorded rather than the number.

## 3. Successor scarcity in the residual band

Every orbit has **exactly 10** free successors. The residual band has `O ∈ 3…10`, so at least
**134 of 144 orbits are still fresh** at every residual state. For a free move to be unavailable
the open set would have to contain one specific 10-element successor set — impossible at `O < 10`
and vanishingly constrained at `O = 10`, and even then it forces only a single paid move, which
`ORBIT-REENTRY` may already be charging.

**Successor and predecessor scarcity cannot bind in this band.**

## 4. Why the whole family fails, and where the leverage actually is

This is the same shape of failure as Round 74. There, no *within-orbit* argument could force a
second segment because a `+1/+2` walk sweeps a 5-cycle. Here, no *between-orbit* argument can force
an extra transition because the generators make the space strongly connected with uniform degree
10–55. **Both movement-based families are exhausted: the engine's group action is too transitive
for reachability arguments to obstruct anything.**

Every bound that has ever bitten in this project is a **resource-counting** bound (`Φ`, `Ndef`,
`O`, dead ports, incidence excess `r`), never a reachability bound. That is the lesson to carry
forward.

### Weakest theorem worth proving next

Not sequencing. The one unexploited **counting** constraint sits on the hexagon–orbit incidence
side, and it is exact:

> At an Area-A NR6 completion, `P = 121` and all 720 windows are visited, so all 120 hexagons are
> touched: `|T| = 120`. Hence the incidence excess satisfies
> **`r_final = P − |T| = 121 − 120 = 1`, exactly.**

Combined with Round 69's proved facts — `r` is non-decreasing, and `6r ≤ 11 − Φ` forces `r ≤ 1`
throughout the Q2 region — this says a completion needs `r` to be **exactly** 1 at the end.
Therefore:

* a state with `r = 1` must never create a second doubly-registered hexagon (already proved);
* **a state with `r = 0` must still create exactly one** — and by Round 69's re-entry accounting,
  giving a hexagon its second registered window requires re-entering a hexagon that already holds
  visited windows, which costs `Φ`.

That is a **demand-side** charge on `Φ` which no current bound levies, it survives `q0` return and
repeated re-entry (creating a bridge is a specific event, not a movement assumption), and it is
cheap to test: `r = P − |T|` is computable from the stored masks alone. Whether the residual band
sits at `r = 0` or `r = 1` decides the payoff, and that measurement is the natural next step.

> **Round-76 correction.** The measurement was made and the `Φ`-charge half of this suggestion is
> **refuted**. `r = 0` does dominate the residual (196,056 of 200,408, 97.83 %), but giving a
> hexagon its second registered window does **not** require `Φ`: `E¹` (`ℓ = 5, w2:10`, kind `Z2`)
> creates a bridge with `ΔΦ = ΔNdef = ΔO = ΔF = 0`, witnessed both on corpus and by an independent
> three-edge walk from `initial_state`. The `r_final = 1` premise stands; the charge does not.
> See `research/RR_BRIDGE_CHARGE_CLAUDE.md`.

## 5. Ledger

| | |
|---|---|
| Q2 residual (unchanged) | **200,408** |
| canonical classes (unchanged) | **1,570** |
| closed by any sequencing bound | **0** |
| orbit-only graph sufficient? | **no** — 0 of 7,920 transitions are phase-universal |
| refinement required | `(orbit, phase)`, 720 nodes — and still strongly connected |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
