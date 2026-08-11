# RR-short G3 — the structural invariant that blocks a *future* co-component R joint

**Author:** Claude (independent verification track)
**Round:** 69
**Scope:** the 1,818 residual anchors of the Round-68 corpus, plus the exact engine semantics.
**Reproducer:** `src/analyze_rr_cocomponent_invariant.py`
**JSON mirror:** `outputs/rr_short_g3_cocomponent_invariant_claude.json`
**No continuation search was run.** Section 7 is a *bounded* falsification probe; it always reports
its node cap and never claims exhaustion.

---

## 0. The question, and the one-line answer

The Round-68 one-step screen asked *"is this R joint same-component now?"*. The question here is the
forward one: **can any descendant of a post-R1 state ever present a same-component R joint?**

The answer is carried by a single integer that is already in every committed coordinate record:

```
Phi(s) = 5 + 6*(TARGET_P - P(s)) - (720 - visited_count(s))          # build_rr_target_a_roots.py:68
```

`Phi >= 0` is exactly `remaining_window_capacity_prune`, which `area_a_prune_reason` enforces on
every child and which `is_target_a` therefore also enforces, because the recognizer calls
`area_a_prune_reason` on its own child before deciding anything else.

From `Phi >= 0` alone:

> **At most one hexagon in the whole incidence forest ever has degree 2, and none ever has degree 3.
> Consequently at most one unordered pair of E-orbits is ever co-component, that pair is permanent
> once created, and for three of the four short-root classes the pair admits no weight-3 transition
> at all — so their `same_component` condition can never be satisfied, at any depth, on any branch.**

Applied to the corpus: **1,415 of the 1,818 residual anchors (root_ell ∈ {1,2,3}) are permanently
closed.** The remaining 403 (root_ell = 4) are not closed by this argument, and that is exactly where
the bounded probe found its only same-component witnesses.

---

## 1. Notation and the two forests

`ExactState` (engine `legacy_research/work/superperm_partial_f1.py`) carries

* `hex_masks[h]` — every **visited** window, grouped by rotation hexagon (σ-orbit, size 6, 120 of them);
* `orbit_masks[q]` — the **registered** pass-start phases, by E-orbit (⟨E⟩-orbit, size 5, 144 of them).

`P = popcount(orbit_masks)` (registered count), `visited_count = popcount(hex_masks)`.

`B(s)` is the bipartite incidence forest `component_forest` builds
(`src/build_rr_target_a_roots.py`): one node per non-empty orbit, one node per hexagon carrying a
registered window, one **edge per registered permutation**. `same_component` in the Target-A
recognizer is connectivity of two *orbit* nodes in `B(pre)`, where `pre = edge.run.state` is the
rotation-run end, i.e. the literal R2 joint source.

Write

* `T(s)` = set of **touched** hexagons (`hex_masks[h] != 0`);
* `r(s) = P(s) − |T(s)|`;
* `b_cur(s)` = number of visited windows in `hexagon(p)`.

`B(s)` has `P` edges and `|T|` hexagon nodes, so **`r = Σ_h (deg_B(h) − 1)`**. Every touched hexagon
carries at least one registered window (it was entered as a joint target, or is the initial hexagon,
which `initial_state` registers), so `|T|` really is the hexagon-node count and `r ≥ 0`.

---

## 2. PROVED THEOREM

### T1 — Forced rotation length (FRL)

*In any macro edge that keeps `F` at `TARGET_F = 1`, the rotation length is uniquely determined by
the state:* `ell = m − 1` *where* `m = min{ j ≥ 1 : σ^j(p) visited }` *— i.e. only the **maximal**
rotation run can be used.*

**Proof.** `extend` sets `abandonment = not state.visited(word_after(state.p, SIGMA))` at the run end
`u = σ^ell(p)`, and `dF = int(abandonment)`. For `ell < m − 1` the successor `σ^(ell+1)(p)` is
unvisited by the definition of `m`, so `abandonment` is true and `F` becomes 2; `area_a_prune_reason`
returns `F_exceeded` and the child is deleted, and `F` is monotone so it can never be repaired. For
`ell = m − 1` the successor is visited, so `abandonment` is false. `rotation_runs` cannot go past
`m − 1` because `extend` refuses a repeated window. ∎

