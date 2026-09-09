# Round 140 — general free-exit charging, successor splicing, and the G=3 column

Author: CODEX. Date: 2026-09-09.

## Result and scope

**Hand proofs:** the stronger free-exit inequality `f_out <= F+e` and the
successor-splicing theorem below hold for arbitrary multiplicity G, not only
G=3. They require a no-repeat permutation word covering its touched rotation
classes completely. The application to all 720 permutations is conditional
on NR6; the reduction from unrestricted shortest superpermutations remains
an assumption.

**Computer-assisted corollary:** all four generic cells `(k,G)=(1,3),(2,3),
(3,3),(4,3)` are excluded at `L<=871`. Their 516 arithmetic resource rows,
or 580 heavy-refined rows, are covered by 40 conservative capacity envelopes.
Thirty-seven envelopes are strict. Three equality envelopes reduce to the
same complete 52-seam test; every seam repeats a hexagon.

Round 139 was NOT used as an assumed proof. Its proposed splice is re-proved
here, the needed new capacity cells are recomputed with two representations,
and the needed extremal seam domains are independently regenerated. Existing
independently established Round-115/136 capacities remain stated dependencies.
Round-139 source code reused as a producer is labeled as such, not evidence
of an externally accepted theorem.

The incoming **13/55** ledger was explicitly provisional. Adding four new
cells gives **17/55 PROVISIONAL**, with the same pending external Round-139
audit. This is not an upgrade of the inherited audit status. No G>=4 cell is
claimed closed in this round. **NR6 is ASSUMED. `L6>=872` is NOT PROVED.**

## 1. Definitions and the historical restriction

Use ACTUAL gaps between consecutive permutation windows. A pass is a maximal
rotation run; write it as `(v_i,l_i)`, in chronological order `0<=i<P`, where
`l_i` counts permutation windows. A full pass has length n. Every pass entry
is registered; a window visited internally by rotation need not be registered.

For n=6, E rotates the first five symbols and fixes the last. Its 144 orbits
have five ports each. A hexagon is a rotation class of six windows, not an
E-orbit. There are 120 hexagons.

S denotes the NUMBER OF PAID JOINTS (weight >=3), not the older convention
of strand count; the latter is S+1. H is `sum max(w-3,0)`. A run is a maximal
sequence of pass entries in the same E-orbit; if there are r runs and O distinct
opened orbits, `e=r-O` counts repeated run-opening EVENTS. Let x count paid
intra-run joints, and f_out count free (weight-2) inter-run exits. Then

`S = O+e-1-f_out+x`.

Define G as pass multiplicity, F as abandonment, and J as their difference:

`G=P-120=sum_h(m_h-1)`, `F=#abandonments`, `J=G-F`.

The Round-129 proof restricted its repeated-hexagon types and counted distinct
split-orbit names in its Type-A step. That suffices for G=2 but is unnecessary:
the repeat-run EVENTS are distinct even when their orbit names coincide.
No assumption of distinct repeat targets is used below.

## 2. General free-exit theorem (hand proof, all G)

Because the rotation classes are completely covered without repetition, the
passes in each hexagon partition its directed cycle. Define its successor
permutation nu by

`v_nu(i) = sigma^l_i(v_i)`.

Nu fixes a full pass and has one cycle of length m_h for each split hexagon.
Chronological ascents `i<nu(i)` are exactly abandonments. If d_h is the number
of descents in that cycle, it has `m_h-d_h` ascents, so

`J=sum_split_h(d_h-1)>=0`.

At a weight-2 joint with literal source `p'=sigma^(l_i-1)(v_i)`,

`target = flip(p') = E(sigma(p')) = E(v_nu(i))`.                 (2.1)

A full-pass free joint stays in its own orbit and is not an inter-run exit.
For a short free exit with `nu(i)<i`, the target orbit was opened at pass
nu(i), and the free exit changes orbit. Hence entry i+1 is a repeat RUN
opening. The map `i -> i+1` is injective across all hexagons. It does not
merge charges when the target orbit is the same.

Let A be the set of nu-ascents, U the set of free inter-run exits, and Rpt
the set of repeat run-opening events. Define

`Ord={i+1: i in U and nu(i)<i} subset Rpt`,
`a=|A\U|`, `eta=|Rpt\Ord|`.

The ascending free exits number F-a, the descending free exits number e-eta.
Thus the exact multi-defect identity is

