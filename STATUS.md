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
