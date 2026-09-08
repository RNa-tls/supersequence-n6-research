# Round 135: partial-arc contraction and the one-heavy-seam obstruction

Author: CODEX. Scope: hypothetical **NR6** complete walks in `(k,G)=(3,2)`
with `L<=871`. NR6 remains ASSUMED. This round closes **18 of the 25 resource
rows**, not the entire cell. Seven one-defect rows remain open. The inherited
outer ledger remains **10/55**. No claim `L6>=872` is made.

Labels below distinguish hand proofs, finite complete calculations, and
small-n controls. No 122-pass NR6 search or broad subcase DFS was performed.
The new capacity computations are local light-chain enumerations.

## 1. Conventions and resource derivation — hand proof

`G=P-120` is multiplicity excess; `F` is abandonment. They are not identified.
`S` counts joints of weight >=3, NOT the old strand-count convention. Let
`r=O+e` count maximal runs of registered pass entries in one E-orbit; `x`
counts paid intra-run joints; `f_out` counts free inter-run joints. A pass
`(v,a)` contains `a` permutation windows, thus `a-1` rotation edges.

Write `sigma` for rotation of all six positions and `E` for rotation of the
first five, fixing the last. Different rotations within one hexagon have
different final symbols and therefore different E-orbits. `O` counts orbits
of **registered pass entries**, not orbits of every visited window.

The master identities give

    P=122, O=27, D=5O-P=13,
    S=(r-1)+x-f_out=26+e+x-f_out,
    N=S+G-O=S-25,
    L=844+G+S+H=846+S+H.

Let `nu` send each short arc to the next arc in its hexagon's cyclic spatial
order. `F` is the number of nu-ascents in chronological order. Every free
nu-descent opens a repeat run, with different descents opening different runs.
The accepted G=2 inequality is `f_out<=F+e`. Set

    delta=F+e-f_out >=0.
    S=26-F+delta+x, N=1-F+delta+x,
    L=872-F+delta+x+H.

Consequently `L<=871` iff `delta+x+H<=F-1`. In Type A, F=1 or 2 and at most
three exits are free; in Type B, F=2 and at most four are free. This gives the
following PROVED compressed form of all 25 rows. Each integer e in a range
is one distinct row; the JSON expands every row and was checked against the
Round-129 row generator.

| Type | F | delta | x | H | e | f_out | S | N | L | Rows | Result |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---|
| A | 1 | 0 | 0 | 0 | 0..2 | e+1 | 25 | 0 | 871 | 3 | order contradiction |
| A | 2 | 0 | 0 | 0 | 0..1 | e+2 | 24 | -1 | 870 | 2 | one-chain capacity |
| A | 2 | 0 | 1 | 0 | 0..1 | e+2 | 25 | 0 | 871 | 2 | one-chain capacity |
| A | 2 | 0 | 0 | 1 | 0..1 | e+2 | 24 | -1 | 871 | 2 | heavy-seam exclusion |
| A | 2 | 1 | 0 | 0 | 0..2 | e+1 | 25 | 0 | 871 | 3 | OPEN |
| B | 2 | 0 | 0 | 0 | 0..2 | e+2 | 24 | -1 | 870 | 3 | one-chain capacity |
| B | 2 | 0 | 1 | 0 | 0..2 | e+2 | 25 | 0 | 871 | 3 | one-chain capacity |
| B | 2 | 0 | 0 | 1 | 0..2 | e+2 | 24 | -1 | 871 | 3 | heavy-seam exclusion |
| B | 2 | 1 | 0 | 0 | 0..3 | e+1 | 25 | 0 | 871 | 4 | OPEN |

Negative N in this repaired accounting is intentional. Historical F-based
N-monotonicity is not imported into these G-based identities.

Since `H=sum_j max(w_j-3,0)` is a nonnegative integer, H=1 means **exactly one
weight-4 joint**, with every other joint weight 2 or 3. There is no weight-5
joint and no alternative way to spend the unit. These rows have delta=x=0.

## 2. A short-pass geometry lemma — hand proof and finite check

A genuine weight-3 tail must avoid an earlier hidden permutation window.
Writing the joint source as y, the three allowed tails are `120,201,210` on
its first three symbols. For a full pass starting at v, `120` gives E^2(v)
(M3a, same orbit); the other two are M3b/M3c, cross-orbit connectors.

