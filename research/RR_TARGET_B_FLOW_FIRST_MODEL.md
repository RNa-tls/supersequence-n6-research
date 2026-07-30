# Target B, flow-first: the walk is primary, the cover is a side condition

Round 34. Supersedes the cover-first model of Round 33 as the *working*
model; Round 33's results are not withdrawn, they are re-read.

## 0. Why the model changed

Round 33 built an exact-cover model: choose a set of orbit segments whose
hexagons partition the residual hexagons, then ask whether that set can be
linearly ordered into one walk. Four of the seven survivors admitted a
cover. None of those covers could be ordered, and the diagnostic was a
single number — among the 24–25 segments of a cover there were **0 or 1**
successor edges, and the longest chain was **1**.

Round 33 was right not to call that an R3 obstruction (`NO_ORDER_FOR_THIS
COVER`, not `R3 infeasible`), because one unorderable cover says nothing
about the others. Round 34 makes the reason precise, and it is worse than
"the cover was unlucky":

> **The cover-first model had no way to see connectability at all.**
> Choosing a cover fixes, for each chosen orbit, one entry phase and one
> word. Whether the previous segment's exit lands on that exact entry
> phase is then a coincidence. The cover-first model optimises the
> abundant resource (hexagons: every residual hexagon had options,
> `hexagons_with_no_option = 0` at all seven survivors) and ignores the
> scarce one.

Section 1 of `RR_TARGET_B_SEGMENT_SUCCESSORS.md` measures this: over the
**whole** option universe the mean out-degree is ~26 and the maximum is 30.
The 0–1 figure was an artefact of the chosen covers, not a property of the
transition relation. So the fix is not a better cover heuristic. The fix is
to stop choosing covers.

## 1. The exact primitive: a macro edge is forced to ℓ=5

Everything below rests on one previously established identity, re-verified
here against the engine:

    Φ(state) = 5 + 6·(TARGET_P − P) − (720 − visited_count)
    ΔΦ = ℓ − 5   for a macro edge rot^ℓ ; joint

and `macro.remaining_window_capacity_prune` is true **exactly** when Φ < 0.
All seven boundary states have **Φ = 0** (measured, not assumed). Hence:

* ℓ < 5 drives Φ negative and is pruned by the engine itself;
* ℓ = 6 revisits the run's own first permutation, so it is illegal;
* therefore **every** macro edge in a Target B continuation has ℓ = 5.

An ℓ=5 rotation run from a port `p` visits `p·Σ⁰ … p·Σ⁵`, which is exactly
the six permutations of `hexagon(p)`. So:

> **one macro edge = one completed hexagon.**

This is what makes the segment layer *exact* rather than a relaxation, and
it is why the whole round can avoid permutation-level search.

Confirmed numerically at the boundary states: the partially visited hexagon
has popcount **1** (only `p` itself), so even the first macro edge has a
full ℓ=5 run available, and the residual hexagon count equals `B+1`
(115 / 116 / 112) at all seven.

## 2. Segments and the forced-successor structure

Of the four joints, two are orbit-**preserving** and two are orbit-
**changing**:

| joint | weight | as a composite `Σ⁵∘a` | effect |
|---|---|---|---|
| `w2:10`  | 2 | `E`   | stays in the E-orbit, phase +1 |
| `w3:120` | 3 | `E²`  | stays in the E-orbit, phase +2 |
| `w3:201` | 3 | ∉ ⟨E⟩ | leaves the orbit |
| `w3:210` | 3 | ∉ ⟨E⟩ | leaves the orbit |

A **segment** is a maximal run of preserving joints: an entry port, a
preserving word over {E, E²} whose partial sums are distinct mod 5, and an
exit port. A segment of capacity `k` is `k` macro edges and completes `k`
hexagons — one per port it stands on.

The flow-first content is the next line. When a segment ends at exit port
`p_exit`, the next segment's entry port is

    p_exit · g_j       for j ∈ {w3:201, w3:210}

so **the next orbit is forced up to a binary choice**. There is no step at
which the walk selects which orbit to visit next. That is the constraint
the cover-first model discarded.

## 3. Resource accounting, re-derived from the engine

`Ndef = S + F − O`, and the engine's `extend` gives `dS = [weight ≥ 3]`,
`dH = max(weight−3, 0)`, `dF = [p·Σ unvisited]`, `dO = [target orbit was
unopened]`. At the end of a full ℓ=5 run the hexagon is complete, so `p·Σ`
is visited and `dF = 0` — no abandonment, which is what keeps `F_def = 1`.
Therefore:

