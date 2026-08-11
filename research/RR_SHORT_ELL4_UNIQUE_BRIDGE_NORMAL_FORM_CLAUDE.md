# ELL4 UNIQUE-BRIDGE TARGET-A NORMAL FORM — the 403 `root_ell = 4` residual anchors, closed

**Author:** Claude (independent verification track)
**Round:** 69b
**Scope label:** **Q2 / Area-A.** Every theorem below consumes `Phi >= 0`, i.e.
`remaining_window_capacity_prune` inside `area_a_prune_reason`, which the committed
`build_rr_target_a_roots.is_target_a` calls on its own R2 child. It is *not* a Q1 result.
**Reproducer:** `src/analyze_rr_cocomponent_invariant.py` (section 7)
**JSON mirror:** `outputs/rr_short_ell4_unique_bridge_normal_form_claude.json`
**No continuation search was run.** No node-capped expansion is used as a proof step anywhere in
sections 1–7; the bounded probe appears only in §8 as a consistency check, explicitly labelled.

---

## 0. Result

> **All 403 of the `root_ell = 4` residual anchors are permanently unable to satisfy the Target-A
> `same_component` condition — at any depth, on any branch.**
>
> The `root_ell = 4` family produces exactly **three** same-component R2 boundaries in total, they
> all occur one macro edge *above* the residual anchors (at the R1 child, not at any anchor), and
> all three are **already in the known 18**, with a **helper-free** `EXHAUSTED_NO_PATH` Target-B
> certificate that applies unchanged.
>
> **New Target-A classes: 0.** Combined with Round 69's T8, **all 1,818 residual anchors of the 24
> residual families are now closed at Q2 scope.**

---

## 1. The ℓ=4 root is rigid

`initial_state()` sits at the identity in the hub hexagon 0 at position 0, registered.
Four `w1:0` rotations visit hub positions 1–4; rotations never touch `orbit_masks`, so those four
windows are **DEAD** (visited, unregistrable — Round 69 T5) forever. From the run end
`(4,5,0,1,2,3)` the four RR tails give

| tail | target | hexagon | E-orbit | `joint_kind` |
|---|---|---|---|---|
| `w2:10` | `(0,1,2,3,5,4)` | **1** (pos 0) | **1** (phase 0) | `Z2abandon` |
| `w3:120` | `(1,2,3,5,0,4)` | 72 | 1 | `other` |
| `w3:201` | `(1,2,3,0,4,5)` | 90 | 72 | `other` |
| `w3:210` | `(1,2,3,0,5,4)` | 114 | 96 | `other` |

`(3, True, ·)` is not in the RR alphabet, so the last three produce no child. **The ℓ=4 root's
joint is unique**: the `Z2abandon` that spends the single `F` unit and lands on hexagon 1 position 0,
registering E-orbit 1 phase 0. Consequences used throughout:

* **`Phi(root) = 5`** (`Phi(initial) = 6`, the root edge has `ell = 4`, cost 1);
* **E-orbit 1 is open at every ℓ=4 descendant**, so a weight-3 joint into any orbit-1 port is an
  `R`, never a `Z3`;
* hexagon 1 is entered at position 0 into a virgin hexagon, so the next macro edge has `ell = 5`
  (T1) and **fills hexagon 1 completely at depth 1**.

The last point is decisive: hexagon 1 positions 1–5 become visited-unregistered, i.e. DEAD, at
depth 1 of every ℓ=4 walk. The corpus agrees independently: `1 ∈ R1.component_hexagons` for
**403 / 403** anchors.

## 2. The bridge is unique: `w* = (5,0,1,2,3,4)`

Round 69 T3 gives `r := P − |T| = Σ_h (deg_B(h) − 1) ≤ 1`, so at most one hexagon of the incidence
forest ever has degree 2. Specialised to ℓ=4:

* at the root, touched hexagons are 0 (positions 0–4) and 1 (position 0); after depth 1 the gap
  identity `gaps = 11 − Phi − 6r` leaves `11 − 5 − 0 = 6` gaps, of which the current hexagon holds
  5, so **exactly one gap outside the current hexagon: hub position 5**;
* re-entering any hexagon first entered at or after the root costs ≥ 6 units of `Phi` (T6) > 5.

**⟹ The only hexagon that can ever acquire a second registered window is the hub, at position 5.**
That window is `w* = (5,0,1,2,3,4)`, E-orbit 1 phase 4. The bridge, if it exists, joins E-orbit 0
(via the identity, position 0) to E-orbit 1 (via `w*`), and

> **the unique co-component E-orbit pair in the entire ℓ=4 family is `{0, 1}`.** *(Task 2: proved,
> not refuted. It is also the only pair ever observed — 397 / 397 bridged anchors carry exactly
> `{0,1}`.)*

## 3. Exactly two R2 shapes

Over all of S₆ there are exactly **two** weight-3 transitions between E-orbits 0 and 1
(exhaustive over 5 + 5 ports × 3 tails):

