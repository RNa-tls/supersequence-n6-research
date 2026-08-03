# The claimed v6 top-8 endpoint audit: conditional proof-significance analysis

## 0. Verification status — read first

**`CLAUDE_OBSERVATION` — no commit, branch, or file was cited this round, and
none was found.** `git fetch origin --prune` followed by `git branch -r`
shows exactly the same four `codex/*` branches already known from prior
rounds (`codex/round-r2-literal-source-correction`,
`codex/round40-short5-r1-complete`, `codex/round43-short-ell0-taxonomy`,
`codex/round51-short5-child-outcomes`) — no new branch. `git log --all
--oneline | grep -i v6` and a repo-wide filename search for `*v6*` both
return nothing. **Every figure in the prompt (6/8 exhausted, 2/8 capped at
a 50,000-expansion cap, 167,820 additional expansions, 207,842 repair
replays, 99,438 R2 replays, 0 component merges, 0 bridge-template
occurrences, 0 literal Target A hits, 0 Target B survivors) is asserted in
the task text, not read from any file this session can reach.**

Per this session's established practice (most recently exercised two
rounds ago for the "v5" figures, which turned out to be accurate once a
real commit landed the following round), this document performs the
requested analysis **conditionally** — reasoning about what would follow
*if* the stated figures are accurate — without promoting any of them to
confirmed fact anywhere below. Every section is marked accordingly.
Section 4 (information request) and the strategy comparison in section 5
do not depend on the v6 figures being real and are given without
qualification.

## 1. Proof significance, conditional on the stated figures

**`CLAUDE_OBSERVATION` — conditional throughout.**

**Six exact branch exhaustions**: *if* "naturally exhausted" here means
the same thing it has meant throughout this project — queue empty **and**
no cap hit — then each of the six is a genuine
`EXACT_EXHAUSTIVE_CERTIFICATE` at the granularity of one `R1`-provenance
child. This is real, but narrow: it is a claim about six specific children
out of 439 in the corpus (and of the top-8 subset specifically), not about
any root, and not about the family.

**Zero bridge occurrences in 207,842 repair replays**: *if* these 207,842
replays cover the *complete* reachable space of the six now-exhausted
branches (which "naturally exhausted" would imply), then "zero bridge
occurrences" is not a sample statistic for those six branches — it is an
**exact, complete fact about them specifically**: the section-6 template
from two rounds ago's component-bridge document (a forced `Z2`/`Z3` edge
landing on a non-`hub_id` hexagon already in hub's component) was checked
against every reachable node of six full branches and found nowhere.
This is meaningfully stronger than before this round's report: previously
the template's existence was entirely unverified in either direction; if
this report is accurate, it is now falsified *specifically within these
six branches' full spaces*, though not beyond them.

**Zero literal Target A hits in 99,438 R2 replays**: *if* accurate, this
extends the "known-18 collapse, no new boundary" pattern established
across every prior round's verified data — still consistent with, not
independent confirmation beyond, that pattern.

**Two capped surviving branches**: contribute nothing to closure, by
construction (nonempty frontier, cap reached before exhaustion) — this is
true regardless of whether the rest of the report is accurate, since a
capped branch is definitionally open.

### Exact certificates vs. bounded observations

| statement | grade, conditional on the report being accurate |
|---|---|
| "these six specific children have no bridge occurrence and no Target A hit anywhere in their reachable space" | **exact fact about these six children specifically** (an `EXACT_EXHAUSTIVE_CERTIFICATE`, per-child) |
| "the bridge template never occurs anywhere in the RR short-root family" | **not supported** — 6 of 439 corpus children checked (and only 6 of this specific 8-child top-8 subset); the two capped siblings of this very subset are already an explicit counterexample to "checked everywhere" |
| "Target A does not exist anywhere in the short-root family beyond known-18" | **not supported**, same reasoning, further weakened by the two still-open branches within this same top-8 set |

## 2. Bridge conjecture reassessment

**Conjecture** (from two rounds ago): *no legal continuation from this
top-8 family can merge the `R1`-target component with the hub component
before `R2`.*

