# Round 141B — NR6 foundation, unconditional repeat credit, and exact exchange gap

Author: CODEX. Date: 2026-09-10. This is the NR6-removal track, separate
from the conditional 55-cell outer theorem.

## 1. Outcome

**NR6 is NOT proved or refuted.** A new unconditional accounting theorem
reduces a hypothetical length <=871 counterexample from the old trivial
146-repeat allowance to **at most 27 repeated permutation-window occurrences**.
At most 4-k of those repeats can be outside a precisely defined blocked-fresh
weight-2 event class. This is a hand theorem, independently audited, with
two literal implementations checking 3,096 n=3 controls and explicit n=4/6
controls. It is not a no-repeat continuation search.

Further, deterministic first-occurrence projection terminates at a
length-nonincreasing geodesic fixed point. In a <=871 fixed point, all but
at most four charged connectors are zero-credit; exactly **seven repeating
zero-credit local templates** exist, in five actual-gap shapes. This catalog
is exhaustively verified by two different local enumerations. It does not
decide global history or give an exact-state quotient.

The remaining normalization implication is isolated as the plateau-exchange
lemma in Section 8. All reductions leading to that lemma, its permitted
moves, coverage/length guarantees and termination implication are proved
below. Its universal escape assertion is MISSING. Thus this track reaches
the user's stopping condition D, not an NR6 theorem or a claimed finite
certificate of all n=6 local patterns.

## 2. Recover NR6 exactly; correct the logical distinction

Canonical repository source: `RR_OUTER_REDUCTION_110_CLAUDE.md`, Section 2:

> Some globally shortest n=6 superpermutation can be chosen to have exactly
> 720 literal permutation-window occurrences.

The input is a finite word over six symbols covering all 720 permutations.
Its literal windows, not selected vertices of an overlap path, are counted.
NR6 permits split hexagons, repeated E-orbit visits, crossings, heavy joints
and nonpermutation windows. It forbids only repeated permutation windows.
The historical definition specified no transformation establishing it.

The sufficient threshold normalization statement is:

    for every covering X with |X|<=871, there is covering Y with
    |Y|<=|X| and exactly 720 literal permutation occurrences.

Intermediate words may contain repeats. The final word alone must be NR6.
No invariance of F, G, pass structure, selected occurrence order or literal
occupancy is required; complete coverage and nonincreasing length are.

**Visible logical correction to R110:** its distinction between “an NR6
shortest word exists” and “every <=871 input can be normalized” must not
claim the former is insufficient. If an NR6 global minimizer exists, choose
it for every input X; its length is <=|X|. Conversely the threshold version,
together with the independently verified literal-NR6 872 witness, implies
the existential canonical NR6 statement: if the minimum is <=871 use the
reduction on a minimizer, and if it is 872 use that witness. This logical
observation supplies no actual normalization proof.

## 3. Sound preprocessing and local moves — proved

### Trimming and Hamilton-order projection

Trim nonpermutation prefix/suffix outside the first and last permutation
windows. Select one occurrence of every required permutation, in increasing
position order. Replace each connection by the shortest suffix-prefix
overlap spelling of its endpoint permutations. Each connection costs at
most its old positional distance. Coverage of all selected permutations
persists, so this gives a Hamilton ORDER spelling no longer than the input.

It does NOT give an NR6 word: the shortest connectors may contain other
permutation windows. Those windows can regenerate repeats after selecting
each vertex only once. The explicit n=3 fixture in the foundation JSON
demonstrates this distinction.

This preprocessing can be made canonical and terminating even without
assuming global minimality. Let T(X) minimally respell the FIRST-occurrence
order. If those starts are a0<...<a719, then

    |T(X)|=6+sum minimum_gaps <=6+a719-a0<=|X|.

Equality forces a0=0, a719+6=|X|, and every gap minimal and <=6.
The source and target windows then uniquely determine every intervening
substring, so **equal length implies T(X)=X literally**. Hence each nonfixed
projection strictly shortens; iteration terminates in a first-occurrence
geodesic fixed point. It may still have repeated windows. In particular
every global minimum is already such a fixed point.

