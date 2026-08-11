# SEPARATE_CLEAR: transition closure analysis

작성자: Claude
role: independent theory derivation. No search run.

---

## 0. Blocking status — the seven anchors do not exist in any ref

This task is explicitly conditioned on *"once the latest Codex Round-62
artifacts are reachable."* **They are not reachable.**

Re-checked this round: `git fetch --all --prune` returns no new branches;
Codex tip is still `codex/round-r1-37-hex82-t4` @
`1f9efff0809c47e7ca1857ed6c7734c20e78f081` (Round 61). Direct existence
checks against `outputs/rr_short_113_family_residuals.json`,
`outputs/rr_short_113_family_mechanisms.json` and
`research/RR_SHORT_113_FAMILY_G3_CODEX.md`: all **ABSENT**. A repo-wide
search for the mechanism vocabulary (`SEPARATE_CLEAR`, `MERGED_BY_R`,
`MERGED_BY_Z2`, `SEPARATE_MONOTONE_BLOCKED`) across every ref returns
**zero** matches.

Consequently the per-state work this task requires — *"for each state:
enumerate every legal next macro transition; classify the child; …"* —
**cannot be performed for the seven anchors**, because the seven anchors
are not published. I will not fabricate seven exact states, their legal
transition sets, their orbit/phase/hex targets, or their resource
coordinates. Doing so would produce a document indistinguishable in form
from a real certificate and worthless in content — precisely the failure
mode this project's §5 invalidated-results discipline exists to prevent.

What follows is the part of the target theorem that **is** provable
without the anchors, derived from committed engine source. It is
deliberately organised so that when the anchors land, only §4 needs new
work.

---

## 1. The transition alphabet is exactly four kinds, and `OTHER` is impossible `[HAND THEOREM]`

Task bullet: *"prove whether OTHER is impossible."* It is — in the strong
sense that no `OTHER` child is ever created.

`joint_kind` in `src/search_rr_target_a_exhaustive.py` (line 111) is a
total function admitting exactly four labels:

| weight | abandonment | new_orbit | label |
|---|---|---|---|
| 2 | False | False | `Z2` |
| 2 | True | True | `Z2abandon` |
| 3 | False | False | `R` |
| 3 | False | True | `Z3` |
| *every other triple* | | | `"other"` |

`evaluate_edge` (line 821) begins

```python
if kind == "other":
    return "outside_RR_joint_model", None, None
```

— returning **no child**. So every `"other"` edge is `DEAD` by
construction, never a state in the mechanism graph. In particular the
abandoning weight-3 kinds (A3 `(3,True,True)`, J `(3,True,False)`), the
abandoning weight-2-into-existing kind (A2 `(2,True,False)`), the
structurally impossible `(2,False,True)`, and **every joint of weight ≥ 4**
all map to `"other"` → `DEAD`.

> **Theorem SC-1.** The mechanism-graph node set
> `{MR, MZ, SM, SC, R2, DEAD}` is exhaustive with respect to *joint kind*:
> no legal child is produced by any edge outside the four RR kinds.

This does **not** yet prove there is no fifth *mechanism* — a fifth
mechanism would be a new classification of surviving `Z2`/`Z3` children,
not a new joint kind. That remains the open (C)-level gap.

## 2. Every macro edge strictly consumes one orbit-phase bit `[HAND THEOREM]`

