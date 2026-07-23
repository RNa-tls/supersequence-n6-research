# `F=1,D=4` partial-cassette exact state

## Scope and status

This note is conditional on **NR6**: the proposed minimal `n=6`
superpermutation is a no-repeat permutation walk.  It treats only the next
unsaturated `k=1` slab

\[
 F=1,\qquad D=4,\qquad N+H\leq 3,
 \qquad P=121,\quad O=25. \tag{1}
\]

The completed saturated forest computation concerns the distinct corner
`(F,D,N)=(5,0,0)`.  Nothing here transfers its port-lift conclusion to (1).
Conversely, this note does **not** launch an exhaustive search for (1).  Its
claims are limited to an exact transition model, a lossless `F<=1` normal
form, and safe necessary pruning.

Status labels used below are:

- **Proof**: a direct finite-state argument valid for every NR6 prefix.
- **Finite program check**: an assertion over an explicitly finite set.
- **Bounded diagnostic**: a node-limited census; never an absence proof.

## 1. Exact state

Let `H` range over the 120 rotation hexagons and `Q` over the 144 `E`-orbits.
For a walk prefix ending at the permutation `p`, define

\[
 \Omega=
 \bigl(p;(M_H)_{H\in\mathcal H};(B_Q)_{Q\in\mathcal Q};F,S,H\bigr). \tag{2}
\]

Here `M_H` is a six-bit mask for precisely the permutation windows already
visited in rotation hexagon `H`, and `B_Q` is a five-bit mask for precisely
the pass-start phases already used in `E`-orbit `Q`.  The symbol `H` is used
both for a hexagon and for the heavy counter only in traditional notation;
in code the latter is `state.H`.

The initial one-window prefix has `S=1`: its terminal permutation is also the
first pass start.  From the masks alone one recovers

\[
 P=\sum_Q |B_Q|,\qquad
 O=\#\{Q:B_Q\ne0\},\qquad
 D=\sum_{B_Q\ne0}(5-|B_Q|)=5O-P,
 \qquad N=S+F-O. \tag{3}
\]

### Theorem 1 (Markov sufficiency) — Proof

Given (2) and an indecomposable tail `pi` of declared length `w`, all of the
following are determined:

1. whether the tail is a legal next transition;
2. whether its new permutation window collides with the prior walk;
3. whether the previous pass ended blocked or by abandonment;
4. `Delta F`, `Delta S`, `Delta H`; and
5. the successor exact state.

**Proof.**  With the right-action convention, the literal tail has endpoint

\[
 p'=p\,a_{w,\pi},\qquad
 a_{w,\pi}=(w,w+1,\ldots,5,\pi(0),\ldots,\pi(w-1)).
\]

Indecomposability says that the intermediate length-six windows in the
literal appended tail are not permutations.  Hence the only new permutation
window to test is `p'`.  Its membership in the visited set is read exactly
from the bit of `M_{hex(p')}`.  If it is absent, set that bit.

For `w>=2`, `p'` is the next pass start, so its unique `E`-orbit and phase
set exactly one bit in `B_Q`.  The preceding pass is blocked precisely when
`p sigma` is already in `M_{hex(p)}`; otherwise it is an abandonment.  Thus

\[
 \Delta F=1_{\{w\ge2,\;p\sigma\notin V\}},\quad
 \Delta S=1_{\{w\ge3\}},\quad
 \Delta H=(w-3)_+ .
\]

For `w=1` no new pass begins and all three increments are zero.  Every
updated datum is therefore a function of (2) and `(w,pi)`.  ∎

### Important convention: literal tails, not endpoint maximal overlap

The endpoint `p'` may accidentally admit a shorter maximal-overlap
representation.  This does not alter the literal transition length: a walk
records the appended indecomposable tail, whose intermediate windows are
non-permutations.  Consequently the implementation keys a replay move by
**both** `(w,right-action)`; it never infers `w` solely from the endpoint
pair.  This distinction is checked against every tail in the finite sanity
test.

## 2. Why both mask layers are required

`B_Q` alone is not a membership oracle.  It records pass starts, not all
interior rotation vertices.  If two mask states have identical `p`,
`B_Q,F,S,H` but one marks `p sigma` and the other does not, the next rotation
is blocked in the first and legal in the second.  The sanity program contains
this explicit mask-level countermodel.  It is deliberately labelled a
state-level countermodel rather than a claim that the two masks arise from
complete walk prefixes.

Conversely `M_H` alone cannot decide whether a future pass start consumes a
new `E` phase, nor can it recover `P,O,D,N`; this makes it insufficient for
the target condition (1), even though it decides window collisions.

The terminal permutation `p` is also essential.  A tail is a right action on
`p`, so the same occupation masks with a different terminal window have a
different set of legal next endpoints.  The counters are required because
membership legality alone does not decide the budget `N+H<=3`.

## 3. The proposed `Omega_1` and its necessary repair

At completion with `F=1`, the frag identity `P=120+F` implies exactly one
rotation hexagon is split into two rotation passes, while every other
hexagon has one pass.  It is tempting to replace all `M_H` by

\[
 (\mathcal U;H_\ast,I_1,I_2), \tag{4}
\]

where `U` contains full hexagons and `I_1,I_2` are the two directed arcs in
the fragment hexagon.  During a search prefix, (4) is **not sufficient as
written**: the currently active pass may lie in a second, distinct and
partially filled hexagon.  Its occupied arc is neither a full hexagon nor
the old fragment hexagon, and deleting it changes later collision tests.

