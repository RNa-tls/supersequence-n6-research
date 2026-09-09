# Round 141A — all-G splice envelope and the 55/55 NR6-conditional closure

Author: CODEX. Date: 2026-09-10. This is the OUTER track; the separate NR6
track is `RR_ROUND141_NR6_REPETITION_REDUCTION_CODEX.md`.

## 1. Result, hypotheses, and inherited audit status

**Computer-assisted theorem, conditional on the stated NR6 model:** there is
no no-repeat literal n=6 superpermutation of length at most 871.
The accepted incoming 17/55 cells become **55/55**: 38 new cells close.
Every new finite enumeration completed; no capped result is an exclusion.
The two capacity representations independently return the same extremal
paths, and two different finite-cover algorithms exclude the remaining
completion instances. The 160 new arithmetic envelopes are recomputed
independently.

The user explicitly supplied independent confirmation of R139 and R140 in
this round's instructions. That updates the previous R140 **provisional**
17/55 starting status; we do not erase its historical qualification.
Previously accepted G=0,1,2,3 closures and R115/136 capacities are dependencies,
not new computations or new cells here.

**NR6 is still unproved.** This result does not establish the unrestricted
statement `L6>=872`. The known 872 witness supplies an upper bound and an
NR6 example, not an optimality proof. The second report explains exactly
why repeated-window words do not yet lie in this certificate's domain.

## 2. Definitions: use current, not historical, coordinates

Count every literal permutation window and its actual gap to the next one.
In this report only, each of the 720 permutations occurs once. A pass is a
maximal run of weight-1 rotations. E rotates the first five symbols and fixes
the last; it has 144 orbits of five possible pass-entry ports. A hexagon is
one of the 120 full six-symbol rotation classes.

S is the number of paid joints (weight at least 3), not strand count; the
old strand convention is S+1. H is the sum of max(weight-3,0).
G=P-120 is pass multiplicity. F is abandonment, not generally G.
For each repeated hexagon, its directed-arc successor permutation nu has
d_h chronological descents. Then

    J=G-F=sum_h(d_h-1).

Let O be opened E-orbits, k=O-24, e repeated run-opening EVENTS, x paid
intra-run joints, f_out free inter-run joints. The accepted all-G injection
gives delta=F+e-f_out=a+eta>=0, where a counts ascents lacking a free exit
and eta counts repeat run openings not paid for by descending free exits.

    L=867+k+J+delta+x+H.

Consequently k+J+delta+x+H<=4, and P<=5O gives 0<=G<=5k.
Thus k=0..4 gives 1+6+11+16+21=55 cells. k=0 forces G=J=0 and belongs
to the already accepted G=0 closure. The artifact lists all 56 slack tuples
for k=1..4 and the 35 k=0 tuples; it does not silently omit k=0.

## 3. The all-G topology and bounded residual normal form — hand proof

Use the R140 canonical successor splice, retaining actual joint sources,
targets and tails. Add the dummy endpoint; alpha is nu fixing the dummy,
T is the full chronological cycle, beta=T alpha^-1. K is the number of
beta components including the dummy path. Write R_int for duplicate
hexagon occurrences within components. Connected alpha/beta incidence gives

    K+R_int<=G+1,     K=G+1 (mod 2).

Let c be the number of pure-free circuits, each an entire E-orbit used
nowhere else. Define

    g=(G+1-K)/2,   d=K-1-c,   z=G-c=2g+d.

These are nonnegative integers. They are NOT the fragment graph's older
Betti number, and g need not vanish. We do not import a genus-zero claim
from another graph. R_int<=2g.

Cut heavy edges; cut the least-index paid edge in each remaining circuit;
then cut before the next whole free block whenever that block collides with
an earlier hexagon in its current piece. At most R_int such collision cuts
are needed. With h heavy joints, the resulting hex-simple full-pass light
chains obey

    m<=d+1+h+R_int<=z+1+h.

For piece j put b_j=e_j+x_j and D_j=5O_j-P_j. Retain the exact sharing
quantity s=sum_j O_j-(O-c), even for repeated returns to the same orbit.
The R140 free-block equalities become

    sum P_j=120-4G+5z,
    sum D_j=5k-G+5s,
    sum b_j+s=S+1-O+c<=4-k-z-H.                 (MASTER-141)

In particular z<=4-k-H and h<=H, so

    m<=5-k.

This is the required **G-independent bound on the NUMBER of residual
chains**, not a quotient of their literal states. Their occupancy, entries,
order and all sharing remain present. Up to c pure E-circuits are removed
with all five ports accounted for. Large G does not mean an unbounded
number of difficult chains. It changes the required pass count and deficit
of at most four chains (when k>=1).