`delta := F+e-f_out = a+eta >= 0`.                            (2.2)

Consequently, for every G,

`f_out <= F+e`,
`O = 1+S+F-delta-x <= 1+S+F-x <= 1+S+G`.                    (A)

An equivalent direct proof charges every first opening to initial entry,
a paid inter-run entry, or an ascending free exit. A blocked free target is
in the orbit of an already registered successor, not merely an arbitrary
visited window. This distinction is precisely what (2.1) and nu resolve.

### Cycle breaking, overlap, and Hall interpretation

If all short exits of a hexagon's nu-cycle are free, each of its descents
forces a separate repeat opening. For several such hexagons, the costs ADD:
the corresponding `i+1` events are distinct. The bipartite obligation graph
has a fixed distinct neighbor for each descending free exit, so Hall's
condition holds trivially. One event cannot pay two such obligations.

A paid ascent entering a previously opened orbit can, however, contribute
both a missing ascent and an exceptional repeat. These are two typed defects
at one joint. Equation (2.2), not an assumption of disjoint defect joints,
is the multi-defect accounting rule.

For G=0, no short pass exists and f_out=0. For G=1, nu is one transposition,
F=1, and its descending free exit is charged above. For G=2 the triple and
double-double cases have F=1 or 2, but the SAME injection proves their bound.
These recover the earlier special cases without F=G or orbit-name privacy.

In the proposed bounds of the request, `Psi=0` works for every multiplicity
pattern; x is unnecessary in the free-exit bound. Likewise `Phi(J)=0` is a
valid refinement. We do not claim a pointwise optimal negative correction
for every large J. The exact nonnegative defect in (2.2) is the proven result.

## 3. Active falsification and privacy with overlap correction

The newly generated complete NORMALIZED NR4 domain (first entry 0123,
all 24 permutations once, length <=39, minimum-overlap joints and no hidden
permutation windows) contains 29,255 words. It was exhausted in 49,682,345
nodes, not capped. This is not the whole unbounded set of all possible NR4
strings. The independent parser checks actual gaps, and additional nonminimal
gap controls cover that distinction.

No word violates (A) or (2.2). G ranges from 0 to 6, with counts
`827,5999,10625,7545,3384,629,246`. In particular 7,545 words have G=3.

Two tempting strengthenings are REFUTED by actual literal words:

* `delta>=J` fails on
  `012301202130210312032102031023103201320`:
  `(G,F,J,e,x,S,H,delta,f_out)=(3,2,1,2,1,2,2,0,4)`.
* Unqualified `delta>=q+s` fails for the fixed run-respecting cut before
  pass 8 in `012302313203120321032013231023012130213`:
  `delta=3`, designate all q=3 typed defects, s=1 shared orbit. The shared
  occurrence at entry 8 IS the designated exceptional repeat, not a new
  charge. This does not refute a qualified canonical-cut privacy theorem.

Here is the correct general privacy statement. Partition the ORIGINAL
chronological passes into run-respecting contiguous pieces. If an orbit
appears in r pieces, its first occurrence in each later piece defines r-1
distinct repeat-opening events. Over all orbits this injects the sharing
count s into an event set Gamma. Let q=a_d+eta_d be designated missing
ascents and exceptional repeats. Let

`o=|Gamma intersect Ord|`,
`z=|Gamma intersect designated exceptional repeats|`.

Then `eta >= eta_d+s-o-z`, and therefore

`delta >= q+s-o-z`.                                         (3.1)

The second counterexample has `(o,z)=(0,1)` and equality in (3.1). If o=z=0,
the desired q+s bound follows. Otherwise it must not be used.

For arbitrary paid cuts, even r-1 REPEAT-RUN events need not exist: the NR4
full-pass word `0123012013201` has two passes in one orbit, e=0 and x=1.
Cutting its paid intra-orbit joint gives s=1. Thus arbitrary extractions must
use the free-block identity in Section 6, which includes x, rather than the
run-respecting privacy lemma. This also covers sharing across more than two
pieces. No new universal privacy assumption is used in the G3 closure.

## 4. Complete local G=3 classification

The positive contributions m_h-1 sum to 3. The only partitions are 3, 2+1,
and 1+1+1:

