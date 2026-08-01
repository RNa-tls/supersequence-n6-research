# The productive `short_ell0` R1 branch, and what would repair the other 5,419

Analyst pass, continuing directly from `RR_SHORT_ELL0_R2_SOURCE_ORBIT_CLAUDE.md`
(commit `868beab`), over the same already-fetched data from Codex commit
`24002fd` (`codex/round43-short-ell0-taxonomy`). No new fetch was
required — the branch head is unchanged (re-confirmed:
`git log origin/codex/round43-short-ell0-taxonomy --oneline` still tops
out at `24002fd`) — and no search was run; every fact below is read from
files already on disk from the prior round's fetch.

## 0. The four R1 events are not siblings — they are alternative stopping points on one spine

**`CLAUDE_OBSERVATION`**, the single most important structural fact this
document adds beyond the prior round: reading all four R1 events'
`literal_macro_trace` fields together (not in isolation, as the prior
round reported them) shows they are **not four independent branches**
from the root. They are four alternative choices of *how many
`w2:10`-preparation edges to run before firing the R-kind `w3:120` edge*,
along a single deterministic prefix:

```
macro_index 1:  Z2  33/0 -> 120/2  (hex 64)   \
macro_index 2:  Z2  64/0 -> 120/3  (hex 90)    |  the shared preparation
macro_index 3:  Z2  90/0 -> 120/4  (hex 96)    |  spine, common to every
macro_index 4:  Z2  96/0 -> 120/0  (hex  0) *  /   event that reaches it
```

At **each** of macro-indices 1, 2, 3, and 4, the walk has (at least) two
legal choices: continue the spine with another `w2:10`, or fire `w3:120`
(an `R`-kind edge, since orbit 120 is already open) instead. The four
exported R1 events are exactly the four "fire now" choices, at
increasing spine depth:

| R1 event | fires at | spine steps taken first | R1 source | R1 target |
|---|---|---|---|---|
| event 1 | macro_index 1 | 0 | (33, 0) | (120, 3) |
| event 2 | macro_index 2 | 1 | (64, 0) | (120, 4) |
| event 3 | macro_index 3 | 2 | (90, 0) | (120, 0) |
| event 4 (**productive**) | macro_index 5 | 4 | (1, 4) | (0, 2) |

Row marked `*` above (macro_index 4, target `(120, 0)`, hex `0`) is the
**hub-completing edge** — orbit 120's phase 0 slot is identically hexagon
0 (the hub), a fixed fact about the permutation structure, not a
coincidence of which move fires there: event 3 reaches phase 0 via the
`R`-kind edge itself (hence `CH1` — the completer *is* R1), while the
spine that continues past macro_index 3 reaches the identical phase-0/
hex-0 slot via a `Z2` instead (hence event 4's `PRE_R_COMPLETER_EVENT_ORDER`
— the completer fires one step *before* R1, not as R1 itself). **Both are
the same underlying geometric coincidence — orbit 120 phase 0 is the hub
— realized by two different move choices at (almost) the same
preparation depth.**

