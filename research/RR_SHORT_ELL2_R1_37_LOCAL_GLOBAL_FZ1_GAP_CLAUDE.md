# Why local FZ1 possibility can coexist with zero exact FZ1: a formal account

## 0. Verification status

**No "Stage D" branch, commit, or file exists anywhere this session
can reach** — confirmed by `git fetch --all --prune`, `git remote show
origin`, and a repository-wide search. Every specific figure in this
round's report (84 starts, 1,318,577 states, 800,516 Z3 transitions,
4/6 seeds exhausted, `seed_3`/`seed_6` capped, 69,369 remaining
frontier) is asserted in the prompt only and is not used as fact
below. Every task in this round is a formal derivation, independent of
these specific figures, building on the already-verified two-rounds-ago
table computation (20 candidate orbits, 5 hub-touching, 144-regular
adjacency).

## 1. Formal local-vs-global distinction

**Four precise definitions, forming the requested implication chain.**

- **Locally admissible FZ1 geometry**: a pair `(q, p)` — candidate
  orbit `q`, phase `p` — such that `HEX_POSITION[perm]` for the unique
  permutation at `ORBIT_PHASE^-1(q,p)` lands on a hexagon already in
  `C_R1`'s registered set. **A pure fact about the fixed global
  tables**, computed once, requiring no state, no walk, no history.
- **Exact-state-realizability**: there exists *some* self-consistent
  hypothetical `ExactState` (satisfying `ExactState.__post_init__`'s
  own invariants — valid mask lengths, current position marked
  visited, etc.) in which `C_R1`'s admission territory is registered,
  orbit `q` is fresh (`om[q]==0`), and the current position is
  positioned to reach `(q,p)`. **A consistency question about the
  bookkeeping structure**, not a question about whether any real walk
  produces it.
- **Branch reachability**: there exists an *actual* sequence of legal
  moves, starting from `short_ell2_r1_37`'s own specific root and `R1`
  admission (established several rounds ago), that reaches a state
  satisfying exact-state-realizability, remaining legal at every step
  (`F<=1` forced-move constraint, `NR6` collision-freedom, hub-touch
  budget, `R`-budget). **A dynamical question about this one branch's
  actual literal history.**
- **Provenance realizability**: branch reachability *plus* the moment
  of arrival also satisfies whatever bookkeeping `target_a_recognizer`
  will eventually need (`hub_touch_count<=2`, `r_count` still `1`,
  etc.) — i.e., reachability that remains *useful*, not merely
  reachability of the bare geometric configuration.

**The requested chain, mapped precisely**: `local geometry → exact
state → reachable exact state → FZ1`. Three arrows:

- **Arrow 1 (local geometry → exact state)**: this arrow is **not the
  likely failure point**. `ExactState`'s own validation constraints are
  weak (mask-length, "current position visited," non-negative masks) —
  almost any locally-admissible geometry can be embedded in *some*
  self-consistent hypothetical state, since the invariants checked by
  `__post_init__` do not encode anything about *how* a state was
  reached, only that it is internally well-formed. This arrow is
  plausibly close to always holding.
