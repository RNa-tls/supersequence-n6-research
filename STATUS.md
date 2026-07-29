# Status: n = 6 minimal superpermutation length

## The problem

A *superpermutation* on n symbols is a string containing every one of the
n! permutations of those symbols as a contiguous substring. Let L(n) be the
length of the shortest one. This repository's goal is to determine L(6).

## What is actually established (checked by code in this repo)

| n | proven minimal L(n) | source |
|---|---|---|
| 1 | 1  | `tests/test_exact_solve.py` — exhaustive search, proven in this repo |
| 2 | 3  | exhaustive search, proven in this repo |
| 3 | 9  | exhaustive search, proven in this repo |
| 4 | 33 | exhaustive search, proven in this repo (matches Ashlock & Tillotson) |
| 5 | 153 | **not** re-proven here (see below); cited from Chaffin, Diehl, Johnston, Kuperberg (2014) |
| 6 | **unknown**, in [867, 872] | see below |

`src/exact_solve.py` implements a plain IDA* search and, run with no special
tricks, proves L(1)=1, L(2)=3, L(3)=9, L(4)=33 outright (`python -m
src.exact_solve`, `tests/test_exact_solve.py`). Run against n=5 with an 8-15
million node budget it does **not** finish — which is itself informative:
even n=5 needs smarter methods than textbook brute force, and that's a
solved case. n=6 is far further out of reach; see
`experiments/n6_search_baseline.py`, which runs the same solver against
n=6 and reports, honestly, that it is inconclusive after several million
nodes.

## The n=6 gap

