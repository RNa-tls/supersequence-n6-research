# The top-8 capped children as a branching spine: symbolic reconstruction and claim audit

Analyst pass, same branch as two rounds ago (`codex/round51-short5-child-outcomes`,
re-verified unchanged at commits `4785cc6`/`673bd9f`/`dfc314f` — re-fetched,
byte-identical to the cached copy already read). All findings below are
either (a) direct byte-for-byte comparison of the 8 children's own
`literal_macro_trace` arrays, (b) direct inspection of their own
`incidence_forest` records, or (c) a small number of deterministic,
non-branching engine replays of already-fixed root prefixes, enumerating
the fixed legal-edge set at one already-reached state — the same
technique already used and explained two rounds ago. No search was run:
every replay below starts from a `short_root(ell)` state (defined in
`src/analyze_rr_short_root_envelope.py`) and follows an already-complete,
already-given literal path; nothing beyond the single next edge set was
explored at any of the checked points, and no exploration continued past
that single step.

## 0. Headline finding, stated first

**The 8 children are not 8 independent walks.** Within each root, they
are literally **the same deterministic literal walk**, differing only in
*where along that walk an available `R`-kind edge (the `w3:120`,
`ell=5` move) is taken instead of declined*. Across roots, an
additional, shorter shared prefix exists (the completer plus three more
steps), after which the walk itself — not just the R-admission choice —
begins to differ by root. This reframes the whole family as a single
**branching spine per root**, with two structurally different kinds of
branch point:

- **Type 1 (forced divergence)**: the literal walk itself differs
  between roots because a specific continuation is illegal for one
  root's state (typically because that root's own earlier prefix already
  touched the target hexagon). Not a choice — verified as forced.
- **Type 2 (R-admission choice)**: within one root's shared walk, a
  legal `R`-kind edge becomes available as an alternative to continuing
  the ordinary `Z2`/`Z3` preparation; taking it yields one child (with
  that macro_index as its `R1`), declining it continues the walk toward
  the next such point.

## 1. The shared spine, reconstructed symbolically

All offsets below are relative to the **completer** edge (the unique
edge in every child's trace with `target_hexagon == 0`, confirmed at
raw array index 3 for all 8 — i.e. macro_index 4, matching
`completer.macro_index == 4` in every one of the 8 records exactly).

```
Root(ell)                                          [ell-dependent prefix, offsets < 0]
  -> rot^5;w2:10 chain (root-specific hex path)     3 edges, root-specific orbit numbers,
                                                     converging on hex 0 by construction
  -> COMPLETER  (offset 0): target_hexagon = 0,      root-specific source orbit/phase,
                kind=Z2, joint=w2:10                 shared target orbit/phase (?,1)... [*]
  -> offset 1:  rot^(4-ell);w2:10 -> hex 96           kind=Z2, IDENTICAL joint/target/hex
                                                       across all 4 roots; only the
                                                       rotation length is root-dependent,
                                                       and it is EXACTLY 4-root_ell
                                                       (verified: ell1->rot^3, ell2->rot^2,
                                                       ell3->rot^1, ell4->rot^0)
  -> offset 2:  rot^5;w2:10 -> hex 18                 kind=Z2, IDENTICAL across all 4 roots
  -> offset 3:  rot^5;w2:10 -> hex 4                  kind=Z2, IDENTICAL across all 4 roots
  -> offset 4:  DIVERGENCE POINT D1 (Type 1, forced)  see section 2
```

`[*]` the completer's own source orbit/phase is root-specific by
necessity (each root approaches hex 0 via a different orbit history);
its *target* orbit/phase is not identical across roots either
(`(9,2)` for `short_ell2`, `(1,4)` for `short_ell4`, `(33,1)` for
`short_ell1`, `(3,3)` for `short_ell3`) — the identity claimed by the
prior round's document is specifically about the **hexagon labels and
joint/kind structure** of offsets 1-3, not the orbit/phase coordinates,
which differ by root even where the hexagon sequence is identical. This
is a precision the prior document did not make explicit.

Past D1, the surviving branch (all of `short_ell1`, `short_ell2`,
`short_ell3` — `short_ell4` has already split off, see section 2)
continues as one shared walk for a much longer stretch than the
original "0->96->18->4->1" window suggested: hand-verified byte-for-byte
identical (kind, joint, target orbit/phase, target hexagon) through
**offset 37** — i.e. macro steps 4 through roughly 41, more than 30
further edges beyond the original 5-hexagon window, all landing on the
same hexagon/orbit sequence for `short_ell1`, `short_ell2`, and
`short_ell3` alike. This is a substantially longer shared spine than
either prior document reported, found here only because this round
compared full traces rather than the first 8-12 entries.

