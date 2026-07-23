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