- **Lower bound: 867.** Proven. First given by an anonymous poster on the
  4chan `/sci/` board (September 2011); formalized and published by Robin
  Houston with Jay Pantone and Vince Vatter:
  R. Houston, "Tackling the Minimal Superpermutation Problem",
  [arXiv:1408.5108](https://arxiv.org/abs/1408.5108) (2014).
  Formula: `L(n) >= n! + (n-1)! + (n-2)! + n - 3`, implemented in
  `src/lower_bound.py::houston_lower_bound`. For n=6 this evaluates to
  720+120+24+3 = **867**.

- **Upper bound: 872.** An explicit superpermutation of length 872 is known
  to exist (found via a TSP-solver-based search, associated with Greg Egan
  and Robin Houston's 2014 work), improving on the naive recursive
  ("sum of factorials") construction's length of 873. **This repository
  does not reproduce or verify that specific 872-length string** — no such
  string was available to independently check, and fabricating one would
  be worse than not having it. `src/construct.py::greedy_construct` gives
  this repo's own, from-scratch, self-verified upper-bound witness for
  n=6: length **873** (matches the naive sum-of-factorials bound exactly;
  see `experiments/n6_search_baseline.py` output).

- **Whether L(6) = 872, or something strictly between 867 and 872, appears
  to be an open problem** in the sources available to this repository. No
  citation found here closes that gap.

## About the research summary this repository started from

A long, highly detailed "progress summary" was provided as the task
description for the session that wrote the code in `src/`, `tests/`, and
`experiments/` (frag/rotation-pass decomposition, `F`, `P`, `S`, `H`, `O`
quantities, an `L = 867 + (k+N+H)` coordinate system, claims of a completed
forest-enumeration computation with specific certificate counts, a
partially-run exact-state search with specific node/state counts, etc.).

At that point **none of it was backed by anything in this repository** —
the repo contained a single commit: a one-line README. That part of this
document is no longer current: the actual local research corpus behind
that summary was uploaded afterward and is now integrated at
[`legacy_research/`](legacy_research/README.md). It is real, substantial,
and internally disciplined about proof status (it distinguishes proved /
finite-computation-certified / experimental-only / disproved throughout,
and its own final status table already marks the headline claims as
open). See `legacy_research/README.md` for the exclusions applied
(one 696MB in-progress checkpoint, `__pycache__`, compiled `.pyc` files)
and a summary of what that corpus does and does not establish.

**Three states need to stay distinct here, and the wording below is
deliberately precise about which one each number describes:**

1. **Latest state contained in the imported repository snapshot.** The
   numbers `expanded=36,250 / accepted=114,182 / frontier=77,932 /
   terminal=142 / success=0` are the last **committed** record inside the
   uploaded ZIP (`legacy_research/outputs/F1_N0_COMMITTED_RESUME_FINAL_STATUS.md`).
   This is a snapshot of one run at one point in time, not a live value.
2. **External live search state: unknown to this repository.** The
   external Windows process that produced that snapshot may have continued
   running afterward, on a different machine this repository has no access
   to. This repository cannot see, and does not claim to know, whatever
   that process's state is *now*. Any statement of the form "the search is
   currently at X" would be a fabrication — nothing here can observe that.
3. **`N=0` exhaustive search: incomplete**, independent of (1) and (2).
   Every checkpoint captured in this corpus records `completed=false` / an
   interrupted run; no artifact anywhere in this repository shows the
   `F=1,H=0,N=0` search reaching a terminal, verified conclusion.

None of the three licenses a claim that `L_6 >= 872` (conditionally, under
`NR6`) or `L_6 = 872` (unconditionally) is proved. The imported corpus's
own status table agrees, listing both as open, and nothing added in this
repository changes that.

## What this repository actually contains now

- `src/perms.py`, `src/verify.py` — permutation utilities and a
  ground-truth superpermutation checker (the thing everything else is
  checked against).
- `src/lower_bound.py` — the published, citation-backed Houston lower
  bound formula, and the classical sum-of-factorials upper bound formula.
- `src/construct.py` — a simple, correct, self-verified greedy
  constructor (not claimed optimal).
- `src/exact_solve.py` — a plain IDA* exhaustive solver, which proves
  L(1..4) from scratch and honestly fails to resolve L(5) or L(6) within a
  bounded node budget.
- `experiments/n6_search_baseline.py` — runs the above against n=6 and
  reports the (inconclusive) result plainly.
- `tests/` — 14 passing tests (`python -m unittest discover -s tests`)
  covering all of the above, including independent verification of a
  literature-sourced n=4 witness string.
- `legacy_research/` — the actual (much larger, much further along) local
  research corpus this project had already produced, integrated as-is;
  see its own README for scope and exclusions.
- `src/analyze_j_completion.py`, `src/verify_j_normal_forms.py`,
  `src/recover_j_witnesses.py`, `src/verify_j_witnesses.py`,
  `src/search_j_afterstate.py`, `research/*.md`, `outputs/j_*.json` — an
  audit of, and now full literal recovery for, the F=1,H=0,N=2 "J"
  charge-2 joint (abandonment weight>=3 into an already-used E-orbit).
  See "J-branch findings" below.

## J-branch findings (F=1,H=0,N=2, the charge-2 joint J)

Full detail in `research/J_COMPLETION_OBSTRUCTION.md`,
`research/J_FUTURE_DEMAND_BOUND.md`, `research/J_NORMAL_FORMS.md`,
`research/J_230_WITNESS_RECOVERY.md`, `research/J_EXACT_NORMAL_FORMS.md`,
`research/J_DECISIVE_EVENT_SEARCH.md`, `research/J_BRANCH_CLOSURE_STATUS.md`,
`research/N2_BRANCH_DECOMPOSITION.md`, `research/N2_CLOSURE_STRATEGY.md`.
Summary:

- **Proved, from definitions alone (no search):** once J occurs, F is
  exhausted (=`TARGET_F`), so no further abandonment is possible for the
  rest of that walk, and at most one further `R`-type joint is possible
  before the N budget (`Ndef+H<=3`) is exceeded. Every other remaining
  joint is forced into a narrow zero-charge alphabet. This reduces
  J-branch completion to the same kind of zero-charge scheduling problem
  as the still-unsolved `N=0` branch — a genuine reduction, not a
  shortcut. A further general argument (`R_blocked_w3_existing` and
  `Z2_blocked_w2_existing` have identical effect on F/O/D/P, differing
  only in N) shows `R` is **never arithmetically required** by any of
  the 230 J states — if it's ever geometrically required, that reason
  hasn't been found.
- **All 230 recorded J states now have a recovered, independently
  verified literal witness** (previously only 1 of 230 did). Recovery
  reproduced the exact same bounded search this corpus's own
  checkpoint_header already specifies (`node_limit=20000,
  max_macro_depth=6` — not a new or larger search) and found all 230
  target hashes just before that same node limit. Independent replay
  (`src/verify_j_witnesses.py`, calling the engine directly, not reusing
  the recovery script's own bookkeeping): **230/230 pass** every check
  (hash match, per-step transition reproduction, N<2 before J, N==2 at
  and after J, exact J deltas, final F/H/N).
- **A coarse per-state normal-form fingerprint (fragment shape, current
  shape, steps-since-J) groups the 230 into 21 classes, but that quotient
  is provably lossy**: 75 pairs of states share a fingerprint yet have
  different 1-step legal-continuation shapes (minimal counterexample
  recorded in `outputs/j_exact_normal_forms.json`). No coarser-than-exact
  normal form was found that guarantees isomorphic continuation trees.
- **A bounded, capped decisive-event search across all 230 seeds** (macro
  depth <=6, edge cap 3,000 each, raw/uncanonicalized for speed) found
  zero completions (expected — completion needs ~100+ more joints) but
  did find `remaining_cover_capacity_impossible` firing on at least one
  branch for 45 of the 230 seeds — the first empirical sign of an
  obstruction beyond pure resource arithmetic, though only on some
  branches of some seeds, not a proof.
- **J completability is still open**, and the closure-status classification
  is explicitly "C: reduction insufficient so far" (not "closed", not
  "reduced to fixed families") per `research/J_BRANCH_CLOSURE_STATUS.md`.

## Capacity obstruction: a proved monotone potential (F=1,H=0 slab-wide)

Full detail in `research/J_CAPACITY_OBSTRUCTION.md`,
`research/J_CAPACITY_CORE_CERTIFICATES.md`, `research/J4_COMPONENT_ANALYSIS.md`.
Following up on the 45/230 `remaining_cover_capacity_impossible` signal
above:

- **Proved (and verified against 11,920 real transitions with zero
  exceptions):** `Phi(S) = 5 + 6*(TARGET_P - S.P) - (720 - S.visited_count)`
  is a monotone potential — `Phi(child) = Phi(parent) + (rotation_run_length
  - 5)`, so it never increases along any legal move, and going negative
  proves the rest of that walk cannot complete. This re-derives the
  engine's existing (but previously just-cited) capacity prune as a real
  theorem, not a black box.
- **Slab-wide fact, not J-specific:** `Phi` at the very start of *any*
  complete F=1,H=0 walk is exactly 6 — across all 121 joints in the whole
  slab, total tolerable rotation shortfall is at most 6. All 230 J states
  inherit an already-tiny remainder of that budget: `Phi` is in
  `{0,1,2,4,5}` for every single one of them (216 of 230 at exactly 4).
- **All 45 observed capacity failures are now fully, mechanically
  explained and independently re-verified (45/45 pass):** each is exactly
  a state with small `Phi` followed by a short rotation run (`ell` mostly
  0) that exceeds it — nothing else is needed. R usage is provably
  irrelevant to this mechanism (R and Z2 have identical effect on `Phi`).
- **Extending the same search (still bounded, depth<=6, larger edge cap)
  found the same failure in 156 of the 230 seeds**, not just the original
  45 — strong evidence (not proof) that the 45/185 split was an artifact
  of how shallow the first search was, not a real distinction between
  seeds.
- Whether *every* J state (or the whole F=1,H=0 slab) is arithmetically
  doomed this way remains a conjecture, not a theorem — proving it would
  require showing no collision-free schedule can stay within the 6-unit
  slab-wide shortfall budget, which is a geometric question this
  potential argument alone cannot answer.

## Follow-up: full boundary formalization, finite charge-word reduction, deeper search

Full detail in `research/SHORTFALL_BUDGET_THEOREM.md`, `research/ZERO_CHARGE_SKELETON.md`,
`research/J_74_SURVIVOR_CLASSIFICATION.md`, `research/FUTURE_SHORTFALL_LOWER_BOUND.md`,
`research/J_BRANCH_BUDGET_CLOSURE.md`.

- **A self-caught-and-corrected error, recorded rather than hidden:** an
  early pass in this follow-up concluded completion requires `Phi>=5`
  throughout (not just `Phi>=0`), which would have meant 229 of 230 J
  states were already arithmetically dead. That was **wrong** — it missed
  that a walk can complete via a trailing rotation-only suffix after the
  last-ever joint. The corrected, verified conclusion:
  **`Phi>=0` is already the tightest bound obtainable from pure
  (P, visited_count) counting** — it cannot be scalar-strengthened without
  genuinely new (geometric) information. Section 3 of
  `SHORTFALL_BUDGET_THEOREM.md` documents the wrong claim and its fix.
- **Finite reduction achieved:** every future "shortfall word" compatible
  with a state's budget `Phi` collapses to a small enumerable catalogue of
  charge multisets — 1, 2, 4, 12, or 19 families depending on whether
  `Phi` is 0, 1, 2, 4, or 5 (all 230 states fall in this range). Also
  clarified: `Phi` oscillates (rises during rotation, drops at each joint)
  at the literal step level and is only non-increasing at joint
  boundaries — an important precision the original theorem statement
  glossed over.
- **Deeper bounded search, not a new full Area-A search:** extending the
  same minimal-failing-path search to depth<=15 with a larger (but still
  finite, single-run, no-checkpoint) edge budget found the same capacity
  failure in **221 of the 230 J states (96%)**, up from 156. Only 9 remain
  unresolved within this bound (3 of which are the most constrained,
  `Phi=0`, single-charge-word states).
- **Important logical caveat, explicitly flagged:** finding that *some*
  branch from a seed hits `Phi<0` does **not** show that seed itself
  cannot complete — other branches (different rotation-length choices)
  might avoid the collision. This work found failing branches, not proof
  that every branch from a given seed fails. That gap is exactly why this
  is reported as a strong bounded pattern, not a closure.
- No nontrivial arithmetic lower bound stronger than `Phi>=0`, and no
  useful vector potential beyond the scalar `Phi`, were found — both
  reported as honest negative results, not forced into false theorems.

## Follow-up: attempted seed-level exact closure of the remaining 9

Full detail in `research/J_9_SEED_LEDGER.md`, `research/J_9_EXACT_CLOSURE.md`,
`research/J_230_BOUNDED_SEED_CLOSURE_STATUS.md`.

- Built a canonical-memoized exhaustive search
  (`src/search_j_9_exact.py`) plus an independent pure-rotation-suffix
  decision procedure (`src/verify_pure_rotation_suffix.py`, 5/5 boundary
  cases pass against real engine rotation mechanics) and a read-only
  certificate verifier (`src/verify_j_9_certificates.py`, 9/9 pass).
- Ran it on all 9 remaining seeds. **All 9 came back `INCOMPLETE`** (not
  `CLOSED`, not `SUCCESS`) — at a node cap of 800 canonical states per
  seed (~38s each; canonicalization's 720-relabel cost limits throughput
  to ~20 states/sec), the frontier was still growing roughly 3x with
  essentially zero canonical-state merging. That means the true reachable
  canonical state count from here is very likely in the tens of thousands
  or more — well beyond what this session can exhaustively search.
- **A more conservative correction to how the 221/230 figure above should
  be read, made explicit here:** finding that *some* branch from a seed
  fails does not prove that seed cannot complete. So, strictly, **no
  single one of the 230 J states — not even the 221 — has been proven
  unable to complete.** The 221 figure means "at least one failing branch
  found," not "closed." This is more conservative than earlier summaries
  may have implied, and is corrected here explicitly.
- `search_j_9_exact.py` supports checkpoint/resume, so a future session
  can continue with a much larger node cap without restarting.

## Follow-up: hunting for a safe state-space reduction (not more node cap)

Full detail in `research/J_STATE_SPACE_REDUCTION.md`, `research/ZERO_CHARGE_GRAPH_STRUCTURE.md`,
`research/J_DOMINANCE_RULES.md`, `research/J_TERMINAL_DEMAND_PRUNES.md`.

- **Explained the branching, precisely:** at every depth measured (0-3,
  all 9 seeds), zero canonical duplicates appeared, and every legal child
  of a state shares the exact same `visited_count` — the ~3-4x growth per
  level is genuine width from *which orbit to jump to*, not from rotation-
  length variation or redundant re-exploration.
- **Proved a general "forced-ell" lemma:** at a state with budget
  `Phi=k`, the very next rotation-run length must satisfy `ell>=5-k` (an
  immediate corollary of the already-proved monotonicity identity). For
  the 3 `Phi=0` seeds this forces `ell=5` on every remaining step. It does
  **not** reduce branching, though: the joint-target choice (which orbit)
  is untouched by this lemma, confirmed empirically (149 unique states at
  depth 3, same as without it — a 0% reduction, reported honestly rather
  than oversold).
- **Proved the state-transition graph is acyclic** (a one-line
  consequence of `visited_count` strictly increasing every legal step) —
  but this only guarantees finiteness, not narrowness, and does not
  explain or fix the branching-width problem.
- **Tested 5 candidate dominance rules against real state pairs; 2
  falsified with concrete counterexamples, 3 left undetermined** (no
  qualifying pair found in a 6,045-state pool — not claimed safe).
- **Investigated, and could not establish:** any symmetry stronger than
  the existing left-S6 canonicalization, any provably-safe way to drop
  stale visited bits, or any arithmetic lower bound tighter than the
  already-proved `Phi>=0`. All reported as honest negative results.
- **No method met the requested 50% state-space reduction bar.** This
  round's contribution is explanatory (why the branching happens) and a
  filtered-out set of naive ideas that don't work, not a working
  reduction.

## U-branch (two-charge-1-defect words) findings

Full detail in `research/U_BRANCH_ARCHITECTURE.md`,
`research/RA2_EXACT_ANALYSIS.md`, `research/A2R_IMPOSSIBILITY_STATUS.md`,
`research/RR_INTERACTION_INVARIANT.md`, `research/RA3_A3R_ASYMMETRY.md`.

The N=2, depth<=6 corpus (25,660 states) splits exactly into J-branch
(single charge-2 defect, 230 states, see above) and U-branch (two
charge-1 defects, five ordered words: RR 4,470 / RA2 24 / A2R 0 / RA3
9,952 / A3R 10,984). This round advanced the U-branch side without
touching the N=0 search/checkpoint and without any new large-scale
search — witnesses were recovered by reusing the existing J-witness
recovery checkpoint's parent chains.

- **RA2 (24 states, all recovered literally): 20/24 proved unable to
  complete** via the same Phi capacity potential already proved for
  J-branch (finite exhaustive continuation search found a concrete
  Phi<0 killer for each). The remaining 4 (all Phi=5) stayed unresolved
  even at depth<=18/edge_cap=1.5M — reported as genuinely unresolved,
  not forced closed. **Not** "RA2 fully CLOSED."
- **A2R (0 observed in the corpus): the conjectured impossibility is
  DISPROVED.** A concrete, literally-verified witness reaches word A2R
  at macro-depth exactly 6 from the initial state (raw BFS), matching
  the corpus's own recorded depth bound. Of 5 candidate explanations for
  the non-observation, 4 are refuted by this witness; the remaining one
  (an artifact of the original `node_limit=20000` canonical search's
  node budget/ordering) is the best-supported explanation by elimination,
  though not directly proved.
- **RR interaction:** over the full 4,470-record corpus (not a sample),
  every state where the two R's resolve to the same incidence-component
  (10/4,470) is also a "chaining" state (first R's target = second R's
  source) — an exact implication with zero counterexamples. The converse
  fails (65/75 chaining states still show unresolved components). The
  structural reason for the forward implication is not proved (flagged
  as conjecture).
- **RA3/A3R order asymmetry — the strongest result this round.** Proved
  (deductively, from the model's F<=1 abandonment budget and the
  definition of `fragment_hex`) a single theorem explaining, for all
  four words RA2/RA3/A3R/RR at once, exactly when a "fragment" structural
  signal can appear: it requires an earlier abandonment in the same walk,
  and F<=1 permits only one. Verified exactly against the full corpus
  (25,430 records, 8/8 slot predictions match with zero exceptions) and
  the causal mechanism itself (a hidden zero-charge abandoning joint
  firing before the second event) was confirmed by literal replay on a
  20-state RR sample (20/20 confirmed).
- None of the four literal success criteria from the originating request
  were met exactly as stated; (2) is met in reversed form (disproof
  instead of proof) and (4) is met in the spirit requested (one unified
  interaction theorem) rather than as a state-count reduction. Recorded
  honestly in `U_BRANCH_ARCHITECTURE.md` rather than claimed as full
  success.
- The section-7 "Theta" composite potential was not attempted this
  round — explicitly left as future work, not silently skipped.

## RA2's 4 remaining unresolved states, and a second RR structural lemma

Full detail in `research/RA2_FOUR_SURVIVORS.md`, `research/FRAGMENT_DEBT_LEMMA.md`,
`research/RA2_THETA_POTENTIAL.md`, `research/RA2_COMPLETION_OBSTRUCTION.md`,
`research/RR_CHAINING_PROOF_STATUS.md`.

Follow-up round targeting the 4 RA2 states left unresolved above, plus
strengthening the fragment-asymmetry theorem into a quantitative
obstruction, plus another attempt at the RR chaining proof. No new
large-scale search; N=0 untouched.

- **The 4 U4 states are proved pairwise non-isomorphic.** Their R and A2
  events are literally identical across all 4 (same source/target
  orbit+phase for both); the only difference is how many zero-charge
  joints intervene. A shallow abstracted-signature comparison suggested a
  misleading "2+2" grouping at depth 1, but depth 2 refutes it exactly --
  since the comparison uses only labeling-independent resource deltas
  (P/F/S/H/O/D/Ndef), the depth-2 mismatch is a deductive proof that no
  structure-preserving equivalence can merge them. Verdict: 4 independent
  exact states, not further reducible.
- **A proven sub-lemma:** once F=1 (the walk's one abandonment spent),
  every legal joint for the rest of the walk must be abandonment=False
  ("blocked" type only) -- a direct consequence of F<=1 and extend()'s
  abandonment formula, verified computationally (0 violations among legal
  transitions, 24/24 seeds).
- **The requested scalar "fragment debt > 0 implies incomplete" lemma is
  false and not salvageable as stated** -- it is a tautology (restates
  "this hex isn't full yet", true of every unfinished hex) rather than a
  reachability argument; documented with a minimal abstract counter-model.
  A genuine byproduct, though: among all 24 RA2 states, fragment-debt=1
  after A2 exactly identifies the 4 unresolved states (24/24, no
  exceptions) -- an exact but unexplained (conjectural) correlation.
- **Theta potential:** Phi and orbit-slack are the only candidate
  coordinates proved monotone; fragment/phase slack monotonicity was
  left genuinely unresolved (a swap mechanism could in principle break
  it; no counterexample was found in bounded search either). No usable
  RA2-specific potential beyond Phi was obtained.
- Per this round's own instruction not to widen search bounds without a
  validated >=30% reduction from a real new prune, the requested
  family-local re-search was run at the specified initial caps only (no
  new prune existed to add) and, as expected, found nothing new --
  reported honestly as 0% improvement rather than silently re-running at
  larger bounds.
- **A second, real RR lemma:** if the two R's chain (first R's target
  orbit = second R's source orbit), the second R's own component relation
  is *never* "unresolved" -- proved deductively (the source orbit is
  automatically a registered union-find node, since it equals the first
  R's own target) and verified exactly against the full 4,470-record
  corpus (75/75 chaining states resolve to same-or-different, zero
  unresolved). The originally-requested exact direction (same-component
  implies chaining) remains unproved and un-refuted -- honestly left
  open, no valid abstract counter-model constructed either (it would
  require replicating the real S6 E-orbit/hexagon combinatorics).
- None of this round's four success criteria (U4 fully closed; U4 reduced
  to few subcases; fragment-debt/Theta proof; RR chaining proof) were met
  in their literal form. Two genuine proven lemmas came out of the
  attempts anyway (post-F1 blocked-only; chaining-implies-resolved) and
  are recorded as real, if partial, progress.

## RA2's zero-charge history: a clean closed-form identity, and the fragment-debt obstruction hypothesis is refuted

Full detail in `research/RA2_ZERO_CHARGE_HISTORY.md`,
`research/FRAGMENT_REPAIR_OBLIGATION.md`, `research/RA2_REPAIR_COST_LEMMA.md`,
`research/RA2_U4_CAUSAL_DIFFERENCE.md`.

Third follow-up round on RA2's 4 unresolved states, targeting a
quantitative completion obstruction from the zero-charge history between
R and A2. No new large-scale search; N=0 untouched.

- **Main result, a genuine theorem:** `Phi(state right after A2) = 1 +
  ell_A2 = 6 - fragment_debt`, exactly, verified over all 24 RA2
  witnesses with zero exceptions. Proof: while F=0, `f1_normal_form`
  forces the current hex to be a single contiguous arc, so its rotation
  successor is always unvisited until the arc reaches full length --
  meaning any abandonment=False ("blocked") joint can only fire once its
  own hex is already FULL. Consequently every joint before A2 (R itself
  and every intervening zero-charge joint) is forced to use the maximal
  rotation length (ell=5), leaving zero residual debt; only A2 itself
  (which requires abandonment=True) can leave a hex incomplete. The
  elaborate zero-charge word structure turns out to be causally
  irrelevant to the eventual fragment debt -- only A2's own preceding
  rotation length matters. This is an exact zero-charge-history invariant
  separating U4 (ell_A2=4) from C20 (ell_A2 in {0,1,3,5}), with zero
  exceptions among all 24.
- **The fragment-debt-as-obstruction hypothesis is refuted, not
  confirmed.** A bounded repair-cone search found 11-15 legal repair
  witnesses per U4 state (within a 20,000-node cap), the shallowest
  costing exactly 0 Phi and 0 orbit slack -- fragment repair is cheap and
  plentiful, not a bottleneck. Of the requested repair-cost lemma
  candidates: R1 (a targeted joint is required) is trivially proved; R2
  (repair costs at least 1 unit of slack) and R3 (repair cost exceeds
  budget) are both refuted with concrete zero-cost witnesses; R4 (orbit
  reuse conflicts with other demand) is left untested since no completion
  witness of this slab exists anywhere to check against.
- The requested combined invariant Omega collapses: Phi and fragment
  debt are the same information (per the identity above), so Omega's
  four components reduce to effectively two (Phi, orbit slack) plus a
  repair-accessibility term that turns out not to be scarce for U4 either.
- **Minimal counterfactual edit found:** replaying the same A2 move at
  every rotation length ell=0..5 immediately before it shows debt =
  5,4,3,(illegal),1,(not-A2) purely as a function of ell -- U4's debt=1
  and a typical C20's debt=4 differ by exactly one rotation step, not by
  any orbit-target choice (only one legal A2-type move existed at that
  point in the tested case).
- An attempted unification with the RR "chaining implies resolved" lemma
  from the previous round was tried and explicitly declined: both share
  a "most of the intervening history is irrelevant" theme, but rest on
  different mechanisms (orbit-hexagon union-find registration vs.
  hexagon-arc rotation mechanics) -- no forced merge.
- Of this round's four success criteria, none were met in their literal
  form (U4 not proved impossible; repair cost does NOT exceed budget --
  the opposite was shown), but criterion 3 (an exact invariant separating
  U4 from C20) was met via the ell_A2/Phi identity, and criterion 4 (few
  exact subcases) is satisfied in the sense that U4 reduces to the single
  parameter value ell_A2=4.

## ell_A2=4 geometry: A2R-like non-observation resolved, and an A2/A3 common theorem

Full detail in `research/A2_ROTATION_LENGTH_CLASSIFICATION.md`,
`research/RA2_ELL4_BOUNDARY_GEOMETRY.md`, `research/RA2_ONE_HOLE_LEMMA.md`,
`research/RA2_TERMINAL_COMPATIBILITY.md`.

Fourth follow-up round on RA2, moving past the fragment-debt line
(refuted last round) to directly classify the A2 rotation-length
spectrum and the exact post-A2 geometry it produces. No new large-scale
search; N=0 untouched.

- **ell_A2=2, unobserved in the 24-state corpus, is NOT structurally
  impossible.** A genuinely exhaustive raw BFS at depth<=6 (frontier
  fully exhausted at 12,367 nodes, well under any cap) confirms it is
  absent within the corpus's own recorded bound -- but a concrete witness
  was found at depth 7, one step beyond that bound. Same pattern as the
  earlier A2R non-observation: a depth-6 search-boundary artifact, not an
  impossibility. ell_A2=5 remains proved structurally impossible (the
  full-hex argument).
- **A controlled counterfactual** (same R-to-A2 prefix, same A2 move,
  only the rotation length before it varied) shows U4's ell_A2=4 differs
  from ell=0,1,2 not only in Phi, but also in an independent geometric
  fact: at ell=4 the move happens to land in an ALREADY-visited orbit
  (new_orbit=False), while at ell=0,1,2 the same move lands in a fresh
  orbit (new_orbit=True) -- a genuine additional distinguishing fact, not
  reducible to the Phi/debt identity alone. Whether this, or just Phi
  being high, explains why capacity-failure search finds violations for
  ell=0,1,2 but not ell=4 remains open (the two co-occur, not separated).
- Of the four "one-hole geometry" candidates: H1 (repair breaks
  terminal-compatibility) is refuted -- repair witnesses pass every known
  necessary condition; H2 (repair forces reuse of an existing E-orbit) is
  proved true (4/4 shortest repair witnesses use new_orbit=False); H3
  (holding the hole traps future moves in one phase class) is refuted;
  H4 ("incidence parity") is left unresolved for lack of a precise
  definition of the term in this codebase.
- **A2/A3 common theorem, confirmed:** the F=0 full-sweep argument behind
  Phi=1+ell=6-debt never used the abandoning move's weight, so it applies
  identically to A3. Verified directly against 60 A3R witnesses: 60/60
  match the identity exactly, and all pre-abandonment joints use ell=5.
  A3R's ell_A3 distribution (sample of 100) covers all five values
  {0,1,2,3,4}, independently confirming ell=2's absence in RA2 was a
  small-sample artifact, not a structural gap.
- Of this round's four success criteria: (1) ell_A2=2's status is fully
  resolved (not impossible, depth-7 witness); (4) the A2/A3 common
  theorem is established with deductive proof plus computational
  confirmation. (2) and (3) were only partially advanced -- no full
  boundary-only obstruction was proved, and U4 reduces to one shared
  parameter value (ell_A2=4) but not a further geometric subclassification
  beyond that, since the 4 states' finer geometry is individually
  distinct (consistent with their proven pairwise independence).

## Abandonment target novelty: (ell, nu) is not a free 2D space, and every obstruction candidate this round was non-binding

Full detail in `research/ABANDONMENT_TARGET_NOVELTY.md`,
`research/RA2_ORBIT_REUSE_CHARGE.md`, `research/EXISTING_TARGET_ABANDONMENT_OBLIGATION.md`,
`research/RA2_ORBIT_DEMAND_MATCHING.md`.

Fifth follow-up round on RA2, examining whether the rotation length
(ell_A) and target-orbit novelty (nu_A: existing vs. fresh) jointly
determine a completion obstruction for U4. No new large-scale search;
N=0 untouched.

- **Central re-derivation:** (ell_A, nu_A) is not an independent 2D
  space. This project's own established joint taxonomy already fixes
  nu_A by which named event you're looking at -- "A2" is DEFINED as
  (weight=2, abandonment, new_orbit=False) and "A3" as (weight=3,
  abandonment, new_orbit=True); the other two weight/novelty
  combinations are different joint kinds entirely (Z2abandon,
  zero-charge; J, the charge-2 J-branch event, a disjoint corpus).
  Re-extracted and confirmed over 622 real abandonment events (RA2's 24,
  a 300-state RA3 sample, a 298-state A3R sample): every existing-target
  (nu=0) event is from RA2 (24/24), every RA3/A3R event is fresh-target
  (598/598). This decomposes the "2D truth table" into two already
  largely-understood 1D spectra (ell_A2, ell_A3) rather than a genuine
  2x2 combinatorial space.
- Direct computation shows U4 never actually faced an existing-vs-fresh
  *choice*: at every rotation length tested, at most one legal weight-2
  abandoning move existed, and its novelty was fully determined by that
  length -- there was no alternative to forgo. A local and a global
  version of the requested "orbit-reuse charge" rho_A were both
  evaluated and found non-binding (global orbit-opening slack is 92-93,
  nowhere near tight).
- H2 (repair reuses an existing orbit, proved last round) resisted every
  strengthening attempt: H2a (reuses A2's own target orbit) and H2c
  (repair costs exactly 1 unit of orbit slack) are refuted with concrete
  counterexamples; H2b (reuses A2's own source component) is refuted
  because that component isn't even registered at that point; H2d is
  left unresolved.
- A minimal Hall-type check (fragment hole as the sole demand, its found
  repair witnesses as supply) trivially holds -- no violating subset
  found, though a full bipartite model over all remaining completion
  demand was explicitly out of scope (would amount to the full
  completion search).
- Of this round's five success criteria, only (1) (a complete local
  truth table for (ell_A, nu_A)) was achieved -- and in a form that
  corrects the round's own premise rather than confirming it. Criteria
  (2), (3), (4), (5) were all attempted and came back non-binding or
  refuted; the round's honest conclusion is that existing-target
  novelty, as an axis, is not a further source of leverage on U4 beyond
  what the ell_A2 spectrum already gives -- closing U4 will need a
  different kind of argument than local rotation-length/orbit-novelty
  geometry.

## RA2 <-> A2R defect-order exchange: a proven adjacent-exchange theorem, a sharp A2R minimum-depth result, but no new leverage on U4

Full detail in `research/RA2_A2R_EXCHANGE_THEOREM.md`, `research/A2R_MINIMUM_DEPTH.md`,
`research/U4_EXCHANGE_OBSTRUCTION.md`, `research/U_BRANCH_DEFECT_ORDER_INVARIANT.md`.

Sixth follow-up round, moving from RA2's local post-A2 geometry to the
defect-order exchange structure between RA2 (R then A2) and A2R (A2 then
R). No new large-scale search; N=0 untouched.

- **Adjacent-exchange theorem, proved:** for all 10 RA2 witnesses where R
  and A2 are macro-adjacent (no zero-charge joint between them), swapping
  A2 before R is impossible for a single, general, structural reason: R's
  own pre-boundary hex is always forced to be fully swept (the F=0
  full-sweep theorem from an earlier round), so no further rotation is
  possible from that exact point -- any nonzero ell_A2 collides
  immediately. Verified 10/10; the analogous bubble-sort generalization
  to the full zero-charge word was attempted and refuted by a
  counterexample (a later joint in the word is often preceded by a
  freshly-restarted hex, not a full one, so the same obstruction does not
  automatically propagate).
- **A2R's minimum depth, pinned down exactly:** depth 6, with a UNIQUE
  canonical witness at that depth (exhaustive raw BFS, frontier fully
  consumed at 2,853 nodes). Explained quantitatively: A3 is legal as the
  walk's literal first move (3 legal options from the true initial
  state), R requires only that its own starting hex be fully swept
  (still the walk's first macro-edge), but A2 requires at least 4 prior
  joints (minimum depth 5) before any existing-target weight-2
  abandoning move becomes available -- confirmed by direct enumeration
  (0 legal existing-target weight-2 moves from the initial state).
- **U4 turned out to be outside this round's classification entirely:**
  all 4 U4 states have a nonzero zero-charge word between R and A2, so
  the proved adjacent-exchange theorem doesn't apply to them, and the
  exchange-distance measure chi (A2R's global minimum depth minus how
  deep each RA2 witness itself reaches A2) does not separate U4 from
  C20 -- both span the same {0,1} range.
- A new defect-order invariant emerged as a byproduct: the minimum
  macro-index at which each event type can first appear (A3: 0, R: 0 but
  gated by a full sweep, A2: 4) -- this offers a plausible (though
  unverified quantitatively) explanation for why RA3/A3R's corpora are
  ~400x larger than RA2's within the same depth<=6 bound.
- Of this round's five success criteria: (1) the adjacent R/A2 diamond
  lemma and (2) A2R's exact minimum-depth theorem were both achieved
  with genuine proofs. (3) (an exchange obstruction separating U4) and
  (5) (a general RA3/A3R exchange theorem) were not achieved -- reported
  honestly as another round where U4 itself resisted the specific new
  angle tried, even though the angle produced real theorems elsewhere.

## R-to-A2 word restart-block decomposition: a new exact U4 signature, and a generalized barrier lemma

Full detail in `research/U_BRANCH_RESTART_BLOCKS.md`, `research/A2_PREREQUISITE_DAG.md`,
`research/RA2_RESTART_BARRIER.md`, `research/U4_RESTART_ANCESTRY.md`,
`research/U_EVENT_FIRST_INDEX_THEOREM.md`.

Seventh follow-up round, decomposing the zero-charge word between R and
A2 into "restart blocks" to look for long-range prerequisite structure.
No new large-scale search; N=0 untouched.

- **Proved (deductive + exhaustive verification over all 107 relevant
  joints):** every joint before A2 fires (R itself and all intervening
  zero-charge joints) must target a completely FRESH hexagon (0 bits
  visited) -- f1_normal_form's F=0 single-partial-hex constraint rules
  out any other option. So at the hex level the requested 6-way restart
  classification collapses to a single case; the real per-block variation
  is at the orbit/component level.
- **A new, exact U4 signature found:** decomposing each RA2 witness into
  R + word-blocks + A2, the 11 witnesses with exactly one intervening
  block split perfectly along group lines -- all 9 C20 cases reuse R's
  own target orbit literally (component "same"); both U4 cases instead
  open a completely unrelated fresh orbit (component "unresolved"). The
  2 two-block U4 states contain exactly the C20 pattern as an optional
  first block, plus this same critical fresh-orbit block appended before
  A2. All 4 U4 states share this exact critical-restart signature with
  zero exceptions -- but it is necessary, not sufficient, for U4
  membership (one C20 outlier shares it too, differing only in the
  already-known ell_A2).
- **Restart-barrier lemma B1, proved and verified over all 107 full-swept
  block boundaries in the corpus (not just R's):** after any block that
  ends in a fully-swept hex, no nonzero-length rotation is possible from
  that exact boundary, generalizing last round's adjacent-exchange
  finding beyond the R-specific case.
- **Completed the event-first-index table** for all 7 joint kinds:
  A3/Z2abandon/R/Z2/Z3 all have minimum first-appearance index 0-1;
  A2 alone requires index 4; J (the other existing-target abandonment)
  needs only index 1 -- isolating "weight-2 existing-target" as the
  specific hard combination. Confirmed the arithmetic identity
  d_min(A2R) = i_min(A2) + 2 = 6 exactly.
- Of this round's four success criteria: (2) the barrier lemma
  generalization and (3) an exact restart-block invariant for U4 were
  both achieved (with the necessary-not-sufficient caveat stated
  honestly). (1) the full prerequisite-DAG proof of why i_min(A2)=4
  exactly stayed qualitative, not fully deductive. (4) RA3/A3R
  application produced a plausible explanation for corpus-size asymmetry
  but not a proven general theorem.

## Five-state focused comparison: a corpus-exact classifier, a methodological correction, and ell_A2 confirmed forced not chosen

Full detail in `research/RA2_FIVE_STATE_COMPARISON.md`, `research/RA2_CRITICAL_RESTART_CLASSIFIER.md`,
`research/RA2_CRITICAL_RESTART_ANCESTRY.md`, `research/A2_PREREQUISITE_DAG_PROOF.md`.

Eighth follow-up round, narrowing to exactly 5 states (U4's 4 plus the
one C20 outlier sharing U4's critical-restart signature) for a tight
comparison. No new large-scale search; N=0 untouched.

- **Methodological correction, found and fixed:** the prior round's
  per-block "component_relation" computed a block's "source" from the
  position *before* that block's own rotation run -- but canonicalize()
  resets the walk's literal position to the identity after every
  macro-edge, so that "source" was always orbit 0 regardless of which
  block was examined, a canonicalization artifact rather than genuine
  per-block information. Switched to a direct, unambiguous comparison
  (literal target-orbit index vs R's own target-orbit index) and
  reconfirmed the prior finding survives intact under the corrected
  definition.
- **Corpus-exact classifier achieved:** "critical-restart target orbit
  differs from R's own target orbit" AND "ell_A2=4" correctly classifies
  all 24 RA2 states (4 true positives, 0 false positives, 20 true
  negatives, 0 false negatives) -- though flagged honestly that ell_A2=4
  alone already fully determines this on its own; the restart-signature
  term adds no extra discriminating power within this corpus.
- **The critical restart is LITERALLY identical (same source, target
  orbit, phase) across all 4 U4 states and the C20 outlier** -- the only
  field that ever differs among these 5 states is ell_A2 itself (4 for
  U4, 0 for the outlier).
- **Proved ell_A2 is forced, not a free/lucky choice:** enumerating
  every rotation length 0-5 at the post-critical-restart boundary for
  all 5 states shows exactly one legal A2 option per state, and its
  length is fixed by the state (U4: only ell=4 works; outlier: only
  ell=0). Since the critical restart itself is identical, the forcing
  factor is the *accumulated* orbit-touching history from the blocks
  preceding it (the outlier passes through 3 extra preparation blocks
  U4's states skip), not the critical restart in isolation.
- A depth<=6 continuation-tree comparison across the same 5 states found
  zero capacity-failure prunes for any U4 state, versus 4 total for the
  outlier starting at depth 4 -- confirmed the already-known Phi gap
  under this tighter control, framed as a bounded "escape-transition"
  observation rather than a new independent mechanism.
- Ancestry theorem candidates C1-C4 were tested directly: C1 refuted
  with a concrete counterexample; C2/C3 left undefined for lack of a
  precise formalization; C4 true but a restatement of the already-known
  Phi/debt identity.
- A new, sharp asymmetry surfaced in the RA3/A3R ledger (sampled, no new
  search): A3R shows exactly 0/150 cases where the critical restart
  before R reuses A3's own target orbit, versus RA3's mixed 38/150 --
  reported as an observation/conjecture, not connected to a proven
  general theorem.
- The three-round-running open problem (a full deductive prerequisite-DAG
  proof for why i_min(A2)=4 exactly) remains unresolved; recorded
  honestly as still incomplete rather than forced.

## A2 legality predicate, minimal sufficient statistic, and an exact U4/outlier causal certificate

Full detail in `research/A2_LEGALITY_PREDICATE.md`, `research/A2_ELL_FORCING_HISTORY.md`,
`research/A2_MINIMUM_INDEX_PROOF.md`, `research/U4_HISTORY_CAUSAL_CERTIFICATES.md`,
`research/RA3_A3R_ORBIT_HISTORY_ASYMMETRY.md`.

Ninth follow-up round, formalizing exactly why a given rotation length
becomes the unique legal choice for A2. No new large-scale search; N=0
untouched. Two real bugs were found and fixed mid-round (see below).

- **Key simplifying fact:** this entire model has exactly ONE weight-2
  move (`w2:10`) -- explaining why every earlier round observed "at most
  one legal weight-2 abandoning move" at any boundary: there was never a
  second candidate to begin with.
- **Two bugs found and fixed while building the per-ell candidate
  table:** an initial version assumed A2 was always the last macro-edge
  in a witness's path (false -- some witnesses have trailing zero-charge
  joints after A2), and after fixing that, a second version returned the
  state already offset by that witness's own ell_A2 rotations rather
  than the true fresh-landing origin. Both were caught by cross-checking
  against the corpus's own recorded ell_A2 values and fixed; the
  corrected candidate table now reproduces the known ell_A2 exactly for
  all 24 RA2 states, with exactly one legal ell per state (matches prior
  rounds' 5-state finding, now confirmed corpus-wide).
- **Exact minimal sufficient statistic obtained and verified:** H_A2(S)
  = (S.p, plus for each ell=0..5 whether the single candidate target is
  visited and whether its orbit is pre-existing) provably determines A2
  legality by construction, and this was checked against real data
  (grouping the 24 witnesses by this statistic exactly separates them
  into consistent legal-vector classes).
- **Exact causal certificate for U4 vs the C20 outlier:** all 4 U4
  states share a literally identical 6-candidate table (same orbit
  sequence at every ell). The entire difference from the outlier is
  that orbit 1 is pre-touched in U4's accumulated history (making ell=4
  the unique legal choice) but not the outlier's, while orbit 120 is
  pre-touched in the outlier's history (making ell=0 its unique legal
  choice) but not U4's -- the two most literal, verifiable facts
  separating them.
- The three-round-running open problem (a deductive, BFS-independent
  lower-bound proof for i_min(A2)=4) remains unresolved for a fourth
  round -- reported honestly; the exhaustive-search-based proof stays
  solid (re-verified, frontier fully consumed).
- A new sharp fact confirmed over the FULL stored ledger (not a sample):
  A3R shows exactly 0/298 cases of the critical restart before R reusing
  A3's own target orbit, versus RA3's 75/300 -- reported as an exact
  corpus observation, explicitly not claimed as proven impossible (this
  project's repeated "non-observation is not impossibility" lesson from
  A2R and ell_A2=2 applies here too).

## Tenth follow-up round: unique weight-2 move proof, H_A2 necessity, and an A3R falsification

Tenth follow-up round. Explicitly told not to repeat the i_min(A2)=4
direct-proof attempt again; redirected toward (a) a genuine
group-theoretic proof of why there is exactly one weight-2 move, and
(b) the two-orbit occupancy structure behind A2 legality and U4. No new
large-scale search; N=0 untouched.

- **Genuinely proved (not enumerated) that `tail_permutations(2)` has
  exactly one element for ANY width-2 tail** (general fact, not
  n=6-specific): from the `is_indecomposable` definition, w=2 only
  checks one prefix condition (`pi(0)=0`), which exactly one of the two
  length-2 permutations violates. Also derived and verified (11 sampled
  p0 values) the closed form `target(ell) = compose(p0, Sigma^ell *
  action)` -- the six A2 candidates are p0 composed with 6 FIXED,
  p0-independent group elements. `research/UNIQUE_WEIGHT2_MOVE_THEOREM.md`.
- **H_A2 sufficiency proved by construction; necessity only 1/3
  confirmed by exact witness:** the `existing`-bit's necessity has a
  real witness pair (U4 vs the C20 outlier, identical `visited` status,
  differing `existing` status, differing legality); the `visited`-bit
  and `S.p` component necessity remain deductive-only, no exact witness
  pair found this round. `research/A2_MINIMAL_SUFFICIENT_HISTORY.md`.
- **Orbit 1 / orbit 120 given coordinate-invariant names:** orbit 120 is
  literally the E-orbit of the unique weight-2 action itself (its
  canonical rep equals SIGMA); orbit 1 is the ell=4 candidate's own
  fixed group element, sharing exactly one hexagon (hex 0) with orbit
  120. The two-bit table across all 24 RA2 witnesses shows
  `(existing(ell=4 cand)=T, existing(ell=0 cand)=F)` exactly
  characterizes U4 (4/4) and the reverse exactly characterizes the
  outlier (1/1) -- but the 4th combination `(T,T)` is unobserved (0/24)
  and `(F,F)` doesn't uniquely determine the legal ell by itself, so
  this stays a corpus exact observation, not a general theorem.
  `research/A2_TWO_ORBIT_CAUSAL_THEOREM.md`.
- **Unexpected structural finding:** replaying all 5 focus witnesses
  (U4 x4 + outlier) in a fixed, never-canonicalized frame shows NEITHER
  candidate orbit ever "opens" during the tracked pre-A2 history -- one
  of the two bits is already true from the word's absolute start
  (literally equal to orbit 0, the E-orbit of the starting identity
  permutation itself) and the other stays false the entire time. The
  requested opening-history counterfactual analysis doesn't apply to
  this corpus for that reason; the occupancy automaton built from these
  5 exact traces is consequently degenerate (zero transitions), so it
  cannot be promoted to an i_min(A2)=4 lower bound (would require the
  full state-space search this round was told not to repeat).
  `research/A2_OCCUPANCY_AUTOMATON.md`, `research/U4_ORBIT_HISTORY_CONFLICT.md`.
- A bounded post-A2 depth<=3 tree comparison (all 5 focus witnesses,
  frontier fully consumed) found no controlled way to test "same history
  delays capacity failure" (U4 and the outlier fire A2 at different ell,
  so it's cross-sectional, not controlled) -- reported inconclusive
  rather than confirmed. Of the four candidate U4-closure obstructions
  (O1-O4), only O1 was clearly refuted by this round's data; O2-O4
  stayed undecided for lack of evidence.
- **A3R reuse-impossibility hypothesis falsified:** a small bounded
  (depth=1, one `macro_edges()` call per state) search over the FULL
  298-witness A3R corpus found that a legal, unpruned R-kind joint
  reusing A3's own just-opened target orbit exists at depth 1 for
  298/298 witnesses. This means the earlier round's "0/298 no reuse"
  fact was about which specific path each stored witness's own recorded
  macro_path happens to take, not a structural endpoint/phase
  impossibility -- immediate reuse is trivially reachable everywhere it
  was checked. `research/A3R_TARGET_REUSE_STATUS.md`.
- The i_min(A2)=4 direct-proof attempt was NOT repeated this round, per
  explicit instruction; its status is unchanged from the ninth round
  (exhaustive-search-verified, not deductively proven).

## Eleventh follow-up round: RR same-component vs chaining, full 4,470-witness literal recovery

Eleventh follow-up round. Moved from the A2/U4 local-history axis (closed
out for this round per explicit instruction) to RR's open "two R events in
the same incidence component implies chaining" question. No new
large-scale search; N=0 untouched. Reused the existing depth<=6,
node_limit=20,000 J-witness recovery search (same bound as prior rounds)
to literally recover the FULL 4,470-witness RR corpus for the first time
in this session (previously only a 300-witness sample was available).

- **Full literal recovery**: all 4,470 RR witnesses (not a sample) now
  have complete macro_path replays in `outputs/rr_literal_witnesses.json`
  (12MB). This let every claim below be checked by independent literal
  replay, not just by cross-referencing the corpus's own precomputed
  fields.
- **same-component (R2's own source/target orbit roots equal) implies
  chaining (R1's target orbit == R2's source orbit): re-confirmed over
  the full 4,470, zero counterexamples, verified by two independent
  scripts** (`analyze_rr_chaining.py`'s own aggregation and
  `verify_rr_chaining_theorem.py`'s separate re-derivation from the raw
  per-witness rows).
- **New mechanism found and exhaustively verified (75/75, the full
  chaining subset): within the chaining witnesses, R2's own
  component_relation is "same" if and only if hex 0 -- the hexagon
  containing the WORD'S OWN STARTING PERMUTATION, uniquely registered
  from `initial_state()` itself -- was touched by some event before R2
  fires.** The sufficiency direction is fully deductive (plain
  union-find semantics once hex 0's special pre-registration is
  granted); the necessity direction is exhaustively verified over the
  full corpus but not proved as a fully general law.
- **Incidence forest property re-confirmed exhaustively**: across every
  pre-joint and post-joint state in all 4,470 RR witnesses (53,054 state
  checks) plus a broader 85,238-state depth<=6 sample, zero
  redundant/cycle-closing union-find merges were ever found.
- **Abstract countermodel constructed**: a small hand-built bipartite
  incidence model, respecting every graph-level axiom the corpus obeys
  (bipartite, degree caps, forest, R-legality) but NOT the specific
  permutation-level fact about hex 0, produces same-component with
  non-chaining -- proving the corpus's exact implication is not a pure
  graph theorem and requires the hex-0 pre-registration fact
  specifically.
- **One incidental correction**: literal replay showed RR words can
  contain a hidden zero-charge `Z2_abandon_w2_new` event that flips F
  from 0 to 1 partway through -- so the earlier "F=0 regime forces every
  joint's target hex fresh" theorem (proved for the strictly-before-A2
  window) does NOT generalize to all of RR as such; this round's own
  results do not depend on that theorem and were obtained by direct
  literal replay instead.

## Twelfth follow-up round: the Unique Hub Hexagon lemma, generalizing hex-0 necessity

Twelfth follow-up round, pushed specifically to go past re-confirming the
75/75 statistic and find either a real proof or the precise minimal axiom
gap. No new large-scale search; N=0 untouched.

- **New general, fully deductive lemma (Unique Hub Hexagon), proved from
  `f1_normal_form`'s own documented F<=1 invariant and re-confirmed
  exhaustively over all 4,470 RR witnesses (0 exceptions)**: in any
  F<=1-budget word, AT MOST ONE hexagon is ever the target of two or
  more different joints over the word's entire history (its "hub", if
  one exists at all). This generalizes last round's "hex 0" finding:
  orbit 0's component can only grow beyond the trivial pair {orbit 0,
  hex 0} if hex 0 itself becomes that hub -- i.e. if the word's one
  allowed abandonment fires while still inside hex 0 (the very first
  joint of the word).
- **Necessity direction narrowed to a single, precisely identified
  remaining gap**: same-component (R2) requires both R2's source and
  target orbit to connect through the hub -- proved in general. Within
  this depth<=6 corpus, the hub (when it exists) is exhaustively
  confirmed to be touched EXACTLY twice, and in all 10 same-component
  witnesses the second touch is always R1 itself (never a third,
  unrelated event) -- an exhaustive, corpus-exact fact, honestly
  labeled a "necessary axiom, not a general proof" since whether this
  holds beyond depth 6 is untested.
- **Abstract-model axiom ablation pinpointed the exact missing axiom**:
  adding a bare "at most one hub hexagon" cardinality cap to the round-11
  countermodel does NOT eliminate it; only additionally requiring "the
  hub's second touch must be R1 itself, not a third party" does. This is
  a genuinely new, precise result -- not a graph axiom, a fact about
  event roles within the word.
- **Bounded local search (depth<=5, exhaustive within bound, from all
  10 same-component witnesses' post-R1 states) found zero
  same-component-non-chaining candidates** -- strong local evidence,
  not a full proof.
- **New completion-cost finding**: R2's own already-proven-tight Phi
  potential is exactly 0 for all 10 same-component witnesses (vs. mean
  3.68 for non-chaining and 4.91 for chaining-but-different) -- these
  10 states sit exactly on the proven Phi>=0 completion boundary, with
  zero tolerance for any further ell<5 move. Reported as a corpus-exact
  correlation, not claimed as a proven causal mechanism.

## Thirteenth follow-up round: Hub Touch Count <=2 proved, "hub=R1" corrected, closure INCOMPLETE

Thirteenth follow-up round, explicitly pushed past re-confirming
statistics toward either a real proof or a precisely isolated gap. No
new large-scale search; N=0 untouched.

- **New lemma proved fully deductively (Hub Touch Count <= 2)**, purely
  from `current_hex`'s own code definition (`hexagon_id(state.p)`) plus
  the already-established F<=1 budget: whenever a hexagon receives a
  second joint-target (a "hub"), that event makes the hub the new
  current hex; since F is already spent, the hub can never again be
  abandoned, so its remaining positions can only be visited by pure
  rotation until it closes forever. Re-confirmed exhaustively over all
  4,470 RR witnesses (0 violations). This upgrades last round's
  corpus-exact-only observation to a genuine, depth-independent proof.
- **Self-correction: round 12's claim "the hub's second touch is always
  R1 itself" is FALSE.** Literal replay found 6/10 same-component
  witnesses where a separate zero-charge event -- not R1 -- completes
  the hub, reusing R1's own target ORBIT via a different phase/hexagon.
  The real, corpus-exact (10/10) necessary condition is purely about
  orbit identity, not event identity: "the hub completer's target orbit
  equals R1's target orbit," independent of which literal event
  performs the completion. The abstract-model axiom ablation (M2) was
  already encoding this correctly at the orbit level; only round 12's
  prose description was too strong.
- **Deep bounded re-search (depth<=9, exhaustive within bound, node_cap
  60,000 per witness) from all 10 same-component witnesses'
  post-abandonment states, exploring ALL reachable R1/R2 choices (not
  just the corpus's own recorded path)** -- one witness alone had 121
  alternative non-R hub-completing candidates before any R fired -- and
  still found zero same-component non-chaining counterexamples. This is
  substantially stronger local evidence than last round's depth<=5,
  fixed-R1 check.
- **Phi=0 continuation confirmed structurally forced by the F<=1
  budget** (not independently by Phi itself): every ell<5 candidate
  after R2 is pruned as `F_exceeded`, and the hub can never be
  re-touched (by the new Hub Touch Count lemma) -- both directly
  verified against `area_a_prune_reason`.
- **Bounded closure search (node_cap=30,000 per witness) toward actual
  completion from all 10 same-component witnesses' post-R2 states did
  NOT resolve** -- all 10 hit the node cap without the frontier
  emptying, so neither success nor exhaustive failure was established.
  Honestly reported as INCOMPLETE, consistent with this project's
  repeated experience that this scale of capacity question (orbit slack
  ~23) resists small bounded searches (cf. RA2's U4 states, unresolved
  even at depth<=18/edge_cap=1.5M).

## Fourteenth follow-up round: hub completer orbit theorem refined and falsified as originally posed

Fourteenth follow-up round, explicitly told not to reuse the false
"completer=R1" claim and to track orbit identity, not event identity.
No new large-scale search; N=0 untouched.

- **The round's originally-posed target theorem ("O != R1's target
  orbit candidates all violate some exact legality condition") is
  FALSIFIED by direct exhaustive enumeration**: from the one
  same-component witness whose abandonment leaves multiple hex-0
  positions open (`989d2261b458`, abandon at ell=0), all 5 remaining
  positions' orbits (1, 3, 9, 33, 120) are legally reachable hub
  completers -- via R, Z2, and even Z3 (fresh) events. Hub completer
  choice is NOT uniquely forced in general.
- **Sharper replacement discovered and proved for the dominant
  sub-case**: whenever the word's one abandonment fires at ell=4
  (9/10 same-component witnesses, and 206/4,470 of the full corpus),
  hex 0 has exactly ONE unvisited position left, so the hub completer
  orbit is uniquely forced by pure combinatorics (the position-orbit
  correspondence on hex 0, already established) -- no legality
  argument needed, the alternative candidates simply don't exist. This
  is a genuine, general, depth-independent proof for this sub-case.
  New corpus-exact finding: same-component NEVER occurs at abandon
  ell=1,2,3 (0/617), only at ell=4 (9/206) and ell=0 (1/200).
  The `ell<4` general case (besides the single ell=0 exception) remains
  open with no corpus data to test it.
- **Classified all 6 non-R1-completer same-component witnesses as one
  "same-orbit delayed completer" family**: R1 and the separate
  completer event always target the same orbit via different phases,
  confirming they are not exceptions but instances of a single pattern
  (2 sub-variants: R1-completer gap of 1 or 2 intervening zero-charge
  events).
- **Built the full RR relation implication lattice** (7 implications
  tested exhaustively over all 4,470 witnesses): only `same-component
  => chaining` and the pre-existing `chaining => not unresolved` hold
  without exception; every proposed generalization or strengthening
  (hub existence alone, same-target-orbit, hub+chaining together, or
  hub+orbit-match alone) is falsified with concrete counterexamples --
  showing the original theorem is already maximally tight.
- **Separated Phi=0 from the chaining argument**: confirmed Phi=0 is
  an independent arithmetic consequence of the specific macro-edge
  length/ell-sequence these witnesses share (traced exactly: Phi_initial=6,
  sum(5-ell)=6 for all 10), not a logical consequence of chaining or
  same-component -- avoiding the circular-argument risk the round
  explicitly warned against.
- Completion search was NOT expanded per instructions; a deep
  150,000-node targeted search (from the one multi-candidate witness,
  looking specifically for a same-component non-chaining pair with a
  non-R1 completer whose orbit differs from R1's target) found none,
  but the frontier did not empty (287,322 remaining) -- reported as
  additional local evidence, not proof.

## Fifteenth follow-up round: the abandonment-ell dichotomy, and why the "5-way ell=0 branch" is actually 1-way in practice

Fifteenth follow-up round, decomposing the same-component branch by the
abandonment event's rotation offset (ell) within hex 0. No new
large-scale search (only small bounded local BFS from real corpus
states, matching the scale of prior rounds' targeted checks); N=0
untouched.

- **Dichotomy theorem, finite complete verification**: replaying all
  4,470 RR witnesses (this corpus is an exhaustive enumeration of
  depth<=6 RR words, not a sample) confirms same-component occurs only
  at abandonment ell=0 (1 witness) or ell=4 (9 witnesses), never at
  ell=1,2,3 (0/2,777). `outputs/rr_abandonment_ell_table.json`.
- **New general fact, exhaustively verified (212/212 hub-completions,
  0 exceptions)**: whenever hex 0 receives a second touch at all
  (regardless of ell), the completer orbit is always exactly the
  *nearest* unvisited hex-0 position (position ell+1) -- never any
  farther residual position, even though a prior round's manual/local
  BFS had shown all 5 residual orbits are *legally* reachable at
  ell=0. Legal-in-principle and realized-in-the-actual-corpus are
  different questions. A bounded local-cost BFS from real
  post-abandonment states shows why: the nearest position always costs
  exactly 2 macro-edges to reach as completer, while every other
  residual orbit costs 4 or more -- inconsistent with the corpus's
  fixed 6-macro-edge total budget once R1 and R2 both still need to
  fit, except for one edge case (completer coincides with R1 itself)
  that the resource argument alone doesn't rule out but that never
  occurs in the exhaustive corpus (0/4,470) -- left honestly open.
- **New lemma, proved and exhaustively verified (212/212): Hub Exit
  Source Lemma** -- once F=1 is exhausted, any joint whose source lies
  within hex 0 must have source orbit exactly 1 (position 5, the only
  hex-0 position whose rotation successor wraps to the always-visited
  anchor). This is strictly stronger than the (already-falsified)
  "completer orbit = R1 target orbit" claim from Round 14.
  - Correction made mid-round: an initial buggy closure-tracking check
    (an `if False else None` no-op) wrongly suggested hex 0 never
    fully closes at ell<4; re-derived with the bug fixed, hex 0 in
    fact *always* fully closes once hub-completed, at every ell --
    this dead end was caught and discarded before being reported.
- **The originally-envisioned "5-way ell=0 branch" collapses to 1-way
  in the actual corpus**: all 43 ell=0 hub-completed witnesses use
  completer orbit 120 (the nearest position); orbits 1, 3, 9, 33 never
  occur as completers despite being legal in principle.
  `outputs/rr_ell0_normal_forms.json`.
- **Full exact trace of the single ell=0 same-component witness**
  (`989d2261b458`) reveals a second, *indirect* mechanism distinct from
  ell=4's direct one: R1 itself is the hub completer, reusing orbit
  120 (already touched at 3 different phases via 3 prior full-hex
  sweeps); after hex 0 forcibly closes and exits via orbit 1 (Hub Exit
  Source Lemma), R2 achieves "same" not through orbit 1 but by reusing
  orbit 120's fifth and final phase in a different hexagon -- all 5
  phases of orbit 120 end up visited across the word.
  `outputs/rr_ell0_completer_truth_table.json`.
- **Phi=0 generalized and cleanly separated from chaining, finite
  complete verification**: Phi(final)=0 holds for *all* 212
  hub-completed witnesses, not just the 10 same-component ones -- since
  Phi depends only on pass-count/visited-count (a pure macro-edge-count
  fact), this proves Phi=0 is fully independent of the
  union-find/component-identity structure that same-component and
  chaining depend on, resolving Round 14's open question without
  circularity. `outputs/rr_ell_branch_phi.json`.
- **Honest gaps left open**: the ancestry invariant Gamma (why exactly
  ell=1,2,3's 124 hub-completed witnesses never achieve same, beyond
  the exhaustive corpus fact itself), the full resource-budget
  impossibility proof (the R1-coincidence edge case), and
  generalizing the ell=0 branch's single exact witness into a proven
  pattern (only one instance exists in the corpus, no second case to
  confirm generality) all remain unresolved.

## Sixteenth follow-up round: a major corpus-completeness correction, plus a genuine minimum-cost theorem

Sixteenth follow-up round, attempting to prove the "nearest residual
completer" theorem Round 15 proposed. While trying to prove it, this
round found and confirmed a significant error in how Rounds 11-15
described the RR corpus. No new large-scale search; N=0 untouched.

- **Central finding: the RR corpus is a capped/bounded frontier
  replay, not a complete enumeration.** `legacy_research/work/
  analyze_f1_n2_defects.py`'s own docstring says its only exploration
  is "a capped continuation," and its scope note reads "finite
  complete replay of an existing bounded Area-A frontier; not an N=2
  enumeration." The underlying checkpoint
  (`A_F1_H0_Nle3_macro_depth6.checkpoint.json`) was capped at 65,340
  frontier states by some earlier round's search. This means every
  "finite complete verification" claim in Rounds 11-15 that relied on
  "the corpus is an exhaustive census of depth<=6 RR words" was an
  overclaim: the claims are true *within the 4,470-witness corpus*,
  but that corpus itself is not proven to cover all legal depth<=6
  states. A concrete counterexample state was constructed (weight
  sequence Z2abandon,R,Z3,Z2,R from the ell=0 abandonment root,
  landing R2 on hex 0's farthest residual position) that passes
  `area_a_prune_reason` (fully legal) and structurally matches "RR"
  (2 R events, F=1, H=0), yet is verifiably absent from the historical
  corpus by hash lookup.
- **Round 15's "nearest-only completer" claim is falsified** by a
  fresh, genuinely exhaustive re-derivation (BFS via
  `macro.macro_edges()`/`area_a_prune_reason()` from each abandonment
  root, independent of the historical corpus, frontier fully empties
  every time -- these state spaces are small, ~1,100-3,900 states):
  legal non-nearest hub completions occur at every ell<4, roughly as
  often as nearest ones.
- **What survives, reproven from scratch**: (1) a genuine, corpus-independent
  proof, via complete case enumeration over the model's only 4 joint
  moves (320 branches total), that cost=1 hub re-completion is
  impossible and cost=2 hub re-completion -- when legal -- always lands
  on the nearest residual position; (2) the same-component dichotomy
  (only ell in {0,4}, never {1,2,3}) is RECONFIRMED by the fresh,
  corpus-independent exhaustive search; (3) the ell=0 branch's
  single same-component exception is RECONFIRMED as unique via a
  fresh, genuinely exhaustive (frontier-emptying) search from the
  ell=0 abandonment root -- this conclusion holds even though the
  "nearest-only" premise it was partly built on did not.
- **Phi=0 refined**: a fresh exhaustive check finds hub-touched RR-final
  states reach Phi=0 in ~98% of cases (293/300), not 100% as Round 15
  claimed from the historical corpus -- 7 genuine counterexamples
  exist. The reverse direction (no hub touch implies Phi!=0) held
  300/300 in the same fresh sample.
- **R1/R2 self-completion**: constructed a concrete, legal,
  non-saturated-phase self-completion witness reaching a non-nearest
  orbit; 3 of 5 proposed obstruction candidates (S1, S2, S5) are
  directly falsified by it, 2 (S3, S4) remain untested. No clean
  obstruction theorem or normal form was established.
- **Methodological takeaway for future rounds**: claims resting on
  `legacy_research/outputs/f1_n2_defect_words.json` or
  `outputs/rr_literal_witnesses.json` should be labeled "within the
  historical bounded corpus" rather than "finite complete
  verification" unless independently reconfirmed via a fresh,
  corpus-independent exhaustive search the way this round did for the
  dichotomy and the ell=0 uniqueness result.

## Seventeenth follow-up round: full evidence audit, a formal exhaustiveness standard, and a corrected theorem dependency graph

Seventeenth follow-up round, explicitly tasked with auditing rather
than extending: reclassify every RR claim's proof status, cleanly
separate capped-corpus claims from genuinely corpus-independent ones,
and formalize what "exhaustive" is allowed to mean going forward. No
new large-scale search; N=0 untouched.

- **Reclassified 15 core RR claims** (`outputs/rr_claim_audit.json`,
  `research/RR_EVIDENCE_AUDIT.md`) into a standardized vocabulary:
  4 remain fully deductive proofs unaffected by the corpus issue
  (Unique Hub Hexagon, Hub Touch Count<=2, the Hub Exit Source Lemma's
  deductive core, abandon_ell=4's combinatorial uniqueness); most
  corpus-resting claims were downgraded from "finite complete
  verification" to "capped-corpus exact"; 2 were explicitly reconfirmed
  as falsified (nearest-only completer, hub-completed=>Phi=0
  universally) and 2 were upgraded to a new, stronger, genuinely
  corpus-independent category ("uncapped local exhaustive": the
  ell-dichotomy and the ell=0 witness uniqueness, both cross-checked by
  an independently-implemented DFS traversal that matches the BFS
  enumerator exactly on every count, every ell).
- **Formalized an exhaustiveness standard**
  (`research/RR_EXHAUSTIVENESS_STANDARD.md`): 9 required conditions
  (root-set completeness, transition-generator completeness, no
  node/edge/time cap, frontier-empty termination, canonicalization and
  prune soundness, deterministic replay, a full certificate, and an
  independent verifier pass) and 6 distinct terms (corpus replay,
  capped BFS, depth-bounded exhaustive, root-local exhaustive, globally
  exhaustive, naturally exhausted) that must not be used
  interchangeably going forward.
- **Found that fully uncapped enumeration (no declared depth ceiling
  at all) is NOT tractable here**: without a depth ceiling, the local
  state space is bounded only by this project's much larger global
  budgets (TARGET_P=121, TARGET_O=25), and a real attempt did not
  terminate within 590 seconds. What Round 16 called a "naturally
  small" state space was implicitly depth-capped all along; this round
  makes that ceiling an explicit, disclosed parameter instead
  (`--depth-ceiling`, reported in every certificate).
- **Built a genuinely uncapped-within-ceiling local enumerator**
  (`src/enumerate_rr_uncapped_local.py`) for root class 1
  (abandonment-instant state, 5 roots for ell=0..4) with a full
  certificate (expanded count, generated edges, unique canonical
  states, duplicate count, frontier-empty flag, max depth reached,
  engine SHA-256), cross-validated by an independently-coded DFS
  verifier (`src/verify_rr_exhaustive_certificate.py`) that agrees
  exactly on all 5 ell branches.
- **A genuine, general minimum-cost theorem** (`RR_COMPLETION_COST_THEOREM.md`):
  cost=1 hub re-completion is impossible and cost=2 always lands on
  the nearest residual position, both proved via a complete (not
  sampled) 320-branch case analysis over this model's only 4 joint
  moves. The converse ("nearest implies cost 2") is FALSE in general
  (using abandonment move w3:210 instead of the real w2:10 gives
  cost 5 to the same nearest orbit) but TRUE when conditioned on the
  real historical abandonment convention (w2:10, verified 4,470/4,470).
- **An unresolved discrepancy found and reported, not papered over**
  (**RESOLVED in Round 18 -- see that section below**): at ell=4, the
  historical capped corpus reports 9 same-component witnesses, but the
  fresh uncapped-local universe finds only 5. Round 17 flagged this as
  open rather than assuming a cause in either direction.
  `outputs/rr_old_new_corpus_diff.json`.
- **Phi=0 further quantified**: in the fresh local universe, hub-touched
  RR-final states reach Phi=0 in 283/290 (97.6%) of cases, not
  universally; the reverse direction (no hub touch implies Phi!=0) held
  991/991 (100%) in the same sample. The 7 counterexamples were not
  individually traced to a structural cause this round.
  `outputs/rr_corrected_phi_distributions.json`.
- **A corrected theorem dependency graph**
  (`research/RR_CORRECTED_THEOREM_GRAPH.md`) separates results into
  three tiers by evidence quality: a solid-line tier of pure deductive
  proofs plus this round's cross-checked uncapped-local results (safe
  to build on), a dashed-line tier of capped-corpus-exact observations
  (not yet falsified but not proven general), and a blocked-off tier of
  explicitly falsified claims that must not be reused as premises.
- **Root classes 2-5** (hub-completion-instant state, R1-precedent
  state, R2-precedent state) were defined conceptually
  (`research/RR_LOCAL_UNIVERSE.md`) but NOT implemented as separate
  enumerations this round -- flagged as the most direct next-round task
  rather than silently skipped.

## Eighteenth follow-up round: the ell=4 9-vs-5 discrepancy fully resolved (counting unit, not a missing witness)

Eighteenth follow-up round, tasked with resolving Round 17's one
outstanding discrepancy before proposing any new RR theorem. No new
search of any kind; N=0 untouched. Every number below comes from exact
replay of the 9 historical witnesses through the current engine.

- **RESOLVED: the gap was a counting-unit plus depth-scope difference,
  with no missing witness in either direction.** The historical
  corpus's unit is a complete 6-macro-edge WORD; the fresh enumerator's
  unit is a distinct post-R2 STATE. Replaying all 9 historical ell=4
  same-component witnesses shows they collapse onto exactly **3**
  distinct post-R2 states, and each of those 3 states has exactly **3**
  legal continuation macro-edges -- 3 x 3 = 9, matching the historical
  count exactly. All 3 states are present in the fresh 5-state set;
  the fresh set's other 2 sit at depth 6 past abandonment (7 total
  macro-edges), strictly outside the historical depth<=6 word scope.
  As post-R2 states, **H9 is a subset of L5** (H9 \ L5 = empty), so the
  direction is normal, not reversed as Round 17 feared.
  `research/RR_ELL4_DISCREPANCY_AUDIT.md`.
- **All 9 historical witnesses replay cleanly in the current engine**:
  every move legal, every step passing the current
  `area_a_prune_reason`, same-component reproduced 9/9, ell=4
  reproduced 9/9, zero divergences. So `HISTORICAL_RECORD_INVALID` and
  `CURRENT_ENGINE_DRIFT` are both ruled out by direct evidence.
- **The specific bug hypothesis raised when the gap appeared was tested
  and REFUTED**: re-running every root-local enumeration with the dedup
  key widened from `state.stable_key()` to `(state.stable_key(),
  r_count, r1_target_orbit)` changes nothing on any ell. A diagnostic
  counter shows **no state in this universe is ever reached with two
  different histories at all**, so the representation is Markov-complete
  for the same-component question here (a finite check over this
  universe, not a general proof).
  `research/RR_LOCAL_STATE_COMPLETENESS.md`.
- **Canonicalization / generator / prune all cleanly reconciled**: the
  historical generator hashes `exact.canonicalize(state)` while the
  Round 17 enumerator hashes the raw state -- canonicalizing this
  round's raw replays reproduces all 9 historical hashes exactly
  (9/9, raw 0/9). Both pipelines use the same child generator
  (`macro.macro_edges()`) and the same prune (`area_a_prune_reason`
  with `macro.AREA_A`); raw vs canonicalized child-label sets differ at
  0 states checked. `research/RR_SEARCH_SCOPE_RECONCILIATION.md`.
- **A real labeling error in Round 17's own output was found and
  fixed**: `outputs/rr_uncapped_local_universe.json`'s field
  `unique_canonical_states` actually counted RAW (uncanonicalized)
  states. Raw dedup is *safe* for completeness -- it can only
  re-expand left-S6-relabeled duplicates, never skip a reachable state
  -- so no Round 17 numeric result is invalidated, but the field is
  renamed `unique_raw_states` with an explicit `dedup_key` field, both
  scripts re-run, and the independent DFS cross-check still matches
  5/5 ell. Seven affected statements across STATUS.md, two research
  documents, two outputs, and two scripts were corrected, with a
  before/after/reason table in `RR_ELL4_DISCREPANCY_AUDIT.md` section
  13. No theorem was overturned by any of these corrections.
- Per the round's instruction, **no new general RR theorem is proposed
  here** -- the discrepancy had to be closed first, and it now is.

## Nineteenth follow-up round: the L5 local universe classified, and a real canonical enumerator

Nineteenth follow-up round. With the Round 18 discrepancy audit closed,
this round classifies the corrected root-local universe. No completion
search; N=0 untouched. Per the round's instruction, nothing here is
claimed as a global RR theorem.

- **A genuinely canonical enumerator was built** (Round 17's deduped on
  raw states, a labeling error Round 18 corrected). The real difficulty
  it had to solve: `exact.canonicalize()` returns the least left-S6
  translate but not the alpha achieving it, while history fields like
  "R1's target orbit" are raw orbit ids -- so the *pair* must be
  canonicalized, transporting history orbit ids through every tied alpha
  via `LEFT_ORBIT_ACTION` and taking the minimum. Result: duplicate
  count 0, every stabilizer tie count 1, and **every number identical to
  the raw enumerator**. So Round 17's raw dedup was not merely "safe" --
  in this universe it was exactly right, because the universe contains
  no two states that are left-S6 translates of each other.
- **The five ell=4 post-R2 states share one identical terminal
  signature** with no exceptions: R1 targets orbit 1, the hub completer
  lands precisely on (orbit 1, phase 4) = hex 0's position 5, R2 then
  fires immediately via `rot^0;w3:120` with source orbit 1 and target
  orbit 0, Phi=0, exactly 3 legal trailing edges, reached by exactly 1
  path. `research/RR_L5_LOCAL_UNIVERSE.md`.
- **The counting identity is exact**: 9 = 3 + 3 + 3, and *why* each
  state admits exactly 3 trailing edges is fully explained rather than
  observed -- once F=1 is spent, every ell<5 edge would be an
  abandonment (pruned `F_exceeded`), leaving only ell=5; there are only
  4 joints in the model; and one of them (`w3:120`) is still abandoning
  here. `research/RR_WORD_STATE_MULTIPLICITY.md`.
- **The proposed N2 theorem is FALSIFIED as stated.** N2 is not "H3 plus
  one inserted zero-charge block": it has two more preparation edges,
  its extra edges are Z3 fresh-orbit openings that H3 never uses at all
  (H3 holds O=2, N2 reaches O=4-5), and its hub completer is always R1
  while H3 contains both the R1-completer and Z2-completer variants. The
  corrected picture is **one shared terminal normal form reached by two
  structurally independent preparation families**.
  `research/RR_H3_N2_NORMAL_FORMS.md`.
- **No nontrivial necessary-and-sufficient chaining predicate was
  found** -- reported as 미완료 rather than dressed up: the only IFF
  predicate is `r1_target == r2_source`, which is chaining's own
  definition. What the ablation did establish: `same_component` is
  strictly sufficient but not necessary (fp=0, fn=23); it coincides
  exactly with "both R2 roots in the hub component"; `r2_source_orbit==1`
  alone is falsified as a predicate (fp=31); and `same_target` is
  disjoint from chaining (tp=0, 449 counterexamples), independently
  reconfirming a Round 14 corpus observation in a corpus-free setting.
  `research/RR_LOCAL_CHAINING_PREDICATE.md`.
- **Markov-completeness: the empirical check is VACUOUS, and the
  deductive answer is "no".** All 2,234 distinct post-R2 states at depth
  6 are reached by exactly one R2 boundary, so there are no two
  histories to compare -- the zero-collision fact proves nothing. The
  real answer is deductive: a post-R2 `ExactState` records which
  (orbit,phase) pairs are visited but not which edge was R1, so
  `r1_target_orbit` is not a function of it and chaining cannot be
  decided from the state alone. Both relations are boundary data, not
  state data, and the enumerator must carry the history fields.
- **Depth-7 stability check** (coverage confirmation, not a completion
  search; frontier exhausted naturally, no cap): the ell=4 five-state
  set is **completely stable** (still exactly 5, same H3/N2 split), the
  ell in {0,4} dichotomy still holds (ell=1,2,3 remain 0), and
  same-component => chaining still has 0 violations. Only ell=0 grows,
  1 -> 3.
- **A permanent counting-unit standard** was written to prevent the
  Round 18 confusion from recurring: four units (word / post-R2-state /
  event / history), mandatory unit-bearing field names, and the exact
  conversion identity between them.
  `research/RR_COUNTING_UNIT_STANDARD.md`. A full re-scan of Rounds
  11-18 for the affected phrasings found **no corrections needed beyond
  the 7 already made in Round 18**.

## Twentieth follow-up round: the decorated boundary state, and a refutation of Round 19's stability claim

Twentieth follow-up round. No completion search; N=0 untouched. Nothing
is claimed as a global RR theorem.

- **The decoration alone determines the relations.** Round 19 proved
  deductively that a post-R2 ExactState cannot decide chaining. This
  round defines the decoration to carry alongside (5 orbit-transported
  fields, 4 hexagon-transported, 18 left-S6-invariant), and finds the
  reverse: over all 2,234 R2 boundaries, the decoration WITHOUT the
  ExactState determines chaining, same-component, and the trailing-edge
  signature -- 2,216 distinct keys, zero conflicting groups.
  Grade: exact decorated quotient. `research/RR_DECORATED_BOUNDARY_STATE.md`.
- **The ablation was designed to avoid being vacuous, and its greedy
  result is reported with its caveat.** Including the ExactState in any
  key would separate every boundary (each state is reached once), making
  "drop a field, look for collisions" report every field as unnecessary.
  So the ExactState is excluded. Only `fresh_orbit_openings` is provably
  necessary; the other 26 fields are labeled "necessity undetermined",
  never "unnecessary". The greedy 7-field subset SEPARATES this finite
  universe but does not let one COMPUTE the relations from their
  definitions -- it omits `r1_target_orbit`, which chaining is defined
  in terms of. Separating-minimality and structural-minimality are
  different notions and the weaker one is flagged as such.
- **Same-component has an exact ancestry characterization.** Three
  predicates are all IFF (tp=6, fp=0, fn=0): the LCA form
  (`every shortest path between R2's endpoints passes through the hub`),
  `both endpoints at finite hub distance`, and Round 19's
  `both roots in the hub component`. The graph reason is the already-proved
  Unique Hub Hexagon lemma -- the hub is the only possible junction.
- **Chaining still has no non-trivial iff predicate** -- reported as
  open again. The best sufficient one improved from Round 19's
  `same_component` (a relation) to `r1_target_hub_distance ==
  r2_source_hub_distance == 1` (pure hub geometry), same confusion
  matrix, still not necessary (fn=4). `hub_completer_orbit ==
  r1_target_orbit` alone is falsified outright (fp=187).
- **Round 19's "the ell=4 set is completely stable" is REFUTED.** A
  depth-8 coverage run (root-local, no cap, frontier exhausted, 43,459
  nodes) grows the ell=4 same-component set from 5 to **9** states. The
  reason depth 6->7 showed no change is **parity**, not closure: ell=4
  boundaries occur only at EVEN depth from the abandonment root (4, 6,
  8) and ell=0 only at ODD depth (5, 7). Raising the ceiling to an odd
  number could not add anything at ell=4. No upper bound on preparation
  depth is established, and fresh-opening blocks can be inserted
  repeatedly (one state uses 5). `research/RR_TERMINAL_NORMAL_FORM_THEOREM.md`.
- **Round 19's "exactly 3 trailing edges" is also refuted, and replaced
  by a proved upper bound.** The F-exhaustion argument proves *at most*
  3 (ell<5 edges are all abandonments; the model has 4 joints; `w3:120`
  is still abandoning). 11 of the 12 states have exactly 3, but
  `cbfdf11e4a79` at depth 8 has only 2 -- an extra visited-collision, not
  `F_exceeded`.
- **A common terminal normal form holds across both branches** (12/12
  states, ell=0 and ell=4): R1 targets the nearest-residual orbit O*,
  the hub completer is the LAST preparation edge and lands on O*, R2's
  source is O* at phase 4 and its target is the initial orbit 0, Phi=0,
  and chaining is therefore forced. The branches differ only in O*
  (1 vs 120), the completer's landing phase (4 vs 0), the
  completer-to-R2 distance (1 vs 2), and depth parity.
- **H3 has a clean parameterized normal form**: preparation is exactly
  3 macro-edges, exactly one of which is R, and the three states are
  precisely the three placements of that R. Whether the completer is R1
  is not separate structure -- it is the i=3 case.
  `research/RR_H3_PREPARATION_NORMAL_FORM.md`.
- **N2 is NOT established as a single parameterized family** (2
  instances, differing Z3 counts and placements), and Round 19's
  "fresh-opening vs no-fresh-opening" dichotomy breaks at depth 8, where
  3 of the 4 new states have exactly one fresh opening. Preparation
  length (3, 5, 7 -- all odd) is the more stable classification axis.
- **The ell=0 family growth is characterized but its finiteness is
  NOT decided** -- reported as open. The 3 ell=0 states share a fully
  identical terminal signature and differ only in preparation length
  (4 vs 6) and Z3 count (0, 2, 3). Given that ell=4 gained a whole new
  preparation length at depth 8, unbounded growth is the better-supported
  expectation, and no evidence for finiteness exists.
  `research/RR_ELL0_FAMILY_GROWTH.md`.
- **Decorated Markov-completeness is partial, honestly.** Child legality
  is a pure function of the ExactState and decoration updates are local
  (both 손증명), but the strong form -- same decorated state implies same
  continuation tree -- is VACUOUS here, since no two histories reach the
  same decorated state. Left as 미완료.

## Twenty-first follow-up round: the preparation grammar, a parity proof, and three corrections

Twenty-first follow-up round. No completion search; N=0 untouched. The
one deep run (ell=0 at depth 9) was a grammar *prediction test*, run
only after the grammar candidate existed, to a separate output path.

- **Depth convention fixed and both stored everywhere.** Round 20's
  "ell=0 is odd depth" was in the abandonment-root convention. In the
  word-start convention (abandonment counted as edge 1) it is the
  reverse: ell=4 is ODD (5,7,9), ell=0 is EVEN (6,8,10). Not a
  contradiction, but it needed stating, and both fields are now on every
  record.
- **Parity is now largely hand-proved.** Decomposing each witness as
  `A_ell · P · C · T_ell · R2`, Lemma P1 proves the branch difference
  outright: the hub's only exit position is position 5 (orbit 1, by the
  Hub Exit Source Lemma), and chaining needs R2's source to be the
  nearest-residual orbit O*. For ell=4, O* IS orbit 1, so the hub-exit
  edge can be R2 itself, giving tail length 0; for ell != 4 it cannot,
  forcing one extra `Xh` edge, tail length 1. That single difference
  produces the whole parity split. The remaining gap is that `|P|` is
  even, which is observed (14/14) but not proved -- and is specifically a
  same-component phenomenon, since over ALL hub completions odd values
  genuinely occur.
- **Phi=0 upgraded from arithmetic coincidence to a consequence of the
  normal form.** A contributes (5-ell); the hub-exit edge fires after
  rotating from position ell+1 to position 5, so it contributes
  (1+ell); the sum is 6 for EVERY ell, which is exactly the Phi=0
  condition. All other preparation edges are ell=5 and contribute 0.
  This closes a question left open since Round 15.
- **A grammar relation was predicted and then confirmed.** The
  before-completer words satisfy `P(ell=0) = the Rh-free members of
  P(ell=4)`, at every length. Having seen this at lengths 2 and 4, the
  round predicted that ell=0 at depth 9 would gain exactly `EEFEEE` and
  `FFFEFF` -- and the run produced exactly those two, nothing else.
  The structural reason: at ell=0 the completer must BE R1, so no
  earlier Rh can exist.
- **The insertion/deletion theorem is FALSIFIED, 8/8 counterexamples
  each way.** No observed preparation word reduces to a shorter valid
  one by deleting a contiguous 2-block, and none is obtained from a
  shorter one by inserting a single contiguous 2-block (`FEFE` cannot
  come from `EE` -- it needs two separated insertions). Every observed
  P is irreducible, so the "finite base forms + repeated insertion
  block" grammar the round aimed for **does not exist** for this data.
  What survives is a hand-proved `T_ell` rule plus a per-length list of
  P words -- honestly graded bounded observation, not an exact grammar.
- **No nontrivial preparation-depth bound was found.** The obstruction
  is concrete: `E` edges (existing-orbit zero-charge transitions)
  consume no monotone resource at all -- O unchanged, no fresh orbit, no
  Phi cost -- and a length-7 preparation exists using only ONE fresh
  opening. Only the trivial finite-state-space bound remains, which the
  round explicitly excluded. Reported as 미완료.
- **The 2-vs-3 trailing predicate is found**: it is a single occupancy
  bit -- whether `w3:210`'s ell=5 target permutation is already visited
  -- and it is predicted exactly by the symbolic word `P = EEFEEE`
  (2/2 with, 12/12 without), across BOTH branches.

Three corrections to earlier rounds, all from this round's checks:
- **Round 20's "the hub completer is the last preparation edge (12/12)"
  is refuted**: true for ell=4 (9/9), false for ell=0 (0/5), where the
  completer is second-to-last. Round 20 generalized an ell=4 pattern to
  ell=0 without checking it.
- **Round 19/20's "w3:120 is removed by F_exceeded" is wrong**: no
  ell=5 RR joint is ever F_exceeded at these states (14/14); w3:120 is
  removed by a literal visited-collision. So the hand-proved trailing
  upper bound is 4 (the joint count), not 3.
- **Round 20's "the ancestry theorem follows from the Unique Hub
  Hexagon lemma" was an overclaim**: that lemma gives uniqueness of the
  twice-touched hexagon, but a once-touched hexagon can still hold two
  orbits, so "the hub is the only junction" does not follow. Two of the
  four directions are hand-proved; the other two are downgraded to
  root-local exhaustive with the missing assumption named.

## Twenty-second follow-up round: the parity route refuted, an automaton built, and two of my own claims corrected

Twenty-second follow-up round. No completion search; N=0 untouched. No
new depth runs -- everything reuses the naturally-exhausted ranges.

- **A self-correction found mid-round, before it reached any
  conclusion.** The first invariant search reported four functionals
  flipping on every preparation edge. It was measuring the wrong
  boundary -- comparing the post-rotation state with the post-joint
  state, i.e. only the joint, not the full macro-edge. Re-measured
  correctly over all 48 preparation edges: visited_count increments by
  6 (even, does NOT flip), n_hexes by 1, P by 1, and ell is always 5.
- **The proposed parity proof route is REFUTED.** Of 15 candidate mod-2
  functionals (permutation sign, hexagon/orbit/phase parities, endpoint
  coordinates, incidence-graph distances to the hub, and sums thereof),
  the only ones flipping on every preparation macro-edge are `n_hexes`
  and `P` -- and both are pure per-edge counters (+1 each). So "start
  and completer-ready have the same colour" is a restatement of "the
  edge count is even", and the argument is circular. The bipartite
  formulation of section 4 fails for the same reason: the transition
  graph is graded by n_hexes, hence trivially bipartite. |P| evenness is
  now reduced to the exactly equivalent statement "the touched-hexagon
  count at the completer-ready boundary is even", which was not
  independently characterized. **Success criterion 1: not achieved**,
  with the reason the proposed route cannot work now precisely
  identified.
- **A symbolic preparation automaton was built** (26 states in each
  branch, 97-104 transitions, alphabet E/F/Rh/Rx). Every transition is
  induced by a real exact edge, but the boundary state carries no
  visited mask, so accepted symbolic words are not guaranteed
  realizable. Graded honestly as a **sound over-approximation /
  necessary-condition automaton**, not an exact automaton. All 14 known
  preparation words parse, uniquely -- bounded coverage only.
- **Why Rh is absent at ell=0 is now settled, and two of the four
  proposed reasons are refuted.** Rh edges ARE locally legal in ell=0
  preparation prefixes (concrete witnesses found), which refutes
  candidates R2 and R3. The real reason (R4) is structural: at ell=0 the
  completer must BE R1, since the completer targets O* and chaining
  requires R1 to target O*, and an RR word has only two R events. Hence
  no earlier Rh can exist. That is a hand proof of Inclusion 1 of the
  Rh-free sublanguage identity; Inclusion 2 remains observation-grade
  because no branch transport map was constructed (**criterion 4: not
  achieved**).
- **The exact trailing-edge formula is established**: m(S) = 4 - #blocked
  candidates, holding 12/12, with zero duplicate targets so the
  correction section 17 asked about is unnecessary here. All four
  candidates legal was never observed but is not ruled out, since
  w3:120's blocking is a state-dependent visited-collision rather than
  a structural fact. **Criterion 6: achieved.**
- **Round 21's claim that E edges consume no monotone resource is
  WRONG, corrected here.** Direct measurement shows every preparation
  edge -- E included -- consumes one hexagon and six permutations. The
  accurate statement is that E consumes no ORBIT-level resource. The
  resulting bounds (|P| <= 118 or 119) are still essentially the trivial
  state-space bound, so the conclusion "no small structural bound"
  stands, but for a different reason than Round 21 gave.
- Correction log written to `outputs/rr_round22_correction_log.json`.
  The three statements section 18 asked to purge were already fixed at
  their primary sites in Round 21; this round scoped two residual
  occurrences and fixed one new Round-21 error.

## Twenty-third follow-up round: the parity source located, and three proposed routes closed

Twenty-third follow-up round. No completion search; N=0 untouched. No new
depth runs.

- **The source of |P| evenness is located.** Enumerating every hub
  completion that lands on the O* position gives a table identical in
  both branches: even |P| always has exactly ONE R event through the
  completer, while odd |P| has either zero or two. Since an RR
  same-component witness needs exactly one R through the completer (R1
  must target O* for chaining, R2 fires strictly after, and an RR word
  has exactly two R events -- a hand proof), the R-count is pinned to 1,
  which forces |P| even. The parity is therefore a consequence of the
  R-placement, not of any graph or counter structure.
  The remaining gap is one measured relation: |P| + #R(through C) is odd
  in every case (all five ell branches, root-local exhaustive),
  equivalently the number of zero-charge edges through the completer is
  even. That relation is not yet hand-proved.
- **Three proposed proof routes are closed, each by a hand proof or an
  explicit counterexample:**
  - *Group-level parity*: all preparation edges are forced to ell=5, so
    the transition graph is the Cayley graph of the four generators
    Sigma^5·action_j. Their signs are (+1,+1,+1,-1) -- not all in one
    coset of A6 -- and an explicit odd closed walk was found. The graph
    is **not bipartite**, so no such argument can exist.
  - *Completer-target constraint*: O*-landing completions occur at BOTH
    |P| parities (9 even, 10 odd) at every ell, so requiring the
    completer to hit O* does not force parity.
  - *Degree / handshake / forest*: every preparation edge makes the same
    degree change, so any degree-based quantity is a linear function of
    the edge count. The forest identity degenerates to n_O = c with k
    cancelling.
- **A second self-correction, caught by measurement.** This round first
  predicted the incidence graph would give each traversed hexagon degree
  6 (from the ell=5 sweep). Measurement refuted it: orbit_masks records
  only JOINT targets, not rotation steps, so every touched hexagon has
  degree exactly 1 and |E| = k+2. The corrected ledger is what the
  document and certificate now carry.
- **An exact branch transport map is proved IMPOSSIBLE.** The
  abandonment root at offset ell has visited_count = ell + 2 exactly, so
  root(0) has 2 visited permutations and root(4) has 6. Any map
  preserving exact legality must preserve the visited set's cardinality,
  since legality of every later joint is decided by whether its target is
  already visited. Hence no state-level bijection Q_4 -> Q_0 exists, and
  the route Round 22 left open for the Rh-free reverse inclusion is
  closed -- that inclusion stays root-local exhaustive with no general
  proof.
- **Automaton x resource ablation**: `r_count` and `hub_residual` refine
  the quotient not at all (state and transition counts unchanged), so
  both are removable; only `fresh_count` and `o_star_phase_mask` refine
  it. No combination reaches exactness, since none encodes the visited
  mask -- all graded sound over-approximation, as instructed.
- **m(S)=4 is not ruled out.** w3:120 is blocked in all 12 terminal
  states, but by a visited-target collision rather than
  area_a_prune_reason, which is state-dependent. So m(S)<=3 is
  root-local exhaustive only; the hand-proved bound stays at 4.

## Twenty-fourth follow-up round: why the parity cannot be proved additively

Twenty-fourth follow-up round, aimed at the single open proposition
|P| + #R = 1 (mod 2). No completion search; N=0 untouched.

- **Round 23's table was checked for an artifact, and survives.** That
  scan capped the R count at 2, so its "odd |P| has #R in {0,2}" could
  have been an artifact of the cap. The cap is removed here and the
  relation still holds, at every ell.
- **The relation is SHARP, and that is new information.** Classifying
  every hub completion by landing position shows |P| + #R is purely odd
  at the O* position (j = ell+1) and at j = ell+2, but MIXED at
  j >= ell+3. So it is not a property of hub completion in general -- it
  is tied to landing on the near residual positions, which points at
  where a real proof would have to come from.
- **The equivalence asked for is proved.** Through the completer there
  are |P|+1 events, split as #R + #zero, so |P| + #R = #zero - 1 (mod 2).
  Hence |P| + #R odd <=> #zero even. Pure arithmetic, hand proof.
- **A genuine impossibility theorem, which explains every failure of
  Rounds 22-24 at once.** Measuring the per-event increment of every
  ExactState field gives a constant per event kind (S: +1/0/+1, O:
  0/0/+1, P: +1/+1/+1, D: -1/-1/+4, Ndef: +1/0/0, visited: +6/+6/+6),
  and D = 5*O - P is an exact identity (0 violations / 1,399 states).
  Therefore every additive field is a fixed linear form in (#R, #E, #F),
  every Z/2 functional built from additive fields is a linear form in
  those counts, and such a form certifies "#E + #F even" only if it IS
  that statement -- circular. **No additive invariant can prove the
  parity.** This subsumes Round 22's 15 mod-2 candidates, Round 23's
  handshake/odd-degree/forest routes and n_hexes/P counters, the Cayley
  sign argument, and this round's own field ledger.
- **The endpoint-role route (section 3) is refuted by the same theorem.**
  A role whose transition depends only on the event kind is an additive
  invariant, so no such role can work; a richer role (hub membership,
  O*-membership, revisit status, O* phase count) was built and does not
  flip consistently either.
- **The odd-preparation exclusion is recorded but rests on the unproved
  relation.** At the O* position with odd |P|, #R is always even (0 or
  2): #R=0 makes chaining impossible, #R=2 makes R2 a third R event. So
  odd |P| is incompatible with same-component RR -- root-local
  exhaustive, not a hand proof, since it uses the relation itself.
- Per the round's instruction, the word-level branch relation (section
  10) was left untouched while the parity remains open.

**Net position on the parity**: still 미완료, but the search space is now
sharply cut. A proof must use a non-additive constraint -- the
orbit/position combinatorics that decide which hub position the completer
may land on -- and the sharpness result localizes exactly where that
constraint bites.

## Twenty-fifth follow-up round: order-dependence made explicit, and one surviving structural partition

Twenty-fifth follow-up round, targeting the non-additive cause of the
preparation parity. No completion search; N=0 untouched. No additive
feature scans, per the round's instruction.

- **Order-dependence is now demonstrated, not just argued.** Eleven
  exact pairs exist whose additive event counts (ell, #R, #Z, #F) are
  identical but whose landing class differs -- e.g. `FFEFR` lands on O*
  while `EFFFR` lands far, with the same counts. So the landing position,
  and hence the parity condition, is a function of the event ORDER, not
  of the counts. This is the empirical complement to Round 24's
  impossibility theorem.
- **The parity is confirmed on a much larger set, with no R-cap**: the
  zero-charge count is even in all 95 O*-landing completions and all 48
  landings at j = ell+2, and MIXED at j >= ell+3 (31 even, 13 odd). So
  the evenness belongs to the two nearest residual positions, and
  degrades in stages as the landing moves away.
- **One structural partition survives, and it is new.** Of five
  candidate pairing rules, four are killed by exact counterexamples
  (same target orbit: `FFEFR`; same target hexagon and same target
  phase: `EER`; same symbol: `RFERR`). The survivor is the split by
  "does this zero-charge event target O*": at O*-landing, BOTH blocks
  have even size, 95/95. That refines the single evenness into two finer
  ones. It fails at j = ell+2 (`ERFERF`) and beyond, so it is specific
  to O*-landing.
  Honest limit: even blocks are not an explicit matching, and the round
  does not claim one -- section 14's target is 미완료.
- **The minimal odd far-landing witnesses are exhibited** (section 11):
  13 exist, the smallest being `EFRRFR` (#Z=3) and `FFRFFE` (#Z=5).
  Why no analogue exists at the two near positions (0 out of 143) is
  **not explained** -- none of section 12's six candidate obstructions
  could be pinned to an exact transition-level contradiction.
- **The ordered group equation is written down explicitly**: since every
  preparation edge is forced to ell=5, landing at hub position j is
  exactly `Sigma^ell · a_2 · g_{x_1}···g_{x_k} · Sigma^m · a_c = Sigma^j`
  with non-commuting generators. A limitation worth recording: the
  symbols F and R can share a move label (they differ only by
  new_orbit), so a symbolic word does not determine the group product --
  which caps how far a purely symbolic argument can go.

**Net position on the parity**: still 미완료. This round did not prove
it, but it converted "additive approaches fail" into "landing is
provably order-determined", and found the first structural refinement
(the O*-targeting split into two even blocks) that is specific to the
landing class where the parity holds.

### The O* phase walk — the surviving partition explained, and the gap narrowed to one lemma

`src/analyze_rr_o_star_winding.py` -> `outputs/rr_o_star_winding.json`,
written up in `research/RR_ORDERED_PHASE_PARITY.md`. No new search: this
is a re-reading of the ordered-word ledger as a walk on the five phases
of the single orbit O* (the nearest residual orbit the abandonment
leaves open).

Six premises, with their grades:

- **(a) F never targets O*** — 손증명. An F event opens a NEW orbit, and
  O* is already open (the abandonment registered it). So the zero-charge
  events touching O* are exactly the E events. Measured: 0 exceptions
  in 95 O*-landing completions.
- **(b) every E step advances the O* phase by exactly +1** — measured,
  110/110. Not proved.
- **(c) every R step advances it by an even amount** — measured, +2
  115 times and +4 10 times, 125/125. Not proved.
- **(d) the total advance is 4 (mod 5) for every ell** — 손증명: hub
  position j has phase j-1 while the abandonment phase is j mod 5.
  Measured: advance = 4 in all 19 completions at each of ell=0..4.
- **(e) the five O* phases are pairwise distinct along the walk**, so
  the walk has at most 4 steps — 손증명 from `orbit_masks` (a visited
  (orbit,phase) cannot be revisited). Measured: 0/95 revisits, walk
  length histogram {1:10, 2:35, 3:45, 4:5}.
- **(f) at most 2 steps are R** — 손증명 from the RR definition (exactly
  two R events in the word). Measured: {0:5, 1:55, 2:35}.

From (a)-(d), with k the winding number of the phase walk
(`sum(deltas) = 4 + 5k`):

> **#Z_{->O*} ≡ k (mod 2)** — the evenness of the zero-charge events
> targeting O* IS the evenness of the winding number.

From (e),(f) a finite case analysis forces **k = 0**: all deltas are
positive and the sum is ≡ 4, so k ≥ 0; the maximum sum is 4+4+1+1 = 10
< 14, so k ≤ 1; and k = 1 needs sum = 9, whose only multiset over
{1} ∪ {2,4} with ≤ 4 entries and ≤ 2 non-1 entries is {4,4,1}, all three
orderings of which revisit a phase. An exhaustive alphabet search
confirms it mechanically: 0 witnesses under #R ≤ 2, and exactly 2
witnesses ((1,2,4,2) and (2,4,2,1), both with odd #E) once that bound is
dropped — so premise (f) is doing real work, not decoration.

Measured k across all 95 O*-landing completions: **k = 0 in every case**,
and (k, #E parity) = (0, 0) in every case. This is the structural cause
of the O*-targeting partition that survived section 14 — the evenness
comes from a phase winding number, not from any pairing rule, which is
why no matching rule needed to exist.

**What is still missing, precisely**: premises (b) and (c). The delta of
a step is measured relative to the previously visited O* phase, not a
local property of the event, so proving "E always lands on the phase
immediately after the last-visited one" needs its own lemma. Until then
the chain is 미완료 and `|P| + #R_{<=C} ≡ 1 (mod 2)` remains unproved.
Two further honest limits: this closes only the O*-targeting block, with
no argument yet for the evenness of #Z_{->other}; and the interval and
first/last-symbol routes were both **refuted** this round (5 of 95
completions leave two F's unclosed; 5 of 95 end their zero-charge run
on F rather than E).

The practical effect is a real narrowing: the parity problem went from
"find an additive invariant" (proved impossible in Round 24) to "prove
the O*-step alphabet is exactly {E:+1, R:even}" — a single local lemma,
after which the finite case analysis above closes #Z_{->O*} immediately.

### The O*-step lemma — premise (b) proved, premise (c) refuted in general, and a sharp threshold found

`src/verify_rr_o_star_alphabet.py` -> `outputs/rr_o_star_alphabet.json`,
`src/prove_rr_o_star_step_lemma.py` -> `outputs/rr_o_star_step_lemma.json`,
written up in `research/RR_O_STAR_STEP_LEMMA.md`. The second script runs
no search at all — it is a finite group computation in S_6.

**The key structural fact.** Every preparation macro-edge is forced to
ell=5, so each acts on the walk position by right-composition with one
fixed element `g_j = Sigma^5 o action_j`. Computing all four:

| joint | `Sigma^5 o action` | in `<E>`? |
|---|---|---|
| `w2:10` | (1,2,3,4,0,5) | **E** |
| `w3:120` | (2,3,4,0,1,5) | **E²** |
| `w3:201` | (2,3,4,1,5,0) | no |
| `w3:210` | (2,3,4,1,0,5) | no |

So the ell=5 `w2:10` edge *is* right-multiplication by the orbit
generator E, and `w3:120` is right-multiplication by E². Two hand proofs
follow immediately:

- **F is never `w2:10` or `w3:120`** — an orbit-preserving edge cannot
  open a new orbit. Measured: 4,629/4,629 and 4,283/4,283 have
  `new_orbit=False`. So every F is `w3:201` or `w3:210`.
- **Premise (b) is now 손증명, not measured**: from a port q of O*, a
  `w2:10` edge lands at q∘E — phase +1 exactly; `w3:120` lands at q∘E².

**Premise (c) in general is 반증됨.** The orbit-changing joints leave
O*, so their displacement is the `<E>`-exponent of the whole intervening
product, and the alphabet lemma becomes a free-monoid statement. An
exhaustive first-return BFS over S_6 (716 non-`<E>` elements reached)
finds **4 violations**: two first-return words of length 7 with exponent
3, and two of length 8 with exponent 1. The alphabet is therefore **not**
a pure group fact — it cannot be proved without legality constraints.

**But the same computation gives a sharp threshold.** Every first-return
word of length ≤ 6 has exponent 1 (single E), 2 (single E²), or even —
exact group computation, no exceptions. The first odd exponent appears at
length 7. Hence:

> If consecutive O* visits are at most 6 preparation edges apart, the
> alphabet lemma holds and the winding argument closes #Z_{->O*}
> evenness.

The observed first-return gaps in the local universe are 0 (for `w2:10`
and `w3:120`, which land immediately), 4 (for `w3:201`) and 3 or 4 (for
`w3:210`) — all below the threshold, which is *why* the alphabet holds
there. This changes the status of the long-standing "small preparation
depth bound" item: it is now known to be **sufficient**, and its needed
form is pinned down precisely — not a bound on word length, but a bound
of 6 on the O*-revisit gap.

**Universe-wide verification.** `verify_rr_o_star_alphabet.py` checks
every legal macro-edge from every reachable state at all five roots (not
only hub-completing edges): 18,778 legal edges, 180 O*-steps, identical
histograms at every ell (`E:+1` 14, `R:+2` 18, `R:+4` 4), and **0**
violations of the E delta, **0** odd R deltas, **0** phase revisits, **0**
F events targeting O*. That exhaustively confirms premises (a) and (e)
as well.

**Net**: the parity chain is now 손증명 at every step except one — the
O*-revisit gap bound — and even that is reduced to a concrete finite
threshold. Two honest limits remain: the gap bound itself is 미완료, and
closing it would give only #Z_{->O*}; the evenness of #Z_{->other}
(observed 95/95) still has no argument at all. So
`|P| + #R_{<=C} ≡ 1 (mod 2)` remains **미완료**.

### Round 26 — the O* revisit-gap bound is FALSE, and with it the alphabet route

`src/enumerate_rr_first_return_words.py`, `src/analyze_rr_length7_obstructions.py`,
`src/verify_rr_o_star_gap.py` -> `outputs/rr_first_return_table.json`,
`outputs/rr_length7_counterexamples.json`, `outputs/rr_o_star_excursions.json`,
`outputs/rr_gap_certificates.json`. Six write-ups, led by
`research/RR_O_STAR_REVISIT_GAP.md`. No completion search; the N=0 search
and checkpoint were not touched.

**Counting convention, fixed and corrected.** L = first-return word
length (macro-edges from the O* port up to and including the edge landing
back in O*); G = L−1 = the gap. Round 25's write-up compared observed G
values (0, 3, 4) against a group threshold stated in L (≤ 6) without
saying so. The conclusion was unaffected — L = 1, 4, 5 are all ≤ 6 — but
the units were mixed, and every table now carries both.

**The target proposition is 반증됨.** Enumerating legal first-return
excursions from all five abandonment roots to L ≤ 8 — a ceiling set
deliberately past the group threshold 6, so that "nothing exceeds 6"
would be a finding rather than an artifact — produces legal excursions of
**L = 7 with ODD return exponent 3, at every one of the five roots**:

```
joints   = w3:201, w3:201, w2:10, w3:210, w2:10, w3:210, w3:201
symbolic = F F E F E F R        (#R=1, #F=4, #E=2)
```

Enumerating every literal word of length 7 and 8 over the four ell=5
generators (81,920 words) and replaying each through the engine: of the
39 odd-exponent first-return words, **38 replay legally**. Exactly one is
removed, by `N_exceeded_monotone`. Section 3's goal — find a common
legality obstruction that kills all of them — has the opposite answer.

**No budget coordinate separates them.** Excursion length fails (L = 7
and 8 carry both odd and even). The R budget fails: the minimal
counterexample needs only 1 R, inside RR's budget of 2. The F budget
fails: odd excursions need #F ≥ 3, but a legal *even* excursion of length
5 (`FFEFR`) already has #F = 3, and observed same-component words reach
#F = 3 too — so no true F bound excludes them.

**The legal length spectrum is not an interval**: {1, 4, 5, 7, 8}.
L ∈ {2,3} are impossible group-theoretically; **L = 6 is
group-theoretically possible but killed by legality**. Since L = 6 is
impossible while L = 7 and 8 are legal, no monotone "longer ⟹ collision"
argument (section 5's prefix collision theorem) can exist. The group
graph and the legality-filtered graph differ in *both* directions.

**Why Round 25 saw no exceptions.** Its universe was depth ≤ 6 after the
abandonment, and a violating excursion needs L = 7 — there was no room
for one. Round 25's "0 violations in 18,778 edges" was the shadow of the
depth cap, not evidence for the alphabet. Using it to argue the alphabet
would be circular, and the Round 25 documents are corrected accordingly.

**What survives** (unchanged and still hand-proved): the four ell=5
composite generators, `w2:10` → E and `w3:120` → E²; F is always `w3:201`
or `w3:210`; from a port q, `w2:10` lands at q∘E (phase +1); the total
advance 4 (mod 5); phase injectivity; the winding reduction
#Z_{→O*} ≡ k (mod 2). What falls is the step that made k = 0 provable.

**Lemma A, newly hand-proved**: any excursion with L ≥ 2 must begin with
`w3:201` or `w3:210` — an orbit-preserving first edge would land back in
O* immediately, giving L = 1.

**Non-O* separation (kept strictly separate).** Across the 95 O*-landing
completions the aggregate #Z_{→other} is even 95/95, but **5 of 95
completions contain an individual orbit with an ODD zero-charge count**.
So "every non-O* orbit is entered and exited in paired excursions" is
**반증됨**; the aggregate evenness is not per-orbit and has no
explanation.

**Net**: `|P| + #R_{<=C} ≡ 1 (mod 2)` remains 미완료, and the O*
half — which Round 25 had reduced to a single lemma — is now known not to
follow from that lemma, because the lemma is false. One question is left
undecided and is stated exactly: whether a preparation prefix containing
an L ≥ 7 excursion extends to a completed same-component RR word.
Settling it needs a completion search, which this round was told not to
run.

### Round 27 — the preparation parity conjecture is REFUTED by exact witnesses

`src/build_rr_long_excursion_roots.py`, `src/search_rr_long_prefix_extensions.py`,
`src/verify_rr_long_extension_certificate.py` ->
`outputs/rr_long_excursion_prefixes.json`, `outputs/rr_long_prefix_quotient.json`,
`outputs/rr_long_prefix_extension_results.json`,
`outputs/rr_long_prefix_certificates.json`. Five write-ups led by
`research/RR_LONG_EXCURSION_EXTENSION.md`. No global RR search was
restarted — only 28 targeted roots. The N=0 search and checkpoint were
not touched.

**Terminology fixed first (it was a real trap).** Two different things
were called F: `F_def` = `ExactState.F`, the abandonment/defect counter
with `TARGET_F = 1`; `F_sym` = the fresh-orbit-opening event symbol (a Z3
joint), bounded only through `O <= TARGET_O = 25`. Round 26's "#F=4" is
`F_sym = 4` and is **not** a violation of `F_def <= 1`. Verified: all 186
prefixes have `F_def = 1`.

**Corpus and quotient.** Round 26's "38" counts WORDS legal from at least
one root; the unit that has a state is a (word, root ell) PAIR, of which
there are **186**. All 186 are distinct exact states *and* distinct
left-S6 canonical pairs (stabilizer ties all 1), so symmetry buys no
reduction in search roots.

**Hand-proved ledger obstruction removes 158 of 186.** An RR word has
exactly two R events and R2 is the last event, so a prefix lying strictly
before R2 carries at most one R. 106 prefixes already have three R's and
52 have two, leaving **28**. Nothing else in the ledger removes any of
them: Φ ∈ {1..5} all positive, hub touches 0, `O <= 8` against a budget
of 25, `N_def = 1` with exactly one R to spare.

**Target A** was fixed against the project's existing predicate (the one
`analyze_rr_ell0_family.py` uses): the second R event, child state with
`F_def = 1` and `H = 0`, and R2 source and target orbits in the same
component. Targets B (terminal continuation) and C (full NR6 completion)
were not attempted and nothing is claimed about them.

**Result: 6 FOUND, 22 INCOMPLETE, 0 EXHAUSTED_IMPOSSIBLE.** All six
witnesses were independently re-verified by literal edge-by-edge replay
(6/6 agree). The minimal one reaches Target A **two macro-edges** after
the prefix:

```
abandonment ell=4, rot^4;w2:10 -> (orbit 1, phase 0) = O*
prep 0..6 : FFEFEFR   (L=7 excursion, return exponent 3 -- ODD)
prep 7    : rot^5;w2:10  E -> (1,4) hex 0   <- HUB COMPLETER
R2   8    : rot^0;w3:120 R -> (0,2)
```

That is the established terminal normal form exactly — completer landing
on (orbit 1, phase 4) = hex0 position 5, last edge `rot^0;w3:120`,
chaining true, Φ = 0, tail length 0 at ell=4. Only the preparation
differs.

**Four propositions are refuted**, with |P| counted the same way as
`preparation_length` in `outputs/rr_preparation_words.json` (inclusive of
the completer and any tail):

| | historical ell=4 corpus (9 records) | the six witnesses |
|---|---|---|
| \|P\| | 3, 5, 7 — all **odd** | **8**, 11 |
| #R_{<=C} | 1 | 1 |
| (\|P\|+#R) mod 2 | **0** in 9/9 | **1** for the \|P\|=8 pair |
| #Z_{->O*} | even (95/95 observed) | **1 or 3 — all ODD** |

1. **#Z_{->O*} is even — 반증됨.** All six witnesses are odd.
2. **The winding number k = 0 — 반증됨.** The hand-proved reduction
   #Z_{->O*} ≡ k (mod 2) still holds, and now it is the *tool*: #Z odd
   forces k odd, so k ≥ 1.
3. **ell=4 preparation length is odd — 반증됨** by the two \|P\| = 8
   witnesses.
4. **\|P\| + #R_{<=C} invariant — 반증됨.**

**What survives**: every hand proof from Rounds 25–26 is untouched — F
never targets O*, the O* zero-charge events are exactly the E events, the
total advance is 4 (mod 5), phases are not revisited, at most two R steps
target O*, and #Z_{->O*} ≡ k (mod 2). The reduction was correct; the
conclusion drawn from it was not, because the alphabet premise was false.

**Why the earlier observations missed this.** A word containing an L = 7
odd excursion needs at least 9 macro-edges (1 abandonment + 7 excursion +
≥1 to R2), i.e. depth ≥ 8 after the abandonment. Every universe from
Rounds 19–25 was capped at depth 6 (comparison runs 7, one at 8). The
"95/95 even" and "0 violations in 18,778 edges" measurements were
**exactly correct within their scope** and simply could not contain a
counterexample. `research/RR_DEPTH_CAP_ARTIFACTS.md` lists every
observation that was scope-limited in this way.

**Honest limits**: the 22 INCOMPLETE roots were truncated at a node cap
of 8,000 and are **not** evidence of impossibility — `EXHAUSTED_IMPOSSIBLE`
was returned zero times. All six witnesses are at ell=4, consistent with
the established ell dichotomy, and nothing is claimed about ell=0. And
Target B/C remain untouched: these are same-component R2 boundaries, not
full completions. The parity proposition was always evaluated at the R2
boundary (the Round 18 counting-unit standard), so Target A is the right
level for the refutation — but it does not make these into NR6 solutions.

**Net**: the preparation parity conjecture, the target of Rounds 24–27,
is **closed as false**. `#Z_{->other}` evenness remains a separate open
question and is deliberately not combined with this result.

## Open problems (genuinely open, not resolved by this repository)

1. **Closing the 867-872 gap for n=6.** This is the actual research
   question. It is unresolved in the literature available to this
   session, and this repository's naive search tooling is nowhere near
   capable of resolving it computationally (see baseline experiment
   above). Making real progress would require either:
   - reproducing and extending Houston/Pantone/Vatter's actual
     combinatorial lower-bound argument (a genuine, nontrivial piece of
     mathematics -- not something to re-derive casually), or
   - a search with domain-specific pruning far beyond textbook IDA*
     (symmetry reduction across the n=6 permutation group, exploitation of
     the recursive rotation-pass/deep-joint block structure, something
     closer to what Chaffin et al. needed just to close n=5).
2. Whether the specific `NR6` assumption described in the original prompt
   (that a minimal n=6 superpermutation is expressible as a
   non-repeating walk visiting all 720 permutations exactly once) is even
   true is, per that same prompt, a separate open question — not
   addressed here.
3. Producing and independently verifying an actual 872-length n=6 string
   would at least pin down the upper bound side concretely; this
   repository does not have one to check.
4. Whether the F=1,H=0,N=2 slab's J-branch (or U-branch) can complete to a
   full walk — see "J-branch findings" above and `research/N2_CLOSURE_STRATEGY.md`.
   The overall conditional `L_6>=872` remains open regardless.

## How to run everything

```
python -m unittest discover -s tests -v   # 14 tests, ~0.4s
python -m src.lower_bound                 # prints the bound table
python -m src.construct                   # builds + verifies greedy witnesses n=1..6
python -m src.exact_solve                 # proves L(2), L(3) from scratch
python -m experiments.n6_search_baseline  # honest, inconclusive n=6 attempt
```