- **Arrow 2 (exact state → reachable exact state)**: **this is the
  most likely locus of the observed gap.** This is the only arrow that
  depends on `short_ell2_r1_37`'s own *specific*, largely forced (`F<=1`)
  literal history — which orbits get opened, in which order, at which
  forced points. A self-consistent hypothetical state is not
  automatically reached by the branch's actual, heavily constrained
  walk: at each forced position, the specific weight-2/3 targets
  legally available are *determined* by the current literal
  permutation, not freely chosen among the 20 table-level candidates.
  Whether any of the 20 orbits ever happens to be the forced target,
  at exactly the qualifying phase, is a fact about the specific
  sequence of permutations this branch's rotation runs actually visit
  — not answerable from the fixed tables alone, and apparently (if this
  round's report is accurate) not yet realized across a very large
  explored space.
- **Arrow 3 (reachable state → FZ1 fires)**: a smaller, "last-mile"
  gap — even having reached the right position, the *specific*
  permutation-window at the target hexagon (not just the hexagon in
  the coarser `orbit_masks` sense) must be `NR6`-unvisited (condition
  D1, established four rounds ago). Plausibly minor relative to Arrow
  2, since by the time a state satisfying Arrow 2 is reached, most of
  the structural work is already done.

**Conclusion**: the missing implication most likely responsible for
the observed zero is **Arrow 2** — table-level possibility says nothing
about whether this one branch's own, largely forced, literal
trajectory ever actually visits one of the 20 qualifying
configurations. This is not a weakness in the table computation; it is
exactly the boundary between combinatorics and dynamics.

## 2. The 20 candidate orbits, symbolically

Recomputed at full phase-level precision (not just "which orbit," but
exactly which phase of it):

| C_R1 hexagon | attaching orbits (orbit, required phase) |
|---|---|
| 40 | `(36,3)`, `(40,0)`, `(41,4)`, `(42,2)`, `(126,2)` |
| 82 | `(42,1)`, `(78,3)`, `(82,0)`, `(83,4)`, `(128,2)` |
| 90 | `(72,2)`, `(90,0)`, `(93,3)`, `(96,1)`, `(120,3)` |
| 91 | `(74,2)`, `(90,4)`, `(95,3)`, `(98,1)`, `(126,3)` |
| 92 | `(78,2)`, `(92,0)`, `(93,4)`, `(102,1)`, `(129,2)` |

**A clean regularity, not previously noted**: each of orbit 91's own 5
hexagons has *exactly* 5 attaching candidate orbits — a uniform
`5x5=25` structure (accounting for the 5 orbits — `42, 78, 90, 93,
126` — that each appear twice, at two different qualifying phases,
against different hexagons, giving `15 + 5x2 = 25` total `(orbit,
phase)` pairs across 20 distinct orbits).

**Required source-state relation**: for each pair, the move firing
must be the specific weight-3 indecomposable tail connecting whatever
permutation the walk currently occupies to the target permutation —
this is a fact about the engine's `ALL_MOVES` table (550 total moves
across weights 1-5) not further decomposed here; it is *not* free
choice among the 20, but determined by which single weight-3 move (if
any) is legal from the current literal position.