From `extend` (`legacy_research/work/superperm_partial_f1.py`, lines
213-255): the `orbit_masks` update is guarded by `if move.weight >= 2:`,
so weight-1 rotation moves leave `orbit_masks` untouched, and every joint
executes `om[q] |= 1 << phase` at line 245. Lines 240-243 assert that bit
was previously **clear** (*"reused pass-start phase without repeated
window"*) — guaranteed because `extend` already returned `None` at line
221 if `target` was visited, and `perm ↔ (orbit, phase)` is a bijection.

A macro edge is a rotation run plus exactly one joint. Therefore:

> **Theorem SC-2.** Every macro edge increases `popcount(orbit_masks)` by
> exactly 1.

## 3. SEPARATE_CLEAR recurrence is finite and acyclic `[HAND THEOREM]`

Task bullet: *"if SEPARATE_CLEAR recurs, determine whether the recurrence
is finite and acyclic under exact-state monotonicity."* This is fully
answerable now.

> **Theorem SC-3.** Any chain of macro edges — in particular any chain of
> `SC → SC` steps — from a state `s` has length at most
> `720 − popcount(orbit_masks(s))`, and no state can recur along it.

*Proof.* `orbit_masks` has `144 × 5 = 720` bits and is add-only. By SC-2
each macro edge consumes exactly one, bounding the length. A strictly
increasing integer statistic forbids returning to an earlier state, giving
acyclicity. ∎

So `SEPARATE_CLEAR` recurrence is **finite and acyclic**: SC can repeat,
but only finitely often and never in a cycle. Combined with SC-1, every
path terminates in `R2` or `DEAD` after at most 720 macro edges. This is
the strongest half of the target theorem, and it holds for *all* residual
mechanisms, not just SC.

## 4. The mechanism transition graph — provable edges, and the gap

Provable now from `evaluate_edge` and SC-2/SC-3:

| edge | status | ground |
|---|---|---|
| `SC → R2` | **PROVED possible** | `evaluate_edge` line 837: an `R` joint at `r_count == 1` is evaluated as the R2 boundary and never enqueued |
| `SC → DEAD` | **PROVED possible** | `"other"` kind (SC-1); `rr_R_budget_exceeded` (844-846); `hub_touch_count_exceeded` (849-850); prune profile (851-853) |
| `SC → MZ` | **PROVED possible** | a `Z2`/`Z3` whose registered phase-hexagon lies in the other component merges them |
| `SC ↛ MR` | **PROVED impossible** | `MR` is defined by R1 itself having created the merger; R1 is already in the past for every post-R1 state, and `r_count` is monotone |
| `MR → MR`, `MZ → MZ` (merged stays merged) | **PROVED** | co-component is permanent (M2′, `RR_SHORT_MERGED_BY_R_THEORY_CLAUDE.md` §2) |
| `MR/MZ ↛ SC`, `↛ SM` (no un-merging) | **PROVED** | same |
| every path terminates in ≤ 720 edges at `R2`/`DEAD` | **PROVED** | SC-3 |
| `SC → SM`, `SC → SC` | **UNDETERMINED** | depends on the uncommitted definition of `SM` |
| **no fifth mechanism** | **CONJECTURE** | the (C)-level gap; "0 other residual families" is an observation on an unpublished corpus |

## 5. The main theorem target — NOT CLAIMED

> *Target: every descendant of the seven SEPARATE_CLEAR anchors remains
> inside a finite closed mechanism graph until R2 or death.*

The task says: *"Do not claim this unless exact transition completeness is
proved."* Exact transition completeness is **not** proved, so **I do not
claim it.**

Precisely what is and is not established:

- **Finiteness and termination: PROVED** (SC-3) — and proved for all
  states, not merely the seven. Every descendant reaches `R2` or `DEAD`
  within 720 macro edges, with no cycles.
- **Closure of the node set under joint kind: PROVED** (SC-1) — no edge
  escapes via an unmodelled joint.
- **Closure of the *mechanism classification*: NOT PROVED.** This needs
  (a) the published definition of `SEPARATE_MONOTONE_BLOCKED`, and (b) the
  seven anchors, to check that every surviving `Z2`/`Z3` child falls into
  `{MR, MZ, SM, SC}` rather than a fifth class.

So the theorem is proved modulo exactly one missing ingredient, and that
ingredient is data, not mathematics.

## 6. What to do when the artifacts land

The remaining work is mechanical and small:

1. Read the seven anchors from `rr_short_113_family_residuals.json`.
2. For each, enumerate the ≤ 24 candidate macro edges (≤ 6 rotation
   lengths × 4 RR joint moves — one weight-2 and three weight-3, from the
   committed weight distribution `{1:1, 2:1, 3:3, 4:13, 5:71, 6:461}`).
3. Run each through `evaluate_edge` and record the returned verdict
   verbatim; classify surviving children.
4. Confirm no child falls outside `{MR, MZ, SM, SC, R2, DEAD}`.

By SC-3 this terminates, and by SC-1 step 4 can only fail by discovering a
genuinely new *classification*, never a new joint kind. Note this is a
bounded, fully deterministic enumeration over seven published states — not
a continuation search, and consistent with the "no blind continuation
search" instruction.

## 7. Proof-status separation

| result | status |
|---|---|
| SC-1: `OTHER` impossible; four RR joint kinds exhaustive | **HAND THEOREM** |
| SC-2: +1 orbit-phase bit per macro edge | **HAND THEOREM** |
| SC-3: SC recurrence finite and acyclic, depth ≤ 720 | **HAND THEOREM** |
| `SC ↛ MR`; merged-stays-merged | **HAND THEOREM** |
| `SC → R2`, `SC → DEAD`, `SC → MZ` possible | **HAND THEOREM** (from `evaluate_edge`) |
| `SC → SM`, `SC → SC` | **UNDETERMINED** — `SM` undefined in any committed artifact |
| no fifth mechanism | **CONJECTURE** |
| per-anchor enumeration for the seven states | **BLOCKED — anchors absent from every ref** |
| the count "7" itself | **UNVERIFIED PREMISE** |

## End token

`CLAUDE_SC_PARTIAL`
