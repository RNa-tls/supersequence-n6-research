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
description for this session (frag/rotation-pass decomposition, `F`, `P`,
`S`, `H`, `O` quantities, an `L = 867 + (k+N+H)` coordinate system, claims
of a completed forest-enumeration computation with specific certificate
counts, a partially-run exact-state search with specific node/state counts,
etc.).

**None of that is backed by anything in this repository.** Before this
session, the repository contained a single commit: a one-line README. There
was no code, no checkpoint file, no verifier, nothing that could be
inspected or resumed. Some of the *shape* of that summary is consistent
with real, published techniques for this problem (e.g. superpermutations
genuinely do decompose into rotation-cycle blocks connected by more
expensive transitions — see the recursive construction discussion above,
and Houston's paper). But every *specific numeric claim* in that summary
(326 certificates, 79,683 canonical states, a proven "N-credit forcing"
lemma, etc.) is **unverified** and should not be treated as established
fact. If that work exists somewhere else (a different repo, a different
session's private state), it was not available here, and this repository
does not attempt to reconstruct it from the prose description alone — that
would risk baking speculative/possibly-wrong mathematics in as if it were
checked.

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

## How to run everything

```
python -m unittest discover -s tests -v   # 14 tests, ~0.4s
python -m src.lower_bound                 # prints the bound table
python -m src.construct                   # builds + verifies greedy witnesses n=1..6
python -m src.exact_solve                 # proves L(2), L(3) from scratch
python -m experiments.n6_search_baseline  # honest, inconclusive n=6 attempt
```
