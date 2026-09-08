# Round 139 — two-defect bookkeeping, one-defect normalization with decorations

> **Historical intermediate phase, superseded within this same round.**
> The 60-closed/13-open resource ledger below is not the current result.
> The final [successor-splicing master proof](RR_ROUND139_SUCCESSOR_SPLICING_MASTER_CODEX.md)
> closes all 73 k2 resource rows and automatically k1. It replaces, rather
> than assumes, the delicate original-order normalization in section 5.
> Current conditional outer ledger: 13/55; NR6 still assumed.

Author: CODEX. Scope: `(k,G)=(2,2)`, NR6 assumed. No full NR6 DFS.

This report distinguishes hand proofs (PROVED), completed finite models
(FINITE-EXHAUSTIVE), observations (EMPIRICAL), open proposals (CONJECTURE),
and false extrapolations (REFUTED). A resource row is an arithmetic envelope,
not an assertion that a word realizing that row exists.

## 1. Independent resource reconstruction — PROVED

`G` is multiplicity excess, never abandonment `F`. At k=2,G=2:

    P=122, O=26, D=8,
    S=25+e+x-f_out,
    L=871+e+x+H-f_out = 871-F+delta+x+H.

Consequently `L<=871` is EXACTLY `delta+x+H<=F`. The possible total slack
q=delta+x+H is 0,1,2. Type A is a tripled hexagon (three short passes),
F=1 or 2; Type B is two doubled hexagons (four short passes), F=2.
Enumerate `0<=f_out<=3/4`, `e=f_out-F+delta>=0`, and x,H,delta>=0.
These inequalities bound e, so no artificial e cutoff is required.

| delta | x | H | Distinct resource rows |
|---:|---:|---:|---:|
|0|0|0|8|
|0|1|0|8|
|0|0|1|8|
|0|2|0|5|
|0|1|1|5|
|0|0|2|5|
|1|0|0|11|
|1|1|0|7|
|1|0|1|7|
|2|0|0|9|

Thus 73 rows; splitting each H2 row into `[5]` versus `[4,4]` gives 78
tuples. The q histogram is 8/27/38. A separate evaluator enumerating
e,f_out,x,H and testing the original length formula reproduces the set.
These reproduce, rather than assume, the Round129 numbers.

## 2. General defect identity — PROVED, no delta=1 hypothesis

For each pass i=(v_i,l_i), let nu(i) be the registered pass beginning at
sigma^l_i(v_i). This exists because complete coverage partitions each
rotation hexagon into disjoint directed arcs. Ascents `i<nu(i)` count F.
Let U be free INTER-RUN exits; full-pass w2 exits are intra-run and not in U.
Let A be the ascents. Every element of U is a short exit and hence is
either an ascent or a descent. A free descent opens an already used orbit:
its target is E(v_nu(i)), so its run-opening event is a repeat.

Define:

    a = |A \ U|,
    J = {i+1: i in U, nu(i)<i},
    Rpt = all repeat RUN OPENINGS (events, not distinct target orbits),
    eta = |Rpt \ J|.

J is a subset of Rpt and |Rpt|=e. Therefore, with no restriction on delta,

    a+eta = F-|U intersect A| + e-|U minus A|
          = F+e-f_out = delta.

The proof also works with heavy joints and x arcs. It does not equate
visited rotation windows with registered pass entries. An ascent at the
last pass cannot occur in a complete word. Full passes have nu(i)=i.

The units are TYPED obligations. At delta2 the possibilities are exactly
`(a,eta)=(2,0),(1,1),(0,2)`; they do not assert two distinct physical edges.
A PAID ASCENT RE-ENTRY contributes one a and one eta on the SAME joint.
Repeated entries to one target orbit are separately counted.

In a bipartite event graph, one side contains ascent obligations and
repeat-opening obligations, the other side literal joints. An obligation
has its actual joint as its unique incident vertex. A joint can have
degree two, so counting joint vertices instead of obligations loses a unit.
The identity, not graph terminology, is the load-bearing fact.