### Equal-window deletion and essential intervals

If X[a:a+n]=X[b:b+n] is a permutation and a<b, set

    X'=X[:a]+X[b:].

The common n-window makes every seam-crossing window agree with the old
one. The only lost permutation types are exactly those whose ALL occurrences
have starts strictly between a and b. Thus deletion preserves coverage iff
there is no such type; when allowed it strictly shortens length by b-a.

It is FALSE that lack of a globally unique window in this one interval
suffices. For n=3, the fixture

    01202102101200120010200201,  a=0,b=9

has no globally unique occurrence inside, yet deletion loses 021 and 210.
Both types have multiple occurrences, all confined to the deleted interval.

A stronger useful statement IS true: in a word irreducible under ALL
coverage-preserving equal-window deletions, every repeated-window interval
contains a globally unique permutation occurrence. Start with a type whose
all occurrences lie inside. If it is not unique, take two of its occurrences
and repeat inside that strictly smaller interval. Finite strict nesting
ends at a globally unique type. A globally shortest word is irreducible in
this sense. Its first and last permutation windows are globally unique:
otherwise dropping respectively the first or last character would preserve
all required permutations and shorten the word.

### Exact exchange rules and boundary information

Relocate one selected permutation within a Hamilton order and respell all
connectors minimally. This always preserves coverage; accept it only if
the recomputed length does not increase. A contiguous selected block can
likewise be moved. For an adjacent-block swap, internal costs cancel, and
the change is exactly the three new boundary overlap costs minus the three
old boundary costs (with missing end boundaries omitted). This is an
explicit safe rule, not an assertion that a useful rule always exists.

Replacing an arbitrary literal segment requires its boundary contexts and
every permutation whose coverage would otherwise be lost, including seams.
For future continuation the exact state `(last n-1 symbols, covered SET)`
is Markov sufficient: appending a symbol changes only that suffix and adds
its new n-window to the set. Endpoint alone, or endpoint plus covered COUNT,
is not sufficient. `0120012` and `0121012` have the same endpoint and covered
count but require respectively 6 and 5 additional symbols at n=3; their
covered sets differ. This is not a claim that equal covered sets fail.

Value-renaming and full-word reversal preserve coverage and length. Global
cyclic word rotation, arbitrary orbit relabeling and removal of provenance
are not granted symmetries. A repeated exact augmented Markov state permits
cycle deletion; a repeated literal endpoint with new coverage does not.

## 4. Unconditional repetition-credit theorem — hand proof

Let X be ANY trimmed covering word, with all literal occurrences counted.
Put M=n!+R_rep, so R_rep counts repeats after the first occurrence of each
permutation. Let P be maximal rotation passes, G=P-(n-1)!, F abandonment,
J=G-F. A pass may now have more than n windows.

Every hexagon has a pass entry, so P>=(n-1)!. Its LAST pass cannot abandon:
there is no later opportunity in that hexagon to visit the missing next
rotation. Therefore F_h<=m_h-1 and **J>=0**, without an arc permutation.

Let O be distinct E-orbits of pass entries, r their consecutive run count,
e=r-O, x paid intra-run joints, f_out free inter-run joints, S paid joints,
H=sum max(weight-3,0). The combinatorial identity

    S=O+e-1-f_out+x

does not require no-repeat. Each E-orbit meets n-1 distinct rotation classes;
covering all (n-1)! hexagons by pass entries implies O>=(n-2)!, so put
k=O-(n-2)!>=0. The old inequality P<=(n-1)O is NOT used.

### The extra event type that NR6 excludes

Partition free inter-run joints into:

1. abandoning: F-a of them, where a is missing free abandonment exits;
2. blocked, entering an old orbit: Ord of them;
3. blocked, entering a fresh orbit: Y of them.

An abandoning pass has fewer than n windows, otherwise it already visited
its whole hexagon. Its free exit changes last symbol and hence orbit.
The old-target blocked events inject into repeated RUN openings. Define
eta=e-Ord>=0. Then, without assuming NR6,

    delta=F+e-f_out=a+eta-Y.

Delta may be negative. The nonnegative quantity is NOT delta.

