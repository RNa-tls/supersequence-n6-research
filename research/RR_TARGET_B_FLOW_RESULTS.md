# Flow-first results: all seven remaining Target A boundaries lose Target B

Round 34, sections 10, 13, 15, 16. Sources:
`src/search_rr_target_b_flow.py` → `outputs/rr_flow_first_models.json`,
`outputs/rr_flow_search_results.json`;
`src/verify_rr_target_b_flow.py` → `outputs/rr_flow_certificates.json`.

## 1. Result

| survivor | `B+1` | `O_cap` | max segs | status | nodes | max segments reached | max hexagons covered |
|---|---|---|---|---|---|---|---|
| `ell4_P6_9bd7590e` | 112 | 22 | 24 | **EXHAUSTED_NO_PATH** | 149 | 7 | 29 / 112 |
| `ell4_P6_cbfdf11e` | 112 | 22 | 24 | **EXHAUSTED_NO_PATH** | 263 | 8 | 33 / 112 |
| `ell4_P6_ec9025e8` | 112 | 22 | 24 | **EXHAUSTED_NO_PATH** | 114 | 7 | 28 / 112 |
| `ell4_P2_5d3f8cb9` | 116 | 23 | 25 | **EXHAUSTED_NO_PATH** | 504 | 8 | 32 / 116 |
| `ell4_P2_fe82b0cd` | 116 | 23 | 25 | **EXHAUSTED_NO_PATH** | 1,499 | 10 | 42 / 116 |
| `ell4_P2_6f1ed828` | 116 | 23 | 25 | **EXHAUSTED_NO_PATH** | 603 | 9 | 37 / 116 |
| `ell0_P2_33d70b42` | 115 | 23 | 25 | **EXHAUSTED_NO_PATH** | 1,357 | 10 | 41 / 115 |

Survivors processed most-constrained-first (§15): refined margin, then
option count, then mean successor branching. Every run finished with
`truncated: false` — the node cap was 20,000,000 and the largest tree had
**1,499** nodes, so `EXHAUSTED_NO_PATH` is a statement about a completed
search, not a budget.

**Not one walk got past 10 segments or past 42 of the 112–116 hexagons.**
The deepest walk covers 36% of what it needs.

## 2. Why it dies, quantitatively

The dominant prune is the dynamic capacity bound, by a wide margin — e.g.
5,538 capacity cut-offs against 1,357 nodes at `ell0_P2_33d70b42`. The
mechanism:

* Every boundary state has `Ndef = 2` against `n_limit = 3`, so the whole
  continuation has an **R budget of exactly 1**.
* With `R_cap = 1` the only usable capacity-5 word is `EEEE` (the other two
  saturating blocks need 2 and 4 E² steps), and `EEEE` requires the forced
  next orbit to be **unopened with all five of its hexagons still free**.
* The profile enumeration (`RR_TARGET_B_SEGMENT_SUCCESSORS.md` §4) shows
  every arithmetically possible profile needs **at least 17–18** such
  capacity-5 segments out of 23–25.
* But the next orbit is **not chosen** — it is `p_exit·g_j` for one of two
  joints. After a handful of segments, neither forced orbit is a clean
  five-free-hexagon orbit any more, the walk must take a short segment, the
  defect budget (5–10 units total, 3 of which the initial segment consumes
  because its phase-walk capacity is only 2) runs out, and the capacity
  bound closes.

So the obstruction is the interaction of two facts that were each already
known and were never before combined: **the segment count is capacity-bound
from above, and the segment identity is flow-forced from the side.** Round
33's cover-first model could see the first and was structurally blind to the
second.

## 3. Independent verification (§17)

The claim "the tree is finite and has 149 nodes" is exactly the kind that
is normally a modelling bug, so it was not accepted on the model's word.
`src/verify_rr_target_b_flow.py` re-runs the search on the **real engine**
— `macro.macro_edges` and `macro.area_a_prune_reason(·, AREA_A)` — with no
knowledge of segments, options, hexagon covers, or the option corpus.

**Variant B (certificate grade)** adds the Round 32 (B+R) capacity bound
recomputed from `ExactState` fields alone:

    need  = TARGET_P − P + 1
    bound = 1 + (5 − used ports of the current orbit)
            + 5·(TARGET_O − O) + 4·(n_limit − Ndef)

