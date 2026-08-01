# Scope correction: the v2 `short_ell0` run is Q2-filtered, not Q1-safe

## 0. Commit verification — `d90b69a` could not be located

Before applying the correction, I checked for the cited commit the same
way as every prior round: `git ls-remote origin` (full ref listing,
independent of any local cache) and a direct GitHub `get_commit` lookup.

```
git ls-remote origin
  7dce52e...  refs/heads/main
  d4391e8...  refs/heads/claude/n6-supersequence-length-rn17wf
  abfcdca...  refs/heads/codex/round40-short5-r1-complete   <- unchanged since last check

get_commit(sha="d90b69a")  -> 422 No commit found for SHA: d90b69a
```

`codex/round40-short5-r1-complete` still tops out at `abfcdca` — the same
commit already inspected in the prior round. No new commit or branch
exists in this repository as of this writing. **This is not treated as a
reason to withhold the correction below**, for a specific reason: the
correction's substance — that `O_exceeded` is a Q2-ONLY, completion-scoped
prune reason and therefore not safe inside a Target-A-boundary-finding
search — is **not new information I would only have from `d90b69a`**. It
is exactly the concern this analyst already raised, independently, in
`RR_SHORT5_POST_R1_ANALYSIS_CLAUDE.md` §6, sourced entirely from this
repository's own pre-existing Round 36 `PRUNE_CLASSIFICATION`
(`src/search_rr_target_a_unified.py`), before `d90b69a` was ever cited.
The correction is applied on that independent basis, not on trust in an
unlocated commit. If `d90b69a` surfaces on a reachable branch later, the
"exact differential state" and "v3 prune registry split" items in §3
below remain open and should be re-checked against it directly.

## 1. What is corrected