The following is the corrected lossless normal form:

\[
 \Omega_{1}^{\rm nf}=
 \bigl(p;\mathcal U;H_\ast,J_\ast;
 H_{\rm cur},J_{\rm cur};(B_Q);F,S,H\bigr). \tag{5}
\]

- `H_cur=hex(p)` and `J_cur` is the union of directed cyclic rotation arcs
  already used there;
- `H_*`, if it exists and differs from `H_cur`, is the one abandoned
  non-current partial hexagon, with its directed arcs `J_*`;
- a full mask belongs to `U`; empty masks are implicit.

If `H_cur=H_*`, the two arc families are stored together in `J_cur` and no
second hexagon name is needed.  A nonfull six-bit mask is canonically a union
of directed `sigma`-components, represented by `(start,end,length)` in the
fixed local hexagon coordinate.  Thus (5) reconstructs every `M_H` and is
equivalent to (2) on its domain.

### Proposition 2 (F<=1 normal-form invariant) — Proof

For every reachable prefix with `F<=1`, there is at most one non-current
partial hexagon and at most `F+1` directed nonfull rotation components in
total.  Thus (5) is lossless.

**Proof.**  Except for the live pass, a nonfull hexagon can remain behind
only when a pass was abandoned; a blocked pass either leaves no new gap or
continues through the `w=2` repair mechanism.  Each abandonment creates at
most one such outstanding non-current gap.  The live pass contributes at
most one additional directed component.  With at most one abandonment this
gives the stated bounds.  The masks in (5) reconstruct exactly the occupied
vertices by taking the indicated cyclic intervals, while `U` reconstructs
the full masks.  ∎

`p` makes an extra exit-phase field unnecessary in the exact representation:
the live component ending at `p` is the current exit.  If intervals are
stored only as un-oriented sets, their directed endpoint information must be
retained (or equivalently recovered from the fixed `sigma` orientation and
`p`).  No separate abstract “repair pairing” is sufficient to replace the
actual interval masks.

The code function `f1_normal_form` implements (5), and
`restore_f1_normal_form` is its inverse on the stated domain.  The finite
sanity report checks this round trip on an explicit one-fragment prefix.

## 4. Safe pruning for the target slab

The following rules are implemented only as necessary conditions.  A branch
that survives them has not been certified extendible.

### Lemma 3 (arithmetic `D` feasibility) — Proof

Let `r=121-P` be the remaining number of pass starts.  Each future start
changes `D` by `+4` if it opens a new `E`-orbit and by `-1` otherwise.
Therefore a necessary condition for final `D=4` is

\[
 4=D-r+5a\quad\hbox{for some }0\le a\le r. \tag{6}
\]

The program rejects a state only if (6) has no integer solution.  It ignores
all geometric restrictions, so it can never reject a real completion. ∎

### Lemma 4 (budget and capacity prunes) — Proof

The following are monotone necessary conditions:

1. `F<=1`, `P<=121`, `O<=25`, and `N+H<=3`;
2. there are at least `121-P` unvisited windows, since every future pass
   start is a distinct new window;
3. the normal-form invariant of Proposition 2 holds;
4. the number `25-O` of still needed new `E`-orbits does not exceed the
   remaining opening credits
   \[
   \max(0,27-H-S)+(1-F). \tag{7}
   \]

For (7), final `N+H<=3` and `F=1,O=25` give
`S_final<=27-H_final<=27-H`.  Thus at most the first term many new strands
can still begin; at most `1-F` abandonments remain.  The proof of Theorem A
applied locally says a new orbit can be opened only by one of these two
credits.  Hence failure of (7) rules out every completion.  The collision
test itself is exact by Theorem 1. ∎

Finally, a repeated **canonical** state is safely memoized: its entire exact
state and resource vector are identical, so Theorem 1 gives exactly the same
set of future completions.  This is not a claim about a canonical parent.

## 5. Controls already required before any long run

`work/superperm_partial_f1.py sanity` performs the following finite checks.

| control | status / purpose |
|---|---|
| all 550 literal indecomposable tails | no intervening permutation window |
| standard 873 word replay | reproduces `(P,F,S,H,O,D,N)=(120,0,24,6,24,0,0)` |
| synthetic first `w=2` tail | produces an explicit legal `F=1` prefix |
| six rotations | the repeated return window is rejected |
| `D=5O-P` | asserted on the synthetic `F=1` prefix |
| normal-form round trip | `restore(f1_normal_form(state))=state` |
| all 720 value relabellings | the legal tail-label set is unchanged |
| missing-`M_H` pair | demonstrates why a membership mask cannot be dropped |

No archived complete `F=1` walk is currently used as a positive control.
The synthetic prefix is explicitly not represented as a full candidate
solution.  A separate `n=5` exhaustive cross-check has not been claimed;
the present engine is intentionally fixed to the established `n=6` group
coordinates.

## 6. What this does and does not establish

**Established by proof and finite checks:** the state transition semantics,
the `F<=1` lossless normal form on reachable prefixes, the left-action
equivariance used by canonicalization, and the listed necessary pruning
conditions.

**Not established:** absence of the `F=1,D=4` slab, a global state-count
bound, a fragment escape inequality, or any unconditional statement about
`L_6`.  Those require a later checkpointed exploration or a new invariant.