## 3. Multi-piece privacy, with the necessary overlap correction — PROVED

Partition a run sequence into labelled pieces, with NO run straddling a
piece boundary. A piece may comprise several intervals. For each orbit Q,
let r_Q be the number of pieces containing it, and put `s=sum_Q(r_Q-1)`.
Scan runs chronologically. The first occurrence of Q has no charge. The
first occurrence of Q in each subsequently new piece gets charged to its
run-opening event. These are distinct repeat openings, even if several
pieces contain the same orbit. Let Gamma be this set of s charged events.

Select a_d distinct missing-ascent obligations and eta_d distinct exceptional
repeat obligations as designated defects; q=a_d+eta_d. Write

    o = |Gamma intersect J|,
    z = |Gamma intersect designated_exceptional_events|.

Since the remaining charged events are distinct, undesignated eta events,

    delta >= q + s - o - z.                       (P139)

No supposition about the size of the word or its continuation is used.
This is a general multi-defect privacy theorem, but it is NOT the
unconditional `delta>=q+s` conjecture. That stronger form requires BOTH
o=0 and z=0 to be established geometrically for the chosen cuts.
Overlapping ascent/repeat obligations on a single joint do not change
P139: they live in different typed sets, while z prevents charging the
same repeat obligation twice.

For any valid extraction partitioning retained pass entries, if p entries
and r orbits disappear from the UNION, the exact deficit identity is
`sum D_j = D - 5r + p + 5s`. An outside-only removal of an orbit still
present inside has r=0 for that orbit. This is not the private-block formula.

For Round138's M cut, a_d=1,eta_d=0; for its R cut, a_d=0,eta_d=1.
The established run-interval argument gives o=z=0 in either case. Thus
P139 recovers precisely delta>=1+s, including the permitted INTERNAL root
return. For several pieces it gives the requested r_Q-1 charge, with the
explicit ordinary/designated exceptions that cannot be discarded.

### Adversarial counterexample — REFUTED fixed-cut extrapolation

The following locally legal n6 word is preserved verbatim, not a complete
720-window counterexample:

    5301245301234501253401253041253024153024513024501324501234051230451230541230514230512430512340

It has G2,F2,a1,eta1,delta2,x=H0. The missing-ascent and exceptional-repeat
obligations occur together at pass-entry event 2 (zero-based). With the
preserved Round138 cut its inside orbit is also registered outside. Declaring
both obligations designated gives q2,s1, but delta2, not >=3. The repeat
charge overlaps the designated repeat, so z=1. It satisfies P139 exactly.
This refutes blindly retaining the old cut and adding one to q; it does
NOT refute existence of a different two-defect canonical cut.

A complete NR4 control with no available one-gap/one-orbit reduction is:

    012301203102310132010321031201302130

It is a positive control for the remaining two-defect mechanisms, not an
n6 exception. The 131,518 symbolic event models (<=7 runs, <=3 consecutive
pieces, arbitrary ordinary/designated repeat sets) verify P139 and also
contain counterexamples to omitting o or z. This finite domain supports,
but does not replace, the arbitrary-length injection above.

## 4. Type-A reversed arc order — a new exclusion, PROVED

For Type A,F1 the three chronological arcs have nu cycle `0->2->1->0`.
Their three entry orbits differ, since the last symbols differ. If a=0,
the sole ascent after arc0 enters T=orb(arc2) by w2. Before arc2 the word
must visit arc1, in a different orbit, and must therefore reopen T.
Neither ordinary descent targets T: they target arc0 and arc1's orbits.
Thus eta>=1. If a>0 then delta>=1 directly. Consequently

    Type A, F1 => delta>=1.

This argument survives x and heavy arcs: changing phase within T cannot
visit arc1. For this cell the only F1 survivors are delta1,x=H0. Nine F1
rows with delta0 are excluded. Four F1/delta1 rows remain OPEN; do not
apply the F2 chronological-triple contraction to them.

## 5. Canonical decorated one-defect normalization — PROVED

