# Proof significance of the claimed v5 fair pilots — conditional analysis

## 0. Verification status — checked, not found

**`CLAUDE_OBSERVATION`.** No commit was cited this round. Checked anyway,
as every round: `git ls-remote origin` shows no ref beyond
`codex/round-r2-literal-source-correction` (`b09f1d5`) — unchanged since
the last independently-verified correction. **No "v5" branch, commit, or
data file exists anywhere this session can reach.** The listed figures
(439 provenance children, 326 exhausted, 113 capped, 596,537 expansions,
`short_ell4`: 3 hits, all mapping to known-18) are asserted in the
prompt, not read from any file.

**This document does not treat those figures as confirmed.** Two things
are true at once, and neither cancels the other: (a) this session's
track record on unverified figures is mixed — the "38,406 hits" claim
turned out, once genuinely pushed and independently checked, to contain
a real bug with a real, verifiable fix (`b09f1d5`); other citations in
this thread never materialized at all. Prior does not predict this case.
(b) The task asks for *proof-significance analysis*, which is a
meaningful thing to do even under a hypothesis — a mathematician can
analyze "if lemma X holds, what follows" without having proved X. **What
follows is exactly that: a conditional analysis, marked as such
throughout, not a verification.** Every section below should be read
with an implicit "if the stated figures are accurate" — stated once
here, not re-hedged in every sentence, but never forgotten. Numeric
conclusions are explicitly not promoted to confirmed facts anywhere in
this document.

If genuine v5 data lands on a reachable branch, this document's §2-4
machinery (built from already-proven material, not from the unverified
numbers) remains directly applicable without rework — only the
*specific figures* plugged into §1/§5 would need replacing.

## 1. Cross-root conclusion (conditional)

**What may be concluded, if the figures are accurate:**

- Within the *specific tested prefixes*, no genuinely new Target-A
  boundary class was found anywhere across all five short roots — every
  reported hit (1 from the independently-verified `short_ell0` result +
  3 claimed from `short_ell4`) reduces to the pre-existing known-18
  corpus.
- 326 of 439 reported provenance children reached what is described as
  *natural* exhaustion — if "natural" here means the same thing it has
  meant throughout this thread (frontier genuinely empty, not merely
  budget-capped), each of those 326 is a real, if narrow-scope, exact
  local closure.
- 113 remain capped with nonempty frontier — honest `INCOMPLETE` status,
  contributing nothing to closure.

**What may not be concluded, even if the figures are accurate:**

- That any of the five short roots is Target-A-exhausted as a *root*.
  "326 children exhausted" is not "the root is exhausted" — 113 children
  remain open, and a "provenance child" (whatever its exact granularity
  in the v5 telemetry — not independently confirmed here) is a finer
  unit than a root.
- That `short_ell1`-`short_ell3` having "no Target A in prefix" means
  those roots *have* no Target-A boundary — only that none appeared in
  the tested, finite prefix. This is exactly outcome A from this
  session's own prior cross-root framework document, and that
  document's own caution applies unchanged: absence in a bounded pilot
  is not an exhaustion certificate.
- That the "collapses to known-18" pattern continues at any depth beyond
  what was tested, or for any of the 113 still-open branches.
- Anything about Target C, `NR6`, or `L_6 ≥ 872` — untouched regardless,
  by construction (Target-A/B facts do not bear on Target C without a
  separate argument this thread has never attempted).
- Whether `short_ell1`-`short_ell3` even achieved fair R1 *admission* in
  the tested normal form, as opposed to admission followed by no R2 hit
  — the summary as given does not distinguish these, and that
  distinction matters (see §4).

## 2. Generalization candidate

**Candidate**: *every short-root Target A boundary is left-`S6`
equivalent to known-18.*