| Type | Split multiplicities | Short passes | Possible F | Nu supports | Length-decorated supports |
|---|---|---:|---|---:|---:|
| A4 | 4 | 4 | 1,2,3 | 6 | 60 |
| A3B2 | 3,2 | 5 | 2,3 | 20 | 1,000 |
| B222 | 2,2,2 | 6 | 3 | 15 | 1,875 |
| Total | | | | 41 | 2,935 |

Supports are on the chronologically ordered SHORT occurrences. The first
occurrence anchors each nu-cycle; full occurrences inserted between them
only subdivide spliced edges. Interleavings are not omitted.

Ordered positive compositions of six have counts 10 (four entries), 10
(three entries), and 5 (two entries). Explicitly:

* Four: permutations of (1,1,1,3) or (1,1,2,2).
* Three: permutations of (1,1,4), (1,2,3), or (2,2,2).
* Two: (1,5),(2,4),(3,3),(4,2),(5,1).

Nu-support counts by F are A4 `1,4,1`, A3B2 `10,10`, B222 `15`.
Length-decorated totals by F=1,2,3 are **10,540,2385**. All cycle lengths
and ordered compositions are retained in `rr_round140_g3_codex.json`.
Only indistinguishable hexagon names/cycle notation are canonicalized; this
is a complete necessary LOCAL classification, not a claim that every support
has a global literal S6 realization or that histories can be quotiented.

## 5. Successor splicing from literal semantics (hand proof, all G)

Replace each pass by a FULL pass with the same entry. For each old chronological
joint `i -> i+1`, create the edge `nu(i) -> i+1`, with its original ACTUAL
appended tail and weight. The new full-pass source endpoint is

`sigma^-1(v_nu(i)) = sigma^(l_i-1)(v_i)`,

exactly the old literal joint source. The target entry is also unchanged.
Thus every retained seam, its hidden-window test, and its actual gap remain
identical. In particular a free edge becomes an E-step. No path shortening
or unproved maximum-overlap normalization is invoked. Positive overlap
(gap<n) is unique for two permutations; gaps >=n are kept as heavy edges
and later cut. At n=6, H<=3 excludes gaps >=7 in the relevant cells.

Every entry has indegree one except entry 0, and outdegree one except
nu(P-1). The graph therefore consists of one open path and directed circuits.
It is NOT yet a valid no-repeat word: full passes of repeated hexagons can
collide. We neither erase these occurrences nor pretend they are independent.
The path begins with the original first entry and ends at the original last
literal endpoint. Other component endpoints will arise only at documented cuts.

### Connected incidence theorem

Add one dummy vertex P. Extend nu by fixing it, put
`T=(0,1,...,P)`, and let `beta=T nu^-1`. Beta cycles are precisely the spliced
components, with the open path closed through the dummy. Write K for their
number. Form a bipartite multigraph with nu-cycles on the left, beta-cycles on
the right, and one edge per occurrence/dummy.

This graph is connected: a component is invariant under nu and beta, hence
under their product T, which is transitive. There are P+1 edges and
`(P+1-G)+K` vertices. Define

`R=sum_(hex h, component j) max(m_hj-1,0)`.

R is exactly the excess parallel-edge count; the singleton dummy contributes
zero. Collapsing parallel edges preserves connectivity. The simple graph
has at least V-1 edges, proving

`K+R <= G+1`.                                              (5.1)

Permutation signs also give `K = G+1 (mod 2)`. For G=3, K is 2 or 4.
The complete support distribution `(K,R)` is
`(4,0):11`, `(2,2):21`, `(2,1):8`, `(2,0):1`.
This is a hand theorem with an independent 46,233-permutation check through
support size eight, not a theorem inferred from those checks.

### Canonical, multiplicity-safe extraction

Use only event order and local collision, never desired capacity values:

1. Remove every all-free circuit. Such a circuit has exactly n-1 ports of
   one E-orbit. Entry uniqueness makes that entire orbit absent elsewhere.
   Let c be the number removed; `c<=K-1`. Each removed circuit is hex-simple.
2. Cut EVERY heavy edge. For any remaining circuit with no heavy edge, cut
   its paid edge having least source occurrence index. The circuit is not
   all-free, so such an edge exists.
3. Along each resulting path, split it into maximal free blocks. Traverse
   blocks from the path's start. If adding the next whole block repeats a
   hexagon already in the current piece, cut immediately before that block.
   Never cut a free block.