The following extension is needed before consuming the new capacities.
It is restricted to F2,G2 and either delta0,x+H<=2, or delta1,x+H<=1.
It does NOT claim normalization for delta2.

### 5.1 Geometry and ordinary blocks

F2 Type A has chronological nu cycle 0->1->2->0. Type B has two ascent/
descent pairs. Each short LIGHT joint changes entry orbit, including the
length-five 201 exception to the last-symbol shortcut. A short heavy
intra-run joint uses BOTH an x unit and a heavy unit. Thus in delta1,H1,
x0 every short joint still ends its run. In delta0 a heavy intra-run joint
is possible only in x1,H1, and is confined to the affected ordinary block.

A free fresh ascent target T with no available reopening stays in one run
through its nu-successor arc c. All intervening passes are full. With no
paid intra-run move this is the ordinary five-entry lock. A genuine full
120 moves by E^2; a full weight-four intra-run joint moves by E^3.
An aligned PAID ascent enters E^2(c), or E^3(c) when its weight is four.
All others are off-target and use gap extraction, not a fictitious lock.

If u paid joints and h heavy excess occur in such an aligned/private block,
its entry count is `j=5-u-h`. The phase path cannot wind an extra time:
there are at most five distinct phase ports and at most two extra forward
steps in this cell. Remove the j entries, merge the rotationally adjacent
arcs, and preserve the exact external endpoint. Then

    Delta P=-(5-u-h), Delta O=-1,
    Delta D=-(u+h), Delta S=-u, Delta H=-h.

These formulas count an aligned paid ASCENT in u, even though it was not
an x event before contraction. No formula is used for an off-target opener.

The order choices are the Round138 Type-A / alpha / beta choices: when
T0=Q1 and the exception belongs to the inner pair, extract the inner gap
first. Completing its opener reconstitutes the outer run, which is then
contracted. Phase skips do not change the forced order
`op0<op1<cl1<cl0`: reaching op1 and cl0 requires the same allowed Q1
reopenings as before. A heavy fresh exit cannot supply a missing Q1 return.

### 5.2 delta0

All ascents are free and fresh, and every repeat is an ordinary free descent.
The two ordinary blocks exist, in inner-first order when nested. x or heavy
intra-run moves only shorten these private blocks as above; an inter-run
heavy move cannot leave an unfinished T block and return to T without an
unavailable repeat event. It must be outside that block. After two removals,
the word is full-pass, with

    P'=112+u+h, D'=8-u-h,
    e'=0, x'+H'<=x+H-u-h.

Retained paid joints are fresh inter-run joints or the retained x arcs.
In particular a retained heavy joint cannot become a new repeat after
contraction: it would already have targeted an old orbit before contraction.

### 5.3 delta1, M

There is one paid ascent and no exceptional repeat. The other free block is
private unless it is the usual beta outer block, in which case inner-first
extraction applies. If the paid ascent is aligned, contract it too. Otherwise
extract the off-target gap. No ordinary descent lies inside that gap; outside
ordinary returns target already registered boundary orbits. The multi-piece
lemma has o=z=0, regardless of an internal x move or a fresh heavy connector.
It yields two PRIVATE full-pass pieces with

    sum P >=117, sum D<=8,
    sum(e+x)<=x_original, sum H<=H_original.

The heavy joint may be the paid opener itself. Extraction deletes that joint,
so the inequality on retained H only improves. We never classify a heavy
opener by the light 201/210 labels.

### 5.4 delta1, R: ordinary, protected, and slot-deletion alternatives

All ascents are free. There is exactly one nonordinary repeat event E*.
If its target is not an ascent-target orbit, contract both unaffected blocks;
the resulting full chain has `e'+x'<=1+x`, H'<=H, D'<=8, P'>=112.
An absorbed 120 return is counted as x after contraction, not silently lost.

Otherwise use the same target-based Type-A/Type-B selection as Round138.
Contract the unaffected block (possibly shorter by its one x move) or extract
the beta inner gap first. There are three possibilities for E*.

