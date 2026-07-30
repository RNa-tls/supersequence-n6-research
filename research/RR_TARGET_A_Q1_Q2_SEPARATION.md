# The Q1/Q2 prune audit: what is safe for "any boundary", what is not

Round 36, Part C (sections 8-10). Source
`src/search_rr_target_a_unified.py::PRUNE_CLASSIFICATION`.

## 0. The bug this fixes

Round 35 introduced the Q1/Q2 distinction and correctly refuted the
capacity/completability bound as a Q1 prune. But its "Q1" search
(`search_rr_target_a_exhaustive.py::run`) still called
`macro.area_a_prune_reason(tr.state, AREA_A)` on **every** intermediate
state — the bundled function, not its atomic pieces. That function bundles
ten sub-conditions, of which six assume the walk eventually reaches
`TARGET_P = 121`, `TARGET_O = 25`, `TARGET_D = 4`. So Round 35's "Q1" run
already had completion assumptions baked in; it was better than using the
explicit capacity bound, but not actually Q1-clean. This document is the
line-by-line audit that fixes that, and `q1_safe_prune_reason` in the
unified module is the corrected implementation.

## 1. The ten sub-conditions of `area_a_prune_reason`, decomposed

| sub-condition | monotone? | Target A's own definition requires it? | verdict |
|---|---|---|---|
| `F_exceeded` (`F_def > 1`) | yes | yes — child must have `F_def == 1` | **Q1-SAFE** |
| `H_positive` (`H > 0`) | yes | yes — child must have `H == 0` | **Q1-SAFE** |
| `N_exceeded_monotone` (`Ndef > 3`) | yes | no, but defines the Area-A **scope** | **Q1-SAFE within Area A** |
| `F1_fragment_normal_form_impossible` | n/a (structural, not forward-looking) | no, a reachability sanity check | **Q1-SAFE** |
| `P_exceeded` (`P > 121`) | yes | **no** | **Q2-ONLY** |
| `O_exceeded` (`O > 25`) | yes | **no** | **Q2-ONLY** |
| `final_D_impossible` | invariant (see §3) | **no** | **Q2-ONLY** |
| `remaining_pass_starts_exceed_remaining_windows` | yes | **no** | **Q2-ONLY** |
| `remaining_cover_capacity_impossible` (Φ<0) | yes | **no** | **Q2-ONLY** |
| `insufficient_future_orbit_opening_credit` | yes | **no** | **Q2-ONLY** |

Every "no" in the third column traces back to the same fact: the check
compares a state quantity against one of `TARGET_P`, `TARGET_O`, `TARGET_D`
— the exact values of a **complete** Area-A NR6 walk. Target A's own
definition (child `F_def==1`, child `H==0`, same-component) never mentions
any of them.

## 2. Why the four Q1-SAFE ones survive scrutiny

* **`F_exceeded`.** `dF = int(abandonment) ∈ {0,1}`, so `F` never
  decreases. Target A's recognizer requires the boundary's own child to have
  `F_def == 1`. Once `F_def > 1`, no descendant can ever return to `F_def ==
  1`, so no descendant can be a Target A boundary. This is not a scope
  choice — it follows directly from Target A's definition.
* **`H_positive`.** Identical argument (`dH = max(weight−3,0) ≥ 0`, and
  Target A requires child `H == 0`). Within the RR alphabet actually
  explored (`w2:10`, `w3:120`, `w3:201`, `w3:210`, all weight 2 or 3),
  `dH = 0` always, so this prune is empirically vacuous here — recorded
  anyway because the argument does not depend on that fact.
* **`N_exceeded_monotone`.** `Ndef` is monotone (`dNdef = dS + dF − dO ∈
  {0, +1}` for every RR joint, checked by case analysis over all four
  joints). `n_limit = 3` defines **Area A**, the search domain every round
  since 27 has operated in — all 18 known boundaries' children satisfy it.
  Using it is a **disclosed scope restriction**, not a claim about Target A
  boundaries outside Area A (which remain entirely unexplored, and are
  recorded as such in `RR_TARGET_A_COVERAGE_STATUS.md`).
