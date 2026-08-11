# Ω applied to the real Round-68 residual anchor corpus (1,818 anchors)

작성자: Claude
role: independent analysis of the supplied anchor corpus. No search run.

---

## 0. Corpus integrity

Three uploaded parts, treated as one corpus. All three carry identical
`schema` (`rr-short-t4-direct-z2-families-v1`), identical
`source_round62_sha256` (`5e8b9650…6549`) and identical `payload_sha256`
(`eae160b9…0904`) — consistent with a single source split three ways.

| part | families | anchors (declared) |
|---|---|---|
| 1/3 | 8 | 594 |
| 2/3 | 8 | 626 |
| 3/3 | 8 | 598 |
| **total** | **24** | **1,818** |

Recounted from the actual `anchors` arrays: **24 families, 1,818 anchors** —
declared counts match. `[EC]`

Still not verifiable: the two SHA-256 values (no source file to hash), and the
439-checkpoint aggregate. Round 68 remains unpushed — `git fetch --all` still
shows the Codex tip at `1f9efff` (Round 61).

---

## 1. Task 1 — Ω-state reconstruction: **4½ of 5 fields recovered**

Ω = `(orbit_masks, p, F, r_count, hub_touch_count)`.

| Ω field | recoverable? | source |
|---|---|---|
| `p` | **yes** | `anchor.endpoint` |
| `F` | **yes** | `anchor.coordinates.F` |
| `r_count` | **yes** | `len(canonical_decoration.r_events)` |
| `hub_touch_count` | **yes** | `canonical_decoration.hub_touch_count` |
| `H` (droppable, §4.3 of the Ω doc) | **yes** | `anchor.coordinates.H` |
| `popcount(orbit_masks)` | **yes** | `anchor.coordinates.P` |
| number of open orbits | **yes** | `anchor.coordinates.O` |
| **the `orbit_masks` bit-vector itself** | **no** (at anchors) | — |

The bit-vector *is* available at the merge event for the 1,795 merged
anchors: `first_R1_hub_merge_provenance` carries complete
`literal_predecessor_state` and `literal_child_state` with `hex_masks`,
`orbit_masks`, `p`, `F`, `H`, `S`. Those are ancestors of the anchor, so by
monotonicity they give a certified **lower bound** on anchor occupancy — sound,
and enough for VNTS-style "already visited" inferences, but not enough to
evaluate `new_orbit` per orbit at the anchor or to recompute component
membership at descendants. **So the Ω-closure still cannot be run.**

### 1.1 OMEGA-MONO confirmed empirically on 1,818 real states `[EC]`

My OMEGA-MONO theorem (`RR_SHORT_POST_MERGER_OMEGA_CLAUDE.md` §4.1) says every
macro edge increases `popcount(orbit_masks)` by exactly 1. The corpus lets me
test this directly, and it holds without exception:

```
P − depth  =  2      for all 1818 / 1818 anchors      (a constant)
```

`P` is the used-orbit-phase count and `depth` counts macro edges, so a constant
offset is precisely the theorem. Independently, across all **1,795** merge
edges the literal predecessor→child `popcount(orbit_masks)` delta is **+1**,
with zero exceptions.

A second, separate check: the `popcount(hex_masks)` delta across the same 1,795
edges is also exactly +1. That is *not* a contradiction — it confirms that
`literal_predecessor_state` is the **literal joint source** (post-rotation-run),
per the Round-48 literal-source correction, so the recorded step is the joint
alone, not the whole macro edge. Verified directly: `joint_source.word ==
predecessor.p` and `joint_target.word == child.p` on the sampled records.

### 1.2 Certified per-anchor capacity bounds `[EC]`

From `P` and `O`, using OMEGA-TERM:

- `P` ranges 4..93 ⟹ remaining macro edges ≤ `720 − P` ∈ **[627, 716]**
- `O` ranges 2..40 ⟹ remaining fresh-orbit (Z3) capacity ≤ `144 − O` ∈ **[104, 142]**

**This settles the tractability question negatively.** With branching ≤ 24 and
depth bounds in the 600s, a naive Ω-closure is not computable. My prior
"termination proved, tractability not established" caveat can now be sharpened:
tractability is not merely unestablished, it is *implausible* by brute force.
Any usable Ω argument must exploit structure, not enumerate.

---

## 2. Task 2 — F7/F8 Ω-closure: **not run**, and the resource half gives zero leverage

### 2.1 Independent reproduction of the mechanism split `[EC]`

Recomputed from raw anchor records:

```
MERGED_BY_R                1183
MERGED_BY_Z2                612
SEPARATE_MONOTONE_BLOCKED    16
SEPARATE_CLEAR                7   ->  1818   ✓ matches Codex exactly
```

