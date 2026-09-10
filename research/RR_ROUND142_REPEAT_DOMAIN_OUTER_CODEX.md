# Round 142B — first-occurrence outer accounting, shadows, and light-clean closure

Author: CODEX. 2026-09-11. No NR6 assumption in the hand reductions below.
This report does NOT prove unrestricted L6>=872.

## B1. Fix the object before counting

For a covering word retain the first occurrence of every permutation. Trim
before the first and after the last retained occurrence. Its selected passes
are maximal consecutive weight-1 runs **among retained occurrences**.
They are not necessarily the original literal passes.

Each selected window appears once. In a rotation hexagon the selected arcs
are disjoint and cover its six vertices. Thus their next-arc map nu is a
permutation, one cycle per hexagon. H1/H2 in the brief are hand theorems,
not n4 extrapolations. Actual first-occurrence gaps give

    P=120+G, O=24+k, D_phi=5O-P=5k-G>=0,
    L=844+G+S+H.                                      (FO)

S counts paid joints w>=3, not strands. This proves H3. Compare with actual
literal counts from Route A:

    R+G_actual+S_actual+H_actual = G_selected+S_selected+H_selected.

Do not mix the two O/G values. In particular the Round141 repetition-credit
k bound originally used **actual** pass entries and did not automatically
bound selected O. We establish the selected bound below.

For finite connector classification one may iterate first-occurrence
maximum-overlap spelling. Length never increases. Equality forces identical
endpoints and gaps and hence the identical word; every nonfixed iteration
strictly decreases integer length. Every cover has a fixed representative.
Its selected gaps are at most six, all hidden permutation windows of a
selected connector occurred earlier, and all repeats are these hidden windows.
The repeat bound below is stated for this representative, not with a silently
preserved original R after changing the word.

## B2. Complete dirty light taxonomy

Let p be an original selected joint endpoint and v=sigma(p) the entry after
successor splicing. Functional composition below acts rightmost first.

| original appended relative tail | weight | spliced target | hidden windows | name |
|---|---:|---|---:|---|
| 10 | 2 | E(v) | 0 | clean tau |
| 01 | 2 | sigma(v) | 1 | A: dirty sigma |
| 012 | 3 | sigma²(v) | 2 | B: dirty sigma² |
| 021 | 3 | E(sigma(v)) | 1 | C: mixed E-sigma |
| 102 | 3 | sigma(E(v)) | 1 | D: mixed sigma-E |
| 120,201,210 | 3 | ordinary clean w3 targets | 0 | clean paid |

All heavier connectors are retained with their exact tails, then cut in the
capacity reduction. There are 719 nonidentity shortest connectors: clean/dirty
counts by weight 1..6 are **1/0,1/1,3/3,13/11,71/49,308/258**.
The independent removed-prefix enumerator also retains all 873 weight1..6
tail variants. This distinction matters: a longer connector can be clean
although its maximum-overlap version is dirty. All 720 simultaneous value
renamings verify **517,680** shortest endpoint pairs with no discrepancy.

Every dirty selected connector contains a repeated window and connector
interiors are disjoint intervals. Hence Q_dirty<=R, with coefficient one.
This assertion applies to actual selected gaps, or to the final fixed-point
word's own repeats. It does not compare a shortened connector's new repeats
against the original word's R.

## B3. Corrected free-successor theorem

A dirty w2 skips sigma(p), already first-seen earlier. That earlier selected
visit cannot be a rotation from p, since p is first appearing now. Therefore
sigma(p) is a selected pass entry. The possible current-pass case nu(i)=i
would make this a full six-window pass. The dirty target sigma^2(p) would
then already have appeared in that pass, contradicting its next first
occurrence. Thus nu(i)<i. The same argument applies to the hidden sigma(p)
of type B: after a full wrap its target sigma^3(p) is already selected too.
This explicitly excludes wraparound rather than assuming an earlier pass.
A clean blocked w2
targets E(sigma(p)), in the orbit of that registered earlier entry.