* **`F1_fragment_normal_form_impossible`.** References no `TARGET_*`
  constant at all; its own docstring calls it "a necessary prefix
  invariant, not an unproved pruning heuristic." It tests whether the
  *current* state's fragment geometry is even a legally reachable F≤1
  prefix — a consistency check, not a forward-looking one. Expected to be
  vacuous downstream of `F_exceeded`; kept for defensiveness.

## 3. The subtle case: `final_D_impossible`

`arithmetic_D_reachable` tests whether `(TARGET_D − D + r)` — with
`r = TARGET_P − P` — is a non-negative multiple of 5 not exceeding `5r`.
Direct simulation (4,000 random legal macro edges from the identity, every
distinct value of `(TARGET_D − D + r) mod 5` recorded) confirms it is
**invariant along the whole trajectory**: every weight≥2 event changes the
quantity by either −5 (fresh orbit) or 0 (existing orbit), both preserving
the residue mod 5. So whether this check ever fires is fixed from the true
root and cannot change state to state along a legal walk.

That invariance makes the Q1/Q2 classification of this one condition
**practically moot** here — it is either always true or always false along
any given trajectory from the identity, so whether it is applied as a
traversal prune changes nothing for these roots. But it is still classified
**Q2-ONLY on principle**: the *property* it tests is reachability of the
exact pair `(TARGET_P, TARGET_D)`, a completion condition Target A's
definition does not ask for. The classification records what the check
means, not merely whether it happens to matter for the corpus at hand.

## 4. `remaining_cover_capacity_impossible` is exactly the refuted bound

This sub-condition is Φ<0, i.e. the Round 32/34/35 capacity bound. It is
**the same bound** Round 35 proved unsound as a Target A prune — replayed
along a known short boundary's own path, it goes negative strictly before
that boundary's R2 edge. Finding it bundled inside `area_a_prune_reason`
and therefore silently present in Round 35's own "Q1" search is the
concrete instance of the bug this round fixes.

## 5. Additional Q1-safe candidates from the brief, and why only one was added

| candidate | adopted? | reasoning |
|---|---|---|
| exact permutation collision | already built in | `exact.extend` returns `None` on a repeated window; not a separate check |
| R count exceeded | **adopted** (`r_count_exceeded`) | an RR word has exactly two R events, 손증명 (Round 33/35); monotone, definitional |
| hub touch count exceeded | **not adopted** | no sound *local* bound exists without assuming a specific eventual CH1/CH2/completer structure — exactly the assumption Part C forbids |
| impossible event order | folded into R-count | Target A's only order constraint ("the R2 event is the second R") is exactly the R-budget |
| exact terminal predicate contradiction | not a traversal prune | it is the recognizer test, applied only at the exact candidate edge, never extrapolated |

## 6. What Q1-safe search actually costs

Dropping the six Q2-only sub-conditions removes most of the pruning power
Rounds 30–35 relied on. A calibration run (the `ell=4` short-family root,
node cap 30,000) expanded at ≈850 nodes/second and the **queued frontier
was still growing faster than nodes were being expanded** — 51,055 queued
after 30,000 expanded. This is not a bug: it is the direct, expected cost of
refusing to use completion-assuming prunes for a completion-agnostic
question. See `RR_TARGET_A_COVERAGE_STATUS.md` for what this means for the
round's actual search budgets and results.

## 7. The forbidden-prune test

`q1_forbidden_prune_check(reason)` raises `AssertionError` if a Q1 run ever
reports a `Q2_ONLY_REASONS` member. `q1_safe_prune_reason` is a **separate,
direct re-implementation** of the four safe checks (not a filter over
`area_a_prune_reason`'s output), specifically so that a future edit to
`area_a_prune_reason` cannot silently widen what Q1 uses.
`tests/test_rr_target_a_unified.py::test_q1_search_never_uses_a_forbidden_prune`
exercises this against a live search run.