Every free block is hex-simple because distinct E-ports belong to distinct
rotation classes. Every additional cut charges a distinct non-first hexagon
occurrence within its ORIGINAL beta-component. Even if earlier heavy cuts
split a component, concatenate its resulting paths in any order for this
charge; a repeated occurrence in one piece remains non-first globally.
There are at most R such cuts.

If h is the NUMBER of heavy edges, the final number of light, hex-simple
full-pass chains satisfies

`m <= K-c+h+R <= G+1-c+h`.                                 (5.2)

All remaining entries are used exactly once. Repeated roles are retained in
different pieces, and no piece has a hidden duplicate; the only deleted
entries are the explicitly counted c pure-free circuits. These conditions,
not mere endpoint agreement, make this a multiplicity-safe extraction.

## 6. General master accounting and capacity inclusion

For n=6 the kept entries have

`P'=120+G-5c`, `O'=24+k-c`.

For piece j let O_j be its distinct orbits, D_j=5O_j-P_j its ACTUAL local
deficit, and b_j=e_j+x_j. Let

`s=sum_j O_j-O' = sum_Q(number of pieces containing Q-1)`.

All free blocks were preserved. The number of free blocks before removal is
`P-#free_edges = S+1`; removing a free circuit subtracts five entries and five
free edges, leaving this unchanged. Within a full-pass chain the free-block
count is O_j+b_j. Therefore

`sum b_j+s = S+1-O+c = delta-F+x+c`.                         (6.1)
`sum P_j = 120+G-5c`.
`sum D_j = 5k-G+5s`.                                       (6.2)

These are equalities, not privacy relaxations. They include repeated returns
to the initial orbit, repeated returns to the same other orbit, and sharing
in more than two pieces. Full-pass paid intra-run M3a contributes x_j; a
short M3a exit in the original walk is treated by its actual source/target
orbit, not silently declared an intra-run event after a rearrangement.

Since `L=844+G+S+H`, at L<=871 we obtain the general necessary master bounds

`sum b_j+s <= 4-G-k+c-H`,
`m <= G+1-c+h`, `0<=c<=K-1`, `K+R<=G+1`.                   (MASTER-G)

Every resulting chain lies in the established relaxed capacity model
`N*(b_j,0,D_j)`: a free full-pass joint is E; a paid intra-orbit full-pass
joint is a non-E phase jump costing one x token; a paid inter-orbit light
joint either opens a fresh orbit or consumes a repeat-entry token. The
model allows arbitrary non-E jumps, a superset of literal intra-orbit moves.
It forbids repeated hexagons and uses the ACTUAL local deficit, so the middle
parameter 0 is not a statement that other pieces use no ports of this orbit.
Their sharing is already in s and the `+5s` deficit term.

The port and whole-run implementations both permit q0 returns and repeated
entries to the SAME orbit. In the whole-run implementation every ordered
self-avoiding phase path is enumerated. A longer current run is represented
by its longer option; it is not charged an extra entry. Optimistic deficit
pruning erases the largest current orbit deficits with remaining entry tokens,
even if such returns are unreachable. This can only make completion easier.
There is no one-segment-per-orbit restriction and no suspect SKIP-COST or
`true_phase_walk_capacity` call in this replacement path.

Substituting G=2 recovers the proposed Round-139 master identity and the
K=1/3 topology. This re-proves its algebra as a corollary. It is a consistency
check, NOT a retroactive independent rerun of all Round-139 numerical results.

## 7. Outer cells and resources derived again

From (2.2),

`N=S+G-O=J+delta+x-1`,
`L=867+k+J+delta+x+H`.

At L<=871, all terms after k are nonnegative, hence k<=4. From
`P=120+G<=5O=120+5k`, we have k>=0 and 0<=G<=5k. Thus the 55-cell envelope
`sum_(k=0..4)(5k+1)=55` follows without assuming a G<=2 Theorem A.

For G=3 the four possible cells have

`P=123`, `O=24+k`, `D=5k-3`,
`L=870+k-F+delta+x+H`,
`delta+x+H <= F+1-k`.                                     (7.1)

| k | O | D | Arithmetic rows | Heavy-refined rows | Conservative master envelopes |
|---:|---:|---:|---:|---:|---:|
| 4 | 28 | 17 | 9 | 9 | 1 |
| 3 | 27 | 12 | 46 | 46 | 3 |
| 2 | 26 | 7 | 139 | 148 | 10 |
| 1 | 25 | 2 | 322 | 377 | 26 |
| Total | | | 516 | 580 | 40 |