Let Y_d be the number of blocked **dirty w2** exits opening a fresh selected
orbit. Let Ord contain all descending free inter-run exits that do NOT open
a fresh orbit, and let eta=e-|Ord|. Every Ord event injects to its particular
repeat-run opening; repeated orbit names are not merged. If a counts missing
free ascents, then

    f_out=F-a+e-eta+Y_d,
    delta=F+e-f_out=a+eta-Y_d,
    f_out<=F+e+Y_d<=F+e+D2.                         (FREE-DIRTY)

This is the exact correction, with D2 counting type A. Delta can be negative.
The original clean theorem is recovered at D2=0. A dirty w2 is not a new
clean E edge merely because its target is a permutation.

## B4. Splice geometry and the dirty-genus charge — HAND PROOF

Replace each selected pass by a full pass with the same entry. Reassign the
old joint i->i+1 to nu(i)->i+1. The full source endpoint is unchanged:

    sigma^-1(v_nu(i)) = original literal joint source.

Every tail and hidden window is preserved, including dirty ones. Add the
dummy, alpha=nu extended by a fixed dummy, T chronological, beta=T alpha^-1.
The connected alpha/beta incidence proof gives

    K+R_int<=G+1,  K=G+1 mod2,
    g=(G+1-K)/2,  R_int<=2g.

R_int is within-beta-component duplicate-hex excess, not literal repeats.
Both type A and type B edges stay in the same hexagon. Since nu(i)<i,
their spliced edge nu(i)->i+1 is strictly forward in chronological index.
Thus these edges are acyclic. Within m copies of one hex in one component
they use at most m-1 edges. Consequently, with Qs=#type B,

    D2+Qs <= R_int <= 2g.                           (SAME-HEX)

This is stronger than merely charging dirty joints to literal R. No
all-dirty circuit is being discarded without justification.

Remove c circuits consisting solely of clean E edges. Each uses all five
distinct ports of its orbit, so that orbit occurs nowhere else. Put

    d=K-1-c>=0, z=G-c=2g+d, Z=z-D2.

Then **Z>=Qs>=0**. In particular dirty sigma³ in the original joint (type B)
forces a positive Z defect; it is not free. At Z=0, D2=2g is even and d=0.

## B5. Two valid capacity extractions

Extraction I cuts every heavy and every dirty joint, then opens remaining
circuits and separates repeated hexagons before whole clean E blocks. It
produces ordinary clean chains, but costs extra pieces for mixed dirty w3.
It must NOT silently consume the old clean-chain count bound unchanged.

Extraction II, used henceforth, retains types C/D. Cut heavy edges, open
every nonpure circuit, cut all same-hex dirty edges, then separate remaining
hex collisions at paid block boundaries. Whole clean E blocks are never cut.
The pieces are **marked hex-simple full-pass chains**, not asserted NR words.
Type D may require an already-visited external window; omitting that global
condition gives a safe necessary relaxation, not a feasible literal word.

There are at most d+R_int nonheavy cuts. To see the charge when a circuit is
opened at a same-hex dirty edge: that cut uses its circuit allowance, and
the remaining linear same-hex dirty cuts each decrease repeat excess by at
least one. The extra repeat excess not spent there pays for later block cuts.
Thus opening at a dirty edge cannot be charged twice as a saved repeat.

Writing h=#heavy joints, and b_j=e_j+x_j in each resulting piece,

    m<=d+1+h+R_int<=z+1+h,
    s=sum O_j-(O-c)>=0,
    B*=sum b_j+s=S+1+D2-O+c>=0,
    sum P_j=120+G-5c,
    sum D_j=5k-G+5s.                               (EXTRACT)

Reason for the new D2 term: retaining only clean E edges gives exactly
S+1+D2 free path blocks. Deleting a pure E circuit removes equally many
vertices and E edges and changes no block count.

