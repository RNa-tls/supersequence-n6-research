# Round 139 — successor splicing closes the remaining G=2 cells under NR6

Author: CODEX. Final proof of this extended research round.

**PROVED, using explicitly identified FINITE-EXHAUSTIVE capacity/seam inputs:**
there is no NR6 covering walk with G=2 and L<=871. In particular, the two
previously open cells `(k,G)=(2,2)` and `(1,2)` close. The same argument
recovers `(3,2)` and `(4,2)` without their case-specific privacy lemmas.
The conditional outer ledger advances **11/55 -> 13/55**, not by four.
NR6 remains assumed. This is NOT a proof of `L6>=872` for unrestricted
superpermutations, nor a closure of the remaining G>=3 cells.

The companion `RR_ROUND139_G2_K2_MULTIDEFECT_CODEX.md` records the initial
73-row reconstruction, typed delta identity, failed unconditional privacy
extension, marked-return computations, and intermediate 60-row reduction.
That was not the stopping point. The proof below replaces the difficult
canonical-gap case analysis with an exact operation on ALL pass entries.
It is the load-bearing final inclusion theorem. No N1*, N2*, new NR6 DFS,
or empirical +15 law is used.

## 1. Definitions and original resource budget — PROVED

Trim characters before its first and after its last permutation window.
The original complete no-repeat word has maximal passes `(v_i,l_i)`,
indexed i=0,...,P-1 in chronological order. Every rotation hexagon is
partitioned into its visited directed arcs. Define nu(i) by

    v_nu(i) = sigma^l_i(v_i).

Full passes are fixed points. Nontrivial nu cycles are exactly the split
hexagons. G2 means either one 3-cycle (Type A, F1 or F2), or two 2-cycles
(Type B, F2). Entry words are distinct, regardless of re-entry into an orbit.

Weights here are ACTUAL appended character counts between consecutive
permutation windows, not a normalization assumption. Let S be the number
of joints of weight >=3, H=sum(weight-3)_+, and O the
number of E-orbits containing pass ENTRIES. F remains abandonment, not G.
Counting literal windows and appended characters gives

    P=122, O=24+k, D=5O-P=5k-2,
    L=846+S+H.

Therefore every counterexample to the desired lower bound has
`S+H<=25`. Extra removable prefix/suffix characters only weaken this
necessary condition; the trimmed literal word gives equality above.

The earlier derivation remains valid:
`delta=a+eta=F+e-f_out` for arbitrary delta, and at k2
`delta+x+H<=F`. But the master proof will not need to decide which literal
joint realizes each typed defect.

## 2. The successor-splicing operation — PROVED, exact literal endpoints

Replace every pass by a FULL pass with the SAME entry v_i. Do not claim that
these full passes in the OLD order form a legal word. Instead reassign the
original joint `i -> i+1` to the directed edge

    nu(i) -> i+1,

retaining its exact literal target and weight. This is legitimate because

    sigma^(6-1)(v_nu(i))
        = sigma^(-1)(sigma^l_i(v_i))
        = sigma^(l_i-1)(v_i),

the original joint source window. The endpoint pair, ACTUAL appended tail
and weight, and absence of intermediate permutation windows are identical.
This works for EVERY joint weight, not just the light tails. It is not the
historically invalid substitution of a macro-entry for a literal joint source.

No unproved maximum-overlap normalization is required: if an actual joint
has weight w<6, its positive overlap is unique, since the first target
symbol occurs in exactly one source position. Thus these joints coincide
with the engine's maximum-overlap moves. Gaps >=6 need not do so, but all
are heavy and will be cut before capacity inclusion. MASTER forces H<=3,
so gaps >=7 cannot occur in a candidate; weight6 is already covered by the
heavy partitions. The equality seams have weight4<6 and are unaffected.

Every vertex still has indegree at most one and outdegree at most one. Vertex
0 has no incoming edge; vertex nu(P-1) has no outgoing edge. Thus the result
is one directed path and some disjoint directed circuits, not an asserted
single Hamilton path. The pass-entry multiset, orbit union, S and H are
unchanged at this stage. A circuit is treated as a graph until an edge is
cut; it is not called a no-repeat linear word including a repeated closure.

Crucially, EVERY weight-two edge is now the literal full-pass E edge:

    v_(i+1) = E(v_nu(i)).

No state quotient or guessed orbit permutation is involved.

## 3. Complete G2 topology — PROVED by five support cases

