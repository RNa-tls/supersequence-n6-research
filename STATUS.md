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