| shape | source `u` | joint | target `v` | forced `ell` |
|---|---|---|---|---|
| **R2-A** | `w* = (5,0,1,2,3,4)` — hub pos 5, orbit 1 ph 4 | `w3:120` | `(2,3,4,0,1,5)` — hex 18, orbit 0 ph 2 | **0** (`σ(w*)` = identity, visited) |
| **R2-B** | `(4,0,1,2,3,5)` — **hex 1 pos 5**, orbit 0 ph 4 | `w3:120` | `(2,3,5,0,1,4)` — hex 12, orbit 1 ph 2 | **5** (entry at hex 1 pos 0) |

Both use the same tail, `w3:120`. This is the **normal form**: a Q2-admissible ℓ=4 descendant that
reaches a same-component R2 must realise R2-A or R2-B, and nothing else.

### 3.1 R2-B is structurally dead in the ℓ=4 family

Its source is hexagon 1 position 5, and hexagon 1 is full from depth 1 (§1). A rotation run needs
its targets unvisited, so a visited permutation can be a run end only at `ell = 0`, i.e. only if it
is the endpoint — and no anchor's endpoint lies in hexagon 1 (**0 / 403**). **R2-B: closed for the
whole family, by hand proof.**

*(The R2-B shape does occur in these walks — as the **R1** event, before `r_count` reaches 1. That
is why 254 of the 403 anchors have `R1.target_orbit = 1`. Once it has fired as R1, its source is
visited and it can never fire again.)*

### 3.2 R2-A requires standing on `w*` with `Phi = 5`

R2-A departs from `w*` with `ell = 0`, hence costs 5. So the R2-A source state has endpoint `w*`,
hexagon 0 full, `r = 1`, `Phi = 5`, and the R2-A child has `Phi = 0`. This is a **single canonical
local shape** — the state immediately after the bridge.

## 4. The bridge is reachable only along a closed E-cycle

Post-R1, E-orbit 1 is open (§1), so a weight-3 joint into `w*` is an `R` at `r_count = 1`: it is
evaluated as an R2 boundary and **never enqueued**. The only enqueued registration of `w*` is
therefore the weight-2 joint. And `Phi` must stay at 5 until the bridge (the post-bridge edge costs
5), so every pre-bridge macro edge has `ell = 5` — and `σ^5 · a_{w2:10} = E` exactly. Hence the
pre-bridge chain is the **E-orbit-1 cycle**, computed forwards:

```
hex1 ph0  --(ell=5, w2:10)-->  hex72 ph1  -->  hex12 ph2  -->  hex2 ph3  -->  hex0 ph4 = w*
```

with the σ-predecessor of `w*` being the identity, so the cycle closes with period 5.

> **Induction.** If the endpoint `p` of a post-R1 ℓ=4 state is *not* an orbit-1 port, no macro edge
> from `p` registers an orbit-1 port: a weight-3 into an open orbit is a terminal `R`, and the only
> weight-2 route has `ell = 5`, i.e. macro action `E`, so its target is `E(p)` — which is an
> orbit-1 port only if `p` already was one. **Off the cycle is permanent.** ∎

## 5. Verdict on the 403 anchors

| class | count | why closed |
|---|---|---|
| `r = 1`, `Phi = 0` (bridge already built) | **397** | R2-B dead (§3.1); R2-A needs endpoint `w*` and costs 5 > `Phi = 0`, and `w*` is visited so the walk cannot return to it |
| `r = 0`, `Phi = 5` (no bridge yet) | **6** | R2-B dead (§3.1); the bridge needs the E-cycle, and none of the six is on it (`endpoint_is_orbit1_port` **0 / 6**) — §4 |

**403 / 403 `PERMANENTLY_NO_TARGET_A`. 0 remaining.**

Everything the verdict consumes is already in the corpus: `canonical_decoration.root_ell`,
`coordinates.Phi`, `endpoint`, `R1.component_orbits`, `R1.component_hexagons`,
`R1_hub_same_component`. Independent corpus checks, all exact:

* `Phi ∈ {0, 5}` for ℓ=4, and nothing else — `{0: 397, 5: 6}`, exactly the theory's two values;
* `(r, Phi) = {(1,0): 397, (0,5): 6}` — bridge ⟺ `Phi = 0`;
* `hub_touch_count = r` for all 403 (and for all 1,818) — so the Round-20 "hub touch ≤ 2" lemma is
  **subsumed** by `r ≤ 1` and never binds;
* the registered orbit-1 phase sets are exactly E-cycle prefixes: `(0,2)`, `(0,3,1)`, `(0,3,2)` for
  the six unbridged, and `(4,0,…)` for all 397 bridged.

## 6. The three same-component boundaries, and known-18

Where R2-A actually fires: from the post-bridge state (endpoint `w*`, `Phi = 5`), which in this
family is the **R1 child** — the R1 event itself lands on `w*` and builds the bridge. Three such
states appear as certified `first_R1_hub_merge_provenance.literal_child_state` records. Firing
R2-A from each and hashing exactly as `verify_rr_target_a_coverage_status.known18_regression` does
(`sha(stable_key())[:16]` raw, `sha(canonicalize(...).stable_key())[:16]` canonical):