At a Y event let p be its literal joint source and b=sigma(p) the blocker.
The free target is E(b). Since that orbit is fresh, b has never been a
registered pass entry. It was nevertheless visited. Every earlier b
occurrence must therefore have arisen by an actual rotation from an earlier
p occurrence. The present p is repeated. Different Y joints have different
source OCCURRENCES, so

    Y<=R_rep.

This handles ell=0, rotation wraparound, earlier macros, and long passes.
The repeated source itself can be an entry or an interior rotation window;
the injection is on occurrences, not distinct permutation names.

Define

    epsilon=R_rep+delta=a+eta+(R_rep-Y)>=0.

Counting gaps gives

    L=n+(M-P)+2(P-1-S)+3S+H
     =B_n+k+J+epsilon+x+H,
    B_n=n!+(n-1)!+(n-2)!+n-3.                 (REPEAT-CREDIT)

This recovers the classical baseline by an event-level derivation; we do
not claim discovery of a new classical lower bound.

### Tight-budget corollary

If L<=B_n+t, then R_rep-Y<=t-k. Each Y opens a distinct fresh orbit other
than the initial one, so Y<=O-1. Consequently

    R_rep<=Y+t-k<=(n-2)!-1+t.

For n=6 and L<=871, B_6=867 and t=4:

    0<=k<=4,   R_rep<=27,
    J+a+eta+(R_rep-Y)+x+H<=4-k.               (NR6-HARD-CORE ENVELOPE)

All but at most 4-k repeated occurrences are sources of fresh blocked-w2
events. This is a universal localization theorem, not an empirical bound.
If R_entry counts repeated PASS ENTRIES, a safe deficit identity is

    D_unique=5O-(P-R_entry)=5k-G+R_entry>=0,
    G<=5k+R_entry<=5k+R_rep.

In a <=871 word this also gives G<=47, but not the old G<=5k domain.
The 55-cell proof cannot simply be applied before normalization.

## 5. Why successor splicing does not yet remove NR6

The algebra flip(p)=E(sigma(p)) is universal. The step “visited blocker
is registered” is not. A local repeated prefix `01234501234510` has a
blocked-fresh w2 exit from repeated 012345 while 123450 was only an internal
visited window. This is precisely Y, not a contradiction to NR6's lemma.

The old nu construction also needs matching multisets of pass entries and
next-rotation endpoints. Complete repeated n=3 word `0120102102` has unequal
multisets. Its long rotation pass cannot be replaced by the old successor
permutation on entries. Thus external endpoint preservation alone does not
create an arbitrary-word normalization. Any repaired occurrence-level splice
must account for that imbalance and repeated ports. We have not assumed
such a repair exists or used conditional outer capacities for it.

## 6. Complete small domains and adversarial controls

The two NR3 implementations enumerate all 720 Hamilton orders. The producer
generates pop/insert moves; the independent verifier constructs adjacency
from equal delete-one signatures. The finite graph has 10,872 directed
length-nonincreasing edges, 18 clean orders; all 720 reach a clean order.
The producer stores 720 normalization paths, and the literal checker verifies
their 1,116 moves. This is a complete small-n certificate, NOT NR6 evidence
by extrapolation.

Hidden-occurrence-only relocation has 2,016 edges and reaches a clean order
from only 708 orders; 12 remain. One exact plateau respells the SAME literal
word `0121020102120`. Shortest-overlap projection can also regenerate hidden
repeats. Neither claim is repaired by calling selected vertices “no-repeat”.

Bounded n=4 discovery (30 deterministic initial orders) found 16 traps for
STRICT one-move lexicographic descent `(length,repeats)`. The minimum found
is length 37 with one repeated window and 529 distinct relocation neighbors:

    1032103012301320131203120231023021302.

This is only a counterexample to strict one-move improvement. The independent
COMPLETE weak, length-nonincreasing reachability domain from this order has
20 orders and 54 edges and DOES reach clean orders. Its replayable path is
in `rr_round141_nr6_verified_codex.json`. The experiment explicitly avoids
mislabeling a plateau as a counterexample to normalization. It shows why
the missing lemma must allow equal-length intermediate moves.