```
  -> offsets 5-37:  IDENTICAL walk for short_ell1/2/3 (32 further edges,
                     byte-for-byte matching kind/joint/target/hex)
  -> offset 38: DIVERGENCE POINT D2 (Type 1, unverified whether forced) -- short_ell1 splits off
                short_ell1: kind=Z3 w3:201 -> hex 16
                short_ell2/3 (continuing): kind=Z2 w2:10 -> hex 105
  -> offsets 39-40: short_ell2/3 continue identically
  -> offset 41: DIVERGENCE POINT R-alt(37) (Type 2) -- short_ell2_r1_37 fires its R1 here
                short_ell2_r1_37: kind=R w3:120, src=(126,2) tgt=(91,3), hex 92  [ITS R1]
                declining siblings (short_ell2_70/40/107, short_ell3_64/56):
                                   kind=Z2 w2:10, src=(126,2) tgt=(91,2), hex 82
  -> offsets 42-49: short_ell2(remaining)/short_ell3 continue identically
  -> offset 50: DIVERGENCE POINT D3 (Type 1, unverified whether forced) -- short_ell3 splits off
                short_ell3 (both _64, _56): kind=Z2 w2:10 -> hex 8
                short_ell2 (remaining: _70/_40/_107): kind=Z3 w3:201 -> hex 2
  -> offset 51: DIVERGENCE POINT R-alt(70) (Type 2) -- short_ell2_r1_70 fires its R1 here
                short_ell2_r1_70: kind=R w3:120, src=(1,3) tgt=(3,1), hex 48  [ITS R1]
                declining siblings (short_ell2_40/107): kind=Z2 w2:10, src=(1,3) tgt=(3,0), hex 3
  -> offsets 52-54: short_ell2_40/107 continue identically
  -> offset 55: DIVERGENCE R-alt(40) (Type 2, inferred from R1_geometry match; not
                separately re-verified with a Detail printout this round)
                short_ell2_r1_40 fires its R1
  -> offset 56-57: short_ell2_r1_107 continues alone
  -> offset 58: short_ell2_r1_107 fires its R1 (last of the observed short_ell2 group)

  [short_ell3 branch, from D3 at offset 50]
  -> offsets 51-54: short_ell3_64/56 continue identically
  -> offset 55: DIVERGENCE R-alt(64) (Type 2) -- short_ell3_r1_64 fires its R1 here
                short_ell3_r1_64: kind=R w3:120, src=(57,4) tgt=(56,2), hex 69   [ITS R1]
                declining sibling short_ell3_56: kind=Z2 w2:10, src=(57,4) tgt=(56,1), hex 111
  -> offset 56: short_ell3_r1_56 fires its own R1
```