**Required registration ordering — the key mechanistic finding of this
section**: for orbit `q` to serve as a *direct* FZ1 witness (a `Z3`
event), its **very first-ever touch** must land exactly on the
qualifying phase. If `q`'s first touch lands on any *other* phase
first (a legitimate `Z3` in its own right, just not FZ1), direct FZ1
for `q` is permanently foreclosed. **A second, delayed route remains
open in principle**: reaching the qualifying phase later via a `Z2`
move fired *while the walk remains continuously resident within `q`*
— since departing `q` (to any other orbit) and later returning would
require an `R`-kind re-entry, which consumes the sole remaining
`R`-budget slot and becomes `R2` itself (terminal, evaluated
immediately, never an intermediate step — established four rounds
ago). **Whether component change requires one or multiple prior
structural events, therefore, has an exact answer**: either exactly
one event (`q`'s first touch is itself the qualifying phase) or exactly
two, with the second constrained to an uninterrupted `Z2` continuation
of the first.

**Grouping into obstruction families** (by which C_R1 hexagon is the
attachment point, the only grouping this data actually supports without
inferring unproven continuation equivalence, per the task's
instruction): the 5 groups shown in the table above. **No claim is made
that these groups behave identically** — they share only their
attachment target, not any proven equivalence of reachability.

## 3. The 5 hub-touching orbits — a derived forbidden-pattern lemma

For all 5 (`96, 120, 126, 128, 129`), computed directly: the
`C_R1`-qualifying phase and the hub-qualifying phase are **never the
same phase**, for any of the 5 (necessarily true, since one phase maps
to exactly one hexagon, and the two hexagon sets are disjoint by
construction).

| orbit | `C_R1`-side (phase, hex) | hub-side (phase, hex) |
|---|---|---|
| 96 | `(1, 90)` | `(0, 96)` |
| 120 | `(3, 90)` | `(0, 0)`, `(4, 96)` |
| 126 | `(2, 40)`, `(3, 91)` | `(0, 6)` |
| 128 | `(2, 82)` | `(0, 8)` |
| 129 | `(2, 92)` | `(0, 9)`, `(4, 24)` |

**Derived lemma (proved, not merely observed)**:

> For any `q ∈ {96,120,126,128,129}`, realizing the two-edge pattern
> `C_R1 → q → C_H` requires visiting two structurally distinct phases
> of `q`. The second of the two touches must be a `Z2` move fired
> while the walk is continuously resident within `q` since it was
> opened — any departure forces the only remaining route back to be an
> `R`-kind re-entry, which is `R2` itself and therefore evaluated as
> terminal (win-or-lose) rather than as an intermediate bridging step.

**A further consequence, checked explicitly rather than assumed**:
this rules out a tempting shortcut — that `R2` itself, by re-entering
one of these 5 orbits at its hub-touching phase, could *simultaneously*
create and benefit from the merge. It cannot: `target_a_recognizer`'s
`same_component` check is computed from the incidence forest *before*
the `R2` transition fires (established four rounds ago), so the merge
must already exist prior to `R2`, never as a byproduct of it. This
confirms, rather than merely assumes, the entire multi-round framing
that the bridge must occur strictly pre-`R2`.

**No cyclic precedence constraint was found this round** (see section
6) — the lemma above is a genuine, proved *sequential* necessity, not
a contradiction. It substantially narrows what any witness at one of
these 5 orbits would have to look like, without proving impossibility.

## 4. Revisiting the 144-Z3 bound — a self-correction

**The task's challenge is well-founded, and on rigorous re-examination,
part of the earlier reasoning needs explicit correction.**

Two rounds ago, this analyst cited "`(720-visited)` decreases by
exactly 6 per move" as grounding for a bound, attributing it to Round
54's own report ("every one of the 64 distinct replayed parent edges
adds exactly six previously unvisited windows"). **On rechecking this
round: that figure was Round 54's own *empirical* finding on one
specific 64-edge sample of one branch's ancestry — not a first-
principles derivation this analyst performed, and not something
re-verified independently this session.** Re-deriving from
`extend()`'s own mechanics directly: each individual call advances
`visited_count` by exactly **1** window (one target permutation
registered), regardless of the firing move's *weight* — weight governs
`F`/`S`/`H` deltas, not window count. A "macro edge" of rotation length
`ell` plus one terminal joint therefore visits `ell + 1` windows, a
quantity that varies with `ell` (itself state-dependent, via the
forced-move constraint) — **there is no general reason for this to
equal 6 uniformly**, and the three-rounds-ago branching-spine
reconstruction already recorded rotation lengths of 0, 1, 2, and 3 at
different points on these very branches, contradicting a universal
"`ell`+1=6" reading. **The "+6 per edge" claim is retracted as a
general law; it stands only as Round 54's own unverified empirical
observation on its own specific sample.**

**What remains valid, on independent grounds, is the orbit-count
pigeonhole**: `Z3` requires a fresh orbit (`om[q]==0`), there are
exactly `ORBIT_COUNT = 144` orbits total (confirmed directly from
`superperm_partial_f1.py`), and a used orbit can never become fresh
again. **This bound is sound and needs no window-counting mechanism at
all.** But the task's challenge exposes a real gap in how it was
previously framed: **"at most 144 `Z3` events" bounds the *count* of
`Z3`-type events, not the *number of moves of any kind* (rotation,
`Z2`, `R`, or rejected collision attempts) that may occur before the
144th (or any specific) `Z3` fires.** Between successive `Z3`s,
arbitrarily many `Z2`/rotation moves — and, separately, arbitrarily
many *rejected* collision attempts, which don't consume any window
budget at all since they never call a successful `extend()` — can
occur.

**Strongest valid replacement, stated as two separate, independently-
grounded bounds, not conflated**:

1. **At most 144 `Z3` events fire in any single branch's history**
   (orbit-pigeonhole, solid, unconditional).
2. **At most `HEX_COUNT x N = 120 x 6 = 720` genuine (successful,
   non-colliding) literal single-window-advancing moves of any kind
   fire in any single branch's history** (window-budget pigeonhole:
   `visited_count` is monotone and bounded above by the fixed total of
   720 windows, and each successful move adds exactly one; both facts
   directly re-derived from `extend()` and `ExactState`'s own source
   this round, not inherited from an empirical citation).