For each type and F, enumerate nonnegative delta,x,H satisfying (7.1), then
`0<=f_out<=short_pass_count` and `e=f_out-F+delta>=0`. This is a complete
ARITHMETIC envelope; it does not assert every tuple has a literal realization.
The independent verifier instead loops e and f_out and checks the original
length equation, recovering exactly the same 516 rows. The bound e<=6 follows
from `e<=short_pass_count+1-k`, so its finite loop is justified.

Heavy refinements are H=0: none; H=1: [4]; H=2: [5] or [4,4]; H=3: [6],
[4,5], or [4,4,4]. Only their number h is used in (5.2). The order of heavy
joints is not quotiented in a search; these are order-independent envelopes.

## 8. Tight-cell first, then complete downward closure

For G=3 set `B=1-k+c-H`. For each K=2/4, c<K, heavy refinement, and sharing
`0<=s<=B`, the maximum local budget is b=B-s, total deficit is Dsum=5k-3+5s,
required passes P_req=123-5c, and `m_max=4-c+h`. With one piece s=0 necessarily.
Convolve capacity bounds over all nonnegative allocations of b and Dsum to
m_max pieces. Padding fewer pieces only relaxes the bound; capacities are
nonnegative and monotone in allowances.

The tightest cell k=4 forces K=4,c=3,H=0,b=s=0,m=1. It requires 108 passes,
but `N*(0,0,17)<=N*(0,0,18)=103`. This closes the whole cell, not only sampled
walks. The same MASTER-G expression then covers k=3,2,1 without introducing
marked-return models or new full NR6 searches.

Representative next bounds: k=3,c=2 needs 113 versus bound 108; k=3,c=3,H=0
needs 108 versus 98. At k=2,c=1 the requirement 118 exceeds 99. All precise
forty rows and every original row's envelope indices are preserved in the
certificate, including the looser envelopes needed at k=1. No row is omitted
because it lacks a canonical literal witness.

### The ONLY equalities

All three occur at

`K=4, c=3, H=1, heavy=[4], m=2, b=0, Dsum=12, P_req=108`,

with `(k,s)=(1,2),(2,1),(3,0)`. Formula (5.1) forces R=0. All three circuits
are pure-free and removed; the one remaining component is one hex-simple
path. Its actual single heavy joint splits it into TWO REAL pieces. This
is not an equality generated by padding or a conveniently selected cut.

The complete deficit convolution for `C0(d)+C0(12-d)` is <=108, with equality
ONLY at d=4 and d=8. Their exact maxima are 46 and 62. Extremal entries are
1 normalized chain at (46,4), 2 at (62,8). Enumerating both directions and
every literal weight-4 seam gives exactly **52**, all with a common hexagon.
The independent verifier enumerates all 720 symbol relabelings and filters
by exact weight/no-hidden-window semantics; it obtains the same 52. Sharing
an orbit is NOT a rejection here. Each failure is an actual hexagon collision.

Thus every G3 master envelope is excluded, and all four G3 cells close under
NR6. There is no remaining G3 hard-core model in this reduction.

## 9. Finite computations and independence

All production runs used committed, pushed sources, with remote HEAD checked
before the finite jobs. The runtime/source/binary hashes, compiler version,
argv, node counts, cap flags and deterministic result digests are in the JSON
artifacts. The 20-billion capacity caps and 2-billion NR4 cap were NOT reached;
a cap would have produced UNKNOWN_CAP, never a proof of absence.

Fresh ordinary capacity cells, computed twice:

| b | deficit cap | N*(b,0,D) | Port nodes | Whole-run nodes |
|---:|---:|---:|---:|---:|
| 0 | 7 | 58 | 72,776 | 9,482 |
| 1 | 7 | 73 | 3,962,874 | 408,800 |
| 2 | 7 | 88 | 107,920,651 | 10,722,957 |
| 0 | 2 | 33 | 461 | 54 |
| 1 | 2 | 48 | 25,258 | 2,283 |
| 2 | 2 | 63 | 657,849 | 57,925 |
| 3 | 2 | 78 | 12,721,335 | 1,117,335 |