* E* is inside the gap, returning to its first orbit T. That orbit was first
  opened at the gap start. Its last entry is c, so after renaming the endpoints
  are phase0 and phase4. It has exactly two runs; all other orbits are fresh.
  Privacy follows by P139 with the internal E* excluded from Gamma. The inside
  piece is R, R_X, or R_H, defined below. The outside piece is ordinary with
  any unused x/heavy mark. Total deficit<=8 and pass total>=117.
* E* is after the closer, or is the free ascent re-entering T from the left.
  The segment from E(c) to c must avoid a T port used on the other side.
  With x0 this traverses all five ports, impossible. With the sole x1 it has
  EXACTLY four ports and omits one. Thus all external T registration consists
  of that ONE omitted port. The four-port block can be removed even though
  T is not private; T remains registered outside. This removes x and the
  exceptional repeat event. Remove the other ordinary five-entry block too:
  `P'=113,O'=25,D'=12,e'=x'=H'=0`. This is the special nonprivate slot-deletion
  case. Applying the private `Delta O=-1` to the four-port deletion would
  be wrong; we expressly use `Delta O=0` there.
* E* becomes an intra-run joint at an aligned contraction seam. Absorb it,
  retaining its x/heavy costs, and use the full-chain alternative.

These possibilities are exhaustive by chronology relative to the chosen
gap. In the second alternative no heavy skip can replace x1: a heavy
intra-run skip costs x1+H1, exceeding delta1's remaining budget.
The two ascent-target orbits cannot coincide via a free-ascent E*: each
complementary traversal E(c_i)..c_i would have to omit the other traversal's
ports. Each requires a skip, while only one is available. Type A excludes
the coincidence directly by distinct last symbols. In beta order the unique
nonordinary return to the OTHER target cannot substitute for the forced
outer ordinary return, so the same inner-first order applies.

### 5.5 Full-chain heavy cut and sharing

For a full-pass word put b=e+x. Cutting at one heavy edge creates two light
pieces. If an orbit is shared between them, a repeat opening pays for it,
except for the orbit of an intra-run heavy cut, which is paid by that x.
Thus s<=b. For b<=1:

* s0: local light b budgets sum<=1; sum D_j=D'.
* s1: both pieces have b0; sum D_j=D'+5.

In the latter case the distinguished heavy x or crossing return already
uses the sole b unit. This is a proved event charge, not the false assertion
that all heavy-cut pieces are orbit-disjoint. With b0,H2 the pieces are
private. H2 is exactly one w5 or two w4 joints; no other multiset is possible.
One w5 gives two light pieces, two w4 gives three.

## 6. Capacity models, inclusions, and independent computation

The reused N*(b,0,d) model allows arbitrary non-E intra-orbit phase jumps
at one b token, and repeated runs at one b token; it is an OVER-approximation
of the literal full-chain moves, which suffices for an upper bound. Different
passes must occupy different hexagons. No supply-side uniqueness assumption
is made. Fresh inter-run connectors are the literal full-pass 201/210 joints.

The new N*(2,0,8)=92 computation uses the established R115 model. A materially
independent whole-run search, with its own literal geometry and explicit
per-orbit counts, verifies 92. Feature-disabled b0/b1 controls give 62/77.
The independent run search may optimistically erase the largest deficits
using future b re-entries. Erasing more than is reachable only UNDERestimates
remaining deficit; it is safe pruning, not a supply upper bound.

New marked root-return models:

* R_X(d): exactly two root runs, first port0, terminal port4, all other
  orbits fresh; exactly one genuine intra-run 120 and no heavy joint.
* R_H(d): same root constraint, no x; exactly one inter-run w4 joint,
  all other joints free or genuine light. The heavy move may be the return.

Both use full passes and pairwise distinct hexagons. They include precisely
the protected pieces of section 5, not arbitrary repeated-orbit chains.
Port-by-port and precomputed-whole-run implementations agree in BOTH maximum
and accepted count for every exact deficit 0..8. They separately reproduce
the old R(d) maxima/counts when the new feature is disabled.