| step | dS | dO | **dNdef** |
|---|---|---|---|
| `w2:10` (E, preserving) | 0 | 0 | **0** |
| `w3:120` (E², preserving) | 1 | 0 | **+1** |
| exit joint into a **fresh** orbit | 1 | 1 | **0** |
| exit joint into an **opened** orbit | 1 | 0 | **+1** |

`area_a` caps `Ndef ≤ n_limit = 3` and every boundary state has
`Ndef = 2`, so the whole continuation has an **R budget of exactly 1**,
spent on either one E² step or one orbit re-entry — not both. Together
with the saturating-block theorem (the three capacity-5 words are `EEEE`,
`E2EEE2`, `E2E2E2E2` with 0/2/4 E² steps) this forces:

> every capacity-5 segment is `EEEE`, costs no R, and is a fresh opening
> (an already opened orbit has a visited port, so a re-entry segment has
> capacity ≤ 4).

Budgets at the boundary: `O_cap = 25 − O` = 23 or 22, `R_cap = 1`, and
`max_segments = O_cap + R_cap + 1` = 25 or 24, because every segment after
the initial one is entered by an exit joint that costs one O or one R.

## 4. The DP state and the prunes

    Q = ( entry port,
          free-hexagon mask            (120 bits),
          per-orbit visited-port masks (144 × 5 bits),
          O_used, R_used, segments_used, covered_count )

`covered_count` is derivable from the free mask; it is carried because
every prune is written in terms of it. Prunes, all safe:

1. **Dynamic capacity** — the incremental form of the Round 32 bound (B+R):

       H − covered  ≤  5·(O_cap − O_used) + 4·(R_cap − R_used)
       H − covered  ≤  5·(max_segments − segments_used)

2. **Static forward reachability (§7)** — every segment stands on its own
   entry port, so an entry port whose hexagon is already visited *at the
   root* can never begin a segment. The free set only shrinks, so the
   prune is monotone and therefore safe. 25–49 of the 720 boundary keys
   are dead this way.

3. **Resource guards** — the table in §3, applied per candidate word.

4. **Coverage** — a candidate word is rejected unless every port it stands
   on is unvisited and every hexagon it completes is still free. This is
   not a heuristic: landing on a visited permutation is illegal in the
   engine, so a walk that reaches a completed hexagon is genuinely stuck.

## 5. Backward terminal reachability: a scope correction (§8)

The brief asked for backward reachability from the terminal set. That set
cannot be characterised at the boundary layer, and saying so is the honest
answer:

> Target B's terminal condition is **`covered_count = H`** — a predicate on
> the *coverage*, not on the boundary. Every port is the exit of some
> completing walk in the unconstrained relation, so backward reachability
> computed on boundary keys alone is **vacuous**: it excludes nothing.

Grade: **scope correction**. The useful backward information is the
residual-capacity bound, which is prune 1 above, applied in the forward
direction where it is exact. No backward boundary set was computed, and
none is claimed.

## 6. Meet-in-the-middle: measured, not assumed (§9)

The brief asked for a memory estimate before implementing MITM. The
estimate was produced by measuring the real forward frontier, deduplicated
on the full DP key (see `frontier` in `outputs/rr_flow_search_results.json`).

The frontier does not survive to depth 12. It peaks between depth 4 and 8
at a few hundred states and then collapses to zero — the forward search
*terminates* well before the meeting depth. Meet-in-the-middle is
therefore not merely unnecessary here, it is undefined: there is no forward
layer 12 to meet.

Two frontiers could not have been joined on the boundary key anyway. The
DP key contains the 120-bit free-hexagon mask and the 144 per-orbit port
masks; two half-walks agree only if their coverage is complementary, so a
join needs the full key, not the boundary. That is recorded here so the
absence of an MITM implementation is a measurement, not an omission.

## 7. Position-free encoding (§11)

No positional/order variables were introduced, and no SAT or ILP encoding
was written. The reason is the point of the round: in a flow-first model
subtours are **structurally impossible**, because the walk is constructed
in order and its successor is forced. Subtour elimination is a repair for
the cover-first formulation — it exists to undo the damage of choosing a
set first. Adding it here would be reintroducing the failure Round 33
diagnosed. Grade: **exact allocation model** is *not* claimed for any ILP,
because none was built.

## 8. Result

See `RR_TARGET_B_FLOW_RESULTS.md` for the measured outcome and
`RR_TARGET_B_R3_CERTIFICATES.md` for the certificates and their exact
scope.