- **Exact statement**: for every root `r ∈ {short_ell0,...,short_ell4}`
  and every Target A boundary `b` reachable from `r` (within the
  Target-A-safe, corrected-recognizer search), `canonicalize(b)` is
  left-`S6`-equal to `canonicalize(b')` for some `b'` in the known-18
  corpus. This is verbatim Lemma 1 of this session's prior cross-root
  framework document — not a new formulation.
- **Evidence** (conditional): if the v5 figures are accurate, the sample
  size grows from `n=1` (the independently-verified `short_ell0` result)
  to `n=4` (adding 3 claimed `short_ell4` hits), with **zero**
  counterexamples in either case. This is the first nontrivial increase
  in evidence for the lemma since it was first stated — still a very
  small sample against an unexhausted space.
- **Missing proof step**: no structural or bijective argument exists
  connecting short-root R2-recognition geometry to known-18's specific
  finite corpus. The evidence, even taken at face value, remains purely
  empirical — four data points, not a derivation.
- **Plausible counterexample shape** (unchanged from the prior framework
  document, and *reinforced*, not weakened, by the new figures): a
  boundary reached via a longer repair/preparation chain, opening enough
  fresh orbits/hexagons to land in a canonical form outside the known-18
  set. **113 capped branches with nonempty frontier are exactly where
  such a boundary would be hiding** — they are, by definition, the
  *unexplored deeper territory* the counterexample pattern points at.
- **Finite-certificate route**: exhaustive (uncapped) Target-A search
  across all five roots. The v5 pilots, even fully verified, are **not**
  this — 113 branches capped with nonempty frontier is definitionally
  incomplete, not exhaustive.
- **Hand-proof route**: still nonexistent. Growing empirical support
  (from `n=1` to `n=4`, if accurate) does not substitute for identifying
  *why* short-root R2 geometry would be structurally confined to
  known-18's set — no such argument has been attempted, let alone
  completed.

## 3. Exhausted-child theorem candidates — mechanisms, not conclusions

**`CLAUDE_OBSERVATION`.** Per instruction, no observation below is
promoted to a theorem about *why* any specific one of the 326 reported
exhaustions occurred — that would require per-branch prune data this
session does not have, verified or not. What follows is a classification
of which *already-proven* legality mechanisms could plausibly contribute
to natural exhaustion, and — the one genuine structural point this
section can make with confidence — which of the six named candidates are
even the *right kind* of mechanism to cause whole-branch termination at
all.

**A load-bearing distinction first**: this engine's own design (three
rounds ago's finding, re-confirmed reading `evaluate_edge`) never
expands past *any* second-`R` edge — every such edge is a terminal test,
win or lose. That means two of the six candidates operate at a
*different level* than the other four:

| candidate | operates at | can it alone terminate a whole branch? |
|---|---|---|
| Component obstruction (`not_same_component`) | individual R2-candidate rejection | **no** — rejects that one R2 attempt; the frontier state may still have other (non-`R`) legal continuations untried |
| Orbit-incidence failure (`r2_wrong_source_orbit`) | individual R2-candidate rejection | **no**, same reason |
| Hub-touch restriction (`hub_touch_count_exceeded`) | edge/state-level legality | **yes, if it is the last remaining legal edge type at that state** — a proven, definitional prune (Round-independent hub-touch theorem) |
| R-budget (`rr_R_budget_exceeded`, at most two `R` events) | edge-level legality | **yes, same condition** — proven exact fact, not root-specific |
| Literal collision (`exact_permutation_collision`) | edge-level legality | **yes** — the `NR6` nonrepeat constraint itself; already the single dominant prune reason in the one independently-verified corrected run (>50% of all prunes) |
| Terminal geometry failure (`F_exceeded`/`H_positive`) | edge-level legality, monotone | **yes** — `F` is proven never-decreasing; once exceeded, permanently disqualifying |