This resolves audit issue #2 from last round: the split is now confirmed
against the **data**, not merely reproduced by duplicated logic.

### 2.2 F7 ⟺ MERGED_BY_R confirmed at anchor level `[EC]`

All 16 F7 families are **100 % MERGED_BY_R** (79+74+79+82+66+73+74+63+75+65+
65+75+77+71+78+87 = 1183). Last round's structural claim, inferred from
family totals, is confirmed anchor-by-anchor.

**F8's fine structure is more regular than the totals suggested:**

| F8 family | MZ | SM | SC |
|---|---:|---:|---:|
| `short_ell1_r1_39` | 64 | **2** | 1 |
| `short_ell1_r1_5` | 79 | **2** | 0 |
| `short_ell2_r1_17` | 77 | **2** | 2 |
| `short_ell2_r1_57` | 78 | **2** | 0 |
| `short_ell3_r1_58` | 77 | **2** | 2 |
| `short_ell3_r1_61` | 76 | **2** | 0 |
| `short_ell4_r1_18` | 87 | **2** | 0 |
| `short_ell4_r1_71` | 74 | **2** | 2 |

**Every F8 family has exactly 2 SEPARATE_MONOTONE_BLOCKED anchors** (8 × 2 =
16), and SEPARATE_CLEAR occurs in exactly 4 of the 8 (1+2+2+2 = 7). That
uniform "2" is a strong structural signal and is stated nowhere in the ledgers.

### 2.3 The two merge mechanisms are sharply distinguished `[EC]`

| | MERGED_BY_R (1183) | MERGED_BY_Z2 (612) |
|---|---|---|
| `(r_count before, after)` | **(0, 1)** — the merge edge *is* R1 | **(1, 1)** — strictly post-R1 |
| `stage` | `R1_CHILD_PREPARATION` | `V5_CONTINUATION` |
| `macro_label` | `rot^*;w3:120 / w3:201` (weight-3) | **`rot^5;w2:10`, all 612** — the unique weight-2 move |
| `hub_touch_count` | {0: 81, 1: 1102} | {1: 612} — uniformly 1 |
| canonical `branch` | CH1 318 / PRE_R_COMPLETER 783 / other 1 / undecided 81 | **CH2, all 612** |

So `CH2 ⟺ MERGED_BY_Z2` exactly (612 = 612), and MERGED_BY_R is literally
"R1 itself performed the merge". (I do **not** rely on comparing
`provenance.macro_index` to `r_events[0].macro_index` — those use literal vs.
canonical indexing and are not comparable; the `r_count 0→1` transition is the
decisive evidence.)

### 2.4 The resource half of Ω yields **no closure at all** `[EC]`

```
F        = 1  for all 1818          H     = 0  for all 1818
Ndef     = 1  for all 1818          r_count = 1  for all 1818
hub_touch ∈ {0: 104, 1: 1714}  — every anchor ≤ 1, and Target A allows ≤ 2

resource-DEAD anchors (monotone-impossible for Target A):  0 / 1818
```

This is a clean **negative** result and it matters. By M3, in a merged family
the only surviving Target-A obstructions are the five non-component
conditions — and **all five are satisfied at every single residual anchor**.
Not one anchor can be closed by a resource-budget argument. The entire
obstruction burden falls on the component condition and on what happens
downstream.

A corollary kills a tempting shortcut: **merging does not reliably cost a hub
touch.** Of the 1,795 merges, 930 targeted hexagon 0 (`hub_touch` 0→1) but
**865 targeted a different hub-component hexagon and did not increment it**
(targets: hex 18 ×382, hex 4 ×289, hex 1 ×194). So there is no universal
"each merge spends hub budget" argument.

---

## 3. Task 3 — Target-A exits

Unchanged from last round: exactly 3, all `EXACT_KNOWN18_MATCH`, all in
`short_ell4`, split 1 F7 / 2 F8. The anchor corpus adds one clarification:
**none of the 1,818 anchors is itself a Target-A boundary** — every anchor has
`r_count = 1`, i.e. they are all pre-R2 frontier states. The three hits live in
the search's R2 telemetry, downstream of anchors, not in the anchor set.

---

## 4. Task 4 — the 7 SEPARATE_CLEAR anchors: **fully characterised**

All seven, with their single candidate each:

| anchor | family | q_R1 | candidate source (unvisited) | candidate target |
|---|---|---:|---|---|
| `short_ell1_r1_39:frontier:0` | ell1_39 | 33 | q32:p4 hex33:5 | **q33:p1 → hex0:2** |
| `short_ell2_r1_17:frontier:0` | ell2_17 | 9 | q129:p4 hex24:1 | **q9:p2 → hex0:3** |
| `short_ell2_r1_17:frontier:1` | ell2_17 | 9 | q129:p4 hex24:1 | **q9:p2 → hex0:3** |
| `short_ell3_r1_58:frontier:0` | ell3_58 | 3 | q57:p1 hex6:2 | **q3:p3 → hex0:4** |
| `short_ell3_r1_58:frontier:1` | ell3_58 | 3 | q57:p1 hex6:2 | **q3:p3 → hex0:4** |
| `short_ell4_r1_71:frontier:0` | ell4_71 | 1 | q15:p2 hex2:3 | **q1:p4 → hex0:5** |
| `short_ell4_r1_71:frontier:1` | ell4_71 | 1 | q15:p2 hex2:3 | **q1:p4 → hex0:5** |

They are astonishingly uniform. Every one has:

- `depth = 2`, and identical coordinates `F=1, H=0, Ndef=1, O=3, P=4, M=−11`
- `r_count = 1`, `hub_touch_count = 0`, `R1_hub_same_component = false`, zero merge events
- R1 component = a single orbit spanning 2 hexagons; hub component = `{orbit 0}` on `{hex 0}`
- exactly **one** direct-Z2 candidate, `cross_hex = true`,
  `unique_weight2_predecessor_from_fixed_move_table = true`
- status `SOURCE_AND_TARGET_CLEAR_REQUIRES_PRIOR_STATE_CHANGE`,
  `bridge_relevance = WOULD_MERGE_IF_ACCEPTED`
- **source completely unvisited** (`source_hex_mask = 0` — the entire source
  hexagon is untouched), target unvisited, `endpoint_is_source = false`

And the target is always **a phase of the R1 orbit itself landing in hexagon 0,
the hub hexagon**, marching in lockstep with the root index:

```
ell1 → q33:p1 → hex0 position 2
ell2 →  q9:p2 → hex0 position 3
ell3 →  q3:p3 → hex0 position 4
ell4 →  q1:p4 → hex0 position 5
```

This is the textbook direct-Z2 bridge: open one more phase of `q_R1` that
happens to lie in the hub's hexagon. **VNTS cannot block it** — hypothesis H1
fails outright, because the source is not visited (indeed its whole hexagon is
empty). The obstruction is purely reachability: the walk must first travel to
an as-yet-unvisited source. Nothing in this corpus decides whether it can.

### 4.1 A concern of mine that the data refutes

Last round (`RR_SHORT_G3_ROUND68_OMEGA_APPLICATION_CLAUDE.md` §5.1) I flagged
that `all()` over an empty list is `True`, so an anchor with no direct-Z2
candidates would be mis-filed as `SEPARATE_MONOTONE_BLOCKED`, and recommended
splitting the label. **That does not occur in this corpus.** Every one of the
23 non-merged anchors has exactly **1** candidate; none has zero. The concern
was sound as a code observation but is vacuous on the actual data, and the
recommended label split is unnecessary. Withdrawn.

### 4.2 The 16 SM anchors are exactly Full-Hex VNTS instances `[EC]`

All 16 share one configuration, and it is precisely the hypothesis set of my
Full-Hex corollary:

```
status                = SOURCE_VNTS          (all 16)
source_visited        = true                 (all 16)   -> VNTS H1
source_hex_mask       = 63  (hexagon FULL)   (all 16)   -> Full-Hex corollary
endpoint_is_source    = false                (all 16)   -> VNTS H2
permanently_blocked_by_monotone_no_repeat = true
```

So the single direct-Z2 candidate of each of these 16 anchors is **permanently
dead in every descendant** `[HAND THEOREM, VNTS]`. Codex has adopted the
`SOURCE_VNTS` name for exactly this configuration.

**This closes the direct-Z2 route for those 16 anchors — it does not close
Target A for them.** Target A needs `same_component(sq, tq)` for the R2
source/target orbit pair, which those anchors could still obtain via a
component-changing Z3, or without any hub merger at all. I state the narrow
result and decline the broad one.

---

## 5. Task 5 — the residual is exactly the D3-failure class `[EC]`

The strongest result of this round. My generic template
(`RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` §5a) makes T4 depend on hypothesis

> **D3**: `Φ(q_R1) ∩ H_hub = ∅`

and §6 gave the dropped-hypothesis counterexample: *"if some hexagon `h*`
belonged to both sets, registering `q_R1`'s own phase in `h*` … unions `C_R1`
with the hub component in a single move."* That was written as a hypothetical.
It is now checkable, and it is **universal across the residual**:

```
anchors whose Φ(q_R1) contains the hub hexagon 0 :  1818 / 1818
anchors whose Φ(q_R1) meets the hub COMPONENT     :  1818 / 1818
per family: ALL FAIL, all 24, no mixed family
```

