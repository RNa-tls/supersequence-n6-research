# Enumerator correctness: the completion-agnostic Q1 search, certified

Round 37, sections 16, 17, 18. Source `src/verify_rr_q1_enumerator.py` →
`outputs/rr_enumerator_statuses.json`.

## 1. Status vocabulary, fixed (§18)

Seven statuses, mutually exclusive, unchanged from Round 36 and re-affirmed
here as the permanent replacement for the retired `frontier_empty` boolean:

| status | meaning |
|---|---|
| `FOUND_TARGET_A` | ≥1 boundary found; queue may or may not be empty |
| `EXHAUSTED_NO_TARGET_A` | queue emptied naturally — no cap, no timeout, no depth-drop, not stop-on-first — zero found |
| `INCOMPLETE_NODE_CAP` | node budget exhausted first |
| `INCOMPLETE_DEPTH_CEILING` | a depth ceiling dropped ≥1 state unexpanded |
| `INCOMPLETE_TIMEOUT` | wall-clock budget exhausted first |
| `STOPPED_AFTER_FIRST` | witness mode; stopped at first hit by design |
| `INVALID_ROOT` | root failed to replay or reconstruct |

`frontier_empty` does not appear anywhere in this round's code, and does
not reappear in any of this round's outputs. The specific confusions it is
retired to prevent (`FOUND_TARGET_A` vs `EXHAUSTED_NO_TARGET_A` vs
`INCOMPLETE_TIMEOUT`/`INCOMPLETE_NODE_CAP`) are kept distinct in every
output this round produces — `rr_incomplete_root_audit.json` and
`rr_root_capacity_envelopes.json` both report status per-root explicitly,
never a collapsed boolean.

## 2. New-boundary pipeline verification (§16)

Round 36's pipeline (exact replay → canonicalize → dedup vs the 18 known →
capacity theorem → Round 34 flow verifier only for capacity survivors) is
re-verified against the final 1,398-boundary corpus:

* **Replay**: 1,398/1,398 independently re-confirmed
  (`rr_new_target_a_boundaries.json`, re-checked again in this round's
  `rr_1398_boundary_capacity_ledger.json` via a *second*, independent replay
  path — both agree).
* **Canonicalize + dedup**: 1,392 of 1,398 correctly identified as new
  relative to the 18 known boundaries; the other 6 correctly identified as
  the known long-FOUND roots' own re-discovered witnesses.
* **Capacity theorem**: applied to all 1,398, **0 survivors**.
* **Step 6 (Round 34 flow verifier)**: **never invoked**, because its
  precondition (a capacity-theorem survivor) never occurred. This is
  recorded as the correct outcome, not a skipped step: `step6_flow_
  verifier_run: false` for every one of the 1,398 in the source JSON.

Target B determination stayed entirely separate post-processing throughout
— no Target B search was performed inside any enumeration this round.

## 3. Completion-agnostic enumerator theorem (§17)

Three independent checks that the Q1 search uses **only** Q1-safe
conditions, none of which alone is treated as sufficient — all three are
run and reported together.

**(a) Static source-level allowlist.** `q1_safe_prune_reason`'s source is
scanned for every Q2-only reason name and every forbidden completion
constant (`TARGET_P`, `TARGET_O`, `TARGET_D`, `remaining_window_capacity_
prune`, `arithmetic_D_reachable`). **Zero forbidden tokens found.**

**(b) Exhaustive runtime assertion.** `q1_forbidden_prune_check` is
exercised against **all 6** Q2-only reasons (must raise) and **all 4**
Q1-safe reasons (must pass) — not a sample. **10/10 pass.**

**(c) Adversarial leakage test.** A deliberately corrupted variant of the
Q1 search — one that re-introduces the Φ<0 capacity check (the exact bound
already proved unsound for Q1) — is run on a live root (`long_q1_0`, whose
honest Q1 search finds 25 boundaries within the tested budget). Two
findings, reported together rather than only the favorable one:

* The corruption is **caught immediately and unconditionally** by the
  static/runtime check: passing the corrupted reason string to
  `q1_forbidden_prune_check` raises every time. This is the load-bearing
  defense — it does not depend on search depth, budget, or which root is
  tested.
* The **empirical** divergence check is weaker and budget-dependent: at the
  tested node budget (20,000), the corrupted prune fired 55 times but the
  found-boundary set happened to coincide exactly with the honest search's
  (25 = 25, identical sets). This is reported honestly rather than re-run
  until a difference appears — the corrupted prune's cuts, at this budget,
  only removed branches that had not yet produced additional distinct hits.
  A larger budget would very likely show a divergence (55 non-trivial
  prunes did occur), but that was not chased further, since the (a)/(b)
  checks are the actual correctness guarantee and do not depend on this
  empirical result at all.

## 4. What "certified" means here

The enumerator's Q1/Q2 separation is certified in the sense that: (1) the
prune sets are statically and dynamically guaranteed disjoint from each
other's forbidden members, verified exhaustively rather than by sampling;
(2) a live corruption attempt is caught by the same mechanism that would
catch an accidental regression. It is **not** certified in the sense of
"the Q1 search is exhaustive" — that remains open at 7 of 33 roots **by the Q1 count
unit** (roots whose Q1 search timed out); the Q2 count unit is different (5 of 33
unresolved), as
`RR_INCOMPLETE_ROOT_AUDIT.md` documents plainly.

## 5. NR6 dependency graph (§19)

**Newly established this round:**

* Q1/Q2 formally separated as predicates, with `Q2⇒Q1` proved (손증명) and
  the converse refuted by an exact counterexample family (28 roots).
* The 22 long-prefix roots have abundant Q1 Target A boundaries (1,398
  found, 26 of 28 long-excursion roots contributing) while all 1,398 fail
  Q2's capacity theorem — reconciling, not contradicting, Round 35's Q2
  closure.
* Round 35's Q2 closure **remains valid**, now independently re-derived by
  a root-level theorem requiring no enumeration.
* Round 35's (and Round 36's) treatment of Q1 as "just incomplete due to
  weak pruning" is **sharpened, not invalidated**: this round shows the
  incompleteness is intrinsic to the RR alphabet's branching (mean ≈2.5,
  no strong Q1-safe prune exists), not a fixable implementation gap — and
  additionally shows 2 of the 7 remaining `INCOMPLETE` roots are fully
  resolved for **Q2** by the envelope theorem, with no Q1 answer implied.

**Still open, unchanged by this round:**

* Q1 coverage at 7 of 33 roots (5 short-family fully open; the 2
  `long_q1_140`/`178` open for Q1 specifically, though closed for Q2).
* The known-18 Target B survivors' status (Round 34's `EXHAUSTED_NO_PATH`,
  untouched).
* CH2 chaining, T3 (exact observation 15/15), Target C, the U/J branches —
  all untouched.
* `L_6 ≥ 872` — the actual open target. Nothing in this round moves either
  bound: `L_6 ≤ 872` verified in this repository, `L_6 ≥ 867` proved.
