# Short-5 frontier analysis (Claude, analyst role — no new search)

## 0. Role and scope

This document is written under a role assignment separate from the numbered
"Round" directives that precede it: Codex is running exact traversal on the
five short roots (`short_ell0`..`short_ell4`). This document does **not**
run any new large search, does **not** duplicate that traversal, does
**not** edit any Codex certificate, and does **not** claim exhaustion of
any search space. Every finding below is read directly off data that
already exists in this repository — the Round 36 coverage checkpoints
(`outputs/rr_target_a_checkpoints/short_ell{0..4}.json`, 140–165 MB each,
gitignored, one per root) and the Round 37/38 ledgers
(`outputs/rr_root_capacity_envelopes.json`,
`outputs/rr_short_root_ledger.json`,
`outputs/rr_short_root_defect_bounds.json`,
`outputs/rr_short_root_resource_results.json`) — plus direct reading of
`src/search_rr_target_a_unified.py`, the engine that produced those
checkpoints.

**Label vocabulary used throughout, per the assigning instruction:**

- `CLAUDE_OBSERVATION` — a fact read directly off existing data or code,
  no new claim about the underlying combinatorial problem.
- `CLAUDE_PROPOSAL` — a suggested change (to a future traversal, not to
  anything in this repository), not yet justified.
- `CLAUDE_HAND_PROOF` — a short proof sketch establishing a proposal's
  soundness/completeness, offered in place of running code.

The single most load-bearing finding in this document is in §5 — read
that section first if short on time.

## 1. Root geometry — `CLAUDE_OBSERVATION`

All five short roots are built identically: `ell` (0..4) literal `w1`
(pure rotation) steps from the true initial state, followed by one
`w2:10` abandonment joint (`literal_root = ["rot^0;w2:10"]` after the
prefix). Reading `outputs/rr_short_root_ledger.json`:

| root | `P` | `O` | `Ndef` | `M=P-5O` | `Phi` (root) | hub-hex popcount (root) | # legal first macro edges |
|---|---|---|---|---|---|---|---|
| `short_ell0` | 2 | 2 | 0 | -8 | 1 | 1 | 4 |
| `short_ell1` | 2 | 2 | 0 | -8 | 2 | 2 | 4 |
| `short_ell2` | 2 | 2 | 0 | -8 | 3 | 3 | 4 |
| `short_ell3` | 2 | 2 | 0 | -8 | 4 | 4 | 4 |
| `short_ell4` | 2 | 2 | 0 | -8 | 5 | 5 | 4 |

