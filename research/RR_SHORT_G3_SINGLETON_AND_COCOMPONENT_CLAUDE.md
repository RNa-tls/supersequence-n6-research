# The singleton exception, and the co-component R-joint question

작성자: Claude
role: independent analysis. No search run — all results are finite table
lookups over the fixed engine plus the supplied 1,818-anchor corpus.

---

## Part I — `short_ell1_r1_94:frontier:76` fully analysed

### 1. Why this anchor alone is `OTHER` — exact answer

The `event_order_class` is a function of **the completer's joint kind** and its
position relative to R1. Cross-tabulating all 1,818 anchors settles it with no
ambiguity:

| `event_order_class` | completer kind | count |
|---|---|---:|
| `CH1` | **R** | 318 |
| `CH2` | **Z2** (post-R1) | 612 |
| `PRE_R_COMPLETER_EVENT_ORDER` | **Z2** (pre-R1) | 783 |
| `UNDECIDED` | none | 104 |
| **`OTHER_POST_R_COMPLETER_EVENT_ORDER`** | **Z3** | **1** |

> **This anchor is the unique one in the corpus whose hub-completer is a `Z3`.**

Every other completer in the residual is an `R` (318) or a `Z2` (1,395). This
one alone completed the hub via a *fresh-orbit* Z3. The label `OTHER` is
therefore not an anomaly or a fallback bucket — it is the correct and
descriptive name for the one anchor outside the {R, Z2} completer dichotomy.

A second uniqueness falls out of the same fact: it is also the **only** anchor
whose canonical `hub_id` equals the engine's literal `HUB = 0` (1 of 1,818).
That is consistent, not coincidental — its completer targets `q0:p0`, the word
`[0,1,2,3,4,5]`, which lies in hexagon 0, so its left-`S6` canonicaliser fixes
the hub hexagon.

### 2. Reconstructed event history

```
macro_index 2 (literal) / 3 (canonical)   R1  —  rot^5;w3:201
    stage R1_CHILD_PREPARATION,  r_count 0 → 1
    joint source  q31:p3  hex32:4  word [1,5,0,2,3,4]
    joint target  q0:p2   hex18:3  word [2,3,4,0,1,5]
    components    before: undefined  →  after: R1 == hub  (ef238a11f158a620)
    hub_touch     0 → 0        (target hexagon 18 ≠ 0, so no hub touch)
    completer     still null,  branch UNDECIDED

    ... 71 further macro edges, r_count stays 1 ...

macro_index 74 (canonical)                COMPLETER — Z3
    source q23:p2   target q0:p0  = word [0,1,2,3,4,5]  = hexagon 0
    hub_touch 0 → 1              (first and only touch of hexagon 0)
    branch → OTHER_OR_UNDECIDED,  event_order_class → OTHER_POST_R_COMPLETER

anchor state = immediately after that edge
    (completer.macro_index 74 == decoration.macro_index 74)
    depth 74,  p = [3,4,5,0,1,2],  F=1 H=0 Ndef=1 O=25 P=76 Phi=2
    R1_hub_same_component = true,  merged component orbits {0,9}, hexes {0,1,4,18}
```

So: **R1 itself merged R1 with the hub at macro-index 2** (hence
`MERGED_BY_R`, like the other 1,182 F7 anchors), and 72 edges later a Z3 first
touched hexagon 0 and became the completer. The two events are independent —
the merge did not involve hexagon 0 at all.

### 3-4. Every post-R1 R-joint from this anchor, and the component relation

An R joint is weight-3, non-abandoning, `new_orbit=False`. From
`p = [3,4,5,0,1,2]` there are exactly **6 rotation lengths × 3 weight-3 moves
= 18** candidates. Computed against the real engine tables:

| rot | source word | `sq` | in comp? | move | target word | `tq` | in comp? |
|---:|---|---:|:--:|---|---|---:|:--:|
| 0 | `[3,4,5,0,1,2]` | **9** | **yes** | w3:120 | `[0,1,2,4,5,3]` | 3 | no |
| 0 | | **9** | **yes** | w3:201 | `[0,1,2,5,3,4]` | 4 | no |
| 0 | | **9** | **yes** | w3:210 | `[0,1,2,5,4,3]` | 5 | no |
| 1 | `[4,5,0,1,2,3]` | 3 | no | ×3 | | 1, 72, 96 | no |
| 2 | `[5,0,1,2,3,4]` | 1 | no | w3:120 | `[2,3,4,0,1,5]` | **0** | **yes** |
| 2 | | 1 | no | w3:201/210 | | 138, 32 | no |
| 3 | `[0,1,2,3,4,5]` | **0** | **yes** | ×3 | | 120, 65, 129 | no |
| 4 | `[1,2,3,4,5,0]` | 120 | no | ×3 | | 33, 51, 57 | no |
| 5 | `[2,3,4,5,0,1]` | 33 | no | w3:120 | `[5,0,1,3,4,2]` | **9** | **yes** |
| 5 | | 33 | no | w3:201/210 | | 13, 15 | no |

**Co-component options (both `sq` and `tq` in the merged component): 0 of 18.**

The near-miss structure is perfectly anti-correlated: whenever the source is
in the component (rot 0 and rot 3), every target is outside; whenever a target
is in the component (rot 2 and rot 5), the source is outside. There is no
alignment.

### 5. Does it canonicalise to known-18?

**The question does not type-check, and the honest answer is "not comparable".**
This anchor is a **pre-R2 frontier state** (`r_count = 1`); the three known-18
witnesses are **post-R2 boundary states**. They are different kinds of object.
For the record its hashes match none of them —
`canonical_state_hash = 49020754…`, `proved_left_S6_canonical_hash = e7e7cc2f…`
versus witness hashes `79f21d2f…`, `20585475…`, `f1a92555…` — but a
non-match between a frontier state and a boundary state carries no
information. No known-18 claim, positive or negative, is made.

### 6. Verdict: **included in the generic theorem** `[HAND THEOREM]`

Not a counterexample, and not a separate exception requiring its own closure.
The decisive argument is that its distinguishing feature is **invisible to the
Target-A predicate**:

`target_a_recognizer` accepts iff its six named conditions hold —
`exactly_two_R_events`, `immediately_after_R2`, `F_def_equals_1`,
`H_equals_0`, `hub_touch_count_le_2`, `same_component`. It reads
`r_count`, the firing joint's `joint_kind`, `state.F`, `state.H`,
`after.hub_touch_count`, and `incidence_components`. **It never reads
`completer`, `event_order_class`, or `branch`.** (`chaining` is computed and
explicitly *not* an acceptance condition.)

So the one property that makes this anchor unique — a Z3 rather than R/Z2
completer — cannot change any Target-A outcome. On every property the
predicate *does* read, it is unexceptional:

| property | this anchor | the other 1,817 |
|---|---|---|
| mechanism | `MERGED_BY_R` | 1,182 others identical |
| `R1_hub_same_component` | true | true for all 1,795 merged |
| `F, H, Ndef, r_count` | 1, 0, 1, 1 | identical for all 1,818 |
| `hub_touch_count` | 1 | ≤ 1 for all 1,818 |
| D3 (`Φ(q_R1) ∋ hexagon 0`) | fails | fails for all 1,818 |
| co-component one-step R joints | 0 of 18 | 0 of 18 for all 1,818 |

It is an ordinary F7/`MERGED_BY_R` anchor carrying an unusual bookkeeping
label. **Classification: included in the generic theorem.**

---

## Part II — the co-component R-joint question over all 24 families

### 7. An engine-universal lemma that sharpens the question `[HAND THEOREM]`

> **Lemma (orbit-changing).** Every move in this engine maps a permutation into
> a **different** E-orbit. Verified exhaustively over the fixed tables: for all
> 720 permutations, source orbit = target orbit in **0** cases for weight-1
> (720 pairs), **0** for the unique weight-2 (720 pairs), and **0** for
> weight-3 (2,160 pairs).

**Consequence.** For every R joint, `sq ≠ tq` necessarily. So Target-A's
`same_component` can never be satisfied the trivial way (source and target in
one and the same orbit); it *always* demands two **distinct** orbits that are
genuinely co-component in the incidence forest. This closes off what would
otherwise be the cheapest route to a Target A, and it is a fact about the
engine, independent of any branch.

### 8. Exhaustive one-step screen over the corpus `[EC]`