Substitute into FO to obtain the **exact identity without NR6**

    L=867+k+Z+H+B*.                                (MASTER-142)

Every summand after 867 is nonnegative. Therefore every <=871 fixed-point
candidate again satisfies

    0<=k<=4, 0<=G<=5k<=20, Z+H+B*<=4-k.

The 55-cell coordinate grid survives, but its clean capacity closures do not
automatically survive: m may now be as large as 5-k+D2, and pieces may be marked.

## B6. Injective mixed-shadow theorem — HAND PROOF

In one marked hex-simple piece, a type C edge v->E(sigma(v)) has shadow
port g=sigma(v). It belongs to the target orbit, but cannot be a piece entry:
its hexagon is already represented by v. A type D edge v->sigma(E(v)) has
shadow g=E(v), in the source orbit, but cannot be a piece entry because its
hexagon is represented by the target. Both are permanently absent ports
of opened piece orbits.

Within each type the shadow map is injective. A collision between types
would give g=sigma(v)=E(u). The second edge's target is sigma(g)=sigma²(v),
in the same hexagon as the first edge's source v, a different permutation
for n>=3. That contradicts piece hex simplicity. Therefore the two types
also cannot share a shadow:

    retained mixed edges in piece j <= D_j.        (SHADOW)

The mixed edges removed at cuts must also be counted. All D2+Qs same-hex
dirty edges are among the at-most d+R_int nonheavy cuts, leaving

    cut mixed edges <= d+R_int-D2-Qs <= Z-Qs.

If Qm is the TOTAL mixed count, including removed edges,

    Qm <= sum D_j+Z-Qs.                            (MIXED)

This avoids the false shortcut of charging removed mixed edges to a
piece they no longer belong to.

## B7. Improved repeat bound: 27 -> 20

For the fixed-point word let t=L-867. Its repeats are exactly connector
interiors. Types A/B/C/D contribute 1/2/1/1. If Rh are hidden windows in
heavy joints, then Rh<=3H (each w>=4 has at most w-1<=3(w-3)). Hence

    R = D2+2Qs+Qm+Rh,
    sum D_j =5k-G+5s <=5t-G-5Z-5H,
    Qm <=5t-G-4Z-5H-Qs,
    R <=5t-c-5Z+Qs-2H <=5t-c-4Z-2H.               (REPEAT-20)

At L<=871,

    **R<=20-c-4Z-2H<=20.**

This is a normalization-domain bound: every hypothetical short cover has
a fixed representative satisfying it. It is not permission to delete seven
repeat positions from an arbitrary original word. The general n>=4 formula is

    R <= (n-1)(L-B_n)-c-(n-2)Z-(n-4)H,
    B_n=n!+(n-1)!+(n-2)!+n-3.

At n4,L=33 it forces R=0, supplying a structural explanation independent
of the older single-repeat layout check. At n5,L=153 it gives R<=4, not R=0;
the n5 all-optima-NR phenomenon is not explained completely here.

The independent shadow checker validates 196 constructed/frozen fixed-point
controls, including 231 mixed edges (172 retained, 59 cut). Random-order
controls are explicitly bounded constructions; no threshold absence is
inferred from their count. The proofs above provide the universal statements.

## B8. The outer theorem DOES extend to light-clean first-occurrence orders

Define LC: every selected w2/w3 joint is clean; heavy joints may be dirty.
This is strictly weaker as a structural condition than literal NR. For
example inserting a complete rotation detour into an NR cover produces
repeats absorbed into a longer selected heavy connector and leaves all
remaining light joints clean.

Under LC, D2=Qs=Qm=0 and Extraction II is the old clean-piece extraction.
All-G accounting and capacity inclusion apply. We did **not** inherit the
old G<=3 engine exclusions, which enforced clean heavy joints. Instead
recomputed **300** necessary arithmetic envelopes across all 55 cells:

    276 strict, 21 equalities, 3 initially loose bounds.

