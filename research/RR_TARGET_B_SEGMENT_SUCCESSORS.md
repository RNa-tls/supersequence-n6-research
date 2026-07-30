# The segment successor relation, measured over the whole option universe

Round 34, sections 2, 5, 6. Source: `src/build_rr_segment_successors.py`,
output `outputs/rr_segment_successor_index.json`.

## 1. The index (§2)

Each option is a **directed transition**, not a set element:

    K_in(x)  = entry port = PORTS[q][ph]
    K_out(x) = exit  port = PORTS[q][(ph + Σ steps) mod 5]

Every permutation is a port of exactly one E-orbit — 144 × 5 = 720, and the
check `each permutation is a port of exactly 1 orbit` passes — so a boundary
key *is* a permutation. The index therefore has **720 slots**, and

    succ(x) = ⋃_{j ∈ {w3:201, w3:210}}  options entered at  K_out(x)·g_j

is computed by two dictionary lookups per option. No O(n²) pairwise
comparison over the ~9,000 options is performed anywhere.

**Resources are deliberately excluded from the key.** `R_used`, `O_used`,
`F_def` and the covered-hexagon set are path-dependent; folding them in
would give a different and much larger object. The index is purely
geometric, and the resource guards are applied at traversal time by
`search_rr_target_b_flow.py`. This split is recorded in the output under
`resources_excluded_from_key`.

## 2. The measurement that reinterprets Round 33

Round 33's covers had **0 or 1** successor edges among 24–25 segments, and
the longest chain was 1. The question this round had to answer: is that a
property of the transition relation, or of those particular covers?

| survivor | options | entry keys used | successor edges | out-degree min / mean / max | zero-successor options |
|---|---|---|---|---|---|
| `ell0_P2_33d70b42` | 9,340 | 683 | 247,960 | 0 / **26.55** / 30 | 144 |
| `ell4_P2_5d3f8cb9` | 9,529 | 689 | 256,195 | 0 / **26.89** / 30 | 126 |
| `ell4_P2_6f1ed828` | 9,529 | 689 | 256,377 | 0 / **26.91** / 30 | 108 |
| `ell4_P2_fe82b0cd` | 9,529 | 689 | 256,213 | 0 / **26.89** / 30 | 108 |
| `ell4_P6_9bd7590e` | 8,811 | 665 | 223,803 | 0 / **25.40** / 30 | 262 |
| `ell4_P6_cbfdf11e` | 8,811 | 665 | 223,834 | 0 / **25.40** / 30 | 272 |
| `ell4_P6_ec9025e8` | 8,811 | 665 | 224,169 | 0 / **25.44** / 30 | 258 |

Out-degree histogram for `ell0_P2_33d70b42`: 7,207 options have the maximum
30 successors; only 144 have none. At most 15 options share an entry key
(one per legal preserving word), so 30 = 2 joints × 15 words is the
structural ceiling, and most options attain it.

**Conclusion.** The transition relation is dense. Round 33's 0–1 figure was
an artefact of the covers, produced by the partition-seeded construction
that chose one entry phase and one word per orbit without reference to any
exit. Round 33's refusal to call it an R3 obstruction (`NO_ORDER_FOR_THIS
COVER`) is confirmed as correct by measurement, not merely by caution.

Grade: **exact segment graph**.

**And yet the dense relation does not help.** The out-degree of ~26 counts
options reachable *ignoring coverage and resources*. Once the walk is
actually grown (see `RR_TARGET_B_FLOW_RESULTS.md`) almost all of those 26
are dead on arrival, because the entry orbit is forced and its hexagons are
usually gone. Density in the static index and density in the live search
are different quantities; conflating them is how Round 33 went wrong in the
other direction.

## 3. The hexagon-disjointness theorem (§5) — PROVED

> **Theorem.** For segments built from full ℓ=5 rotation runs,
> hexagon-disjointness implies permutation-disjointness.

*Proof.* Two facts, both verified exhaustively over all 720 permutations by
`hexagon_disjointness_theorem()`:

1. The 120 hexagons — the orbits of right multiplication by Σ — **partition**
   the 720 permutations into blocks of exactly 6. (Checked: 120 blocks, all
   of size 6, total 720.)
2. An ℓ=5 rotation run from a port `p` visits `p·Σ⁰ … p·Σ⁵`, which is
   exactly the 6 permutations of `hexagon(p)`. (Checked at all 720 ports:
   every run has 6 distinct permutations and a single hexagon id.)

So a capacity-`k` segment consumes precisely the disjoint union of the `k`
hexagons it covers. Two segments covering disjoint hexagon sets consume
disjoint permutation sets. ∎

Grade: **손증명** (with an exhaustive machine check of both premises).

### Consequences, stated exactly

* **R4 is implied by R1 for all fresh hexagons.** There is no permutation
  conflict beyond the hexagon conflict, so no permutation conflict mask is
  needed and no counterexample exists to exhibit. `permutation_conflict_
  mask_still_needed: false`.
* **R2 is also implied**, by the same structure: the five ports of an
  E-orbit lie in five *distinct* hexagons (checked at all 144 orbits), so a
  hexagon partition cannot reuse a port.
* **One exception, and R4 is not deleted because of it.** The first hexagon
  of the first segment is the hexagon the boundary state stands in. At all
  seven survivors that hexagon has popcount **1** — only `p` itself — so an
  ℓ=5 run does complete it; but that is a measured property of these seven
  states, not a consequence of the hexagon algebra. It stays an engine-
  replay obligation, discharged in `verify_rr_target_b_flow.py`.

Absorbing R4 into R1 removes a layer from the Round 33 hierarchy. It does
**not** make Target B easier: R3, the flow layer, was and remains the
binding constraint.

## 4. Is 24–25 segments forced? (§6) — no, but the range is narrow

Round 33 reported covers of 24 and 25 segments. That was one solution's
value. Enumerating every arithmetically consistent profile — subject to
total capacity = `B+1`, `c_initial ≤` the phase-walk initial capacity (= 2,
Round 33), `segments ≤ O_cap + R_cap + 1`, fresh `≤ O_cap`, re-entries
`≤ R_cap`, capacity-5 ⟹ `EEEE` ⟹ fresh, re-entry capacity `≤ 4`:

| survivor | `B+1` | `O_cap` | possible segment counts | profiles | min capacity-5 segments |
|---|---|---|---|---|---|
| `ell0_P2` | 115 | 23 | **{24, 25}** | 6 | 17 |
| `ell4_P2` (×3) | 116 | 23 | **{24, 25}** | 4 | 18 |
| `ell4_P6` (×3) | 112 | 22 | **{23, 24}** | 3 | 18 |

So the count is not a single forced value, but it is pinned to two
consecutive values, and in every profile **at least 17–18 of the segments
must be capacity-5 `EEEE` segments on pairwise hexagon-disjoint orbits**.
That is the real content of the profile analysis, and it is what makes the
flow search terminate: each such segment demands a forced-successor orbit
all five of whose hexagons are still free.

Grade: **safe relaxation** — the enumeration enforces the counting
constraints but not the geometry, so every genuinely feasible profile
appears in the list while the converse is not claimed. It is emphatically
*not* an exhaustive statement about which profiles are realisable.

## Round 39 correction

The quoted initial capacity `=2` came from the now-retracted generic
phase-walk helper. The successor graph itself is geometric, but every
profile bound using `initial_capacity_max=2` is historical metadata, not a
current certificate. The all-18 helper-free engine re-audit does not rely
on this profile layer.