For contrast, the T4-verified branch `short_ell2_r1_37` has
`Φ(91) = {40,82,90,91,92}`, which does **not** contain hexagon 0 — that is
exactly why T4 went through there.

> **Theorem (D3-failure characterisation of the residual).** `[EC over the corpus]`
> Every one of the 1,818 residual anchors violates hypothesis D3. Consequently
> the direct-Z2 disjointness lemma — and therefore T4 as proved for
> `short_ell2_r1_37` — is **structurally inapplicable to every residual
> family**, not merely unproved for them.

**One-directional.** I verified D3 fails on all 24 residual families. I did
**not** verify that D3 holds on the 89 closed families — their anchors are not
in this extract, and the 21 `F5` families are also A4-class and may well fail
D3 while closing by monotone blocking instead. So D3-failure is *necessary*
for being residual on this evidence, not shown sufficient.

### 5.1 What the residual now reduces to

Combining §2.4 (all resource conditions live at every anchor), M2′ (co-component
is permanent), M3 (five non-component obstructions) and §5:

> **The 24 residual families reduce to a single question**: for each anchor,
> can a legal `R`-kind joint fire post-R1 whose literal joint-source orbit is
> co-component with its target orbit? Every other Target-A condition is either
> already satisfied (all resources, at all 1,818) or already discharged
> (component, for the 1,795 merged).

This is a genuine sharpening — the obstruction is now one clause, not five —
but it is **not a closure**. No residual family is closed by this round's work,
and I do not claim G3. Observed R2 telemetry (`not_same_component` and
`recognizer_geometry_failure` dominating, 3 `TARGET_A_HIT`) is consistent with
the answer being "rarely, and known-18 when yes", which remains `[BO]`.

---

## 6. Items for Codex

1. **A singleton anchor class.** Exactly one of 1,818 has
   `event_order_class = OTHER_POST_R_COMPLETER_EVENT_ORDER`:
   `short_ell1_r1_94:frontier:76`, depth 74, `O=25, P=76`, merged by an `R`
   edge (`rot^5;w3:201`, target hex 18), with a **Z3** completer
   (`q23:p2 → q0:p0`). A class of size 1 in a 1,818-anchor corpus is worth a
   look before it is relied on.
2. **`canonical_decoration.hub_id` is not the engine's `HUB`.** It ranges over
   all 120 hexagons (1,817 of 1,818 differ from `hub.hub_id = 0`), while the
   *literal* decorations inside the merge provenance correctly carry
   `hub_id = 0`. This is left-`S6` canonicalisation, **not** a bug — I checked
   before reporting. But since `hub_touch_count` is defined relative to
   `dec.hub_id`, it is worth an explicit test that the count is transported
   correctly by the canonicaliser.
3. Audit issue #1 from last round stands unaffected: the
   `true_phase_walk_capacity` firewall greps 2 of 5 proof-path files.
4. Still outstanding: `rr_short_113_family_mechanisms.json` (the earlier item 4
   was a duplicate), and pushing Round 68 so hashes become checkable.

---

## 7. Proof-status summary

| result | status |
|---|---|
| corpus integrity: 24 families / 1,818 anchors as declared | **EC** |
| mechanism split 1183/612/16/7 reproduced from raw anchors | **EC** |
| F7 ⟺ MERGED_BY_R at anchor level; every F8 family has exactly 2 SM | **EC** |
| OMEGA-MONO: `P − depth = 2` on all 1,818; +1 popcount on all 1,795 merges | **EC** (empirical confirmation of a HAND THEOREM) |
| certified capacity bounds `720−P ∈ [627,716]`, `144−O ∈ [104,142]` | **EC** |
| resource half of Ω gives zero closure; 0 resource-dead anchors | **EC** |
| merging does not reliably cost a hub touch (865 of 1,795) | **EC** |
| the 16 SM anchors' direct-Z2 candidates are permanently dead | **HAND THEOREM** (VNTS) |
| D3 fails at 1,818/1,818 ⟹ T4 structurally inapplicable to the residual | **EC over the corpus** |
| residual reduces to the single co-component R2-source question | **HAND THEOREM** |
| the 7 SC anchors' fate | **OPEN** — VNTS cannot apply (H1 fails) |
| Ω-closure of F7/F8 | **NOT RUN** — `orbit_masks` bit-vector absent at anchors |
| any residual family closed | **NO** — G3 not claimed |
| MR-Theorem (all merged Target-A exits known-18) | **CONJECTURE — still declined** |

## End token

`CLAUDE_G3_ROUND68_CORPUS_PARTIAL`