For all 1,818 anchors × 6 rotation lengths × 3 weight-3 moves = **32,724**
candidate R joints, classified by whether `sq` and `tq` lie in the R1/hub
merged component:

```
(source in comp, target in comp)      count
(False, False)                       32,350
(False, True )                          323
(True , False)                           51
(True , True )                            0     <-- never occurs
```

Per family, the count of anchors possessing at least one co-component one-step
R joint is **0 / n** for all 24 families, without exception.

### 9. What this does and does not establish — stated carefully

**Definitively decided (374 of 32,724 candidates):** the 323 `(False, True)`
and 51 `(True, False)` candidates **cannot** yield Target A. If exactly one of
`sq`, `tq` lies in the merged component then they are in different components,
so `same_component` is false. `[HAND THEOREM]`

**Not decided (32,350 candidates):** both orbits lie outside the R1/hub
component. They could still be co-component **in some third component**, and
this corpus does not carry the full component structure — only the R1 and hub
components are recorded, while `O` runs as high as 40 open orbits. I cannot
evaluate `same_component` for these, and I do not.

**Therefore the honest headline is narrower than "0 of 1,818":**

> **Theorem (one-step R1-component obstruction).** `[EC over the corpus]`
> At every one of the 1,818 residual anchors, no immediately-firing R joint —
> at any of the 6 rotation lengths, with any of the 3 weight-3 moves — has both
> its literal joint-source orbit and its target orbit inside the R1/hub merged
> component. Exhaustive over 32,724 candidates, zero exceptions.

Three limits, all load-bearing:

1. **One step only.** This is the immediate R joint *from the anchor*. It says
   nothing about descendants, whose position `p` differs and whose components
   have grown (monotonically, by M2′).
2. **R1 component only.** A Target A lying wholly inside some other component
   is untouched by this screen.
3. **Component relation only.** Legality is not tested — target-window
   freshness, non-abandonment, and `om[tq] ≠ 0` are all unchecked here.

So this is **not** a closure of any family, and G3 is not claimed. It is a
sharp, exhaustive, and previously unrecorded structural fact about the residual.

### 10. Why this is nevertheless the right theorem to chase

Combining with the earlier results the residual now sits in a very tight spot:

- all five non-component Target-A conditions are satisfied at **every** anchor
  (F=1, H=0, Ndef=1, r_count=1, hub_touch ≤ 1) — zero resource leverage;
- D3 fails at **1,818/1,818**, so the direct-Z2 disjointness lemma and T4 are
  structurally inapplicable;
- co-component is permanent once achieved (M2′), so the merged component can
  only grow;
- yet the merged component contributes **no** one-step Target A at any anchor,
  and by §7 no R joint can shortcut via `sq = tq`.

The single remaining question is therefore sharper than before:

> **Can any descendant of a residual anchor reach a state where the R2 joint
> source orbit and target orbit are co-component — in the merged component or
> any other?**

For the merged component the one-step answer is uniformly no. Extending that
from one step to all descendants is exactly the missing theorem, and §9's
limit 2 (third components) is the part that most needs data: publishing the
**full component partition per anchor**, not just the R1 and hub components,
would let this screen become decisive rather than partial.

---

## 11. Proof-status summary

| result | status |
|---|---|
| the singleton is `OTHER` because its completer is the corpus's only Z3 | **EC** |
| its event history (R1 merge at mi 2, Z3 completer at mi 74) | **EC** |
| its 18 one-step R joints, 0 co-component | **EC** |
| the recognizer never reads `completer`/`event_order_class`/`branch` | **HAND THEOREM** (source) |
| **verdict: included in the generic theorem, not an exception, not a counterexample** | **HAND THEOREM** |
| known-18 comparison | **NOT APPLICABLE** — frontier vs boundary state |
| orbit-changing lemma: every move changes E-orbit; `sq ≠ tq` always | **HAND THEOREM** (exhaustive over fixed tables) |
| one-step R1-component obstruction, 0 of 32,724 | **EC over the corpus** |
| 374 candidates definitively not Target A | **HAND THEOREM** |
| 32,350 candidates undecidable (third components unknown) | **explicitly OPEN** |
| any residual family closed | **NO** — G3 not claimed |

## End token

`CLAUDE_G3_SINGLETON_INCLUDED_COCOMPONENT_PARTIAL`