3. **No bound is derived here on the number of *rejected* (colliding)
   candidate attempts** — this is the quantity search-tree "expansion"
   counts actually measure, and it is not controlled by either bound
   above; it can be, and empirically (per prior rounds' pilot data) is,
   very large relative to genuine moves.

**Neither (1) nor (2) says anything about *when* FZ1 occurs relative
to overall search cost** — they bound the *content* of a branch's
literal history, not the *effort* required to discover it. This is the
precise sense in which the original bound, while not false, was
insufficiently qualified.

## 5. Provenance invariant candidates

None of the listed history-sensitive quantities is shown here to
*prevent* attachment of any of the 20 candidates — none of them can be,
without the actual per-branch literal trace this round's data does not
provide. What section 2 *does* establish precisely is which of these
candidates is most directly relevant: **"registered orbit order" and
"phase at first registration," combined**, form exactly the gating
condition derived in section 2 (whether `q`'s first touch lands on the
qualifying phase or not) — the single most load-bearing provenance fact
for this specific question, ranking above the others listed
(`incidence-edge chronology`, `macro suffix class`, `Z2/Z3 count
vector`, `component birth time`) which are either strictly coarser
restatements of the same underlying fact or not directly implicated by
anything derived in sections 1-3.

## 6. Attempt at a forbidden-order theorem

**No cyclic precedence constraint was found.** The candidate shape
("event A must occur before B, but B must occur before A") was
actively sought against section 2/3's own derived ordering requirement
(open `q` at phase `x`, then `Z2`-complete at phase `y` without
departing) — but no *second*, independent constraint forcing the
opposite order was identified from the fixed-table data or the
already-established resource-budget facts (`F<=1`, `hub_touch<=2`,
single remaining `R`). **This is reported honestly as a negative
result of an active search, not a gap left unexamined**: the section
3 lemma is a genuine *sequential* necessity, valuable for narrowing the
witness search, but it is not — on the evidence available this round —
a *contradiction*. Whether some deeper interaction (e.g., between the
forced-move sequence needed to *reach* one of the 20 orbits and the
forced-move sequence needed to later revisit it) produces a genuine
cycle remains open and would require the specific per-branch forced-
move trace, not available this round.

## 7. Theorem ladder, updated

- **L0 — direct Z2 obstruction.** **Proved** (two rounds ago,
  unchanged): orbit 91 alone cannot reach hub directly via `Z2`.
- **L1 — depth-4 FZ1-free.** **Cannot be asserted** — no depth-4 data
  in this session's reach.
- **L1+ — Stage-D 1.3M-state FZ1-free.** **Unverified this round** — no
  branch found. Conditionally, if real, a much larger bounded
  observation than before, still not a proof, and explicitly silent
  on the two still-capped seeds.
- **L2 — candidate-family obstruction.** **Partial progress, not
  complete.** Section 3's forbidden-pattern lemma is a genuine, proved
  *necessary condition* narrowing what a witness at any of the 5
  hub-touching orbits must look like (two distinct phases, second
  reached by uninterrupted `Z2` residency) — this is real structural
  progress toward L2, but it is a *necessary-condition characterization*,
  not an impossibility proof for the family.
- **L3 — provenance impossibility.** **Not established.** Arrow 2
  (section 1) remains the open, unresolved link — no argument here
  shows any of the 20 orbits is dynamically unreachable.
- **L4 — first component-changing Z3 impossible.** **Not provable**
  from anything in this document.
- **L5 — pre-R2 bridge impossible.** **Not provable**; the 5-orbit
  lemma narrows the shape a counterexample would take without ruling
  it out.

## 8. Codex-result interpretation, pre-registered

- **If Codex finds "`C5` states" but no FZ1**: this document does not
  have Codex's own `C0`-`C5` stage definitions on file; interpreted
  generically as "reached a deeper structural checkpoint without a
  witness" — this would extend the bounded-observation base (more of
  the same grade of evidence) without resolving Arrow 2, exactly as
  L1+ above.
- **If all 20 candidates die at `C0`-`C4`**: this would be the single
  most directly relevant possible result to this document — a direct
  empirical test of the section 2/3 predictions. If it means every one
  of the 20 table-level candidates is shown dynamically unreachable up
  to whatever depth `C0`-`C4` represents, that is genuine, targeted
  progress narrowing toward L3 (though still bounded by that depth, not
  a proof of unreachability at all depths).
- **If one exact FZ1 witness appears**: immediately promotes past L2
  for that specific instance; triggers the strict replay checklist
  already established two rounds ago (independently replay; confirm
  section 1's A1-F1 against the replayed state; test whether the
  specific orbit is one of the 5 two-step candidates or a new,
  unidentified path; test whether a later `Z2` reaching a hub hexagon
  is legal from the post-witness state; test `R2`-source admissibility;
  test the full `target_a_recognizer` conditions) — not re-derived in
  full here, referenced from that prior document.
- **If Stage E again finds zero**: incremental strengthening of the
  bounded-evidence base only, same caveats, particularly if it does
  not close the two still-open seeds.
- **If `seed_3`/`seed_6` exhaust**: a genuine, complete closure
  certificate for those two specific subproblems (and, combined with
  the prior round's verified 4/6, potential closure of the whole
  `short_ell2_r1_37` all-13 continuation) — significant for this one
  branch specifically, carrying no implication beyond it for the wider
  top-8 family or the 439-child corpus, exactly as every prior closure
  in this session has been scoped.

## What this document does not do

- Does not verify any Stage-D figure — no branch or file exists to
  check them against.
- Does not claim branch-wide impossibility at any level beyond L0.
- Does not claim to have found a cyclic forbidden-order theorem —
  actively sought, not found, reported as a negative result.
- Retracts, rather than repeats, an earlier over-general citation of a
  "+6 windows per edge" law — replaced with two independently-derived,
  narrower, and correctly-scoped bounds.
- No search run, no Codex artifact modified.

CLAUDE_FZ1_PROVENANCE_THEORY_READY