`RR_SHORT5_POST_R1_ANALYSIS_CLAUDE.md` and
`outputs/rr_short5_post_r1_analysis_claude.json` (both already amended
in-place with a superseding notice, not deleted or rewritten) analyzed
the 100,250-node `short_ell0` v2 run
(`outputs/rr_short_ell0_medium_v2.json`, migrated from the 84-frontier
`short_ell0` v2 pilot). That run's traversal engine
(`search_rr_target_a_exhaustive.py::evaluate_edge`) calls
`macro.area_a_prune_reason` **unconditionally** — no Q1/Q2 mode split —
so every one of the six Q2-ONLY sub-reasons in this repository's own
`PRUNE_CLASSIFICATION` (`P_exceeded`, `O_exceeded`, `final_D_impossible`,
`remaining_pass_starts_exceed_remaining_windows`,
`remaining_cover_capacity_impossible`,
`insufficient_future_orbit_opening_credit`) was live throughout that run,
and `O_exceeded` is confirmed to have actually fired (40,428 times, per
that run's own `stats.post_R1_prunes`). A Q2-ONLY reason assumes the walk
continues to full Area-A completion (`TARGET_O=25` is, per
`PRUNE_CLASSIFICATION`'s own text, *"nothing -- TARGET_O=25 is a
full-completion target"*) — it says nothing about whether a **local**
Target-A boundary (F_def≤1, Ndef==2, H==0, same-component, all evaluated
at the R2 edge itself) remains reachable. Applying it as a traversal-level
prune inside a search whose own module docstring says it is *"not a
completion search"* discards states that could, for all this run's data
shows, still reach a genuine Target-A boundary.

**Consequence, applied per instruction:**

| statistic | new status |
|---|---|
| Target A frontier structure (frontier size, depth distribution, `queued_frontier_at_stop`) from the v2/medium run | `V2_Q2_FILTERED_OBSERVATION` |
| R1 target-orbit/phase distribution (the 4-event table) | `V2_Q2_FILTERED_OBSERVATION` |
| R2 failure motifs / `post_R1_prunes` histogram | `V2_Q2_FILTERED_OBSERVATION` |
| hub-completion timing tally (CH1/CH0-pattern/pending counts) | `V2_Q2_FILTERED_OBSERVATION` |
| `Phi_at_R1` / `M_at_R1` histograms | `V2_Q2_FILTERED_OBSERVATION` |
| Candidate-1 prune "confirmation" text (cited v2 recognizer behavior as corroboration) | use disallowed for prune-proposal purposes; the proof itself is code-derived and unaffected, only the illustrative run-based corroboration is retracted as evidence |

None of these are asserted to be *false* — a `V2_Q2_FILTERED_OBSERVATION`
is a real record of what the scope-tainted run actually did, useful for
debugging that run, but it is not evidence about `short_ell0`'s true
Target-A reachability, because an unknown number of states that a
Target-A-safe (Q1-only) traversal would have kept were discarded before
ever being counted.

## 2. What survives, unchanged

Exactly four things, all independent of run output — read from
`Decoration.branch`'s **source code**
(`search_rr_target_a_exhaustive.py` lines 142-152), not from any
traversal's results:

1. **`CH2` requires R1 strictly before the completer** —
   `c.kind=="Z2" and r1.macro_index < c.macro_index` is the literal,
   executable condition. This does not depend on which prunes were active
   during any particular run; it is true of every state the function is
   ever called on, tainted-run or not.
2. **A pre-R1 completer is therefore not `CH2`** — a direct logical
   corollary of (1): if the completer's `macro_index` is less than R1's,
   condition (1) is false by construction, regardless of what search
   produced that state.
3. **The `CH0` pattern remains provisional** — whether hub-complete-before-
   R1 deserves a dedicated label, or should stay inside the generic
   `OTHER_OR_UNDECIDED` bucket, was already stated as an open taxonomy
   question in the prior document and remains exactly that; nothing here
   moves it either direction.
4. **The state-key grade is exhaustive tested-universe equivalence, not a
   universal proof** — a methodological grade about what kind of evidence
   a key-collision regression test can and cannot establish; it does not
   depend on which prune reasons a given run applied, only on how many
   states were actually regression-tested.

These four are retained in `RR_SHORT5_POST_R1_ANALYSIS_CLAUDE.md` exactly
as before; only the run-derived statistics around them were downgraded.

## 3. Independent confirmation of the substantive claim (task 4)

I could not read `d90b69a` (§0), so the following is confirmed
**independently, from this repository's own pre-existing record**, not
from that commit:

- **`O_exceeded` is not Target-A-safe** — `CONFIRMED`. This repository's
  own `PRUNE_CLASSIFICATION` (`src/search_rr_target_a_unified.py`,
  written in Round 36, months before this round) already classifies
  `O_exceeded` as `Q2-ONLY` with the explicit reasoning `"identical
  argument to P_exceeded"` → `"nothing -- TARGET_O=25 is a full-completion
  target"`. This is not a new derivation; it is a citation of an
  already-established, already-tested classification
  (`Q1_SAFE_REASONS`/`Q2_ONLY_REASONS` are asserted equal to a fixed set
  by an `assert` in that same module, and `tests/test_rr_target_a_unified.py`
  exercises the split). I can confirm the *claim*; I cannot confirm
  anything about what `d90b69a` specifically says, since I cannot read it.
- **"the exact differential state"** — `NOT CONFIRMED, no access`. Without
  `d90b69a` (or the underlying diff it presumably contains), I have no way
  to state what specific state(s) the differential refers to. This is
  listed as an open item, not silently assumed.
- **"the v3 prune registry split"** — `NOT CONFIRMED, no access`. Same
  reason. §4 below prepares an analysis schema that would consume such a
  split once it exists and is reachable, but this document does not
  presume its shape beyond what `PRUNE_CLASSIFICATION`'s existing
  Q1-SAFE/Q2-ONLY split already establishes as the necessary minimum (any
  v3 registry must, at minimum, separate the four already-named Q1-SAFE
  reasons from the six already-named Q2-ONLY ones to be Target-A-safe for
  a boundary-finding traversal).

## 4. No search run

Per instruction, no search was executed to produce this correction —
every claim above is either read from already-committed files (this
repository's own `PRUNE_CLASSIFICATION`, the v2 run's own `stats`) or is
a direct logical consequence of code already read in the prior round.

See `outputs/rr_short5_v3_analysis_schema_claude.json` for the prepared
analysis schema awaiting the forthcoming v3 medium run.

CLAUDE_V3_ANALYSIS_READY
