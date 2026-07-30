# Meet-in-the-middle for the Target B flow: measured, then not needed

Round 34, sections 7–9, 11. Source: `frontier_profile()` in
`src/search_rr_target_b_flow.py`; data under `frontier` in
`outputs/rr_flow_search_results.json`.

## 1. What was asked and what was found

The brief asked for a forward-12 / backward-12–13 meet-in-the-middle, with
a **memory estimate produced first**. The estimate was produced by
measuring the real forward frontier rather than guessing at it. The
measurement says the meeting depth does not exist:

| survivor | frontier sizes by depth (1 → …) |
|---|---|
| `ell4_P6_9bd7590e` | 3, 15, 38, 42, 31, 12, 8, **0** |
| `ell4_P6_cbfdf11e` | 3, 16, 41, 74, 70, 36, 22, 1, **0** |
| `ell4_P6_ec9025e8` | 3, 14, 31, 34, 22, 8, 2, **0** |
| `ell4_P2_5d3f8cb9` | 3, 20, 74, 112, 130, 93, 50, 22, **0** |
| `ell4_P2_6f1ed828` | 3, 21, 80, 132, 153, 114, 66, 32, 2, **0** |
| `ell4_P2_fe82b0cd` | 4, 36, 139, 260, 351, 321, 235, 121, 28, 4, **0** |
| `ell0_P2_33d70b42` | 3, 28, 116, 269, 326, 290, 191, 98, 32, 4, **0** |

Measured with the frontier depth limit set to **14** and the state cap to
400,000; the cap was never hit at any survivor (`hit_state_cap: false`
everywhere), so these are complete layer counts, not truncations.

States are deduplicated on the **full** DP key — entry port, 120-bit
free-hexagon mask, all 144 per-orbit port masks, `O_used`, `R_used` — which
is the honest key and the reason the frontier could in principle explode.
It does not. It peaks between depth 4 and 8 at a few hundred states and
then collapses to exactly zero. The last non-empty layer is depth 7–10;
**no survivor's frontier reaches depth 11, let alone 12.**

**Therefore meet-in-the-middle is not merely unnecessary here, it is
undefined: there is no forward layer 12 to meet.** Memory was never the
constraint; the search terminates for free.

Grade: **exact observation** (the frontier sizes), **미완료** for MITM
itself — it was scoped, measured, and then correctly not built.

## 2. Why the two frontiers could not have been joined on the boundary

Recorded because the absence of an implementation should be a reasoned
absence, not a gap.

A meet-in-the-middle join needs a key on which a forward half-walk and a
backward half-walk are compatible. For this problem that key must contain
the coverage: two halves fit together only if their covered-hexagon sets are
**complementary**, and only if their per-orbit port usage does not collide.
So the join key is the full DP key (≈ 120 + 144×5 bits plus the boundary),
not the boundary port. A boundary-only join would produce spurious matches
and could only ever be used as a relaxation — which is precisely the
cover-first mistake in a new costume.

## 3. Backward terminal reachability is vacuous here (§8) — scope correction

Target B's terminal condition is `covered_count = H`: a predicate on the
coverage, **not** on the boundary. In the boundary graph, essentially every
port is the exit of some completing walk once coverage is ignored, so a
backward reachability set computed over boundary keys excludes nothing.

No backward boundary set was computed, and none is claimed. Grade: **scope
correction**. The useful backward information is the residual-capacity
bound, and that is applied in the forward direction, where it is exact:

    H − covered  ≤  5·(O_cap − O_used) + 4·(R_cap − R_used)
    H − covered  ≤  5·(max_segments − segments_used)

## 4. Forward reachability pruning (§7) — implemented and small

The one static prune that does apply: **every segment stands on its own
entry port and completes that port's hexagon**, so an entry port whose
hexagon is already visited *at the root* can never begin a segment. The
free-hexagon set only shrinks along a walk, so the prune is monotone and
therefore safe.

| survivor | statically dead entry boundaries (of 720) |
|---|---|
| `ell0_P2_33d70b42` | 31 |
| `ell4_P2_*` | 25 |
| `ell4_P6_*` | 49 |

Small, as expected — five to nine hexagons are complete at the boundary
states, and each complete hexagon kills its 6 ports. This prune is not
what makes the search terminate; the capacity bound and the forced
successor are.

## 5. No positional / order encoding was written (§11)

No SAT or ILP model with position variables exists in this round, and the
omission is deliberate. In a flow-first model **subtours cannot occur**:
the walk is constructed in order, and its successor is forced up to a binary
choice. Subtour elimination is a repair for the cover-first formulation —
it exists to undo the damage of choosing a set before ordering it. Adding
it here would reintroduce exactly the failure Round 33 diagnosed.

Consequently no `SAT_MODEL_UNSAT_WITH_CERTIFICATE` label is used anywhere in
this round: no SAT model was built, so no SAT certificate can be claimed.
The status actually reached is `EXHAUSTED_NO_PATH`, which is a statement
about an explicitly counted search tree.