### A sharper link with J

Every non-dummy beta circuit has a minimum chronological entry m>=1.
If v is its predecessor, beta(v)=m implies alpha(m-1)=v. Since v is in
that circuit, v>=m>m-1, so this is a distinct alpha ascent. Thus

    K-1<=F,       J<=2g.

For a pure-free circuit this selected original joint is also a free
inter-run ascent. Distinct circuits select distinct joints; hence c<=F-a.
Define omega=F-a-c>=0. Then the exact typed-defect identities are

    z=J+a+omega=2g+d,
    sum b_j+s=eta+x-omega.

They allow multiple charges at one chronological joint; there is no
assumption that missing ascents and exceptional returns are disjoint events.
Combining J<=2g<=z<=4-k-H proves **J<=2** for every remaining k>=1
candidate. In particular the proposed J=3 family is impossible BEFORE
capacity evaluation. For k>=3, g=0 and J=0. This sharper observation is
not needed to discard rows in the 160-envelope verifier: that verifier
keeps the larger conservative domain.

## 4. J normal forms and their limits

For a cyclic permutation of ordered support, exactly one descent means
the cycle lists that support in increasing order, with the final wrap.
Thus J=0 fixes the cyclic ordering separately in each split hexagon;
positive arc lengths still sum to six. It does NOT force independent,
noncrossing, laminar, or nested histories among different hexagons.

J=1 marks one hexagon with excess one (at least three ports). J=2 marks
either one excess-two hexagon (at least four ports) or two excess-one
hexagons. An exceptional hexagon has at most six ports, so at most 6J
exceptional endpoints are marked; ordinary endpoints are not discarded
or quotiented. J=3 formally has distributions 3, 2+1, 1+1+1, but the
topology/budget argument just given eliminates all three in this scope.

Self-falsification controls:

* J=0 need not imply g=0 or noncrossing. Literal NR4 word
  `012301203102130210312013201023103210` has successor cycles
  (1 5), (2 7), (4 8), with 1<2<5<7; G=F=3, J=0, K=2, g=1.
* z>=J is sharp: `012310213012023120312301320130210321023`
  has G=5,F=3,J=2,c=3,a=omega=0,z=2.
* Neither unrestricted privacy nor the global empirical +15 capacity law
  is assumed. A finite model has at most 120 hex-simple passes, so an
  unrestricted linear +15 law is impossible. More specifically the
  independently accepted b=1,D=15 capacity is 106, not 96+15=111.

The additional J identities have a 46,233-support check through size eight
and a check on the existing 29,255-word normalized NR4 corpus. Those checks
are falsification controls; the proofs above do not extrapolate from them.

## 5. Sharing, not privacy, in the capacity certificate

Build the bipartite graph piece <-> orbit, keeping also orbits occurring in
only one piece. If it has C_inc components and cycle rank beta_inc, then
E=sum O_j, V=m+(O-c) imply

    s=beta_inc+m-C_inc.

This is an exact Euler identity. Sharing across multiple pieces costs s
on the left of MASTER-141 and adds 5s to the summed deficit. It is not
prohibited. Every resulting chain lies in the accepted dominating
N*(b_j,0,D_j) model, including initial-orbit returns and repeated returns
to the SAME orbit. Full-pass paid intra-orbit moves consume x_j. A cut
never splits a free block, so no token is lost.

For each allocation define the finite convolution

    C(m,b,D)=max sum_j N*(b_j,0,D_j),
    sum b_j=b, sum D_j=D.

Use m=z+1+h and b=4-k-z-H-s as conservative upper budgets. Fewer actual
pieces/tokens are included by padding the upper bound; no literal extra
piece is claimed. Heavy patterns are enumerated by their actual weights
and summed excess H, not merely their number. The independent verifier
uses recursive convolution rather than the producer's composition loop.

## 6. Finite residuals: 160 envelopes, six equalities

The entire G>=4 grid has 160 conservative envelopes. 154 are strict;
six are equalities. They occur in six cells:

| k,G | z,H | summed D | required passes | possible extremal split |
|---|---|---:|---:|---|
| 1,4; 2,4; 3,4 | 0,1 | 11 | 104 | 46+58, deficits 4+7 |
| 2,7; 3,7 | 0,1 | 8 | 92 | 46+46, deficits 4+4 |
| 4,6 | 0,0 | 14 | 96 | one 96-pass chain |

At equality z=0 gives g=d=R_int=0: all other components are pure-free
circuits. With H=1 the residual is one actual hex-simple path cut at its
single weight-4 joint, not two arbitrary padded capacity pieces.