Corollary: the branching factor of the whole continuation is at most `|NONROT_H0| = 4`
(`w2:10`, `w3:120`, `w3:201`, `w3:210`), not 24. `H = 0` (also enforced by `area_a_prune_reason`)
forces weight ≤ 3, and `(2,False,True)` and every weight-≥4 joint are outside the RR alphabet.

### T2 — The Φ ledger

`ΔP = 1` and `Δvisited_count = ell + 1` for every macro edge, hence

```
ΔPhi = ell − 5 ,     cost(edge) := 5 − ell ≥ 0 ,     Phi non-increasing.
```

`Phi(initial_state) = 6`, so the **total cost spent from the initial state is exactly `6 − Phi(s)`**,
and `visited_count(s) = 6·P(s) + Phi(s) − 11`.

### T3 — UNIQUE BRIDGE: `6·r ≤ 11 − Phi`, hence `r ≤ 1`

**Proof.** Each hexagon holds at most 6 windows, so `6·|T| ≥ visited_count = 6P + Phi − 11`. Substituting
`|T| = P − r` gives `6P − 6r ≥ 6P + Phi − 11`, i.e. `6r ≤ 11 − Phi`. With `Phi ≥ 0` this forces
`r ≤ 1`. ∎

**Consequences.**

* At most one hexagon node has degree 2; none has degree ≥ 3.
* Every component of `B(s)` is a star centred on an orbit node, except at most one component, which is
  two orbit-stars joined at a single **bridge** hexagon.
* Since a path between two *distinct* orbit nodes alternates orbit/hexagon and every internal hexagon
  on it has degree ≥ 2, **the only orbit pair that can be co-component is the pair bridged at that
  single hexagon.**
* `r` is non-decreasing, so once `r = 1` no second bridge can ever be built: **the co-component pair
  is frozen at the anchor.** This is the answer to "can it become co-component in the future": for
  `r = 1` states, the future cannot change the answer at all.

The bound is tight: `Phi ∈ [0,5]` gives `r ≤ 1` and both values occur; `Phi ≥ 6` gives `r = 0`
(so the initial segment cannot bridge anything); at `Phi = −1` the bound already degrades to `r ≤ 2`.

### T4 — Orbit-changing lemma, in the macro alphabet

For every one of the `6 × 4 = 24` macro generators `g = σ^ell · a` and every one of the 720 words,
`e_orbit_id(σ^ell w) ≠ e_orbit_id(w·g)` and `hexagon_id(σ^ell w) ≠ hexagon_id(w·g)`.
Checked exhaustively: **17,280 / 17,280, zero fixed points on both coordinates.**
So `sq ≠ tq` always, and `same_component` is never satisfied trivially.

### T5 — LIVE / DEAD incidence (a one-sided invariant needing no partition)

Call a permutation **dead** at `s` if it is visited but not registered. A dead permutation can never
be registered afterwards, because registration happens only in `extend` at a joint whose target is
that permutation, and `extend` returns `None` when the target is visited. Dead-ness is therefore
monotone, and every rotation target is dead the moment it is used (weight-1 moves do not touch
`orbit_masks`).

Let `B_live(s)` be the incidence graph on the full 144 + 120 node set whose edges are the
permutations that are **not** dead at `s`. Then `B(s') ⊆ B_live(s)` for every descendant `s'`, so:

> If two orbits are separated in `B_live(s)`, they are separated in every future state.

This is one-sided in the strong sense the brief asks for: knowing only *some* dead permutations
gives a *larger* graph, so any separation certificate computed from partial knowledge remains valid.

### T6 — Re-entry costs

Entering a hexagon that already holds `a ≥ 1` visited windows forces the **next** macro edge to cost
at least `a` (the free run after the entry point has length at most `5 − a`, so `m ≤ 6 − a`).
Symmetrically, leaving a hexagon with gaps and returning to it costs at least `5 + b ≥ 6` in total,
where `b` is the occupancy at departure. Hence:

> With `Phi(s) ≤ 5`, **no hexagon first entered at or after `s` can ever be bridged.** Only hexagons
> already gapped at `s` are candidates, and re-entering one with `g` gaps costs `6 − g`.

### T7 — σ-adjacency admissibility lemma

*Two distinct E-orbits sharing a hexagon `h` admit a weight-3 transition (in either direction) **iff**
their ports in `h` are σ-adjacent.*

Checked exhaustively on all `120 × C(6,2) = 1,800` co-hexagonal port pairs: rotation distance 1 →
720 pairs, **all admissible**; rotation distance 2 → 720 pairs, **none**; rotation distance 3 → 360
pairs, **none**. Agreement 1,800/1,800, disagreement 0. Every admissible pair is admissible in
*both* directions (720 ordered pairs over 360 unordered). The same 360 pairs are exactly the
weight-2-admissible ones.

Global geometry, for context: `B_full` is 5-regular on orbits, 6-regular on hexagons, connected, of
diameter 8. Of the 2,160 ordered weight-3 orbit pairs, 720 are at incidence distance 2 and 1,440 at
distance 4. Of the 1,440 unordered orbit pairs at distance 2, **1,080 (75%) admit no weight-3
transition whatsoever.**

### T8 — Short-root closure

The hub hexagon is `hexagon_id(identity) = 0`. Its six windows lie in orbits
`0, 120, 33, 9, 3, 1` at positions `0, 1, 2, 3, 4, 5`. A short root with rotation length `ell0`
starts at the identity (position 0, registered) and rotates through positions `1 … ell0`, which
become **dead** (visited by a rotation, never registrable, T5). Positions `ell0+1 … 5` stay free, and
`Phi(root) = 6 − (5 − ell0) = ell0 + 1`.

For an `r = 0` state the counting closes completely: `r = 0` means every entry was into a virgin
hexagon, so `b_cur = 1`, so the gaps outside the current hexagon number
`(11 − Phi) − (6 − 1) = 6 − Phi`. A bridge must re-enter a gapped non-current hexagon, at cost
`≥ 6 − g ≥ 6 − (6 − Phi) = Phi`; the budget is `Phi`; hence **the cost is exactly `Phi`, all outside
gaps lie in one hexagon, and that hexagon is the hub** (its free run has `5 − ell0 = 6 − Phi`
positions). A joint into hub position `g` therefore makes the *next* edge cost exactly `g`:

| root_ell | Φ | dead hub pos. | free hub pos. | entry g | bridged pair | σ-dist | w3? | next-edge cost | outcome |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 1 | 2,3,4,5 | 2 | {0,33} | 2 | no | 2 | survives, **pair has no weight-3 transition** |
| | | | | 3 | {0,9} | 3 | no | 3 | dead end (cost > Φ) |
| | | | | 4 | {0,3} | 2 | no | 4 | dead end |
| | | | | 5 | {0,1} | 1 | **yes** | 5 | **dead end (cost 5 > Φ=2)** |
| 2 | 3 | 1,2 | 3,4,5 | 3 | {0,9} | 3 | no | 3 | survives, no weight-3 transition |
| | | | | 4,5 | {0,3},{0,1} | 2,1 | no,yes | 4,5 | dead end |
| 3 | 4 | 1,2,3 | 4,5 | 4 | {0,3} | 2 | no | 4 | survives, no weight-3 transition |
| | | | | 5 | {0,1} | 1 | **yes** | 5 | **dead end (cost 5 > Φ=4)** |
| 4 | 5 | 1,2,3,4 | 5 | 5 | {0,1} | 1 | **yes** | 5 | **LIVE** |

> **THEOREM (POST-R1 R-COCOMPONENT OBSTRUCTION, short-root form).**
> For a short root with `ell0 ∈ {1,2,3}`, no legal R joint in any descendant of any of its post-R1
> states satisfies `same_component`. The unique bridge that the Φ budget can afford joins orbit 0 to
> the orbit at hub position `ell0+1`, which is at σ-distance 2 or 3 and therefore admits no weight-3
> transition at all (T7); the one σ-adjacent live partner sits at hub position 5 and costs 5, which
> exceeds `Phi ≤ 4`, so a bridge to it leaves a state with **zero** legal macro edges and no R2 can
> fire after it; the other σ-adjacent partner (position 1) is dead by T5; and no *second* bridge is
> ever possible by T3. ∎