| exact d | R(d) | R_X(d) | R_H(d) |
|---:|---:|---:|---:|
|0|20|empty|15|
|1|empty|19|19|
|2|8|empty|empty|
|3|empty|7|22|
|4|empty|empty|26|
|5|empty|empty|30|
|6|24|empty|34|
|7|empty|23|38|
|8|22|empty|52|

The marked maxima/counts are FINITE-EXHAUSTIVE, not inferred from the low
deficit values. Metadata records committed blob hashes separately from
runtime source bytes, executable hashes, arguments, caps and exact nodes.
R115's historical CRLF file is not mislabeled a committed blob hash.

N1* and N2* are NOT used. The reported Claude N1*(0,0,13)=102 does not by
itself establish inclusion of our surviving mixed/crossing defect models.
No new generic 122-pass solver is introduced.

### The +15 extrapolation — REFUTED as a universal law

At d8 the independently exhausted values b0,1,2 are 62,77,92. This proves
only those cells. The unlimited proposed equality is false: N* has at most
120 passes because its hexagons are distinct. N*(0,0,0)=20, so the proposed
b7 value 20+15*7=125 is impossible. The exact smallest failing b is not
claimed. A restricted low-b theorem remains CONJECTURE and is not consumed.

## 7. Convolutions and extremal seam certificates

C0 at deficit <=d, d0..8 is `[20,20,33,33,46,46,49,58,62]`.
C1 there is C0+15, using the actual archived entries, not a general +15 law.

| Included model | Required P (at least) | Upper bound / refinement |
|---|---:|---:|
|full b<=2,H0,D<=8|112|92|
|full b0,H1,D<=8|112|two C0: 92|
|full b1,H1, no cross-piece orbit|112|C1+C0: 107|
|full b1,H1, one cross-piece orbit|112|two C0 at D<=13: 112; seams impossible|
|full b0,H2, one w5|112|two C0: 92|
|full b0,H2, two w4|112|three C0 at D<=8: 112; seams impossible|
|private M gap, x<=1,H0|117|C1+C0: 107|
|private M gap, x0,H<=1|117|three C0: 112|
|protected R + ordinary, no extra mark|117|R+C0: 82|
|protected R_X + ordinary|117|R_X+C0: 77|
|protected R + C1|117|R+C1: 97|
|protected R_H + ordinary|117|R_H+C0: 77|
|protected R + ordinary split at heavy|117|R+C0+C0: <=112|
|nonprivate four-port deletion + ordinary lock|113|C0(12)=83|

All convolutions are evaluated over integer deficit splits, with empty
R cells omitted. When a removed x/heavy mark increases required P and
reduces D, these same monotone bounds remain valid.

For the two-piece D13 equality, the only deficit split is 4/9 or 9/4,
with 46/66 passes. Recheck ALL 312 genuine w4 seams, now allowing a shared
orbit instead of prematurely rejecting it: every seam has a HEXAGON
collision. This strengthens the old orbit-first R135 test. In particular
the six cases with exactly one shared orbit ALSO collide in hexagons.

For the three-piece D8 equality the splits are permutations of (0,4,4)
and (2,2,4), not just the former. Independently enumerate the C0 extremizers
at deficits 0,2,4. There are 78 first-seam attempts: 30 orbit collisions,
40 further hexagon collisions, and 8 surviving pairs. Their 104 second-seam
attempts give 53 orbit collisions and 51 further hexagon collisions. None
is a full triple. This domain is normalized only by proved value-renaming
S6 symmetry; all genuine w4 targets and all extremal chains are retained.

## 8. Local controls and failure ledger

* NR4: complete finite enumeration of normalized literal walks L<=39 with
  P<=8: 162,536,447 visited search nodes, 17,451 complete words in that
  domain. Among them 1,506 have G2 and delta+x+H<=F.