| raw | canonical | boundary state | known-18 row | Target-B |
|---|---|---|---|---|
| `fe82b0cdb5126756` | `20585475b28fe99d` | `P=6 O=2 F=1 H=0 Ndef=2 Phi=0` | `ell4_P2_fe82b0cd`, `short_family_ell4`, `P_core=2`, `R2_edge_ell=0` | `EXHAUSTED_NO_PATH` |
| `6f1ed828b231741d` | `79f21d2facc1ce2a` | idem | `ell4_P2_6f1ed828` | `EXHAUSTED_NO_PATH` |
| `5d3f8cb9fdd40f22` | `f1a925551da6109e` | idem | `ell4_P2_5d3f8cb9` | `EXHAUSTED_NO_PATH` |

**Both** hashes match for all three, so the identification is unambiguous under either convention.
All nine `short_family_ell4` known-18 rows carry `R2_edge_ell = 0` and end their search path with
`rot^0;w3:120` — the R2-A shape, independently corroborating §3.

**Task 5 — helper-free certificate reuse.** `outputs/rr_target_b_18_boundary_corrected_ledger.json`
(Round 39, commit `9b345c4`, verified reachable in this repository's history) carries
`phase_helper_used: false`, `replacement_path: [Round-30 coarse capacity, Round-32 B+R bound, exact
macro DFS]`, and for each of the three rows `corrected_final_status: EXHAUSTED_NO_PATH` with
`truncated: false` (nodes 3558 / 1450 / 1206, max depth 41 / 36 / 33). Its recorded coordinates
`{D:4, Ndef:2, O:2, P:6, phi:0, visited:25}` reproduce my computed boundary states exactly.
Its `surviving_ells: [5]` is also an independent confirmation of the forced-rotation-length theorem
from a Codex-side artifact. **The certificate is reusable verbatim; nothing needs re-running.**

## 7. Task 7 — state recovery: nothing new is needed

The six `r = 0` anchors were **fully reconstructed from corpus fields alone** — hexagon 0 carries
the root's rotation run with only position 0 registered; every hexagon holding a registered orbit-1
port is full (forced by `gaps = 11 − Phi − 6r`); the endpoint's hexagon holds exactly the endpoint.
The reconstructions are legal `ExactState`s and reproduce `P, O, Ndef, F, H, Phi` for **6 / 6**, and
`forced_ell = 5` with four legal RR edges each, none targeting an orbit-1 port.

> **No additional fields are requested.** Round 69's MP-1 (a per-anchor `sparse_hex()` /
> `sparse_orbits()` dump for the 403) is **withdrawn** — it is not needed.

## 8. Consistency check (not a proof step)

The Round-69 bounded probe expanded 960,000 nodes from 24 certified post-R1 states and found
exactly **3** `SAME_COMPONENT` R2 evaluations, all `ell = 0`, `sq = 1`, `tq = 0`, `w3:120` — the
R2-A shape — and all three from the `Phi = 5` roots, whose endpoint is `w*` (verified: `p == w*`
for all three). No same-component evaluation arose from any other root. This agrees with §3–§6 but
is **not** used to establish anything: every claim in §1–§7 is a hand proof or an exhaustive finite
computation over fixed tables.

## 9. Scope and evidence

| label | statement |
|---|---|
| **HP** | §1 root rigidity, §2 unique bridge, §3.1 R2-B death, §3.2 R2-A shape, §4 E-cycle induction, §5 verdict |
| **EC** | the two-element R2 shape table (exhaustive over 2,160 weight-3 orbit pairs), the ℓ=4 root joint table |
| **IV** | the `Phi ∈ {0,5}` split, `(r, Phi)`, `hub_touch_count = r`, `1 ∈ R1.component_hexagons` (403/403), the six reconstructions, the three known-18 hash matches, the helper-free ledger rows |
| **BO** | §8 only |

**The premise, stated once more:** every step uses `Phi >= 0`. That is
`remaining_window_capacity_prune`, a necessary condition for an Area-A **NR6 completion**
(`P = 121`). It is unconditional inside the committed corrected-v5 program because `is_target_a`
calls `area_a_prune_reason` on its own child. It is **not** available for the Q1 question
("does a Target-A boundary exist at all, ignoring completability?") — `build_rr_target_a_roots.py`'s
own docstring warns about exactly that distinction. Dropping the prune lets the search reach
`Phi = −3`, so the premise is load-bearing.

**This project has not proved `L₆ >= 872` unconditionally.** What is established here is that the
24 residual families of the corrected-v5 RR-short program contribute no Target-A boundary beyond
the three already-known-18 ones, at Q2 scope. It says nothing about the 1,398 Target-A boundaries
found in Rounds 35–37, which were never run through the Target-B ledger.