Adjoin a dummy vertex linking the old last pass to the old first pass.
The extended successor is the single chronological cycle T before splicing
and `T compose nu^(-1)` afterwards, with nu fixing the dummy. Removing the
dummy gives the path component. The nontrivial support has only three or
four vertices. Inserting ordinary full passes merely subdivides its edges,
so the following exact five-case calculation proves the general topology:

| nu support | spliced components | repeated-hex entries |
|---|---|---|
|Type A, chronological 3-cycle (F2)|path + 2 circuits|all three in different components|
|Type A, reversed 3-cycle (F1)|one path|three entries may repeat that hex on the path|
|Type B, disjoint pairs|path + 2 circuits|each pair separated across components|
|Type B, nested pairs|path + 2 circuits|each pair separated across components|
|Type B, crossing pairs|one path|both pairs on the path|

The machine table contains the actual support permutations and components.
It covers all 2 three-cycles and all 3 matchings of four ordered endpoints.
The subdivision argument is the unbounded proof, not a sample of long walks.

In the three-component case EVERY component is hexagon-simple: unsplit
hexagons have only one vertex globally, and the table separates all copies
of each split hexagon. In the one-path case only the original multiplicity
excess two can cause hexagon repetition. No unspecified crossing/nesting
case remains, including Type-A F1.

## 4. Free E-path decomposition and exact defect budget — PROVED

Retain only the weight-two edges of the spliced graph. Each such edge
advances one E phase. Because each registered port is unique and E has order
five, a free directed circuit must contain exactly all five ports of ONE
E-orbit. Such a circuit is already an entire component of the spliced graph:
none of its vertices has room for any additional incoming/outgoing joint.

Let c be the number of these pure-free circuits. Then c is 0,1,2, and c=0
in the one-path topology. Remove them. Each removes five entries and one
orbit from the GLOBAL union; none of its orbit can occur elsewhere, because
all five distinct ports have been removed. Consequently

    P' = 122-5c,        O' = 24+k-c,        D'=5k-2.

These removals are performed on disjoint graph components. They need not
be contiguous locked blocks in the original chronological word. That is
why this operation avoids the older difficult canonical-contraction premise.