Two exact patterns, both simple arithmetic consequences of the
construction (not new theorems, just read off the identity already in
`audit_rr_capacity_helpers.py`'s `phi = lambda st: 5 + 6*(TARGET_P-P) -
(720-visited_count)`):

- **`Phi(root) = ell + 1` exactly.** Each extra `w1` prefix step visits one
  more permutation of the *same* (hub) hexagon before the first joint
  fires, so `P` is unchanged (`P=2` at all five roots) while
  `visited_count` increases by exactly 1 per `ell`, and `Phi` increases by
  exactly 1 per unit of `visited_count` at fixed `P`.
- **`hub_residual_popcount(root) = ell + 1` exactly**, for the identical
  reason: the extra rotations are literally extra slots of the hub hexagon
  being touched before abandonment.

`P`, `O`, `Ndef`, `M`, `O_cap` (23), `R_cap` (3), and the **set** of 4
legal first macro edges (`rot^5;w2:10`, `rot^5;w3:120`, `rot^5;w3:201`,
`rot^5;w3:210`) are identical, token-for-token, across all five roots. The
only differences are `ell` itself, `Phi`/hub-popcount (both `=ell+1`, so
not independent information), and the raw/canonical state hashes, which
are pairwise distinct at all five roots (`outputs/rr_short_root_ledger.json`:
`"distinct_canonical_decorated_hashes": 5`). Round 38 already recorded
that these five are **not** merged on resource signature despite sharing
one — that decision is corroborated here, not revisited.

## 2. Frontier structure — `CLAUDE_OBSERVATION`

Every one of the five Round 36 checkpoint files records a `Q1`-mode,
coverage=True run that stopped at `INCOMPLETE_TIMEOUT` (90 s budget, none
finished inside it):

| root | expanded | generated | queued frontier at stop | wall seconds | depths present in frontier |
|---|---|---|---|---|---|
| `short_ell0` | 70,999 | 1,516,030 | 120,103 | 100.36 | **{11, 12}** |
| `short_ell1` | 80,000 | 1,703,209 | 134,378 | 112.86 | **{11, 12}** |
| `short_ell2` | 80,000 | 1,702,942 | 134,275 | 107.52 | **{11, 12}** |
| `short_ell3` | 80,000 | 1,702,151 | 133,889 | 105.68 | **{11, 12}** |
| `short_ell4` | 80,000 | 1,700,998 | 133,668 | 103.23 | **{11, 12}** |

Every frontier entry, at all five roots, without exception, sits at depth
11 or 12 — there is no depth-13+ material anywhere in these checkpoints.
`found_boundary_count: 0` at all five (no hits). `duplicate_state_merges`
is tiny (37–43 out of >1.5M generated edges per root), so the ~120K–134K
distinct depth-11/12 frontier states are not an artifact of merge
under-counting — the branching factor genuinely is that large this
shallow. `depth_ceiling_dropped_nodes: 0` everywhere (no depth cap was
set; the stop is purely a wall-clock timeout, confirmed by
`stop_reason: INCOMPLETE_TIMEOUT` and `frontier_emptied_naturally: false`
in `outputs/rr_target_a_resumed_frontiers.json`).

## 3. Prune histograms — `CLAUDE_OBSERVATION`

Exactly three prune reasons ever fire, at all five roots, out of the four
Q1-safe reasons defined in `search_rr_target_a_unified.py`'s
`Q1_SAFE_REASONS` (`F_exceeded`, `H_positive`, `N_exceeded_monotone`,
`F1_fragment_normal_form_impossible`) plus the two non-`area_a_prune_reason`
Q1-safe reasons (`outside_RR_alphabet`, `R_event_not_eligible_r_count`):

| root | `F_exceeded` | `outside_RR_alphabet` | `R_event_not_eligible_r_count` | `H_positive` | `N_exceeded_monotone` | `F1_fragment_normal_form_impossible` |
|---|---|---|---|---|---|---|
| `short_ell0` | 303,133 (20.0%) | 952,209 (62.8%) | 69,550 (4.6%) | 0 | 0 | 0 |
| `short_ell1` | 340,110 (20.0%) | 1,070,482 (62.9%) | 78,200 (4.6%) | 0 | 0 | 0 |
| `short_ell2` | 340,432 (20.0%) | 1,070,065 (62.8%) | 78,129 (4.6%) | 0 | 0 | 0 |
| `short_ell3` | 340,356 (20.0%) | 1,069,795 (62.8%) | 78,069 (4.6%) | 0 | 0 | 0 |
| `short_ell4` | 341,292 (20.1%) | 1,068,226 (62.8%) | 77,770 (4.6%) | 0 | 0 | 0 |

(Percentages are of `generated`, not `expanded`.) The remaining ≈12.6% of
generated edges become legal survivors (added to the frontier, modulo the
tiny duplicate-merge count) — consistent arithmetic check:
`expanded + queued_frontier_at_stop` ≈ `generated − (F_exceeded +
outside_RR_alphabet + R_event_not_eligible_r_count) − duplicate_state_merges`
at every root (verified for `short_ell0`: `70999+120103=191102` vs.
`1516030−303133−952209−69550−37=191101`, off by exactly 1, the root node
itself).

**`H_positive`, `N_exceeded_monotone`, and
`F1_fragment_normal_form_impossible` never fire, at any of the five
roots, at any point in the explored region.** This is not incidental — see
§5: since `Ndef` only ever increases on an `R`-kind edge (Round 37's
conservation law: `dNdef=+1` for `R`, `0` for `Z2`/`Z3`), and §5 shows no
`R`-kind edge is ever added to the frontier from these roots, `Ndef`
stays pinned at its root value (`0`) throughout **all** 120K–134K frontier
states at all five roots. `N_exceeded_monotone` (`Ndef>3`) therefore
cannot possibly fire in this data — its zero count is a direct corollary
of §5, not new information.

## 4. Recurring dead-end motif — `CLAUDE_OBSERVATION`

There is exactly one dead-end motif in this data, and it accounts for
100% of the pruning that touches R-type edges: every `R`-kind macro edge
generated from an `r_count=0` state is classified
`R_event_not_eligible_r_count` (69,550–78,200 occurrences per root, §3),
because `is_target_a_edge` (line 337 of `search_rr_target_a_unified.py`)
returns `None` whenever `r_count_before != 1` — by Target A's own
definition, only the *second* R event can be a boundary. No other dead-end
pattern (e.g. a specific hexagon geometry, a specific orbit-reuse pattern)
appears anywhere in the prune histogram — `F_exceeded` and
`outside_RR_alphabet` are generic, definition-level filters unrelated to
root-specific geometry. See §5 for why this single motif is actually a
traversal-completeness gap, not a combinatorial fact about the roots.

## 5. First unavoidable defect — `CLAUDE_OBSERVATION` (the headline finding)

**Every one of the 120,103–134,378 frontier states at all five roots has
`r_count = 0`.** Not "mostly" — literally 100%, verified directly:

```
short_ell0: n=120103  r_count={0: 120103}
short_ell1: n=134378  r_count={0: 134378}
short_ell2: n=134275  r_count={0: 134275}
short_ell3: n=133889  r_count={0: 133889}
short_ell4: n=133668  r_count={0: 133668}
```

Reading `search_rr_target_a_unified.py` lines 445–469 explains why, and it
is **not** a timeout artifact:

```python
for edge in sorted_macro_edges(state):
    ...
    if k == "R":
        v = is_target_a_edge(edge, r_count)
        ...
        continue  # never expand past an R event (2nd R must be the boundary)
    nr = r_count + (1 if k == "R" else 0)
    ...
    frontier.append((tr.state, nr, depth + 1, ...))
```

**Every `R`-kind macro edge is unconditionally `continue`d — its child
state is never appended to the frontier, regardless of `r_count_before`.**
This is stated as intentional design ("never expand past an R event") and
it is *correct* for the 28 long-excursion roots, whose root already
carries `r_count=1`: from there, Target A requires exactly one more R
event (`k=1`), and that R event, wherever it occurs, is fully decided by
`is_target_a_edge` on the spot — there is nothing to gain by continuing
past it, since a third R is already proven impossible
(`r_count_exceeded`'s own docstring: *"the root already carries one R, and
the second is the R2 boundary itself"* — a premise that is explicitly
about long-excursion roots).

**That premise is false for the five short roots.** Their root has
`r_count=0`; Target A requires `k=2` R events from there (already recorded
in `analyze_rr_root_capacity_envelopes.py`'s own `envelope_for_root`: `k =
1 if root_r_count == 1 else 2`). The *first* of those two R events must
transition `r_count` from 0 to 1 and then **continue** — only from an
`r_count=1` state can the *second* R event be recognized as a boundary at
all (`is_target_a_edge` requires `r_count_before == 1` exactly). Because
line 469 discards every R-transition's child unconditionally, **this
traversal can never produce an `r_count=1` state from a short root, at any
depth, regardless of how long it runs.** The `r_count=1` subspace — the
only place a Target A boundary can live, for these five roots specifically
— is not merely unexplored in this 90-second budget; it is structurally
unreachable by this code path, full stop. The empirical 100%-at-`r_count=0`
result above is the direct, exact signature of that gap, not evidence that
boundaries are rare or deep.

**This is a completeness gap, not a soundness bug.** Nothing in the
Round 36 checkpoints is incorrectly *reported* — `found_boundary_count: 0`
with `status: INCOMPLETE_TIMEOUT` is literally true of what this traversal
explored. But because of the gap above, that `0` carries no information
about whether a Target A boundary exists at any of the five short roots:
the region where one could exist was never entered.

**Consequence for Codex's exact traversal (stated as an observation about
requirements, not an instruction):** if Codex's traversal reuses this
engine's R-edge handling as-is, it will inherit the identical gap and can
never find a Target A boundary at a short root, however long it runs. If
Codex's traversal is independently designed to continue through the first
R event for `r_count=0` roots, this paragraph does not apply to it — this
document has no visibility into Codex's implementation and makes no claim
about it either way. See §9 for a proposed fix, offered only as a
proposal with a hand-argument, per the assigning instruction — not
implemented here.

## 6. CH1/CH2 distribution — `CLAUDE_OBSERVATION`

**Cannot be observed from this data.** CH1 (the hub completer edge C is
itself the first R event) vs. CH2 (C is a Z2 and R1 happened earlier) is a
question about ordering relative to the *first* R event. Since §5 shows
`r_count` never leaves 0 anywhere in these checkpoints, no frontier state
has taken an R event yet, and the CH1/CH2 branch is undetermined at every
single one of the 120K–134K frontier states — 0% resolved either way, not
because the branch is balanced but because it is entirely unreached. This
matches (and does not update) Round 35/36's existing note that the branch
is undetermined at a root while the hub hexagon is incomplete — except
here the branch is undetermined for a stronger reason: no R event of any
kind has occurred in the explored region at all.

## 7. Hub/completer timing — `CLAUDE_OBSERVATION`

Even though CH1/CH2 cannot be resolved (§6), the hub hexagon's *occupancy*
can still be tracked, since hub-touching does not require an R event. An
8,000-state random sample of `short_ell0`'s frontier (seed fixed for
reproducibility) gives:

| hub-hexagon popcount | count (of 8000) |
|---|---|
| 1 (root value, untouched since) | 7,348 (91.9%) |
| 2 | 207 |
| 3 | 57 |
| 4 | 77 |
| 5 | 145 |
| 6 (**fully complete**) | 166 (2.1%) |

**The hub hexagon can reach full completion (popcount 6) purely through
`Z2`/`Z3` preserving/opening moves, with no R event at all**, in about 2%
of the sampled depth-11/12 frontier. A concrete single-path trajectory
(replayed from the `short_ell0` root, one arbitrary depth-12 frontier
member) shows this happening as early as the walk's second macro edge:

```
root                  P=2  O=2  hubpc=1
rot^5;w2:10           P=3  O=2  hubpc=1
rot^5;w2:10           P=4  O=2  hubpc=1
rot^5;w2:10           P=5  O=2  hubpc=1
rot^5;w2:10           P=6  O=2  hubpc=2
rot^4;w3:201          P=7  O=3  hubpc=6   <- hub hexagon fully completed here
rot^5;w2:10           P=8  O=3  hubpc=6
...
```

So "hub completion" and "R-event timing" are not coupled the way the hub
completer's *eventual* role (CH1 vs. CH2) might suggest — the hexagon can
fill up long before any R event is even attempted. What determines CH1 vs.
CH2 is which specific edge later serves as the completer, not whether the
hexagon is full; this data says nothing about that assignment (§6).

## 8. Phi and M trajectories — `CLAUDE_OBSERVATION`

Using the same replayed path as §7 (all values exact, engine-computed, not
estimated):

```
label                 P   O  Ndef    M=P-5O  Phi  hubpc  visited
root                   2   2   0       -8      1    1      2
rot^5;w2:10            3   2   0       -7      1    1      8
rot^5;w2:10            4   2   0       -6      1    1     14
rot^5;w2:10            5   2   0       -5      1    1     20
rot^5;w2:10            6   2   0       -4      1    2     26
rot^4;w3:201           7   3   0       -8      0    6     31
rot^5;w2:10            8   3   0       -7      0    6     37
rot^5;w2:10            9   3   0       -6      0    6     43
rot^5;w2:10           10   3   0       -5      0    6     49
rot^5;w2:10           11   3   0       -4      0    6     55
rot^5;w3:201          12   4   0       -8      0    6     61
rot^5;w2:10           13   4   0       -7      0    6     67
rot^5;w3:201          14   5   0      -11      0    6     73
```

Two things confirmed directly against the engine, both already proven
theorems from earlier rounds (this is corroboration, not a new claim):

- **`M` moves by exactly `+1` on every `Z2` (`w2`) edge and exactly `-4`
  on every `Z3` (`w3`) edge** — the Round 37 conservation law, visible
  step by step above. `Ndef` never moves (stays 0 throughout, consistent
  with §3/§5: no R edge is ever taken in this traversal).
- **`Phi` is flat across every `rot^5` macro edge and drops by exactly
  `(ell_run − 5)` on any macro edge whose rotation run is shorter than 5**
  (here: `rot^4;w3:201` drops Phi from 1 to 0). This matches the sawtooth
  behavior already proven in `research/SHORTFALL_BUDGET_THEOREM.md` §2
  (`c(t) = 5 − ell(t)`, `Phi` rises by 1 per literal rotation and drops by
  `c(t)` at each joint) — cited here, not re-derived. Once `Phi` reaches 0
  it stays at 0 for the remainder of this particular path, consistent
  with the existing "Phi=0 forces ell=5" note (every subsequent edge in
  this trace is indeed `rot^5`).

No path in this data was observed to make `Phi` negative in a way that
contradicts the engine's own `remaining_window_capacity_prune`; the
population-level `Phi` histogram in §S1 below (sampled) shows a small tail
of negative `Phi` states surviving in the Q1 frontier, which is expected
and correct — that prune is Q2-only (not in `Q1_SAFE_REASONS`), so
Q1-mode is supposed to keep exploring states a Q2 (completion-aware)
search would already have cut.

**§S1 — sampled aggregate (`short_ell0`, n=8000):** `Phi` distribution
`{-9:1, -7:1, -4:170, -3:55, -2:77, -1:144, 0:166, 1:7386}` — i.e. 92.3%
of the sample still sits at the root's own `Phi=1`, 2.1% at `Phi=0`
(matching the hub-complete count in §7 — every `Phi=0` state in this
sample also has `hubpc=6`, consistent with `rot^4` runs being what both
drops `Phi` and (in this construction) tends to complete the hub), and a
small tail (0.4%) at negative `Phi`, correctly retained by Q1-mode.

## 9. A proposal for the traversal gap — `CLAUDE_PROPOSAL` + `CLAUDE_HAND_PROOF`

**`CLAUDE_PROPOSAL`:** if a future short-root traversal needs to actually
reach a Target A boundary (as opposed to re-confirming §5's gap), it
should treat an `R`-kind edge from an `r_count_before == 0` state as a
normal continuable transition — append `(child_state, r_count=1, ...)` to
the frontier, subject to the same `q1_safe_prune_reason` filter Z2/Z3
children already receive — rather than unconditionally discarding it. An
`R`-kind edge from `r_count_before == 1` should keep its current terminal
treatment unchanged (checked via `is_target_a_edge`, never expanded
further). This is not a new *prune* — it does not shrink anything — it
restores reachability of a subspace the current code cannot enter at all.
It is offered here only as a proposal; it changes no file in this
repository and is Codex's call, not this document's, whether to use it.

**`CLAUDE_HAND_PROOF` (soundness/completeness of the proposal):**

Claim: appending the `r_count: 0→1` transition for `R`-kind edges (i) does
not introduce any false positive, and (ii) removes the specific gap in
§5.

1. **No false positive.** The recognizer itself
   (`is_target_a_edge`) is untouched by the proposal: a state is only ever
   reported as `found_boundary_count`/`hits` when `F_def==1`, `H==0`,
   same-component *and* `r_count_before == 1` exactly. The proposal adds a
   traversal edge, not a new acceptance condition, so it cannot manufacture
   a hit that the existing recognizer would reject.
2. **No unsound prune reuse.** The four Q1-safe reasons
   (`F_exceeded`, `H_positive`, `N_exceeded_monotone`,
   `F1_fragment_normal_form_impossible`, see `PRUNE_CLASSIFICATION`) are
   each proven monotone by an argument over `dF`, `dH`, `dNdef` that does
   not mention which macro-edge *kind* produced the child — the proofs
   hold for any child state regardless of whether it came from a `Z2`,
   `Z3`, or (now) `R` edge. Applying the same filter to the one newly
   continuable `R` child is therefore licensed by the existing proofs, not
   a new assumption.
3. **No infinite regress / no third R.** `r_count_exceeded(nr) = nr > 2`
   already fires on any attempt to reach `r_count=3`; this check is
   evaluated for `R`-kind edges under the proposal exactly as it already
   is for `Z2`/`Z3` edges reaching `nr`, so a third R event remains
   pruned exactly as it is today. The proposal only ever adds the single
   missing `r_count: 0→1` transition, never more.
4. **Removes the §5 gap.** By Round 33/35's own already-established fact
   (restated in `r_count_exceeded`'s docstring) an RR word has at most two
   R events, so for a short root (`root_r_count=0`) a Target A boundary,
   if one exists, is necessarily preceded by exactly one prior R event.
   Since (1)-(3) show the newly added transition is sound and the only
   change made, the `r_count=1` subspace — previously provably
   unreachable — becomes reachable, and only that subspace, closing
   exactly the gap identified in §5 and no more.

This is a proof sketch about an unimplemented proposal, not a claim about
this repository's existing certificates, and it does not, by itself,
establish that a Target A boundary exists at any short root — only that a
traversal built this way would be capable of finding one if it does.

## 10. What this document does not claim

- It does not claim any of the five short roots is `EXHAUSTED_NO_TARGET_A`,
  `STRUCTURAL_SURVIVOR`, or any other terminal classification — Round 38's
  `STRUCTURAL_SURVIVOR` verdict (`outputs/rr_short_root_resource_results.json`)
  is unchanged and untouched by this document.
- It does not claim the `r_count=1` subspace is empty of Target A
  boundaries, nor that it contains one — §5 establishes only that the
  existing checkpoints carry zero information about that subspace either
  way.
- It does not run, resume, or checkpoint any search. Every number above
  is read from files that already existed before this document was
  written.
- It does not edit `outputs/rr_target_a_checkpoints/*.json`,
  `outputs/rr_short_root_ledger.json`,
  `outputs/rr_short_root_resource_results.json`, or any other file
  produced by a prior round or by Codex.
- §9's proposal is not implemented anywhere in this repository as of this
  document.