**Evidence now available, conditional**: if accurate, a comprehensive
(not sampled) check of six of the eight children's full reachable spaces,
using — it appears — exactly the template this analysis proposed two
rounds ago (the report's own "bridge-template occurrences: 0" figure
matches the section-6 template's vocabulary directly), found no
occurrence. This is the strongest evidence offered so far *for* the
conjecture, conditional on the report being real.

**Precise missing cases represented by the two capped branches**: the
conjecture's truth-value for the *entire* top-8 family depends on exactly
these two branches' still-unexplored frontiers — nothing else is
missing within this specific 8-child set if the report is accurate. These
two are, by construction, the two members of the family that most
resisted natural exhaustion (reached a 50,000-expansion cap rather than
emptying their frontier), making them the most plausible place — within
this family — for the template to eventually fire, if it fires anywhere
in this specific set at all.

**Why zero occurrences is not a proof**, even granting the report:

1. It is conditional on the report existing and being accurate at all —
   not established this round.
2. Even if accurate, "naturally exhausted" must genuinely mean
   queue-empty, not a silent relabeling of a capped state — not
   independently checked here.
3. It covers 6 of 439 total `R1`-provenance children in the wider
   corpus, and only this one top-8 subset — a vanishingly small fraction
   of the family even under the most generous reading.
4. The two branches most likely to contain a counterexample (the ones
   that resisted exhaustion the longest) are precisely the ones **not**
   covered by the zero-occurrence claim.
5. No structural argument (only an empirical count) is offered for *why*
   the template would be geometrically unrealizable — a large finite
   negative count is evidence, not a proof, exactly as a large
   negative count was never treated as proof anywhere else in this
   project.

**Strongest finite-certificate route**: complete, uncapped exhaustion of
the two remaining branches, *plus* extending the identical exhaustive
check (not a sample) across the other 431 children in the 439-child
corpus. The six exhausted branches alone, even fully certified, constitute
a finite certificate only for those six children — not for the family-wide
conjecture as stated.

**Strongest hand-proof route**: derive directly from the fixed
`HEX_POSITION`/`ORBIT_PHASE` geometry tables (not from search) whether an
`R1`-target orbit arising from this specific spine parametrization (the
branching-spine structure reconstructed two rounds ago, parametrized by
`root_ell`) can *ever*, by construction, have an unvisited phase whose
hexagon is already a member of hub's incidence component. Proving this
impossible for the whole family would be a genuine hand-proof of the
conjecture; exhibiting one constructively would refute it. Neither has
been attempted in this document or, so far as this session can verify,
anywhere else.

## 3. Six exhausted branches: common terminal mechanism

**Per the task's own instruction, no common theorem is inferred here,
because no terminal certificate data exists to support one.** No v6 file
or commit was found (section 0), so none of the six candidate mechanisms
(literal collision saturation, `F` cap, hub-touch restriction, `R`-budget,
terminal geometry loss, legal-successor exhaustion) can be attributed to
any specific one of the six claimed exhaustions this round.

The one thing available is a **carry-forward plausibility** from
already-verified prior-round data on this exact family: two rounds ago's
hand-verified dominant-prune tables for these same top-8 children showed
`exact_permutation_collision` as the single largest prune category
(77,000–79,000 occurrences per child) and `F_exceeded`/
`outside_RR_joint_model` as secondary (8,000–9,000 per child), with
`recognizer_geometry_failure` dominant among R2-specific failures. *If*
the six now-exhausted children are drawn from (or structurally similar
to) this same top-8 set, it would be unsurprising — **not confirmed** —
for collision saturation and the `F`-cap to again be the leading
candidates. This is explicitly a carried-forward plausibility from
already-verified older data, not a new finding, and not a substitute for
the terminal certificates the task asks for and that do not exist here.
**No common mechanism is asserted.**

## 4. Two capped branches: minimal information needed from Codex

This section does not depend on the v6 report's accuracy — it specifies
what would be needed to analyze the two capped branches without resuming
the (stated-to-be-unsafe) v6 checkpoints, regardless of whether the
figures above are ever confirmed.

- **Exact child IDs** of the two capped branches (which 2 of the
  original top-8 — this determines which root(s), which prior structural
  data from two rounds ago already applies).
- **Frontier structural profile**: frontier size, per-frontier-node
  depth, and per-frontier-node accepted-successor count (mirroring
  `accepted_successors` from `analyze_rr_short5_child_outcomes.py`,
  already independently verified three rounds ago).
- **Component partition** at the cap point: the full `incidence_forest`
  snapshot (component list, each with its `e_orbits`/`hexagons` sets) —
  specifically enough to identify hub's current component and its full
  hexagon membership, and `R1`-target orbit's current component.
- **Hub relation**: for every frontier node, whether any currently-legal
  edge targets a hexagon in hub's component, broken out by whether that
  hexagon equals `hub_id` specifically or some other hub-component
  hexagon (the exact distinction the section-6 template turns on).
- **Remaining legal successors**, categorized by kind (`Z2`/`Z3`/`R`
  counts) and, for each, the target orbit/phase/hexagon — enough to
  evaluate the section-6 bridge template directly against the live
  frontier without any further search.
- **Distance to bridge template**: for each frontier node, an explicit
  yes/no against the exact section-6 condition (forced, non-abandoning
  `Z2`/`Z3`, target hexagon in hub's component, target hexagon ≠
  `hub_id`) — this is the single most decision-relevant field, since it
  reduces the open question to a direct lookup rather than requiring any
  further computation on this side.
- **Provenance fields needed for continuation without resuming v6**: the
  full `literal_macro_trace` to the cap point (as used for all replay
  verification two and three rounds ago), the current `Decoration` fields
  (`r_events`, `hub_touch_count`, `completer`, `macro_index`), and the
  current `F`/`H`/`P` values — sufficient to deterministically replay
  and independently re-verify the endpoint state from scratch, exactly
  as done for `short_ell2_r1_70` three rounds ago, without touching the
  writer whose auxiliary-field preservation is flagged unsafe.

## 5. Strategy recommendation

**A. Replay-reconstruct and deepen the two capped branches** — directly
operationalizes section 4: once the frontier data above is available,
apply the section-6 bridge template as an explicit lookup against each
frontier node — no search, a deterministic classification. This is the
only option that can *directly* advance the bridge conjecture's truth
value for this specific family, because the two capped branches are, by
construction, the only unresolved cases within it (section 2).

**B. Generalize from the six exhausted branches** — low marginal
mathematical value right now. Exhausted branches, by definition, contain
neither a bridge occurrence nor a Target A hit; further characterizing
*why* they closed (task 3) would, at best, reconfirm the already-
established collision/`F`-cap pattern from two rounds ago on a
structurally identical family. It does not touch the open existential.

**C. Move to the remaining 105 capped children** (of the 113 total capped
children in the 439-child corpus, outside this top-8) — broadens the
empirical base but dilutes effort across many under-explored branches
without resolving the mechanism question for *any* of them at the same
depth already reached by the two branches in hand.

**Recommendation: A.** The two capped branches are, within this family,
the deepest-explored, hardest-to-close cases — the most information-dense
place to look next. The mathematically substantive next step is not
merely "deepen the cap" (a computation, not a proof step) but to apply
the already-derived section-6 template as a direct, deterministic
classification against their frontiers the moment section 4's data is
available. If the template fires on either branch, it constructively
refutes the conjecture (task 2) with an exact witness; if it verifiably
does not — and the frontier is small enough to argue exhaustively by hand
from the geometry tables rather than by raising the cap again — that
would be a genuine step toward the hand-proof route named in section 2,
rather than another bounded observation. Option B offers no route to
either outcome; option C offers only more of the same bounded observation
already in hand.

## What this document does not do

- Does not confirm any figure in the v6 report — no commit, branch, or
  file was found this round.
- Does not infer a common exhaustion mechanism for the six claimed
  branches — no terminal certificates exist to check, and the task's own
  instruction against inferring one without such support is followed
  literally.
- Does not claim the bridge conjecture is proved or disproved — both
  remain open, conditional on data not yet verified.
- Does not recommend raising the v6 checkpoint cap or resuming it — the
  stated writer-safety concern is taken at face value; section 4's
  request is specifically designed to avoid needing to.
- No search run, no Codex file touched.

CLAUDE_TOP8_V6_ANALYSIS_INCOMPLETE