For a short pass `(v,a)`, a=1..5, none of those tails leads to orb(v):

* a=1..3: the fixed final symbol of v lies in the target's retained prefix,
  hence cannot be its last symbol;
* a=4: same last symbol would require tail 012, which is not genuine weight 3;
* a=5: it would require tail 021, which introduces an earlier permutation
  window and is not a consecutive-permutation joint.

Weight 2 after a short pass also changes its entry orbit. Therefore when H=0,
**every short pass is last in its run**, even when x=1. When x=0 the same
conclusion holds regardless of H: a same-orbit paid exit would contribute x.

Independent literal geometry checks all 720 entries and all five short
lengths (3,600 entry/length pairs, all their genuine weight-3 candidates):
zero same-entry-orbit targets. This is secondary evidence for the argument,
not a premise deduced from samples.

## 3. Generalized partial-arc contraction — hand proof

The old six-pass lemma is insufficient as a statement for Type A. Use the
following stricter, explicitly checkable generalization.

In a legal no-repeat pass list, take a contiguous interval

    (v,a), (t1,6), ..., (t_(j-1),6), (c,b)

such that

    c=sigma^a(v), a+b<=6,
    every t_i and c belongs to T=orb(c),
    no pass entry outside this interval belongs to T.

The endpoints v,c are different rotations, so orb(v)!=T. Replace the interval
by `(v,a+b)`. This is allowed even when a+b<6.

The new entry is v; the new exit sigma^(a+b-1)(v) is exactly the old exit.
The merged arc visits exactly the union of the old two endpoint arcs.
Every deleted middle pass is removed altogether. The new permutation-window
set is a subset of the old one; every external joint and its hidden-window
semantics remains unchanged. Thus no-repeat and literal legality survive.

Exactly one registered orbit T disappears. The still-visited window c does
not register T after merging. If s internal paid joints and h internal heavy
units are deleted, the exact changes are

    P' = P-j, O'=O-1, D'=D+j-5,
    S'=S-s, H'=H-h.

The external-occurrence condition is essential; do not infer orbit removal
from a local arc pattern alone. The operation is a one-way reduction to a
PARTIAL word, not a claim of continuation-state equivalence or preserved
complete coverage.

For a free ascent followed by its unique locked run, the run starts at E(c)
and ends at c. With only E steps it contains five entries and j=5. With one
intra-run M3a it advances once by E^2 instead of E and contains four entries:
j=4, s=1. Skipping past c cannot give a different legal path to c: returning
would hit a previously visited phase before reaching it. All intervening
passes are full by the preceding short-last lemma.

## 4. Which rows force removable blocks? — hand proof

### Equality bookkeeping, including the changed x/H budgets

Write a for the number of nonfree nu-ascents and eta for the number of repeat
run openings which are NOT free nu-descents. Counting gives the exact identity

    delta = a + eta.

Thus delta=0 forces every ascent free and every repeat opening a free descent.
In particular, a free ascent opens a **fresh** orbit. These facts do not
assume x=H=0. The short-last lemma supplies the other ingredient needed to
extend the old order taxonomy to this round's x=1 or H=1 rows.

### Type A, F=1: zero blocks, an order contradiction

Chronological arcs 0<1<2 have nu-order `0->2->1->0`. The only ascent is 0->2.
Its fresh target orbit is orb(entry2). Repeat openings from descents can only
target orb(entry1) and orb(entry0), both different from orb(entry2). Therefore
the run immediately following arc0 is the unique run containing arc2. Arc1
must lie chronologically inside that run, but belongs to a different orbit.
Contradiction. All three F=1 rows close before contraction. This argument uses
the short-last property and is not an unconditional strengthening for words
with arbitrary heavy joints.

### Type A, F=2, delta=0: two PARTIAL-ARC merges

Nu-order is `0->1->2->0`. The two ascent targets are distinct orbits; neither
is the sole possible descent target orb(entry0). Each is fresh and unique.
Each corresponding run ends at its short arc. Merge arc0 through arc1 first,
then the merged arc through arc2 (or reverse the two operations with the
corresponding updated endpoint). The first merged length need not be six;
after the second it is six. At x=0 this is an eleven-pass macro contracting
to one pass, not two disjoint old six-pass blocks. At x=1 one run may have
four entries; alternatively the M3a is elsewhere. Distinctness of the two
removed orbits and absence of outside entries follow from uniqueness.