The `ell0 = 0` row of the same table comes out **LIVE** (`g = 1`, pair `{0,120}`, cost 1 ≤ Φ = 1),
which is the right sanity check — the project's known Target-A boundaries include ℓ=0 ones, and the
criterion does not wrongly close them.

---

## 3. Corpus application (all 1,818 anchors)

Corpus: the three Round-68 parts, `schema rr-short-t4-direct-z2-families-v1`,
`source_round62_sha256 5e8b9650…`, `payload_sha256 eae160b9…`, 24 families / 1,818 anchors.

| quantity | value |
|---|---|
| `Phi` distribution | `{0: 1713, 2: 87, 3: 6, 4: 6, 5: 6}` |
| `root_ell` distribution | `{1: 528, 2: 446, 3: 441, 4: 403}` |
| `r = 1` (bridge already built) | 1,714 |
| `r = 0` (no bridge yet) | 104, all with `Phi = root_ell + 1` exactly |
| distinct bridged pairs over the whole corpus | **4**: `{0,33}` (441), `{0,9}` (441), `{0,3}` (435), `{0,1}` (397) |
| bridge hexagon | hexagon 0 in every certified case |
| `|R1.component_orbits|` | `{1: 104, 2: 1714}` — matches `r` exactly |
| `|hub.component_orbits|` | `{1: 104, 2: 1714}` — identical |

`root_ell` determines the bridged pair with no exceptions: `1→{0,33}`, `2→{0,9}`, `3→{0,3}`,
`4→{0,1}` — precisely the hub positions `ell0+1` predicted by T8.

### Verdict

| class | anchors | verdict |
|---|---|---|
| `root_ell ∈ {1,2,3}` | **1,415** | **PERMANENTLY_NO_SAME_COMPONENT_R_JOINT** — no Target-A boundary anywhere in their subtrees |
| `root_ell = 4` | **403** | not closed by this argument; bridged pair `{0,1}` is weight-3 admissible in both directions |

A refinement of the Codex mechanism labels falls out. `D_ALREADY_MERGED_BY_R1` conflates two
structurally different situations: 1,633 anchors where a genuine bridge exists (`r = 1`), and **81
anchors where the R1 target orbit simply *is* the hub orbit 0** (`r = 0`, no bridge, one bridge still
affordable). The 23 `SEPARATE_*` anchors (16 `SEPARATE_MONOTONE_BLOCKED` + 7 `SEPARATE_CLEAR`) are
exactly the 23 with `R1_hub_same_component = false`, all of them `r = 0`. The `r` split is the one
that governs the future; the mechanism labels are not.

---

## 4. REFUTED CONJECTURES

**RC-1 — "a post-R1 legal R joint can never become co-component." FALSE.**
The bounded probe (§7) found genuine `SAME_COMPONENT` R2 evaluations from certified post-R1 states,
with source/target orbit pair exactly `{0,1}` — the `root_ell = 4` bridged pair. The universal
version of the obstruction is refuted; only the `ell0 ∈ {1,2,3}` version survives. This is a real
refutation of my own strongest candidate, not a technicality: it is what forces the theorem to be
stated per root class.

**RC-2 — "a group-theoretic / parity invariant separates the two orbits." FALSE.**
Every macro edge is right multiplication by `σ^ell · a`; the 24 generators mix signs
(`σ` odd, `w3:210` even), `B_full` is connected with diameter 8, and the exhaustive count shows no
generator preserves either coordinate. No Cayley or parity invariant can block anything. The
obstruction is a **resource** obstruction (Φ), not an algebraic one.

**RC-3 — "deciding future co-componentness needs the full component partition." FALSE.**
`r ≤ 1` is derived from two integers (`P`, `visited_count`) via `Phi`. The verdict for 1,415 anchors
needs only `root_ell`. Nothing in §2 or §3 required a component partition to be transmitted.