* All target F2/delta<=1 controls enter the full-chain or gap model of
  section 5. Four reversed-Type-A F1 controls and 90 Type-B delta2 controls
  have no reduction in the specified one-gap plus arbitrary single-orbit
  contraction domain. These are useful positive hard-core controls.
* The 67 previously preserved local shared configurations are replayed
  without filtering their extra defect. Their fused-event annotation is
  new. Their 15 distinct words are not 67 independent complete NR6 samples.
* All marked-capacity maximizing paths are checked in literal geometry;
  general N* paths are separately identified as relaxed-model witnesses.

The local controls do not prove normalization. The universal inclusion is
the chronological/slot argument of section 5. Conversely, finding a legal
local shared configuration does not prove extendability to 720 windows.

## 9. Full closure table and exact residual scope

| delta,x,H | rows | result |
|---|---:|---|
|0,0,0|8|CLOSED: F1 order obstruction or two locks|
|0,1,0|8|CLOSED: F1 order obstruction or decorated locks|
|0,0,1|8|CLOSED: F1 order obstruction or heavy cut|
|0,2,0|5|CLOSED: N*(2,0,8)|
|0,1,1|5|CLOSED: mixed heavy/b bound and seams|
|0,0,2|5|CLOSED: heavy multiset and extremal triple seams|
|1,0,0|11|7 F2 CLOSED; 4 reversed-Type-A F1 OPEN|
|1,1,0|7|CLOSED: decorated M/R or nonprivate slot deletion|
|1,0,1|7|CLOSED: heavy M/R or absorbed full-chain model|
|2,0,0|9|OPEN: genuine two-defect mechanisms|

This excludes 60/73 distinct resource envelopes (82.19%), including ALL
mechanisms in each closed envelope, or 65/78 heavy-refined tuples. The
percentage is explicitly resource-envelope weighted, not a count of literal
words or target-orbit equality patterns. The exact unresolved envelopes are:

1. Type A,F1,delta1,x=H0, e=0..3, f_out=e. The reversed three-arc order
   must be retained. M is possible for e0..2, R for e1..3 at the event level.
2. Type A,F2,delta2,x=H0, e=0..3, f_out=e.
3. Type B,F2,delta2,x=H0, e=0..4, f_out=e.

The last two contain M+M, M+R (including a fused joint), and R+R. For each
row the machine ledger lists its feasible (a,eta). These are sharply defined
mechanisms but NOT yet five proved exact capacity models. We claim the
major-reduction stopping condition, not the stronger complete-decomposition
stopping condition.

## 10. Why the remaining work is different

The repeated-hexagon intervals may be disjoint, nested or crossing; a tripled
hexagon can share an arc endpoint. Chronological Type-A F1 is not obtained
from the F2 order by renaming. A two-defect return can itself be the charge
for a shared orbit (z>0), and an ordinary return across a chosen cut can pay
o>0. Local five-port occupancy alone does not forbid either. The exact
missing inclusion invariant is a cut construction controlling BOTH o and z
and the repeated-hexagon multiplicity inside the resulting pieces.

Blindly applying a three-ordinary-chain convolution would assume that very
invariant: crossed or reversed arcs need not produce three hexagon-simple
pieces, and an extracted piece can share an orbit already paid by a defect.
The exhaustive NR4 no-reduction controls and the literal n6 fused/sharing
control expose these gaps. Phase projection is not used as a quotient.

An event-order CSP, coloured-run injection, literal permutation/phase algebra,
private and nonprivate surgery, chain capacities, and extremal seam matching
were distinct approaches in this round. No continuation search, broad NR6
DFS, or unproved +15 pruning was needed. The full finite source/certificate
trail is in the accompanying JSONs and verifier.

For k1 the same algebra gives delta+x+H<=F+1. That admits NEW three-unit
cases and is not closed by the present one-defect normalization. No separate
k1 project was started. `(2,2)` remains OPEN; outer ledger remains **11/55**.
NR6 remains ASSUMED. This project has NOT proved `L6>=872`.

ASTRA_G2_K2_MAJOR_REDUCTION
