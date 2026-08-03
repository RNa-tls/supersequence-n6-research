# The 439-child v5 ledger: canonicalization, exhaustion soundness, and the top 8 capped children

Analyst pass over Codex's `codex/round51-short5-child-outcomes` branch.
All data below is read directly from committed files, cross-checked by
independent recomputation from raw records (not by re-reading summary
claims), and in one case by a short, non-search deterministic replay of
an already-given literal path. No search was run.

## 0. Commit verification

```
git fetch origin codex/round51-short5-child-outcomes
git log --oneline: dfc314f, 673bd9f, 4785cc6, all reachable
```

All three cited commits (`4785cc6`, `673bd9f`, `dfc314f`) confirmed
reachable — via `git log` and, for `dfc314f`, independently via the
GitHub API `get_commit` as well. Read: both markdown reports, and the
three JSON files (`rr_short5_child_classes.json`,
`rr_short5_child_outcomes.json`, `rr_short5_capped_priority.json`), plus
`rr_short1_4_corrected_fair_verified.json` and the two analysis source
files (`analyze_rr_short5_child_outcomes.py`,
`analyze_rr_short_ell0_target_b.py`) and the engine
(`search_rr_target_a_exhaustive.py`).

**Independent hash check, done directly rather than trusted**: the
`rr_short1_4_corrected_fair_results.json` file's recorded SHA-256
(`858bf5da...`) did not match a raw byte-hash of the checked-out file —
traced immediately to the same CRLF/LF cross-platform artifact identified
two rounds ago (Codex's Windows authoring environment vs. this Linux
checkout): re-inserting CRLF line endings reproduces the recorded hash
exactly. Not a data-integrity concern, confirmed rather than assumed.
Both independent verifiers already in the branch (`rr_short1_4_corrected_fair_verified.json`
→ `VERIFIED_CAPPED_PILOTS`, `literal_R2_source_verified: true`,
`known18_comparison_verified: true`) are consistent with this.

## 1. Canonicalization: no two children are left-`S6` equivalent

**`CLAUDE_HAND_PROOF`** — independently recomputed, not merely read from
the summary counts:

```python
classes = json.load(open('rr_short5_child_classes.json'))['classes']
member_count distribution: Counter({1: 439})
n mixed_outcomes=True: 0
sum of member_count: 439
n distinct canonical_child_class hashes: 439  (== n classes)
n distinct child_ids across all classes: 439  (== total children, no duplicate)
```

Every one of the 439 canonical classes has exactly one member; every
`canonical_child_class` hash is distinct; every `child_id` appears
exactly once across the whole class ledger. This is a direct
recomputation from the raw per-class records, not a repetition of the
report's own summary line — it independently confirms **no two of the
439 exact decorated children are left-`S6` equivalent to each other**.

**On the canonicalization method itself**: `canonical_boundary`
(`analyze_rr_short_ell0_target_b.py` lines 207-220) does **not** use the
original 720-fold `exact.canonicalize` loop directly — it uses a proven
algebraic shortcut (`action_to_identity`, computing the unique `α` that
maps the state's own terminal permutation to the identity word, which is
always lexicographically least, so the two methods are mathematically
equivalent). This shortcut is cross-checked against the slow,
already-established `exact.canonicalize` method by `full_canonical_control`
on a 24-state audit sample **elsewhere in the pipeline** (the known-18
witness-reconstruction path in the same file), with a hard
`AssertionError` guarding disagreement — and the pipeline completed
without raising it. **This audit is not re-run specifically against the
439-child dataset** — it validates the shared method, not this exact
invocation of it. Recorded as a precise scope distinction, not a gap
papered over.

## 2. Immediate legal-successor count 0 as a local exhaustion certificate

**`CLAUDE_HAND_PROOF`.** `accepted_successors` (`analyze_rr_short5_child_outcomes.py`
lines 70-86) computes:

```python
for edge, collision in rr.iter_raw_macro_candidates(state):
    ...
    verdict, child, _ = rr.evaluate_edge(state, dec, edge, prune_profile=TARGET_A_SAFE_PROFILE)
    if verdict == "child" and child is not None:
        counts["accepted"] += 1
```

`iter_raw_macro_candidates` (`search_rr_target_a_exhaustive.py` lines
451-458) iterates `macro.rotation_runs(state) × macro.NONROT_H0` — every
rotation length crossed with every non-rotation joint move, the complete
move alphabet, with no subsetting. `evaluate_edge` is the exact same
function already independently exercised (regression-tested by this
session, three rounds ago, in an isolated worktree) as the live search's
own classifier. **`accepted_successors(...)['accepted'] == 0` therefore
means literally every possible macro edge from that state — the complete
set, not a sample — was rejected by the same legality check the search
itself uses.** A frontier with nothing addable to it is empty by
definition; an empty frontier with the node cap nowhere near reached is
exactly this project's own established `EXHAUSTED_NO_TARGET_A` criterion
(`queue empty AND no cap hit`, Round 36's status vocabulary). The proof
is genuinely tautological, as the source itself labels it — not
overstated, correctly graded.

**Independently re-verified from raw data** (not trusting the report's
own "107" figure): filtering the 439-child ledger directly for
`immediate_successors.accepted == 0` yields exactly 107 children, and
**100% of them** have `outcome == NATURALLY_EXHAUSTED` — zero exceptions.

## 3. The six exhaustion mechanisms, reassessed against real data

**`CLAUDE_OBSERVATION`**, refining the reassessment from two rounds ago
now that real per-child data exists to check it against:

| candidate mechanism | classification | evidence |
|---|---|---|
| Zero immediate legal successors | **branch-terminating (proved)** | §2 — tautological, 107/107 confirmed |
| Hub-touch restriction (`hub_touch_count_exceeded`) | **branch-terminating (mechanism proved; not shown to explain the 326)** | a genuine, definitional legality blocker when it is the last remaining option; not isolated as the specific cause of any counted exhaustion here |
| R-budget (`rr_R_budget_exceeded`) | **branch-terminating (mechanism proved; not shown to explain the 326)** | same status — proven exact fact, not isolated to specific cases |
| Literal collision (`exact_permutation_collision`) | **branch-terminating, dominant by volume** | the single largest prune category in every one of the top-8 capped children's own dominant-prune tables (77-79k occurrences each) and, by extension, plausibly the largest contributor among the 326 too — a volume observation, not a per-branch causal claim |
| Terminal geometry failure (`F_exceeded`/`H_positive`) | **branch-terminating, secondary by volume** | second-largest prune category throughout (8-9k per top-8 child) |
| Component obstruction (`not_same_component`) | **candidate-rejecting only** | rejects one R2 attempt; per §2's mechanics, cannot by itself empty a frontier that still has non-`R` legal edges |
| Orbit-incidence failure (`r2_wrong_source_orbit`/`recognizer_geometry_failure`) | **candidate-rejecting only, by far the dominant R2 failure reason** | 1,988-2,279 occurrences per top-8 child vs. 120-219 `not_same_component` — roughly 10-20:1 — but still only rejects individual R2 attempts, never a whole branch |
| Event-order class (`PRE_R_COMPLETER_EVENT_ORDER`, `CH1`, `UNDECIDED`) | **observational only — explicitly refuted as a shortcut** | independently recomputed cross-tab: `PRE_R_COMPLETER_EVENT_ORDER` splits `326` exhausted / `100` capped (both outcomes present); `CH1` is `4/4` capped, `UNDECIDED` is `9/9` capped — **neither CH1 nor UNDECIDED shows a single natural exhaustion in this corpus**, a real pattern worth flagging precisely as a small-sample (13 total) observation, explicitly **not** promoted to a theorem |
| Hub popcount at R1 | **observational only — explicitly refuted as a shortcut** | matches the report's own finding: popcount-6 occurs in both 326 exhausted and 101 capped children |

## 4. The top 8 capped children — structural comparison

**`CLAUDE_OBSERVATION`**, all fields read from `rr_short5_capped_priority.json`
and cross-checked against `rr_short5_child_outcomes.json`:

| child | root | R1 depth | `ell` | max depth | immediate accepted | component count | geometry:same-component ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| `short_ell2_r1_70` | `short_ell2` | 55 | 5 | 104 | 1 (Z3) | 18 | 2279:182 |
| `short_ell4_r1_12` | `short_ell4` | 57 | 5 | 102 | 1 (Z3) | 19 | 2074:219 |
| `short_ell1_r1_98` | `short_ell1` | 60 | 5 | 97 | 2 (Z2+Z3) | 21 | 1988:164 |
| `short_ell2_r1_40` | `short_ell2` | 59 | 5 | 101 | 1 (Z3) | 20 | 2268:198 |
| `short_ell3_r1_64` | `short_ell3` | 59 | 5 | 100 | 3 (Z2+2×Z3) | 20 | 2269:120 |
| `short_ell2_r1_37` | `short_ell2` | 45 | 5 | 101 | 1 (Z3) | 14 | 2270:189 |
| `short_ell2_r1_107` | `short_ell2` | 62 | 5 | 101 | 2 (Z2+Z3) | 21 | 2193:186 |
| `short_ell3_r1_56` | `short_ell3` | 60 | 5 | 96 | 2 (Z2+Z3) | 20 | 2174:130 |

**Every one of the 8 shares, without exception**: `event_order_class =
PRE_R_COMPLETER_EVENT_ORDER`; `R1_geometry.joint_label = w3:120`,
`kind = R`, `ell = 5`; completer `kind = Z2`, **`macro_index = 4`**
exactly; `Ndef = 1`, `Phi = 0`, `H = 0`, `F = 1`; dominant prune order
`exact_permutation_collision > outside_RR_joint_model > F_exceeded`;
dominant R2-failure order `recognizer_geometry_failure ≫
not_same_component`.

### A hand-verified structural fact beyond what the summary reports

**`CLAUDE_HAND_PROOF` — the literal target-hexagon sequence for macro
steps 4 through 8 is identical, edge for edge, across all 8 children,
spanning all four roots**: hex `0` (the completer, step 4) → hex `96`
(step 5) → hex `18` (step 6) → hex `4` (step 7) → hex `1` (step 8). Read
directly from each child's own `literal_macro_trace`, not inferred.

**A second exact pattern, also hand-verified from the raw rotation
lengths, not asserted**: the rotation length of step 5 (the one step in
this shared sequence that is *not* a full `rot^5`) is exactly `4 −
root_ell`: `short_ell1 → rot^3`, `short_ell2 → rot^2`, `short_ell3 →
rot^1`, `short_ell4 → rot^0`. This is a clean, testable arithmetic
relationship — recorded as an observation with a strong candidate
explanation (the root's own `ell` extra pure-rotation steps shift the
phase alignment of everything downstream by exactly `root_ell`), not yet
proven from first principles here.

**A live check, not an assumption**: to test whether this shared
sequence reflects the same "R1 available as an alternative to
continuing" structure `short_ell0`'s own productive branch showed, I
replayed `short_ell2_r1_70`'s literal trace up to (not including) step 6
using the actual engine (`exact.extend`, deterministic replay of an
already-complete literal path — not a search) and enumerated every legal
macro candidate at that exact point. **Result: an `R`-kind edge *is*
legal at that point** (`ell=5, w3:120, target=(orbit 0, phase 3), hex
4`) — but it targets a *different* phase/hexagon than the observed `hex
18` continuation, not the same one. This is genuine, hand-verified
confirmation that R1 alternatives exist along this deep preparation
history (matching the qualitative pattern), while also showing the
specific hypothesis "R1 could have fired exactly at the hex-18 point"
is **not** what happens here — a real negative result for the narrower
claim, reported honestly rather than smoothed over. This should be read
as one data point, from one child, at one step — not a general claim
about all 8, let alone all 439.

## 5. Per-child obstruction assessment

**`CLAUDE_OBSERVATION`** for all eight — the *type* of obstruction is
shared (all eight fail overwhelmingly on `recognizer_geometry_failure`,
i.e. the same source-orbit-never-registered mechanism already hand-proved
for `short_ell0`'s own productive branch, via the identical `ell=5`
rotation-lands-in-an-unregistered-orbit argument), so no child among the
8 presents a *qualitatively different* obstruction from the others.
What differs is quantitative, and that is what should drive the
evidence each needs:

| child | most plausible obstruction | evidence needed |
|---|---|---|
| `short_ell2_r1_70` | source-orbit registration barrier (1 accepted successor, `Z3` only) | since only one legal continuation exists, a short forced lookahead (2-3 levels) would already reveal whether this branch's *only* path stays trapped, cheaply |
| `short_ell4_r1_12` | same, structurally identical profile (1 accepted, `Z3` only) | same — single-path lookahead |
| `short_ell1_r1_98` | same barrier, but 2 live continuations (`Z2`+`Z3`) | needs both branches checked; not reducible to a single lookahead |
| `short_ell2_r1_40` | same as `_70`/`_12` (1 accepted, `Z3` only) | single-path lookahead |
| `short_ell3_r1_64` | same barrier, **3** live continuations (`Z2`+2×`Z3`) — the most branching of the 8 | the least tractable of the 8 for a cheap lookahead; likely needs the deepest additional budget |
| `short_ell2_r1_37` | same barrier; smallest `component_count` (14) and shallowest `R1_macro_depth` (45) of the 8, but *largest* checkpoint (81.8 MB) and deepest `post_R1_depth_span` (56) | the component structure is least merged of the 8 — worth checking first whether its small component count reflects genuinely fewer opened orbits or just fewer merges; 1 accepted successor |
| `short_ell2_r1_107` | same barrier; 2 live continuations, best `not_same_component`-to-`geometry_failure` ratio among the 8 (highest share of near-misses that at least clear the source-orbit test) | worth prioritizing if the goal is finding a genuinely new boundary — proportionally closer to satisfying both conditions than its siblings |
| `short_ell3_r1_56` | same barrier; smallest `maximum_macro_depth` (96) and smallest checkpoint (65.4 MB) of the 8 | cheapest of the 8 to deepen further given its smaller state footprint |

**None of the 8 is shown, by this analysis, to have a fundamentally
different obstruction from `short_ell0`'s own already-characterized
mechanism** — this is itself informative: it suggests (does not prove)
that the source-orbit-registration barrier may be a genuinely RR-wide
phenomenon for deep `ell=5`-only R2 attempts, not a `short_ell0`
peculiarity. That remains a conjecture (Lemma-status, not a theorem),
consistent with §3 and two rounds ago's cross-root framework document.

## What this document does not do

- Does not claim any of the 8 (or any of the 113 capped children) will
  eventually resolve to `EXHAUSTED_NO_TARGET_A` or `FOUND_TARGET_A` —
  every one remains genuinely open.
- Does not promote any of the six §3 mechanisms to a theorem about which
  one caused any specific one of the 326 exhaustions — only zero-successor
  is proved as a sufficient local condition.
- Does not claim the hex-`0→96→18→4→1` sequence or the `4−root_ell`
  rotation identity holds beyond the 8 children actually checked here.
- Does not claim the single replayed R-alternative at `short_ell2_r1_70`
  generalizes to the other 7, or to the other 431 children.
- Runs no search, edits no Codex file. The one replay performed (§4) is a
  deterministic re-execution of an already-complete, already-given
  literal path — no branching, no exploration, no new state discovered
  beyond what the existing trace already specifies.

CLAUDE_TOP8_CAPPED_ANALYSIS_READY