**RC-4 — "the D3 failure (`hexagon 0 ∈ Φ(q_R1)` for 1,818/1,818) is the mechanism." Downgraded to a
symptom.** D3 fails universally *because* the bridge is always at hexagon 0. The mechanism is the
σ-position of the bridge inside the hub, not its presence.

**RC-5 — my own Round-68 note that "the one-step screen leaves 32,350 candidates undecidable because
third components are unknown." Superseded.** T3 removes the third-component case outright: a
length-4 path would need two degree-2 hexagons, i.e. `r ≥ 2`, which `Phi ≥ 0` forbids. There are no
third components to be ignorant about.

---

## 5. FINITE RESIDUAL MECHANISMS

The complete list of ways a post-R1 legal R joint could acquire `same_component`, and the exact
status of each:

| # | mechanism | status |
|---|---|---|
| M-A | the bridge already exists (`r = 1`); pair fixed = `{0, orbit at hub position ell0+1}` | **closed** for `ell0 ∈ {1,2,3}` by T7; **open** for `ell0 = 4` |
| M-B | no bridge yet (`r = 0`); a joint enters hub gap `g` — sub-cases `g ≤ Phi` (survives) and `g > Phi` (bridged state has zero legal macro edges) | fully enumerated in the T8 table; the only survivable `g` is `ell0+1`, whose pair is inadmissible for `ell0 ∈ {1,2,3}` |
| M-C | a bridge in a hexagon other than the hub | **excluded**: `r = 0 ⟹ b_cur = 1 ⟹` all outside gaps number `6 − Phi` and lie in the hub; and by T6 any hexagon first entered at or after the anchor costs ≥ 6 to bridge |
| M-D | a length-4 path — source and target joined *through a third component* | **excluded** by T3 (`r ≥ 2` required) |
| M-E | `sq = tq` (self-pair) | **excluded** by T4 (0 / 17,280) |
| M-F | source orbit not in the forest at all | not a route to co-componentness; it is the dominant *failure* mode — 97.4% of all R2 evaluations in the probe |

M-D is the "third component" question in the brief, and it is answered outright: with `Phi ≥ 0`
there is no third component to merge through.

---

## 6. EXACT MISSING PREMISE

Three things, stated as precisely as I can make them.

**MP-1 — the 403 `root_ell = 4` anchors are not closed, and closing them needs data the corpus does
not carry.** For those the bridged pair `{0,1}` is weight-3 admissible in both directions, so T7
gives nothing. Deciding each one requires the legality of a weight-3 joint between the ports of
orbits 0 and 1, which depends on `hex_masks` and `orbit_masks` at those specific windows.
**Minimal request to Codex: for each `root_ell = 4` residual anchor, the two sparse lists
`sparse_hex()` and `sparse_orbits()` — nothing else.** That is roughly 403 × (a few dozen integer
pairs), and it makes each anchor decidable by direct replay. Everything else already in the corpus
(component ids, candidate tables, digests) is not needed for this.

