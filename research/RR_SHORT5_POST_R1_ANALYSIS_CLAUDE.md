# Post-R1 analysis of the corrected `short_ell0` pilot (Claude, analyst role)

## 0. What was inspected, and how

Per this round's instruction, all four cited commits were fetched and
inspected directly, without relying on the prior (correct, at the time)
"not found" conclusion:

```
git fetch origin codex/round40-short5-r1-complete   # new branch, now present
```

All four commits are reachable on that branch:

| commit | title |
|---|---|
| `d8600b9` | Round 40 Codex: fix short-root R1 traversal completeness |
| `e9ff19c` | Round 40 Codex: retire pre-R worker and firewall v2 checkpoints |
| `5e13395` | Round 40 Codex: validate corrected short-root pilot |
| `abfcdca` | Round 40 Codex: run corrected ell0 medium continuation |

Files read (all via `git show <branch>:<path>`, no checkout, nothing
written into Codex's namespace):

- `research/RR_SHORT_ELL0_MEDIUM_RUN_CODEX.md`
- `outputs/rr_short_ell0_medium_v2.json`, `..._verified.json`
- `research/RR_SHORT5_CORRECTED_PILOT_CODEX.md`
- `outputs/rr_short5_corrected_pilot.json`, `..._verified.json`
- `research/RR_SHORT5_R1_COMPLETENESS_CORRECTION_CODEX.md`
- `outputs/rr_short5_r1_completeness_audit.json`,
  `rr_short5_worker_retirement.json`,
  `outputs/rr_short5_checkpoints/PRE_R_SCOPE_INVALIDATION.md`
- `outputs/checkpoints/rr_short5/r1_complete_v2/short_ell0_r1_seed.json`
  (364 lines — read in full; small)
- `src/search_rr_target_a_exhaustive.py` (read for the recognizer,
  `Decoration.branch`, and `evaluate_edge` logic — needed to ground every
  claim below in code, not just aggregate numbers)

**Not read:** `outputs/checkpoints/rr_short5/r1_complete_v2/short_ell0_pilot.json`
(55,310 lines, the raw frontier dump) and the final medium checkpoint it
migrated into — per instruction 5, the aggregated `rr_short5_corrected_pilot.json`
and `rr_short_ell0_medium_v2.json` already carry every per-R1-event
decoration (`r1_decorations`, `stats`) needed for this analysis; no
structural question below required frontier-state replay.

**Scope of the underlying run, stated up front:** this is a single root
(`short_ell0` only), a single `INCOMPLETE` bounded pilot (node-capped, not
exhaustion), with exactly **4 distinct R1 events** observed so far. Every
number below is scaled to that — a sample of 4, not a distribution in the
statistical sense. `short_ell1`–`short_ell4` have no corrected-run data at
all yet.

## 1. State-key grade — preserved as corrected

Per the standing correction: **the state-key sufficiency result is
exhaustive tested-universe equivalence, not a universal proof**, and that
grade is used consistently here for *both* key schemes now in play:

- `search_rr_target_a_unified.py`'s `(state.stable_key(), r_count)` (the
  scheme this analyst thread originally examined).
- `search_rr_target_a_exhaustive.py`'s richer `Decoration`-keyed scheme
  (`decorated_key = (state.stable_key(), dec.key())`, where `dec.key()`
  additionally retains `root_ell, o_star, hub_id, macro_index`, the
  ordered `r_events` tuple, `hub_touch_count`, and the first `completer`).