The three loose cases are G0 with two w4 joints: a three-chain bound125
against120. All unresolved envelopes have z=0, b=0. Thus every residual
nonpure component is the one hex-simple path; its one/two heavy joints are
actual seams. Full domains down to five passes below the extrema suffice
for the loose cases, not just exact maximizers.

Twenty narrowly specified ordinary-chain domains were completely enumerated
twice (whole-run and independent port-prefix). Examples: (28,D2) has2 paths,
(41,D4) has2, (70,D10) has8, (74,D11) has10, (83,D12) has4; (96,D14) retains2.
All node caps were unhit. No new whole-cover DFS was used.

The two seam generators use removed-prefix tail permutations versus all720
value maps/string overlap. **Both include dirty w4 tails.** Their exact
transcripts agree:

| G,H | seam attempts | dirty attempts | full disjoint paths |
|---|---:|---:|---:|
| 0,1 | 672 | 308 | 0 |
| 0,2 | 936 | 429 | 0 |
| 1,1 | 768 | 352 | 0 |
| 2,1 | 576 | 264 | 0 |
| 2,2 | 336 | 154 | 0 |
| 3,1 | 96 | 44 | 0 |
| 4,1 | 96 | 44 | 0 |
| 6,0 | 0 | 0 | 2 |
| 7,1 | 24 | 11 | 1 |

There are 3,504 seam attempts, including1,606 dirty. Early disjoint prefixes
in three-chain cases are not full paths. The only three full survivors are
the already independently rejected static completion instances: two96 chains
and the one92 chain. Thus:

> **Computer-assisted theorem, no NR6 assumption:** every n6 covering word
> whose first-occurrence structure is LC has length at least872.

Only the sufficient **structural condition** is proved. The normalization
“every cover can be transformed into LC at no cost” is UNPROVED. Calling LC
NR6' does not prove that missing implication.

## B9. Small genuine marked capacities and unconditional869

Retain C alone (model A) or C/D with external-shadow obligations relaxed
(model AB), with b=0 and D=0..5. Independent whole-run and literal-port
implementations both exhaust and give

    20,20,33,33,46,46

for BOTH models. This finite agreement does not assert equality of marked
and clean capacity functions at other budgets. At D5 the AB counts are
4,116 /12,601 nodes. Every maximal witness is checked; AB is not relabeled
a literal feasible first-occurrence path when external occupancy is absent.

These small marked tables and MASTER-142 exclude all words of length<=868
without NR6, in a14-row independently recomputed ledger. The complete proof
is `RR_ROUND142_UNCONDITIONAL_869_CODEX.md`.

**End-to-end currently proved in this round: 869<=L6<=872.**
Lengths869,870,871 and NR-UNIVERSAL(6) remain open.

## B10. Exact finite dirty hard-core representation; NOT four solved instances

Every hypothetical <=871 cover has a fixed representative with at most140
selected passes, at most28 opened E-orbits, at most20 repeated windows, and
at least one of A/B/C/D. A lossless CSP may retain distinct entry ports v_i,
positive arc lengths summing to6 per hex, actual/minimum tails, and chronological
first-appearance constraints on every hidden window. Spelling these data and
checking all720 selected vertices gives an exact verifier. Budgets are FO,
MASTER-142, SAME-HEX and MIXED; no quotient of occupancy/history is allowed.

The earliest dirty light joint partitions this domain into four disjoint
tagged families A/B/C/D. This is a finite local alphabet and a genuine
reduction after closing LC, **not four fixed-size SAT instances already
exhausted**. Later dirty events, chronology, shadows in other pieces and
same-hex sigma couplings remain present. We do not claim the requested
strong D-tier global hard-core completion from this local partition.

New proof targets can now address nonempty marked-chain domains: for example
the cost of coupling two sigma-cut endpoints, or sharp shadow-capacity bounds.
They must be proved on those domains, not renamed as “no <=871 cover.”