**MP-2 — the theorem is a Q2-level theorem, not a Q1-level theorem.**
`Phi ≥ 0` is `remaining_window_capacity_prune`, a necessary condition for an Area-A **NR6 completion**
(`P = 121`). It is unconditional *inside the committed corrected-v5 program*, because `is_target_a`
calls `area_a_prune_reason` on its own child. But `src/build_rr_target_a_roots.py`'s own docstring
draws the Q1/Q2 distinction and warns that capacity reasoning is unsound for Q1 ("is there a Target-A
boundary at all, ignoring completability?"). I ran the sensitivity test: with the window-capacity
prune dropped, the search really does leave the region (`Phi` reached **−3** within 20,000 nodes), so
the premise is load-bearing, not vacuous. **If the project ever needs Q1 rather than Q2, T3 and
everything downstream must be re-derived; at `Phi = −1` the bound already only gives `r ≤ 2`.**
This is the single most important caveat in this document.

**MP-3 — small open points.** Whether hub position 2 is *reachable* for `ell0 = 1` was not decided
(the bounded probe saw entries at positions 3, 4, 5 but none at 2 within 40,000 nodes). It does not
affect the verdict, since `{0,33}` is inadmissible either way. And I claim no exhaustion of any
subtree: every probe below terminated on its node cap.

---

## 7. ADVERSARIAL CHECK (bounded, falsification-directed)

Roots: the **24 distinct certified literal post-R1 states** recovered from
`first_R1_hub_merge_provenance.literal_child_state` across the corpus (1,183 `R1_CHILD_PREPARATION`
provenances with `r_count 0→1` and 612 `V5_CONTINUATION` with `1→1`, deduplicated by `stable_key`).
These are real `ExactState`s, not reconstructions. Expansion mirrors
`search_rr_target_a_exhaustive`: `macro.macro_edges` → `area_a_prune_reason(child, AREA_A)` →
`joint_kind` → R at `r_count = 1` evaluated as an R2 boundary and never enqueued. The probe omits the
hub-touch decoration, which makes it a **superset** of the real search — the sound direction for a
"nothing found" result.

| target of the attack | result |
|---|---|
| T1 (FRL) | **0 violations in 3,411,563 surviving in-alphabet macro edges.** Rotation lengths used: `ell = 5` for 3,411,517 of them; the other 46 are the first edges out of the `Phi > 0` roots and used `ell = 5 − Phi` exactly as predicted. |
| T3 (`r ≤ 1`) | `max r = 1` and `max hexagon degree = 2` over every state reached, including the relaxed-prune runs. |
| T8 / "every future target lands in a virgin hexagon" | **2,507,131 virgin against 427 non-virgin**, and all 427 come from the single `r = 0` root. |
| "no bridge ever forms" | **refuted, as expected**: that `r = 0` root produced 427 non-virgin joint targets and 118 strict merges. |
| "a bridge is useless" | **every** bridge-creating edge from that root led to a state with **zero** legal macro edges: hub position 3 (123×, pair `{0,9}`), position 4 (109×, `{0,3}`), position 5 (195×, `{0,1}`, *the admissible pair*). Costs 3, 4, 5 against `Phi = 2`. Exactly the T8 prediction. |
| RC-1 (universal obstruction) | **refuted**: exactly **3** `SAME_COMPONENT` R2 evaluations, all from `Phi = 5`, `r = 1`, bridged pair `{0,1}` roots — i.e. `root_ell = 4`. All three are identical in shape: depth 1, `ell = 0`, `sq = 1`, `tq = 0`, joint `w3:120`, child `Phi = 0`. No same-component evaluation from any `root_ell ∈ {1,2,3}` root. |
| MP-2 (premise sensitivity) | dropping `remaining_window_capacity_prune` let `Phi` fall to **−3**; `r ≤ 1` still held empirically there, but the *proof* no longer covers it. |

Aggregate over all 24 roots: **960,000 nodes expanded, max depth 12, 904,005 R2 evaluations**, of
which `source_or_target_orbit_not_in_forest` 877,875 (97.11%), `different_components` 26,127 (2.89%),
`SAME_COMPONENT` 3. **All 24 runs stopped on their node cap. No exhaustion is claimed for any root.**

The count of 3 independently matches the corpus's reported "3 Target-A boundaries", and the probe
locates all three in the `root_ell = 4` class, which is where the theorem says they must be.

---

## 8. Evidence grading

| label | statement |
|---|---|
| **HP** (hand proof from committed source) | T1, T2, T3, T5, T6, T8 |
| **EC** (exhaustive finite computation) | T4 (17,280 pairs), T7 (1,800 pairs), the `B_full` geometry, the 360/1,080 split |
| **IV** (independently verified on certified data) | `r ≤ 1`, `visited = 6P + Phi − 11`, the bridge-at-hexagon-0 fact, and the `(Phi, b_cur, gaps)` identity on all 47 certified literal states |
| **BO** (bounded observation, no exhaustion) | everything in §7 |
| **OPEN** | the 403 `root_ell = 4` anchors (MP-1); the Q1 form of the theorem (MP-2) |

Nothing here changes the project's global status: **this project has not proved L₆ ≥ 872
unconditionally.** What it does is remove 1,415 of the 1,818 residual anchors from the Target-A
search space by a hand proof, and reduce the remainder to one crisply stated data request.