**This reframes "productive vs. nonproductive."** Event 4 is not
"productive" because of some special property that events 1-3 lack — it
is the *deepest* of four sibling alternatives along the same spine, and
`outputs/rr_short_ell0_medium_v3.json`'s own config records
`"traversal": "deterministic-LIFO-by-reversed-label"` — a depth-first,
stack-based order. A LIFO/DFS traversal, given a large-but-finite node
budget, naturally drives arbitrarily deep down the *last*-discovered
alternative at each branch point before ever returning to explore its
earlier-discovered siblings. **Within a 100,250-expansion budget, that
mechanically explains why one branch (event 4's) accumulated 49,440 R2
candidates while the other three accumulated zero — without needing any
claim that events 1-3 are structurally worse.** This is stated as the
governing hypothesis for §5 (task 7), not as a proof that events 1-3
*would* eventually produce candidates too — only that "zero candidates
within this budget" does not, by itself, distinguish "harder" from
"scheduled later."

## 1. The productive R1 event, exactly

**`CLAUDE_OBSERVATION`**, from `rr_short_ell0_medium_v3.json`'s
`R1_events` (event id `87cbc56a565e566d`):

| field | value |
|---|---|
| fires at macro_index | 5 |
| source (orbit, phase) | (1, 4) |
| target (orbit, phase) | **(0, 2)** — the hub's own orbit, not orbit 120 |
| `ell` (rotation-run length) | **4**, not 5 (the only one of the four events with a short rotation run) |
| `Phi` before / after | 5 / **0** |
| `M` before / after | -4 / -3 |
| `P` before / after | 6 / 7 |
| `O` before / after | 2 / 2 (no fresh orbit opened anywhere in this spine) |
| hub popcount before / after | 6 / 6 (already complete before R1 fires) |
| `event_order_class` | `PRE_R_COMPLETER_EVENT_ORDER` |
| completer | `Z2`, macro_index 4, `(96,0)->(120,0)`, hex 0 |

## 2. Comparison with the three nonproductive events

**`CLAUDE_OBSERVATION`**, all fields read directly, no field estimated:

| | event 1 | event 2 | event 3 | event 4 (productive) |
|---|---|---|---|---|
| target orbit/phase | (120, 3) | (120, 4) | (120, 0) | **(0, 2)** |
| `ell` | 5 | 5 | 5 | **4** |
| hub popcount before→after | 1→1 | 1→1 | 1→2 | 6→6 |
| completer | none yet | none yet | **is R1 itself** (`CH1`) | **fires one step earlier** (`Z2`, macro_index 4) |
| `event_order_class` | `UNDECIDED` | `UNDECIDED` | `CH1` | `PRE_R_COMPLETER_EVENT_ORDER` |
| `Phi` before→after | 6→1 | 6→1 | 6→1 | **5→0** |
| `M` before→after | -8→-7 | -7→-6 | -6→-5 | -4→-3 |
| `O` before/after | 2/2 | 2/2 | 2/2 | 2/2 |
| incidence-forest effect of R1 itself | adds an edge `(orbit 120) -- hex(90)`; does not touch hub's component | adds an edge `(orbit 120) -- hex(96)`; does not touch hub's component | adds an edge `(orbit 120) -- hex(0)`, **merging orbit 120's component with the hub's component at this exact step** | orbit 120's component was **already merged with the hub's one step earlier** (by the `Z2` completer, not by R1); R1 itself adds a *different* edge, `(orbit 0) -- hex(18)`, extending the already-merged component further |

Three facts worth stating precisely, since they are easy to
overstate or understate:

- **The three "nonproductive" events are the shallow prefixes of the
  exact same spine event 4 sits at the end of** — events 1 and 2 are
  literally earlier truncations of event 4's own preparation history
  (event 4's `literal_macro_trace` steps 1-2 are byte-identical to event
  2's own trace).
- **`R`-kind edges never register their own source orbit** (§2 of the
  prior document, re-confirmed here from `extend()`: only the *target*
  orbit's phase bit is set). This applies to R1 itself, not only to R2
  candidates — event 4's own R1 source orbit (`1`) is not thereby
  registered in the forest; only its target orbit (`0`, already open)
  gains an additional phase.
- **`O` never changes across any of the four events or their shared
  preparation spine** (`O=2` throughout) — no `Z3` edge fires anywhere in
  this explored region; every edge in the spine and in all four R1
  choices is `Z2` or `R`, re-using the same two orbits opened at the
  root.

## 3. What would merge the two components, for the 5,419 mismatch candidates

**`CLAUDE_OBSERVATION`**, from `outputs/rr_short_ell0_v3_component_failures.json`
(§4 of the prior document, restated here as the basis for the causal
question this round asks): in all 5,419 cases, the R2 candidate's source
orbit sits in a small, solo component (exactly 1 E-orbit plus 1-4
hexagons), strictly disjoint from R1-target's own component (a single
fixed, larger component across all 5,419: `e_orbits: 2, hexagons: 8,
incidences: 10` in the one fully-detailed sample record read).

By the transition law (§2 of the prior document): a union between two
components happens exactly when some weight-`≥2` edge's **target
hexagon** already belongs to one component while its **own orbit**
already belongs to the other. So the required earlier event is:

> **a `Z2` or `Z3` edge, fired at a moment when the walk is standing in
> (or opening) an orbit already in the R2-source-orbit's small
> component, whose target hexagon is already registered as part of
> R1-target's larger component** (or, symmetrically, the reverse
> assignment of which orbit/hexagon belongs to which side — either
> ordering merges the same two components).

**`CLAUDE_HAND_PROOF` — it cannot be an `R` edge, and specifically cannot
be R2 itself:** this repository's own already-proven fact
(`r_count_exceeded`, restated in `RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md`'s
formal hierarchy) is that an RR word from a bare short root has **exactly
two** `R` events: R1 (already fixed, already fired) and R2 (the boundary
candidate itself, whose legality is exactly what is being tested). A
third `R` is provably excluded (`rr_R_budget`, retained/Q1-safe). The
merging event, if one exists, must therefore fire **strictly between**
the fixed R1 and the (not-yet-fired) R2 attempt, and cannot itself be an
`R` — leaving only `Z2` or `Z3` as candidates. This directly answers one
branch of task 4: **the repair event, by construction, cannot consume an
"unavailable" R — an `R` is never even a candidate for this role.** ∎

## 4. Does inserting that merging event stay legal?

**`CLAUDE_OBSERVATION` for each sub-question, task 4:**

- **Consumes an unavailable R?** No — proven in §3; the repair event is
  necessarily `Z2`/`Z3`, and the R-budget question does not arise for it.
- **Violates hub touch?** *Conditionally possible, not proven either
  way.* `RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md`'s retention table lists
  `hub_touch_count` as a **retained** (Q1-safe) prune — "more than two
  hub targets under `F≤1`" is illegal. If the specific merging edge
  chosen happens to also land on the hub hexagon a third time, it would
  be rejected on that ground. Nothing in the exported data proves every
  possible merging edge does this, nor that none do — it depends on
  which specific edge is chosen, which this data does not enumerate.
- **Destroys terminal geometry?** *Conditionally possible, not proven
  either way, and the mechanism is identifiable.* `F` only increases on
  an *abandonment* (the walk's next literal rotation, had it continued
  the old pass, would have been unvisited) — inserting any additional
  edge changes the walk's subsequent trajectory and could easily trigger
  an abandonment that would not otherwise have occurred, pushing `F`
  from 1 to 2 (`F_exceeded`, monotone, retained, immediately
  disqualifying). `H` cannot be pushed positive by any edge in the RR
  alphabet actually used here (weight ≤3 everywhere observed, and
  `dH=max(weight-3,0)=0` for weight ≤3) — so **`H` is not at risk from
  this class of insertion**, but `F` genuinely is, and this data does not
  show whether a *specific* merging edge would or would not trigger it.
- **Changes the candidate R2 source orbit?** **Yes, necessarily, and
  provably.** Inserting any additional macro edge anywhere in the walk's
  history shifts every subsequent position (rotation runs land
  differently once the preceding history has one more edge in it).
  **The 5,419 recorded candidates are candidates of the walk exactly as
  it stands; "repairing" the component mismatch does not patch those
  specific 5,419 states — it produces a materially different walk with
  its own, currently unknown, set of R2 candidates at the corresponding
  depths.** This is not a minor caveat: it means no insertion can be
  evaluated as "does this fix candidate #N" — only "does this produce a
  walk that reaches *some* Target-A boundary," a different and larger
  question.
- **Remains legal overall?** Not proven impossible, not proven
  guaranteed. Both real risks above (`hub_touch_count`,
  `F_exceeded`-via-abandonment) are named mechanisms, not hypothetical
  hand-waving, but neither is shown to be unavoidable for *every*
  possible choice of merging edge.

## 5. The theorem — not provable as stated, and not refutable either, this round

**Candidate theorem (from the assigning instruction):** *"Any event that
repairs the component mismatch necessarily destroys source-orbit
admissibility or terminal geometry."*

**`CLAUDE_OBSERVATION`: this document can prove neither the theorem nor
its negation.** §4 identifies two real, named risk mechanisms
(`hub_touch_count`, `F_exceeded`-via-abandonment) that a merging edge
*could* trigger, and a proven fact that a merging edge *necessarily*
changes the downstream R2 candidate set (§4's "changes the candidate R2
source orbit" answer) — but "changes" is not "destroys admissibility":
a different candidate can still be source-admissible, just a different
one. No argument was found — and per instruction, none is fabricated —
showing every possible `Z2`/`Z3` merging choice, at every possible
insertion point, must trigger `F_exceeded` or `hub_touch_count_exceeded`.
Equally, no witness merging edge was found (or could be, without running
a search, which this round explicitly forbids) that provably stays
legal. **The theorem is left open, honestly, rather than forced to a
verdict either direction.**

## 6. The exact minimal repair pattern (task 6)

Since the theorem is not resolved, task 6's fallback applies: the
smallest exact pattern that *could*, if it exists, evade the current
failure mode is specified precisely enough to be a real search target:

**`CLAUDE_PROPOSAL`** (a description of what to look for — not a claim
that it exists, and not something this document searches for):

| field | requirement |
|---|---|
| event type | `Z2` or `Z3` only (never `R` — proven excluded, §3) |
| source/target orbit | source orbit already a member of the R2-source-orbit's eventual small component; target hexagon already a member of R1-target's component at the moment this edge fires (either assignment of which side is "source" vs "target" merges the same pair) |
| timing relative to completer | strictly after R1 (macro_index > 5 in this lineage) and strictly before the re-attempted R2 candidate; no constraint relative to the *original* completer (macro_index 4), which already fired before R1 |
| required decoration | the walk's full component-forest state at the insertion point (to confirm the target hexagon is genuinely in R1-target's component, not merely plausible from a class-shape match) and confirmation of `F`/`H` immediately after insertion (to rule out an accidental abandonment) |
| expected Codex search predicate | **do not search for this by extending the current 100,250-node frontier.** Per §4, any insertion changes the downstream R2 candidate set entirely, so the search this predicate implies is: from the *fixed* post-R1 state at macro_index 5 (or any other post-R1 state), enumerate `Z2`/`Z3` continuations and, for each, check (a) whether it merges the R2-source-orbit's component with R1-target's component, (b) whether `F` stays `≤1` immediately after, and (c) whether `hub_touch_count` stays `≤2` immediately after — reporting the first (or all, if cheap) edges satisfying all three, rather than reporting only aggregate counts. |

## 7. The three zero-candidate branches — structural facts only, no impossibility inferred

**`CLAUDE_OBSERVATION`**, per instruction not to infer impossibility from
current depth: events 1, 2, and 3 are reported here exactly as they are —
three legitimate, legal R1 firings, each with its own target
orbit/phase, `Phi`/`M` trajectory, and (for event 3) its own immediate
hub-completion — and nothing more. §0 already gives the specific,
non-speculative reason zero R2 candidates exist for them within this
budget: **a deterministic LIFO/DFS traversal order, applied to a shared
preparation spine, mechanically exhausts the deepest alternative's
subtree first** — a scheduling fact stated directly in the run's own
config (`"traversal": "deterministic-LIFO-by-reversed-label"`), not an
inference from silence. No claim is made here about what these three
branches' subtrees *would* contain if explored to comparable depth —
only that "zero observed" and "structurally worse" are not the same
claim, and this document does not conflate them.

## Safe-prune candidates

None proposed this round, for the same reason as the prior round:
§5's theorem attempt could not be completed in either direction, and
proposing a prune on an unproven "necessarily destroys" premise would be
exactly the overclaiming this analyst role exists to avoid.

## Final response

1. **Productive R1 event identified exactly:** macro_index 5, source
   `(1,4)`, target `(0,2)`, `ell=4`, completer fired one step earlier
   (`PRE_R_COMPLETER_EVENT_ORDER`) — §1.
2. **Comparison with the three nonproductive events:** §2's table; the
   four are not independent siblings but four stopping points on one
   shared preparation spine (§0), a fact this document adds beyond the
   prior round's report.
3. **Required merging event for the 5,419 mismatches:** a `Z2`/`Z3` edge
   (never `R`, proven) bridging the two components — §3.
4. **Legality of that merge:** not consuming an unavailable R (proven);
   conditionally at risk from `hub_touch_count` and `F_exceeded`-via-
   abandonment (named, not proven unavoidable); necessarily changes the
   downstream R2 candidate set (proven) — §4.
5. **Theorem verdict:** neither proven nor refuted this round — §5.
6. **Minimal repair pattern / Codex predicate:** §6.
7. **Zero-candidate branches:** reported structurally only; the absence
   of R2 candidates is attributed to the run's own documented
   deterministic-LIFO traversal order, not to any proven structural
   difference — §7.

CLAUDE_PRODUCTIVE_R1_ANALYSIS_COMPLETE