### Type B, delta=0: alpha / beta, with the exact shape checked

Let Q_i be opener-i's orbit and T_i closer-i's orbit, with opener0 earlier.
T_i!=Q_i. The later ascent opens fresh T1. Both Q0 and Q1, and also T0, have
already been registered by then; hence **T1 differs from all of them**.
Repeat openings can target only Q0,Q1. T1 consequently has just one run and
its closer is locked. This proves the later lock without transferring a
k=4 resource assumption silently.

The first target T0 is either nonrepeated, giving a disjoint alpha interval,
or equals Q1. In the latter case its first run U ends at opener1, and its only
later run V opens at the free closer1 and ends at closer0. It cannot equal
Q0; no other repeated target exists. Contract the T1 interval first. This
joins U and V by the preserved endpoint geometry and leaves one T0 interval.
Contract that second. This is precisely inner-first beta, not a simultaneous
contraction of overlapping blocks. Model T with Q0=Q1 lies in alpha and still
has distinct T0,T1.

If x=0, each interval has the old five removed entries. If x=1, the sole M3a
may occur in one full-pass portion of U,V or either lock, skipping one entry;
the two generalized deletions then remove 5 and 4 entries. If it is outside
both intervals, they still remove 5 and 5. With H=1, x=0 puts the heavy joint
outside both locked intervals: every internal joint is free. It is retained.

### Summary of block counts

| Resource group | Forced reduction |
|---|---|
| A,F1,delta0 | impossible order; no contraction needed |
| A,F2,delta0 | two orbit-removing partial-arc merges; final full pass |
| B,delta0,alpha | two disjoint locks; generalized one if internal M3a |
| B,delta0,beta | inner first, then outer; generalized one if internal M3a |
| A,F2,delta1 | at least one merge; two-merger instances excluded below |
| B,delta1 | no uniform two-merge assertion; residual may have zero or one |

## 5. Exact contracted outputs and Round-115 inclusion

In the F2/delta0 rows let u=0 or 1 count removed M3a joints. Then u<=x and

    P'=112+u, O'=25, D'=13-u,
    S'=24+x-u, H'=H.

Every remaining pass is full. Its run accounting is now

    S'=(O'-1)+e'+x', hence e'+x'=x-u.

This derives the residual budget; it does not assume repeats or x cancel.
With H=0 there is one light chain. Round-115 N*(b,g,s) means maximum passes
with b extra runs plus paid intra-run steps, g exempt incomplete-orbit handoff
tokens, and s permanent unused phases. Its in-run b move is an overapproximation
(any unused phase); in particular it includes exact M3a. It permits repeated
entry at unit b cost. Current-orbit deficit is optimistically omitted during
growth, and remaining b/g tokens can excuse future fill/handoff deficits.
Those relaxations enlarge the model; no assumption of one segment per orbit
is made when b=1. Fully visited hexagons may not repeat.

The contracted partial word has no terminal coverage requirement. These
local chain maxima apply to arbitrary prefixes, not just F=0 complete covers.
One chain needs g=0, with s=D'. Therefore

* x=H=0: P'=112 > N*(0,0,13)=83;
* x=1,H=0: P'>=112 > N*(1,0,15)=106, a safe enlargement of s<=13;
  if u=1 the exact residual is instead (b,s)=(0,12).

Thus all ten F2/delta0/H0 rows close, including all five x=1 rows.

## 6. A general full-pass decomposition/convolution theorem — hand proof

After valid contractions **which remove every short pass**, cut at every
remaining heavy joint. There are t<=H'+1 light pieces. The italicized premise
cannot be dropped: cutting a partially contracted short-bearing word alone
does not embed its pieces into Round-115 full-pass chains.

Let h_in count heavy cuts inside a run. For orbit q let a_q be the number of
pieces containing its entries, and put z=sum_q(a_q-1). Across pieces, define
b_i=e_i+x_i, give one handoff token for each occurrence of an orbit shared by
two or more pieces, and charge only unshared-orbit deficits to s_i. Then

    sum b_i=e'+x'-z,  0<=z<=e'+h_in<=e'+x',
    sum g_i<=2z,      sum s_i<=D'.