These are seven finite equalities, NOT a conjectured `+15` extrapolation.
The smaller deficit caps in convolutions may deliberately use these looser
upper bounds. Existing uncapped R115 cells supply C0 through D=12, C0(D18)=103,
and the small b=1 cells. Independently established R136 b=1,D=13 supplies 98.

The endpoint/support producer freshly generated the D4/D8 extrema in 436 and
24,752 nodes. The independent fixed-target whole-run verifier regenerated
their COMPLETE extreme sets in 548 and 31,812 nodes, with the same 1/2 counts.
No external audit acceptance of the reused producer code is assumed.

Other complete finite domains:

* 46,233 abstract permutations through size eight validate the connected
  incidence construction, parity, and K+R inequality. Abstract permutations
  need not be literal NR6 realizations; this tests a broader graph identity.
* All n=4,5,6 permutations and pass lengths give 5,016 endpoint identities.
* 1,397 valid local insertion controls through three insertions at n=4/5/6
  replay, with full touched rotation classes. They are not a whole n6 census.
* All 29,255 NR4 words are replayed independently for free-exit accounting and
  spliced graph structure. The producer extracts pieces for ALL of them.
  The independent verifier additionally checks full piece replay for 594
  distinct recorded metric/topology representatives.
* Those 594 plus the 1,397 local controls and three actual nonminimal-heavy-gap
  controls give 1,994 separately serialized piece certificates.

The producer uses nu-based construction; the independent verifier rebuilds
the spliced graph by mapping each full-pass EXIT WINDOW to its old literal
joint, without calling producer parse/splice/support/convolution functions.
It independently checks connected incidence, all resource sets, deficit
allocations, capacities, complete extremal sets, and literal seam collisions.
This is implementation independence, not a claim of a completed external
researcher audit. An additional bounded mathematical review found no gap in
the graph/cut/equality implications; its producer-assertion concern is fixed,
and the stronger independent seam check was already present.

## 10. Artifact map and reproducibility

Source and result roles:

* `src/research_round140_g3_codex.py`: support/compositions, actual-gap splices,
  local controls, 516 resource rows, producer seam enumeration.
* `src/round140_nr4_controls_codex.c`: independent normalized NR4 enumeration.
* `src/run_round140_finite_codex.py`: committed-build paired capacity runs.
* `src/certify_round140_g3_codex.py`: literal census/extractions and 40-envelope
  certificate, including the two counterexamples.
* `src/verify_round140_g3_codex.py`: independent graph/literal/arithmetic/seam
  verification. It rejects capped inputs and checks unique equality splits.
* `tests/test_round140_g3_codex.py`: source-level and artifact regressions.

Artifact files (all under outputs/): `rr_round140_g3_codex.json`,
`rr_round140_nr4_codex.json`, `rr_round140_capacity_codex.json`,
`rr_round140_certificate_codex.json`, `rr_round140_verified_codex.json`.

Fast audit using preserved artifacts:

```powershell
python src/verify_round140_g3_codex.py
python -m unittest discover -s tests -p test_round140_g3_codex.py -v
python -m unittest discover -s tests -p 'test_round13*_codex.py' -v
```

The source/runtime committed hashes are distinguished in certificates; the
package manifest additionally binds final report, tests, source and result
files. No previous checkpoint, engine, supervisor, or broad NR6 search was
modified. No background research job remains necessary for this conclusion.

## 11. Final scope ledger

Both requested goals are achieved, with a stronger stopping condition:

1. Theorem A and the stronger `f_out<=F+e`: **PROVED, all G**.
2. General connected-incidence successor-splicing MASTER-G: **PROVED, all G**.
3. G3 local multiplicities and length shapes: **COMPLETE FINITE CLASSIFICATION**.
4. All four `(k,3)` cells: **COMPUTER-ASSISTED CLOSED under NR6**.
5. `delta>=J` and unqualified `delta>=q+s`: **REFUTED**, exact words preserved.
6. Remaining G3 hard core: **none within this reduction**.
7. Inherited Round139 audit: **still PROVISIONAL**; combined ledger **17/55
   PROVISIONAL**, not 17 independently externally accepted cells.
8. G>=4 numerical program: **not executed**. Full shortest-word reduction:
   **NR6 still assumed**. Global `L6>=872`: **NOT PROVED**.

ASTRA_GENERAL_SUCCESSOR_SPLICING_THEOREM