### Complete extreme-chain domains

Value-renaming makes the first entry 012345 without loss. All whole-run
and independently generated port-prefix paths to these limits were kept:

| passes,D | producer nodes | independent nodes | normalized paths |
|---|---:|---:|---:|
| 46,4 | 548 | 1,522 | 1 |
| 58,7 | 12,081 | 32,420 | 2 |
| 62,8 | 31,812 | 83,994 | 2 |
| 96,14 | 6,420,459 | 15,529,584 | 2 |

All cap flags are false. The 62,8 domain is retained as an extra verified
control; the final equalities do not require it. No +15 extrapolation
produced any of these paths.

For 46+58 and its reverse, all 52 literal weight-4 seams repeat a hexagon.
For 46+46, 12 of the 13 seams repeat a hexagon; **one is legal**. It must
not be suppressed as a collision. That seam uses 20 distinct orbits and
92 distinct hexagons. The seven removed pure-free circuits must be seven
distinct closed orbits covering the other 28 hexagons. A complete finite
set-cover check says UNSAT. For k=2 its zero sharing also already disagrees
with required s=1, but the cover exclusion is independently sufficient.

Each of the two 96-pass chains uses 22 distinct orbits. The six removed
pure-free circuits must cover the remaining 24 hexagons using six closed
orbits. Both complete cover checks are UNSAT.

These are NECESSARY static conditions only: a SAT cover would not prove
literal realizability. UNSAT is sufficient. The first solver chooses an
uncovered column; the independent solver uses binary include/exclude in
a fixed row order, suffix unions, and an optimistic top-gain bound. Both
are complete, uncapped. Distinct selected closed orbits may be padded to
exactly c when a <=c witness exists; at least c closed orbits are available.
Both 96-pass cases are checked by both solvers, and the one legal 92-pass
case is also cross-checked by both implementations in the test suite.

## 7. Full outer ledger and cutoff

| k | accepted G | newly closed G | closed / applicable |
|---:|---|---|---:|
| 0 | 0 | none | 1/1 |
| 1 | 0,1,2,3 | 4,5 | 6/6 |
| 2 | 0,1,2,3 | 4,5,6,7,8,9,10 | 11/11 |
| 3 | 0,1,2,3 | 4,5,6,7,8,9,10,11,12,13,14,15 | 16/16 |
| 4 | 0,1,2,3 | 4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20 | 21/21 |
| total | 17 | 38 | **55/55** |

Before any equality work, the master arithmetic already excludes every
applicable **G>=8**. This is a non-vacuous, all-J high-G cutoff at the
pre-equality stage, not a new universal statement about arbitrary long
walks. G=4,5,6,7 are then all closed as above; no ordinary outer hard core
remains. No new G-specific raw frontier or NR6 global DFS was used.

## 8. Artifacts, independence, and reproducibility

Primary scripts:

* `research_round141_outer_codex.py`: slack types and envelopes.
* `round141_extrema_codex.c` / `run_round141_extrema_codex.py`: whole-run producer.
* `round141_verify_extrema_codex.c`: separate literal port-prefix enumeration.
* `verify_round141_completion_cover_codex.py`: independent column-cover check.
* `verify_round141_outer_codex.py`: binary cover, heavy seams, full 55-cell ledger.
* `verify_round141_j_topology_codex.py`: additional topology falsification domain.

Machine evidence: `rr_round141_extrema_codex.json`,
`rr_round141_completion_cover_codex.json`, `rr_round141_outer_codex.json`,
and final `rr_round141_outer_verified_codex.json`. The preliminary envelope
JSON deliberately retains its six RESIDUAL_CORE cells; the final independent
ledger supersedes them with explicitly identified equality certificates.

The source was committed and pushed BEFORE the load-bearing runs. The
artifacts record exact source commits, SHA-256, argv, compiler/binary, nodes,
elapsed times and cap flags. Old CRLF runtime sources are not rewritten:
their hashes are separately labeled, and equality to the committed canonical
blob is asserted modulo newlines. The publication manifest adds current
artifact hashes. No old checkpoint, supervisor or continuation was modified.

## 9. Precise remaining dependency

NR6 is the existence of a globally shortest literal word with exactly 720
permutation-window occurrences. The useful threshold reduction is to
normalize every putative <=871 word without increasing length. This report
does neither. Repetition invalidates entry uniqueness, the old deficit
bound, and potentially the successor-permutation construction. The other
track proves a new repetition-credit bound but leaves a specific exchange
lemma open. Therefore **the unrestricted shortest length is not proved here**.

ASTRA_OUTER_55_OF_55