Codex's own `state_key_audit` (`rr_short5_corrected_pilot.json`) uses
independently-worded but equivalent language for exactly this grade:
*"lossless raw-key contract plus complete depth-2 successor-signature
regression, including enqueued R1 states"* — `99` states examined, `0`
key/signature mismatches, `34` deliberately-duplicated post-R1 groups
resolving correctly. This is the same kind of evidence this document's
correction already named: **validated against the tested universe (99
states, depth ≤2, one root's frontier), not proven for every reachable
state in the abstract.** Nothing here upgrades that grade for either
engine.

## 2. Task 1 — is CH0 a true third class, or a CH2 subtype? **Answered, from code, not guessed**

`search_rr_target_a_exhaustive.py`'s `Decoration.branch` (lines 142-152)
is the actual, executable definition in this corrected engine:

```python
@property
def branch(self) -> str:
    c = self.completer
    r1 = self.r1
    if c is None:
        return "UNDECIDED"
    if c.kind == "R" and r1 is not None and c.macro_index == r1.macro_index:
        return "CH1"
    if c.kind == "Z2" and r1 is not None and r1.macro_index < c.macro_index:
        return "CH2"
    return "OTHER_OR_UNDECIDED"
```

**`CLAUDE_OBSERVATION`, definitive:** CH2's condition is
`r1.macro_index < c.macro_index` — R1 strictly *before* the completer,
coded exactly as the originally published prose ("C is a Z2 and R1
happened earlier"). A hub completer that fires *before* R1 makes this
condition `False` by construction (`c.macro_index < r1.macro_index`
implies `r1.macro_index < c.macro_index` is `False`), regardless of the
completer's kind. **CH0, as I defined it (hub complete before R1), cannot
be a CH2 instance under this engine's actual, current definition — the
code excludes it, it does not merely fail to test for it.**

This is not a hypothetical: the pilot data contains exactly one such case
(R1 event 4, §3 below — completer at `macro_index=4`, R1 at
`macro_index=5`), and its recorded `branch` is `"OTHER_OR_UNDECIDED"`,
confirmed directly in `rr_short5_corrected_pilot.json`'s
`r1_decorations` — not `"CH2"`.

**What remains genuinely open (unresolved by this data, and correctly
so):** `OTHER_OR_UNDECIDED` is not a dedicated CH0 label — it is a
catch-all for *any* completer pattern that matches neither CH1 nor CH2
(a Z2-before-R1 completer, but also, in principle, a `Z3` or other-kind
completer regardless of order — none of which are distinguished from each
other in the current code). The one observed instance happens to be the
Z2-before-R1 pattern, but the code does not yet give that pattern its own
name. So the answer to task 1 has two parts, and they should not be
merged: **(a)** CH0 is *not* a CH2 subtype — settled, by direct inspection
of the branch logic plus one concrete matching instance; **(b)** whether
CH0 deserves its *own* dedicated label (a "true third class") as opposed
to remaining folded into the generic `OTHER_OR_UNDECIDED` bucket is an
engineering/taxonomy choice nobody has made yet in this codebase — it is
not something this data can settle, because the code does not currently
distinguish it from other, structurally different `OTHER_OR_UNDECIDED`
causes. `provisional_CH0_events: 1` in the medium-run stats is computed as
a *separate*, ad-hoc diagnostic counter, outside `Decoration.branch`
entirely (confirmed: `branch_transitions` in the same stats block only
ever records `"UNDECIDED->CH1"` and `"UNDECIDED->OTHER_OR_UNDECIDED"`,
never a `CH0`-named transition).

## 3. Tasks 2/3 — R1 target orbit and phase classification

All four R1 events observed so far, read directly from
`rr_short5_corrected_pilot.json`'s `r1_decorations` (independently
cross-verified against `rr_short5_corrected_pilot_verified.json`'s
`r1_metadata`, `verified: true`, `failures: []`):

| # | fires at (macro-index / depth) | source (orbit, phase) | target (orbit, phase) | joint | hub state at R1 | branch |
|---|---|---|---|---|---|---|
| 1 | 1 (the literal root's own first edge) | (33, 0) | **(120, 3)** | `w3:120` | untouched (0 events) | `UNDECIDED` |
| 2 | 2 | (64, 0) | **(120, 4)** | `w3:120`-family | untouched | `UNDECIDED` |
| 3 | 3 | (90, 0) | **(120, 0)** | `w3:120`-family | R1 **is** the completer | `CH1` |
| 4 | 5 | (1, 4) | **(0, 2)** | — | completed **before** R1, at index 4, via a `Z2` edge | `OTHER_OR_UNDECIDED` (CH0 pattern) |

**`CLAUDE_OBSERVATION`:** 3 of 4 R1 events target **orbit 120** — the
orbit the root's own initial `w2:10` abandonment already opened (`O=2` at
the root: hub orbit 0 and orbit 120). This matches the structural
necessity noted in the prior planning document (§3.1 of
`RR_SHORT5_POST_R1_ANALYSIS_PLAN_CLAUDE.md`): an `R`-kind edge must land
in an *already-open* orbit, and at shallow depth only orbits 0 and 120 are
open, so re-entering 120 is the only non-hub option until a `Z3` opens a
third orbit. Event 4 is the exception: it targets **orbit 0 — the hub
itself** — reached only after depth 4 (once enough `Z2`/`Z3` edges have
run for the hub to already be open, which it always is from the start,
being the root's own home orbit). **Target phases observed: {3, 4, 0, 2}
— four distinct values out of five possible (0-4), phase 1 not yet seen.**
With `n=4`, this is reported as raw observation, not a distribution claim.

## 4. Task 4 — hub completion before/after R1

Directly from the same four rows (`hub_touch_count`, `completer` fields):

| case | count (of 4 R1 events) | which events |
|---|---|---|
| hub not yet touched at R1 (pending) | 2 | events 1, 2 |
| hub completed **at** R1 (`CH1`) | 1 | event 3 |
| hub completed **before** R1 (CH0 pattern, §2) | 1 | event 4 |
| hub completed **after** R1 via a later `Z2` (`CH2`) | 0 | — |

**`CLAUDE_OBSERVATION`:** in this one root's pilot data, **no CH2 instance
has been observed at all** — every hub-completion event so far is either
simultaneous with R1 (`CH1`) or strictly precedes it (the CH0 pattern).
This is consistent with (not proof of) the geometric intuition that a
short root's hub orbit is *already open from the start* (it is the root's
own home orbit), so there is no structural reason completion must wait
until after R1, unlike the 22 long-excursion roots where the hub
constraint historically motivated the CH1/CH2 split in the first place.
`n=4` is far too small to treat this as anything beyond a single data
point per case.

## 5. Task 5 — Phi_at_R1 and M_at_R1

Read directly from `outputs/rr_short_ell0_medium_v2.json`'s `stats` (and
matching `RR_SHORT_ELL0_MEDIUM_RUN_CODEX.md`'s histogram table):

```
Phi_at_R1: {"0": 1, "1": 3}
M_at_R1:   {"-3": 1, "-5": 1, "-6": 1, "-7": 1}
```

**`CLAUDE_OBSERVATION`:** both histograms have exactly 4 entries (matching
`R1_transitions: 4`), consistent with — but this document does **not**
assert — a 1:1 correspondence to the four rows in §3; the committed JSON
does not tag which `Phi`/`M` value belongs to which specific R1 event
(source/target orbit), and reconstructing that mapping would require
replaying full state from the raw 55,310-line pilot checkpoint, which
instruction 5 says not to do unless genuinely needed. It is not needed
here: the histogram itself already answers "what values of `Phi`/`M`
occur at R1," which is what was asked. If the per-event mapping is wanted,
see §7's missing-field list.

One value is checkable without any replay: **`Phi_at_R1=0` occurs exactly
once**, and by the previously-established sawtooth identity (Phi is flat
across `rot^5` runs and drops by `(ell_run-5)` at a joint), a `Phi=0`
landing requires a rotation run strictly shorter than 5 immediately before
R1 fires. Three of the four events keep `Phi_at_R1=1` (the root's own
value, per `RR_SHORT5_FRONTIER_ANALYSIS_CLAUDE.md` §1: `Phi(short_ell0
root) = 1`), meaning those three R1 edges are themselves full `rot^5` runs
with no intervening short rotation. This is arithmetic consistent with the
reported numbers, not a new measurement.

## 6. Tasks 6/7 — R2 predecessor failure categories and recurring post-R1 dead-end motifs

From `outputs/rr_short_ell0_medium_v2.json`'s `stats.post_R1_prunes`
(100,245 post-R1 node expansions, 2,405,996 - <pre-R generated edges>
generated post-R1):

| reason | count | share of post-R1 prune total |
|---|---:|---:|
| `exact_permutation_collision` | 1,285,544 | 53.4% |
| `area_a:F_exceeded` | 925,880 | 38.5% |
| `r2_not_target` | 53,708 | 2.2% |
| `area_a:O_exceeded` | 40,428 | 1.7% |
| `decorated_memo_duplicate` | 4 | ~0% |

**`CLAUDE_OBSERVATION` — the single dominant recurring post-R1 dead-end
motif is `exact_permutation_collision`** (over half of all post-R1
prunes) — an ordinary re-visit check (the candidate landing permutation
was already visited), not specific to any R1/R2 geometry. `area_a:
F_exceeded` (Q1-safe, monotone, already audited in this repository's
`PRUNE_CLASSIFICATION`) is the second largest. **`r2_not_target`
(53,708) equals `R2_candidate_edges` (53,708) exactly** — every single R2
candidate attempted in this run failed the recognizer, consistent with
`Target_A_hits: 0`. No finer reason is available for *why* each one
failed (see §7).

**`CLAUDE_OBSERVATION` — a scope question worth flagging, not a claimed
bug:** `area_a:O_exceeded` fired 40,428 times. Reading `evaluate_edge`
(`search_rr_target_a_exhaustive.py`, around line 422), the prune reason
comes from an **unconditional** call —

```python
reason = macro.area_a_prune_reason(transition.state, macro.AREA_A)
if reason is not None:
    return f"area_a:{reason}", None, None
```

— to the same bundled `area_a_prune_reason` function this repository's
own Round 36 audit (`PRUNE_CLASSIFICATION`,
`src/search_rr_target_a_unified.py`) already classified into 4 **Q1-SAFE**
sub-reasons and 6 **Q2-ONLY** (completion-assuming) sub-reasons.
`O_exceeded` is one of the six Q2-ONLY ones in that classification
(`"target_A_requires": "nothing -- TARGET_O=25 is a full-completion
target"`), because `state.O > 25` only rules out *later reaching full
Area-A NR6 completion* — it says nothing about whether a Target A
boundary (a purely local condition: `F_def<=1`, `Ndef==2`, `H==0`,
same-component, all evaluated at the R2 edge itself) is still reachable
from that state. Round 36's whole "Part C" correction
(`search_rr_target_a_unified.py`'s own module docstring) was built around
exactly this distinction, in a *different* file
(`search_rr_target_a_unified.py`'s `q1_safe_prune_reason`, which
re-implements only the 4 Q1-safe sub-conditions for coverage-mode
searches). **`search_rr_target_a_exhaustive.py` is the *older*, Round 35
file** (its own module docstring: `"Round 35: checkpointable exact
Target-A traversal... deliberately a root-local Target-A boundary
search... not a Target-B or NR6 completion search"`) — and it calls the
full bundle unconditionally, with no Q1/Q2 mode split at all.

**What this does and does not establish:** it does not establish that
this run's `Target_A_hits: 0` result is wrong — 0 is 0 regardless of
which prunes contributed. What it *does* establish is that **the 40,428
states discarded via `O_exceeded` in this run were discarded using a
completion-scoped criterion, inside a search whose own docstring disclaims
being a completion search** — so if any of those 40,428 states (or their
descendants) could have reached a genuine Target A boundary that simply
would not go on to a full Area-A completion, this run's traversal would
never have found it, and its `INCOMPLETE`/`0 hits` status would not
reflect that. This is not asserted as a bug — it may be that Codex's
intent for `search_rr_target_a_exhaustive.py` really is Q2-scoped
(matching its historical Round 35 role, before this repository's Round 36
introduced the Q1/Q2 split in a sibling file) and the docstring's "not a
completion search" line refers to Target B/C rather than Q1/Q2 coverage.
That distinction is Codex's design decision to state, not this analyst's
to assume either way — flagged here precisely so it can be confirmed
rather than silently inherited into a "Target A is unreachable from
short roots" conclusion later. **No prune is proposed and nothing is
edited; this is an observation about an existing prune's scope, for
Codex's attention.**

## 7. Safe prune candidates — none new; one prediction confirmed

No new prune is proposed this round; the required proof-and-scope format
is honored by re-examining the one candidate already on record
(`RR_SHORT5_POST_R1_ANALYSIS_PLAN_CLAUDE.md` §4, Candidate 1) against real
telemetry rather than by inventing another.

**Candidate 1 recap (post-R1 `Ndef ≥ n_limit` ceiling):** predicted
**vacuous** for these five roots, because `Ndef` should stay pinned at
exactly 1 throughout the post-R1/pre-R2 region (root `Ndef=0`, exactly one
R event so far). **`CLAUDE_OBSERVATION` — independently confirmed by
Codex's own recognizer, not merely by absence of a counterexample:**
`target_a_recognizer`'s `conditions` dict (`search_rr_target_a_exhaustive.py`,
around line 384) requires `"Ndef_equals_2": transition.state.Ndef == 2`
for the **R2** child exactly — i.e. `Ndef(root)+1 (R1) +1 (R2) = 2`,
matching this document's own derivation (`Ndef(boundary_child) =
Ndef(current)+1` exactly, from a post-R1 state) precisely, and confirming
Candidate 1's threshold (`Ndef >= n_limit = 3`) is never approached in
this search's actual Ndef range (pinned at 1, one short of the
recognizer's required exact value of 2). The candidate remains correct
and remains not useful here — reported as confirmed-vacuous, not silently
dropped.

**Candidate 2 (same-component monotonicity) status unchanged:** still not
proposed as a prune, for the same reason as before (the sound direction —
a merge lower bound — was not established). Nothing in this round's data
changes that.

**No new prune candidate is proposed**, because none of the newly-observed
facts (the CH0 pattern, the orbit-120 concentration, the
`exact_permutation_collision` dominance) yields an argument this document
can complete a hand proof for. `exact_permutation_collision` in particular
is a basic legality check, not a structural fact about R1/R2 geometry —
there is nothing to prune further there; it is already the tightest
possible test (visited or not).

## 8. Missing fields — requested from Codex, not inferred

Per instruction 9, exact fields, not inferred:

1. **A per-candidate breakdown of `r2_not_target`** (53,708 in this run):
   `target_a_recognizer`'s own `conditions` dict already computes 7
   named booleans (`exactly_two_R_events`, `immediately_after_R2`,
   `F_def_le_1`, `Ndef_equals_2`, `H_equals_0`, `area_a_legal`,
   `same_component`) per candidate edge, but the aggregated stats collapse
   all of them into one count. A histogram of *which* condition(s) were
   `False` across all `r2_not_target` events (or at minimum, a count of
   `same_component=False` specifically, since that is the one condition
   this repository's Target A definition treats as the substantive
   geometric test, versus the others being definitional bookkeeping) would
   let this analysis characterize *why* R2 candidates fail, not just how
   many do.
2. **Per-R1-event `Phi_at_R1`/`M_at_R1` tagging** — the histogram in §5 is
   correct but anonymous; tagging each value with its originating R1
   event's `(macro_index, source_orbit, target_orbit)` (already present in
   `r1_decorations`) would let §5's arithmetic check be verified exactly
   rather than left as "consistent, not confirmed."
3. **Explicit confirmation of `search_rr_target_a_exhaustive.py`'s
   Q1/Q2 scope intent** (§6's flagged question) — a one-line statement of
   whether this engine's traversal is meant to answer the Q1 question
   (any Target A boundary) or the Q2 question (only completion-compatible
   ones), since the unconditional `area_a_prune_reason` call currently
   answers Q2 regardless of the module docstring's "not a completion
   search" framing.
4. **Runs for `short_ell1`–`short_ell4`** — all of §§2-6 above describe
   `short_ell0` only; the other four short roots have no corrected-run
   telemetry yet in this branch.

## 9. What this document does not claim

- Does not claim `short_ell0` (or any short root) is `FOUND_TARGET_A`,
  `EXHAUSTED_NO_TARGET_A`, or any status beyond the `INCOMPLETE` this
  pilot itself reports.
- Does not treat `n=4` R1 events as a statistically meaningful
  distribution — every count in §§3-4 is reported as a raw tally.
- Does not resolve whether CH0 deserves a dedicated label versus staying
  inside `OTHER_OR_UNDECIDED` — only that it is not, and structurally
  cannot be, a `CH2` instance under the code as it stands today (§2).
- Does not assert `search_rr_target_a_exhaustive.py`'s `O_exceeded` usage
  is a bug — only that it is a completion-scoped (Q2-ONLY, per this
  repository's own prior audit) condition being applied inside a search
  whose stated goal is boundary-finding, and that this is worth an
  explicit scope confirmation before trusting this run's negative result
  as Q1-complete.
- Edits no Codex file, checkpoint, or certificate; runs no search of its
  own (every number above is read, not computed by a new traversal).

CLAUDE_POST_R1_ANALYSIS_COMPLETE