All remaining free components are paths. Their exact number t is

    t = P - (#weight-two joints) = P-(P-1-S)=S+1.

Removing free circuits changes vertices and edges by the same amount and
does not change t. Every remaining orbit has at least one free path. Hence

    t-O' = S+1-O+c >=0.

This counts extra FREE-PATH blocks, not distinct return target names. It
automatically accounts for aligned paid ascents, fused M+R joints, arbitrary
ordinary returns, repeated targets, full-pass x moves, and heavy in-orbit moves.

## 5. Canonical cutting to literal light chains — PROVED

Cut every heavy edge. For every remaining circuit with no heavy edge, cut
one paid edge, chosen by smallest original source index. A non-pure-free
circuit has such an edge. These cuts never split a free E-path block.

In the three-component topology the pieces are already hexagon-simple.
If h is the NUMBER of heavy joints (not H), the number m of resulting light
chains is at most

    m <= 3-c+h.

A circuit containing heavy edges needs no additional paid cut; this only
reduces m from the displayed upper bound.

In the one-path topology, also separate repeated hexagons. Scan its FREE
E-PATH BLOCKS in path order (after heavy cuts); whenever the next block
contains a hexagon already seen in the current chain, cut the paid edge
before that block and restart the seen set. An individual free block cannot
repeat a hexagon: the five phases of an E-orbit belong to five distinct
rotation hexagons. Each extra cut charges a distinct non-first occurrence
of a split hexagon. There are at most G=2 such occurrences, so at most two
extra cuts. Again `m<=3+h=3-c+h` because c=0 here.

Every resulting chain is now a LITERAL full-pass, no-repeat, all-light word:
its hexagons are distinct and every retained joint has the original exact
literal endpoint pair. Cutting before a whole block, not at an arbitrary
pass, is essential. No orbit-disjointness test chooses these cuts.

For chain j let b_j=e_j+x_j, O_j be its registered orbit count, and D_j=5O_j-P_j.
Define the orbit multiplicity across pieces by

    s = sum_j O_j - O' = sum_Q(number_of_pieces_containing_Q - 1).

The number of free blocks within chain j is exactly O_j+b_j: runs contribute
O_j+e_j, and every intra-run paid joint splits one further free block.
No chosen cut split a free block, so summing gives the central EXACT identity

    sum_j b_j + s = S+1-O+c.                       (MASTER)

Together with S+H<=25 this gives

    sum_j b_j+s <= 2-k+c-H,
    sum_j P_j = 122-5c,
    sum_j D_j = 5k-2+5s,
    m <= 3-c+h.                                   (M139)

This is the requested general privacy/contraction theorem, in a different
representation. It retains shared orbits as s instead of assuming s=0.
In terms of the earlier coordinates, the exact right-hand side of MASTER
is `delta-F+x+c`. The +5s deficit penalty is therefore paid out of the
S-budget. It cannot be charged twice or silently ignored.

Since the left-hand side is nonnegative, `k+H<=2+c<=4`. Thus k>4 is excluded
already, while D>=0 and G2 force k>=1. No extra G2 outer cell is omitted.

## 6. Capacity inclusion — PROVED

Each produced chain belongs to the established N*(b_j,0,D_j) relaxation.
Its full free transitions advance E; paid light cross-orbit joints are
201/210; full 120 is an intra-orbit non-E step. N* even permits arbitrary
non-E phase jumps at one b token, so it contains all these literal chains.
Its permanent deficit is the chain's ACTUAL D_j, including ports used in
other chains as absent from this one. Thus no unproved g=0 privacy assumption
is being imposed. Sharing is accounted for in sum D_j by 5s.

Independently bounding each chain can only enlarge the feasible family.
Value-renaming S6 normalization of its first entry is proved equivariant;
there is no arbitrary orbit relabeling. Whole-chain capacity maximizers need
not concatenate unless an equality seam test explicitly checks that.

The final proof uses only ordinary N* values and two small equality seam
domains. It does NOT consume the intermediate R_X/R_H computations,
Round138 privacy, N1*, or a guessed +15 theorem.

## 7. New and retained finite capacity certificates

New load-bearing values:

| b,g,s | maximum | R115 port nodes | independent whole-run nodes |
|---|---:|---:|---:|
|2,0,8|92|271,115,024|27,453,775|
|2,0,3|63|1,696,230|156,820|
|3,0,3|78|34,921,301|3,200,244|

All runs exhausted below their stated node caps; none is UNKNOWN_CAP. The
independent implementation uses literal lookup geometry, whole-run port
permutations and explicit per-orbit occupancies rather than the producer's
port DFS and deficit histogram. Disabling the new token range reproduces
N*(0,0,8)=62, N*(1,0,8)=77 and N*(0,0,3)=33, N*(1,0,3)=48.

Retained verified values include N*(1,0,13)=98, N*(0,0,18)=103, the C0 table
at deficits 0..13, and C1 at the smaller deficits. Each actually consumed
cell and its provenance is listed in the JSON. The convolutions use stored
cell values, not a +15 extrapolation. For some k1 two-chain cases the safe
bound N*(2,0,d)<=63 for d<=3 is intentionally used in place of an exact
small-d table; the resulting loose upper bound 96 still suffices.

All source/executable/argument/node/digest records distinguish committed blob
bytes from historical CRLF working-tree bytes. New C jobs were committed,
pushed and remote-HEAD checked before launch. No full-word n6 search occurred.

## 8. Equality seams, including shared orbits — FINITE-EXHAUSTIVE

There are only two equality shapes in M139, and both require c=2. The two
removed free circuits leave ONE literal full-pass path, so its remaining
heavy seams really connect the capacity pieces in order. No artificial
cycle cut or repeated-hexagon cut has intervened.

**E2:** two ordinary chains, total deficit13, required passes112, one w4 seam.
The only maximal split is 46/66 at deficits4/9 (either order). All 312 genuine
literal w4 seams collide in HEXAGONS. This rechecks candidates rejected by
the older orbit-first test instead of assuming that shared orbits are forbidden.
The result remains valid for s=0,1 OR 2 as needed in the various k cells.

**E3:** three ordinary chains, total deficit8, required passes112, two w4 seams.
All maximal splits are permutations of (20,46,46) with deficits(0,4,4), or
(33,33,46) with deficits(2,2,4). The first seam has 78 possibilities; 70
have hexagon collisions and 8 survive. The 8 pairs generate 104 second seams,
ALL with a hexagon collision. In particular, all orbit-collision rejections
from the earlier private test were independently checked to collide in hexagons
as well. This is necessary for k1, where s=1 is allowed. Three of the final
104 attempts have s=1 and fail literally, not merely by orbit sharing.

The independent verifier regenerates the complete E3 extremal sets
port-by-port and the E2 deficit4/9 sets by the retained independent
run-level recurrence (548 / 82,162 nodes, 1 / 12 extreme chains). It
compares the complete sets against the producers and rebuilds all seams.
Saturation of a numerical capacity alone is never declared UNSAT.

## 9. Complete k2 reduction — 10 conservative master envelopes

Let B=2-k+c-H. For each allowed s, allocate at most B-s local b tokens and
total deficit D+5s. Fewer than m_max actual chains may be padded by empty
formal pieces of zero budget; allowing a capacity value for such a piece
only increases the upper bound. The JSON lists every resource envelope.

| c | H | s | max light pieces | required P | upper bound / resolution |
|---:|---:|---:|---:|---:|---|
|0|0|0|3|122|112 <122 (both support topologies)|
|1|0|0|2|117|107 <117|
|1|0|1|2|117|112 <117|
|1|1|0|3|117|112 <117|
|2|0|0|1|112|92 <112|
|2|1|0|2|112|107 <112|
|2|1|1|2|112|112, E2 eliminates equality|
|2|2 (one w5)|0|2|112|92 <112|
|2|2 (two w4)|0|3|112|112, E3 eliminates equality|

This covers ALL original 73 resource rows / 78 heavy-refined tuples,
including the former F1 and delta2 core. There is no assumption of a
successful ordinary contraction order in the original word. `(2,2)` closes.

## 10. Automatic k1 corollary, and recovery of k3/k4

Use the SAME M139 with D3 and B=1+c-H. This gives 24 conservative envelopes:

* c0: H0 with s0/s1, or H1 with s0. Bounds are 88,112,93, all <122.
* c1: H0 has s0/s1/s2 and bounds96/107/112; H1 has bounds88/112;
  H2 has bounds73 or93 depending on its heavy multiset. All are <117.
* c2,H0: N*(3,0,3)=78<112.
* c2,H1: bounds96,107 for s0,s1; s2 uses E2 at equality112.
* c2,H2: one w5 gives68/92; two w4 gives88 for s0 and E3 for s1.
* c2,H3: heavy multisets `[6]`, `[5,4]`, `[4,4,4]` give53,73,93, all <112.

Thus `(1,2)` closes as an automatic application, not a separate exploration.
For k3 only three envelopes survive the elementary nonnegative budget:
c1,H0 ->112<117; c2,H0 ->98<112; c2,H1 ->E2. For k4 only c2,H0 survives,
giving103<112. These recover the accepted k3/k4 closures as corollaries.

## 11. Adversarial checks and certificate scope

The finite source-support table is exhaustive; its edge-subdivision proof
covers arbitrary pass counts. Endpoint identities are checked independently
for every permutation and every pass length at n4,n5,n6 (5,016 tests).

The literal splice operation is separately checked on 1,510 distinct
preserved G2 words: all 1,506 NR4 controls and four local n6 G2 sharing/fusion
counterexamples. This includes the 94 controls which defeated the earlier
one-gap reduction domain. Every spliced edge, deleted orbit, full light
piece, repeat multiplicity, and the exact b+s and deficit identities is
recomputed. A second verifier builds successors by an EXIT-WINDOW lookup,
not by the producer's nu-index reassignment.

These finite controls are not substitutes for the universal proof in
sections 2-6, and are not complete NR6 counterexamples. The only new
load-bearing exhaustive searches are the narrowly specified ordinary chain
capacity models and extremal seam domains. Caps are recorded and never
used to assert absence. Existing old search checkpoints are untouched.

## 12. Final scope and research outcome

This round began with explicit resources, typed a/eta bookkeeping, event-CSP
counterexamples to naive q+s, and marked root-return capacities. It did not
stop at that partial result. Successor splicing is the decisive change of
representation: ALL multi-defect mechanisms are absorbed into the exact
free-block identity, and only 38 conservative envelopes remain across k1..4.

No general +15 law is claimed; the unrestricted law is already impossible
at b7 because 20+15*7>120 in a hexagon-simple chain. The intermediate
R_X/R_H tables remain valid finite results but are not proof dependencies.

**Final:** the entire G2 column is excluded for NR6 words with L<=871.
New outer closures: `(2,2)` and `(1,2)` only. Conditional ledger: **13/55**.
NR6 remains ASSUMED. No conclusion about G>=3 or removal of NR6 is made.
The project has NOT proved `L6>=872` globally.

ASTRA_G2_K2_AND_K1_CLOSED