**Conclusion of this section (an observation about taxonomy, not a
theorem about the 326)**: natural exhaustion of a frontier state
requires *every* generated edge at that state to be individually
illegal, for reasons drawn from the four state/edge-level legality
mechanisms (hub-touch, R-budget, collision, terminal geometry) — the two
recognition-level rejections (component obstruction, orbit-incidence
failure) can only ever explain why a *specific R2 attempt* failed to be
a Target-A hit, never why a branch ran out of continuations entirely.
Given collision and `F_exceeded` were already, in the one verified
dataset, the two dominant prune reasons by a wide margin, they are the
most plausible *leading candidates* for explaining most of the 326 —
stated as a plausibility ranking from already-proven mechanics, not a
claim about which one(s) actually fired.

## 4. Remaining proof burden — four distinct levels, not to be conflated

- **326 exact local closures** (conditional): each, if genuinely
  naturally exhausted (not budget-capped), is a real
  `EXACT_EXHAUSTIVE_CERTIFICATE` at the granularity of one provenance
  child — narrow in scope, but not nothing.
- **113 bounded open branches**: honest `INCOMPLETE`, contributes zero
  to closure, and is specifically where §2's plausible counterexample
  shape would have to be found if it exists.
- **Root-level admission incompleteness**: a gap the summary as given
  does not resolve — it is not stated whether `short_ell1`-`short_ell3`
  achieved fair R1 admission at all in the tested normal form, or
  whether admission happened but simply produced no R2 hit. This
  distinction is exactly outcome E of this session's prior cross-root
  framework document (*"one root has no R1 admission"* — flagged there
  as a potentially major, surprising finding if it occurred, given all
  five roots have shared an identical resource signature since Round
  36). **This document does not assume either reading** — it is recorded
  as an open clarification needed from whatever export eventually
  documents the v5 run in detail.
- **Short-five global incompleteness**: even taking every stated figure
  at face value, **all five short roots remain formally `Q1`-open** at
  the root level — none is shown exhausted, `short_ell0` alone already
  known (independently, from `b09f1d5`) to have 3 of 4 branches
  incomplete, and the aggregate 113-capped-branches figure confirms
  incompleteness is distributed, not confined to one root.

## 5. Progress reassessment — conservative, per instruction

**`CLAUDE_OBSERVATION`.** Because the underlying v5 data is unverified,
the conservative and honest move is **not to revise any numeric range**
from `RR_SHORT5_STRATEGY_CLAUDE.md` two rounds ago. What can be said is
only the *qualitative* shift the figures would imply, clearly marked
conditional:

| scope | prior range | conditional implication if v5 is accurate |
|---|---:|---|
| Unconditional `L_6 ≥ 872` proof | `~0%` | **unchanged** — nothing here bears on the unconditional claim regardless of verification status |
| RR-branch, Q1 question, short-root family specifically | "essentially just starting, 1 of 5 roots sampled" | **would shift to** "shallowly sampled across all 5 roots" — still far from exhaustive (113 of 439 children capped), and the shift itself is not adopted as a formal range revision here, only noted as the qualitative direction a confirmed result would point |
| `short_ell0` alone | `~1-10%`, likely low end | **unchanged** — nothing about `short_ell0`'s own figures changed (the `b09f1d5` result is the same one already counted) |
| known-18-collapse pattern (Lemma 1, §2) | `n=1`, no counterexample | **would become** `n=4`, no counterexample — still far too small a sample to move from `OPEN` to any stronger grade |

No range above is moved. The table's right column is explicitly a
description of *what a confirmed result would imply*, not an adopted
revision — consistent with §0's framing throughout.

## What this document does not do

- Does not confirm any of the v5 figures — no commit or file exists to
  check them against.
- Does not revise any numeric progress estimate from the prior strategy
  document.
- Does not promote any of §3's mechanism candidates to a theorem about
  which one caused any specific exhaustion.
- Does not resolve the root-admission-vs-no-R2-hit ambiguity for
  `short_ell1`-`short_ell3` — flags it as needing clarification.
- Runs no search, edits no Codex file.

CLAUDE_SHORT5_V5_ANALYSIS_READY