| survivor | engine verdict | engine nodes | max macro depth | windows short of 720 | surviving ℓ | model verdict | contradiction |
|---|---|---|---|---|---|---|---|
| `ell0_P2_33d70b42` | EXHAUSTED_NO_PATH | 3,214 | 40 | 449 | **{5}** | EXHAUSTED_NO_PATH | none |
| `ell4_P2_5d3f8cb9` | EXHAUSTED_NO_PATH | 1,206 | 33 | 497 | **{5}** | EXHAUSTED_NO_PATH | none |
| `ell4_P2_6f1ed828` | EXHAUSTED_NO_PATH | 1,450 | 36 | 479 | **{5}** | EXHAUSTED_NO_PATH | none |
| `ell4_P2_fe82b0cd` | EXHAUSTED_NO_PATH | 3,558 | 41 | 449 | **{5}** | EXHAUSTED_NO_PATH | none |
| `ell4_P6_9bd7590e` | EXHAUSTED_NO_PATH | 359 | 28 | 503 | **{5}** | EXHAUSTED_NO_PATH | none |
| `ell4_P6_cbfdf11e` | EXHAUSTED_NO_PATH | 630 | 35 | 461 | **{5}** | EXHAUSTED_NO_PATH | none |
| `ell4_P6_ec9025e8` | EXHAUSTED_NO_PATH | 281 | 27 | 509 | **{5}** | EXHAUSTED_NO_PATH | none |

**7 / 7 independently verified UNSAT, 0 contradictions.** Cross-check on a
quantity neither search shares: the engine's maximum macro depth (macro
edges = completed hexagons) against the model's maximum covered hexagon
count — 40 vs 41, 33 vs 32, 36 vs 37, 41 vs 42, 28 vs 29, **35 vs 33**,
27 vs 28. Agreement to within **2** (six of seven within 1). The two
prunes are close but not identical — the model checks its bound at segment
boundaries while the engine checks after every macro edge, and on a
re-entry they differ by `used_ports − 2` — which is why the agreement is
close rather than exact. Both are separately proved safe, and an exact
match would have been the weaker outcome, since it would suggest the same
computation run twice.

`ell = 5` was **{5} at every surviving macro edge in all seven trees**,
confirming from the engine side that Φ = 0 forces full rotation runs — the
premise the whole segment layer rests on.

**Variant A (area_a only)** — the engine's own prune set and *nothing*
else, not even the capacity bound — is fully independent but prunes
strictly less. It is **INCOMPLETE at all seven** (36,374–62,657 nodes,
macro depth 70–79, 60 s budget each). Reported as `INCOMPLETE`, not as
agreement and not as disagreement: a truncated run is weaker evidence, not
contrary evidence. It is recorded because it shows exactly which prune
does the work — without the (B+R) capacity bound the tree does not
terminate in a minute, with it the tree has a few thousand nodes.

Also re-derived from the engine (§12): the R charges. `Ndef = S + F − O`
with `dS = [weight ≥ 3]`, `dO = [target orbit unopened]`, and `dF = 0` at
the end of a full ℓ=5 run because the hexagon is complete so `p·Σ` is
visited. Hence E costs 0, E² costs 1, a fresh opening costs 0, a re-entry
costs 1 — exactly the model's budget, from the engine's own arithmetic
rather than from our bookkeeping.

## 4. What this does and does not establish

**Does:** all **18 of 18** known Target A boundary states now provably have
no Target B continuation inside Area A (F=1, H=0, N ≤ 3). Cumulatively:
18 → 9 (R30 coarse capacity) → 8 (R31 initial-phase refinement) → 7 (R32
orbit-reuse penalty) → **0 (R34, flow-first exhaustive search)**.

**Does not:**

* **This is not "Target B is impossible."** The 18 are the *known* Target A
  boundary states, from a Round 27 enumeration that returned **6 FOUND, 22
  INCOMPLETE** at a node cap of 8,000. Whether other Target A boundary
  states exist is open, and 22 truncated roots is a live reason to think
  the set may not be complete. What is now closed is Target B *from these
  18*.
* **It says nothing about `L_6 ≥ 872`.** Verified upper bound 872, proved
  lower bound 867, open target lower bound 872 — unchanged.
* It says nothing about Target C, the U/J branches, the N=0 checkpoint
  (untouched, as instructed), CH2 (frozen), or T3 (still exact observation
  15/15). In particular T3 is **not** proved from these results.
* No `FLOW_RELAXATION_FEASIBLE` result was produced, because no relaxed
  model was solved; and no `SAT_MODEL_UNSAT_WITH_CERTIFICATE` label appears
  anywhere, because no SAT model was built (§11).

## 5. Failure-driven cuts (§13) — not needed, and why that is reported

The brief asked for cuts learned from failed attempts, fed back to prune
later ones. None were implemented: the largest search tree in the round has
1,499 nodes and completes in 0.1 s. A learned-cut mechanism would be
untestable at that scale — there is no measurable cost to reduce, and an
unexercised cut generator is a liability, not an asset. Grade for §13:
**미완료**, deliberately.

## 6. Component compatibility (R5) — correctly never reached (§14)

The brief said not to build the full R5 component encoding until an R3/R4
feasible candidate exists. None exists: every survivor fails at R3, the
flow layer. Rounds 29–32 repeatedly named the component condition as the
next bottleneck; that was wrong three rounds running, and Round 34 confirms
Round 33's correction. Target B's final component requirement remains
uncharacterised, and nothing in this round assumes anything about it.