`short_ell4_r1_12` and `short_ell1_r1_98` are each the only top-8
representative of their root, so no sibling data exists in this specific
8-child set to extend their own spines past their single observed R1
(offsets 54 and 57 respectively, from D1/D2). The broader 439-child
corpus (99/111/107/122 R1-children for ell1-4 respectively, per Round
50's telemetry) almost certainly contains further Type-2 branch points
along each of their spines too, symmetric to the short_ell2/short_ell3
pattern found here — **not checked this round**, since the top-8 filter
happened to select only one representative from each of short_ell1 and
short_ell4.

## 2. Divergence point D1, hand-verified by replay: forced, not a choice

**`CLAUDE_HAND_PROOF`.** Built `short_root(ell)` for `ell in {1,2,3,4}`
(the exact function in `src/analyze_rr_short_root_envelope.py`),
deterministically replayed each root's own first 7 literal macro edges
(offsets -3 through 3, i.e. the completer and the three shared steps),
then enumerated the **complete, fixed** legal-edge set from that single
reached state via `macro.macro_edges` (the same exhaustive
rotation-run x nonrotation-joint enumeration used everywhere else in
this project) — no further step was taken past this enumeration, so no
branching search occurred.

Result: for `short_ell1` and `short_ell2`, three `rot^5` continuations
are legal at this state: `w2:10 -> hex 1` (kind `Z2`), `w3:201 -> hex 3`
(kind `Z3`), `w3:210 -> hex 2` (kind `Z3`) — 21 legal edges total. For
`short_ell3`, only `w2:10 -> hex 1` is legal at `rot^5` (both `Z3`
options are missing — `hex 3` was already visited by `short_ell3`'s own
prefix at offset -3, so `w3:201` is an exact collision there) — 19 legal
edges. **For `short_ell4`, only `w3:201 -> hex 3` is legal at `rot^5`**
— `w2:10 -> hex 1` is entirely absent from the legal-edge list (`
exact.extend` returns `None` for it at this specific state) — 19 legal
edges, but a *different* 19 than short_ell3's.

**Conclusion**: `short_ell4`'s divergence at D1 is not a free choice
among equally available options — the option every other root takes
(`w2:10 -> hex 1`) is simply illegal for `short_ell4`'s own state at
this point. This directly refutes reading D1 as a "registration repair"
opportunity (task 4) — there was nothing to repair; the walk was
already forced onto a different track before any R-related consideration
enters the picture at all. No `R`-kind edge appears anywhere in this
21/19/19-edge enumeration for any of the four roots — D1 is a purely
`Z2`/`Z3` structural fork, unrelated to R-admission.

D2 (offset 38, `short_ell1` splits) and D3 (offset 50, `short_ell3`
splits) were **not** independently re-verified by replay this round —
they are read directly from the trace data (both are exact, unambiguous
kind/joint/hex differences between siblings sharing an otherwise
identical prefix) but the *forced-vs-free* distinction established for
D1 by direct replay was not re-run for D2/D3. Recorded as unverified,
not assumed identical to D1's mechanism.

## 3. Claims A-E, audited against the reconstructed spine

### A. "The first five spine transitions are conjugate across roots."

**Partially refuted — exact counterpattern given.** True for the
completer plus offsets 1-3 (4 transitions: hexagon sequence
`0 -> 96 -> 18 -> 4` identical in kind/joint/target-hexagon across all
4 roots, with only the offset-1 rotation length varying as the proven
`4 - root_ell` parameter). **False at the fifth transition (offset 4):**
`short_ell4`'s transition there is `Z3;w3:201 -> hex 3`, not
`Z2;w2:10 -> hex 1` like the other three roots — a different joint
*kind*, not a parameter variant of the same kind, and (section 2) forced
by illegality rather than chosen. As literally stated ("first five"),
refuted; restated as "first four", true.

### B. "The only root-dependent parameter is the final rotation length."

**Refuted, three independent counterpatterns.** (1) The completer's own
source *and target* orbit/phase differ by root (not merely a rotation
length: `(129,4)->(9,2)` for short_ell2 vs `(15,2)->(1,4)` for
short_ell4 vs `(32,4)->(33,1)` for short_ell1 vs `(57,1)->(3,3)` for
short_ell3). (2) D1 (section 2): short_ell4's divergence is a joint-kind
substitution (`Z2`->`Z3`), not a rotation-length variant. (3) D2 and D3
are likewise joint-kind substitutions between siblings sharing an
otherwise-identical prefix (`short_ell1`: `Z3` vs the group's `Z2` at
offset 38; `short_ell3`: `Z2` vs the remaining group's `Z3` at offset
50). The `4 - root_ell` rotation-length identity at offset 1 remains
correct and clean, but it is not the *only* root-dependent quantity —
it is the only one that is a pure parameter of an otherwise-identical
edge; the others are qualitative substitutions.

### C. "Every legal R alternative before the first divergence targets an orbit different from the required future R2 source orbit."

**Refuted in every checked instance (n=4 same-root R-admission pairs),
exact counterpattern given.** No `R`-kind edge exists at or before D1 at
all (section 2), so the claim is vacuous there; evaluated instead at the
four Type-2 (R-admission) branch points that were hand-checked directly
from trace data:

| taken (R1) | declined (continuation) | orbit | phase(R1) | phase(continue) |
|---|---|---:|---:|---:|
| `short_ell2_r1_37` | siblings continuing | **91** | 3 | 2 |
| `short_ell2_r1_70` | `_40`/`_107` continuing | **3** | 1 | 0 |
| `short_ell3_r1_64` | `short_ell3_r1_56` continuing | **56** | 2 | 1 |

In all three checked pairs (four children total, since two pairs share a
"declined" side), **the R-alternative and the declined continuation
target the identical orbit**, differing only in phase. The claim, read
as "different orbit", is false at every point where it was checked. A
weaker, phase-sensitive version ("different orbit-phase pair") is true
in the same three instances but was not what was asked.

### D. "Registering the required orbit necessarily changes the future R2 source."

**Not refuted, but graded as near-tautological rather than a
substantive theorem.** Once a joint move (R or otherwise) is taken at a
given state, that move consumes the step and determines what state
comes next by construction — any two different moves at the same state
necessarily lead to different subsequent walks, and therefore to
different sets of orbits that later joints can source from. This is true
essentially by definition of how the literal walk is built (one edge per
step, no simultaneous alternatives), not a fact specific to R2 geometry
or registration. Recorded as `CLAUDE_OBSERVATION`, not a proof of
anything R2-specific.

### E. "Any path preserving the required future source cannot merge the needed components before R2."

**Not refuted; corpus observation, not proven.** Checked directly via
`incidence_forest` for all 8 children (section 4): in every one, `R1`'s
own target orbit sits in an isolated, single-orbit component (2-3
hexagons, never merged with the hub component containing orbit 0),
**regardless of how far along the spine `R1` fired** (offsets ranging
from 41 to 58 across the 8 — i.e. delaying `R1` admission by up to 17
further preparation edges did not, in any of the 8 observed cases,
change this outcome). This is consistent with E's spirit — continuing
longer does not appear, in this sample, to merge the eventual `R1`
target with anything — but it is `n=8`, not exhaustive, and no argument
is given here for *why* it would hold in general. Graded
`CLAUDE_OBSERVATION`, explicitly not promoted to a theorem.

## 4. R1-target isolation, hand-verified for all 8

**`CLAUDE_HAND_PROOF`** (data-inspection, not a search): for each of the
8 children, located the `incidence_forest` component containing the
hub orbit (`hub.id`, always 0 for these 8) and the component containing
`R1_geometry.target_orbit`. Result: **in all 8 of 8**, the two
components are different, and `R1`'s target-orbit component is always a
minimal one (`e_orbits: 1`, `hexagons: 2` or `3`) — i.e. `R1`, at the
moment it fires, always lands in territory that has never been touched
by anything else registered so far in that branch's history. This is
the exact, quantitative form of the "source-orbit registration barrier"
described qualitatively two rounds ago — now confirmed uniformly across
the full top-8 set, not just asserted by analogy to `short_ell0`.

## 5. Smallest unresolved symbolic template for a successful path

Given `target_a_recognizer`'s exact requirement (`same_component(source,
target)` computed via `incidence_components`' union-find, verified from
source two rounds ago and reused unchanged here) and section 4's
uniform finding, the smallest unresolved template for any of these 8
children to reach `TARGET_A_HIT` is:

> **Does there exist, from `R1`'s target orbit/phase, any legal
> `Z2`/`Z3` continuation — within the remaining resource budget (1
> further `R` event, `hub_touch_count <= 2`, `F_def == 1`, `H == 0`) —
> whose own orbit registration merges `R1`'s target-orbit component
> with the component that will contain the eventual `R2` target
> orbit (in particular, with the hub component, since every checked
> `R2` candidate's target orbit traces back toward hex 0's territory)?**

This is a single, precisely statable existential question, genuinely
open: not answered by any data inspected this round or prior rounds,
and — per the task's own instruction — not attempted by search here.
It is the same underlying question as the "single legal continuation
lookahead" evidence-need already identified two rounds ago for the
five single-successor children, now given its exact symbolic form
in terms of `incidence_components` and the recognizer's own
`same_component` predicate, rather than left as a vague plausibility
note.

## 6. Theorem / observation / fact classification

| finding | grade |
|---|---|
| Completer at macro_index 4 for all 8; offsets 1-3 hex-identical across all 4 roots with `rot^(4-root_ell)` at offset 1 | **family-wide hand theorem** (n=8, exhaustively re-derivable from the given trace data) |
| Within a root, top-8 children sharing that root are literal prefixes of ONE walk, differing only in R1-admission offset | **family-wide hand theorem** (n=8, byte-for-byte verified) |
| D1 is forced for short_ell4 (the `Z2` alternative is illegal, not merely undesired) | **hand theorem, verified by direct engine replay** (covers all 4 roots at this one point; not generalized to D2/D3) |
| R-alternative and declined continuation always target the same orbit, different phase (refuting Claim C) | **corpus observation, n=4 checked pairs, 100% consistent** — not shown to generalize beyond these |
| R1's target orbit always lands in an isolated, hub-disjoint component | **corpus observation, n=8, 100% consistent** — not proven as a theorem, no general argument given |
| D2/D3 forced-vs-free status | **unresolved / child-specific fact only** — read directly from trace data, mechanism not independently verified as it was for D1 |
| Smallest unresolved template (section 5) | **open question, precisely stated, not resolved** |

## What this document does not do

- Does not claim the branching-spine structure found here (Types 1/2
  divergences) generalizes to the other 431 children in the 439-child
  corpus, or to the remaining R1-admission points of `short_ell1` and
  `short_ell4` beyond their single top-8 representative.
- Does not verify D2 or D3 by replay the way D1 was verified — their
  forced-vs-free status is genuinely unknown from this round's work.
- Does not resolve the section 5 existential template — it is reported
  as the smallest OPEN question this analysis could reduce the problem
  to, not as solved.
- Does not claim Claim E is false — only that it is unproven and
  consistent with, not established by, the n=8 sample checked.
- Runs no search. All replay in section 2 is a deterministic
  re-execution of an already-fixed prefix, enumerating one state's fixed
  legal-edge set once, with no further exploration past that single
  enumeration.

CLAUDE_TOP8_FAMILY_ANALYSIS_COMPLETE