Proof: cutting creates h_in extra runs, so sum r_i=r'+h_in, whereas
sum O_i=O'+z and sum x_i=x'-h_in. Subtract to obtain the b identity.
For a_q>=2, a_q<=2(a_q-1), proving the token bound. Unshared deficits are a
subset of the global unused phases. Literal no-repeat persists in each piece.
The optimistic R115 token semantics therefore accepts each piece.

Consequently P' is at most the maximum of sum_i N*(b_i,g_i,s_i) over these
integer budget allocations and t<=H'+1. This is a conditional general G2
tool, not a proof that every G2 word admits enough contractions. No other k
cell was computationally investigated in deriving it.

## 7. H=1: the coarse convolution is NOT sufficient

Here P'=112,O'=25,D'=13,S'=24 and e'=x'=0. The one weight-4 joint is
inter-orbit; cutting it yields exactly two chains with disjoint orbit sets.
Thus z=g_i=b_i=0 and D_left+D_right=13. The independently replayed table is:

| s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| N*(0,0,s) |20|20|33|33|46|46|49|58|62|66|70|74|83|83|

The maximum convolution is **112**, not 111. Equality requires deficits
(4,9) or (9,4) and lengths (46,66) or (66,46). Any argument stopping at this
table cannot close the H1 rows.

### Equality seam certificate — finite COMPLETE calculation

Enumerate only the extremal light chains, with first word normalized by the
proved left-S6 action. There is exactly one length-46 chain at D<=4 and twelve
length-66 chains at D<=9. Pass-level generator counts are 1,522 and 214,765
nodes. A separately formulated **run-level** verifier, using direct positional
M3b/M3c formulas instead of the generator's joint list, obtains exactly the
same paths in 548 and 82,162 run nodes. All paths are literal-replayed.

For each ordered pair of extrema, try every genuine weight-4 seam. Such a
seam has 13 candidate target permutations. Its target fixes the right chain's
symbol relabeling uniquely. Both length orders give 312 candidates:

    158 have a common registered E-orbit;
    154 (after excluding those 158) have a common hexagon;
    0 are legal disjoint-chain joins.

The verifier independently tries all 720 relabelings for every ordered pair:
17,280 trials, exactly the same 312 genuine weight-4 seams and counts. No
reversal or arbitrary orbit renaming is used. Every required candidate is
accounted for; no cap/timeout occurred. Thus in this exact two-chain model
the total is at most **111**. All five H=1 rows close.

## 8. The seven surviving rows: an exact defect decomposition, not absence

All have F2,delta1,x=H=0,S25,N0,L871. Their exact list is

    Type A: e=0,1,2, f_out=e+1;
    Type B: e=0,1,2,3, f_out=e+1.

The identity delta=a+eta=1 splits the mechanism into:

1. one nonfree ascent and no extra repeat opening (a=1,eta=0); or
2. all ascents free and one extra repeat opening (a=0,eta=1).

The extra opening can be a paid re-entry **or a free ascent entering an
already-open orbit**. It is not valid to call it necessarily one paid joint.
At e=0 only case 1 is possible. At A/e2 or B/e3 every short exit is free and
only case 2 is possible. Intermediate rows allow both mechanisms.

For Type A the two ascent target orbits are distinct from the ordinary
descent-repeat target. A single defect can spoil at most one of their fresh,
unique locked runs, hence at least one partial-arc merge remains. For Type B
the extra repeat may interact with the existing nested/repeat structure, so
no corresponding one-merge universal claim is used.

In any of these rows, if two valid orbit-removing intervals remove all short
passes, x=H=0 makes the within-run portions free. A nonfree ascent can still
enter its target orbit by weight 3 at E^2(c), rather than the free E(c).
Such a merge deletes four entries and one paid joint, not five entries.
Let u count these deleted paid entries. Then u<=1 and the exact output is
P'=112+u,O'=25,D'=13-u,S'=25-u, hence e'+x'=1-u.
The same N*(1,0,15)=106 contradiction applies in both cases. The remaining
hard core consists only of instances with **fewer than two** such intervals:
Type A exactly one, Type B zero or one. This is a geometric restriction inside
seven resource rows, not a reduction of the number of rows to five.

## 9. Counterexample-first controls and their exact limits

The independent NR4 adjacency DFS enumerated all 29,255 complete walks starting
0123 with length<=39, visiting 49,682,345 nodes, no cap. The 248 G2 controls
satisfying the analogous resource inequality have these contraction counts:

| delta | two merges | one merge | zero merges |
|---|---:|---:|---:|
| 0 | 93 | 0 | 0 |
| 1 | 102 | 33 | 20 |

The 195 fully contracted controls also pass the full decomposition identities
in section 6, including actual heavy cuts and shared-orbit token accounting.
The delta1 counterexamples refute the naive general-n assertion that allowing
one defect still forces two merges. Minimal examples IN THIS EXHAUSTIVE NR4
CONTROL CORPUS (not claimed globally shortest) are stored with literal paths:

* A,one merge: `012301203021302031023103210312013201`;
* B,one merge: `012301032102310213021030120312013201`;
* B,zero merges: `0123012031023132013231032103120213021`.

They are not counterexamples to an n6-specific conjecture or complete NR6
capacity bound. The n6 local checks include 60 partial-arc surgeries, 771
legal external-heavy contexts, 46 legal Type-A two-merge examples, and 2,446
one-M3a variants of the preserved Type-B rigid controls. All replay/surgery
checks pass. External registration of the would-be-deleted orbit is tested
as a forbidden context, not silently ignored.

Visible harness correction: of 70 synthetic Type-A shapes, 24 are already
literally colliding. An initial assertion mistakenly treated every synthetic
shape as legal. Commit d6bbc9e distinguishes the 24 negative controls and
applies the theorem only to the 46 legal inputs. No illegal input is counted
as a contraction failure or as a complete NR6 absence certificate.

## 10. Provenance, reproducibility, and unchanged scope

Artifacts:

* `outputs/rr_round135_controls_codex.json`: resources, exhaustive NR4 domain,
  literal local surgeries; source commit 80c87e9.
* `outputs/rr_round135_capacity_codex.json`: all 15 actual capacity replays,
  full argv, times, node counts, source/binary hashes; source commit 80c87e9.
* `outputs/rr_round135_heavy_seams_codex.json`: extremal paths and all seams;
  source commit de76176.
* `outputs/rr_round135_verified_codex.json`: independent run enumeration,
  literal replays, all 25 rows, conditional outputs, seven-row open ledger;
  source commit b27ac51. Its mathematical_certificate_digest excludes run
  location/timing metadata; input file SHA values retain byte provenance.

The capacity source is the unchanged `src/chain_capacity_115.c`, raw SHA256
`c7694b66f3d31770f5ed9d91b7b61a1973c2138d22513a0d7ca40615dc74544a`.
The independently built inherited binary was actually rerun for this round.
At s=0..13, its node counts are respectively

    64,114,461,1221,3555,10367,27307,72776,186282,469852,
    1142550,2737333,6332475,14407541.

N*(1,0,15)=106 finishes at 3,142,716,999 nodes. The explicit safety cap was
20,000,000,000 per job and **every result has capped=false**. No capped value
is used as an upper bound. Source was committed before these jobs. The C
node count is not a complete-NR6 search count. Nine new regression tests pass,
as do all nine inherited Round-134 contraction regressions.

Visible accounting correction: the initial residual-row draft treated x=0
as making even the interval's entry joint free. This need not hold at delta1.
Commit b27ac51 adds the explicit weight-3 short-entry fixture, and section 8
and the JSON now retain both u=0 and u=1 conditional contraction outputs.
The already-closed delta0 rows and the 18/7 result are unchanged.

Reproduce the small independent verification without rerunning the large
capacity jobs:

    python src/verify_round135_structural_codex.py
    python -m unittest discover -s tests -p test_round135_contraction_codex.py -v

Capacity reproduction uses the unchanged C source compiled locally, commands
`chain_capacity_115 0 0 s 20000000000` for s=0..13, and
`chain_capacity_115 1 0 15 20000000000`. The driver records its original local
binary path; that path is not a mathematical dependency for rebuilding it.
No production traversal, old checkpoint, prior proof output, or global ledger
was modified. No G>=3 or other-cell search was launched.

## 11. Result and recommended next theorem

18 rows are excluded: 3 by order, 10 by single-chain capacity, 5 by the finite
heavy-seam theorem. Seven delta1 rows remain OPEN. The next structural target
is the one-defect failure of simultaneous two-orbit removal, with the Type-A
one-merge family a natural first target; no new exact search is authorized or
started here. The outer ledger stays **10/55, NR6 conditional**.

ASTRA_G2_CONTRACTION_THEOREM