The repeat-credit implementations independently agree on all 3,096 distinct
words formed from S3 Hamilton spellings and one complete rotation detour at
each permutation occurrence. 1,458 have Y>0. The shortest bad-fresh example
IN THAT DOMAIN is `0120121021`. They also agree on the n=4 trap, the verified
872 n=6 witness and four repeated-window detours of that witness. These are
finite controls; the universal proof is Section 4.

### NR3 and NR4 at their classical minima

REPEAT-CREDIT at n=3,L<=9 gives R_rep=0. The explicit word `012010210`
has length 9 and covers all six permutations.

At n=4,L<=33 it gives R_rep<=1. If R_rep=1, equality forces
k=J=epsilon=x=H=0,Y=1,a=eta=0. Only two orbits can open: the initial
one and the Y target. An abandoning free joint would either open a third
orbit or cause an exceptional repeated run; a paid abandonment costs a.
Thus F=0 and G=0. Paid joints likewise require either a third opening,
eta>0, or x>0; hence S=0. There are exactly six passes: five of length 4
and one of length 5, joined only by the unique free move. After renaming
the initial permutation, all SIX placements of that long pass are explicitly
spelled and checked; none covers 24 distinct permutations. Therefore all
length-33 n=4 covering words are NR4. The explicit length-33 word
`012301203120132010231021302103210` attains the bound.

This small-n proof uses the unconditional credit theorem, not an enumeration
that assumed no-repeat. No new n=5 exact search was needed or performed.

## 7. Minimal-counterexample consequences

### A complete finite local catalog before attempting a global exchange

In a first-occurrence geodesic fixed point, every selected endpoint occurs
for the first time and every internal permutation window of a connector
occurred earlier. Conversely every repeated occurrence is internal to exactly
one connector. Equal permutations cannot start fewer than six positions
apart, so the internal windows of each connector are distinct.

Normalize its first permutation to 012345. Its different final permutation
has 719 possibilities; its minimal gap is <=6. For one connector let h be
its internal permutation-window count, y the number of those internal
windows whose NEXT actual gap is 2, and H_local its actual heavy excess.
Every Y event's repeated source is such an internal window. Consequently

    u=h-y+H_local>=0,
    sum u=R_rep-sum y+H <=R_rep-Y+H
         <=4-k-J-a-eta-x.                                  (LOCAL-CREDIT)

At most 4-k-J-a-eta-x connectors have positive integer u. All other
REPEATING connectors must be one of these seven zero-u templates, up to
proved value-renaming:

| normalized target | actual gaps | internal repeats |
|---|---|---:|
| 103254 | 2,2,2 | 2 |
| 345021 | 1,2 | 1 |
| 451032 | 2,2 | 1 |
| 502143 | 1,2,2 | 2 |
| 512043 | 3,2 | 1 |
| 520143 | 3,2 | 1 |
| 521043 | 3,2 | 1 |

There are also five nonrepeating zero-u templates. A target-pair/overlap
enumerator and an independent enumeration of ALL 55,986 appended symbol
tails of lengths 1..6 produce the identical 719-entry catalog. Smaller
n=3,4,5 catalogs are cross-checked as controls. No stored frontier or
continuation engine participates.

“Eligible for Y” is not “is Y”: the blocked/fresh history conditions still
have to hold. If one of these eligible sources is not an actual Y, it
consumes R_rep-Y elsewhere in the same small global budget. Thus the seven
local shapes do not imply any literal global history exists or does not
exist. Nor are they seven equivalence classes of continuation states.
The positive-credit exceptional connectors are fully listed in the catalog,
with total cost <=4-k-J-a-eta-x; none is silently excluded.

Assume a <=871 covering word exists but no no-longer NR6 output does.
Choose a global minimum length word and then a minimum repeat count.
It is trimmed, first/last windows are unique, its repeated intervals are
essential as in Section 3, and it has a Hamilton-order spelling. It lies
in NR6-HARD-CORE ENVELOPE, with 1<=R_rep<=27.

Every safe deletion would contradict minimal length. Every nonincreasing
exchange reaching lower `(length,repeats)` would contradict the chosen
minimum. Equal-length exchanges may change repeats temporarily and must
not be pruned merely for doing so. Those intermediate words remain complete
and <=871, so the unconditional credit bound still applies.

## 8. One precise missing lemma; all other implications proved

Here is a finite, exact proposed rewrite class, rather than “some suitable
surgery”. Vertices are Hamilton orders of all 720 permutations, evaluated
by their literal maximum-overlap spelling. Two orders are adjacent if
one selected permutation is deleted and reinserted at another position.
An arc is allowed iff spelling length does not increase. All such moves
preserve coverage. Equal-length adjacency is symmetric, so strongly
connected components are equal-length relocation plateaus. A finite
component can be certified by listing all vertices and all legal exits.

**MISSING — bounded repetition plateau-escape lemma (sufficient, not claimed):**
For every repeated FIRST-OCCURRENCE-GEODESIC FIXED POINT of length <=871
that is irreducible under equal-window coverage deletions, its equal-length
relocation plateau contains either

1. a word with fewer repeated permutation occurrences, or
2. an order with a single-vertex relocation of strictly smaller length.

Equivalently one can restrict to plateaus minimizing repeat count internally;
every such positive-repeat plateau must have a shorter exit. Its domain is
sharply constrained by R_rep<=27, the typed credit envelope, the seven
zero-credit repeating connectors and at most four charged connectors.
No port-only or coverage-count quotient is substituted for its full literal order.
The n=3 graph proves the required escape mechanism in that finite analogue.
The strict n=4 trap is not a counterexample because weak moves escape it.
The universal n=6 assertion is unproved; even universal single-vertex
relocation may be too restrictive and must be falsified before use.

**Why this ONE lemma is sufficient:** iterate the first-occurrence projection
to a fixed point. If a coverage-preserving equal-window deletion exists,
shorten and reproject to a fixed point. Otherwise apply the asserted escape. Its finite
equal-length path followed by an exit decreases `(length,repeats)`
lexicographically. Repeat. Length is a nonnegative integer and, at fixed
length, repeats are nonnegative (indeed <=27); this terminates at a complete
word with zero repeats. Projection after a strict shortening need not preserve
repeat count because the FIRST potential coordinate decreases. After a cleaner
word is found, project it again: if projection is length-neutral it preserves
that word literally (and its new repeat count); if shorter it improves the
first coordinate. Every intermediate
move is literal, coverage preserving and length nonincreasing. Confluence
is unnecessary. Thus the missing escape assertion alone implies threshold
NR6; no unproved outer closure is used in this implication.

This is a precise unresolved exchange problem, not a certified small local
hard core. Its exact state still contains global occupancy/order. A finite
automaton `(suffix,covered set)` alone does not supply NR6 representatives;
the required domination assertion would be the same unresolved content.
No phantom finite UNSAT or formal proof-assistant certificate is claimed.

## 9. Deliverables and separation of conclusions

Sources: `research_round141_nr6_codex.py`,
`research_round141_repeat_credit_codex.py`,
`verify_round141_nr_foundation_codex.py`,
`verify_round141_nr_geodesic_templates_codex.py`.
Evidence: `rr_round141_nr6_foundation_codex.json`,
`rr_round141_repeat_credit_codex.json`, `rr_round141_nr6_verified_codex.json`,
`rr_round141_nr_geodesic_templates_codex.json`.
They retain literal counterexamples, complete small rewrite domains,
normalization paths, input/source hashes and scopes. The publication manifest
records canonical committed sources separately from runtime hashes.

No older theorem saying visited implies registered is used on repeated
words. No capped continuation, endpoint-only symmetry, hidden-window omission
or guessed normalization establishes a proof here. There is no NR6'
replacement strong enough to invoke the old outer 55-grid yet.

Outer result: 55/55 under NR6. This result: unconditional repetition
localization and an explicit missing plateau-exchange lemma. Therefore the
combination STILL DOES NOT prove unrestricted `L6>=872`.

ASTRA_NR6_HARD_CORE
